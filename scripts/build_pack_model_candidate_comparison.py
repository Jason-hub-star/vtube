#!/usr/bin/env python3
"""Build a model-candidate comparison report for Mini Cubism pack splitter."""

from __future__ import annotations

import argparse
import json
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = ROOT / "experiments/mini-cubism-pack-splitter-v0-001"
PACKS = ["hair_pack", "outfit_pack", "accessory_pack", "keypose_asset_pack"]

MODEL_REPORTS = [
    {
        "id": "layerd_birefnet",
        "label": "LayerD BiRefNet",
        "report": "layerd_birefnet_inference_report.json",
        "role": "layer decomposition reference",
    },
    {
        "id": "birefnet",
        "label": "BiRefNet",
        "report": "birefnet_inference_report.json",
        "role": "stable foreground alpha cleanup",
    },
    {
        "id": "birefnet_hr",
        "label": "BiRefNet HR",
        "report": "birefnet_hr_inference_report.json",
        "role": "primary high-resolution alpha cleanup",
    },
    {
        "id": "birefnet_matting",
        "label": "BiRefNet matting",
        "report": "birefnet_matting_inference_report.json",
        "role": "optional edge/matting cleanup",
    },
    {
        "id": "sam2_tiny",
        "label": "SAM2 tiny ROI",
        "report": "facebook_sam2_1_hiera_tiny_roi_refinement_report.json",
        "role": "ROI point-prompt refinement test",
    },
    {
        "id": "sam2_large",
        "label": "SAM2 large ROI",
        "report": "facebook_sam2_1_hiera_large_roi_refinement_report.json",
        "role": "ROI point-prompt refinement test",
    },
    {
        "id": "fashion_segformer",
        "label": "Fashion SegFormer",
        "report": "fashion_segformer_probe_report.json",
        "role": "outfit semantic hint probe",
    },
    {
        "id": "anime_instance",
        "label": "AnimeInstance",
        "report": "anime_instance_probe_report.json",
        "role": "anime instance probe",
    },
]


MODEL_DECISIONS = {
    "layerd_birefnet": {
        "decision": "REFERENCE_ONLY",
        "why": "Hair/outfit are usable candidates, but accessory/keypose masks are broad.",
    },
    "birefnet": {
        "decision": "SELECTED_STABLE_FALLBACK",
        "why": "All four packs passed runtime and simple mask gates with no broad-mask issues.",
    },
    "birefnet_hr": {
        "decision": "SELECTED_PRIMARY_ALPHA",
        "why": "All four packs passed and it is the best default for full-pack alpha cleanup.",
    },
    "birefnet_matting": {
        "decision": "OPTIONAL_EDGE_CLEANUP",
        "why": "Hair/outfit/accessory passed, but keypose became near full-canvas and must not be used there.",
    },
    "sam2_tiny": {
        "decision": "REJECT_CURRENT_OUTPUTS",
        "why": "Runtime passed, but strict visual QA detected cropped or fragment masks.",
    },
    "sam2_large": {
        "decision": "REJECT_CURRENT_OUTPUTS",
        "why": "Large model did not improve the ROI crop/fragment failure pattern.",
    },
    "fashion_segformer": {
        "decision": "BLOCKED_NOT_SELECTED",
        "why": "The current HF repo cannot be loaded by the default Transformers image-segmentation pipeline.",
    },
    "anime_instance": {
        "decision": "BLOCKED_NOT_SELECTED",
        "why": "The current HF repo is not directly loadable by Transformers without a custom legacy wrapper.",
    },
}

PACK_DECISIONS = {
    "base_mannequin": {
        "primary": "imagegen alpha base",
        "fallback": "none",
        "use": "Keep the two-piece rig underlayer: chest and pelvis covered, abdomen visible.",
        "blocked_by": [],
        "next_action": "Use as the stable mannequin target for pack fitting.",
    },
    "hair_pack": {
        "primary": "ZhengPeng7/BiRefNet_HR",
        "fallback": "ZhengPeng7/BiRefNet",
        "use": "Full-pack alpha cleanup, then separate hair-specific splitter for front/side/back/tips.",
        "blocked_by": ["No actual 18+ strand-level hair split yet."],
        "next_action": "Run hair band/contour splitter on the selected BiRefNet HR mask.",
    },
    "outfit_pack": {
        "primary": "ZhengPeng7/BiRefNet_HR",
        "fallback": "ZhengPeng7/BiRefNet",
        "use": "Full-pack alpha cleanup for outfit pieces; semantic Fashion SegFormer is not selected.",
        "blocked_by": ["No proven semantic outfit label split from Fashion SegFormer."],
        "next_action": "Use geometry/ROI splitter for sleeves, top, frills, ribbons on BiRefNet HR alpha.",
    },
    "accessory_pack": {
        "primary": "ZhengPeng7/BiRefNet_HR",
        "fallback": "ZhengPeng7/BiRefNet",
        "use": "Use only as full-pack alpha cleanup for now.",
        "blocked_by": ["Current SAM2 ROI outputs are cropped/fragments.", "Small accessories are too dense for the current layout."],
        "next_action": "Regenerate or relayout accessory pack with larger spacing, then retry connected-component or SAM2 ROI.",
    },
    "keypose_asset_pack": {
        "primary": "ZhengPeng7/BiRefNet",
        "fallback": "ZhengPeng7/BiRefNet_HR",
        "use": "Use only as full-pack alpha cleanup for now; do not split final eye/mouth states from current SAM2 output.",
        "blocked_by": ["Current SAM2 ROI outputs are cropped/fragments.", "BiRefNet-matting over-expands keypose alpha."],
        "next_action": "Regenerate as separate eye keypose pack and mouth keypose pack with larger spacing and no overlap.",
    },
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def font(size: int) -> ImageFont.ImageFont:
    for candidate in [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def quality_for_pack(report: dict[str, Any], pack_id: str) -> dict[str, Any] | None:
    records = report.get("records") or []
    direct = [rec for rec in records if rec.get("pack_id") == pack_id]
    if not direct:
        return None
    statuses = [rec.get("quality_status") or rec.get("quality") for rec in direct]
    if any(status == "VISUAL_FAIL" for status in statuses):
        status = "VISUAL_FAIL"
    elif any(status == "REVISE_MASK" for status in statuses):
        status = "REVISE_MASK"
    elif any(status == "CANDIDATE" for status in statuses):
        status = "CANDIDATE"
    else:
        status = statuses[0] or "UNKNOWN"
    return {
        "status": status,
        "record_count": len(direct),
        "sample_path": next((rec.get("output_path") for rec in direct if rec.get("output_path")), None),
        "issues": sorted({issue for rec in direct for issue in rec.get("issues", [])}),
        "hard_failures": sorted({issue for rec in direct for issue in rec.get("hard_failures", [])}),
    }


def summarize_model(exp: Path, item: dict[str, str]) -> dict[str, Any]:
    path = exp / "reports" / item["report"]
    report = load_json(path)
    if report is None:
        return {
            "id": item["id"],
            "label": item["label"],
            "role": item["role"],
            "report_path": str(path),
            "status": "MISSING_REPORT",
            "actual_hf_inference_count": 0,
            "pack_results": {},
            **MODEL_DECISIONS[item["id"]],
        }
    return {
        "id": item["id"],
        "label": item["label"],
        "role": item["role"],
        "report_path": str(path),
        "contact_sheet": report.get("contact_sheet"),
        "status": report.get("status"),
        "runtime_status": report.get("runtime_status"),
        "quality_status": report.get("quality_status"),
        "model_id": report.get("model_id"),
        "actual_hf_inference_count": report.get("actual_hf_inference_count", 0),
        "issue_count": report.get("issue_count"),
        "hard_failure_count": report.get("hard_failure_count", 0),
        "error_type": report.get("error_type"),
        "error": report.get("error"),
        "pack_results": {pack: quality_for_pack(report, pack) for pack in PACKS},
        **MODEL_DECISIONS[item["id"]],
    }


def image_card(
    sheet: Image.Image,
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    result: dict[str, Any] | None,
) -> None:
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill="#fffaf2", outline="#d6cec5")
    small = font(11)
    draw.text((x0 + 8, y0 + 7), title, fill="#202124", font=small)
    if not result:
        draw.text((x0 + 8, y0 + 30), "no output", fill="#8a5a00", font=small)
        return
    status = result.get("status", "UNKNOWN")
    color = "#287a3e" if status == "CANDIDATE" else ("#b3261e" if status == "VISUAL_FAIL" else "#9a6700")
    draw.text((x0 + 8, y0 + 30), status, fill=color, font=small)
    sample = result.get("sample_path")
    if sample and Path(sample).exists():
        image = Image.open(sample).convert("RGBA")
        bbox = image.getchannel("A").getbbox()
        crop = image.crop(bbox) if bbox else image
        bg = Image.new("RGB", crop.size, "#f8f6f0")
        bg.paste(crop.convert("RGB"), mask=crop.getchannel("A"))
        bg.thumbnail((x1 - x0 - 24, y1 - y0 - 60), Image.Resampling.LANCZOS)
        sheet.paste(bg, (x0 + (x1 - x0 - bg.width) // 2, y0 + 52))
    else:
        issues = ", ".join(result.get("issues") or result.get("hard_failures") or [])
        draw.text((x0 + 8, y0 + 52), issues[:28] or "no sample", fill="#5f6368", font=small)


def wrap_lines(text: str, width: int) -> str:
    return "\n".join(textwrap.wrap(text, width=width)) or text


def build_contact_sheet(models: list[dict[str, Any]], out: Path) -> None:
    row_h = 190
    left_w = 190
    cell_w = 210
    verdict_w = 240
    header_h = 88
    width = left_w + len(PACKS) * cell_w + verdict_w
    height = header_h + max(1, len(models)) * row_h
    sheet = Image.new("RGB", (width, height), "#f4f0e8")
    draw = ImageDraw.Draw(sheet)
    draw.text((18, 14), "Mini Cubism pack model candidate comparison", fill="#202124", font=font(24))
    draw.text((18, 48), "Actual HF probes and blocked candidates. PASS here does not promote Mini Cubism project.", fill="#5f6368", font=font(13))
    small = font(12)
    for i, pack in enumerate(PACKS):
        draw.text((left_w + i * cell_w + 10, header_h - 24), pack, fill="#202124", font=small)
    draw.text((left_w + len(PACKS) * cell_w + 10, header_h - 24), "decision", fill="#202124", font=small)
    for row, model in enumerate(models):
        y = header_h + row * row_h
        draw.rectangle([0, y, width, y + row_h], outline="#ddd5ca")
        draw.text((14, y + 16), model["label"], fill="#202124", font=font(14))
        draw.text((14, y + 40), str(model.get("status")), fill="#5f6368", font=small)
        draw.text((14, y + 62), model["decision"], fill="#5f6368", font=small)
        for i, pack in enumerate(PACKS):
            box = (left_w + i * cell_w + 8, y + 8, left_w + (i + 1) * cell_w - 8, y + row_h - 8)
            image_card(sheet, draw, box, pack, (model.get("pack_results") or {}).get(pack))
        vx = left_w + len(PACKS) * cell_w
        draw.rectangle([vx + 8, y + 8, width - 8, y + row_h - 8], fill="#fffaf2", outline="#d6cec5")
        draw.text((vx + 18, y + 20), model["decision"], fill="#202124", font=small)
        draw.multiline_text((vx + 18, y + 44), wrap_lines(model["why"], 31), fill="#5f6368", font=small, spacing=3)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def build_markdown(report: dict[str, Any], out: Path) -> None:
    lines = [
        "# Mini Cubism Pack Model Candidate Decision",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Verdict",
        "",
        "Mini Cubism project promotion stays blocked. The model comparison is complete enough to choose roles, but accessory and keypose pack splitting still needs relayout/regeneration before rig promotion.",
        "",
        "## Pack Decisions",
        "",
        "| Pack | Primary | Fallback | Use | Blocker | Next action |",
        "|---|---|---|---|---|---|",
    ]
    for pack, decision in report["pack_decisions"].items():
        blockers = "<br>".join(decision["blocked_by"]) if decision["blocked_by"] else "none"
        lines.append(
            f"| `{pack}` | {decision['primary']} | {decision['fallback']} | {decision['use']} | {blockers} | {decision['next_action']} |"
        )
    lines += [
        "",
        "## Model Decisions",
        "",
        "| Model | Status | Decision | Actual outputs | Why |",
        "|---|---:|---|---:|---|",
    ]
    for model in report["models"]:
        lines.append(
            f"| {model['label']} | {model.get('status')} | {model['decision']} | {model.get('actual_hf_inference_count', 0)} | {model['why']} |"
        )
    lines += [
        "",
        "## Practical Pipeline",
        "",
        "1. Keep the current two-piece base mannequin.",
        "2. Use `BiRefNet_HR` as the default alpha cleanup for hair and outfit packs.",
        "3. Use `BiRefNet` or `BiRefNet_HR` only as full-pack alpha cleanup for accessory and keypose packs.",
        "4. Do not use current SAM2 ROI outputs for production because they are cropped/fragments.",
        "5. Regenerate or relayout accessory/keypose packs with larger spacing, then retry component/SAM2 splitting.",
        "6. Build Mini Cubism only after the next QA report has no visual fail for accessory/keypose outputs.",
        "",
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Mini Cubism pack model comparison artifacts.")
    parser.add_argument("--experiment", default=str(DEFAULT_EXPERIMENT))
    args = parser.parse_args()
    exp = Path(args.experiment).resolve()
    models = [summarize_model(exp, item) for item in MODEL_REPORTS]
    contact_sheet = exp / "reports" / "model_candidate_comparison_contact_sheet.png"
    build_contact_sheet(models, contact_sheet)
    report = {
        "schema_version": 1,
        "experiment_id": exp.name,
        "generated_at": now(),
        "status": "MODEL_COMPARISON_DONE_PROMOTION_BLOCKED_RELAYOUT_REQUIRED",
        "promotion_allowed": False,
        "models": models,
        "pack_decisions": PACK_DECISIONS,
        "contact_sheet": str(contact_sheet),
        "decision_markdown": str(exp / "reports" / "model_candidate_decision.md"),
    }
    write_json(exp / "reports" / "model_candidate_comparison_report.json", report)
    build_markdown(report, exp / "reports" / "model_candidate_decision.md")
    print(
        json.dumps(
            {
                "ok": True,
                "status": report["status"],
                "models": len(models),
                "contact_sheet": str(contact_sheet),
                "report": str(exp / "reports" / "model_candidate_comparison_report.json"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

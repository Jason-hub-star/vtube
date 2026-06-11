#!/usr/bin/env python3
"""Build a v22 64-part manifest candidate with corrected B4 and provisional B5 layers."""

from __future__ import annotations

import importlib.util
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
BASE_MANIFEST_SCRIPT = ROOT / "scripts/build_cubism_v2_64part_candidate_manifest_002.py"
REPORT_DIR = EXP / "reports/v22_64part_corrected_b4_b5_manifest"
REPORT_JSON = REPORT_DIR / "v22_64part_corrected_b4_b5_manifest.json"
REPORT_MD = REPORT_DIR / "v22_64part_corrected_b4_b5_manifest.md"
CONTACT_SHEET = REPORT_DIR / "v22_64part_corrected_b4_b5_manifest_contact_sheet.png"
CANVAS = 2048


LAYER_DIR_OVERRIDES = {
    "B4": EXP / "v22_b4_b5_anchor_corrected_auto_draft/normalized_layers",
    "B5": EXP / "v22_b5_provisional_minipass_candidate/normalized_layers",
}

EVIDENCE = {
    "b4_corrected_candidate": EXP
    / "reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_anchor_corrected_auto_draft_report.json",
    "b4_focused_review": EXP / "reports/v22_b4_hair_focused_review/v22_b4_hair_focused_review.json",
    "b5_provisional_candidate": EXP
    / "reports/v22_b5_provisional_minipass_candidate/v22_b5_provisional_minipass_candidate_report.json",
    "b5_provisional_overlay_qa": EXP
    / "reports/v22_b5_provisional_minipass_candidate/v22_b5_provisional_minipass_overlay_qa_report.json",
}

B5_TARGETS = {"torso_base", "shoulder_L", "shoulder_R"}


def load_base_module():
    spec = importlib.util.spec_from_file_location("v22_base_manifest", BASE_MANIFEST_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {BASE_MANIFEST_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = load_base_module()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def image_mode_size(path: Path) -> tuple[str, list[int]]:
    img = Image.open(path)
    return img.mode, list(img.size)


def bbox_from_alpha(path: Path) -> list[int] | None:
    img = Image.open(path).convert("RGBA")
    arr = np.asarray(img.getchannel("A"), dtype=np.uint8)
    ys, xs = np.where(arr > 5)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def alpha_coverage(path: Path) -> float:
    img = Image.open(path).convert("RGBA")
    arr = np.asarray(img.getchannel("A"), dtype=np.uint8)
    return round(float((arr > 5).mean()), 8)


def b4_gate(part_id: str, b4_front_ids: set[str]) -> tuple[str, str]:
    if part_id in b4_front_ids:
        return (
            "B4_FRONT_HAIR_MOTION_READINESS_CANDIDATE_REVIEW_REQUIRED",
            "TECHNICAL_PRESENT_B4_FRONT_HAIR_MOTION_CANDIDATE_REVIEW_REQUIRED",
        )
    return (
        "B4_SECONDARY_DRAW_ORDER_OR_MASK_REVIEW_REQUIRED",
        "TECHNICAL_PRESENT_B4_SECONDARY_REVIEW_REQUIRED",
    )


def b5_gate(part_id: str, b5_qa_by_part: dict[str, dict]) -> tuple[str, str]:
    if part_id in b5_qa_by_part:
        verdict = b5_qa_by_part[part_id]["qa_verdict"]
        if verdict == "PASS_DRAW_ORDER_MASK_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED":
            return (
                verdict,
                "TECHNICAL_PRESENT_B5_DRAW_ORDER_MASK_IMPROVEMENT_REVIEW_REQUIRED",
            )
        return (verdict, "TECHNICAL_PRESENT_B5_TORSO_REVIEW_REQUIRED")
    return (
        "B5_COPIED_FROM_REFINED_MASK_V2_REVIEW_REQUIRED",
        "TECHNICAL_PRESENT_B5_COPIED_REVIEW_REQUIRED",
    )


def layer_dir_for(batch_id: str) -> Path:
    return LAYER_DIR_OVERRIDES.get(batch_id, BASE.BATCH_REPORTS[batch_id]["layer_dir"])


def build_manifest() -> dict:
    spec = load_json(BASE.SPEC_JSON)
    g0 = load_json(BASE.G0_JSON)
    b4_focused = load_json(EVIDENCE["b4_focused_review"])
    b5_qa = load_json(EVIDENCE["b5_provisional_overlay_qa"])
    b4_front_ids = {
        entry["part_id"]
        for entry in b4_focused["entries"]
        if entry["recommendation"] == "FRONT_HAIR_CHILD_CANDIDATE_HUMAN_REVIEW_REQUIRED"
    }
    b5_qa_by_part = {entry["part_id"]: entry for entry in b5_qa["qa_entries"]}

    batch_status = {}
    for batch_id, cfg in BASE.BATCH_REPORTS.items():
        batch_status[batch_id] = {
            "layer_report": rel(cfg["layer_report"]),
            "layer_dir": rel(layer_dir_for(batch_id)),
            "visual_report": rel(cfg["visual_report"]),
            "source_note": "overridden_by_corrected_b4_b5_candidate" if batch_id in LAYER_DIR_OVERRIDES else "base_v22_candidate",
        }
    batch_status["B4"]["corrected_candidate_report"] = rel(EVIDENCE["b4_corrected_candidate"])
    batch_status["B4"]["focused_review"] = rel(EVIDENCE["b4_focused_review"])
    batch_status["B5"]["provisional_candidate_report"] = rel(EVIDENCE["b5_provisional_candidate"])
    batch_status["B5"]["provisional_overlay_qa_report"] = rel(EVIDENCE["b5_provisional_overlay_qa"])

    entries = []
    missing: list[str] = []
    wrong_mode: list[str] = []
    wrong_size: list[str] = []
    empty: list[str] = []
    for part in spec["parts"]:
        part_id = part["id"]
        batch_id = BASE.PART_SOURCE_BATCH[part_id]
        layer_path = layer_dir_for(batch_id) / f"{part_id}.png"
        exists = layer_path.exists()
        mode = None
        size = None
        bbox = None
        coverage = 0.0
        if exists:
            mode, size = image_mode_size(layer_path)
            bbox = bbox_from_alpha(layer_path)
            coverage = alpha_coverage(layer_path)
            if mode != "RGBA":
                wrong_mode.append(part_id)
            if size != [CANVAS, CANVAS]:
                wrong_size.append(part_id)
            if bbox is None:
                empty.append(part_id)
        else:
            missing.append(part_id)

        if batch_id == "B4":
            visual_gate, manifest_status = b4_gate(part_id, b4_front_ids)
        elif batch_id == "B5":
            visual_gate, manifest_status = b5_gate(part_id, b5_qa_by_part)
        else:
            visual_gate = BASE.VISUAL_GATE_BY_BATCH[batch_id]
            manifest_status = "TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED"
        if not exists or mode != "RGBA" or size != [CANVAS, CANVAS] or bbox is None:
            manifest_status = "TECHNICAL_INCOMPLETE"

        entries.append(
            {
                **part,
                "source_batch": batch_id,
                "path": rel(layer_path) if exists else None,
                "exists": exists,
                "mode": mode,
                "size": size,
                "bbox": bbox,
                "alpha_coverage": coverage,
                "batch_visual_gate": visual_gate,
                "manifest_status": manifest_status,
            }
        )

    group_counts = Counter(entry["group"] for entry in entries if entry.get("exists"))
    visual_gate_counts = Counter(entry.get("batch_visual_gate", "UNKNOWN") for entry in entries)
    status_counts = Counter(entry["manifest_status"] for entry in entries)
    duplicate_ids = [part_id for part_id, count in Counter(entry["id"] for entry in entries).items() if count > 1]
    complete_technical = not missing and not wrong_mode and not wrong_size and not empty and not duplicate_ids
    b4_review_count = sum(1 for entry in entries if entry["source_batch"] == "B4")
    b5_review_count = sum(1 for entry in entries if entry["source_batch"] == "B5")

    manifest = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest_id": "cubism-v2-new-character-002-v22-64part-corrected-b4-b5-manifest-001",
        "status": "G1_64PART_CORRECTED_B4_B5_MANIFEST_TECHNICAL_PASS_REVIEW_REQUIRED"
        if complete_technical
        else "G1_64PART_CORRECTED_B4_B5_MANIFEST_TECHNICAL_REVISE",
        "spec": rel(BASE.SPEC_JSON),
        "g0_source_review": rel(BASE.G0_JSON),
        "g0_status": g0["status"],
        "canvas": [CANVAS, CANVAS],
        "batch_status": batch_status,
        "manifest_entries": entries,
        "quality_gate_interpretation": {
            "g1_64part_completeness": "PASS_TECHNICAL" if complete_technical else "REVISE_TECHNICAL",
            "g2_full_canvas_rgba": "PASS_TECHNICAL" if complete_technical else "REVISE_TECHNICAL",
            "g4_g5_visual_overlay": "REVIEW_REQUIRED_FOR_CORRECTED_B4_B5",
            "g6_manual_anchor_correction": "PROVISIONAL_B4_B5_CORRECTED_CANDIDATE_READY_FOR_REVIEW",
            "g7_mini_cubism_diagnostic": "BLOCKED_UNTIL_VISUAL_QA_ACCEPTS_B1_B5",
            "g8_real_cubism_authoring": "BLOCKED_UNTIL_MATERIAL_QA_AND_VISUAL_REVIEW",
            "param_hair_front": "HIDDEN_CONTRACT_ONLY",
        },
        "self_review": {
            "required_part_count": len(spec["parts"]),
            "manifest_entry_count": len(entries),
            "unique_manifest_part_count": len({entry["id"] for entry in entries}),
            "missing_part_count": len(missing),
            "wrong_mode_count": len(wrong_mode),
            "wrong_size_count": len(wrong_size),
            "empty_part_count": len(empty),
            "duplicate_part_count": len(duplicate_ids),
            "group_counts": dict(group_counts),
            "required_group_counts": spec["part_groups"],
            "group_counts_match_spec": dict(group_counts) == spec["part_groups"],
            "visual_gate_counts": dict(visual_gate_counts),
            "status_counts": dict(status_counts),
            "b4_entry_count": b4_review_count,
            "b5_entry_count": b5_review_count,
            "b4_front_hair_motion_candidate_count": len(b4_front_ids),
            "b5_provisional_target_count": len(B5_TARGETS),
            "b5_shoulder_improvement_candidate_count": b5_qa["self_review"]["shoulder_improvement_candidate_count"],
            "b5_torso_review_candidate": b5_qa["self_review"]["has_torso_review_candidate"],
            "material_pass_blocked": True,
            "validator_only_promotion_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "status": "PASS" if complete_technical else "REVISE",
        },
        "decision": (
            "This corrected B4/B5 manifest candidate is technically complete and uses improved B5 provisional layers, "
            "but it remains review-required. Do not promote to material PASS, Mini Cubism, or real Cubism."
        ),
        "next_action": [
            "Run corrected B4/B5 overlay QA from this manifest.",
            "Only after visual QA accepts corrected B4/B5 should G2-G5 material QA continue.",
            "Keep ParamHairFront hidden until front hair motion-readiness passes.",
        ],
    }
    return manifest


def draw_contact_sheet(manifest: dict) -> None:
    entries = manifest["manifest_entries"]
    cols = 8
    thumb = 210
    label_h = 66
    rows = math.ceil(len(entries) / cols)
    sheet = Image.new("RGB", (cols * thumb, rows * (thumb + label_h)), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, entry in enumerate(entries):
        row, col = divmod(idx, cols)
        x = col * thumb
        y = row * (thumb + label_h)
        fill = (230, 245, 230)
        if entry["source_batch"] in {"B4", "B5"}:
            fill = (255, 245, 220)
        draw.rectangle((x, y, x + thumb, y + label_h), fill=fill)
        draw.text((x + 5, y + 5), entry["id"][:28], fill=(20, 20, 20))
        draw.text((x + 5, y + 24), entry["source_batch"], fill=(50, 50, 50))
        draw.text((x + 5, y + 43), entry["batch_visual_gate"][:24], fill=(80, 60, 40))
        if entry.get("path"):
            img = Image.open(ROOT / entry["path"]).convert("RGBA")
            bg = Image.new("RGBA", (CANVAS, CANVAS), (244, 238, 226, 255))
            bg.alpha_composite(img)
            sheet.paste(bg.convert("RGB").resize((thumb, thumb), Image.Resampling.LANCZOS), (x, y + label_h))
        else:
            draw.rectangle((x, y + label_h, x + thumb, y + label_h + thumb), fill=(255, 210, 210))
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET)


def write_markdown(manifest: dict) -> None:
    lines = [
        "# Character 002 v22 64-Part Corrected B4/B5 Manifest",
        "",
        f"- status: `{manifest['status']}`",
        f"- G0 status: `{manifest['g0_status']}`",
        f"- contact sheet: `{rel(CONTACT_SHEET)}`",
        "",
        "## Gate Interpretation",
        "",
    ]
    for key, value in manifest["quality_gate_interpretation"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Self Review", ""])
    for key, value in manifest["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", "", manifest["decision"], "", "## Next Action", ""])
    lines.extend(f"- {item}" for item in manifest["next_action"])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    manifest = build_manifest()
    draw_contact_sheet(manifest)
    manifest["contact_sheet"] = rel(CONTACT_SHEET)
    save_json(REPORT_JSON, manifest)
    write_markdown(manifest)
    print(json.dumps({"status": manifest["status"], "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

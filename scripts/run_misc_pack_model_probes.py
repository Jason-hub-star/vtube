#!/usr/bin/env python3
"""Probe miscellaneous HF vision models for Mini Cubism pack splitter."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = ROOT / "experiments/mini-cubism-pack-splitter-v0-001"
MODEL_ALIASES = {
    "fashion_segformer": "Itbanque/fashion_segformer",
    "anime_instance": "dreMaz/AnimeInstanceSegmentation",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def font(size: int) -> ImageFont.ImageFont:
    for candidate in ["/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"]:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def model_slug(model_id: str) -> str:
    for alias, repo in MODEL_ALIASES.items():
        if model_id in {alias, repo}:
            return alias
    return model_id.replace("/", "_").replace("-", "_").lower()


def rgba_to_rgb(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    bg = Image.new("RGBA", image.size, (248, 246, 240, 255))
    bg.alpha_composite(image)
    return bg.convert("RGB")


def bbox_alpha(image: Image.Image) -> tuple[list[int], int, float]:
    alpha = image.convert("RGBA").getchannel("A")
    bbox = alpha.getbbox()
    nonzero = sum(alpha.histogram()[1:])
    if not bbox:
        return [0, 0, 0, 0], 0, 0.0
    left, top, right, bottom = bbox
    return [left, top, right - left, bottom - top], nonzero, nonzero / (image.width * image.height)


def build_sheet(records: list[dict[str, Any]], out: Path, title: str) -> None:
    cols = max(1, min(4, len(records)))
    cell_w, cell_h = 360, 420
    sheet = Image.new("RGB", (cols * cell_w, 78 + cell_h), "#f4f0e8")
    draw = ImageDraw.Draw(sheet)
    draw.text((18, 14), title, fill="#202124", font=font(22))
    small = font(13)
    for idx, rec in enumerate(records[:cols]):
        x = idx * cell_w
        y = 78
        draw.rectangle([x + 10, y + 10, x + cell_w - 10, y + cell_h - 10], fill="#fffaf2", outline="#d6cec5")
        image = Image.open(rec["output_path"]).convert("RGBA")
        bb = image.getchannel("A").getbbox()
        crop = image.crop(bb) if bb else image
        bg = Image.new("RGB", crop.size, "#f8f6f0")
        bg.paste(crop.convert("RGB"), mask=crop.getchannel("A"))
        bg.thumbnail((cell_w - 44, cell_h - 95), Image.Resampling.LANCZOS)
        sheet.paste(bg, (x + (cell_w - bg.width) // 2, y + 22))
        draw.text((x + 18, y + cell_h - 58), rec["pack_id"], fill="#202124", font=small)
        draw.text((x + 18, y + cell_h - 36), rec["quality_status"], fill="#287a3e" if rec["quality_status"] == "CANDIDATE" else "#9a6700", font=small)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe miscellaneous HF models on pack sources.")
    parser.add_argument("--experiment", default=str(DEFAULT_EXPERIMENT))
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--packs", default="outfit_pack")
    parser.add_argument("--task", default="image-segmentation")
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "mps"])
    args = parser.parse_args()

    exp = Path(args.experiment).resolve()
    manifest = load_json(exp / "pack_splitter_manifest.json")
    resolved_model_id = MODEL_ALIASES.get(args.model_id, args.model_id)
    slug = model_slug(resolved_model_id)
    report_path = exp / "reports" / f"{slug}_probe_report.json"
    packs = [pack.strip() for pack in args.packs.split(",") if pack.strip()]
    try:
        import torch
        from transformers import pipeline

        if args.device == "auto":
            device = "mps" if torch.backends.mps.is_available() else "cpu"
        else:
            device = args.device
        pipe = pipeline(args.task, model=resolved_model_id, trust_remote_code=True, device=device)
        records: list[dict[str, Any]] = []
        for pack_id in packs:
            source = Path(manifest["packs"][pack_id]["source"])
            source_image = Image.open(source).convert("RGBA")
            rgb = rgba_to_rgb(source_image)
            result = pipe(rgb)
            masks = result if isinstance(result, list) else [result]
            for index, item in enumerate(masks[:4]):
                mask = item.get("mask") if isinstance(item, dict) else None
                if mask is None:
                    continue
                mask = mask.convert("L").resize(source_image.size, Image.Resampling.LANCZOS)
                out = source_image.copy()
                out.putalpha(mask)
                out_path = exp / "hf_actual" / slug / pack_id / f"{pack_id}_{slug}_{index:02d}.png"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out.save(out_path)
                bbox, nonzero, coverage = bbox_alpha(out)
                issues = []
                if nonzero == 0:
                    issues.append("EMPTY_ALPHA")
                if coverage > 0.7:
                    issues.append("BROAD_MASK")
                records.append(
                    {
                        "pack_id": pack_id,
                        "source_path": str(source),
                        "output_path": str(out_path),
                        "bbox": bbox,
                        "nonzero_alpha": nonzero,
                        "alpha_coverage": round(coverage, 8),
                        "label": item.get("label") if isinstance(item, dict) else None,
                        "score": item.get("score") if isinstance(item, dict) else None,
                        "issues": issues,
                        "quality_status": "REVISE_MASK" if issues else "CANDIDATE",
                        "is_actual_hf_inference": True,
                    }
                )
        sheet = exp / "reports" / f"{slug}_contact_sheet.png"
        build_sheet(records, sheet, f"{resolved_model_id} probe")
        issue_count = sum(len(rec["issues"]) for rec in records)
        report = {
            "schema_version": 1,
            "experiment_id": exp.name,
            "generated_at": now(),
            "status": "PASS" if records and not issue_count else ("RUNTIME_PASS_REVISE_MASK" if records else "FAIL_NO_RECORDS"),
            "model_id": resolved_model_id,
            "model_slug": slug,
            "task": args.task,
            "device": device,
            "actual_hf_inference_count": len(records),
            "issue_count": issue_count,
            "records": records,
            "contact_sheet": str(sheet),
        }
        write_json(report_path, report)
        print(json.dumps({"ok": True, "status": report["status"], "records": len(records), "report": str(report_path)}, indent=2))
        return 0 if records else 1
    except Exception as exc:
        report = {
            "schema_version": 1,
            "experiment_id": exp.name,
            "generated_at": now(),
            "status": "BLOCKED_MODEL_PROBE",
            "model_id": resolved_model_id,
            "model_slug": slug,
            "task": args.task,
            "packs": packs,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        write_json(report_path, report)
        print(json.dumps({"ok": False, "status": report["status"], "error": str(exc), "report": str(report_path)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

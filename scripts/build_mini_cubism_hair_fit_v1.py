#!/usr/bin/env python3
"""Fit the BiRefNet_HR hair pack to the clean base mannequin for Hair+Face Motion v1."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = ROOT / "experiments/mini-cubism-hair-face-motion-v1-001"
BASE_SOURCE = ROOT / "experiments/mini-cubism-pack-splitter-v0-001/base_mannequin/canonical_base.png"
HAIR_SOURCE = ROOT / "experiments/mini-cubism-pack-splitter-v0-001/hf_actual/birefnet_hr/hair_pack/hair_pack_birefnet_hr.png"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def font(size: int) -> ImageFont.ImageFont:
    for candidate in ["/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"]:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def bbox_alpha(image: Image.Image) -> tuple[list[int], int, float]:
    alpha = image.convert("RGBA").getchannel("A")
    bbox = alpha.getbbox()
    nonzero = sum(alpha.histogram()[1:])
    if not bbox:
        return [0, 0, 0, 0], 0, 0.0
    left, top, right, bottom = bbox
    return [left, top, right - left, bottom - top], nonzero, round(nonzero / (image.width * image.height), 8)


def composite_preview(base: Image.Image, original_hair: Image.Image, fitted_hair: Image.Image, out: Path, report: dict[str, Any]) -> None:
    cell_w, cell_h = 420, 560
    header_h = 70
    sheet = Image.new("RGB", (cell_w * 3, header_h + cell_h), "#f4f0e8")
    draw = ImageDraw.Draw(sheet)
    draw.text((18, 14), "Mini Cubism Hair Fit v1", fill="#202124", font=font(24))
    labels = ["base", "original oversized", "fitted overlay"]
    images = []
    base_rgb = Image.new("RGB", base.size, "#f8f6f0")
    base_rgb.paste(base.convert("RGB"), mask=base.getchannel("A"))
    images.append(base_rgb)
    original_overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    original_overlay.alpha_composite(base)
    original_overlay.alpha_composite(original_hair)
    original_rgb = Image.new("RGB", base.size, "#f8f6f0")
    original_rgb.paste(original_overlay.convert("RGB"), mask=original_overlay.getchannel("A"))
    images.append(original_rgb)
    fitted_overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    fitted_overlay.alpha_composite(base)
    fitted_overlay.alpha_composite(fitted_hair)
    fitted_rgb = Image.new("RGB", base.size, "#f8f6f0")
    fitted_rgb.paste(fitted_overlay.convert("RGB"), mask=fitted_overlay.getchannel("A"))
    images.append(fitted_rgb)
    small = font(13)
    for index, image in enumerate(images):
        x = index * cell_w
        thumb = image.copy()
        thumb.thumbnail((cell_w - 24, cell_h - 64), Image.Resampling.LANCZOS)
        sheet.paste(thumb, (x + (cell_w - thumb.width) // 2, header_h + 12))
        draw.text((x + 16, header_h + cell_h - 42), labels[index], fill="#202124", font=small)
    draw.text((18, 45), f"scale={report['fit_scale']} fitted_bbox={report['fitted_bbox']}", fill="#5f6368", font=small)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", default=str(DEFAULT_EXPERIMENT))
    parser.add_argument("--base", default=str(BASE_SOURCE))
    parser.add_argument("--hair", default=str(HAIR_SOURCE))
    parser.add_argument("--target-height", type=int, default=1050)
    parser.add_argument("--target-top", type=int, default=18)
    parser.add_argument("--target-center-x", type=int, default=1024)
    args = parser.parse_args()

    exp = Path(args.experiment).resolve()
    base_path = Path(args.base).resolve()
    hair_path = Path(args.hair).resolve()
    if not base_path.exists():
        raise SystemExit(f"missing base: {base_path}")
    if not hair_path.exists():
        raise SystemExit(f"missing hair: {hair_path}")
    base = Image.open(base_path).convert("RGBA")
    hair = Image.open(hair_path).convert("RGBA")
    base_bbox, _, _ = bbox_alpha(base)
    hair_bbox, _, _ = bbox_alpha(hair)
    if hair_bbox[2] <= 0 or hair_bbox[3] <= 0:
        raise SystemExit("hair alpha is empty")
    crop = hair.crop((hair_bbox[0], hair_bbox[1], hair_bbox[0] + hair_bbox[2], hair_bbox[1] + hair_bbox[3]))
    scale = args.target_height / hair_bbox[3]
    target_width = int(round(hair_bbox[2] * scale))
    resized = crop.resize((target_width, args.target_height), Image.Resampling.LANCZOS)
    left = int(round(args.target_center_x - target_width / 2))
    top = args.target_top
    fitted = Image.new("RGBA", base.size, (0, 0, 0, 0))
    fitted.alpha_composite(resized, (left, top))
    fitted_bbox, nonzero, coverage = bbox_alpha(fitted)
    out_path = exp / "hair_fit_v1" / "hair_fit_birefnet_hr.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fitted.save(out_path)
    report: dict[str, Any] = {
        "schema_version": 1,
        "experiment_id": exp.name,
        "generated_at": now(),
        "status": "PASS" if nonzero > 0 else "FAIL_EMPTY_FIT",
        "base_source": str(base_path),
        "hair_source": str(hair_path),
        "base_bbox": base_bbox,
        "source_hair_bbox": hair_bbox,
        "target_height": args.target_height,
        "target_top": args.target_top,
        "target_center_x": args.target_center_x,
        "fit_scale": round(scale, 4),
        "fitted_bbox": fitted_bbox,
        "fitted_alpha_coverage": coverage,
        "output_path": str(out_path),
        "contact_sheet": str(exp / "hair_fit_v1" / "reports" / "hair_fit_contact_sheet.png"),
    }
    write_json(exp / "hair_fit_v1" / "hair_fit_report.json", report)
    write_json(exp / "hair_fit_v1" / "reports" / "hair_fit_report.json", report)
    composite_preview(base, hair, fitted, Path(report["contact_sheet"]), report)
    print(json.dumps({"ok": report["status"] == "PASS", "status": report["status"], "scale": report["fit_scale"], "bbox": fitted_bbox}, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

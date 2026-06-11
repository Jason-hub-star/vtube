#!/usr/bin/env python3
"""Build local hair split parts for Mini Cubism Hair+Face Motion v1."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = ROOT / "experiments/mini-cubism-hair-face-motion-v1-001"
SOURCE_HAIR = ROOT / "experiments/mini-cubism-pack-splitter-v0-001/hf_actual/birefnet_hr/hair_pack/hair_pack_birefnet_hr.png"


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


def rect_from_fractions(bbox: list[int], x0: float, y0: float, x1: float, y1: float) -> list[int]:
    x, y, w, h = bbox
    left = int(round(x + w * x0))
    top = int(round(y + h * y0))
    right = int(round(x + w * x1))
    bottom = int(round(y + h * y1))
    return [left, top, max(1, right - left), max(1, bottom - top)]


def feathered_rect_mask(size: tuple[int, int], rect: list[int], feather: int = 26) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    x, y, w, h = rect
    draw.rectangle([x, y, x + w, y + h], fill=255)
    if feather > 0:
        # A light blur-like feather without depending on filters that alter bbox too much.
        for step in range(1, 4):
            inset = int(feather * step / 4)
            alpha = max(0, 255 - step * 55)
            draw.rectangle([x - inset, y - inset, x + w + inset, y + h + inset], outline=alpha, width=max(1, feather // 5))
    return mask


def apply_region(source: Image.Image, rect: list[int]) -> Image.Image:
    rgba = source.convert("RGBA")
    alpha = np.array(rgba.getchannel("A"), dtype=np.uint8)
    region = np.array(feathered_rect_mask(rgba.size, rect), dtype=np.uint8)
    out_alpha = ((alpha.astype(np.uint16) * region.astype(np.uint16)) // 255).astype(np.uint8)
    out = rgba.copy()
    out.putalpha(Image.fromarray(out_alpha, mode="L"))
    return out


def part_specs(hair_bbox: list[int]) -> list[dict[str, Any]]:
    return [
        {"id": "back_hair_base", "folder": "Hair Back", "role": "back", "rect": rect_from_fractions(hair_bbox, 0.16, 0.00, 0.84, 0.34)},
        {"id": "back_hair_L", "folder": "Hair Back", "role": "back", "rect": rect_from_fractions(hair_bbox, 0.54, 0.20, 1.00, 0.78)},
        {"id": "back_hair_C", "folder": "Hair Back", "role": "back", "rect": rect_from_fractions(hair_bbox, 0.36, 0.17, 0.64, 0.82)},
        {"id": "back_hair_R", "folder": "Hair Back", "role": "back", "rect": rect_from_fractions(hair_bbox, 0.00, 0.20, 0.46, 0.78)},
        {"id": "back_hair_tip_L", "folder": "Hair Tips", "role": "tip", "rect": rect_from_fractions(hair_bbox, 0.58, 0.70, 1.00, 1.00)},
        {"id": "back_hair_tip_C", "folder": "Hair Tips", "role": "tip", "rect": rect_from_fractions(hair_bbox, 0.34, 0.68, 0.66, 1.00)},
        {"id": "back_hair_tip_R", "folder": "Hair Tips", "role": "tip", "rect": rect_from_fractions(hair_bbox, 0.00, 0.70, 0.42, 1.00)},
        {"id": "side_hair_L", "folder": "Hair Side", "role": "side", "rect": rect_from_fractions(hair_bbox, 0.66, 0.28, 0.98, 0.88)},
        {"id": "side_hair_R", "folder": "Hair Side", "role": "side", "rect": rect_from_fractions(hair_bbox, 0.02, 0.28, 0.34, 0.88)},
        {"id": "side_lock_L", "folder": "Hair Front", "role": "front_side", "rect": rect_from_fractions(hair_bbox, 0.58, 0.12, 0.82, 0.52)},
        {"id": "side_lock_R", "folder": "Hair Front", "role": "front_side", "rect": rect_from_fractions(hair_bbox, 0.18, 0.12, 0.42, 0.52)},
        {"id": "front_bang_L", "folder": "Hair Front", "role": "front_bang", "rect": rect_from_fractions(hair_bbox, 0.58, 0.02, 0.72, 0.34)},
        {"id": "front_bang_CL", "folder": "Hair Front", "role": "front_bang", "rect": rect_from_fractions(hair_bbox, 0.49, 0.02, 0.60, 0.39)},
        {"id": "front_bang_C", "folder": "Hair Front", "role": "front_bang", "rect": rect_from_fractions(hair_bbox, 0.43, 0.02, 0.55, 0.43)},
        {"id": "front_bang_CR", "folder": "Hair Front", "role": "front_bang", "rect": rect_from_fractions(hair_bbox, 0.38, 0.02, 0.50, 0.39)},
        {"id": "front_bang_R", "folder": "Hair Front", "role": "front_bang", "rect": rect_from_fractions(hair_bbox, 0.28, 0.02, 0.42, 0.34)},
    ]


def build_sheet(records: list[dict[str, Any]], out: Path) -> None:
    cols = 4
    cell_w, cell_h = 300, 330
    header_h = 70
    rows = (len(records) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, header_h + rows * cell_h), "#f4f0e8")
    draw = ImageDraw.Draw(sheet)
    draw.text((18, 14), "Mini Cubism Hair Split v1", fill="#202124", font=font(24))
    small = font(12)
    for index, record in enumerate(records):
        x = (index % cols) * cell_w
        y = header_h + (index // cols) * cell_h
        draw.rectangle([x + 8, y + 8, x + cell_w - 8, y + cell_h - 8], fill="#fffaf2", outline="#d6cec5")
        image = Image.open(record["output_path"]).convert("RGBA")
        bbox = image.getchannel("A").getbbox()
        crop = image.crop(bbox) if bbox else Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        bg = Image.new("RGB", crop.size, "#f8f6f0")
        bg.paste(crop.convert("RGB"), mask=crop.getchannel("A"))
        bg.thumbnail((cell_w - 36, cell_h - 78), Image.Resampling.LANCZOS)
        sheet.paste(bg, (x + (cell_w - bg.width) // 2, y + 16))
        draw.text((x + 14, y + cell_h - 52), record["part_id"], fill="#202124", font=small)
        draw.text((x + 14, y + cell_h - 31), f"bbox={record['bbox']} alpha={record['alpha_coverage']}", fill="#5f6368", font=small)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", default=str(DEFAULT_EXPERIMENT))
    parser.add_argument("--source-hair", default=str(SOURCE_HAIR))
    args = parser.parse_args()

    exp = Path(args.experiment).resolve()
    source_hair = Path(args.source_hair).resolve()
    if not source_hair.exists():
        raise SystemExit(f"missing BiRefNet_HR hair source: {source_hair}")
    source = Image.open(source_hair).convert("RGBA")
    hair_bbox, nonzero, coverage = bbox_alpha(source)
    if nonzero <= 0:
        raise SystemExit("hair source has empty alpha")

    parts_dir = exp / "hair_split_v1" / "parts"
    records: list[dict[str, Any]] = []
    for spec in part_specs(hair_bbox):
        out = apply_region(source, spec["rect"])
        bbox, count, alpha_coverage = bbox_alpha(out)
        if count <= 0:
            raise SystemExit(f"empty split result: {spec['id']}")
        out_path = parts_dir / f"{spec['id']}.png"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out.save(out_path)
        records.append(
            {
                "part_id": spec["id"],
                "folder": spec["folder"],
                "role": spec["role"],
                "source_path": str(source_hair),
                "output_path": str(out_path),
                "split_rect": spec["rect"],
                "bbox": bbox,
                "nonzero_alpha": count,
                "alpha_coverage": alpha_coverage,
                "is_physics_target": True,
            }
        )

    report = {
        "schema_version": 1,
        "experiment_id": exp.name,
        "generated_at": now(),
        "status": "PASS" if len(records) >= 14 else "FAIL_TOO_FEW_PARTS",
        "source_hair": str(source_hair),
        "source_bbox": hair_bbox,
        "source_alpha_coverage": coverage,
        "part_count": len(records),
        "physics_target_count": len([item for item in records if item["is_physics_target"]]),
        "records": records,
        "contact_sheet": str(exp / "hair_split_v1" / "reports" / "hair_split_contact_sheet.png"),
    }
    write_json(exp / "hair_split_v1" / "hair_split_manifest.json", report)
    write_json(exp / "hair_split_v1" / "reports" / "hair_split_report.json", report)
    build_sheet(records, Path(report["contact_sheet"]))
    print(json.dumps({"ok": report["status"] == "PASS", "status": report["status"], "parts": len(records)}, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

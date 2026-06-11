#!/usr/bin/env python3
"""Normalize generated Character 002 eye sheet into v19 full-canvas eye assets."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
DEFAULT_INPUT = EXP / "generated_eye_v19/raw_outputs/eye_asset_sheet_chromakey.png"
DEFAULT_OUT = EXP / "generated_eye_v19"
CANVAS = (2048, 2048)

TARGETS = {
    "eye_L_white": {"cell": (0, 0), "center": (880.5, 669.5), "fit": (191, 101)},
    "eye_R_white": {"cell": (1, 0), "center": (1170.5, 669.0), "fit": (191, 100)},
    "eye_L_iris": {"cell": (0, 1), "center": (885.0, 666.5), "fit": (84, 84)},
    "eye_R_iris": {"cell": (1, 1), "center": (1166.5, 666.0), "fit": (84, 84)},
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def remove_green(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    pix = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = pix[x, y]
            # The generated sheet background is intentionally flat #00ff00. Keep a soft margin
            # for antialiasing while preserving non-green eye colors.
            green_score = g - max(r, b)
            if g > 150 and green_score > 70:
                pix[x, y] = (r, g, b, 0)
            elif g > 110 and green_score > 35:
                alpha = max(0, min(255, int(a * (1 - green_score / 120))))
                pix[x, y] = (r, g, b, alpha)
    return rgba


def crop_cell(sheet: Image.Image, col: int, row: int) -> Image.Image:
    w, h = sheet.size
    box = (int(col * w / 2), int(row * h / 2), int((col + 1) * w / 2), int((row + 1) * h / 2))
    cell = sheet.crop(box).convert("RGBA")
    bbox = cell.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError(f"empty generated cell {col},{row}")
    # Trim with a little padding so stray edge pixels do not define scaling.
    pad = 8
    trim = (
        max(0, bbox[0] - pad),
        max(0, bbox[1] - pad),
        min(cell.width, bbox[2] + pad),
        min(cell.height, bbox[3] + pad),
    )
    return cell.crop(trim)


def fit_to_canvas(asset: Image.Image, center: tuple[float, float], fit: tuple[int, int]) -> tuple[Image.Image, dict[str, Any]]:
    bbox = asset.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("empty asset")
    crop = asset.crop(bbox)
    scale = min(fit[0] / crop.width, fit[1] / crop.height)
    new_size = (max(1, round(crop.width * scale)), max(1, round(crop.height * scale)))
    resized = crop.resize(new_size, Image.Resampling.LANCZOS)
    out = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    paste = (round(center[0] - resized.width / 2), round(center[1] - resized.height / 2))
    out.alpha_composite(resized, paste)
    out_bbox = out.getchannel("A").getbbox()
    if out_bbox is None:
        raise ValueError("normalized asset became empty")
    alpha = out.getchannel("A")
    nonzero = int(sum(alpha.histogram()[1:]))
    metrics = {
        "source_bbox": list(bbox),
        "scale": scale,
        "paste_xy": list(paste),
        "bbox_xywh": [out_bbox[0], out_bbox[1], out_bbox[2] - out_bbox[0], out_bbox[3] - out_bbox[1]],
        "alpha_nonzero": nonzero,
        "alpha_coverage": round(nonzero / (CANVAS[0] * CANVAS[1]), 8),
    }
    return out, metrics


def font(size: int) -> ImageFont.ImageFont:
    for candidate in ["/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"]:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def fit_preview(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    crop = image.getbbox()
    show = image.crop(crop) if crop else image
    bg = Image.new("RGB", size, "#202124")
    rgb = Image.new("RGB", show.size, "#202124")
    rgb.paste(show.convert("RGBA"), mask=show.convert("RGBA").getchannel("A"))
    rgb.thumbnail((size[0] - 12, size[1] - 36), Image.Resampling.LANCZOS)
    bg.paste(rgb, ((size[0] - rgb.width) // 2, 30 + (size[1] - 36 - rgb.height) // 2))
    return bg


def build_contact_sheet(raw: Image.Image, normalized: dict[str, Image.Image], out: Path) -> None:
    cell_w, cell_h = 340, 270
    sheet = Image.new("RGB", (cell_w * 4, cell_h * 2 + 80), "#151719")
    draw = ImageDraw.Draw(sheet)
    draw.text((24, 18), "Character 002 v19 Generated Eye Asset Packet", fill="#f1f3f4", font=font(24))
    draw.text((24, 48), "Top: raw generated sheet quadrants. Bottom: normalized 2048 full-canvas assets fitted to v15 eye anchors.", fill="#b8c0c8", font=font(14))
    raw_rgba = remove_green(raw)
    for idx, (part_id, cfg) in enumerate(TARGETS.items()):
        col, row = cfg["cell"]
        raw_cell = crop_cell(raw_rgba, col, row)
        x = idx * cell_w
        draw.text((x + 12, 86), f"raw {part_id}", fill="#f1f3f4", font=font(14))
        sheet.paste(fit_preview(raw_cell, (cell_w, cell_h)), (x, 100))
        draw.text((x + 12, 86 + cell_h), f"normalized {part_id}", fill="#f1f3f4", font=font(14))
        sheet.paste(fit_preview(normalized[part_id], (cell_w, cell_h)), (x, 100 + cell_h))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    out_root = Path(args.out).resolve()
    layers = out_root / "normalized_layers"
    reports = out_root / "reports"
    layers.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    raw = Image.open(input_path).convert("RGBA")
    keyed = remove_green(raw)
    normalized: dict[str, Image.Image] = {}
    metrics: dict[str, Any] = {}
    for part_id, cfg in TARGETS.items():
        cell = crop_cell(keyed, *cfg["cell"])
        canvas, item_metrics = fit_to_canvas(cell, cfg["center"], cfg["fit"])
        canvas.save(layers / f"{part_id}.png")
        normalized[part_id] = canvas
        metrics[part_id] = item_metrics

    contact_sheet = reports / "generated_eye_v19_contact_sheet.png"
    build_contact_sheet(raw, normalized, contact_sheet)
    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "GENERATED_EYE_V19_NORMALIZED",
        "input": rel(input_path),
        "normalized_layers": {part_id: rel(layers / f"{part_id}.png") for part_id in TARGETS},
        "contact_sheet": rel(contact_sheet),
        "metrics": metrics,
        "policy": {
            "fixed_eye_white": ["eye_L_white", "eye_R_white"],
            "moving_coherent_eye_detail": ["eye_L_iris", "eye_R_iris"],
            "pupil_highlight_are_baked_into_iris_layer": True,
        },
    }
    report_path = reports / "generated_eye_v19_report.json"
    write_json(report_path, report)
    print(json.dumps({"ok": True, "report": str(report_path), "contact_sheet": str(contact_sheet)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build separated eye and mouth keypose layers for Mini Cubism Hair+Face Motion v1."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = ROOT / "experiments/mini-cubism-hair-face-motion-v1-001"
CANVAS = [2048, 2048]


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


def blank() -> Image.Image:
    return Image.new("RGBA", tuple(CANVAS), (0, 0, 0, 0))


def draw_face_cover() -> Image.Image:
    image = blank()
    draw = ImageDraw.Draw(image)
    skin = (248, 213, 194, 245)
    blush = (244, 176, 178, 70)
    # Cover the original base eyes and mouth so new keypose layers do not double-render.
    draw.rounded_rectangle([790, 145, 1258, 365], radius=86, fill=skin)
    draw.ellipse([785, 235, 940, 330], fill=blush)
    draw.ellipse([1110, 235, 1265, 330], fill=blush)
    draw.arc([980, 252, 1038, 330], 72, 144, fill=(191, 117, 103, 120), width=3)
    return image


def draw_eye(side: str, state: str) -> Image.Image:
    image = blank()
    draw = ImageDraw.Draw(image)
    cx = 920 if side == "L" else 1130
    cy = 225
    if state == "open":
        draw.ellipse([cx - 72, cy - 39, cx + 72, cy + 39], fill=(252, 252, 250, 245), outline=(67, 41, 55, 235), width=5)
        draw.ellipse([cx - 30, cy - 34, cx + 30, cy + 34], fill=(83, 128, 177, 250))
        draw.ellipse([cx - 16, cy - 23, cx + 16, cy + 23], fill=(18, 28, 52, 255))
        draw.ellipse([cx + 5, cy - 25, cx + 25, cy - 5], fill=(255, 255, 255, 235))
        draw.arc([cx - 80, cy - 48, cx + 80, cy + 36], 195, 342, fill=(42, 27, 43, 255), width=8)
        draw.arc([cx - 66, cy - 26, cx + 66, cy + 50], 20, 160, fill=(42, 27, 43, 205), width=4)
    elif state == "half":
        draw.ellipse([cx - 70, cy - 27, cx + 70, cy + 27], fill=(252, 252, 250, 230), outline=(67, 41, 55, 220), width=4)
        draw.ellipse([cx - 26, cy - 20, cx + 26, cy + 23], fill=(83, 128, 177, 230))
        draw.ellipse([cx - 13, cy - 12, cx + 13, cy + 18], fill=(18, 28, 52, 245))
        draw.rectangle([cx - 75, cy - 42, cx + 75, cy - 7], fill=(248, 213, 194, 245))
        draw.arc([cx - 80, cy - 42, cx + 80, cy + 24], 195, 342, fill=(42, 27, 43, 255), width=8)
        draw.arc([cx - 68, cy - 20, cx + 68, cy + 38], 20, 160, fill=(42, 27, 43, 185), width=3)
    else:
        draw.arc([cx - 76, cy - 14, cx + 76, cy + 42], 190, 340, fill=(54, 31, 47, 255), width=8)
        draw.arc([cx - 54, cy - 2, cx + 54, cy + 34], 190, 340, fill=(94, 54, 72, 180), width=3)
    return image


def draw_mouth(state: str) -> Image.Image:
    image = blank()
    draw = ImageDraw.Draw(image)
    cx = 1024
    cy = 330
    lip = (126, 55, 69, 245)
    inner = (50, 22, 31, 255)
    if state == "closed":
        draw.arc([cx - 58, cy - 24, cx + 58, cy + 30], 15, 165, fill=lip, width=7)
    elif state == "half":
        draw.ellipse([cx - 56, cy - 18, cx + 56, cy + 32], fill=lip)
        draw.ellipse([cx - 45, cy - 12, cx + 45, cy + 26], fill=inner)
        draw.arc([cx - 45, cy - 6, cx + 45, cy + 26], 20, 160, fill=(232, 132, 134, 180), width=4)
    else:
        draw.ellipse([cx - 62, cy - 26, cx + 62, cy + 50], fill=lip)
        draw.ellipse([cx - 49, cy - 16, cx + 49, cy + 42], fill=inner)
        draw.rounded_rectangle([cx - 25, cy - 12, cx + 25, cy + 2], radius=4, fill=(255, 230, 220, 225))
        draw.ellipse([cx - 31, cy + 10, cx + 31, cy + 40], fill=(207, 89, 105, 220))
    return image


def save_part(image: Image.Image, out_path: Path, part_id: str, role: str, parameter_id: str | None) -> dict[str, Any]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)
    bbox, nonzero, coverage = bbox_alpha(image)
    if nonzero <= 0:
        raise SystemExit(f"empty keypose layer: {part_id}")
    return {
        "part_id": part_id,
        "role": role,
        "parameter_id": parameter_id,
        "output_path": str(out_path),
        "bbox": bbox,
        "nonzero_alpha": nonzero,
        "alpha_coverage": coverage,
    }


def build_sheet(records: list[dict[str, Any]], out: Path) -> None:
    cols = 5
    cell_w, cell_h = 250, 250
    header_h = 68
    rows = (len(records) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, header_h + rows * cell_h), "#f4f0e8")
    draw = ImageDraw.Draw(sheet)
    draw.text((18, 14), "Mini Cubism Face Keypose v1", fill="#202124", font=font(24))
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
        bg.thumbnail((cell_w - 32, cell_h - 66), Image.Resampling.LANCZOS)
        sheet.paste(bg, (x + (cell_w - bg.width) // 2, y + 18))
        draw.text((x + 14, y + cell_h - 38), record["part_id"], fill="#202124", font=small)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", default=str(DEFAULT_EXPERIMENT))
    args = parser.parse_args()

    exp = Path(args.experiment).resolve()
    parts_dir = exp / "face_keypose_v1" / "parts"
    records: list[dict[str, Any]] = []
    records.append(save_part(draw_face_cover(), parts_dir / "face_cover.png", "face_cover", "face_cover", None))
    for side in ["L", "R"]:
        parameter_id = f"ParamEye{side}Open"
        for state in ["open", "half", "closed"]:
            part_id = f"eye_{state}_{side}"
            records.append(save_part(draw_eye(side, state), parts_dir / f"{part_id}.png", part_id, f"eye_{state}", parameter_id))
    for state in ["closed", "half", "open"]:
        part_id = f"mouth_{state}"
        records.append(save_part(draw_mouth(state), parts_dir / f"{part_id}.png", part_id, f"mouth_{state}", "ParamMouthOpenY"))

    report = {
        "schema_version": 1,
        "experiment_id": exp.name,
        "generated_at": now(),
        "status": "PASS",
        "canvas_size": CANVAS,
        "source_policy": "generated_separate_keypose_layers_not_crowded_pack",
        "records": records,
        "eye_visibility_groups": {
            "states": {
                "0": ["eye_closed_L", "eye_closed_R"],
                "0.5": ["eye_half_L", "eye_half_R"],
                "1": ["eye_open_L", "eye_open_R"],
            },
            "closed_hidden_parts": ["eye_open_L", "eye_half_L", "eye_open_R", "eye_half_R"],
        },
        "mouth_visibility_groups": {
            "states": {
                "0": ["mouth_closed"],
                "0.5": ["mouth_half"],
                "1": ["mouth_open"],
            }
        },
        "contact_sheet": str(exp / "face_keypose_v1" / "reports" / "face_keypose_contact_sheet.png"),
    }
    write_json(exp / "face_keypose_v1" / "face_keypose_manifest.json", report)
    write_json(exp / "face_keypose_v1" / "reports" / "face_keypose_report.json", report)
    build_sheet(records, Path(report["contact_sheet"]))
    print(json.dumps({"ok": True, "status": report["status"], "records": len(records)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

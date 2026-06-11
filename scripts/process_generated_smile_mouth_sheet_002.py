#!/usr/bin/env python3
"""Process generated chroma-key smile mouth sheet into Character 002 full-canvas mouth layers."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
DEFAULT_INPUT = EXP / "generated_mouth_v10/raw_outputs/smile_mouth_keypose_sheet_chromakey.png"
DEFAULT_PARTS = EXP / "model_edit_v8_existing_mouth_tuned_preview/mini_cubism_diagnostic_project/parts"
DEFAULT_OUT = EXP / "generated_mouth_v10"
CANVAS_SIZE = (2048, 2048)
PART_IDS = [
    "mouth_smile_closed_gen",
    "mouth_smile_small_open_gen",
    "mouth_smile_mid_teeth_gen",
    "mouth_smile_wide_teeth_tongue_gen",
]
TARGET_WIDTHS = [168, 184, 208, 232]
TARGET_CENTER = (1035, 892)
DEFAULT_TITLE = "Character 002 Generated Smile Mouth"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def font(size: int) -> ImageFont.ImageFont:
    for candidate in ["/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"]:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def chroma_to_alpha(image: Image.Image) -> Image.Image:
    rgb = np.asarray(image.convert("RGB")).astype(np.int32)
    key = np.array([0, 255, 0], dtype=np.int32)
    distance = np.sqrt(np.sum((rgb - key) ** 2, axis=2))
    alpha = np.clip((distance - 24) / (105 - 24), 0, 1) * 255
    green_dominance = rgb[:, :, 1] - np.maximum(rgb[:, :, 0], rgb[:, :, 2])
    green_background = (rgb[:, :, 1] > 150) & (green_dominance > 80)
    alpha = np.where(green_background, 0, alpha)
    alpha_u8 = alpha.astype(np.uint8)
    rgb_out = rgb.copy()
    edge = alpha_u8 > 0
    green_cap = np.maximum(rgb_out[:, :, 0], rgb_out[:, :, 2]) + 8
    rgb_out[:, :, 1] = np.where(edge, np.minimum(rgb_out[:, :, 1], green_cap), rgb_out[:, :, 1])
    rgb_out = np.clip(rgb_out, 0, 255).astype(np.uint8)
    rgba = np.dstack([rgb_out, alpha_u8])
    return Image.fromarray(rgba, "RGBA")


def component_x_runs(alpha: Image.Image) -> list[tuple[int, int]]:
    mask = np.asarray(alpha) > 32
    col_has = mask.any(axis=0)
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for index, has_value in enumerate(col_has):
        if has_value and start is None:
            start = index
        elif not has_value and start is not None:
            if index - start > 20:
                runs.append((start, index))
            start = None
    if start is not None and len(col_has) - start > 20:
        runs.append((start, len(col_has)))
    return runs


def crop_components(sheet_rgba: Image.Image) -> list[Image.Image]:
    alpha = sheet_rgba.getchannel("A")
    runs = component_x_runs(alpha)
    if len(runs) != 4:
        raise RuntimeError(f"expected 4 mouth components, found {len(runs)} x-runs: {runs}")
    crops = []
    alpha_np = np.asarray(alpha)
    for left, right in runs:
        region = alpha_np[:, left:right] > 32
        ys, xs = np.where(region)
        if len(xs) == 0:
            raise RuntimeError(f"empty component run: {(left, right)}")
        box = (
            max(0, left + int(xs.min()) - 8),
            max(0, int(ys.min()) - 8),
            min(sheet_rgba.width, left + int(xs.max()) + 9),
            min(sheet_rgba.height, int(ys.max()) + 9),
        )
        crops.append(sheet_rgba.crop(box))
    return crops


def normalize_component(component: Image.Image, target_width: int, target_center: tuple[int, int]) -> Image.Image:
    bbox = component.getchannel("A").getbbox()
    if not bbox:
        raise RuntimeError("component has empty alpha")
    component = component.crop(bbox)
    scale = target_width / component.width
    target_height = max(1, int(round(component.height * scale)))
    resized = component.resize((target_width, target_height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    x = int(round(target_center[0] - target_width / 2))
    y = int(round(target_center[1] - target_height / 2))
    canvas.alpha_composite(resized, (x, y))
    return canvas


def neutral_face(parts_dir: Path) -> Image.Image:
    face = Image.open(parts_dir / "face_base_clean.png").convert("RGBA")
    for part_id in ["eye_L_open", "eye_R_open"]:
        path = parts_dir / f"{part_id}.png"
        if path.exists():
            face.alpha_composite(Image.open(path).convert("RGBA"))
    return face


def fit_image(image: Image.Image, size: tuple[int, int], bg: str = "#202124") -> Image.Image:
    rgba = image.convert("RGBA")
    rgba.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, bg)
    canvas.paste(rgba.convert("RGB"), ((size[0] - rgba.width) // 2, (size[1] - rgba.height) // 2), rgba.getchannel("A"))
    return canvas


def review_crop(image: Image.Image, bbox: tuple[int, int, int, int] | None) -> Image.Image:
    if bbox is None:
        bbox = (900, 820, 1160, 980)
    return image.crop(
        (
            max(0, bbox[0] - 150),
            max(0, bbox[1] - 120),
            min(CANVAS_SIZE[0], bbox[2] + 150),
            min(CANVAS_SIZE[1], bbox[3] + 120),
        )
    )


def build_contact_sheet(face: Image.Image, rows: list[dict[str, Any]], out_path: Path, title: str) -> None:
    cell_w = 390
    cell_h = 650
    margin = 28
    header_h = 72
    sheet = Image.new("RGB", (margin * 2 + cell_w * len(rows), margin * 2 + header_h + cell_h), "#151719")
    draw = ImageDraw.Draw(sheet)
    title_font = font(24)
    label_font = font(17)
    small_font = font(13)
    draw.text((margin, margin), title, fill="#f1f3f4", font=title_font)
    draw.text((margin, margin + 34), "New generated mouth keyposes normalized to 2048 full-canvas RGBA.", fill="#b8c0c8", font=small_font)
    for index, row in enumerate(rows):
        x = margin + index * cell_w
        y = margin + header_h
        layer = Image.open(row["path"]).convert("RGBA")
        composite = face.copy()
        composite.alpha_composite(layer)
        bbox = tuple(row["bbox"]) if row["bbox"] else None
        full = fit_image(composite, (cell_w - 24, 300), bg="#f0eee7")
        close = fit_image(review_crop(composite, bbox), (cell_w - 24, 138), bg="#f0eee7")
        isolated = fit_image(review_crop(layer, bbox), (cell_w - 24, 116))
        draw.rounded_rectangle((x + 6, y + 6, x + cell_w - 6, y + cell_h - 6), radius=8, fill="#202124", outline="#3a3f45")
        draw.text((x + 18, y + 18), row["id"], fill="#f1f3f4", font=label_font)
        draw.text((x + 18, y + 42), f"bbox {row['bbox']}", fill="#b8c0c8", font=small_font)
        sheet.paste(full, (x + 12, y + 70))
        draw.text((x + 18, y + 376), "face close-up", fill="#b8c0c8", font=small_font)
        sheet.paste(close, (x + 12, y + 400))
        draw.text((x + 18, y + 546), "isolated layer crop", fill="#b8c0c8", font=small_font)
        sheet.paste(isolated, (x + 12, y + 570))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--parts-dir", default=str(DEFAULT_PARTS))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--target-widths", default=",".join(str(value) for value in TARGET_WIDTHS))
    parser.add_argument("--title", default=f"{DEFAULT_TITLE} v10")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    parts_dir = Path(args.parts_dir).resolve()
    out_dir = Path(args.out).resolve()
    target_widths = [int(value.strip()) for value in args.target_widths.split(",") if value.strip()]
    if len(target_widths) != len(PART_IDS):
        raise RuntimeError(f"expected {len(PART_IDS)} target widths, got {target_widths}")
    layers_dir = out_dir / "normalized_layers"
    reports_dir = out_dir / "reports"
    layers_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    chroma = Image.open(input_path).convert("RGB")
    rgba_sheet = chroma_to_alpha(chroma)
    rgba_sheet_path = reports_dir / "smile_mouth_keypose_sheet_alpha.png"
    rgba_sheet.save(rgba_sheet_path)
    components = crop_components(rgba_sheet)
    rows: list[dict[str, Any]] = []
    for part_id, component, target_width in zip(PART_IDS, components, target_widths):
        layer = normalize_component(component, target_width, TARGET_CENTER)
        path = layers_dir / f"{part_id}.png"
        layer.save(path)
        bbox = layer.getchannel("A").getbbox()
        rows.append(
            {
                "id": part_id,
                "path": str(path),
                "size": list(layer.size),
                "mode": layer.mode,
                "bbox": list(bbox) if bbox else None,
                "alpha_nonzero": int(sum(layer.getchannel("A").histogram()[1:])),
                "target_width": target_width,
            }
        )
    contact_sheet = reports_dir / "generated_smile_mouth_contact_sheet.png"
    build_contact_sheet(neutral_face(parts_dir), rows, contact_sheet, args.title)
    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "PASS_GENERATED_MOUTH_NORMALIZED_READY_FOR_VISUAL_QA",
        "source_image": str(input_path),
        "alpha_sheet": str(rgba_sheet_path),
        "layers_dir": str(layers_dir),
        "contact_sheet": str(contact_sheet),
        "mouth_layers": rows,
    }
    report_path = reports_dir / "generated_smile_mouth_normalize_report.json"
    write_json(report_path, report)
    print(json.dumps({"ok": True, "status": report["status"], "report": str(report_path), "contact_sheet": str(contact_sheet)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

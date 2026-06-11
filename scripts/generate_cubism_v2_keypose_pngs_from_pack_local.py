#!/usr/bin/env python3
"""Generate local clean-socket/keypose PNG candidates from the prepared input pack.

This is a deterministic pack-realization step. It creates real 2048 RGBA PNG
files for validation, but it is not a substitute for human visual QA or a
model-native inpaint pass.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
REQ_DIR = ROOT / "experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements"
DEFAULT_PACK = REQ_DIR / "imagen_input_pack_v1"
DEFAULT_OUT = REQ_DIR / "local_generated_keypose_v1"
MATERIAL_DIR = ROOT / "experiments/cubism-v2-new-character-001/material_pack_v0"
CURRENT_LAYER_DIR = MATERIAL_DIR / "production_layers_face_detail_rebuild_v1"


EXISTING_ASSET_FILES = {
    "eye_L_closed_lid": CURRENT_LAYER_DIR / "25_eye_L_closed_lid.png",
    "eye_R_closed_lid": CURRENT_LAYER_DIR / "33_eye_R_closed_lid.png",
    "mouth_inner": CURRENT_LAYER_DIR / "38_mouth_inner.png",
    "mouth_teeth": CURRENT_LAYER_DIR / "41_mouth_teeth.png",
    "mouth_tongue": CURRENT_LAYER_DIR / "42_mouth_tongue.png",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def paste_box(base: Image.Image, patch: Image.Image, bbox: list[int], mask: Image.Image | None = None) -> None:
    x, y, w, h = bbox
    base.paste(patch.resize((w, h), Image.Resampling.BICUBIC), (x, y), mask.resize((w, h), Image.Resampling.BICUBIC) if mask else None)


def bbox_center(bbox: list[int]) -> tuple[float, float]:
    x, y, w, h = bbox
    return x + w / 2, y + h / 2


def alpha_bbox(path: Path) -> list[int] | None:
    if not path.exists():
        return None
    alpha = Image.open(path).convert("RGBA").getchannel("A")
    box = alpha.getbbox()
    if not box:
        return None
    left, top, right, bottom = box
    return [left, top, right - left, bottom - top]


def padded(bbox: list[int], pad_x: int, pad_y: int, canvas: tuple[int, int] = (2048, 2048)) -> list[int]:
    x, y, w, h = bbox
    left = max(0, x - pad_x)
    top = max(0, y - pad_y)
    right = min(canvas[0], x + w + pad_x)
    bottom = min(canvas[1], y + h + pad_y)
    return [left, top, right - left, bottom - top]


def skin_color(source: Image.Image, bbox: list[int]) -> tuple[int, int, int, int]:
    x, y, w, h = bbox
    crop = source.crop((x, y, x + w, y + h)).convert("RGBA")
    arr = np.asarray(crop, dtype=np.uint8)
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3]
    # Prefer bright warm skin pixels and avoid dark eye/mouth line pixels.
    mask = (
        (alpha > 0)
        & (rgb[:, :, 0] > 185)
        & (rgb[:, :, 1] > 125)
        & (rgb[:, :, 2] > 110)
        & (rgb[:, :, 0] >= rgb[:, :, 2])
    )
    if int(mask.sum()) < 32:
        mask = (alpha > 0) & (rgb.mean(axis=2) > 150)
    if int(mask.sum()) < 32:
        return (245, 205, 191, 255)
    median = np.median(rgb[mask], axis=0).astype(np.uint8)
    return (int(median[0]), int(median[1]), int(median[2]), 255)


def soft_rect_mask(size: tuple[int, int], radius: int = 18, blur: float = 5.0) -> Image.Image:
    w, h = size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(blur))


def ellipse_mask(size: tuple[int, int], blur: float = 4.0) -> Image.Image:
    w, h = size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, w - 1, h - 1), fill=255)
    return mask.filter(ImageFilter.GaussianBlur(blur))


def make_skin_patch(source: Image.Image, bbox: list[int], alpha_scale: float = 1.0) -> Image.Image:
    x, y, w, h = bbox
    color = skin_color(source, padded(bbox, 44, 44))
    patch = Image.new("RGBA", (w, h), color)
    sample = source.crop((x, y, x + w, y + h)).convert("RGBA").filter(ImageFilter.GaussianBlur(18))
    patch = Image.blend(patch, sample, 0.18)
    mask = soft_rect_mask((w, h), radius=max(10, min(w, h) // 5), blur=5)
    if alpha_scale < 1:
        mask = mask.point(lambda value: int(value * alpha_scale))
    patch.putalpha(mask)
    return patch


def quadratic_points(points: tuple[tuple[float, float], tuple[float, float], tuple[float, float]], steps: int = 48) -> list[tuple[float, float]]:
    p0, p1, p2 = points
    result = []
    for index in range(steps + 1):
        t = index / steps
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1]
        result.append((x, y))
    return result


def draw_lid(canvas: Image.Image, bbox: list[int], openness: float, source: Image.Image) -> None:
    x, y, w, h = bbox
    color = skin_color(source, padded(bbox, 40, 36))
    line = (103, 55, 52, 215)
    shadow = (190, 117, 105, 120)
    cx, cy = bbox_center(bbox)
    top = y + h * (0.18 + 0.32 * (1.0 - openness))
    lower = y + h * (0.78 - 0.42 * (1.0 - openness))
    shape = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shape)
    if openness <= 0.05:
        curve = quadratic_points(((x + w * 0.08, cy), (cx, y + h * 0.78), (x + w * 0.92, cy)), 72)
        draw.line(curve, fill=line, width=max(4, int(h * 0.055)), joint="curve")
        draw.line([(px, py + h * 0.10) for px, py in curve], fill=shadow, width=max(2, int(h * 0.035)))
    else:
        upper = quadratic_points(((x + w * 0.08, top), (cx, y + h * 0.05), (x + w * 0.92, top)), 72)
        lower_curve = quadratic_points(((x + w * 0.12, lower), (cx, y + h * 0.86), (x + w * 0.88, lower)), 72)
        polygon = upper + list(reversed(lower_curve))
        fill_alpha = 170 if openness < 0.45 else 130
        draw.polygon(polygon, fill=(color[0], color[1], color[2], fill_alpha))
        draw.line(upper, fill=line, width=max(3, int(h * 0.045)), joint="curve")
        draw.line(lower_curve, fill=(120, 62, 58, 90), width=max(2, int(h * 0.025)), joint="curve")
    canvas.alpha_composite(shape.filter(ImageFilter.GaussianBlur(0.35)))


def draw_mouth(canvas: Image.Image, bbox: list[int], kind: str, source: Image.Image) -> None:
    x, y, w, h = bbox
    line = (126, 63, 58, 230)
    inner = (96, 43, 52, 235)
    teeth = (255, 241, 229, 235)
    tongue = (224, 137, 137, 220)
    cx, cy = bbox_center(bbox)
    layer = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    if kind == "mouth_closed_smile":
        curve = quadratic_points(((x + w * 0.24, y + h * 0.48), (cx, y + h * 0.64), (x + w * 0.76, y + h * 0.48)), 60)
        draw.line(curve, fill=line, width=4, joint="curve")
    elif kind == "mouth_small_open":
        draw.ellipse((cx - w * 0.16, cy - h * 0.10, cx + w * 0.16, cy + h * 0.16), fill=inner)
        draw.arc((cx - w * 0.17, cy - h * 0.11, cx + w * 0.17, cy + h * 0.17), 180, 360, fill=line, width=3)
        draw.ellipse((cx - w * 0.10, cy + h * 0.04, cx + w * 0.10, cy + h * 0.15), fill=tongue)
    elif kind == "mouth_wide_open":
        draw.rounded_rectangle((cx - w * 0.26, cy - h * 0.14, cx + w * 0.26, cy + h * 0.22), radius=18, fill=inner)
        draw.rectangle((cx - w * 0.22, cy - h * 0.12, cx + w * 0.22, cy - h * 0.02), fill=teeth)
        draw.ellipse((cx - w * 0.18, cy + h * 0.04, cx + w * 0.18, cy + h * 0.22), fill=tongue)
        draw.rounded_rectangle((cx - w * 0.26, cy - h * 0.14, cx + w * 0.26, cy + h * 0.22), radius=18, outline=line, width=3)
    elif kind == "mouth_o_vowel":
        draw.ellipse((cx - w * 0.17, cy - h * 0.20, cx + w * 0.17, cy + h * 0.22), fill=inner)
        draw.ellipse((cx - w * 0.17, cy - h * 0.20, cx + w * 0.17, cy + h * 0.22), outline=line, width=4)
        draw.ellipse((cx - w * 0.09, cy + h * 0.07, cx + w * 0.09, cy + h * 0.20), fill=tongue)
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.25)))


def generate_face_base_clean(source: Image.Image, out_path: Path, rois: dict[str, list[int]]) -> None:
    base_path = CURRENT_LAYER_DIR / "11_face_base.png"
    base = Image.open(base_path).convert("RGBA") if base_path.exists() else source.copy()
    for key in ("eye_L", "eye_R", "mouth"):
        patch = make_skin_patch(source, rois[key], alpha_scale=1.0)
        paste_box(base, patch, rois[key], patch.getchannel("A"))
    base.save(out_path)


def generate_asset(asset_id: str, source: Image.Image, rois: dict[str, list[int]], out_path: Path) -> str:
    canvas = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    if asset_id == "face_base_clean":
        generate_face_base_clean(source, out_path, rois)
        return "generated_clean_face_base_from_source_roi_patches"

    if asset_id.startswith("eye_"):
        side = "eye_L" if asset_id.startswith("eye_L") else "eye_R"
        bbox = alpha_bbox(EXISTING_ASSET_FILES.get(f"{side}_closed_lid", Path())) or rois[side]
        patch_bbox = padded(bbox, 24, 24)
        if asset_id.endswith("clean_socket") or asset_id.endswith("closed_underpaint"):
            patch = make_skin_patch(source, patch_bbox, alpha_scale=0.96)
            paste_box(canvas, patch, patch_bbox, patch.getchannel("A"))
            canvas.save(out_path)
            return "generated_skin_underpaint_from_pack_eye_roi"
        if "half_closed" in asset_id:
            draw_lid(canvas, patch_bbox, openness=0.5, source=source)
        elif "mostly_closed" in asset_id:
            draw_lid(canvas, patch_bbox, openness=0.18, source=source)
        else:
            draw_lid(canvas, patch_bbox, openness=0.0, source=source)
        canvas.save(out_path)
        return "generated_lid_keypose_from_pack_eye_roi"

    if asset_id == "mouth_base_clean":
        bbox = rois["mouth"]
        patch = make_skin_patch(source, bbox, alpha_scale=0.95)
        paste_box(canvas, patch, bbox, patch.getchannel("A"))
        canvas.save(out_path)
        return "generated_mouth_clean_socket_from_pack_roi"

    if asset_id.startswith("mouth_"):
        draw_mouth(canvas, rois["mouth"], asset_id, source)
        canvas.save(out_path)
        return "generated_mouth_keypose_from_pack_roi"

    canvas.save(out_path)
    return "generated_empty_unhandled"


def build_contact_sheet(paths: list[Path], out_path: Path) -> None:
    thumb_w, thumb_h = 260, 260
    cols = 5
    rows = math.ceil(len(paths) / cols)
    sheet = Image.new("RGB", (cols * thumb_w, rows * thumb_h), (242, 238, 229))
    draw = ImageDraw.Draw(sheet)
    for idx, path in enumerate(paths):
        x = (idx % cols) * thumb_w
        y = (idx // cols) * thumb_h
        bg = Image.new("RGBA", (thumb_w, thumb_h), (242, 238, 229, 255))
        img = Image.open(path).convert("RGBA")
        alpha_box = img.getchannel("A").getbbox()
        if alpha_box:
            crop = img.crop(alpha_box)
        else:
            crop = img
        crop.thumbnail((thumb_w - 24, thumb_h - 48), Image.Resampling.LANCZOS)
        bg.alpha_composite(crop, ((thumb_w - crop.width) // 2, 34 + (thumb_h - 48 - crop.height) // 2))
        sheet.paste(bg.convert("RGB"), (x, y))
        draw.text((x + 8, y + 8), path.stem[:31], fill=(30, 32, 36))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    pack = load_json(args.pack / "imagen_input_pack_manifest.json")
    spec = load_json(Path(pack["references"]["requirements"]))
    source = Image.open(pack["references"]["source_2048_rgba"]).convert("RGBA")
    rois = pack["rois"]
    out_layers = args.out_dir / "normalized_layers"
    out_layers.mkdir(parents=True, exist_ok=True)

    rows = []
    for asset in spec["required_assets"]:
        asset_id = asset["asset_id"]
        out_path = out_layers / f"{asset_id}.png"
        existing = EXISTING_ASSET_FILES.get(asset_id)
        if existing and existing.exists():
            shutil.copy2(existing, out_path)
            mode = "copied_existing_validated_layer"
        else:
            mode = generate_asset(asset_id, source, rois, out_path)
        rows.append({"asset_id": asset_id, "output_path": str(out_path), "generation_mode": mode})

    build_contact_sheet([Path(row["output_path"]) for row in rows], args.out_dir / "local_generated_keypose_contact_sheet.png")
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS_LOCAL_PNGS_GENERATED_REQUIRES_VISUAL_QA",
        "input_pack": str(args.pack.resolve()),
        "output_dir": str(args.out_dir.resolve()),
        "normalized_layers": str(out_layers.resolve()),
        "note": "Deterministic local pack realization. Validator-ready PNGs, not model-native inpaint proof.",
        "assets": rows,
    }
    write_json(args.out_dir / "local_generation_report.json", report)
    print(json.dumps({"ok": True, "status": report["status"], "layers": str(out_layers)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Helpers for the Cubism v2 material asset draft pipeline."""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


ROOT = Path("/Users/family/jason/Vtube")
EXPERIMENT = ROOT / "experiments/cubism-v2-new-character-001"
MATERIAL_PACK = EXPERIMENT / "material_pack_v0"
REPORTS = MATERIAL_PACK / "reports"
CANONICAL_DIR = MATERIAL_PACK / "canonical"
LAYERS_DIR = MATERIAL_PACK / "production_layers"
MERGED_DIR = MATERIAL_PACK / "merged_metadata"

SOURCE_CANDIDATE = EXPERIMENT / "concepts/g0_adult_cute_female_candidate_002.png"
G1_PLAN = EXPERIMENT / "reports/g1_material_planning_packet.json"
MANIFEST_PATH = MATERIAL_PACK / "material_asset_manifest.json"
LAYER_MANIFEST_PATH = MATERIAL_PACK / "layer_manifest.json"
CANONICAL_2048 = CANONICAL_DIR / "candidate_002_2048_rgba.png"
PSD_CANDIDATE = MATERIAL_PACK / "import_ready_candidate.psd"
CONTACT_SHEET = REPORTS / "material_contact_sheet.png"
VALIDATION_JSON = REPORTS / "material_asset_validation_report.json"
VALIDATION_MD = REPORTS / "material_asset_validation_report.md"

CANVAS = (2048, 2048)
SOURCE_SIZE = (1086, 1448)
PASTE_OFFSET = ((CANVAS[0] - SOURCE_SIZE[0]) // 2, (CANVAS[1] - SOURCE_SIZE[1]) // 2)


@dataclass(frozen=True)
class BBox:
    x: int
    y: int
    w: int
    h: int

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h

    def clamp(self) -> "BBox":
        x0 = max(0, min(CANVAS[0], self.x))
        y0 = max(0, min(CANVAS[1], self.y))
        x1 = max(0, min(CANVAS[0], self.right))
        y1 = max(0, min(CANVAS[1], self.bottom))
        return BBox(x0, y0, max(0, x1 - x0), max(0, y1 - y0))

    def pad(self, x: int, y: int) -> "BBox":
        return BBox(self.x - x, self.y - y, self.w + x * 2, self.h + y * 2).clamp()

    def as_list(self) -> list[int]:
        return [self.x, self.y, self.w, self.h]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def source_bbox(x: int, y: int, w: int, h: int) -> list[int]:
    return [x, y, w, h]


def canvas_bbox(src_bbox: list[int]) -> BBox:
    ox, oy = PASTE_OFFSET
    return BBox(src_bbox[0] + ox, src_bbox[1] + oy, src_bbox[2], src_bbox[3]).clamp()


def band_order(band: str) -> int:
    order = [
        "body_back",
        "hair_back",
        "body_mid",
        "body_front",
        "clothing_mid",
        "face_back",
        "face_mid",
        "face_front",
        "eye_back",
        "eye_mid",
        "eye_front",
        "brow_front",
        "mouth_back",
        "mouth_mid",
        "mouth_front",
        "hair_side",
        "hair_front",
        "clothing_front",
    ]
    return order.index(band) if band in order else len(order)


def bbox_from_alpha(path: Path, threshold: int = 10) -> list[int] | None:
    img = Image.open(path).convert("RGBA")
    alpha = np.array(img)[:, :, 3]
    ys, xs = np.where(alpha > threshold)
    if len(xs) == 0:
        return None
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    return [x0, y0, x1 - x0, y1 - y0]


def alpha_coverage(path: Path, bbox: list[int] | None) -> float:
    if not bbox:
        return 0.0
    img = Image.open(path).convert("RGBA")
    x, y, w, h = bbox
    alpha = np.array(img.crop((x, y, x + w, y + h)))[:, :, 3]
    if alpha.size == 0:
        return 0.0
    return round(float(np.count_nonzero(alpha > 10) / alpha.size), 6)


def create_subject_rgba() -> Image.Image:
    src = Image.open(SOURCE_CANDIDATE).convert("RGB")
    arr = np.array(src).astype(np.int16)
    corners = np.concatenate(
        [
            arr[:20, :20].reshape(-1, 3),
            arr[:20, -20:].reshape(-1, 3),
            arr[-20:, :20].reshape(-1, 3),
            arr[-20:, -20:].reshape(-1, 3),
        ],
        axis=0,
    )
    bg = np.median(corners, axis=0)
    dist = np.sqrt(((arr - bg) ** 2).sum(axis=2))
    alpha = np.clip((dist - 18) * 10, 0, 255).astype(np.uint8)
    alpha = np.array(Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(1.0)))
    rgba = np.dstack([arr.astype(np.uint8), alpha])
    canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    canvas.paste(Image.fromarray(rgba, "RGBA"), PASTE_OFFSET)
    CANONICAL_DIR.mkdir(parents=True, exist_ok=True)
    canvas.save(CANONICAL_2048)
    return canvas


def source_alpha(img: Image.Image) -> np.ndarray:
    return np.array(img)[:, :, 3]


def ellipse_mask(size: tuple[int, int], inset: int = 0) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((inset, inset, size[0] - 1 - inset, size[1] - 1 - inset), fill=255)
    return mask.filter(ImageFilter.GaussianBlur(1.0))


def rounded_mask(size: tuple[int, int], radius: int = 20) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(1.0))


def tapered_underpaint_mask(size: tuple[int, int], part_id: str) -> Image.Image:
    """Soft hidden-area mask that avoids the blocky first draft look."""
    w, h = size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    if "body" in part_id:
        draw.rounded_rectangle((int(w * 0.10), int(h * 0.03), int(w * 0.90), int(h * 0.88)), radius=max(18, w // 10), fill=175)
    elif "arm" in part_id:
        draw.rounded_rectangle((int(w * 0.20), int(h * 0.03), int(w * 0.80), int(h * 0.92)), radius=max(16, w // 5), fill=170)
    elif "neck" in part_id:
        draw.rounded_rectangle((int(w * 0.18), int(h * 0.10), int(w * 0.82), int(h * 0.82)), radius=max(16, w // 6), fill=160)
    elif "face" in part_id:
        draw.ellipse((int(w * 0.04), int(h * 0.02), int(w * 0.96), int(h * 0.94)), fill=150)
    elif "eye" in part_id:
        draw.ellipse((int(w * 0.08), int(h * 0.16), int(w * 0.92), int(h * 0.84)), fill=155)
    elif "hair" in part_id:
        draw.rounded_rectangle((int(w * 0.08), int(h * 0.02), int(w * 0.92), int(h * 0.96)), radius=max(28, w // 12), fill=165)
    else:
        draw.rounded_rectangle((int(w * 0.10), int(h * 0.08), int(w * 0.90), int(h * 0.90)), radius=20, fill=160)
    return mask.filter(ImageFilter.GaussianBlur(max(2, min(w, h) // 24)))


def average_color(img: Image.Image, bbox: BBox, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    crop = img.crop((bbox.x, bbox.y, bbox.right, bbox.bottom)).convert("RGBA")
    arr = np.array(crop)
    mask = arr[:, :, 3] > 20
    if not np.any(mask):
        return fallback
    rgb = arr[:, :, :3][mask]
    return tuple(int(v) for v in np.median(rgb, axis=0))


def draw_centered_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fill: tuple[int, int, int]) -> None:
    try:
        font = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 22)
    except OSError:
        font = ImageFont.load_default()
    draw.text(xy, text, fill=fill, font=font)


def make_empty_layer() -> Image.Image:
    return Image.new("RGBA", CANVAS, (0, 0, 0, 0))


def crop_with_mask(src: Image.Image, bbox: BBox, shape: str = "rect", use_subject_alpha: bool = True) -> Image.Image:
    layer = make_empty_layer()
    crop = src.crop((bbox.x, bbox.y, bbox.right, bbox.bottom)).convert("RGBA")
    if shape == "ellipse":
        shape_mask = ellipse_mask(crop.size)
    elif shape == "rounded":
        shape_mask = rounded_mask(crop.size, radius=max(8, min(crop.size) // 8))
    else:
        shape_mask = Image.new("L", crop.size, 255)
    if use_subject_alpha:
        alpha = ImageChops.multiply(crop.getchannel("A"), shape_mask)
    else:
        alpha = shape_mask
    crop.putalpha(alpha)
    layer.paste(crop, (bbox.x, bbox.y), crop)
    return layer


def color_condition_layer(src: Image.Image, bbox: BBox, condition: str, fallback: tuple[int, int, int]) -> Image.Image:
    layer = make_empty_layer()
    crop = src.crop((bbox.x, bbox.y, bbox.right, bbox.bottom)).convert("RGBA")
    arr = np.array(crop)
    r, g, b, a = [arr[:, :, i] for i in range(4)]
    if condition == "hair":
        mask = (a > 20) & (r > 70) & (r < 190) & (g > 40) & (g < 140) & (b > 40) & (b < 140)
    elif condition == "skin":
        mask = (a > 20) & (r > 185) & (g > 130) & (b > 115) & (r > b)
    elif condition == "dark":
        mask = (a > 20) & (((r + g + b) / 3) < 135)
    elif condition == "pink":
        mask = (a > 20) & (r > 150) & (g < 170) & (b < 180)
    elif condition == "light":
        mask = (a > 20) & (r > 185) & (g > 165) & (b > 150)
    else:
        mask = a > 20
    if np.count_nonzero(mask) < 12:
        color = fallback
        arr[:, :, :3] = np.array(color, dtype=np.uint8)
        arr[:, :, 3] = np.array(rounded_mask(crop.size, 12), dtype=np.uint8)
    else:
        arr[:, :, 3] = np.where(mask, 255, 0).astype(np.uint8)
    result = Image.fromarray(arr, "RGBA").filter(ImageFilter.GaussianBlur(0.4))
    layer.paste(result, (bbox.x, bbox.y), result)
    return layer


def draw_derived_part(part_id: str, bbox: BBox) -> Image.Image:
    layer = make_empty_layer()
    draw = ImageDraw.Draw(layer)
    x, y, w, h = bbox.as_list()
    if part_id in {"eye_L_highlight", "eye_R_highlight"}:
        cx = x + w // 2
        cy = y + h // 2
        draw.ellipse((cx - 8, cy - 10, cx + 8, cy + 8), fill=(255, 255, 255, 230))
        draw.ellipse((cx + 8, cy + 8, cx + 14, cy + 14), fill=(255, 255, 255, 180))
    elif "closed_lid" in part_id:
        draw.arc((x + 12, y + h // 5, x + w - 12, y + h - 16), start=196, end=344, fill=(72, 38, 42, 235), width=6)
        draw.arc((x + 16, y + h // 5 + 10, x + w - 16, y + h - 8), start=200, end=340, fill=(207, 121, 132, 135), width=3)
        for dx in (int(w * 0.25), int(w * 0.50), int(w * 0.75)):
            draw.line((x + dx, y + h // 2 + 10, x + dx + 8, y + h // 2 + 22), fill=(72, 38, 42, 120), width=2)
    elif part_id == "mouth_inner":
        draw.ellipse((x + 26, y + 18, x + w - 26, y + h - 12), fill=(73, 31, 39, 235))
    elif part_id == "mouth_teeth":
        y0 = y + max(6, h // 4)
        y1 = min(y + h - 6, y0 + max(12, h // 3))
        draw.rounded_rectangle((x + 24, y0, x + w - 24, y1), radius=7, fill=(255, 244, 232, 230))
    elif part_id == "mouth_tongue":
        y0 = y + max(10, h // 3)
        y1 = y + h - 6
        draw.ellipse((x + 28, y0, x + w - 28, y1), fill=(219, 118, 130, 215))
    elif part_id == "mouth_line":
        draw.arc((x + 24, y + 8, x + w - 24, y + h - 16), start=28, end=152, fill=(102, 43, 50, 230), width=5)
        draw.arc((x + 34, y + 15, x + w - 34, y + h - 12), start=35, end=145, fill=(232, 150, 150, 115), width=2)
    elif part_id == "mouth_upper_lip_mask":
        draw.arc((x + 24, y + 8, x + w - 24, y + h - 8), start=205, end=335, fill=(116, 52, 60, 210), width=4)
    elif part_id == "mouth_lower_lip_mask":
        draw.arc((x + 28, y + 4, x + w - 28, y + h - 8), start=25, end=155, fill=(214, 128, 136, 175), width=4)
    elif part_id == "mouth_corner_L":
        draw.arc((x + 20, y + 12, x + w + 20, y + h - 8), start=145, end=205, fill=(102, 43, 50, 220), width=4)
    elif part_id == "mouth_corner_R":
        draw.arc((x - 20, y + 12, x + w - 20, y + h - 8), start=335, end=35, fill=(102, 43, 50, 220), width=4)
    return layer.filter(ImageFilter.GaussianBlur(0.25))


def draw_underpaint(part_id: str, src: Image.Image, bbox: BBox) -> Image.Image:
    fallback = (239, 190, 170)
    if "hair" in part_id:
        fallback = (127, 83, 82)
    elif "eye" in part_id:
        fallback = (248, 224, 213)
    elif "body" in part_id or "arm" in part_id or "neck" in part_id or "face" in part_id:
        fallback = (241, 196, 175)
    # The generated source has a bright background and soft alpha. For hidden
    # underpaint, a stable style color is safer than a gray background-biased
    # median, so use the intended fallback color directly.
    color = fallback
    layer = make_empty_layer()
    shape = Image.new("RGBA", (bbox.w, bbox.h), (*color, 210))
    shape.putalpha(tapered_underpaint_mask((bbox.w, bbox.h), part_id))
    layer.paste(shape, (bbox.x, bbox.y), shape)
    return layer


def write_layer_entry_image(entry: dict[str, Any], src: Image.Image) -> dict[str, Any]:
    bbox = BBox(*entry["bbox"])
    part_id = entry["part_id"]
    layer_path = ROOT / entry["output_path"]
    layer_path.parent.mkdir(parents=True, exist_ok=True)
    generation = entry["source_type"]
    shape = entry.get("mask_shape", "rect")
    condition = entry.get("color_condition")
    if generation == "DERIVED_KEYPOSE":
        layer = draw_derived_part(part_id, bbox)
    elif generation == "UNDERPAINT":
        layer = draw_underpaint(part_id, src, bbox)
    elif condition:
        layer = color_condition_layer(src, bbox, condition, entry.get("fallback_color", [220, 180, 170]))
    else:
        layer = crop_with_mask(src, bbox, shape=shape, use_subject_alpha=True)
    layer.save(layer_path)
    alpha_bbox = bbox_from_alpha(layer_path)
    entry["generated"] = True
    entry["bbox_actual"] = alpha_bbox
    entry["alpha_coverage"] = alpha_coverage(layer_path, alpha_bbox)
    entry["canvas_size"] = list(CANVAS)
    return entry


def psd_metadata(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    data = path.read_bytes()
    if data[:4] != b"8BPS":
        return {"exists": True, "valid_header": False}
    import struct

    channels = struct.unpack(">H", data[12:14])[0]
    height = struct.unpack(">I", data[14:18])[0]
    width = struct.unpack(">I", data[18:22])[0]
    depth = struct.unpack(">H", data[22:24])[0]
    color_mode = struct.unpack(">H", data[24:26])[0]
    offset = 26
    color_mode_len = struct.unpack(">I", data[offset : offset + 4])[0]
    offset += 4 + color_mode_len
    resources_len = struct.unpack(">I", data[offset : offset + 4])[0]
    offset += 4 + resources_len
    layer_mask_len = struct.unpack(">I", data[offset : offset + 4])[0]
    offset += 4
    layer_count = 0
    if layer_mask_len >= 6:
        layer_info_len = struct.unpack(">I", data[offset : offset + 4])[0]
        if layer_info_len >= 2:
            layer_count = abs(struct.unpack(">h", data[offset + 4 : offset + 6])[0])
    return {
        "exists": True,
        "valid_header": True,
        "channels": channels,
        "width": width,
        "height": height,
        "depth": depth,
        "color_mode": "RGB" if color_mode == 3 else color_mode,
        "layer_count": layer_count,
    }


def write_psd_candidate(entries: list[dict[str, Any]]) -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "scripts"))
    from cubism_material_pack import write_layered_psd

    psd_entries = [
        {
            "layer_name": item["layer_name"],
            "output_path": str(ROOT / item["output_path"]),
            "draw_order": item["draw_order"],
        }
        for item in entries
        if item.get("include_in_import_psd") and item.get("output_path")
    ]
    writer = write_layered_psd(PSD_CANDIDATE, psd_entries)
    return {"writer": writer, "psd_path": rel(PSD_CANDIDATE), "psd_metadata": psd_metadata(PSD_CANDIDATE)}


def load_font(size: int = 22) -> ImageFont.ImageFont:
    for font_path in [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]:
        try:
            return ImageFont.truetype(font_path, size)
        except OSError:
            pass
    return ImageFont.load_default()

#!/usr/bin/env python3
"""Rebuild Cubism v2 face detail masks from saved manual localization ROIs.

The manual labels are used as semantic location seeds, not as raw rectangular
production crops. This pass replaces fragile face/eye/mouth detail layers with
canonical-pixel masks constrained by the saved ROIs, while preserving the rest
of the active material pack.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from build_cubism_v2_semantic_purity_gate import (
    NEUTRAL_HIDDEN,
    bbox_from_alpha,
    composite,
    eye_mouth_alignment,
    include_layers,
    layer_role_qa,
    load_arrays,
    rel,
    save_layer_contact_sheet,
    save_roi_closeup_sheet,
    score,
    semantic_group,
    underpaint_leakage,
    union_bbox,
)


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "experiments/cubism-v2-new-character-001/material_pack_v0"
CANONICAL_PATH = PACK / "canonical/candidate_002_2048_rgba.png"
MANIFEST_PATH = PACK / "layer_manifest.json"
TEMPLATE_PATH = PACK / "reports/part_localization_template.json"
OUT_DIR = PACK / "production_layers_face_detail_rebuild_v1"
OUT_PACK = PACK / "face_detail_rebuild_pack_v1"
SNAPSHOT_MANIFEST = PACK / "layer_manifest.face_detail_rebuild_v1.json"
REPORT_JSON = PACK / "reports/face_detail_rebuild_report.json"
REPORT_MD = PACK / "reports/face_detail_rebuild_report.md"
CONTACT_SHEET = PACK / "reports/face_detail_rebuild_contact_sheet.png"
PROBLEM_SHEET = PACK / "reports/face_detail_rebuild_problem_sheet.png"
CLOSEUP_SHEET = PACK / "reports/face_detail_rebuild_eye_mouth_closeup.png"
NEUTRAL_AFTER = PACK / "reports/face_detail_rebuild_neutral_composite_after.png"
CHANGED_SHEET = PACK / "reports/face_detail_rebuild_changed_layers.png"

FACE_DETAIL_PREFIXES = ("eye_", "mouth_", "brow_", "face_")
FACE_DETAIL_PARTS = {"nose", "cheek_L", "cheek_R", "face_base"}
UNDERPAINT_PARTS = {"face_underpaint_L", "face_underpaint_R", "eye_L_underpaint", "eye_R_underpaint"}
NEUTRAL_VISUAL_HIDDEN_PARTS = {
    "body_underpaint",
    "neck_shadow_underpaint",
    "arm_L_underpaint",
    "arm_R_underpaint",
    "hair_back_underpaint",
    "hair_front_L",
    "hair_front_R",
    "hair_front_center",
    "hair_front_side_L",
    "hair_front_side_R",
    "hair_front_tip_L",
    "hair_front_tip_R",
    "hair_side_L_inner",
    "hair_side_R_inner",
    "face_underpaint_L",
    "face_underpaint_R",
    "eye_L_underpaint",
    "eye_R_underpaint",
    "eye_L_white",
    "eye_L_iris",
    "eye_L_pupil",
    "eye_L_highlight",
    "eye_L_upper_lash",
    "eye_L_lower_lash",
    "eye_R_white",
    "eye_R_iris",
    "eye_R_pupil",
    "eye_R_highlight",
    "eye_R_upper_lash",
    "eye_R_lower_lash",
    "brow_L",
    "brow_R",
    "face_shadow_L",
    "face_shadow_R",
    "cheek_L",
    "cheek_R",
    "nose",
    "mouth_line",
}
NEUTRAL_VISUAL_HIDDEN = set(NEUTRAL_HIDDEN) | NEUTRAL_VISUAL_HIDDEN_PARTS
NEUTRAL_CANONICAL_BASE_PART = "face_base"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolve(path_value: str) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def font(size: int) -> ImageFont.ImageFont:
    for candidate in [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


def is_face_detail(part_id: str) -> bool:
    return part_id in FACE_DETAIL_PARTS or part_id.startswith(FACE_DETAIL_PREFIXES)


def template_by_part(template: dict[str, Any]) -> dict[str, dict[str, Any]]:
    parts = template.get("parts", {})
    if isinstance(parts, dict):
        return {part_id: dict(row, part_id=part_id) for part_id, row in parts.items()}
    return {row["part_id"]: row for row in parts}


def clamp_bbox(bbox: list[int], pad: int = 0, size: tuple[int, int] = (2048, 2048)) -> list[int]:
    x, y, w, h = [int(v) for v in bbox]
    x0 = max(0, x - pad)
    y0 = max(0, y - pad)
    x1 = min(size[0], x + w + pad)
    y1 = min(size[1], y + h + pad)
    return [x0, y0, max(0, x1 - x0), max(0, y1 - y0)]


def bbox_mask(bbox: list[int], shape: tuple[int, int] = (2048, 2048)) -> np.ndarray:
    x, y, w, h = [int(v) for v in bbox]
    mask = np.zeros(shape, dtype=bool)
    if w > 0 and h > 0:
        mask[y : y + h, x : x + w] = True
    return mask


def ellipse_mask(bbox: list[int], blur: int = 0, scale: float = 1.0) -> np.ndarray:
    x, y, w, h = [int(v) for v in bbox]
    image = Image.new("L", (2048, 2048), 0)
    draw = ImageDraw.Draw(image)
    cx = x + w / 2
    cy = y + h / 2
    sw = w * scale
    sh = h * scale
    draw.ellipse((cx - sw / 2, cy - sh / 2, cx + sw / 2, cy + sh / 2), fill=255)
    if blur:
        image = image.filter(ImageFilter.GaussianBlur(blur))
    return np.array(image, dtype=np.uint8)


def rounded_mask(bbox: list[int], radius: int = 24, blur: int = 0) -> np.ndarray:
    x, y, w, h = [int(v) for v in bbox]
    image = Image.new("L", (2048, 2048), 0)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=255)
    if blur:
        image = image.filter(ImageFilter.GaussianBlur(blur))
    return np.array(image, dtype=np.uint8)


def paste_with_alpha(canonical: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    out = np.zeros_like(canonical)
    out[:, :, :3] = canonical[:, :, :3]
    out[:, :, 3] = np.minimum(alpha.astype(np.uint8), canonical[:, :, 3])
    return out


def soft_color_layer(color: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    out = np.zeros((2048, 2048, 4), dtype=np.uint8)
    out[:, :, :3] = color.astype(np.uint8)
    out[:, :, 3] = alpha.astype(np.uint8)
    return out


def alpha_bbox_metadata(arr: np.ndarray) -> dict[str, Any]:
    bbox = bbox_from_alpha(arr)
    return {
        "bbox_actual": bbox,
        "alpha_coverage": round(float((arr[:, :, 3] > 5).sum() / (arr.shape[0] * arr.shape[1])), 8),
    }


def local_pixels(canonical: np.ndarray, bbox: list[int]) -> np.ndarray:
    x, y, w, h = [int(v) for v in bbox]
    crop = canonical[y : y + h, x : x + w]
    visible = crop[:, :, 3] > 5
    if visible.any():
        return crop[:, :, :3][visible].astype(np.float32)
    return crop[:, :, :3].reshape(-1, 3).astype(np.float32)


def median_color(canonical: np.ndarray, bboxes: list[list[int]], fallback: tuple[int, int, int]) -> np.ndarray:
    chunks = [local_pixels(canonical, bbox) for bbox in bboxes if bbox and bbox[2] > 0 and bbox[3] > 0]
    chunks = [chunk for chunk in chunks if len(chunk)]
    if not chunks:
        return np.array(fallback, dtype=np.uint8)
    pixels = np.concatenate(chunks, axis=0)
    return np.median(pixels, axis=0).clip(0, 255).astype(np.uint8)


def luminance(rgb: np.ndarray) -> np.ndarray:
    return rgb[:, :, 0] * 0.299 + rgb[:, :, 1] * 0.587 + rgb[:, :, 2] * 0.114


def saturation(rgb: np.ndarray) -> np.ndarray:
    rgb_f = rgb.astype(np.float32)
    maxc = rgb_f.max(axis=2)
    minc = rgb_f.min(axis=2)
    return (maxc - minc) / np.maximum(maxc, 1)


def color_distance(rgb: np.ndarray, color: np.ndarray) -> np.ndarray:
    diff = rgb.astype(np.float32) - color.astype(np.float32)
    return np.sqrt(np.sum(diff * diff, axis=2))


def ensure_nonempty(alpha: np.ndarray, fallback: np.ndarray, min_pixels: int = 20) -> np.ndarray:
    if int((alpha > 5).sum()) >= min_pixels:
        return alpha.astype(np.uint8)
    return np.maximum(alpha.astype(np.uint8), fallback.astype(np.uint8))


def remove_mask(alpha: np.ndarray, masks: list[np.ndarray]) -> np.ndarray:
    out = alpha.copy()
    for mask in masks:
        out[mask > 5] = 0
    return out


def build_eye_masks(part_id: str, canonical: np.ndarray, roi: list[int]) -> tuple[np.ndarray, str]:
    rgb = canonical[:, :, :3]
    lum = luminance(rgb)
    sat = saturation(rgb)
    in_roi = bbox_mask(roi)
    soft = ellipse_mask(roi, blur=2, scale=1.0)
    dark = ((lum < 120) | ((lum < 165) & (sat > 0.22))) & in_roi & (canonical[:, :, 3] > 5)
    bright = (lum > 145) & (sat < 0.42) & in_roi & (canonical[:, :, 3] > 5)

    if part_id.endswith("_white"):
        alpha = np.where(bright, 230, 0).astype(np.uint8)
        alpha = np.maximum(alpha, (soft * 0.62).astype(np.uint8))
        return paste_with_alpha(canonical, alpha), "eye_white_luminance_roi"
    if part_id.endswith("_iris"):
        alpha = np.where(dark | (((sat > 0.18) & (lum < 190)) & in_roi), 245, 0).astype(np.uint8)
        alpha = np.maximum(alpha, ellipse_mask(roi, blur=1, scale=0.9))
        return paste_with_alpha(canonical, alpha), "eye_iris_color_roi"
    if part_id.endswith("_pupil"):
        alpha = np.where((lum < 90) & in_roi & (canonical[:, :, 3] > 5), 255, 0).astype(np.uint8)
        alpha = ensure_nonempty(alpha, ellipse_mask(roi, blur=1, scale=0.82), 15)
        return paste_with_alpha(canonical, alpha), "eye_pupil_dark_roi"
    if part_id.endswith("_highlight"):
        alpha = np.where((lum > 210) & (sat < 0.28) & in_roi & (canonical[:, :, 3] > 5), 255, 0).astype(np.uint8)
        alpha = ensure_nonempty(alpha, ellipse_mask(roi, blur=1, scale=0.65), 12)
        return paste_with_alpha(canonical, alpha), "eye_highlight_bright_roi"
    if part_id.endswith("_upper_lash") or part_id.endswith("_lower_lash"):
        alpha = np.where((lum < 130) & in_roi & (canonical[:, :, 3] > 5), 255, 0).astype(np.uint8)
        alpha = ensure_nonempty(alpha, soft, 40)
        return paste_with_alpha(canonical, alpha), "eye_lash_dark_roi"
    if part_id.endswith("_closed_lid"):
        x, y, w, h = roi
        image = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        color = tuple(int(v) for v in median_color(canonical, [roi], (82, 56, 54))) + (230,)
        draw.arc((x + 6, y + h * 0.22, x + w - 6, y + h * 1.15), start=190, end=350, fill=color, width=max(3, h // 9))
        image = image.filter(ImageFilter.GaussianBlur(0.4))
        return np.array(image, dtype=np.uint8), "eye_closed_lid_drawn_from_roi"
    if "underpaint" in part_id:
        color = median_color(canonical, [roi], (248, 224, 213))
        alpha = (ellipse_mask(roi, blur=4, scale=0.82) * 0.42).clip(0, 110).astype(np.uint8)
        return soft_color_layer(color, alpha), "eye_underpaint_soft_fill_from_eye_core_roi"
    return paste_with_alpha(canonical, soft), "eye_generic_roi"


def build_mouth_masks(part_id: str, canonical: np.ndarray, roi: list[int]) -> tuple[np.ndarray, str]:
    rgb = canonical[:, :, :3]
    lum = luminance(rgb)
    sat = saturation(rgb)
    in_roi = bbox_mask(roi)
    dark = (lum < 120) & in_roi & (canonical[:, :, 3] > 5)
    red = (rgb[:, :, 0] > rgb[:, :, 1] + 12) & (rgb[:, :, 0] > rgb[:, :, 2] + 8) & (sat > 0.12) & in_roi
    bright = (lum > 185) & (sat < 0.35) & in_roi

    if part_id == "mouth_line":
        alpha = np.where(dark | red, 255, 0).astype(np.uint8)
        alpha = ensure_nonempty(alpha, rounded_mask(roi, radius=max(4, roi[3] // 2), blur=1), 30)
        return paste_with_alpha(canonical, alpha), "mouth_line_dark_red_roi"
    if part_id == "mouth_inner":
        alpha = np.maximum(np.where(dark | red, 245, 0).astype(np.uint8), ellipse_mask(roi, blur=2, scale=0.82))
        return paste_with_alpha(canonical, alpha), "mouth_inner_dark_soft_roi"
    if part_id == "mouth_teeth":
        alpha = np.where(bright, 245, 0).astype(np.uint8)
        alpha = ensure_nonempty(alpha, rounded_mask(roi, radius=8, blur=1), 18)
        return paste_with_alpha(canonical, alpha), "mouth_teeth_bright_roi"
    if part_id == "mouth_tongue":
        color = median_color(canonical, [roi], (196, 90, 110))
        alpha = ellipse_mask(roi, blur=2, scale=0.78)
        return soft_color_layer(color, alpha), "mouth_tongue_soft_roi"
    if "lip_mask" in part_id:
        alpha = (rounded_mask(roi, radius=max(4, roi[3] // 2), blur=2) * 0.68).astype(np.uint8)
        return paste_with_alpha(canonical, alpha), "mouth_lip_mask_soft_roi"
    if "corner" in part_id:
        alpha = np.where(dark | red, 255, 0).astype(np.uint8)
        alpha = ensure_nonempty(alpha, ellipse_mask(roi, blur=1, scale=0.82), 12)
        return paste_with_alpha(canonical, alpha), "mouth_corner_roi"
    return paste_with_alpha(canonical, rounded_mask(roi, radius=8, blur=1)), "mouth_generic_roi"


def build_face_masks(
    part_id: str,
    canonical: np.ndarray,
    roi: list[int],
    template_parts: dict[str, dict[str, Any]],
    reference_bboxes: dict[str, list[int]],
    skin_color: np.ndarray,
    existing_arr: np.ndarray | None = None,
) -> tuple[np.ndarray, str]:
    rgb = canonical[:, :, :3]
    lum = luminance(rgb)
    face_roi = reference_bboxes.get("face") or roi
    face_mask = ellipse_mask(clamp_bbox(face_roi, pad=16), blur=2, scale=1.08)
    in_roi = bbox_mask(roi)
    skin_like = (color_distance(rgb, skin_color) < 92) & (lum > 95) & (canonical[:, :, 3] > 5)

    exclusion_ids: list[str] = []
    exclusions = [ellipse_mask(template_parts[p]["roi_abs"], blur=3, scale=1.08) for p in exclusion_ids if p in template_parts]

    if part_id == "face_base":
        # Use face_base as a low draw-order neutral underlay. The visible
        # face/eye/mouth parts are still separate and drawn above this layer,
        # but any tiny alpha holes left by hidden helper layers fall back to
        # the clean canonical pixels instead of black/skin-color blotches.
        alpha = canonical[:, :, 3].copy()
        out = paste_with_alpha(canonical, alpha)
        detail_holes = np.zeros((2048, 2048), dtype=bool)
        for mask in exclusions:
            detail_holes |= mask > 5
        detail_holes &= alpha > 5
        out[detail_holes, :3] = skin_color
        return out, "face_base_canonical_neutral_underlay"
    if part_id in UNDERPAINT_PARTS:
        alpha = (ellipse_mask(roi, blur=9, scale=1.0) * 0.58).clip(0, 160).astype(np.uint8)
        return soft_color_layer(skin_color, alpha), "face_eye_underpaint_soft_skin_fill"
    if part_id.startswith("face_shadow_"):
        side = "L" if part_id.endswith("_L") else "R"
        alpha = (np.where(in_roi & skin_like, 18, 0).astype(np.uint8) + (ellipse_mask(roi, blur=10, scale=0.96) * 0.035)).clip(0, 28).astype(np.uint8)
        if side == "L":
            alpha[:, roi[0] + roi[2] // 2 :] = (alpha[:, roi[0] + roi[2] // 2 :] * 0.45).astype(np.uint8)
        else:
            alpha[:, : roi[0] + roi[2] // 2] = (alpha[:, : roi[0] + roi[2] // 2] * 0.45).astype(np.uint8)
        return paste_with_alpha(canonical, alpha), "face_shadow_soft_skin_roi"
    if part_id == "nose":
        dark = (lum < np.percentile(lum[in_roi], 45) if in_roi.any() else lum < 140) & in_roi
        alpha = np.where(dark & skin_like, 190, 0).astype(np.uint8)
        alpha = ensure_nonempty(alpha, ellipse_mask(roi, blur=3, scale=0.72), 40)
        return paste_with_alpha(canonical, alpha), "nose_soft_detail_roi"
    if part_id.startswith("cheek_"):
        alpha = (ellipse_mask(roi, blur=6, scale=0.62) * 0.08).clip(0, 24).astype(np.uint8)
        return paste_with_alpha(canonical, alpha), "cheek_soft_blush_roi"
    return paste_with_alpha(canonical, np.where(in_roi, 255, 0).astype(np.uint8)), "face_generic_roi"


def build_brow_mask(part_id: str, canonical: np.ndarray, roi: list[int]) -> tuple[np.ndarray, str]:
    lum = luminance(canonical[:, :, :3])
    in_roi = bbox_mask(roi)
    alpha = np.where((lum < 145) & in_roi & (canonical[:, :, 3] > 5), 255, 0).astype(np.uint8)
    alpha = ensure_nonempty(alpha, rounded_mask(roi, radius=max(6, roi[3] // 2), blur=1), 35)
    return paste_with_alpha(canonical, alpha), "brow_dark_roi"


def eye_core_roi(part_id: str, template_parts: dict[str, dict[str, Any]]) -> list[int] | None:
    if part_id.startswith("eye_L_"):
        side = "eye_L"
    elif part_id.startswith("eye_R_"):
        side = "eye_R"
    else:
        return None
    related = [
        f"{side}_white",
        f"{side}_iris",
        f"{side}_pupil",
        f"{side}_highlight",
        f"{side}_upper_lash",
        f"{side}_lower_lash",
    ]
    related_rois = [template_parts[p]["roi_abs"] for p in related if p in template_parts]
    return union_bbox(related_rois, pad=8) if related_rois else None


def build_rebuilt_layer(
    part_id: str,
    layer: dict[str, Any],
    canonical: np.ndarray,
    template_parts: dict[str, dict[str, Any]],
    reference_bboxes: dict[str, list[int]],
    skin_color: np.ndarray,
) -> tuple[np.ndarray, str]:
    row = template_parts.get(part_id)
    if part_id == "face_base":
        roi = clamp_bbox(reference_bboxes.get("face") or layer.get("bbox") or [796, 685, 470, 389], pad=20)
    elif row:
        roi = row["roi_abs"]
    else:
        roi = layer.get("bbox_actual") or layer.get("bbox") or [0, 0, 0, 0]
    roi = clamp_bbox(roi)

    if part_id.startswith("eye_"):
        if part_id.endswith("_underpaint") or part_id.endswith("_closed_lid"):
            roi = clamp_bbox(eye_core_roi(part_id, template_parts) or roi)
        elif part_id.endswith("_white"):
            side = "eye_L" if part_id.startswith("eye_L_") else "eye_R"
            related = [part_id, f"{side}_iris", f"{side}_pupil", f"{side}_highlight"]
            related_rois = [template_parts[p]["roi_abs"] for p in related if p in template_parts]
            roi = union_bbox(related_rois, pad=6) if related_rois else roi
        return build_eye_masks(part_id, canonical, roi)
    if part_id.startswith("mouth_"):
        return build_mouth_masks(part_id, canonical, roi)
    if part_id.startswith("brow_"):
        return build_brow_mask(part_id, canonical, roi)
    existing_arr = np.array(Image.open(resolve(layer["output_path"])).convert("RGBA"))
    return build_face_masks(part_id, canonical, roi, template_parts, reference_bboxes, skin_color, existing_arr)


def save_changed_sheet(rows: list[dict[str, Any]], out_path: Path) -> None:
    cell_w, cell_h = 270, 270
    cols = 4
    page_rows = max(1, (len(rows) + cols - 1) // cols)
    sheet = Image.new("RGB", (cols * cell_w, page_rows * cell_h), (247, 249, 252))
    draw = ImageDraw.Draw(sheet)
    title_font = font(14)
    small_font = font(11)
    for index, row in enumerate(rows):
        x = (index % cols) * cell_w
        y = (index // cols) * cell_h
        draw.rounded_rectangle((x + 8, y + 8, x + cell_w - 8, y + cell_h - 8), radius=8, fill=(255, 255, 255), outline=(226, 232, 240))
        image = Image.open(row["output_path"]).convert("RGBA")
        bbox = row["bbox_actual"]
        if bbox and bbox[2] > 0 and bbox[3] > 0:
            crop = image.crop((bbox[0], bbox[1], bbox[0] + bbox[2], bbox[1] + bbox[3]))
            bg = Image.new("RGBA", crop.size, (245, 245, 245, 255))
            bg.alpha_composite(crop)
            bg.thumbnail((cell_w - 36, 150), Image.Resampling.LANCZOS)
            sheet.paste(bg.convert("RGB"), (x + (cell_w - bg.width) // 2, y + 16))
        draw.text((x + 16, y + 178), row["part_id"][:28], fill=(25, 31, 40), font=title_font)
        draw.text((x + 16, y + 200), row["method"][:34], fill=(75, 85, 99), font=small_font)
        draw.text((x + 16, y + 218), f"bbox={bbox}", fill=(75, 85, 99), font=small_font)
        draw.text((x + 16, y + 236), f"alpha={row['alpha_coverage']}", fill=(75, 85, 99), font=small_font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def neutral_hidden_keyframe(part_id: str) -> dict[str, Any]:
    return {
        "part_id": part_id,
        "parameter_id": "ParamAngleX",
        "mode": "linear",
        "keyframes": [
            {"value": -30, "opacity": 1},
            {"value": -1, "opacity": 0},
            {"value": 0, "opacity": 0},
            {"value": 1, "opacity": 0},
            {"value": 30, "opacity": 1},
        ],
        "purpose": "neutral visual repair v2: hide helper/underpaint/shadow layer at default pose so the stacked preview matches the canonical face",
    }


def neutral_visual_hidden_parts(layers: list[dict[str, Any]]) -> set[str]:
    # The current source art carries semi-transparent pixels. If several
    # extracted parts are visible at the default pose, alpha accumulates even
    # when RGB values match the canonical image. Keep the clean canonical base
    # as the only default-pose visual owner; the split parts remain available
    # away from neutral through opacity keyframes.
    return {
        layer["part_id"]
        for layer in include_layers(layers)
        if layer["part_id"] != NEUTRAL_CANONICAL_BASE_PART
    } | set(NEUTRAL_HIDDEN) | NEUTRAL_VISUAL_HIDDEN_PARTS


def apply_neutral_visual_opacity_keyframes(manifest: dict[str, Any]) -> set[str]:
    hidden_parts = neutral_visual_hidden_parts(manifest["layers"])
    existing = list(manifest.get("part_opacity_keyframes") or [])
    keyed = {
        (row.get("part_id"), row.get("parameter_id"), row.get("purpose", ""))
        for row in existing
    }
    for part_id in sorted(hidden_parts):
        key = (part_id, "ParamAngleX", "neutral visual repair v2: hide helper/underpaint/shadow layer at default pose so the stacked preview matches the canonical face")
        if key in keyed:
            continue
        existing.append(neutral_hidden_keyframe(part_id))
    manifest["part_opacity_keyframes"] = existing
    return hidden_parts


def build_rois(template_parts: dict[str, dict[str, Any]], updated_layers: list[dict[str, Any]]) -> dict[str, list[int]]:
    def tr(part_id: str) -> list[int]:
        if part_id in template_parts:
            return clamp_bbox(template_parts[part_id]["roi_abs"], pad=8)
        by_part = {layer["part_id"]: layer for layer in include_layers(updated_layers)}
        layer = by_part.get(part_id, {})
        return layer.get("bbox_actual") or layer.get("bbox") or [0, 0, 0, 0]

    return {
        "eye_L": union_bbox([tr(part) for part in ["eye_L_white", "eye_L_iris", "eye_L_pupil", "eye_L_highlight", "eye_L_upper_lash", "eye_L_lower_lash", "eye_L_closed_lid"]], 8),
        "eye_R": union_bbox([tr(part) for part in ["eye_R_white", "eye_R_iris", "eye_R_pupil", "eye_R_highlight", "eye_R_upper_lash", "eye_R_lower_lash", "eye_R_closed_lid"]], 8),
        "mouth": union_bbox([tr(part) for part in ["mouth_line", "mouth_inner", "mouth_teeth", "mouth_tongue", "mouth_upper_lip_mask", "mouth_lower_lip_mask", "mouth_corner_L", "mouth_corner_R"]], 8),
    }


def build(promote: bool) -> dict[str, Any]:
    template = load_json(TEMPLATE_PATH)
    manifest = load_json(MANIFEST_PATH)
    template_parts = template_by_part(template)
    reference_bboxes = template.get("reference_bboxes") or {}
    canonical = np.array(Image.open(CANONICAL_PATH).convert("RGBA"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    skin_sample_parts = ["cheek_L", "cheek_R", "nose", "face_shadow_L", "face_shadow_R"]
    skin_bboxes = [template_parts[p]["roi_abs"] for p in skin_sample_parts if p in template_parts]
    skin_color = median_color(canonical, skin_bboxes, (242, 196, 178))

    updated = json.loads(json.dumps(manifest))
    updated["status"] = "FACE_DETAIL_REBUILD_V1_APPLIED"
    updated["face_detail_rebuild"] = {
        "schema_version": 1,
        "applied_at": now(),
        "template": rel(TEMPLATE_PATH),
        "canonical": rel(CANONICAL_PATH),
        "output_dir": rel(OUT_DIR),
        "method": "manual ROI seeds plus canonical-pixel semantic masks; anchors preserved as evidence but not used as primary extraction centers",
        "promoted_to_active_manifest": promote,
        "neutral_visual_hidden_parts": [],
    }
    neutral_hidden = apply_neutral_visual_opacity_keyframes(updated)
    updated["face_detail_rebuild"]["neutral_visual_hidden_parts"] = sorted(neutral_hidden)

    changed_rows: list[dict[str, Any]] = []
    copied = 0
    rebuilt = 0
    rebuilt_arrays: dict[str, np.ndarray] = {}
    for layer in updated["layers"]:
        if not layer.get("include_in_import_psd"):
            continue
        part_id = layer["part_id"]
        output = OUT_DIR / Path(layer["output_path"]).name
        if is_face_detail(part_id):
            arr, method = build_rebuilt_layer(part_id, layer, canonical, template_parts, reference_bboxes, skin_color)
            Image.fromarray(arr.astype(np.uint8), "RGBA").save(output)
            layer["pre_face_detail_rebuild_output_path"] = layer["output_path"]
            layer["output_path"] = rel(output)
            layer["face_detail_rebuild_method"] = method
            layer["semantic_group"] = semantic_group(part_id, layer.get("source_type"))
            layer.update(alpha_bbox_metadata(arr))
            layer["notes"] = (layer.get("notes") or "").strip() + " Face detail rebuild v1 regenerated this layer from clean canonical and manual ROI seed."
            changed_rows.append(
                {
                    "part_id": part_id,
                    "method": method,
                    "bbox_actual": layer["bbox_actual"],
                    "alpha_coverage": layer["alpha_coverage"],
                    "output_path": str(output),
                }
            )
            rebuilt_arrays[part_id] = arr
            rebuilt += 1
        else:
            shutil.copy2(resolve(layer["output_path"]), output)
            layer["pre_face_detail_rebuild_output_path"] = layer["output_path"]
            layer["output_path"] = rel(output)
            copied += 1

    write_json(SNAPSHOT_MANIFEST, updated)
    OUT_PACK.mkdir(parents=True, exist_ok=True)
    write_json(OUT_PACK / "layer_manifest.json", updated)
    if promote:
        backup = MANIFEST_PATH.with_name("layer_manifest.before_face_detail_rebuild_v1.json")
        if not backup.exists():
            shutil.copy2(MANIFEST_PATH, backup)
        write_json(MANIFEST_PATH, updated)

    arrays = load_arrays(updated["layers"])
    rois = build_rois(template_parts, updated["layers"])
    after_composite, after_owner = composite(updated["layers"], arrays, neutral_hidden, (2048, 2048))
    after_score = score(canonical, after_composite)
    after_underpaint = underpaint_leakage(updated["layers"], arrays, after_owner, "face_detail_rebuild_after")
    after_eye_mouth = eye_mouth_alignment(updated["layers"], arrays, rois)
    qa_rows = layer_role_qa(updated["layers"], arrays, rois)
    problem_rows = [row for row in qa_rows if row["verdict"] != "PASS"]

    save_layer_contact_sheet(updated["layers"], arrays, qa_rows, CONTACT_SHEET)
    save_layer_contact_sheet(updated["layers"], arrays, qa_rows, PROBLEM_SHEET, only_problem=True)
    save_roi_closeup_sheet(canonical, after_composite, arrays, rois, CLOSEUP_SHEET)
    Image.fromarray(after_composite.astype(np.uint8), "RGBA").save(NEUTRAL_AFTER)
    save_changed_sheet(changed_rows, CHANGED_SHEET)

    face_parts = [row for row in changed_rows if row["part_id"] == "face_base" or row["part_id"].startswith(("face_", "eye_", "mouth_", "brow_")) or row["part_id"] in {"nose", "cheek_L", "cheek_R"}]
    empty_rebuilt = [row["part_id"] for row in face_parts if row["bbox_actual"][2] <= 0 or row["bbox_actual"][3] <= 0]
    pass_conditions = {
        "import_layer_count_62": len([layer for layer in include_layers(updated["layers"])]) == 62,
        "rebuilt_parts_nonempty": not empty_rebuilt,
        "neutral_after_lte_5pct": after_score["bad_ratio_visible"] <= 0.05,
        "eye_mouth_after_pass": after_eye_mouth["status"] == "PASS",
        "snapshot_manifest_written": SNAPSHOT_MANIFEST.exists(),
        "preview_pack_manifest_written": (OUT_PACK / "layer_manifest.json").exists(),
    }
    status = "PASS_FACE_DETAIL_REBUILD_V1" if all(pass_conditions.values()) else "REVISE_FACE_DETAIL_REBUILD_V1"
    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": status,
        "promoted_to_active_manifest": promote,
        "source_manifest": rel(MANIFEST_PATH),
        "snapshot_manifest": rel(SNAPSHOT_MANIFEST),
        "output_dir": rel(OUT_DIR),
        "preview_pack": rel(OUT_PACK),
        "counts": {
            "copied_layers": copied,
            "rebuilt_layers": rebuilt,
            "changed_rows": len(changed_rows),
            "qa_problem_rows": len(problem_rows),
        },
        "skin_color_median": skin_color.tolist(),
        "neutral_scores": {"after": after_score},
        "underpaint_leakage": {"after": after_underpaint},
        "eye_mouth_alignment": {"after": after_eye_mouth},
        "layer_qa": {
            "total": len(qa_rows),
            "problem_count": len(problem_rows),
            "problem_rows": problem_rows,
        },
        "changed_rows": changed_rows,
        "empty_rebuilt_parts": empty_rebuilt,
        "pass_conditions": pass_conditions,
        "artifacts": {
            "contact_sheet": rel(CONTACT_SHEET),
            "problem_sheet": rel(PROBLEM_SHEET),
            "changed_layers": rel(CHANGED_SHEET),
            "eye_mouth_closeup": rel(CLOSEUP_SHEET),
            "neutral_composite_after": rel(NEUTRAL_AFTER),
            "preview_pack": rel(OUT_PACK),
        },
        "interpretation": [
            "Manual ROI coordinates were reused as semantic seeds, not production rectangular crops.",
            "This pass rebuilds face detail layers from clean canonical pixels and preserves non-face material layers.",
            "PASS is a material/preview gate only; 주인님 human visual QA is still required before Cubism authoring.",
        ],
    }
    write_json(REPORT_JSON, report)
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Face Detail Rebuild v1",
                "",
                f"- status: `{status}`",
                f"- rebuilt layers: `{rebuilt}`",
                f"- copied layers: `{copied}`",
                f"- neutral after bad ratio: `{after_score['bad_ratio_visible']}`",
                f"- eye/mouth after: `{after_eye_mouth['status']}`",
                f"- QA problem rows: `{len(problem_rows)}`",
                f"- snapshot manifest: `{rel(SNAPSHOT_MANIFEST)}`",
                f"- output dir: `{rel(OUT_DIR)}`",
                f"- preview pack: `{rel(OUT_PACK)}`",
                "",
                "## Artifacts",
                "",
                *[f"- `{value}`" for value in report["artifacts"].values()],
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--promote", action="store_true", help="Write the snapshot back to the active layer_manifest.json after building it.")
    args = parser.parse_args()
    report = build(promote=args.promote)
    print(
        json.dumps(
            {
                "ok": report["status"].startswith("PASS"),
                "status": report["status"],
                "rebuilt_layers": report["counts"]["rebuilt_layers"],
                "neutral_after": report["neutral_scores"]["after"],
                "eye_mouth_after": report["eye_mouth_alignment"]["after"]["status"],
                "snapshot_manifest": str(SNAPSHOT_MANIFEST),
                "report": str(REPORT_JSON),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if report["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())

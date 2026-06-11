#!/usr/bin/env python3
"""Expand coarse See-through layers into Mini Cubism dedicated part candidates."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from build_mini_cubism_dedicated_model_v1 import CANVAS, GROUP_FOLDERS, draw_part_image, part_bbox


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = ROOT / "experiments/mini-cubism-dedicated-model-v1-001"

SOURCE_BY_PART = {
    "body_base": "clothes",
    "neck": "neck",
    "neck_shadow": "neck",
    "chest": "clothes",
    "chest_shadow": "clothes",
    "shoulder_L": "clothes",
    "shoulder_R": "clothes",
    "arm_L": "L_arm",
    "arm_R": "R_arm",
    "sleeve_L": "L_arm",
    "sleeve_R": "R_arm",
    "face_base": "face_base",
    "face_shadow_L": "face_base",
    "face_shadow_R": "face_base",
    "ear_L": "L_ear_outer",
    "ear_R": "R_ear_outer",
    "ear_inner_L": "L_ear_outer",
    "ear_inner_R": "R_ear_outer",
    "cheek_blush_L": "face_base",
    "cheek_blush_R": "face_base",
    "front_bang_L": "front_hair",
    "front_bang_CL": "front_hair",
    "front_bang_C": "front_hair",
    "front_bang_CR": "front_hair",
    "front_bang_R": "front_hair",
    "front_side_lock_L": "front_hair",
    "front_side_lock_R": "front_hair",
    "side_hair_L_upper": "back_hair",
    "side_hair_L_lower": "back_hair",
    "side_hair_R_upper": "back_hair",
    "side_hair_R_lower": "back_hair",
    "back_hair_base": "back_hair",
    "back_hair_L": "back_hair",
    "back_hair_C": "back_hair",
    "back_hair_R": "back_hair",
    "back_hair_tip_L": "back_hair",
    "back_hair_tip_C": "back_hair",
    "back_hair_tip_R": "back_hair",
    "eye_white_L": "L_eye_white",
    "eye_white_R": "R_eye_white",
    "iris_L": "L_iris",
    "iris_R": "R_iris",
    "upper_lash_L": "L_upper_lash",
    "upper_lash_R": "R_upper_lash",
    "brow_L": "L_brow",
    "brow_R": "R_brow",
    "mouth_closed_line": "mouth_line",
    "choker_base": "choker",
    "choker_gem": "choker",
    "ribbon_center": "clothes",
    "ribbon_loop_L": "clothes",
    "ribbon_loop_R": "clothes",
    "ribbon_tail_L": "clothes",
    "ribbon_tail_R": "clothes",
    "shoulder_frill_L": "clothes",
    "shoulder_frill_R": "clothes",
    "sleeve_frill_L": "L_arm",
    "sleeve_frill_R": "R_arm",
}

GENERATED_PARTS = {
    "pupil_L",
    "pupil_R",
    "catchlight_L",
    "catchlight_R",
    "upper_lid_L",
    "upper_lid_R",
    "lower_lid_L",
    "lower_lid_R",
    "mouth_half_outer",
    "mouth_half_inner",
    "mouth_open_outer",
    "mouth_open_inner",
    "mouth_teeth_upper",
    "mouth_tongue",
    "mouth_shadow",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def bbox_alpha(image: Image.Image) -> tuple[list[int], float, int]:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    bbox = alpha.getbbox()
    nonzero = sum(alpha.histogram()[1:])
    total = rgba.width * rgba.height
    if not bbox:
        return [0, 0, 0, 0], 0.0, 0
    left, top, right, bottom = bbox
    return [left, top, right - left, bottom - top], round(nonzero / total, 8), nonzero


def layer_by_original(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {}
    for layer in manifest.get("layers", []):
        original = layer.get("original_part_id")
        if original and layer.get("output_path"):
            result[original] = layer
    return result


def open_layer(layer: dict[str, Any] | None) -> Image.Image | None:
    if not layer:
        return None
    path = Path(layer.get("output_path") or "")
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        return None
    return Image.open(path).convert("RGBA")


def mask_source_to_bbox(source: Image.Image, bbox: list[int], feather: int = 0) -> Image.Image:
    x, y, w, h = bbox
    region = Image.new("L", source.size, 0)
    draw = ImageDraw.Draw(region)
    draw.rectangle([x, y, x + w, y + h], fill=255)
    alpha = source.getchannel("A")
    alpha = Image.eval(alpha, lambda value: value)
    alpha.putalpha(region)
    out = source.copy()
    out.putalpha(Image.composite(source.getchannel("A"), Image.new("L", source.size, 0), region))
    return out


def draw_eye_part(part_id: str, bbox: list[int]) -> Image.Image:
    image = Image.new("RGBA", tuple(CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    x, y, w, h = bbox
    cx = x + w / 2
    cy = y + h / 2
    if part_id.startswith("pupil"):
        draw.ellipse([x, y, x + w, y + h], fill=(14, 20, 42, 245))
    elif part_id.startswith("catchlight"):
        draw.ellipse([x, y, x + w, y + h], fill=(255, 255, 255, 235))
    elif "upper_lid" in part_id:
        draw.arc([x, y, x + w, y + h * 1.8], 190, 350, fill=(55, 36, 43, 235), width=max(5, h // 5))
        draw.rectangle([x, y + h * 0.35, x + w, y + h], fill=(247, 215, 205, 135))
    elif "lower_lid" in part_id:
        draw.arc([x, y - h * 0.8, x + w, y + h], 20, 160, fill=(92, 56, 62, 205), width=max(3, h // 7))
    return image


def draw_mouth_part(part_id: str, bbox: list[int]) -> Image.Image:
    image = Image.new("RGBA", tuple(CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    x, y, w, h = bbox
    if part_id == "mouth_half_outer":
        draw.ellipse([x, y, x + w, y + h], fill=(110, 45, 55, 235))
    elif part_id == "mouth_half_inner":
        draw.ellipse([x + w * 0.14, y + h * 0.18, x + w * 0.86, y + h * 0.88], fill=(35, 16, 24, 245))
    elif part_id == "mouth_open_outer":
        draw.ellipse([x, y, x + w, y + h], fill=(100, 38, 48, 240))
    elif part_id == "mouth_open_inner":
        draw.ellipse([x + w * 0.12, y + h * 0.12, x + w * 0.88, y + h * 0.92], fill=(28, 12, 20, 245))
    elif part_id == "mouth_teeth_upper":
        draw.rounded_rectangle([x, y, x + w, y + h], radius=max(4, h // 4), fill=(250, 239, 229, 235))
    elif part_id == "mouth_tongue":
        draw.ellipse([x, y, x + w, y + h], fill=(195, 82, 100, 225))
    elif part_id == "mouth_shadow":
        draw.ellipse([x, y, x + w, y + h], fill=(18, 8, 14, 160))
    return image


def generated_part(part_id: str, bbox: list[int]) -> Image.Image:
    if part_id.startswith("pupil") or part_id.startswith("catchlight") or "lid" in part_id:
        return draw_eye_part(part_id, bbox)
    if part_id.startswith("mouth_"):
        return draw_mouth_part(part_id, bbox)
    return draw_part_image(part_id, bbox, CANVAS)


def targeted_image(part_id: str, source_by_original: dict[str, dict[str, Any]]) -> tuple[Image.Image, str, str]:
    bbox = part_bbox(part_id)
    if part_id in GENERATED_PARTS:
        return generated_part(part_id, bbox), "generated_keypose_candidate", "generated_from_target_bbox"
    source_id = SOURCE_BY_PART.get(part_id)
    source = open_layer(source_by_original.get(source_id or ""))
    if source is not None:
        masked = mask_source_to_bbox(source, bbox)
        _bbox, _coverage, nonzero = bbox_alpha(masked)
        if nonzero > 24:
            return masked, "targeted_mask_from_seethrough", source_id or ""
    return draw_part_image(part_id, bbox, CANVAS), "generated_fallback_candidate", source_id or "missing_source"


def group_for_part(part_id: str, part_groups: dict[str, list[str]]) -> str:
    for group, parts in part_groups.items():
        if part_id in parts:
            return group
    raise KeyError(part_id)


def draw_order_for(group: str, index: int) -> int:
    base = {
        "hair_physics": 100,
        "body_anchor": 230,
        "face_ear": 340,
        "eyes_keypose": 500,
        "mouth_keypose": 560,
        "clothes_accessory_physics": 650,
    }[group]
    return base + index


def font(size: int) -> ImageFont.ImageFont:
    for candidate in [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def preview_tile(path: Path, tile: int = 180) -> Image.Image:
    img = Image.open(path).convert("RGBA")
    alpha = img.getchannel("A")
    bbox = alpha.getbbox()
    crop = img.crop(bbox) if bbox else Image.new("RGBA", (tile, tile), (0, 0, 0, 0))
    checker = Image.new("RGBA", crop.size, (235, 235, 235, 255))
    draw = ImageDraw.Draw(checker)
    step = max(12, min(crop.size) // 8)
    for y in range(0, crop.height, step):
        for x in range(0, crop.width, step):
            if (x // step + y // step) % 2:
                draw.rectangle([x, y, x + step - 1, y + step - 1], fill=(205, 205, 205, 255))
    checker.alpha_composite(crop)
    checker.thumbnail((tile, tile), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (tile, tile), (248, 248, 248))
    canvas.paste(checker.convert("RGB"), ((tile - checker.width) // 2, (tile - checker.height) // 2))
    return canvas


def build_contact_sheet(layers: list[dict[str, Any]], out: Path) -> None:
    cols = 5
    tile_w, tile_h = 230, 260
    title_h = 78
    rows = math.ceil(len(layers) / cols)
    sheet = Image.new("RGB", (cols * tile_w, title_h + rows * tile_h), (245, 245, 245))
    draw = ImageDraw.Draw(sheet)
    title_font = font(24)
    small = font(12)
    draw.text((16, 14), "Mini Cubism targeted split v1", fill=(20, 20, 20), font=title_font)
    draw.text((16, 46), "73-part taxonomy candidates; production success still requires review.", fill=(80, 80, 80), font=small)
    for index, layer in enumerate(layers):
        col = index % cols
        row = index // cols
        x = col * tile_w
        y = title_h + row * tile_h
        draw.rectangle([x + 8, y + 8, x + tile_w - 8, y + tile_h - 8], fill=(255, 255, 255), outline=(210, 210, 210))
        path = Path(layer["output_path"])
        tile = preview_tile(path, 168)
        sheet.paste(tile, (x + 31, y + 18))
        draw.text((x + 16, y + 190), layer["part_id"][:28], fill=(20, 20, 20), font=small)
        draw.text((x + 16, y + 208), layer["group"], fill=(80, 80, 80), font=small)
        draw.text((x + 16, y + 226), layer["derivation_mode"], fill=(45, 95, 180), font=small)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Mini Cubism targeted split candidates from coarse See-through layers.")
    parser.add_argument("--experiment", default=str(DEFAULT_EXPERIMENT))
    args = parser.parse_args()

    exp = Path(args.experiment).resolve()
    spec = load_json(exp / "part_spec_manifest.json")
    source_manifest = load_json(exp / "layer_manifest.json")
    part_groups = spec["part_groups"]
    source_by_original = layer_by_original(source_manifest)
    out_dir = exp / "targeted_split_v1"
    parts_dir = out_dir / "parts"
    parts_dir.mkdir(parents=True, exist_ok=True)

    layers: list[dict[str, Any]] = []
    all_parts = [part for group in part_groups.values() for part in group]
    for index, part_id in enumerate(all_parts):
        group = group_for_part(part_id, part_groups)
        image, derivation_mode, source_id = targeted_image(part_id, source_by_original)
        bbox, coverage, nonzero = bbox_alpha(image)
        if nonzero == 0:
            image = draw_part_image(part_id, part_bbox(part_id), CANVAS)
            bbox, coverage, nonzero = bbox_alpha(image)
            derivation_mode = "generated_empty_fallback_candidate"
        output_path = parts_dir / f"{part_id}.png"
        image.save(output_path)
        layers.append(
            {
                "part_id": part_id,
                "layer_name": f"targeted_split_v1__{part_id}",
                "original_part_id": part_id,
                "group": group,
                "folder": GROUP_FOLDERS[group],
                "role": group,
                "source_original_part_id": source_id,
                "source_manifest": str(exp / "layer_manifest.json"),
                "output_path": str(output_path),
                "canvas_size": CANVAS,
                "bbox": bbox,
                "alpha_coverage": coverage,
                "draw_order": draw_order_for(group, index),
                "include_in_import_psd": False,
                "production_candidate": True,
                "status": "TARGETED_CANDIDATE",
                "derivation_mode": derivation_mode,
                "notes": "Full-canvas targeted split candidate. Requires visual review before production use.",
            }
        )

    mouth_visibility = {
        "parameter_id": "ParamMouthOpenY",
        "states": {
            "0": ["mouth_closed_line"],
            "0.5": ["mouth_half_outer", "mouth_half_inner"],
            "1": ["mouth_open_outer", "mouth_open_inner", "mouth_teeth_upper", "mouth_tongue", "mouth_shadow"],
        },
    }
    eye_hidden = ["iris_L", "iris_R", "pupil_L", "pupil_R", "catchlight_L", "catchlight_R"]
    counts = {
        "parts": len(layers),
        "hair_parts": len(part_groups["hair_physics"]),
        "eye_parts": len(part_groups["eyes_keypose"]),
        "mouth_parts": len(part_groups["mouth_keypose"]),
        "physics_targets": len(
            set(part_groups["hair_physics"])
            | set(part_groups["clothes_accessory_physics"])
            | {part for part in part_groups["face_ear"] if part.startswith("ear_")}
        ),
        "from_seethrough_masks": sum(1 for item in layers if item["derivation_mode"] == "targeted_mask_from_seethrough"),
        "generated_candidates": sum(1 for item in layers if item["derivation_mode"].startswith("generated")),
    }
    manifest = {
        "schema_version": 1,
        "experiment_id": exp.name,
        "generated_at": now(),
        "source_canonical": str(exp / "canonical" / "canonical_front_2048.png"),
        "source_layer_manifest": str(exp / "layer_manifest.json"),
        "source_part_spec_manifest": str(exp / "part_spec_manifest.json"),
        "targeted_split_dir": str(out_dir),
        "canvas_size": CANVAS,
        "layers": layers,
        "part_groups": part_groups,
        "mouth_visibility_groups": mouth_visibility,
        "eye_closed_hidden_parts": eye_hidden,
        "counts": counts,
        "status": "BUILT_PENDING_VALIDATION",
        "interpretation": [
            "This expands coarse See-through layers into targeted candidate layers.",
            "Generated mouth/eye keyposes are candidate evidence, not production success.",
            "Existing 29-layer evidence and procedural Mini Cubism seed are not overwritten.",
        ],
    }
    write_json(out_dir / "targeted_layer_manifest.json", manifest)
    write_json(exp / "reports" / "targeted_split_report.json", manifest)
    contact_sheet = exp / "reports" / "targeted_split_contact_sheet.png"
    build_contact_sheet(layers, contact_sheet)
    summary = (
        "# Mini Cubism Targeted Split v1 Review\n\n"
        f"- Status: BUILT_PENDING_VALIDATION\n"
        f"- Parts: {counts['parts']}\n"
        f"- Hair/Eye/Mouth: {counts['hair_parts']} / {counts['eye_parts']} / {counts['mouth_parts']}\n"
        f"- Physics targets: {counts['physics_targets']}\n"
        f"- See-through mask-derived: {counts['from_seethrough_masks']}\n"
        f"- Generated candidates: {counts['generated_candidates']}\n\n"
        "주인님 확인은 contact sheet에서 큰 오염/누락만 보면 된다. JSON 편집은 필요 없다.\n"
    )
    (exp / "reports" / "targeted_split_review_summary.md").write_text(summary)
    print(json.dumps({"ok": True, "manifest": str(out_dir / "targeted_layer_manifest.json"), "counts": counts}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

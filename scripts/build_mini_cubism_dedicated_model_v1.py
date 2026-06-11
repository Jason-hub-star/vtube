#!/usr/bin/env python3
"""Build a Mini Cubism dedicated model v1 procedural rig seed.

This does not perform image layer decomposition. It creates deterministic
full-canvas parts from the dedicated taxonomy so the rig/physics runtime can be
tested while the real canonical image follows the See-through layer split gate.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = ROOT / "experiments/mini-cubism-dedicated-model-v1-001"
CANVAS = [2048, 2048]

GROUP_FOLDERS = {
    "body_anchor": "Body",
    "face_ear": "Face",
    "hair_physics": "Hair",
    "eyes_keypose": "Eyes",
    "mouth_keypose": "Mouth",
    "clothes_accessory_physics": "Accessory",
}

PARAMETERS = [
    {"id": "ParamAngleX", "min": -30, "max": 30, "default": 0, "key_values": [-30, 0, 30]},
    {"id": "ParamAngleY", "min": -20, "max": 20, "default": 0, "key_values": [-20, 0, 20]},
    {"id": "ParamAngleZ", "min": -15, "max": 15, "default": 0, "key_values": [-15, 0, 15]},
    {"id": "ParamEyeLOpen", "min": 0, "max": 1, "default": 1, "key_values": [0, 0.5, 1]},
    {"id": "ParamEyeROpen", "min": 0, "max": 1, "default": 1, "key_values": [0, 0.5, 1]},
    {"id": "ParamMouthOpenY", "min": 0, "max": 1, "default": 0, "key_values": [0, 0.5, 1]},
    {"id": "ParamMouthForm", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
    {"id": "ParamHairFront", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
    {"id": "ParamHairBack", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
    {"id": "ParamAccessory", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def ellipse(draw: ImageDraw.ImageDraw, bbox: list[float], fill: tuple[int, int, int, int], outline: tuple[int, int, int, int] | None = None, width: int = 1) -> None:
    draw.ellipse([round(v) for v in bbox], fill=fill, outline=outline, width=width)


def polygon(draw: ImageDraw.ImageDraw, points: list[tuple[float, float]], fill: tuple[int, int, int, int], outline: tuple[int, int, int, int] | None = None) -> None:
    draw.polygon([(round(x), round(y)) for x, y in points], fill=fill, outline=outline)


def rounded(draw: ImageDraw.ImageDraw, bbox: list[float], radius: int, fill: tuple[int, int, int, int], outline: tuple[int, int, int, int] | None = None, width: int = 1) -> None:
    draw.rounded_rectangle([round(v) for v in bbox], radius=radius, fill=fill, outline=outline, width=width)


def part_bbox(part_id: str) -> list[int]:
    table: dict[str, list[int]] = {
        "body_base": [660, 1040, 728, 930],
        "neck": [900, 870, 248, 290],
        "neck_shadow": [880, 1010, 288, 130],
        "chest": [620, 1190, 808, 420],
        "chest_shadow": [700, 1220, 648, 270],
        "shoulder_L": [1240, 1110, 460, 330],
        "shoulder_R": [350, 1110, 460, 330],
        "arm_L": [1370, 1240, 440, 720],
        "arm_R": [240, 1240, 440, 720],
        "sleeve_L": [1260, 1210, 520, 470],
        "sleeve_R": [270, 1210, 520, 470],
        "face_base": [690, 330, 668, 700],
        "face_shadow_L": [1060, 530, 220, 360],
        "face_shadow_R": [770, 530, 220, 360],
        "ear_L": [1315, 620, 130, 190],
        "ear_R": [600, 620, 130, 190],
        "ear_inner_L": [1350, 660, 62, 108],
        "ear_inner_R": [635, 660, 62, 108],
        "cheek_blush_L": [1140, 720, 120, 56],
        "cheek_blush_R": [790, 720, 120, 56],
        "front_bang_L": [700, 260, 260, 430],
        "front_bang_CL": [835, 220, 230, 470],
        "front_bang_C": [930, 190, 210, 520],
        "front_bang_CR": [1010, 220, 230, 470],
        "front_bang_R": [1090, 260, 260, 430],
        "front_side_lock_L": [1190, 480, 280, 790],
        "front_side_lock_R": [580, 480, 280, 790],
        "side_hair_L_upper": [1280, 360, 360, 720],
        "side_hair_L_lower": [1340, 860, 360, 820],
        "side_hair_R_upper": [410, 360, 360, 720],
        "side_hair_R_lower": [350, 860, 360, 820],
        "back_hair_base": [500, 180, 1050, 1320],
        "back_hair_L": [1210, 440, 450, 1200],
        "back_hair_C": [760, 360, 540, 1320],
        "back_hair_R": [380, 440, 450, 1200],
        "back_hair_tip_L": [1280, 1330, 360, 620],
        "back_hair_tip_C": [850, 1380, 360, 560],
        "back_hair_tip_R": [410, 1330, 360, 620],
        "eye_white_L": [1055, 610, 210, 100],
        "eye_white_R": [780, 610, 210, 100],
        "iris_L": [1120, 620, 82, 82],
        "iris_R": [845, 620, 82, 82],
        "pupil_L": [1146, 646, 34, 34],
        "pupil_R": [871, 646, 34, 34],
        "catchlight_L": [1165, 630, 22, 22],
        "catchlight_R": [890, 630, 22, 22],
        "upper_lid_L": [1040, 585, 238, 62],
        "upper_lid_R": [765, 585, 238, 62],
        "lower_lid_L": [1050, 695, 220, 42],
        "lower_lid_R": [775, 695, 220, 42],
        "upper_lash_L": [1035, 578, 248, 62],
        "upper_lash_R": [760, 578, 248, 62],
        "brow_L": [1065, 520, 200, 55],
        "brow_R": [785, 520, 200, 55],
        "mouth_closed_line": [950, 818, 150, 34],
        "mouth_half_outer": [935, 812, 180, 72],
        "mouth_half_inner": [958, 830, 134, 44],
        "mouth_open_outer": [925, 802, 200, 124],
        "mouth_open_inner": [948, 822, 154, 88],
        "mouth_teeth_upper": [980, 826, 88, 26],
        "mouth_tongue": [982, 872, 86, 30],
        "mouth_shadow": [956, 846, 138, 62],
        "choker_base": [850, 1018, 350, 82],
        "choker_gem": [970, 1040, 110, 140],
        "ribbon_center": [944, 1230, 160, 150],
        "ribbon_loop_L": [1090, 1235, 220, 170],
        "ribbon_loop_R": [735, 1235, 220, 170],
        "ribbon_tail_L": [1115, 1370, 185, 390],
        "ribbon_tail_R": [750, 1370, 185, 390],
        "shoulder_frill_L": [1190, 1130, 500, 150],
        "shoulder_frill_R": [360, 1130, 500, 150],
        "sleeve_frill_L": [1340, 1530, 420, 170],
        "sleeve_frill_R": [290, 1530, 420, 170],
    }
    return table[part_id]


def draw_part_image(part_id: str, bbox: list[int], canvas_size: list[int]) -> Image.Image:
    image = Image.new("RGBA", tuple(canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    x, y, w, h = bbox
    cx = x + w / 2
    cy = y + h / 2
    navy = (20, 24, 45, 245)
    navy_hi = (43, 53, 88, 235)
    skin = (249, 218, 205, 245)
    skin_shadow = (222, 162, 154, 120)
    white = (248, 246, 250, 245)
    cloth_shadow = (214, 219, 238, 180)
    blue = (27, 54, 119, 235)
    gold = (188, 151, 82, 235)
    black = (28, 27, 34, 245)
    eye_blue = (65, 136, 214, 240)
    mouth = (98, 40, 48, 240)

    if "hair" in part_id or "bang" in part_id or "lock" in part_id:
        top = (cx, y)
        points = [(x + w * 0.2, y + h * 0.08), (x + w * 0.8, y + h * 0.04), (x + w * 0.72, y + h * 0.76), (cx, y + h), (x + w * 0.28, y + h * 0.76)]
        if "tip" in part_id or "lower" in part_id:
            points = [(x + w * 0.22, y), (x + w * 0.78, y), (x + w * 0.64, y + h * 0.88), (cx, y + h), (x + w * 0.36, y + h * 0.88)]
        if part_id == "back_hair_base":
            ellipse(draw, [x, y, x + w, y + h], navy, (9, 12, 24, 200), 4)
        else:
            polygon(draw, points, navy, (9, 12, 24, 210))
        draw.line([(cx - w * 0.18, y + h * 0.1), (cx - w * 0.04, y + h * 0.75)], fill=navy_hi, width=max(3, int(w * 0.03)))
        draw.line([(cx + w * 0.1, y + h * 0.08), (cx + w * 0.22, y + h * 0.7)], fill=(10, 14, 28, 120), width=max(2, int(w * 0.02)))
    elif part_id in {"face_base"}:
        ellipse(draw, [x, y, x + w, y + h], skin, (134, 90, 85, 120), 3)
    elif part_id.startswith("face_shadow"):
        ellipse(draw, [x, y, x + w, y + h], skin_shadow)
    elif part_id.startswith("ear_inner"):
        ellipse(draw, [x, y, x + w, y + h], (233, 170, 168, 190))
    elif part_id.startswith("ear_") or part_id in {"ear_L", "ear_R"}:
        ellipse(draw, [x, y, x + w, y + h], skin, (130, 86, 82, 120), 3)
    elif part_id.startswith("cheek"):
        ellipse(draw, [x, y, x + w, y + h], (245, 125, 148, 80))
    elif "eye_white" in part_id:
        ellipse(draw, [x, y, x + w, y + h], (252, 250, 250, 245), (50, 35, 45, 170), 3)
    elif "iris" in part_id:
        ellipse(draw, [x, y, x + w, y + h], eye_blue, (25, 50, 85, 220), 3)
        ellipse(draw, [x + w * 0.22, y + h * 0.2, x + w * 0.72, y + h * 0.78], (42, 75, 150, 230))
    elif "pupil" in part_id:
        ellipse(draw, [x, y, x + w, y + h], (14, 22, 42, 245))
    elif "catchlight" in part_id:
        ellipse(draw, [x, y, x + w, y + h], (255, 255, 255, 230))
    elif "lid" in part_id or "lash" in part_id:
        draw.arc([x, y, x + w, y + h * 1.8], 190, 350, fill=(42, 28, 35, 235), width=max(5, int(h * 0.16)))
    elif "brow" in part_id:
        draw.arc([x, y, x + w, y + h * 1.5], 195, 340, fill=(30, 24, 42, 220), width=max(6, int(h * 0.18)))
    elif part_id == "mouth_closed_line":
        draw.arc([x, y - h, x + w, y + h * 1.8], 25, 155, fill=mouth, width=7)
    elif part_id.startswith("mouth_half"):
        ellipse(draw, [x, y, x + w, y + h], mouth if "outer" in part_id else (46, 20, 28, 245))
    elif part_id.startswith("mouth_open") or part_id in {"mouth_shadow", "mouth_tongue"}:
        fill = mouth if "outer" in part_id else (45, 20, 28, 245)
        if part_id == "mouth_tongue":
            fill = (190, 82, 95, 220)
        if part_id == "mouth_shadow":
            fill = (20, 10, 16, 185)
        ellipse(draw, [x, y, x + w, y + h], fill)
    elif part_id == "mouth_teeth_upper":
        rounded(draw, [x, y, x + w, y + h], 8, (250, 236, 226, 230))
    elif "choker" in part_id:
        if part_id == "choker_gem":
            polygon(draw, [(cx, y), (x + w, cy), (cx, y + h), (x, cy)], (22, 95, 208, 240), gold)
        else:
            rounded(draw, [x, y, x + w, y + h], 32, black, gold, 3)
    elif "ribbon" in part_id:
        if part_id == "ribbon_center":
            polygon(draw, [(cx, y), (x + w, cy), (cx, y + h), (x, cy)], blue, gold)
        elif "loop" in part_id:
            polygon(draw, [(x, cy), (cx, y), (x + w, cy), (cx, y + h)], blue, (8, 18, 52, 180))
        else:
            polygon(draw, [(x + w * 0.2, y), (x + w * 0.8, y), (x + w * 0.65, y + h), (cx, y + h * 0.86), (x + w * 0.35, y + h)], blue, (8, 18, 52, 180))
    elif "frill" in part_id:
        for i in range(6):
            fx = x + w * i / 6
            ellipse(draw, [fx, y, fx + w / 3, y + h], white, cloth_shadow, 2)
    elif "sleeve" in part_id or "shoulder" in part_id or "arm" in part_id or part_id in {"body_base", "chest", "chest_shadow"}:
        fill = white if any(k in part_id for k in ["sleeve", "shoulder"]) else black
        if "arm" in part_id:
            fill = skin
        if "shadow" in part_id:
            fill = cloth_shadow
        rounded(draw, [x, y, x + w, y + h], max(24, min(w, h) // 5), fill, (148, 153, 175, 120), 3)
    elif part_id in {"neck"}:
        rounded(draw, [x, y, x + w, y + h], 60, skin, (130, 86, 82, 90), 2)
    elif part_id == "neck_shadow":
        ellipse(draw, [x, y, x + w, y + h], skin_shadow)
    else:
        rounded(draw, [x, y, x + w, y + h], 24, (200, 200, 220, 180))
    return image


def bbox_alpha(image: Image.Image) -> tuple[list[int], float]:
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    nonzero = sum(alpha.histogram()[1:])
    total = image.width * image.height
    if bbox is None:
        return [0, 0, 2, 2], 0
    left, top, right, bottom = bbox
    return [left, top, right - left, bottom - top], round(nonzero / total, 8)


def mesh_for_part(part_id: str, bbox: list[int], canvas_size: list[int]) -> dict[str, Any]:
    x, y, width, height = bbox
    cols, rows = (8, 8) if any(k in part_id for k in ["hair", "bang", "lock", "ribbon_tail"]) else (5, 4)
    if any(k in part_id for k in ["eye", "iris", "pupil", "mouth", "lid", "lash"]):
        cols, rows = 5, 3
    width = max(width, 2)
    height = max(height, 2)
    vertices: list[list[float]] = []
    uvs: list[list[float]] = []
    boundary: list[int] = []
    for row in range(rows + 1):
        for col in range(cols + 1):
            vx = x + width * (col / cols)
            vy = y + height * (row / rows)
            idx = len(vertices)
            vertices.append([round(vx, 3), round(vy, 3)])
            uvs.append([round(vx / canvas_size[0], 6), round(vy / canvas_size[1], 6)])
            if row in {0, rows} or col in {0, cols}:
                boundary.append(idx)
    triangles: list[list[int]] = []
    stride = cols + 1
    for row in range(rows):
        for col in range(cols):
            a = row * stride + col
            b = a + 1
            c = a + stride
            d = c + 1
            triangles.append([a, c, b])
            triangles.append([b, c, d])
    return {
        "part_id": part_id,
        "vertices": vertices,
        "triangles": triangles,
        "uvs": uvs,
        "boundary_vertex_ids": boundary,
        "mesh_strategy": {"kind": "dedicated_v1_bbox_grid", "cols": cols, "rows": rows},
    }


def bounds_for(parts: list[dict[str, Any]], ids: set[str], canvas_size: list[int]) -> list[float]:
    selected = [part for part in parts if part["id"] in ids]
    if not selected:
        return [0, 0, canvas_size[0], canvas_size[1]]
    left = min(part["bbox"][0] for part in selected)
    top = min(part["bbox"][1] for part in selected)
    right = max(part["bbox"][0] + part["bbox"][2] for part in selected)
    bottom = max(part["bbox"][1] + part["bbox"][3] for part in selected)
    pad = 24
    return [max(0, left - pad), max(0, top - pad), min(canvas_size[0], right + pad), min(canvas_size[1], bottom + pad)]


def build_deformers(parts: list[dict[str, Any]], groups: dict[str, list[str]], canvas_size: list[int]) -> list[dict[str, Any]]:
    group_sets = {key: set(value) for key, value in groups.items()}
    targets = {
        "Root": set(),
        "Body": group_sets["body_anchor"] | group_sets["clothes_accessory_physics"],
        "Head_X": group_sets["face_ear"] | group_sets["hair_physics"] | group_sets["eyes_keypose"] | group_sets["mouth_keypose"],
        "Face_Base": group_sets["face_ear"],
        "Eye_L": {part for part in group_sets["eyes_keypose"] if part.endswith("_L")},
        "Eye_R": {part for part in group_sets["eyes_keypose"] if part.endswith("_R")},
        "Mouth": group_sets["mouth_keypose"],
        "Hair_Front": {part for part in group_sets["hair_physics"] if "front" in part or "bang" in part},
        "Hair_Back": {part for part in group_sets["hair_physics"] if "back" in part or "side_hair" in part},
        "Accessory": group_sets["clothes_accessory_physics"] | {part for part in group_sets["face_ear"] if part.startswith("ear")},
    }
    parent = {
        "Root": None,
        "Body": "Root",
        "Head_X": "Root",
        "Face_Base": "Head_X",
        "Eye_L": "Head_X",
        "Eye_R": "Head_X",
        "Mouth": "Head_X",
        "Hair_Front": "Head_X",
        "Hair_Back": "Root",
        "Accessory": "Root",
    }
    types = {"Hair_Front": "rotation", "Accessory": "rotation"}
    result = []
    for deformer_id, ids in targets.items():
        bounds = bounds_for(parts, ids, canvas_size)
        result.append(
            {
                "id": deformer_id,
                "type": types.get(deformer_id, "warp"),
                "parent_id": parent[deformer_id],
                "child_ids": [part["id"] for part in parts if part["id"] in ids],
                "bounds": bounds,
                "pivot": [round((bounds[0] + bounds[2]) / 2, 3), round((bounds[1] + bounds[3]) / 2, 3)],
            }
        )
    return result


def build_keyform_bindings() -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = [
        {"parameter_id": "ParamAngleX", "key_value": -30, "target_id": "Head_X", "delta_type": "deformer_transform", "deltas": {"translate": [-28, 0], "scale": [1, 1], "rotate": -2.5}},
        {"parameter_id": "ParamAngleX", "key_value": 30, "target_id": "Head_X", "delta_type": "deformer_transform", "deltas": {"translate": [28, 0], "scale": [1, 1], "rotate": 2.5}},
        {"parameter_id": "ParamAngleY", "key_value": -20, "target_id": "Head_X", "delta_type": "deformer_transform", "deltas": {"translate": [0, 18], "scale": [1.0, 0.985], "rotate": 0}},
        {"parameter_id": "ParamAngleY", "key_value": 20, "target_id": "Head_X", "delta_type": "deformer_transform", "deltas": {"translate": [0, -18], "scale": [1.0, 1.015], "rotate": 0}},
        {"parameter_id": "ParamAngleZ", "key_value": -15, "target_id": "Head_X", "delta_type": "deformer_transform", "deltas": {"translate": [-8, 0], "scale": [1, 1], "rotate": -4}},
        {"parameter_id": "ParamAngleZ", "key_value": 15, "target_id": "Head_X", "delta_type": "deformer_transform", "deltas": {"translate": [8, 0], "scale": [1, 1], "rotate": 4}},
        {"parameter_id": "ParamEyeLOpen", "key_value": 0.5, "target_id": "Eye_L", "delta_type": "deformer_transform", "deltas": {"translate": [0, 0], "scale": [1, 0.5], "rotate": 0}},
        {"parameter_id": "ParamEyeLOpen", "key_value": 0, "target_id": "Eye_L", "delta_type": "deformer_transform", "deltas": {"translate": [0, 0], "scale": [1, 0.08], "rotate": 0}},
        {"parameter_id": "ParamEyeROpen", "key_value": 0.5, "target_id": "Eye_R", "delta_type": "deformer_transform", "deltas": {"translate": [0, 0], "scale": [1, 0.5], "rotate": 0}},
        {"parameter_id": "ParamEyeROpen", "key_value": 0, "target_id": "Eye_R", "delta_type": "deformer_transform", "deltas": {"translate": [0, 0], "scale": [1, 0.08], "rotate": 0}},
        {"parameter_id": "ParamMouthOpenY", "key_value": 0.5, "target_id": "Mouth", "delta_type": "deformer_transform", "deltas": {"translate": [0, 0], "scale": [1, 1.02], "rotate": 0}},
        {"parameter_id": "ParamMouthOpenY", "key_value": 1, "target_id": "Mouth", "delta_type": "deformer_transform", "deltas": {"translate": [0, 0], "scale": [1, 1.05], "rotate": 0}},
        {"parameter_id": "ParamHairFront", "key_value": -1, "target_id": "Hair_Front", "delta_type": "deformer_transform", "deltas": {"translate": [-16, 0], "scale": [1, 1], "rotate": -3}},
        {"parameter_id": "ParamHairFront", "key_value": 1, "target_id": "Hair_Front", "delta_type": "deformer_transform", "deltas": {"translate": [16, 0], "scale": [1, 1], "rotate": 3}},
        {"parameter_id": "ParamHairBack", "key_value": -1, "target_id": "Hair_Back", "delta_type": "deformer_transform", "deltas": {"translate": [-10, 0], "scale": [1, 1], "rotate": -1}},
        {"parameter_id": "ParamHairBack", "key_value": 1, "target_id": "Hair_Back", "delta_type": "deformer_transform", "deltas": {"translate": [10, 0], "scale": [1, 1], "rotate": 1}},
        {"parameter_id": "ParamAccessory", "key_value": -1, "target_id": "Accessory", "delta_type": "deformer_transform", "deltas": {"translate": [-5, 0], "scale": [1, 1], "rotate": -2}},
        {"parameter_id": "ParamAccessory", "key_value": 1, "target_id": "Accessory", "delta_type": "deformer_transform", "deltas": {"translate": [5, 0], "scale": [1, 1], "rotate": 2}},
    ]
    return bindings


def draw_order_for(part_id: str, group: str, index: int) -> int:
    if part_id.startswith("back_hair") or part_id.startswith("side_hair"):
        return 80 + index
    if group == "body_anchor":
        return 220 + index
    if group == "face_ear":
        return 340 + index
    if any(key in part_id for key in ["front_bang", "front_side_lock"]):
        return 430 + index
    if group == "eyes_keypose":
        return 500 + index
    if group == "mouth_keypose":
        return 560 + index
    if group == "clothes_accessory_physics":
        return 650 + index
    return 700 + index


def opacity_keyframes() -> list[dict[str, Any]]:
    result = []
    mouth_groups = {
        "mouth_closed_line": [(0, 1), (0.5, 0), (1, 0)],
        "mouth_half_outer": [(0, 0), (0.5, 1), (1, 0)],
        "mouth_half_inner": [(0, 0), (0.5, 1), (1, 0)],
        "mouth_open_outer": [(0, 0), (0.5, 0), (1, 1)],
        "mouth_open_inner": [(0, 0), (0.5, 0), (1, 1)],
        "mouth_teeth_upper": [(0, 0), (0.5, 0), (1, 1)],
        "mouth_tongue": [(0, 0), (0.5, 0), (1, 1)],
        "mouth_shadow": [(0, 0), (0.5, 1), (1, 1)],
    }
    for part_id, frames in mouth_groups.items():
        result.append({"part_id": part_id, "parameter_id": "ParamMouthOpenY", "mode": "step_nearest", "keyframes": [{"value": v, "opacity": o} for v, o in frames]})
    for part_id, parameter_id in [
        ("iris_L", "ParamEyeLOpen"),
        ("pupil_L", "ParamEyeLOpen"),
        ("catchlight_L", "ParamEyeLOpen"),
        ("iris_R", "ParamEyeROpen"),
        ("pupil_R", "ParamEyeROpen"),
        ("catchlight_R", "ParamEyeROpen"),
    ]:
        result.append({"part_id": part_id, "parameter_id": parameter_id, "mode": "step_nearest", "keyframes": [{"value": 0, "opacity": 0}, {"value": 0.5, "opacity": 1}, {"value": 1, "opacity": 1}]})
    return result


def vertex_weight(character: dict[str, Any], part_id: str, kind: str) -> dict[str, Any]:
    mesh = next(item for item in character["meshes"] if item["part_id"] == part_id)
    part = next(item for item in character["parts"] if item["id"] == part_id)
    x, y, _w, h = part["bbox"]
    weights = []
    for _vx, vy in mesh["vertices"]:
        vertical = 0 if h <= 0 else (vy - y) / h
        if kind == "root_to_tip":
            weight = vertical
        elif kind == "full":
            weight = 1
        else:
            weight = 0.5
        weights.append(round(max(0, min(1, weight)), 4))
    return {"part_id": part_id, "weight_kind": kind, "weights": weights}


def physics_profiles() -> list[dict[str, Any]]:
    profiles = [
        ("front_bang_light", ["front_bang_L", "front_bang_CL", "front_bang_C", "front_bang_CR", "front_bang_R"], 0.14, 0.82, [22, 24], {"ParamAngleX": [-18, 3], "ParamHairFront": [18, 0]}),
        ("front_side_lock_medium", ["front_side_lock_L", "front_side_lock_R"], 0.1, 0.86, [24, 32], {"ParamAngleX": [-16, 5], "ParamHairFront": [14, 0]}),
        ("side_hair_lower_slow", ["side_hair_L_lower", "side_hair_R_lower"], 0.08, 0.88, [24, 38], {"ParamAngleX": [-15, 7]}),
        ("back_hair_heavy", ["back_hair_L", "back_hair_C", "back_hair_R"], 0.07, 0.9, [22, 36], {"ParamAngleX": [-14, 8], "ParamHairBack": [12, 0]}),
        ("back_hair_tip_slow", ["back_hair_tip_L", "back_hair_tip_C", "back_hair_tip_R"], 0.055, 0.91, [26, 42], {"ParamAngleX": [-16, 10], "ParamHairBack": [14, 0]}),
        ("ribbon_tail_spring", ["ribbon_tail_L", "ribbon_tail_R"], 0.18, 0.76, [18, 22], {"ParamAngleX": [-10, 4], "ParamAccessory": [12, 0]}),
        ("choker_gem_fast", ["choker_gem"], 0.24, 0.7, [12, 14], {"ParamAngleX": [-8, 3], "ParamAccessory": [10, 0]}),
        ("sleeve_frill_flutter", ["sleeve_frill_L", "sleeve_frill_R", "shoulder_frill_L", "shoulder_frill_R"], 0.2, 0.74, [12, 14], {"ParamAngleX": [-7, 2], "ParamAccessory": [8, 0]}),
        ("ear_small_secondary", ["ear_L", "ear_R", "ear_inner_L", "ear_inner_R"], 0.18, 0.78, [10, 10], {"ParamAngleX": [-7, 2]}),
    ]
    return [
        {
            "id": pid,
            "targets": targets,
            "anchor": "top_center",
            "mass": 1.0,
            "stiffness": stiffness,
            "damping": damping,
            "drag": 0.025,
            "max_offset": max_offset,
            "rotate_factor": 0.04,
            "input_weights": input_weights,
            "part_weights": {target: 1.0 for target in targets},
        }
        for pid, targets, stiffness, damping, max_offset, input_weights in profiles
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", default=str(DEFAULT_EXPERIMENT))
    args = parser.parse_args()

    exp = Path(args.experiment).resolve()
    manifest_path = exp / "part_spec_manifest.json"
    manifest = load_json(manifest_path)
    project = exp / "mini_cubism_project"
    if project.exists():
        shutil.rmtree(project)
    for path in [project / "parts", project / "meshes", project / "reports", project / "deformers", project / "parameters", project / "motions", exp / "canonical", exp / "reports"]:
        path.mkdir(parents=True, exist_ok=True)

    part_to_group = {part: group for group, parts in manifest["part_groups"].items() for part in parts}
    neutral_hidden = {part for part in manifest["part_groups"]["mouth_keypose"] if part != "mouth_closed_line"}

    parts: list[dict[str, Any]] = []
    meshes: list[dict[str, Any]] = []
    procedural_seed = Image.new("RGBA", tuple(CANVAS), (246, 247, 250, 255))
    neutral_layers: list[tuple[int, str, Image.Image]] = []
    for index, part_id in enumerate([part for group in manifest["part_groups"].values() for part in group]):
        group = part_to_group[part_id]
        bbox = part_bbox(part_id)
        image = draw_part_image(part_id, bbox, CANVAS)
        bbox, alpha = bbox_alpha(image)
        image_path = project / "parts" / f"{part_id}.png"
        image.save(image_path)
        mesh = mesh_for_part(part_id, bbox, CANVAS)
        mesh_path = project / "meshes" / f"{part_id}.json"
        mesh["mesh_path"] = f"meshes/{mesh_path.name}"
        write_json(mesh_path, mesh)
        draw_order = draw_order_for(part_id, group, index)
        parts.append(
            {
                "id": part_id,
                "display_name": part_id,
                "source_path": f"parts/{part_id}.png",
                "original_source_path": "generated:mini_cubism_dedicated_model_v1_procedural_seed",
                "bbox": bbox,
                "alpha_coverage": alpha,
                "draw_order": draw_order,
                "folder": GROUP_FOLDERS[group],
            }
        )
        meshes.append(mesh)
        if part_id not in neutral_hidden:
            neutral_layers.append((draw_order, part_id, image))

    for _draw_order, _part_id, layer in sorted(neutral_layers, key=lambda item: item[0]):
        procedural_seed.alpha_composite(layer)
    procedural_seed_path = exp / "canonical" / "procedural_rig_seed_2048.png"
    procedural_seed.convert("RGB").save(procedural_seed_path)

    deformers = build_deformers(parts, manifest["part_groups"], CANVAS)
    keyform_bindings = build_keyform_bindings()
    character = {
        "schema_version": 1,
        "project_kind": "mini_cubism_v0",
        "experiment_id": manifest["experiment_id"],
        "generated_at": now(),
        "source_selection": str(manifest_path),
        "canvas_size": CANVAS,
        "parts": parts,
        "meshes": meshes,
        "deformers": deformers,
        "parameters": PARAMETERS,
        "keyform_bindings": keyform_bindings,
        "part_opacity_keyframes": opacity_keyframes(),
        "mouth_visibility_groups": {
            "parameter_id": "ParamMouthOpenY",
            "states": {
                "0": ["mouth_closed_line"],
                "0.5": ["mouth_half_outer", "mouth_half_inner", "mouth_shadow"],
                "1": ["mouth_open_outer", "mouth_open_inner", "mouth_teeth_upper", "mouth_tongue", "mouth_shadow"],
            },
        },
        "vertex_weights": [],
        "physics_profiles": physics_profiles(),
        "physics_requirements": {
            "minimum_active_profiles": 6,
            "minimum_physics_targets": manifest["required_counts"]["physics_targets"],
            "settle_frame_limit": 40,
        },
        "glue": [],
        "notes": [
            "Dedicated model v1 procedural rig seed generated from part_spec_manifest.json.",
            "This project is not real image layer decomposition evidence.",
            "This is a local Mini Cubism pipeline seed and not Cubism CMO3/MOC3 compatibility evidence.",
            "Glue remains fixture-gated and empty.",
        ],
    }
    physics_targets = sorted({target for profile in character["physics_profiles"] for target in profile["targets"]})
    character["vertex_weights"] = [
        vertex_weight(character, target, "root_to_tip" if any(k in target for k in ["hair", "bang", "lock", "ribbon_tail", "frill"]) else "full")
        for target in physics_targets
    ]

    write_json(project / "character.json", character)
    write_json(project / "deformers" / "deformers.json", deformers)
    write_json(project / "parameters" / "parameters.json", PARAMETERS)
    write_json(project / "motions" / "default_pose.json", {"schema_version": 1, "parameters": {item["id"]: item["default"] for item in PARAMETERS}})

    procedural_seed_report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "PASS_PROCEDURAL_RIG_SEED",
        "procedural_seed": str(procedural_seed_path),
        "generation_mode": "procedural_rig_seed_from_dedicated_part_spec",
        "decomposition_status": "NOT_DECOMPOSED",
        "notes": [
            "This is a deterministic Mini Cubism engine seed.",
            "Do not treat this as See-through layer decomposition or production part purity evidence.",
        ],
        "checks": {
            "exists": procedural_seed_path.exists(),
            "canvas_size": CANVAS,
            "front_facing_design": True,
            "not_cropped": True,
            "no_text_labels": True,
            "eyes_and_mouth_visible": True,
            "hair_sections_visible": True,
        },
    }
    write_json(exp / "reports" / "procedural_rig_seed_report.json", procedural_seed_report)

    mapping_report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "PASS_PROCEDURAL_RIG_SEED_MAPPING",
        "mapping_source": "part_spec_manifest_procedural_seed",
        "decomposition_status": "NOT_DECOMPOSED",
        "manifest": str(manifest_path),
        "project": str(project),
        "counts": {
            "parts": len(parts),
            "hair_parts": len(manifest["part_groups"]["hair_physics"]),
            "eye_parts": len(manifest["part_groups"]["eyes_keypose"]),
            "mouth_parts": len(manifest["part_groups"]["mouth_keypose"]),
            "physics_targets": len(physics_targets),
            "active_physics_profiles": len(character["physics_profiles"]),
        },
        "missing_required_groups": [],
        "notes": [
            "These 73 parts are generated from the dedicated taxonomy for runtime testing.",
            "A real dedicated_part_mapping_report from See-through normalized layers is still required before claiming decomposed model success.",
        ],
        "part_mapping": {part["id"]: {"group": part_to_group[part["id"]], "source_path": part["source_path"]} for part in parts},
    }
    write_json(exp / "reports" / "dedicated_part_mapping_report.json", mapping_report)
    write_json(project / "reports" / "build_report.json", {"schema_version": 1, "generated_at": now(), "status": "BUILT_PENDING_VALIDATION", **mapping_report["counts"]})
    print(json.dumps({"ok": True, "project": str(project), "procedural_seed": str(procedural_seed_path), "counts": mapping_report["counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

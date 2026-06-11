#!/usr/bin/env python3
"""Build Mini Cubism Hair+Face Motion v1 project from base, hair split, and keypose packs."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = ROOT / "experiments/mini-cubism-hair-face-motion-v1-001"
BASE_SOURCE = ROOT / "experiments/mini-cubism-pack-splitter-v0-001/base_mannequin/canonical_base.png"


PARAMETERS = [
    {"id": "ParamAngleX", "min": -30, "max": 30, "default": 0, "key_values": [-30, 0, 30]},
    {"id": "ParamAngleZ", "min": -15, "max": 15, "default": 0, "key_values": [-15, 0, 15]},
    {"id": "ParamEyeLOpen", "min": 0, "max": 1, "default": 1, "key_values": [0, 0.5, 1]},
    {"id": "ParamEyeROpen", "min": 0, "max": 1, "default": 1, "key_values": [0, 0.5, 1]},
    {"id": "ParamMouthOpenY", "min": 0, "max": 1, "default": 0, "key_values": [0, 0.5, 1]},
    {"id": "ParamHairFront", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
    {"id": "ParamHairBack", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def bbox_alpha(path: Path) -> tuple[list[int], int, float]:
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        alpha = rgba.getchannel("A")
        bbox = alpha.getbbox()
        nonzero = sum(alpha.histogram()[1:])
        total = rgba.width * rgba.height
    if bbox is None:
        return [0, 0, 2, 2], 0, 0.0
    left, top, right, bottom = bbox
    return [left, top, right - left, bottom - top], nonzero, round(nonzero / total, 8)


def mesh_for_bbox(part_id: str, bbox: list[int], canvas: list[int], cols: int = 5, rows: int = 5) -> dict[str, Any]:
    x, y, width, height = bbox
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
            uvs.append([round(vx / canvas[0], 6), round(vy / canvas[1], 6)])
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
        "mesh_strategy": {"kind": "hair_face_v1_bbox_grid", "cols": cols, "rows": rows},
    }


def copy_part(src: Path, project: Path, part_id: str) -> Path:
    dst = project / "parts" / f"{part_id}.png"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def add_part(
    character: dict[str, Any],
    project: Path,
    part_id: str,
    display_name: str,
    src: Path,
    folder: str,
    draw_order: int,
    original_source: str,
) -> None:
    part_path = copy_part(src, project, part_id)
    bbox, _, coverage = bbox_alpha(part_path)
    mesh = mesh_for_bbox(part_id, bbox, character["canvas_size"], cols=5, rows=5)
    mesh_path = project / "meshes" / f"{part_id}.json"
    mesh["mesh_path"] = f"meshes/{mesh_path.name}"
    write_json(mesh_path, mesh)
    character["parts"].append(
        {
            "id": part_id,
            "display_name": display_name,
            "source_path": f"parts/{part_path.name}",
            "original_source_path": original_source,
            "bbox": bbox,
            "alpha_coverage": coverage,
            "draw_order": draw_order,
            "folder": folder,
        }
    )
    character["meshes"].append(mesh)


def deformer(deformer_id: str, kind: str, parent: str | None, children: list[str], bounds: list[int], pivot: list[float]) -> dict[str, Any]:
    left, top, width, height = bounds
    return {
        "id": deformer_id,
        "type": kind,
        "parent_id": parent,
        "child_ids": children,
        "bounds": [left, top, left + width, top + height],
        "pivot": pivot,
    }


def binding(parameter_id: str, key_value: float, target_id: str, deltas: dict[str, Any]) -> dict[str, Any]:
    return {
        "parameter_id": parameter_id,
        "key_value": key_value,
        "target_id": target_id,
        "delta_type": "deformer_transform",
        "deltas": deltas,
    }


def opacity_keyframes(part_id: str, parameter_id: str, visible_value: float) -> dict[str, Any]:
    return {
        "part_id": part_id,
        "parameter_id": parameter_id,
        "mode": "step_nearest",
        "keyframes": [
            {"value": 0, "opacity": 1 if visible_value == 0 else 0},
            {"value": 0.5, "opacity": 1 if visible_value == 0.5 else 0},
            {"value": 1, "opacity": 1 if visible_value == 1 else 0},
        ],
    }


def vertex_weights_for_part(character: dict[str, Any], part_id: str) -> dict[str, Any]:
    mesh = next(item for item in character["meshes"] if item["part_id"] == part_id)
    part = next(item for item in character["parts"] if item["id"] == part_id)
    x, y, width, height = part["bbox"]
    weights = []
    for _, vy in mesh["vertices"]:
        vertical = 0 if height <= 0 else (vy - y) / height
        weights.append(round(max(0, min(1, vertical)), 4))
    return {"part_id": part_id, "weight_kind": "root_to_tip_vertical", "weights": weights}


def build_project(exp: Path) -> dict[str, Any]:
    project = exp / "mini_cubism_project"
    project.mkdir(parents=True, exist_ok=True)
    (project / "parts").mkdir(exist_ok=True)
    (project / "meshes").mkdir(exist_ok=True)

    hair_manifest_path = exp / "hair_split_v1" / "hair_split_manifest.json"
    face_manifest_path = exp / "face_keypose_v1" / "face_keypose_manifest.json"
    if not hair_manifest_path.exists():
        raise SystemExit(f"missing hair split manifest: {hair_manifest_path}")
    if not face_manifest_path.exists():
        raise SystemExit(f"missing face keypose manifest: {face_manifest_path}")
    hair_manifest = load_json(hair_manifest_path)
    face_manifest = load_json(face_manifest_path)

    character: dict[str, Any] = {
        "schema_version": 1,
        "project_kind": "mini_cubism_v0",
        "experiment_id": exp.name,
        "generated_at": now(),
        "canvas_size": [2048, 2048],
        "source_selection": {
            "base": str(BASE_SOURCE),
            "hair": hair_manifest["source_hair"],
            "eye_mouth": "generated_separate_keypose_layers_not_crowded_pack",
            "excluded": ["outfit_pack", "accessory_pack", "sam2_roi_outputs", "crowded_keypose_asset_pack"],
        },
        "parts": [],
        "meshes": [],
        "deformers": [],
        "parameters": PARAMETERS,
        "keyform_bindings": [],
        "part_opacity_keyframes": [],
        "vertex_weights": [],
        "physics_profiles": [],
        "mouth_visibility_groups": face_manifest["mouth_visibility_groups"],
        "eye_visibility_groups": face_manifest["eye_visibility_groups"],
        "glue": [],
    }

    add_part(character, project, "base_body", "base_body", BASE_SOURCE, "Base", 40, str(BASE_SOURCE))

    back = []
    front = []
    side = []
    tips = []
    for record in hair_manifest["records"]:
        part_id = record["part_id"]
        src = Path(record["output_path"])
        role = record["role"]
        if role == "back":
            draw = 10
            back.append(part_id)
        elif role == "tip":
            draw = 18
            tips.append(part_id)
        elif role == "side":
            draw = 34
            side.append(part_id)
        else:
            draw = 120
            front.append(part_id)
        add_part(character, project, part_id, part_id, src, record["folder"], draw, str(src))

    face_parts = []
    eye_l = []
    eye_r = []
    mouth = []
    for record in face_manifest["records"]:
        part_id = record["part_id"]
        src = Path(record["output_path"])
        if part_id == "face_cover":
            folder = "Face"
            draw = 62
            face_parts.append(part_id)
        elif part_id.endswith("_L"):
            folder = "Eyes"
            draw = 150
            eye_l.append(part_id)
        elif part_id.endswith("_R"):
            folder = "Eyes"
            draw = 151
            eye_r.append(part_id)
        else:
            folder = "Mouth"
            draw = 160
            mouth.append(part_id)
        add_part(character, project, part_id, part_id, src, folder, draw, str(src))

    all_parts = [part["id"] for part in character["parts"]]
    head_parts = ["base_body", *face_parts, *eye_l, *eye_r, *mouth, *front, *side]
    character["deformers"] = [
        deformer("Root", "warp", None, all_parts, [560, 0, 920, 2048], [1024, 600]),
        deformer("Head_X", "warp", "Root", head_parts, [640, 40, 760, 520], [1024, 250]),
        deformer("Head_Z", "rotation", "Head_X", head_parts, [650, 40, 740, 560], [1024, 275]),
        deformer("Face", "warp", "Head_Z", face_parts, [760, 150, 500, 260], [1024, 260]),
        deformer("Eye_L", "warp", "Head_Z", eye_l, [830, 185, 200, 110], [920, 230]),
        deformer("Eye_R", "warp", "Head_Z", eye_r, [1040, 185, 200, 110], [1130, 230]),
        deformer("Mouth", "warp", "Head_Z", mouth, [940, 300, 160, 90], [1024, 335]),
        deformer("Hair_Front", "warp", "Head_Z", front, [650, 0, 760, 760], [1024, 105]),
        deformer("Hair_Back", "warp", "Root", back + side + tips, [300, 0, 1460, 1840], [1024, 90]),
    ]

    character["keyform_bindings"] = [
        binding("ParamAngleX", -30, "Head_X", {"translate": [-34, 2], "scale": [0.98, 1.0], "rotate": -2}),
        binding("ParamAngleX", 30, "Head_X", {"translate": [34, 2], "scale": [0.98, 1.0], "rotate": 2}),
        binding("ParamAngleZ", -15, "Head_Z", {"translate": [-6, 0], "scale": [1, 1], "rotate": -13}),
        binding("ParamAngleZ", 15, "Head_Z", {"translate": [6, 0], "scale": [1, 1], "rotate": 13}),
        binding("ParamEyeLOpen", 0, "Eye_L", {"translate": [0, 5], "scale": [1, 0.38], "rotate": 0}),
        binding("ParamEyeLOpen", 0.5, "Eye_L", {"translate": [0, 2], "scale": [1, 0.66], "rotate": 0}),
        binding("ParamEyeROpen", 0, "Eye_R", {"translate": [0, 5], "scale": [1, 0.38], "rotate": 0}),
        binding("ParamEyeROpen", 0.5, "Eye_R", {"translate": [0, 2], "scale": [1, 0.66], "rotate": 0}),
        binding("ParamMouthOpenY", 0.5, "Mouth", {"translate": [0, 1], "scale": [1.05, 1.08], "rotate": 0}),
        binding("ParamMouthOpenY", 1, "Mouth", {"translate": [0, 4], "scale": [1.1, 1.18], "rotate": 0}),
        binding("ParamHairFront", -1, "Hair_Front", {"translate": [-16, 2], "scale": [1, 1], "rotate": -2}),
        binding("ParamHairFront", 1, "Hair_Front", {"translate": [16, 2], "scale": [1, 1], "rotate": 2}),
        binding("ParamHairBack", -1, "Hair_Back", {"translate": [-13, 4], "scale": [1, 1], "rotate": -1.5}),
        binding("ParamHairBack", 1, "Hair_Back", {"translate": [13, 4], "scale": [1, 1], "rotate": 1.5}),
    ]

    for part_id, value in [("mouth_closed", 0), ("mouth_half", 0.5), ("mouth_open", 1)]:
        character["part_opacity_keyframes"].append(opacity_keyframes(part_id, "ParamMouthOpenY", value))
    for side_param, suffix in [("ParamEyeLOpen", "L"), ("ParamEyeROpen", "R")]:
        for part_id, value in [(f"eye_closed_{suffix}", 0), (f"eye_half_{suffix}", 0.5), (f"eye_open_{suffix}", 1)]:
            character["part_opacity_keyframes"].append(opacity_keyframes(part_id, side_param, value))

    physics_targets = sorted(set(back + side + tips + front))
    character["vertex_weights"] = [vertex_weights_for_part(character, part_id) for part_id in physics_targets]
    character["physics_profiles"] = [
        {
            "id": "front_bangs_light_spring",
            "targets": [part for part in front if part.startswith("front_bang")],
            "anchor": "top_center",
            "mass": 0.65,
            "stiffness": 0.18,
            "damping": 0.68,
            "drag": 0.03,
            "max_offset": [32, 24],
            "rotate_factor": 0.06,
            "input_weights": {"ParamAngleX": [-20, 2], "ParamAngleZ": [-8, 2], "ParamHairFront": [24, 0]},
            "part_weights": {part: 1.0 for part in front if part.startswith("front_bang")},
        },
        {
            "id": "side_locks_medium_spring",
            "targets": [part for part in front if part.startswith("side_lock")],
            "anchor": "top_center",
            "mass": 0.85,
            "stiffness": 0.14,
            "damping": 0.72,
            "drag": 0.03,
            "max_offset": [38, 28],
            "rotate_factor": 0.07,
            "input_weights": {"ParamAngleX": [-26, 5], "ParamAngleZ": [-10, 3], "ParamHairFront": [22, 0]},
            "part_weights": {part: 1.0 for part in front if part.startswith("side_lock")},
        },
        {
            "id": "side_hair_slow_spring",
            "targets": side,
            "anchor": "top_center",
            "mass": 1.2,
            "stiffness": 0.1,
            "damping": 0.76,
            "drag": 0.04,
            "max_offset": [30, 34],
            "rotate_factor": 0.045,
            "input_weights": {"ParamAngleX": [-18, 7], "ParamAngleZ": [-8, 5], "ParamHairBack": [20, 0]},
            "part_weights": {part: 1.0 for part in side},
        },
        {
            "id": "back_hair_heavy_spring",
            "targets": back,
            "anchor": "top_center",
            "mass": 1.45,
            "stiffness": 0.08,
            "damping": 0.8,
            "drag": 0.05,
            "max_offset": [24, 34],
            "rotate_factor": 0.03,
            "input_weights": {"ParamAngleX": [-16, 8], "ParamAngleZ": [-7, 5], "ParamHairBack": [18, 0]},
            "part_weights": {part: 1.0 for part in back},
        },
        {
            "id": "hair_tips_delayed_spring",
            "targets": tips,
            "anchor": "top_center",
            "mass": 1.65,
            "stiffness": 0.07,
            "damping": 0.82,
            "drag": 0.05,
            "max_offset": [42, 42],
            "rotate_factor": 0.065,
            "input_weights": {"ParamAngleX": [-30, 12], "ParamAngleZ": [-12, 8], "ParamHairBack": [28, 0]},
            "part_weights": {part: 1.0 for part in tips},
        },
    ]
    character["physics_requirements"] = {
        "minimum_active_profiles": 5,
        "minimum_physics_targets": 10,
        "required_scenarios": ["angle_swing", "head_tilt", "hair_settle", "mouth_talk", "eye_blink"],
    }

    write_json(project / "character.json", character)
    report = {
        "schema_version": 1,
        "experiment_id": exp.name,
        "generated_at": now(),
        "status": "PASS",
        "project": str(project),
        "counts": {
            "parts": len(character["parts"]),
            "meshes": len(character["meshes"]),
            "deformers": len(character["deformers"]),
            "parameters": len(character["parameters"]),
            "keyform_bindings": len(character["keyform_bindings"]),
            "part_opacity_keyframes": len(character["part_opacity_keyframes"]),
            "vertex_weights": len(character["vertex_weights"]),
            "physics_profiles": len(character["physics_profiles"]),
        },
        "excluded_packs": ["outfit_pack", "accessory_pack"],
    }
    write_json(exp / "reports" / "hair_face_project_build_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", default=str(DEFAULT_EXPERIMENT))
    args = parser.parse_args()
    exp = Path(args.experiment).resolve()
    if not BASE_SOURCE.exists():
        raise SystemExit(f"missing base source: {BASE_SOURCE}")
    report = build_project(exp)
    print(json.dumps({"ok": True, "status": report["status"], "counts": report["counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

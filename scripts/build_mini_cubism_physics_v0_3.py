#!/usr/bin/env python3
"""Build the Mini Cubism Physics v0.3 project from the v0.1 best candidate."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "experiments/mini-cubism-auto-authoring-001/candidates/candidate_009/mini_cubism_project"
DEFAULT_OUT = ROOT / "experiments/mini-cubism-physics-v0-3-001"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def bbox_alpha(path: Path) -> tuple[list[int], float]:
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        alpha = rgba.getchannel("A")
        bbox = alpha.getbbox()
        nonzero = sum(alpha.histogram()[1:])
        total = rgba.width * rgba.height
    if bbox is None:
        return [0, 0, 2, 2], 0
    left, top, right, bottom = bbox
    return [left, top, right - left, bottom - top], round(nonzero / total, 8)


def make_mouth_keypose(path: Path, canvas_size: list[int], mouth_bbox: list[int], openness: float) -> tuple[list[int], float]:
    image = Image.new("RGBA", tuple(canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    x, y, w, h = mouth_bbox
    cx = x + w / 2
    cy = y + h / 2 + h * 0.12
    width = max(58, w * (0.58 + openness * 0.26))
    height = max(16, h * (0.16 + openness * 0.56))
    left = cx - width / 2
    top = cy - height / 2
    right = cx + width / 2
    bottom = cy + height / 2
    lip = (92, 35, 44, 235)
    inner = (45, 22, 28, 245)
    shadow = (122, 57, 67, 180)
    draw.ellipse([left - 5, top - 4, right + 5, bottom + 4], fill=lip)
    draw.ellipse([left, top, right, bottom], fill=inner)
    if openness >= 0.85:
        draw.rounded_rectangle([left + width * 0.25, top + height * 0.12, right - width * 0.25, top + height * 0.28], radius=4, fill=(248, 226, 218, 210))
        draw.ellipse([left + width * 0.28, cy + height * 0.08, right - width * 0.28, bottom - height * 0.08], fill=shadow)
    else:
        draw.arc([left, top - 2, right, bottom + 3], 8, 172, fill=shadow, width=5)
    image.save(path)
    return bbox_alpha(path)


def mesh_for_bbox(part_id: str, bbox: list[int], canvas_size: list[int], cols: int = 5, rows: int = 3) -> dict[str, Any]:
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
        "mesh_strategy": {"kind": "physics_v0_3_keypose_bbox_grid", "cols": cols, "rows": rows},
    }


def add_part(character: dict[str, Any], project: Path, part_id: str, bbox: list[int], alpha: float, draw_order: int) -> None:
    part_path = project / "parts" / f"{part_id}.png"
    mesh = mesh_for_bbox(part_id, bbox, character["canvas_size"])
    mesh_path = project / "meshes" / f"{part_id}.json"
    mesh["mesh_path"] = f"meshes/{mesh_path.name}"
    write_json(mesh_path, mesh)
    character["parts"].append(
        {
            "id": part_id,
            "display_name": part_id,
            "source_path": f"parts/{part_path.name}",
            "original_source_path": "generated:mini_cubism_physics_v0_3_mouth_keypose",
            "bbox": bbox,
            "alpha_coverage": alpha,
            "draw_order": draw_order,
            "folder": "Mouth",
        }
    )
    character["meshes"].append(mesh)


def add_eye_half_keyforms(character: dict[str, Any]) -> None:
    existing = {(item["parameter_id"], item["key_value"], item["target_id"]) for item in character["keyform_bindings"]}
    for parameter_id, target_id in [("ParamEyeLOpen", "Eye_L"), ("ParamEyeROpen", "Eye_R")]:
        key = (parameter_id, 0.5, target_id)
        if key not in existing:
            character["keyform_bindings"].append(
                {
                    "parameter_id": parameter_id,
                    "key_value": 0.5,
                    "target_id": target_id,
                    "delta_type": "deformer_transform",
                    "deltas": {"translate": [0, 0], "scale": [1.0, 0.48], "rotate": 0},
                }
            )


def replace_mouth_binding(character: dict[str, Any]) -> None:
    character["keyform_bindings"] = [
        item
        for item in character["keyform_bindings"]
        if not (item.get("parameter_id") == "ParamMouthOpenY" and item.get("target_id") == "Mouth")
    ]
    for key_value, scale_y in [(0.5, 1.03), (1, 1.06)]:
        character["keyform_bindings"].append(
            {
                "parameter_id": "ParamMouthOpenY",
                "key_value": key_value,
                "target_id": "Mouth",
                "delta_type": "deformer_transform",
                "deltas": {"translate": [0, 0], "scale": [1.0, scale_y], "rotate": 0},
            }
        )


def vertex_weights_for_part(character: dict[str, Any], part_id: str, kind: str) -> dict[str, Any]:
    mesh = next(item for item in character["meshes"] if item["part_id"] == part_id)
    part = next(item for item in character["parts"] if item["id"] == part_id)
    x, y, width, height = part["bbox"]
    weights = []
    for vx, vy in mesh["vertices"]:
        vertical = 0 if height <= 0 else (vy - y) / height
        if kind == "root_to_tip_vertical":
            weight = vertical
        elif kind == "accessory_full":
            weight = 1
        else:
            weight = 0.5
        weights.append(round(max(0, min(1, weight)), 4))
    return {"part_id": part_id, "weight_kind": kind, "weights": weights}


def add_physics_schema(character: dict[str, Any]) -> None:
    physics_targets = {
        "front_hair": "root_to_tip_vertical",
        "back_hair": "root_to_tip_vertical",
        "L_ear_outer": "accessory_full",
        "R_ear_outer": "accessory_full",
        "choker": "accessory_full",
    }
    character["vertex_weights"] = [
        vertex_weights_for_part(character, part_id, kind)
        for part_id, kind in physics_targets.items()
        if any(part["id"] == part_id for part in character["parts"])
    ]
    character["physics_profiles"] = [
        {
            "id": "front_hair_soft_spring",
            "targets": ["front_hair"],
            "anchor": "top_center",
            "mass": 0.8,
            "stiffness": 0.13,
            "damping": 0.82,
            "drag": 0.03,
            "max_offset": [34, 28],
            "rotate_factor": 0.055,
            "input_weights": {"ParamAngleX": [-24, 3], "ParamHairFront": [24, 0]},
            "part_weights": {"front_hair": 1.0},
        },
        {
            "id": "back_hair_heavy_spring",
            "targets": ["back_hair"],
            "anchor": "top_center",
            "mass": 1.4,
            "stiffness": 0.08,
            "damping": 0.88,
            "drag": 0.04,
            "max_offset": [24, 34],
            "rotate_factor": 0.03,
            "input_weights": {"ParamAngleX": [-18, 8]},
            "part_weights": {"back_hair": 1.0},
        },
        {
            "id": "ear_accessory_quick_spring",
            "targets": ["L_ear_outer", "R_ear_outer", "choker"],
            "anchor": "center",
            "mass": 0.5,
            "stiffness": 0.2,
            "damping": 0.72,
            "drag": 0.02,
            "max_offset": [16, 14],
            "rotate_factor": 0.08,
            "input_weights": {"ParamAngleX": [-12, 4]},
            "part_weights": {"L_ear_outer": 0.9, "R_ear_outer": 0.9, "choker": 0.35},
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    source = Path(args.source).resolve()
    out_root = Path(args.out).resolve()
    project = out_root / "best" / "mini_cubism_project"
    if not (source / "character.json").exists():
        raise SystemExit(f"missing source character.json: {source}")
    if project.exists():
        shutil.rmtree(project)
    shutil.copytree(source, project, ignore=shutil.ignore_patterns("reports/preview_evidence", "reports/validation_report.json"))

    character_path = project / "character.json"
    character = load_json(character_path)
    character["project_kind"] = "mini_cubism_v0"
    character["experiment_id"] = "mini-cubism-physics-v0-3-001"
    character["physics_v0_3"] = {
        "schema_version": 1,
        "generated_at": now(),
        "source_project": str(source),
        "note": "Adds mouth/eye keyposes, vertex weights, and preview spring-damper physics. This is not Cubism CMO3/MOC3 compatibility evidence.",
    }

    mouth = next(part for part in character["parts"] if part["id"] == "mouth_line")
    mouth_bbox = mouth["bbox"]
    base_order = int(mouth["draw_order"])
    for part_id, openness, order_offset in [("mouth_half_open", 0.5, 1), ("mouth_open", 1.0, 2)]:
        path = project / "parts" / f"{part_id}.png"
        bbox, alpha = make_mouth_keypose(path, character["canvas_size"], mouth_bbox, openness)
        add_part(character, project, part_id, bbox, alpha, base_order + order_offset)

    for deformer in character["deformers"]:
        if deformer["id"] == "Mouth":
            deformer["child_ids"] = sorted(set(deformer.get("child_ids", [])) | {"mouth_line", "mouth_half_open", "mouth_open"})

    character["part_opacity_keyframes"] = [
        {
            "part_id": "mouth_line",
            "parameter_id": "ParamMouthOpenY",
            "mode": "step_nearest",
            "keyframes": [{"value": 0, "opacity": 1}, {"value": 0.5, "opacity": 0}, {"value": 1, "opacity": 0}],
        },
        {
            "part_id": "mouth_half_open",
            "parameter_id": "ParamMouthOpenY",
            "mode": "step_nearest",
            "keyframes": [{"value": 0, "opacity": 0}, {"value": 0.5, "opacity": 1}, {"value": 1, "opacity": 0}],
        },
        {
            "part_id": "mouth_open",
            "parameter_id": "ParamMouthOpenY",
            "mode": "step_nearest",
            "keyframes": [{"value": 0, "opacity": 0}, {"value": 0.5, "opacity": 0}, {"value": 1, "opacity": 1}],
        },
        {
            "part_id": "L_iris",
            "parameter_id": "ParamEyeLOpen",
            "mode": "step_nearest",
            "keyframes": [{"value": 0, "opacity": 0}, {"value": 0.5, "opacity": 1}, {"value": 1, "opacity": 1}],
        },
        {
            "part_id": "R_iris",
            "parameter_id": "ParamEyeROpen",
            "mode": "step_nearest",
            "keyframes": [{"value": 0, "opacity": 0}, {"value": 0.5, "opacity": 1}, {"value": 1, "opacity": 1}],
        },
    ]
    add_eye_half_keyforms(character)
    replace_mouth_binding(character)
    add_physics_schema(character)
    character["notes"] = character.get("notes", []) + [
        "Physics v0.3 adds generated mouth keypose layers for closed/half/open visibility gating.",
        "Physics is preview-only spring-damper behavior; Glue remains fixture-gated and empty.",
    ]
    write_json(character_path, character)

    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "BUILT_PENDING_VALIDATION",
        "source_project": str(source),
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
            "glue": len(character.get("glue", [])),
        },
    }
    write_json(project / "reports" / "physics_v0_3_build_report.json", report)
    print(json.dumps({"ok": True, "project": str(project), "counts": report["counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

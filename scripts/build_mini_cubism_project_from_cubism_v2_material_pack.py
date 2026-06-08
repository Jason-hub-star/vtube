#!/usr/bin/env python3
"""Build a Mini Cubism preview project from the Cubism v2 material pack."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACK = ROOT / "experiments/cubism-v2-new-character-001/material_pack_v0"
DEFAULT_OUT = DEFAULT_PACK / "mini_cubism_project_material_v0"

PARAMETERS = [
    {"id": "ParamAngleX", "min": -30, "max": 30, "default": 0, "key_values": [-30, 0, 30]},
    {"id": "ParamAngleY", "min": -30, "max": 30, "default": 0, "key_values": [-30, 0, 30]},
    {"id": "ParamAngleZ", "min": -30, "max": 30, "default": 0, "key_values": [-30, 0, 30]},
    {"id": "ParamBodyAngleX", "min": -10, "max": 10, "default": 0, "key_values": [-10, 0, 10]},
    {"id": "ParamBodyAngleY", "min": -10, "max": 10, "default": 0, "key_values": [-10, 0, 10]},
    {"id": "ParamEyeLOpen", "min": 0, "max": 1, "default": 1, "key_values": [0, 1]},
    {"id": "ParamEyeROpen", "min": 0, "max": 1, "default": 1, "key_values": [0, 1]},
    {"id": "ParamEyeBallX", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
    {"id": "ParamEyeBallY", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
    {"id": "ParamMouthOpenY", "min": 0, "max": 1, "default": 0, "key_values": [0, 1]},
    {"id": "ParamMouthForm", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
    {"id": "ParamHairFront", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
    {"id": "ParamHairSide", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
    {"id": "ParamHairBack", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
    {"id": "ParamBreath", "min": 0, "max": 1, "default": 0, "key_values": [0, 1]},
]

FOLDER_LABELS = {
    "body": "Body",
    "face_base": "Face",
    "eye_L": "Eyes",
    "eye_R": "Eyes",
    "brow": "Eyes",
    "mouth": "Mouth",
    "hair": "Hair",
    "clothing": "Clothing",
}

DEFORMER_PARENT = {
    "root_warp": None,
    "body_root_warp": "root_warp",
    "shoulder_arm_rotation": "body_root_warp",
    "head_angle_warp": "root_warp",
    "brow_L_R_warp": "head_angle_warp",
    "eye_L_warp": "head_angle_warp",
    "eye_R_warp": "head_angle_warp",
    "mouth_warp": "head_angle_warp",
    "front_hair_warp": "head_angle_warp",
    "side_hair_L_R_warp": "head_angle_warp",
    "back_hair_warp": "root_warp",
}

DEFORMER_TYPE = {
    "shoulder_arm_rotation": "rotation",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def safe_id(value: str) -> str:
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in value)


def bbox_from_alpha(image: Image.Image) -> tuple[list[int], int, int]:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    bbox = alpha.getbbox()
    nonzero = sum(alpha.histogram()[1:])
    total = rgba.width * rgba.height
    if bbox is None:
        return [0, 0, rgba.width, rgba.height], 0, total
    left, top, right, bottom = bbox
    return [left, top, right - left, bottom - top], nonzero, total


def grid_density(part_id: str, group: str) -> tuple[int, int]:
    if group == "hair":
        return 8, 8
    if group in {"face_base", "body", "clothing"}:
        return 5, 5
    if group in {"eye_L", "eye_R", "brow", "mouth"}:
        return 4, 3
    return 3, 3


def mesh_for_part(part_id: str, group: str, bbox: list[int], canvas_size: list[int]) -> dict[str, Any]:
    x, y, width, height = bbox
    cols, rows = grid_density(part_id, group)
    width = max(width, 2)
    height = max(height, 2)
    vertices: list[list[float]] = []
    uvs: list[list[float]] = []
    boundary: list[int] = []
    canvas_w, canvas_h = canvas_size
    for row in range(rows + 1):
        for col in range(cols + 1):
            vx = x + width * (col / cols)
            vy = y + height * (row / rows)
            index = len(vertices)
            vertices.append([round(vx, 3), round(vy, 3)])
            uvs.append([round(vx / canvas_w, 6), round(vy / canvas_h, 6)])
            if row in {0, rows} or col in {0, cols}:
                boundary.append(index)

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
        "mesh_strategy": {
            "kind": "material_pack_alpha_bbox_grid",
            "cols": cols,
            "rows": rows,
            "note": "Mini Cubism preview mesh only; not final Cubism ArtMesh quality.",
        },
    }


def bounds_for_targets(parts: list[dict[str, Any]], targets: list[str], canvas_size: list[int]) -> list[float]:
    selected = [part for part in parts if part["id"] in targets]
    if not selected:
        return [0, 0, canvas_size[0], canvas_size[1]]
    left = min(part["bbox"][0] for part in selected)
    top = min(part["bbox"][1] for part in selected)
    right = max(part["bbox"][0] + part["bbox"][2] for part in selected)
    bottom = max(part["bbox"][1] + part["bbox"][3] for part in selected)
    pad = 24
    return [
        max(0, left - pad),
        max(0, top - pad),
        min(canvas_size[0], right + pad),
        min(canvas_size[1], bottom + pad),
    ]


def build_deformers(parts: list[dict[str, Any]], canvas_size: list[int]) -> list[dict[str, Any]]:
    by_node: dict[str, list[str]] = {}
    for part in parts:
        by_node.setdefault(part["deformer_node"], []).append(part["id"])
    deformers: list[dict[str, Any]] = []
    for node in DEFORMER_PARENT:
        targets = by_node.get(node, [])
        bounds = bounds_for_targets(parts, targets, canvas_size)
        deformers.append(
            {
                "id": node,
                "type": DEFORMER_TYPE.get(node, "warp"),
                "parent_id": DEFORMER_PARENT[node],
                "child_ids": targets,
                "bounds": bounds,
                "pivot": [round((bounds[0] + bounds[2]) / 2, 3), round((bounds[1] + bounds[3]) / 2, 3)],
            }
        )
    return deformers


def binding(parameter_id: str, key_value: float, target_id: str, translate: list[float], scale: list[float] | None = None, rotate: float = 0, opacity: float = 1) -> dict[str, Any]:
    return {
        "parameter_id": parameter_id,
        "key_value": key_value,
        "target_id": target_id,
        "delta_type": "deformer_transform",
        "deltas": {
            "translate": translate,
            "scale": scale or [1, 1],
            "rotate": rotate,
            "opacity": opacity,
        },
    }


def build_keyform_bindings() -> list[dict[str, Any]]:
    bindings = [
        binding("ParamAngleX", -30, "head_angle_warp", [-26, 0], [0.98, 1], -2),
        binding("ParamAngleX", 30, "head_angle_warp", [26, 0], [0.98, 1], 2),
        binding("ParamAngleY", -30, "head_angle_warp", [0, 18], [1, 0.98], 0),
        binding("ParamAngleY", 30, "head_angle_warp", [0, -18], [1, 1.02], 0),
        binding("ParamAngleZ", -30, "head_angle_warp", [-4, 0], [1, 1], -5),
        binding("ParamAngleZ", 30, "head_angle_warp", [4, 0], [1, 1], 5),
        binding("ParamBodyAngleX", -10, "body_root_warp", [-18, 0], [1, 1], -1),
        binding("ParamBodyAngleX", 10, "body_root_warp", [18, 0], [1, 1], 1),
        binding("ParamBodyAngleY", -10, "body_root_warp", [0, 8], [1, 0.99], 0),
        binding("ParamBodyAngleY", 10, "body_root_warp", [0, -8], [1, 1.01], 0),
        binding("ParamEyeLOpen", 0, "eye_L_warp", [0, 0], [1, 0.12], 0),
        binding("ParamEyeROpen", 0, "eye_R_warp", [0, 0], [1, 0.12], 0),
        binding("ParamMouthOpenY", 1, "mouth_warp", [0, 12], [1, 1.35], 0),
        binding("ParamMouthForm", -1, "mouth_warp", [-6, 0], [0.9, 1], 0),
        binding("ParamMouthForm", 1, "mouth_warp", [6, 0], [1.08, 1], 0),
        binding("ParamHairFront", -1, "front_hair_warp", [-16, 0], [1, 1], -3),
        binding("ParamHairFront", 1, "front_hair_warp", [16, 0], [1, 1], 3),
        binding("ParamHairSide", -1, "side_hair_L_R_warp", [-18, 0], [1, 1], -2),
        binding("ParamHairSide", 1, "side_hair_L_R_warp", [18, 0], [1, 1], 2),
        binding("ParamHairBack", -1, "back_hair_warp", [-12, 0], [1, 1], -2),
        binding("ParamHairBack", 1, "back_hair_warp", [12, 0], [1, 1], 2),
        binding("ParamBreath", 1, "body_root_warp", [0, -8], [1.01, 1.01], 0),
    ]
    for side in ["L", "R"]:
        for part_suffix, weight in [("iris", 1.0), ("pupil", 1.15), ("highlight", 0.75)]:
            target = f"eye_{side}_{part_suffix}"
            bindings.extend(
                [
                    binding("ParamEyeBallX", -1, target, [-10 * weight, 0], [1, 1], 0),
                    binding("ParamEyeBallX", 1, target, [10 * weight, 0], [1, 1], 0),
                    binding("ParamEyeBallY", -1, target, [0, -7 * weight], [1, 1], 0),
                    binding("ParamEyeBallY", 1, target, [0, 7 * weight], [1, 1], 0),
                ]
            )
    return bindings


def build_physics_profiles(parts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def targets_for(node: str) -> list[str]:
        return [part["id"] for part in parts if part["deformer_node"] == node]

    return [
        {
            "id": "front_hair_physics",
            "targets": targets_for("front_hair_warp"),
            "input_weights": {"ParamAngleX": [22, 0], "ParamAngleZ": [12, 4], "ParamHairFront": [18, 0]},
            "part_weights": {part_id: 1 for part_id in targets_for("front_hair_warp")},
            "stiffness": 0.11,
            "damping": 0.84,
            "max_offset": [34, 18],
            "rotate_factor": 0.08,
        },
        {
            "id": "side_hair_physics",
            "targets": targets_for("side_hair_L_R_warp"),
            "input_weights": {"ParamAngleX": [18, 0], "ParamHairSide": [24, 0]},
            "part_weights": {part_id: 1 for part_id in targets_for("side_hair_L_R_warp")},
            "stiffness": 0.1,
            "damping": 0.83,
            "max_offset": [38, 20],
            "rotate_factor": 0.08,
        },
        {
            "id": "back_hair_physics",
            "targets": targets_for("back_hair_warp"),
            "input_weights": {"ParamAngleX": [12, 0], "ParamHairBack": [20, 0]},
            "part_weights": {part_id: 1 for part_id in targets_for("back_hair_warp")},
            "stiffness": 0.08,
            "damping": 0.86,
            "max_offset": [30, 16],
            "rotate_factor": 0.05,
        },
    ]


def build_part_opacity_keyframes(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return list(manifest.get("part_opacity_keyframes") or [])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", default=str(DEFAULT_PACK))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    pack_dir = Path(args.pack).resolve()
    out_dir = Path(args.out).resolve()
    layer_manifest_path = pack_dir / "layer_manifest.json"
    manifest = load_json(layer_manifest_path)
    layers = [item for item in manifest["layers"] if item.get("include_in_import_psd")]
    if not layers:
        raise SystemExit(f"No import PSD layers found: {layer_manifest_path}")

    project_dir = out_dir
    parts_dir = project_dir / "parts"
    meshes_dir = project_dir / "meshes"
    reports_dir = project_dir / "reports"
    for path in [parts_dir, meshes_dir, project_dir / "deformers", project_dir / "parameters", project_dir / "motions", reports_dir]:
        path.mkdir(parents=True, exist_ok=True)

    parts: list[dict[str, Any]] = []
    meshes: list[dict[str, Any]] = []
    canvas_size = [2048, 2048]
    for layer in sorted(layers, key=lambda item: int(item.get("draw_order", 500))):
        part_id = safe_id(layer["part_id"])
        source = Path(layer["output_path"])
        if not source.is_absolute():
            source = ROOT / source
        if not source.exists():
            raise SystemExit(f"Missing layer image: {source}")
        dest = parts_dir / f"{part_id}.png"
        shutil.copy2(source, dest)
        with Image.open(source) as image:
            bbox, nonzero, total = bbox_from_alpha(image)
            canvas_size = [image.width, image.height]
        alpha_coverage = round(nonzero / total, 8) if total else 0
        group = layer.get("group", "misc")
        part = {
            "id": part_id,
            "display_name": layer.get("label_ko") or part_id,
            "source_path": f"parts/{dest.name}",
            "original_source_path": str(source),
            "bbox": bbox,
            "alpha_coverage": alpha_coverage,
            "draw_order": int(layer.get("draw_order", 500)),
            "folder": FOLDER_LABELS.get(group, group.title()),
            "deformer_node": layer.get("deformer_node") or "root_warp",
            "material_group": group,
            "risk_tags": layer.get("risk_tags", []),
        }
        mesh = mesh_for_part(part_id, group, bbox, canvas_size)
        mesh_path = meshes_dir / f"{part_id}.json"
        mesh["mesh_path"] = f"meshes/{mesh_path.name}"
        mesh_path.write_text(json.dumps(mesh, ensure_ascii=False, indent=2) + "\n")
        parts.append(part)
        meshes.append(mesh)

    deformers = build_deformers(parts, canvas_size)
    parameters = PARAMETERS
    keyform_bindings = build_keyform_bindings()
    physics_profiles = build_physics_profiles(parts)
    part_opacity_keyframes = build_part_opacity_keyframes(manifest)

    (project_dir / "deformers" / "deformers.json").write_text(json.dumps(deformers, ensure_ascii=False, indent=2) + "\n")
    (project_dir / "parameters" / "parameters.json").write_text(json.dumps(parameters, ensure_ascii=False, indent=2) + "\n")
    (project_dir / "motions" / "default_pose.json").write_text(
        json.dumps({"schema_version": 1, "parameters": {item["id"]: item["default"] for item in parameters}}, ensure_ascii=False, indent=2) + "\n"
    )

    character = {
        "schema_version": 1,
        "project_kind": "mini_cubism_v0",
        "experiment_id": "cubism-v2-new-character-001/material_pack_v0",
        "generated_at": now(),
        "source_selection": str(layer_manifest_path),
        "canvas_size": canvas_size,
        "parts": parts,
        "meshes": meshes,
        "deformers": deformers,
        "parameters": parameters,
        "keyform_bindings": keyform_bindings,
        "physics_profiles": physics_profiles,
        "part_opacity_keyframes": part_opacity_keyframes,
        "glue": [],
        "notes": [
            "Mini Cubism material preview project built from the Cubism v2 material pack.",
            "This validates local preview loading, draw order, simple deformer/keyform response, and physics preview only.",
            "This is not a Cubism CMO3/MOC3 export and not final ArtMesh quality.",
        ],
    }
    character_path = project_dir / "character.json"
    character_path.write_text(json.dumps(character, ensure_ascii=False, indent=2) + "\n")

    report = {
        "schema_version": 1,
        "status": "BUILT_PENDING_VALIDATION",
        "generated_at": now(),
        "pack_dir": str(pack_dir),
        "project_dir": str(project_dir),
        "character_json": str(character_path),
        "counts": {
            "parts": len(parts),
            "meshes": len(meshes),
            "deformers": len(deformers),
            "parameters": len(parameters),
            "keyform_bindings": len(keyform_bindings),
            "physics_profiles": len(physics_profiles),
            "part_opacity_keyframes": len(part_opacity_keyframes),
            "glue": 0,
        },
    }
    report_path = reports_dir / "build_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"ok": True, "project": str(project_dir), "report": str(report_path), "counts": report["counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

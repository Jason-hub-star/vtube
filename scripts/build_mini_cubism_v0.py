#!/usr/bin/env python3
"""Build a Vtube-native Mini Cubism v0 project from accepted Cubism parts."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT_ID = "imagen-live2d-001"
REQUIRED_PARAMETERS = [
    "ParamAngleX",
    "ParamEyeLOpen",
    "ParamEyeROpen",
    "ParamMouthOpenY",
    "ParamHairFront",
]

FOLDERS = {
    "front_hair": "Hair",
    "back_hair": "Hair",
    "face_base": "Face",
    "neck": "Face",
    "L_eye_white": "Eyes",
    "R_eye_white": "Eyes",
    "L_iris": "Eyes",
    "R_iris": "Eyes",
    "L_upper_lash": "Eyes",
    "R_upper_lash": "Eyes",
    "L_brow": "Eyes",
    "R_brow": "Eyes",
    "mouth_line": "Mouth",
    "clothes": "Body",
    "L_arm": "Body",
    "R_arm": "Body",
    "choker": "Accessory",
    "L_ear_outer": "Accessory",
    "R_ear_outer": "Accessory",
}

DEFORMER_TARGETS = {
    "Root": [],
    "Body": ["clothes", "choker", "neck", "L_arm", "R_arm"],
    "Head_X": ["face_base", "front_hair", "back_hair", "L_ear_outer", "R_ear_outer"],
    "Face_Base": ["face_base", "neck", "L_brow", "R_brow"],
    "Eye_L": ["L_eye_white", "L_iris", "L_upper_lash"],
    "Eye_R": ["R_eye_white", "R_iris", "R_upper_lash"],
    "Mouth": ["mouth_line"],
    "Hair_Front": ["front_hair"],
    "Hair_Back": ["back_hair"],
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def safe_id(value: str) -> str:
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in value)


def bbox_from_alpha(image: Image.Image) -> tuple[list[int], int, int]:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    bbox = alpha.getbbox()
    histogram = alpha.histogram()
    nonzero = sum(histogram[1:])
    if bbox is None:
        return [0, 0, rgba.width, rgba.height], 0, rgba.width * rgba.height
    left, top, right, bottom = bbox
    return [left, top, right - left, bottom - top], nonzero, rgba.width * rgba.height


def grid_density(part_id: str) -> tuple[int, int]:
    if "hair" in part_id:
        return 8, 8
    if "face" in part_id or part_id == "clothes":
        return 5, 5
    if "eye" in part_id or "iris" in part_id or "lash" in part_id or "brow" in part_id:
        return 4, 3
    if "arm" in part_id or "ear" in part_id:
        return 4, 4
    return 3, 3


def mesh_for_part(part_id: str, bbox: list[int], canvas_size: list[int]) -> dict[str, Any]:
    x, y, width, height = bbox
    cols, rows = grid_density(part_id)
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
            idx = len(vertices)
            vertices.append([round(vx, 3), round(vy, 3)])
            uvs.append([round(vx / canvas_w, 6), round(vy / canvas_h, 6)])
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
        "mesh_strategy": {
            "kind": "alpha_bbox_grid",
            "cols": cols,
            "rows": rows,
            "note": "v0 conservative mesh based on alpha bbox; not final Cubism ArtMesh quality",
        },
    }


def choose_layers(experiment_id: str) -> tuple[list[dict[str, Any]], str]:
    exp_dir = ROOT / "experiments" / experiment_id
    gate_path = exp_dir / "reports" / "psd_candidate_gate_report.json"
    manifest_path = exp_dir / "layer_manifest.json"
    if gate_path.exists():
        gate = load_json(gate_path)
        accepted = gate.get("accepted_layers", [])
        if accepted:
            return accepted, rel(gate_path)
    manifest = load_json(manifest_path)
    layers = [item for item in manifest.get("layers", []) if item.get("include_in_import_psd")]
    if not layers:
        layers = [
            item
            for item in manifest.get("layers", [])
            if item.get("production_candidate") and item.get("status") != "REFERENCE_ONLY"
        ]
    return layers, rel(manifest_path)


def part_record(layer: dict[str, Any], image_path: Path, dest_path: Path, canvas_size: list[int]) -> tuple[dict[str, Any], dict[str, Any]]:
    part_id = layer.get("part_id") or layer.get("original_part_id") or image_path.stem
    part_id = safe_id(part_id)
    with Image.open(image_path) as image:
        bbox, nonzero, total = bbox_from_alpha(image)
        actual_canvas = [image.width, image.height]
    if actual_canvas != canvas_size:
        canvas_size[:] = actual_canvas
    alpha_coverage = round(nonzero / total, 8) if total else 0.0
    part = {
        "id": part_id,
        "display_name": part_id,
        "source_path": f"parts/{dest_path.name}",
        "original_source_path": str(image_path),
        "bbox": bbox,
        "alpha_coverage": alpha_coverage,
        "draw_order": int(layer.get("draw_order", 500)),
        "folder": FOLDERS.get(part_id, "Accessory"),
    }
    mesh = mesh_for_part(part_id, bbox, canvas_size)
    return part, mesh


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
    }
    deformer_types = {
        "Root": "warp",
        "Body": "warp",
        "Head_X": "warp",
        "Face_Base": "warp",
        "Eye_L": "warp",
        "Eye_R": "warp",
        "Mouth": "warp",
        "Hair_Front": "rotation",
        "Hair_Back": "warp",
    }
    result = []
    for deformer_id, targets in DEFORMER_TARGETS.items():
        bounds = bounds_for_targets(parts, targets, canvas_size)
        result.append(
            {
                "id": deformer_id,
                "type": deformer_types[deformer_id],
                "parent_id": parent[deformer_id],
                "child_ids": [part["id"] for part in parts if part["id"] in targets],
                "bounds": bounds,
                "pivot": [round((bounds[0] + bounds[2]) / 2, 3), round((bounds[1] + bounds[3]) / 2, 3)],
            }
        )
    return result


def build_parameters() -> list[dict[str, Any]]:
    return [
        {"id": "ParamAngleX", "min": -30, "max": 30, "default": 0, "key_values": [-30, 0, 30]},
        {"id": "ParamEyeLOpen", "min": 0, "max": 1, "default": 1, "key_values": [0, 1]},
        {"id": "ParamEyeROpen", "min": 0, "max": 1, "default": 1, "key_values": [0, 1]},
        {"id": "ParamMouthOpenY", "min": 0, "max": 1, "default": 0, "key_values": [0, 1]},
        {"id": "ParamHairFront", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
    ]


def build_keyform_bindings(parts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    part_ids = {part["id"] for part in parts}
    bindings: list[dict[str, Any]] = [
        {
            "parameter_id": "ParamAngleX",
            "key_value": -30,
            "target_id": "Head_X",
            "delta_type": "deformer_transform",
            "deltas": {"translate": [-22, 0], "scale": [1.0, 1.0], "rotate": -2},
        },
        {
            "parameter_id": "ParamAngleX",
            "key_value": 30,
            "target_id": "Head_X",
            "delta_type": "deformer_transform",
            "deltas": {"translate": [22, 0], "scale": [1.0, 1.0], "rotate": 2},
        },
    ]
    if {"L_eye_white", "L_iris", "L_upper_lash"} & part_ids:
        bindings.append(
            {
                "parameter_id": "ParamEyeLOpen",
                "key_value": 0,
                "target_id": "Eye_L",
                "delta_type": "deformer_transform",
                "deltas": {"translate": [0, 0], "scale": [1.0, 0.12], "rotate": 0},
            }
        )
    if {"R_eye_white", "R_iris", "R_upper_lash"} & part_ids:
        bindings.append(
            {
                "parameter_id": "ParamEyeROpen",
                "key_value": 0,
                "target_id": "Eye_R",
                "delta_type": "deformer_transform",
                "deltas": {"translate": [0, 0], "scale": [1.0, 0.12], "rotate": 0},
            }
        )
    if "mouth_line" in part_ids:
        bindings.append(
            {
                "parameter_id": "ParamMouthOpenY",
                "key_value": 1,
                "target_id": "Mouth",
                "delta_type": "deformer_transform",
                "deltas": {"translate": [0, 10], "scale": [1.0, 1.45], "rotate": 0},
            }
        )
    if "front_hair" in part_ids:
        for value, dx, rotate in [(-1, -16, -3), (1, 16, 3)]:
            bindings.append(
                {
                    "parameter_id": "ParamHairFront",
                    "key_value": value,
                    "target_id": "Hair_Front",
                    "delta_type": "deformer_transform",
                    "deltas": {"translate": [dx, 0], "scale": [1.0, 1.0], "rotate": rotate},
                }
            )
    return bindings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", default=DEFAULT_EXPERIMENT_ID)
    parser.add_argument("--out", default="experiments/mini-cubism-v0-001")
    args = parser.parse_args()

    out_dir = (ROOT / args.out).resolve()
    project_dir = out_dir / "mini_cubism_project"
    parts_dir = project_dir / "parts"
    meshes_dir = project_dir / "meshes"
    reports_dir = project_dir / "reports"
    for path in [parts_dir, meshes_dir, project_dir / "deformers", project_dir / "parameters", project_dir / "motions", reports_dir]:
        path.mkdir(parents=True, exist_ok=True)

    layers, source_selection = choose_layers(args.experiment_id)
    if not layers:
        raise SystemExit(f"No accepted layers found for {args.experiment_id}")

    parts: list[dict[str, Any]] = []
    meshes: list[dict[str, Any]] = []
    canvas_size = [2048, 2048]
    seen: set[str] = set()
    for layer in sorted(layers, key=lambda item: int(item.get("draw_order", 500))):
        image_path = Path(layer.get("output_path") or layer.get("source_path", ""))
        if not image_path.is_absolute():
            image_path = ROOT / image_path
        if not image_path.exists():
            raise SystemExit(f"Layer image does not exist: {image_path}")
        part_id = safe_id(layer.get("part_id") or layer.get("original_part_id") or image_path.stem)
        if part_id in seen:
            continue
        seen.add(part_id)
        dest_path = parts_dir / f"{part_id}.png"
        shutil.copy2(image_path, dest_path)
        part, mesh = part_record(layer, image_path, dest_path, canvas_size)
        mesh_path = meshes_dir / f"{part_id}.json"
        mesh["mesh_path"] = f"meshes/{mesh_path.name}"
        mesh_path.write_text(json.dumps(mesh, ensure_ascii=False, indent=2) + "\n")
        parts.append(part)
        meshes.append(mesh)

    deformers = build_deformers(parts, canvas_size)
    parameters = build_parameters()
    keyform_bindings = build_keyform_bindings(parts)
    (project_dir / "deformers" / "deformers.json").write_text(json.dumps(deformers, ensure_ascii=False, indent=2) + "\n")
    (project_dir / "parameters" / "parameters.json").write_text(json.dumps(parameters, ensure_ascii=False, indent=2) + "\n")
    (project_dir / "motions" / "default_pose.json").write_text(
        json.dumps({"schema_version": 1, "parameters": {item["id"]: item["default"] for item in parameters}}, ensure_ascii=False, indent=2) + "\n"
    )

    character = {
        "schema_version": 1,
        "project_kind": "mini_cubism_v0",
        "experiment_id": args.experiment_id,
        "generated_at": now(),
        "source_selection": source_selection,
        "canvas_size": canvas_size,
        "parts": parts,
        "meshes": meshes,
        "deformers": deformers,
        "parameters": parameters,
        "keyform_bindings": keyform_bindings,
        "glue": [],
        "notes": [
            "Mini Cubism v0 proves local mesh/deformer/keyform preview only.",
            "Stretchy Studio is not copied; this is a Vtube-native local rig format.",
            "Glue stays empty until fixture-backed CGlueSource evidence exists.",
        ],
    }
    character_path = project_dir / "character.json"
    character_path.write_text(json.dumps(character, ensure_ascii=False, indent=2) + "\n")

    report = {
        "schema_version": 1,
        "experiment_id": "mini-cubism-v0-001",
        "generated_at": now(),
        "source_experiment_id": args.experiment_id,
        "source_selection": source_selection,
        "project_dir": str(project_dir),
        "character_json": str(character_path),
        "counts": {
            "parts": len(parts),
            "meshes": len(meshes),
            "deformers": len(deformers),
            "parameters": len(parameters),
            "keyform_bindings": len(keyform_bindings),
            "glue": 0,
        },
        "status": "BUILT_PENDING_VALIDATION",
    }
    report_path = reports_dir / "build_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"ok": True, "project": str(project_dir), "report": str(report_path), "counts": report["counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build a Mini Cubism diagnostic project from character-002 keypose layers."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
LAYERS = EXP / "model_edit_v4_strict_mouth" / "normalized_layers"
PROJECT = EXP / "model_edit_v4_strict_mouth" / "mini_cubism_diagnostic_project"
PARTS_DIR = PROJECT / "parts"
MESHES_DIR = PROJECT / "meshes"
REPORTS = PROJECT / "reports"


PARAMETERS = [
    {"id": "ParamAngleX", "min": -30, "max": 30, "default": 0, "key_values": [-30, 0, 30]},
    {"id": "ParamEyeLOpen", "min": 0, "max": 1, "default": 1, "key_values": [0, 0.5, 1]},
    {"id": "ParamEyeROpen", "min": 0, "max": 1, "default": 1, "key_values": [0, 0.5, 1]},
    {"id": "ParamEyeBallX", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
    {"id": "ParamEyeBallY", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
    {"id": "ParamMouthOpenY", "min": 0, "max": 1, "default": 0, "key_values": [0, 0.5, 1]},
    {"id": "ParamMouthForm", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
    {"id": "ParamHairFront", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
]

GROUPS = {
    "face_base_clean": ("face_base", "Face", "head_angle_warp", 100),
    "eye_L_clean_socket": ("eye_L", "Eyes", "eye_L_warp", 180),
    "eye_R_clean_socket": ("eye_R", "Eyes", "eye_R_warp", 181),
    "eye_L_closed_underpaint": ("eye_L", "Eyes", "eye_L_warp", 190),
    "eye_R_closed_underpaint": ("eye_R", "Eyes", "eye_R_warp", 191),
    "eye_L_open": ("eye_L", "Eyes", "eye_L_warp", 300),
    "eye_R_open": ("eye_R", "Eyes", "eye_R_warp", 301),
    "eye_L_half_closed_lid": ("eye_L", "Eyes", "eye_L_warp", 310),
    "eye_R_half_closed_lid": ("eye_R", "Eyes", "eye_R_warp", 311),
    "eye_L_mostly_closed_lid": ("eye_L", "Eyes", "eye_L_warp", 320),
    "eye_R_mostly_closed_lid": ("eye_R", "Eyes", "eye_R_warp", 321),
    "eye_L_closed_lid": ("eye_L", "Eyes", "eye_L_warp", 330),
    "eye_R_closed_lid": ("eye_R", "Eyes", "eye_R_warp", 331),
    "mouth_base_clean": ("mouth", "Mouth", "mouth_warp", 390),
    "mouth_closed_smile": ("mouth", "Mouth", "mouth_warp", 400),
    "mouth_small_open": ("mouth", "Mouth", "mouth_warp", 410),
    "mouth_wide_open": ("mouth", "Mouth", "mouth_warp", 420),
    "mouth_o_vowel": ("mouth", "Mouth", "mouth_warp", 430),
    "mouth_inner": ("mouth", "Mouth", "mouth_warp", 440),
    "mouth_teeth": ("mouth", "Mouth", "mouth_warp", 450),
    "mouth_tongue": ("mouth", "Mouth", "mouth_warp", 460),
}


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def mesh_for_part(part_id: str, bbox: list[int], canvas_size: list[int]) -> dict[str, Any]:
    x, y, width, height = bbox
    cols, rows = (5, 5) if part_id == "face_base_clean" else (4, 3)
    width = max(width, 2)
    height = max(height, 2)
    vertices: list[list[float]] = []
    uvs: list[list[float]] = []
    triangles: list[list[int]] = []
    for row in range(rows + 1):
        for col in range(cols + 1):
            vx = x + width * col / cols
            vy = y + height * row / rows
            vertices.append([round(vx, 3), round(vy, 3)])
            uvs.append([round(vx / canvas_size[0], 6), round(vy / canvas_size[1], 6)])
    stride = cols + 1
    for row in range(rows):
        for col in range(cols):
            a = row * stride + col
            b = a + 1
            c = a + stride
            d = c + 1
            triangles.append([a, c, b])
            triangles.append([b, c, d])
    return {"part_id": part_id, "vertices": vertices, "triangles": triangles, "uvs": uvs}


def opacity_key(part_id: str, parameter_id: str, keyframes: list[tuple[float, float]]) -> dict[str, Any]:
    return {
        "part_id": part_id,
        "parameter_id": parameter_id,
        "mode": "step_nearest",
        "keyframes": [{"value": value, "opacity": opacity} for value, opacity in keyframes],
    }


def build_part_opacity_keyframes(excluded: set[str] | None = None) -> list[dict[str, Any]]:
    excluded = excluded or set()
    rules: list[dict[str, Any]] = []
    for side in ["L", "R"]:
        p = f"ParamEye{side}Open"
        rules.extend(
            [
                opacity_key(f"eye_{side}_clean_socket", p, [(0, 0), (0.5, 0), (1, 0)]),
                opacity_key(f"eye_{side}_open", p, [(0, 0), (0.5, 0), (1, 1)]),
                opacity_key(f"eye_{side}_half_closed_lid", p, [(0, 0), (0.5, 1), (1, 0)]),
                opacity_key(f"eye_{side}_mostly_closed_lid", p, [(0, 0), (0.5, 0), (1, 0)]),
                opacity_key(f"eye_{side}_closed_underpaint", p, [(0, 1), (0.5, 0), (1, 0)]),
                opacity_key(f"eye_{side}_closed_lid", p, [(0, 1), (0.5, 0), (1, 0)]),
            ]
        )
    mouth_rules = [
        ("mouth_closed_smile", "ParamMouthOpenY", [(0, 1), (0.5, 0), (1, 0)]),
        ("mouth_small_open", "ParamMouthOpenY", [(0, 0), (0.5, 1), (1, 1 if "mouth_wide_open" in excluded else 0)]),
        ("mouth_wide_open", "ParamMouthOpenY", [(0, 0), (0.5, 0), (1, 1)]),
        ("mouth_o_vowel", "ParamMouthForm", [(-1, 1), (0, 0), (1, 0)]),
        ("mouth_inner", "ParamMouthOpenY", [(0, 0), (0.5, 0), (1, 0)]),
        ("mouth_teeth", "ParamMouthOpenY", [(0, 0), (0.5, 0), (1, 0)]),
        ("mouth_tongue", "ParamMouthOpenY", [(0, 0), (0.5, 0), (1, 0)]),
    ]
    rules.extend(opacity_key(part_id, parameter_id, frames) for part_id, parameter_id, frames in mouth_rules if part_id not in excluded)
    return rules


def binding(parameter_id: str, target_id: str, key_value: float = 1, translate: list[float] | None = None, scale: list[float] | None = None) -> dict[str, Any]:
    return {
        "parameter_id": parameter_id,
        "key_value": key_value,
        "target_id": target_id,
        "delta_type": "deformer_transform",
        "deltas": {"translate": translate or [0, 0], "scale": scale or [1, 1], "rotate": 0, "opacity": 1},
    }


def main() -> int:
    import argparse

    global LAYERS, PROJECT, PARTS_DIR, MESHES_DIR, REPORTS

    parser = argparse.ArgumentParser()
    parser.add_argument("--layers-dir", type=Path, default=LAYERS)
    parser.add_argument("--project", type=Path, default=PROJECT)
    parser.add_argument("--candidate-id", default="model_edit_v4_strict_mouth")
    parser.add_argument("--exclude-part", action="append", default=[])
    args = parser.parse_args()

    LAYERS = args.layers_dir if args.layers_dir.is_absolute() else ROOT / args.layers_dir
    PROJECT = args.project if args.project.is_absolute() else ROOT / args.project
    PARTS_DIR = PROJECT / "parts"
    MESHES_DIR = PROJECT / "meshes"
    REPORTS = PROJECT / "reports"
    excluded_parts = set(args.exclude_part)

    for path in [PARTS_DIR, MESHES_DIR, PROJECT / "deformers", PROJECT / "parameters", PROJECT / "motions", REPORTS]:
        path.mkdir(parents=True, exist_ok=True)

    parts: list[dict[str, Any]] = []
    meshes: list[dict[str, Any]] = []
    canvas_size = [2048, 2048]
    groups = {asset_id: row for asset_id, row in GROUPS.items() if asset_id not in excluded_parts}
    for asset_id, (group, folder, deformer_node, draw_order) in sorted(groups.items(), key=lambda item: item[1][3]):
        source = LAYERS / f"{asset_id}.png"
        if not source.exists():
            raise SystemExit(f"missing layer: {source}")
        dest = PARTS_DIR / source.name
        shutil.copy2(source, dest)
        with Image.open(source) as image:
            bbox, nonzero, total = bbox_from_alpha(image)
            canvas_size = [image.width, image.height]
        mesh = mesh_for_part(asset_id, bbox, canvas_size)
        mesh_path = MESHES_DIR / f"{asset_id}.json"
        mesh["mesh_path"] = f"meshes/{mesh_path.name}"
        mesh_path.write_text(json.dumps(mesh, ensure_ascii=False, indent=2) + "\n")
        parts.append(
            {
                "id": asset_id,
                "display_name": asset_id,
                "source_path": f"parts/{dest.name}",
                "original_source_path": str(source),
                "bbox": bbox,
                "alpha_coverage": round(nonzero / total, 8) if total else 0,
                "draw_order": draw_order,
                "folder": folder,
                "deformer_node": deformer_node,
                "material_group": group,
                "risk_tags": ["diagnostic_keypose_layer"],
            }
        )
        meshes.append(mesh)

    deformers = [
        {"id": "root_warp", "type": "warp", "parent_id": None, "child_ids": [], "bounds": [0, 0, 2048, 2048], "pivot": [1024, 1024]},
        {"id": "head_angle_warp", "type": "warp", "parent_id": "root_warp", "child_ids": ["face_base_clean"], "bounds": [300, 20, 1740, 2048], "pivot": [1024, 850]},
        {"id": "eye_L_warp", "type": "warp", "parent_id": "head_angle_warp", "child_ids": [p["id"] for p in parts if p["id"].startswith("eye_L_")], "bounds": [730, 560, 1040, 790], "pivot": [880, 690]},
        {"id": "eye_R_warp", "type": "warp", "parent_id": "head_angle_warp", "child_ids": [p["id"] for p in parts if p["id"].startswith("eye_R_")], "bounds": [1025, 560, 1320, 790], "pivot": [1170, 690]},
        {"id": "mouth_warp", "type": "warp", "parent_id": "head_angle_warp", "child_ids": [p["id"] for p in parts if p["id"].startswith("mouth_")], "bounds": [900, 760, 1175, 930], "pivot": [1035, 845]},
        {"id": "front_hair_warp", "type": "warp", "parent_id": "head_angle_warp", "child_ids": [], "bounds": [600, 20, 1400, 760], "pivot": [1024, 390]},
    ]
    keyform_bindings = [
        binding("ParamAngleX", "head_angle_warp", -30, [-22, 0]),
        binding("ParamAngleX", "head_angle_warp", 30, [22, 0]),
        binding("ParamEyeLOpen", "eye_L_warp", 0, [0, 0], [1, 0.2]),
        binding("ParamEyeROpen", "eye_R_warp", 0, [0, 0], [1, 0.2]),
        binding("ParamMouthOpenY", "mouth_warp", 1, [0, 8], [1, 1.15]),
        binding("ParamHairFront", "front_hair_warp", 1, [10, 0]),
    ]

    character = {
        "schema_version": 1,
        "project_kind": "mini_cubism_v0",
        "experiment_id": f"cubism-v2-new-character-002/{args.candidate_id}",
        "generated_at": now(),
        "source_selection": rel(LAYERS),
        "canvas_size": canvas_size,
        "parts": parts,
        "meshes": meshes,
        "deformers": deformers,
        "parameters": PARAMETERS,
        "keyform_bindings": keyform_bindings,
        "physics_profiles": [],
        "part_opacity_keyframes": build_part_opacity_keyframes(excluded_parts),
        "glue": [],
        "notes": [
            "Diagnostic Mini Cubism preview from keypose material layers.",
            "Not a Cubism CMO3/MOC3 export and not final ArtMesh quality.",
            f"Excluded parts: {sorted(excluded_parts)}",
        ],
    }
    (PROJECT / "character.json").write_text(json.dumps(character, ensure_ascii=False, indent=2) + "\n")
    (PROJECT / "motions/default_pose.json").write_text(json.dumps({"schema_version": 1, "parameters": {p["id"]: p["default"] for p in PARAMETERS}}, ensure_ascii=False, indent=2) + "\n")
    report = {
        "schema_version": 1,
        "status": "BUILT_PENDING_VALIDATION",
        "generated_at": now(),
        "project": str(PROJECT),
        "counts": {"parts": len(parts), "meshes": len(meshes), "deformers": len(deformers), "parameters": len(PARAMETERS), "keyform_bindings": len(keyform_bindings), "part_opacity_keyframes": len(character["part_opacity_keyframes"])},
    }
    (REPORTS / "build_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"ok": True, "project": str(PROJECT), "report": str(REPORTS / "build_report.json"), "counts": report["counts"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

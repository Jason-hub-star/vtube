#!/usr/bin/env python3
"""Build a Mini Cubism project from targeted split candidate layers."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image

from build_mini_cubism_dedicated_model_v1 import (
    CANVAS,
    PARAMETERS,
    bbox_alpha,
    build_deformers,
    build_keyform_bindings,
    mesh_for_part,
    physics_profiles,
    vertex_weight,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = ROOT / "experiments/mini-cubism-dedicated-model-v1-001"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def opacity_keyframes_targeted() -> list[dict[str, Any]]:
    result = []
    mouth_groups = {
        "mouth_closed_line": [(0, 1), (0.5, 0), (1, 0)],
        "mouth_half_outer": [(0, 0), (0.5, 1), (1, 0)],
        "mouth_half_inner": [(0, 0), (0.5, 1), (1, 0)],
        "mouth_open_outer": [(0, 0), (0.5, 0), (1, 1)],
        "mouth_open_inner": [(0, 0), (0.5, 0), (1, 1)],
        "mouth_teeth_upper": [(0, 0), (0.5, 0), (1, 1)],
        "mouth_tongue": [(0, 0), (0.5, 0), (1, 1)],
        "mouth_shadow": [(0, 0), (0.5, 0), (1, 1)],
    }
    for part_id, frames in mouth_groups.items():
        result.append({"part_id": part_id, "parameter_id": "ParamMouthOpenY", "mode": "step_nearest", "keyframes": [{"value": value, "opacity": opacity} for value, opacity in frames]})
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


def build() -> dict[str, Any]:
    parser = argparse.ArgumentParser(description="Build Mini Cubism project from targeted split manifest.")
    parser.add_argument("--experiment", default=str(DEFAULT_EXPERIMENT))
    args = parser.parse_args()
    exp = Path(args.experiment).resolve()
    manifest_path = exp / "targeted_split_v1" / "targeted_layer_manifest.json"
    manifest = load_json(manifest_path)
    groups = manifest["part_groups"]
    project = exp / "mini_cubism_project_targeted"
    parts_dir = project / "parts"
    meshes_dir = project / "meshes"
    for path in [parts_dir, meshes_dir, project / "reports", project / "deformers", project / "parameters", project / "motions"]:
        path.mkdir(parents=True, exist_ok=True)

    parts: list[dict[str, Any]] = []
    meshes: list[dict[str, Any]] = []
    for layer in sorted(manifest["layers"], key=lambda item: int(item.get("draw_order", 500))):
        part_id = layer["part_id"]
        source = resolve(layer["output_path"])
        dest = parts_dir / f"{part_id}.png"
        shutil.copy2(source, dest)
        image = Image.open(dest).convert("RGBA")
        bbox, coverage = bbox_alpha(image)
        mesh = mesh_for_part(part_id, bbox, CANVAS)
        mesh_path = meshes_dir / f"{part_id}.json"
        mesh["mesh_path"] = f"meshes/{mesh_path.name}"
        write_json(mesh_path, mesh)
        parts.append(
            {
                "id": part_id,
                "display_name": part_id,
                "source_path": f"parts/{dest.name}",
                "original_source_path": str(source),
                "bbox": bbox,
                "alpha_coverage": coverage,
                "draw_order": int(layer.get("draw_order", 500)),
                "folder": layer.get("folder", "Accessory"),
            }
        )
        meshes.append(mesh)

    deformers = build_deformers(parts, groups, CANVAS)
    character = {
        "schema_version": 1,
        "project_kind": "mini_cubism_v0",
        "experiment_id": f"{exp.name}-targeted",
        "generated_at": now(),
        "source_selection": "targeted_split_v1/targeted_layer_manifest.json",
        "canvas_size": CANVAS,
        "parts": parts,
        "meshes": meshes,
        "deformers": deformers,
        "parameters": PARAMETERS,
        "keyform_bindings": build_keyform_bindings(),
        "part_opacity_keyframes": opacity_keyframes_targeted(),
        "mouth_visibility_groups": manifest["mouth_visibility_groups"],
        "eye_visibility_groups": {
            "parameter_ids": {"left": "ParamEyeLOpen", "right": "ParamEyeROpen"},
            "closed_hidden_parts": manifest["eye_closed_hidden_parts"],
        },
        "eye_closed_hidden_parts": manifest["eye_closed_hidden_parts"],
        "vertex_weights": [],
        "physics_profiles": physics_profiles(),
        "physics_requirements": {
            "minimum_active_profiles": 6,
            "minimum_physics_targets": 12,
            "targeted_split_physics_target_candidates": manifest["counts"]["physics_targets"],
            "settle_frame_limit": 40,
        },
        "glue": [],
        "notes": [
            "Built from targeted split v1 candidate layers.",
            "Generated/derived keypose parts are candidate evidence, not production art approval.",
            "This is local Mini Cubism preview evidence, not Cubism CMO3/MOC3 compatibility.",
        ],
    }
    physics_targets = sorted({target for profile in character["physics_profiles"] for target in profile["targets"] if target in {part["id"] for part in parts}})
    character["vertex_weights"] = [
        vertex_weight(character, target, "root_to_tip" if any(key in target for key in ["hair", "bang", "lock", "ribbon_tail", "frill"]) else "full")
        for target in physics_targets
    ]
    write_json(project / "character.json", character)
    write_json(project / "deformers" / "deformers.json", deformers)
    write_json(project / "parameters" / "parameters.json", PARAMETERS)
    write_json(project / "motions" / "default_pose.json", {"schema_version": 1, "parameters": {parameter["id"]: parameter["default"] for parameter in PARAMETERS}})
    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "BUILT_PENDING_VALIDATION",
        "project": str(project),
        "source_manifest": str(manifest_path),
        "counts": {
            "parts": len(parts),
            "meshes": len(meshes),
            "deformers": len(deformers),
            "parameters": len(PARAMETERS),
            "keyform_bindings": len(character["keyform_bindings"]),
            "physics_profiles": len(character["physics_profiles"]),
            "vertex_weights": len(character["vertex_weights"]),
        },
    }
    write_json(project / "reports" / "build_report.json", report)
    return {"ok": True, "project": str(project), "counts": report["counts"]}


def main() -> int:
    result = build()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

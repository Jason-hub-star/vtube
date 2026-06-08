#!/usr/bin/env python3
"""Validate a Mini Cubism v0 project contract."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_PARAMETERS = {"ParamAngleX", "ParamEyeLOpen", "ParamEyeROpen", "ParamMouthOpenY", "ParamHairFront"}


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        fail(f"missing file: {path}")
    return json.loads(path.read_text())


def validate_mesh(mesh: dict[str, Any], project: Path) -> None:
    part_id = mesh.get("part_id")
    vertices = mesh.get("vertices")
    triangles = mesh.get("triangles")
    uvs = mesh.get("uvs")
    if not part_id:
        fail("mesh missing part_id")
    if not isinstance(vertices, list) or len(vertices) < 3:
        fail(f"{part_id} has too few vertices")
    if not isinstance(uvs, list) or len(uvs) != len(vertices):
        fail(f"{part_id} uv count mismatch")
    if not isinstance(triangles, list) or not triangles:
        fail(f"{part_id} has no triangles")
    for idx, vertex in enumerate(vertices):
        if not isinstance(vertex, list) or len(vertex) != 2:
            fail(f"{part_id} vertex {idx} invalid")
    for triangle in triangles:
        if not isinstance(triangle, list) or len(triangle) != 3:
            fail(f"{part_id} triangle invalid: {triangle}")
        for index in triangle:
            if not isinstance(index, int) or index < 0 or index >= len(vertices):
                fail(f"{part_id} triangle index out of range: {triangle}")
    mesh_path = mesh.get("mesh_path")
    if mesh_path and not (project / mesh_path).exists():
        fail(f"{part_id} mesh_path missing: {mesh_path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    project = Path(args.project).resolve()
    character_path = project / "character.json"
    character = load_json(character_path)
    if character.get("schema_version") != 1:
        fail("schema_version must be 1")
    if character.get("project_kind") != "mini_cubism_v0":
        fail("project_kind must be mini_cubism_v0")
    canvas = character.get("canvas_size")
    if not isinstance(canvas, list) or len(canvas) != 2 or min(canvas) <= 0:
        fail("canvas_size invalid")

    parts = character.get("parts")
    meshes = character.get("meshes")
    deformers = character.get("deformers")
    parameters = character.get("parameters")
    bindings = character.get("keyform_bindings")
    if not isinstance(parts, list) or len(parts) < 15:
        fail(f"expected at least 15 parts, got {len(parts) if isinstance(parts, list) else 'invalid'}")
    if not isinstance(meshes, list) or len(meshes) != len(parts):
        fail("mesh count must match part count")
    part_ids = set()
    for part in parts:
        for field in ["id", "display_name", "source_path", "bbox", "alpha_coverage", "draw_order", "folder"]:
            if field not in part:
                fail(f"part missing {field}: {part}")
        part_path = project / part["source_path"]
        if not part_path.exists():
            fail(f"part image missing: {part_path}")
        if part["id"] in part_ids:
            fail(f"duplicate part id: {part['id']}")
        part_ids.add(part["id"])
        bbox = part["bbox"]
        if not isinstance(bbox, list) or len(bbox) != 4 or bbox[2] <= 0 or bbox[3] <= 0:
            fail(f"{part['id']} invalid bbox: {bbox}")

    for mesh in meshes:
        validate_mesh(mesh, project)
        if mesh["part_id"] not in part_ids:
            fail(f"mesh references unknown part: {mesh['part_id']}")

    if not isinstance(deformers, list) or len(deformers) < 5:
        fail("expected deformer hierarchy")
    deformer_ids = {deformer.get("id") for deformer in deformers}
    for deformer in deformers:
        for child in deformer.get("child_ids", []):
            if child not in part_ids:
                fail(f"deformer {deformer.get('id')} references unknown child {child}")
        parent = deformer.get("parent_id")
        if parent is not None and parent not in deformer_ids:
            fail(f"deformer {deformer.get('id')} references unknown parent {parent}")

    parameter_ids = {parameter.get("id") for parameter in parameters or []}
    missing = REQUIRED_PARAMETERS - parameter_ids
    if missing:
        fail(f"missing required parameters: {sorted(missing)}")
    if not isinstance(bindings, list) or not bindings:
        fail("missing keyform bindings")
    bound_parameters = {binding.get("parameter_id") for binding in bindings}
    for parameter_id in REQUIRED_PARAMETERS:
        if parameter_id not in bound_parameters:
            fail(f"parameter has no binding: {parameter_id}")
    for binding in bindings:
        target = binding.get("target_id")
        if target not in deformer_ids and target not in part_ids:
            fail(f"binding target missing: {target}")
        if binding.get("parameter_id") not in parameter_ids:
            fail(f"binding parameter missing: {binding.get('parameter_id')}")

    if character.get("glue") != []:
        fail("v0 glue must be an empty placeholder array")

    report = {
        "schema_version": 1,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "project": str(project),
        "status": "PASS",
        "counts": {
            "parts": len(parts),
            "meshes": len(meshes),
            "deformers": len(deformers),
            "parameters": len(parameters),
            "keyform_bindings": len(bindings),
            "glue": 0,
        },
    }
    reports_dir = project / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "validation_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"ok": True, "report": str(report_path), "counts": report["counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

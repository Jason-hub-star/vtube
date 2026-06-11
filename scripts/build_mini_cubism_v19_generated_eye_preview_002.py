#!/usr/bin/env python3
"""Build Character 002 v19 by replacing v15 eye assets with generated clean eye materials."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
DEFAULT_SOURCE = EXP / "model_edit_v15_eye_nose_position_preview/mini_cubism_diagnostic_project"
DEFAULT_LAYERS = EXP / "generated_eye_v19/normalized_layers"
DEFAULT_OUT = EXP / "model_edit_v19_generated_eye_preview/mini_cubism_diagnostic_project"
DEFAULT_REPORTS = EXP / "reports/model_edit_v19_generated_eye_preview"
CANVAS = [2048, 2048]
REPLACED_PARTS = ["eye_L_white", "eye_R_white", "eye_L_iris", "eye_R_iris"]
HIDDEN_PARTS = ["eye_L_pupil", "eye_R_pupil", "eye_L_highlight", "eye_R_highlight"]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def bbox_metrics(image: Image.Image) -> tuple[list[int], int, float]:
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError("empty alpha")
    nonzero = int(sum(alpha.histogram()[1:]))
    return [bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]], nonzero, round(nonzero / (CANVAS[0] * CANVAS[1]), 8)


def mesh_for_part(part_id: str, bbox: list[int]) -> dict[str, Any]:
    x, y, width, height = bbox
    cols = 4
    rows = 3
    vertices: list[list[float]] = []
    uvs: list[list[float]] = []
    triangles: list[list[int]] = []
    for row in range(rows + 1):
        for col in range(cols + 1):
            vx = x + width * col / cols
            vy = y + height * row / rows
            vertices.append([round(vx, 3), round(vy, 3)])
            uvs.append([round(vx / CANVAS[0], 6), round(vy / CANVAS[1], 6)])
    for row in range(rows):
        for col in range(cols):
            a = row * (cols + 1) + col
            b = a + 1
            c = a + cols + 1
            d = c + 1
            triangles.append([a, c, b])
            triangles.append([b, c, d])
    return {"part_id": part_id, "vertices": vertices, "triangles": triangles, "uvs": uvs, "mesh_path": f"meshes/{part_id}.json"}


def replace_part(character: dict[str, Any], project: Path, layers: Path, part_id: str) -> dict[str, Any]:
    src = layers / f"{part_id}.png"
    if not src.exists():
        raise FileNotFoundError(src)
    image = Image.open(src).convert("RGBA")
    if list(image.size) != CANVAS:
        raise ValueError(f"{part_id} must be {CANVAS}, got {image.size}")
    bbox, nonzero, coverage = bbox_metrics(image)
    shutil.copy2(src, project / "parts" / f"{part_id}.png")
    mesh = mesh_for_part(part_id, bbox)
    (project / "meshes" / f"{part_id}.json").write_text(json.dumps(mesh, ensure_ascii=False, indent=2) + "\n")
    for part in character.get("parts", []):
        if part.get("id") == part_id:
            part["source_path"] = f"parts/{part_id}.png"
            part["original_source_path"] = str(src)
            part["bbox"] = bbox
            part["alpha_coverage"] = coverage
            tags = set(part.get("risk_tags", []))
            tags.add("generated_eye_v19")
            if part_id.endswith("_iris"):
                tags.add("coherent_iris_pupil_highlight_baked")
            if part_id.endswith("_white"):
                tags.add("clean_fixed_eye_white")
            part["risk_tags"] = sorted(tags)
            break
    character["meshes"] = [row for row in character.get("meshes", []) if row.get("part_id") != part_id] + [mesh]
    return {"bbox_xywh": bbox, "alpha_nonzero": nonzero, "alpha_coverage": coverage, "source": rel(src)}


def hide_old_detail_parts(character: dict[str, Any]) -> None:
    character["keyform_bindings"] = [
        row
        for row in character.get("keyform_bindings", [])
        if not (row.get("target_id") in HIDDEN_PARTS and row.get("parameter_id") in {"ParamEyeBallX", "ParamEyeBallY"})
    ]
    hidden = set(HIDDEN_PARTS)
    character["part_opacity_keyframes"] = [
        row for row in character.get("part_opacity_keyframes", []) if row.get("part_id") not in hidden
    ]
    for side in ["L", "R"]:
        p = f"ParamEye{side}Open"
        for suffix in ["pupil", "highlight"]:
            character.setdefault("part_opacity_keyframes", []).append(
                {
                    "part_id": f"eye_{side}_{suffix}",
                    "parameter_id": p,
                    "mode": "linear",
                    "purpose": "v19 hide old split detail; pupil/highlight baked into generated eye_{side}_iris",
                    "keyframes": [{"value": 0.27, "opacity": 0}, {"value": 1.0, "opacity": 0}],
                }
            )


def keep_eye_ball_bindings_to_generated_iris(character: dict[str, Any]) -> None:
    detail_targets = {"eye_L_iris", "eye_R_iris", *HIDDEN_PARTS}
    character["keyform_bindings"] = [
        row
        for row in character.get("keyform_bindings", [])
        if not (row.get("parameter_id") in {"ParamEyeBallX", "ParamEyeBallY"} and row.get("target_id") in detail_targets)
    ]
    for part_id in ["eye_L_iris", "eye_R_iris"]:
        for parameter_id, key_value, translate in [
            ("ParamEyeBallX", -1, [-7.5, 0]),
            ("ParamEyeBallX", 1, [7.5, 0]),
            ("ParamEyeBallY", -1, [0, -4.5]),
            ("ParamEyeBallY", 1, [0, 4.5]),
        ]:
            character["keyform_bindings"].append(
                {
                    "parameter_id": parameter_id,
                    "key_value": key_value,
                    "target_id": part_id,
                    "delta_type": "deformer_transform",
                    "deltas": {"translate": translate, "scale": [1, 1], "rotate": 0, "opacity": 1},
                }
            )


def sort_project(character: dict[str, Any]) -> None:
    character["parts"] = sorted(character["parts"], key=lambda row: (row.get("draw_order", 0), row.get("id", "")))
    order = {part["id"]: index for index, part in enumerate(character["parts"])}
    character["meshes"] = sorted(character["meshes"], key=lambda row: order.get(row.get("part_id"), 9999))
    character["keyform_bindings"] = sorted(
        character["keyform_bindings"],
        key=lambda row: (row.get("parameter_id", ""), row.get("target_id", ""), float(row.get("key_value", 0))),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-project", default=str(DEFAULT_SOURCE))
    parser.add_argument("--layers", default=str(DEFAULT_LAYERS))
    parser.add_argument("--out-project", default=str(DEFAULT_OUT))
    parser.add_argument("--reports", default=str(DEFAULT_REPORTS))
    args = parser.parse_args()

    source_project = Path(args.source_project).resolve()
    layers = Path(args.layers).resolve()
    out_project = Path(args.out_project).resolve()
    reports = Path(args.reports).resolve()
    if out_project.exists():
        shutil.rmtree(out_project)
    shutil.copytree(source_project, out_project)
    reports.mkdir(parents=True, exist_ok=True)

    character_path = out_project / "character.json"
    character = json.loads(character_path.read_text())
    replaced = {part_id: replace_part(character, out_project, layers, part_id) for part_id in REPLACED_PARTS}
    hide_old_detail_parts(character)
    keep_eye_ball_bindings_to_generated_iris(character)

    character["experiment_id"] = "cubism-v2-new-character-002/model_edit_v19_generated_eye_preview"
    character["generated_at"] = now()
    character["notes"] = character.get("notes", []) + [
        "v19 preserves v15 mouth, nose, eye height, EyeOpen 0.27 clamp, and MouthOpenY 0.85 clamp.",
        "v19 replaces fixed eye white assets with generated clean whites and replaces eye_L/R_iris with coherent generated iris+pupil+highlight assets.",
        "v19 hides old split pupil/highlight layers because pupil/highlight are baked into the generated iris layer.",
    ]
    sort_project(character)
    character_path.write_text(json.dumps(character, ensure_ascii=False, indent=2) + "\n")

    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "V19_GENERATED_EYE_READY_FOR_VALIDATION",
        "source_project": rel(source_project),
        "project": rel(out_project),
        "generated_layers": rel(layers),
        "replaced_parts": replaced,
        "hidden_old_detail_parts": HIDDEN_PARTS,
        "policy": {
            "fixed_eye_white": ["eye_L_white", "eye_R_white"],
            "moving_eye_detail": ["eye_L_iris", "eye_R_iris"],
            "pupil_highlight_baked_into_iris": True,
            "preserve_v15_non_eye_state": True,
        },
    }
    report_path = reports / "mini_cubism_v19_generated_eye_report.json"
    write_json(report_path, report)
    print(json.dumps({"ok": True, "report": str(report_path), "project": str(out_project)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

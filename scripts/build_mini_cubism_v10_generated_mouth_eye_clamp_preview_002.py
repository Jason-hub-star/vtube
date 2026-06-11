#!/usr/bin/env python3
"""Build Character 002 generated-mouth preview with EyeOpen min clamp."""

from __future__ import annotations

import json
import shutil
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SRC_PROJECT = EXP / "model_edit_v8_existing_mouth_tuned_preview/mini_cubism_diagnostic_project"
GENERATED_LAYERS = EXP / "generated_mouth_v10/normalized_layers"
OUT_PROJECT = EXP / "model_edit_v10_generated_mouth_eye_clamp_preview/mini_cubism_diagnostic_project"
REPORTS = EXP / "reports/model_edit_v10_generated_mouth_eye_clamp_preview"
CANVAS_SIZE = [2048, 2048]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def bbox_from_alpha(path: Path) -> tuple[list[int], int, int]:
    image = Image.open(path).convert("RGBA")
    if list(image.size) != CANVAS_SIZE:
        raise ValueError(f"expected {CANVAS_SIZE}, got {image.size}: {path}")
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError(f"empty alpha: {path}")
    left, top, right, bottom = bbox
    hist = alpha.histogram()
    nonzero = int(sum(hist[1:]))
    total = image.width * image.height
    return [left, top, right - left, bottom - top], nonzero, total


def mesh_for_part(part_id: str, bbox: list[int], canvas_size: list[int]) -> dict[str, Any]:
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
            uvs.append([round(vx / canvas_size[0], 6), round(vy / canvas_size[1], 6)])
    for row in range(rows):
        for col in range(cols):
            a = row * (cols + 1) + col
            b = a + 1
            c = a + cols + 1
            d = c + 1
            triangles.append([a, c, b])
            triangles.append([b, c, d])
    return {"part_id": part_id, "vertices": vertices, "triangles": triangles, "uvs": uvs, "mesh_path": f"meshes/{part_id}.json"}


def part_record(part_id: str, source_path: Path, draw_order: int, risk_tag: str) -> dict[str, Any]:
    bbox, nonzero, total = bbox_from_alpha(source_path)
    return {
        "id": part_id,
        "display_name": part_id,
        "source_path": f"parts/{part_id}.png",
        "original_source_path": str(source_path),
        "bbox": bbox,
        "alpha_coverage": round(nonzero / total, 8),
        "draw_order": draw_order,
        "folder": "Mouth",
        "deformer_node": "mouth_warp",
        "material_group": "mouth",
        "risk_tags": [risk_tag],
    }


def opacity_key(part_id: str, parameter_id: str, frames: list[tuple[float, float]], mode: str = "linear") -> dict[str, Any]:
    return {
        "part_id": part_id,
        "parameter_id": parameter_id,
        "mode": mode,
        "keyframes": [{"value": value, "opacity": opacity} for value, opacity in frames],
    }


def mouth_binding(key_value: float, translate_y: float, scale_y: float) -> dict[str, Any]:
    return {
        "parameter_id": "ParamMouthOpenY",
        "key_value": key_value,
        "target_id": "mouth_warp",
        "delta_type": "deformer_transform",
        "deltas": {"translate": [0, translate_y], "scale": [1, scale_y], "rotate": 0, "opacity": 1},
    }


def upsert_mouth_part(character: dict[str, Any], project: Path, part_id: str, source: Path, draw_order: int, risk_tag: str) -> None:
    parts_dir = project / "parts"
    meshes_dir = project / "meshes"
    target = parts_dir / f"{part_id}.png"
    shutil.copy2(source, target)
    part = part_record(part_id, target, draw_order, risk_tag)
    mesh = mesh_for_part(part_id, part["bbox"], CANVAS_SIZE)
    (meshes_dir / f"{part_id}.json").write_text(json.dumps(mesh, ensure_ascii=False, indent=2) + "\n")
    character["parts"] = [row for row in character.get("parts", []) if row.get("id") != part_id] + [part]
    character["meshes"] = [row for row in character.get("meshes", []) if row.get("part_id") != part_id] + [mesh]
    for deformer in character.get("deformers", []):
        if deformer.get("id") == "mouth_warp":
            child_ids = [child for child in deformer.get("child_ids", []) if child != part_id]
            child_ids.append(part_id)
            deformer["child_ids"] = child_ids


def sort_project(character: dict[str, Any]) -> None:
    character["parts"] = sorted(character["parts"], key=lambda row: (row.get("draw_order", 0), row.get("id", "")))
    order = {part["id"]: index for index, part in enumerate(character["parts"])}
    character["meshes"] = sorted(character["meshes"], key=lambda row: order.get(row.get("part_id"), 9999))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", default="v10")
    parser.add_argument("--source-project", default=str(SRC_PROJECT))
    parser.add_argument("--generated-layers", default=str(GENERATED_LAYERS))
    parser.add_argument("--out-project", default=str(OUT_PROJECT))
    parser.add_argument("--reports", default=str(REPORTS))
    parser.add_argument("--mouth-max", type=float, default=1.0)
    args = parser.parse_args()

    variant = args.variant
    source_project = Path(args.source_project).resolve()
    generated_layers = Path(args.generated_layers).resolve()
    out_project = Path(args.out_project).resolve()
    reports = Path(args.reports).resolve()
    mouth_map = {
        "mouth_closed_smile": generated_layers / "mouth_smile_closed_gen.png",
        "mouth_small_open": generated_layers / "mouth_smile_small_open_gen.png",
        "mouth_mid_teeth_gen": generated_layers / "mouth_smile_mid_teeth_gen.png",
        "mouth_wide_teeth_tongue_gen": generated_layers / "mouth_smile_wide_teeth_tongue_gen.png",
    }
    risk_tag = f"generated_mouth_{variant}"

    if out_project.exists():
        shutil.rmtree(out_project)
    shutil.copytree(source_project, out_project)
    reports.mkdir(parents=True, exist_ok=True)

    character_path = out_project / "character.json"
    character = json.loads(character_path.read_text())

    for param in character.get("parameters", []):
        if param.get("id") in {"ParamEyeLOpen", "ParamEyeROpen"}:
            param["min"] = 0.27
            param["default"] = 1
            param["key_values"] = [0.27, 0.5, 1]
        if param.get("id") == "ParamMouthOpenY":
            param["max"] = args.mouth_max
            param["default"] = min(float(param.get("default", 0)), args.mouth_max)
            param["key_values"] = sorted({0, 0.5, args.mouth_max})

    draw_orders = {
        "mouth_closed_smile": 400,
        "mouth_small_open": 410,
        "mouth_mid_teeth_gen": 420,
        "mouth_wide_teeth_tongue_gen": 430,
    }
    for part_id, source in mouth_map.items():
        upsert_mouth_part(character, out_project, part_id, source, draw_orders[part_id], risk_tag)

    generated_mouth_ids = set(mouth_map)
    hidden_old_helpers = {"mouth_inner", "mouth_teeth", "mouth_tongue"}
    character["part_opacity_keyframes"] = [
        row
        for row in character.get("part_opacity_keyframes", [])
        if not str(row.get("part_id", "")).startswith("mouth_")
    ] + [
        opacity_key("mouth_closed_smile", "ParamMouthOpenY", [(0.0, 1.0), (0.22, 0.88), (0.40, 0.30), (0.55, 0.0), (1.0, 0.0)]),
        opacity_key("mouth_small_open", "ParamMouthOpenY", [(0.0, 0.0), (0.18, 0.20), (0.35, 0.90), (0.55, 0.40), (0.68, 0.0), (1.0, 0.0)]),
        opacity_key("mouth_mid_teeth_gen", "ParamMouthOpenY", [(0.0, 0.0), (0.38, 0.0), (0.58, 0.95), (0.78, 0.35), (0.90, 0.0), (1.0, 0.0)]),
        opacity_key("mouth_wide_teeth_tongue_gen", "ParamMouthOpenY", [(0.0, 0.0), (0.65, 0.0), (0.82, 0.72), (1.0, 1.0)]),
        opacity_key("mouth_inner", "ParamMouthOpenY", [(0.0, 0.0), (1.0, 0.0)]),
        opacity_key("mouth_teeth", "ParamMouthOpenY", [(0.0, 0.0), (1.0, 0.0)]),
        opacity_key("mouth_tongue", "ParamMouthOpenY", [(0.0, 0.0), (1.0, 0.0)]),
    ]

    character["keyform_bindings"] = [
        binding
        for binding in character.get("keyform_bindings", [])
        if not (binding.get("parameter_id") == "ParamMouthOpenY" and binding.get("target_id") == "mouth_warp")
    ] + [
        mouth_binding(0.5, 0.8, 1.01),
        mouth_binding(1.0, 1.6, 1.02),
    ]

    character["experiment_id"] = f"cubism-v2-new-character-002/model_edit_{variant}_generated_mouth_eye_clamp_preview"
    character["generated_at"] = now()
    character["notes"] = character.get("notes", []) + [
        f"{variant} uses newly generated smile-open mouth keyposes normalized from a chroma-key sheet.",
        f"{variant} clamps ParamEyeLOpen and ParamEyeROpen min to 0.27 so the UI and automation cannot drive eyes more closed than the natural-close threshold.",
        f"{variant} keeps old mouth_inner/teeth/tongue hidden because the generated wide keypose already includes natural teeth/tongue.",
    ]
    sort_project(character)
    character_path.write_text(json.dumps(character, ensure_ascii=False, indent=2) + "\n")

    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": f"{variant.upper()}_GENERATED_MOUTH_EYE_CLAMP_READY_FOR_VALIDATION",
        "source_project": rel(source_project),
        "project": rel(out_project),
        "generated_mouth_layers": {part_id: rel(path) for part_id, path in mouth_map.items()},
        "eye_clamp": {"ParamEyeLOpen": {"min": 0.27}, "ParamEyeROpen": {"min": 0.27}},
        "mouth_clamp": {"ParamMouthOpenY": {"max": args.mouth_max}},
        "active_mouth_parts": sorted(generated_mouth_ids),
        "hidden_old_helpers": sorted(hidden_old_helpers),
    }
    report_path = reports / f"mini_cubism_{variant}_generated_mouth_eye_clamp_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"ok": True, "report": str(report_path), "project": str(out_project)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

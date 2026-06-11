#!/usr/bin/env python3
"""Build a Character 002 Mini Cubism preview with all existing mouth assets enabled."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SRC_PROJECT = EXP / "model_edit_v8_existing_mouth_tuned_preview/mini_cubism_diagnostic_project"
WIDE_SOURCE = EXP / "reports/model_edit_v8_existing_mouth_packet/normalized_layers/mouth_wide_open.png"
OUT_PROJECT = EXP / "model_edit_v9_all_mouth_enabled_preview/mini_cubism_diagnostic_project"
REPORTS = EXP / "reports/model_edit_v9_all_mouth_enabled_preview"
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


def part_record(part_id: str, source_path: Path, draw_order: int) -> dict[str, Any]:
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
        "risk_tags": ["diagnostic_keypose_layer", "all_mouth_enabled"],
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


def ensure_param(character: dict[str, Any]) -> None:
    if any(param.get("id") == "ParamMouthForm" for param in character.get("parameters", [])):
        return
    character["parameters"].append({"id": "ParamMouthForm", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]})


def upsert_part_and_mesh(character: dict[str, Any], project: Path, part_id: str, source: Path, draw_order: int) -> None:
    parts_dir = project / "parts"
    meshes_dir = project / "meshes"
    parts_dir.mkdir(parents=True, exist_ok=True)
    meshes_dir.mkdir(parents=True, exist_ok=True)
    target_image = parts_dir / f"{part_id}.png"
    if source.resolve() != target_image.resolve():
        shutil.copy2(source, target_image)
    part = part_record(part_id, target_image, draw_order)
    character["parts"] = [row for row in character.get("parts", []) if row.get("id") != part_id] + [part]
    mesh = mesh_for_part(part_id, part["bbox"], CANVAS_SIZE)
    (meshes_dir / f"{part_id}.json").write_text(json.dumps(mesh, ensure_ascii=False, indent=2) + "\n")
    character["meshes"] = [row for row in character.get("meshes", []) if row.get("part_id") != part_id] + [mesh]
    for deformer in character.get("deformers", []):
        if deformer.get("id") == "mouth_warp":
            child_ids = [child for child in deformer.get("child_ids", []) if child != part_id]
            child_ids.append(part_id)
            deformer["child_ids"] = child_ids


def sort_parts(character: dict[str, Any]) -> None:
    character["parts"] = sorted(character["parts"], key=lambda row: (row.get("draw_order", 0), row.get("id", "")))
    order = {part["id"]: index for index, part in enumerate(character["parts"])}
    character["meshes"] = sorted(character["meshes"], key=lambda row: order.get(row.get("part_id"), 9999))


def main() -> int:
    if OUT_PROJECT.exists():
        shutil.rmtree(OUT_PROJECT)
    shutil.copytree(SRC_PROJECT, OUT_PROJECT)
    REPORTS.mkdir(parents=True, exist_ok=True)

    character_path = OUT_PROJECT / "character.json"
    character = json.loads(character_path.read_text())
    ensure_param(character)

    upsert_part_and_mesh(character, OUT_PROJECT, "mouth_o_vowel", OUT_PROJECT / "parts/mouth_o_vowel.png", 430)
    upsert_part_and_mesh(character, OUT_PROJECT, "mouth_wide_open", WIDE_SOURCE, 420)

    active_mouth_ids = {
        "mouth_closed_smile",
        "mouth_small_open",
        "mouth_wide_open",
        "mouth_o_vowel",
        "mouth_inner",
        "mouth_teeth",
        "mouth_tongue",
    }
    non_mouth_opacity = [
        row
        for row in character.get("part_opacity_keyframes", [])
        if row.get("part_id") not in active_mouth_ids
    ]
    character["part_opacity_keyframes"] = non_mouth_opacity + [
        opacity_key("mouth_closed_smile", "ParamMouthOpenY", [(0.0, 1.0), (0.25, 0.85), (0.45, 0.35), (0.65, 0.0), (1.0, 0.0)]),
        opacity_key("mouth_small_open", "ParamMouthOpenY", [(0.0, 0.0), (0.20, 0.15), (0.40, 0.90), (0.58, 0.55), (0.75, 0.0), (1.0, 0.0)]),
        opacity_key("mouth_wide_open", "ParamMouthOpenY", [(0.0, 0.0), (0.45, 0.0), (0.65, 0.55), (0.82, 0.92), (1.0, 1.0)]),
        opacity_key("mouth_inner", "ParamMouthOpenY", [(0.0, 0.0), (0.35, 0.0), (0.60, 0.28), (0.82, 0.55), (1.0, 0.65)]),
        opacity_key("mouth_teeth", "ParamMouthOpenY", [(0.0, 0.0), (0.48, 0.0), (0.72, 0.25), (1.0, 0.42)]),
        opacity_key("mouth_tongue", "ParamMouthOpenY", [(0.0, 0.0), (0.62, 0.0), (0.82, 0.22), (1.0, 0.38)]),
        opacity_key("mouth_o_vowel", "ParamMouthForm", [(-1.0, 1.0), (-0.45, 0.35), (0.0, 0.0), (1.0, 0.0)]),
    ]

    character["keyform_bindings"] = [
        binding
        for binding in character.get("keyform_bindings", [])
        if not (binding.get("parameter_id") == "ParamMouthOpenY" and binding.get("target_id") == "mouth_warp")
    ] + [
        mouth_binding(0.5, 2.0, 1.04),
        mouth_binding(1.0, 5.0, 1.10),
    ]

    character["experiment_id"] = "cubism-v2-new-character-002/model_edit_v9_all_mouth_enabled_preview"
    character["generated_at"] = now()
    character["notes"] = character.get("notes", []) + [
        "v9 diagnostic enables every existing generated mouth asset, including previously excluded mouth_o_vowel and mouth_wide_open.",
        "v9 is for visual comparison only; it does not change the previous rejection evidence for O/wide mouth quality.",
        "mouth_inner, mouth_teeth, and mouth_tongue are now visible at higher MouthOpenY values for this diagnostic version.",
    ]
    sort_parts(character)
    character_path.write_text(json.dumps(character, ensure_ascii=False, indent=2) + "\n")

    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "V9_ALL_MOUTH_ENABLED_READY_FOR_VALIDATION",
        "source_project": rel(SRC_PROJECT),
        "project": rel(OUT_PROJECT),
        "enabled_mouth_parts": sorted(active_mouth_ids),
        "parameters": [param["id"] for param in character.get("parameters", [])],
        "note": "Diagnostic comparison only; all mouth assets are active by request.",
    }
    report_path = REPORTS / "mini_cubism_v9_all_mouth_enabled_preview_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (REPORTS / "mini_cubism_v9_all_mouth_enabled_preview_report.md").write_text(
        "\n".join(
            [
                "# Mini Cubism v9 All Mouth Enabled Preview",
                "",
                f"- status: `{report['status']}`",
                f"- project: `{report['project']}`",
                "- all existing generated mouth assets are active for diagnostic review.",
                "- previous O/wide rejection evidence is preserved; this is not a production approval.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "report": str(report_path), "project": str(OUT_PROJECT)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

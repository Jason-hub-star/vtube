#!/usr/bin/env python3
"""Build Character 002 v20 by applying saved manual eye-detail anchors from v19."""

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
DEFAULT_SOURCE = EXP / "model_edit_v19_generated_eye_preview/mini_cubism_diagnostic_project"
DEFAULT_OVERRIDES = EXP / "reports/model_edit_v19_generated_eye_preview/manual_eye_detail_anchor_v1/manual_eye_detail_anchor_overrides.json"
DEFAULT_OUT = EXP / "model_edit_v20_manual_eye_anchor_preview/mini_cubism_diagnostic_project"
DEFAULT_REPORTS = EXP / "reports/model_edit_v20_manual_eye_anchor_preview"
CANVAS = [2048, 2048]
SIDES = {"L": "eye_L_iris", "R": "eye_R_iris"}


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


def shift_full_canvas(image: Image.Image, dx: int, dy: int) -> Image.Image:
    shifted = Image.new("RGBA", tuple(CANVAS), (0, 0, 0, 0))
    shifted.paste(image, (dx, dy), image)
    return shifted


def apply_anchor_shift(character: dict[str, Any], project: Path, side: str, current: list[float], anchor: list[float]) -> dict[str, Any]:
    part_id = SIDES[side]
    raw_dx = float(anchor[0]) - float(current[0])
    raw_dy = float(anchor[1]) - float(current[1])
    dx = int(round(raw_dx))
    dy = int(round(raw_dy))
    part_path = project / "parts" / f"{part_id}.png"
    image = Image.open(part_path).convert("RGBA")
    if list(image.size) != CANVAS:
        raise ValueError(f"{part_id} must be {CANVAS}, got {image.size}")
    shifted = shift_full_canvas(image, dx, dy)
    shifted.save(part_path)
    bbox, nonzero, coverage = bbox_metrics(shifted)
    mesh = mesh_for_part(part_id, bbox)
    write_json(project / "meshes" / f"{part_id}.json", mesh)

    for part in character.get("parts", []):
        if part.get("id") == part_id:
            part["bbox"] = bbox
            part["alpha_coverage"] = coverage
            part["original_source_path"] = f"{part.get('original_source_path', '')} + v20_manual_anchor_shift({dx},{dy})"
            tags = set(part.get("risk_tags", []))
            tags.add("manual_eye_anchor_v20")
            tags.add("drag_zoom_anchor_corrected")
            part["risk_tags"] = sorted(tags)
            break
    character["meshes"] = [row for row in character.get("meshes", []) if row.get("part_id") != part_id] + [mesh]
    return {
        "part_id": part_id,
        "current_center": current,
        "target_anchor": anchor,
        "raw_delta_xy": [round(raw_dx, 3), round(raw_dy, 3)],
        "applied_integer_delta_xy": [dx, dy],
        "result_bbox_xywh": bbox,
        "alpha_nonzero": nonzero,
        "alpha_coverage": coverage,
    }


def sort_project(character: dict[str, Any]) -> None:
    character["parts"] = sorted(character["parts"], key=lambda row: (row.get("draw_order", 0), row.get("id", "")))
    order = {part["id"]: index for index, part in enumerate(character["parts"])}
    character["meshes"] = sorted(character["meshes"], key=lambda row: order.get(row.get("part_id"), 9999))
    character["keyform_bindings"] = sorted(
        character.get("keyform_bindings", []),
        key=lambda row: (row.get("parameter_id", ""), row.get("target_id", ""), float(row.get("key_value", 0))),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-project", default=str(DEFAULT_SOURCE))
    parser.add_argument("--overrides", default=str(DEFAULT_OVERRIDES))
    parser.add_argument("--out-project", default=str(DEFAULT_OUT))
    parser.add_argument("--reports", default=str(DEFAULT_REPORTS))
    args = parser.parse_args()

    source_project = Path(args.source_project).resolve()
    overrides_path = Path(args.overrides).resolve()
    out_project = Path(args.out_project).resolve()
    reports = Path(args.reports).resolve()
    if not (source_project / "character.json").exists():
        raise FileNotFoundError(source_project / "character.json")
    if not overrides_path.exists():
        raise FileNotFoundError(overrides_path)
    overrides = json.loads(overrides_path.read_text())
    if overrides.get("status") != "SAVED":
        raise ValueError(f"manual overrides are not saved: {overrides_path}")

    if out_project.exists():
        shutil.rmtree(out_project)
    shutil.copytree(source_project, out_project)
    reports.mkdir(parents=True, exist_ok=True)

    character_path = out_project / "character.json"
    character = json.loads(character_path.read_text())
    shifts = {}
    for side in ["L", "R"]:
        shifts[side] = apply_anchor_shift(character, out_project, side, overrides["current"][side], overrides["anchors"][side])

    character["experiment_id"] = "cubism-v2-new-character-002/model_edit_v20_manual_eye_anchor_preview"
    character["generated_at"] = now()
    character["notes"] = character.get("notes", []) + [
        "v20 starts from v19 generated-eye preview and applies 주인님-saved manual eye-detail anchors.",
        "v20 keeps fixed generated eye whites still; only coherent eye_L/R_iris assets are shifted to match the manual anchors.",
        "v20 preserves EyeOpen min 0.27, MouthOpenY max 0.85, generated mouth state, and old split pupil/highlight hidden state.",
    ]
    sort_project(character)
    character_path.write_text(json.dumps(character, ensure_ascii=False, indent=2) + "\n")

    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "V20_MANUAL_EYE_ANCHOR_READY_FOR_VALIDATION",
        "source_project": rel(source_project),
        "project": rel(out_project),
        "manual_overrides": rel(overrides_path),
        "shifts": shifts,
        "policy": {
            "white_parts_stay_fixed": ["eye_L_white", "eye_R_white"],
            "moving_parts": ["eye_L_iris", "eye_R_iris"],
            "full_canvas_rgba": CANVAS,
            "human_anchor_editor": "scripts/run_v19_eye_detail_anchor_editor_002.py",
        },
    }
    report_path = reports / "mini_cubism_v20_manual_eye_anchor_report.json"
    write_json(report_path, report)
    print(json.dumps({"ok": True, "report": str(report_path), "project": str(out_project), "shifts": shifts}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

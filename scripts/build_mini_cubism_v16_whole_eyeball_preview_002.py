#!/usr/bin/env python3
"""Build Character 002 v16 by moving the full eyeball group on EyeBall X/Y."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
DEFAULT_SOURCE = EXP / "model_edit_v15_eye_nose_position_preview/mini_cubism_diagnostic_project"
DEFAULT_OUT = EXP / "model_edit_v16_whole_eyeball_preview/mini_cubism_diagnostic_project"
DEFAULT_REPORTS = EXP / "reports/model_edit_v16_whole_eyeball_preview"

EYEBALL_PARTS = [
    "eye_L_white",
    "eye_L_iris",
    "eye_L_pupil",
    "eye_L_highlight",
    "eye_R_white",
    "eye_R_iris",
    "eye_R_pupil",
    "eye_R_highlight",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def binding(parameter_id: str, target_id: str, key_value: float, translate: list[float]) -> dict[str, Any]:
    return {
        "parameter_id": parameter_id,
        "key_value": key_value,
        "target_id": target_id,
        "delta_type": "deformer_transform",
        "deltas": {"translate": translate, "scale": [1, 1], "rotate": 0, "opacity": 1},
    }


def update_eye_ball_bindings(character: dict[str, Any], strength_x: float, strength_y: float) -> None:
    targets = set(EYEBALL_PARTS)
    character["keyform_bindings"] = [
        row
        for row in character.get("keyform_bindings", [])
        if not (row.get("parameter_id") in {"ParamEyeBallX", "ParamEyeBallY"} and row.get("target_id") in targets)
    ]
    for part_id in sorted(targets):
        character["keyform_bindings"].extend(
            [
                binding("ParamEyeBallX", part_id, -1, [-strength_x, 0]),
                binding("ParamEyeBallX", part_id, 1, [strength_x, 0]),
                binding("ParamEyeBallY", part_id, -1, [0, -strength_y]),
                binding("ParamEyeBallY", part_id, 1, [0, strength_y]),
            ]
        )
        for part in character.get("parts", []):
            if part.get("id") == part_id:
                tags = set(part.get("risk_tags", []))
                tags.add("v16_whole_eyeball_motion")
                part["risk_tags"] = sorted(tags)
                break


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
    parser.add_argument("--out-project", default=str(DEFAULT_OUT))
    parser.add_argument("--reports", default=str(DEFAULT_REPORTS))
    parser.add_argument("--eye-ball-x", type=float, default=7.5)
    parser.add_argument("--eye-ball-y", type=float, default=4.5)
    args = parser.parse_args()

    source_project = Path(args.source_project).resolve()
    out_project = Path(args.out_project).resolve()
    reports = Path(args.reports).resolve()
    if out_project.exists():
        shutil.rmtree(out_project)
    shutil.copytree(source_project, out_project)
    reports.mkdir(parents=True, exist_ok=True)

    character_path = out_project / "character.json"
    character = json.loads(character_path.read_text())
    update_eye_ball_bindings(character, args.eye_ball_x, args.eye_ball_y)
    character["experiment_id"] = "cubism-v2-new-character-002/model_edit_v16_whole_eyeball_preview"
    character["generated_at"] = now()
    character["notes"] = character.get("notes", []) + [
        "v16 preserves v15 eye height, nose_detail, EyeOpen 0.27 clamp, and MouthOpenY 0.85 clamp.",
        "v16 moves the full diagnostic eyeball group on ParamEyeBallX/Y: white, iris, pupil, and highlight share identical deltas.",
        "Lids/lashes stay fixed so the eyeball moves inside the eye opening.",
    ]
    sort_project(character)
    character_path.write_text(json.dumps(character, ensure_ascii=False, indent=2) + "\n")

    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "V16_WHOLE_EYEBALL_READY_FOR_VALIDATION",
        "source_project": rel(source_project),
        "project": rel(out_project),
        "eye_ball_binding_strength": {"x": args.eye_ball_x, "y": args.eye_ball_y},
        "eye_ball_parts": EYEBALL_PARTS,
        "policy": {
            "preserve_v15_eye_height": True,
            "preserve_nose_detail": True,
            "preserve_v13_mouth_pattern": True,
            "eye_open_min": 0.27,
            "mouth_open_y_max": 0.85,
            "production_claim": "diagnostic only; full eyeball motion requires human visual QA before promotion",
        },
    }
    report_path = reports / "mini_cubism_v16_whole_eyeball_report.json"
    write_json(report_path, report)
    print(json.dumps({"ok": True, "report": str(report_path), "project": str(out_project)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

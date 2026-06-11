#!/usr/bin/env python3
"""Build a v7 Mini Cubism preview with smooth mouth and unsupported sliders removed."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SRC_PROJECT = EXP / "model_edit_v6_no_wide_open/mini_cubism_diagnostic_project"
OUT_PROJECT = EXP / "model_edit_v7_smooth_mouth_preview/mini_cubism_diagnostic_project"
REPORTS = EXP / "reports/model_edit_v7_smooth_mouth_preview"
REMOVED_ACTIVE_PARTS = {"mouth_o_vowel"}
REMOVED_PARAMETERS = {"ParamEyeBallX", "ParamEyeBallY", "ParamMouthForm"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def opacity_key(part_id: str, parameter_id: str, frames: list[tuple[float, float]], mode: str = "linear") -> dict[str, Any]:
    return {
        "part_id": part_id,
        "parameter_id": parameter_id,
        "mode": mode,
        "keyframes": [{"value": value, "opacity": opacity} for value, opacity in frames],
    }


def main() -> int:
    if OUT_PROJECT.exists():
        shutil.rmtree(OUT_PROJECT)
    shutil.copytree(SRC_PROJECT, OUT_PROJECT)
    REPORTS.mkdir(parents=True, exist_ok=True)

    character_path = OUT_PROJECT / "character.json"
    character = json.loads(character_path.read_text())

    active_parts = [part for part in character["parts"] if part["id"] not in REMOVED_ACTIVE_PARTS]
    active_part_ids = {part["id"] for part in active_parts}
    character["parts"] = active_parts
    character["meshes"] = [mesh for mesh in character["meshes"] if mesh.get("part_id") in active_part_ids]
    character["parameters"] = [param for param in character["parameters"] if param.get("id") not in REMOVED_PARAMETERS]
    character["keyform_bindings"] = [
        binding
        for binding in character.get("keyform_bindings", [])
        if binding.get("parameter_id") not in REMOVED_PARAMETERS and binding.get("target_id") in active_part_ids | {d["id"] for d in character.get("deformers", [])}
    ]

    for deformer in character.get("deformers", []):
        deformer["child_ids"] = [child for child in deformer.get("child_ids", []) if child in active_part_ids]

    non_mouth = [
        row
        for row in character.get("part_opacity_keyframes", [])
        if not str(row.get("part_id", "")).startswith("mouth_") and row.get("part_id") in active_part_ids
    ]
    character["part_opacity_keyframes"] = non_mouth + [
        opacity_key("mouth_closed_smile", "ParamMouthOpenY", [(0.0, 1.0), (0.35, 0.35), (0.65, 0.0), (1.0, 0.0)]),
        opacity_key("mouth_small_open", "ParamMouthOpenY", [(0.0, 0.0), (0.25, 0.45), (0.55, 1.0), (1.0, 1.0)]),
        opacity_key("mouth_inner", "ParamMouthOpenY", [(0.0, 0.0), (1.0, 0.0)]),
        opacity_key("mouth_teeth", "ParamMouthOpenY", [(0.0, 0.0), (1.0, 0.0)]),
        opacity_key("mouth_tongue", "ParamMouthOpenY", [(0.0, 0.0), (1.0, 0.0)]),
    ]

    character["experiment_id"] = "cubism-v2-new-character-002/model_edit_v7_smooth_mouth_preview"
    character["generated_at"] = now()
    notes = character.get("notes", [])
    notes.extend(
        [
            "v7 removes unsupported ParamEyeBallX/Y and ParamMouthForm from diagnostic UI because current eye and mouth sources are not separated into eyeball/vowel controls.",
            "v7 keeps ParamHairFront only for contract compatibility; it remains visually unsupported because there is no independent front hair part in this keypose pack.",
            "v7 uses linear opacity crossfade for mouth_closed_smile -> mouth_small_open; mouth_wide_open and mouth_o_vowel are excluded from active preview.",
        ]
    )
    character["notes"] = notes
    character_path.write_text(json.dumps(character, ensure_ascii=False, indent=2) + "\n")

    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "V7_SMOOTH_MOUTH_PREVIEW_READY_FOR_VALIDATION",
        "source_project": rel(SRC_PROJECT),
        "project": rel(OUT_PROJECT),
        "removed_active_parts": sorted(REMOVED_ACTIVE_PARTS),
        "removed_parameters": sorted(REMOVED_PARAMETERS),
        "remaining_parts": len(character["parts"]),
        "remaining_parameters": [param["id"] for param in character["parameters"]],
        "mouth_policy": "ParamMouthOpenY crossfades closed_smile and small_open. Wide open and MouthForm/o_vowel are not active in this diagnostic preview.",
        "unsupported": {
            "ParamHairFront": "No independent front_hair part exists in this keypose pack.",
            "eyeball": "No separated iris/pupil/highlight parts exist; eye_open is a baked eye image.",
        },
    }
    (REPORTS / "mini_cubism_v7_smooth_mouth_preview_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (REPORTS / "mini_cubism_v7_smooth_mouth_preview_report.md").write_text(
        "\n".join(
            [
                "# Mini Cubism v7 Smooth Mouth Preview",
                "",
                f"- status: `{report['status']}`",
                f"- project: `{report['project']}`",
                f"- removed active parts: `{report['removed_active_parts']}`",
                f"- removed parameters: `{report['removed_parameters']}`",
                "- ParamHairFront remains unsupported until a separated front hair part exists.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "report": str(REPORTS / "mini_cubism_v7_smooth_mouth_preview_report.json"), "project": str(OUT_PROJECT)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

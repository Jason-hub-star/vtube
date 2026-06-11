#!/usr/bin/env python3
"""Build a v8 Mini Cubism preview tuned for existing generated mouth assets only."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SRC_PROJECT = EXP / "model_edit_v7_smooth_mouth_preview/mini_cubism_diagnostic_project"
OUT_PROJECT = EXP / "model_edit_v8_existing_mouth_tuned_preview/mini_cubism_diagnostic_project"
REPORTS = EXP / "reports/model_edit_v8_existing_mouth_tuned_preview"


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


def mouth_binding(key_value: float, translate_y: float, scale_y: float) -> dict[str, Any]:
    return {
        "parameter_id": "ParamMouthOpenY",
        "key_value": key_value,
        "target_id": "mouth_warp",
        "delta_type": "deformer_transform",
        "deltas": {"translate": [0, translate_y], "scale": [1, scale_y], "rotate": 0, "opacity": 1},
    }


def main() -> int:
    if OUT_PROJECT.exists():
        shutil.rmtree(OUT_PROJECT)
    shutil.copytree(SRC_PROJECT, OUT_PROJECT)
    REPORTS.mkdir(parents=True, exist_ok=True)

    character_path = OUT_PROJECT / "character.json"
    character = json.loads(character_path.read_text())

    non_mouth_opacity = [
        row
        for row in character.get("part_opacity_keyframes", [])
        if not str(row.get("part_id", "")).startswith("mouth_")
    ]
    character["part_opacity_keyframes"] = non_mouth_opacity + [
        opacity_key("mouth_closed_smile", "ParamMouthOpenY", [(0.0, 1.0), (0.25, 0.92), (0.50, 0.55), (0.75, 0.22), (1.0, 0.0)]),
        opacity_key("mouth_small_open", "ParamMouthOpenY", [(0.0, 0.0), (0.20, 0.10), (0.50, 0.42), (0.75, 0.74), (1.0, 1.0)]),
        opacity_key("mouth_inner", "ParamMouthOpenY", [(0.0, 0.0), (1.0, 0.0)]),
        opacity_key("mouth_teeth", "ParamMouthOpenY", [(0.0, 0.0), (1.0, 0.0)]),
        opacity_key("mouth_tongue", "ParamMouthOpenY", [(0.0, 0.0), (1.0, 0.0)]),
    ]

    character["keyform_bindings"] = [
        binding
        for binding in character.get("keyform_bindings", [])
        if not (binding.get("parameter_id") == "ParamMouthOpenY" and binding.get("target_id") == "mouth_warp")
    ] + [
        mouth_binding(0.5, 1.0, 1.015),
        mouth_binding(1.0, 2.0, 1.03),
    ]

    character["experiment_id"] = "cubism-v2-new-character-002/model_edit_v8_existing_mouth_tuned_preview"
    character["generated_at"] = now()
    notes = character.get("notes", [])
    notes.extend(
        [
            "v8 uses only already generated active mouth PNGs: mouth_closed_smile and mouth_small_open.",
            "v8 keeps mouth_inner/teeth/tongue as hidden reference helpers and keeps mouth_o_vowel/mouth_wide_open excluded from active preview.",
            "v8 reduces mouth_warp movement from v7 translate [0,8], scale [1,1.15] to a mild translate/scale ramp to reduce visual popping.",
            "v8 uses a wider overlap opacity crossfade so closed_smile fades out while small_open fades in gradually.",
        ]
    )
    character["notes"] = notes
    character_path.write_text(json.dumps(character, ensure_ascii=False, indent=2) + "\n")

    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "V8_EXISTING_MOUTH_TUNED_PREVIEW_READY_FOR_VALIDATION",
        "source_project": rel(SRC_PROJECT),
        "project": rel(OUT_PROJECT),
        "active_mouth_parts": ["mouth_closed_smile", "mouth_small_open"],
        "reference_only_mouth_parts": ["mouth_inner", "mouth_teeth", "mouth_tongue"],
        "excluded_mouth_parts": ["mouth_o_vowel", "mouth_wide_open"],
        "mouth_policy": "Use existing generated mouth assets only; tune opacity and mouth_warp timing before generating new art.",
        "mouth_warp_policy": {
            "v7": {"key_value": 1.0, "translate": [0, 8], "scale": [1, 1.15]},
            "v8": [
                {"key_value": 0.5, "translate": [0, 1.0], "scale": [1, 1.015]},
                {"key_value": 1.0, "translate": [0, 2.0], "scale": [1, 1.03]},
            ],
        },
    }
    report_path = REPORTS / "mini_cubism_v8_existing_mouth_tuned_preview_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (REPORTS / "mini_cubism_v8_existing_mouth_tuned_preview_report.md").write_text(
        "\n".join(
            [
                "# Mini Cubism v8 Existing Mouth Tuned Preview",
                "",
                f"- status: `{report['status']}`",
                f"- project: `{report['project']}`",
                "- active mouth parts: `mouth_closed_smile`, `mouth_small_open`",
                "- generated new mouth art: `false`",
                "- `mouth_o_vowel` and `mouth_wide_open` remain excluded from active preview.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "report": str(report_path), "project": str(OUT_PROJECT)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

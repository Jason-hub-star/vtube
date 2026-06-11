#!/usr/bin/env python3
"""Build Character 002 v21 supported-control Mini Cubism rig smoke from v20."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
DEFAULT_SOURCE = EXP / "model_edit_v20_manual_eye_anchor_preview/mini_cubism_diagnostic_project"
DEFAULT_OUT = EXP / "model_edit_v21_supported_rig_smoke_preview/mini_cubism_diagnostic_project"
DEFAULT_REPORTS = EXP / "reports/model_edit_v21_supported_rig_smoke_preview"
UNSUPPORTED_PARAMETERS = {"ParamHairFront": "front_hair_warp has no child parts; keep contract parameter but hide from active preview"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-project", default=str(DEFAULT_SOURCE))
    parser.add_argument("--out-project", default=str(DEFAULT_OUT))
    parser.add_argument("--reports", default=str(DEFAULT_REPORTS))
    args = parser.parse_args()

    source = Path(args.source_project).resolve()
    out = Path(args.out_project).resolve()
    reports = Path(args.reports).resolve()
    if not (source / "character.json").exists():
        raise FileNotFoundError(source / "character.json")
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(source, out)
    reports.mkdir(parents=True, exist_ok=True)

    character_path = out / "character.json"
    character = json.loads(character_path.read_text())
    original_counts = {
        "parameters": len(character.get("parameters", [])),
        "deformers": len(character.get("deformers", [])),
        "keyform_bindings": len(character.get("keyform_bindings", [])),
    }
    character["unsupported_parameters"] = {
        parameter_id: {
            "reason": reason,
            "hide_in_preview": True,
            "keep_for_contract_validation": True,
        }
        for parameter_id, reason in UNSUPPORTED_PARAMETERS.items()
    }
    character["experiment_id"] = "cubism-v2-new-character-002/model_edit_v21_supported_rig_smoke_preview"
    character["generated_at"] = now()
    character["notes"] = character.get("notes", []) + [
        "v21 starts from v20 and marks unsupported ParamHairFront/front_hair_warp hidden from active Mini Cubism preview while keeping it for validator contract compatibility.",
        "v21 supported controls: ParamAngleX, ParamEyeBallX/Y, ParamEyeLOpen/ROpen, ParamMouthOpenY.",
        "HairFront remains a production asset gap until independent front hair parts exist.",
    ]
    character_path.write_text(json.dumps(character, ensure_ascii=False, indent=2) + "\n")

    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "V21_SUPPORTED_RIG_SMOKE_READY_FOR_VALIDATION",
        "source_project": rel(source),
        "project": rel(out),
        "unsupported_parameters": character["unsupported_parameters"],
        "original_counts": original_counts,
        "new_counts": {
            "parameters": len(character.get("parameters", [])),
            "deformers": len(character.get("deformers", [])),
            "keyform_bindings": len(character.get("keyform_bindings", [])),
        },
        "active_controls": [
            row["id"]
            for row in character.get("parameters", [])
            if row["id"] not in character["unsupported_parameters"]
        ],
        "policy": {
            "exclude_fake_sliders": True,
            "hair_front_requires_independent_parts": True,
            "mini_cubism_only_not_real_cubism_authoring": True,
        },
    }
    report_path = reports / "mini_cubism_v21_supported_rig_smoke_report.json"
    write_json(report_path, report)
    print(json.dumps({"ok": True, "report": str(report_path), "project": str(out)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

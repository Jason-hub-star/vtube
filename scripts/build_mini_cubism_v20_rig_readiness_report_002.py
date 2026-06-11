#!/usr/bin/env python3
"""Build a v20 rig-readiness and v21 scope report for Character 002."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
DEFAULT_PROJECT = EXP / "model_edit_v20_manual_eye_anchor_preview/mini_cubism_diagnostic_project"
DEFAULT_REPORTS = EXP / "reports/model_edit_v20_manual_eye_anchor_preview/rig_readiness_v1"
DEFAULT_POSE_SWEEP = EXP / "reports/model_edit_v20_manual_eye_anchor_preview/rig_readiness_pose_sweep_v1/reports/pose_sweep_report.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def deformer_by_id(character: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in character.get("deformers", [])}


def binding_targets(character: dict[str, Any], parameter_id: str) -> set[str]:
    targets = {row.get("target_id") for row in character.get("keyform_bindings", []) if row.get("parameter_id") == parameter_id}
    targets |= {row.get("part_id") for row in character.get("part_opacity_keyframes", []) if row.get("parameter_id") == parameter_id}
    return {str(target) for target in targets if target}


def classify_controls(character: dict[str, Any]) -> dict[str, Any]:
    deformers = deformer_by_id(character)
    params = {row["id"]: row for row in character.get("parameters", [])}
    controls: dict[str, Any] = {}
    for parameter_id, param in params.items():
        targets = sorted(binding_targets(character, parameter_id))
        status = "UNKNOWN"
        reason = ""
        v21_action = "manual review"
        if parameter_id in {"ParamEyeBallX", "ParamEyeBallY"}:
            whites_targeted = any(target.endswith("_white") for target in targets)
            iris_targets = [target for target in targets if target.endswith("_iris")]
            status = "SUPPORTED_DIAGNOSTIC"
            reason = "moves coherent generated iris+pupil+highlight detail layers while fixed whites stay still"
            v21_action = "keep and tune movement strength only if 주인님 sees drift"
            if whites_targeted or len(iris_targets) < 2:
                status = "REVISE"
                reason = "expected both iris layers only, with no white movement"
        elif parameter_id in {"ParamEyeLOpen", "ParamEyeROpen"}:
            status = "SUPPORTED_DIAGNOSTIC_CLAMPED"
            reason = f"keypose/opacity eye close is clamped at min {param.get('min')}; 0.0 is intentionally not exposed"
            v21_action = "keep; use automation/canvas proof because UI pose sweep can under-report eye close"
        elif parameter_id == "ParamMouthOpenY":
            status = "SUPPORTED_DIAGNOSTIC_KEYPOSE"
            reason = "mouth opens through diagnostic keypose opacity/mouth_warp, not final phoneme-ready Cubism mouth rig"
            v21_action = "keep for v21 smoke; production mouth still needs final visual acceptance"
        elif parameter_id == "ParamAngleX":
            status = "PARTIAL_DIAGNOSTIC"
            reason = "head_angle_warp exists, but Mini Cubism preview is still a local deformer approximation, not real Cubism hierarchy proof"
            v21_action = "include in v21 smoke, then validate through real Cubism deformer hierarchy later"
        elif parameter_id == "ParamHairFront":
            target = targets[0] if targets else ""
            child_ids = deformers.get(target, {}).get("child_ids", []) if target else []
            if not child_ids:
                status = "UNSUPPORTED_CONTRACT_ONLY"
                reason = "front_hair_warp has no child parts; slider cannot visibly move hair"
                v21_action = "remove from active v21 smoke or create/separate real front hair parts first"
            else:
                status = "SUPPORTED_DIAGNOSTIC"
                reason = "front hair deformer has child parts"
                v21_action = "keep"
        controls[parameter_id] = {
            "range": [param.get("min"), param.get("max")],
            "default": param.get("default"),
            "targets": targets,
            "status": status,
            "reason": reason,
            "v21_action": v21_action,
        }
    return controls


def build_report(project: Path, reports: Path, pose_sweep_path: Path | None) -> dict[str, Any]:
    character = load_json(project / "character.json")
    validation_path = project / "reports/validation_report.json"
    validation = load_json(validation_path) if validation_path.exists() else None
    pose_sweep = load_json(pose_sweep_path) if pose_sweep_path and pose_sweep_path.exists() else None
    controls = classify_controls(character)
    part_ids = {row["id"] for row in character.get("parts", [])}
    front_hair_parts = sorted(part_id for part_id in part_ids if part_id.startswith("hair_front") or part_id.startswith("front_hair"))
    mouth_parts = sorted(part_id for part_id in part_ids if part_id.startswith("mouth_"))
    eye_parts = sorted(part_id for part_id in part_ids if part_id.startswith("eye_"))
    blocked = [
        "ParamHairFront is contract-only because no independent front hair parts are present",
        "v20 has 36 diagnostic parts, below the confirmed v2_standard 64-part production target",
        "Mini Cubism diagnostic PASS does not prove real Cubism ArtMesh/Deformer/Keyform authoring",
        "mouth is still diagnostic keypose/crossfade and needs human visual acceptance before production mouth rigging",
    ]
    ready_for_v21 = all(
        controls.get(parameter_id, {}).get("status", "").startswith("SUPPORTED")
        or controls.get(parameter_id, {}).get("status") == "PARTIAL_DIAGNOSTIC"
        for parameter_id in ["ParamAngleX", "ParamEyeBallX", "ParamEyeBallY", "ParamEyeLOpen", "ParamEyeROpen", "ParamMouthOpenY"]
    )
    status = "READY_FOR_V21_SUPPORTED_CONTROL_RIG_SMOKE_NOT_REAL_CUBISM_READY" if ready_for_v21 else "REVISE_BEFORE_V21_RIG_SMOKE"
    if controls.get("ParamHairFront", {}).get("status") == "UNSUPPORTED_CONTRACT_ONLY":
        status = "READY_FOR_V21_SUPPORTED_CONTROL_RIG_SMOKE_WITH_HAIR_EXCLUDED"
    return {
        "schema_version": 1,
        "generated_at": now(),
        "status": status,
        "project": rel(project),
        "validation": {
            "path": rel(validation_path) if validation_path.exists() else None,
            "status": validation.get("status") if validation else None,
            "counts": validation.get("counts") if validation else None,
        },
        "pose_sweep": {
            "path": rel(pose_sweep_path) if pose_sweep_path and pose_sweep_path.exists() else None,
            "status": pose_sweep.get("status") if pose_sweep else None,
            "score": pose_sweep.get("score") if pose_sweep else None,
            "summary": pose_sweep.get("summary") if pose_sweep else None,
            "note": "UI-driven pose sweep may under-report eye close; use automation smoke for parameter support before final judgment.",
        },
        "counts": {
            "parts": len(part_ids),
            "eye_parts": len(eye_parts),
            "mouth_parts": len(mouth_parts),
            "front_hair_parts": len(front_hair_parts),
            "parameters": len(character.get("parameters", [])),
            "deformers": len(character.get("deformers", [])),
            "keyform_bindings": len(character.get("keyform_bindings", [])),
        },
        "controls": controls,
        "front_hair_parts": front_hair_parts,
        "v21_scope": {
            "include": [
                "ParamAngleX local diagnostic motion",
                "ParamEyeBallX/Y generated iris detail motion",
                "ParamEyeLOpen/ROpen clamped keypose blink",
                "ParamMouthOpenY diagnostic mouth open",
            ],
            "exclude_until_assets_exist": ["ParamHairFront"],
            "first_v21_task": "build a supported-controls-only Mini Cubism rig smoke/review packet from v20 and hide or clearly mark unsupported HairFront",
        },
        "real_cubism_blockers": blocked,
        "decision": "Proceed to v21 Mini Cubism supported-control rig smoke, not final Cubism authoring, unless 주인님 first accepts v20 human visual QA.",
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Character 002 v20 Rig Readiness",
        "",
        f"- Status: `{report['status']}`",
        f"- Project: `{report['project']}`",
        f"- Validator: `{report['validation']['status']}`",
        f"- Pose sweep: `{report['pose_sweep']['status']}` score `{report['pose_sweep']['score']}`",
        "",
        "## Supported Controls",
        "",
        "| Parameter | Status | Targets | v21 action |",
        "|---|---|---|---|",
    ]
    for parameter_id, row in report["controls"].items():
        targets = ", ".join(row["targets"]) or "-"
        lines.append(f"| `{parameter_id}` | `{row['status']}` | `{targets}` | {row['v21_action']} |")
    lines.extend(
        [
            "",
            "## v21 Scope",
            "",
            "Include:",
        ]
    )
    lines.extend([f"- {item}" for item in report["v21_scope"]["include"]])
    lines.extend(["", "Exclude until assets exist:"])
    lines.extend([f"- {item}" for item in report["v21_scope"]["exclude_until_assets_exist"]])
    lines.extend(["", "## Real Cubism Blockers", ""])
    lines.extend([f"- {item}" for item in report["real_cubism_blockers"]])
    lines.extend(["", "## Decision", "", report["decision"], ""])
    path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=str(DEFAULT_PROJECT))
    parser.add_argument("--reports", default=str(DEFAULT_REPORTS))
    parser.add_argument("--pose-sweep", default=str(DEFAULT_POSE_SWEEP))
    args = parser.parse_args()

    project = Path(args.project).resolve()
    reports = Path(args.reports).resolve()
    pose_sweep = Path(args.pose_sweep).resolve() if args.pose_sweep else None
    if not (project / "character.json").exists():
        raise FileNotFoundError(project / "character.json")
    report = build_report(project, reports, pose_sweep)
    reports.mkdir(parents=True, exist_ok=True)
    json_path = reports / "v20_rig_readiness_report.json"
    md_path = reports / "v20_rig_readiness_report.md"
    write_json(json_path, report)
    write_markdown(report, md_path)
    print(json.dumps({"ok": True, "status": report["status"], "report": str(json_path), "markdown": str(md_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

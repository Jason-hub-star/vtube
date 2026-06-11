#!/usr/bin/env python3
"""Build G6 HairFront anchor-correction input and override template.

The packet turns the G6 anchor probe into a reproducible manual-correction
contract. It deliberately saves no accepted override values and grants no
material acceptance, ParamHairFront activation, G7, or real Cubism promotion.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/Users/family/jason/Vtube")
EXP = ROOT / "experiments/cubism-v2-new-character-002"
PROBE = EXP / "reports/v22_g6_hairfront_anchor_probe/v22_g6_hairfront_anchor_probe_packet.json"
REPORT_DIR = EXP / "reports/v22_g6_hairfront_anchor_correction_input"
REPORT_JSON = REPORT_DIR / "v22_g6_hairfront_anchor_correction_input_packet.json"
REPORT_MD = REPORT_DIR / "v22_g6_hairfront_anchor_correction_input_packet.md"
OVERRIDE_TEMPLATE = REPORT_DIR / "manual_hairfront_anchor_overrides.template.json"

STATUS = "G6_HAIRFRONT_ANCHOR_CORRECTION_INPUT_READY_OVERRIDES_NOT_SAVED_PARAM_HIDDEN"
VERDICT = "CORRECTION_INPUT_READY_NO_OVERRIDE_APPLIED_NOT_MATERIAL_PASS"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def override_entry(row: dict) -> dict:
    anchor = row["anchor_center"]
    return {
        "row_id": row["row_id"],
        "path": row["path"],
        "current_anchor": anchor,
        "target_anchor": anchor,
        "delta": [0, 0],
        "scale": 1.0,
        "opacity": 1.0,
        "motion_envelope_bbox": row["motion_envelope_bbox"],
        "bbox": row["bbox"],
        "status": "TEMPLATE_PENDING_VISUAL_REVIEW",
        "action": "REVIEW_THEN_KEEP_MOVE_OR_REGENERATE",
        "saved_override": False,
        "notes": "",
    }


def main() -> int:
    probe = load_json(PROBE)
    entries = [override_entry(row) for row in probe["hairfront_rows"]]
    template = {
        "schema_version": "v1",
        "status": "TEMPLATE_READY_NO_SAVED_OVERRIDES",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_anchor_probe": rel(PROBE),
        "source_status": probe["status"],
        "instructions": [
            "Review each HairFront row visually before changing target_anchor.",
            "Set saved_override true only for rows that were intentionally moved or accepted as a manual override.",
            "Use action KEEP_CURRENT, MOVE_ANCHOR, or REGENERATE_SOURCE_CANDIDATE after review.",
            "Do not use this template as material acceptance or ParamHairFront activation.",
        ],
        "entries": entries,
        "locks": {
            "v21_eye_open_lower_bound": 0.27,
            "v21_mouth_open_y_max": 0.85,
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "validator_only_promotion_blocked": True,
            "material_pass_status": "BLOCKED",
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "not_owner_approval": True,
        },
    }
    save_json(OVERRIDE_TEMPLATE, template)

    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": STATUS,
        "source_anchor_probe": rel(PROBE),
        "source_status": probe["status"],
        "override_template": rel(OVERRIDE_TEMPLATE),
        "correction_input_verdict": VERDICT,
        "correction_rows": entries,
        "summary": {
            "hairfront_row_count": probe["summary"]["hairfront_row_count"],
            "anchor_probe_row_count": probe["summary"]["anchor_probe_row_count"],
            "correction_input_row_count": len(entries),
            "override_template_entry_count": len(template["entries"]),
            "current_anchor_count": sum(1 for entry in entries if entry["current_anchor"]),
            "target_anchor_default_count": sum(
                1 for entry in entries if entry["target_anchor"] == entry["current_anchor"]
            ),
            "zero_delta_default_count": sum(1 for entry in entries if entry["delta"] == [0, 0]),
            "saved_override_count": sum(1 for entry in entries if entry["saved_override"]),
            "manual_anchor_override_ready_count": len(entries),
            "manual_anchor_override_applied_count": 0,
            "regeneration_route_ready_count": len(entries),
            "codex_visual_acceptance_pass_count": 0,
            "motion_readiness_pass_count": 0,
            "param_hairfront_activation_count": 0,
            "material_acceptance_pass_count": 0,
            "owner_approval_count": 0,
            "g6_anchor_correction_status": "INPUT_READY_OVERRIDES_NOT_SAVED",
            "g5_material_acceptance_status": "BLOCKED_HAIRFRONT_CORRECTION_INPUT_REVIEW_REQUIRED",
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE",
            "g8_real_cubism_status": "BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE",
        },
        "gate_matrix": {
            "G6_HAIRFRONT_ANCHOR_CORRECTION_INPUT": "READY_OVERRIDES_NOT_SAVED",
            "G6_MANUAL_ANCHOR_CORRECTION": "BLOCKED_UNTIL_OVERRIDE_JSON_SAVED_OR_REGENERATION_SELECTED",
            "G5_MATERIAL_ACCEPTANCE": "BLOCKED_HAIRFRONT_CORRECTION_INPUT_REVIEW_REQUIRED",
            "G7_MINI_CUBISM_DIAGNOSTIC": "BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE",
            "G8_REAL_CUBISM_AUTHORING": "BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE",
        },
        "locks": {
            "v21_eye_open_lower_bound": 0.27,
            "v21_mouth_open_y_max": 0.85,
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "validator_only_promotion_blocked": True,
            "codex_visual_not_owner_approval": True,
            "material_pass_status": "BLOCKED",
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "not_owner_approval": True,
        },
        "decision": (
            "HairFront anchor correction input and an override template are ready. No override "
            "has been saved or applied, so this does not grant material acceptance, "
            "ParamHairFront activation, G7, or real Cubism readiness."
        ),
        "next_action": [
            "Serve or reuse a drag/zoom editor that writes a reviewed override JSON from this template.",
            "If visual review rejects a row instead of moving it, route that row to regeneration.",
            "After saved overrides exist, rebuild shifted full-canvas HairFront PNGs and rerun overlay/anchor probe QA.",
        ],
        "self_review": {
            "source_status": probe["status"],
            "override_template_exists": OVERRIDE_TEMPLATE.exists(),
            "hairfront_row_count": probe["summary"]["hairfront_row_count"],
            "correction_input_row_count": len(entries),
            "override_template_entry_count": len(template["entries"]),
            "current_anchor_count": sum(1 for entry in entries if entry["current_anchor"]),
            "target_anchor_default_count": sum(
                1 for entry in entries if entry["target_anchor"] == entry["current_anchor"]
            ),
            "zero_delta_default_count": sum(1 for entry in entries if entry["delta"] == [0, 0]),
            "saved_override_count": 0,
            "manual_anchor_override_ready_count": len(entries),
            "manual_anchor_override_applied_count": 0,
            "regeneration_route_ready_count": len(entries),
            "codex_visual_acceptance_pass_count": 0,
            "motion_readiness_pass_count": 0,
            "param_hairfront_activation_count": 0,
            "material_acceptance_pass_count": 0,
            "owner_approval_count": 0,
            "g5_material_not_accepted": True,
            "validator_only_promotion_blocked": True,
            "codex_visual_not_owner_approval": True,
            "material_pass_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "not_owner_approval": True,
            "status": "PASS",
        },
    }
    save_json(REPORT_JSON, report)

    lines = [
        "# Character 002 v22 G6 HairFront Anchor Correction Input",
        "",
        f"- status: `{report['status']}`",
        f"- verdict: `{report['correction_input_verdict']}`",
        f"- source: `{report['source_anchor_probe']}`",
        f"- override template: `{report['override_template']}`",
        f"- G5 material acceptance: `{report['summary']['g5_material_acceptance_status']}`",
        f"- ParamHairFront: `{report['summary']['param_hair_front_status']}`",
        "",
        "## Counts",
        "",
        f"- correction_input_row_count: `{report['summary']['correction_input_row_count']}`",
        f"- override_template_entry_count: `{report['summary']['override_template_entry_count']}`",
        f"- current_anchor_count: `{report['summary']['current_anchor_count']}`",
        f"- target_anchor_default_count: `{report['summary']['target_anchor_default_count']}`",
        f"- zero_delta_default_count: `{report['summary']['zero_delta_default_count']}`",
        f"- saved_override_count: `{report['summary']['saved_override_count']}`",
        f"- manual_anchor_override_ready_count: `{report['summary']['manual_anchor_override_ready_count']}`",
        f"- manual_anchor_override_applied_count: `{report['summary']['manual_anchor_override_applied_count']}`",
        f"- regeneration_route_ready_count: `{report['summary']['regeneration_route_ready_count']}`",
        f"- material_acceptance_pass_count: `{report['summary']['material_acceptance_pass_count']}`",
        "",
        "## Rows",
        "",
    ]
    for entry in entries:
        lines.append(
            f"- `{entry['row_id']}`: current `{entry['current_anchor']}`, "
            f"target `{entry['target_anchor']}`, delta `{entry['delta']}`, status `{entry['status']}`"
        )
    lines.extend(["", "## Next Action", ""])
    for action in report["next_action"]:
        lines.append(f"- {action}")
    lines.extend(
        [
            "",
            "## Self Review",
            "",
            "```json",
            json.dumps(report["self_review"], ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {REPORT_JSON}")
    print(f"Wrote {REPORT_MD}")
    print(f"Wrote {OVERRIDE_TEMPLATE}")
    print(STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

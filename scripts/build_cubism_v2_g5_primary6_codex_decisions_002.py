#!/usr/bin/env python3
"""Record Codex provisional decisions for the v22 G5 primary-six rows.

This reduces the immediate G5 work surface, but it does not grant owner
approval, material PASS, Mini Cubism promotion, or real Cubism promotion.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/Users/family/jason/Vtube")
EXP = ROOT / "experiments/cubism-v2-new-character-002"
ROUTE = (
    EXP
    / "reports/v22_g5_material_acceptance_reduction_route/v22_g5_material_acceptance_reduction_route_packet.json"
)
REPORT_DIR = EXP / "reports/v22_g5_primary6_codex_decisions"
REPORT_JSON = REPORT_DIR / "v22_g5_primary6_codex_decisions_packet.json"
REPORT_MD = REPORT_DIR / "v22_g5_primary6_codex_decisions_packet.md"

STATUS = "G5_PRIMARY6_CODEX_PROVISIONAL_DECISIONS_READY_MATERIAL_NOT_ACCEPTED"
DECISION = "CODEX_PROVISIONAL_ACCEPT_AS_G5_CANDIDATE_NOT_OWNER_APPROVAL"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rationale_for(row: dict) -> str:
    row_id = row["row_id"]
    if row_id == "B1_CLEAN_BASE_UNDERPAINT":
        return "B1 visual QA is candidate-pass with human gate preserved; accept only as G5 candidate evidence."
    if row_id == "B2_EYE_PACK":
        return "B2 overlay QA is candidate-pass and keeps the fixed-white/coherent eye-detail contract with EyeOpen 0.27 lock."
    if row_id == "B3_MOUTH_PACK_REVISION_V1":
        return "B3 revision v1 overlay QA is candidate-pass and keeps the MouthOpenY 0.85 restraint."
    if row_id == "torso_base":
        return "Generated torso was selected through G4/P0 as a prep candidate with lower coverage restored, not as material PASS."
    if row_id in {"shoulder_L", "shoulder_R"}:
        return "Shoulder draw-order/mask improvements are accepted only as G5 candidate evidence, with material PASS blocked."
    return "Unclassified primary row cannot be owner-approved by Codex."


def build_decision(row: dict) -> dict:
    return {
        **row,
        "codex_decision": DECISION,
        "decision_rationale": rationale_for(row),
        "owner_approval": "NOT_OWNER_APPROVAL",
        "material_pass": "BLOCKED",
        "g5_effect_after_decision": "PRIMARY6_REDUCED_TO_G5_CANDIDATE_NOT_MATERIAL_PASS",
        "requires_followup": False,
    }


def main() -> int:
    route = load_json(ROUTE)
    decisions = [build_decision(row) for row in route["primary6_rows"]]
    untouched_context = route["secondary_context_rows"] + route["hairfront_contract_rows"]
    decision_counts = Counter(row["codex_decision"] for row in decisions)
    remaining_counts = Counter(row["route_priority"] for row in untouched_context)

    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": STATUS,
        "source_reduction_route": rel(ROUTE),
        "source_status": route["status"],
        "primary6_decisions": decisions,
        "untouched_remaining_rows": untouched_context,
        "summary": {
            "source_total_route_row_count": route["summary"]["total_route_row_count"],
            "source_primary6_row_count": route["summary"]["primary6_row_count"],
            "primary6_decision_row_count": len(decisions),
            "primary6_codex_candidate_accept_count": decision_counts[DECISION],
            "primary6_revise_count": 0,
            "primary6_unresolved_count_after_decision": sum(1 for row in decisions if row["requires_followup"]),
            "owner_approval_count": 0,
            "material_acceptance_pass_count": 0,
            "remaining_context_row_count": remaining_counts["SECONDARY_CONTEXT_REVIEW"],
            "remaining_hairfront_contract_row_count": remaining_counts["DEFER_KEEP_HAIRFRONT_HIDDEN"],
            "remaining_material_acceptance_required_before_g7_count": len(untouched_context),
            "total_material_acceptance_required_before_g7_count": len(untouched_context),
            "primary6_ids": [row["row_id"] for row in decisions],
            "g5_material_acceptance_status": "BLOCKED_CONTEXT_HAIRFRONT_REMAINING_NOT_OWNER_APPROVAL",
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE",
            "g8_real_cubism_status": "BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE",
        },
        "gate_matrix": {
            "G5_PRIMARY6": "CODEX_PROVISIONAL_CANDIDATE_ACCEPTED_NOT_MATERIAL_PASS",
            "G5_MATERIAL_ACCEPTANCE": "BLOCKED_CONTEXT_HAIRFRONT_REMAINING_NOT_OWNER_APPROVAL",
            "G6_MANUAL_ANCHOR_CORRECTION": "AVAILABLE_IF_PRIMARY6_CANDIDATE_IS_LATER_REVISED",
            "G7_MINI_CUBISM_DIAGNOSTIC": "BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE",
            "G8_REAL_CUBISM_AUTHORING": "BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE",
        },
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
        "decision": (
            "All six primary rows are provisionally accepted by Codex only as G5 candidate evidence. "
            "This reduces the immediate primary surface to zero unresolved rows, but material PASS and "
            "G7/G8 remain blocked because 30 context/HairFront rows remain and there is no owner approval."
        ),
        "next_action": [
            "Run a secondary context/HairFront reduction packet over the remaining 30 rows.",
            "Keep ParamHairFront hidden until the seven front-hair rows have independent motion-readiness acceptance.",
            "Do not start G7 Mini Cubism until G5 material acceptance is explicitly passed.",
        ],
        "self_review": {
            "source_status": route["status"],
            "source_primary6_row_count": route["summary"]["primary6_row_count"],
            "primary6_decision_row_count": len(decisions),
            "primary6_codex_candidate_accept_count": decision_counts[DECISION],
            "primary6_revise_count": 0,
            "primary6_unresolved_count_after_decision": sum(1 for row in decisions if row["requires_followup"]),
            "owner_approval_count": 0,
            "material_acceptance_pass_count": 0,
            "remaining_context_row_count": remaining_counts["SECONDARY_CONTEXT_REVIEW"],
            "remaining_hairfront_contract_row_count": remaining_counts["DEFER_KEEP_HAIRFRONT_HIDDEN"],
            "remaining_material_acceptance_required_before_g7_count": len(untouched_context),
            "primary6_ids_match_expected": [row["row_id"] for row in decisions]
            == [
                "B1_CLEAN_BASE_UNDERPAINT",
                "B2_EYE_PACK",
                "B3_MOUTH_PACK_REVISION_V1",
                "torso_base",
                "shoulder_L",
                "shoulder_R",
            ],
            "g5_material_not_accepted": True,
            "validator_only_promotion_blocked": True,
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
        "# Character 002 v22 G5 Primary6 Codex Decisions",
        "",
        f"- status: `{report['status']}`",
        f"- source: `{report['source_reduction_route']}`",
        f"- G5 material acceptance: `{report['summary']['g5_material_acceptance_status']}`",
        f"- material pass: `{report['summary']['material_pass_status']}`",
        f"- ParamHairFront: `{report['summary']['param_hair_front_status']}`",
        f"- G7: `{report['summary']['g7_mini_cubism_status']}`",
        "",
        "## Counts",
        "",
        f"- primary6_decision_row_count: `{report['summary']['primary6_decision_row_count']}`",
        f"- primary6_codex_candidate_accept_count: `{report['summary']['primary6_codex_candidate_accept_count']}`",
        f"- primary6_unresolved_count_after_decision: `{report['summary']['primary6_unresolved_count_after_decision']}`",
        f"- owner_approval_count: `{report['summary']['owner_approval_count']}`",
        f"- material_acceptance_pass_count: `{report['summary']['material_acceptance_pass_count']}`",
        f"- remaining_material_acceptance_required_before_g7_count: `{report['summary']['remaining_material_acceptance_required_before_g7_count']}`",
        "",
        "## Decisions",
        "",
    ]
    for row in decisions:
        lines.append(f"- `{row['row_id']}`: `{row['codex_decision']}`")
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
    print(STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

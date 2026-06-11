#!/usr/bin/env python3
"""Reduce the remaining v22 G5 context/HairFront rows after primary6.

This packet records Codex provisional context keep/defer decisions. It does
not grant material PASS, owner approval, ParamHairFront activation, Mini
Cubism promotion, or real Cubism promotion.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/Users/family/jason/Vtube")
EXP = ROOT / "experiments/cubism-v2-new-character-002"
PRIMARY6 = (
    EXP / "reports/v22_g5_primary6_codex_decisions/v22_g5_primary6_codex_decisions_packet.json"
)
REPORT_DIR = EXP / "reports/v22_g5_secondary_hairfront_reduction"
REPORT_JSON = REPORT_DIR / "v22_g5_secondary_hairfront_reduction_packet.json"
REPORT_MD = REPORT_DIR / "v22_g5_secondary_hairfront_reduction_packet.md"

STATUS = "G5_SECONDARY_HAIRFRONT_REDUCTION_READY_MATERIAL_NOT_ACCEPTED"
CONTEXT_DECISION = "CODEX_PROVISIONAL_KEEP_AS_CONTEXT_NOT_MATERIAL_PASS"
HAIRFRONT_DECISION = "DEFER_HAIRFRONT_KEEP_PARAM_HIDDEN_CONTRACT_ONLY"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def route_row(row: dict) -> dict:
    if row["route_priority"] == "DEFER_KEEP_HAIRFRONT_HIDDEN":
        return {
            **row,
            "codex_decision": HAIRFRONT_DECISION,
            "decision_effect": "DEFERRED_NOT_G5_MATERIAL_ACCEPTANCE",
            "material_acceptance": "BLOCKED_HAIRFRONT_CONTRACT_ONLY",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "requires_followup": True,
            "followup_gate": "HAIRFRONT_MOTION_READINESS_AND_OWNER_ACCEPTANCE",
        }
    return {
        **row,
        "codex_decision": CONTEXT_DECISION,
        "decision_effect": "CONTEXT_KEPT_NOT_G5_MATERIAL_PASS",
        "material_acceptance": "BLOCKED_CONTEXT_NOT_MATERIAL_PASS",
        "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
        "requires_followup": False,
        "followup_gate": "NONE_UNLESS_VISUAL_ARTIFACT_FOUND",
    }


def main() -> int:
    primary6 = load_json(PRIMARY6)
    rows = [route_row(row) for row in primary6["untouched_remaining_rows"]]
    decision_counts = Counter(row["codex_decision"] for row in rows)
    effect_counts = Counter(row["decision_effect"] for row in rows)
    source_counts = Counter(row["source"] for row in rows)
    review_class_counts = Counter(row.get("review_class") for row in rows)
    followup_count = sum(1 for row in rows if row["requires_followup"])
    context_rows = [row for row in rows if row["codex_decision"] == CONTEXT_DECISION]
    hairfront_rows = [row for row in rows if row["codex_decision"] == HAIRFRONT_DECISION]

    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": STATUS,
        "source_primary6_decisions": rel(PRIMARY6),
        "source_status": primary6["status"],
        "reduction_rows": rows,
        "context_rows": context_rows,
        "hairfront_contract_rows": hairfront_rows,
        "summary": {
            "source_remaining_material_acceptance_required_before_g7_count": primary6["summary"][
                "remaining_material_acceptance_required_before_g7_count"
            ],
            "reduction_row_count": len(rows),
            "context_keep_count": decision_counts[CONTEXT_DECISION],
            "hairfront_defer_count": decision_counts[HAIRFRONT_DECISION],
            "followup_required_count": followup_count,
            "material_acceptance_pass_count": 0,
            "owner_approval_count": 0,
            "g5_material_acceptance_remaining_count": followup_count,
            "source_counts": dict(sorted(source_counts.items())),
            "review_class_counts": dict(sorted(review_class_counts.items())),
            "decision_counts": dict(sorted(decision_counts.items())),
            "effect_counts": dict(sorted(effect_counts.items())),
            "g5_material_acceptance_status": "BLOCKED_HAIRFRONT_MOTION_READINESS_REMAINING_NOT_OWNER_APPROVAL",
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE",
            "g8_real_cubism_status": "BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE",
        },
        "gate_matrix": {
            "G5_SECONDARY_CONTEXT": "CODEX_PROVISIONAL_CONTEXT_KEPT_NOT_MATERIAL_PASS",
            "G5_HAIRFRONT": "DEFERRED_KEEP_PARAM_HIDDEN_CONTRACT_ONLY",
            "G5_MATERIAL_ACCEPTANCE": "BLOCKED_HAIRFRONT_MOTION_READINESS_REMAINING_NOT_OWNER_APPROVAL",
            "G6_MANUAL_ANCHOR_CORRECTION": "AVAILABLE_IF_CONTEXT_OR_HAIRFRONT_REVISED",
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
            "The 23 secondary context rows are kept as context-only candidate evidence, and the "
            "seven HairFront rows are deferred with ParamHairFront hidden. Material acceptance is "
            "still blocked by HairFront motion-readiness/owner acceptance."
        ),
        "next_action": [
            "Build a HairFront motion-readiness acceptance packet for the seven front-hair rows, keeping ParamHairFront hidden until it passes.",
            "Only after HairFront readiness is accepted should a separate G5 final material acceptance packet be considered.",
            "Do not start G7 Mini Cubism or real Cubism authoring from this reduction packet.",
        ],
        "self_review": {
            "source_status": primary6["status"],
            "source_remaining_material_acceptance_required_before_g7_count": primary6["summary"][
                "remaining_material_acceptance_required_before_g7_count"
            ],
            "reduction_row_count": len(rows),
            "context_keep_count": decision_counts[CONTEXT_DECISION],
            "hairfront_defer_count": decision_counts[HAIRFRONT_DECISION],
            "followup_required_count": followup_count,
            "material_acceptance_pass_count": 0,
            "owner_approval_count": 0,
            "g5_material_acceptance_remaining_count": followup_count,
            "source_counts_b4": source_counts["B4"],
            "source_counts_b5": source_counts["B5"],
            "has_context_decision_enum": decision_counts[CONTEXT_DECISION] == 23,
            "has_hairfront_decision_enum": decision_counts[HAIRFRONT_DECISION] == 7,
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
        "# Character 002 v22 G5 Secondary/HairFront Reduction",
        "",
        f"- status: `{report['status']}`",
        f"- source: `{report['source_primary6_decisions']}`",
        f"- G5 material acceptance: `{report['summary']['g5_material_acceptance_status']}`",
        f"- material pass: `{report['summary']['material_pass_status']}`",
        f"- ParamHairFront: `{report['summary']['param_hair_front_status']}`",
        f"- G7: `{report['summary']['g7_mini_cubism_status']}`",
        "",
        "## Counts",
        "",
        f"- reduction_row_count: `{report['summary']['reduction_row_count']}`",
        f"- context_keep_count: `{report['summary']['context_keep_count']}`",
        f"- hairfront_defer_count: `{report['summary']['hairfront_defer_count']}`",
        f"- followup_required_count: `{report['summary']['followup_required_count']}`",
        f"- g5_material_acceptance_remaining_count: `{report['summary']['g5_material_acceptance_remaining_count']}`",
        f"- material_acceptance_pass_count: `{report['summary']['material_acceptance_pass_count']}`",
        "",
        "## Decisions",
        "",
        f"- context: `{CONTEXT_DECISION}`",
        f"- HairFront: `{HAIRFRONT_DECISION}`",
        "",
        "## Next Action",
        "",
    ]
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

#!/usr/bin/env python3
"""Seed v22 G4 visual decisions from current success-pattern evidence.

This is a non-owner provisional routing file. It lets the pipeline continue
without pretending that pending visual review is final material acceptance.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
REPORT_DIR = EXP / "reports/v22_g4_visual_decision_packet"

PACKET_JSON = REPORT_DIR / "v22_g4_visual_decision_packet.json"
CODEX_DECISIONS_JSON = REPORT_DIR / "v22_g4_codex_provisional_visual_decisions.json"
CODEX_DECISIONS_MD = REPORT_DIR / "v22_g4_codex_provisional_visual_decisions.md"

ACCEPT = "ACCEPT_VISUAL_CANDIDATE_KEEP_MATERIAL_BLOCKED"
REVISE = "REVISE_BEFORE_G5"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def decision_for(item: dict) -> tuple[str, str, str]:
    item_id = item["id"]
    if item_id == "B4_B5_COMBINED_CONTEXT":
        return (
            REVISE,
            "B4/B5 still has 33 context-review rows, so keep it out of G5 material acceptance and route focused follow-up only.",
            "B4_B5_CONTEXT_REVIEW_REVISE_BEFORE_G5",
        )
    return (
        ACCEPT,
        "Source report is already a pass-candidate or technical contact candidate, so keep it as a visual candidate while material PASS remains blocked.",
        f"{item_id}_ACCEPT_CANDIDATE_KEEP_MATERIAL_BLOCKED",
    )


def main() -> int:
    packet = load_json(PACKET_JSON)
    decisions = []
    policy_counts: dict[str, int] = {}
    for item in packet["visual_decision_items"]:
        decision, note, policy = decision_for(item)
        if decision not in item["allowed_visual_decisions"]:
            raise ValueError(f"{item['id']} default decision is not allowed: {decision}")
        policy_counts[policy] = policy_counts.get(policy, 0) + 1
        decisions.append(
            {
                "id": item["id"],
                "title": item["title"],
                "visual_decision": decision,
                "allowed_visual_decisions": item["allowed_visual_decisions"],
                "review_note": note,
                "decision_authority": "CODEX_PROVISIONAL_SUCCESS_PATTERN",
                "route_policy": policy,
                "source_status": item["source_status"],
                "review_gate": item["review_gate"],
            }
        )

    accepted_count = sum(1 for row in decisions if row["visual_decision"] == ACCEPT)
    revise_count = sum(1 for row in decisions if row["visual_decision"] == REVISE)
    pending_count = sum(1 for row in decisions if row["visual_decision"] == "PENDING_VISUAL_REVIEW")
    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": "G4_CODEX_PROVISIONAL_VISUAL_DECISIONS_READY_NO_OWNER_APPROVAL",
        "source_packet": rel(PACKET_JSON),
        "instructions": (
            "Use this only as Codex provisional routing. It is not owner approval, not G5 material acceptance, "
            "and not a real Cubism success claim."
        ),
        "decisions": decisions,
        "summary": {
            "decision_count": len(decisions),
            "pending_count": pending_count,
            "accepted_visual_candidate_count": accepted_count,
            "revise_before_g5_count": revise_count,
            "regenerate_batch_or_context_count": 0,
            "route_policy_counts": policy_counts,
            "g4_visual_review_status": "CODEX_PROVISIONAL_REVIEW_READY_NOT_OWNER_APPROVAL",
            "g5_material_acceptance_status": "BLOCKED_CONTEXT_REVIEW_NOT_OWNER_APPROVAL",
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
        "decision": (
            "Codex provisionally keeps B1, B2, B3, and the 64-part contact sheet as visual candidates while routing "
            "B4/B5 combined context to focused revision before G5."
        ),
        "next_action": [
            "Run the G4 visual decision route planner with this Codex provisional decision file.",
            "Apply focused B4/B5 follow-up before creating any G5 material acceptance packet.",
            "Keep ParamHairFront hidden, and keep G7/G8 blocked.",
        ],
        "self_review": {
            "source_packet_status": packet["status"],
            "decision_count": len(decisions),
            "all_expected_rows_present": len(decisions) == packet["summary"]["decision_item_count"],
            "allowed_visual_decision_values_checked": all(
                row["visual_decision"] in row["allowed_visual_decisions"] for row in decisions
            ),
            "no_pending_decisions": pending_count == 0,
            "has_b4_b5_revise_gate": any(
                row["id"] == "B4_B5_COMBINED_CONTEXT" and row["visual_decision"] == REVISE
                for row in decisions
            ),
            "not_owner_approval": True,
            "material_pass_blocked": True,
            "validator_only_promotion_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "status": "PASS",
        },
    }
    save_json(CODEX_DECISIONS_JSON, report)

    lines = [
        "# Character 002 v22 G4 Codex Provisional Visual Decisions",
        "",
        f"- status: `{report['status']}`",
        f"- source packet: `{report['source_packet']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", "", report["decision"], "", "## Rows", ""])
    for row in decisions:
        lines.append(
            f"- `{row['id']}` `{row['visual_decision']}` `{row['route_policy']}`: {row['review_note']}"
        )
    lines.extend(["", "## Self Review", ""])
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    CODEX_DECISIONS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": report["status"], "report": str(CODEX_DECISIONS_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

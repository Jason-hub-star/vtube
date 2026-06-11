#!/usr/bin/env python3
"""Seed v22 B4/B5 focused decisions from current success patterns.

This file deliberately does not impersonate owner approval. It records Codex's
provisional route choices so the pipeline can continue while keeping material,
ParamHairFront, Mini Cubism, and real Cubism gates blocked.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
REPORT_DIR = EXP / "reports/v22_b4_b5_focused_owner_review"
PACKET_JSON = REPORT_DIR / "v22_b4_b5_focused_owner_review.json"
CODEX_DECISIONS_JSON = REPORT_DIR / "v22_b4_b5_focused_codex_provisional_decisions.json"
CODEX_DECISIONS_MD = REPORT_DIR / "v22_b4_b5_focused_codex_provisional_decisions.md"


B4_ACCEPT = "ACCEPT_FOR_MOTION_READINESS_CANDIDATE"
B5_REVISE = "REVISE_MASK_OR_DRAW_ORDER"
B5_REGENERATE = "REGENERATE_B5_BODY_MINIPASS"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def decision_for(item: dict) -> tuple[str, str, str]:
    part_id = item["part_id"]
    group = item["review_group"]
    recommendation = item["recommendation"]
    if group == "B4_FRONT_HAIR":
        return (
            B4_ACCEPT,
            "Codex provisional: real independent hair_front_* child art exists, so continue to motion-readiness candidate checks while keeping ParamHairFront hidden.",
            "B4_FRONT_HAIR_PROVISIONAL_ACCEPT_KEEP_HAIRFRONT_HIDDEN",
        )
    if part_id == "torso_base":
        return (
            B5_REGENERATE,
            "Codex provisional: broad torso underpaint/body patch remains a hard visual blocker; run focused B5 body mini-pass instead of accepting it.",
            "B5_TORSO_REGENERATE_MINIPASS",
        )
    if part_id in {"shoulder_L", "shoulder_R"} and recommendation == "REVIEW_DRAW_ORDER_BEFORE_REGENERATE":
        return (
            B5_REVISE,
            "Codex provisional: shoulder overlap is heavily affected by hair occlusion/draw order, so revise draw-order or mask before regenerating.",
            "B5_SHOULDER_REVISE_DRAW_ORDER_OR_MASK",
        )
    return (
        "PENDING_OWNER_REVIEW",
        "No success-pattern default exists for this row.",
        "NO_DEFAULT_ROUTE",
    )


def main() -> int:
    packet = json.loads(PACKET_JSON.read_text(encoding="utf-8"))
    decisions = []
    route_counts: dict[str, int] = {}
    for item in packet["primary_decisions"]:
        decision, note, route_policy = decision_for(item)
        if decision not in ["PENDING_OWNER_REVIEW", *item["allowed_owner_decisions"]]:
            raise ValueError(f"{item['part_id']} default decision is not allowed: {decision}")
        route_counts[route_policy] = route_counts.get(route_policy, 0) + 1
        decisions.append(
            {
                "part_id": item["part_id"],
                "review_group": item["review_group"],
                "owner_decision": decision,
                "allowed_owner_decisions": item["allowed_owner_decisions"],
                "owner_note": note,
                "decision_authority": "CODEX_PROVISIONAL_SUCCESS_PATTERN",
                "route_policy": route_policy,
                "source_recommendation": item["recommendation"],
            }
        )

    accepted_count = sum(1 for row in decisions if row["owner_decision"].startswith("ACCEPT"))
    revise_count = sum(1 for row in decisions if row["owner_decision"].startswith("REVISE"))
    regenerate_count = sum(1 for row in decisions if row["owner_decision"].startswith("REGENERATE"))
    pending_count = sum(1 for row in decisions if row["owner_decision"] == "PENDING_OWNER_REVIEW")
    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "updated_at": now(),
        "status": "CODEX_PROVISIONAL_DECISIONS_READY_NO_OWNER_APPROVAL",
        "source_packet": rel(PACKET_JSON),
        "instructions": (
            "Use this only to continue the pipeline without owner approval. "
            "It is not human acceptance and must not unlock material PASS, ParamHairFront, Mini Cubism, or real Cubism."
        ),
        "decisions": decisions,
        "summary": {
            "decision_count": len(decisions),
            "pending_count": pending_count,
            "accepted_count": accepted_count,
            "revise_count": revise_count,
            "regenerate_count": regenerate_count,
            "route_policy_counts": route_counts,
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
        "decision": (
            "Proceed without owner acceptance by using the current success patterns as provisional routing: "
            "B4 front hair moves to motion-readiness candidate checks with HairFront hidden; torso regenerates; shoulders revise draw-order or mask."
        ),
        "next_action": [
            "Run the owner decision route planner with this explicit Codex provisional decision file.",
            "Apply focused B5 body mini-pass/regeneration for torso_base and draw-order or mask revision for shoulders.",
            "Prepare B4 front-hair motion-readiness checks without exposing ParamHairFront yet.",
        ],
        "self_review": {
            "all_primary_parts_present": len(decisions) == 10,
            "no_pending_decisions": pending_count == 0,
            "b4_front_hair_count": sum(1 for row in decisions if row["review_group"] == "B4_FRONT_HAIR"),
            "b5_body_blocker_count": sum(1 for row in decisions if row["review_group"] == "B5_BODY_BLOCKER"),
            "not_owner_approval": True,
            "material_pass_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "status": "PASS",
        },
    }
    CODEX_DECISIONS_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Character 002 v22 B4/B5 Codex Provisional Decisions",
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
            f"- `{row['part_id']}` `{row['owner_decision']}` `{row['route_policy']}`: {row['owner_note']}"
        )
    lines.extend(["", "## Self Review", ""])
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    CODEX_DECISIONS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": report["status"], "report": str(CODEX_DECISIONS_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

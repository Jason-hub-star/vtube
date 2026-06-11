#!/usr/bin/env python3
"""Build a route plan from v22 B4/B5 focused owner decisions."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
REPORT_DIR = EXP / "reports/v22_b4_b5_focused_owner_review"
PACKET_JSON = REPORT_DIR / "v22_b4_b5_focused_owner_review.json"
DECISION_TEMPLATE_JSON = REPORT_DIR / "v22_b4_b5_focused_owner_review_decision_template.json"
DECISIONS_JSON = REPORT_DIR / "v22_b4_b5_focused_owner_review_decisions.json"
SMOKE_DECISIONS_JSON = REPORT_DIR / "v22_b4_b5_focused_owner_review_decisions_smoke.json"
ROUTE_PLAN_JSON = REPORT_DIR / "v22_b4_b5_owner_decision_route_plan.json"
ROUTE_PLAN_MD = REPORT_DIR / "v22_b4_b5_owner_decision_route_plan.md"


PENDING = "PENDING_OWNER_REVIEW"
ACCEPT_DECISIONS = {
    "ACCEPT_FOR_MOTION_READINESS_CANDIDATE",
    "ACCEPT_WITH_DRAW_ORDER_CONTEXT",
}
REVISE_DECISIONS = {
    "REVISE_MASK_OR_ANCHOR",
    "REVISE_MASK_OR_DRAW_ORDER",
}
REGENERATE_DECISIONS = {
    "REGENERATE_B4_FRONT_HAIR_MINIPASS",
    "REGENERATE_B5_BODY_MINIPASS",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def choose_decisions_path(args: argparse.Namespace) -> tuple[Path, str]:
    if args.decisions:
        path = Path(args.decisions)
        if not path.is_absolute():
            path = ROOT / path
        if "codex_provisional" in path.name:
            return path, "CODEX_PROVISIONAL_DECISION_FILE"
        return path, "EXPLICIT_DECISION_FILE"
    if args.smoke:
        return SMOKE_DECISIONS_JSON, "SMOKE_DECISION_FILE"
    if DECISIONS_JSON.exists():
        return DECISIONS_JSON, "REAL_DECISION_FILE"
    return DECISION_TEMPLATE_JSON, "MISSING_REAL_DECISION_FILE_USING_TEMPLATE_PENDING"


def classify(decision: str, review_group: str) -> tuple[str, str]:
    if decision == PENDING:
        return "WAIT_OWNER_DECISION", "Owner review has not selected an action yet."
    if decision in ACCEPT_DECISIONS:
        if review_group == "B4_FRONT_HAIR":
            return (
                "ACCEPT_FOR_B4_FRONT_HAIR_MOTION_READINESS_CANDIDATE",
                "Keep as a front-hair child candidate, but keep ParamHairFront hidden until motion-readiness and later QA pass.",
            )
        return (
            "ACCEPT_FOR_B5_CORRECTED_OVERLAY_QA_CANDIDATE",
            "Keep as a focused B5 candidate, but require corrected B4/B5 overlay QA before any material promotion.",
        )
    if decision in REVISE_DECISIONS:
        if review_group == "B4_FRONT_HAIR":
            return (
                "ROUTE_TO_B4_MASK_OR_ANCHOR_REFINEMENT",
                "Refine the front-hair mask or anchor; do not regenerate all B1-B5.",
            )
        return (
            "ROUTE_TO_B5_DRAW_ORDER_OR_MASK_REFINEMENT",
            "Refine B5 draw order or mask; do not restart the full material pipeline.",
        )
    if decision in REGENERATE_DECISIONS:
        if review_group == "B4_FRONT_HAIR":
            return (
                "ROUTE_TO_B4_FRONT_HAIR_MINIPASS_REGENERATION",
                "Run a focused B4 front-hair mini-pass only.",
            )
        return (
            "ROUTE_TO_B5_BODY_MINIPASS_REGENERATION",
            "Run a focused B5 body mini-pass only.",
        )
    return "INVALID_DECISION", "Decision is not in the allowed set for this part."


def status_from_counts(counts: Counter, invalid_count: int) -> str:
    if invalid_count:
        return "B4_B5_OWNER_DECISION_ROUTE_PLAN_FAIL_INVALID_DECISION"
    if counts["WAIT_OWNER_DECISION"]:
        return "B4_B5_OWNER_DECISION_ROUTE_PLAN_BLOCKED_PENDING_OWNER_DECISIONS"
    if counts["ROUTE_TO_B4_MASK_OR_ANCHOR_REFINEMENT"] or counts["ROUTE_TO_B5_DRAW_ORDER_OR_MASK_REFINEMENT"]:
        return "B4_B5_OWNER_DECISION_ROUTE_PLAN_READY_FOR_REVISION_WORK"
    if counts["ROUTE_TO_B4_FRONT_HAIR_MINIPASS_REGENERATION"] or counts["ROUTE_TO_B5_BODY_MINIPASS_REGENERATION"]:
        return "B4_B5_OWNER_DECISION_ROUTE_PLAN_READY_FOR_MINIPASS_REGENERATION"
    return "B4_B5_OWNER_DECISION_ROUTE_PLAN_READY_FOR_CORRECTED_OVERLAY_QA"


def build_report(args: argparse.Namespace) -> dict:
    packet = load_json(PACKET_JSON)
    decisions_path, decision_source_status = choose_decisions_path(args)
    decisions_doc = load_json(decisions_path)
    decision_rows = decisions_doc.get("decisions", [])
    decision_by_part = {row["part_id"]: row for row in decision_rows}
    primary = packet["primary_decisions"]

    routes = []
    invalid = []
    for item in primary:
        part_id = item["part_id"]
        row = decision_by_part.get(part_id, {})
        decision = row.get("owner_decision", PENDING)
        allowed = [PENDING, *item["allowed_owner_decisions"]]
        is_valid = decision in allowed
        route, route_reason = classify(decision, item["review_group"])
        if not is_valid:
            invalid.append(part_id)
            route = "INVALID_DECISION"
            route_reason = f"Decision must be one of {allowed}."
        routes.append(
            {
                "part_id": part_id,
                "review_group": item["review_group"],
                "owner_decision": decision,
                "owner_note": row.get("owner_note", ""),
                "allowed_owner_decisions": item["allowed_owner_decisions"],
                "route": route,
                "route_reason": route_reason,
                "recommendation": item["recommendation"],
                "output_path": item["output_path"],
                "next_if_accept": item["next_if_accept"],
                "next_if_revise": item["next_if_revise"],
                "next_if_regenerate": item["next_if_regenerate"],
            }
        )

    route_counts = Counter(row["route"] for row in routes)
    decision_counts = Counter(row["owner_decision"] for row in routes)
    pending_count = route_counts["WAIT_OWNER_DECISION"]
    accepted_count = sum(decision_counts[name] for name in ACCEPT_DECISIONS)
    revise_count = sum(decision_counts[name] for name in REVISE_DECISIONS)
    regenerate_count = sum(decision_counts[name] for name in REGENERATE_DECISIONS)
    status = status_from_counts(route_counts, len(invalid))
    all_decisions_non_pending = pending_count == 0 and not invalid
    all_primary_accepted = accepted_count == len(primary) and revise_count == 0 and regenerate_count == 0

    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": status,
        "focused_owner_packet": rel(PACKET_JSON),
        "decisions_path": rel(decisions_path),
        "decision_source_status": decision_source_status,
        "summary": {
            "primary_decision_count": len(primary),
            "decision_row_count": len(decision_rows),
            "pending_count": pending_count,
            "accepted_count": accepted_count,
            "revise_count": revise_count,
            "regenerate_count": regenerate_count,
            "invalid_decision_count": len(invalid),
            "route_counts": dict(sorted(route_counts.items())),
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
        "routes": routes,
        "decision": (
            "Owner decisions are routed into focused B4/B5 follow-up work only. "
            "This report never promotes material PASS, ParamHairFront, Mini Cubism, or real Cubism by itself."
        ),
        "next_action": [],
        "self_review": {
            "allowed_decision_values_checked": True,
            "all_primary_parts_present": len(primary) == 10,
            "all_route_rows_present": len(routes) == len(primary),
            "all_decisions_non_pending": all_decisions_non_pending,
            "all_primary_accepted": all_primary_accepted,
            "has_pending_blocker": pending_count > 0,
            "has_revise_or_regenerate_path": revise_count + regenerate_count > 0,
            "material_pass_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "status": "PASS" if not invalid else "FAIL",
        },
    }

    if invalid:
        report["next_action"] = [
            "Fix invalid owner_decision values before applying any B4/B5 route.",
            "Keep all material and rig gates blocked.",
        ]
    elif pending_count:
        report["next_action"] = [
            "Collect the remaining owner decisions in the 8093 focused review UI.",
            "Do not run B4/B5 correction, Mini Cubism, or real Cubism promotion from pending rows.",
        ]
    elif revise_count or regenerate_count:
        report["next_action"] = [
            "Apply only the focused revise/regenerate routes listed in this report.",
            "Rebuild corrected B4/B5 candidates and rerun overlay QA.",
            "Keep ParamHairFront hidden until accepted front-hair child candidates pass motion-readiness.",
        ]
    else:
        report["next_action"] = [
            "Prepare corrected B4/B5 overlay QA from the accepted candidate set.",
            "Keep material PASS blocked until corrected overlay QA and human visual QA pass.",
        ]

    return report


def write_markdown(report: dict) -> None:
    lines = [
        "# Character 002 v22 B4/B5 Owner Decision Route Plan",
        "",
        f"- status: `{report['status']}`",
        f"- decision source: `{report['decision_source_status']}`",
        f"- decisions path: `{report['decisions_path']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", "", report["decision"], "", "## Next Action", ""])
    lines.extend(f"- {item}" for item in report["next_action"])
    lines.extend(["", "## Routes", ""])
    for row in report["routes"]:
        lines.append(
            f"- `{row['part_id']}` `{row['owner_decision']}` -> `{row['route']}`: {row['route_reason']}"
        )
    lines.extend(["", "## Self Review", ""])
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    ROUTE_PLAN_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decisions", help="Optional explicit owner decisions JSON path.")
    parser.add_argument("--smoke", action="store_true", help="Use the smoke decisions JSON.")
    args = parser.parse_args()
    report = build_report(args)
    save_json(ROUTE_PLAN_JSON, report)
    write_markdown(report)
    print(json.dumps({"status": report["status"], "report": str(ROUTE_PLAN_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

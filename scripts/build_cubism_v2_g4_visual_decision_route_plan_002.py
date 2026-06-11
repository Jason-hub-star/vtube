#!/usr/bin/env python3
"""Build a route plan from v22 G4 visual decisions."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
REPORT_DIR = EXP / "reports/v22_g4_visual_decision_packet"

PACKET_JSON = REPORT_DIR / "v22_g4_visual_decision_packet.json"
DECISION_TEMPLATE_JSON = REPORT_DIR / "v22_g4_visual_decision_template.json"
CODEX_DECISIONS_JSON = REPORT_DIR / "v22_g4_codex_provisional_visual_decisions.json"
ROUTE_PLAN_JSON = REPORT_DIR / "v22_g4_visual_decision_route_plan.json"
ROUTE_PLAN_MD = REPORT_DIR / "v22_g4_visual_decision_route_plan.md"

PENDING = "PENDING_VISUAL_REVIEW"
ACCEPT = "ACCEPT_VISUAL_CANDIDATE_KEEP_MATERIAL_BLOCKED"
REVISE = "REVISE_BEFORE_G5"
REGENERATE = "REGENERATE_BATCH_OR_CONTEXT"


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
            return path, "CODEX_PROVISIONAL_VISUAL_DECISION_FILE"
        return path, "EXPLICIT_VISUAL_DECISION_FILE"
    if CODEX_DECISIONS_JSON.exists() and args.use_codex_default:
        return CODEX_DECISIONS_JSON, "CODEX_PROVISIONAL_VISUAL_DECISION_FILE"
    return DECISION_TEMPLATE_JSON, "TEMPLATE_PENDING_VISUAL_REVIEW"


def classify(decision: str, item_id: str) -> tuple[str, str]:
    if decision == PENDING:
        return "WAIT_VISUAL_REVIEW", "Visual decision has not selected a route yet."
    if decision == ACCEPT:
        if item_id == "B4_B5_COMBINED_CONTEXT":
            return (
                "ACCEPT_B4_B5_AS_CANDIDATE_KEEP_G5_BLOCKED",
                "B4/B5 can only remain a candidate here; G5 still needs separate material acceptance.",
            )
        return (
            "KEEP_AS_G4_VISUAL_CANDIDATE",
            "Keep this item as a G4 visual candidate while material PASS remains blocked.",
        )
    if decision == REVISE:
        if item_id == "B4_B5_COMBINED_CONTEXT":
            return (
                "ROUTE_TO_B4_B5_FOCUSED_FOLLOWUP_BEFORE_G5",
                "Use the focused B4/B5 context rows for mask, anchor, draw-order, or mini-pass follow-up before G5.",
            )
        return (
            "ROUTE_TO_BATCH_FOCUSED_REVISION_BEFORE_G5",
            "Revise only this batch before any G5 material acceptance packet.",
        )
    if decision == REGENERATE:
        if item_id == "B4_B5_COMBINED_CONTEXT":
            return (
                "ROUTE_TO_B4_B5_BATCH_OR_CONTEXT_REGENERATION",
                "Regenerate only the failing B4/B5 batch or context target.",
            )
        return (
            "ROUTE_TO_BATCH_REGENERATION_BEFORE_G5",
            "Regenerate this batch only; preserve unrelated candidate evidence.",
        )
    return "INVALID_VISUAL_DECISION", "Decision is not in the allowed set for this G4 row."


def status_from_counts(route_counts: Counter, invalid_count: int) -> str:
    if invalid_count:
        return "G4_VISUAL_DECISION_ROUTE_PLAN_FAIL_INVALID_DECISION"
    if route_counts["WAIT_VISUAL_REVIEW"]:
        return "G4_VISUAL_DECISION_ROUTE_PLAN_BLOCKED_PENDING_VISUAL_REVIEW"
    if (
        route_counts["ROUTE_TO_B4_B5_FOCUSED_FOLLOWUP_BEFORE_G5"]
        or route_counts["ROUTE_TO_BATCH_FOCUSED_REVISION_BEFORE_G5"]
        or route_counts["ROUTE_TO_B4_B5_BATCH_OR_CONTEXT_REGENERATION"]
        or route_counts["ROUTE_TO_BATCH_REGENERATION_BEFORE_G5"]
    ):
        return "G4_VISUAL_DECISION_ROUTE_PLAN_READY_FOR_FOCUSED_FOLLOWUP_MATERIAL_BLOCKED"
    return "G4_VISUAL_DECISION_ROUTE_PLAN_READY_FOR_G5_PACKET_PREP_MATERIAL_BLOCKED"


def build_report(args: argparse.Namespace) -> dict:
    packet = load_json(PACKET_JSON)
    decisions_path, decision_source_status = choose_decisions_path(args)
    decisions_doc = load_json(decisions_path)
    decision_rows = decisions_doc.get("decisions", [])
    decision_by_id = {row["id"]: row for row in decision_rows}
    items = packet["visual_decision_items"]

    routes = []
    invalid = []
    for item in items:
        item_id = item["id"]
        row = decision_by_id.get(item_id, {})
        decision = row.get("visual_decision", PENDING)
        allowed = item["allowed_visual_decisions"]
        is_valid = decision in allowed
        route, route_reason = classify(decision, item_id)
        if not is_valid:
            invalid.append(item_id)
            route = "INVALID_VISUAL_DECISION"
            route_reason = f"Decision must be one of {allowed}."
        routes.append(
            {
                "id": item_id,
                "title": item["title"],
                "visual_decision": decision,
                "review_note": row.get("review_note", ""),
                "allowed_visual_decisions": allowed,
                "route": route,
                "route_reason": route_reason,
                "source_status": item["source_status"],
                "review_gate": item["review_gate"],
                "image": item["image"],
                "report": item["report"],
                "next_if_accept": item["next_if_accept"],
                "next_if_revise": item["next_if_revise"],
                "next_if_regenerate": item["next_if_regenerate"],
            }
        )

    route_counts = Counter(row["route"] for row in routes)
    decision_counts = Counter(row["visual_decision"] for row in routes)
    pending_count = decision_counts[PENDING]
    accepted_count = decision_counts[ACCEPT]
    revise_count = decision_counts[REVISE]
    regenerate_count = decision_counts[REGENERATE]
    status = status_from_counts(route_counts, len(invalid))
    all_decisions_non_pending = pending_count == 0 and not invalid
    all_g4_items_accepted = accepted_count == len(items) and revise_count == 0 and regenerate_count == 0
    has_focused_followup = revise_count + regenerate_count > 0

    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": status,
        "g4_visual_decision_packet": rel(PACKET_JSON),
        "decisions_path": rel(decisions_path),
        "decision_source_status": decision_source_status,
        "summary": {
            "decision_item_count": len(items),
            "decision_row_count": len(decision_rows),
            "pending_count": pending_count,
            "accepted_visual_candidate_count": accepted_count,
            "revise_before_g5_count": revise_count,
            "regenerate_batch_or_context_count": regenerate_count,
            "invalid_decision_count": len(invalid),
            "route_counts": dict(sorted(route_counts.items())),
            "g4_visual_review_status": "ROUTE_PLANNED_NOT_MATERIAL_PASS",
            "g5_material_acceptance_status": "BLOCKED_PENDING_FOCUSED_G4_FOLLOWUP",
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
        "routes": routes,
        "decision": (
            "G4 visual decisions are routed into focused follow-up or G5 packet prep only. "
            "This route plan never promotes material PASS, ParamHairFront, Mini Cubism, or real Cubism by itself."
        ),
        "next_action": [],
        "self_review": {
            "allowed_visual_decision_values_checked": True,
            "all_expected_rows_present": len(routes) == packet["summary"]["decision_item_count"],
            "all_decisions_non_pending": all_decisions_non_pending,
            "all_g4_items_accepted": all_g4_items_accepted,
            "has_pending_blocker": pending_count > 0,
            "has_focused_followup_path": has_focused_followup,
            "not_owner_approval": decision_source_status == "CODEX_PROVISIONAL_VISUAL_DECISION_FILE",
            "material_pass_blocked": True,
            "validator_only_promotion_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "status": "PASS" if not invalid else "FAIL",
        },
    }

    if invalid:
        report["next_action"] = [
            "Fix invalid visual_decision values before applying any G4 route.",
            "Keep all material and rig gates blocked.",
        ]
    elif pending_count:
        report["next_action"] = [
            "Record G4 visual decisions or provide an explicit Codex provisional decision file.",
            "Do not create a G5 material acceptance packet from pending rows.",
        ]
    elif has_focused_followup:
        report["next_action"] = [
            "Apply only the focused G4 follow-up routes listed in this report.",
            "For the current Codex provisional path, resolve B4/B5 combined context before G5.",
            "Keep ParamHairFront hidden until independent front-hair child art passes motion-readiness.",
        ]
    else:
        report["next_action"] = [
            "Prepare a separate G5 material acceptance packet.",
            "Keep material PASS blocked until G5 verifies visual acceptance, v21 locks, Mini Cubism diagnostic separation, and real Cubism remains separately gated.",
        ]
    return report


def write_markdown(report: dict) -> None:
    lines = [
        "# Character 002 v22 G4 Visual Decision Route Plan",
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
        lines.append(f"- `{row['id']}` `{row['visual_decision']}` -> `{row['route']}`: {row['route_reason']}")
    lines.extend(["", "## Self Review", ""])
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    ROUTE_PLAN_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decisions", help="Path to a G4 visual decisions JSON file.")
    parser.add_argument(
        "--use-codex-default",
        action="store_true",
        help="Use the Codex provisional visual decisions file when no explicit --decisions path is provided.",
    )
    args = parser.parse_args()
    report = build_report(args)
    save_json(ROUTE_PLAN_JSON, report)
    write_markdown(report)
    print(json.dumps({"status": report["status"], "report": str(ROUTE_PLAN_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

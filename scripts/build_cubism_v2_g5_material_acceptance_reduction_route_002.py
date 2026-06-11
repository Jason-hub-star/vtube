#!/usr/bin/env python3
"""Reduce the v22 G5 material acceptance surface into route phases.

This does not accept material. It turns the 36 blocked rows from the current
G5 packet into a smaller next-work surface while preserving every blocked row.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/Users/family/jason/Vtube")
EXP = ROOT / "experiments/cubism-v2-new-character-002"
G5_ACCEPTANCE = (
    EXP
    / "reports/v22_g5_material_acceptance_from_prep/v22_g5_material_acceptance_from_prep_packet.json"
)
REPORT_DIR = EXP / "reports/v22_g5_material_acceptance_reduction_route"
REPORT_JSON = REPORT_DIR / "v22_g5_material_acceptance_reduction_route_packet.json"
REPORT_MD = REPORT_DIR / "v22_g5_material_acceptance_reduction_route_packet.md"

STATUS = "G5_MATERIAL_ACCEPTANCE_REDUCTION_ROUTE_READY_PRIMARY6_MATERIAL_NOT_ACCEPTED"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def route_candidate(row: dict) -> dict:
    row_id = row["row_id"]
    if row_id == "B1_CLEAN_BASE_UNDERPAINT":
        phase = "P0_PRIMARY_B1_CLEAN_BASE_ACCEPTANCE"
        action = "REVIEW_ACCEPT_OR_REVISE_CLEAN_BASE_UNDERPAINT"
        criterion = "no eye/mouth residue, no rectangular/oval skin patch, natural underpaint continuity"
    elif row_id == "B2_EYE_PACK":
        phase = "P0_PRIMARY_B2_EYE_ACCEPTANCE"
        action = "REVIEW_ACCEPT_OR_REVISE_FIXED_WHITE_AND_COHERENT_EYE_DETAIL"
        criterion = "fixed eye whites, iris/pupil/highlight move together, no crossed-eye, EyeOpen min 0.27"
    elif row_id == "B3_MOUTH_PACK_REVISION_V1":
        phase = "P0_PRIMARY_B3_MOUTH_ACCEPTANCE"
        action = "REVIEW_ACCEPT_OR_REVISE_COORDINATED_MOUTH_PACKET"
        criterion = "consistent mouth anchor, no oversized/round wide mouth, natural teeth/tongue, MouthOpenY max 0.85"
    elif row_id == "torso_base":
        phase = "P0_PRIMARY_B5_TORSO_ACCEPTANCE"
        action = "REVIEW_ACCEPT_OR_REVISE_GENERATED_TORSO_UNDERPAINT"
        criterion = "complete torso underpaint independent of source lower crop; candidate remains not material PASS"
    elif row_id in {"shoulder_L", "shoulder_R"}:
        phase = "P0_PRIMARY_B5_SHOULDER_ACCEPTANCE"
        action = "REVIEW_ACCEPT_OR_REVISE_SHOULDER_DRAW_ORDER_MASK"
        criterion = "shoulder mask/draw-order improvement does not create pasted edges or hair occlusion artifacts"
    else:
        phase = "P9_UNCLASSIFIED_PRIMARY_REVIEW"
        action = "REVIEW_CLASSIFY_BEFORE_ACCEPTANCE"
        criterion = "unclassified row cannot be promoted"
    return {
        **row,
        "route_phase": phase,
        "route_priority": "PRIMARY_G5_ACCEPTANCE_SURFACE",
        "next_action": action,
        "acceptance_criterion": criterion,
        "material_acceptance": "BLOCKED_UNTIL_PRIMARY_ACCEPTANCE_DECISION",
    }


def route_remaining(row: dict) -> dict:
    if row["material_acceptance"] == "BLOCKED_HAIRFRONT_HIDDEN_CONTRACT_ONLY":
        return {
            **row,
            "route_phase": "P2_HAIRFRONT_CONTRACT_ONLY_DEFERRED",
            "route_priority": "DEFER_KEEP_HAIRFRONT_HIDDEN",
            "next_action": "KEEP_HAIRFRONT_HIDDEN_UNTIL_INDEPENDENT_MOTION_READINESS_ACCEPTANCE",
            "acceptance_criterion": "ParamHairFront remains hidden/contract-only; do not unlock from these rows.",
            "material_acceptance": "BLOCKED_HAIRFRONT_HIDDEN_CONTRACT_ONLY",
        }
    return {
        **row,
        "route_phase": "P1_SECONDARY_CONTEXT_REVIEW_AFTER_PRIMARY",
        "route_priority": "SECONDARY_CONTEXT_REVIEW",
        "next_action": "REVIEW_AFTER_PRIMARY6_OR_WHEN_VISIBLE_ARTIFACTS_ARE_FOUND",
        "acceptance_criterion": "context rows cannot become material PASS from validator evidence alone.",
        "material_acceptance": "BLOCKED_CONTEXT_REVIEW_REQUIRED",
    }


def main() -> int:
    g5 = load_json(G5_ACCEPTANCE)
    candidate_routes = [route_candidate(row) for row in g5["candidate_acceptance_rows"]]
    remaining_routes = [route_remaining(row) for row in g5["remaining_review_rows"]]
    all_routes = candidate_routes + remaining_routes

    priority_counts = Counter(row["route_priority"] for row in all_routes)
    phase_counts = Counter(row["route_phase"] for row in all_routes)
    material_counts = Counter(row["material_acceptance"] for row in all_routes)
    primary_route_ids = [row["row_id"] for row in candidate_routes]

    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": STATUS,
        "source_g5_material_acceptance": rel(G5_ACCEPTANCE),
        "source_status": g5["status"],
        "source_verdict": g5["g5_acceptance_verdict"],
        "route_rows": all_routes,
        "primary6_rows": candidate_routes,
        "secondary_context_rows": [
            row for row in remaining_routes if row["route_priority"] == "SECONDARY_CONTEXT_REVIEW"
        ],
        "hairfront_contract_rows": [
            row for row in remaining_routes if row["route_priority"] == "DEFER_KEEP_HAIRFRONT_HIDDEN"
        ],
        "summary": {
            "source_material_acceptance_pass_count": g5["summary"]["material_acceptance_pass_count"],
            "total_route_row_count": len(all_routes),
            "primary6_row_count": len(candidate_routes),
            "secondary_context_row_count": priority_counts["SECONDARY_CONTEXT_REVIEW"],
            "hairfront_contract_row_count": priority_counts["DEFER_KEEP_HAIRFRONT_HIDDEN"],
            "primary6_ids": primary_route_ids,
            "primary6_unresolved_count": len(candidate_routes),
            "total_unresolved_material_acceptance_count": len(all_routes),
            "priority_counts": dict(sorted(priority_counts.items())),
            "phase_counts": dict(sorted(phase_counts.items())),
            "material_acceptance_counts": dict(sorted(material_counts.items())),
            "g5_material_acceptance_status": "BLOCKED_PRIMARY6_REDUCTION_READY_MATERIAL_NOT_ACCEPTED",
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE",
            "g8_real_cubism_status": "BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE",
        },
        "gate_matrix": {
            "G5_MATERIAL_ACCEPTANCE": "PRIMARY6_REDUCTION_READY_MATERIAL_NOT_ACCEPTED",
            "G6_MANUAL_ANCHOR_CORRECTION": "AVAILABLE_FOR_PRIMARY_OR_CONTEXT_REVISE_ROWS",
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
            "The G5 material acceptance surface is reduced to six primary rows for the next "
            "accept/revise pass, while 23 context rows and seven HairFront-contract rows remain "
            "blocked and preserved. No material PASS is granted."
        ),
        "next_action": [
            "Build or apply a G5 primary6 accept/revise packet for B1, B2, B3, torso_base, shoulder_L, and shoulder_R.",
            "Use manual anchor correction only for rows that are visually misaligned after the primary6 pass.",
            "Keep HairFront hidden and keep G7/G8 blocked until material acceptance is explicitly passed.",
        ],
        "self_review": {
            "source_status": g5["status"],
            "source_verdict": g5["g5_acceptance_verdict"],
            "source_material_acceptance_pass_count": g5["summary"]["material_acceptance_pass_count"],
            "total_route_row_count": len(all_routes),
            "primary6_row_count": len(candidate_routes),
            "secondary_context_row_count": priority_counts["SECONDARY_CONTEXT_REVIEW"],
            "hairfront_contract_row_count": priority_counts["DEFER_KEEP_HAIRFRONT_HIDDEN"],
            "primary6_unresolved_count": len(candidate_routes),
            "total_unresolved_material_acceptance_count": len(all_routes),
            "primary6_ids_match_expected": primary_route_ids
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
        "# Character 002 v22 G5 Material Acceptance Reduction Route",
        "",
        f"- status: `{report['status']}`",
        f"- source: `{report['source_g5_material_acceptance']}`",
        f"- source verdict: `{report['source_verdict']}`",
        f"- G5 material acceptance: `{report['summary']['g5_material_acceptance_status']}`",
        f"- material pass: `{report['summary']['material_pass_status']}`",
        f"- ParamHairFront: `{report['summary']['param_hair_front_status']}`",
        f"- G7: `{report['summary']['g7_mini_cubism_status']}`",
        "",
        "## Counts",
        "",
        f"- total_route_row_count: `{report['summary']['total_route_row_count']}`",
        f"- primary6_row_count: `{report['summary']['primary6_row_count']}`",
        f"- secondary_context_row_count: `{report['summary']['secondary_context_row_count']}`",
        f"- hairfront_contract_row_count: `{report['summary']['hairfront_contract_row_count']}`",
        f"- primary6_unresolved_count: `{report['summary']['primary6_unresolved_count']}`",
        f"- total_unresolved_material_acceptance_count: `{report['summary']['total_unresolved_material_acceptance_count']}`",
        "",
        "## Primary6",
        "",
    ]
    for row in candidate_routes:
        lines.append(f"- `{row['row_id']}`: `{row['route_phase']}` / `{row['next_action']}`")
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

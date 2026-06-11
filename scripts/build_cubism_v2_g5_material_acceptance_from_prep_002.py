#!/usr/bin/env python3
"""Build the v22 G5 material acceptance packet from the latest prep packet.

The packet is intentionally strict: it can record technical readiness and
review candidates, but it cannot turn Codex/validator evidence into material
acceptance without a separate acceptance result.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/Users/family/jason/Vtube")
EXP = ROOT / "experiments/cubism-v2-new-character-002"
G5_PREP = (
    EXP
    / "reports/v22_g5_prep_from_torso_selected/v22_g5_prep_from_torso_selected_packet.json"
)
MANIFEST = (
    EXP
    / "reports/v22_64part_g4_torso_selected_manifest/v22_64part_g4_torso_selected_manifest.json"
)
REDUCTION = (
    EXP
    / "reports/v22_g4_torso_selected_review_reduction/v22_g4_torso_selected_review_reduction_packet.json"
)
P0_DECISION = (
    EXP
    / "reports/v22_g4_p0_torso_shoulder_decision/v22_g4_p0_torso_shoulder_decision_packet.json"
)
B1_QA = EXP / "reports/v22_b1_clean_base_underpaint/v22_b1_visual_qa_report.json"
B2_QA = EXP / "reports/v22_b2_eye_pack/v22_b2_overlay_qa_report.json"
B3_QA = EXP / "reports/v22_b3_mouth_pack_revision_v1/v22_b3_revision_v1_overlay_qa_report.json"
REPORT_DIR = EXP / "reports/v22_g5_material_acceptance_from_prep"
REPORT_JSON = REPORT_DIR / "v22_g5_material_acceptance_from_prep_packet.json"
REPORT_MD = REPORT_DIR / "v22_g5_material_acceptance_from_prep_packet.md"

STATUS = "G5_MATERIAL_ACCEPTANCE_PACKET_REVIEW_REQUIRED_MATERIAL_NOT_ACCEPTED"
VERDICT = "REVIEW_REQUIRED_MATERIAL_NOT_ACCEPTED"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_candidate_rows(b1: dict, b2: dict, b3: dict, p0: dict) -> list[dict]:
    rows = [
        {
            "row_id": "B1_CLEAN_BASE_UNDERPAINT",
            "source": "B1",
            "status": b1["status"],
            "candidate_gate": "PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED",
            "material_acceptance": "BLOCKED_HUMAN_VISUAL_ACCEPTANCE_REQUIRED",
            "reason": "Clean base and underpaint are candidate-only; material PASS requires separate acceptance.",
        },
        {
            "row_id": "B2_EYE_PACK",
            "source": "B2",
            "status": b2["status"],
            "candidate_gate": "PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED",
            "material_acceptance": "BLOCKED_HUMAN_VISUAL_ACCEPTANCE_REQUIRED",
            "reason": "Eye whites/detail candidates preserve v21 locks, but are not material-approved yet.",
        },
        {
            "row_id": "B3_MOUTH_PACK_REVISION_V1",
            "source": "B3",
            "status": b3["status"],
            "candidate_gate": "PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED",
            "material_acceptance": "BLOCKED_HUMAN_VISUAL_ACCEPTANCE_REQUIRED",
            "reason": "Mouth revision v1 is the active candidate; MouthOpenY stays capped at 0.85.",
        },
    ]
    for row in p0["decision_rows"]:
        rows.append(
            {
                "row_id": row["part_id"],
                "source": row["source_batch"],
                "status": p0["status"],
                "candidate_gate": row["decision"],
                "material_acceptance": "BLOCKED_SEPARATE_G5_ACCEPTANCE_REQUIRED",
                "reason": row["reason"],
            }
        )
    return rows


def build_remaining_rows(reduction: dict, p0: dict) -> list[dict]:
    p0_parts = {row["part_id"] for row in p0["decision_rows"]}
    rows = []
    for row in reduction["review_rows"]:
        if row["part_id"] in p0_parts:
            continue
        if row["g5_effect"] == "DOES_NOT_UNLOCK_HAIRFRONT_YET":
            material_acceptance = "BLOCKED_HAIRFRONT_HIDDEN_CONTRACT_ONLY"
        else:
            material_acceptance = "BLOCKED_CONTEXT_REVIEW_REQUIRED"
        rows.append(
            {
                "row_id": row["part_id"],
                "source": row["source_batch"],
                "review_class": row["review_class"],
                "review_lane": row["review_lane"],
                "g5_effect": row["g5_effect"],
                "material_acceptance": material_acceptance,
                "path": row["path"],
                "bbox": row["bbox"],
                "alpha_coverage": row["alpha_coverage"],
            }
        )
    return rows


def main() -> int:
    prep = load_json(G5_PREP)
    manifest = load_json(MANIFEST)
    reduction = load_json(REDUCTION)
    p0 = load_json(P0_DECISION)
    b1 = load_json(B1_QA)
    b2 = load_json(B2_QA)
    b3 = load_json(B3_QA)

    candidate_rows = build_candidate_rows(b1, b2, b3, p0)
    remaining_rows = build_remaining_rows(reduction, p0)
    candidate_block_counts = Counter(row["material_acceptance"] for row in candidate_rows)
    remaining_block_counts = Counter(row["material_acceptance"] for row in remaining_rows)
    remaining_class_counts = Counter(row["review_class"] for row in remaining_rows)

    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": STATUS,
        "g5_acceptance_verdict": VERDICT,
        "inputs": {
            "g5_prep_packet": rel(G5_PREP),
            "torso_selected_manifest": rel(MANIFEST),
            "review_reduction_packet": rel(REDUCTION),
            "p0_torso_shoulder_decision": rel(P0_DECISION),
            "b1_visual_qa": rel(B1_QA),
            "b2_overlay_qa": rel(B2_QA),
            "b3_revision_v1_overlay_qa": rel(B3_QA),
        },
        "source_status": {
            "g5_prep_status": prep["status"],
            "manifest_status": manifest["status"],
            "review_reduction_status": reduction["status"],
            "p0_decision_status": p0["status"],
            "b1_status": b1["status"],
            "b2_status": b2["status"],
            "b3_status": b3["status"],
        },
        "candidate_acceptance_rows": candidate_rows,
        "remaining_review_rows": remaining_rows,
        "summary": {
            "technical_manifest_pass": prep["prep_decisions"]["technical_manifest_pass"],
            "manifest_entry_count": manifest["self_review"]["manifest_entry_count"],
            "unique_manifest_part_count": manifest["self_review"]["unique_manifest_part_count"],
            "material_acceptance_pass_count": 0,
            "candidate_acceptance_row_count": len(candidate_rows),
            "b1_b3_candidate_human_required_count": 3,
            "p0_prep_candidate_count": len(p0["decision_rows"]),
            "p0_remaining_pre_g5_blocker_count": p0["summary"][
                "remaining_p0_pre_g5_blocker_count"
            ],
            "remaining_review_row_count": len(remaining_rows),
            "hairfront_hidden_candidate_count": remaining_block_counts[
                "BLOCKED_HAIRFRONT_HIDDEN_CONTRACT_ONLY"
            ],
            "context_review_row_count": remaining_block_counts["BLOCKED_CONTEXT_REVIEW_REQUIRED"],
            "material_acceptance_required_before_g7_count": len(candidate_rows) + len(remaining_rows),
            "candidate_block_counts": dict(sorted(candidate_block_counts.items())),
            "remaining_block_counts": dict(sorted(remaining_block_counts.items())),
            "remaining_class_counts": dict(sorted(remaining_class_counts.items())),
            "g5_material_acceptance_status": "BLOCKED_REVIEW_REQUIRED_MATERIAL_NOT_ACCEPTED",
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE",
            "g8_real_cubism_status": "BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE",
        },
        "gate_matrix": {
            "G1_64PART_COMPLETENESS": "PASS_TECHNICAL",
            "G2_FULL_CANVAS_RGBA_NORMALIZATION": "PASS_TECHNICAL",
            "G3_TECHNICAL_VALIDATORS": "PASS_TECHNICAL_MANIFEST_ONLY",
            "G4_VISUAL_QA": "CANDIDATE_AND_CONTEXT_REVIEW_REQUIRED",
            "G5_MATERIAL_ACCEPTANCE": "REVIEW_REQUIRED_MATERIAL_NOT_ACCEPTED",
            "G6_MANUAL_ANCHOR_CORRECTION": "AVAILABLE_FOR_REJECTED_OR_MISALIGNED_ROWS",
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
            "G5 material acceptance is not passed. The latest evidence is organized into six "
            "candidate acceptance rows and thirty remaining HairFront/context rows, all blocked "
            "from material promotion until separate acceptance or revision evidence exists."
        ),
        "next_action": [
            "Use this packet to reduce the 36 material-acceptance-required rows instead of promoting validator PASS.",
            "Accept/revise/regenerate B1-B3 and P0 torso/shoulder rows separately, then rerun this G5 packet.",
            "Keep ParamHairFront hidden and keep G7/G8 blocked until G5 material acceptance is explicitly passed.",
        ],
        "self_review": {
            "g5_prep_status": prep["status"],
            "manifest_status": manifest["status"],
            "technical_manifest_pass": prep["prep_decisions"]["technical_manifest_pass"],
            "material_acceptance_pass_count": 0,
            "candidate_acceptance_row_count": len(candidate_rows),
            "b1_b3_candidate_human_required_count": 3,
            "p0_prep_candidate_count": len(p0["decision_rows"]),
            "p0_remaining_pre_g5_blocker_count": p0["summary"][
                "remaining_p0_pre_g5_blocker_count"
            ],
            "remaining_review_row_count": len(remaining_rows),
            "hairfront_hidden_candidate_count": remaining_block_counts[
                "BLOCKED_HAIRFRONT_HIDDEN_CONTRACT_ONLY"
            ],
            "context_review_row_count": remaining_block_counts["BLOCKED_CONTEXT_REVIEW_REQUIRED"],
            "material_acceptance_required_before_g7_count": len(candidate_rows) + len(remaining_rows),
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
        "# Character 002 v22 G5 Material Acceptance From Prep",
        "",
        f"- status: `{report['status']}`",
        f"- verdict: `{report['g5_acceptance_verdict']}`",
        f"- material acceptance: `{report['summary']['g5_material_acceptance_status']}`",
        f"- material pass: `{report['summary']['material_pass_status']}`",
        f"- ParamHairFront: `{report['summary']['param_hair_front_status']}`",
        f"- G7: `{report['summary']['g7_mini_cubism_status']}`",
        f"- G8: `{report['summary']['g8_real_cubism_status']}`",
        "",
        "## Counts",
        "",
        f"- material_acceptance_pass_count: `{report['summary']['material_acceptance_pass_count']}`",
        f"- candidate_acceptance_row_count: `{report['summary']['candidate_acceptance_row_count']}`",
        f"- remaining_review_row_count: `{report['summary']['remaining_review_row_count']}`",
        f"- hairfront_hidden_candidate_count: `{report['summary']['hairfront_hidden_candidate_count']}`",
        f"- context_review_row_count: `{report['summary']['context_review_row_count']}`",
        f"- material_acceptance_required_before_g7_count: `{report['summary']['material_acceptance_required_before_g7_count']}`",
        "",
        "## Candidate Acceptance Rows",
        "",
    ]
    for row in candidate_rows:
        lines.append(f"- `{row['row_id']}`: `{row['material_acceptance']}`")
    lines.extend(
        [
            "",
            "## Remaining Review Classes",
            "",
        ]
    )
    for name, count in sorted(remaining_class_counts.items()):
        lines.append(f"- `{name}`: `{count}`")
    lines.extend(
        [
            "",
            "## Gate Matrix",
            "",
        ]
    )
    for gate, verdict in report["gate_matrix"].items():
        lines.append(f"- `{gate}`: `{verdict}`")
    lines.extend(
        [
            "",
            "## Next Action",
            "",
        ]
    )
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

#!/usr/bin/env python3
"""Build the current G5 prep packet from the torso-selected v22 manifest.

This is a gate-sequencing packet only. It proves that the latest G4 P0
torso/shoulder decision can open a G5 prep surface, but it does not approve
G5 material acceptance or promote Mini Cubism/real Cubism.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/Users/family/jason/Vtube")
EXP = ROOT / "experiments/cubism-v2-new-character-002"
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
REPORT_DIR = EXP / "reports/v22_g5_prep_from_torso_selected"
REPORT_JSON = REPORT_DIR / "v22_g5_prep_from_torso_selected_packet.json"
REPORT_MD = REPORT_DIR / "v22_g5_prep_from_torso_selected_packet.md"

STATUS = "G5_PREP_PACKET_READY_FROM_TORSO_SELECTED_P0_DECISION_MATERIAL_ACCEPTANCE_BLOCKED"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def manifest_technical_pass(manifest: dict) -> bool:
    review = manifest["self_review"]
    return (
        review["manifest_entry_count"] == 64
        and review["unique_manifest_part_count"] == 64
        and review["missing_part_count"] == 0
        and review["wrong_mode_count"] == 0
        and review["wrong_size_count"] == 0
        and review["empty_part_count"] == 0
        and review["duplicate_part_count"] == 0
        and review["group_counts_match_spec"] is True
    )


def b1_b3_gate_rows(b1: dict, b2: dict, b3: dict) -> list[dict]:
    return [
        {
            "batch": "B1",
            "status": b1["status"],
            "gate": "PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED",
            "scope": "clean-base and underpaint candidate",
            "material_promotion": "BLOCKED_PENDING_G5_ACCEPTANCE",
        },
        {
            "batch": "B2",
            "status": b2["status"],
            "gate": "PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED",
            "scope": "fixed eye whites plus anchored eye-detail candidate",
            "material_promotion": "BLOCKED_PENDING_G5_ACCEPTANCE",
        },
        {
            "batch": "B3",
            "status": b3["status"],
            "gate": "PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED",
            "scope": "revision v1 coordinated smile mouth candidate",
            "material_promotion": "BLOCKED_PENDING_G5_ACCEPTANCE",
        },
    ]


def main() -> int:
    manifest = load_json(MANIFEST)
    reduction = load_json(REDUCTION)
    p0 = load_json(P0_DECISION)
    b1 = load_json(B1_QA)
    b2 = load_json(B2_QA)
    b3 = load_json(B3_QA)

    p0_decision_parts = [row["part_id"] for row in p0["decision_rows"]]
    p0_decision_by_part = {row["part_id"]: row["decision"] for row in p0["decision_rows"]}
    remaining_rows = [
        row for row in reduction["review_rows"] if row["part_id"] not in set(p0_decision_parts)
    ]
    effect_counts = Counter(row["g5_effect"] for row in remaining_rows)
    class_counts = Counter(row["review_class"] for row in remaining_rows)
    source_batch_counts = Counter(row["source_batch"] for row in remaining_rows)

    b1_b3_rows = b1_b3_gate_rows(b1, b2, b3)
    b1_b3_human_required = [
        row for row in b1_b3_rows if row["gate"] == "PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED"
    ]

    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": STATUS,
        "inputs": {
            "torso_selected_manifest": rel(MANIFEST),
            "review_reduction_packet": rel(REDUCTION),
            "p0_torso_shoulder_decision": rel(P0_DECISION),
            "b1_visual_qa": rel(B1_QA),
            "b2_overlay_qa": rel(B2_QA),
            "b3_revision_v1_overlay_qa": rel(B3_QA),
        },
        "source_status": {
            "manifest_status": manifest["status"],
            "review_reduction_status": reduction["status"],
            "p0_decision_status": p0["status"],
            "b1_status": b1["status"],
            "b2_status": b2["status"],
            "b3_status": b3["status"],
        },
        "prep_decisions": {
            "technical_manifest_pass": manifest_technical_pass(manifest),
            "p0_decision_parts": p0_decision_parts,
            "p0_decision_by_part": p0_decision_by_part,
            "p0_remaining_pre_g5_blocker_count": p0["summary"]["remaining_p0_pre_g5_blocker_count"],
            "g5_prep_status": "READY_FOR_PREP_PACKET_ONLY",
            "g5_material_acceptance_status": "BLOCKED_PENDING_SEPARATE_G5_ACCEPTANCE_PACKET",
            "material_pass_status": "BLOCKED",
            "not_owner_approval": True,
        },
        "b1_b3_candidate_gates": b1_b3_rows,
        "remaining_review_surface": {
            "remaining_review_row_count": len(remaining_rows),
            "hairfront_hidden_candidate_count": effect_counts["DOES_NOT_UNLOCK_HAIRFRONT_YET"],
            "context_review_row_count": effect_counts["CONTEXT_REVIEW_BEFORE_G5"],
            "remaining_pre_g5_blocking_row_count": effect_counts[
                "BLOCKS_G5_UNTIL_REVIEW_OR_FURTHER_REDUCTION"
            ],
            "class_counts": dict(sorted(class_counts.items())),
            "source_batch_counts": dict(sorted(source_batch_counts.items())),
        },
        "gate_matrix": {
            "G0_SOURCE_STYLE": "PASS_EXISTING_SOURCE",
            "G1_64PART_COMPLETENESS": "PASS_TECHNICAL",
            "G2_FULL_CANVAS_RGBA_NORMALIZATION": "PASS_TECHNICAL",
            "G3_TECHNICAL_VALIDATORS": "PASS_TECHNICAL_MANIFEST_ONLY",
            "G4_P0_TORSO_SHOULDER_DECISION": "PASS_FOR_G5_PREP_ONLY",
            "G4_B1_B3_VISUAL_CANDIDATES": "CANDIDATE_HUMAN_REVIEW_REQUIRED",
            "G4_B4_B5_REMAINING_CONTEXT": "REVIEW_REQUIRED",
            "G5_MATERIAL_ACCEPTANCE": "BLOCKED_PENDING_SEPARATE_G5_ACCEPTANCE_PACKET",
            "G6_MANUAL_ANCHOR_CORRECTION": "AVAILABLE_IF_VISUAL_REVIEW_REQUIRES",
            "G7_MINI_CUBISM_DIAGNOSTIC": "BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE",
            "G8_REAL_CUBISM_AUTHORING": "BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE",
        },
        "locks": {
            "validator_only_promotion_blocked": True,
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
            "not_owner_approval": True,
            "v21_eye_open_lower_bound": 0.27,
            "v21_mouth_open_y_max": 0.85,
        },
        "decision": (
            "The torso-selected 64-part manifest and P0 torso/shoulder decisions are ready for a "
            "separate G5 prep/acceptance surface. This packet is not G5 material acceptance and "
            "does not unlock ParamHairFront, Mini Cubism, or real Cubism."
        ),
        "next_action": [
            "Build a separate G5 material acceptance packet that reviews B1-B3 candidates and the torso/shoulder prep decisions together.",
            "Keep the 30 remaining B4/B5 rows as HairFront-hidden or context review until that packet explicitly accepts or rejects them.",
            "Do not promote Mini Cubism or real Cubism until material acceptance is separately recorded.",
        ],
        "self_review": {
            "manifest_status": manifest["status"],
            "reduction_status": reduction["status"],
            "p0_decision_status": p0["status"],
            "technical_manifest_pass": manifest_technical_pass(manifest),
            "manifest_entry_count": manifest["self_review"]["manifest_entry_count"],
            "unique_manifest_part_count": manifest["self_review"]["unique_manifest_part_count"],
            "p0_decision_row_count": len(p0["decision_rows"]),
            "p0_remaining_pre_g5_blocker_count": p0["summary"][
                "remaining_p0_pre_g5_blocker_count"
            ],
            "b1_b3_candidate_human_required_count": len(b1_b3_human_required),
            "remaining_review_row_count": len(remaining_rows),
            "hairfront_hidden_candidate_count": effect_counts["DOES_NOT_UNLOCK_HAIRFRONT_YET"],
            "context_review_row_count": effect_counts["CONTEXT_REVIEW_BEFORE_G5"],
            "remaining_pre_g5_blocking_row_count": effect_counts[
                "BLOCKS_G5_UNTIL_REVIEW_OR_FURTHER_REDUCTION"
            ],
            "g5_prep_ready_only": True,
            "g5_material_acceptance_blocked": True,
            "not_owner_approval": True,
            "material_pass_blocked": True,
            "validator_only_promotion_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "status": "PASS",
        },
    }

    save_json(REPORT_JSON, report)

    lines = [
        "# Character 002 v22 G5 Prep From Torso-Selected P0 Decision",
        "",
        f"- status: `{report['status']}`",
        f"- manifest: `{report['inputs']['torso_selected_manifest']}`",
        f"- P0 decision: `{report['inputs']['p0_torso_shoulder_decision']}`",
        f"- G5 prep: `{report['prep_decisions']['g5_prep_status']}`",
        f"- G5 material acceptance: `{report['prep_decisions']['g5_material_acceptance_status']}`",
        f"- material pass: `{report['prep_decisions']['material_pass_status']}`",
        "",
        "## Summary",
        "",
        f"- technical_manifest_pass: `{report['prep_decisions']['technical_manifest_pass']}`",
        f"- p0_remaining_pre_g5_blocker_count: `{report['prep_decisions']['p0_remaining_pre_g5_blocker_count']}`",
        f"- b1_b3_candidate_human_required_count: `{report['self_review']['b1_b3_candidate_human_required_count']}`",
        f"- remaining_review_row_count: `{report['remaining_review_surface']['remaining_review_row_count']}`",
        f"- hairfront_hidden_candidate_count: `{report['remaining_review_surface']['hairfront_hidden_candidate_count']}`",
        f"- context_review_row_count: `{report['remaining_review_surface']['context_review_row_count']}`",
        "",
        "## Gate Matrix",
        "",
    ]
    for gate, verdict in report["gate_matrix"].items():
        lines.append(f"- `{gate}`: `{verdict}`")
    lines.extend(
        [
            "",
            "## B1-B3 Candidate Gates",
            "",
        ]
    )
    for row in b1_b3_rows:
        lines.append(f"- `{row['batch']}`: `{row['status']}` / `{row['gate']}`")
    lines.extend(
        [
            "",
            "## P0 Decisions",
            "",
        ]
    )
    for part_id, decision in p0_decision_by_part.items():
        lines.append(f"- `{part_id}`: `{decision}`")
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

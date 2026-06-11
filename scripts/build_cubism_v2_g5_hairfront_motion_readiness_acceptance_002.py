#!/usr/bin/env python3
"""Build the v22 HairFront motion-readiness acceptance packet.

The seven front-hair child PNGs exist as independent candidates, but this
packet keeps ParamHairFront hidden because motion-readiness/owner acceptance is
not proven by static PNG existence alone.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/Users/family/jason/Vtube")
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SOURCE = EXP / "reports/v22_g5_secondary_hairfront_reduction/v22_g5_secondary_hairfront_reduction_packet.json"
REPORT_DIR = EXP / "reports/v22_g5_hairfront_motion_readiness_acceptance"
REPORT_JSON = REPORT_DIR / "v22_g5_hairfront_motion_readiness_acceptance_packet.json"
REPORT_MD = REPORT_DIR / "v22_g5_hairfront_motion_readiness_acceptance_packet.md"

STATUS = "G5_HAIRFRONT_MOTION_READINESS_REVIEW_REQUIRED_PARAM_HIDDEN"
VERDICT = "REVIEW_REQUIRED_KEEP_PARAM_HAIRFRONT_HIDDEN"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def row_acceptance(row: dict) -> dict:
    png_path = ROOT / row["path"]
    exists = png_path.exists()
    return {
        **row,
        "png_exists": exists,
        "independent_part_candidate": exists
        and row.get("bbox") is not None
        and row.get("alpha_coverage", 0) > 0,
        "motion_readiness_verdict": "STATIC_PART_PRESENT_MOTION_READINESS_REVIEW_REQUIRED",
        "param_hairfront_activation": "BLOCKED_KEEP_HIDDEN_CONTRACT_ONLY",
        "material_acceptance": "BLOCKED_PENDING_HAIRFRONT_MOTION_READINESS_ACCEPTANCE",
        "owner_approval": "NOT_OWNER_APPROVAL",
    }


def main() -> int:
    source = load_json(SOURCE)
    rows = [row_acceptance(row) for row in source["hairfront_contract_rows"]]
    verdict_counts = Counter(row["motion_readiness_verdict"] for row in rows)
    activation_counts = Counter(row["param_hairfront_activation"] for row in rows)
    all_png_exist = all(row["png_exists"] for row in rows)
    all_independent_candidates = all(row["independent_part_candidate"] for row in rows)

    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": STATUS,
        "hairfront_acceptance_verdict": VERDICT,
        "source_secondary_hairfront_reduction": rel(SOURCE),
        "source_status": source["status"],
        "hairfront_rows": rows,
        "summary": {
            "source_g5_material_acceptance_remaining_count": source["summary"][
                "g5_material_acceptance_remaining_count"
            ],
            "hairfront_row_count": len(rows),
            "hairfront_png_exists_count": sum(1 for row in rows if row["png_exists"]),
            "independent_part_candidate_count": sum(
                1 for row in rows if row["independent_part_candidate"]
            ),
            "motion_readiness_pass_count": 0,
            "motion_readiness_review_required_count": verdict_counts[
                "STATIC_PART_PRESENT_MOTION_READINESS_REVIEW_REQUIRED"
            ],
            "param_hairfront_activation_count": 0,
            "param_hairfront_hidden_count": activation_counts[
                "BLOCKED_KEEP_HIDDEN_CONTRACT_ONLY"
            ],
            "material_acceptance_pass_count": 0,
            "owner_approval_count": 0,
            "g5_material_acceptance_remaining_count": len(rows),
            "all_png_exist": all_png_exist,
            "all_independent_candidates": all_independent_candidates,
            "g5_material_acceptance_status": "BLOCKED_HAIRFRONT_MOTION_READINESS_REVIEW_REQUIRED",
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE",
            "g8_real_cubism_status": "BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE",
        },
        "gate_matrix": {
            "G5_HAIRFRONT_STATIC_PARTS": "PRESENT_AS_INDEPENDENT_CANDIDATES",
            "G5_HAIRFRONT_MOTION_READINESS": "REVIEW_REQUIRED_KEEP_PARAM_HIDDEN",
            "G5_MATERIAL_ACCEPTANCE": "BLOCKED_HAIRFRONT_MOTION_READINESS_REVIEW_REQUIRED",
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
            "Seven front-hair child PNGs exist as independent candidates, but motion-readiness is "
            "not accepted from static evidence alone. ParamHairFront remains hidden/contract-only, "
            "G5 material acceptance remains blocked, and G7/G8 remain blocked."
        ),
        "next_action": [
            "Create a HairFront motion-readiness preview or pose-sweep packet that demonstrates safe independent front-hair motion.",
            "Keep ParamHairFront hidden until that motion-readiness packet explicitly passes.",
            "Do not start G7 Mini Cubism from static HairFront PNG existence alone.",
        ],
        "self_review": {
            "source_status": source["status"],
            "source_g5_material_acceptance_remaining_count": source["summary"][
                "g5_material_acceptance_remaining_count"
            ],
            "hairfront_row_count": len(rows),
            "hairfront_png_exists_count": sum(1 for row in rows if row["png_exists"]),
            "independent_part_candidate_count": sum(
                1 for row in rows if row["independent_part_candidate"]
            ),
            "motion_readiness_pass_count": 0,
            "motion_readiness_review_required_count": verdict_counts[
                "STATIC_PART_PRESENT_MOTION_READINESS_REVIEW_REQUIRED"
            ],
            "param_hairfront_activation_count": 0,
            "param_hairfront_hidden_count": activation_counts[
                "BLOCKED_KEEP_HIDDEN_CONTRACT_ONLY"
            ],
            "material_acceptance_pass_count": 0,
            "owner_approval_count": 0,
            "g5_material_acceptance_remaining_count": len(rows),
            "all_png_exist": all_png_exist,
            "all_independent_candidates": all_independent_candidates,
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
        "# Character 002 v22 HairFront Motion Readiness Acceptance",
        "",
        f"- status: `{report['status']}`",
        f"- verdict: `{report['hairfront_acceptance_verdict']}`",
        f"- source: `{report['source_secondary_hairfront_reduction']}`",
        f"- G5 material acceptance: `{report['summary']['g5_material_acceptance_status']}`",
        f"- ParamHairFront: `{report['summary']['param_hair_front_status']}`",
        f"- G7: `{report['summary']['g7_mini_cubism_status']}`",
        "",
        "## Counts",
        "",
        f"- hairfront_row_count: `{report['summary']['hairfront_row_count']}`",
        f"- hairfront_png_exists_count: `{report['summary']['hairfront_png_exists_count']}`",
        f"- independent_part_candidate_count: `{report['summary']['independent_part_candidate_count']}`",
        f"- motion_readiness_pass_count: `{report['summary']['motion_readiness_pass_count']}`",
        f"- motion_readiness_review_required_count: `{report['summary']['motion_readiness_review_required_count']}`",
        f"- param_hairfront_activation_count: `{report['summary']['param_hairfront_activation_count']}`",
        f"- material_acceptance_pass_count: `{report['summary']['material_acceptance_pass_count']}`",
        "",
        "## HairFront Rows",
        "",
    ]
    for row in rows:
        lines.append(
            f"- `{row['row_id']}`: `{row['motion_readiness_verdict']}` / `{row['param_hairfront_activation']}`"
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
    print(STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

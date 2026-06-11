#!/usr/bin/env python3
"""Record conservative visual QA for B5 refined-mask v2."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
V2_REPORT_JSON = EXP / "reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_report.json"
REPORT_JSON = EXP / "reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_overlay_qa_report.json"
REPORT_MD = EXP / "reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_overlay_qa_report.md"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def main() -> int:
    v2 = json.loads(V2_REPORT_JSON.read_text(encoding="utf-8"))
    checks = [
        {
            "id": "technical_refined_mask_v2_pack",
            "status": "PASS_TECHNICAL",
            "evidence": "B5 refined-mask v2 generated 17/17 full-canvas 2048 RGBA non-empty candidates, with six focused v2 refinements and eleven v1 copies.",
        },
        {
            "id": "focused_mask_reduction",
            "status": "IMPROVED_CANDIDATE_REVIEW_REQUIRED",
            "evidence": "Torso, shoulders, face shadows, and nose are narrower than v1 in the overlay sheet.",
        },
        {
            "id": "body_semantic_quality",
            "status": "REVISE_REGENERATE_OR_REEXTRACT",
            "evidence": "Torso and shoulders still read as broad body patches rather than clean source-matched B5 production parts. More alpha shrinking risks losing required body/clothing material.",
        },
        {
            "id": "face_detail_quality",
            "status": "REVIEW_REQUIRED",
            "evidence": "Nose and face shadows are smaller and may be reviewable, but should not be promoted without 주인님 visual acceptance.",
        },
        {
            "id": "material_promotion_gate",
            "status": "BLOCKED",
            "evidence": "B5 v2 remains candidate evidence only. Technical validators cannot promote it to material PASS.",
        },
        {
            "id": "g7_g8_gate",
            "status": "BLOCKED",
            "evidence": "Mini Cubism diagnostic and real Cubism authoring remain blocked until B4/B5 visual QA and human review accept corrected materials.",
        },
    ]
    report = {
        "schema_version": "v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": "B5_REFINED_MASK_V2_OVERLAY_QA_REVISE_REGENERATE_OR_HUMAN_REVIEW_REQUIRED",
        "v2_report": rel(V2_REPORT_JSON),
        "overlay_sheet": v2["overlay_sheet"],
        "contact_sheet": v2["contact_sheet"],
        "checks": checks,
        "remaining_b5_revise_parts": [
            "torso_base",
            "shoulder_L",
            "shoulder_R",
        ],
        "possible_human_review_parts": [
            "nose",
            "face_shadow_L",
            "face_shadow_R",
        ],
        "decision": "Keep B5 refined-mask v2 as the current best automatic mask-reduction candidate, but do not keep shrinking body masks blindly. Torso and shoulders should move to regeneration/re-extraction or human review; nose/face shadows can be reviewed as smaller candidates.",
        "next_action": [
            "Do not ask 주인님 to anchor all B5 parts.",
            "Use regeneration/re-extraction for torso_base and shoulder_L/R, or ask 주인님 for focused acceptance/rejection of those three.",
            "Review nose and face shadows as small candidates if needed.",
            "Keep B4 hair focused review separate and keep G7/G8 blocked.",
        ],
        "self_review": {
            "v2_report_status": v2["status"],
            "refined_mask_v2_count": v2["self_review"]["refined_mask_v2_count"],
            "copied_from_v1_count": v2["self_review"]["copied_from_v1_count"],
            "has_revise_gate": True,
            "has_regenerate_or_reextract_gate": True,
            "has_blocked_material_gate": True,
            "validator_only_promotion_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "status": "PASS",
        },
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Character 002 v22 B5 Refined Mask v2 Overlay QA",
        "",
        f"- status: `{report['status']}`",
        f"- v2 report: `{report['v2_report']}`",
        f"- overlay sheet: `{report['overlay_sheet']}`",
        "",
        "## Checks",
        "",
    ]
    for check in checks:
        lines.append(f"- `{check['status']}` `{check['id']}`: {check['evidence']}")
    lines.extend(
        [
            "",
            "## Remaining B5 Revise Parts",
            "",
            *[f"- `{part}`" for part in report["remaining_b5_revise_parts"]],
            "",
            "## Possible Human Review Parts",
            "",
            *[f"- `{part}`" for part in report["possible_human_review_parts"]],
            "",
            "## Decision",
            "",
            report["decision"],
            "",
            "## Next Action",
            "",
            *[f"- {item}" for item in report["next_action"]],
            "",
            "## Self Review",
            "",
        ]
    )
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": report["status"], "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

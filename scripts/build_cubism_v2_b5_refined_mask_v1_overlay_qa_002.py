#!/usr/bin/env python3
"""Record conservative visual QA for B5 refined-mask v1."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
REFINED_REPORT_JSON = EXP / "reports/v22_b5_refined_mask_v1/v22_b5_refined_mask_v1_report.json"
REPORT_JSON = EXP / "reports/v22_b5_refined_mask_v1/v22_b5_refined_mask_v1_overlay_qa_report.json"
REPORT_MD = EXP / "reports/v22_b5_refined_mask_v1/v22_b5_refined_mask_v1_overlay_qa_report.md"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def main() -> int:
    refined = json.loads(REFINED_REPORT_JSON.read_text(encoding="utf-8"))
    checks = [
        {
            "id": "technical_refined_mask_pack",
            "status": "PASS_TECHNICAL",
            "evidence": "B5 refined-mask v1 generated 17/17 full-canvas 2048 RGBA non-empty candidates, with 13 targeted mask refinements and 4 copied auto-draft controls.",
        },
        {
            "id": "json_override_rebuild_path",
            "status": "PASS_TECHNICAL",
            "evidence": "The B5 refined candidates were built downstream of the auto-draft JSON override path, proving repeatable regeneration instead of one-off manual edits.",
        },
        {
            "id": "face_detail_mask_reduction",
            "status": "IMPROVED_CANDIDATE_REVIEW_REQUIRED",
            "evidence": "Nose, cheek, and face-shadow masks are smaller/softer than the previous auto-draft overlay, but still require visual review and may need another semantic mask pass.",
        },
        {
            "id": "body_clothing_mask_quality",
            "status": "REVISE_EXTRACTION_MASK",
            "evidence": "Torso and shoulder/body regions still read as broad overlay patches in the QA sheet. Anchor movement is not the main issue; extraction-mask semantics need more refinement or regeneration.",
        },
        {
            "id": "material_promotion_gate",
            "status": "BLOCKED",
            "evidence": "Do not promote B5 material quality from this v1. Validator and full-canvas PNG checks are technical evidence only.",
        },
        {
            "id": "g7_g8_gate",
            "status": "BLOCKED",
            "evidence": "Mini Cubism diagnostic and real Cubism authoring remain blocked until B4/B5 visual QA and 주인님 review accept corrected materials.",
        },
    ]
    report = {
        "schema_version": "v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": "B5_REFINED_MASK_V1_OVERLAY_QA_REVISE_REEXTRACTION_OR_HUMAN_REVIEW_REQUIRED",
        "refined_mask_report": rel(REFINED_REPORT_JSON),
        "overlay_sheet": refined["overlay_sheet"],
        "contact_sheet": refined["contact_sheet"],
        "checks": checks,
        "focused_revise_parts": [
            "torso_base",
            "shoulder_L",
            "shoulder_R",
            "face_shadow_L",
            "face_shadow_R",
            "nose",
        ],
        "possible_review_parts": [
            "cheek_L",
            "cheek_R",
            "chest_cloth_shadow",
            "collar_shadow",
            "arm_L_upper_simple",
            "arm_R_upper_simple",
        ],
        "decision": "Keep B5 refined-mask v1 as useful intermediate evidence, not as material PASS. Continue automatic mask/extraction refinement for the focused revise parts before asking 주인님 for broad B5 approval.",
        "next_action": [
            "Run a smaller v2 refinement for torso/shoulders/face shadows/nose.",
            "Keep B4 hair focused review separate from B5 body/clothing mask refinement.",
            "Rebuild the combined B4/B5 corrected candidate only after B5 focused revise parts improve.",
        ],
        "self_review": {
            "refined_report_status": refined["status"],
            "refined_mask_count": refined["self_review"]["refined_mask_count"],
            "copied_from_auto_draft_count": refined["self_review"]["copied_from_auto_draft_count"],
            "has_revise_gate": True,
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
        "# Character 002 v22 B5 Refined Mask v1 Overlay QA",
        "",
        f"- status: `{report['status']}`",
        f"- refined mask report: `{report['refined_mask_report']}`",
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
            "## Focused Revise Parts",
            "",
            *[f"- `{part}`" for part in report["focused_revise_parts"]],
            "",
            "## Possible Review Parts",
            "",
            *[f"- `{part}`" for part in report["possible_review_parts"]],
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

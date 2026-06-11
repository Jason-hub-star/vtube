#!/usr/bin/env python3
"""Run conservative overlay QA for the v22 B5 body/clothing layer-pack candidate."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
LAYER_REPORT_JSON = EXP / "reports/v22_b5_body_clothing_pack/v22_b5_layer_pack_report.json"
REPORT_DIR = EXP / "reports/v22_b5_body_clothing_pack"
REPORT_JSON = REPORT_DIR / "v22_b5_overlay_qa_report.json"
REPORT_MD = REPORT_DIR / "v22_b5_overlay_qa_report.md"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def main() -> int:
    layer = json.loads(LAYER_REPORT_JSON.read_text(encoding="utf-8"))
    checks = [
        {
            "id": "technical_layer_pack",
            "status": "PASS_TECHNICAL",
            "evidence": "B5 layer pack generated 17/17 full-canvas 2048 RGBA candidates with no missing or empty outputs.",
        },
        {
            "id": "body_clothing_scope",
            "status": "PASS_CANDIDATE",
            "evidence": "Torso, neck, shoulders, arms, collar, chest cloth, brow, nose, cheek, and face-shadow outputs exist as candidate PNGs.",
        },
        {
            "id": "body_clothing_overlay_alignment",
            "status": "REVISE_ANCHOR_OR_EXTRACTION",
            "evidence": "Overlay sheet shows torso/neck/arm/clothing candidates are visually misaligned or overlaid too heavily on the source body, so they need anchor correction or refined extraction before material PASS.",
        },
        {
            "id": "face_detail_overlay_alignment",
            "status": "REVISE_ANCHOR_OR_EXTRACTION",
            "evidence": "Brow/nose/cheek/face-shadow candidates exist, but current automatic face-detail placement is too large or patch-like on the face.",
        },
        {
            "id": "breath_body_angle_gate",
            "status": "REVIEW_BLOCKED_UNTIL_ALIGNMENT",
            "evidence": "Breath/body-angle support cannot be judged until body/clothing anchors and crop assignments are visually corrected.",
        },
        {
            "id": "human_visual_review",
            "status": "REQUIRED",
            "evidence": "주인님 review is required after crop/anchor correction; technical PNG generation alone cannot approve B5 material.",
        },
    ]

    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_id": "cubism-v2-new-character-002-v22-b5-overlay-qa-001",
        "status": "B5_CODEX_OVERLAY_QA_REVISE_ANCHOR_OR_EXTRACTION_HUMAN_REVIEW_REQUIRED",
        "layer_pack_report": rel(LAYER_REPORT_JSON),
        "layer_pack_status": layer["status"],
        "contact_sheet": layer["contact_sheet"],
        "overlay_sheet": layer["overlay_sheet"],
        "checks": checks,
        "decision": "Do not promote B5 to material PASS. Keep the 17 RGBA body/clothing outputs as extraction candidates, but revise anchor placement/crop assignment before manifest promotion, Mini Cubism diagnostics, or real Cubism authoring.",
        "next_action": [
            "Use manual anchor correction or a refined extraction script for torso, neck, arms, clothing, and face-detail placement.",
            "Regenerate B5 only if crop refinement cannot make the parts read as source-matched body/clothing material.",
            "Keep B5 blocked from material PASS until overlay QA and 주인님 human review accept the corrected candidate.",
        ],
        "self_review": {
            "b5_layer_pack_status": layer["status"],
            "b5_layer_self_review_status": layer["self_review"]["status"],
            "check_count": len(checks),
            "has_revise_gate": any(str(check["status"]).startswith("REVISE") for check in checks),
            "has_human_required_gate": any(check["status"] == "REQUIRED" for check in checks),
            "has_breath_body_angle_block": any(check["id"] == "breath_body_angle_gate" for check in checks),
            "status": "PASS",
        },
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Character 002 v22 B5 Overlay QA",
        "",
        f"- status: `{report['status']}`",
        f"- layer pack report: `{report['layer_pack_report']}`",
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

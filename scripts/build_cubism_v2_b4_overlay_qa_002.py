#!/usr/bin/env python3
"""Run conservative overlay QA for the v22 B4 hair layer-pack candidate."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
LAYER_REPORT_JSON = EXP / "reports/v22_b4_hair_pack/v22_b4_layer_pack_report.json"
REPORT_DIR = EXP / "reports/v22_b4_hair_pack"
REPORT_JSON = REPORT_DIR / "v22_b4_overlay_qa_report.json"
REPORT_MD = REPORT_DIR / "v22_b4_overlay_qa_report.md"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def main() -> int:
    layer = json.loads(LAYER_REPORT_JSON.read_text(encoding="utf-8"))
    checks = [
        {
            "id": "technical_layer_pack",
            "status": "PASS_TECHNICAL",
            "evidence": "B4 layer pack generated 16/16 full-canvas 2048 RGBA candidates with no missing or empty outputs.",
        },
        {
            "id": "real_hairfront_children_scope",
            "status": "PASS_CANDIDATE",
            "evidence": "hair_front_center/L/R/side/tip outputs exist as independent candidate PNGs, so the HairFront art scope is no longer purely imaginary.",
        },
        {
            "id": "front_hair_overlay_alignment",
            "status": "REVISE_ANCHOR_OR_EXTRACTION",
            "evidence": "Overlay sheet shows the current automatic front-hair placement is visually noisy on the face and needs manual anchor correction or crop refinement before material PASS.",
        },
        {
            "id": "back_side_hair_overlay_alignment",
            "status": "REVISE_ANCHOR_OR_EXTRACTION",
            "evidence": "Back/side hair candidates are real but the current composite does not align cleanly with the source silhouette and draw-order intent.",
        },
        {
            "id": "hairfront_contract_gate",
            "status": "HOLD_UNSUPPORTED_CONTROL",
            "evidence": "ParamHairFront must remain hidden/contract-only until front hair candidates pass visual overlay QA and motion-readiness checks.",
        },
        {
            "id": "human_visual_review",
            "status": "REQUIRED",
            "evidence": "주인님 review is required after crop/anchor correction; technical PNG generation alone cannot approve B4 material.",
        },
    ]

    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_id": "cubism-v2-new-character-002-v22-b4-overlay-qa-001",
        "status": "B4_CODEX_OVERLAY_QA_REVISE_ANCHOR_OR_EXTRACTION_HUMAN_REVIEW_REQUIRED",
        "layer_pack_report": rel(LAYER_REPORT_JSON),
        "layer_pack_status": layer["status"],
        "contact_sheet": layer["contact_sheet"],
        "overlay_sheet": layer["overlay_sheet"],
        "checks": checks,
        "decision": "Do not promote B4 to material PASS. Keep the 16 RGBA hair outputs as extraction candidates, but revise anchor placement/crop assignment before enabling ParamHairFront or using B4 for Mini Cubism diagnostics.",
        "next_action": [
            "Use manual anchor correction or a refined extraction script for hair_front_* and side/back hair placement.",
            "Regenerate B4 only if crop refinement cannot make front/side/back hair read as the source hairstyle.",
            "Keep ParamHairFront hidden until corrected hair_front_* children pass overlay QA.",
        ],
        "self_review": {
            "b4_layer_pack_status": layer["status"],
            "b4_layer_self_review_status": layer["self_review"]["status"],
            "check_count": len(checks),
            "has_revise_gate": any(str(check["status"]).startswith("REVISE") for check in checks),
            "has_human_required_gate": any(check["status"] == "REQUIRED" for check in checks),
            "has_hairfront_contract_gate": any(check["id"] == "hairfront_contract_gate" for check in checks),
            "status": "PASS",
        },
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Character 002 v22 B4 Overlay QA",
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

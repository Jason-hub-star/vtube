#!/usr/bin/env python3
"""Record Codex visual QA for the v22 B1 clean-base layer pack.

This is a first-pass visual QA based on the generated contact sheet and overlay
sheet. It does not replace 주인님 human review and does not promote B1 to final
material PASS.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
REPORT_DIR = EXP / "reports/v22_b1_clean_base_underpaint"
LAYER_PACK_REPORT = REPORT_DIR / "v22_b1_layer_pack_report.json"
VISUAL_QA_JSON = REPORT_DIR / "v22_b1_visual_qa_report.json"
VISUAL_QA_MD = REPORT_DIR / "v22_b1_visual_qa_report.md"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def main() -> int:
    layer_pack = json.loads(LAYER_PACK_REPORT.read_text(encoding="utf-8"))
    checks = [
        {
            "id": "clean_face_no_eye_mouth_residue",
            "status": "PASS_CANDIDATE",
            "evidence": "Overlay sheet shows the raw B1 reference and face composite without open eyes, iris/pupil/white/lash detail, or mouth line.",
        },
        {
            "id": "no_oval_or_rectangular_patch_boundary",
            "status": "PASS_CANDIDATE",
            "evidence": "Eye and mouth areas read as soft continuous skin gradients on the B1 raw reference; no obvious oval mouth fill like the previous failed clean-base attempts.",
        },
        {
            "id": "b1_outputs_complete_and_nonempty",
            "status": "PASS_TECHNICAL",
            "evidence": "Layer pack self-review reports 11/11 expected outputs present, 0 missing, 0 empty, 2048 canvas.",
        },
        {
            "id": "mask_precision_for_final_material",
            "status": "REVISE_BEFORE_FINAL_MATERIAL_PASS",
            "evidence": "Automatic masks are coarse around face side hair, arms, body, and hair_back; acceptable as B1 candidate inputs, not final Cubism ArtMesh-ready masks.",
        },
        {
            "id": "human_visual_review",
            "status": "REQUIRED",
            "evidence": "주인님 human review is still required before promoting B1 from candidate to material PASS.",
        },
    ]
    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_id": "cubism-v2-new-character-002-v22-b1-visual-qa-001",
        "status": "B1_CODEX_VISUAL_QA_PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED",
        "layer_pack_report": rel(LAYER_PACK_REPORT),
        "contact_sheet": layer_pack["contact_sheet"],
        "overlay_sheet": layer_pack["overlay_sheet"],
        "checks": checks,
        "decision": "Keep the B1 layer pack as the current clean-base/underpaint candidate for follow-on B2/B3 prompt inputs, but do not promote it to final material PASS until human visual QA accepts it.",
        "next_action": [
            "Use B1 clean-base reference and layer pack to guide B2 eye pack generation.",
            "Keep B1 mask precision issues visible in contact-sheet QA; refine masks if they block overlay QA.",
            "Do not activate Mini Cubism diagnostic from this B1 pack alone.",
        ],
        "self_review": {
            "has_layer_pack_report": LAYER_PACK_REPORT.exists(),
            "has_contact_sheet": Path(layer_pack["contact_sheet"]).exists(),
            "has_overlay_sheet": Path(layer_pack["overlay_sheet"]).exists(),
            "check_count": len(checks),
            "has_human_required_gate": any(check["status"] == "REQUIRED" for check in checks),
            "status": "PASS",
        },
    }
    VISUAL_QA_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Character 002 v22 B1 Visual QA",
        "",
        f"- status: `{report['status']}`",
        f"- layer pack report: `{report['layer_pack_report']}`",
        f"- contact sheet: `{report['contact_sheet']}`",
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
    lines.append("")
    VISUAL_QA_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(VISUAL_QA_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

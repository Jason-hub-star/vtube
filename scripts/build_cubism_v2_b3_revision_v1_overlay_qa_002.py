#!/usr/bin/env python3
"""Record overlay QA for v22 B3 mouth extraction revision v1."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
REV_REPORT = EXP / "reports/v22_b3_mouth_pack_revision_v1/v22_b3_revision_v1_layer_pack_report.json"
PREV_OVERLAY = EXP / "reports/v22_b3_mouth_pack/v22_b3_overlay_qa_report.json"
REPORT_DIR = EXP / "reports/v22_b3_mouth_pack_revision_v1"
REPORT_JSON = REPORT_DIR / "v22_b3_revision_v1_overlay_qa_report.json"
REPORT_MD = REPORT_DIR / "v22_b3_revision_v1_overlay_qa_report.md"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def main() -> int:
    rev = json.loads(REV_REPORT.read_text(encoding="utf-8"))
    prev = json.loads(PREV_OVERLAY.read_text(encoding="utf-8"))
    checks = [
        {
            "id": "previous_failure_preserved",
            "status": "PASS_RECORDED",
            "evidence": f"Previous B3 overlay remains recorded as {prev['status']}; revision v1 does not overwrite that failed evidence.",
        },
        {
            "id": "technical_layer_pack",
            "status": "PASS_TECHNICAL",
            "evidence": "Revision v1 layer-pack self-review reports 12/12 expected outputs, 0 missing, 0 empty, all RGBA 2048.",
        },
        {
            "id": "open_internals_overlay",
            "status": "PASS_CANDIDATE",
            "evidence": "Revision v1 derives mouth_inner, teeth, and tongue from the same coherent wide-mouth crop, removing the previous large rectangular skin patch and reducing the pasted-helper look.",
        },
        {
            "id": "mouth_anchor_and_scale",
            "status": "REVIEW_VISUALLY",
            "evidence": "The open-mouth candidate is coherent but still needs 주인님 review for mouth anchor, expression size, and fit against the source face.",
        },
        {
            "id": "wide_reference_restraint",
            "status": "REVIEW_VISUALLY",
            "evidence": "Wide-open reference remains subject to the v21/v13 MouthOpenY 0.85 restraint before material promotion.",
        },
        {
            "id": "human_visual_review",
            "status": "REQUIRED",
            "evidence": "주인님 human visual review is required before promoting B3 revision v1 beyond candidate.",
        },
    ]
    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_id": "cubism-v2-new-character-002-v22-b3-revision-v1-overlay-qa-001",
        "status": "B3_REVISION_V1_CODEX_OVERLAY_QA_PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED",
        "revision_layer_pack_report": rel(REV_REPORT),
        "previous_overlay_qa_report": rel(PREV_OVERLAY),
        "overlay_sheet": rev["overlay_sheet"],
        "checks": checks,
        "decision": "B3 revision v1 fixes the first extraction's obvious pasted-internals failure enough to continue as a candidate, but it is not final material PASS until 주인님 visual review accepts anchor, scale, and MouthOpenY restraint.",
        "next_action": [
            "Use B3 revision v1 as the current B3 candidate for human review or manual anchor correction.",
            "If 주인님 rejects mouth size/anchor or wide-open restraint, regenerate B3 or tune revision anchors without reusing v10/v12/v13 mouth PNGs.",
            "Do not proceed to Mini Cubism diagnostics from B3 until visual QA accepts the mouth candidate.",
        ],
        "self_review": {
            "revision_layer_pack_status": rev["status"],
            "revision_layer_self_review_status": rev["self_review"]["status"],
            "previous_overlay_status": prev["status"],
            "check_count": len(checks),
            "has_pass_candidate_gate": any(check["status"] == "PASS_CANDIDATE" for check in checks),
            "has_human_required_gate": any(check["status"] == "REQUIRED" for check in checks),
            "has_review_visually_gate": any(check["status"] == "REVIEW_VISUALLY" for check in checks),
            "status": "PASS",
        },
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Character 002 v22 B3 Revision v1 Overlay QA",
        "",
        f"- status: `{report['status']}`",
        f"- revision layer-pack report: `{report['revision_layer_pack_report']}`",
        f"- previous overlay QA: `{report['previous_overlay_qa_report']}`",
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
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

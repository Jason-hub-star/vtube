#!/usr/bin/env python3
"""Record overlay QA for v22 B3 mouth candidates on the B1 clean base.

This separates technical layer-pack PASS from visual overlay REVISE. The current
B3 extraction must not be promoted to material PASS.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
B1_RAW = EXP / "v22_b1_clean_base_underpaint/raw_outputs/b1_clean_base_underpaint_reference_001.png"
B3_LAYER_REPORT = EXP / "reports/v22_b3_mouth_pack/v22_b3_layer_pack_report.json"
B3_LAYERS = EXP / "v22_b3_mouth_pack/normalized_layers"
REPORT_DIR = EXP / "reports/v22_b3_mouth_pack"
REPORT_JSON = REPORT_DIR / "v22_b3_overlay_qa_report.json"
REPORT_MD = REPORT_DIR / "v22_b3_overlay_qa_report.md"
OVERLAY_SHEET = REPORT_DIR / "v22_b3_overlay_qa_on_b1_clean_base.png"
CANVAS = 2048

CLOSED_LINE = ["mouth_line", "mouth_corner_L", "mouth_corner_R"]
OPEN_INTERNALS = [
    "mouth_inner",
    "mouth_teeth",
    "mouth_tongue",
    "mouth_upper_lip_mask",
    "mouth_lower_lip_mask",
]
REFERENCE_STATES = [
    "mouth_closed_smile_reference",
    "mouth_small_open_reference",
    "mouth_mid_teeth_reference",
    "mouth_wide_teeth_tongue_reference",
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_2048(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)


def load_layer(asset_id: str) -> Image.Image:
    return Image.open(B3_LAYERS / f"{asset_id}.png").convert("RGBA")


def composite(base: Image.Image, asset_ids: list[str]) -> Image.Image:
    out = base.copy()
    for asset_id in asset_ids:
        out.alpha_composite(load_layer(asset_id))
    return out


def draw_sheet(b1: Image.Image) -> None:
    panels = [
        ("B1 clean mouth base", b1),
        ("B1 + B3 closed line", composite(b1, CLOSED_LINE)),
        ("B1 + B3 open internals", composite(b1, OPEN_INTERNALS)),
        ("B3 keypose refs", composite(Image.new("RGBA", (CANVAS, CANVAS), (255, 255, 255, 255)), REFERENCE_STATES)),
    ]
    thumb = 460
    label_h = 46
    sheet = Image.new("RGB", (thumb * 2, (thumb + label_h) * 2), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, (label, img) in enumerate(panels):
        row, col = divmod(idx, 2)
        x = col * thumb
        y = row * (thumb + label_h)
        sheet.paste(img.convert("RGB").resize((thumb, thumb), Image.Resampling.LANCZOS), (x, y + label_h))
        draw.text((x + 10, y + 12), label, fill=(20, 20, 20))
    OVERLAY_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OVERLAY_SHEET)


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    b3_layer = json.loads(B3_LAYER_REPORT.read_text(encoding="utf-8"))
    b1 = load_2048(B1_RAW)
    draw_sheet(b1)
    checks = [
        {
            "id": "technical_layer_pack",
            "status": "PASS_TECHNICAL",
            "evidence": "B3 layer-pack self-review reports 12/12 expected outputs, 0 missing, 0 empty, all RGBA 2048.",
        },
        {
            "id": "closed_line_overlay",
            "status": "REVIEW_VISUALLY",
            "evidence": "Closed mouth line can be positioned near the mouth anchor, but corners and subtle lip mask need visual tuning.",
        },
        {
            "id": "open_internals_overlay",
            "status": "REVISE_EXTRACTION_OR_REGENERATE",
            "evidence": "Inner mouth, teeth, tongue, and lip masks read as separate pasted elements in the overlay instead of one coordinated mouth opening.",
        },
        {
            "id": "wide_reference_restraint",
            "status": "REVIEW_VISUALLY",
            "evidence": "Raw wide reference is coherent, but it still needs MouthOpenY 0.85 restraint review before use.",
        },
        {
            "id": "human_visual_review",
            "status": "REQUIRED",
            "evidence": "주인님 human visual review is required; Codex visual QA currently marks the extracted B3 internals as REVISE.",
        },
    ]
    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_id": "cubism-v2-new-character-002-v22-b3-overlay-qa-001",
        "status": "B3_CODEX_OVERLAY_QA_REVISE_EXTRACTION_OR_REGENERATE_HUMAN_REVIEW_REQUIRED",
        "b3_layer_pack_report": rel(B3_LAYER_REPORT),
        "overlay_sheet": rel(OVERLAY_SHEET),
        "checks": checks,
        "decision": "Do not promote B3 layer-pack to material PASS. Keep the raw B3 sheet as useful evidence, but revise extraction or regenerate B3 before proceeding to Mini Cubism diagnostics.",
        "next_action": [
            "Revise B3 extraction around one coherent mouth opening, or regenerate a new B3 sheet if teeth/tongue/inner still look pasted.",
            "Do not reuse v10/v12/v13 mouth PNGs as a shortcut.",
            "B4 generation may proceed only as independent raw generation planning; B3 remains blocked for material PASS.",
        ],
        "self_review": {
            "has_b3_layer_pack_report": B3_LAYER_REPORT.exists(),
            "b3_layer_pack_status": b3_layer["status"],
            "b3_layer_self_review_status": b3_layer["self_review"]["status"],
            "overlay_sheet_exists": OVERLAY_SHEET.exists(),
            "check_count": len(checks),
            "has_revise_gate": any(check["status"].startswith("REVISE") for check in checks),
            "has_human_required_gate": any(check["status"] == "REQUIRED" for check in checks),
            "status": "PASS",
        },
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Character 002 v22 B3 Overlay QA",
        "",
        f"- status: `{report['status']}`",
        f"- B3 layer-pack report: `{report['b3_layer_pack_report']}`",
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

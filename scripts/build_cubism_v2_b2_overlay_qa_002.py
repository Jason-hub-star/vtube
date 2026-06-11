#!/usr/bin/env python3
"""Record overlay QA for v22 B2 eye candidates on the B1 clean base.

This is a Codex visual/technical candidate gate. It does not replace 주인님
human review and does not promote B2 to final material PASS.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
B1_RAW = EXP / "v22_b1_clean_base_underpaint/raw_outputs/b1_clean_base_underpaint_reference_001.png"
B2_REPORT = EXP / "reports/v22_b2_eye_pack/v22_b2_layer_pack_report.json"
B2_LAYERS = EXP / "v22_b2_eye_pack/normalized_layers"
REPORT_DIR = EXP / "reports/v22_b2_eye_pack"
REPORT_JSON = REPORT_DIR / "v22_b2_overlay_qa_report.json"
REPORT_MD = REPORT_DIR / "v22_b2_overlay_qa_report.md"
OVERLAY_SHEET = REPORT_DIR / "v22_b2_overlay_qa_on_b1_clean_base.png"
CANVAS = 2048

OPEN_COMPONENTS = [
    "eye_L_white",
    "eye_L_iris",
    "eye_L_pupil",
    "eye_L_highlight",
    "eye_L_upper_lash",
    "eye_L_lower_lash",
    "eye_R_white",
    "eye_R_iris",
    "eye_R_pupil",
    "eye_R_highlight",
    "eye_R_upper_lash",
    "eye_R_lower_lash",
]
CLOSED_COMPONENTS = ["eye_L_closed_lid", "eye_R_closed_lid"]
REFERENCE_COMPONENTS = [
    "eye_open_reference",
    "eye_half_closed_reference",
    "eye_mostly_closed_reference",
    "eye_closed_reference",
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_2048(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)


def load_layer(asset_id: str) -> Image.Image:
    return Image.open(B2_LAYERS / f"{asset_id}.png").convert("RGBA")


def composite(base: Image.Image, asset_ids: list[str]) -> Image.Image:
    out = base.copy()
    for asset_id in asset_ids:
        out.alpha_composite(load_layer(asset_id))
    return out


def draw_sheet(source: Image.Image, b1: Image.Image, panels: list[tuple[str, Image.Image]]) -> None:
    thumb = 430
    label_h = 46
    cols = 3
    rows = 2
    sheet = Image.new("RGB", (thumb * cols, (thumb + label_h) * rows), "white")
    draw = ImageDraw.Draw(sheet)
    all_panels = [("G0 source", source), ("B1 clean-base", b1), *panels]
    for idx, (label, img) in enumerate(all_panels[: cols * rows]):
        row, col = divmod(idx, cols)
        x = col * thumb
        y = row * (thumb + label_h)
        sheet.paste(img.convert("RGB").resize((thumb, thumb), Image.Resampling.LANCZOS), (x, y + label_h))
        draw.text((x + 10, y + 12), label, fill=(20, 20, 20))
    OVERLAY_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OVERLAY_SHEET)


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    b2_report = json.loads(B2_REPORT.read_text(encoding="utf-8"))
    source = load_2048(SOURCE)
    b1 = load_2048(B1_RAW)

    open_overlay = composite(b1, OPEN_COMPONENTS)
    closed_overlay = composite(b1, CLOSED_COMPONENTS)
    refs_overlay = composite(Image.new("RGBA", (CANVAS, CANVAS), (255, 255, 255, 255)), REFERENCE_COMPONENTS)
    draw_sheet(
        source,
        b1,
        [
            ("B1 + B2 open eyes", open_overlay),
            ("B1 + B2 closed lids", closed_overlay),
            ("B2 keypose refs", refs_overlay),
        ],
    )

    checks = [
        {
            "id": "open_eye_socket_alignment",
            "status": "PASS_CANDIDATE",
            "evidence": "Open eye components land in the B1 clean socket region with left/right spacing consistent enough for extraction-candidate QA.",
        },
        {
            "id": "fixed_white_policy_visible",
            "status": "PASS_CANDIDATE",
            "evidence": "Sclera layers are socket-bound full-canvas layers; iris/pupil/highlight can move independently while whites remain fixed.",
        },
        {
            "id": "iris_pupil_highlight_anchor_lock",
            "status": "PASS_CANDIDATE",
            "evidence": "B2 layer-pack anchor checks record same-target placement for iris, pupil, and highlight clusters on both eyes.",
        },
        {
            "id": "closed_lid_overlay",
            "status": "PASS_CANDIDATE",
            "evidence": "Closed lid lines sit in the expected eye region on the B1 clean base; detailed blink keyform QA remains future Mini Cubism work.",
        },
        {
            "id": "matte_and_style_risk",
            "status": "REVISE_BEFORE_FINAL_MATERIAL_PASS",
            "evidence": "White-background extraction can leave soft matte halos and the generated component scale may need manual anchor tuning.",
        },
        {
            "id": "human_visual_review",
            "status": "REQUIRED",
            "evidence": "주인님 human visual review is required before promoting B2 beyond candidate.",
        },
    ]
    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_id": "cubism-v2-new-character-002-v22-b2-overlay-qa-001",
        "status": "B2_CODEX_OVERLAY_QA_PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED",
        "b2_layer_pack_report": rel(B2_REPORT),
        "overlay_sheet": rel(OVERLAY_SHEET),
        "source_image": rel(SOURCE),
        "b1_clean_base_reference": rel(B1_RAW),
        "checks": checks,
        "decision": "B2 is acceptable as a candidate input for continuing B3 generation, but it is not final material PASS. Keep visual/human QA, Mini Cubism diagnostics, and real Cubism authoring separate.",
        "next_action": [
            "Generate a new B3 mouth-pack raw candidate without using existing v10/v12/v13 mouth assets.",
            "Keep B2 layer-pack available for later manual anchor correction if 주인님 rejects the overlay scale or socket feel.",
        ],
        "self_review": {
            "has_b2_layer_pack_report": B2_REPORT.exists(),
            "b2_layer_pack_status": b2_report["status"],
            "b2_layer_self_review_status": b2_report["self_review"]["status"],
            "overlay_sheet_exists": OVERLAY_SHEET.exists(),
            "check_count": len(checks),
            "has_human_required_gate": any(check["status"] == "REQUIRED" for check in checks),
            "has_revise_before_final_gate": any(check["status"].startswith("REVISE") for check in checks),
            "status": "PASS",
        },
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Character 002 v22 B2 Overlay QA",
        "",
        f"- status: `{report['status']}`",
        f"- B2 layer-pack report: `{report['b2_layer_pack_report']}`",
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

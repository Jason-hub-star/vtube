#!/usr/bin/env python3
"""Review the v22 B3 newly generated mouth-pack raw candidate.

This records a new B3 mouth sheet generated without reusing previous v10/v11/v12
or model_edit mouth assets. The sheet is raw reference evidence only.
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
B3_RAW = EXP / "v22_b3_mouth_pack/raw_outputs/b3_mouth_pack_reference_001.png"
REPORT_DIR = EXP / "reports/v22_b3_mouth_pack"
REPORT_JSON = REPORT_DIR / "v22_b3_mouth_pack_review.json"
REPORT_MD = REPORT_DIR / "v22_b3_mouth_pack_review.md"
CONTACT_SHEET = REPORT_DIR / "v22_b3_mouth_pack_contact_sheet.png"

BUILT_IN_SOURCE = Path(
    "/Users/family/.codex/generated_images/019eabbe-60d9-79b2-ae99-4e869fb2525a/"
    "ig_0778ebb58b495b6b016a2804f3622c8191886e404dc8c47e77.png"
)

FORBIDDEN_EXISTING_MOUTH_ASSETS = [
    EXP / "generated_mouth_v10",
    EXP / "generated_mouth_v11",
    EXP / "generated_mouth_v12",
    EXP / "model_edit_v4_mouth_alpha",
    EXP / "model_edit_v4_strict_mouth",
    EXP / "model_edit_v7_smooth_mouth_preview",
    EXP / "model_edit_v8_existing_mouth_tuned_preview",
    EXP / "model_edit_v9_all_mouth_enabled_preview",
    EXP / "model_edit_v10_generated_mouth_eye_clamp_preview",
    EXP / "model_edit_v11_generated_mouth_eye_clamp_preview",
    EXP / "model_edit_v12_generated_mouth_eye_clamp_preview",
    EXP / "model_edit_v13_scaled_eye_mouth_preview",
]

PROMPT = """Use case: stylized-concept
Asset type: Live2D/Cubism v22 B3 mouth-pack reference sheet for character material generation.
Input images in conversation: the original front/source character is the identity/style reference; the clean-base underpaint image is the face/mouth socket placement reference. Do not copy, reuse, trace, or imitate any previous generated mouth assets from v10/v11/v12/v13 or any model_edit mouth preview; this must be a newly drawn B3 mouth pack.
Primary request: Create a clean, production-oriented anime mouth asset sheet for the same adult-cute female VTuber character. Match the source character's tiny gentle smile anchor, soft pink lip color, delicate linework, pale skin tone, and subtle blush style. The mouth should sit naturally at the same mouth anchor as the source, with consistent left/right corners across all expressions.
Sheet contents: closed gentle smile, small open smile, mid open smile with natural upper/lower teeth, and proportion-limited wide smile-open with teeth and tongue. Also include separate component references: mouth line, inner mouth shape, upper lip mask, lower lip mask, teeth, tongue, left mouth corner, right mouth corner. The internals must read as one coordinated mouth packet, not pasted helper overlays.
Rigging requirements: all mouth states share the same center anchor and corner alignment; wide open must stay cute and restrained, not oversized, circular, or horror-wide; MouthOpenY visual maximum should feel like 0.85, not exaggerated 1.0; teeth and tongue follow the mouth opening shape; no tiny centered O-vowel; no separate floating teeth/tongue; no mouth labels.
Layout: single square reference sheet, clean white or very light neutral background, generous spacing, organized rows, no text, no labels, no arrows, no grids, no watermarks. Keep components isolated enough for later extraction, with crisp edges and minimal overlap.
Style: polished 2D anime VTuber concept art, same soft semi-clean shading as the source, thin warm brown mouth line, natural soft pink lips, tasteful teeth/tongue details, subtle skin-toned lip shadows."""


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def rel_or_abs(path: Path) -> str:
    try:
        return rel(path)
    except ValueError:
        return str(path.resolve())


def load_rgb(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def draw_contact_sheet(source: Image.Image, b1: Image.Image, b3: Image.Image) -> None:
    width, height = source.size
    scale = 0.34
    thumb = (int(width * scale), int(height * scale))
    margin = 24
    label_h = 34
    sheet = Image.new("RGB", (thumb[0] * 3 + margin * 4, thumb[1] + margin * 2 + label_h), "white")
    draw = ImageDraw.Draw(sheet)
    panels = [
        ("G0 source/style", source.resize(thumb, Image.Resampling.LANCZOS)),
        ("B1 clean mouth base", b1.resize(thumb, Image.Resampling.LANCZOS)),
        ("B3 new mouth-pack raw", b3.resize(thumb, Image.Resampling.LANCZOS)),
    ]
    for idx, (label, image) in enumerate(panels):
        x = margin + idx * (thumb[0] + margin)
        y = margin + label_h
        draw.text((x, margin), label, fill=(20, 20, 20))
        sheet.paste(image, (x, y))
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET)


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    source = load_rgb(SOURCE)
    b1 = load_rgb(B1_RAW)
    b3 = load_rgb(B3_RAW)
    draw_contact_sheet(source, b1, b3)

    visual_checks = [
        {
            "id": "new_generation_no_existing_mouth_asset_reuse",
            "status": "PASS_RECORDED",
            "evidence": "B3 raw sheet was generated via built-in imagegen after the no-existing-assets rule; prior generated/model_edit mouth folders are recorded as forbidden inputs.",
        },
        {
            "id": "same_character_mouth_style",
            "status": "PASS_CANDIDATE",
            "evidence": "The sheet keeps the source character's soft pink mouth style, subtle highlights, and adult-cute expression language.",
        },
        {
            "id": "mouthopen_keypose_rows",
            "status": "PASS_CANDIDATE",
            "evidence": "Closed, small-open, mid-open, and wide-open reference states are visibly present.",
        },
        {
            "id": "coordinated_internals",
            "status": "PASS_CANDIDATE",
            "evidence": "The visible open-mouth states draw inner mouth, teeth, and tongue as a coherent mouth packet instead of isolated helper overlays.",
        },
        {
            "id": "wide_mouth_limit",
            "status": "REVIEW_VISUALLY",
            "evidence": "The wide-open reference is expressive and coherent, but must be reviewed against the v21/v13 MouthOpenY max 0.85 restraint before promotion.",
        },
        {
            "id": "extraction_readiness",
            "status": "REVISE_BEFORE_LAYER_PROMOTION",
            "evidence": "The sheet is RGB on a white background with face crops in the top rows, so it needs extraction/masking before full-canvas RGBA B3 material can be claimed.",
        },
        {
            "id": "human_visual_review",
            "status": "REQUIRED",
            "evidence": "주인님 must approve mouth style, anchor consistency, and wide-mouth restraint before B3 is promoted beyond raw candidate.",
        },
    ]

    allowed_inputs = [
        SOURCE,
        B1_RAW,
        EXP / "reports/v22_64part_generation_input_packet/v22_64part_generation_input_packet.json",
        EXP / "reports/v22_b1_clean_base_underpaint/v22_b1_visual_qa_report.json",
        EXP / "reports/v22_b2_eye_pack/v22_b2_overlay_qa_report.json",
    ]
    forbidden = [
        {
            "path": rel_or_abs(path),
            "exists": path.exists(),
            "status": "FORBIDDEN_AS_B3_INPUT",
        }
        for path in FORBIDDEN_EXISTING_MOUTH_ASSETS
    ]

    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "review_id": "cubism-v2-new-character-002-v22-b3-mouth-pack-review-001",
        "status": "B3_RAW_MOUTH_PACK_CANDIDATE_READY_FOR_EXTRACTION_HUMAN_REVIEW_REQUIRED",
        "source_image": rel(SOURCE),
        "b1_clean_base_reference": rel(B1_RAW),
        "b3_raw_image": rel(B3_RAW),
        "built_in_imagegen_source": rel_or_abs(BUILT_IN_SOURCE),
        "contact_sheet": rel(CONTACT_SHEET),
        "imagegen_mode": "built_in_image_gen",
        "image_generation": "RUN_ON_2026_06_09",
        "prompt": PROMPT,
        "allowed_inputs": [rel(path) for path in allowed_inputs],
        "forbidden_existing_mouth_assets": forbidden,
        "locked_success_criteria": [
            "Do not reuse v10/v11/v12/v13 generated or model_edit mouth PNGs for B3 material.",
            "Closed, small, mid, and wide references share one mouth anchor and corner alignment.",
            "Mouth internals are generated as one coordinated packet, not pasted helper overlays.",
            "MouthOpenY visual max follows the v21/v13 restraint around 0.85.",
            "Do not promote this raw sheet to final material without RGBA extraction, overlay QA, and human visual review.",
        ],
        "visual_checks": visual_checks,
        "decision": "Keep this as the v22 B3 newly generated mouth-pack raw candidate. It can feed B3 extraction planning, but it is not yet separated full-canvas RGBA mouth material and does not unlock Mini Cubism or real Cubism success claims.",
        "next_action": [
            "Extract/normalize B3 components into full-canvas RGBA candidates: mouth_line, inner, lip masks, teeth, tongue, corners, and four MouthOpenY reference states.",
            "Run B3 contact-sheet and overlay QA against the G0 source and B1 clean mouth base.",
            "If wide mouth is too large or internals look pasted after extraction, regenerate B3 instead of reusing old v10/v12/v13 mouth assets.",
        ],
        "self_review": {
            "source_exists": SOURCE.exists(),
            "b1_raw_exists": B1_RAW.exists(),
            "b3_raw_exists": B3_RAW.exists(),
            "built_in_imagegen_source_exists": BUILT_IN_SOURCE.exists(),
            "source_size": source.size,
            "b1_raw_size": b1.size,
            "b3_raw_size": b3.size,
            "b3_mode": b3.mode,
            "allowed_input_count": len(allowed_inputs),
            "forbidden_existing_mouth_asset_count": len(forbidden),
            "visual_check_count": len(visual_checks),
            "has_human_required_gate": any(check["status"] == "REQUIRED" for check in visual_checks),
            "has_wide_mouth_review_gate": any(check["id"] == "wide_mouth_limit" for check in visual_checks),
            "forbidden_assets_not_output_path": all(path.resolve() != B3_RAW.resolve() for path in FORBIDDEN_EXISTING_MOUTH_ASSETS),
            "status": "PASS",
        },
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Character 002 v22 B3 Mouth Pack Review",
        "",
        f"- status: `{report['status']}`",
        f"- source image: `{report['source_image']}`",
        f"- B1 clean-base reference: `{report['b1_clean_base_reference']}`",
        f"- B3 raw image: `{report['b3_raw_image']}`",
        f"- contact sheet: `{report['contact_sheet']}`",
        f"- imagegen mode: `{report['imagegen_mode']}`",
        "",
        "## Allowed Inputs",
        "",
        *[f"- `{item}`" for item in report["allowed_inputs"]],
        "",
        "## Forbidden Existing Mouth Assets",
        "",
    ]
    for item in forbidden:
        lines.append(f"- `{item['status']}` `{item['path']}` exists `{item['exists']}`")
    lines.extend(["", "## Visual Checks", ""])
    for check in visual_checks:
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

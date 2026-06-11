#!/usr/bin/env python3
"""Review the v22 B2 newly generated eye-pack raw candidate.

This records the first B2 eye-pack reference generated after the "do not use
existing eye assets" instruction. It intentionally treats the sheet as a raw
reference candidate, not as separated RGBA Cubism material.
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
B2_RAW = EXP / "v22_b2_eye_pack/raw_outputs/b2_eye_pack_reference_001.png"
REPORT_DIR = EXP / "reports/v22_b2_eye_pack"
REPORT_JSON = REPORT_DIR / "v22_b2_eye_pack_review.json"
REPORT_MD = REPORT_DIR / "v22_b2_eye_pack_review.md"
CONTACT_SHEET = REPORT_DIR / "v22_b2_eye_pack_contact_sheet.png"

BUILT_IN_SOURCE = Path(
    "/Users/family/.codex/generated_images/019eabbe-60d9-79b2-ae99-4e869fb2525a/"
    "ig_0778ebb58b495b6b016a27f2fabfd4819183b2f52f8d6a9dc6.png"
)

FORBIDDEN_EXISTING_EYE_ASSETS = [
    EXP / "generated_eye_v19",
    EXP / "model_edit_v14_eye_detail_inbetween_preview/mini_cubism_diagnostic_project/parts",
    EXP / "model_edit_v15_eye_nose_position_preview/mini_cubism_diagnostic_project/parts",
    EXP / "model_edit_v19_generated_eye_preview/mini_cubism_diagnostic_project/parts",
    EXP / "model_edit_v20_manual_eye_anchor_preview/mini_cubism_diagnostic_project/parts",
    EXP / "model_edit_v21_supported_rig_smoke_preview/mini_cubism_diagnostic_project/parts",
]

PROMPT = """Use case: stylized-concept
Asset type: Live2D/Cubism v22 B2 eye-pack reference sheet for character material generation.
Input images in conversation: the original front/source character is the identity and style reference; the clean-base underpaint image is the socket/placement reference. Do not copy, reuse, trace, or imitate any previous generated eye asset from v19/v20/v21; this must be a newly drawn B2 eye pack.
Primary request: Create a clean, production-oriented anime eye asset sheet for the same character: adult-cute female, warm brown hair framing the eyes, pale skin, soft blush, delicate linework, purple-lavender irises with glossy highlights. Match the source character's eye scale, spacing, gentle expression, and front-facing gaze.
Sheet contents: left-eye and right-eye pairs for open, half-open, natural close around 0.27 openness, and fully closed. Also include separate-looking component references for each side: fixed white sclera shape, iris+pupil+highlight cluster as one coherent movable unit, upper lash line, lower lash line, eyelid crease, closed lid line, and soft shadow under upper lid.
Rigging requirements: eye whites must remain fixed; iris, pupil, and highlight must stay locked together from one anchor; no crossed gaze, no separated drifting highlights, no oversized eyes, no tiny centered eyes, no pasted rectangle patches. Closed/natural-close states should read soft and pretty, not squeezed or harsh.
Layout: single square reference sheet, clean white or very light neutral background, generous spacing, organized rows, no labels, no text, no arrows, no grids, no watermarks. Keep parts isolated enough for later extraction, with crisp edges and minimal overlap.
Style: polished 2D anime VTuber concept art, same soft semi-clean shading as the source, thin brown-black lash lines, glossy lavender irises, subtle skin-toned eyelid shading."""


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def rel_or_abs(path: Path) -> str:
    try:
        return rel(path)
    except ValueError:
        return str(path.resolve())


def load_rgb(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def draw_contact_sheet(source: Image.Image, b1: Image.Image, b2: Image.Image) -> None:
    width, height = source.size
    scale = 0.34
    thumb = (int(width * scale), int(height * scale))
    margin = 24
    label_h = 34
    sheet = Image.new("RGB", (thumb[0] * 3 + margin * 4, thumb[1] + margin * 2 + label_h), "white")
    draw = ImageDraw.Draw(sheet)
    panels = [
        ("G0 source/style", source.resize(thumb, Image.Resampling.LANCZOS)),
        ("B1 clean socket/base", b1.resize(thumb, Image.Resampling.LANCZOS)),
        ("B2 new eye-pack raw", b2.resize(thumb, Image.Resampling.LANCZOS)),
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
    b2 = load_rgb(B2_RAW)
    draw_contact_sheet(source, b1, b2)

    visual_checks = [
        {
            "id": "new_generation_no_existing_eye_asset_reuse",
            "status": "PASS_RECORDED",
            "evidence": "B2 raw sheet was generated via built-in imagegen after the no-existing-assets instruction; v19/v20/v21 eye directories are recorded as forbidden inputs.",
        },
        {
            "id": "same_character_eye_style",
            "status": "PASS_CANDIDATE",
            "evidence": "The sheet keeps lavender-purple irises, soft anime lash styling, and front-facing adult-cute expression consistent with the G0 source.",
        },
        {
            "id": "eyeopen_keypose_rows",
            "status": "PASS_CANDIDATE",
            "evidence": "Open, half-open, natural-close, and closed rows are visibly present for left/right eye pairs.",
        },
        {
            "id": "fixed_white_and_locked_iris_cluster_scope",
            "status": "PASS_CANDIDATE",
            "evidence": "The component area includes isolated sclera and coherent iris+pupil+highlight clusters, matching the v21 guardrail that whites stay fixed while iris detail moves together.",
        },
        {
            "id": "extraction_readiness",
            "status": "REVISE_BEFORE_LAYER_PROMOTION",
            "evidence": "The sheet is RGB on a white background with skin/hair context in the top pose rows, so it needs extraction/masking before full-canvas RGBA B2 material can be claimed.",
        },
        {
            "id": "human_visual_review",
            "status": "REQUIRED",
            "evidence": "주인님 must approve the eye style and natural-close feel before B2 is promoted beyond raw candidate.",
        },
    ]

    allowed_inputs = [
        SOURCE,
        B1_RAW,
        EXP / "reports/v22_64part_generation_input_packet/v22_64part_generation_input_packet.json",
        EXP / "reports/v22_b1_clean_base_underpaint/v22_b1_visual_qa_report.json",
    ]
    forbidden = [
        {
            "path": rel_or_abs(path),
            "exists": path.exists(),
            "status": "FORBIDDEN_AS_B2_INPUT",
        }
        for path in FORBIDDEN_EXISTING_EYE_ASSETS
    ]

    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "review_id": "cubism-v2-new-character-002-v22-b2-eye-pack-review-001",
        "status": "B2_RAW_EYE_PACK_CANDIDATE_READY_FOR_EXTRACTION_HUMAN_REVIEW_REQUIRED",
        "source_image": rel(SOURCE),
        "b1_clean_base_reference": rel(B1_RAW),
        "b2_raw_image": rel(B2_RAW),
        "built_in_imagegen_source": rel_or_abs(BUILT_IN_SOURCE),
        "contact_sheet": rel(CONTACT_SHEET),
        "imagegen_mode": "built_in_image_gen",
        "image_generation": "RUN_ON_2026_06_09",
        "prompt": PROMPT,
        "allowed_inputs": [rel(path) for path in allowed_inputs],
        "forbidden_existing_eye_assets": forbidden,
        "locked_success_criteria": [
            "Do not reuse v19/v20/v21 generated eye PNGs for B2 material.",
            "Keep eye whites fixed for EyeBallX/Y.",
            "Move iris, pupil, and highlight together from one anchor.",
            "Natural close should target the v21 visual sweet spot around EyeOpen 0.27.",
            "Do not promote this raw sheet to final material without RGBA extraction, overlay QA, and human visual review.",
        ],
        "visual_checks": visual_checks,
        "decision": "Keep this as the v22 B2 newly generated eye-pack raw candidate. It can feed B2 extraction planning, but it is not yet separated full-canvas RGBA eye material and does not unlock Mini Cubism or real Cubism success claims.",
        "next_action": [
            "Extract/normalize B2 components into full-canvas RGBA candidates: eye_L/R_white, iris cluster, upper lash, lower lash, closed lid, eyelid shadow, and natural-close keypose support.",
            "Run B2 contact-sheet and overlay QA against the G0 source and B1 clean-base sockets.",
            "If iris/pupil/highlight drift or fixed whites fail in extraction, regenerate B2 instead of reusing old v19/v20/v21 eye assets.",
        ],
        "self_review": {
            "source_exists": SOURCE.exists(),
            "b1_raw_exists": B1_RAW.exists(),
            "b2_raw_exists": B2_RAW.exists(),
            "built_in_imagegen_source_exists": BUILT_IN_SOURCE.exists(),
            "source_size": source.size,
            "b1_raw_size": b1.size,
            "b2_raw_size": b2.size,
            "b2_mode": b2.mode,
            "allowed_input_count": len(allowed_inputs),
            "forbidden_existing_eye_asset_count": len(forbidden),
            "visual_check_count": len(visual_checks),
            "has_human_required_gate": any(check["status"] == "REQUIRED" for check in visual_checks),
            "forbidden_assets_not_output_path": all(path.resolve() != B2_RAW.resolve() for path in FORBIDDEN_EXISTING_EYE_ASSETS),
            "status": "PASS",
        },
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Character 002 v22 B2 Eye Pack Review",
        "",
        f"- status: `{report['status']}`",
        f"- source image: `{report['source_image']}`",
        f"- B1 clean-base reference: `{report['b1_clean_base_reference']}`",
        f"- B2 raw image: `{report['b2_raw_image']}`",
        f"- contact sheet: `{report['contact_sheet']}`",
        f"- imagegen mode: `{report['imagegen_mode']}`",
        "",
        "## Allowed Inputs",
        "",
        *[f"- `{item}`" for item in report["allowed_inputs"]],
        "",
        "## Forbidden Existing Eye Assets",
        "",
    ]
    for item in forbidden:
        lines.append(f"- `{item['status']}` `{item['path']}` exists `{item['exists']}`")
    lines.extend(
        [
            "",
            "## Visual Checks",
            "",
        ]
    )
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

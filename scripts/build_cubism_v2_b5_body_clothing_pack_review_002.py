#!/usr/bin/env python3
"""Review the v22 B5 newly generated body/clothing-pack raw candidate.

This records a new B5 body/clothing sheet generated for later extraction into
full-canvas Cubism parts. It is raw reference evidence only, not separated RGBA
material or body-motion success.
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
B5_RAW = EXP / "v22_b5_body_clothing_pack/raw_outputs/b5_body_clothing_pack_reference_001.png"
REPORT_DIR = EXP / "reports/v22_b5_body_clothing_pack"
REPORT_JSON = REPORT_DIR / "v22_b5_body_clothing_pack_review.json"
REPORT_MD = REPORT_DIR / "v22_b5_body_clothing_pack_review.md"
CONTACT_SHEET = REPORT_DIR / "v22_b5_body_clothing_pack_contact_sheet.png"

BUILT_IN_SOURCE = Path(
    "/Users/family/.codex/generated_images/019eabbe-60d9-79b2-ae99-4e869fb2525a/"
    "ig_0acae21c1c26dfc8016a280deceaf8819187567ad354e33e72.png"
)

EXPECTED_B5_PARTS = [
    "torso_base",
    "neck",
    "shoulder_L",
    "shoulder_R",
    "arm_L_upper_simple",
    "arm_R_upper_simple",
    "collar_front",
    "collar_shadow",
    "chest_cloth_base",
    "chest_cloth_shadow",
    "brow_L",
    "brow_R",
    "nose",
    "cheek_L",
    "cheek_R",
    "face_shadow_L",
    "face_shadow_R",
]

FORBIDDEN_EXISTING_BODY_CLOTHING_ASSETS = [
    EXP / "material_pack_first_v0/normalized_layers",
    EXP / "model_edit_v13_scaled_eye_mouth_preview/mini_cubism_diagnostic_project/parts",
    EXP / "model_edit_v21_supported_rig_smoke_preview/mini_cubism_diagnostic_project/parts",
    ROOT / "experiments/cubism-v2-new-character-001/material_pack_v0/production_layers",
    ROOT / "experiments/cubism-v2-new-character-001/material_pack_v0/production_layers_roi_semantic_remask_v1",
]

PROMPT = """Use case: stylized-concept
Asset type: Live2D/Cubism v2_standard B5 body and clothing material reference sheet for character material generation.
Primary request: Create a clean anime Live2D / Cubism B5 body and clothing material reference sheet for the same character identity: adult cute woman, long warm brown hair, soft pale skin, white ribbed off-shoulder sweater with simple shoulder straps, front-facing neutral upper-body proportions. This is a new body/clothing parts sheet, not a crop of an existing image.
Sheet contents: 17 rig-friendly material candidates: torso base, neck, left shoulder, right shoulder, simple left upper arm, simple right upper arm, front collar edge, collar shadow, chest cloth base, chest cloth shadow, left brow, right brow, subtle nose detail, left cheek blush, right cheek blush, left face shadow, right face shadow.
Style and identity: keep the same outfit design, color palette, line thickness, soft anime shading, and upper-body composition as the accepted source character.
Rigging requirements: body and clothing parts should be cleanly separated, symmetrical where appropriate, simple for breath and body-angle motion, with enough underpaint/back-fill coverage to avoid visible holes. Nose and cheeks must stay subtle but visible as separate material references.
Negative prompt: no complex hands, no fingers, no large props, no jewelry, no new accessories, no hairstyle change, no labels, no typography, no guide arrows, no grids, no extra character, no side view, no extreme pose, no cropped shoulders, no perspective distortion, no source-image crop artifacts."""


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def rel_or_abs(path: Path) -> str:
    try:
        return rel(path)
    except ValueError:
        return str(path.resolve())


def load_rgb(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def draw_contact_sheet(source: Image.Image, b1: Image.Image, b5: Image.Image) -> None:
    source_thumb = source.resize((330, 330), Image.Resampling.LANCZOS)
    b1_thumb = b1.resize((330, 330), Image.Resampling.LANCZOS)
    b5_thumb = b5.resize((495, 330), Image.Resampling.LANCZOS)
    margin = 24
    label_h = 34
    width = margin * 4 + source_thumb.width + b1_thumb.width + b5_thumb.width
    height = margin * 2 + label_h + 330
    sheet = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(sheet)
    panels = [
        ("G0 source/style", source_thumb),
        ("B1 clean base", b1_thumb),
        ("B5 body/clothing raw", b5_thumb),
    ]
    x = margin
    for label, image in panels:
        draw.text((x, margin), label, fill=(20, 20, 20))
        sheet.paste(image, (x, margin + label_h))
        x += image.width + margin
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET)


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    source = load_rgb(SOURCE)
    b1 = load_rgb(B1_RAW)
    b5 = load_rgb(B5_RAW)
    draw_contact_sheet(source, b1, b5)

    visual_checks = [
        {
            "id": "new_generation_no_existing_body_clothing_asset_reuse",
            "status": "PASS_RECORDED",
            "evidence": "B5 raw sheet was generated via built-in imagegen after the no-existing-assets instruction; prior normalized/model_edit/body-clothing material folders are recorded as forbidden inputs.",
        },
        {
            "id": "same_character_outfit_style",
            "status": "PASS_CANDIDATE",
            "evidence": "The sheet keeps the white ribbed off-shoulder sweater, shoulder straps, soft skin shading, and simple upper-body design from the source.",
        },
        {
            "id": "body_clothing_scope_visible",
            "status": "PASS_CANDIDATE",
            "evidence": "Torso, neck, shoulders, simple sleeves/upper arms, collar, chest cloth, and cloth shadow candidates are visibly present.",
        },
        {
            "id": "face_detail_scope_visible",
            "status": "PASS_CANDIDATE",
            "evidence": "Left/right brows, subtle nose, cheek blush, and side face-shadow candidates are present as separate material references.",
        },
        {
            "id": "breath_body_angle_support",
            "status": "REVIEW_VISUALLY",
            "evidence": "The body/clothing pieces include underpaint-like coverage, but extraction/overlay QA must confirm breath and body-angle motion will not expose holes.",
        },
        {
            "id": "extraction_readiness",
            "status": "REVISE_BEFORE_LAYER_PROMOTION",
            "evidence": "The sheet is RGB on a light background and includes a full torso context pose; it must be extracted/masked before full-canvas RGBA B5 material can be claimed.",
        },
        {
            "id": "human_visual_review",
            "status": "REQUIRED",
            "evidence": "주인님 must approve outfit identity, body proportions, face-detail subtlety, and body/clothing readability before B5 is promoted beyond raw candidate.",
        },
    ]

    allowed_inputs = [
        SOURCE,
        B1_RAW,
        EXP / "reports/v22_64part_generation_spec/v22_64part_generation_spec.json",
        EXP / "reports/v22_64part_generation_input_packet/v22_64part_generation_input_packet.json",
        EXP / "reports/v22_b1_clean_base_underpaint/v22_b1_visual_qa_report.json",
    ]
    forbidden = [
        {
            "path": rel_or_abs(path),
            "exists": path.exists(),
            "status": "FORBIDDEN_AS_B5_INPUT",
        }
        for path in FORBIDDEN_EXISTING_BODY_CLOTHING_ASSETS
    ]

    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "review_id": "cubism-v2-new-character-002-v22-b5-body-clothing-pack-review-001",
        "status": "B5_RAW_BODY_CLOTHING_PACK_CANDIDATE_READY_FOR_EXTRACTION_HUMAN_REVIEW_REQUIRED",
        "source_image": rel(SOURCE),
        "b1_clean_base_reference": rel(B1_RAW),
        "b5_raw_image": rel(B5_RAW),
        "built_in_imagegen_source": rel_or_abs(BUILT_IN_SOURCE),
        "contact_sheet": rel(CONTACT_SHEET),
        "imagegen_mode": "built_in_image_gen",
        "image_generation": "RUN_ON_2026_06_09",
        "prompt": PROMPT,
        "expected_b5_parts": EXPECTED_B5_PARTS,
        "allowed_inputs": [rel(path) for path in allowed_inputs],
        "forbidden_existing_body_clothing_assets": forbidden,
        "locked_success_criteria": [
            "Do not reuse prior normalized/model_edit/body-clothing PNGs for B5 material.",
            "Do not rely on the source lower-body crop alone; B5 must provide complete torso, neck, shoulder, arm, clothing, and face-detail references.",
            "Body and clothing parts must support breath/body-angle motion without visible holes after extraction.",
            "Nose, cheeks, brows, and face shadows must remain subtle but visible as separate material references.",
            "Do not promote this raw sheet to final material without RGBA extraction, overlay QA, and human visual review.",
        ],
        "visual_checks": visual_checks,
        "decision": "Keep this as the v22 B5 newly generated body/clothing-pack raw candidate. It can feed B5 extraction planning, but it is not yet separated full-canvas RGBA material and does not prove body-motion or real Cubism success.",
        "next_action": [
            "Extract/normalize B5 components into full-canvas RGBA candidates for the 17 expected body, clothing, brow, nose, cheek, and face-shadow parts.",
            "Run B5 contact-sheet and overlay QA against the G0 source and B1 clean-base silhouette.",
            "Only after B1-B5 visual QA acceptance, build the 64-part manifest and continue to G1-G5 material QA.",
        ],
        "self_review": {
            "source_exists": SOURCE.exists(),
            "b1_raw_exists": B1_RAW.exists(),
            "b5_raw_exists": B5_RAW.exists(),
            "built_in_imagegen_source_exists": BUILT_IN_SOURCE.exists(),
            "source_size": list(source.size),
            "b1_raw_size": list(b1.size),
            "b5_raw_size": list(b5.size),
            "b5_mode": b5.mode,
            "expected_b5_part_count": len(EXPECTED_B5_PARTS),
            "allowed_input_count": len(allowed_inputs),
            "forbidden_existing_body_clothing_asset_count": len(forbidden),
            "visual_check_count": len(visual_checks),
            "has_human_required_gate": any(check["status"] == "REQUIRED" for check in visual_checks),
            "has_breath_body_angle_review_gate": any(check["id"] == "breath_body_angle_support" for check in visual_checks),
            "has_face_detail_scope": all(part in EXPECTED_B5_PARTS for part in ["brow_L", "brow_R", "nose", "cheek_L", "cheek_R", "face_shadow_L", "face_shadow_R"]),
            "forbidden_assets_not_output_path": all(path.resolve() != B5_RAW.resolve() for path in FORBIDDEN_EXISTING_BODY_CLOTHING_ASSETS),
            "status": "PASS",
        },
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Character 002 v22 B5 Body/Clothing Pack Review",
        "",
        f"- status: `{report['status']}`",
        f"- source image: `{report['source_image']}`",
        f"- B1 clean-base reference: `{report['b1_clean_base_reference']}`",
        f"- B5 raw image: `{report['b5_raw_image']}`",
        f"- contact sheet: `{report['contact_sheet']}`",
        f"- imagegen mode: `{report['imagegen_mode']}`",
        "",
        "## Expected B5 Parts",
        "",
        *[f"- `{item}`" for item in EXPECTED_B5_PARTS],
        "",
        "## Allowed Inputs",
        "",
        *[f"- `{item}`" for item in report["allowed_inputs"]],
        "",
        "## Forbidden Existing Body/Clothing Assets",
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
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": report["status"], "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

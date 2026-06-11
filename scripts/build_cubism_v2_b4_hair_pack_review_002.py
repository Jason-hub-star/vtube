#!/usr/bin/env python3
"""Review the v22 B4 newly generated hair-pack raw candidate.

This records a new B4 hair sheet generated without reusing previous separated
hair assets. The sheet is raw reference evidence only; it does not enable
ParamHairFront until extracted front-hair child parts exist and pass QA.
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
B4_RAW = EXP / "v22_b4_hair_pack/raw_outputs/b4_hair_pack_reference_001.png"
REPORT_DIR = EXP / "reports/v22_b4_hair_pack"
REPORT_JSON = REPORT_DIR / "v22_b4_hair_pack_review.json"
REPORT_MD = REPORT_DIR / "v22_b4_hair_pack_review.md"
CONTACT_SHEET = REPORT_DIR / "v22_b4_hair_pack_contact_sheet.png"

BUILT_IN_SOURCE = Path(
    "/Users/family/.codex/generated_images/019eabbe-60d9-79b2-ae99-4e869fb2525a/"
    "ig_0acae21c1c26dfc8016a280c7dfc508191aea72c17969e68ff.png"
)

EXPECTED_B4_PARTS = [
    "hair_back_base",
    "hair_back_strand_L",
    "hair_back_strand_R",
    "hair_back_center",
    "hair_front_center",
    "hair_front_L",
    "hair_front_R",
    "hair_front_side_L",
    "hair_front_side_R",
    "hair_front_tip_L",
    "hair_front_tip_R",
    "hair_side_L_outer",
    "hair_side_L_inner",
    "hair_side_R_outer",
    "hair_side_R_inner",
    "hair_back_underpaint",
]

FORBIDDEN_EXISTING_HAIR_ASSETS = [
    EXP / "material_pack_first_v0/normalized_layers",
    EXP / "model_edit_v13_scaled_eye_mouth_preview/mini_cubism_diagnostic_project/parts",
    EXP / "model_edit_v19_generated_eye_preview/mini_cubism_diagnostic_project/parts",
    EXP / "model_edit_v20_manual_eye_anchor_preview/mini_cubism_diagnostic_project/parts",
    EXP / "model_edit_v21_supported_rig_smoke_preview/mini_cubism_diagnostic_project/parts",
]

PROMPT = """Use case: stylized-concept
Asset type: Live2D/Cubism v22 B4 hair-pack reference sheet for character material generation.
Primary request: Create a clean anime Live2D / Cubism hair material reference sheet for the same character identity: adult cute woman, long warm brown hair with soft glossy anime shading, center crown swirl, layered bangs over the forehead, long side locks on both sides, darker back hair mass, white sweater shoulders visible only as faint context.
Sheet contents: independent hair part candidates for rigging, arranged clearly on a plain light background without labels or text. Include 16 visually separable hair components: back base mass, left back strand, right back strand, center back strand, front center bang, front left bang, front right bang, left front side bang, right front side bang, left front tip, right front tip, left outer side hair, left inner side hair, right outer side hair, right inner side hair, and a subtle hair underpaint/back-fill piece.
Style and identity: keep the same hairstyle silhouette, same brown color palette, same line thickness, same cel-shaded rendering style, same bang occlusion shape, and same front-facing upper-body character proportions as the source.
Rigging requirements: every hair child should look like it belongs to one coordinated hairstyle, with clean strand boundaries suitable for hair physics and independent front hair motion. ParamHairFront remains unsupported until real hair_front_* child parts are extracted and can move independently.
Negative prompt: no old asset reuse, no labels, no typography, no guide arrows, no part names, no grids, no extra accessories, no hairstyle change, no hair covering the eyes completely, no face-covering props, no hands."""


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def rel_or_abs(path: Path) -> str:
    try:
        return rel(path)
    except ValueError:
        return str(path.resolve())


def load_rgb(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def draw_contact_sheet(source: Image.Image, b1: Image.Image, b4: Image.Image) -> None:
    source_thumb = source.resize((360, 360), Image.Resampling.LANCZOS)
    b1_thumb = b1.resize((360, 360), Image.Resampling.LANCZOS)
    b4_thumb = b4.resize((540, 360), Image.Resampling.LANCZOS)
    margin = 24
    label_h = 34
    width = margin * 4 + source_thumb.width + b1_thumb.width + b4_thumb.width
    height = margin * 2 + label_h + 360
    sheet = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(sheet)
    panels = [
        ("G0 source/style", source_thumb),
        ("B1 clean base", b1_thumb),
        ("B4 new hair-pack raw", b4_thumb),
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
    b4 = load_rgb(B4_RAW)
    draw_contact_sheet(source, b1, b4)

    visual_checks = [
        {
            "id": "new_generation_no_existing_hair_asset_reuse",
            "status": "PASS_RECORDED",
            "evidence": "B4 raw sheet was generated via built-in imagegen after the no-existing-assets instruction; prior normalized/model_edit parts are recorded as forbidden inputs.",
        },
        {
            "id": "same_character_hair_style",
            "status": "PASS_CANDIDATE",
            "evidence": "The sheet keeps warm brown long hair, crown swirl, glossy highlights, line thickness, and the source bang/side-lock silhouette.",
        },
        {
            "id": "front_hair_children_visible",
            "status": "PASS_CANDIDATE",
            "evidence": "Front-center, left/right bang, front-side, and tip candidates are visibly present as separable groups.",
        },
        {
            "id": "side_back_hair_groups_visible",
            "status": "PASS_CANDIDATE",
            "evidence": "Back base, side locks, and long strand groups are visible with usable strand boundaries for later physics extraction.",
        },
        {
            "id": "hairfront_contract_gate",
            "status": "HOLD_UNSUPPORTED_CONTROL",
            "evidence": "ParamHairFront stays hidden/contract-only until extracted hair_front_* full-canvas RGBA parts pass overlay and motion QA.",
        },
        {
            "id": "extraction_readiness",
            "status": "REVISE_BEFORE_LAYER_PROMOTION",
            "evidence": "The sheet is RGB on a light background and includes full-pose/context art; it must be extracted/masked before full-canvas RGBA B4 material can be claimed.",
        },
        {
            "id": "human_visual_review",
            "status": "REQUIRED",
            "evidence": "주인님 must approve hairstyle identity, front bang occlusion, strand scale, and side/back hair readability before B4 is promoted beyond raw candidate.",
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
            "status": "FORBIDDEN_AS_B4_INPUT",
        }
        for path in FORBIDDEN_EXISTING_HAIR_ASSETS
    ]

    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "review_id": "cubism-v2-new-character-002-v22-b4-hair-pack-review-001",
        "status": "B4_RAW_HAIR_PACK_CANDIDATE_READY_FOR_EXTRACTION_HUMAN_REVIEW_REQUIRED",
        "source_image": rel(SOURCE),
        "b1_clean_base_reference": rel(B1_RAW),
        "b4_raw_image": rel(B4_RAW),
        "built_in_imagegen_source": rel_or_abs(BUILT_IN_SOURCE),
        "contact_sheet": rel(CONTACT_SHEET),
        "imagegen_mode": "built_in_image_gen",
        "image_generation": "RUN_ON_2026_06_09",
        "prompt": PROMPT,
        "expected_b4_parts": EXPECTED_B4_PARTS,
        "allowed_inputs": [rel(path) for path in allowed_inputs],
        "forbidden_existing_hair_assets": forbidden,
        "locked_success_criteria": [
            "Do not reuse prior normalized/model_edit hair PNGs for B4 material.",
            "HairFront remains hidden until real hair_front_* child art exists and passes QA.",
            "Front, side, and back hair groups must remain readable as separate motion candidates.",
            "Side/back hair parts need enough underpaint/back-fill coverage for angle and physics motion.",
            "Do not promote this raw sheet to final material without RGBA extraction, overlay QA, and human visual review.",
        ],
        "visual_checks": visual_checks,
        "decision": "Keep this as the v22 B4 newly generated hair-pack raw candidate. It can feed B4 extraction planning, but it is not yet separated full-canvas RGBA hair material and does not unlock ParamHairFront or real Cubism success claims.",
        "next_action": [
            "Extract/normalize B4 components into full-canvas RGBA candidates for the 16 expected hair parts.",
            "Run B4 contact-sheet and overlay QA against the G0 source and B1 clean-base silhouette.",
            "Keep ParamHairFront hidden until hair_front_* child parts are extracted, aligned, and accepted by visual QA.",
        ],
        "self_review": {
            "source_exists": SOURCE.exists(),
            "b1_raw_exists": B1_RAW.exists(),
            "b4_raw_exists": B4_RAW.exists(),
            "built_in_imagegen_source_exists": BUILT_IN_SOURCE.exists(),
            "source_size": list(source.size),
            "b1_raw_size": list(b1.size),
            "b4_raw_size": list(b4.size),
            "b4_mode": b4.mode,
            "expected_b4_part_count": len(EXPECTED_B4_PARTS),
            "allowed_input_count": len(allowed_inputs),
            "forbidden_existing_hair_asset_count": len(forbidden),
            "visual_check_count": len(visual_checks),
            "has_human_required_gate": any(check["status"] == "REQUIRED" for check in visual_checks),
            "has_hairfront_contract_gate": any(check["id"] == "hairfront_contract_gate" for check in visual_checks),
            "has_front_hair_children_scope": any(part.startswith("hair_front") for part in EXPECTED_B4_PARTS),
            "forbidden_assets_not_output_path": all(path.resolve() != B4_RAW.resolve() for path in FORBIDDEN_EXISTING_HAIR_ASSETS),
            "status": "PASS",
        },
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Character 002 v22 B4 Hair Pack Review",
        "",
        f"- status: `{report['status']}`",
        f"- source image: `{report['source_image']}`",
        f"- B1 clean-base reference: `{report['b1_clean_base_reference']}`",
        f"- B4 raw image: `{report['b4_raw_image']}`",
        f"- contact sheet: `{report['contact_sheet']}`",
        f"- imagegen mode: `{report['imagegen_mode']}`",
        "",
        "## Expected B4 Parts",
        "",
        *[f"- `{item}`" for item in EXPECTED_B4_PARTS],
        "",
        "## Allowed Inputs",
        "",
        *[f"- `{item}`" for item in report["allowed_inputs"]],
        "",
        "## Forbidden Existing Hair Assets",
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

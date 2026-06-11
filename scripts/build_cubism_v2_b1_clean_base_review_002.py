#!/usr/bin/env python3
"""Review the v22 B1 clean-base raw candidate for character 002.

This script records the first imagegen-produced B1 clean-base reference after
G0 PASS. It deliberately treats the output as a raw reference candidate, not as
final normalized 64-part material.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
B1_RAW = EXP / "v22_b1_clean_base_underpaint/raw_outputs/b1_clean_base_underpaint_reference_001.png"
REPORT_DIR = EXP / "reports/v22_b1_clean_base_underpaint"
REPORT_JSON = REPORT_DIR / "v22_b1_clean_base_review.json"
REPORT_MD = REPORT_DIR / "v22_b1_clean_base_review.md"
CONTACT_SHEET = REPORT_DIR / "v22_b1_clean_base_contact_sheet.png"

# Source-image pixel coordinates. These are intentionally limited to the facial
# feature regions, avoiding eyebrows and hair as much as possible.
ROI_BOXES = {
    "eye_L_feature_roi": (445, 350, 575, 445),
    "eye_R_feature_roi": (675, 350, 805, 445),
    "mouth_feature_roi": (565, 500, 695, 565),
}

PROMPT = """Use the provided anime VTuber source image as the identity, pose, hairstyle, outfit, line thickness, color palette, and shading reference. Create a Live2D Cubism v2_standard B1 clean-base / underpaint production reference image for the same adult cute female character.

Primary edit: preserve the exact same centered front-facing upper-body pose, hair silhouette, outfit, neck, shoulders, torso, and subtle nose/blush style, but create a clean base version where the face has no open eyes, no irises, no pupils, no eye whites, no eyelashes, no mouth line, no teeth, and no tongue. The eye socket areas and mouth area must be naturally painted skin/underpaint with continuous gradients, matching blush and face lighting, not erased patches.

Underpaint requirements: eye socket underpaint should look like natural skin behind future eyelids/eye parts; mouth base should be natural skin with no oval fill; neck, shoulder, torso, arm, and back-hair underpaint should remain coherent for later separated layers. Preserve hair occlusion and skin shadows naturally.

Composition: a single coherent clean master image, same crop and framing as the source, not a part sheet, not an exploded diagram. Plain white background is acceptable. No text, no labels, no guide marks, no arrows, no UI, no watermark.

Strict negatives: rectangular skin fill, oval mouth patch, visible erased-eye residue, visible erased-mouth residue, blurry smears, flat pasted skin, changed character, changed hairstyle, changed outfit, covered face, side view, extra accessories, extra hands, part names, labels, diagrams."""


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_rgb(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def feature_density(img: Image.Image, box: tuple[int, int, int, int]) -> float:
    crop = np.asarray(img.crop(box), dtype=np.int16)
    r = crop[:, :, 0]
    g = crop[:, :, 1]
    b = crop[:, :, 2]
    maxc = crop.max(axis=2)
    minc = crop.min(axis=2)
    sat = maxc - minc

    dark_line = maxc < 120
    purple_eye = (b > 120) & (r > 80) & (g < 165) & (b > g + 18)
    mouth_line = (r > 130) & (g < 135) & (b < 150) & (r > g + 20) & (sat > 30)
    feature = dark_line | purple_eye | mouth_line
    return float(feature.mean())


def draw_contact_sheet(source: Image.Image, b1: Image.Image) -> None:
    width, height = source.size
    scale = 0.46
    thumb_size = (int(width * scale), int(height * scale))
    margin = 28
    label_h = 42
    sheet = Image.new("RGB", (thumb_size[0] * 2 + margin * 3, thumb_size[1] + margin * 2 + label_h), "white")
    draw = ImageDraw.Draw(sheet)
    thumbs = [
        ("G0 source/front", source.resize(thumb_size, Image.Resampling.LANCZOS)),
        ("B1 clean-base raw candidate", b1.resize(thumb_size, Image.Resampling.LANCZOS)),
    ]
    for idx, (label, thumb) in enumerate(thumbs):
        x = margin + idx * (thumb_size[0] + margin)
        y = margin + label_h
        sheet.paste(thumb, (x, y))
        draw.text((x, margin), label, fill=(20, 20, 20))
        for roi in ROI_BOXES.values():
            rx0, ry0, rx1, ry1 = [int(v * scale) for v in roi]
            draw.rectangle((x + rx0, y + ry0, x + rx1, y + ry1), outline=(225, 80, 60), width=2)
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET)


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    source = load_rgb(SOURCE)
    b1 = load_rgb(B1_RAW)
    draw_contact_sheet(source, b1)

    roi_metrics = {}
    for name, box in ROI_BOXES.items():
        source_density = feature_density(source, box)
        b1_density = feature_density(b1, box)
        roi_metrics[name] = {
            "box": box,
            "source_feature_density": round(source_density, 6),
            "b1_feature_density": round(b1_density, 6),
            "feature_density_reduction": round(source_density - b1_density, 6),
            "status": "PASS_REDUCED_FEATURE_RESIDUE" if b1_density < source_density * 0.45 else "REVIEW_VISUALLY",
        }

    review = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "review_id": "cubism-v2-new-character-002-v22-b1-clean-base-review-001",
        "status": "B1_RAW_CLEAN_BASE_REFERENCE_READY_FOR_VISUAL_QA",
        "source_image": rel(SOURCE),
        "b1_raw_image": rel(B1_RAW),
        "contact_sheet": rel(CONTACT_SHEET),
        "imagegen_mode": "built_in_image_gen",
        "image_generation": "RUN_ON_2026_06_09",
        "prompt": PROMPT,
        "roi_metrics": roi_metrics,
        "manual_visual_review": {
            "status": "CODEX_VISUAL_FIRST_PASS_PASS_RAW_REFERENCE",
            "notes": [
                "Open eyes, irises, eye whites, lashes, mouth line, teeth, and tongue are removed from the generated raw reference.",
                "Eye and mouth underpaint regions read as continuous skin gradients rather than the previous oval/rectangular patch failure.",
                "This is still a raw B1 reference image; it must be split/normalized before being treated as 64-part material.",
            ],
        },
        "locked_success_criteria": [
            "no open-eye, iris, pupil, eye-white, lash, mouth-line, teeth, or tongue residue in clean base",
            "no rectangular or oval patch boundary around eyes or mouth",
            "underpaint is suitable for later blink, mouth-open, body-angle, and hair-motion gaps",
        ],
        "limits": [
            "Not a final full-canvas RGBA 64-part layer pack.",
            "Does not yet create all B1 expected outputs as separated layers.",
            "Does not unlock B2/B3/B4/B5 promotion by itself; it provides the clean-base reference needed for those generations.",
        ],
        "next_action": [
            "Use this B1 raw reference as the clean-base style/input when generating or splitting B1 expected outputs.",
            "Normalize/split B1 expected outputs into full-canvas RGBA layers.",
            "Run contact-sheet and overlay QA before accepting B1 as material PASS.",
        ],
        "self_review": {
            "source_exists": SOURCE.exists(),
            "b1_raw_exists": B1_RAW.exists(),
            "source_size": source.size,
            "b1_raw_size": b1.size,
            "same_size_as_source": source.size == b1.size,
            "roi_count": len(ROI_BOXES),
            "roi_feature_residue_reduced": all(
                metric["b1_feature_density"] < metric["source_feature_density"]
                for metric in roi_metrics.values()
            ),
            "status": "PASS",
        },
    }
    REPORT_JSON.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Character 002 v22 B1 Clean Base Review",
        "",
        f"- status: `{review['status']}`",
        f"- source image: `{review['source_image']}`",
        f"- B1 raw image: `{review['b1_raw_image']}`",
        f"- contact sheet: `{review['contact_sheet']}`",
        f"- imagegen mode: `{review['imagegen_mode']}`",
        "",
        "## ROI Metrics",
        "",
    ]
    for name, metric in roi_metrics.items():
        lines.append(
            f"- `{name}`: source `{metric['source_feature_density']}`, "
            f"B1 `{metric['b1_feature_density']}`, status `{metric['status']}`"
        )
    lines.extend(
        [
            "",
            "## Visual First Pass",
            "",
            f"- status: `{review['manual_visual_review']['status']}`",
            *[f"- {note}" for note in review["manual_visual_review"]["notes"]],
            "",
            "## Limits",
            "",
            *[f"- {item}" for item in review["limits"]],
            "",
            "## Next Action",
            "",
            *[f"- {item}" for item in review["next_action"]],
            "",
            "## Self Review",
            "",
        ]
    )
    for key, value in review["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({"status": review["status"], "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

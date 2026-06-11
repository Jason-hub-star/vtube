#!/usr/bin/env python3
"""Build the v22 G4 generated torso_base candidate packet.

This script normalizes the focused imagegen torso underpaint candidate into a
2048x2048 full-canvas RGBA Live2D/Cubism review candidate. It does not promote
the part to material PASS.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path("/Users/family/jason/Vtube")
EXP = ROOT / "experiments/cubism-v2-new-character-002"
INPUT_PACKET = (
    EXP
    / "reports/v22_g4_torso_base_regen_review_packet/v22_g4_torso_base_regen_input_packet.json"
)
RAW_IMAGE = (
    EXP
    / "v22_g4_torso_base_regen_candidate/raw_outputs/torso_base_regen_reference_001.png"
)
ALPHA_IMAGE = (
    EXP
    / "v22_g4_torso_base_regen_candidate/normalized_layers/torso_base_generated_alpha_candidate.png"
)
FULL_CANVAS = EXP / "v22_g4_torso_base_regen_candidate/normalized_layers/torso_base.png"
REPORT_DIR = EXP / "reports/v22_g4_torso_base_regen_candidate"
REPORT_JSON = REPORT_DIR / "v22_g4_torso_base_regen_candidate_report.json"
REPORT_MD = REPORT_DIR / "v22_g4_torso_base_regen_candidate_report.md"
OVERLAY = REPORT_DIR / "v22_g4_torso_base_regen_candidate_overlay.png"
MASK_OVERLAY = REPORT_DIR / "v22_g4_torso_base_regen_candidate_mask_overlay.png"
CONTACT_SHEET = REPORT_DIR / "v22_g4_torso_base_regen_candidate_contact_sheet.png"
SOURCE_IMAGE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
CANVAS_SIZE = (2048, 2048)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def alpha_bbox(image: Image.Image, threshold: int = 8) -> list[int] | None:
    arr = np.array(image.convert("RGBA"))
    alpha = arr[:, :, 3]
    ys, xs = np.where(alpha > threshold)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)]


def alpha_metrics(image: Image.Image) -> dict:
    rgba = image.convert("RGBA")
    arr = np.array(rgba)
    alpha = arr[:, :, 3]
    nonzero = int((alpha > 8).sum())
    partial = int(((alpha > 0) & (alpha < 255)).sum())
    total = int(alpha.size)
    return {
        "mode": rgba.mode,
        "size": list(rgba.size),
        "bbox": alpha_bbox(rgba),
        "alpha_pixels": nonzero,
        "partial_alpha_pixels": partial,
        "alpha_coverage": round(nonzero / total, 8),
        "corner_alpha": [
            int(alpha[0, 0]),
            int(alpha[0, -1]),
            int(alpha[-1, 0]),
            int(alpha[-1, -1]),
        ],
    }


def load_font(size: int = 18) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def label_panel(image: Image.Image, title: str, lines: list[str], size: tuple[int, int]) -> Image.Image:
    panel = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(panel)
    font_title = load_font(18)
    font = load_font(14)
    draw.text((12, 10), title, fill=(20, 24, 32), font=font_title)
    y = 36
    for line in lines:
        draw.text((12, y), line, fill=(56, 64, 80), font=font)
        y += 20
    max_w = size[0] - 28
    max_h = size[1] - y - 12
    thumb = image.convert("RGBA")
    thumb.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    bg = Image.new("RGBA", thumb.size, (245, 247, 250, 255))
    bg.alpha_composite(thumb)
    panel.paste(bg.convert("RGB"), ((size[0] - thumb.width) // 2, y + 6))
    return panel


def build_overlays(source: Image.Image, candidate: Image.Image) -> tuple[Image.Image, Image.Image]:
    base = source.convert("RGB").resize(CANVAS_SIZE, Image.Resampling.LANCZOS).convert("RGBA")
    actual = base.copy()
    toned = candidate.convert("RGBA")
    alpha = np.array(toned)[:, :, 3]
    toned_arr = np.array(toned)
    toned_arr[:, :, 3] = np.minimum(alpha, 178)
    actual.alpha_composite(Image.fromarray(toned_arr, "RGBA"))

    mask = base.copy()
    mask_arr = np.array(candidate.convert("RGBA"))
    mask_alpha = mask_arr[:, :, 3]
    color = np.zeros_like(mask_arr)
    color[:, :, 0] = 255
    color[:, :, 1] = 68
    color[:, :, 2] = 68
    color[:, :, 3] = np.where(mask_alpha > 8, 112, 0).astype(np.uint8)
    mask.alpha_composite(Image.fromarray(color, "RGBA"))
    return actual.convert("RGB"), mask.convert("RGB")


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    FULL_CANVAS.parent.mkdir(parents=True, exist_ok=True)

    input_packet = json.loads(INPUT_PACKET.read_text())
    crop_box = input_packet["target"]["crop_box"]
    crop_x0, crop_y0, crop_x1, crop_y1 = crop_box
    crop_w = crop_x1 - crop_x0
    crop_h = crop_y1 - crop_y0

    alpha_candidate = Image.open(ALPHA_IMAGE).convert("RGBA")
    candidate_bbox = alpha_bbox(alpha_candidate)
    if candidate_bbox is None:
        raise RuntimeError("alpha candidate is empty")
    x0, y0, x1, y1 = candidate_bbox
    cropped = alpha_candidate.crop((x0, y0, x1, y1))

    scale = crop_w / cropped.width
    resized_h = int(round(cropped.height * scale))
    if resized_h > crop_h:
        scale = crop_h / cropped.height
        resized_w = int(round(cropped.width * scale))
        resized_h = crop_h
    else:
        resized_w = crop_w

    resized = cropped.resize((resized_w, resized_h), Image.Resampling.LANCZOS)
    paste_x = crop_x0 + (crop_w - resized_w) // 2
    paste_y = crop_y0

    full = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    full.alpha_composite(resized, (paste_x, paste_y))
    full.save(FULL_CANVAS)

    source = Image.open(SOURCE_IMAGE)
    overlay, mask_overlay = build_overlays(source, full)
    overlay.save(OVERLAY)
    mask_overlay.save(MASK_OVERLAY)

    raw = Image.open(RAW_IMAGE)
    panels = [
        label_panel(raw, "raw imagegen torso reference", ["flat chroma source"], (520, 420)),
        label_panel(alpha_candidate, "alpha extracted candidate", ["transparent corners", "not full canvas"], (520, 420)),
        label_panel(full, "2048 full-canvas torso_base", [f"bbox {alpha_metrics(full)['bbox']}"], (520, 420)),
        label_panel(mask_overlay, "source mask overlay", ["red = generated torso alpha"], (520, 420)),
    ]
    sheet = Image.new("RGB", (1040, 840), (238, 241, 245))
    for idx, panel in enumerate(panels):
        x = (idx % 2) * 520
        y = (idx // 2) * 420
        sheet.paste(panel, (x, y))
    sheet.save(CONTACT_SHEET)

    full_metrics = alpha_metrics(full)
    raw_metrics = {
        "mode": raw.mode,
        "size": list(raw.size),
    }
    alpha_candidate_metrics = alpha_metrics(alpha_candidate)
    target_bbox = full_metrics["bbox"]
    crop_contains_bbox = (
        target_bbox is not None
        and target_bbox[0] >= crop_x0
        and target_bbox[1] >= crop_y0
        and target_bbox[2] <= crop_x1
        and target_bbox[3] <= crop_y1
    )

    status = "G4_TORSO_BASE_REGEN_CANDIDATE_READY_FOR_OVERLAY_QA_MATERIAL_BLOCKED"
    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "input_status": input_packet["status"],
        "source_image": rel(SOURCE_IMAGE),
        "raw_image": rel(RAW_IMAGE),
        "alpha_candidate": rel(ALPHA_IMAGE),
        "full_canvas_candidate": rel(FULL_CANVAS),
        "overlay": rel(OVERLAY),
        "mask_overlay": rel(MASK_OVERLAY),
        "contact_sheet": rel(CONTACT_SHEET),
        "target": {
            "part_id": "torso_base",
            "required_output": "full-canvas 2048x2048 RGBA torso_base.png",
            "crop_box": crop_box,
            "placement": {
                "mode": "fit_candidate_alpha_bbox_to_target_crop_width_top_aligned",
                "scale": round(scale, 8),
                "paste_xy": [paste_x, paste_y],
                "resized_size": [resized_w, resized_h],
            },
        },
        "metrics": {
            "raw": raw_metrics,
            "alpha_candidate": alpha_candidate_metrics,
            "full_canvas": full_metrics,
            "crop_contains_bbox": crop_contains_bbox,
        },
        "qa": {
            "automated_verdict": "PASS_TECHNICAL_CANDIDATE_REVIEW_REQUIRED",
            "visual_verdict": "PENDING_OVERLAY_QA_REVIEW",
            "material_promotion": "BLOCKED",
            "reason": (
                "Generated torso_base is a coherent single-part underpaint candidate, "
                "but generated anatomy/style/placement require overlay QA before any G5 material gate."
            ),
        },
        "locks": {
            "not_owner_approval": True,
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g5_status": "BLOCKED_PENDING_TORSO_OVERLAY_QA_AND_SEPARATE_G5_ACCEPTANCE",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
    }
    report["self_review"] = {
        "status": report["status"] == status,
        "input_status": report["input_status"] == "TORSO_BASE_REGEN_INPUT_READY_MATERIAL_BLOCKED",
        "raw_exists": RAW_IMAGE.exists(),
        "alpha_candidate_exists": ALPHA_IMAGE.exists(),
        "full_canvas_exists": FULL_CANVAS.exists(),
        "full_canvas_rgba_2048": full_metrics["mode"] == "RGBA" and full_metrics["size"] == [2048, 2048],
        "full_canvas_non_empty": full_metrics["alpha_pixels"] > 0,
        "transparent_corners": full_metrics["corner_alpha"] == [0, 0, 0, 0],
        "crop_contains_bbox": crop_contains_bbox,
        "overlay_exists": OVERLAY.exists(),
        "mask_overlay_exists": MASK_OVERLAY.exists(),
        "contact_sheet_exists": CONTACT_SHEET.exists(),
        "not_owner_approval": report["locks"]["not_owner_approval"] is True,
        "material_pass_blocked": report["locks"]["material_pass_status"] == "BLOCKED",
        "param_hair_front_hidden": report["locks"]["param_hair_front_status"] == "HIDDEN_CONTRACT_ONLY",
        "g7_blocked": report["locks"]["g7_mini_cubism_status"] == "BLOCKED",
        "g8_blocked": report["locks"]["g8_real_cubism_status"] == "BLOCKED",
    }

    save_json(REPORT_JSON, report)
    md_lines = [
        "# v22 G4 torso_base Regen Candidate",
        "",
        f"- status: `{report['status']}`",
        f"- input status: `{report['input_status']}`",
        f"- raw image: `{report['raw_image']}`",
        f"- alpha candidate: `{report['alpha_candidate']}`",
        f"- full-canvas candidate: `{report['full_canvas_candidate']}`",
        f"- overlay: `{report['overlay']}`",
        f"- mask overlay: `{report['mask_overlay']}`",
        f"- contact sheet: `{report['contact_sheet']}`",
        "",
        "## Metrics",
        "",
        f"- full-canvas mode/size: `{full_metrics['mode']}` `{full_metrics['size']}`",
        f"- bbox: `{full_metrics['bbox']}`",
        f"- alpha coverage: `{full_metrics['alpha_coverage']}`",
        f"- crop contains bbox: `{crop_contains_bbox}`",
        "",
        "## QA",
        "",
        f"- automated verdict: `{report['qa']['automated_verdict']}`",
        f"- visual verdict: `{report['qa']['visual_verdict']}`",
        f"- material promotion: `{report['qa']['material_promotion']}`",
        f"- G5: `{report['locks']['g5_status']}`",
        f"- ParamHairFront: `{report['locks']['param_hair_front_status']}`",
        f"- G7 Mini Cubism: `{report['locks']['g7_mini_cubism_status']}`",
        f"- G8 real Cubism: `{report['locks']['g8_real_cubism_status']}`",
        "",
        "## Self Review",
        "",
    ]
    for key, value in report["self_review"].items():
        md_lines.append(f"- `{key}`: `{value}`")
    REPORT_MD.write_text("\n".join(md_lines) + "\n")

    if not all(report["self_review"].values()):
        failed = [k for k, v in report["self_review"].items() if not v]
        raise RuntimeError(f"self review failed: {failed}")
    print(json.dumps({"status": status, "self_review": "PASS", "report": rel(REPORT_JSON)}, indent=2))


if __name__ == "__main__":
    main()

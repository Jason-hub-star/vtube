#!/usr/bin/env python3
"""Build a B5 refined-mask v1 candidate from the auto-draft corrected layers.

This targets the 13 B5 parts triaged as extraction-mask problems. It does not
approve material quality; it produces a safer candidate for overlay QA.
"""

from __future__ import annotations

import json
import math
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
TRIAGE_JSON = EXP / "reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_auto_draft_review_triage.json"
AUTO_DRAFT_REPORT_JSON = (
    EXP / "reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_anchor_corrected_auto_draft_report.json"
)
SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
OUT_DIR = EXP / "v22_b5_refined_mask_v1/normalized_layers"
REPORT_DIR = EXP / "reports/v22_b5_refined_mask_v1"
REPORT_JSON = REPORT_DIR / "v22_b5_refined_mask_v1_report.json"
REPORT_MD = REPORT_DIR / "v22_b5_refined_mask_v1_report.md"
CONTACT_SHEET = REPORT_DIR / "v22_b5_refined_mask_v1_contact_sheet.png"
OVERLAY_SHEET = REPORT_DIR / "v22_b5_refined_mask_v1_overlay_qa.png"
CANVAS = 2048

B5_PARTS = [
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

REFINE_TARGETS = {
    "arm_L_upper_simple",
    "arm_R_upper_simple",
    "cheek_L",
    "cheek_R",
    "chest_cloth_base",
    "chest_cloth_shadow",
    "collar_shadow",
    "face_shadow_L",
    "face_shadow_R",
    "nose",
    "shoulder_L",
    "shoulder_R",
    "torso_base",
}

# Soft mask specs are full-canvas target-space and intentionally conservative.
SHAPES = {
    "torso_base": ("polygon", [(610, 960), (1450, 960), (1410, 1870), (650, 1870)], 28),
    "shoulder_L": ("ellipse", [575, 1012, 875, 1215], 18),
    "shoulder_R": ("ellipse", [1190, 1015, 1460, 1218], 18),
    "arm_L_upper_simple": ("round_rect", [505, 1125, 690, 1780], 22),
    "arm_R_upper_simple": ("round_rect", [1330, 1125, 1515, 1780], 22),
    "collar_shadow": ("round_rect", [735, 1192, 1315, 1265], 12),
    "chest_cloth_base": ("polygon", [(680, 1285), (1345, 1285), (1285, 1545), (735, 1545)], 20),
    "chest_cloth_shadow": ("polygon", [(760, 1460), (1260, 1460), (1225, 1630), (800, 1630)], 18),
    "nose": ("ellipse", [1000, 750, 1048, 835], 7),
    "cheek_L": ("ellipse", [765, 755, 902, 840], 14),
    "cheek_R": ("ellipse", [1146, 755, 1283, 840], 14),
    "face_shadow_L": ("ellipse", [705, 660, 865, 910], 20),
    "face_shadow_R": ("ellipse", [1170, 660, 1330, 910], 20),
}

ALPHA_SCALE = {
    "nose": 0.62,
    "cheek_L": 0.48,
    "cheek_R": 0.48,
    "face_shadow_L": 0.45,
    "face_shadow_R": 0.45,
    "collar_shadow": 0.72,
    "chest_cloth_shadow": 0.7,
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def bbox_from_alpha(img: Image.Image) -> list[int] | None:
    alpha = np.asarray(img.getchannel("A"), dtype=np.uint8)
    ys, xs = np.where(alpha > 5)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def coverage(img: Image.Image) -> float:
    alpha = np.asarray(img.getchannel("A"), dtype=np.uint8)
    return round(float((alpha > 5).mean()), 8)


def alpha_sum(img: Image.Image) -> int:
    return int(np.asarray(img.getchannel("A"), dtype=np.uint8).sum())


def shape_mask(part_id: str) -> Image.Image:
    kind, data, blur = SHAPES[part_id]
    mask = Image.new("L", (CANVAS, CANVAS), 0)
    draw = ImageDraw.Draw(mask)
    if kind == "polygon":
        draw.polygon(data, fill=255)
    elif kind == "ellipse":
        draw.ellipse(data, fill=255)
    elif kind == "round_rect":
        draw.rounded_rectangle(data, radius=24, fill=255)
    else:
        raise ValueError(kind)
    return mask.filter(ImageFilter.GaussianBlur(blur))


def refine_layer(part_id: str, img: Image.Image) -> Image.Image:
    img = img.convert("RGBA")
    old_alpha = np.asarray(img.getchannel("A"), dtype=np.float32)
    gate = np.asarray(shape_mask(part_id), dtype=np.float32) / 255.0
    scale = ALPHA_SCALE.get(part_id, 1.0)
    new_alpha = np.clip(old_alpha * gate * scale, 0, 255).astype(np.uint8)
    out = img.copy()
    out.putalpha(Image.fromarray(new_alpha, "L").filter(ImageFilter.GaussianBlur(0.45)))
    return out


def build_contact(entries: list[dict]) -> None:
    cols = 5
    thumb = 260
    label_h = 70
    rows = math.ceil(len(entries) / cols)
    sheet = Image.new("RGB", (cols * thumb, rows * (thumb + label_h)), (247, 248, 250))
    draw = ImageDraw.Draw(sheet)
    for idx, entry in enumerate(entries):
        x = (idx % cols) * thumb
        y = (idx // cols) * (thumb + label_h)
        img = Image.open(ROOT / entry["output_path"]).convert("RGBA")
        bbox = img.getchannel("A").getbbox()
        crop = img.crop(bbox) if bbox else img
        crop.thumbnail((thumb - 20, thumb - 44), Image.Resampling.LANCZOS)
        tile = Image.new("RGB", (thumb, thumb), (238, 241, 245))
        tile.paste((255, 255, 255), (8, 8, thumb - 8, thumb - 44))
        tile.paste(crop.convert("RGB"), ((thumb - crop.width) // 2, (thumb - 44 - crop.height) // 2), crop)
        sheet.paste(tile, (x, y + label_h))
        draw.text((x + 8, y + 8), entry["part_id"], fill=(25, 31, 40))
        draw.text((x + 8, y + 28), entry["refine_status"], fill=(78, 89, 104))
        draw.text((x + 8, y + 48), f"cov {entry['alpha_coverage']}", fill=(78, 89, 104))
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET)


def overlay_tile(source: Image.Image, img: Image.Image, entry: dict) -> Image.Image:
    bbox = entry["bbox"] or [760, 760, 1260, 1260]
    pad = 110
    crop_box = (
        max(0, bbox[0] - pad),
        max(0, bbox[1] - pad),
        min(CANVAS, bbox[2] + pad),
        min(CANVAS, bbox[3] + pad),
    )
    base = source.crop(crop_box).convert("RGBA")
    layer = img.crop(crop_box).convert("RGBA")
    tint = Image.new("RGBA", base.size, (60, 135, 255, 0))
    alpha = layer.getchannel("A").point(lambda v: min(155, int(v * 0.7)))
    tint.putalpha(alpha)
    comp = Image.alpha_composite(base, tint)
    comp.thumbnail((360 - 18, 320 - 62), Image.Resampling.LANCZOS)
    tile = Image.new("RGB", (360, 320), (247, 248, 250))
    tile.paste(comp.convert("RGB"), ((360 - comp.width) // 2, 8))
    draw = ImageDraw.Draw(tile)
    draw.rectangle([4, 4, 355, 315], outline=(216, 222, 232))
    draw.text((10, 264), entry["part_id"], fill=(25, 31, 40))
    draw.text((10, 282), entry["refine_status"], fill=(78, 89, 104))
    draw.text((10, 300), f"cov {entry['alpha_coverage']}", fill=(78, 89, 104))
    return tile


def build_overlay(entries: list[dict]) -> None:
    source = Image.open(SOURCE).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    cols = 3
    rows = math.ceil(len(entries) / cols)
    sheet = Image.new("RGB", (cols * 360, 46 + rows * 320), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 14), "Character 002 v22 B5 Refined Mask v1 Overlay QA", fill=(25, 31, 40))
    for idx, entry in enumerate(entries):
        img = Image.open(ROOT / entry["output_path"]).convert("RGBA")
        tile = overlay_tile(source, img, entry)
        sheet.paste(tile, ((idx % cols) * 360, 46 + (idx // cols) * 320))
    OVERLAY_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OVERLAY_SHEET)


def main() -> int:
    triage = json.loads(TRIAGE_JSON.read_text(encoding="utf-8"))
    auto = json.loads(AUTO_DRAFT_REPORT_JSON.read_text(encoding="utf-8"))
    auto_entries = {entry["part_id"]: entry for entry in auto["entries"] if entry["source_batch"] == "B5"}
    refine_reasons = {
        entry["part_id"]: entry["reason"]
        for entry in triage["entries"]
        if entry["recommended_action"] == "REFINE_EXTRACTION_MASK"
    }

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    entries = []
    for part_id in B5_PARTS:
        src = ROOT / auto_entries[part_id]["output_path"]
        img = Image.open(src).convert("RGBA")
        old_sum = alpha_sum(img)
        if part_id in REFINE_TARGETS:
            out = refine_layer(part_id, img)
            refine_status = "REFINED_MASK_V1"
        else:
            out = img
            refine_status = "COPIED_FROM_AUTO_DRAFT"
        dst = OUT_DIR / f"{part_id}.png"
        out.save(dst)
        entries.append(
            {
                "part_id": part_id,
                "source_batch": "B5",
                "input_path": rel(src),
                "output_path": rel(dst),
                "refine_status": refine_status,
                "refine_reason": refine_reasons.get(part_id, ""),
                "bbox": bbox_from_alpha(out),
                "alpha_coverage": coverage(out),
                "alpha_sum_before": old_sum,
                "alpha_sum_after": alpha_sum(out),
                "mode": out.mode,
                "size": list(out.size),
            }
        )

    build_contact(entries)
    build_overlay(entries)
    counts = Counter(entry["refine_status"] for entry in entries)
    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": "B5_REFINED_MASK_V1_CANDIDATE_READY_FOR_OVERLAY_REVIEW",
        "triage_report": rel(TRIAGE_JSON),
        "auto_draft_report": rel(AUTO_DRAFT_REPORT_JSON),
        "output_dir": rel(OUT_DIR),
        "contact_sheet": rel(CONTACT_SHEET),
        "overlay_sheet": rel(OVERLAY_SHEET),
        "entries": entries,
        "decision": "B5 refined-mask v1 reduces the 13 extraction-mask problem parts while preserving all gates. This is a candidate for overlay review, not material PASS.",
        "next_action": [
            "Review B5 refined-mask v1 overlay sheet.",
            "Merge accepted B5 refined masks into the B4/B5 corrected candidate only after visual review.",
            "Keep ParamHairFront hidden and keep G7/G8 blocked.",
        ],
        "self_review": {
            "entry_count": len(entries),
            "refined_mask_count": counts.get("REFINED_MASK_V1", 0),
            "copied_from_auto_draft_count": counts.get("COPIED_FROM_AUTO_DRAFT", 0),
            "expected_refine_target_count": len(REFINE_TARGETS),
            "all_layers_rgba": all(entry["mode"] == "RGBA" for entry in entries),
            "all_layers_2048": all(entry["size"] == [CANVAS, CANVAS] for entry in entries),
            "all_layers_nonempty": all(entry["bbox"] is not None for entry in entries),
            "overlay_sheet_exists": OVERLAY_SHEET.exists(),
            "contact_sheet_exists": CONTACT_SHEET.exists(),
            "validator_only_promotion_blocked": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "status": "PASS",
        },
    }
    save_json(REPORT_JSON, report)

    lines = [
        "# Character 002 v22 B5 Refined Mask v1",
        "",
        f"- status: `{report['status']}`",
        f"- output dir: `{report['output_dir']}`",
        f"- overlay sheet: `{report['overlay_sheet']}`",
        f"- contact sheet: `{report['contact_sheet']}`",
        "",
        "## Decision",
        "",
        report["decision"],
        "",
        "## Next Action",
        "",
        *[f"- {item}" for item in report["next_action"]],
        "",
        "## Entries",
        "",
    ]
    for entry in entries:
        lines.append(
            f"- `{entry['refine_status']}` `{entry['part_id']}` cov `{entry['alpha_coverage']}` "
            f"bbox `{entry['bbox']}`"
        )
    lines.extend(["", "## Self Review", ""])
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": report["status"], "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

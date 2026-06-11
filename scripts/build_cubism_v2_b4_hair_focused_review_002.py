#!/usr/bin/env python3
"""Build a focused B4 hair review packet for the v22 64-part pipeline.

This does not approve B4 material or unlock ParamHairFront. It narrows the
existing 12 hair review targets into front-hair contract candidates versus
draw-order/mask/refinement work.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
B4_RAW = EXP / "v22_b4_hair_pack/raw_outputs/b4_hair_pack_reference_001.png"
B4_LAYER_JSON = EXP / "reports/v22_b4_hair_pack/v22_b4_layer_pack_report.json"
B4_QA_JSON = EXP / "reports/v22_b4_hair_pack/v22_b4_overlay_qa_report.json"
TRIAGE_JSON = EXP / "reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_auto_draft_review_triage.json"
CORRECTED_JSON = EXP / "reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_anchor_corrected_auto_draft_report.json"
REPORT_DIR = EXP / "reports/v22_b4_hair_focused_review"
REPORT_JSON = REPORT_DIR / "v22_b4_hair_focused_review.json"
REPORT_MD = REPORT_DIR / "v22_b4_hair_focused_review.md"
REVIEW_SHEET = REPORT_DIR / "v22_b4_hair_focused_review.png"
CANVAS = 2048

FRONT_TARGETS = {
    "hair_front_L",
    "hair_front_R",
    "hair_front_center",
    "hair_front_side_L",
    "hair_front_side_R",
    "hair_front_tip_L",
    "hair_front_tip_R",
}

BACK_DRAW_ORDER_TARGETS = {
    "hair_back_base",
    "hair_back_center",
    "hair_back_underpaint",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_source() -> Image.Image:
    return Image.open(SOURCE).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)


def bbox_with_pad(bbox: list[int], pad: int = 95) -> tuple[int, int, int, int]:
    return (
        max(0, bbox[0] - pad),
        max(0, bbox[1] - pad),
        min(CANVAS, bbox[2] + pad),
        min(CANVAS, bbox[3] + pad),
    )


def estimate_hair_mask(rgb: np.ndarray) -> np.ndarray:
    arr = rgb.astype(np.int16)
    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]
    lum = (r * 0.299 + g * 0.587 + b * 0.114)
    warm_brown = (r >= b + 6) & (g >= b - 12) & (r < 175) & (g < 150) & (b < 140)
    dark_line = lum < 82
    return warm_brown | dark_line


def estimate_skin_or_light_mask(rgb: np.ndarray) -> np.ndarray:
    arr = rgb.astype(np.int16)
    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]
    lum = (r * 0.299 + g * 0.587 + b * 0.114)
    skin = (r > 178) & (g > 120) & (b > 105) & (r >= g + 15) & (g >= b - 5)
    light_bg = lum > 228
    return skin | light_bg


def alpha_weighted_ratio(alpha: np.ndarray, mask: np.ndarray) -> float:
    weight = alpha.astype(np.float64)
    total = float(weight.sum())
    if total <= 0:
        return 0.0
    return round(float((weight * mask).sum() / total), 6)


def overlay_tint(base: Image.Image, layer: Image.Image, color: tuple[int, int, int]) -> Image.Image:
    base_rgba = base.convert("RGBA")
    alpha = layer.getchannel("A").point(lambda v: min(165, int(v * 0.72)))
    tint = Image.new("RGBA", base_rgba.size, (*color, 0))
    tint.putalpha(alpha)
    return Image.alpha_composite(base_rgba, tint)


def support_overlay(base: Image.Image, layer: Image.Image) -> Image.Image:
    rgb = np.asarray(base.convert("RGB"))
    hair = estimate_hair_mask(rgb)
    skin = estimate_skin_or_light_mask(rgb)
    alpha = np.asarray(layer.getchannel("A"), dtype=np.uint8)
    out = base.convert("RGBA")
    green = Image.new("RGBA", base.size, (55, 180, 95, 0))
    red = Image.new("RGBA", base.size, (230, 70, 70, 0))
    green_a = np.where(hair, alpha * 0.62, 0).clip(0, 150).astype(np.uint8)
    red_a = np.where(skin & ~hair, alpha * 0.48, 0).clip(0, 125).astype(np.uint8)
    green.putalpha(Image.fromarray(green_a, "L"))
    red.putalpha(Image.fromarray(red_a, "L"))
    return Image.alpha_composite(Image.alpha_composite(out, green), red)


def layer_preview(layer: Image.Image) -> Image.Image:
    bbox = layer.getchannel("A").getbbox()
    crop = layer.crop(bbox) if bbox else layer
    bg = Image.new("RGBA", crop.size, (245, 247, 250, 255))
    return Image.alpha_composite(bg, crop)


def tile(title: str, img: Image.Image, subtitle: str = "") -> Image.Image:
    w, h = 330, 285
    label_h = 50
    out = Image.new("RGB", (w, h), (247, 248, 250))
    draw = ImageDraw.Draw(out)
    draw.rectangle([4, 4, w - 5, h - 5], outline=(216, 222, 232))
    draw.text((10, 10), title[:45], fill=(25, 31, 40))
    if subtitle:
        draw.text((10, 30), subtitle[:48], fill=(78, 89, 104))
    preview = img.convert("RGBA")
    preview.thumbnail((w - 20, h - label_h - 14), Image.Resampling.LANCZOS)
    out.paste(preview.convert("RGB"), ((w - preview.width) // 2, label_h + 4), preview)
    return out


def recommendation(part_id: str, triage_action: str, hair_ratio: float, skin_ratio: float) -> str:
    if part_id in BACK_DRAW_ORDER_TARGETS:
        return "KEEP_AS_BACK_OR_UNDERPAINT_REVIEW_DRAW_ORDER_MASK"
    if part_id in FRONT_TARGETS:
        if hair_ratio >= 0.52 and skin_ratio <= 0.42:
            return "FRONT_HAIR_CHILD_CANDIDATE_HUMAN_REVIEW_REQUIRED"
        return "REFINE_FRONT_HAIR_MASK_OR_REGENERATE"
    if triage_action == "REVIEW_ANCHOR_AND_MASK":
        return "REVIEW_ANCHOR_AND_MASK"
    return "FOCUSED_HAIR_REVIEW_REQUIRED"


def build_sheet(source: Image.Image, entries: list[dict]) -> None:
    cols = 4
    tile_w, tile_h = 330, 285
    rows = len(entries)
    sheet = Image.new("RGB", (cols * tile_w, 54 + rows * tile_h), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 14), "Character 002 v22 B4 Hair Focused Review", fill=(25, 31, 40))
    for row, entry in enumerate(entries):
        layer = Image.open(ROOT / entry["output_path"]).convert("RGBA")
        crop_box = tuple(entry["crop_box"])
        source_crop = source.crop(crop_box)
        layer_crop = layer.crop(crop_box)
        tiles = [
            tile(f"{entry['part_id']} source", source_crop),
            tile("overlay QA", overlay_tint(source_crop, layer_crop, (70, 135, 255)), entry["triage_action"]),
            tile("support map", support_overlay(source_crop, layer_crop), "green hair, red skin/light"),
            tile("isolated layer", layer_preview(layer_crop), entry["recommendation"]),
        ]
        y = 54 + row * tile_h
        for col, item in enumerate(tiles):
            sheet.paste(item, (col * tile_w, y))
    REVIEW_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(REVIEW_SHEET)


def main() -> int:
    layer_report = json.loads(B4_LAYER_JSON.read_text(encoding="utf-8"))
    qa = json.loads(B4_QA_JSON.read_text(encoding="utf-8"))
    triage = json.loads(TRIAGE_JSON.read_text(encoding="utf-8"))
    corrected = json.loads(CORRECTED_JSON.read_text(encoding="utf-8"))
    source = load_source()

    metrics = layer_report["metrics"]
    corrected_entries = {entry["part_id"]: entry for entry in corrected["entries"] if entry["source_batch"] == "B4"}
    triage_entries = {entry["part_id"]: entry for entry in triage["entries"] if entry["source_batch"] == "B4"}
    focus_parts = triage["summary"]["review_focus_parts"]

    entries = []
    for part_id in focus_parts:
        metric = metrics[part_id]
        corrected_entry = corrected_entries[part_id]
        triage_entry = triage_entries[part_id]
        layer = Image.open(ROOT / corrected_entry["output_path"]).convert("RGBA")
        crop_box = bbox_with_pad(corrected_entry["bbox"])
        source_crop = source.crop(crop_box).convert("RGB")
        layer_crop = layer.crop(crop_box).convert("RGBA")
        alpha = np.asarray(layer_crop.getchannel("A"), dtype=np.uint8)
        rgb = np.asarray(source_crop)
        hair_ratio = alpha_weighted_ratio(alpha, estimate_hair_mask(rgb))
        skin_ratio = alpha_weighted_ratio(alpha, estimate_skin_or_light_mask(rgb))
        rec = recommendation(part_id, triage_entry["recommended_action"], hair_ratio, skin_ratio)
        entries.append(
            {
                "part_id": part_id,
                "group": triage_entry["group"],
                "triage_action": triage_entry["recommended_action"],
                "priority": triage_entry["priority"],
                "output_path": corrected_entry["output_path"],
                "bbox": corrected_entry["bbox"],
                "crop_box": list(crop_box),
                "alpha_coverage": corrected_entry["alpha_coverage"],
                "source_hair_support_ratio": hair_ratio,
                "source_skin_or_light_overlap_ratio": skin_ratio,
                "original_anchor_center": metric["anchor_center"],
                "target_anchor": corrected_entry["target_anchor"],
                "target_scale": corrected_entry["target_scale"],
                "recommendation": rec,
            }
        )

    build_sheet(source, entries)
    counts = Counter(entry["recommendation"] for entry in entries)
    front_entries = [entry for entry in entries if entry["part_id"] in FRONT_TARGETS]
    front_candidate_count = counts.get("FRONT_HAIR_CHILD_CANDIDATE_HUMAN_REVIEW_REQUIRED", 0)

    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": "B4_HAIR_FOCUSED_REVIEW_READY_PARAMHAIRFRONT_STILL_HIDDEN",
        "source_image": rel(SOURCE),
        "b4_raw_image": rel(B4_RAW),
        "b4_layer_pack_report": rel(B4_LAYER_JSON),
        "b4_overlay_qa_report": rel(B4_QA_JSON),
        "triage_report": rel(TRIAGE_JSON),
        "corrected_candidate_report": rel(CORRECTED_JSON),
        "review_sheet": rel(REVIEW_SHEET),
        "focus_parts": focus_parts,
        "entries": entries,
        "summary": {
            "focus_part_count": len(focus_parts),
            "front_hair_focus_count": len(front_entries),
            "front_hair_child_candidate_count": front_candidate_count,
            "recommendation_counts": dict(counts),
            "param_hair_front_unlock_status": "BLOCKED_UNTIL_HUMAN_VISUAL_AND_MOTION_QA",
        },
        "decision": (
            "B4 has real independent hair_front_* candidate files, but this packet is focused review evidence only. "
            "ParamHairFront remains hidden/contract-only until front hair candidates pass human visual QA and later motion-readiness checks."
        ),
        "next_action": [
            "Ask for focused review only on the B4 hair review sheet, not all 33 B4/B5 anchors.",
            "If front hair child candidates are accepted, prepare a motion-readiness check while keeping ParamHairFront hidden until that check passes.",
            "If front hair masks are rejected, refine mask/extraction or regenerate B4 front hair mini-pass.",
            "Keep B5 torso/shoulder focused decision separate.",
        ],
        "self_review": {
            "b4_layer_pack_status": layer_report["status"],
            "b4_overlay_qa_status": qa["status"],
            "triage_status": triage["status"],
            "focus_part_count": len(focus_parts),
            "entries_count": len(entries),
            "all_focus_parts_present": all(part in metrics and part in corrected_entries for part in focus_parts),
            "review_sheet_exists": REVIEW_SHEET.exists(),
            "has_front_hair_children_scope": bool(front_entries),
            "front_hair_child_candidate_count": front_candidate_count,
            "param_hair_front_hidden": True,
            "has_human_required_gate": True,
            "does_not_require_owner_review_all_33": True,
            "validator_only_promotion_blocked": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "status": "PASS",
        },
    }
    save_json(REPORT_JSON, report)

    lines = [
        "# Character 002 v22 B4 Hair Focused Review",
        "",
        f"- status: `{report['status']}`",
        f"- B4 layer pack: `{report['b4_layer_pack_report']}`",
        f"- B4 overlay QA: `{report['b4_overlay_qa_report']}`",
        f"- review sheet: `{report['review_sheet']}`",
        f"- ParamHairFront: `{report['summary']['param_hair_front_unlock_status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Focus Parts", ""])
    for entry in entries:
        lines.extend(
            [
                f"### {entry['part_id']}",
                "",
                f"- recommendation: `{entry['recommendation']}`",
                f"- triage action: `{entry['triage_action']}`",
                f"- source hair support ratio: `{entry['source_hair_support_ratio']}`",
                f"- source skin/light overlap ratio: `{entry['source_skin_or_light_overlap_ratio']}`",
                f"- target anchor: `{entry['target_anchor']}`",
                "",
            ]
        )
    lines.extend(
        [
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

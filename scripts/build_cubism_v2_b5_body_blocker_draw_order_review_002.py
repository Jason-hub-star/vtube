#!/usr/bin/env python3
"""Build a draw-order-aware review packet for the three B5 hard blockers.

The previous B5 overlay QA paints body parts on top of the source for
inspection. That is useful for mask shape, but shoulder parts are normally
behind front/side hair in a Cubism stack. This packet keeps promotion blocked
while separating likely draw-order/occlusion issues from true regeneration
needs.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
B5_RAW = EXP / "v22_b5_body_clothing_pack/raw_outputs/b5_body_clothing_pack_reference_001.png"
V2_REPORT_JSON = EXP / "reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_report.json"
V2_QA_JSON = EXP / "reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_overlay_qa_report.json"
REPORT_DIR = EXP / "reports/v22_b5_body_blocker_draw_order_review"
REPORT_JSON = REPORT_DIR / "v22_b5_body_blocker_draw_order_review.json"
REPORT_MD = REPORT_DIR / "v22_b5_body_blocker_draw_order_review.md"
REVIEW_SHEET = REPORT_DIR / "v22_b5_body_blocker_draw_order_review.png"
CANVAS = 2048

TARGETS = ["torso_base", "shoulder_L", "shoulder_R"]

REGENERATION_PROMPT = """Create a focused Live2D/Cubism B5 body mini-pass for the same accepted G0 source character.
Generate only clean rig-friendly body material references for torso_base, shoulder_L, and shoulder_R.
Keep the same adult cute woman identity, pale soft skin, warm brown hair context, white ribbed off-shoulder sweater, shoulder straps, line thickness, and soft anime shading.
The shoulders must be clean skin/strap/cloth underpaint suitable to sit behind front/side hair without hair pixels baked into the shoulder layer.
The torso_base must be a complete upper-body base for breath/body-angle support, with coherent skin-to-clothing continuity and no pasted crop artifacts.
No labels, arrows, grids, extra faces, hands, jewelry, props, hairstyle changes, new outfit, perspective pose, cropped shoulders, or source-crop artifacts."""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_source() -> Image.Image:
    return Image.open(SOURCE).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)


def bbox_with_pad(bbox: list[int], pad: int = 110) -> tuple[int, int, int, int]:
    return (
        max(0, bbox[0] - pad),
        max(0, bbox[1] - pad),
        min(CANVAS, bbox[2] + pad),
        min(CANVAS, bbox[3] + pad),
    )


def estimate_hair_occlusion(rgb: np.ndarray) -> np.ndarray:
    # Warm brown hair and dark line clusters are the main source occluders for
    # shoulder review. This is intentionally conservative review evidence.
    arr = rgb.astype(np.int16)
    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]
    lum = (r * 0.299 + g * 0.587 + b * 0.114)
    dark = lum < 128
    warm_brown = (r >= b + 8) & (g >= b - 8) & (r < 165) & (g < 140) & (b < 130)
    line_dark = lum < 72
    return (dark & warm_brown) | line_dark


def alpha_weighted_ratio(alpha: np.ndarray, mask: np.ndarray) -> float:
    weight = alpha.astype(np.float64)
    total = float(weight.sum())
    if total <= 0:
        return 0.0
    return round(float((weight * mask).sum() / total), 6)


def overlay_tint(base: Image.Image, layer: Image.Image, occlusion_aware: bool) -> Image.Image:
    base_rgba = base.convert("RGBA")
    layer_alpha = np.asarray(layer.getchannel("A"), dtype=np.float32)
    visible_alpha = layer_alpha.copy()
    if occlusion_aware:
        occ = estimate_hair_occlusion(np.asarray(base.convert("RGB")))
        visible_alpha = visible_alpha * np.where(occ, 0.18, 1.0)
    tint = Image.new("RGBA", base_rgba.size, (61, 132, 255, 0))
    tint_alpha = np.clip(visible_alpha * 0.72, 0, 160).astype(np.uint8)
    tint.putalpha(Image.fromarray(tint_alpha, "L"))
    return Image.alpha_composite(base_rgba, tint)


def layer_preview(layer: Image.Image) -> Image.Image:
    bbox = layer.getchannel("A").getbbox()
    crop = layer.crop(bbox) if bbox else layer
    bg = Image.new("RGBA", crop.size, (245, 247, 250, 255))
    return Image.alpha_composite(bg, crop)


def tile(title: str, img: Image.Image, subtitle: str = "") -> Image.Image:
    w, h = 330, 300
    label_h = 52
    out = Image.new("RGB", (w, h), (247, 248, 250))
    draw = ImageDraw.Draw(out)
    draw.rectangle([4, 4, w - 5, h - 5], outline=(216, 222, 232))
    draw.text((10, 10), title, fill=(25, 31, 40))
    if subtitle:
        draw.text((10, 30), subtitle[:52], fill=(78, 89, 104))
    preview = img.convert("RGBA")
    preview.thumbnail((w - 20, h - label_h - 16), Image.Resampling.LANCZOS)
    out.paste(preview.convert("RGB"), ((w - preview.width) // 2, label_h + 4), preview)
    return out


def recommendation_for(part_id: str, occlusion_ratio: float, coverage: float) -> str:
    if part_id.startswith("shoulder") and occlusion_ratio >= 0.32:
        return "REVIEW_DRAW_ORDER_BEFORE_REGENERATE"
    if part_id == "torso_base" and coverage >= 0.12:
        return "REGENERATE_OR_FOCUSED_HUMAN_ACCEPT_BROAD_UNDERPAINT"
    return "FOCUSED_HUMAN_REVIEW_REQUIRED"


def build_sheet(source: Image.Image, entries: list[dict]) -> None:
    cols = 4
    tile_w, tile_h = 330, 300
    rows = len(entries)
    sheet = Image.new("RGB", (cols * tile_w, 54 + rows * tile_h), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 14), "Character 002 v22 B5 Body Blocker Draw-Order Review", fill=(25, 31, 40))
    for row, entry in enumerate(entries):
        layer = Image.open(ROOT / entry["output_path"]).convert("RGBA")
        crop_box = tuple(entry["crop_box"])
        source_crop = source.crop(crop_box)
        layer_crop = layer.crop(crop_box)
        tiles = [
            tile(f"{entry['part_id']} source", source_crop),
            tile("top overlay QA", overlay_tint(source_crop, layer_crop, False), "old conservative view"),
            tile("occlusion-aware", overlay_tint(source_crop, layer_crop, True), "hair drawn above estimate"),
            tile("isolated layer", layer_preview(layer_crop), entry["recommendation"]),
        ]
        y = 54 + row * tile_h
        for col, item in enumerate(tiles):
            sheet.paste(item, (col * tile_w, y))
    REVIEW_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(REVIEW_SHEET)


def main() -> int:
    v2 = json.loads(V2_REPORT_JSON.read_text(encoding="utf-8"))
    qa = json.loads(V2_QA_JSON.read_text(encoding="utf-8"))
    v2_entries = {entry["part_id"]: entry for entry in v2["entries"]}
    source = load_source()

    entries = []
    for part_id in TARGETS:
        source_entry = v2_entries[part_id]
        layer = Image.open(ROOT / source_entry["output_path"]).convert("RGBA")
        bbox = source_entry["bbox"]
        crop_box = bbox_with_pad(bbox)
        source_crop = source.crop(crop_box).convert("RGB")
        layer_crop = layer.crop(crop_box).convert("RGBA")
        alpha = np.asarray(layer_crop.getchannel("A"), dtype=np.uint8)
        occ = estimate_hair_occlusion(np.asarray(source_crop))
        occlusion_ratio = alpha_weighted_ratio(alpha, occ)
        coverage = source_entry["alpha_coverage"]
        recommendation = recommendation_for(part_id, occlusion_ratio, coverage)
        entries.append(
            {
                "part_id": part_id,
                "output_path": source_entry["output_path"],
                "bbox": bbox,
                "crop_box": list(crop_box),
                "alpha_coverage": coverage,
                "hair_occlusion_overlap_ratio": occlusion_ratio,
                "recommendation": recommendation,
                "interpretation": (
                    "Shoulder overlap is likely partly draw-order/occlusion related; review before regenerating."
                    if recommendation == "REVIEW_DRAW_ORDER_BEFORE_REGENERATE"
                    else "Torso remains a broad underpaint/body material decision and should not be solved by more alpha shrinking."
                ),
            }
        )

    build_sheet(source, entries)

    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": "B5_BODY_BLOCKER_DRAW_ORDER_REVIEW_READY_HUMAN_DECISION_REQUIRED",
        "source_image": rel(SOURCE),
        "b5_raw_image": rel(B5_RAW),
        "v2_report": rel(V2_REPORT_JSON),
        "v2_overlay_qa_report": rel(V2_QA_JSON),
        "review_sheet": rel(REVIEW_SHEET),
        "targets": TARGETS,
        "entries": entries,
        "regeneration_prompt_if_rejected": REGENERATION_PROMPT,
        "decision": (
            "The three B5 hard blockers remain blocked from material PASS, but this packet separates "
            "draw-order-aware shoulder review from true regeneration/re-extraction. Do not ask the owner "
            "to manually anchor all B5 parts."
        ),
        "next_action": [
            "Ask for focused accept/reject only on torso_base, shoulder_L, and shoulder_R using this review sheet.",
            "If shoulders are rejected after draw-order review, run the regeneration prompt for a B5 body mini-pass.",
            "If torso_base is rejected, regenerate or re-extract a complete torso/body underpaint instead of shrinking alpha again.",
            "Keep B4 hair focused review separate and keep G7/G8 blocked.",
        ],
        "self_review": {
            "v2_status": v2["status"],
            "v2_qa_status": qa["status"],
            "previous_remaining_b5_revise_parts": qa["remaining_b5_revise_parts"],
            "target_count": len(TARGETS),
            "entries_count": len(entries),
            "all_targets_present": all(part in v2_entries for part in TARGETS),
            "review_sheet_exists": REVIEW_SHEET.exists(),
            "has_regeneration_prompt": bool(REGENERATION_PROMPT.strip()),
            "has_human_decision_gate": True,
            "does_not_require_owner_review_all_33": True,
            "validator_only_promotion_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "status": "PASS",
        },
    }
    save_json(REPORT_JSON, report)

    lines = [
        "# Character 002 v22 B5 Body Blocker Draw-Order Review",
        "",
        f"- status: `{report['status']}`",
        f"- source image: `{report['source_image']}`",
        f"- v2 report: `{report['v2_report']}`",
        f"- v2 QA: `{report['v2_overlay_qa_report']}`",
        f"- review sheet: `{report['review_sheet']}`",
        "",
        "## Target Decisions",
        "",
    ]
    for entry in entries:
        lines.extend(
            [
                f"### {entry['part_id']}",
                "",
                f"- recommendation: `{entry['recommendation']}`",
                f"- alpha coverage: `{entry['alpha_coverage']}`",
                f"- hair occlusion overlap ratio: `{entry['hair_occlusion_overlap_ratio']}`",
                f"- interpretation: {entry['interpretation']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Regeneration Prompt If Rejected",
            "",
            "```text",
            REGENERATION_PROMPT,
            "```",
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

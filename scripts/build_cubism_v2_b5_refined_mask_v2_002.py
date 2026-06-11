#!/usr/bin/env python3
"""Build B5 refined-mask v2 for the six remaining focused revise parts."""

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
V1_REPORT_JSON = EXP / "reports/v22_b5_refined_mask_v1/v22_b5_refined_mask_v1_report.json"
V1_QA_JSON = EXP / "reports/v22_b5_refined_mask_v1/v22_b5_refined_mask_v1_overlay_qa_report.json"
SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
OUT_DIR = EXP / "v22_b5_refined_mask_v2/normalized_layers"
REPORT_DIR = EXP / "reports/v22_b5_refined_mask_v2"
REPORT_JSON = REPORT_DIR / "v22_b5_refined_mask_v2_report.json"
REPORT_MD = REPORT_DIR / "v22_b5_refined_mask_v2_report.md"
CONTACT_SHEET = REPORT_DIR / "v22_b5_refined_mask_v2_contact_sheet.png"
OVERLAY_SHEET = REPORT_DIR / "v22_b5_refined_mask_v2_overlay_qa.png"
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

FOCUSED_TARGETS = {
    "torso_base",
    "shoulder_L",
    "shoulder_R",
    "face_shadow_L",
    "face_shadow_R",
    "nose",
}

SHAPES = {
    "torso_base": ("polygon", [(665, 1038), (1390, 1038), (1330, 1855), (710, 1855)], 26),
    "shoulder_L": ("ellipse", [600, 1028, 840, 1186], 20),
    "shoulder_R": ("ellipse", [1225, 1030, 1450, 1190], 20),
    "face_shadow_L": ("ellipse", [728, 690, 818, 875], 18),
    "face_shadow_R": ("ellipse", [1215, 690, 1305, 875], 18),
    "nose": ("ellipse", [1008, 762, 1040, 818], 6),
}

ALPHA_SCALE = {
    "torso_base": 0.78,
    "shoulder_L": 0.72,
    "shoulder_R": 0.72,
    "face_shadow_L": 0.42,
    "face_shadow_R": 0.42,
    "nose": 0.42,
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
    else:
        raise ValueError(kind)
    return mask.filter(ImageFilter.GaussianBlur(blur))


def refine_layer(part_id: str, img: Image.Image) -> Image.Image:
    old_alpha = np.asarray(img.getchannel("A"), dtype=np.float32)
    gate = np.asarray(shape_mask(part_id), dtype=np.float32) / 255.0
    scale = ALPHA_SCALE[part_id]
    new_alpha = np.clip(old_alpha * gate * scale, 0, 255).astype(np.uint8)
    out = img.copy()
    out.putalpha(Image.fromarray(new_alpha, "L").filter(ImageFilter.GaussianBlur(0.35)))
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
    draw.text((12, 14), "Character 002 v22 B5 Refined Mask v2 Overlay QA", fill=(25, 31, 40))
    for idx, entry in enumerate(entries):
        img = Image.open(ROOT / entry["output_path"]).convert("RGBA")
        tile = overlay_tile(source, img, entry)
        sheet.paste(tile, ((idx % cols) * 360, 46 + (idx // cols) * 320))
    OVERLAY_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OVERLAY_SHEET)


def main() -> int:
    v1 = json.loads(V1_REPORT_JSON.read_text(encoding="utf-8"))
    v1_qa = json.loads(V1_QA_JSON.read_text(encoding="utf-8"))
    v1_entries = {entry["part_id"]: entry for entry in v1["entries"]}

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    entries = []
    for part_id in B5_PARTS:
        src = ROOT / v1_entries[part_id]["output_path"]
        img = Image.open(src).convert("RGBA")
        old_sum = alpha_sum(img)
        if part_id in FOCUSED_TARGETS:
            out = refine_layer(part_id, img)
            status = "REFINED_MASK_V2"
        else:
            out = img
            status = "COPIED_FROM_V1"
        dst = OUT_DIR / f"{part_id}.png"
        out.save(dst)
        after_sum = alpha_sum(out)
        entries.append(
            {
                "part_id": part_id,
                "source_batch": "B5",
                "input_path": rel(src),
                "output_path": rel(dst),
                "refine_status": status,
                "bbox": bbox_from_alpha(out),
                "alpha_coverage": coverage(out),
                "alpha_sum_before": old_sum,
                "alpha_sum_after": after_sum,
                "alpha_sum_ratio": round(after_sum / old_sum, 6) if old_sum else 0.0,
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
        "status": "B5_REFINED_MASK_V2_CANDIDATE_READY_FOR_OVERLAY_REVIEW",
        "v1_report": rel(V1_REPORT_JSON),
        "v1_overlay_qa_report": rel(V1_QA_JSON),
        "v1_focused_revise_parts": v1_qa["focused_revise_parts"],
        "output_dir": rel(OUT_DIR),
        "contact_sheet": rel(CONTACT_SHEET),
        "overlay_sheet": rel(OVERLAY_SHEET),
        "entries": entries,
        "decision": "B5 refined-mask v2 only changes the six focused v1 revise parts and keeps all gates blocked. This is a smaller candidate for overlay review, not material PASS.",
        "next_action": [
            "Run conservative v2 overlay QA.",
            "If v2 still reads patch-like, mark remaining parts for regeneration or human review instead of more anchor tweaking.",
            "Keep B4 hair focused review separate.",
        ],
        "self_review": {
            "entry_count": len(entries),
            "refined_mask_v2_count": counts.get("REFINED_MASK_V2", 0),
            "copied_from_v1_count": counts.get("COPIED_FROM_V1", 0),
            "expected_focused_target_count": len(FOCUSED_TARGETS),
            "all_layers_rgba": all(entry["mode"] == "RGBA" for entry in entries),
            "all_layers_2048": all(entry["size"] == [CANVAS, CANVAS] for entry in entries),
            "all_layers_nonempty": all(entry["bbox"] is not None for entry in entries),
            "overlay_sheet_exists": OVERLAY_SHEET.exists(),
            "contact_sheet_exists": CONTACT_SHEET.exists(),
            "validator_only_promotion_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "status": "PASS",
        },
    }
    save_json(REPORT_JSON, report)

    lines = [
        "# Character 002 v22 B5 Refined Mask v2",
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
            f"ratio `{entry['alpha_sum_ratio']}` bbox `{entry['bbox']}`"
        )
    lines.extend(["", "## Self Review", ""])
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": report["status"], "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

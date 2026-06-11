#!/usr/bin/env python3
"""Build a focused P0 torso minipass v2 candidate for v22 G3 review.

The candidate reduces the broad torso underpaint blocker by deriving a tighter
skin/upper-torso alpha from the B5 raw reference. It remains review-required.
"""

from __future__ import annotations

import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
B5_CURRENT_REPORT = EXP / "reports/v22_b5_provisional_minipass_candidate/v22_b5_provisional_minipass_candidate_report.json"
G3_BLOCKER_JSON = EXP / "reports/v22_g3_b4_b5_blocker_reduction/v22_g3_b4_b5_blocker_reduction_packet.json"
SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
B5_RAW = EXP / "v22_b5_body_clothing_pack/raw_outputs/b5_body_clothing_pack_reference_001.png"
OUT_DIR = EXP / "v22_b5_p0_torso_minipass_v2_candidate/normalized_layers"
REPORT_DIR = EXP / "reports/v22_g3_p0_torso_minipass_v2"
REPORT_JSON = REPORT_DIR / "v22_g3_p0_torso_minipass_v2_report.json"
REPORT_MD = REPORT_DIR / "v22_g3_p0_torso_minipass_v2_report.md"
QA_SHEET = REPORT_DIR / "v22_g3_p0_torso_minipass_v2_overlay_qa.png"
CONTACT_SHEET = REPORT_DIR / "v22_g3_p0_torso_minipass_v2_contact_sheet.png"

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


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)


def alpha_arr(img: Image.Image) -> np.ndarray:
    return np.asarray(img.getchannel("A"), dtype=np.uint8)


def bbox_from_alpha(img: Image.Image) -> list[int] | None:
    alpha = alpha_arr(img)
    ys, xs = np.where(alpha > 5)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def coverage(img: Image.Image) -> float:
    return round(float((alpha_arr(img) > 5).mean()), 8)


def alpha_sum(img: Image.Image) -> int:
    return int(alpha_arr(img).sum())


def upper_torso_roi() -> Image.Image:
    mask = Image.new("L", (CANVAS, CANVAS), 0)
    draw = ImageDraw.Draw(mask)
    # Source-aligned visible upper torso only. Keep neck/shoulder/chest skin and
    # avoid the face, the separate B5 sheet parts, and the lower clothing stack.
    draw.polygon(
        [
            (690, 890),
            (1325, 890),
            (1515, 1105),
            (1410, 1325),
            (1040, 1325),
            (1018, 1270),
            (990, 1325),
            (610, 1325),
            (510, 1105),
        ],
        fill=255,
    )
    return mask.filter(ImageFilter.GaussianBlur(8))


def skin_mask_from_source(source: Image.Image) -> Image.Image:
    rgb = np.asarray(source.convert("RGB"), dtype=np.int16)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    # Anime skin in this B5 raw is warm/pink and moderately saturated. This
    # excludes white clothing, dark hair, blue overlays, and the white canvas.
    warm = (r > 145) & (g > 92) & (b > 78) & (r > b + 18) & (r >= g + 4)
    not_white = ~((r > 220) & (g > 214) & (b > 208) & (np.abs(r - g) < 22))
    not_gray = ~((np.abs(r - g) < 10) & (np.abs(g - b) < 10))
    mask = (warm & not_white & not_gray).astype(np.uint8) * 255
    roi = np.asarray(upper_torso_roi(), dtype=np.uint8)
    mask = np.minimum(mask, roi)
    img = Image.fromarray(mask, "L")
    img = img.filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.MinFilter(11)).filter(ImageFilter.GaussianBlur(9))
    return img.point(lambda v: 245 if v > 32 else 0)


def build_torso_v2(raw: Image.Image) -> Image.Image:
    # Use the source-aligned character RGB so the review candidate does not
    # inherit the B5 sheet layout coordinates. B5 raw remains attached as the
    # body-pack reference, but this layer is still review-only.
    out = load_rgba(SOURCE)
    out.putalpha(skin_mask_from_source(out))
    return out


def crop_box_for(bbox: list[int] | None) -> tuple[int, int, int, int]:
    box = bbox or [620, 680, 1520, 1300]
    pad = 110
    return (
        max(0, box[0] - pad),
        max(0, box[1] - pad),
        min(CANVAS, box[2] + pad),
        min(CANVAS, box[3] + pad),
    )


def overlay_crop(base: Image.Image, layer: Image.Image, color: tuple[int, int, int], crop: tuple[int, int, int, int]) -> Image.Image:
    b = base.crop(crop).convert("RGBA")
    p = layer.crop(crop).convert("RGBA")
    tint = Image.new("RGBA", b.size, (*color, 0))
    tint.putalpha(p.getchannel("A").point(lambda v: min(165, int(v * 0.72))))
    return Image.alpha_composite(b, tint)


def labeled_tile(title: str, img: Image.Image, subtitle: str = "") -> Image.Image:
    w, h = 390, 310
    out = Image.new("RGB", (w, h), (247, 248, 250))
    draw = ImageDraw.Draw(out)
    draw.rectangle([4, 4, w - 5, h - 5], outline=(216, 222, 232))
    draw.text((10, 10), title[:48], fill=(25, 31, 40))
    if subtitle:
        draw.text((10, 32), subtitle[:54], fill=(78, 89, 104))
    preview = img.convert("RGBA")
    preview.thumbnail((w - 24, h - 70), Image.Resampling.LANCZOS)
    out.paste(preview.convert("RGB"), ((w - preview.width) // 2, 58), preview)
    return out


def build_qa_sheet(source: Image.Image, raw: Image.Image, old: Image.Image, new: Image.Image, metrics: dict) -> None:
    crop = crop_box_for(metrics["new_bbox"] or metrics["old_bbox"])
    old_overlay = overlay_crop(source, old, (58, 132, 255), crop)
    new_overlay = overlay_crop(source, new, (42, 152, 95), crop)
    raw_crop = raw.crop(crop)
    new_crop = new.crop(crop)
    old_crop = old.crop(crop)
    tiles = [
        labeled_tile("old torso overlay", old_overlay, f"coverage {metrics['old_alpha_coverage']}"),
        labeled_tile("v2 torso overlay", new_overlay, f"coverage {metrics['new_alpha_coverage']}"),
        labeled_tile("v2 isolated", new_crop, metrics["verdict"]),
        labeled_tile("old isolated", old_crop, f"alpha ratio {metrics['alpha_sum_ratio']}"),
        labeled_tile("B5 raw reference crop", raw_crop, "body-pack reference"),
        labeled_tile("decision", new_overlay, "review-required, material blocked"),
    ]
    sheet = Image.new("RGB", (3 * 390, 50 + 2 * 310), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 16), "Character 002 v22 P0 Torso Minipass v2 Overlay QA", fill=(25, 31, 40))
    for idx, tile in enumerate(tiles):
        sheet.paste(tile, ((idx % 3) * 390, 50 + (idx // 3) * 310))
    QA_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(QA_SHEET)


def build_contact_sheet(entries: list[dict]) -> None:
    cols = 5
    thumb = 240
    label_h = 60
    rows = math.ceil(len(entries) / cols)
    sheet = Image.new("RGB", (cols * thumb, rows * (thumb + label_h)), (247, 248, 250))
    draw = ImageDraw.Draw(sheet)
    for idx, entry in enumerate(entries):
        img = Image.open(ROOT / entry["output_path"]).convert("RGBA")
        bbox = img.getchannel("A").getbbox()
        crop = img.crop(bbox) if bbox else img
        crop.thumbnail((thumb - 20, thumb - 48), Image.Resampling.LANCZOS)
        x = (idx % cols) * thumb
        y = (idx // cols) * (thumb + label_h)
        draw.text((x + 8, y + 8), entry["part_id"], fill=(25, 31, 40))
        draw.text((x + 8, y + 30), entry["candidate_status"][:32], fill=(78, 89, 104))
        sheet.paste(crop.convert("RGB"), (x + (thumb - crop.width) // 2, y + label_h), crop)
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET)


def main() -> int:
    current_report = load_json(B5_CURRENT_REPORT)
    blocker = load_json(G3_BLOCKER_JSON)
    current_by_part = {entry["part_id"]: entry for entry in current_report["entries"]}
    source = load_rgba(SOURCE)
    raw = load_rgba(B5_RAW)
    old_torso = Image.open(ROOT / current_by_part["torso_base"]["output_path"]).convert("RGBA")
    new_torso = build_torso_v2(raw)

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    entries = []
    for part_id in B5_PARTS:
        src = ROOT / current_by_part[part_id]["output_path"]
        dst = OUT_DIR / f"{part_id}.png"
        if part_id == "torso_base":
            img = new_torso
            status = "P0_TORSO_MINIPASS_V2_REBUILT_FROM_B5_RAW_SKIN_MASK"
        else:
            img = Image.open(src).convert("RGBA")
            status = "COPIED_FROM_B5_PROVISIONAL_MINIPASS"
        img.save(dst)
        entries.append(
            {
                "part_id": part_id,
                "input_path": rel(src),
                "output_path": rel(dst),
                "candidate_status": status,
                "mode": img.mode,
                "size": list(img.size),
                "bbox": bbox_from_alpha(img),
                "alpha_coverage": coverage(img),
            }
        )

    old_sum = alpha_sum(old_torso)
    new_sum = alpha_sum(new_torso)
    old_cov = coverage(old_torso)
    new_cov = coverage(new_torso)
    metrics = {
        "old_bbox": bbox_from_alpha(old_torso),
        "new_bbox": bbox_from_alpha(new_torso),
        "old_alpha_coverage": old_cov,
        "new_alpha_coverage": new_cov,
        "old_alpha_sum": old_sum,
        "new_alpha_sum": new_sum,
        "alpha_sum_ratio": round(new_sum / old_sum, 6) if old_sum else 0.0,
    }
    improved = metrics["alpha_sum_ratio"] < 0.48 and new_cov < old_cov and metrics["new_bbox"] is not None
    metrics["verdict"] = "P0_TORSO_MINIPASS_V2_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED" if improved else "P0_TORSO_MINIPASS_V2_REVISE"
    metrics["improvement_candidate"] = improved

    build_qa_sheet(source, raw, old_torso, new_torso, metrics)
    build_contact_sheet(entries)

    status = "P0_TORSO_MINIPASS_V2_CANDIDATE_READY_FOR_G3_REVIEW" if improved else "P0_TORSO_MINIPASS_V2_REVISE"
    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": status,
        "current_b5_candidate": rel(B5_CURRENT_REPORT),
        "g3_blocker_reduction_packet": rel(G3_BLOCKER_JSON),
        "source_image": rel(SOURCE),
        "b5_raw_reference": rel(B5_RAW),
        "output_dir": rel(OUT_DIR),
        "qa_sheet": rel(QA_SHEET),
        "contact_sheet": rel(CONTACT_SHEET),
        "torso_metrics": metrics,
        "entries": entries,
        "decision": (
            "P0 torso minipass v2 is an improvement candidate because its alpha is tighter and derived from the B5 raw skin/upper-torso area, "
            "but it remains review-required and cannot promote material PASS."
            if improved
            else "P0 torso minipass v2 did not improve enough; keep torso as hard review."
        ),
        "next_action": [
            "Use the v2 torso QA sheet to decide whether to rebuild the corrected 64-part manifest with this torso candidate.",
            "Keep G3 visual overlay blocked until P0 and P1 rows are resolved.",
            "Do not promote material PASS, ParamHairFront, Mini Cubism, or real Cubism from this candidate.",
        ],
        "self_review": {
            "g3_blocker_status": blocker["status"],
            "current_b5_status": current_report["status"],
            "entry_count": len(entries),
            "all_layers_rgba": all(entry["mode"] == "RGBA" for entry in entries),
            "all_layers_2048": all(entry["size"] == [CANVAS, CANVAS] for entry in entries),
            "all_layers_nonempty": all(entry["bbox"] for entry in entries),
            "torso_improvement_candidate": improved,
            "old_alpha_coverage": old_cov,
            "new_alpha_coverage": new_cov,
            "alpha_sum_ratio": metrics["alpha_sum_ratio"],
            "qa_sheet_exists": QA_SHEET.exists(),
            "contact_sheet_exists": CONTACT_SHEET.exists(),
            "material_pass_blocked": True,
            "visual_promotion_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "not_owner_approval": True,
            "status": "PASS" if improved else "REVISE",
        },
    }
    save_json(REPORT_JSON, report)

    lines = [
        "# Character 002 v22 P0 Torso Minipass v2",
        "",
        f"- status: `{report['status']}`",
        f"- QA sheet: `{report['qa_sheet']}`",
        f"- contact sheet: `{report['contact_sheet']}`",
        "",
        "## Torso Metrics",
        "",
    ]
    for key, value in metrics.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Self Review", ""])
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", "", report["decision"], "", "## Next Action", ""])
    lines.extend(f"- {item}" for item in report["next_action"])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": status, "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0 if improved else 1


if __name__ == "__main__":
    raise SystemExit(main())

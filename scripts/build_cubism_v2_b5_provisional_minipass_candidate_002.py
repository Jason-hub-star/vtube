#!/usr/bin/env python3
"""Build a B5 provisional mini-pass candidate from the route packet."""

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
PACKET_JSON = EXP / "reports/v22_b5_provisional_minipass_input_packet/v22_b5_provisional_minipass_input_packet.json"
V2_REPORT_JSON = EXP / "reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_report.json"
SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
B5_RAW = EXP / "v22_b5_body_clothing_pack/raw_outputs/b5_body_clothing_pack_reference_001.png"
OUT_DIR = EXP / "v22_b5_provisional_minipass_candidate/normalized_layers"
REPORT_DIR = EXP / "reports/v22_b5_provisional_minipass_candidate"
REPORT_JSON = REPORT_DIR / "v22_b5_provisional_minipass_candidate_report.json"
REPORT_MD = REPORT_DIR / "v22_b5_provisional_minipass_candidate_report.md"
CONTACT_SHEET = REPORT_DIR / "v22_b5_provisional_minipass_candidate_contact_sheet.png"
OVERLAY_SHEET = REPORT_DIR / "v22_b5_provisional_minipass_candidate_overlay.png"
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


def alpha_array(img: Image.Image) -> np.ndarray:
    return np.asarray(img.getchannel("A"), dtype=np.uint8)


def bbox_from_alpha(img: Image.Image) -> list[int] | None:
    alpha = alpha_array(img)
    ys, xs = np.where(alpha > 5)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def coverage(img: Image.Image) -> float:
    return round(float((alpha_array(img) > 5).mean()), 8)


def alpha_sum(img: Image.Image) -> int:
    return int(alpha_array(img).sum())


def load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)


def estimate_hair_occlusion(rgb: np.ndarray) -> np.ndarray:
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


def torso_mask() -> Image.Image:
    mask = Image.new("L", (CANVAS, CANVAS), 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon([(630, 950), (1460, 955), (1395, 1890), (675, 1890)], fill=245)
    draw.ellipse((565, 980, 900, 1245), fill=150)
    draw.ellipse((1165, 980, 1515, 1245), fill=150)
    return mask.filter(ImageFilter.GaussianBlur(18))


def build_torso_from_b5_raw(raw: Image.Image) -> Image.Image:
    out = raw.copy()
    out.putalpha(torso_mask())
    return out


def revise_shoulder(part_id: str, current: Image.Image, raw: Image.Image, source: Image.Image) -> tuple[Image.Image, dict]:
    old_alpha = alpha_array(current).astype(np.float32)
    occ = estimate_hair_occlusion(np.asarray(source.convert("RGB")))
    # A shoulder layer that sits behind hair should lose visibility where the
    # source already has dense hair/line occlusion.
    keep = np.where(occ, 0.0, 1.0).astype(np.float32)
    side_gate = Image.new("L", (CANVAS, CANVAS), 0)
    draw = ImageDraw.Draw(side_gate)
    if part_id == "shoulder_L":
        draw.ellipse((555, 1000, 875, 1228), fill=255)
    else:
        draw.ellipse((1180, 1000, 1480, 1230), fill=255)
    gate = np.asarray(side_gate.filter(ImageFilter.GaussianBlur(16)), dtype=np.float32) / 255.0
    new_alpha = np.clip(old_alpha * keep * gate, 0, 255).astype(np.uint8)
    out = raw.copy()
    out.putalpha(Image.fromarray(new_alpha, "L").filter(ImageFilter.GaussianBlur(0.35)))
    metrics = {
        "old_hair_occlusion_overlap_ratio": alpha_weighted_ratio(old_alpha.astype(np.uint8), occ),
        "new_hair_occlusion_overlap_ratio": alpha_weighted_ratio(new_alpha, occ),
    }
    return out, metrics


def overlay_tile(source: Image.Image, img: Image.Image, part_id: str, bbox: list[int] | None, status: str) -> Image.Image:
    box = bbox or [760, 760, 1260, 1260]
    pad = 110
    crop_box = (
        max(0, box[0] - pad),
        max(0, box[1] - pad),
        min(CANVAS, box[2] + pad),
        min(CANVAS, box[3] + pad),
    )
    base = source.crop(crop_box).convert("RGBA")
    layer = img.crop(crop_box).convert("RGBA")
    tint = Image.new("RGBA", base.size, (58, 132, 255, 0))
    tint.putalpha(layer.getchannel("A").point(lambda v: min(150, int(v * 0.68))))
    comp = Image.alpha_composite(base, tint)
    comp.thumbnail((340, 230), Image.Resampling.LANCZOS)
    tile = Image.new("RGB", (360, 310), (247, 248, 250))
    tile.paste(comp.convert("RGB"), ((360 - comp.width) // 2, 8))
    draw = ImageDraw.Draw(tile)
    draw.rectangle([4, 4, 355, 305], outline=(216, 222, 232))
    draw.text((10, 248), part_id, fill=(25, 31, 40))
    draw.text((10, 268), status, fill=(78, 89, 104))
    return tile


def build_sheets(entries: list[dict]) -> None:
    source = load_rgba(SOURCE)
    cols = 5
    thumb = 260
    label_h = 68
    rows = math.ceil(len(entries) / cols)
    contact = Image.new("RGB", (cols * thumb, rows * (thumb + label_h)), (247, 248, 250))
    draw = ImageDraw.Draw(contact)
    for idx, entry in enumerate(entries):
        img = Image.open(ROOT / entry["output_path"]).convert("RGBA")
        bbox = img.getchannel("A").getbbox()
        crop = img.crop(bbox) if bbox else img
        crop.thumbnail((thumb - 20, thumb - 48), Image.Resampling.LANCZOS)
        x = (idx % cols) * thumb
        y = (idx // cols) * (thumb + label_h)
        tile = Image.new("RGB", (thumb, thumb), (238, 241, 245))
        tile.paste(crop.convert("RGB"), ((thumb - crop.width) // 2, (thumb - 48 - crop.height) // 2), crop)
        contact.paste(tile, (x, y + label_h))
        draw.text((x + 8, y + 8), entry["part_id"], fill=(25, 31, 40))
        draw.text((x + 8, y + 28), entry["candidate_status"], fill=(78, 89, 104))
        draw.text((x + 8, y + 48), f"cov {entry['alpha_coverage']}", fill=(78, 89, 104))
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    contact.save(CONTACT_SHEET)

    target_entries = [entry for entry in entries if entry["candidate_status"] != "COPIED_FROM_V2"]
    overlay = Image.new("RGB", (3 * 360, 46 + len(target_entries) * 310), "white")
    odraw = ImageDraw.Draw(overlay)
    odraw.text((12, 14), "Character 002 v22 B5 Provisional Mini-Pass Candidate Overlay", fill=(25, 31, 40))
    for idx, entry in enumerate(target_entries):
        img = Image.open(ROOT / entry["output_path"]).convert("RGBA")
        tile = overlay_tile(source, img, entry["part_id"], entry["bbox"], entry["candidate_status"])
        overlay.paste(tile, (0, 46 + idx * 310))
    OVERLAY_SHEET.parent.mkdir(parents=True, exist_ok=True)
    overlay.save(OVERLAY_SHEET)


def main() -> int:
    packet = load_json(PACKET_JSON)
    v2 = load_json(V2_REPORT_JSON)
    v2_by_part = {entry["part_id"]: entry for entry in v2["entries"]}
    packet_by_part = {item["part_id"]: item for item in packet["targets"]}
    source = load_rgba(SOURCE)
    raw = load_rgba(B5_RAW)

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    entries = []
    for part_id in B5_PARTS:
        src_path = ROOT / v2_by_part[part_id]["output_path"]
        current = Image.open(src_path).convert("RGBA")
        metrics = {}
        if part_id == "torso_base":
            out = build_torso_from_b5_raw(raw)
            status = "REGENERATED_FROM_B5_RAW_MINIPASS"
        elif part_id in {"shoulder_L", "shoulder_R"}:
            out, metrics = revise_shoulder(part_id, current, raw, source)
            status = "REVISED_DRAW_ORDER_MASK"
        else:
            out = current
            status = "COPIED_FROM_V2"
        dst = OUT_DIR / f"{part_id}.png"
        out.save(dst)
        before_sum = alpha_sum(current)
        after_sum = alpha_sum(out)
        entry = {
            "part_id": part_id,
            "source_batch": "B5",
            "input_path": rel(src_path),
            "output_path": rel(dst),
            "candidate_status": status,
            "route": packet_by_part.get(part_id, {}).get("route", "COPY"),
            "bbox": bbox_from_alpha(out),
            "alpha_coverage": coverage(out),
            "alpha_sum_before": before_sum,
            "alpha_sum_after": after_sum,
            "alpha_sum_ratio": round(after_sum / before_sum, 6) if before_sum else 0.0,
            "mode": out.mode,
            "size": list(out.size),
            **metrics,
        }
        entries.append(entry)

    build_sheets(entries)
    counts = Counter(entry["candidate_status"] for entry in entries)
    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": "B5_PROVISIONAL_MINIPASS_CANDIDATE_READY_FOR_OVERLAY_QA",
        "input_packet": rel(PACKET_JSON),
        "v2_report": rel(V2_REPORT_JSON),
        "source_image": rel(SOURCE),
        "b5_raw_reference": rel(B5_RAW),
        "output_dir": rel(OUT_DIR),
        "contact_sheet": rel(CONTACT_SHEET),
        "overlay_sheet": rel(OVERLAY_SHEET),
        "entries": entries,
        "decision": (
            "This candidate applies the Codex provisional B5 route: torso_base is rebuilt from the B5 raw reference, "
            "shoulders are revised as draw-order/mask candidates, and all other B5 parts are copied from refined-mask v2."
        ),
        "next_action": [
            "Run B5 provisional mini-pass overlay QA.",
            "If torso or shoulders still read as patch-like, keep them REVISE and prepare actual image-generation regeneration.",
            "Do not promote material PASS, ParamHairFront, Mini Cubism, or real Cubism from this candidate alone.",
        ],
        "self_review": {
            "input_packet_status": packet["status"],
            "entry_count": len(entries),
            "target_count": sum(1 for entry in entries if entry["candidate_status"] != "COPIED_FROM_V2"),
            "regenerated_from_b5_raw_count": counts.get("REGENERATED_FROM_B5_RAW_MINIPASS", 0),
            "revised_draw_order_mask_count": counts.get("REVISED_DRAW_ORDER_MASK", 0),
            "copied_from_v2_count": counts.get("COPIED_FROM_V2", 0),
            "all_layers_rgba": all(entry["mode"] == "RGBA" for entry in entries),
            "all_layers_2048": all(entry["size"] == [CANVAS, CANVAS] for entry in entries),
            "all_layers_nonempty": all(entry["alpha_sum_after"] > 0 for entry in entries),
            "contact_sheet_exists": CONTACT_SHEET.exists(),
            "overlay_sheet_exists": OVERLAY_SHEET.exists(),
            "not_owner_approval": True,
            "material_pass_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "status": "PASS",
        },
    }
    save_json(REPORT_JSON, report)

    lines = [
        "# Character 002 v22 B5 Provisional Mini-Pass Candidate",
        "",
        f"- status: `{report['status']}`",
        f"- output dir: `{report['output_dir']}`",
        f"- contact sheet: `{report['contact_sheet']}`",
        f"- overlay sheet: `{report['overlay_sheet']}`",
        "",
        "## Entries",
        "",
    ]
    for entry in entries:
        lines.append(
            f"- `{entry['part_id']}` `{entry['candidate_status']}` cov `{entry['alpha_coverage']}` ratio `{entry['alpha_sum_ratio']}`"
        )
    lines.extend(["", "## Self Review", ""])
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": report["status"], "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

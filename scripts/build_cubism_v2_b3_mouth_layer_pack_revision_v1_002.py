#!/usr/bin/env python3
"""Build a v22 B3 mouth extraction revision from coherent mouth-state crops.

Revision v1 preserves the failed first extraction evidence and writes to a
separate folder. It uses only the newly generated B3 raw sheet, deriving mouth
internals from the same wide-mouth crop so teeth/tongue/inner stay aligned.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
B1_RAW = EXP / "v22_b1_clean_base_underpaint/raw_outputs/b1_clean_base_underpaint_reference_001.png"
B3_RAW = EXP / "v22_b3_mouth_pack/raw_outputs/b3_mouth_pack_reference_001.png"
RAW_REVIEW_JSON = EXP / "reports/v22_b3_mouth_pack/v22_b3_mouth_pack_review.json"
PREV_OVERLAY_JSON = EXP / "reports/v22_b3_mouth_pack/v22_b3_overlay_qa_report.json"
OUT_ROOT = EXP / "v22_b3_mouth_pack_revision_v1"
LAYERS_DIR = OUT_ROOT / "normalized_layers"
REPORT_DIR = EXP / "reports/v22_b3_mouth_pack_revision_v1"
REPORT_JSON = REPORT_DIR / "v22_b3_revision_v1_layer_pack_report.json"
REPORT_MD = REPORT_DIR / "v22_b3_revision_v1_layer_pack_report.md"
CONTACT_SHEET = REPORT_DIR / "v22_b3_revision_v1_layer_pack_contact_sheet.png"
OVERLAY_SHEET = REPORT_DIR / "v22_b3_revision_v1_overlay_qa.png"
CANVAS = 2048

B3_EXPECTED_OUTPUTS = [
    "mouth_line",
    "mouth_inner",
    "mouth_upper_lip_mask",
    "mouth_lower_lip_mask",
    "mouth_teeth",
    "mouth_tongue",
    "mouth_corner_L",
    "mouth_corner_R",
    "mouth_closed_smile_reference",
    "mouth_small_open_reference",
    "mouth_mid_teeth_reference",
    "mouth_wide_teeth_tongue_reference",
]

# Raw-sheet global crop boxes. These target coherent mouth drawings in the top
# four expression panels, not the isolated helper-like component row.
MOUTH_STATE_BOXES = {
    "closed": (238, 230, 420, 306),
    "small": (820, 218, 1045, 330),
    "mid": (195, 625, 465, 785),
    "wide": (748, 608, 1095, 835),
}

TARGET_CENTER = (1024, 895)
TARGET_SIZES = {
    "closed": (230, 96),
    "small": (255, 128),
    "mid": (290, 172),
    "wide": (330, 216),
    "corner": (82, 74),
}


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def crop(raw: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
    return raw.crop(box).convert("RGBA")


def alpha_from_rgb(img: Image.Image, kind: str) -> Image.Image:
    rgb = np.asarray(img.convert("RGB"), dtype=np.uint8)
    h, w = rgb.shape[:2]
    yy = np.arange(h)[:, None] / max(h - 1, 1)
    r = rgb[:, :, 0]
    g = rgb[:, :, 1]
    b = rgb[:, :, 2]
    maxc = rgb.max(axis=2)
    minc = rgb.min(axis=2)
    sat = maxc - minc
    bg = (r > 245) & (g > 245) & (b > 245)
    skin = (r > 205) & (g > 165) & (b > 145) & (r > b + 10)
    if kind == "line":
        mask = ((maxc < 155) | ((sat > 35) & (maxc < 205))) & ~skin & ~bg
    elif kind == "inner":
        mask = ((r > 70) & (r < 155) & (g < 115) & (b < 125) & (sat > 22)) | (maxc < 85)
    elif kind == "teeth":
        warm_skin_like = (r > g + 14) & (r > b + 14) & (g > b + 2)
        mask = (yy < 0.48) & (maxc > 188) & (minc > 165) & (sat < 62) & ~bg & ~warm_skin_like
    elif kind == "tongue":
        mask = (yy > 0.36) & (r > 135) & (g < 165) & (b < 165) & (r > g + 16) & ~bg & ~skin
    elif kind == "lip":
        mask = (r > 150) & (g < 178) & (b < 172) & (r > g + 12) & (sat > 24) & ~bg & ~skin
    else:
        mask = ~bg & ~skin
    return Image.fromarray(mask.astype(np.uint8) * 255, "L").filter(ImageFilter.GaussianBlur(0.65))


def masked_part(img: Image.Image, kind: str) -> Image.Image:
    out = img.copy()
    out.putalpha(alpha_from_rgb(img, kind))
    return out


def make_canvas(part: Image.Image, size: tuple[int, int], center: tuple[int, int] = TARGET_CENTER) -> Image.Image:
    part = part.resize(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    x = int(center[0] - size[0] / 2)
    y = int(center[1] - size[1] / 2)
    canvas.alpha_composite(part, (x, y))
    return canvas


def bbox_from_alpha(img: Image.Image) -> list[int] | None:
    arr = np.asarray(img.getchannel("A"), dtype=np.uint8)
    ys, xs = np.where(arr > 5)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def alpha_coverage(img: Image.Image) -> float:
    return float((np.asarray(img.getchannel("A"), dtype=np.uint8) > 5).mean())


def alpha_center(img: Image.Image) -> list[float] | None:
    bbox = bbox_from_alpha(img)
    if not bbox:
        return None
    return [round((bbox[0] + bbox[2]) / 2, 3), round((bbox[1] + bbox[3]) / 2, 3)]


def build_layers(raw: Image.Image) -> dict[str, Image.Image]:
    states = {name: crop(raw, box) for name, box in MOUTH_STATE_BOXES.items()}
    closed = states["closed"]
    wide = states["wide"]
    small = states["small"]
    mid = states["mid"]

    layers = {
        "mouth_line": make_canvas(masked_part(closed, "line"), TARGET_SIZES["closed"]),
        "mouth_inner": make_canvas(masked_part(wide, "inner"), TARGET_SIZES["wide"]),
        "mouth_upper_lip_mask": make_canvas(masked_part(small, "lip"), TARGET_SIZES["small"], (TARGET_CENTER[0], TARGET_CENTER[1] - 6)),
        "mouth_lower_lip_mask": make_canvas(masked_part(mid, "lip"), TARGET_SIZES["mid"], (TARGET_CENTER[0], TARGET_CENTER[1] + 12)),
        "mouth_teeth": make_canvas(masked_part(wide, "teeth"), TARGET_SIZES["wide"]),
        "mouth_tongue": make_canvas(masked_part(wide, "tongue"), TARGET_SIZES["wide"]),
        "mouth_closed_smile_reference": make_canvas(masked_part(closed, "all"), TARGET_SIZES["closed"]),
        "mouth_small_open_reference": make_canvas(masked_part(small, "all"), TARGET_SIZES["small"]),
        "mouth_mid_teeth_reference": make_canvas(masked_part(mid, "all"), TARGET_SIZES["mid"]),
        "mouth_wide_teeth_tongue_reference": make_canvas(masked_part(wide, "all"), TARGET_SIZES["wide"]),
    }

    line_crop = masked_part(closed, "line").resize(TARGET_SIZES["closed"], Image.Resampling.LANCZOS)
    w, h = line_crop.size
    corner_l = line_crop.crop((0, 0, int(w * 0.36), h))
    corner_r = line_crop.crop((int(w * 0.64), 0, w, h))
    layers["mouth_corner_L"] = make_canvas(corner_l, TARGET_SIZES["corner"], (TARGET_CENTER[0] - 135, TARGET_CENTER[1] + 4))
    layers["mouth_corner_R"] = make_canvas(corner_r, TARGET_SIZES["corner"], (TARGET_CENTER[0] + 135, TARGET_CENTER[1] + 4))
    return {asset_id: layers[asset_id] for asset_id in B3_EXPECTED_OUTPUTS}


def draw_contact_sheet(layers: dict[str, Image.Image], metrics: dict[str, dict]) -> None:
    cols = 4
    thumb = 330
    label_h = 58
    rows = math.ceil(len(layers) / cols)
    sheet = Image.new("RGB", (cols * thumb, rows * (thumb + label_h)), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, (asset_id, img) in enumerate(layers.items()):
        row, col = divmod(idx, cols)
        x = col * thumb
        y = row * (thumb + label_h)
        bg = Image.new("RGBA", (CANVAS, CANVAS), (244, 238, 226, 255))
        bg.alpha_composite(img)
        sheet.paste(bg.convert("RGB").resize((thumb, thumb), Image.Resampling.LANCZOS), (x, y + label_h))
        draw.text((x + 6, y + 8), asset_id, fill=(20, 20, 20))
        draw.text((x + 6, y + 30), f"cov {metrics[asset_id]['alpha_coverage']:.5f}", fill=(80, 80, 80))
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET)


def composite(base: Image.Image, layers: dict[str, Image.Image], ids: list[str]) -> Image.Image:
    out = base.copy()
    for asset_id in ids:
        out.alpha_composite(layers[asset_id])
    return out


def draw_overlay_sheet(raw: Image.Image, b1: Image.Image, layers: dict[str, Image.Image]) -> None:
    panels = [
        ("B3 raw sheet", raw.convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)),
        ("B1 + rev closed line", composite(b1, layers, ["mouth_line", "mouth_corner_L", "mouth_corner_R"])),
        ("B1 + rev open internals", composite(b1, layers, ["mouth_inner", "mouth_teeth", "mouth_tongue", "mouth_upper_lip_mask", "mouth_lower_lip_mask"])),
        ("rev keypose refs", composite(Image.new("RGBA", (CANVAS, CANVAS), (255, 255, 255, 255)), layers, ["mouth_closed_smile_reference", "mouth_small_open_reference", "mouth_mid_teeth_reference", "mouth_wide_teeth_tongue_reference"])),
    ]
    thumb = 460
    label_h = 46
    sheet = Image.new("RGB", (thumb * 2, (thumb + label_h) * 2), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, (label, img) in enumerate(panels):
        row, col = divmod(idx, 2)
        x = col * thumb
        y = row * (thumb + label_h)
        sheet.paste(img.convert("RGB").resize((thumb, thumb), Image.Resampling.LANCZOS), (x, y + label_h))
        draw.text((x + 10, y + 12), label, fill=(20, 20, 20))
    OVERLAY_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OVERLAY_SHEET)


def main() -> int:
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    raw = Image.open(B3_RAW).convert("RGB")
    b1 = Image.open(B1_RAW).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    raw_review = json.loads(RAW_REVIEW_JSON.read_text(encoding="utf-8"))
    prev_overlay = json.loads(PREV_OVERLAY_JSON.read_text(encoding="utf-8"))
    layers = build_layers(raw)

    metrics = {}
    for asset_id, img in layers.items():
        path = LAYERS_DIR / f"{asset_id}.png"
        img.save(path)
        metrics[asset_id] = {
            "path": rel(path),
            "mode": img.mode,
            "size": img.size,
            "bbox": bbox_from_alpha(img),
            "alpha_coverage": round(alpha_coverage(img), 8),
            "anchor_center": alpha_center(img),
        }
    draw_contact_sheet(layers, metrics)
    draw_overlay_sheet(raw, b1, layers)

    missing = [asset_id for asset_id in B3_EXPECTED_OUTPUTS if asset_id not in layers]
    empty = [asset_id for asset_id, metric in metrics.items() if metric["bbox"] is None]
    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_id": "cubism-v2-new-character-002-v22-b3-mouth-layer-pack-revision-v1-001",
        "status": "B3_REVISION_V1_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED",
        "revision_reason": "Previous B3 overlay QA marked open internals as REVISE because separated helper-row parts looked pasted.",
        "previous_overlay_qa_report": rel(PREV_OVERLAY_JSON),
        "previous_overlay_qa_status": prev_overlay["status"],
        "raw_review_report": rel(RAW_REVIEW_JSON),
        "b3_raw_image": rel(B3_RAW),
        "normalized_layers_dir": rel(LAYERS_DIR),
        "contact_sheet": rel(CONTACT_SHEET),
        "overlay_sheet": rel(OVERLAY_SHEET),
        "expected_outputs": B3_EXPECTED_OUTPUTS,
        "metrics": metrics,
        "forbidden_existing_mouth_assets": raw_review["forbidden_existing_mouth_assets"],
        "decision": "Revision v1 is a new full-canvas RGBA candidate derived from coherent mouth-state crops in the same new B3 raw sheet. It still requires visual overlay QA and 주인님 review before B3 material PASS.",
        "self_review": {
            "expected_output_count": len(B3_EXPECTED_OUTPUTS),
            "generated_output_count": len(layers),
            "missing_output_count": len(missing),
            "empty_output_count": len(empty),
            "all_layers_rgba": all(metric["mode"] == "RGBA" for metric in metrics.values()),
            "all_layers_2048": all(tuple(metric["size"]) == (CANVAS, CANVAS) for metric in metrics.values()),
            "forbidden_existing_mouth_asset_count": len(raw_review["forbidden_existing_mouth_assets"]),
            "forbidden_assets_not_output_path": raw_review["self_review"]["forbidden_assets_not_output_path"],
            "has_human_required_gate": True,
            "has_wide_mouth_review_gate": raw_review["self_review"]["has_wide_mouth_review_gate"],
            "status": "PASS" if not missing and not empty else "REVISE",
        },
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Character 002 v22 B3 Mouth Layer Pack Revision v1",
        "",
        f"- status: `{report['status']}`",
        f"- previous overlay QA: `{report['previous_overlay_qa_status']}`",
        f"- raw review: `{report['raw_review_report']}`",
        f"- normalized layers: `{report['normalized_layers_dir']}`",
        f"- contact sheet: `{report['contact_sheet']}`",
        f"- overlay sheet: `{report['overlay_sheet']}`",
        "",
        "## Decision",
        "",
        report["decision"],
        "",
        "## Self Review",
        "",
    ]
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

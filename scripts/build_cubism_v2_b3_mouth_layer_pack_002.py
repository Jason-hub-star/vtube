#!/usr/bin/env python3
"""Extract v22 B3 mouth-pack full-canvas RGBA candidates from the new raw sheet.

The source is the newly generated B3 sheet only. Previous v10-v13/model_edit
mouth assets remain forbidden as inputs.
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
OUT_ROOT = EXP / "v22_b3_mouth_pack"
LAYERS_DIR = OUT_ROOT / "normalized_layers"
REPORT_DIR = EXP / "reports/v22_b3_mouth_pack"
REPORT_JSON = REPORT_DIR / "v22_b3_layer_pack_report.json"
REPORT_MD = REPORT_DIR / "v22_b3_layer_pack_report.md"
CONTACT_SHEET = REPORT_DIR / "v22_b3_layer_pack_contact_sheet.png"
OVERLAY_SHEET = REPORT_DIR / "v22_b3_layer_pack_overlay_qa.png"
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

COMPONENT_BOXES = {
    "mouth_line": (55, 875, 385, 980),
    "mouth_inner": (385, 850, 625, 1010),
    "mouth_upper_lip_mask": (645, 850, 875, 990),
    "mouth_lower_lip_mask": (890, 850, 1190, 990),
    "mouth_teeth": (300, 1035, 570, 1135),
    "mouth_tongue": (630, 1015, 850, 1165),
    "mouth_corner_L": (125, 1010, 260, 1170),
    "mouth_corner_R": (1040, 1010, 1180, 1170),
}

REFERENCE_BOXES = {
    "mouth_closed_smile_reference": (40, 38, 610, 425),
    "mouth_small_open_reference": (640, 38, 1210, 425),
    "mouth_mid_teeth_reference": (40, 465, 610, 858),
    "mouth_wide_teeth_tongue_reference": (640, 465, 1210, 858),
}

TARGETS = {
    "mouth": {"center": (1024, 895), "line": (310, 118), "inner": (235, 165), "lip": (300, 140), "teeth": (250, 94), "tongue": (210, 150), "corner": (110, 130)},
    "reference": {"center": (1024, 895), "size": (520, 360)},
}


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def crop_with_alpha(raw: Image.Image, box: tuple[int, int, int, int], *, alpha_kind: str = "non_bg") -> Image.Image:
    crop = raw.crop(box).convert("RGBA")
    rgb = np.asarray(crop.convert("RGB"), dtype=np.uint8)
    maxc = rgb.max(axis=2)
    minc = rgb.min(axis=2)
    sat = maxc - minc
    if alpha_kind == "line":
        mask = (maxc < 185) | ((sat > 35) & (maxc < 232))
    elif alpha_kind == "inner":
        mask = ((rgb[:, :, 0] > 95) & (rgb[:, :, 1] < 130) & (rgb[:, :, 2] < 135)) | (maxc < 120)
    elif alpha_kind == "teeth":
        mask = (maxc > 185) & (minc > 145) & (sat < 95) & ~((rgb[:, :, 0] > 246) & (rgb[:, :, 1] > 246) & (rgb[:, :, 2] > 246))
    elif alpha_kind == "tongue":
        mask = (rgb[:, :, 0] > 140) & (rgb[:, :, 1] < 150) & (rgb[:, :, 2] < 155) & (rgb[:, :, 0] > rgb[:, :, 1] + 18)
    elif alpha_kind == "lip":
        mask = (rgb[:, :, 0] > 150) & (rgb[:, :, 1] < 175) & (rgb[:, :, 2] < 170) & (sat > 18)
    else:
        mask = ~((rgb[:, :, 0] > 246) & (rgb[:, :, 1] > 246) & (rgb[:, :, 2] > 246))
    alpha = Image.fromarray(mask.astype(np.uint8) * 255, "L").filter(ImageFilter.GaussianBlur(0.7))
    crop.putalpha(alpha)
    return crop


def make_canvas(part: Image.Image, center: tuple[int, int], size: tuple[int, int]) -> Image.Image:
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
    arr = np.asarray(img.getchannel("A"), dtype=np.uint8)
    return float((arr > 5).mean())


def alpha_bbox_center(img: Image.Image) -> list[float] | None:
    bbox = bbox_from_alpha(img)
    if bbox is None:
        return None
    return [round((bbox[0] + bbox[2]) / 2, 3), round((bbox[1] + bbox[3]) / 2, 3)]


def build_layers(raw: Image.Image) -> dict[str, Image.Image]:
    center = TARGETS["mouth"]["center"]
    layers = {
        "mouth_line": make_canvas(crop_with_alpha(raw, COMPONENT_BOXES["mouth_line"], alpha_kind="line"), center, TARGETS["mouth"]["line"]),
        "mouth_inner": make_canvas(crop_with_alpha(raw, COMPONENT_BOXES["mouth_inner"], alpha_kind="inner"), center, TARGETS["mouth"]["inner"]),
        "mouth_upper_lip_mask": make_canvas(crop_with_alpha(raw, COMPONENT_BOXES["mouth_upper_lip_mask"], alpha_kind="lip"), (center[0], center[1] - 18), TARGETS["mouth"]["lip"]),
        "mouth_lower_lip_mask": make_canvas(crop_with_alpha(raw, COMPONENT_BOXES["mouth_lower_lip_mask"], alpha_kind="lip"), (center[0], center[1] + 18), TARGETS["mouth"]["lip"]),
        "mouth_teeth": make_canvas(crop_with_alpha(raw, COMPONENT_BOXES["mouth_teeth"], alpha_kind="teeth"), (center[0], center[1] - 26), TARGETS["mouth"]["teeth"]),
        "mouth_tongue": make_canvas(crop_with_alpha(raw, COMPONENT_BOXES["mouth_tongue"], alpha_kind="tongue"), (center[0], center[1] + 42), TARGETS["mouth"]["tongue"]),
        "mouth_corner_L": make_canvas(crop_with_alpha(raw, COMPONENT_BOXES["mouth_corner_L"], alpha_kind="line"), (center[0] - 160, center[1]), TARGETS["mouth"]["corner"]),
        "mouth_corner_R": make_canvas(crop_with_alpha(raw, COMPONENT_BOXES["mouth_corner_R"], alpha_kind="line"), (center[0] + 160, center[1]), TARGETS["mouth"]["corner"]),
    }
    for asset_id, box in REFERENCE_BOXES.items():
        layers[asset_id] = make_canvas(crop_with_alpha(raw, box), TARGETS["reference"]["center"], TARGETS["reference"]["size"])
    return layers


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


def draw_overlay_sheet(raw: Image.Image, b1: Image.Image, layers: dict[str, Image.Image]) -> None:
    panels: list[tuple[str, Image.Image]] = []
    panels.append(("B3 raw sheet", raw.convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)))
    for label, ids in [
        ("B1 + closed smile line", ["mouth_line", "mouth_corner_L", "mouth_corner_R"]),
        ("B1 + open internals", ["mouth_inner", "mouth_teeth", "mouth_tongue", "mouth_upper_lip_mask", "mouth_lower_lip_mask"]),
        ("B3 keypose refs", ["mouth_closed_smile_reference", "mouth_small_open_reference", "mouth_mid_teeth_reference", "mouth_wide_teeth_tongue_reference"]),
    ]:
        canvas = b1.copy() if label.startswith("B1") else Image.new("RGBA", (CANVAS, CANVAS), (255, 255, 255, 255))
        for asset_id in ids:
            canvas.alpha_composite(layers[asset_id])
        panels.append((label, canvas))

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
            "anchor_center": alpha_bbox_center(img),
        }

    draw_contact_sheet(layers, metrics)
    draw_overlay_sheet(raw, b1, layers)
    missing = [asset_id for asset_id in B3_EXPECTED_OUTPUTS if asset_id not in layers]
    empty = [asset_id for asset_id, metric in metrics.items() if metric["bbox"] is None]
    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_id": "cubism-v2-new-character-002-v22-b3-mouth-layer-pack-001",
        "status": "B3_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED",
        "raw_review_report": rel(RAW_REVIEW_JSON),
        "b3_raw_image": rel(B3_RAW),
        "normalized_layers_dir": rel(LAYERS_DIR),
        "contact_sheet": rel(CONTACT_SHEET),
        "overlay_sheet": rel(OVERLAY_SHEET),
        "expected_outputs": B3_EXPECTED_OUTPUTS,
        "metrics": metrics,
        "forbidden_existing_mouth_assets": raw_review["forbidden_existing_mouth_assets"],
        "decision": "Keep this B3 extraction as a full-canvas RGBA candidate only. It preserves the new generated mouth sheet, but wide-mouth restraint, internals coherence, overlay QA, and 주인님 review are required before B3 material PASS.",
        "limits": [
            "RGB white-background extraction can leave soft matte halos around lips, teeth, and tongue.",
            "Reference states include face-crop context and are QA/keypose references, not final separated mouth internals by themselves.",
            "This does not activate Mini Cubism diagnostic and does not prove real Cubism rig success.",
        ],
        "next_action": [
            "Run B3 overlay QA against the B1 clean mouth base.",
            "If visual QA accepts B3, continue to B4 hair-pack generation without using existing hair assets unless 주인님 explicitly allows them.",
            "If wide mouth is too large or internals look pasted, regenerate a new B3 sheet instead of importing v10/v12/v13 mouth PNGs.",
        ],
        "self_review": {
            "raw_review_status": raw_review["status"],
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
        "# Character 002 v22 B3 Mouth Layer Pack",
        "",
        f"- status: `{report['status']}`",
        f"- raw review: `{report['raw_review_report']}`",
        f"- B3 raw image: `{report['b3_raw_image']}`",
        f"- normalized layers: `{report['normalized_layers_dir']}`",
        f"- contact sheet: `{report['contact_sheet']}`",
        f"- overlay sheet: `{report['overlay_sheet']}`",
        "",
        "## Expected Outputs",
        "",
        f"- expected: `{len(B3_EXPECTED_OUTPUTS)}`",
        f"- generated: `{len(layers)}`",
        f"- missing: `{missing}`",
        f"- empty: `{empty}`",
        "",
        "## Limits",
        "",
        *[f"- {item}" for item in report["limits"]],
        "",
        "## Next Action",
        "",
        *[f"- {item}" for item in report["next_action"]],
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

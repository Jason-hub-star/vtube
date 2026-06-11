#!/usr/bin/env python3
"""Extract v22 B5 body/clothing full-canvas RGBA candidates from the new raw sheet.

The source is the newly generated B5 sheet only. Prior normalized/model_edit
body or clothing assets remain forbidden as inputs; this is candidate material
until overlay QA and human review pass.
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
B5_RAW = EXP / "v22_b5_body_clothing_pack/raw_outputs/b5_body_clothing_pack_reference_001.png"
RAW_REVIEW_JSON = EXP / "reports/v22_b5_body_clothing_pack/v22_b5_body_clothing_pack_review.json"
SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
OUT_ROOT = EXP / "v22_b5_body_clothing_pack"
LAYERS_DIR = OUT_ROOT / "normalized_layers"
REPORT_DIR = EXP / "reports/v22_b5_body_clothing_pack"
REPORT_JSON = REPORT_DIR / "v22_b5_layer_pack_report.json"
REPORT_MD = REPORT_DIR / "v22_b5_layer_pack_report.md"
CONTACT_SHEET = REPORT_DIR / "v22_b5_layer_pack_contact_sheet.png"
OVERLAY_SHEET = REPORT_DIR / "v22_b5_layer_pack_overlay_qa.png"
CANVAS = 2048

B5_EXPECTED_OUTPUTS = [
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

# Raw-sheet crop boxes are in B5 raw 1536x1024 pixel coordinates. They target
# the newly generated B5 sheet components, not previous material-pack PNGs.
CROP_BOXES = {
    "torso_base": (50, 125, 640, 775),
    "neck": (920, 20, 1125, 250),
    "shoulder_L": (670, 125, 875, 275),
    "shoulder_R": (1210, 125, 1455, 275),
    "arm_L_upper_simple": (680, 295, 820, 740),
    "arm_R_upper_simple": (1320, 295, 1455, 740),
    "collar_front": (850, 292, 1245, 370),
    "collar_shadow": (860, 395, 1250, 460),
    "chest_cloth_base": (800, 500, 1248, 680),
    "chest_cloth_shadow": (835, 685, 1245, 805),
    "brow_L": (250, 836, 382, 884),
    "brow_R": (450, 836, 582, 884),
    "nose": (650, 830, 748, 930),
    "cheek_L": (795, 830, 980, 948),
    "cheek_R": (990, 830, 1175, 948),
    "face_shadow_L": (1215, 790, 1330, 995),
    "face_shadow_R": (1400, 790, 1512, 995),
}

TARGETS = {
    "torso_base": ((1024, 1370), (900, 990)),
    "neck": ((1024, 875), (310, 430)),
    "shoulder_L": ((705, 1110), (330, 250)),
    "shoulder_R": ((1345, 1110), (330, 250)),
    "arm_L_upper_simple": ((600, 1450), (230, 720)),
    "arm_R_upper_simple": ((1450, 1450), (230, 720)),
    "collar_front": ((1024, 1138), (600, 120)),
    "collar_shadow": ((1024, 1230), (610, 105)),
    "chest_cloth_base": ((1024, 1395), (700, 300)),
    "chest_cloth_shadow": ((1024, 1585), (700, 205)),
    "brow_L": ((845, 650), (170, 60)),
    "brow_R": ((1190, 650), (170, 60)),
    "nose": ((1024, 790), (100, 115)),
    "cheek_L": ((830, 800), (240, 150)),
    "cheek_R": ((1215, 800), (240, 150)),
    "face_shadow_L": ((775, 800), (170, 300)),
    "face_shadow_R": ((1250, 800), (170, 300)),
}

MASK_KIND = {
    "torso_base": "body",
    "neck": "skin",
    "shoulder_L": "skin",
    "shoulder_R": "skin",
    "arm_L_upper_simple": "cloth",
    "arm_R_upper_simple": "cloth",
    "collar_front": "cloth",
    "collar_shadow": "cloth_shadow",
    "chest_cloth_base": "cloth",
    "chest_cloth_shadow": "cloth_shadow",
    "brow_L": "brow",
    "brow_R": "brow",
    "nose": "nose",
    "cheek_L": "blush",
    "cheek_R": "blush",
    "face_shadow_L": "skin_shadow",
    "face_shadow_R": "skin_shadow",
}


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ellipse_alpha(size: tuple[int, int], inset_x: float = 0.04, inset_y: float = 0.08, alpha: int = 210) -> Image.Image:
    w, h = size
    img = Image.new("L", size, 0)
    draw = ImageDraw.Draw(img)
    draw.ellipse((w * inset_x, h * inset_y, w * (1 - inset_x), h * (1 - inset_y)), fill=alpha)
    return img.filter(ImageFilter.GaussianBlur(max(1.0, min(w, h) * 0.01)))


def mask_for(part: Image.Image, kind: str) -> Image.Image:
    rgb = np.asarray(part.convert("RGB"), dtype=np.uint8)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    maxc = rgb.max(axis=2)
    minc = rgb.min(axis=2)
    sat = maxc - minc
    bg = (r > 246) & (g > 246) & (b > 246)
    line = (maxc < 135) & (sat > 6)
    skin = (r > 185) & (g > 130) & (b > 105) & (r > g + 12) & (g > b - 10)
    cloth_line = (maxc < 220) & (sat < 70) & ~skin
    cloth_soft = (maxc < 246) & (minc > 175) & (sat < 56) & ~skin
    pink = (r > 190) & (g > 118) & (b > 112) & (r > g + 22) & (r > b + 20)
    brown = (r > 55) & (r < 160) & (g > 35) & (g < 120) & (b > 25) & (b < 110) & (sat > 10)

    if kind == "skin":
        mask = (skin | line) & ~bg
    elif kind == "body":
        mask = (skin | cloth_soft | cloth_line | line) & ~bg
    elif kind == "cloth":
        mask = (cloth_soft | cloth_line | line) & ~bg
    elif kind == "cloth_shadow":
        mask = ((maxc < 235) & (sat < 70) & ~skin) | line
        mask &= ~bg
    elif kind == "brow":
        mask = (brown | line) & ~bg
    elif kind == "nose":
        mask = (pink | skin | line) & ~bg
        alpha = Image.fromarray(mask.astype(np.uint8) * 190, "L")
        soft = ellipse_alpha(part.size, 0.2, 0.08, 125)
        return Image.composite(Image.new("L", part.size, 230), soft, alpha).filter(ImageFilter.GaussianBlur(0.7))
    elif kind == "blush":
        mask = pink & ~bg
        alpha = Image.fromarray(mask.astype(np.uint8) * 210, "L")
        soft = ellipse_alpha(part.size, 0.08, 0.15, 150)
        return Image.composite(Image.new("L", part.size, 230), soft, alpha).filter(ImageFilter.GaussianBlur(1.1))
    elif kind == "skin_shadow":
        mask = (skin | pink | line) & ~bg
    else:
        mask = ~bg

    alpha = Image.fromarray(mask.astype(np.uint8) * 255, "L")
    return alpha.filter(ImageFilter.GaussianBlur(0.75))


def crop_part(raw: Image.Image, asset_id: str) -> Image.Image:
    part = raw.crop(CROP_BOXES[asset_id]).convert("RGBA")
    part.putalpha(mask_for(part, MASK_KIND[asset_id]))
    return part


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


def alpha_center(img: Image.Image) -> list[float] | None:
    bbox = bbox_from_alpha(img)
    if not bbox:
        return None
    return [round((bbox[0] + bbox[2]) / 2, 3), round((bbox[1] + bbox[3]) / 2, 3)]


def build_layers(raw: Image.Image) -> dict[str, Image.Image]:
    layers = {}
    for asset_id in B5_EXPECTED_OUTPUTS:
        center, size = TARGETS[asset_id]
        layers[asset_id] = make_canvas(crop_part(raw, asset_id), center, size)
    return layers


def draw_contact_sheet(layers: dict[str, Image.Image], metrics: dict[str, dict]) -> None:
    cols = 5
    thumb = 300
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


def draw_overlay_sheet(raw: Image.Image, source: Image.Image, layers: dict[str, Image.Image]) -> None:
    raw_panel = raw.convert("RGBA").resize((CANVAS, int(CANVAS * raw.size[1] / raw.size[0])), Image.Resampling.LANCZOS)
    raw_canvas = Image.new("RGBA", (CANVAS, CANVAS), (255, 255, 255, 255))
    raw_canvas.alpha_composite(raw_panel, (0, 256))
    source_base = source.convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    body_ids = ["torso_base", "neck", "shoulder_L", "shoulder_R", "arm_L_upper_simple", "arm_R_upper_simple"]
    cloth_ids = ["collar_front", "collar_shadow", "chest_cloth_base", "chest_cloth_shadow"]
    face_ids = ["brow_L", "brow_R", "nose", "cheek_L", "cheek_R", "face_shadow_L", "face_shadow_R"]
    panels = [
        ("B5 raw sheet", raw_canvas),
        ("source + body", composite(source_base, layers, body_ids)),
        ("source + clothing", composite(source_base, layers, cloth_ids)),
        ("source + face details", composite(source_base, layers, face_ids)),
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
    raw = Image.open(B5_RAW).convert("RGB")
    source = Image.open(SOURCE).convert("RGB")
    raw_review = json.loads(RAW_REVIEW_JSON.read_text(encoding="utf-8"))
    layers = build_layers(raw)

    metrics = {}
    for asset_id, img in layers.items():
        path = LAYERS_DIR / f"{asset_id}.png"
        img.save(path)
        metrics[asset_id] = {
            "path": rel(path),
            "mode": img.mode,
            "size": list(img.size),
            "bbox": bbox_from_alpha(img),
            "alpha_coverage": round(alpha_coverage(img), 8),
            "anchor_center": alpha_center(img),
        }
    draw_contact_sheet(layers, metrics)
    draw_overlay_sheet(raw, source, layers)

    missing = [asset_id for asset_id in B5_EXPECTED_OUTPUTS if asset_id not in layers]
    empty = [asset_id for asset_id, metric in metrics.items() if metric["bbox"] is None]
    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_id": "cubism-v2-new-character-002-v22-b5-body-clothing-layer-pack-001",
        "status": "B5_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED",
        "raw_review_report": rel(RAW_REVIEW_JSON),
        "b5_raw_image": rel(B5_RAW),
        "normalized_layers_dir": rel(LAYERS_DIR),
        "contact_sheet": rel(CONTACT_SHEET),
        "overlay_sheet": rel(OVERLAY_SHEET),
        "expected_outputs": B5_EXPECTED_OUTPUTS,
        "metrics": metrics,
        "forbidden_existing_body_clothing_assets": raw_review["forbidden_existing_body_clothing_assets"],
        "locked_success_criteria": [
            "Do not reuse prior normalized/model_edit/body-clothing PNGs for B5 material.",
            "All outputs are 2048 full-canvas RGBA candidates.",
            "B5 must provide complete torso, neck, shoulder, arm, clothing, and face-detail references instead of relying on a source crop.",
            "Contact sheet and overlay QA are required before material PASS.",
        ],
        "decision": "Keep this B5 extraction as full-canvas RGBA candidate evidence only. It does not prove body-motion, visual material PASS, Mini Cubism success, or real Cubism success before overlay QA and 주인님 review.",
        "next_action": [
            "Run B5 overlay QA and visual review against the G0 source silhouette.",
            "Use manual anchor correction or refined extraction if body/clothing/face detail parts are visually misaligned.",
            "Only after B1-B5 visual QA acceptance, build the v22 64-part manifest.",
        ],
        "self_review": {
            "expected_output_count": len(B5_EXPECTED_OUTPUTS),
            "generated_output_count": len(layers),
            "missing_output_count": len(missing),
            "empty_output_count": len(empty),
            "all_layers_rgba": all(metric["mode"] == "RGBA" for metric in metrics.values()),
            "all_layers_2048": all(metric["size"] == [CANVAS, CANVAS] for metric in metrics.values()),
            "forbidden_existing_body_clothing_asset_count": len(raw_review["forbidden_existing_body_clothing_assets"]),
            "forbidden_assets_not_output_path": all(
                Path(item["path"]).name != "b5_body_clothing_pack_reference_001.png"
                for item in raw_review["forbidden_existing_body_clothing_assets"]
            ),
            "has_human_required_gate": True,
            "has_overlay_qa_requirement": True,
            "has_face_detail_scope": all(
                part in B5_EXPECTED_OUTPUTS
                for part in ["brow_L", "brow_R", "nose", "cheek_L", "cheek_R", "face_shadow_L", "face_shadow_R"]
            ),
            "status": "PASS" if not missing and not empty else "REVISE",
        },
    }
    save_json(REPORT_JSON, report)

    lines = [
        "# Character 002 v22 B5 Body/Clothing Layer Pack",
        "",
        f"- status: `{report['status']}`",
        f"- raw review: `{report['raw_review_report']}`",
        f"- B5 raw image: `{report['b5_raw_image']}`",
        f"- normalized layers: `{report['normalized_layers_dir']}`",
        f"- contact sheet: `{report['contact_sheet']}`",
        f"- overlay sheet: `{report['overlay_sheet']}`",
        "",
        "## Expected Outputs",
        "",
        *[f"- `{asset_id}`" for asset_id in B5_EXPECTED_OUTPUTS],
        "",
        "## Metrics",
        "",
    ]
    for asset_id, metric in metrics.items():
        lines.append(
            f"- `{asset_id}`: bbox `{metric['bbox']}`, coverage `{metric['alpha_coverage']}`, center `{metric['anchor_center']}`"
        )
    lines.extend(
        [
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

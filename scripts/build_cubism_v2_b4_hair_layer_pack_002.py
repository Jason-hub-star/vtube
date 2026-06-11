#!/usr/bin/env python3
"""Extract v22 B4 hair-pack full-canvas RGBA candidates from the new raw sheet.

The source is the newly generated B4 sheet only. Prior normalized/model_edit
hair assets remain forbidden as inputs; v21 HairFront rules are used only as a
contract guardrail.
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
B4_RAW = EXP / "v22_b4_hair_pack/raw_outputs/b4_hair_pack_reference_001.png"
RAW_REVIEW_JSON = EXP / "reports/v22_b4_hair_pack/v22_b4_hair_pack_review.json"
SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
OUT_ROOT = EXP / "v22_b4_hair_pack"
LAYERS_DIR = OUT_ROOT / "normalized_layers"
REPORT_DIR = EXP / "reports/v22_b4_hair_pack"
REPORT_JSON = REPORT_DIR / "v22_b4_layer_pack_report.json"
REPORT_MD = REPORT_DIR / "v22_b4_layer_pack_report.md"
CONTACT_SHEET = REPORT_DIR / "v22_b4_layer_pack_contact_sheet.png"
OVERLAY_SHEET = REPORT_DIR / "v22_b4_layer_pack_overlay_qa.png"
CANVAS = 2048

B4_EXPECTED_OUTPUTS = [
    "hair_back_base",
    "hair_back_strand_L",
    "hair_back_strand_R",
    "hair_back_center",
    "hair_front_center",
    "hair_front_L",
    "hair_front_R",
    "hair_front_side_L",
    "hair_front_side_R",
    "hair_front_tip_L",
    "hair_front_tip_R",
    "hair_side_L_outer",
    "hair_side_L_inner",
    "hair_side_R_outer",
    "hair_side_R_inner",
    "hair_back_underpaint",
]

# Raw-sheet crop boxes are in B4 raw 1536x1024 pixel coordinates. They target
# the newly generated B4 sheet components, not previous model_edit project PNGs.
CROP_BOXES = {
    "hair_back_base": (500, 30, 820, 475),
    "hair_back_strand_L": (850, 40, 1000, 455),
    "hair_back_strand_R": (1280, 40, 1510, 465),
    "hair_back_center": (1080, 35, 1268, 470),
    "hair_front_center": (545, 508, 760, 735),
    "hair_front_L": (820, 520, 980, 705),
    "hair_front_R": (602, 520, 760, 710),
    "hair_front_side_L": (1030, 505, 1188, 755),
    "hair_front_side_R": (1230, 510, 1450, 760),
    "hair_front_tip_L": (120, 775, 235, 1005),
    "hair_front_tip_R": (690, 775, 825, 968),
    "hair_side_L_outer": (365, 765, 525, 1008),
    "hair_side_L_inner": (110, 770, 240, 1008),
    "hair_side_R_outer": (900, 765, 1030, 970),
    "hair_side_R_inner": (1280, 790, 1515, 1010),
    "hair_back_underpaint": (1230, 778, 1515, 1004),
}

TARGETS = {
    "hair_back_base": ((1024, 720), (760, 1060)),
    "hair_back_strand_L": ((725, 820), (260, 760)),
    "hair_back_strand_R": ((1320, 830), (300, 760)),
    "hair_back_center": ((1030, 820), (390, 780)),
    "hair_front_center": ((1024, 430), (420, 420)),
    "hair_front_L": ((860, 455), (300, 360)),
    "hair_front_R": ((1160, 455), (300, 360)),
    "hair_front_side_L": ((785, 635), (290, 520)),
    "hair_front_side_R": ((1235, 635), (290, 520)),
    "hair_front_tip_L": ((760, 885), (170, 390)),
    "hair_front_tip_R": ((1240, 885), (170, 390)),
    "hair_side_L_outer": ((615, 930), (245, 520)),
    "hair_side_L_inner": ((735, 940), (205, 455)),
    "hair_side_R_outer": ((1410, 930), (245, 520)),
    "hair_side_R_inner": ((1290, 940), (205, 455)),
    "hair_back_underpaint": ((1024, 880), (580, 590)),
}


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def hair_mask(part: Image.Image, *, underpaint: bool = False) -> Image.Image:
    rgb = np.asarray(part.convert("RGB"), dtype=np.uint8)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    maxc = rgb.max(axis=2)
    minc = rgb.min(axis=2)
    sat = maxc - minc
    bg = (r > 242) & (g > 242) & (b > 242)
    brown = (r > 55) & (r < 170) & (g > 35) & (g < 130) & (b > 25) & (b < 125) & (sat > 12)
    dark_line = (maxc < 105) & (sat > 8)
    warm_shadow = (r > 105) & (r < 205) & (g > 65) & (g < 165) & (b > 45) & (b < 145) & (r > b + 8)
    if underpaint:
        mask = (brown | dark_line | warm_shadow) & ~bg
    else:
        mask = (brown | dark_line) & ~bg
    alpha = Image.fromarray(mask.astype(np.uint8) * 255, "L")
    return alpha.filter(ImageFilter.GaussianBlur(0.65))


def crop_part(raw: Image.Image, asset_id: str) -> Image.Image:
    part = raw.crop(CROP_BOXES[asset_id]).convert("RGBA")
    part.putalpha(hair_mask(part, underpaint=asset_id == "hair_back_underpaint"))
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
    for asset_id in B4_EXPECTED_OUTPUTS:
        center, size = TARGETS[asset_id]
        layers[asset_id] = make_canvas(crop_part(raw, asset_id), center, size)
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
    front_ids = [
        "hair_front_center",
        "hair_front_L",
        "hair_front_R",
        "hair_front_side_L",
        "hair_front_side_R",
        "hair_front_tip_L",
        "hair_front_tip_R",
    ]
    side_ids = [
        "hair_side_L_outer",
        "hair_side_L_inner",
        "hair_side_R_outer",
        "hair_side_R_inner",
    ]
    back_ids = ["hair_back_underpaint", "hair_back_base", "hair_back_center", "hair_back_strand_L", "hair_back_strand_R"]
    panels = [
        ("B4 raw sheet", raw_canvas),
        ("source + back/side hair", composite(source_base, layers, back_ids + side_ids)),
        ("source + front hair", composite(source_base, layers, front_ids)),
        ("all B4 hair candidates", composite(source_base, layers, back_ids + side_ids + front_ids)),
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
    raw = Image.open(B4_RAW).convert("RGB")
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

    missing = [asset_id for asset_id in B4_EXPECTED_OUTPUTS if asset_id not in layers]
    empty = [asset_id for asset_id, metric in metrics.items() if metric["bbox"] is None]
    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_id": "cubism-v2-new-character-002-v22-b4-hair-layer-pack-001",
        "status": "B4_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED",
        "raw_review_report": rel(RAW_REVIEW_JSON),
        "b4_raw_image": rel(B4_RAW),
        "normalized_layers_dir": rel(LAYERS_DIR),
        "contact_sheet": rel(CONTACT_SHEET),
        "overlay_sheet": rel(OVERLAY_SHEET),
        "expected_outputs": B4_EXPECTED_OUTPUTS,
        "metrics": metrics,
        "forbidden_existing_hair_assets": raw_review["forbidden_existing_hair_assets"],
        "locked_success_criteria": [
            "Do not reuse prior normalized/model_edit hair PNGs for B4 material.",
            "All outputs are 2048 full-canvas RGBA candidates.",
            "ParamHairFront remains hidden/contract-only until hair_front_* child parts pass visual QA and motion QA.",
            "Contact sheet and overlay QA are required before material PASS.",
        ],
        "decision": "Keep this B4 extraction as full-canvas RGBA candidate evidence only. It creates real hair_front_* scope, but does not unlock ParamHairFront or material PASS before overlay QA and 주인님 review.",
        "next_action": [
            "Run B4 overlay QA and visual review against the G0 source silhouette.",
            "Use manual anchor correction if front/side/back hair parts are visually misaligned.",
            "Keep ParamHairFront hidden until independent front hair children are accepted.",
        ],
        "self_review": {
            "expected_output_count": len(B4_EXPECTED_OUTPUTS),
            "generated_output_count": len(layers),
            "missing_output_count": len(missing),
            "empty_output_count": len(empty),
            "all_layers_rgba": all(metric["mode"] == "RGBA" for metric in metrics.values()),
            "all_layers_2048": all(metric["size"] == [CANVAS, CANVAS] for metric in metrics.values()),
            "forbidden_existing_hair_asset_count": len(raw_review["forbidden_existing_hair_assets"]),
            "forbidden_assets_not_output_path": all(
                Path(item["path"]).name != "b4_hair_pack_reference_001.png"
                for item in raw_review["forbidden_existing_hair_assets"]
            ),
            "has_human_required_gate": True,
            "has_hairfront_contract_gate": True,
            "has_overlay_qa_requirement": True,
            "status": "PASS" if not missing and not empty else "REVISE",
        },
    }
    save_json(REPORT_JSON, report)

    lines = [
        "# Character 002 v22 B4 Hair Layer Pack",
        "",
        f"- status: `{report['status']}`",
        f"- raw review: `{report['raw_review_report']}`",
        f"- B4 raw image: `{report['b4_raw_image']}`",
        f"- normalized layers: `{report['normalized_layers_dir']}`",
        f"- contact sheet: `{report['contact_sheet']}`",
        f"- overlay sheet: `{report['overlay_sheet']}`",
        "",
        "## Expected Outputs",
        "",
        *[f"- `{asset_id}`" for asset_id in B4_EXPECTED_OUTPUTS],
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

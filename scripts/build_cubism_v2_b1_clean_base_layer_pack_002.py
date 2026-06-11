#!/usr/bin/env python3
"""Build v22 B1 clean-base/underpaint full-canvas RGBA candidates.

The input is the same-character B1 raw clean-base reference. The output is an
11-layer B1 candidate pack matching the v22 B1 expected outputs. These masks
are conservative production-prep candidates, not final accepted material.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
B1_RAW = EXP / "v22_b1_clean_base_underpaint/raw_outputs/b1_clean_base_underpaint_reference_001.png"
OUT_ROOT = EXP / "v22_b1_clean_base_underpaint"
LAYERS_DIR = OUT_ROOT / "normalized_layers"
REPORT_DIR = EXP / "reports/v22_b1_clean_base_underpaint"
REPORT_JSON = REPORT_DIR / "v22_b1_layer_pack_report.json"
REPORT_MD = REPORT_DIR / "v22_b1_layer_pack_report.md"
CONTACT_SHEET = REPORT_DIR / "v22_b1_layer_pack_contact_sheet.png"
OVERLAY_SHEET = REPORT_DIR / "v22_b1_layer_pack_overlay_qa.png"
CANVAS = 2048

B1_EXPECTED_OUTPUTS = [
    "face_base",
    "face_underpaint_L",
    "face_underpaint_R",
    "eye_L_underpaint",
    "eye_R_underpaint",
    "mouth_base_clean_reference",
    "body_underpaint",
    "neck_shadow_underpaint",
    "arm_L_underpaint",
    "arm_R_underpaint",
    "hair_back_underpaint",
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_2048(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)


def character_alpha(img: Image.Image) -> Image.Image:
    arr = np.asarray(img.convert("RGB"), dtype=np.uint8)
    non_bg = ~((arr[:, :, 0] > 247) & (arr[:, :, 1] > 247) & (arr[:, :, 2] > 247))
    alpha = non_bg.astype(np.uint8) * 255
    return Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(1))


def feather(mask: Image.Image, blur: float = 4.0) -> Image.Image:
    return mask.filter(ImageFilter.GaussianBlur(blur))


def ellipse_mask(box: tuple[int, int, int, int], blur: float = 4.0) -> Image.Image:
    mask = Image.new("L", (CANVAS, CANVAS), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(box, fill=255)
    return feather(mask, blur)


def polygon_mask(points: list[tuple[int, int]], blur: float = 4.0) -> Image.Image:
    mask = Image.new("L", (CANVAS, CANVAS), 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon(points, fill=255)
    return feather(mask, blur)


def rect_mask(box: tuple[int, int, int, int], blur: float = 4.0) -> Image.Image:
    mask = Image.new("L", (CANVAS, CANVAS), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle(box, radius=28, fill=255)
    return feather(mask, blur)


def max_mask(*masks: Image.Image) -> Image.Image:
    arr = np.maximum.reduce([np.asarray(mask, dtype=np.uint8) for mask in masks])
    return Image.fromarray(arr, "L")


def min_mask(mask: Image.Image, alpha: Image.Image) -> Image.Image:
    arr = np.minimum(np.asarray(mask, dtype=np.uint8), np.asarray(alpha, dtype=np.uint8))
    return Image.fromarray(arr, "L")


def subtract_mask(mask: Image.Image, *subtracts: Image.Image) -> Image.Image:
    arr = np.asarray(mask, dtype=np.int16)
    for sub in subtracts:
        arr = arr - np.asarray(sub, dtype=np.int16)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "L")


def keep_y(alpha: Image.Image, y_min: int | None = None, y_max: int | None = None) -> Image.Image:
    arr = np.asarray(alpha, dtype=np.uint8).copy()
    if y_min is not None:
        arr[:y_min, :] = 0
    if y_max is not None:
        arr[y_max:, :] = 0
    return Image.fromarray(arr, "L")


def keep_x(alpha: Image.Image, x_min: int | None = None, x_max: int | None = None) -> Image.Image:
    arr = np.asarray(alpha, dtype=np.uint8).copy()
    if x_min is not None:
        arr[:, :x_min] = 0
    if x_max is not None:
        arr[:, x_max:] = 0
    return Image.fromarray(arr, "L")


def apply_mask(img: Image.Image, mask: Image.Image) -> Image.Image:
    out = img.copy()
    out.putalpha(mask)
    return out


def bbox_from_alpha(mask: Image.Image) -> list[int] | None:
    arr = np.asarray(mask, dtype=np.uint8)
    ys, xs = np.where(arr > 5)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def alpha_coverage(mask: Image.Image) -> float:
    arr = np.asarray(mask, dtype=np.uint8)
    return float((arr > 5).mean())


def mean_rgb(img: Image.Image, mask: Image.Image) -> list[float]:
    rgb = np.asarray(img.convert("RGB"), dtype=np.float32)
    m = np.asarray(mask, dtype=np.uint8) > 5
    if not m.any():
        return [0.0, 0.0, 0.0]
    vals = rgb[m]
    return [round(float(v), 3) for v in vals.mean(axis=0)]


def build_masks(char_alpha: Image.Image) -> dict[str, Image.Image]:
    # Face shape intentionally includes clean skin under where eyes/mouth will be
    # authored later, while avoiding broad hair and torso regions.
    face_oval = ellipse_mask((650, 360, 1370, 1035), 5)
    chin = polygon_mask([(800, 850), (1024, 1080), (1248, 850), (1165, 1165), (1024, 1225), (885, 1165)], 8)
    face_base = min_mask(max_mask(face_oval, chin), char_alpha)

    eye_l = min_mask(ellipse_mask((720, 590, 965, 765), 5), char_alpha)
    eye_r = min_mask(ellipse_mask((1083, 590, 1328, 765), 5), char_alpha)
    mouth = min_mask(ellipse_mask((910, 800, 1140, 930), 5), char_alpha)

    face_under_l = min_mask(ellipse_mask((610, 520, 950, 1070), 12), face_base)
    face_under_r = min_mask(ellipse_mask((1098, 520, 1438, 1070), 12), face_base)

    neck = min_mask(polygon_mask([(860, 930), (1150, 930), (1230, 1310), (820, 1310)], 10), char_alpha)
    body = min_mask(keep_y(char_alpha, y_min=1085), char_alpha)
    # Keep body underpaint from swallowing all long hair by emphasizing central
    # torso/shoulder/sleeve regions.
    body_core = max_mask(
        polygon_mask([(520, 1160), (1548, 1160), (1760, 2048), (250, 2048)], 12),
        rect_mask((430, 1220, 680, 2048), 16),
        rect_mask((1375, 1220, 1625, 2048), 16),
    )
    body = min_mask(body_core, body)
    arm_l = min_mask(rect_mask((380, 1210, 680, 2048), 14), char_alpha)
    arm_r = min_mask(rect_mask((1368, 1210, 1668, 2048), 14), char_alpha)

    # Back hair is the character silhouette outside face/body, mostly below and
    # behind the head. This is a coarse underpaint support layer.
    head_hair_region = min_mask(
        max_mask(
            ellipse_mask((475, 130, 1548, 1380), 10),
            rect_mask((360, 620, 1695, 1700), 12),
        ),
        char_alpha,
    )
    hair_back = subtract_mask(head_hair_region, face_base, neck, body)
    hair_back = min_mask(hair_back, char_alpha)

    return {
        "face_base": face_base,
        "face_underpaint_L": face_under_l,
        "face_underpaint_R": face_under_r,
        "eye_L_underpaint": eye_l,
        "eye_R_underpaint": eye_r,
        "mouth_base_clean_reference": mouth,
        "body_underpaint": body,
        "neck_shadow_underpaint": neck,
        "arm_L_underpaint": arm_l,
        "arm_R_underpaint": arm_r,
        "hair_back_underpaint": hair_back,
    }


def draw_layer_contact_sheet(layers: dict[str, Image.Image], metrics: dict[str, dict]) -> None:
    cols = 4
    thumb = 360
    label_h = 58
    rows = math.ceil(len(layers) / cols)
    sheet = Image.new("RGB", (cols * thumb, rows * (thumb + label_h)), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, (asset_id, img) in enumerate(layers.items()):
        row, col = divmod(idx, cols)
        x = col * thumb
        y = row * (thumb + label_h)
        bg = Image.new("RGBA", (CANVAS, CANVAS), (242, 236, 226, 255))
        bg.alpha_composite(img)
        thumb_img = bg.convert("RGB").resize((thumb, thumb), Image.Resampling.LANCZOS)
        sheet.paste(thumb_img, (x, y + label_h))
        draw.text((x + 8, y + 8), asset_id, fill=(20, 20, 20))
        draw.text((x + 8, y + 30), f"coverage {metrics[asset_id]['alpha_coverage']:.4f}", fill=(80, 80, 80))
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET)


def draw_overlay_sheet(source: Image.Image, b1: Image.Image, layers: dict[str, Image.Image]) -> None:
    composites: list[tuple[str, Image.Image]] = []
    base = Image.new("RGBA", (CANVAS, CANVAS), (255, 255, 255, 255))
    source_rgb = source.convert("RGBA")
    b1_rgb = b1.convert("RGBA")
    composites.append(("G0 source", source_rgb))
    composites.append(("B1 raw clean ref", b1_rgb))
    for label, asset_ids in [
        ("B1 face + eye/mouth underpaint", ["face_base", "eye_L_underpaint", "eye_R_underpaint", "mouth_base_clean_reference"]),
        ("B1 body + arms + neck", ["body_underpaint", "neck_shadow_underpaint", "arm_L_underpaint", "arm_R_underpaint"]),
        ("B1 hair back underpaint", ["hair_back_underpaint"]),
    ]:
        canvas = base.copy()
        for asset_id in asset_ids:
            canvas.alpha_composite(layers[asset_id])
        composites.append((label, canvas))

    thumb_w = 420
    thumb_h = 420
    label_h = 46
    sheet = Image.new("RGB", (thumb_w * 2, (thumb_h + label_h) * 2), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, (label, img) in enumerate(composites[:4]):
        row, col = divmod(idx, 2)
        x = col * thumb_w
        y = row * (thumb_h + label_h)
        thumb = img.convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        sheet.paste(thumb, (x, y + label_h))
        draw.text((x + 10, y + 12), label, fill=(20, 20, 20))
    sheet.save(OVERLAY_SHEET)


def main() -> int:
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    source = load_2048(SOURCE)
    b1 = load_2048(B1_RAW)
    char_alpha = character_alpha(b1)
    b1.putalpha(char_alpha)
    b1.save(OUT_ROOT / "b1_clean_base_underpaint_reference_001_2048.png")

    masks = build_masks(char_alpha)
    layers: dict[str, Image.Image] = {}
    metrics: dict[str, dict] = {}
    for asset_id in B1_EXPECTED_OUTPUTS:
        mask = masks[asset_id]
        layer = apply_mask(b1, mask)
        out_path = LAYERS_DIR / f"{asset_id}.png"
        layer.save(out_path)
        layers[asset_id] = layer
        metrics[asset_id] = {
            "path": rel(out_path),
            "bbox": bbox_from_alpha(mask),
            "alpha_coverage": round(alpha_coverage(mask), 6),
            "mean_rgb": mean_rgb(b1, mask),
            "status": "PASS_LAYER_NONEMPTY" if bbox_from_alpha(mask) else "FAIL_EMPTY_LAYER",
        }

    draw_layer_contact_sheet(layers, metrics)
    draw_overlay_sheet(source, b1, layers)

    missing = [asset_id for asset_id in B1_EXPECTED_OUTPUTS if not (LAYERS_DIR / f"{asset_id}.png").exists()]
    empty = [asset_id for asset_id, metric in metrics.items() if metric["bbox"] is None]
    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_id": "cubism-v2-new-character-002-v22-b1-clean-base-layer-pack-001",
        "status": "B1_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA",
        "source_image": rel(SOURCE),
        "b1_raw_reference": rel(B1_RAW),
        "b1_reference_2048": rel(OUT_ROOT / "b1_clean_base_underpaint_reference_001_2048.png"),
        "output_layers_dir": rel(LAYERS_DIR),
        "expected_outputs": B1_EXPECTED_OUTPUTS,
        "generated_outputs": sorted(metrics),
        "missing_outputs": missing,
        "empty_outputs": empty,
        "contact_sheet": rel(CONTACT_SHEET),
        "overlay_sheet": rel(OVERLAY_SHEET),
        "layer_metrics": metrics,
        "manual_visual_review": {
            "status": "REQUIRED",
            "notes": "This is an automatically masked B1 layer pack candidate. Visual QA must confirm no patch boundaries before B1 material PASS.",
        },
        "limits": [
            "Automatic masks are coarse and must not be treated as final Cubism ArtMesh geometry.",
            "This does not generate B2 eyes, B3 mouth expressions, B4 hair children, or B5 final body/clothing parts.",
            "Mini Cubism diagnostic and real Cubism authoring gates remain locked until later material QA passes.",
        ],
        "next_action": [
            "Run B1 overlay/contact-sheet visual QA.",
            "If accepted, use these B1 layers as clean-base inputs for B2 eye pack and B3 mouth pack generation.",
            "If rejected, regenerate or manually edit only the failing B1 layer areas; do not fall back to patch-style clean bases.",
        ],
        "self_review": {
            "expected_output_count": len(B1_EXPECTED_OUTPUTS),
            "generated_output_count": len(metrics),
            "missing_output_count": len(missing),
            "empty_output_count": len(empty),
            "all_outputs_present": not missing,
            "all_outputs_nonempty": not empty,
            "canvas": [CANVAS, CANVAS],
            "status": "PASS" if not missing and not empty else "FAIL",
        },
    }
    save_json(REPORT_JSON, report)

    lines = [
        "# Character 002 v22 B1 Clean Base Layer Pack",
        "",
        f"- status: `{report['status']}`",
        f"- output layers: `{report['output_layers_dir']}`",
        f"- contact sheet: `{report['contact_sheet']}`",
        f"- overlay sheet: `{report['overlay_sheet']}`",
        "",
        "## Outputs",
        "",
    ]
    for asset_id in B1_EXPECTED_OUTPUTS:
        metric = metrics[asset_id]
        lines.append(
            f"- `{asset_id}`: `{metric['status']}`, coverage `{metric['alpha_coverage']}`, bbox `{metric['bbox']}`"
        )
    lines.extend(
        [
            "",
            "## Visual QA",
            "",
            "- `manual_visual_review`: `REQUIRED`",
            "- Do not promote this to B1 material PASS until contact-sheet and overlay QA are accepted.",
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
    )
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

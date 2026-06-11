#!/usr/bin/env python3
"""Build layer-alpha seed clean-base candidates for character-002.

v1 used broad feathered ovals for clean sockets and mouth cleanup. That fixed
some baked pixels but still looked like pasted skin patches in overlay QA. This
This candidate keeps the source-front and expression assets, but limits clean
base alpha to already-normalized keypose layer alpha. It intentionally avoids
source-color skin and sclera thresholds that create rectangular patches.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
PACK0 = EXP / "material_pack_first_v0"
PACK2 = EXP / "material_pack_first_v5_layer_alpha_seed_strict_expr"
RAW = PACK0 / "raw_outputs"
SRC_LAYERS = PACK0 / "normalized_layers"
LAYERS = PACK2 / "normalized_layers"
REPORTS = EXP / "reports"
REPORT_DIR = REPORTS / "layer_alpha_seed_v5"
CANVAS = 2048


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_2048() -> Image.Image:
    return Image.open(RAW / "new_character_002_source_front.raw.png").convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)


def character_alpha(source: Image.Image) -> Image.Image:
    arr = np.asarray(source.convert("RGB"), dtype=np.uint8)
    non_bg = ~((arr[:, :, 0] > 247) & (arr[:, :, 1] > 247) & (arr[:, :, 2] > 247))
    alpha = (non_bg.astype(np.uint8) * 255)
    return Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(1))


def mask_from_layer_alpha(layer: Image.Image, kernel_size: int, blur: int) -> Image.Image:
    alpha = np.asarray(layer.getchannel("A"), dtype=np.uint8)
    _, mask_crop = cv2.threshold(alpha, 12, 255, cv2.THRESH_BINARY)
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    mask_crop = cv2.morphologyEx(mask_crop, cv2.MORPH_CLOSE, kernel)
    mask_crop = cv2.dilate(mask_crop, kernel, iterations=1)
    return Image.fromarray(mask_crop, "L").filter(ImageFilter.GaussianBlur(blur))


def cv_inpaint(source: Image.Image, mask: Image.Image, radius: int = 5) -> Image.Image:
    rgb = np.asarray(source.convert("RGB"), dtype=np.uint8)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    m = np.asarray(mask, dtype=np.uint8)
    _, m = cv2.threshold(m, 18, 255, cv2.THRESH_BINARY)
    out = cv2.inpaint(bgr, m, radius, cv2.INPAINT_TELEA)
    rgb_out = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb_out, "RGB").convert("RGBA")


def max_mask(*masks: Image.Image) -> Image.Image:
    arr = np.maximum.reduce([np.asarray(mask, dtype=np.uint8) for mask in masks])
    return Image.fromarray(arr, "L")


def patch_layer(inpainted: Image.Image, alpha: Image.Image) -> Image.Image:
    layer = inpainted.copy()
    layer.putalpha(alpha)
    return layer


def feature_only_layer(path: Path, asset_id: str) -> Image.Image:
    img = Image.open(path).convert("RGBA")
    arr = np.asarray(img).copy()
    rgb = arr[:, :, :3].astype(np.int16)
    alpha = arr[:, :, 3]
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    maxc = rgb.max(axis=2)
    minc = rgb.min(axis=2)
    sat = maxc - minc

    dark = maxc < 145
    strong_line = (r < 170) & (g < 135) & (b < 135)
    purple_eye = (b > 120) & (r > 80) & (g < 170) & (b > g + 20)
    pink_mouth = (r > 145) & (g < 152) & (b < 172) & (r > g + 30) & (r > b + 18)
    white_detail = (r > 210) & (g > 205) & (b > 195) & (sat < 45)

    if asset_id.startswith("eye_"):
        keep = dark | strong_line | purple_eye
        if asset_id.endswith("_open"):
            keep = keep | white_detail
    elif asset_id == "mouth_teeth":
        keep = dark | strong_line | white_detail
    elif asset_id.startswith("mouth_"):
        keep = dark | strong_line | pink_mouth
    else:
        keep = alpha > 0

    new_alpha = np.where(keep & (alpha > 0), alpha, 0).astype(np.uint8)
    arr[:, :, 3] = new_alpha
    return Image.fromarray(arr, "RGBA")


def save_mask_preview(mask: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mask.convert("RGBA").save(path)


def main() -> int:
    LAYERS.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    source = source_2048()
    source.putalpha(character_alpha(source))

    eye_l_seed = feature_only_layer(SRC_LAYERS / "eye_L_open.png", "eye_L_open")
    eye_r_seed = feature_only_layer(SRC_LAYERS / "eye_R_open.png", "eye_R_open")
    mouth_seed = feature_only_layer(SRC_LAYERS / "mouth_closed_smile.png", "mouth_closed_smile")
    eye_l_mask = mask_from_layer_alpha(eye_l_seed, kernel_size=17, blur=4)
    eye_r_mask = mask_from_layer_alpha(eye_r_seed, kernel_size=17, blur=4)
    mouth_mask = mask_from_layer_alpha(mouth_seed, kernel_size=9, blur=2)
    combined_mask = max_mask(eye_l_mask, eye_r_mask, mouth_mask)

    inpainted = cv_inpaint(source, combined_mask, radius=5)
    inpainted.putalpha(character_alpha(source))
    inpainted.save(REPORT_DIR / "source_front_2048_layer_alpha_seed_inpaint.png")
    save_mask_preview(eye_l_mask, REPORT_DIR / "layer_alpha_seed_eye_L_alpha.png")
    save_mask_preview(eye_r_mask, REPORT_DIR / "layer_alpha_seed_eye_R_alpha.png")
    save_mask_preview(mouth_mask, REPORT_DIR / "layer_alpha_seed_mouth_alpha.png")
    save_mask_preview(combined_mask, REPORT_DIR / "layer_alpha_seed_combined_alpha.png")

    copied: list[str] = []
    for src in sorted(SRC_LAYERS.glob("*.png")):
        out = LAYERS / src.name
        shutil.copy2(src, out)
        copied.append(src.stem)

    replace_layers: dict[str, Image.Image] = {
        "face_base_clean": inpainted,
        "eye_L_clean_socket": patch_layer(inpainted, eye_l_mask),
        "eye_R_clean_socket": patch_layer(inpainted, eye_r_mask),
        "eye_L_closed_underpaint": patch_layer(inpainted, eye_l_mask),
        "eye_R_closed_underpaint": patch_layer(inpainted, eye_r_mask),
        "mouth_base_clean": patch_layer(inpainted, mouth_mask),
    }
    for asset_id, layer in replace_layers.items():
        layer.save(LAYERS / f"{asset_id}.png")

    feature_filtered: list[str] = []
    for path in sorted(LAYERS.glob("*.png")):
        asset_id = path.stem
        if asset_id in replace_layers:
            continue
        if asset_id.startswith("eye_") or asset_id.startswith("mouth_"):
            feature_only_layer(path, asset_id).save(path)
            feature_filtered.append(asset_id)

    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment_id": "cubism-v2-new-character-002",
        "candidate_id": "material_pack_first_v5_layer_alpha_seed_strict_expr",
        "status": "LAYER_ALPHA_SEED_STRICT_EXPR_CANDIDATE_READY",
        "source": rel(RAW / "new_character_002_source_front.raw.png"),
        "source_inpainted": rel(REPORT_DIR / "source_front_2048_layer_alpha_seed_inpaint.png"),
        "feature_mask_preview": rel(REPORT_DIR / "layer_alpha_seed_combined_alpha.png"),
        "output_layers": rel(LAYERS),
        "copied_layers": copied,
        "replaced_layers": sorted(replace_layers),
        "feature_filtered_layers": feature_filtered,
        "human_review_basis": rel(REPORTS / "material_pack_first_overlay_human_review_20260609.md"),
        "note": "Clean-base alpha is limited to normalized keypose layer alpha to avoid broad oval or rectangular skin patch boundaries.",
    }
    save_json(REPORT_DIR / "feature_mask_clean_base_report.json", report)
    (REPORT_DIR / "feature_mask_clean_base_report.md").write_text(
        "\n".join(
            [
                "# Cubism v2 Character 002 Layer-Alpha-Seed Clean Bases",
                "",
                f"- status: `{report['status']}`",
                f"- output layers: `{report['output_layers']}`",
                f"- source inpainted: `{report['source_inpainted']}`",
                f"- mask preview: `{report['feature_mask_preview']}`",
                "",
                "## Replaced Layers",
                "",
                *[f"- `{asset_id}`" for asset_id in sorted(replace_layers)],
                "",
                "## Filtered Expression Layers",
                "",
                *[f"- `{asset_id}`" for asset_id in feature_filtered],
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "report": str(REPORT_DIR / "feature_mask_clean_base_report.json")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

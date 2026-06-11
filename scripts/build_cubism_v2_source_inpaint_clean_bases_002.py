#!/usr/bin/env python3
"""Build source-face inpaint clean-base candidates for character-002.

The previous material-pack-first candidates passed PNG validation but failed
human overlay review because clean sockets and mouth base looked like pasted
oval skin patches. This script keeps the selected source_front and expression
shapes, then creates a v1 candidate folder where:

- clean socket / underpaint / mouth base pixels come from source-face inpaint
- expression layers are filtered toward feature-only alpha, reducing skin patch
  carry-over from the generated close-up sheet
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
PACK0 = EXP / "material_pack_first_v0"
PACK1 = EXP / "material_pack_first_v1_source_inpaint"
RAW = PACK0 / "raw_outputs"
SRC_LAYERS = PACK0 / "normalized_layers"
LAYERS = PACK1 / "normalized_layers"
REPORTS = EXP / "reports"
REPORT_DIR = REPORTS / "source_inpaint_v1"
CANVAS = 2048


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def source_2048() -> Image.Image:
    return Image.open(RAW / "new_character_002_source_front.raw.png").convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)


def feathered_ellipse(box: tuple[int, int, int, int], blur: int = 18) -> Image.Image:
    mask = Image.new("L", (CANVAS, CANVAS), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(box, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(blur))


def hard_ellipse(box: tuple[int, int, int, int]) -> Image.Image:
    mask = Image.new("L", (CANVAS, CANVAS), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(box, fill=255)
    return mask


def character_alpha(source: Image.Image) -> Image.Image:
    arr = np.asarray(source.convert("RGB"), dtype=np.uint8)
    # White background removal with a soft bias: keep bright skin, remove only
    # near-white low-detail background.
    non_bg = ~((arr[:, :, 0] > 247) & (arr[:, :, 1] > 247) & (arr[:, :, 2] > 247))
    alpha = (non_bg.astype(np.uint8) * 255)
    alpha_img = Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(1))
    return alpha_img


def cv_inpaint(source: Image.Image, mask: Image.Image, radius: int = 7) -> Image.Image:
    rgb = np.asarray(source.convert("RGB"), dtype=np.uint8)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    m = np.asarray(mask, dtype=np.uint8)
    _, m = cv2.threshold(m, 16, 255, cv2.THRESH_BINARY)
    out = cv2.inpaint(bgr, m, radius, cv2.INPAINT_TELEA)
    rgb_out = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb_out, "RGB").convert("RGBA")


def patch_layer(inpainted: Image.Image, source: Image.Image, alpha: Image.Image) -> Image.Image:
    # Keep only the inpainted pixels inside a feathered mask.
    layer = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    layer_rgb = inpainted.copy()
    layer_rgb.putalpha(alpha)
    layer.alpha_composite(layer_rgb)
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
    pink_mouth = (r > 155) & (g < 170) & (b < 185) & (r > g + 20)
    white_detail = (r > 210) & (g > 205) & (b > 195) & (sat < 45)

    if asset_id.startswith("eye_"):
        keep = dark | strong_line | purple_eye
        if asset_id.endswith("_open"):
            keep = keep | white_detail
    elif asset_id == "mouth_teeth":
        keep = dark | strong_line | white_detail
    elif asset_id.startswith("mouth_"):
        keep = dark | strong_line | pink_mouth | white_detail
    else:
        keep = alpha > 0

    # Remove very faint sheet-antialias remnants.
    new_alpha = np.where(keep & (alpha > 0), alpha, 0).astype(np.uint8)
    arr[:, :, 3] = new_alpha
    return Image.fromarray(arr, "RGBA")


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    LAYERS.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    source = source_2048()
    src_alpha = character_alpha(source)

    # Masks are source-front coordinates after the previous overlay QA anchor
    # correction. Use hard masks for inpainting, feathered masks for layer alpha.
    eye_l_hard = hard_ellipse((805, 610, 965, 755))
    eye_r_hard = hard_ellipse((1095, 610, 1255, 755))
    mouth_hard = hard_ellipse((930, 785, 1115, 900))
    eye_l_soft = feathered_ellipse((792, 598, 978, 768), 14)
    eye_r_soft = feathered_ellipse((1082, 598, 1268, 768), 14)
    mouth_soft = feathered_ellipse((918, 775, 1128, 912), 16)

    combined_hard = Image.new("L", (CANVAS, CANVAS), 0)
    for m in [eye_l_hard, eye_r_hard, mouth_hard]:
        combined_hard = Image.fromarray(np.maximum(np.asarray(combined_hard), np.asarray(m)).astype(np.uint8), "L")

    inpainted = cv_inpaint(source, combined_hard, radius=9)
    inpainted.putalpha(src_alpha)
    (REPORT_DIR / "source_front_2048_inpaint_clean.png").parent.mkdir(parents=True, exist_ok=True)
    inpainted.save(REPORT_DIR / "source_front_2048_inpaint_clean.png")

    # Copy all current normalized layers first; then replace weak layers and
    # feature-filter expression layers.
    copied: list[str] = []
    for src in sorted(SRC_LAYERS.glob("*.png")):
        out = LAYERS / src.name
        shutil.copy2(src, out)
        copied.append(src.stem)

    replace_layers: dict[str, Image.Image] = {
        "face_base_clean": inpainted,
        "eye_L_clean_socket": patch_layer(inpainted, source, eye_l_soft),
        "eye_R_clean_socket": patch_layer(inpainted, source, eye_r_soft),
        "eye_L_closed_underpaint": patch_layer(inpainted, source, eye_l_soft),
        "eye_R_closed_underpaint": patch_layer(inpainted, source, eye_r_soft),
        "mouth_base_clean": patch_layer(inpainted, source, mouth_soft),
    }
    for asset_id, layer in replace_layers.items():
        layer.save(LAYERS / f"{asset_id}.png")

    # Filter expression assets so generated-sheet skin patches do not carry into
    # overlay QA. The inpainted clean base now supplies the skin underneath.
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
        "status": "SOURCE_INPAINT_CLEAN_BASE_CANDIDATE_READY",
        "source": rel(RAW / "new_character_002_source_front.raw.png"),
        "source_inpainted": rel(REPORT_DIR / "source_front_2048_inpaint_clean.png"),
        "output_layers": rel(LAYERS),
        "copied_layers": copied,
        "replaced_layers": sorted(replace_layers),
        "feature_filtered_layers": feature_filtered,
        "human_review_basis": rel(REPORTS / "material_pack_first_overlay_human_review_20260609.md"),
        "note": "This candidate attempts to remove pasted oval skin patches by using source-face inpaint and feature-only expression alpha.",
    }
    save_json(REPORT_DIR / "source_inpaint_clean_base_report.json", report)
    (REPORT_DIR / "source_inpaint_clean_base_report.md").write_text(
        "\n".join(
            [
                "# Cubism v2 Character 002 Source-Inpaint Clean Bases",
                "",
                f"- status: `{report['status']}`",
                f"- output layers: `{report['output_layers']}`",
                f"- source inpainted: `{report['source_inpainted']}`",
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
    print(json.dumps({"ok": True, "report": str(REPORT_DIR / "source_inpaint_clean_base_report.json")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

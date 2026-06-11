#!/usr/bin/env python3
"""Build a character-002 clean-base candidate from a model-edit source.

This keeps the good material_pack_first_v0 keypose set as the source of truth
for expression shapes, then replaces only the clean-base family with pixels from
a model-edited clean face. The goal is to return to the good contact-sheet
stage while removing overlay-only skin patch boundaries.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
PACK0 = EXP / "material_pack_first_v0"
SRC_LAYERS = PACK0 / "normalized_layers"
PACK = EXP / "model_edit_v2"
RAW = EXP / "model_edit_v1" / "raw_outputs"
LAYERS = PACK / "normalized_layers"
REPORTS = EXP / "reports" / "model_edit_v2"
CANVAS = 2048

MODEL_EDIT_RAW = RAW / "model_edit_clean_base_source.raw.png"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def alpha_coverage(image: Image.Image) -> float:
    alpha = np.asarray(image.getchannel("A"), dtype=np.uint8)
    return round(float((alpha > 0).sum()) / float(alpha.size), 8)


def character_alpha(image: Image.Image) -> Image.Image:
    rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    non_bg = ~((rgb[:, :, 0] > 247) & (rgb[:, :, 1] > 247) & (rgb[:, :, 2] > 247))
    alpha = (non_bg.astype(np.uint8) * 255)
    return Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(1))


def load_model_edit_clean() -> Image.Image:
    if not MODEL_EDIT_RAW.exists():
        raise SystemExit(f"missing model edit raw: {MODEL_EDIT_RAW}")
    clean = Image.open(MODEL_EDIT_RAW).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    clean.putalpha(character_alpha(clean))
    return clean


def mask_from_alpha(asset_ids: list[str], *, kernel_size: int, blur: int) -> Image.Image:
    merged = np.zeros((CANVAS, CANVAS), dtype=np.uint8)
    for asset_id in asset_ids:
        layer = Image.open(SRC_LAYERS / f"{asset_id}.png").convert("RGBA")
        alpha = np.asarray(layer.getchannel("A"), dtype=np.uint8)
        merged = np.maximum(merged, np.where(alpha > 12, 255, 0).astype(np.uint8))
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    merged = cv2.morphologyEx(merged, cv2.MORPH_CLOSE, kernel)
    merged = cv2.dilate(merged, kernel, iterations=1)
    return Image.fromarray(merged, "L").filter(ImageFilter.GaussianBlur(blur))


def patch_layer(clean: Image.Image, mask: Image.Image) -> Image.Image:
    out = clean.copy()
    out.putalpha(mask)
    return out


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
    eye_highlight = (r > 210) & (g > 205) & (b > 195) & (sat < 45)
    pink_mouth = (r > 145) & (g < 152) & (b < 172) & (r > g + 30) & (r > b + 18)
    teeth_white = (r > 205) & (g > 198) & (b > 188) & (sat < 65)

    if asset_id.startswith("eye_"):
        keep = dark | strong_line | purple_eye
        if asset_id.endswith("_open"):
            keep = keep | eye_highlight
    elif asset_id == "mouth_teeth":
        keep = dark | strong_line | teeth_white
    elif asset_id in {"mouth_inner", "mouth_tongue"}:
        keep = alpha > 0
    elif asset_id.startswith("mouth_"):
        keep = dark | strong_line | pink_mouth
    else:
        keep = alpha > 0

    arr[:, :, 3] = np.where(keep & (alpha > 0), alpha, 0).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def draw_contact_sheet(asset_ids: list[str], out: Path) -> None:
    tiles: list[Image.Image] = []
    for asset_id in asset_ids:
        image = Image.open(LAYERS / f"{asset_id}.png").convert("RGBA")
        bbox = image.getchannel("A").getbbox()
        if bbox:
            image = image.crop(bbox)
        image.thumbnail((220, 220), Image.Resampling.LANCZOS)
        tile = Image.new("RGBA", (260, 280), (248, 248, 248, 255))
        tile.alpha_composite(image, ((260 - image.width) // 2, 18))
        draw = ImageDraw.Draw(tile)
        draw.text((12, 238), asset_id[:30], fill=(30, 30, 30), font=ImageFont.load_default())
        tiles.append(tile)
    cols = 4
    sheet = Image.new("RGBA", (cols * 260, ((len(tiles) + cols - 1) // cols) * 280), (235, 235, 235, 255))
    for idx, tile in enumerate(tiles):
        sheet.alpha_composite(tile, ((idx % cols) * 260, (idx // cols) * 280))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out)


def main() -> int:
    LAYERS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    clean = load_model_edit_clean()
    clean.save(REPORTS / "model_edit_clean_base_source_2048_rgba.png")

    asset_ids = [src.stem for src in sorted(SRC_LAYERS.glob("*.png"))]
    for src in sorted(SRC_LAYERS.glob("*.png")):
        shutil.copy2(src, LAYERS / src.name)

    eye_l_mask = mask_from_alpha(["eye_L_open"], kernel_size=13, blur=4)
    eye_r_mask = mask_from_alpha(["eye_R_open"], kernel_size=13, blur=4)
    mouth_mask = mask_from_alpha(["mouth_closed_smile", "mouth_small_open", "mouth_o_vowel"], kernel_size=11, blur=4)

    replacements: dict[str, Image.Image] = {
        "face_base_clean": clean,
        "eye_L_clean_socket": patch_layer(clean, eye_l_mask),
        "eye_R_clean_socket": patch_layer(clean, eye_r_mask),
        "eye_L_closed_underpaint": patch_layer(clean, eye_l_mask),
        "eye_R_closed_underpaint": patch_layer(clean, eye_r_mask),
        "mouth_base_clean": patch_layer(clean, mouth_mask),
    }
    for asset_id, layer in replacements.items():
        layer.save(LAYERS / f"{asset_id}.png")

    # Keep v0 expression layers unchanged because the original contact sheet was
    # the visually preferred stage. Only clean-base family layers are replaced.
    filtered: list[str] = []

    draw_contact_sheet(asset_ids, REPORTS / "model_edit_v2_contact_sheet.png")

    rows: list[dict[str, Any]] = []
    for asset_id in asset_ids:
        image = Image.open(LAYERS / f"{asset_id}.png").convert("RGBA")
        bbox = image.getchannel("A").getbbox()
        rows.append(
            {
                "asset_id": asset_id,
                "path": rel(LAYERS / f"{asset_id}.png"),
                "alpha_bbox": list(bbox) if bbox else [],
                "alpha_coverage": alpha_coverage(image),
            }
        )

    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment_id": "cubism-v2-new-character-002",
        "candidate_id": "model_edit_v2_clean_base_from_material_pack_first_v0",
        "status": "MODEL_EDIT_CLEAN_BASE_CANDIDATE_READY_FOR_VALIDATOR",
        "basis": {
            "kept_good_contact_sheet": "experiments/cubism-v2-new-character-002/reports/material_pack_first_contact_sheet.png",
            "model_edit_raw": rel(MODEL_EDIT_RAW),
            "model_edit_clean_2048": rel(REPORTS / "model_edit_clean_base_source_2048_rgba.png"),
            "source_layers": rel(SRC_LAYERS),
        },
        "output_layers": rel(LAYERS),
        "contact_sheet": rel(REPORTS / "model_edit_v2_contact_sheet.png"),
        "replaced_layers": sorted(replacements),
        "feature_filtered_layers": filtered,
        "assets": rows,
        "note": "This candidate preserves material_pack_first_v0 expression shapes but replaces clean-base layers with a model-edited clean face source.",
    }
    save_json(REPORTS / "model_edit_v2_candidate_report.json", report)
    (REPORTS / "model_edit_v2_candidate_report.md").write_text(
        "\n".join(
            [
                "# Cubism v2 Character 002 Model-Edit v2 Clean Base Candidate",
                "",
                f"- status: `{report['status']}`",
                f"- output layers: `{report['output_layers']}`",
                f"- contact sheet: `{report['contact_sheet']}`",
                "",
                "## Replaced Layers",
                "",
                *[f"- `{asset_id}`" for asset_id in sorted(replacements)],
                "",
                "## Filtered Expression Layers",
                "",
                *[f"- `{asset_id}`" for asset_id in filtered],
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "report": str(REPORTS / "model_edit_v2_candidate_report.json")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

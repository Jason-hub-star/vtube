#!/usr/bin/env python3
"""Build model-edit v4 by removing skin alpha from mouth expressions only."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SRC = EXP / "model_edit_v3_hybrid" / "normalized_layers"
PACK = EXP / "model_edit_v4_mouth_alpha"
LAYERS = PACK / "normalized_layers"
REPORTS = EXP / "reports" / "model_edit_v4_mouth_alpha"
TARGET_MOUTHS = ["mouth_closed_smile", "mouth_small_open", "mouth_wide_open", "mouth_o_vowel"]
FEATURE_BOXES = {
    "mouth_closed_smile": (930, 785, 1158, 872),
    "mouth_small_open": (955, 795, 1118, 898),
    "mouth_wide_open": (900, 770, 1172, 922),
    "mouth_o_vowel": (960, 780, 1112, 912),
}


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def alpha_coverage(image: Image.Image) -> float:
    alpha = np.asarray(image.getchannel("A"), dtype=np.uint8)
    return round(float((alpha > 0).sum()) / float(alpha.size), 8)


def filter_mouth_alpha(path: Path, asset_id: str) -> Image.Image:
    img = Image.open(path).convert("RGBA")
    arr = np.asarray(img).copy()
    rgb = arr[:, :, :3].astype(np.int16)
    alpha = arr[:, :, 3]
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    maxc = rgb.max(axis=2)
    minc = rgb.min(axis=2)
    sat = maxc - minc

    dark = maxc < 130
    brown_line = (r < 172) & (g < 128) & (b < 128) & (r > g + 8)
    mouth_red = (r > 140) & (g < 158) & (b < 176) & (r > g + 32) & (r > b + 18) & (sat > 42)
    core = (dark | brown_line | mouth_red) & (alpha > 0)

    kernel = np.ones((17, 17), np.uint8)
    near_core = cv2.dilate(core.astype(np.uint8), kernel, iterations=1).astype(bool)
    white_detail = (r > 205) & (g > 195) & (b > 185) & (sat < 70) & near_core

    keep = (core | white_detail) & (alpha > 0)
    allowed = np.zeros_like(keep, dtype=bool)
    x1, y1, x2, y2 = FEATURE_BOXES[asset_id]
    allowed[y1:y2, x1:x2] = True
    keep = keep & allowed
    new_alpha = np.where(keep, alpha, 0).astype(np.uint8)
    arr[:, :, 3] = new_alpha
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
    asset_ids = [src.stem for src in sorted(SRC.glob("*.png"))]
    before_after: list[dict[str, Any]] = []
    for src in sorted(SRC.glob("*.png")):
        shutil.copy2(src, LAYERS / src.name)

    for asset_id in TARGET_MOUTHS:
        path = LAYERS / f"{asset_id}.png"
        before = Image.open(path).convert("RGBA")
        filtered = filter_mouth_alpha(path, asset_id)
        filtered.save(path)
        before_after.append(
            {
                "asset_id": asset_id,
                "before_alpha_bbox": list(before.getchannel("A").getbbox() or []),
                "after_alpha_bbox": list(filtered.getchannel("A").getbbox() or []),
                "before_alpha_coverage": alpha_coverage(before),
                "after_alpha_coverage": alpha_coverage(filtered),
            }
        )

    draw_contact_sheet(asset_ids, REPORTS / "model_edit_v4_mouth_alpha_contact_sheet.png")
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment_id": "cubism-v2-new-character-002",
        "candidate_id": "model_edit_v4_mouth_alpha_filtered",
        "status": "MODEL_EDIT_MOUTH_ALPHA_CANDIDATE_READY_FOR_VALIDATOR",
        "source_layers": rel(SRC),
        "output_layers": rel(LAYERS),
        "contact_sheet": rel(REPORTS / "model_edit_v4_mouth_alpha_contact_sheet.png"),
        "filtered_mouth_layers": TARGET_MOUTHS,
        "before_after": before_after,
        "note": "Mouth alpha filtering removes skin-patch pixels while preserving dark/red/white mouth feature pixels near the mouth core.",
    }
    (REPORTS / "model_edit_v4_mouth_alpha_candidate_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "report": str(REPORTS / "model_edit_v4_mouth_alpha_candidate_report.json")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

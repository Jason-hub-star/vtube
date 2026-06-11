#!/usr/bin/env python3
"""Build model-edit v3 hybrid candidate.

Hybrid policy:
- keep model_edit_v2 clean-base and mouth layers because contact sheet quality is preferred
- filter only eye expression layers to reduce oval skin-patch boundaries in assembly QA
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SRC = EXP / "model_edit_v2" / "normalized_layers"
PACK = EXP / "model_edit_v3_hybrid"
LAYERS = PACK / "normalized_layers"
REPORTS = EXP / "reports" / "model_edit_v3_hybrid"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def feature_only_eye(path: Path, asset_id: str) -> Image.Image:
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
    highlight = (r > 210) & (g > 205) & (b > 195) & (sat < 45)
    keep = dark | strong_line | purple_eye
    if asset_id.endswith("_open"):
        keep = keep | highlight
    arr[:, :, 3] = np.where(keep & (alpha > 0), alpha, 0).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def draw_contact_sheet(asset_ids: list[str], out: Path) -> None:
    tiles = []
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
    for src in sorted(SRC.glob("*.png")):
        shutil.copy2(src, LAYERS / src.name)

    filtered = []
    for path in sorted(LAYERS.glob("eye_*.png")):
        asset_id = path.stem
        if asset_id.endswith("_clean_socket") or asset_id.endswith("_closed_underpaint"):
            continue
        feature_only_eye(path, asset_id).save(path)
        filtered.append(asset_id)

    draw_contact_sheet(asset_ids, REPORTS / "model_edit_v3_hybrid_contact_sheet.png")
    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment_id": "cubism-v2-new-character-002",
        "candidate_id": "model_edit_v3_hybrid_eye_filtered_mouth_v2",
        "status": "MODEL_EDIT_HYBRID_CANDIDATE_READY_FOR_VALIDATOR",
        "source_layers": rel(SRC),
        "output_layers": rel(LAYERS),
        "contact_sheet": rel(REPORTS / "model_edit_v3_hybrid_contact_sheet.png"),
        "filtered_eye_layers": filtered,
        "note": "Hybrid keeps v2 clean-base and mouth layers, filters only eye expression layers to reduce assembly skin-patch boundaries.",
    }
    (REPORTS / "model_edit_v3_hybrid_candidate_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "report": str(REPORTS / "model_edit_v3_hybrid_candidate_report.json")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

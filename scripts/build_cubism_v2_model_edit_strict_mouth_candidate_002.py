#!/usr/bin/env python3
"""Build model-edit v4 strict-mouth candidate.

Keeps the best current clean base and eye set from model_edit_v3_hybrid, then
replaces only the four mouth expression layers with the cleaner strict-alpha
mouth layers from the earlier layer_alpha_seed_v5 candidate.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
BASE = EXP / "model_edit_v3_hybrid" / "normalized_layers"
STRICT = EXP / "material_pack_first_v5_layer_alpha_seed_strict_expr" / "normalized_layers"
PACK = EXP / "model_edit_v4_strict_mouth"
LAYERS = PACK / "normalized_layers"
REPORTS = EXP / "reports" / "model_edit_v4_strict_mouth"
STRICT_MOUTHS = ["mouth_closed_smile", "mouth_small_open", "mouth_wide_open", "mouth_o_vowel"]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def alpha_coverage(image: Image.Image) -> float:
    alpha = image.getchannel("A")
    hist = alpha.histogram()
    return round(float(sum(hist[1:])) / float(alpha.width * alpha.height), 8)


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
    asset_ids = [src.stem for src in sorted(BASE.glob("*.png"))]
    for src in sorted(BASE.glob("*.png")):
        shutil.copy2(src, LAYERS / src.name)

    replacements: list[dict[str, Any]] = []
    for asset_id in STRICT_MOUTHS:
        src = STRICT / f"{asset_id}.png"
        dst = LAYERS / f"{asset_id}.png"
        before = Image.open(dst).convert("RGBA")
        after = Image.open(src).convert("RGBA")
        shutil.copy2(src, dst)
        replacements.append(
            {
                "asset_id": asset_id,
                "source": rel(src),
                "before_alpha_bbox": list(before.getchannel("A").getbbox() or []),
                "after_alpha_bbox": list(after.getchannel("A").getbbox() or []),
                "before_alpha_coverage": alpha_coverage(before),
                "after_alpha_coverage": alpha_coverage(after),
            }
        )

    draw_contact_sheet(asset_ids, REPORTS / "model_edit_v4_strict_mouth_contact_sheet.png")
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment_id": "cubism-v2-new-character-002",
        "candidate_id": "model_edit_v4_strict_mouth",
        "status": "MODEL_EDIT_STRICT_MOUTH_CANDIDATE_READY_FOR_VALIDATOR",
        "base_layers": rel(BASE),
        "strict_mouth_layers": rel(STRICT),
        "output_layers": rel(LAYERS),
        "contact_sheet": rel(REPORTS / "model_edit_v4_strict_mouth_contact_sheet.png"),
        "replacements": replacements,
        "note": "Best current clean base/eye candidate with strict-alpha mouth expression layers.",
    }
    (REPORTS / "model_edit_v4_strict_mouth_candidate_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "report": str(REPORTS / "model_edit_v4_strict_mouth_candidate_report.json")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

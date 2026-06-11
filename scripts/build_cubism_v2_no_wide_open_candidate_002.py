#!/usr/bin/env python3
"""Build character-002 candidate that excludes the bad wide-open mouth visually."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SRC = EXP / "model_edit_v5_manual_aligned" / "normalized_layers"
PACK = EXP / "model_edit_v6_no_wide_open"
LAYERS = PACK / "normalized_layers"
REPORTS = EXP / "reports/model_edit_v6_no_wide_open"
EXCLUDED = {"mouth_wide_open"}


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def draw_contact_sheet(asset_ids: list[str], out: Path) -> None:
    tiles: list[Image.Image] = []
    for asset_id in asset_ids:
        if asset_id in EXCLUDED:
            continue
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
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * 260, rows * 280), (235, 235, 235, 255))
    for idx, tile in enumerate(tiles):
        sheet.alpha_composite(tile, ((idx % cols) * 260, (idx // cols) * 280))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out)


def main() -> int:
    LAYERS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    asset_ids = [path.stem for path in sorted(SRC.glob("*.png"))]
    for src in sorted(SRC.glob("*.png")):
        shutil.copy2(src, LAYERS / src.name)

    contact_sheet = REPORTS / "model_edit_v6_no_wide_open_contact_sheet.png"
    draw_contact_sheet(asset_ids, contact_sheet)
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment_id": "cubism-v2-new-character-002",
        "candidate_id": "model_edit_v6_no_wide_open",
        "status": "NO_WIDE_OPEN_CANDIDATE_READY_FOR_QA",
        "source_layers": rel(SRC),
        "output_layers": rel(LAYERS),
        "excluded_visual_parts": sorted(EXCLUDED),
        "contact_sheet": rel(contact_sheet),
        "policy": "mouth_wide_open is preserved as evidence in normalized_layers but excluded from visual QA sheets and Mini Cubism diagnostic preview because 주인님 judged the generated image itself visually wrong.",
    }
    (REPORTS / "model_edit_v6_no_wide_open_candidate_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (REPORTS / "model_edit_v6_no_wide_open_candidate_report.md").write_text(
        "\n".join(
            [
                "# Model Edit v6 No Wide Open",
                "",
                f"- status: `{report['status']}`",
                f"- excluded visual parts: `{report['excluded_visual_parts']}`",
                f"- contact sheet: `{report['contact_sheet']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "report": str(REPORTS / "model_edit_v6_no_wide_open_candidate_report.json")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

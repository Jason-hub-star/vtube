#!/usr/bin/env python3
"""Apply saved manual eye/mouth anchor alignment to character-002 keypose layers."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SRC = EXP / "model_edit_v4_strict_mouth" / "normalized_layers"
OVERRIDES = EXP / "reports/model_edit_v4_strict_mouth/manual_alignment_v1/manual_keypose_alignment_overrides.json"
PACK = EXP / "model_edit_v5_manual_aligned"
LAYERS = PACK / "normalized_layers"
REPORTS = EXP / "reports/model_edit_v5_manual_aligned"
CANVAS = (2048, 2048)


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def alpha_bbox(image: Image.Image) -> list[int] | None:
    bbox = image.convert("RGBA").getchannel("A").getbbox()
    if not bbox:
        return None
    left, top, right, bottom = bbox
    return [left, top, right, bottom]


def center_of_bbox(bbox: list[int]) -> tuple[float, float]:
    return ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)


def coverage(image: Image.Image) -> float:
    alpha = image.convert("RGBA").getchannel("A")
    return round(sum(alpha.histogram()[1:]) / float(alpha.width * alpha.height), 8)


def transform_layer(source: Image.Image, source_origin: tuple[float, float], target_anchor: tuple[float, float], scale: float) -> Image.Image:
    rgba = source.convert("RGBA")
    bbox = alpha_bbox(rgba)
    if bbox is None:
        return Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    left, top, right, bottom = bbox
    crop = rgba.crop((left, top, right, bottom))
    new_w = max(1, int(round(crop.width * scale)))
    new_h = max(1, int(round(crop.height * scale)))
    resized = crop.resize((new_w, new_h), Image.Resampling.LANCZOS)
    src_cx, src_cy = source_origin
    dst_x = int(round(target_anchor[0] + (left - src_cx) * scale))
    dst_y = int(round(target_anchor[1] + (top - src_cy) * scale))
    out = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    out.alpha_composite(resized, (dst_x, dst_y))
    return out


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
    overrides = json.loads(OVERRIDES.read_text())
    LAYERS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    asset_ids = [path.stem for path in sorted(SRC.glob("*.png"))]
    for src in sorted(SRC.glob("*.png")):
        shutil.copy2(src, LAYERS / src.name)

    adjustments: list[dict[str, Any]] = []
    for group_id, group in sorted((overrides.get("groups") or {}).items()):
        preview_part = group["preview_part"]
        preview_image = Image.open(SRC / f"{preview_part}.png").convert("RGBA")
        preview_bbox = alpha_bbox(preview_image)
        if preview_bbox is None:
            raise SystemExit(f"preview part has no alpha: {preview_part}")
        source_origin = center_of_bbox(preview_bbox)
        target_anchor = (float(group["anchor"][0]), float(group["anchor"][1]))
        scale = float(group["scale"])
        for part_id in group.get("parts") or []:
            src = SRC / f"{part_id}.png"
            if not src.exists():
                continue
            before = Image.open(src).convert("RGBA")
            after = transform_layer(before, source_origin, target_anchor, scale)
            after.save(LAYERS / f"{part_id}.png")
            adjustments.append(
                {
                    "group_id": group_id,
                    "part_id": part_id,
                    "preview_part": preview_part,
                    "source_origin": [round(source_origin[0], 3), round(source_origin[1], 3)],
                    "target_anchor": [round(target_anchor[0], 3), round(target_anchor[1], 3)],
                    "scale": scale,
                    "before_alpha_bbox": alpha_bbox(before),
                    "after_alpha_bbox": alpha_bbox(after),
                    "before_alpha_coverage": coverage(before),
                    "after_alpha_coverage": coverage(after),
                }
            )

    contact_sheet = REPORTS / "model_edit_v5_manual_aligned_contact_sheet.png"
    draw_contact_sheet(asset_ids, contact_sheet)
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment_id": "cubism-v2-new-character-002",
        "candidate_id": "model_edit_v5_manual_aligned",
        "status": "MANUAL_ALIGNED_CANDIDATE_READY_FOR_VALIDATOR",
        "source_layers": rel(SRC),
        "manual_overrides": rel(OVERRIDES),
        "output_layers": rel(LAYERS),
        "contact_sheet": rel(contact_sheet),
        "adjustment_count": len(adjustments),
        "adjustments": adjustments,
        "note": "Applies saved manual eye/mouth anchors and scales. This is material alignment evidence, not final Cubism authoring.",
    }
    (REPORTS / "model_edit_v5_manual_aligned_candidate_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (REPORTS / "model_edit_v5_manual_aligned_candidate_report.md").write_text(
        "\n".join(
            [
                "# Model Edit v5 Manual Aligned Candidate",
                "",
                f"- status: `{report['status']}`",
                f"- output layers: `{report['output_layers']}`",
                f"- contact sheet: `{report['contact_sheet']}`",
                f"- adjustments: `{report['adjustment_count']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "report": str(REPORTS / "model_edit_v5_manual_aligned_candidate_report.json")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

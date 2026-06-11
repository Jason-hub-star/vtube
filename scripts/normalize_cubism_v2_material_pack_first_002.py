#!/usr/bin/env python3
"""Normalize character-002 material-pack-first raw outputs into 2048 RGBA layers.

This is a first-pass evidence builder, not a production art approval. It keeps
the generated raw sheets intact, crops the visible material candidates, removes
the white sheet background, and places each crop near the source-front feature
location on a 2048 canvas so the existing keypose validator can run.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
PACK = EXP / "material_pack_first_v0"
RAW = PACK / "raw_outputs"
LAYERS = PACK / "normalized_layers"
CROPS = PACK / "raw_crops"
REPORTS = EXP / "reports"

CANVAS_SIZE = 2048


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def remove_white_background(image: Image.Image, threshold: int = 246) -> Image.Image:
    rgba = image.convert("RGBA")
    arr = np.asarray(rgba).copy()
    rgb = arr[:, :, :3].astype(np.int16)
    white_distance = np.abs(rgb - 255).max(axis=2)
    alpha = np.where(white_distance <= (255 - threshold), 0, arr[:, :, 3])
    # Softly keep pale skin pixels that are not near border-white.
    alpha = np.where((rgb[:, :, 0] > 235) & (rgb[:, :, 1] > 225) & (rgb[:, :, 2] > 215), np.maximum(alpha, 190), alpha)
    # Force true white border/background transparent again.
    alpha = np.where((rgb[:, :, 0] >= 250) & (rgb[:, :, 1] >= 250) & (rgb[:, :, 2] >= 250), 0, alpha)
    arr[:, :, 3] = alpha.astype(np.uint8)
    out = Image.fromarray(arr, "RGBA")
    bbox = out.getchannel("A").getbbox()
    return out.crop(bbox) if bbox else out


def crop_sheet(path: Path, box: tuple[int, int, int, int], *, alpha: bool = True) -> Image.Image:
    crop = load_rgba(path).crop(box)
    return remove_white_background(crop) if alpha else crop


def fit_to_box(image: Image.Image, max_w: int, max_h: int) -> Image.Image:
    w, h = image.size
    scale = min(max_w / w, max_h / h)
    return image.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.Resampling.LANCZOS)


def place_on_canvas(image: Image.Image, center: tuple[int, int], max_size: tuple[int, int]) -> tuple[Image.Image, list[int]]:
    fitted = fit_to_box(image, *max_size)
    canvas = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    x = round(center[0] - fitted.size[0] / 2)
    y = round(center[1] - fitted.size[1] / 2)
    canvas.alpha_composite(fitted, (x, y))
    bbox = canvas.getchannel("A").getbbox()
    return canvas, list(bbox) if bbox else []


def alpha_coverage(image: Image.Image) -> float:
    alpha = np.asarray(image.getchannel("A"), dtype=np.uint8)
    return round(float((alpha > 0).sum()) / float(alpha.size), 8)


def draw_sheet(rows: list[dict[str, Any]], out: Path) -> None:
    thumbs: list[tuple[str, Image.Image]] = []
    for row in rows:
        image = load_rgba(ROOT / row["normalized_path"])
        bbox = image.getchannel("A").getbbox()
        if bbox:
            image = image.crop(bbox)
        image.thumbnail((220, 220), Image.Resampling.LANCZOS)
        tile = Image.new("RGBA", (260, 280), (248, 248, 248, 255))
        tile.alpha_composite(image, ((260 - image.size[0]) // 2, 18))
        draw = ImageDraw.Draw(tile)
        label = row["asset_id"]
        draw.text((12, 238), label[:30], fill=(30, 30, 30), font=ImageFont.load_default())
        thumbs.append((label, tile))
    cols = 4
    rows_count = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * 260, rows_count * 280), (235, 235, 235, 255))
    for idx, (_, tile) in enumerate(thumbs):
        sheet.alpha_composite(tile, ((idx % cols) * 260, (idx // cols) * 280))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out)


def main() -> int:
    source = RAW / "new_character_002_source_front.raw.png"
    closeups = RAW / "material_keypose_pack_closeups.raw.png"
    fullface = RAW / "material_keypose_pack_fullface.raw.png"
    for path in [source, closeups, fullface]:
        if not path.exists():
            raise SystemExit(f"missing raw input: {path}")

    LAYERS.mkdir(parents=True, exist_ok=True)
    CROPS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    # Coordinates are measured on the generated close-up sheet.
    # Anchors are measured on the normalized 2048 source_front. The first pass
    # used sheet-local visual centers and landed too far left/up in overlay QA.
    eye_l = (880, 687)
    eye_r = (1170, 687)
    mouth = (1035, 845)
    specs: list[dict[str, Any]] = [
        {"asset_id": "face_base_clean", "source": fullface, "box": (512, 930, 760, 1220), "center": (1024, 980), "max": (980, 1160), "alpha": True},
        {"asset_id": "eye_L_open", "source": closeups, "box": (40, 60, 290, 190), "center": eye_l, "max": (260, 140), "alpha": True},
        {"asset_id": "eye_R_open", "source": closeups, "box": (390, 60, 640, 190), "center": eye_r, "max": (260, 140), "alpha": True},
        {"asset_id": "eye_L_clean_socket", "source": closeups, "box": (690, 45, 910, 170), "center": eye_l, "max": (220, 120), "alpha": True},
        {"asset_id": "eye_R_clean_socket", "source": closeups, "box": (990, 45, 1220, 170), "center": eye_r, "max": (220, 120), "alpha": True},
        {"asset_id": "eye_L_half_closed_lid", "source": closeups, "box": (40, 250, 285, 380), "center": eye_l, "max": (260, 135), "alpha": True},
        {"asset_id": "eye_R_half_closed_lid", "source": closeups, "box": (390, 250, 640, 380), "center": eye_r, "max": (260, 135), "alpha": True},
        {"asset_id": "eye_L_mostly_closed_lid", "source": closeups, "box": (55, 420, 290, 535), "center": eye_l, "max": (250, 120), "alpha": True},
        {"asset_id": "eye_R_mostly_closed_lid", "source": closeups, "box": (390, 420, 640, 535), "center": eye_r, "max": (250, 120), "alpha": True},
        {"asset_id": "eye_L_closed_lid", "source": closeups, "box": (70, 585, 290, 690), "center": eye_l, "max": (245, 115), "alpha": True},
        {"asset_id": "eye_R_closed_lid", "source": closeups, "box": (405, 585, 620, 690), "center": eye_r, "max": (245, 115), "alpha": True},
        {"asset_id": "eye_L_closed_underpaint", "source": closeups, "box": (710, 420, 900, 535), "center": eye_l, "max": (230, 130), "alpha": True},
        {"asset_id": "eye_R_closed_underpaint", "source": closeups, "box": (995, 420, 1175, 535), "center": eye_r, "max": (230, 130), "alpha": True},
        {"asset_id": "mouth_base_clean", "source": closeups, "box": (55, 720, 300, 850), "center": mouth, "max": (250, 135), "alpha": True},
        {"asset_id": "mouth_closed_smile", "source": closeups, "box": (380, 720, 600, 850), "center": mouth, "max": (230, 120), "alpha": True},
        {"asset_id": "mouth_small_open", "source": closeups, "box": (655, 725, 875, 850), "center": mouth, "max": (230, 120), "alpha": True},
        {"asset_id": "mouth_wide_open", "source": closeups, "box": (930, 720, 1145, 865), "center": mouth, "max": (240, 145), "alpha": True},
        {"asset_id": "mouth_o_vowel", "source": closeups, "box": (1225, 720, 1455, 850), "center": mouth, "max": (230, 130), "alpha": True},
        {"asset_id": "mouth_inner", "source": closeups, "box": (410, 880, 600, 1005), "center": mouth, "max": (215, 125), "alpha": True},
        {"asset_id": "mouth_teeth", "source": closeups, "box": (665, 880, 895, 1005), "center": mouth, "max": (230, 120), "alpha": True},
        {"asset_id": "mouth_tongue", "source": closeups, "box": (970, 880, 1135, 1005), "center": mouth, "max": (205, 120), "alpha": True},
    ]

    rows: list[dict[str, Any]] = []
    for spec in specs:
        crop = crop_sheet(spec["source"], spec["box"], alpha=spec["alpha"])
        crop_path = CROPS / f"{spec['asset_id']}.crop.png"
        crop.save(crop_path)
        layer, bbox = place_on_canvas(crop, spec["center"], spec["max"])
        out = LAYERS / f"{spec['asset_id']}.png"
        layer.save(out)
        rows.append(
            {
                "asset_id": spec["asset_id"],
                "source_raw": rel(spec["source"]),
                "source_box": list(spec["box"]),
                "crop_path": rel(crop_path),
                "normalized_path": rel(out),
                "canvas_size": [CANVAS_SIZE, CANVAS_SIZE],
                "placement_center": list(spec["center"]),
                "max_size": list(spec["max"]),
                "alpha_bbox": bbox,
                "alpha_coverage": alpha_coverage(layer),
                "evidence_status": "TECHNICAL_CANDIDATE_VISUAL_QA_REQUIRED",
            }
        )

    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment_id": "cubism-v2-new-character-002",
        "status": "TECHNICAL_CANDIDATES_READY_FOR_VALIDATOR",
        "note": "Generated material candidates are not visual PASS. They need contact-sheet review before Mini Cubism.",
        "raw_outputs": [rel(source), rel(closeups), rel(fullface)],
        "normalized_layers": len(rows),
        "assets": rows,
        "contact_sheet": rel(REPORTS / "material_pack_first_contact_sheet.png"),
    }
    (REPORTS / "material_pack_first_normalize_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (REPORTS / "material_pack_first_normalize_report.md").write_text(
        "\n".join(
            [
                "# Cubism v2 Character 002 Material-Pack-First Normalize Report",
                "",
                f"- status: `{report['status']}`",
                f"- normalized layers: `{len(rows)}`",
                f"- contact sheet: `{report['contact_sheet']}`",
                "",
                "These are technical candidates only. Visual QA is still required.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    draw_sheet(rows, REPORTS / "material_pack_first_contact_sheet.png")
    print(json.dumps({"ok": True, "layers": len(rows), "report": str(REPORTS / "material_pack_first_normalize_report.json")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

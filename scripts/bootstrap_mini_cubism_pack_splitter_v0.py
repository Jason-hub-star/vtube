#!/usr/bin/env python3
"""Bootstrap Mini Cubism pack-splitter-v0 experiment inputs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = ROOT / "experiments/mini-cubism-pack-splitter-v0-001"
CANVAS = [2048, 2048]

PACKS: dict[str, dict[str, Any]] = {
    "base_mannequin": {
        "source": "base_mannequin/canonical_base.png",
        "description": "Clean bald neutral bodysuit mannequin for rig-safe base tests.",
        "targets": {
            "head_base": [720, 270, 608, 610],
            "ear_L": [1292, 560, 128, 188],
            "ear_R": [628, 560, 128, 188],
            "neck": [898, 840, 252, 280],
            "torso_bodysuit": [650, 1050, 748, 800],
            "arm_L": [1320, 1120, 320, 760],
            "arm_R": [408, 1120, 320, 760],
        },
    },
    "hair_pack": {
        "source": "hair_pack/source_hair_pack.png",
        "description": "Detachable hair pack for physics-first split tests.",
        "targets": {
            "front_bang_L": [725, 245, 260, 430],
            "front_bang_C": [885, 190, 278, 500],
            "front_bang_R": [1062, 245, 260, 430],
            "side_lock_L": [1220, 430, 260, 760],
            "side_lock_R": [568, 430, 260, 760],
            "back_hair_base": [520, 150, 1008, 1190],
            "hair_tip_L": [1248, 1080, 250, 570],
            "hair_tip_R": [550, 1080, 250, 570],
        },
    },
    "outfit_pack": {
        "source": "outfit_pack/source_outfit_pack.png",
        "description": "Detachable neutral outfit pack for garment physics split tests.",
        "targets": {
            "collar": [790, 960, 468, 130],
            "chest_cloth": [665, 1075, 718, 460],
            "shoulder_L": [1210, 1065, 330, 230],
            "shoulder_R": [508, 1065, 330, 230],
            "sleeve_L": [1320, 1165, 330, 470],
            "sleeve_R": [398, 1165, 330, 470],
            "front_frill": [700, 1245, 648, 180],
            "ribbon_center": [944, 1120, 160, 140],
            "ribbon_L": [1090, 1130, 230, 180],
            "ribbon_R": [728, 1130, 230, 180],
        },
    },
    "accessory_pack": {
        "source": "accessory_pack/source_accessory_pack.png",
        "description": "Small detachable accessory pack for attach-point tests.",
        "targets": {
            "choker_base": [845, 925, 358, 78],
            "choker_gem": [970, 943, 108, 134],
            "earring_L": [1350, 735, 56, 130],
            "earring_R": [642, 735, 56, 130],
            "hairpin_L": [1190, 360, 116, 54],
            "hairpin_R": [742, 360, 116, 54],
        },
    },
    "keypose_asset_pack": {
        "source": "keypose_asset_pack/source_keypose_guide.png",
        "description": "Reference-only placeholders for eye and mouth keypose asset planning.",
        "targets": {
            "eye_open_L": [1055, 595, 220, 110],
            "eye_open_R": [773, 595, 220, 110],
            "mouth_closed": [942, 805, 164, 42],
            "mouth_half": [930, 805, 188, 82],
            "mouth_open": [918, 794, 212, 138],
        },
        "production_allowed": False,
    },
}

MODEL_CANDIDATES = [
    {"id": "layerd", "repo": "cyberagent/layerd-birefnet", "role": "primary layer decomposition"},
    {"id": "birefnet", "repo": "ZhengPeng7/BiRefNet", "role": "foreground alpha cleanup"},
    {"id": "birefnet_hr", "repo": "ZhengPeng7/BiRefNet_HR", "role": "high-resolution alpha cleanup"},
    {"id": "birefnet_matting", "repo": "ZhengPeng7/BiRefNet-matting", "role": "matting-oriented alpha cleanup"},
    {"id": "sam2_roi", "repo": "facebook/sam2.1-hiera-large", "role": "ROI box/point refinement"},
    {"id": "fashion_segformer", "repo": "Itbanque/fashion_segformer", "role": "outfit semantic hints"},
    {"id": "anime_instance", "repo": "dreMaz/AnimeInstanceSegmentation", "role": "anime character foreground sanity check"},
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def font(size: int) -> ImageFont.ImageFont:
    for candidate in [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def ellipse(draw: ImageDraw.ImageDraw, bbox: list[float], fill: tuple[int, int, int, int], outline: tuple[int, int, int, int] | None = None, width: int = 1) -> None:
    draw.ellipse([round(value) for value in bbox], fill=fill, outline=outline, width=width)


def rounded(draw: ImageDraw.ImageDraw, bbox: list[float], radius: int, fill: tuple[int, int, int, int], outline: tuple[int, int, int, int] | None = None, width: int = 1) -> None:
    draw.rounded_rectangle([round(value) for value in bbox], radius=radius, fill=fill, outline=outline, width=width)


def polygon(draw: ImageDraw.ImageDraw, points: list[tuple[float, float]], fill: tuple[int, int, int, int], outline: tuple[int, int, int, int] | None = None) -> None:
    draw.polygon([(round(x), round(y)) for x, y in points], fill=fill, outline=outline)


def draw_base() -> Image.Image:
    image = Image.new("RGBA", tuple(CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    skin = (248, 220, 207, 255)
    skin_line = (146, 102, 96, 160)
    suit = (205, 216, 232, 250)
    suit_line = (105, 122, 148, 180)
    ellipse(draw, [720, 270, 1328, 880], skin, skin_line, 4)
    ellipse(draw, [1292, 560, 1420, 748], skin, skin_line, 3)
    ellipse(draw, [628, 560, 756, 748], skin, skin_line, 3)
    ellipse(draw, [1328, 610, 1395, 720], (236, 172, 169, 170))
    ellipse(draw, [653, 610, 720, 720], (236, 172, 169, 170))
    rounded(draw, [898, 840, 1150, 1120], 90, skin, skin_line, 3)
    rounded(draw, [650, 1050, 1398, 1850], 95, suit, suit_line, 4)
    rounded(draw, [1320, 1120, 1640, 1880], 110, skin, skin_line, 3)
    rounded(draw, [408, 1120, 728, 1880], 110, skin, skin_line, 3)
    rounded(draw, [700, 1110, 1348, 1840], 80, (178, 194, 218, 230), suit_line, 3)
    draw.arc([800, 575, 990, 660], 195, 345, fill=(92, 62, 72, 220), width=8)
    draw.arc([1058, 575, 1248, 660], 195, 345, fill=(92, 62, 72, 220), width=8)
    draw.arc([940, 760, 1108, 838], 25, 155, fill=(132, 62, 72, 220), width=6)
    draw.line([(1024, 650), (1008, 742), (1044, 764)], fill=(150, 104, 96, 160), width=5)
    return image


def draw_hair() -> Image.Image:
    image = Image.new("RGBA", tuple(CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    navy = (18, 23, 43, 248)
    hi = (57, 70, 115, 170)
    ellipse(draw, [520, 150, 1528, 1340], navy, (8, 10, 20, 190), 5)
    for x0, x1, tip in [(725, 985, 640), (885, 1163, 700), (1062, 1322, 640)]:
        polygon(draw, [(x0, 260), (x1, 220), ((x0 + x1) / 2, tip)], navy, (8, 10, 20, 180))
        draw.line([((x0 + x1) / 2 - 38, 300), ((x0 + x1) / 2 - 12, tip - 60)], fill=hi, width=7)
    for side, x in [("L", 1220), ("R", 568)]:
        polygon(draw, [(x, 430), (x + 260, 470), (x + 210, 1190), (x + 130, 1520), (x + 42, 1190)], navy, (8, 10, 20, 180))
    polygon(draw, [(1248, 1080), (1498, 1080), (1390, 1650), (1315, 1520)], navy)
    polygon(draw, [(550, 1080), (800, 1080), (733, 1520), (658, 1650)], navy)
    return image.filter(ImageFilter.GaussianBlur(0.2))


def draw_outfit() -> Image.Image:
    image = Image.new("RGBA", tuple(CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    white = (250, 248, 252, 245)
    blue = (31, 62, 135, 240)
    shadow = (214, 220, 238, 200)
    gold = (190, 154, 82, 235)
    rounded(draw, [790, 960, 1258, 1090], 40, white, shadow, 3)
    rounded(draw, [665, 1075, 1383, 1535], 55, white, shadow, 3)
    rounded(draw, [1210, 1065, 1540, 1295], 60, white, shadow, 3)
    rounded(draw, [508, 1065, 838, 1295], 60, white, shadow, 3)
    rounded(draw, [1320, 1165, 1650, 1635], 72, white, shadow, 3)
    rounded(draw, [398, 1165, 728, 1635], 72, white, shadow, 3)
    for index in range(7):
        x = 700 + index * 92
        ellipse(draw, [x, 1245, x + 156, 1425], (255, 255, 255, 215), shadow, 2)
    polygon(draw, [(1024, 1120), (1104, 1190), (1024, 1260), (944, 1190)], blue, gold)
    polygon(draw, [(1090, 1130), (1320, 1188), (1110, 1310)], blue, (8, 18, 52, 180))
    polygon(draw, [(958, 1130), (728, 1188), (938, 1310)], blue, (8, 18, 52, 180))
    return image


def draw_accessory() -> Image.Image:
    image = Image.new("RGBA", tuple(CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    black = (27, 26, 34, 245)
    blue = (28, 103, 220, 245)
    gold = (194, 157, 86, 240)
    rounded(draw, [845, 925, 1203, 1003], 36, black, gold, 3)
    polygon(draw, [(1024, 943), (1078, 1010), (1024, 1077), (970, 1010)], blue, gold)
    for x in [642, 1350]:
        ellipse(draw, [x, 735, x + 56, 865], gold, (120, 92, 45, 220), 2)
    rounded(draw, [1190, 360, 1306, 414], 18, gold, (120, 92, 45, 220), 2)
    rounded(draw, [742, 360, 858, 414], 18, gold, (120, 92, 45, 220), 2)
    return image


def draw_keypose_guide() -> Image.Image:
    image = Image.new("RGBA", tuple(CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    line = (110, 54, 70, 210)
    ellipse(draw, [1055, 595, 1275, 705], (255, 255, 255, 230), line, 3)
    ellipse(draw, [773, 595, 993, 705], (255, 255, 255, 230), line, 3)
    draw.arc([942, 770, 1106, 848], 25, 155, fill=line, width=6)
    ellipse(draw, [930, 805, 1118, 887], (110, 45, 58, 180), line, 3)
    ellipse(draw, [918, 794, 1130, 932], (48, 20, 30, 200), line, 3)
    return image


def save_pack_source(exp: Path, pack_id: str) -> Path:
    source = exp / PACKS[pack_id]["source"]
    source.parent.mkdir(parents=True, exist_ok=True)
    image = {
        "base_mannequin": draw_base,
        "hair_pack": draw_hair,
        "outfit_pack": draw_outfit,
        "accessory_pack": draw_accessory,
        "keypose_asset_pack": draw_keypose_guide,
    }[pack_id]()
    image.save(source)
    return source


def build_preview(exp: Path) -> Path:
    canvas = Image.new("RGBA", tuple(CANVAS), (244, 241, 235, 255))
    for pack_id in ["base_mannequin", "hair_pack", "outfit_pack", "accessory_pack", "keypose_asset_pack"]:
        path = exp / PACKS[pack_id]["source"]
        canvas.alpha_composite(Image.open(path).convert("RGBA"))
    draw = ImageDraw.Draw(canvas)
    draw.text((36, 36), "Mini Cubism pack-splitter-v0 source composite", fill=(32, 32, 32, 255), font=font(30))
    out = exp / "reports" / "source_composite_preview.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap Mini Cubism pack-splitter-v0 experiment.")
    parser.add_argument("--experiment", default=str(DEFAULT_EXPERIMENT))
    args = parser.parse_args()

    exp = Path(args.experiment).resolve()
    exp.mkdir(parents=True, exist_ok=True)
    generated_sources: dict[str, str] = {}
    for pack_id in PACKS:
        source = save_pack_source(exp, pack_id)
        generated_sources[pack_id] = str(source)
        pack_manifest = {
            "schema_version": 1,
            "pack_id": pack_id,
            "generated_at": now(),
            "source_image": str(source),
            "description": PACKS[pack_id]["description"],
            "targets": [{"part_id": part_id, "roi": roi} for part_id, roi in PACKS[pack_id]["targets"].items()],
            "status": "BOOTSTRAPPED_PENDING_PROBE",
        }
        write_json(exp / pack_id / "candidate_manifest.json", pack_manifest)

    preview = build_preview(exp)
    manifest = {
        "schema_version": 1,
        "experiment_id": exp.name,
        "generated_at": now(),
        "status": "BOOTSTRAPPED_PENDING_PROBE",
        "canvas_size": CANVAS,
        "plan": str(ROOT / "docs/ref/MINI-CUBISM-PACK-SPLITTER-v0-PLAN.md"),
        "packs": {
            pack_id: {
                "source": generated_sources[pack_id],
                "description": spec["description"],
                "targets": spec["targets"],
                "production_allowed": spec.get("production_allowed", True),
            }
            for pack_id, spec in PACKS.items()
        },
        "model_candidates": MODEL_CANDIDATES,
        "qa_thresholds": {
            "minimum_candidate_parts": 24,
            "minimum_pack_count": 5,
            "require_contact_sheets": True,
            "project_promotion_requires": "pack_splitter_qa_report.status == PASS",
        },
        "outputs": {
            "source_composite_preview": str(preview),
        },
        "notes": [
            "This is a deterministic clean base/pack source bootstrap, not final character art.",
            "HF model probe outputs are candidate evidence until pack QA PASS.",
            "Do not create mini_cubism_project_pack_v0 before QA PASS.",
        ],
    }
    write_json(exp / "pack_splitter_manifest.json", manifest)
    write_json(exp / "reports" / "bootstrap_report.json", manifest)
    print(json.dumps({"ok": True, "experiment": str(exp), "packs": list(PACKS), "preview": str(preview)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

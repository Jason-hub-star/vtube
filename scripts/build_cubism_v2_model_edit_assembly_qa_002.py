#!/usr/bin/env python3
"""Build clean-base assembly QA sheets for character-002 model-edit candidate."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
DEFAULT_LAYERS = EXP / "model_edit_v1" / "normalized_layers"
DEFAULT_REPORT_DIR = EXP / "reports" / "model_edit_v1" / "assembly_qa"
CANVAS = 2048


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load(layers_dir: Path, asset_id: str) -> Image.Image:
    return Image.open(layers_dir / f"{asset_id}.png").convert("RGBA")


def composite(layers_dir: Path, asset_ids: list[str]) -> Image.Image:
    out = load(layers_dir, "face_base_clean")
    for asset_id in asset_ids:
        out.alpha_composite(load(layers_dir, asset_id))
    return out


def make_tile(label: str, image: Image.Image, roi: tuple[int, int, int, int]) -> Image.Image:
    view = image.crop(roi)
    view.thumbnail((390, 390), Image.Resampling.LANCZOS)
    tile = Image.new("RGBA", (420, 455), (248, 248, 248, 255))
    tile.alpha_composite(view, ((420 - view.width) // 2, 18))
    draw = ImageDraw.Draw(tile)
    draw.text((14, 420), label[:52], fill=(25, 25, 25), font=ImageFont.load_default())
    return tile


def build_sheet(items: list[dict[str, Any]], out: Path, cols: int) -> None:
    rows = (len(items) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * 420, rows * 455), (232, 232, 232, 255))
    for idx, item in enumerate(items):
        sheet.alpha_composite(make_tile(item["label"], item["image"], item["roi"]), ((idx % cols) * 420, (idx // cols) * 455))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--layers-dir", type=Path, default=DEFAULT_LAYERS)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--candidate-id", default="model_edit_v1_clean_base_from_material_pack_first_v0")
    parser.add_argument("--exclude-mouth-wide-open", action="store_true")
    args = parser.parse_args()
    layers_dir = args.layers_dir.resolve()
    report_dir = args.report_dir.resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    face_roi = (430, 260, 1220, 1020)
    eye_roi = (470, 440, 1180, 720)
    mouth_roi = (830, 735, 1240, 960)

    eye_states = [
        ("clean_base", []),
        ("open", ["eye_L_open", "eye_R_open"]),
        ("half_closed", ["eye_L_half_closed_lid", "eye_R_half_closed_lid"]),
        ("mostly_closed", ["eye_L_mostly_closed_lid", "eye_R_mostly_closed_lid"]),
        ("closed", ["eye_L_closed_underpaint", "eye_R_closed_underpaint", "eye_L_closed_lid", "eye_R_closed_lid"]),
        ("closed_lids_only", ["eye_L_closed_lid", "eye_R_closed_lid"]),
    ]
    mouth_states = [
        ("clean_base", []),
        ("closed_smile", ["mouth_closed_smile"]),
        ("small_open", ["mouth_small_open"]),
        ("o_vowel", ["mouth_o_vowel"]),
        ("inner_teeth_tongue", ["mouth_inner", "mouth_teeth", "mouth_tongue"]),
    ]
    if not args.exclude_mouth_wide_open:
        mouth_states.insert(3, ("wide_open", ["mouth_wide_open"]))
        mouth_states.append(("wide_inner_tongue", ["mouth_inner", "mouth_tongue", "mouth_wide_open"]))

    rows: list[dict[str, Any]] = []
    eye_items = []
    face_items = []
    for label, assets in eye_states:
        image = composite(layers_dir, assets)
        out = report_dir / f"eye_{label}.png"
        image.save(out)
        eye_items.append({"label": label, "image": image, "roi": eye_roi})
        face_items.append({"label": label, "image": image, "roi": face_roi})
        rows.append({"group": "eye", "state": label, "assets": assets, "image": rel(out)})
    build_sheet(eye_items, report_dir / "eye_assembly_qa_sheet.png", cols=3)
    build_sheet(face_items, report_dir / "face_assembly_qa_sheet.png", cols=2)

    mouth_items = []
    for label, assets in mouth_states:
        image = composite(layers_dir, assets)
        out = report_dir / f"mouth_{label}.png"
        image.save(out)
        mouth_items.append({"label": label, "image": image, "roi": mouth_roi})
        rows.append({"group": "mouth", "state": label, "assets": assets, "image": rel(out)})
    build_sheet(mouth_items, report_dir / "mouth_assembly_qa_sheet.png", cols=3)

    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment_id": "cubism-v2-new-character-002",
        "candidate_id": args.candidate_id,
        "status": "ASSEMBLY_QA_READY_FOR_VISUAL_REVIEW",
        "layers_dir": rel(layers_dir),
        "excluded_visual_parts": ["mouth_wide_open"] if args.exclude_mouth_wide_open else [],
        "sheets": {
            "eye_assembly_qa_sheet": rel(report_dir / "eye_assembly_qa_sheet.png"),
            "face_assembly_qa_sheet": rel(report_dir / "face_assembly_qa_sheet.png"),
            "mouth_assembly_qa_sheet": rel(report_dir / "mouth_assembly_qa_sheet.png"),
        },
        "rows": rows,
    }
    (report_dir / "model_edit_assembly_qa_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (report_dir / "model_edit_assembly_qa_report.md").write_text(
        "\n".join(
            [
                "# Cubism v2 Character 002 Model-Edit v1 Assembly QA",
                "",
                f"- status: `{report['status']}`",
                f"- eye: `{report['sheets']['eye_assembly_qa_sheet']}`",
                f"- face: `{report['sheets']['face_assembly_qa_sheet']}`",
                f"- mouth: `{report['sheets']['mouth_assembly_qa_sheet']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "report": str(report_dir / "model_edit_assembly_qa_report.json")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build overlay QA sheets for character-002 material-pack-first candidates."""

from __future__ import annotations

import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
PACK = EXP / "material_pack_first_v0"
RAW = PACK / "raw_outputs"
REPORTS = EXP / "reports"
DEFAULT_LAYERS = PACK / "normalized_layers"
DEFAULT_OVERLAY_DIR = REPORTS / "overlay_qa"
CANVAS = 2048


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_layer(layers_dir: Path, asset_id: str) -> Image.Image:
    return Image.open(layers_dir / f"{asset_id}.png").convert("RGBA")


def source_canvas() -> Image.Image:
    raw = Image.open(RAW / "new_character_002_source_front.raw.png").convert("RGBA")
    return raw.resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)


def composite(base: Image.Image, layers_dir: Path, asset_ids: list[str]) -> Image.Image:
    out = base.copy()
    for asset_id in asset_ids:
        out.alpha_composite(load_layer(layers_dir, asset_id))
    return out


def crop_roi(image: Image.Image, roi: tuple[int, int, int, int]) -> Image.Image:
    return image.crop(roi)


def make_tile(label: str, image: Image.Image, roi: tuple[int, int, int, int] | None = None) -> Image.Image:
    view = crop_roi(image, roi) if roi else image.copy()
    view.thumbnail((390, 390), Image.Resampling.LANCZOS)
    tile = Image.new("RGBA", (420, 455), (248, 248, 248, 255))
    tile.alpha_composite(view, ((420 - view.width) // 2, 18))
    draw = ImageDraw.Draw(tile)
    draw.text((14, 420), label[:52], fill=(25, 25, 25), font=ImageFont.load_default())
    return tile


def build_sheet(items: list[dict[str, Any]], out_path: Path, *, cols: int = 3) -> None:
    rows = (len(items) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * 420, rows * 455), (232, 232, 232, 255))
    for idx, item in enumerate(items):
        sheet.alpha_composite(make_tile(item["label"], item["image"], item.get("roi")), ((idx % cols) * 420, (idx // cols) * 455))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--layers-dir", type=Path, default=DEFAULT_LAYERS)
    parser.add_argument("--overlay-dir", type=Path, default=DEFAULT_OVERLAY_DIR)
    parser.add_argument("--report-json", type=Path, default=REPORTS / "material_pack_first_overlay_qa_report.json")
    parser.add_argument("--report-md", type=Path, default=REPORTS / "material_pack_first_overlay_qa_report.md")
    parser.add_argument("--candidate-id", default="material_pack_first_v0")
    args = parser.parse_args()

    layers_dir = args.layers_dir.resolve()
    overlay_dir = args.overlay_dir.resolve()
    overlay_dir.mkdir(parents=True, exist_ok=True)
    base = source_canvas()
    base_path = overlay_dir / "source_front_2048.png"
    base.save(base_path)

    eye_roi = (470, 440, 1180, 720)
    mouth_roi = (830, 735, 1240, 960)
    face_roi = (430, 260, 1220, 1020)

    eye_states = [
        ("source", []),
        ("open_overlay", ["eye_L_open", "eye_R_open"]),
        ("clean_socket_only", ["eye_L_clean_socket", "eye_R_clean_socket"]),
        ("clean_socket_plus_half", ["eye_L_clean_socket", "eye_R_clean_socket", "eye_L_half_closed_lid", "eye_R_half_closed_lid"]),
        ("clean_socket_plus_mostly", ["eye_L_clean_socket", "eye_R_clean_socket", "eye_L_mostly_closed_lid", "eye_R_mostly_closed_lid"]),
        ("underpaint_plus_closed", ["eye_L_closed_underpaint", "eye_R_closed_underpaint", "eye_L_closed_lid", "eye_R_closed_lid"]),
        ("closed_lid_only", ["eye_L_closed_lid", "eye_R_closed_lid"]),
        ("face_base_clean", ["face_base_clean"]),
    ]
    mouth_states = [
        ("source", []),
        ("mouth_base_clean_only", ["mouth_base_clean"]),
        ("closed_smile", ["mouth_base_clean", "mouth_closed_smile"]),
        ("small_open", ["mouth_base_clean", "mouth_small_open"]),
        ("wide_open", ["mouth_base_clean", "mouth_wide_open"]),
        ("o_vowel", ["mouth_base_clean", "mouth_o_vowel"]),
        ("inner_teeth_tongue_stack", ["mouth_base_clean", "mouth_inner", "mouth_teeth", "mouth_tongue"]),
        ("wide_inner_tongue", ["mouth_base_clean", "mouth_inner", "mouth_tongue", "mouth_wide_open"]),
    ]

    rows: list[dict[str, Any]] = []
    eye_items = []
    for label, assets in eye_states:
        image = composite(base, layers_dir, assets)
        out = overlay_dir / f"eye_{label}.png"
        image.save(out)
        eye_items.append({"label": label, "image": image, "roi": eye_roi})
        rows.append({"group": "eye", "state": label, "assets": assets, "image": rel(out), "roi": list(eye_roi)})
    build_sheet(eye_items, overlay_dir / "eye_overlay_qa_sheet.png")

    face_items = []
    for label, assets in eye_states:
        image = composite(base, layers_dir, assets)
        face_items.append({"label": label, "image": image, "roi": face_roi})
    build_sheet(face_items, overlay_dir / "face_overlay_qa_sheet.png", cols=2)

    mouth_items = []
    for label, assets in mouth_states:
        image = composite(base, layers_dir, assets)
        out = overlay_dir / f"mouth_{label}.png"
        image.save(out)
        mouth_items.append({"label": label, "image": image, "roi": mouth_roi})
        rows.append({"group": "mouth", "state": label, "assets": assets, "image": rel(out), "roi": list(mouth_roi)})
    build_sheet(mouth_items, overlay_dir / "mouth_overlay_qa_sheet.png")

    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment_id": "cubism-v2-new-character-002",
        "candidate_id": args.candidate_id,
        "status": "OVERLAY_QA_REVISE_MINI_CUBISM_BLOCKED",
        "layers_dir": rel(layers_dir),
        "source_front_2048": rel(base_path),
        "sheets": {
            "eye_overlay_qa_sheet": rel(overlay_dir / "eye_overlay_qa_sheet.png"),
            "face_overlay_qa_sheet": rel(overlay_dir / "face_overlay_qa_sheet.png"),
            "mouth_overlay_qa_sheet": rel(overlay_dir / "mouth_overlay_qa_sheet.png"),
        },
        "rows": rows,
        "overlay_codex_judgement": {
            "status": "OVERLAY_QA_REVISE_MINI_CUBISM_BLOCKED",
            "reason": "Anchor placement is much improved after normalization correction, but eye clean sockets/underpaint and mouth_base_clean still create visible skin-patch boundaries on the source face.",
            "findings": [
                {
                    "area": "eye_open",
                    "status": "KEEP_FOR_REVIEW",
                    "note": "Open-eye candidates align near the real eyes after anchor correction, but scale/style still need human preference review."
                },
                {
                    "area": "eye_clean_socket_and_underpaint",
                    "status": "REVISE_OR_REGENERATE",
                    "note": "Skin patch boundaries are visible when composited over the source face."
                },
                {
                    "area": "eye_half_mostly_closed",
                    "status": "REVISE",
                    "note": "Blink states land in the correct area, but inherit the socket patch boundary problem."
                },
                {
                    "area": "mouth_anchor",
                    "status": "KEEP_FOR_REVIEW",
                    "note": "Mouth states are centered much better after anchor correction."
                },
                {
                    "area": "mouth_base_clean",
                    "status": "REVISE",
                    "note": "Mouth base removes the baked smile but has a visible oval patch boundary."
                },
                {
                    "area": "mouth_expression_shapes",
                    "status": "KEEP_FOR_REVIEW",
                    "note": "Closed, small-open, wide-open, O-vowel, inner, teeth, and tongue candidates are useful, but should be used only after mouth_base cleanup."
                }
            ],
            "blocked_next_step": "Mini Cubism diagnostic preview",
            "recommended_next_step": "Regenerate or edit clean sockets, closed underpaint, and mouth_base_clean with source-face inpaint/native clean-base context, then rerun overlay QA."
        },
    }
    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.report_md.write_text(
        "\n".join(
            [
                "# Cubism v2 Character 002 Overlay QA",
                "",
                f"- status: `{report['status']}`",
                f"- judgement: `{report['overlay_codex_judgement']['status']}`",
                "",
                "## Sheets",
                "",
                f"- eye: `{report['sheets']['eye_overlay_qa_sheet']}`",
                f"- face: `{report['sheets']['face_overlay_qa_sheet']}`",
                f"- mouth: `{report['sheets']['mouth_overlay_qa_sheet']}`",
                "",
                "## Findings",
                "",
                "| Area | Status | Note |",
                "|---|---|---|",
                *[
                    f"| `{row['area']}` | `{row['status']}` | {row['note']} |"
                    for row in report["overlay_codex_judgement"]["findings"]
                ],
                "",
                "## Decision",
                "",
                "- Do not proceed to Mini Cubism diagnostic preview yet.",
                "- Regenerate or edit clean sockets, closed underpaint, and `mouth_base_clean` with source-face inpaint/native clean-base context.",
                "- Rerun this overlay QA after cleanup.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "report": str(args.report_json)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

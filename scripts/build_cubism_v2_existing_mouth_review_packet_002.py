#!/usr/bin/env python3
"""Build a review packet from existing generated Character 002 mouth PNGs only."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
DEFAULT_ACTIVE_PARTS = EXP / "model_edit_v7_smooth_mouth_preview/mini_cubism_diagnostic_project/parts"
DEFAULT_WIDE_SOURCE = EXP / "model_edit_v6_no_wide_open/normalized_layers/mouth_wide_open.png"
DEFAULT_OUT = EXP / "reports/model_edit_v8_existing_mouth_packet"
CANVAS_SIZE = (2048, 2048)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_rgba(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    if image.size != CANVAS_SIZE:
        raise ValueError(f"expected {CANVAS_SIZE}, got {image.size}: {path}")
    return image


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def font(size: int) -> ImageFont.ImageFont:
    for candidate in [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def alpha_nonzero(image: Image.Image) -> int:
    return int(sum(image.getchannel("A").histogram()[1:]))


def fit_image(image: Image.Image, size: tuple[int, int], bg: str = "#202124") -> Image.Image:
    rgba = image.convert("RGBA")
    rgba.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, bg)
    canvas.paste(rgba.convert("RGB"), ((size[0] - rgba.width) // 2, (size[1] - rgba.height) // 2), rgba.getchannel("A"))
    return canvas


def neutral_face(parts_dir: Path) -> Image.Image:
    face = load_rgba(parts_dir / "face_base_clean.png")
    for part_id in ["eye_L_open", "eye_R_open"]:
        path = parts_dir / f"{part_id}.png"
        if path.exists():
            face.alpha_composite(load_rgba(path))
    return face


def mouth_review_crop(image: Image.Image, bbox: tuple[int, int, int, int] | None) -> Image.Image:
    if not bbox:
        bbox = (900, 800, 1160, 980)
    box = (
        max(0, bbox[0] - 150),
        max(0, bbox[1] - 125),
        min(CANVAS_SIZE[0], bbox[2] + 150),
        min(CANVAS_SIZE[1], bbox[3] + 125),
    )
    return image.crop(box)


def copy_existing_mouths(parts_dir: Path, wide_source: Path, out_layers: Path) -> list[dict[str, Any]]:
    out_layers.mkdir(parents=True, exist_ok=True)
    sources = [
        ("mouth_closed_smile", parts_dir / "mouth_closed_smile.png", "ACTIVE", "closed smile, current v7 closed state"),
        ("mouth_small_open", parts_dir / "mouth_small_open.png", "ACTIVE", "current v7 open state"),
        ("mouth_inner", parts_dir / "mouth_inner.png", "REFERENCE_ONLY", "existing inner-mouth helper, not active in v7 crossfade"),
        ("mouth_teeth", parts_dir / "mouth_teeth.png", "REFERENCE_ONLY", "existing teeth helper, not active in v7 crossfade"),
        ("mouth_tongue", parts_dir / "mouth_tongue.png", "REFERENCE_ONLY", "existing tongue helper, not active in v7 crossfade"),
        ("mouth_o_vowel", parts_dir / "mouth_o_vowel.png", "REJECTED_ACTIVE_EXCLUDED", "rejected because it reads as tiny centered O mouth"),
    ]
    if wide_source.exists():
        sources.append(("mouth_wide_open", wide_source, "REJECTED_ACTIVE_EXCLUDED", "rejected by 주인님 as visually awkward"))

    rows: list[dict[str, Any]] = []
    for part_id, source, policy, note in sources:
        image = load_rgba(source)
        target = out_layers / f"{part_id}.png"
        shutil.copy2(source, target)
        bbox = image.getbbox()
        rows.append(
            {
                "id": part_id,
                "source": str(source),
                "path": str(target),
                "policy": policy,
                "note": note,
                "mode": image.mode,
                "size": list(image.size),
                "bbox": list(bbox) if bbox else None,
                "alpha_nonzero": alpha_nonzero(image),
            }
        )
    return rows


def build_contact_sheet(face: Image.Image, rows: list[dict[str, Any]], out_path: Path) -> None:
    cell_w = 340
    cell_h = 610
    margin = 26
    header_h = 78
    cols = min(4, len(rows))
    rows_count = (len(rows) + cols - 1) // cols
    sheet = Image.new("RGB", (margin * 2 + cell_w * cols, margin * 2 + header_h + cell_h * rows_count), "#151719")
    draw = ImageDraw.Draw(sheet)
    title_font = font(24)
    label_font = font(17)
    small_font = font(13)
    draw.text((margin, margin), "Character 002 Existing Generated Mouth Packet", fill="#f1f3f4", font=title_font)
    draw.text(
        (margin, margin + 34),
        "No new mouth art generated. Active v7 states are separated from reference/rejected existing PNGs.",
        fill="#b8c0c8",
        font=small_font,
    )

    for index, row in enumerate(rows):
        col = index % cols
        row_index = index // cols
        x = margin + col * cell_w
        y = margin + header_h + row_index * cell_h
        mouth = load_rgba(Path(row["path"]))
        composite = face.copy()
        composite.alpha_composite(mouth)
        bbox = tuple(row["bbox"]) if row["bbox"] else None
        full = fit_image(composite, (cell_w - 22, 255), bg="#f0eee7")
        close = fit_image(mouth_review_crop(composite, bbox), (cell_w - 22, 128), bg="#f0eee7")
        isolated = fit_image(mouth_review_crop(mouth, bbox), (cell_w - 22, 112), bg="#202124")

        outline = "#5f9ea0" if row["policy"] == "ACTIVE" else "#8b6f3d" if row["policy"] == "REFERENCE_ONLY" else "#8b4a4a"
        draw.rounded_rectangle((x + 6, y + 6, x + cell_w - 6, y + cell_h - 6), radius=8, fill="#202124", outline=outline)
        draw.text((x + 16, y + 16), row["id"], fill="#f1f3f4", font=label_font)
        draw.text((x + 16, y + 40), row["policy"], fill="#b8c0c8", font=small_font)
        sheet.paste(full, (x + 11, y + 68))
        draw.text((x + 16, y + 328), "face close-up", fill="#b8c0c8", font=small_font)
        sheet.paste(close, (x + 11, y + 350))
        draw.text((x + 16, y + 482), "isolated layer crop", fill="#b8c0c8", font=small_font)
        sheet.paste(isolated, (x + 11, y + 504))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def validation_issues(rows: list[dict[str, Any]]) -> list[str]:
    issues = []
    for row in rows:
        if row["mode"] != "RGBA":
            issues.append(f"{row['id']}: mode is not RGBA")
        if row["size"] != list(CANVAS_SIZE):
            issues.append(f"{row['id']}: not full-canvas {CANVAS_SIZE}")
        if row["alpha_nonzero"] <= 0:
            issues.append(f"{row['id']}: empty alpha")
        if row["policy"] == "ACTIVE" and row["id"] not in {"mouth_closed_smile", "mouth_small_open"}:
            issues.append(f"{row['id']}: unexpected active mouth policy")
    return issues


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Character 002 Existing Generated Mouth Packet",
        "",
        f"- Status: `{report['status']}`",
        f"- Contact sheet: `{report['contact_sheet']}`",
        f"- Generated at: `{report['generated_at']}`",
        "",
        "## Decision",
        "",
        "- Proceed using existing generated mouth PNGs only.",
        "- Active v7 mouth states remain `mouth_closed_smile` and `mouth_small_open`.",
        "- `mouth_inner`, `mouth_teeth`, and `mouth_tongue` are preserved as references, but not active in the current v7 crossfade.",
        "- `mouth_o_vowel` and `mouth_wide_open` are preserved as evidence but excluded from active preview.",
        "",
        "## Mouth PNGs",
        "",
        "| ID | Policy | BBox | Source |",
        "|---|---|---|---|",
    ]
    for row in report["mouths"]:
        lines.append(f"| `{row['id']}` | `{row['policy']}` | `{row['bbox']}` | `{row['source']}` |")
    lines.extend(["", "## Validation", ""])
    if report["validation_issues"]:
        for issue in report["validation_issues"]:
            lines.append(f"- REVISE: {issue}")
    else:
        lines.append("- PASS: existing mouth PNGs are full-canvas 2048 RGBA and non-empty.")
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parts-dir", default=str(DEFAULT_ACTIVE_PARTS))
    parser.add_argument("--wide-source", default=str(DEFAULT_WIDE_SOURCE))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    parts_dir = Path(args.parts_dir).resolve()
    wide_source = Path(args.wide_source).resolve()
    out_dir = Path(args.out).resolve()
    layers_dir = out_dir / "normalized_layers"
    face = neutral_face(parts_dir)
    rows = copy_existing_mouths(parts_dir, wide_source, layers_dir)
    contact_sheet = out_dir / "existing_generated_mouth_contact_sheet.png"
    build_contact_sheet(face, rows, contact_sheet)
    issues = validation_issues(rows)
    status = "PASS_EXISTING_MOUTH_PACKET_READY_FOR_VISUAL_QA" if not issues else "REVISE_EXISTING_MOUTH_PACKET"
    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": status,
        "parts_dir": str(parts_dir),
        "layers_dir": str(layers_dir),
        "contact_sheet": str(contact_sheet),
        "validation_issues": issues,
        "mouths": rows,
        "active_policy": {
            "ParamMouthOpenY": ["mouth_closed_smile", "mouth_small_open"],
            "excluded_from_active": ["mouth_o_vowel", "mouth_wide_open"],
            "reference_only": ["mouth_inner", "mouth_teeth", "mouth_tongue"],
        },
    }
    report_path = out_dir / "existing_generated_mouth_packet_report.json"
    md_path = out_dir / "existing_generated_mouth_packet_report.md"
    write_json(report_path, report)
    write_markdown(report, md_path)
    print(
        json.dumps(
            {
                "ok": True,
                "status": status,
                "report": str(report_path),
                "markdown": str(md_path),
                "contact_sheet": str(contact_sheet),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

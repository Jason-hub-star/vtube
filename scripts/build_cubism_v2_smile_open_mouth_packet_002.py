#!/usr/bin/env python3
"""Build a smile-open-only mouth keypose packet for Character 002."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PARTS = (
    ROOT
    / "experiments"
    / "cubism-v2-new-character-002"
    / "model_edit_v7_smooth_mouth_preview"
    / "mini_cubism_diagnostic_project"
    / "parts"
)
DEFAULT_OUT = (
    ROOT
    / "experiments"
    / "cubism-v2-new-character-002"
    / "reports"
    / "model_edit_v8_smile_open_mouth_packet"
)
CANVAS_SIZE = (2048, 2048)


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
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def load_rgba(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    if image.size != CANVAS_SIZE:
        raise ValueError(f"expected {CANVAS_SIZE}, got {image.size}: {path}")
    return image


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    return image.getchannel("A").getbbox()


def sample_color(image: Image.Image, fallback: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    bbox = alpha_bbox(image)
    if not bbox:
        return fallback
    pixels = []
    rgba = image.load()
    for y in range(bbox[1], bbox[3], 3):
        for x in range(bbox[0], bbox[2], 3):
            if rgba[x, y][3] > 80:
                pixels.append(rgba[x, y])
    if not pixels:
        return fallback
    pixels.sort(key=lambda px: px[3], reverse=True)
    top = pixels[: max(1, len(pixels) // 5)]
    return tuple(int(sum(px[i] for px in top) / len(top)) for i in range(4))


def draw_soft_ellipse(mask_size: tuple[int, int], bbox: tuple[int, int, int, int], blur: float = 1.5) -> Image.Image:
    mask = Image.new("L", mask_size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(bbox, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(blur))


def quad_points(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    steps: int = 24,
) -> list[tuple[int, int]]:
    points = []
    for index in range(steps + 1):
        t = index / steps
        x = (1 - t) * (1 - t) * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) * (1 - t) * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        points.append((int(round(x)), int(round(y))))
    return points


def smile_opening_geometry(cx: int, cy: int, width: int, height: int) -> dict[str, list[tuple[int, int]]]:
    left = (cx - width / 2, cy - height * 0.08)
    right = (cx + width / 2, cy - height * 0.08)
    upper_control = (cx, cy - height * 0.34)
    lower_control = (cx, cy + height * 0.52)
    upper = quad_points(left, upper_control, right)
    lower = quad_points(right, lower_control, left)
    return {"upper": upper, "lower": lower, "polygon": upper + lower}


def draw_soft_smile_opening(
    mask_size: tuple[int, int],
    cx: int,
    cy: int,
    width: int,
    height: int,
    blur: float = 1.3,
) -> tuple[Image.Image, dict[str, list[tuple[int, int]]]]:
    geom = smile_opening_geometry(cx, cy, width, height)
    mask = Image.new("L", mask_size, 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon(geom["polygon"], fill=255)
    return mask.filter(ImageFilter.GaussianBlur(blur)), geom


def crop_to_bbox(image: Image.Image, bbox: tuple[int, int, int, int], pad: int = 16) -> Image.Image:
    box = (
        max(0, bbox[0] - pad),
        max(0, bbox[1] - pad),
        min(image.width, bbox[2] + pad),
        min(image.height, bbox[3] + pad),
    )
    return image.crop(box)


def fit_image(image: Image.Image, size: tuple[int, int], bg: str = "#202124") -> Image.Image:
    fitted = image.convert("RGBA")
    fitted.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, bg)
    canvas.paste(fitted.convert("RGB"), ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2), fitted.getchannel("A"))
    return canvas


def make_smile_candidate(
    closed_smile: Image.Image,
    mouth_inner: Image.Image,
    mouth_teeth: Image.Image,
    mouth_tongue: Image.Image,
    *,
    open_value: float,
    width: int,
    height: int,
    y_offset: int,
    include_teeth: bool,
    include_tongue: bool,
) -> Image.Image:
    closed_bbox = alpha_bbox(closed_smile)
    if not closed_bbox:
        raise ValueError("mouth_closed_smile has empty alpha")
    cx = (closed_bbox[0] + closed_bbox[2]) // 2
    cy = (closed_bbox[1] + closed_bbox[3]) // 2 + y_offset
    lip_color = sample_color(closed_smile, (96, 43, 45, 230))
    inner_color = sample_color(mouth_inner, (68, 24, 35, 235))
    teeth_color = sample_color(mouth_teeth, (246, 232, 222, 220))
    tongue_color = sample_color(mouth_tongue, (190, 86, 103, 180))

    layer = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    opening = (cx - width // 2, cy - height // 2, cx + width // 2, cy + height // 2)
    opening_mask, opening_geom = draw_soft_smile_opening(CANVAS_SIZE, cx, cy, width, height, blur=1.4)

    shadow = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    shadow.paste(inner_color, (0, 0), opening_mask)
    layer = Image.alpha_composite(layer, shadow)

    if include_teeth:
        teeth_h = max(4, int(height * 0.24))
        teeth_box = (cx - int(width * 0.30), cy - int(height * 0.18), cx + int(width * 0.30), cy - int(height * 0.18) + teeth_h)
        draw.rounded_rectangle(teeth_box, radius=max(2, teeth_h // 2), fill=teeth_color)

    if include_tongue:
        tongue_h = max(5, int(height * 0.32))
        tongue_box = (cx - int(width * 0.26), cy + int(height * 0.10), cx + int(width * 0.26), cy + int(height * 0.10) + tongue_h)
        draw.ellipse(tongue_box, fill=tongue_color)

    rim_alpha = min(245, int(178 + open_value * 48))
    lip_outline = (lip_color[0], lip_color[1], lip_color[2], rim_alpha)
    draw.line(opening_geom["upper"], fill=lip_outline, width=3, joint="curve")
    draw.line(opening_geom["lower"], fill=(lip_color[0], lip_color[1], lip_color[2], max(115, rim_alpha - 30)), width=2, joint="curve")

    corner_y = cy - max(0, int(height * 0.18))
    corner_len = max(14, int(width * 0.16))
    for side in (-1, 1):
        x0 = cx + side * (width // 2 - 4)
        x1 = x0 + side * corner_len
        y1 = corner_y - int(height * 0.18)
        draw.line((x0, corner_y, x1, y1), fill=lip_outline, width=3)
        draw.ellipse((x1 - 3, y1 - 2, x1 + 3, y1 + 3), fill=lip_outline)

    smile_line = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    smile_line.alpha_composite(closed_smile)
    smile_line.putalpha(ImageChops.multiply(smile_line.getchannel("A"), Image.new("L", CANVAS_SIZE, int(105 - open_value * 35))))
    layer = Image.alpha_composite(smile_line, layer)
    return layer


def build_candidates(parts_dir: Path, layers_dir: Path) -> list[dict[str, Any]]:
    layers_dir.mkdir(parents=True, exist_ok=True)
    closed_smile = load_rgba(parts_dir / "mouth_closed_smile.png")
    mouth_inner = load_rgba(parts_dir / "mouth_inner.png")
    mouth_teeth = load_rgba(parts_dir / "mouth_teeth.png")
    mouth_tongue = load_rgba(parts_dir / "mouth_tongue.png")
    specs = [
        {
            "id": "mouth_smile_closed",
            "label": "smile closed",
            "open_value": 0.0,
            "image": closed_smile,
            "qa": "reference",
        },
        {
            "id": "mouth_smile_small_open",
            "label": "smile small open",
            "open_value": 0.35,
            "image": make_smile_candidate(
                closed_smile,
                mouth_inner,
                mouth_teeth,
                mouth_tongue,
                open_value=0.35,
                width=82,
                height=20,
                y_offset=0,
                include_teeth=False,
                include_tongue=False,
            ),
            "qa": "candidate",
        },
        {
            "id": "mouth_smile_mid_open",
            "label": "smile mid open",
            "open_value": 0.65,
            "image": make_smile_candidate(
                closed_smile,
                mouth_inner,
                mouth_teeth,
                mouth_tongue,
                open_value=0.65,
                width=112,
                height=32,
                y_offset=2,
                include_teeth=True,
                include_tongue=False,
            ),
            "qa": "candidate",
        },
        {
            "id": "mouth_smile_wide_open_candidate",
            "label": "smile wide candidate",
            "open_value": 1.0,
            "image": make_smile_candidate(
                closed_smile,
                mouth_inner,
                mouth_teeth,
                mouth_tongue,
                open_value=1.0,
                width=138,
                height=44,
                y_offset=4,
                include_teeth=True,
                include_tongue=True,
            ),
            "qa": "candidate_needs_human_review",
        },
    ]
    rows = []
    for spec in specs:
        path = layers_dir / f"{spec['id']}.png"
        spec["image"].save(path)
        bbox = alpha_bbox(spec["image"])
        rows.append(
            {
                "id": spec["id"],
                "label": spec["label"],
                "open_value": spec["open_value"],
                "path": str(path),
                "mode": spec["image"].mode,
                "size": list(spec["image"].size),
                "bbox": list(bbox) if bbox else None,
                "alpha_nonzero": int(sum(spec["image"].getchannel("A").histogram()[1:])),
                "qa": spec["qa"],
            }
        )
    return rows


def overlay_on_face(face: Image.Image, mouth: Image.Image) -> Image.Image:
    result = face.copy()
    result.alpha_composite(mouth)
    return result


def neutral_face(parts_dir: Path) -> Image.Image:
    face = load_rgba(parts_dir / "face_base_clean.png")
    for part_id in ["eye_L_open", "eye_R_open"]:
        path = parts_dir / f"{part_id}.png"
        if path.exists():
            face.alpha_composite(load_rgba(path))
    return face


def build_contact_sheet(face: Image.Image, rows: list[dict[str, Any]], out_path: Path) -> None:
    cell_w = 390
    cell_h = 660
    margin = 28
    header_h = 72
    sheet = Image.new("RGB", (margin * 2 + cell_w * len(rows), margin * 2 + header_h + cell_h), "#151719")
    draw = ImageDraw.Draw(sheet)
    title_font = font(24)
    label_font = font(18)
    small_font = font(14)
    draw.text((margin, margin), "Character 002 Smile-Open Mouth Packet v1", fill="#f1f3f4", font=title_font)
    draw.text(
        (margin, margin + 34),
        "Smile-form mouth candidates only; wide/O vowel rejected assets are not reused as active states.",
        fill="#b8c0c8",
        font=small_font,
    )
    for index, row in enumerate(rows):
        x = margin + index * cell_w
        y = margin + header_h
        mouth = load_rgba(Path(row["path"]))
        composite = overlay_on_face(face, mouth)
        bbox = tuple(row["bbox"]) if row["bbox"] else (900, 810, 1160, 980)
        closeup_box = (
            max(0, bbox[0] - 115),
            max(0, bbox[1] - 105),
            min(CANVAS_SIZE[0], bbox[2] + 115),
            min(CANVAS_SIZE[1], bbox[3] + 105),
        )
        mouth_crop = crop_to_bbox(mouth, bbox, pad=24)
        comp_crop = composite.crop(closeup_box)
        full = fit_image(composite, (cell_w - 24, 310), bg="#f0eee7")
        close = fit_image(comp_crop, (cell_w - 24, 132), bg="#f0eee7")
        isolated = fit_image(mouth_crop, (cell_w - 24, 118), bg="#202124")
        draw.rounded_rectangle((x + 6, y + 6, x + cell_w - 6, y + cell_h - 6), radius=8, fill="#202124", outline="#3a3f45")
        draw.text((x + 18, y + 18), row["label"], fill="#f1f3f4", font=label_font)
        draw.text((x + 18, y + 44), f"MouthOpenY target {row['open_value']:.2f}", fill="#b8c0c8", font=small_font)
        sheet.paste(full, (x + 12, y + 76))
        draw.text((x + 18, y + 392), "face close-up", fill="#b8c0c8", font=small_font)
        sheet.paste(close, (x + 12, y + 416))
        draw.text((x + 18, y + 548), "isolated full-canvas layer crop", fill="#b8c0c8", font=small_font)
        sheet.paste(isolated, (x + 12, y + 572))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def row_validation(rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    for row in rows:
        if row["size"] != list(CANVAS_SIZE):
            issues.append(f"{row['id']}: not {CANVAS_SIZE}")
        if row["mode"] != "RGBA":
            issues.append(f"{row['id']}: not RGBA")
        if not row["bbox"]:
            issues.append(f"{row['id']}: empty alpha")
        if row["bbox"]:
            x0, y0, x1, y1 = row["bbox"]
            if not (850 <= x0 <= 990 and 1060 <= x1 <= 1160 and 810 <= y0 <= 900 and 900 <= y1 <= 990):
                issues.append(f"{row['id']}: bbox outside expected mouth review zone {row['bbox']}")
    return issues


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Character 002 Smile-Open Mouth Packet v1",
        "",
        f"- Status: `{report['status']}`",
        f"- Contact sheet: `{report['contact_sheet']}`",
        f"- Generated at: `{report['generated_at']}`",
        "",
        "## Decision",
        "",
        "- This packet isolates smile-form mouth opening candidates from rejected `mouth_wide_open` and `mouth_o_vowel` assets.",
        "- The generated PNGs are 2048 RGBA full-canvas candidates for visual review, not production-approved Live2D/Cubism mouth art.",
        "- Use this packet to decide whether the synthetic smile-open direction is acceptable or whether model-native/manual repaint is needed.",
        "",
        "## Candidates",
        "",
        "| Candidate | Open Value | BBox | QA | Path |",
        "|---|---:|---|---|---|",
    ]
    for row in report["candidates"]:
        lines.append(
            f"| `{row['id']}` | {row['open_value']:.2f} | `{row['bbox']}` | `{row['qa']}` | `{row['path']}` |"
        )
    lines.extend(["", "## Validation", ""])
    if report["validation_issues"]:
        for issue in report["validation_issues"]:
            lines.append(f"- REVISE: {issue}")
    else:
        lines.append("- PASS: all candidates are 2048 RGBA, non-empty, and in the expected mouth review zone.")
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parts-dir", default=str(DEFAULT_PARTS))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    parts_dir = Path(args.parts_dir).resolve()
    out_dir = Path(args.out).resolve()
    layers_dir = out_dir / "normalized_layers"
    face = neutral_face(parts_dir)
    rows = build_candidates(parts_dir, layers_dir)
    contact_sheet = out_dir / "smile_open_mouth_contact_sheet.png"
    build_contact_sheet(face, rows, contact_sheet)
    validation_issues = row_validation(rows)
    status = "PASS_READY_FOR_HUMAN_VISUAL_QA" if not validation_issues else "REVISE_TECHNICAL_QA"
    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": status,
        "source_parts_dir": str(parts_dir),
        "layers_dir": str(layers_dir),
        "contact_sheet": str(contact_sheet),
        "validation_issues": validation_issues,
        "candidates": rows,
        "excluded_assets": ["mouth_wide_open", "mouth_o_vowel"],
        "decision": "Smile-open mouth candidates generated for visual QA; do not promote until 주인님 approves contact sheet.",
    }
    report_path = out_dir / "smile_open_mouth_packet_report.json"
    md_path = out_dir / "smile_open_mouth_packet_report.md"
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

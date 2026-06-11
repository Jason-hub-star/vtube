#!/usr/bin/env python3
"""Build a contact sheet from a Mini Cubism pose sweep report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def font(size: int) -> ImageFont.ImageFont:
    for candidate in [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def fit_image(path: str, size: tuple[int, int]) -> Image.Image:
    image = Image.open(path).convert("RGB")
    image.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "#202124")
    canvas.paste(image, ((size[0] - image.width) // 2, (size[1] - image.height) // 2))
    return canvas


def flatten_frames(report: dict[str, Any]) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    for viewport in report.get("results", []):
        viewport_name = viewport.get("viewport", {}).get("name", "viewport")
        for pose in viewport.get("poses", []):
            frames.append({"viewport": viewport_name, **pose})
    return frames


def build_sheet(report: dict[str, Any], out_path: Path, title: str) -> None:
    frames = flatten_frames(report)
    cols = 4
    cell_w = 360
    cell_h = 330
    margin = 28
    header_h = 84
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (margin * 2 + cols * cell_w, margin * 2 + header_h + rows * cell_h), "#151719")
    draw = ImageDraw.Draw(sheet)
    title_font = font(24)
    label_font = font(16)
    small_font = font(12)
    draw.text((margin, margin), title, fill="#f1f3f4", font=title_font)
    summary = report.get("summary", {})
    draw.text(
        (margin, margin + 36),
        f"status {report.get('status')} / score {report.get('score')} / pass {summary.get('counts', {}).get('PASS')} revise {summary.get('counts', {}).get('REVISE')} fail {summary.get('counts', {}).get('FAIL')}",
        fill="#b8c0c8",
        font=small_font,
    )
    for index, frame in enumerate(frames):
        col = index % cols
        row = index // cols
        x = margin + col * cell_w
        y = margin + header_h + row * cell_h
        draw.rounded_rectangle((x + 6, y + 6, x + cell_w - 6, y + cell_h - 6), radius=8, fill="#202124", outline="#3a3f45")
        label = f"{frame['viewport']} / {frame['pose']}"
        draw.text((x + 16, y + 16), label, fill="#f1f3f4", font=label_font)
        verdict = frame.get("verdict", "")
        ratio = frame.get("metrics", {}).get("changedRatio", 0)
        color = "#50dc78" if verdict == "PASS" else "#ffcc33" if verdict == "REVISE" else "#ff5b33"
        draw.text((x + 16, y + 40), f"{verdict} changed {ratio:.6f}", fill=color, font=small_font)
        image = fit_image(frame["screenshot"], (cell_w - 28, 235))
        sheet.paste(image, (x + 14, y + 64))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--title", default="Mini Cubism Pose Sweep Review")
    args = parser.parse_args()
    report = load_json(Path(args.report).resolve())
    build_sheet(report, Path(args.out).resolve(), args.title)
    print(json.dumps({"ok": True, "contact_sheet": args.out}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build a one-page-ish contact sheet for generated Cubism v2 material assets."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from cubism_v2_material_asset_lib import CONTACT_SHEET, MANIFEST_PATH, REPORTS, ROOT, load_font, load_json, rel, save_json


SECTION_LABELS = {
    "DIRECT_VISIBLE": "바로 분리",
    "DIRECT_VISIBLE_RISK": "정리 필요",
    "DERIVED_KEYPOSE_REQUIRED": "보조 생성",
    "UNDERPAINT_REQUIRED": "밑색",
    "SIMPLIFY_OR_MERGE": "병합/메타",
}

SECTION_COLORS = {
    "DIRECT_VISIBLE": (49, 130, 246),
    "DIRECT_VISIBLE_RISK": (245, 158, 11),
    "DERIVED_KEYPOSE_REQUIRED": (139, 92, 246),
    "UNDERPAINT_REQUIRED": (16, 185, 129),
    "SIMPLIFY_OR_MERGE": (100, 116, 139),
}


def checker(size: tuple[int, int]) -> Image.Image:
    img = Image.new("RGB", size, (245, 247, 251))
    draw = ImageDraw.Draw(img)
    step = 12
    for y in range(0, size[1], step):
        for x in range(0, size[0], step):
            if (x // step + y // step) % 2:
                draw.rectangle((x, y, x + step - 1, y + step - 1), fill=(232, 236, 244))
    return img


def thumb_for(entry: dict, thumb_size: int) -> Image.Image:
    tile = checker((thumb_size, thumb_size))
    if entry.get("output_path"):
        path = ROOT / entry["output_path"]
        if path.exists():
            layer = Image.open(path).convert("RGBA")
            bbox = entry.get("bbox_actual") or entry.get("bbox")
            if bbox:
                x, y, w, h = bbox
                crop = layer.crop((x, y, x + w, y + h))
            else:
                crop = layer
            crop.thumbnail((thumb_size - 22, thumb_size - 58), Image.Resampling.LANCZOS)
            px = (thumb_size - crop.width) // 2
            py = 16 + (thumb_size - 68 - crop.height) // 2
            tile = tile.convert("RGBA")
            tile.alpha_composite(crop, (px, py))
            tile = tile.convert("RGB")
    return tile


def build_sheet() -> dict:
    manifest = load_json(MANIFEST_PATH)
    entries = manifest["layers"]
    cols = 8
    thumb = 210
    header_h = 92
    rows = (len(entries) + cols - 1) // cols
    width = cols * thumb
    height = header_h + rows * thumb
    sheet = Image.new("RGB", (width, height), (246, 248, 252))
    draw = ImageDraw.Draw(sheet)
    title_font = load_font(32)
    body_font = load_font(17)
    small_font = load_font(14)
    draw.text((24, 18), "Cubism v2 material contact sheet", fill=(15, 23, 42), font=title_font)
    draw.text(
        (24, 56),
        "파츠 초안 62개 + 병합 메타 2개. 빨강 표시는 자동검사에서 다시 볼 후보입니다.",
        fill=(71, 85, 105),
        font=body_font,
    )
    for idx, entry in enumerate(entries):
        col = idx % cols
        row = idx // cols
        x = col * thumb
        y = header_h + row * thumb
        tile = thumb_for(entry, thumb)
        sheet.paste(tile, (x, y))
        color = SECTION_COLORS.get(entry["feasibility"], (100, 116, 139))
        draw.rounded_rectangle((x + 8, y + 8, x + thumb - 8, y + thumb - 8), radius=8, outline=color, width=4)
        label = SECTION_LABELS.get(entry["feasibility"], entry["feasibility"])
        draw.rounded_rectangle((x + 14, y + 14, x + 14 + len(label) * 12 + 18, y + 40), radius=8, fill=color)
        draw.text((x + 23, y + 17), label, fill=(255, 255, 255), font=small_font)
        part = entry["part_id"]
        status_color = (220, 38, 38) if entry.get("risk_tags") or entry.get("status", "").startswith("FAIL") else (15, 23, 42)
        draw.text((x + 14, y + thumb - 44), part[:23], fill=status_color, font=small_font)
        draw.text((x + 14, y + thumb - 24), entry["label_ko"][:18], fill=(71, 85, 105), font=small_font)

    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET)
    report = {
        "status": "PASS_CONTACT_SHEET_READY" if CONTACT_SHEET.exists() else "FAIL",
        "contact_sheet": rel(CONTACT_SHEET),
        "entries": len(entries),
        "risk_or_review_candidates": len([e for e in entries if e.get("risk_tags") or e.get("feasibility") in {"DIRECT_VISIBLE_RISK", "DERIVED_KEYPOSE_REQUIRED", "UNDERPAINT_REQUIRED"}]),
    }
    save_json(REPORTS / "material_contact_sheet_report.json", report)
    (REPORTS / "material_contact_sheet_report.md").write_text(
        "\n".join(
            [
                "# Cubism v2 Material Contact Sheet",
                "",
                f"- status: `{report['status']}`",
                f"- contact sheet: `{report['contact_sheet']}`",
                f"- entries: `{report['entries']}`",
                f"- review candidates: `{report['risk_or_review_candidates']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report


def main() -> None:
    report = build_sheet()
    print(report["status"])
    print(ROOT / report["contact_sheet"])


if __name__ == "__main__":
    main()

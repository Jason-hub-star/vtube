#!/usr/bin/env python3
"""Build a visual contact sheet and triage report for MPS See-through candidates."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "see-through-mps-compat-002"
MANIFEST_PATH = EXP / "layer_manifest.json"
REPORT_DIR = EXP / "reports"
CONTACT_SHEET = REPORT_DIR / "mps_candidate_contact_sheet.png"
TRIAGE_REPORT = REPORT_DIR / "mps_candidate_triage_report.json"

PRACTICAL_GROUPS = {"hair", "face", "eyes", "brows", "mouth"}
PRACTICAL_PARTS = {
    "front_hair",
    "back_hair",
    "face_base",
    "mouth_line",
    "L_iris",
    "R_iris",
    "L_eye_white",
    "R_eye_white",
    "L_upper_lash",
    "R_upper_lash",
    "L_brow",
    "R_brow",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path | str | None) -> str | None:
    if path is None:
        return None
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    try:
        return p.relative_to(ROOT).as_posix()
    except ValueError:
        return str(p)


def load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Missing manifest: {MANIFEST_PATH}")
    return json.loads(MANIFEST_PATH.read_text())


def configure_experiment(experiment_id: str) -> None:
    global EXP, MANIFEST_PATH, REPORT_DIR, CONTACT_SHEET, TRIAGE_REPORT
    EXP = ROOT / "experiments" / experiment_id
    MANIFEST_PATH = EXP / "layer_manifest.json"
    REPORT_DIR = EXP / "reports"
    CONTACT_SHEET = REPORT_DIR / "mps_candidate_contact_sheet.png"
    TRIAGE_REPORT = REPORT_DIR / "mps_candidate_triage_report.json"


def font(size: int) -> ImageFont.ImageFont:
    for candidate in [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def composite_preview(path: Path, tile_size: int) -> Image.Image:
    img = Image.open(path).convert("RGBA")
    alpha = img.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        crop = Image.new("RGBA", (tile_size, tile_size), (0, 0, 0, 0))
    else:
        x0, y0, x1, y1 = bbox
        pad = max(16, int(max(x1 - x0, y1 - y0) * 0.12))
        x0 = max(0, x0 - pad)
        y0 = max(0, y0 - pad)
        x1 = min(img.width, x1 + pad)
        y1 = min(img.height, y1 + pad)
        crop = img.crop((x0, y0, x1, y1))
    checker = Image.new("RGBA", crop.size, (235, 235, 235, 255))
    draw = ImageDraw.Draw(checker)
    step = max(12, min(crop.size) // 8)
    for y in range(0, crop.height, step):
        for x in range(0, crop.width, step):
            if (x // step + y // step) % 2:
                draw.rectangle([x, y, x + step - 1, y + step - 1], fill=(205, 205, 205, 255))
    checker.alpha_composite(crop)
    checker.thumbnail((tile_size, tile_size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (tile_size, tile_size), (248, 248, 248, 255))
    canvas.alpha_composite(checker, ((tile_size - checker.width) // 2, (tile_size - checker.height) // 2))
    return canvas.convert("RGB")


def triage_status(layer: dict[str, Any]) -> tuple[str, list[str]]:
    notes = []
    bbox = layer.get("bbox")
    coverage = float(layer.get("alpha_coverage") or 0)
    part = layer.get("original_part_id")
    production_candidate = bool(layer.get("production_candidate"))
    if not bbox:
        return "X_CANDIDATE_EMPTY", ["empty alpha"]
    x, y, w, h = bbox
    if w <= 0 or h <= 0:
        return "X_CANDIDATE_EMPTY", ["invalid bbox"]
    if part in PRACTICAL_PARTS:
        notes.append("practical_gate_target")
    if production_candidate:
        notes.append("production_candidate")
    if coverage < 0.02:
        notes.append("very_sparse_alpha")
    if coverage > 0.9:
        notes.append("dense_alpha")
    if max(w, h) > 1800 and part not in {"back_hair"}:
        notes.append("likely_too_broad")
    if part and str(part).startswith("raw_"):
        notes.append("unmapped_raw_layer")
    if part and str(part).endswith("_reference"):
        notes.append("reference_only_mapping")
    if "likely_too_broad" in notes or "unmapped_raw_layer" in notes:
        return "REVIEW_HIGH_RISK", notes
    if production_candidate:
        return "REVIEW_PRIORITY", notes
    return "REFERENCE_REVIEW", notes


def build() -> dict[str, Any]:
    manifest = load_manifest()
    layers = manifest.get("layers", [])
    rows = []
    for layer in layers:
        status, notes = triage_status(layer)
        rows.append(
            {
                "layer_name": layer.get("layer_name"),
                "original_part_id": layer.get("original_part_id"),
                "role": layer.get("role"),
                "side": layer.get("side"),
                "bbox": layer.get("bbox"),
                "alpha_coverage": layer.get("alpha_coverage"),
                "production_candidate": bool(layer.get("production_candidate")),
                "include_in_import_psd": bool(layer.get("include_in_import_psd")),
                "triage_status": status,
                "triage_notes": notes,
                "image_path": rel(layer.get("output_path")),
            }
        )
    priority = {"REVIEW_PRIORITY": 0, "REVIEW_HIGH_RISK": 1, "REFERENCE_REVIEW": 2, "X_CANDIDATE_EMPTY": 3}
    rows.sort(key=lambda row: (priority.get(row["triage_status"], 9), row["role"] or "", row["layer_name"] or ""))

    tile_w, tile_h = 260, 320
    cols = 4
    title_h = 72
    rows_count = (len(rows) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tile_w, title_h + rows_count * tile_h), (245, 245, 245))
    draw = ImageDraw.Draw(sheet)
    title_font = font(24)
    label_font = font(14)
    small_font = font(12)
    draw.text((16, 14), f"{manifest.get('experiment_id', EXP.name)} 후보 contact sheet", fill=(20, 20, 20), font=title_font)
    draw.text((16, 45), "O/X/REVISE는 review_app에서 별도 저장. 이 시트는 검수 우선순위 evidence.", fill=(80, 80, 80), font=small_font)

    for index, row in enumerate(rows):
        col = index % cols
        grid_row = index // cols
        x = col * tile_w
        y = title_h + grid_row * tile_h
        draw.rectangle([x + 8, y + 8, x + tile_w - 8, y + tile_h - 8], fill=(255, 255, 255), outline=(210, 210, 210))
        path = ROOT / row["image_path"]
        if path.exists():
            preview = composite_preview(path, 208)
            sheet.paste(preview, (x + 26, y + 16))
        status_color = {
            "REVIEW_PRIORITY": (26, 115, 232),
            "REVIEW_HIGH_RISK": (196, 88, 0),
            "REFERENCE_REVIEW": (100, 100, 100),
            "X_CANDIDATE_EMPTY": (180, 0, 0),
        }.get(row["triage_status"], (80, 80, 80))
        text_y = y + 232
        draw.text((x + 18, text_y), str(row["layer_name"])[:28], fill=(20, 20, 20), font=label_font)
        draw.text((x + 18, text_y + 20), str(row["original_part_id"]), fill=(70, 70, 70), font=small_font)
        draw.text((x + 18, text_y + 38), row["triage_status"], fill=status_color, font=small_font)
        draw.text((x + 18, text_y + 56), f"alpha={row['alpha_coverage']} bbox={row['bbox']}", fill=(90, 90, 90), font=small_font)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET)
    report = {
        "schema_version": 1,
        "experiment_id": manifest.get("experiment_id", EXP.name),
        "generated_at": now(),
        "source_manifest": rel(MANIFEST_PATH),
        "contact_sheet": rel(CONTACT_SHEET),
        "counts": {
            "total": len(rows),
            "review_priority": sum(1 for row in rows if row["triage_status"] == "REVIEW_PRIORITY"),
            "review_high_risk": sum(1 for row in rows if row["triage_status"] == "REVIEW_HIGH_RISK"),
            "reference_review": sum(1 for row in rows if row["triage_status"] == "REFERENCE_REVIEW"),
            "empty": sum(1 for row in rows if row["triage_status"] == "X_CANDIDATE_EMPTY"),
            "practical_gate_targets": sum(1 for row in rows if "practical_gate_target" in row["triage_notes"]),
        },
        "practical_success_gate": "Human review must mark at least 5 hair/face/eye/mouth candidates as O or REVISE.",
        "items": rows,
    }
    TRIAGE_REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a visual contact sheet and triage report for MPS See-through candidates.")
    parser.add_argument("--experiment-id", default="see-through-mps-compat-002")
    args = parser.parse_args()
    configure_experiment(args.experiment_id)
    report = build()
    print(json.dumps({"contact_sheet": report["contact_sheet"], "counts": report["counts"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

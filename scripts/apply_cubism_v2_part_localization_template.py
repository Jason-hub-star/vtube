#!/usr/bin/env python3
"""Apply part_localization_template.json to split current candidate layers."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path("/Users/family/jason/Vtube")
PACK = ROOT / "experiments/cubism-v2-new-character-001/material_pack_v0"
MANIFEST_PATH = PACK / "layer_manifest.json"
TEMPLATE_PATH = PACK / "reports/part_localization_template.json"
CANONICAL_PATH = PACK / "canonical/candidate_002_2048_rgba.png"
OUT_DIR = PACK / "production_layers_localized_v1"
REPORT_JSON = PACK / "reports/part_localization_split_report.json"
REPORT_MD = PACK / "reports/part_localization_split_report.md"
CONTACT_SHEET = PACK / "reports/part_localization_split_contact_sheet.png"
LOCALIZED_MANIFEST_PATH = PACK / "layer_manifest.localization_template_split_v1.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def resolve(path_value: str) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def bbox_from_alpha(arr: np.ndarray, threshold: int = 5) -> list[int]:
    ys, xs = np.where(arr[:, :, 3] > threshold)
    if len(xs) == 0:
        return [0, 0, 0, 0]
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    return [x0, y0, x1 - x0, y1 - y0]


def crop_canonical_layer(canonical: Image.Image, roi: list[int], source_type: str | None, part_id: str) -> Image.Image:
    x, y, w, h = [int(v) for v in roi]
    canvas = Image.new("RGBA", canonical.size, (0, 0, 0, 0))
    crop = canonical.crop((x, y, x + w, y + h)).convert("RGBA")
    arr = np.array(crop)
    if source_type == "UNDERPAINT" or "underpaint" in part_id:
        fallback = (241, 196, 175)
        if "hair" in part_id:
            fallback = (127, 83, 82)
        elif "eye" in part_id:
            fallback = (248, 224, 213)
        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)
        if "eye" in part_id:
            draw.ellipse((max(1, w * 0.08), max(1, h * 0.10), w * 0.92, h * 0.90), fill=145)
        else:
            draw.rounded_rectangle((max(1, w * 0.08), max(1, h * 0.06), w * 0.92, h * 0.90), radius=max(6, min(w, h) // 6), fill=145)
        mask = mask.filter(ImageFilter.GaussianBlur(max(1, min(w, h) // 24)))
        fill = Image.new("RGBA", (w, h), (*fallback, 180))
        fill.putalpha(mask)
        canvas.paste(fill, (x, y), fill)
        return canvas

    # For visible source parts, use canonical RGB/alpha within the human ROI.
    # This deliberately uses the visible subject mask instead of moving an old
    # layer, because the saved label says "this region is the part".
    alpha = arr[:, :, 3]
    arr[:, :, 3] = np.where(alpha > 5, alpha, 0).astype(np.uint8)
    crop = Image.fromarray(arr, "RGBA")
    canvas.paste(crop, (x, y), crop)
    return canvas


def load_existing_layer(layer: dict[str, Any]) -> Image.Image:
    return Image.open(resolve(layer["output_path"])).convert("RGBA")


def update_bbox_metadata(layer: dict[str, Any], image: Image.Image) -> None:
    arr = np.array(image)
    bbox = bbox_from_alpha(arr)
    layer["bbox_actual"] = bbox
    layer["alpha_coverage"] = round(float((arr[:, :, 3] > 5).sum() / (arr.shape[0] * arr.shape[1])), 8)


def build_contact_sheet(rows: list[dict[str, Any]], out: Path) -> None:
    cell_w, cell_h = 250, 260
    cols = 4
    page_rows = max(1, (len(rows) + cols - 1) // cols)
    sheet = Image.new("RGB", (cols * cell_w, page_rows * cell_h), (247, 249, 252))
    draw = ImageDraw.Draw(sheet)
    for idx, row in enumerate(rows):
        x = (idx % cols) * cell_w
        y = (idx // cols) * cell_h
        draw.rounded_rectangle((x + 8, y + 8, x + cell_w - 8, y + cell_h - 8), radius=8, fill=(255, 255, 255), outline=(226, 232, 240))
        image = Image.open(row["output_path"]).convert("RGBA")
        bbox = row["bbox_actual"]
        if bbox and bbox[2] and bbox[3]:
            crop = image.crop((bbox[0], bbox[1], bbox[0] + bbox[2], bbox[1] + bbox[3]))
            bg = Image.new("RGBA", crop.size, (245, 245, 245, 255))
            bg.alpha_composite(crop)
            bg.thumbnail((cell_w - 34, 152), Image.Resampling.LANCZOS)
            sheet.paste(bg.convert("RGB"), (x + (cell_w - bg.width) // 2, y + 16))
        draw.text((x + 16, y + 178), row["part_id"][:26], fill=(25, 31, 40))
        draw.text((x + 16, y + 200), row["action"][:26], fill=(75, 85, 99))
        draw.text((x + 16, y + 220), f"bbox={row['bbox_actual']}", fill=(75, 85, 99))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def main() -> int:
    if not TEMPLATE_PATH.exists():
        raise SystemExit(f"Missing template: {TEMPLATE_PATH}")
    template = load_json(TEMPLATE_PATH)
    manifest = load_json(MANIFEST_PATH)
    canonical = Image.open(CANONICAL_PATH).convert("RGBA")
    parts = template.get("parts", {})
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    updated = json.loads(json.dumps(manifest))
    previous_semantic_purity = updated.pop("semantic_purity", None)
    updated["status"] = "LOCALIZATION_TEMPLATE_SPLIT_V1_APPLIED"
    updated["part_localization_split"] = {
        "schema_version": 1,
        "applied_at": now(),
        "template": rel(TEMPLATE_PATH),
        "output_dir": rel(OUT_DIR),
        "method": "use manual ROI absolute coordinates for current candidate; keep relative template for future character localization",
    }
    if previous_semantic_purity:
        updated["part_localization_split"]["superseded_semantic_purity"] = {
            "reason": "Localization split rewrites layer output paths, so earlier semantic repair metadata no longer describes the active manifest.",
            "previous_gate": previous_semantic_purity.get("gate"),
            "previous_applied_at": previous_semantic_purity.get("applied_at"),
        }

    rows: list[dict[str, Any]] = []
    applied = 0
    kept = 0
    for layer in updated["layers"]:
        if not layer.get("include_in_import_psd"):
            continue
        part_id = layer["part_id"]
        part_template = parts.get(part_id)
        if part_template and part_template.get("action") in {"REEXTRACT_FROM_CANONICAL", "REPAIR_UNDERPAINT", "REPAIR_MASK", "REPAIR_POSITION"}:
            image = crop_canonical_layer(canonical, part_template["roi_abs"], layer.get("source_type"), part_id)
            action = part_template.get("action")
            applied += 1
        else:
            image = load_existing_layer(layer)
            action = "KEEP_EXISTING"
            kept += 1
        output = OUT_DIR / Path(layer["output_path"]).name
        image.save(output)
        layer["pre_localization_split_output_path"] = layer["output_path"]
        layer["output_path"] = rel(output)
        layer["localization_template"] = part_template
        layer["localization_action"] = action
        update_bbox_metadata(layer, image)
        rows.append(
            {
                "part_id": part_id,
                "action": action,
                "bbox_actual": layer["bbox_actual"],
                "alpha_coverage": layer["alpha_coverage"],
                "output_path": str(output),
            }
        )

    backup = MANIFEST_PATH.with_name("layer_manifest.before_localization_template_split_v1.json")
    if not backup.exists():
        shutil.copy2(MANIFEST_PATH, backup)
    write_json(MANIFEST_PATH, updated)
    write_json(LOCALIZED_MANIFEST_PATH, updated)
    build_contact_sheet([row for row in rows if row["action"] != "KEEP_EXISTING"], CONTACT_SHEET)
    report = {
        "schema_version": 1,
        "status": "PASS_LOCALIZATION_TEMPLATE_SPLIT_APPLIED" if applied else "FAIL_NO_TEMPLATE_PARTS_APPLIED",
        "generated_at": now(),
        "template": rel(TEMPLATE_PATH),
        "manifest": rel(MANIFEST_PATH),
        "localized_manifest": rel(LOCALIZED_MANIFEST_PATH),
        "backup_manifest": rel(backup),
        "output_dir": rel(OUT_DIR),
        "applied_parts": applied,
        "kept_parts": kept,
        "rows": rows,
        "contact_sheet": rel(CONTACT_SHEET),
        "interpretation": [
            "This is a current-candidate layer split from saved manual semantic ROI labels.",
            "It proves manual locations can drive layer generation; visual quality still needs G1.5 and Mini Cubism checks.",
        ],
    }
    write_json(REPORT_JSON, report)
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Part Localization Template Split",
                "",
                f"- status: `{report['status']}`",
                f"- applied parts: `{applied}`",
                f"- kept parts: `{kept}`",
                f"- contact sheet: `{report['contact_sheet']}`",
                f"- manifest: `{report['manifest']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"ok": report["status"].startswith("PASS"), "status": report["status"], "applied": applied, "kept": kept, "report": str(REPORT_JSON)}, indent=2))
    return 0 if report["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())

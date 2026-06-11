#!/usr/bin/env python3
"""Build ROI-guided semantic remask layers from manual localization seeds.

This is intentionally different from the raw localization crop split:

- part_localization_template.json supplies ROI seeds only.
- Existing repaired/neutral layer art remains the source of pixels.
- The neutral semantic owner map moves exposed underpaint pixels into the
  visible owner target, then removes those pixels from underpaint.
- Eye/mouth/face detail layers are clamped by manual ROI seeds instead of
  being regenerated from a rectangular crop.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

from build_cubism_v2_semantic_purity_gate import (
    CANONICAL_PATH,
    MANIFEST_PATH,
    NEUTRAL_HIDDEN,
    ROOT,
    UNDERPAINT_TARGETS,
    bbox_from_alpha,
    composite,
    eye_mouth_alignment,
    include_layers,
    layer_role_qa,
    load_arrays,
    load_json,
    make_underpaint_map,
    rel,
    save_layer_contact_sheet,
    save_owner_map,
    save_roi_closeup_sheet,
    score,
    semantic_group,
    underpaint_leakage,
    union_bbox,
    write_json,
)


PACK = ROOT / "experiments/cubism-v2-new-character-001/material_pack_v0"
TEMPLATE_PATH = PACK / "reports/part_localization_template.json"
SOURCE_MANIFEST = PACK / "layer_manifest.before_semantic_repair_v1.json"
OUT_DIR = PACK / "production_layers_roi_semantic_remask_v1"
SNAPSHOT_MANIFEST = PACK / "layer_manifest.roi_guided_semantic_remask_v1.json"
REPORT_DIR = PACK / "reports/roi_guided_semantic_remask"
REPORT_JSON = REPORT_DIR / "roi_guided_semantic_remask_report.json"
REPORT_MD = REPORT_DIR / "roi_guided_semantic_remask_report.md"
CONTACT_SHEET = REPORT_DIR / "roi_guided_contact_sheet.png"
PROBLEM_SHEET = REPORT_DIR / "roi_guided_problem_sheet.png"


ROI_GUIDED_PART_PREFIXES = ("eye_", "mouth_", "brow_")
ROI_GUIDED_PART_IDS = {
    "nose",
    "cheek_L",
    "cheek_R",
    "face_shadow_L",
    "face_shadow_R",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clamp_bbox(bbox: list[int], pad: int = 0, size: tuple[int, int] = (2048, 2048)) -> list[int]:
    x, y, w, h = [int(v) for v in bbox]
    x0 = max(0, x - pad)
    y0 = max(0, y - pad)
    x1 = min(size[0], x + w + pad)
    y1 = min(size[1], y + h + pad)
    return [x0, y0, max(0, x1 - x0), max(0, y1 - y0)]


def mask_from_bbox(bbox: list[int], size: tuple[int, int] = (2048, 2048)) -> np.ndarray:
    x, y, w, h = [int(v) for v in bbox]
    mask = np.zeros((size[1], size[0]), dtype=bool)
    if w <= 0 or h <= 0:
        return mask
    mask[y : y + h, x : x + w] = True
    return mask


def template_rois(template: dict[str, Any]) -> dict[str, list[int]]:
    rois: dict[str, list[int]] = {}
    for part_id, row in (template.get("parts") or {}).items():
        roi = row.get("roi_abs")
        if not roi or len(roi) != 4:
            continue
        if part_id.startswith("eye_") or part_id.startswith("mouth_"):
            pad = 6
        elif part_id.startswith("brow_") or part_id in ROI_GUIDED_PART_IDS:
            pad = 10
        else:
            pad = 0
        rois[part_id] = clamp_bbox(roi, pad=pad)
    return rois


def grouped_rois(part_rois: dict[str, list[int]]) -> dict[str, list[int]]:
    return {
        "eye_L": union_bbox([roi for part, roi in part_rois.items() if part.startswith("eye_L_")], 8),
        "eye_R": union_bbox([roi for part, roi in part_rois.items() if part.startswith("eye_R_")], 8),
        "mouth": union_bbox([roi for part, roi in part_rois.items() if part.startswith("mouth_")], 8),
    }


def should_roi_clamp(part_id: str, layer: dict[str, Any], part_rois: dict[str, list[int]]) -> bool:
    if part_id not in part_rois:
        return False
    if layer.get("source_type") == "UNDERPAINT" or "underpaint" in part_id:
        return False
    return part_id.startswith(ROI_GUIDED_PART_PREFIXES) or part_id in ROI_GUIDED_PART_IDS


def alpha_metadata(arr: np.ndarray) -> dict[str, Any]:
    bbox = bbox_from_alpha(arr)
    return {
        "bbox_actual": bbox,
        "alpha_coverage": round(float((arr[:, :, 3] > 5).sum() / (arr.shape[0] * arr.shape[1])), 8),
    }


def save_contact_sheet(rows: list[dict[str, Any]], out: Path) -> None:
    cell_w, cell_h = 270, 250
    cols = 4
    page_rows = max(1, (len(rows) + cols - 1) // cols)
    sheet = Image.new("RGB", (cols * cell_w, page_rows * cell_h), (247, 249, 252))
    draw = ImageDraw.Draw(sheet)
    for idx, row in enumerate(rows):
        x = (idx % cols) * cell_w
        y = (idx // cols) * cell_h
        draw.rounded_rectangle((x + 8, y + 8, x + cell_w - 8, y + cell_h - 8), radius=8, fill=(255, 255, 255), outline=(226, 232, 240))
        path = Path(row["output_path"])
        image = Image.open(path).convert("RGBA")
        bbox = row["bbox_actual"]
        if bbox and bbox[2] > 0 and bbox[3] > 0:
            crop = image.crop((bbox[0], bbox[1], bbox[0] + bbox[2], bbox[1] + bbox[3]))
            bg = Image.new("RGBA", crop.size, (245, 245, 245, 255))
            bg.alpha_composite(crop)
            bg.thumbnail((cell_w - 36, 150), Image.Resampling.LANCZOS)
            sheet.paste(bg.convert("RGB"), (x + (cell_w - bg.width) // 2, y + 16))
        draw.text((x + 16, y + 174), row["part_id"][:28], fill=(25, 31, 40))
        draw.text((x + 16, y + 196), row["method"][:30], fill=(75, 85, 99))
        draw.text((x + 16, y + 216), f"bbox={row['bbox_actual']}", fill=(75, 85, 99))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def build_remask(source_manifest: Path, promote: bool) -> dict[str, Any]:
    if not TEMPLATE_PATH.exists():
        raise SystemExit(f"Missing template: {TEMPLATE_PATH}")
    if not source_manifest.exists():
        raise SystemExit(f"Missing source manifest: {source_manifest}")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    template = load_json(TEMPLATE_PATH)
    manifest = load_json(source_manifest)
    layers = manifest["layers"]
    canonical = np.array(Image.open(CANONICAL_PATH).convert("RGBA"))
    arrays = load_arrays(layers)
    part_rois = template_rois(template)
    rois = grouped_rois(part_rois)

    before_composite, before_owner = composite(layers, arrays, NEUTRAL_HIDDEN, (2048, 2048))
    before_score = score(canonical, before_composite)
    before_underpaint = underpaint_leakage(layers, arrays, before_owner, "before_roi_guided")
    save_owner_map(
        layers,
        before_owner,
        REPORT_DIR / "semantic_owner_map_before.png",
        REPORT_DIR / "semantic_owner_legend_before.json",
    )
    make_underpaint_map(before_owner, REPORT_DIR / "underpaint_leakage_map_before.png")

    repaired = {part_id: arr.copy() for part_id, arr in arrays.items()}
    underpaint_moved: dict[str, int] = {}
    for underpaint_id, target_id in UNDERPAINT_TARGETS.items():
        if underpaint_id not in repaired or target_id not in repaired:
            continue
        move = before_owner == underpaint_id
        underpaint_moved[underpaint_id] = int(move.sum())
        if move.any():
            repaired[target_id][move] = canonical[move]
            repaired[underpaint_id][move, 3] = 0

    roi_rows: list[dict[str, Any]] = []
    layer_by_part = {layer["part_id"]: layer for layer in include_layers(layers)}
    for part_id, layer in layer_by_part.items():
        if not should_roi_clamp(part_id, layer, part_rois):
            continue
        arr = repaired[part_id]
        before_alpha = int((arr[:, :, 3] > 5).sum())
        roi_mask = mask_from_bbox(part_rois[part_id])
        removed = int(((arr[:, :, 3] > 5) & ~roi_mask).sum())
        arr[~roi_mask, 3] = 0
        after_alpha = int((arr[:, :, 3] > 5).sum())
        roi_rows.append(
            {
                "part_id": part_id,
                "roi_abs_padded": part_rois[part_id],
                "before_alpha_pixels": before_alpha,
                "removed_outside_roi_pixels": removed,
                "after_alpha_pixels": after_alpha,
                "status": "PASS" if after_alpha > 0 else "REVIEW_EMPTY_AFTER_ROI",
            }
        )

    updated = json.loads(json.dumps(manifest))
    updated["status"] = "ROI_GUIDED_SEMANTIC_REMASK_V1_APPLIED"
    updated["roi_guided_semantic_remask"] = {
        "schema_version": 1,
        "applied_at": now(),
        "template": rel(TEMPLATE_PATH),
        "source_manifest": rel(source_manifest),
        "output_dir": rel(OUT_DIR),
        "method": "semantic owner-map underpaint transfer plus ROI-guided alpha remask from part_localization_template; no raw rectangular crop regeneration",
        "promoted_to_active_manifest": promote,
    }

    output_rows: list[dict[str, Any]] = []
    for layer in updated["layers"]:
        if not layer.get("include_in_import_psd"):
            continue
        part_id = layer["part_id"]
        target = OUT_DIR / Path(layer["output_path"]).name
        Image.fromarray(repaired[part_id].astype(np.uint8), "RGBA").save(target)
        method = "KEEP_EXISTING_ALPHA"
        if part_id in underpaint_moved:
            method = "UNDERPAINT_OWNER_TRANSFER"
        if any(row["part_id"] == part_id for row in roi_rows):
            method = "ROI_GUIDED_ALPHA_REMASK"
        layer["pre_roi_guided_semantic_remask_output_path"] = layer["output_path"]
        layer["output_path"] = rel(target)
        layer["semantic_group"] = semantic_group(part_id, layer.get("source_type"))
        layer["roi_guided_semantic_method"] = method
        meta = alpha_metadata(repaired[part_id])
        layer.update(meta)
        notes = layer.get("notes") or ""
        layer["notes"] = f"{notes} ROI-guided semantic remask v1 used localization seed without raw crop regeneration.".strip()
        output_rows.append(
            {
                "part_id": part_id,
                "method": method,
                "bbox_actual": layer["bbox_actual"],
                "alpha_coverage": layer["alpha_coverage"],
                "output_path": str(target),
            }
        )

    after_arrays = load_arrays(updated["layers"])
    after_composite, after_owner = composite(updated["layers"], after_arrays, NEUTRAL_HIDDEN, (2048, 2048))
    after_score = score(canonical, after_composite)
    after_underpaint = underpaint_leakage(updated["layers"], after_arrays, after_owner, "after_roi_guided")
    after_eye_mouth = eye_mouth_alignment(updated["layers"], after_arrays, rois)
    qa_rows = layer_role_qa(updated["layers"], after_arrays, rois)
    problem_rows = [row for row in qa_rows if row["verdict"] != "PASS"]

    save_owner_map(
        updated["layers"],
        after_owner,
        REPORT_DIR / "semantic_owner_map_after.png",
        REPORT_DIR / "semantic_owner_legend_after.json",
    )
    make_underpaint_map(after_owner, REPORT_DIR / "underpaint_leakage_map_after.png")
    save_layer_contact_sheet(updated["layers"], after_arrays, qa_rows, CONTACT_SHEET)
    save_layer_contact_sheet(updated["layers"], after_arrays, qa_rows, PROBLEM_SHEET, only_problem=True)
    save_roi_closeup_sheet(canonical, after_composite, after_arrays, rois, REPORT_DIR / "eye_mouth_roi_closeup_after.png")
    Image.fromarray(after_composite.astype(np.uint8), "RGBA").save(REPORT_DIR / "neutral_composite_after.png")
    save_contact_sheet([row for row in output_rows if row["method"] != "KEEP_EXISTING_ALPHA"], REPORT_DIR / "changed_layers_contact_sheet.png")

    write_json(SNAPSHOT_MANIFEST, updated)
    if promote:
        backup = MANIFEST_PATH.with_name("layer_manifest.before_roi_guided_semantic_remask_v1.json")
        if not backup.exists():
            shutil.copy2(MANIFEST_PATH, backup)
        write_json(MANIFEST_PATH, updated)

    pass_conditions = {
        "neutral_after_lte_5pct": after_score["bad_ratio_visible"] <= 0.05,
        "underpaint_top_owner_zero": after_underpaint["total_underpaint_top_owner_pixels"] == 0,
        "eye_mouth_after_pass": after_eye_mouth["status"] == "PASS",
        "roi_rows_nonempty": len(roi_rows) > 0,
        "no_empty_roi_guided_parts": all(row["status"] == "PASS" for row in roi_rows),
        "snapshot_manifest_written": SNAPSHOT_MANIFEST.exists(),
    }
    status = "PASS_ROI_GUIDED_SEMANTIC_REMASK_V1" if all(pass_conditions.values()) else "REVISE_ROI_GUIDED_SEMANTIC_REMASK_V1"
    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": status,
        "promoted_to_active_manifest": promote,
        "source_manifest": rel(source_manifest),
        "snapshot_manifest": rel(SNAPSHOT_MANIFEST),
        "active_manifest": rel(MANIFEST_PATH),
        "template": rel(TEMPLATE_PATH),
        "output_dir": rel(OUT_DIR),
        "metrics": {
            "template_parts": len(template.get("parts") or {}),
            "roi_guided_parts": len(roi_rows),
            "underpaint_moved_pixels_total": sum(underpaint_moved.values()),
            "changed_layers": sum(1 for row in output_rows if row["method"] != "KEEP_EXISTING_ALPHA"),
            "problem_rows_after": len(problem_rows),
        },
        "neutral_scores": {
            "before": before_score,
            "after": after_score,
        },
        "underpaint_leakage": {
            "before": before_underpaint,
            "after": after_underpaint,
            "moved_pixels_by_underpaint": underpaint_moved,
        },
        "eye_mouth_alignment": {
            "after": after_eye_mouth,
        },
        "roi_guided_rows": roi_rows,
        "layer_qa": {
            "total": len(qa_rows),
            "problem_count": len(problem_rows),
            "problem_rows": problem_rows,
        },
        "pass_conditions": pass_conditions,
        "artifacts": {
            "semantic_owner_map_before": rel(REPORT_DIR / "semantic_owner_map_before.png"),
            "semantic_owner_map_after": rel(REPORT_DIR / "semantic_owner_map_after.png"),
            "underpaint_leakage_map_after": rel(REPORT_DIR / "underpaint_leakage_map_after.png"),
            "layer_contact_sheet": rel(CONTACT_SHEET),
            "problem_sheet": rel(PROBLEM_SHEET),
            "eye_mouth_roi_closeup_after": rel(REPORT_DIR / "eye_mouth_roi_closeup_after.png"),
            "changed_layers_contact_sheet": rel(REPORT_DIR / "changed_layers_contact_sheet.png"),
            "neutral_composite_after": rel(REPORT_DIR / "neutral_composite_after.png"),
        },
        "interpretation": [
            "This remask uses manual localization as ROI seeds only; it does not regenerate visible layers by raw crop.",
            "A PASS means the localization template has been integrated into the semantic owner-map/underpaint repair path.",
            "This is still a material gate and does not replace real Cubism CMO3 deformer/keyform validation.",
        ],
    }
    write_json(REPORT_JSON, report)
    REPORT_MD.write_text(
        "\n".join(
            [
                "# ROI-Guided Semantic Remask v1",
                "",
                f"- status: `{status}`",
                f"- template parts: `{report['metrics']['template_parts']}`",
                f"- ROI-guided parts: `{report['metrics']['roi_guided_parts']}`",
                f"- changed layers: `{report['metrics']['changed_layers']}`",
                f"- neutral after bad ratio: `{after_score['bad_ratio_visible']}`",
                f"- underpaint top-owner after: `{after_underpaint['total_underpaint_top_owner_pixels']}`",
                f"- eye/mouth after: `{after_eye_mouth['status']}`",
                f"- problem rows after: `{len(problem_rows)}`",
                f"- snapshot manifest: `{rel(SNAPSHOT_MANIFEST)}`",
                f"- output dir: `{rel(OUT_DIR)}`",
                "",
                "## Artifacts",
                "",
                *[f"- `{value}`" for value in report["artifacts"].values()],
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-manifest", type=Path, default=SOURCE_MANIFEST)
    parser.add_argument("--promote", action="store_true", help="Write the ROI-guided snapshot back to the active layer_manifest.json when it passes.")
    args = parser.parse_args()
    report = build_remask(args.source_manifest, promote=args.promote)
    print(
        json.dumps(
            {
                "ok": report["status"].startswith("PASS"),
                "status": report["status"],
                "neutral_after": report["neutral_scores"]["after"],
                "underpaint_after": report["underpaint_leakage"]["after"]["total_underpaint_top_owner_pixels"],
                "eye_mouth_after": report["eye_mouth_alignment"]["after"]["status"],
                "snapshot_manifest": str(SNAPSHOT_MANIFEST),
                "report": str(REPORT_JSON),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if report["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())

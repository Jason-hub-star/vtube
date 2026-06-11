#!/usr/bin/env python3
"""Build and apply the Cubism v2 G1.5 semantic purity gate.

This gate checks whether full-canvas parts only look right when composited, or
whether they also carry pixels that match their semantic role.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = ROOT / "experiments/cubism-v2-new-character-001/material_pack_v0"
MANIFEST_PATH = PACK_DIR / "layer_manifest.json"
CANONICAL_PATH = PACK_DIR / "canonical/candidate_002_2048_rgba.png"
REPORT_DIR = PACK_DIR / "reports/semantic_purity"
REPAIRED_DIR = PACK_DIR / "production_layers_semantic_repair_v1"

NEUTRAL_HIDDEN = {
    "eye_L_closed_lid",
    "eye_R_closed_lid",
    "mouth_inner",
    "mouth_teeth",
    "mouth_tongue",
    "mouth_upper_lip_mask",
    "mouth_lower_lip_mask",
    "mouth_corner_L",
    "mouth_corner_R",
}

UNDERPAINT_TARGETS = {
    "body_underpaint": "torso_base",
    "neck_shadow_underpaint": "neck",
    "arm_L_underpaint": "arm_L_upper_simple",
    "arm_R_underpaint": "arm_R_upper_simple",
    "face_underpaint_L": "face_base",
    "face_underpaint_R": "face_base",
    "eye_L_underpaint": "eye_L_white",
    "eye_R_underpaint": "eye_R_white",
    "hair_back_underpaint": "hair_back_base",
}

SEMANTIC_COLORS = {
    "body": (67, 133, 255, 230),
    "hair": (151, 93, 74, 230),
    "face": (255, 184, 162, 230),
    "eye": (120, 92, 255, 230),
    "brow": (99, 69, 55, 230),
    "mouth": (230, 66, 110, 230),
    "clothing": (255, 204, 71, 230),
    "underpaint": (96, 201, 145, 230),
    "metadata": (130, 130, 130, 230),
    "unknown": (220, 220, 220, 230),
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def resolve(path_value: str) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def font(size: int) -> ImageFont.ImageFont:
    for candidate in [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


def semantic_group(part_id: str, source_type: str | None = None) -> str:
    if source_type == "MERGED_METADATA":
        return "metadata"
    if source_type == "UNDERPAINT" or "underpaint" in part_id:
        return "underpaint"
    if part_id.startswith("hair_"):
        return "hair"
    if part_id.startswith("eye_"):
        return "eye"
    if part_id.startswith("brow_"):
        return "brow"
    if part_id.startswith("mouth_"):
        return "mouth"
    if part_id.startswith("face_") or part_id in {"nose", "cheek_L", "cheek_R"}:
        return "face"
    if "cloth" in part_id or "collar" in part_id:
        return "clothing"
    if any(token in part_id for token in ["body", "torso", "neck", "shoulder", "arm_"]):
        return "body"
    return "unknown"


def include_layers(layers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in layers if item.get("include_in_import_psd")]


def load_arrays(layers: list[dict[str, Any]]) -> dict[str, np.ndarray]:
    arrays: dict[str, np.ndarray] = {}
    for layer in include_layers(layers):
        arrays[layer["part_id"]] = np.array(Image.open(resolve(layer["output_path"])).convert("RGBA"))
    return arrays


def composite(
    layers: list[dict[str, Any]],
    arrays: dict[str, np.ndarray],
    hidden: set[str],
    size: tuple[int, int],
) -> tuple[np.ndarray, np.ndarray]:
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    owner = np.full((size[1], size[0]), "", dtype=object)
    for layer in sorted(include_layers(layers), key=lambda item: int(item.get("draw_order", 500))):
        part_id = layer["part_id"]
        if part_id in hidden:
            continue
        arr = arrays[part_id]
        alpha = arr[:, :, 3] > 5
        owner[alpha] = part_id
        canvas.alpha_composite(Image.fromarray(arr.astype(np.uint8), "RGBA"))
    return np.array(canvas), owner


def score(canonical: np.ndarray, current: np.ndarray) -> dict[str, Any]:
    visible = (canonical[:, :, 3] > 5) | (current[:, :, 3] > 5)
    rgb_diff = np.abs(canonical[:, :, :3].astype(int) - current[:, :, :3].astype(int)).mean(axis=2)
    alpha_diff = np.abs(canonical[:, :, 3].astype(int) - current[:, :, 3].astype(int))
    bad = visible & ((rgb_diff > 35) | (alpha_diff > 35))
    missing = (canonical[:, :, 3] > 5) & (current[:, :, 3] <= 5)
    extra = (current[:, :, 3] > 5) & (canonical[:, :, 3] <= 5)
    return {
        "visible_pixels": int(visible.sum()),
        "bad_pixels": int(bad.sum()),
        "bad_ratio_visible": round(float(bad.sum() / max(1, visible.sum())), 6),
        "missing_pixels": int(missing.sum()),
        "extra_pixels": int(extra.sum()),
    }


def bbox_from_alpha(arr: np.ndarray, threshold: int = 5) -> list[int]:
    ys, xs = np.where(arr[:, :, 3] > threshold)
    if len(xs) == 0:
        return [0, 0, 0, 0]
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    return [x0, y0, x1 - x0, y1 - y0]


def union_bbox(rows: list[list[int]], pad: int = 0, size: tuple[int, int] = (2048, 2048)) -> list[int]:
    valid = [r for r in rows if r and r[2] > 0 and r[3] > 0]
    if not valid:
        return [0, 0, 0, 0]
    x0 = max(0, min(r[0] for r in valid) - pad)
    y0 = max(0, min(r[1] for r in valid) - pad)
    x1 = min(size[0], max(r[0] + r[2] for r in valid) + pad)
    y1 = min(size[1], max(r[1] + r[3] for r in valid) + pad)
    return [x0, y0, x1 - x0, y1 - y0]


def in_bbox_mask(shape: tuple[int, int], bbox: list[int]) -> np.ndarray:
    y, x = np.indices(shape)
    bx, by, bw, bh = bbox
    return (x >= bx) & (x < bx + bw) & (y >= by) & (y < by + bh)


def build_rois(layers: list[dict[str, Any]]) -> dict[str, list[int]]:
    by_part = {layer["part_id"]: layer for layer in include_layers(layers)}

    def b(part: str) -> list[int]:
        row = by_part.get(part, {})
        return row.get("bbox_actual") or row.get("bbox") or [0, 0, 0, 0]

    return {
        "eye_L": union_bbox([b(p) for p in ["eye_L_white", "eye_L_iris", "eye_L_pupil", "eye_L_highlight", "eye_L_upper_lash", "eye_L_lower_lash", "eye_L_closed_lid"]], 18),
        "eye_R": union_bbox([b(p) for p in ["eye_R_white", "eye_R_iris", "eye_R_pupil", "eye_R_highlight", "eye_R_upper_lash", "eye_R_lower_lash", "eye_R_closed_lid"]], 18),
        "mouth": union_bbox([b(p) for p in ["mouth_line", "mouth_inner", "mouth_teeth", "mouth_tongue", "mouth_upper_lip_mask", "mouth_lower_lip_mask", "mouth_corner_L", "mouth_corner_R"]], 20),
    }


def save_owner_map(
    layers: list[dict[str, Any]],
    owner: np.ndarray,
    out_path: Path,
    legend_path: Path,
) -> dict[str, Any]:
    lookup = {layer["part_id"]: semantic_group(layer["part_id"], layer.get("source_type")) for layer in include_layers(layers)}
    rgba = np.zeros((owner.shape[0], owner.shape[1], 4), dtype=np.uint8)
    counts: dict[str, int] = {}
    part_counts: dict[str, int] = {}
    for part_id in sorted(set(owner.flatten()) - {""}):
        group = lookup.get(part_id, "unknown")
        mask = owner == part_id
        rgba[mask] = SEMANTIC_COLORS[group]
        counts[group] = counts.get(group, 0) + int(mask.sum())
        part_counts[part_id] = int(mask.sum())
    Image.fromarray(rgba, "RGBA").save(out_path)
    legend = {
        "semantic_colors": {key: list(value) for key, value in SEMANTIC_COLORS.items()},
        "top_owner_pixels_by_group": counts,
        "top_owner_pixels_by_part": dict(sorted(part_counts.items(), key=lambda item: item[1], reverse=True)),
    }
    write_json(legend_path, legend)
    return legend


def layer_role_qa(layers: list[dict[str, Any]], arrays: dict[str, np.ndarray], rois: dict[str, list[int]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    masks = {
        "eye_L": in_bbox_mask((2048, 2048), rois["eye_L"]),
        "eye_R": in_bbox_mask((2048, 2048), rois["eye_R"]),
        "mouth": in_bbox_mask((2048, 2048), rois["mouth"]),
    }
    for layer in include_layers(layers):
        part_id = layer["part_id"]
        arr = arrays[part_id]
        alpha = arr[:, :, 3] > 5
        alpha_pixels = int(alpha.sum())
        issues: list[str] = []
        verdict = "PASS"
        expected_roi = None
        if part_id.startswith("eye_L_"):
            expected_roi = "eye_L"
        elif part_id.startswith("eye_R_"):
            expected_roi = "eye_R"
        elif part_id.startswith("mouth_"):
            expected_roi = "mouth"
        if alpha_pixels <= 0:
            issues.append("empty_alpha")
        if expected_roi and alpha_pixels:
            outside = int((alpha & ~masks[expected_roi]).sum())
            outside_ratio = outside / max(1, alpha_pixels)
            if outside_ratio > 0.02:
                issues.append("outside_roi")
        else:
            outside_ratio = 0.0
        if layer.get("source_type") == "UNDERPAINT":
            issues.append("check_underpaint_leakage")
        if alpha_pixels and alpha_pixels < 20:
            issues.append("tiny_alpha")
        if issues:
            if "empty_alpha" in issues or "outside_roi" in issues:
                verdict = "REPAIR_MASK"
            elif "check_underpaint_leakage" in issues:
                verdict = "CHECK_UNDERPAINT"
            else:
                verdict = "REVIEW"
        rows.append(
            {
                "part_id": part_id,
                "label_ko": layer.get("label_ko"),
                "semantic_group": semantic_group(part_id, layer.get("source_type")),
                "source_type": layer.get("source_type"),
                "bbox_actual": layer.get("bbox_actual") or layer.get("bbox"),
                "alpha_pixels": alpha_pixels,
                "outside_expected_roi_ratio": round(outside_ratio, 6),
                "issues": issues,
                "verdict": verdict,
            }
        )
    return rows


def save_layer_contact_sheet(
    layers: list[dict[str, Any]],
    arrays: dict[str, np.ndarray],
    qa_rows: list[dict[str, Any]],
    out_path: Path,
    only_problem: bool = False,
) -> None:
    qa_by_part = {row["part_id"]: row for row in qa_rows}
    selected = [layer for layer in include_layers(layers) if not only_problem or qa_by_part[layer["part_id"]]["verdict"] != "PASS"]
    cell_w, cell_h = 260, 300
    cols = 4
    rows = max(1, (len(selected) + cols - 1) // cols)
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), (247, 249, 252))
    draw = ImageDraw.Draw(sheet)
    title_font = font(16)
    small_font = font(12)
    for idx, layer in enumerate(selected):
        x = (idx % cols) * cell_w
        y = (idx // cols) * cell_h
        draw.rounded_rectangle((x + 8, y + 8, x + cell_w - 8, y + cell_h - 8), radius=8, fill=(255, 255, 255), outline=(225, 230, 238))
        part_id = layer["part_id"]
        arr = arrays[part_id]
        bbox = bbox_from_alpha(arr)
        if bbox[2] > 0 and bbox[3] > 0:
            crop = Image.fromarray(arr.astype(np.uint8), "RGBA").crop((bbox[0], bbox[1], bbox[0] + bbox[2], bbox[1] + bbox[3]))
            bg = Image.new("RGBA", crop.size, (245, 245, 245, 255))
            bg.alpha_composite(crop)
            bg.thumbnail((cell_w - 36, 170), Image.Resampling.LANCZOS)
            sheet.paste(bg.convert("RGB"), (x + (cell_w - bg.width) // 2, y + 20))
        qa = qa_by_part[part_id]
        color = (25, 135, 84) if qa["verdict"] == "PASS" else (214, 51, 70)
        draw.text((x + 16, y + 202), part_id[:28], fill=(30, 40, 55), font=title_font)
        draw.text((x + 16, y + 225), qa["verdict"], fill=color, font=small_font)
        draw.text((x + 16, y + 244), f"bbox={qa['bbox_actual']} px={qa['alpha_pixels']}", fill=(85, 96, 112), font=small_font)
        draw.text((x + 16, y + 264), ",".join(qa["issues"])[:36] or "ok", fill=(85, 96, 112), font=small_font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def save_roi_closeup_sheet(
    canonical: np.ndarray,
    current: np.ndarray,
    arrays: dict[str, np.ndarray],
    rois: dict[str, list[int]],
    out_path: Path,
) -> None:
    specs = [
        ("eye_L", ["eye_L_white", "eye_L_iris", "eye_L_pupil", "eye_L_highlight", "eye_L_upper_lash", "eye_L_lower_lash", "eye_L_closed_lid"]),
        ("eye_R", ["eye_R_white", "eye_R_iris", "eye_R_pupil", "eye_R_highlight", "eye_R_upper_lash", "eye_R_lower_lash", "eye_R_closed_lid"]),
        ("mouth", ["mouth_line", "mouth_inner", "mouth_teeth", "mouth_tongue", "mouth_upper_lip_mask", "mouth_lower_lip_mask", "mouth_corner_L", "mouth_corner_R"]),
    ]
    thumb_w, thumb_h = 180, 150
    label_h = 38
    cols = 5
    cards: list[tuple[str, Image.Image]] = []
    for roi_name, parts in specs:
        x, y, w, h = rois[roi_name]
        crop_box = (x, y, x + w, y + h)
        cards.append((f"{roi_name} canonical", Image.fromarray(canonical.astype(np.uint8), "RGBA").crop(crop_box)))
        cards.append((f"{roi_name} composite", Image.fromarray(current.astype(np.uint8), "RGBA").crop(crop_box)))
        for part in parts:
            if part in arrays:
                cards.append((part, Image.fromarray(arrays[part].astype(np.uint8), "RGBA").crop(crop_box)))
    rows = max(1, (len(cards) + cols - 1) // cols)
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), (246, 248, 251))
    draw = ImageDraw.Draw(sheet)
    small = font(12)
    for idx, (label, image) in enumerate(cards):
        x = (idx % cols) * thumb_w
        y = (idx // cols) * (thumb_h + label_h)
        draw.rounded_rectangle((x + 6, y + 6, x + thumb_w - 6, y + thumb_h + label_h - 6), radius=8, fill=(255, 255, 255), outline=(226, 232, 240))
        bg = Image.new("RGBA", image.size, (245, 245, 245, 255))
        bg.alpha_composite(image)
        bg.thumbnail((thumb_w - 22, thumb_h - 16), Image.Resampling.LANCZOS)
        sheet.paste(bg.convert("RGB"), (x + (thumb_w - bg.width) // 2, y + 12))
        draw.text((x + 12, y + thumb_h + 4), label[:24], fill=(45, 55, 72), font=small)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def eye_mouth_alignment(layers: list[dict[str, Any]], arrays: dict[str, np.ndarray], rois: dict[str, list[int]]) -> dict[str, Any]:
    def bbox(part: str) -> list[int]:
        return bbox_from_alpha(arrays[part]) if part in arrays else [0, 0, 0, 0]

    def center(box: list[int]) -> tuple[float, float]:
        return (box[0] + box[2] / 2, box[1] + box[3] / 2)

    checks: list[dict[str, Any]] = []
    for side in ["L", "R"]:
        prefix = f"eye_{side}"
        roi = rois[f"eye_{side}"]
        roi_mask = in_bbox_mask((2048, 2048), roi)
        for suffix in ["white", "iris", "pupil", "highlight", "upper_lash", "lower_lash", "closed_lid"]:
            part = f"{prefix}_{suffix}"
            if part not in arrays:
                checks.append({"part_id": part, "status": "MISSING"})
                continue
            alpha = arrays[part][:, :, 3] > 5
            outside = int((alpha & ~roi_mask).sum())
            alpha_pixels = int(alpha.sum())
            checks.append(
                {
                    "part_id": part,
                    "status": "PASS" if alpha_pixels > 0 and outside / max(1, alpha_pixels) <= 0.02 else "REPAIR",
                    "bbox": bbox(part),
                    "center": list(center(bbox(part))),
                    "outside_roi_ratio": round(outside / max(1, alpha_pixels), 6),
                    "alpha_pixels": alpha_pixels,
                }
            )
        white_box = bbox(f"{prefix}_white")
        for child in [f"{prefix}_iris", f"{prefix}_pupil"]:
            child_box = bbox(child)
            inside = (
                child_box[0] >= white_box[0] - 20
                and child_box[1] >= white_box[1] - 30
                and child_box[0] + child_box[2] <= white_box[0] + white_box[2] + 35
                and child_box[1] + child_box[3] <= white_box[1] + white_box[3] + 35
            )
            checks.append({"part_id": child, "relation": "inside_eye_white_with_margin", "status": "PASS" if inside else "REPAIR"})

    mouth_roi_mask = in_bbox_mask((2048, 2048), rois["mouth"])
    for part in ["mouth_line", "mouth_inner", "mouth_teeth", "mouth_tongue", "mouth_upper_lip_mask", "mouth_lower_lip_mask", "mouth_corner_L", "mouth_corner_R"]:
        alpha = arrays.get(part, np.zeros((2048, 2048, 4), dtype=np.uint8))[:, :, 3] > 5
        outside = int((alpha & ~mouth_roi_mask).sum())
        alpha_pixels = int(alpha.sum())
        checks.append(
            {
                "part_id": part,
                "status": "PASS" if alpha_pixels > 0 and outside / max(1, alpha_pixels) <= 0.02 else "REPAIR",
                "bbox": bbox(part),
                "center": list(center(bbox(part))),
                "outside_roi_ratio": round(outside / max(1, alpha_pixels), 6),
                "alpha_pixels": alpha_pixels,
            }
        )
    return {
        "status": "PASS" if all(row.get("status") == "PASS" for row in checks if "status" in row) else "REPAIR",
        "rois": rois,
        "checks": checks,
    }


def underpaint_leakage(
    layers: list[dict[str, Any]],
    arrays: dict[str, np.ndarray],
    owner: np.ndarray,
    stage: str,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    total = 0
    for layer in include_layers(layers):
        if layer.get("source_type") != "UNDERPAINT":
            continue
        part_id = layer["part_id"]
        top = owner == part_id
        alpha = arrays[part_id][:, :, 3] > 5
        top_pixels = int(top.sum())
        alpha_pixels = int(alpha.sum())
        total += top_pixels
        rows.append(
            {
                "part_id": part_id,
                "stage": stage,
                "alpha_pixels": alpha_pixels,
                "neutral_top_owner_pixels": top_pixels,
                "top_owner_ratio_of_alpha": round(top_pixels / max(1, alpha_pixels), 6),
                "target_part": UNDERPAINT_TARGETS.get(part_id),
                "status": "PASS" if top_pixels == 0 else "REPAIR_UNDERPAINT",
            }
        )
    return {
        "stage": stage,
        "total_underpaint_top_owner_pixels": total,
        "rows": sorted(rows, key=lambda item: item["neutral_top_owner_pixels"], reverse=True),
    }


def make_underpaint_map(owner: np.ndarray, out_path: Path) -> None:
    rgba = np.zeros((owner.shape[0], owner.shape[1], 4), dtype=np.uint8)
    for part in UNDERPAINT_TARGETS:
        rgba[owner == part] = [255, 0, 80, 230]
    Image.fromarray(rgba, "RGBA").save(out_path)


def apply_semantic_remask(
    layers: list[dict[str, Any]],
    arrays: dict[str, np.ndarray],
    owner: np.ndarray,
    rois: dict[str, list[int]],
    canonical: np.ndarray,
) -> dict[str, np.ndarray]:
    repaired = {part_id: arr.copy() for part_id, arr in arrays.items()}

    # Move neutral-visible pixels owned by underpaint into the closest semantic
    # visible layer, then hide that exact pixel in the underpaint layer.
    for underpaint_id, target_id in UNDERPAINT_TARGETS.items():
        if underpaint_id not in repaired or target_id not in repaired:
            continue
        move = owner == underpaint_id
        if move.any():
            repaired[target_id][move] = canonical[move]
            repaired[underpaint_id][move, 3] = 0

    # Keep eye and mouth helper/source parts inside their dedicated ROIs. This
    # prevents a neutral-perfect composite from hiding off-role stray pixels.
    roi_masks = {
        "eye_L": in_bbox_mask((2048, 2048), rois["eye_L"]),
        "eye_R": in_bbox_mask((2048, 2048), rois["eye_R"]),
        "mouth": in_bbox_mask((2048, 2048), rois["mouth"]),
    }
    for part_id, arr in repaired.items():
        if part_id.startswith("eye_L_"):
            arr[~roi_masks["eye_L"], 3] = 0
        elif part_id.startswith("eye_R_"):
            arr[~roi_masks["eye_R"], 3] = 0
        elif part_id.startswith("mouth_"):
            arr[~roi_masks["mouth"], 3] = 0

    return repaired


def update_layer_metadata(layer: dict[str, Any], arr: np.ndarray) -> None:
    bbox = bbox_from_alpha(arr)
    layer["bbox_actual"] = bbox
    layer["alpha_coverage"] = round(float((arr[:, :, 3] > 5).sum() / (arr.shape[0] * arr.shape[1])), 8)


def write_repaired_layers(manifest: dict[str, Any], repaired: dict[str, np.ndarray]) -> dict[str, Any]:
    REPAIRED_DIR.mkdir(parents=True, exist_ok=True)
    updated = json.loads(json.dumps(manifest))
    updated["status"] = "SEMANTIC_REPAIR_V1_APPLIED"
    updated["semantic_purity"] = {
        "schema_version": 1,
        "applied_at": now(),
        "gate": "G1.5_SEMANTIC_PURITY",
        "repaired_layer_dir": rel(REPAIRED_DIR),
        "method": "move neutral-visible underpaint ownership into semantic visible parts and clamp eye/mouth alpha to ROIs",
    }
    for layer in updated["layers"]:
        if not layer.get("include_in_import_psd"):
            continue
        part_id = layer["part_id"]
        target = REPAIRED_DIR / Path(layer["output_path"]).name
        Image.fromarray(repaired[part_id].astype(np.uint8), "RGBA").save(target)
        layer["pre_semantic_repair_output_path"] = layer["output_path"]
        layer["output_path"] = rel(target)
        layer["semantic_group"] = semantic_group(part_id, layer.get("source_type"))
        update_layer_metadata(layer, repaired[part_id])
        notes = layer.get("notes") or ""
        layer["notes"] = f"{notes} Semantic repair v1 checked owner role and clamped role-specific alpha.".strip()
    backup = MANIFEST_PATH.with_name("layer_manifest.before_semantic_repair_v1.json")
    if not backup.exists():
        shutil.copy2(MANIFEST_PATH, backup)
    write_json(MANIFEST_PATH, updated)
    return updated


def write_md_report(report: dict[str, Any], path: Path) -> None:
    md = [
        "# G1.5 Semantic Purity Gate",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Neutral Composite",
        "",
        f"- Before semantic repair: `{report['neutral_scores']['before_semantic_repair']['bad_ratio_visible']}`",
        f"- After semantic repair: `{report['neutral_scores']['after_semantic_repair']['bad_ratio_visible']}`",
        "",
        "## Underpaint Leakage",
        "",
        f"- Before top-owned underpaint pixels: `{report['underpaint_leakage']['before']['total_underpaint_top_owner_pixels']}`",
        f"- After top-owned underpaint pixels: `{report['underpaint_leakage']['after']['total_underpaint_top_owner_pixels']}`",
        "",
        "## Eye/Mouth ROI",
        "",
        f"- Before: `{report['eye_mouth_alignment']['before']['status']}`",
        f"- After: `{report['eye_mouth_alignment']['after']['status']}`",
        "",
        "## Layer QA",
        "",
        f"- Total layers checked: `{report['layer_alone_qa']['total']}`",
        f"- Problem/review layers after repair: `{report['layer_alone_qa']['after_problem_count']}`",
        "",
        "## Artifacts",
        "",
    ]
    for key, value in report["artifacts"].items():
        md.append(f"- `{key}`: `{value}`")
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def run(apply_remask: bool, source_manifest: Path | None = None) -> dict[str, Any]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if source_manifest is not None:
        source_manifest_path = source_manifest
    else:
        default_backup = MANIFEST_PATH.with_name("layer_manifest.before_semantic_repair_v1.json")
        source_manifest_path = default_backup if default_backup.exists() else MANIFEST_PATH
    manifest = load_json(source_manifest_path)
    layers = manifest["layers"]
    canonical = np.array(Image.open(CANONICAL_PATH).convert("RGBA"))
    arrays = load_arrays(layers)
    rois = build_rois(layers)

    before_composite, before_owner = composite(layers, arrays, NEUTRAL_HIDDEN, (2048, 2048))
    before_score = score(canonical, before_composite)
    before_legend = save_owner_map(
        layers,
        before_owner,
        REPORT_DIR / "semantic_owner_map_before.png",
        REPORT_DIR / "semantic_owner_legend_before.json",
    )
    before_underpaint = underpaint_leakage(layers, arrays, before_owner, "before")
    make_underpaint_map(before_owner, REPORT_DIR / "underpaint_leakage_map_before.png")
    before_eye_mouth = eye_mouth_alignment(layers, arrays, rois)
    before_qa = layer_role_qa(layers, arrays, rois)
    save_layer_contact_sheet(layers, arrays, before_qa, REPORT_DIR / "layer_alone_contact_sheet_before.png")
    save_layer_contact_sheet(layers, arrays, before_qa, REPORT_DIR / "layer_alone_problem_sheet_before.png", only_problem=True)

    repaired_arrays = apply_semantic_remask(layers, arrays, before_owner, rois, canonical)
    effective_layers = layers
    effective_arrays = repaired_arrays
    if apply_remask:
        repaired_manifest = write_repaired_layers(manifest, repaired_arrays)
        effective_layers = repaired_manifest["layers"]
        effective_arrays = load_arrays(effective_layers)

    after_composite, after_owner = composite(effective_layers, effective_arrays, NEUTRAL_HIDDEN, (2048, 2048))
    after_score = score(canonical, after_composite)
    after_legend = save_owner_map(
        effective_layers,
        after_owner,
        REPORT_DIR / "semantic_owner_map_after.png",
        REPORT_DIR / "semantic_owner_legend_after.json",
    )
    after_underpaint = underpaint_leakage(effective_layers, effective_arrays, after_owner, "after")
    make_underpaint_map(after_owner, REPORT_DIR / "underpaint_leakage_map_after.png")
    after_eye_mouth = eye_mouth_alignment(effective_layers, effective_arrays, build_rois(effective_layers))
    after_qa = layer_role_qa(effective_layers, effective_arrays, build_rois(effective_layers))
    save_layer_contact_sheet(effective_layers, effective_arrays, after_qa, REPORT_DIR / "layer_alone_contact_sheet_after.png")
    save_layer_contact_sheet(effective_layers, effective_arrays, after_qa, REPORT_DIR / "layer_alone_problem_sheet_after.png", only_problem=True)
    save_roi_closeup_sheet(canonical, before_composite, arrays, rois, REPORT_DIR / "eye_mouth_roi_closeup_before.png")
    save_roi_closeup_sheet(canonical, after_composite, effective_arrays, build_rois(effective_layers), REPORT_DIR / "eye_mouth_roi_closeup_after.png")
    Image.fromarray(after_composite.astype(np.uint8), "RGBA").save(REPORT_DIR / "semantic_repair_neutral_composite_after.png")

    before_problems = [row for row in before_qa if row["verdict"] != "PASS"]
    after_problems = [row for row in after_qa if row["verdict"] != "PASS"]
    pass_conditions = {
        "neutral_after_lte_5pct": after_score["bad_ratio_visible"] <= 0.05,
        "underpaint_leakage_reduced": after_underpaint["total_underpaint_top_owner_pixels"] < before_underpaint["total_underpaint_top_owner_pixels"],
        "eye_mouth_after_pass": after_eye_mouth["status"] == "PASS",
        "layer_alone_generated": (REPORT_DIR / "layer_alone_contact_sheet_after.png").exists(),
        "owner_maps_generated": (REPORT_DIR / "semantic_owner_map_after.png").exists(),
        "manifest_applied": (not apply_remask) or load_json(MANIFEST_PATH).get("status") == "SEMANTIC_REPAIR_V1_APPLIED",
    }
    status = "PASS_G1_5_SEMANTIC_PURITY_GATE" if all(pass_conditions.values()) else "REVISE_G1_5_SEMANTIC_PURITY_GATE"
    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": status,
        "apply_remask": apply_remask,
        "source_manifest": str(source_manifest_path if source_manifest_path.exists() else MANIFEST_PATH),
        "active_manifest": str(MANIFEST_PATH),
        "rois": rois,
        "neutral_scores": {
            "before_semantic_repair": before_score,
            "after_semantic_repair": after_score,
        },
        "semantic_owner": {
            "before": before_legend,
            "after": after_legend,
        },
        "underpaint_leakage": {
            "before": before_underpaint,
            "after": after_underpaint,
        },
        "eye_mouth_alignment": {
            "before": before_eye_mouth,
            "after": after_eye_mouth,
        },
        "layer_alone_qa": {
            "total": len(after_qa),
            "before_problem_count": len(before_problems),
            "after_problem_count": len(after_problems),
            "before_problem_rows": before_problems,
            "after_problem_rows": after_problems,
        },
        "pass_conditions": pass_conditions,
        "artifacts": {
            "semantic_owner_map_before": str(REPORT_DIR / "semantic_owner_map_before.png"),
            "semantic_owner_map_after": str(REPORT_DIR / "semantic_owner_map_after.png"),
            "semantic_owner_legend_before": str(REPORT_DIR / "semantic_owner_legend_before.json"),
            "semantic_owner_legend_after": str(REPORT_DIR / "semantic_owner_legend_after.json"),
            "layer_alone_contact_sheet_before": str(REPORT_DIR / "layer_alone_contact_sheet_before.png"),
            "layer_alone_contact_sheet_after": str(REPORT_DIR / "layer_alone_contact_sheet_after.png"),
            "layer_alone_problem_sheet_before": str(REPORT_DIR / "layer_alone_problem_sheet_before.png"),
            "layer_alone_problem_sheet_after": str(REPORT_DIR / "layer_alone_problem_sheet_after.png"),
            "eye_mouth_roi_closeup_before": str(REPORT_DIR / "eye_mouth_roi_closeup_before.png"),
            "eye_mouth_roi_closeup_after": str(REPORT_DIR / "eye_mouth_roi_closeup_after.png"),
            "underpaint_leakage_map_before": str(REPORT_DIR / "underpaint_leakage_map_before.png"),
            "underpaint_leakage_map_after": str(REPORT_DIR / "underpaint_leakage_map_after.png"),
            "semantic_repair_neutral_composite_after": str(REPORT_DIR / "semantic_repair_neutral_composite_after.png"),
        },
        "interpretation": [
            "This gate checks role ownership after neutral composite repair.",
            "A PASS means the current material pack is safer to take into real Cubism ArtMesh/deformer authoring, but still does not prove CMO3 runtime quality.",
        ],
    }
    write_json(REPORT_DIR / "semantic_purity_gate_report.json", report)
    write_md_report(report, REPORT_DIR / "semantic_purity_gate_report.md")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-apply-remask", action="store_true", help="Generate reports without writing the semantic repair manifest/layers.")
    parser.add_argument(
        "--source-manifest",
        type=Path,
        default=None,
        help="Manifest to validate instead of the default pre-semantic-repair backup.",
    )
    args = parser.parse_args()
    report = run(apply_remask=not args.no_apply_remask, source_manifest=args.source_manifest)
    print(
        json.dumps(
            {
                "ok": report["status"] == "PASS_G1_5_SEMANTIC_PURITY_GATE",
                "status": report["status"],
                "neutral_after": report["neutral_scores"]["after_semantic_repair"],
                "underpaint_before": report["underpaint_leakage"]["before"]["total_underpaint_top_owner_pixels"],
                "underpaint_after": report["underpaint_leakage"]["after"]["total_underpaint_top_owner_pixels"],
                "report": str(REPORT_DIR / "semantic_purity_gate_report.json"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if report["status"] == "PASS_G1_5_SEMANTIC_PURITY_GATE" else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build ROI-focused cleanup candidates for MPS See-through parts.

The outputs are review candidates only. They are never included in the PSD until
the human review app marks them as O.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
MPS_EXP = ROOT / "experiments" / "see-through-mps-compat-002"
MPS_MANIFEST = MPS_EXP / "layer_manifest.json"
CANONICAL = ROOT / "experiments" / "concept-regeneration-001" / "canonical" / "canonical_front_2048.png"
CANVAS = [2048, 2048]

EXPERIMENTS = {
    "mouth": ROOT / "experiments" / "mouth-roi-cleanup-001",
    "neck": ROOT / "experiments" / "neck-roi-cleanup-001",
    "clothes": ROOT / "experiments" / "clothes-roi-cleanup-001",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_rgba(path: Path) -> Image.Image:
    if not path.exists():
        raise FileNotFoundError(path)
    return Image.open(path).convert("RGBA")


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def bbox_from_alpha(alpha: np.ndarray) -> list[int] | None:
    ys, xs = np.where(alpha > 10)
    if len(xs) == 0:
        return None
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    return [x0, y0, x1 - x0, y1 - y0]


def alpha_coverage(alpha: np.ndarray, bbox: list[int] | None) -> float:
    if not bbox:
        return 0.0
    x, y, w, h = bbox
    crop = alpha[y : y + h, x : x + w]
    if crop.size == 0:
        return 0.0
    return round(float(np.count_nonzero(crop > 10) / crop.size), 6)


def roi_mask(roi: list[int]) -> np.ndarray:
    x, y, w, h = roi
    mask = np.zeros((CANVAS[1], CANVAS[0]), dtype=bool)
    mask[y : y + h, x : x + w] = True
    return mask


def layer_alpha(layer_name: str, radius: int = 0, directory: Path | None = None) -> np.ndarray:
    base = directory or MPS_EXP / "normalized_layers"
    img = load_rgba(base / f"{layer_name}.png")
    alpha = img.getchannel("A")
    if radius > 1:
        alpha = alpha.filter(ImageFilter.MaxFilter(radius if radius % 2 else radius + 1))
    return np.array(alpha) > 10


def skin_mask(rgba: np.ndarray) -> np.ndarray:
    r = rgba[:, :, 0].astype(np.int16)
    g = rgba[:, :, 1].astype(np.int16)
    b = rgba[:, :, 2].astype(np.int16)
    a = rgba[:, :, 3] > 10
    return a & (r > 130) & (g > 80) & (b > 60) & (r > g) & (g > b) & ((r - b) > 35)


def skin_keep_mask(rgba: np.ndarray) -> np.ndarray:
    r = rgba[:, :, 0].astype(np.int16)
    g = rgba[:, :, 1].astype(np.int16)
    b = rgba[:, :, 2].astype(np.int16)
    a = rgba[:, :, 3] > 10
    return a & (r > 145) & (g > 100) & (b > 90) & (r >= g - 10) & (g >= b - 12) & ((r - b) > 8)


def dark_or_gold_mask(rgba: np.ndarray) -> np.ndarray:
    r = rgba[:, :, 0].astype(np.int16)
    g = rgba[:, :, 1].astype(np.int16)
    b = rgba[:, :, 2].astype(np.int16)
    a = rgba[:, :, 3] > 10
    luma = (r * 30 + g * 59 + b * 11) // 100
    dark = luma < 118
    gold = (r > 118) & (g > 75) & (b < 100) & (r >= g) & ((r - b) > 38)
    return a & (dark | gold)


def mouth_masks(rgba: np.ndarray) -> dict[str, np.ndarray]:
    r = rgba[:, :, 0].astype(np.int16)
    g = rgba[:, :, 1].astype(np.int16)
    b = rgba[:, :, 2].astype(np.int16)
    a = rgba[:, :, 3] > 10
    luma = (r * 30 + g * 59 + b * 11) // 100
    line = a & ((luma < 150) | ((r > g + 8) & (r > b + 8) & (luma < 190)))
    teeth = a & (luma > 214) & (abs(r - g) < 20) & (abs(g - b) < 25)
    tongue = a & (r > 150) & (g > 80) & (b > 90) & (r > b + 8) & (luma < 214) & ~line
    inner = a & ~line & ~teeth & ~tongue
    return {
        "mouth_line": line,
        "mouth_inner": inner,
        "teeth": teeth,
        "tongue": tongue,
    }


def write_masked_layer(source: Image.Image, keep: np.ndarray, output: Path) -> dict[str, Any]:
    rgba = np.array(source)
    rgba[:, :, 3] = np.where(keep, rgba[:, :, 3], 0).astype(np.uint8)
    output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, "RGBA").save(output)
    bbox = bbox_from_alpha(rgba[:, :, 3])
    return {
        "bbox": bbox,
        "alpha_coverage": alpha_coverage(rgba[:, :, 3], bbox),
    }


def write_filled_layer(keep: np.ndarray, color: tuple[int, int, int, int], output: Path) -> dict[str, Any]:
    rgba = np.zeros((CANVAS[1], CANVAS[0], 4), dtype=np.uint8)
    rgba[:, :, 0] = color[0]
    rgba[:, :, 1] = color[1]
    rgba[:, :, 2] = color[2]
    rgba[:, :, 3] = np.where(keep, color[3], 0).astype(np.uint8)
    output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, "RGBA").save(output)
    bbox = bbox_from_alpha(rgba[:, :, 3])
    return {
        "bbox": bbox,
        "alpha_coverage": alpha_coverage(rgba[:, :, 3], bbox),
    }


def canonical_skin_color(mask: np.ndarray) -> tuple[int, int, int, int]:
    img = load_rgba(CANONICAL)
    rgba = np.array(img)
    pixels = rgba[mask & (rgba[:, :, 3] > 10)]
    if len(pixels) == 0:
        return (205, 150, 136, 255)
    rgb = np.median(pixels[:, :3], axis=0).astype(np.uint8)
    return (int(rgb[0]), int(rgb[1]), int(rgb[2]), 255)


def layer_entry(
    *,
    experiment_id: str,
    layer_name: str,
    original_part_id: str,
    role: str,
    output_path: Path,
    source_path: Path,
    raw_tag: str,
    draw_order: int,
    stats: dict[str, Any],
    note: str,
    production_candidate: bool = True,
) -> dict[str, Any]:
    return {
        "layer_name": layer_name,
        "original_part_id": original_part_id,
        "raw_tag": raw_tag,
        "role": role,
        "side": None,
        "source_path": str(source_path),
        "output_path": str(output_path),
        "relative_output_path": str(output_path.relative_to(MPS_EXP)) if output_path.is_relative_to(MPS_EXP) else None,
        "canonical_path": str(CANONICAL),
        "canvas_size": CANVAS,
        "bbox": stats["bbox"],
        "alpha_coverage": stats["alpha_coverage"],
        "draw_order": draw_order,
        "depth_median": None,
        "status": "OBSERVED" if stats["bbox"] else "EMPTY",
        "include_in_import_psd": False,
        "production_candidate": production_candidate and bool(stats["bbox"]),
        "depth_path": None,
        "experiment_id": "see-through-mps-compat-002",
        "roi_cleanup_experiment_id": experiment_id,
        "notes": note + " Human O review is required before PSD inclusion.",
    }


def build_mouth_roi() -> list[dict[str, Any]]:
    exp = EXPERIMENTS["mouth"]
    src_path = MPS_EXP / "normalized_layers" / "seethrough_mps__mouth_line.png"
    source = load_rgba(src_path)
    rgba = np.array(source)
    keep_roi = roi_mask([930, 880, 190, 130])
    masks = mouth_masks(rgba)
    outputs = []
    config = {
        "mouth_line": ("mouth_line", 410, "line/edge pixels only"),
        "mouth_inner": ("mouth_inner", 405, "inner mouth fill candidate"),
        "teeth": ("teeth", 415, "bright teeth candidate if present"),
        "tongue": ("tongue", 416, "pink tongue candidate if present"),
    }
    for part_id, keep in masks.items():
        role, draw_order, note = config[part_id]
        output = exp / "layers" / f"seethrough_mps_roi__{part_id}.png"
        stats = write_masked_layer(source, keep & keep_roi, output)
        outputs.append(
            layer_entry(
                experiment_id="mouth-roi-cleanup-001",
                layer_name=f"seethrough_mps_roi__{part_id}",
                original_part_id=part_id,
                role=role,
                output_path=output,
                source_path=src_path,
                raw_tag=f"roi_cleanup:mouth:{part_id}",
                draw_order=draw_order,
                stats=stats,
                note=f"Mouth ROI cleanup: {note}.",
            )
        )
    return outputs


def build_neck_roi() -> list[dict[str, Any]]:
    exp = EXPERIMENTS["neck"]
    src_path = MPS_EXP / "manual_layers" / "seethrough_mps_manual__neck.png"
    if not src_path.exists():
        src_path = MPS_EXP / "normalized_layers" / "seethrough_mps__neck.png"
    source = load_rgba(src_path)
    source_alpha = np.array(source.getchannel("A")) > 10
    keep = source_alpha & roi_mask([840, 900, 360, 330])
    keep &= ~layer_alpha("seethrough_mps__mouth_line", 7)
    keep &= ~layer_alpha("seethrough_mps__face_base", 5)
    keep &= ~layer_alpha("seethrough_mps__clothes", 3)
    stats_neck = write_masked_layer(source, keep, exp / "layers" / "seethrough_mps_roi__neck.png")

    dilated = Image.fromarray(np.where(keep, 255, 0).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(35))
    underpaint = np.array(dilated) > 10
    underpaint &= roi_mask([850, 930, 340, 300])
    color = canonical_skin_color(keep | underpaint)
    stats_underpaint = write_filled_layer(
        underpaint,
        color,
        exp / "layers" / "seethrough_mps_roi__neck_underpaint.png",
    )
    return [
        layer_entry(
            experiment_id="neck-roi-cleanup-001",
            layer_name="seethrough_mps_roi__neck",
            original_part_id="neck",
            role="neck",
            output_path=exp / "layers" / "seethrough_mps_roi__neck.png",
            source_path=src_path,
            raw_tag="roi_cleanup:neck",
            draw_order=200,
            stats=stats_neck,
            note="Neck ROI cleanup: face, mouth, and clothes masks are excluded.",
        ),
        layer_entry(
            experiment_id="neck-roi-cleanup-001",
            layer_name="seethrough_mps_roi__neck_underpaint",
            original_part_id="neck_underpaint",
            role="underpaint",
            output_path=exp / "layers" / "seethrough_mps_roi__neck_underpaint.png",
            source_path=src_path,
            raw_tag="roi_cleanup:neck_underpaint",
            draw_order=190,
            stats=stats_underpaint,
            note="Neck ROI underpaint: slightly expanded skin fill for Cubism deformation margin.",
        ),
    ]


def build_clothes_roi() -> list[dict[str, Any]]:
    exp = EXPERIMENTS["clothes"]
    src_path = MPS_EXP / "normalized_layers" / "seethrough_mps__clothes.png"
    source = load_rgba(src_path)
    rgba = np.array(source)
    keep = (rgba[:, :, 3] > 10) & roi_mask([0, 1000, 2048, 1048])
    keep &= dark_or_gold_mask(rgba)
    keep &= ~skin_mask(rgba)
    keep &= ~layer_alpha("seethrough_mps__face_base", 9)
    keep &= ~layer_alpha("seethrough_mps__neck", 9)
    keep &= ~layer_alpha("seethrough_mps__front_hair", 5)
    stats = write_masked_layer(source, keep, exp / "layers" / "seethrough_mps_roi__clothes.png")
    return [
        layer_entry(
            experiment_id="clothes-roi-cleanup-001",
            layer_name="seethrough_mps_roi__clothes",
            original_part_id="clothes",
            role="clothes",
            output_path=exp / "layers" / "seethrough_mps_roi__clothes.png",
            source_path=src_path,
            raw_tag="roi_cleanup:clothes",
            draw_order=210,
            stats=stats,
            note="Clothes ROI cleanup: skin, face, neck, and front hair are excluded while dark/gold clothing pixels are kept.",
        )
    ]


def write_experiment_report(exp_id: str, layers: list[dict[str, Any]]) -> None:
    exp = ROOT / "experiments" / exp_id
    save_json(
        exp / "reports" / "roi_cleanup_report.json",
        {
            "schema_version": 1,
            "experiment_id": exp_id,
            "generated_at": now(),
            "layers": layers,
            "acceptance": "Review these ROI cleanup candidates in the MPS review app. Only human O can enter the PSD candidate.",
        },
    )
    readme = exp / "README.md"
    if not readme.exists():
        readme.write_text(
            f"# {exp_id}\n\nROI cleanup candidates for See-through MPS review. Human O review is required before PSD inclusion.\n"
        )


def update_mps_manifest(roi_layers: list[dict[str, Any]]) -> None:
    manifest = json.loads(MPS_MANIFEST.read_text())
    existing = [
        layer
        for layer in manifest.get("layers", [])
        if not str(layer.get("layer_name", "")).startswith("seethrough_mps_roi__")
    ]
    existing.extend(roi_layers)
    existing.sort(key=lambda layer: (float(layer.get("draw_order") or 9999), layer.get("layer_name", "")))
    manifest["layers"] = existing
    manifest["updated_at"] = now()
    manifest["roi_cleanup_candidates"] = {
        "generated_at": manifest["updated_at"],
        "count": len(roi_layers),
        "experiments": sorted({layer["roi_cleanup_experiment_id"] for layer in roi_layers}),
    }
    MPS_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    save_json(
        MPS_EXP / "reports" / "roi_cleanup_candidate_report.json",
        {
            "schema_version": 1,
            "experiment_id": "see-through-mps-compat-002",
            "generated_at": manifest["updated_at"],
            "layers": roi_layers,
        },
    )


def main() -> int:
    mouth_layers = build_mouth_roi()
    neck_layers = build_neck_roi()
    clothes_layers = build_clothes_roi()
    write_experiment_report("mouth-roi-cleanup-001", mouth_layers)
    write_experiment_report("neck-roi-cleanup-001", neck_layers)
    write_experiment_report("clothes-roi-cleanup-001", clothes_layers)
    all_layers = mouth_layers + neck_layers + clothes_layers
    update_mps_manifest(all_layers)
    print(
        json.dumps(
            {
                "roi_cleanup_candidates": len(all_layers),
                "experiments": ["mouth-roi-cleanup-001", "neck-roi-cleanup-001", "clothes-roi-cleanup-001"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build cleanup candidates for failed MPS See-through semantic layers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "see-through-mps-compat-002"
MANIFEST_PATH = EXP / "layer_manifest.json"
NORMALIZED_DIR = EXP / "normalized_layers"
CLEANUP_DIR = EXP / "cleanup_layers"
REPORT_PATH = EXP / "reports" / "cleanup_candidate_report.json"
CANVAS = [2048, 2048]

CLEANUP_TARGETS = {
    "face_base": {
        "source": "seethrough_mps__face_base",
        "subtract": [
            ("seethrough_mps__mouth_line", 5),
            ("seethrough_mps__L_eye_white", 3),
            ("seethrough_mps__R_eye_white", 3),
            ("seethrough_mps__L_iris", 3),
            ("seethrough_mps__R_iris", 3),
            ("seethrough_mps__L_upper_lash", 3),
            ("seethrough_mps__R_upper_lash", 3),
            ("seethrough_mps__L_brow", 3),
            ("seethrough_mps__R_brow", 3),
        ],
        "keep_skin": True,
        "roi": [560, 260, 930, 850],
        "draw_order": 315,
        "role": "face",
        "note": "Face cleanup: subtract accepted hair, eye, brow, and mouth masks.",
    },
    "neck": {
        "source": "seethrough_mps__neck",
        "subtract": [
            ("seethrough_mps__mouth_line", 9),
            ("seethrough_mps__face_base", 7),
            ("seethrough_mps__clothes", 5),
            ("seethrough_mps__front_hair", 5),
        ],
        "roi": [820, 780, 430, 470],
        "draw_order": 310,
        "role": "neck",
        "note": "Neck cleanup: keep central neck ROI and subtract mouth, face, clothes, and hair masks.",
    },
    "clothes": {
        "source": "seethrough_mps__clothes",
        "subtract": [
            ("seethrough_mps__face_base", 9),
            ("seethrough_mps__neck", 7),
            ("seethrough_mps__front_hair", 5),
            ("seethrough_mps__back_hair", 3),
            ("seethrough_mps__L_ear_outer", 3),
            ("seethrough_mps__R_ear_outer", 3),
        ],
        "roi": [0, 1000, 2048, 1048],
        "draw_order": 311,
        "role": "clothes",
        "remove_skin": True,
        "keep_dark_or_gold": True,
        "note": "Clothes cleanup: remove skin-colored pixels and subtract face/neck/hair/ear masks.",
    },
    "mouth_line": {
        "source": "seethrough_mps__mouth_line",
        "roi": [930, 880, 190, 130],
        "draw_order": 317,
        "role": "mouth_line",
        "keep_dark_line": True,
        "note": "Mouth cleanup: keep only darker line pixels inside the mouth ROI; remove pale oval fill.",
    },
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_rgba(path: Path) -> Image.Image:
    if not path.exists():
        raise FileNotFoundError(path)
    return Image.open(path).convert("RGBA")


def alpha_mask(layer_name: str, radius: int = 0) -> np.ndarray:
    img = load_rgba(NORMALIZED_DIR / f"{layer_name}.png")
    alpha = img.getchannel("A")
    if radius > 1:
        alpha = alpha.filter(ImageFilter.MaxFilter(radius if radius % 2 else radius + 1))
    return np.array(alpha) > 10


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
    return a & (r > 150) & (g > 125) & (b > 120) & (r >= g - 4) & (g >= b - 6) & ((r - b) > 4)


def dark_or_gold_mask(rgba: np.ndarray) -> np.ndarray:
    r = rgba[:, :, 0].astype(np.int16)
    g = rgba[:, :, 1].astype(np.int16)
    b = rgba[:, :, 2].astype(np.int16)
    a = rgba[:, :, 3] > 10
    luma = (r * 30 + g * 59 + b * 11) // 100
    dark = luma < 105
    gold = (r > 120) & (g > 80) & (b < 95) & (r >= g) & ((r - b) > 45)
    return a & (dark | gold)


def dark_line_mask(rgba: np.ndarray) -> np.ndarray:
    r = rgba[:, :, 0].astype(np.int16)
    g = rgba[:, :, 1].astype(np.int16)
    b = rgba[:, :, 2].astype(np.int16)
    a = rgba[:, :, 3] > 10
    luma = (r * 30 + g * 59 + b * 11) // 100
    red_line = (r > g + 10) & (r > b + 10) & (luma < 190)
    dark_edge = luma < 145
    return a & (red_line | dark_edge)


def build_candidate(part_id: str, spec: dict[str, Any]) -> dict[str, Any]:
    source_name = spec["source"]
    source_path = NORMALIZED_DIR / f"{source_name}.png"
    img = load_rgba(source_path)
    rgba = np.array(img)
    alpha = rgba[:, :, 3].copy()
    keep = alpha > 10
    keep &= roi_mask(spec["roi"])
    if spec.get("keep_skin"):
        keep &= skin_keep_mask(rgba)
    if spec.get("keep_dark_or_gold"):
        keep &= dark_or_gold_mask(rgba)
    if spec.get("keep_dark_line"):
        keep &= dark_line_mask(rgba)
    for subtract_name, radius in spec.get("subtract", []):
        keep &= ~alpha_mask(subtract_name, radius)
    if spec.get("remove_skin"):
        keep &= ~skin_mask(rgba)
    cleaned = rgba.copy()
    cleaned[:, :, 3] = np.where(keep, alpha, 0).astype(np.uint8)
    output = CLEANUP_DIR / f"seethrough_mps_clean__{part_id}.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(cleaned, "RGBA").save(output)
    bbox = bbox_from_alpha(cleaned[:, :, 3])
    return {
        "layer_name": f"seethrough_mps_clean__{part_id}",
        "original_part_id": part_id,
        "raw_tag": f"cleanup:{source_name}",
        "role": spec["role"],
        "side": None,
        "source_path": str(source_path),
        "output_path": str(output),
        "canonical_path": str(EXP / "canonical_front_2048.png") if (EXP / "canonical_front_2048.png").exists() else str(ROOT / "experiments" / "concept-regeneration-001" / "canonical" / "canonical_front_2048.png"),
        "canvas_size": CANVAS,
        "bbox": bbox,
        "alpha_coverage": alpha_coverage(cleaned[:, :, 3], bbox),
        "draw_order": spec["draw_order"],
        "depth_median": None,
        "status": "OBSERVED",
        "include_in_import_psd": False,
        "production_candidate": True,
        "depth_path": None,
        "experiment_id": "see-through-mps-compat-002",
        "cleanup_source_layer": source_name,
        "notes": spec["note"] + " Human O review is required before PSD inclusion.",
    }


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text())
    layers = [
        layer
        for layer in manifest.get("layers", [])
        if not str(layer.get("layer_name", "")).startswith("seethrough_mps_clean__")
    ]
    cleanup_layers = [build_candidate(part_id, spec) for part_id, spec in CLEANUP_TARGETS.items()]
    layers.extend(cleanup_layers)
    manifest["layers"] = sorted(layers, key=lambda layer: (float(layer.get("draw_order") or 9999), layer["layer_name"]))
    manifest["updated_at"] = now()
    manifest["cleanup_candidates"] = {
        "generated_at": manifest["updated_at"],
        "count": len(cleanup_layers),
        "targets": list(CLEANUP_TARGETS),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    report = {
        "schema_version": 1,
        "experiment_id": "see-through-mps-compat-002",
        "generated_at": manifest["updated_at"],
        "targets": cleanup_layers,
        "acceptance": "Review seethrough_mps_clean__* candidates in the MPS review app. O verdict auto-adds them to the PSD candidate.",
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"cleanup_candidates": len(cleanup_layers), "report": str(REPORT_PATH.relative_to(ROOT))}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

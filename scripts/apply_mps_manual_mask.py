#!/usr/bin/env python3
"""Apply a human-painted review mask to a Mac MPS See-through candidate."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT_ID = "see-through-mps-compat-002"
CANVAS = [2048, 2048]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        if default is None:
            raise FileNotFoundError(path)
        return default
    return json.loads(path.read_text())


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


def resolve_source_path(layer: dict[str, Any], experiment_dir: Path) -> Path:
    for key in ("output_path", "relative_output_path", "source_path"):
        value = layer.get(key)
        if not value:
            continue
        path = Path(value)
        if not path.is_absolute():
            path = experiment_dir / path
        if path.exists():
            return path
    raise FileNotFoundError(f"No source image for {layer.get('layer_name')}")


def apply_mask(source_path: Path, mask_path: Path, output_path: Path) -> dict[str, Any]:
    source = Image.open(source_path).convert("RGBA").resize(CANVAS, Image.Resampling.LANCZOS)
    mask = Image.open(mask_path).convert("RGBA").resize(CANVAS, Image.Resampling.LANCZOS)
    rgba = np.array(source)
    mask_alpha = np.array(mask)[:, :, 3].astype(np.float32) / 255.0
    source_alpha = rgba[:, :, 3].astype(np.float32)
    final_alpha = np.clip(source_alpha * mask_alpha, 0, 255).astype(np.uint8)
    rgba[:, :, 3] = final_alpha
    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, "RGBA").save(output_path)
    bbox = bbox_from_alpha(final_alpha)
    return {
        "bbox": bbox,
        "alpha_coverage": alpha_coverage(final_alpha, bbox),
    }


def build_manual_layer(args: argparse.Namespace) -> dict[str, Any]:
    experiment_dir = ROOT / "experiments" / args.experiment_id
    manifest_path = experiment_dir / "layer_manifest.json"
    report_path = experiment_dir / "reports" / "manual_mask_report.json"
    manifest = load_json(manifest_path, {"layers": []})
    layers = manifest.get("layers", [])
    source_layer = next((layer for layer in layers if layer.get("layer_name") == args.part_id), None)
    if not source_layer:
        raise SystemExit(f"FAIL: part_id not found in layer_manifest.json: {args.part_id}")

    original_part_id = source_layer.get("original_part_id") or args.part_id
    manual_part_id = f"seethrough_mps_manual__{original_part_id}"
    mask_path = Path(args.mask_path)
    if not mask_path.is_absolute():
        mask_path = ROOT / mask_path
    source_path = resolve_source_path(source_layer, experiment_dir)
    output_path = experiment_dir / "manual_layers" / f"{manual_part_id}.png"
    stats = apply_mask(source_path, mask_path, output_path)

    canonical_path = source_layer.get("canonical_path") or str(
        experiment_dir / "canonical_front_2048.png"
    )
    if not Path(canonical_path).exists():
        canonical_path = str(ROOT / "experiments" / "concept-regeneration-001" / "canonical" / "canonical_front_2048.png")

    manual_layer = {
        "layer_name": manual_part_id,
        "original_part_id": original_part_id,
        "raw_tag": f"manual_mask:{args.part_id}",
        "role": source_layer.get("role"),
        "side": source_layer.get("side"),
        "source_path": str(source_path),
        "output_path": str(output_path),
        "relative_output_path": str(output_path.relative_to(experiment_dir)),
        "canonical_path": canonical_path,
        "canvas_size": source_layer.get("canvas_size") or CANVAS,
        "bbox": stats["bbox"],
        "alpha_coverage": stats["alpha_coverage"],
        "draw_order": source_layer.get("draw_order"),
        "depth_median": source_layer.get("depth_median"),
        "status": "OBSERVED",
        "include_in_import_psd": False,
        "production_candidate": bool(source_layer.get("production_candidate", True)),
        "depth_path": source_layer.get("depth_path"),
        "experiment_id": args.experiment_id,
        "manual_mask_path": str(mask_path),
        "manual_source_layer": args.part_id,
        "notes": "Human-painted review-app mask candidate. Human O review is required before PSD inclusion.",
    }

    next_layers = [layer for layer in layers if layer.get("layer_name") != manual_part_id]
    next_layers.append(manual_layer)
    next_layers.sort(key=lambda layer: (float(layer.get("draw_order") or 9999), layer.get("layer_name", "")))
    manifest["layers"] = next_layers
    manifest["updated_at"] = now()
    manifest["manual_mask_candidates"] = {
        "updated_at": manifest["updated_at"],
        "latest_part_id": manual_part_id,
    }
    save_json(manifest_path, manifest)

    report = load_json(
        report_path,
        {
            "schema_version": 1,
            "experiment_id": args.experiment_id,
            "items": [],
        },
    )
    report["updated_at"] = manifest["updated_at"]
    report.setdefault("items", []).append(
        {
            "generated_at": manifest["updated_at"],
            "source_part_id": args.part_id,
            "manual_part_id": manual_part_id,
            "mask_path": str(mask_path.relative_to(ROOT)),
            "output_path": str(output_path.relative_to(ROOT)),
            "bbox": stats["bbox"],
            "alpha_coverage": stats["alpha_coverage"],
        }
    )
    save_json(report_path, report)
    return {
        "ok": True,
        "experiment_id": args.experiment_id,
        "source_part_id": args.part_id,
        "manual_part_id": manual_part_id,
        "mask_path": str(mask_path.relative_to(ROOT)),
        "output_path": str(output_path.relative_to(ROOT)),
        "bbox": stats["bbox"],
        "alpha_coverage": stats["alpha_coverage"],
        "report_path": str(report_path.relative_to(ROOT)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply a review-app painted mask to an MPS candidate.")
    parser.add_argument("--experiment-id", default=DEFAULT_EXPERIMENT_ID)
    parser.add_argument("--part-id", required=True)
    parser.add_argument("--mask-path", required=True)
    args = parser.parse_args()
    print(json.dumps(build_manual_layer(args), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

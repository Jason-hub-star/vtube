#!/usr/bin/env python3
"""Prepare Mini Cubism dedicated model v1 canonical and See-through inputs."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = ROOT / "experiments/mini-cubism-dedicated-model-v1-001"
SOURCE_COMFY_EXP = ROOT / "experiments/see-through-layer-decomp-001"

MATRIX_TEMPLATE = [
    {
        "case_id": "mps_512_safe",
        "input_image": "canonical_front_mps_512.png",
        "resolution": 512,
        "steps": 8,
        "depth_resolution": 384,
        "env": {
            "PYTORCH_ENABLE_MPS_FALLBACK": "1",
            "PYTORCH_MPS_LOW_WATERMARK_RATIO": "0.85",
            "PYTORCH_MPS_HIGH_WATERMARK_RATIO": "1.20",
        },
        "status": "READY_TO_RUN",
        "risk": "lowest memory; first dedicated decomposition gate",
    },
    {
        "case_id": "mps_640_safe",
        "input_image": "canonical_front_mps_640.png",
        "resolution": 640,
        "steps": 12,
        "depth_resolution": 512,
        "env": {
            "PYTORCH_ENABLE_MPS_FALLBACK": "1",
            "PYTORCH_MPS_LOW_WATERMARK_RATIO": "0.90",
            "PYTORCH_MPS_HIGH_WATERMARK_RATIO": "1.30",
        },
        "status": "READY_TO_RUN_AFTER_512",
        "risk": "practical review candidate if 512 creates useful layers",
    },
    {
        "case_id": "mps_768_safe",
        "input_image": "canonical_front_mps_768.png",
        "resolution": 768,
        "steps": 16,
        "depth_resolution": 512,
        "env": {
            "PYTORCH_ENABLE_MPS_FALLBACK": "1",
            "PYTORCH_MPS_LOW_WATERMARK_RATIO": "0.95",
            "PYTORCH_MPS_HIGH_WATERMARK_RATIO": "1.40",
        },
        "status": "MANUAL_ONLY_AFTER_512_640",
        "risk": "quality probe only after 512/640 produce useful layers",
    },
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def square_fit_to_2048(source: Path, output: Path) -> dict[str, Any]:
    image = Image.open(source).convert("RGBA")
    fitted = ImageOps.contain(image, (2048, 2048), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (2048, 2048), (255, 255, 255, 255))
    offset = ((2048 - fitted.width) // 2, (2048 - fitted.height) // 2)
    canvas.alpha_composite(fitted, offset)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output)
    return {
        "source_size": list(image.size),
        "canonical_size": [2048, 2048],
        "fit_size": [fitted.width, fitted.height],
        "offset": list(offset),
        "background": "white",
    }


def make_mps_inputs(canonical: Path, input_dir: Path) -> list[dict[str, Any]]:
    input_dir.mkdir(parents=True, exist_ok=True)
    source = Image.open(canonical).convert("RGB")
    outputs = []
    for size in [512, 640, 768]:
        output = input_dir / f"canonical_front_mps_{size}.png"
        source.resize((size, size), Image.Resampling.LANCZOS).save(output)
        outputs.append(
            {
                "size": [size, size],
                "path": str(output.relative_to(ROOT)),
                "source": str(canonical.relative_to(ROOT)),
            }
        )
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare dedicated Mini Cubism canonical and layer split inputs.")
    parser.add_argument("--source-image", required=True)
    parser.add_argument("--experiment", default=str(DEFAULT_EXPERIMENT))
    args = parser.parse_args()

    exp = Path(args.experiment).resolve()
    source = repo_path(args.source_image)
    if not source.exists():
        raise FileNotFoundError(source)

    raw_dir = exp / "raw"
    canonical_dir = exp / "canonical"
    input_dir = exp / "input"
    reports = exp / "reports"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_copy = raw_dir / "imagegen_source.png"
    shutil.copy2(source, raw_copy)

    canonical = canonical_dir / "canonical_front_2048.png"
    canonical_fit = square_fit_to_2048(raw_copy, canonical)
    mps_inputs = make_mps_inputs(canonical, input_dir)

    matrix = {
        "schema_version": 1,
        "experiment_id": exp.name,
        "character_id": "mini_cubism_dedicated_v1",
        "filename_prefix_base": "mini_cubism_dedicated_v1",
        "generated_at": now(),
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "source_comfy_experiment": str(SOURCE_COMFY_EXP.relative_to(ROOT)),
        "source_image": str(raw_copy.relative_to(ROOT)),
        "canonical_image": str(canonical.relative_to(ROOT)),
        "canonical_report": canonical_fit,
        "input_outputs": mps_inputs,
        "matrix": MATRIX_TEMPLATE,
        "gates": {
            "canonical_success": "front-facing, not cropped, no text, eyes/mouth visible, separable hair/accessories",
            "layer_split_success": "512 or 640 creates *_layers.json and normalized layer_manifest.json",
            "mapping_success_floor": ">=60 mapped parts, >=18 hair, >=16 eye, >=8 mouth, >=12 physics targets",
            "human_review_rule": "See-through output is candidate evidence only until review app verdicts exist.",
        },
        "status": "READY_FOR_LAYER_DECOMPOSITION",
    }
    save_json(exp / "mps_run_matrix.json", matrix)
    save_json(reports / "canonical_generation_report.json", matrix)
    print(
        json.dumps(
            {
                "ok": True,
                "experiment": str(exp.relative_to(ROOT)),
                "canonical": str(canonical.relative_to(ROOT)),
                "mps_inputs": len(mps_inputs),
                "status": matrix["status"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

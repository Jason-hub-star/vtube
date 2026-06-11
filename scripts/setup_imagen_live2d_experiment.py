#!/usr/bin/env python3
"""Prepare an Imagen-generated Live2D front-canonical experiment."""

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
DEFAULT_EXPERIMENT_ID = "imagen-live2d-001"
SOURCE_COMFY_EXP = ROOT / "experiments" / "see-through-layer-decomp-001"


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
        "risk": "lowest memory; first decomposition gate",
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
        "status": "READY_TO_RUN",
        "risk": "practical review candidate if 512 succeeds",
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
        "status": "READY_TO_RUN",
        "risk": "quality probe only after 512/640 produce useful layers",
    },
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def square_fit_to_2048(source: Path, output: Path) -> dict[str, Any]:
    img = Image.open(source).convert("RGBA")
    src_size = img.size
    fitted = ImageOps.contain(img, (2048, 2048), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (2048, 2048), (255, 255, 255, 255))
    offset = ((2048 - fitted.width) // 2, (2048 - fitted.height) // 2)
    canvas.alpha_composite(fitted, offset)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output)
    return {
        "source_size": list(src_size),
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
        out = input_dir / f"canonical_front_mps_{size}.png"
        source.resize((size, size), Image.Resampling.LANCZOS).save(out)
        outputs.append(
            {
                "size": [size, size],
                "path": str(out.relative_to(ROOT)),
                "source": str(canonical.relative_to(ROOT)),
            }
        )
    return outputs


def write_readme(exp: Path, source: Path) -> None:
    (exp / "README.md").write_text(
        f"""# Imagen Live2D 001

Imagen으로 생성한 새 정면 캐릭터를 Live2D/Cubism production material pack까지 밀어보기 위한 실험이다.

## Source

```text
{source}
```

## Canonical

```text
canonical/canonical_front_2048.png
input/canonical_front_mps_512.png
input/canonical_front_mps_640.png
input/canonical_front_mps_768.png
```

## Pipeline

```bash
python3 scripts/run_mps_compat_matrix.py --experiment-id imagen-live2d-001 --case mps_512_safe
python3 scripts/run_mps_compat_matrix.py --experiment-id imagen-live2d-001 --case mps_640_safe
python3 scripts/build_mps_candidate_review_sheet.py --experiment-id imagen-live2d-001
python3 scripts/build_review_manifest.py --experiment-id imagen-live2d-001
python3 scripts/validate_review_app.py
```

Only `O` production candidates may enter `import_ready_candidate.psd`.
Cubism Editor actual import smoke is still required before promotion to `import_ready.psd`.
""",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare Imagen Live2D experiment inputs")
    parser.add_argument("--source-image", required=True)
    parser.add_argument("--experiment-id", default=DEFAULT_EXPERIMENT_ID)
    args = parser.parse_args()

    exp = ROOT / "experiments" / args.experiment_id
    source = repo_path(args.source_image)
    if not source.exists():
        raise FileNotFoundError(source)

    raw_dir = exp / "raw"
    canonical_dir = exp / "canonical"
    input_dir = exp / "input"
    report_dir = exp / "reports"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_copy = raw_dir / "imagen_source.png"
    shutil.copy2(source, raw_copy)

    canonical = canonical_dir / "canonical_front_2048.png"
    canonical_report = square_fit_to_2048(raw_copy, canonical)
    mps_inputs = make_mps_inputs(canonical, input_dir)

    matrix = {
        "schema_version": 1,
        "experiment_id": args.experiment_id,
        "character_id": "imagen_live2d",
        "filename_prefix_base": "imagen_live2d",
        "generated_at": now(),
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "source_comfy_experiment": str(SOURCE_COMFY_EXP.relative_to(ROOT)),
        "source_image": str(raw_copy.relative_to(ROOT)),
        "canonical_image": str(canonical.relative_to(ROOT)),
        "canonical_report": canonical_report,
        "input_outputs": mps_inputs,
        "matrix": MATRIX_TEMPLATE,
        "gates": {
            "minimum_success": "512 or 640 creates *_layers.json",
            "practical_success": "review app marks enough hair/face/eye/mouth candidates as O or REVISE",
            "psd_success": "O-only import_ready_candidate.psd imports in Cubism without flattening",
            "rig_success": "Cubism project has ArtMesh, Deformer hierarchy, and MVP eye/mouth/head parameter keyforms",
        },
    }
    save_json(exp / "mps_run_matrix.json", matrix)
    save_json(report_dir / "canonical_generation_report.json", matrix)
    write_readme(exp, raw_copy.relative_to(ROOT))

    print(
        json.dumps(
            {
                "experiment": str(exp.relative_to(ROOT)),
                "source": str(raw_copy.relative_to(ROOT)),
                "canonical": str(canonical.relative_to(ROOT)),
                "mps_inputs": len(mps_inputs),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

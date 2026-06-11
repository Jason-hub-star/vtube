#!/usr/bin/env python3
"""Prepare the Apple Silicon MPS compatibility experiment."""

from __future__ import annotations

import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE_EXP = ROOT / "experiments" / "see-through-layer-decomp-001"
EXP = ROOT / "experiments" / "see-through-mps-compat-002"
INPUT_DIR = EXP / "input"
REPORT_DIR = EXP / "reports"
MATRIX_PATH = EXP / "mps_run_matrix.json"
README_PATH = EXP / "README.md"
SETUP_REPORT = REPORT_DIR / "setup_report.json"
SOURCE_IMAGE = SOURCE_EXP / "input" / "canonical_front_1280.png"


MATRIX = [
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
        "risk": "lowest quality, lowest memory; minimum success gate is *_layers.json",
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
        "risk": "target practical smoke if 512 produces layers",
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
        "risk": "quality probe; run only after 512 or 640 completes",
    },
    {
        "case_id": "mps_512_high_watermark_manual",
        "input_image": "canonical_front_mps_512.png",
        "resolution": 512,
        "steps": 8,
        "depth_resolution": 384,
        "env": {
            "PYTORCH_ENABLE_MPS_FALLBACK": "1",
            "PYTORCH_MPS_LOW_WATERMARK_RATIO": "0.00",
            "PYTORCH_MPS_HIGH_WATERMARK_RATIO": "0.00",
        },
        "status": "MANUAL_ONLY",
        "risk": "dangerous: disables allocator high watermark and may destabilize the Mac",
    },
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def resize_inputs() -> list[dict[str, Any]]:
    if not SOURCE_IMAGE.exists():
        raise FileNotFoundError(f"Missing source image: {SOURCE_IMAGE}")
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    source = Image.open(SOURCE_IMAGE).convert("RGBA")
    outputs = []
    for size in [512, 640, 768]:
        out = INPUT_DIR / f"canonical_front_mps_{size}.png"
        source.resize((size, size), Image.Resampling.LANCZOS).save(out)
        outputs.append(
            {
                "size": [size, size],
                "path": str(out.relative_to(ROOT)),
                "source": str(SOURCE_IMAGE.relative_to(ROOT)),
            }
        )
    return outputs


def write_readme() -> None:
    README_PATH.write_text(
        """# See-through MPS Compatibility 002

목표는 Apple Silicon에서 See-through 계열 decomposition이 production 품질로 충분한지 보는 것이 아니라,
저해상도 안전 매트릭스에서 `*_layers.json`이 실제로 생성되는지 확인하는 것이다.

## 입력

원본 기준:

```text
experiments/see-through-layer-decomp-001/input/canonical_front_1280.png
```

working copy:

```text
input/canonical_front_mps_512.png
input/canonical_front_mps_640.png
input/canonical_front_mps_768.png
```

## 실행

ComfyUI-See-through 서버를 먼저 실행한 뒤:

```bash
python3 scripts/run_mps_compat_matrix.py --case mps_512_safe
```

512가 `*_layers.json`을 만들면 640, 그 다음 768을 실행한다.

```bash
python3 scripts/run_mps_compat_matrix.py --case mps_640_safe
python3 scripts/run_mps_compat_matrix.py --case mps_768_safe
```

## 판정

- 최소 성공: 512 또는 640에서 `*_layers.json` 생성
- 실용 성공: review app에서 hair/face/eye/mouth 계열 5개 이상이 `O` 또는 `REVISE`
- 실패: 512에서도 출력 없음, 또는 전부 semantic contamination이 심함

`mps_512_high_watermark_manual`은 마지막 수동 실험이다. 기본 실행에서 제외한다.
""",
        encoding="utf-8",
    )


def main() -> int:
    outputs = resize_inputs()
    write_readme()
    matrix = {
        "schema_version": 1,
        "experiment_id": "see-through-mps-compat-002",
        "generated_at": now(),
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "source_experiment": str(SOURCE_EXP.relative_to(ROOT)),
        "input_outputs": outputs,
        "matrix": MATRIX,
        "gates": {
            "minimum_success": "512 or 640 creates *_layers.json",
            "practical_success": "5 or more hair/face/eye/mouth candidates receive O or REVISE in review app",
            "failure": "512 creates no layer output or all candidates are semantically contaminated",
        },
    }
    save_json(MATRIX_PATH, matrix)
    save_json(SETUP_REPORT, matrix)
    print(json.dumps({"experiment": str(EXP.relative_to(ROOT)), "inputs": len(outputs), "cases": len(MATRIX)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

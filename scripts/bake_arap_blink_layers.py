#!/usr/bin/env python3
"""ARAP 깜빡임 프레임을 리그용 inbetween 레이어로 굽는다 (런타임 무수정 통합).

- 원본 중립 조립에 커튼 워프(t=0.25/0.5/0.75/1.0)를 적용해 눈 영역 패치를
  풀캔버스 레이어(eye_{L,R}_arap_{025..100}.png)로 저장한다. 픽셀 전부 원본.
- 워프 수치는 arap_blink_config.json에 기록 — **나중에 이 파일을 고치고
  이 스크립트만 재실행하면 깜빡임 모양이 바뀐다** (주인님 수정 보장).

사용: python3 scripts/bake_arap_blink_layers.py [--config <json>] \
        --out-dir experiments/autorig-template-001/arap_blink_layers
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, load_json, now_iso, rel, write_json  # noqa: E402
from run_arap_blink_experiment import curtain_warp, eye_bbox_from_layer  # noqa: E402

DEFAULT_CONFIG = {
    "assembly": "experiments/autorig-template-001/reports/full_assembly/hybrid_true_origeyes.png",
    "eye_white_L": "experiments/autorig-template-001/seethrough_true_reskinned/L_eye_white.png",
    "eye_white_R": "experiments/autorig-template-001/seethrough_true_reskinned/R_eye_white.png",
    "t_steps": [0.25, 0.5, 0.75, 1.0],
    "patch_pad": 26,
    "skin_band": 0.9,
    "lower_rise": 0.2,
    "lower_band": 0.35,
    # EXPR-002 눈웃음 곡선 (주인님 선택 A — smile_candidates 리포트)
    "smile_lid_center": 0.34,
    "smile_low_center": 0.42,
    "notes": "워프 형태(아치 깊이 등)는 run_arap_blink_experiment.curtain_warp의 0.45/0.28/0.55 상수 — 조정 후 본 스크립트 재실행. lower_rise=아랫꺼풀 상승 비율(EYE-NATURAL-001, 0이면 구형 셔터식)",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    config = dict(DEFAULT_CONFIG)
    if args.config and args.config.exists():
        config.update(load_json(args.config))

    out = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    base = np.asarray(Image.open(ROOT / config["assembly"]).convert("RGBA"))
    pad = int(config["patch_pad"])
    baked = []
    for side in ("L", "R"):
        bbox = eye_bbox_from_layer(ROOT / config[f"eye_white_{side}"])
        x0, lash_top, x1, y1 = bbox
        h = y1 - lash_top
        # 패치 크롭: 위쪽 피부 밴드 + 아래 피부 밴드(아랫꺼풀 상승 영향권) 포함
        py0 = max(0, lash_top - round(h * float(config["skin_band"])) - pad)
        py1 = min(base.shape[0], y1 + round(h * float(config.get("lower_band", 0.35))) + pad)
        px0 = max(0, x0 - pad)
        px1 = min(base.shape[1], x1 + pad)
        # t=0 항등 패치: 정점 키폼 메시(EYE-NATURAL-002)의 텍스처 — 중립 픽셀 그대로
        neutral = np.zeros_like(base)
        neutral[py0:py1, px0:px1] = base[py0:py1, px0:px1]
        name0 = f"eye_{side}_arap_000.png"
        Image.fromarray(neutral, "RGBA").save(out / name0)
        baked.append(name0)
        for t in config["t_steps"]:
            warped = curtain_warp(
                base, bbox, float(t),
                skin_band=float(config["skin_band"]),
                lower_rise=float(config.get("lower_rise", 0.2)),
                lower_band=float(config.get("lower_band", 0.35)),
            )
            canvas = np.zeros_like(base)
            canvas[py0:py1, px0:px1] = warped[py0:py1, px0:px1]
            name = f"eye_{side}_arap_{int(round(t * 100)):03d}.png"
            Image.fromarray(canvas, "RGBA").save(out / name)
            baked.append(name)

    config["generated_at"] = now_iso()
    config["baked"] = baked
    write_json(out / "arap_blink_config.json", config)
    print(f"baked {len(baked)} layers -> {rel(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

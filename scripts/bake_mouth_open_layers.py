#!/usr/bin/env python3
"""입 벌림 워프 프레임을 리그용 레이어로 굽는다 (깜빡임 베이크와 동일 구조).

원본 중립 조립에 mouth_warp(t=0.25/0.5/0.75/1.0)를 적용해 입 영역 패치를
풀캔버스 레이어(mouth_warp_{025..100}.png)로 저장. 입술 픽셀 = 원본 워프,
내부 = 진짜 마스터 참조 동일세션 시트의 interior (입만의 예외).
수치는 config(json) 수정 후 본 스크립트 재실행으로 언제든 변경.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, load_json, now_iso, rel, write_json  # noqa: E402
from run_mouth_open_experiment import DEFAULT_CONFIG, bbox_of, mouth_warp  # noqa: E402

T_STEPS = [0.25, 0.5, 0.75, 1.0]


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
    internals_img = None
    for path in config["internals"]:
        layer = Image.open(ROOT / path).convert("RGBA")
        internals_img = layer if internals_img is None else Image.alpha_composite(internals_img, layer)
    internals = np.asarray(internals_img)
    mouth_bbox = bbox_of(ROOT / config["mouth_line"])
    mx0, my0, mx1, my1 = mouth_bbox
    mouth_w = mx1 - mx0
    pad = 24
    px0, px1 = max(0, mx0 - pad), min(base.shape[1], mx1 + pad)
    py0 = max(0, my0 - pad)
    py1 = min(base.shape[0], int(my1 + mouth_w * float(config["chin_band_ratio"])) + pad)

    baked = []
    for t in T_STEPS:
        warped = mouth_warp(base, internals, mouth_bbox, config, float(t))
        canvas = np.zeros_like(base)
        canvas[py0:py1, px0:px1] = warped[py0:py1, px0:px1]
        name = f"mouth_warp_{int(round(t * 100)):03d}.png"
        Image.fromarray(canvas, "RGBA").save(out / name)
        baked.append(name)

    config["generated_at"] = now_iso()
    config["baked"] = baked
    write_json(out / "mouth_open_bake_config.json", config)
    print(f"baked {len(baked)} layers -> {rel(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

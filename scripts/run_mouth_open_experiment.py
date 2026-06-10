#!/usr/bin/env python3
"""MOUTH-EXP-001: 원본 픽셀 워프로 입 벌림을 단계화한다 (깜빡임 공식의 재적용).

공식 모델 실측 (hiyori/miara MouthOpenY min/max):
  - 윗입술 거의 고정, 아랫입술+턱이 하강 (행정 ≈ 입 폭의 ~40%)
  - 입꼬리 양끝 고정, 열린 모양은 아래로 둥근 타원
방식: 입라인 아래 밴드를 컬럼별로 아래로 밀어 압축(역-커튼), 벌어진 틈은
  생성 내부(mouth_inner/teeth/tongue — 입만의 예외)를 열림량에 비례해 노출.
설정: mouth_open_config.json — 수치 수정 후 재실행하면 모양이 바뀐다.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, load_json, now_iso, rel, write_json  # noqa: E402

DEFAULT_CONFIG = {
    "assembly": "experiments/autorig-template-001/reports/full_assembly/hybrid_true_origeyes.png",
    "mouth_line": "experiments/autorig-template-001/seethrough_true_reskinned/mouth_line.png",
    "internals": [
        "experiments/autorig-template-001/rig_v0_project/parts/mouth_inner.png",
        "experiments/autorig-template-001/rig_v0_project/parts/mouth_teeth.png",
        "experiments/autorig-template-001/rig_v0_project/parts/mouth_tongue.png",
    ],
    "t_steps": [0.0, 0.25, 0.5, 0.75, 1.0],
    "max_gap_ratio": 0.40,
    "chin_band_ratio": 0.95,
    "corner_pin": 0.92,
    "upper_share": 0.25,   # 벌어짐 중 윗입술 상승 비중
    "upper_band_ratio": 0.55,  # 윗입술 변형이 감쇠하는 범위 (입 폭 대비)
    "ease_exp": 0.55,      # 아랫밴드 압축 집중도 (작을수록 입술 밑에 접힘 집중, 턱끝 고정)
}


def bbox_of(path: Path) -> tuple[int, int, int, int]:
    alpha = np.asarray(Image.open(path).convert("RGBA"))[..., 3]
    ys, xs = np.where(alpha > 8)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def mouth_warp(base: np.ndarray, internals: np.ndarray, mouth_bbox, config, t: float) -> np.ndarray:
    mx0, my0, mx1, my1 = mouth_bbox
    mouth_w = mx1 - mx0
    lip_y = (my0 + my1) / 2
    max_gap = mouth_w * float(config["max_gap_ratio"])
    chin_end = int(my1 + mouth_w * float(config["chin_band_ratio"]))
    cx = (mx0 + mx1) / 2
    half = max(mouth_w / 2, 1e-6)
    pin = float(config["corner_pin"])

    # 내부 합성의 세로 범위 (틈에 비례 매핑)
    in_alpha = internals[..., 3]
    iys, ixs = np.where(in_alpha > 8)
    iy0, iy1 = int(iys.min()), int(iys.max()) + 1

    upper_share = float(config.get("upper_share", 0.25))
    upper_band = mouth_w * float(config.get("upper_band_ratio", 0.55))
    ease_exp = float(config.get("ease_exp", 0.55))

    out = base.copy()
    for x in range(mx0, mx1):
        ratio = (x - cx) / half
        arc = float(np.sqrt(max(0.0, 1.0 - min(1.0, ratio * ratio * pin))))
        gap = t * max_gap * arc
        if gap < 0.5:
            continue
        up = gap * upper_share          # 윗입술 상승량
        down = gap - up                 # 아랫입술 하강량
        gap_top = lip_y - up
        gap_bottom = lip_y + down
        band_top = int(max(0, lip_y - upper_band))
        ys_out = np.arange(band_top, chin_end, dtype=np.float64)
        column = base[:, x, :].astype(np.float64)
        new_col = column[np.clip(ys_out.astype(int), 0, base.shape[0] - 1)].copy()

        in_gap = (ys_out >= gap_top) & (ys_out < gap_bottom)
        above = ys_out < gap_top
        below = ys_out >= gap_bottom
        # 윗밴드: [band_top, lip_y] → [band_top, gap_top] 으로 부드럽게 스트레치 (윗입술 상승, 코쪽 감쇠)
        denom_u = max(gap_top - band_top, 1e-6)
        src_above = band_top + (ys_out[above] - band_top) * ((lip_y - band_top) / denom_u)
        # 아랫밴드: 감쇠 변위장 — 입술 밑은 down만큼, 턱끝(chin_end)은 0 (ease로 입술 밑에 압축 집중)
        s = np.clip((ys_out[below] - gap_bottom) / max(chin_end - gap_bottom, 1e-6), 0, 1)
        src_below = lip_y + np.power(s, ease_exp) * (chin_end - lip_y)
        for sel, src in ((above, src_above), (below, src_below)):
            idx = np.clip(src, 0, base.shape[0] - 1)
            lo = np.floor(idx).astype(int)
            hi = np.minimum(lo + 1, base.shape[0] - 1)
            frac = (idx - lo)[:, None]
            new_col[sel] = column[lo] * (1 - frac) + column[hi] * frac
        # 틈: 내부 마스크 노출 (비율 보존)
        src_in = np.clip(iy0 + (ys_out[in_gap] - gap_top), 0, internals.shape[0] - 1)
        lo_i = np.floor(src_in).astype(int)
        sample = internals[lo_i, x, :].astype(np.float64)
        a = (sample[:, 3:4] / 255.0)
        dark = np.array([70.0, 28.0, 32.0, 255.0])
        new_col[in_gap] = sample * a + dark * (1 - a)
        out[band_top:chin_end, x, :] = new_col.astype(base.dtype)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "experiments/autorig-template-001/reports/mouth_open_exp")
    args = parser.parse_args()
    config = dict(DEFAULT_CONFIG)
    if args.config and args.config.exists():
        config.update(load_json(args.config))
    args.out_dir.mkdir(parents=True, exist_ok=True)

    base = np.asarray(Image.open(ROOT / config["assembly"]).convert("RGBA"))
    internals_img = None
    for path in config["internals"]:
        layer = Image.open(ROOT / path).convert("RGBA")
        internals_img = layer if internals_img is None else Image.alpha_composite(internals_img, layer)
    internals = np.asarray(internals_img)
    mouth_bbox = bbox_of(ROOT / config["mouth_line"])

    mx0, my0, mx1, my1 = mouth_bbox
    fw = (mx0 - 160, my0 - 220, mx1 + 160, my1 + 260)
    frames = []
    for t in config["t_steps"]:
        warped = mouth_warp(base, internals, mouth_bbox, config, float(t))
        frame = Image.fromarray(warped, "RGBA")
        frame.save(args.out_dir / f"mouth_t{int(t*100):03d}.png")
        frames.append(frame.crop(fw))
    fwid, fh = frames[0].size
    strip = Image.new("RGB", (fwid * len(frames) + 8 * (len(frames) - 1), fh), (255, 255, 255))
    for i, frame in enumerate(frames):
        strip.paste(frame.convert("RGB"), (i * (fwid + 8), 0))
    strip_path = args.out_dir / "mouth_strip.png"
    strip.save(strip_path)

    config["generated_at"] = now_iso()
    write_json(args.out_dir / "mouth_open_config.json", config)
    print(f"strip: {rel(strip_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

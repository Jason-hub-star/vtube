#!/usr/bin/env python3
"""ARAP-EXP-001: 원본 픽셀만으로 눈꺼풀 감김(깜빡임)을 만드는 메시 워프 실험.

가설: 눈 영역에 "커튼 워프"(윗눈꺼풀 피부가 곡선을 그리며 내려와 눈을 덮는
컬럼별 세로 리매핑)를 적용하면, 생성 픽셀 없이(스타일 드리프트 0) 자연스러운
깜빡임 중간 프레임을 얻는다.

방식: 각 컬럼 x에서 감김량 t_x = t·sqrt(1-((x-cx)/(w/2))²) (타원 곡선 눈꺼풀).
  위쪽 피부 밴드 [y0, lash_top] → [y0, L(t_x)] 로 늘리고 (눈꺼풀 하강),
  눈 밴드 [lash_top, y1] → [L(t_x), y1] 로 압축한다.
픽셀은 전부 중립 조립본(원본)에서만 온다.

산출: t=0/0.25/0.5/0.75/1.0 스트립 + 현행 크로스페이드 비교
      → experiments/autorig-template-001/reports/arap_blink_exp/
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, now_iso, rel, write_json  # noqa: E402

T_STEPS = [0.0, 0.25, 0.5, 0.75, 1.0]


def eye_bbox_from_layer(path: Path) -> tuple[int, int, int, int]:
    alpha = np.asarray(Image.open(path).convert("RGBA"))[..., 3]
    ys, xs = np.where(alpha > 8)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def curtain_warp(
    image: np.ndarray,
    bbox: tuple[int, int, int, int],
    t: float,
    skin_band: float = 0.9,
    lower_rise: float = 0.2,
    lower_band: float = 0.35,
) -> np.ndarray:
    """아몬드형 눈에 맞춘 커튼 워프 (공식 모델 관찰 반영, EYE-NATURAL-001 v3).

    - 윗눈꺼풀이 주도 (top-down), 눈꼬리 양끝은 고정점
    - 닫힌 선은 바닥이 아니라 눈 높이 ~63% 지점의 "아래로 볼록한 아치"
    - 컬럼별로 윗곡선 up_x → 닫힘 아치 closed_x 로 보간
    - 아랫꺼풀도 컬럼 높이의 lower_rise 비율만큼 상승 (공식 패턴: 위 ~80% + 아래 ~20%가
      중심 아래에서 만남 — koharu_haruto의 下まつげ 독립 파트 구조 등가).
      눈 아래 피부 밴드 [low_x, yb]가 따라 늘어나 아랫속눈썹이 함께 올라온다.
      lower_rise=0이면 기존(v2, 아랫꺼풀 고정) 동작과 동일.
    """
    x0, lash_top, x1, y1 = bbox
    h = y1 - lash_top
    y0 = max(0, lash_top - round(h * skin_band))
    yb = min(image.shape[0], y1 + round(h * lower_band))  # 아래 피부 밴드 끝 (변위 0 고정점)
    out = image.copy()
    cx = (x0 + x1) / 2
    half = max((x1 - x0) / 2, 1e-6)
    for x in range(x0, x1):
        ratio = (x - cx) / half
        arc = float(np.sqrt(max(0.0, 1.0 - ratio * ratio)))  # 중앙 1, 눈꼬리 0
        up_x = lash_top + h * 0.45 * (1.0 - arc)             # 윗곡선 (중앙=top, 꼬리=45%)
        low_x = lash_top + h * (0.45 + 0.55 * arc)           # 아랫곡선 (중앙=바닥, 꼬리=45%)
        closed_x = lash_top + h * (0.45 + 0.28 * arc)        # 닫힘 아치 (중앙=73%, 꼬리=45%)
        lid = up_x + t * (closed_x - up_x)
        # 아랫꺼풀: 컬럼 눈높이(low_x-up_x)의 lower_rise 비율만큼 상승 — 항상 closed_x 아래에 머묾
        lid_low = low_x - t * lower_rise * (low_x - up_x)
        if lid - up_x < 0.5 and low_x - lid_low < 0.5:
            continue
        ys_out = np.arange(y0, yb, dtype=np.float64)
        src = np.empty_like(ys_out)
        upper = ys_out <= lid
        middle = (~upper) & (ys_out <= lid_low)
        below = ys_out > lid_low
        denom_u = max(lid - y0, 1e-6)
        src[upper] = y0 + (ys_out[upper] - y0) * ((up_x - y0) / denom_u)
        denom_m = max(lid_low - lid, 1e-6)
        src[middle] = up_x + (ys_out[middle] - lid) * ((low_x - up_x) / denom_m)
        denom_b = max(yb - lid_low, 1e-6)
        src[below] = low_x + (ys_out[below] - lid_low) * ((yb - low_x) / denom_b)
        src_idx = np.clip(src, 0, image.shape[0] - 1)
        lo = np.floor(src_idx).astype(int)
        hi = np.minimum(lo + 1, image.shape[0] - 1)
        frac = (src_idx - lo)[:, None]
        column = image[:, x, :].astype(np.float64)
        out[y0:yb, x, :] = (column[lo] * (1 - frac) + column[hi] * frac).astype(image.dtype)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assembly", type=Path, default=ROOT / "experiments/autorig-template-001/reports/full_assembly/hybrid_true_origeyes.png")
    parser.add_argument("--eye-white-l", type=Path, default=ROOT / "experiments/autorig-template-001/seethrough_true_reskinned/L_eye_white.png")
    parser.add_argument("--eye-white-r", type=Path, default=ROOT / "experiments/autorig-template-001/seethrough_true_reskinned/R_eye_white.png")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "experiments/autorig-template-001/reports/arap_blink_exp")
    args = parser.parse_args()

    base = np.asarray(Image.open(args.assembly).convert("RGBA"))
    bboxes = [eye_bbox_from_layer(args.eye_white_l), eye_bbox_from_layer(args.eye_white_r)]
    args.out_dir.mkdir(parents=True, exist_ok=True)

    # 얼굴 크롭 영역 (두 눈 + 여백)
    fx0 = min(b[0] for b in bboxes) - 120
    fx1 = max(b[2] for b in bboxes) + 120
    fy0 = min(b[1] for b in bboxes) - 160
    fy1 = max(b[3] for b in bboxes) + 200

    frames = []
    for t in T_STEPS:
        warped = base
        for bbox in bboxes:
            warped = curtain_warp(warped, bbox, t)
        frame = Image.fromarray(warped, "RGBA")
        frame.save(args.out_dir / f"blink_t{int(t*100):03d}.png")
        frames.append(frame.crop((fx0, fy0, fx1, fy1)))

    # 스트립 합성
    fw, fh = frames[0].size
    strip = Image.new("RGB", (fw * len(frames) + 8 * (len(frames) - 1), fh), (255, 255, 255))
    for i, frame in enumerate(frames):
        strip.paste(frame.convert("RGB"), (i * (fw + 8), 0))
    strip_path = args.out_dir / "blink_strip.png"
    strip.save(strip_path)

    write_json(
        args.out_dir / "arap_blink_report.json",
        {
            "test_id": "ARAP-EXP-001",
            "generated_at": now_iso(),
            "method": "column-wise curtain warp on the neutral assembly — original pixels only, zero generated pixels",
            "t_steps": T_STEPS,
            "strip": rel(strip_path),
            "verdict": "PENDING_HUMAN_REVIEW",
        },
    )
    print(f"strip: {rel(strip_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

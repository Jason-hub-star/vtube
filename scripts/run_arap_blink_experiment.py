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


def curtain_warp(image: np.ndarray, bbox: tuple[int, int, int, int], t: float, skin_band: float = 0.9) -> np.ndarray:
    """아몬드형 눈에 맞춘 커튼 워프 (공식 모델 관찰 반영, ARAP-EXP-001 v2).

    - 윗눈꺼풀이 주도 (top-down), 눈꼬리 양끝은 고정점
    - 닫힌 선은 바닥이 아니라 눈 높이 ~63% 지점의 "아래로 볼록한 아치"
    - 컬럼별로 윗곡선 up_x → 닫힘 아치 closed_x 로 보간
    """
    x0, lash_top, x1, y1 = bbox
    h = y1 - lash_top
    y0 = max(0, lash_top - round(h * skin_band))
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
        if lid - up_x < 0.5:
            continue
        ys_out = np.arange(y0, int(round(low_x)), dtype=np.float64)
        src = np.empty_like(ys_out)
        upper = ys_out <= lid
        denom_u = max(lid - y0, 1e-6)
        src[upper] = y0 + (ys_out[upper] - y0) * ((up_x - y0) / denom_u)
        denom_l = max(low_x - lid, 1e-6)
        src[~upper] = up_x + (ys_out[~upper] - lid) * ((low_x - up_x) / denom_l)
        src_idx = np.clip(src, 0, image.shape[0] - 1)
        lo = np.floor(src_idx).astype(int)
        hi = np.minimum(lo + 1, image.shape[0] - 1)
        frac = (src_idx - lo)[:, None]
        column = image[:, x, :].astype(np.float64)
        out[y0 : int(round(low_x)), x, :] = (column[lo] * (1 - frac) + column[hi] * frac).astype(image.dtype)
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

#!/usr/bin/env python3
"""face_base에 구워진 입을 피부로 덮어 부품형 입이 입 전담하게 한다 (MOUTH-CLEAR-001).

이중 입 사건(005 지피쨩): face_base 텍스처에 입이 구워져 있어(고정) 부품형 입이 그 위/밑에
열리면 입이 두 개로 보인다. 구운 입을 주변 피부색 페더 타원으로 덮으면 부품 입만 남아 원천 차단.
결정론: 피부색은 입 주변 살구 픽셀 중앙값 실측, 타원은 mouth_line bbox에서 파생.

사용: python3 scripts/clear_face_mouth.py --face face_base.png --mouth-line mouth_line.png --out face_base.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT  # noqa: E402


def layer_bbox(path: Path) -> tuple[int, int, int, int]:
    a = np.asarray(Image.open(path).convert("RGBA"))[..., 3]
    ys, xs = np.where(a > 8)
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--face", type=Path, required=True)
    parser.add_argument("--mouth-line", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    face = args.face if args.face.is_absolute() else ROOT / args.face
    mline = args.mouth_line if args.mouth_line.is_absolute() else ROOT / args.mouth_line
    out = args.out if args.out.is_absolute() else ROOT / args.out

    fb = np.asarray(Image.open(face).convert("RGBA")).astype(np.float64)
    rgb, alpha = fb[..., :3], fb[..., 3]
    lum = rgb.mean(-1)
    mx0, my0, mx1, my1 = layer_bbox(mline)
    cx0, line_h, line_w = (mx0 + mx1) / 2.0, max(my1 - my0, 6), max(mx1 - mx0, 10)
    # 구운 미소선은 분해 mouth_line보다 넓을 수 있다(입꼬리 잔존=수염). face_base에서 실제
    # 어두운 입 픽셀을 검출해 그 범위를 덮는다. seed 영역: mouth_line 중심 ±1.6배 폭, 아래로 4배.
    ry0, ry1 = int(my0 - line_h), int(my0 + line_h * 5)
    rx0, rx1 = int(cx0 - line_w * 1.6), int(cx0 + line_w * 1.6)
    sub_lum = lum[ry0:ry1, rx0:rx1]
    sub_a = alpha[ry0:ry1, rx0:rx1]
    dark = (sub_lum < 115) & (sub_a > 128)
    dys, dxs = np.where(dark)
    if len(dxs):  # 실제 어두운 입 범위(입꼬리 포함)
        bx0, bx1 = rx0 + int(dxs.min()), rx0 + int(dxs.max())
        by0, by1 = ry0 + int(dys.min()), ry0 + int(dys.max())
        cx = (bx0 + bx1) / 2.0
        cy = (by0 + by1) / 2.0
        ax = (bx1 - bx0) / 2.0 * 1.35 + 6   # 입꼬리까지 + 여유
        ay = (by1 - by0) / 2.0 * 1.35 + 6
    else:  # 폴백: mouth_line 기반
        cx, cy = cx0, my0 + line_h * 2.0
        ax, ay = line_w * 0.85, line_h * 3.0

    # 피부색: 타원 바깥 ~안쪽 링의 밝은 살구 픽셀 중앙값
    yy, xx = np.mgrid[0:fb.shape[0], 0:fb.shape[1]]
    ell = ((xx - cx) / ax) ** 2 + ((yy - cy) / ay) ** 2
    ring = (ell > 1.0) & (ell < 2.2) & (alpha > 200) & (lum > 170) & (rgb[..., 0] > rgb[..., 2] + 8)
    if ring.sum() < 50:
        ring = (ell > 1.0) & (ell < 3.0) & (alpha > 200)
    skin = np.median(rgb[ring], axis=0)

    # 페더 마스크: 타원 내부 1.0 → 경계 0 (부드러운 블렌드)
    w = np.clip(1.4 - ell, 0.0, 1.0)  # ell<0.4 완전, 1.4에서 0
    w = w[..., None]
    fb[..., :3] = rgb * (1 - w) + skin * w
    # 알파는 유지(얼굴 영역). 입 영역은 어차피 face_base 내부라 alpha 그대로.
    Image.fromarray(fb.astype(np.uint8), "RGBA").save(out)
    print(f"face 입 제거: 피부 {skin.astype(int).tolist()} 타원 중심({cx:.0f},{cy:.0f}) 반경({ax:.0f},{ay:.0f}) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

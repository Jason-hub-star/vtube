#!/usr/bin/env python3
"""각도 작화 눈꺼풀(블링크) 오버레이 생성 — 옆모습 리깅 PoC (ANGLE-SWAP-003).

각 각도 작화에서 홍채(보라끼)를 색분리해 눈 영역을 찾고, 그 위를 덮는 '감은 눈'
오버레이(눈 위 피부색 샘플 채움 + 기존 속눈썹 어둠선)를 만든다. 런타임에서 이
오버레이를 ParamEyeLOpen 역수 opacity로 켜면(눈뜸=숨김, 눈감음=덮음) 옆모습에서도
블링크가 된다. 생성 없이 결정론적 추출만 — LLM 픽셀 추측 금지.

PoC: 절차적 눈꺼풀이 실런타임 캡처에서 자연스러우면 채택, 거칠면 생성 변형으로 전환.

사용: python3 scripts/build_angle_blink.py --parts <angle parts dir> --angles 2,4
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import scipy.ndimage as ndi
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, now_iso, rel, write_json  # noqa: E402


def detect_eye_bbox(rgba: np.ndarray) -> tuple[int, int, int, int] | None:
    """홍채(보라끼) 색분리 → 최상단 얼굴 근처 컴포넌트들의 합 bbox (눈 영역)."""
    rgb = rgba[..., :3].astype(int)
    al = rgba[..., 3]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    iris = (al > 128) & (b > r + 10) & (b > g + 5) & (b > 60) & (b < 200)
    if iris.sum() < 40:
        return None
    ys, xs = np.where(al > 128)
    face_top = ys.min()
    # 얼굴 상단 35% 밴드 안의 홍채만 (가슴 장식 보라끼 오검출 제거)
    band_lo, band_hi = face_top, face_top + (ys.max() - face_top) * 0.35
    irys, irxs = np.where(iris)
    keep = (irys >= band_lo) & (irys <= band_hi)
    if keep.sum() < 40:
        return None
    iy, ix = irys[keep], irxs[keep]
    x0, y0, x1, y1 = int(ix.min()), int(iy.min()), int(ix.max()) + 1, int(iy.max()) + 1
    # 눈 흰자·속눈썹까지 덮도록 여유 확장 (위로 더, 좌우로)
    mw, mh = round((x1 - x0) * 0.35), round((y1 - y0) * 0.9)
    return (x0 - mw, y0 - mh, x1 + mw, y1 + round((y1 - y0) * 0.4))


def skin_color(rgba: np.ndarray, bbox: tuple[int, int, int, int]) -> tuple[int, int, int]:
    """눈 bbox 바로 위 피부 픽셀 중앙값 (눈꺼풀 채움색)."""
    x0, y0, x1, y1 = bbox
    al = rgba[..., 3]
    strip = rgba[max(0, y0 - 40):y0, x0:x1]
    sa = strip[..., 3]
    rgb = rgba[..., :3].astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    skin = (sa > 128) & (strip[..., 0].astype(int) > strip[..., 2].astype(int) + 8)
    if skin.sum() < 10:  # 폴백: bbox 주변 알파>128 중앙값
        ys, xs = np.where(al > 128)
        return tuple(int(np.median(rgba[ys, xs, c])) for c in range(3))
    pix = strip[..., :3][skin]
    return tuple(int(np.median(pix[:, c])) for c in range(3))


def build_lid(rgba: np.ndarray, bbox: tuple[int, int, int, int],
              skin: tuple[int, int, int]) -> np.ndarray:
    """감은 눈 오버레이: 눈 영역을 피부색으로 덮고 하단에 속눈썹 어둠선."""
    h, w = rgba.shape[:2]
    x0, y0, x1, y1 = (max(0, bbox[0]), max(0, bbox[1]), min(w, bbox[2]), min(h, bbox[3]))
    out = np.zeros((h, w, 4), np.uint8)
    # 눈 영역에서 어두운(속눈썹) 픽셀 위치 기록 → 닫힌 눈 선으로 재사용
    region = rgba[y0:y1, x0:x1]
    lum = region[..., :3].astype(int).mean(-1)
    dark = (region[..., 3] > 128) & (lum < 90)
    # 피부 채움 (눈 영역 타원형)
    yy, xx = np.mgrid[0:y1 - y0, 0:x1 - x0]
    cy, cx = (y1 - y0) / 2, (x1 - x0) / 2
    ell = ((yy - cy) / max(cy, 1)) ** 2 + ((xx - cx) / max(cx, 1)) ** 2 <= 1.0
    fill = np.zeros_like(region)
    fill[ell] = [skin[0], skin[1], skin[2], 255]
    # 속눈썹 선: 닫힌 눈 위치(영역 중하단)에 기존 어둠픽셀 색을 가로선으로
    lash_y = int((y1 - y0) * 0.55)
    lash_band = (yy >= lash_y - 2) & (yy <= lash_y + 2) & ell
    fill[lash_band] = [40, 35, 38, 255]
    # 원래 속눈썹 어둠도 흐리게 남겨 자연스럽게
    keep_dark = dark & ell
    fill[keep_dark] = region[keep_dark]
    out[y0:y1, x0:x1] = fill
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parts", type=Path, required=True)
    parser.add_argument("--angles", default="1,2,3,4", help="좌향 각도 인덱스 (콤마)")
    parser.add_argument("--include-right", action="store_true", help="우향 미러도 처리")
    args = parser.parse_args()
    parts = args.parts if args.parts.is_absolute() else ROOT / args.parts
    idxs = [int(x) for x in args.angles.split(",")]

    targets = [f"head_angle_{k}.png" for k in idxs]
    if args.include_right:
        targets += [f"head_angle_right_{k}.png" for k in idxs]

    written, manifest = [], []
    for name in targets:
        src = parts / name
        if not src.exists():
            print(f"  건너뜀(없음): {name}")
            continue
        rgba = np.array(Image.open(src).convert("RGBA"))
        bbox = detect_eye_bbox(rgba)
        if bbox is None:
            print(f"  {name}: 눈 색분리 실패 — 생성 변형 필요")
            manifest.append({"part": name, "eye_detected": False})
            continue
        skin = skin_color(rgba, bbox)
        lid = build_lid(rgba, bbox, skin)
        lid_name = src.stem + "_lid.png"
        Image.fromarray(lid, "RGBA").save(parts / lid_name)
        written.append(lid_name)
        manifest.append({"part": name, "eye_detected": True, "eye_bbox": list(bbox),
                         "skin_rgb": list(skin), "lid": lid_name})
        print(f"  {name}: 눈 bbox {bbox} 피부 {skin} -> {lid_name}")

    write_json(parts.parent / "blink_manifest.json", {
        "generated_at": now_iso(), "parts_dir": rel(parts), "written": written,
        "method": "절차적 눈꺼풀(피부색 채움+속눈썹선), ParamEyeLOpen 역수 opacity 스왑",
        "cells": manifest})
    print(f"눈꺼풀 오버레이 {len(written)}장 -> {rel(parts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

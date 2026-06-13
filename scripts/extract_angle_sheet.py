#!/usr/bin/env python3
"""각도 시트(1×5) → 머리 중심 정렬된 풀캔버스 각도 작화 5장 (ANGLE-SWAP-001).

gpt-image-2가 생성한 5각도(정면→좌측면, 20도 간격) 시트를 셀 분리해, 각 각도의
머리 꼭대기 중심을 공통 앵커에 맞춰 2048 캔버스에 배치한다 → ParamAngleX opacity
스왑 시 머리가 제자리, 몸만 각도 따라 미세 이동. 입 4상태 추출 패턴의 각도판.

배경 제거: 시트는 크로마(마젠타)가 아니라 연한 단색 배경 → 가장자리에서 연결된
흰/저채도 영역만 알파 0 (인물 내부 흰 트림은 보존). flood 라벨링.

사용: python3 scripts/extract_angle_sheet.py --sheet <angle5.png> --out-dir <dir> --cols 5
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import scipy.ndimage as ndi
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.sheet_overlay import cell_of, load_sheet, place_content  # noqa: E402
from lib.vtube_io import ROOT, now_iso, rel, write_json  # noqa: E402

CANVAS = 2048
BG_LUM = 232      # 배경 밝기 하한 (시트 실측 244)
BG_SAT = 22       # 배경 저채도 상한 (실측 5)
HEAD_BAND = 0.22  # 머리 중심 추정용 상단 밴드 비율
DST_HEAD = (CANVAS // 2, 360)  # 공통 머리 꼭대기 앵커 (x중심, y)


def background_alpha(rgb: np.ndarray) -> np.ndarray:
    """가장자리에서 연결된 흰/저채도 영역만 배경(알파 0) — 인물 내부 흰색 보존."""
    lum = rgb.mean(-1)
    sat = rgb.max(-1) - rgb.min(-1)
    bg = (lum > BG_LUM) & (sat < BG_SAT)
    labels, _ = ndi.label(bg)
    edge = set(labels[0, :]) | set(labels[-1, :]) | set(labels[:, 0]) | set(labels[:, -1])
    edge.discard(0)
    bg_connected = np.isin(labels, list(edge))
    return ((~bg_connected) * 255).astype(np.uint8)


def head_anchor(alpha: np.ndarray) -> tuple[float, float, int, int, int, int]:
    """인물 알파 bbox + 머리 꼭대기 중심 (상단 밴드 가중 x, bbox top y)."""
    ys, xs = np.where(alpha > 128)
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
    band = ys < y0 + (y1 - y0) * HEAD_BAND
    head_cx = float(xs[band].mean()) if band.any() else (x0 + x1) / 2
    return head_cx, float(y0), x0, y0, x1, y1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--cols", type=int, default=5)
    args = parser.parse_args()
    out = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    (out / "parts").mkdir(parents=True, exist_ok=True)

    sheet = load_sheet(args.sheet, size=CANVAS)
    heights = []
    cells = []
    for i in range(args.cols):
        cell = cell_of(sheet, 0, i, rows=1, cols=args.cols)
        alpha = background_alpha(cell)
        if (alpha > 128).sum() < 5000:
            raise SystemExit(f"셀 {i}: 인물 픽셀 부족 (배경 제거 과다?)")
        hcx, htop, x0, y0, x1, y1 = head_anchor(alpha)
        rgba = np.dstack([cell, alpha])
        heights.append(y1 - y0)
        cells.append({"i": i, "rgba": rgba, "hcx": hcx, "htop": htop, "bbox": [x0, y0, x1, y1]})

    # 공통 스케일: 첫 셀(정면) 인물 높이 기준으로 정규화 (각도별 생성 크기 변동 흡수)
    ref_h = heights[0]
    written, manifest_cells = [], []
    for c in cells:
        x0, y0, x1, y1 = c["bbox"]
        crop = c["rgba"][y0:y1, x0:x1]
        scale = ref_h / max(c["bbox"][3] - c["bbox"][1], 1)
        src = (c["hcx"] - x0, c["htop"] - y0)
        canvas = place_content(crop, scale, src, DST_HEAD, canvas=CANVAS)
        path = out / "parts" / f"head_angle_{c['i']}.png"
        canvas.save(path)
        written.append(path.name)
        manifest_cells.append({"index": c["i"], "scale": round(scale, 4),
                               "head_cx": round(c["hcx"], 1), "head_top": round(c["htop"], 1)})
        print(f"head_angle_{c['i']}: scale {scale:.3f} head_cx {c['hcx']:.0f}")

    write_json(out / "angle_manifest.json", {
        "generated_at": now_iso(), "sheet": rel(args.sheet), "cols": args.cols,
        "dst_head_anchor": list(DST_HEAD), "cells": manifest_cells, "written": written})

    # 겹침 미리보기 (머리 정렬 확인)
    prev = Image.new("RGBA", (CANVAS, CANVAS), (90, 90, 90, 255))
    for name in written:
        layer = Image.open(out / "parts" / name).convert("RGBA")
        layer.putalpha(layer.getchannel("A").point(lambda a: a // 3))
        prev.alpha_composite(layer)
    prev.convert("RGB").save(out / "angle_overlap_preview.png")
    print(f"angle parts: {len(written)} -> {rel(out)} (겹침 미리보기: angle_overlap_preview.png)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

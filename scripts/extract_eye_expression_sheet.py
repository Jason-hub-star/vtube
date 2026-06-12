#!/usr/bin/env python3
"""눈 표정 시트(2×3) → 어셈블리 정렬 표정 오버레이 6장 (EXPR-003, 004 사이클).

EXPR-002 눈웃음 워프 폴백("그저그렇")의 대체 — 생성 시트의 작화 그대로를 쓴다.
각 셀(눈쌍+눈썹)을 크로마 분리 → 눈 밴드(눈썹 아래 밴드)의 좌/우 중심 간격을
원본 눈흰자 중심 간격에 맞춰 스케일·배치 → 스킨 플레이트(원본 눈/눈썹을 컬럼
인페인트로 지운 패치) 위에 합성. 활성 시 기본 눈 파트는 리그 불투명 곡선이 숨긴다.

사용: python3 scripts/extract_eye_expression_sheet.py --sheet <eyes.png> \
        --reskin-dir <seethrough_true_reskinned> --assembly <assembly.png> --out-dir <dir>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.sheet_overlay import (  # noqa: E402
    CANVAS, cell_content, cell_of, feather, half_centers, inpaint_columns,
    layer_bbox, load_sheet, mask_bbox, place_content, row_bands,
)
from lib.vtube_io import ROOT, now_iso, rel, write_json  # noqa: E402

# MASTER-SPEC §3.2 셀 배치 (row, col)
EXPRESSIONS = [("smile", 0, 0), ("wink", 0, 1), ("surprise", 0, 2),
               ("jito", 1, 0), ("squeeze", 1, 1), ("heart", 1, 2)]
BASE_EYE_LAYERS = ["L_eye_white", "R_eye_white", "L_iris", "R_iris",
                   "L_upper_lash", "R_upper_lash", "L_brow", "R_brow"]
PLATE_PAD = 18
FEATHER_PX = 10


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet", type=Path, required=True)
    parser.add_argument("--reskin-dir", type=Path, required=True)
    parser.add_argument("--assembly", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    # 타깃 기하: 원본 눈흰자 중심 간격 (뷰어 좌/우는 x로 정렬되므로 명명 무관)
    eye_boxes = [layer_bbox(args.reskin_dir / f"{side}_eye_white.png") for side in ("L", "R")]
    centers = sorted((((b[0] + b[2]) / 2), ((b[1] + b[3]) / 2)) for b in eye_boxes)
    target_span = centers[1][0] - centers[0][0]
    target_mid = ((centers[0][0] + centers[1][0]) / 2, (centers[0][1] + centers[1][1]) / 2)

    sheet = load_sheet(args.sheet)
    assembly = np.asarray(Image.open(args.assembly).convert("RGBA"))

    # 스킨 플레이트: 원본 눈/눈썹/속눈썹 픽셀을 컬럼 인페인트로 지운 얼굴 패치 (전 표정 공용 영역)
    fill = np.zeros(assembly.shape[:2], dtype=bool)
    plate_x0, plate_y0, plate_x1, plate_y1 = CANVAS, CANVAS, 0, 0
    for name in BASE_EYE_LAYERS:
        path = args.reskin_dir / f"{name}.png"
        if not path.exists():
            continue
        alpha = np.asarray(Image.open(path).convert("RGBA"))[..., 3]
        fill |= alpha > 8
        x0, y0, x1, y1 = layer_bbox(path)
        plate_x0, plate_y0 = min(plate_x0, x0), min(plate_y0, y0)
        plate_x1, plate_y1 = max(plate_x1, x1), max(plate_y1, y1)
    # 인페인트 마스크 3px 팽창 — 안티앨리어스 테두리 잔픽셀 제거
    for _ in range(3):
        fill |= np.roll(fill, 1, 0) | np.roll(fill, -1, 0) | np.roll(fill, 1, 1) | np.roll(fill, -1, 1)
    plate_box = (max(0, plate_x0 - PLATE_PAD), max(0, plate_y0 - PLATE_PAD),
                 min(CANVAS, plate_x1 + PLATE_PAD), min(CANVAS, plate_y1 + PLATE_PAD))
    px0, py0, px1, py1 = plate_box
    region_rgb = inpaint_columns(assembly[py0:py1, px0:px1, :3], fill[py0:py1, px0:px1])
    face_alpha = np.asarray(Image.open(args.reskin_dir / "face_base.png").convert("RGBA"))[py0:py1, px0:px1, 3]
    plate = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    plate.paste(Image.fromarray(np.dstack([region_rgb, face_alpha]), "RGBA"), (px0, py0))
    plate = feather(plate, FEATHER_PX)

    written, cells = [], {}
    for name, row, col in EXPRESSIONS:
        cell = cell_of(sheet, row, col, rows=2, cols=3)
        rgba, mask = cell_content(cell)
        if mask is None:
            raise SystemExit(f"{name}: 셀에 콘텐츠 없음")
        # 눈 밴드 = 눈썹 밴드 아래 (밴드 1개뿐이면 전체가 눈)
        bands = row_bands(mask, min_gap=6)
        eye_y0 = bands[1][0] if len(bands) >= 2 else bands[0][0]
        eye_mask = np.zeros_like(mask)
        eye_mask[eye_y0:] = mask[eye_y0:]
        pair = half_centers(eye_mask)
        if pair is None:
            raise SystemExit(f"{name}: 눈 좌/우 분리 실패")
        (lx, ly), (rx, ry) = pair
        span = max(rx - lx, 1.0)
        scale = target_span / span
        if not 0.15 <= scale <= 2.0:
            raise SystemExit(f"{name}: 스케일 {scale:.2f} 비정상 (셀 간격 {span:.0f}px)")
        x0, y0, x1, y1 = mask_bbox(mask)
        src_anchor = ((lx + rx) / 2 - x0, (ly + ry) / 2 - y0)
        overlay = place_content(rgba[y0:y1, x0:x1], scale, src_anchor, target_mid)
        composed = plate.copy()
        composed.alpha_composite(overlay)
        path = out / f"eye_expr_{name}.png"
        composed.save(path)
        written.append(path.name)
        cells[name] = {"scale": round(scale, 4), "cell_span": round(span, 1),
                       "bands": len(bands), "eye_centers": [[round(lx), round(ly)], [round(rx), round(ry)]]}
        print(f"{name}: scale {scale:.3f} bands {len(bands)}")

    write_json(out / "eye_expr_manifest.json", {
        "generated_at": now_iso(), "sheet": rel(args.sheet),
        "target_span": round(target_span, 1), "target_mid": [round(v, 1) for v in target_mid],
        "plate_box": list(plate_box), "expressions": [n for n, _, _ in EXPRESSIONS],
        "cells": cells, "written": written,
    })
    print(f"eye_expr: {len(written)}장 -> {rel(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

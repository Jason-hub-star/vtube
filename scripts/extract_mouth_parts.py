#!/usr/bin/env python3
"""부품형 입 추출 (MOUTH-PARTS-001): wide 셀 → 입술/입안/이빨/혀 5부품 풀캔버스 레이어.

4상태 스냅(내용 스왑)의 근본 대체 — 한 작화의 부품들이 정점 키폼으로 연속 개폐된다.
색·연결성분 분류 (전부 결정론, 004 wide 셀 실측 임계값):
  - 어두움(L<100) → 두꺼운 성분(모폴로지 열림) = 입안, 얇은 성분 = 입술 스트로크
  - 흰색(L>190, sat<60) → 입안 중심 위 = 이빨, 아래 = 아랫입술 하이라이트
  - 분홍(R>140, sat 40..130, L 120..215) = 혀
  - 입안 부품은 이빨/혀 자리를 입안 중간색으로 메운 솔리드 — 클립 마스크 겸용
  - 잔여 픽셀은 입안 중심 y 기준 윗/아랫입술로 — 부품 합집합 = 원본 셀 (누락 0)

분류 실패(부품 픽셀 부족) 시 manifest ok=false + exit 3 — 파이프라인은 4상태 스냅 폴백.

사용: python3 scripts/extract_mouth_parts.py --sheet <mouth.png> \
        --mouth-line <mouth_line.png> --out-dir <dir>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import scipy.ndimage as ndi
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.sheet_overlay import CANVAS, cell_content, cell_of, layer_bbox, load_sheet, mask_bbox  # noqa: E402
from lib.vtube_io import ROOT, now_iso, rel, write_json  # noqa: E402

SCALE_MARGIN = 0.97  # v21 교훈 (extract_mouth_states 동일): 폭은 원본 입선에 절제 정합
MIN_PX = {"interior": 5000, "teeth": 1500, "tongue": 1500, "upper_lip": 800, "lower_lip": 800}
DRAW_NAMES = ("interior", "tongue", "teeth", "lower_lip", "upper_lip")  # 아래→위


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet", type=Path, required=True)
    parser.add_argument("--mouth-line", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    def give_up(reason: str) -> int:
        write_json(out / "mouth_parts_manifest.json", {
            "generated_at": now_iso(), "ok": False, "reason": reason, "sheet": rel(args.sheet)})
        print(f"FALLBACK: {reason} — 4상태 스냅 경로 유지")
        return 3

    sheet = load_sheet(args.sheet)
    cell = cell_of(sheet, 1, 1, rows=2, cols=2)  # wide
    rgba, mask = cell_content(cell)
    if mask is None:
        return give_up("wide 셀 콘텐츠 없음")
    rgb = rgba[..., :3].astype(int)
    lum = rgb.mean(axis=-1)
    sat = rgb.max(axis=-1) - rgb.min(axis=-1)

    dark = (lum < 100) & mask
    white = (lum > 190) & (sat < 60) & mask
    pink = (rgb[..., 0] > 140) & (sat >= 40) & (sat <= 130) & (lum >= 120) & (lum <= 215) & mask

    # 입안 = 두꺼운 어두운 성분 (열림 연산으로 얇은 스트로크 제거 → 최대 성분)
    thick = ndi.binary_opening(dark, structure=np.ones((9, 9)))
    labels, n = ndi.label(thick)
    if n == 0:
        return give_up("두꺼운 입안 성분 없음")
    interior_core = labels == (np.bincount(labels.ravel())[1:].argmax() + 1)
    interior_dark = dark & ndi.binary_dilation(interior_core, iterations=6)
    strokes = dark & ~interior_dark

    # 혀 = 최대 분홍 성분
    labels, n = ndi.label(pink)
    if n == 0:
        return give_up("혀(분홍) 성분 없음")
    tongue = labels == (np.bincount(labels.ravel())[1:].argmax() + 1)

    # 솔리드 입안 = (입안∪이빨∪혀) 채움 — 이빨/혀 자리는 입안 중간색으로 메워 클립 마스크 겸용
    iy = np.where(interior_dark.any(axis=1))[0]
    split_y = int((iy.min() + iy.max()) / 2)
    aperture = ndi.binary_fill_holes(interior_dark | (white & ~strokes) | tongue)
    aperture &= ~strokes  # 입술 스트로크는 입안이 아니다 (경계 명확화)

    # 이빨/아랫입술 하이라이트: 흰 성분을 입안 중심 y로 분류
    teeth = np.zeros_like(mask)
    lower_white = np.zeros_like(mask)
    labels, n = ndi.label(white)
    for i in range(1, n + 1):
        comp = labels == i
        cy = np.where(comp.any(axis=1))[0].mean()
        (teeth if cy < split_y else lower_white)[comp] = True

    # 잔여 픽셀(안티앨리어스·기타) → 상/하 입술로 흡수 (부품 합집합 = 콘텐츠 보장)
    assigned = aperture | tongue | teeth
    rest = mask & ~assigned
    rows_idx = np.arange(mask.shape[0])[:, None]
    upper_lip = rest & (rows_idx < split_y) & ~lower_white
    lower_lip = (rest & (rows_idx >= split_y)) | lower_white
    # 이빨/혀에서 입안 밖으로 새는 픽셀은 그대로 두되 클리핑이 가둔다 (런타임 마스크 = 입안)

    parts_mask = {"interior": aperture, "teeth": teeth & aperture, "tongue": tongue & aperture,
                  "upper_lip": upper_lip, "lower_lip": lower_lip}
    counts = {k: int(v.sum()) for k, v in parts_mask.items()}
    lacking = [k for k, v in counts.items() if v < MIN_PX[k]]
    if lacking:
        return give_up(f"부품 픽셀 부족: { {k: counts[k] for k in lacking} }")

    # 공유 변환: 콘텐츠 폭 → 원본 입선 폭 (0.97). MOUTH-LIP-RIDE-001: 윗입술은 미소선이
    # 담당하므로 입안(interior) 상단을 미소선 하단보다 OVERLAP px 위에 물려 미소선이 입안
    # 윗경계를 덮는다 (이음새 0). 미소선 중심은 중앙 30% 컬럼 실측(앵커·H(v) 붕괴점).
    mx0, my0, mx1, my1 = layer_bbox(args.mouth_line)
    line_alpha = np.asarray(Image.open(args.mouth_line).convert("RGBA"))[..., 3] > 8
    centers, lows = [], []
    for cx_ in range(int(mx0 + (mx1 - mx0) * 0.35), int(mx0 + (mx1 - mx0) * 0.65)):
        ys_ = np.where(line_alpha[:, cx_])[0]
        if len(ys_):
            centers.append((ys_.min() + ys_.max()) / 2)
            lows.append(ys_.max())
    line_center_y = float(np.mean(centers)) if centers else (my0 + my1) / 2
    line_bottom_y = float(np.mean(lows)) if lows else float(my1)
    x0, y0, x1, y1 = mask_bbox(mask)
    scale = ((mx1 - mx0) * SCALE_MARGIN) / (x1 - x0)
    dst_x = (mx0 + mx1) / 2
    OVERLAP = 11  # 미소선이 입안 윗경계를 덮는 겹침 — 윗입술↔입안 이음새 0 (미소곡선 입안은 중앙이 살짝 처져 8px로는 3px 갭)
    iy = np.where(parts_mask["interior"].any(axis=1))[0]
    interior_top_cell = float(iy.min()) if len(iy) else float(y0)
    paste_y = round((line_bottom_y - OVERLAP) - (interior_top_cell - y0) * scale)
    interior_fill = np.median(rgb[interior_dark], axis=0).astype(np.uint8)

    written, part_boxes = [], {}
    for name in DRAW_NAMES:
        pm = parts_mask[name]
        layer = np.zeros_like(rgba)
        layer[pm] = rgba[pm]
        if name == "interior":  # 이빨/혀 자리 메움 (원본 어두운 픽셀은 보존)
            hole = aperture & ~interior_dark
            layer[hole, :3] = interior_fill
            layer[hole, 3] = 255
        crop = Image.fromarray(layer[y0:y1, x0:x1], "RGBA")
        new_size = (max(1, round(crop.width * scale)), max(1, round(crop.height * scale)))
        crop = crop.resize(new_size, Image.LANCZOS)
        canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
        canvas.alpha_composite(crop, (round(dst_x - crop.width / 2), paste_y))
        path = out / f"mouth_parts_{name}.png"
        canvas.save(path)
        written.append(path.name)
        pys, pxs = np.where(pm)
        part_boxes[name] = {"px": counts[name],
                            "cell_bbox": [int(pxs.min()), int(pys.min()), int(pxs.max()) + 1, int(pys.max()) + 1]}
        print(f"{name}: px={counts[name]}")

    write_json(out / "mouth_parts_manifest.json", {
        "generated_at": now_iso(), "ok": True, "sheet": rel(args.sheet),
        # anchor_y = 입안 상단(미소선 바로 아래) — H(v) 세로 스케일의 고정점.
        # 미소선 중심이 아니라 입안 상단이어야 윗부분이 고정되고 아래로만 펼쳐진다 = 윗입술 고정
        # (중심 앵커는 입안이 위로도 올라가 미소선을 어둡게 덮어 미소선이 묻혔다 — H2 5차 진단).
        "scale": round(scale, 5), "anchor_y": round(line_bottom_y - OVERLAP), "split_y_cell": split_y,
        "mouth_line_bbox": [mx0, my0, mx1, my1], "parts": part_boxes, "written": written,
    })
    print(f"mouth_parts: {written} -> {rel(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

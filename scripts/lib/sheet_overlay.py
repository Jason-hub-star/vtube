"""시트 오버레이 공유 헬퍼 — 004 표정/액센트/부품입 추출기 공용 (MOUTH-PARTS-001 / EXPR 시트).

크로마 셀 분리·콘텐츠 밴드 분석·어셈블리 좌표 정렬. 전부 결정론적 픽셀 연산 —
좌표에 LLM 비전 추측 금지 원칙 준수. 크로마/despill은 run_autorig_sheet_pilot 재사용.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from run_autorig_sheet_pilot import chroma_alpha, despill

CANVAS = 2048
MAGENTA = (255, 0, 255)


def load_sheet(path: Path, size: int = CANVAS) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB").resize((size, size), Image.LANCZOS))


def cell_of(sheet: np.ndarray, row: int, col: int, rows: int, cols: int) -> np.ndarray:
    h, w = sheet.shape[:2]
    ys = [round(h * i / rows) for i in range(rows + 1)]
    xs = [round(w * i / cols) for i in range(cols + 1)]
    return sheet[ys[row] : ys[row + 1], xs[col] : xs[col + 1]]


def cell_content(cell: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """크로마 셀 → (RGBA uint8, 콘텐츠 마스크). 마스크 없으면 둘 다 None."""
    alpha = chroma_alpha(cell, MAGENTA)
    mask = alpha > 0.5
    if not mask.any():
        return None, None
    rgba = np.dstack([despill(cell), (alpha * 255).astype(np.uint8)])
    return rgba, mask


def mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    """(x0, y0, x1, y1) — 끝 좌표는 exclusive."""
    ys, xs = np.where(mask)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def row_bands(mask: np.ndarray, min_gap: int = 6) -> list[tuple[int, int]]:
    """행 프로파일로 콘텐츠 밴드 분리 (눈썹/눈 분리용). [(y0, y1)] 위→아래."""
    rows = mask.any(axis=1)
    bands, start = [], None
    gap = 0
    for y, on in enumerate(rows):
        if on:
            if start is None:
                start = y
            gap = 0
        elif start is not None:
            gap += 1
            if gap >= min_gap:
                bands.append((start, y - gap + 1))
                start = None
    if start is not None:
        bands.append((start, len(rows)))
    return bands


def half_centers(mask: np.ndarray) -> tuple[tuple[float, float], tuple[float, float]] | None:
    """콘텐츠 bbox 세로 중앙선으로 좌/우 분할 → 각 반쪽 콘텐츠 bbox 중심."""
    x0, y0, x1, y1 = mask_bbox(mask)
    mid = (x0 + x1) // 2
    out = []
    for sl in (np.s_[:, :mid], np.s_[:, mid:]):
        part = np.zeros_like(mask)
        part[sl] = mask[sl]
        if not part.any():
            return None
        px0, py0, px1, py1 = mask_bbox(part)
        out.append(((px0 + px1) / 2, (py0 + py1) / 2))
    return out[0], out[1]


def layer_bbox(path: Path) -> tuple[int, int, int, int]:
    """레이어 PNG 알파 bbox (x0, y0, x1, y1)."""
    alpha = np.asarray(Image.open(path).convert("RGBA"))[..., 3]
    mask = alpha > 8
    if not mask.any():
        return 0, 0, 4, 4
    return mask_bbox(mask)


def place_content(rgba: np.ndarray, scale: float, src_anchor: tuple[float, float],
                  dst_anchor: tuple[float, float], canvas: int = CANVAS) -> Image.Image:
    """콘텐츠 RGBA를 균일 스케일 후 src_anchor가 dst_anchor에 오도록 캔버스에 배치."""
    img = Image.fromarray(rgba, "RGBA")
    new_size = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
    img = img.resize(new_size, Image.LANCZOS)
    out = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    px = round(dst_anchor[0] - src_anchor[0] * scale)
    py = round(dst_anchor[1] - src_anchor[1] * scale)
    out.alpha_composite(img, (px, py))
    return out


def feather(img: Image.Image, px: int) -> Image.Image:
    """알파를 블러와 min — 경계가 바탕에 녹아든다 (extract_mouth_states 패턴)."""
    a = img.getchannel("A")
    blurred = a.filter(ImageFilter.GaussianBlur(px))
    img = img.copy()
    img.putalpha(Image.fromarray(np.minimum(np.asarray(a), np.asarray(blurred))))
    return img


def inpaint_columns(rgb: np.ndarray, fill_mask: np.ndarray) -> np.ndarray:
    """컬럼별 선형 보간 인페인트 — fill_mask 픽셀을 위/아래 비채움 픽셀 색으로 메운다.

    아니메 평면 셰이딩 전제의 결정론 인페인트 (표정 플레이트의 원본 눈/눈썹 지우기).
    """
    out = rgb.astype(np.float64).copy()
    h = rgb.shape[0]
    idx = np.arange(h, dtype=np.float64)
    for x in np.where(fill_mask.any(axis=0))[0]:
        col_fill = fill_mask[:, x]
        good = ~col_fill
        if good.sum() < 2:
            continue
        gy = np.where(good)[0]
        for c in range(3):
            out[col_fill, x, c] = np.interp(idx[col_fill], gy, out[gy, x, c])
    return np.clip(out, 0, 255).astype(np.uint8)

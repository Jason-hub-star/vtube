#!/usr/bin/env python3
"""어깨 위 머리카락 분리 — 분해가 가닥을 clothes에 구워놓은 경우 (CHAIN-001 후속).

머리를 따라가야 할 어깨·가슴 위 가닥이 clothes 소속이면 회두 시 머리 본체와 분리된다.
머리카락색 픽셀을 분리해 shoulder_hair 파트로 만들고(머리 체인 소속), clothes의 해당
픽셀은 주변 정규화 블러 필드로 재도색한다 (알파 유지 — 구멍이 아니라 밑그림 충전).

사용: python3 scripts/split_shoulder_hair.py \
        --clothes <clothes_trimmed.png> --hair-ref <hair_back_L.png> --out-dir <dir>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, now_iso, rel, write_json  # noqa: E402

# AUTORIG-TEMPLATE-001: COLOR_DIST를 머리-의상 색 거리에서 자동 산출 (캐릭터 색 무관 적응).
# 004 위벨 사건: 검은 드레스(50,50,55) vs 암녹 머리(65,66,36) RGB 거리 29 — 고정 60으로는
# 드레스 18.7만px가 머리로 오분류. 임계 = 머리-의상 거리 × 비율로 두면 색이 가까운 캐릭터도 안전.
COLOR_DIST_MAX = 60    # 자동 임계 상한 (색 거리가 매우 큰 캐릭터의 캡)
COLOR_DIST_RATIO = 0.5  # 임계 = min(상한, 머리-의상 색 거리 × 0.5) — 머리는 안, 의상은 밖
LUM_MAX = 150        # 피부 그림자 오분류 방지 (머리카락은 어둡다)
# 명도 불변 색도(chromaticity) 판별 — 어두운 의상과 어두운 머리를 색상으로 가른다 (004 래칫)
CHROMA_DIST = 0.10   # 정규화 색도 거리 임계 (004 실측: 머리-드레스 0.169, 머리 내부 분산 << 0.10)
LUM_MIN = 25         # 근흑색은 색도가 노이즈 — 머리 인정 제외
MAX_CLOTHES_RATIO = 0.25  # 가드: 가시 의상의 25% 초과 분리 = 색 누수 — 분리 포기(의상 통짜 유지)
DENSITY = 0.35       # 5px 박스 밀도 — 고립 스펙클 제거 (가닥은 두껍다)
FILL_DILATE = 4      # 재도색 범위 (가닥 + 번짐 여유)
FILL_SIGMA = 14      # 정규화 블러 필드 시그마
FEATHER = 2.5        # shoulder_hair 알파 페더


def blur_f(arr: np.ndarray, sigma: float) -> np.ndarray:
    # PIL 'F' 모드는 GaussianBlur 미지원 — 0..255로 정규화해 'L'로 블러 후 복원 (8bit 양자화 허용)
    peak = float(arr.max())
    if peak <= 0:
        return arr.astype(np.float64)
    scaled = np.clip(arr / peak * 255.0, 0, 255).astype(np.uint8)
    blurred = np.asarray(Image.fromarray(scaled, "L").filter(ImageFilter.GaussianBlur(sigma)))
    return blurred.astype(np.float64) / 255.0 * peak


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clothes", type=Path, required=True)
    parser.add_argument("--hair-ref", type=Path, required=True, help="머리카락 색 기준 (hair_back 덩어리)")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    clothes = np.asarray(Image.open(args.clothes).convert("RGBA")).copy()
    ref = np.asarray(Image.open(args.hair_ref).convert("RGBA"))
    hair_med = np.median(ref[ref[..., 3] > 200][:, :3], axis=0)

    rgb = clothes[..., :3].astype(np.float64)
    alpha = clothes[..., 3]
    # 색 임계 자동: 머리색(실측)과 의상색(실측)의 거리에서 — 검은드레스처럼 가까운 색도 안전 분리
    clothes_med = np.median(rgb[alpha > 100], axis=0)
    hair_clothes_dist = float(np.sqrt(((hair_med - clothes_med) ** 2).sum()))
    color_dist = min(COLOR_DIST_MAX, hair_clothes_dist * COLOR_DIST_RATIO)
    dist = np.sqrt(((rgb - hair_med) ** 2).sum(-1))
    lum = rgb.mean(-1)
    # 색도 판별 (명도 불변): 어두운 의상과 어두운 머리를 색상으로 가른다 (004 래칫)
    chroma = rgb / np.maximum(rgb.sum(-1, keepdims=True), 1e-6)
    hair_chroma = hair_med / max(float(hair_med.sum()), 1e-6)
    cdist = np.sqrt(((chroma - hair_chroma) ** 2).sum(-1))
    raw = (alpha > 100) & (dist < color_dist) & (lum < LUM_MAX) & (lum > LUM_MIN) & (cdist < CHROMA_DIST)
    # 밀도 필터: 가닥(두꺼움)은 살리고 그림자 가장자리 스펙클은 버린다
    density = blur_f(raw.astype(np.float64), 2.5)
    mask = raw & (density > DENSITY)
    count = int(mask.sum())
    if count < 500:
        print(f"shoulder_hair: 가닥 픽셀 {count} < 500 — 분리 불필요 (산출 없음)")
        write_json(out / "shoulder_hair_config.json", {"generated_at": now_iso(), "pixels": count, "split": False})
        return 0
    visible_n = int((alpha > 100).sum())
    if count > visible_n * MAX_CLOTHES_RATIO:
        print(f"shoulder_hair: {count}px > 의상 {visible_n}px의 {MAX_CLOTHES_RATIO:.0%} — 색 누수 가드, 분리 포기")
        write_json(out / "shoulder_hair_config.json", {
            "generated_at": now_iso(), "pixels": count, "split": False,
            "reason": f"color_leak_guard: {count}/{visible_n}"})
        return 0

    # shoulder_hair 파트: 가닥 픽셀 + 소프트 페더 (재합성 시 원본과 일치하도록 코어는 불투명)
    a = mask.astype(np.float64) * 255.0
    a = np.maximum(a, blur_f(a, FEATHER))
    shoulder = clothes.copy()
    shoulder[..., 3] = np.clip(a, 0, 255).astype(np.uint8)

    # clothes 재도색: 가닥 주변을 제외한 픽셀로 정규화 블러 필드를 만들어 가닥 영역을 충전
    dil = np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(FILL_DILATE * 2 + 1))) > 0
    valid = (alpha > 100) & (~dil)
    w = valid.astype(np.float64)
    field = np.dstack([blur_f(rgb[..., c] * w, FILL_SIGMA) for c in range(3)])
    norm = blur_f(w, FILL_SIGMA)[..., None]
    field = field / np.maximum(norm, 1e-4)
    filled = clothes.copy()
    fill_region = dil & (alpha > 100)
    filled[..., :3][fill_region] = np.clip(field[fill_region], 0, 255).astype(np.uint8)

    # 재합성 무손실 검사: shoulder over filled ≈ 원본 clothes
    comp = Image.fromarray(filled, "RGBA").copy()
    comp.alpha_composite(Image.fromarray(shoulder, "RGBA"))
    ca = np.asarray(comp).astype(int)
    diff = np.abs(ca[..., :3] - clothes[..., :3].astype(int)).max(-1)
    visible = alpha > 100
    strong = float((diff[visible] > 60).mean())
    mean_delta = float(diff[visible].mean())
    status = "PASS" if strong < 0.005 and mean_delta < 2.0 else "FAIL"

    Image.fromarray(shoulder, "RGBA").save(out / "shoulder_hair.png")
    Image.fromarray(filled, "RGBA").save(out / "clothes_filled.png")
    ys, xs = np.where(mask)
    write_json(out / "shoulder_hair_config.json", {
        "generated_at": now_iso(), "split": True, "pixels": count,
        "bbox": [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1],
        "integrity": {"status": status, "strong_ratio": round(strong, 5), "mean_delta": round(mean_delta, 3)},
        "outputs": [rel(out / "shoulder_hair.png"), rel(out / "clothes_filled.png")],
    })
    print(f"shoulder_hair: {count}px, 재합성 {status} (strong {strong:.4%}, mean {mean_delta:.2f})")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

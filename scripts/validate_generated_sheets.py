#!/usr/bin/env python3
"""시트 P0 검증 (MASTER-SPEC §3.4) — 생성 시트의 셀 동일성·정렬을 결정론적으로 검사.

H1 게이트 앞 자동 필터: 어느 셀이 왜 틀렸는지 지목해 저비용 재생성(장당 ~$0.26)을 돕는다.

검사:
- 공통: 마젠타 배경 비율(콘텐츠 외 영역), 셀별 콘텐츠 존재(점유율 하한/상한)
- eyes(2×3): 셀별 눈 콘텐츠 bbox 폭 편차 < 기준(중앙값) ±10%, 좌우 눈 중심 간격 편차 < 5%
- mouth(2×2): 셀별 입꼬리 x(콘텐츠 bbox 좌/우) 편차 < 입폭(중앙값) 5%
- accent(2×2): 공통 검사만 (오버레이 자산 — 정렬은 부착 시점 결정론)

§3.5 주의: 셀에 얼굴 윤곽선(턱 V)이 딸려오는 것은 추출기가 자동 제거하므로 H1 불합격
사유가 아니다 — 측정은 셀 중앙 70% 창 안의 콘텐츠만 본다 (윤곽 오염 회피).

사용: python3 scripts/validate_generated_sheets.py --sheet <sheet.png> --kind mouth \
        --out-dir experiments/autorig-character-004/reports/sheet_p0
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, now_iso, rel, write_json  # noqa: E402
from run_autorig_sheet_pilot import chroma_alpha  # noqa: E402 — 마젠타 거리 램프 (검증된 단일 원본)

CHROMA = (255, 0, 255)
GRID = {"mouth": (2, 2), "eyes": (2, 3), "accent": (2, 2)}
CENTER_WINDOW = 0.70  # 측정은 셀 중앙 70%만 — 딸려온 얼굴 윤곽 스트로크 오염 회피 (§3.5)
MIN_CONTENT, MAX_CONTENT = 0.005, 0.80
BG_MAGENTA_MIN = 0.30  # 시트 전체에서 마젠타 배경이 차지해야 하는 최소 비율
# MOUTH-SKIN-GATE (005 함정 근본 예방): 입 시트에 얼굴/턱 하관이 그려지면 전경 대부분이
# 살구색 피부가 되고, 추출기의 white(이빨) 분류가 피부를 이빨로 오인해 입이 깨진다(005 사고).
# 시트 단계에서 잡아 재생성을 유도한다. 살구색=따뜻한 색(R-B 큼)으로 무채색 이빨과 구분.
# 표본: 004(살구 입술 60.3%)·005신(검은 입술선 0.3%) PASS / 005구(얼굴 덩어리 93.9%) FAIL.
MAX_SKIN_RATIO = 0.80  # 전경 중 살구색 피부 비율 상한 (mouth 한정)


def cell_content(img: np.ndarray) -> tuple[np.ndarray, tuple[int, int, int, int] | None]:
    """중앙 창 내 콘텐츠 마스크와 bbox(x0,y0,x1,y1 — 창 좌표)."""
    h, w = img.shape[:2]
    mh, mw = int(h * (1 - CENTER_WINDOW) / 2), int(w * (1 - CENTER_WINDOW) / 2)
    window = img[mh:h - mh, mw:w - mw]
    mask = chroma_alpha(window[..., :3], CHROMA) > 0.5
    if not mask.any():
        return mask, None
    ys, xs = np.where(mask)
    return mask, (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def eye_pair_metrics(mask: np.ndarray) -> dict | None:
    """컬럼 점유로 좌/우 눈 분리 — 중앙 갭 기준 두 덩어리의 중심과 전체 폭."""
    cols = mask.sum(axis=0)
    occupied = np.where(cols > 0)[0]
    if occupied.size < 10:
        return None
    mid = (occupied[0] + occupied[-1]) // 2
    left, right = cols[:mid], cols[mid:]
    lo = np.where(left > 0)[0]
    ro = np.where(right > 0)[0] + mid
    if lo.size == 0 or ro.size == 0:
        return None
    l_center = float((lo * left[lo]).sum() / left[lo].sum())
    r_center = float((ro * cols[ro]).sum() / cols[ro].sum())
    return {"width": float(occupied[-1] - occupied[0]), "gap": r_center - l_center}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet", type=Path, required=True)
    parser.add_argument("--kind", choices=list(GRID), required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    sheet_path = args.sheet if args.sheet.is_absolute() else ROOT / args.sheet
    out = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    img = np.asarray(Image.open(sheet_path).convert("RGB"))
    h, w = img.shape[:2]
    rows, cols = GRID[args.kind]
    bg_ratio = float((chroma_alpha(img, CHROMA) < 0.5).mean())  # 마젠타에 가까운 픽셀 비율

    cells, failures = [], []
    if bg_ratio < BG_MAGENTA_MIN:
        failures.append(f"마젠타 배경 비율 {bg_ratio:.2f} < {BG_MAGENTA_MIN} — 크로마 배경 미준수")
    skin_ratio = None
    if args.kind == "mouth":  # MOUTH-SKIN-GATE: 전경 살구색 피부 과다 = 얼굴/턱 그려짐
        fg = chroma_alpha(img, CHROMA) >= 0.5
        rgb = img[fg].astype(int)
        if len(rgb):
            R, G, B, lum = rgb[:, 0], rgb[:, 1], rgb[:, 2], rgb.mean(axis=1)
            skin = (R - B > 15) & (lum >= 150) & (lum <= 248) & (R > G) & (G > B)
            skin_ratio = float(skin.mean())
            if skin_ratio > MAX_SKIN_RATIO:
                failures.append(
                    f"전경 살구색 피부 {skin_ratio:.1%} > {MAX_SKIN_RATIO:.0%} — 입 시트에 얼굴/턱이 "
                    f"그려짐(추출기가 피부를 이빨로 오인). 시트 재생성 필요")
    for r in range(rows):
        for c in range(cols):
            name = f"r{r + 1}c{c + 1}"
            cell = img[r * h // rows:(r + 1) * h // rows, c * w // cols:(c + 1) * w // cols]
            mask, bbox = cell_content(cell)
            ratio = float(mask.mean())
            rec = {"cell": name, "content_ratio": round(ratio, 4)}
            if not (MIN_CONTENT <= ratio <= MAX_CONTENT):
                failures.append(f"{name}: 콘텐츠 점유율 {ratio:.4f} 범위 밖 [{MIN_CONTENT},{MAX_CONTENT}]")
            elif bbox:
                rec["bbox"] = bbox
                rec["bbox_width"] = bbox[2] - bbox[0]
                if args.kind == "eyes":
                    rec["pair"] = eye_pair_metrics(mask)
            cells.append(rec)

    widths = [c["bbox_width"] for c in cells if "bbox_width" in c]
    if args.kind in ("mouth", "eyes") and widths:
        ref_w = float(np.median(widths))
        for c in cells:
            if "bbox_width" not in c:
                continue
            dev = abs(c["bbox_width"] - ref_w) / max(ref_w, 1)
            c["width_dev"] = round(dev, 3)
            if args.kind == "eyes" and dev > 0.10:
                failures.append(f"{c['cell']}: 눈 폭 편차 {dev:.1%} > ±10%")
            if args.kind == "mouth":
                # 입꼬리 x 정렬 — 좌/우 모서리의 셀 간 편차 < 입폭 5%
                c["corners"] = [c["bbox"][0], c["bbox"][2]]
        if args.kind == "mouth":
            for side, idx in (("left", 0), ("right", 1)):
                xs = [c["corners"][idx] for c in cells if "corners" in c]
                if xs and (max(xs) - min(xs)) / max(ref_w, 1) > 0.05:
                    failures.append(f"입꼬리 {side} x 편차 {(max(xs) - min(xs)) / ref_w:.1%} > 5%")
    if args.kind == "eyes":
        gaps = [c["pair"]["gap"] for c in cells if c.get("pair")]
        if gaps:
            ref_gap = float(np.median(gaps))
            for c in cells:
                if not c.get("pair"):
                    continue
                dev = abs(c["pair"]["gap"] - ref_gap) / max(ref_gap, 1)
                if dev > 0.05:
                    failures.append(f"{c['cell']}: 좌우 눈 간격 편차 {dev:.1%} > 5%")

    status = "PASS" if not failures else "FAIL"
    report = {"test_id": "SHEET-P0", "generated_at": now_iso(), "sheet": rel(sheet_path),
              "kind": args.kind, "bg_magenta_ratio": round(bg_ratio, 4),
              "skin_ratio": round(skin_ratio, 4) if skin_ratio is not None else None,
              "cells": cells, "failures": failures, "status": status}
    write_json(out / f"sheet_p0_{args.kind}.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

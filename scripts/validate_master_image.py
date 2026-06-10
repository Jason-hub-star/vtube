#!/usr/bin/env python3
"""P0 마스터 검증 — AUTORIG-MASTER-SPEC 조건의 결정론 검사.

두 모드:
1) 생성 직후:  python3 scripts/validate_master_image.py --master <png>
   해상도/포맷, 인물 bbox 단일성(배경 대비), 상반신 구도 비율.
2) 분해 후:    ... --master <png> --manifest <layer_manifest.json>
   eye/mouth/face/hair/neck 계열 레이어 알파 점유 assert
   (눈없는 마스터·목 레이어 공백 사건의 코드화).
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

MIN_SIZE = 1024
FIGURE_MIN_WIDTH_RATIO = 0.35   # 인물 폭 ≥ 캔버스 35% (상반신 구도)
HEAD_MARGIN_MAX_RATIO = 0.25    # 머리 위 여백 ≤ 25%
BG_DISTANCE = 30                # 배경색 대비 거리 (모서리 중앙값 기준)

# 분해 후 필수 레이어 계열: (라벨, part_id 부분 문자열 후보들, 최소 알파 픽셀)
REQUIRED_LAYER_FAMILIES = [
    ("eyes", ("eye", "iris"), 400),
    ("mouth", ("mouth",), 150),
    ("face", ("face",), 5000),
    ("hair", ("hair",), 5000),
    ("neck", ("neck",), 200),  # 목 공백 사건 — 공백이면 숨은목이 마스터 채취로 폴백되므로 경고 수준
]
WARN_ONLY = {"neck"}


def figure_checks(master: Path) -> list[dict]:
    img = Image.open(master)
    checks = [{"name": "size", "ok": min(img.size) >= MIN_SIZE and img.size[0] == img.size[1],
               "value": list(img.size), "rule": f"정사각 ≥{MIN_SIZE}"}]
    arr = np.asarray(img.convert("RGB")).astype(np.int32)
    h, w = arr.shape[:2]
    corners = np.concatenate([arr[:40, :40].reshape(-1, 3), arr[:40, -40:].reshape(-1, 3),
                              arr[-40:, :40].reshape(-1, 3), arr[-40:, -40:].reshape(-1, 3)])
    bg = np.median(corners, axis=0)
    fg = (np.abs(arr - bg[None, None, :]).sum(axis=2) > BG_DISTANCE)
    ys, xs = np.where(fg)
    if len(xs) == 0:
        checks.append({"name": "figure_present", "ok": False, "value": 0, "rule": "배경 대비 인물 존재"})
        return checks
    fx0, fx1, fy0 = int(xs.min()), int(xs.max()) + 1, int(ys.min())
    width_ratio = (fx1 - fx0) / w
    head_margin = fy0 / h
    # 단일 인물: 인물 컬럼 점유가 중간에 크게 끊기지 않는지 (두 덩어리 감지)
    col_occupied = fg[:, fx0:fx1].any(axis=0)
    gaps = np.where(~col_occupied)[0]
    max_gap = 0
    if len(gaps):
        splits = np.split(gaps, np.where(np.diff(gaps) > 1)[0] + 1)
        max_gap = max(len(s) for s in splits)
    checks += [
        {"name": "figure_width", "ok": width_ratio >= FIGURE_MIN_WIDTH_RATIO,
         "value": round(width_ratio, 3), "rule": f"≥{FIGURE_MIN_WIDTH_RATIO} (상반신 구도)"},
        {"name": "head_margin", "ok": head_margin <= HEAD_MARGIN_MAX_RATIO,
         "value": round(head_margin, 3), "rule": f"≤{HEAD_MARGIN_MAX_RATIO}"},
        {"name": "single_figure", "ok": max_gap < (fx1 - fx0) * 0.18,
         "value": int(max_gap), "rule": "인물 영역 중간 공백 < 폭 18%"},
    ]
    return checks


def layer_checks(manifest_path: Path) -> list[dict]:
    manifest = json.loads(manifest_path.read_text())
    layers = manifest.get("layers", manifest if isinstance(manifest, list) else [])
    checks = []
    for label, needles, min_pixels in REQUIRED_LAYER_FAMILIES:
        total = 0
        for layer in layers:
            pid = layer.get("part_id") or layer.get("original_part_id") or layer.get("role") or ""
            if any(n in pid for n in needles) and "reference" not in pid:
                raw = layer.get("path") or layer.get("output_path") or layer.get("source_path") or ""
                path = Path(raw) if Path(raw).is_absolute() else ROOT / raw
                if path.exists():
                    alpha = np.asarray(Image.open(path).convert("RGBA"))[..., 3]
                    total += int((alpha > 24).sum())
        ok = total >= min_pixels
        checks.append({"name": f"layer_{label}", "ok": ok or label in WARN_ONLY,
                       "warn": (not ok) and label in WARN_ONLY,
                       "value": total, "rule": f"알파 픽셀 ≥{min_pixels}"})
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=None, help="분해 후 layer_manifest.json")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    checks = figure_checks(args.master)
    if args.manifest is not None:
        checks += layer_checks(args.manifest)
    status = "PASS" if all(c["ok"] for c in checks) else "FAIL"
    report = {"generated_at": now_iso(), "master": rel(args.master), "status": status, "checks": checks}
    if args.out:
        write_json(args.out, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

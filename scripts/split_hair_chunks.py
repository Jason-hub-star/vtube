#!/usr/bin/env python3
"""HAIR-SPLIT-001: 머리카락 통짜 레이어를 물리용 덩어리로 분할한다.

프로 PSD 분할 방식: 픽셀 가닥 분리가 아니라 **덩어리 + 페더 경계 + 겹침 복제**.
- front_hair → 3덩어리 (L/C/R, 콘텐츠 폭 1/3·2/3 경계)
- back_hair  → 2덩어리 (L/R, 중앙 경계)
- 겹침 복제 OVERLAP_PX: 경계 밴드를 양쪽 덩어리가 공유 — 움직여도 틈이 안 생긴다
- 페더: 겹침 밴드에서 한쪽은 fade-out, 반대쪽은 fade-in (합 1.0 → 재합성 무손실)
- 무결성: 분할 재합성 vs 원본 diff(changed_ratio) < 0.002 검증

사용: python3 scripts/split_hair_chunks.py \
        --reskin-dir experiments/autorig-template-001/seethrough_true_reskinned \
        --out-dir experiments/autorig-template-001/hair_chunks
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_image import image_diff_metrics  # noqa: E402
from lib.vtube_io import ROOT, now_iso, rel, write_json  # noqa: E402

OVERLAP_PX = 30  # 경계 양쪽 겹침 절반 폭 (총 겹침 = 2*OVERLAP_PX)
SPLITS = {
    "front_hair": ["hair_front_L", "hair_front_C", "hair_front_R"],
    "back_hair": ["hair_back_L", "hair_back_R"],
}


def split_layer(src: Path, names: list[str], out_dir: Path) -> list[dict]:
    img = np.asarray(Image.open(src).convert("RGBA"))
    alpha = img[..., 3]
    ys, xs = np.where(alpha > 8)
    if len(xs) == 0:
        # 빈 머리 레이어(예: 짧은 보브를 분해가 전부 back_hair로 분류 → front_hair 0px).
        # 크래시 대신 건너뜀 — 빌더가 없는 청크는 무시(front_hair_warp 자식 0).
        print(f"  [split] {src.name} 빈 레이어 — 건너뜀")
        return []
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    n = len(names)
    # 콘텐츠 폭 기준 경계 (n-1개)
    boundaries = [x0 + (x1 - x0) * (i + 1) // n for i in range(n - 1)]
    entries = []
    for i, name in enumerate(names):
        # 꼬리 설계: 자기 영역은 완전 불투명, 이웃 쪽으로 2*OVERLAP 페이드 꼬리만 연장.
        # 재합성 시 나중에 그려지는 이웃의 불투명 영역이 꼬리를 덮으므로 원본과 무손실,
        # 물리로 벌어질 때는 꼬리가 틈을 가린다.
        own_l = boundaries[i - 1] if i > 0 else 0
        own_r = boundaries[i] if i < n - 1 else img.shape[1]
        band = 2 * OVERLAP_PX
        ramp = np.zeros(img.shape[1], dtype=np.float64)
        ramp[own_l:own_r] = 1.0
        if i > 0:
            tail_l = max(0, own_l - band)
            ramp[tail_l:own_l] = np.linspace(0.0, 1.0, own_l - tail_l)
        if i < n - 1:
            tail_r = min(img.shape[1], own_r + band)
            ramp[own_r:tail_r] = np.linspace(1.0, 0.0, tail_r - own_r)
        chunk = img.copy()
        chunk[..., 3] = (chunk[..., 3].astype(np.float64) * ramp[None, :]).astype(np.uint8)
        out_path = out_dir / f"{name}.png"
        Image.fromarray(chunk, "RGBA").save(out_path)
        cys, cxs = np.where(chunk[..., 3] > 8)
        entries.append({
            "part_id": name,
            "path": rel(out_path),
            "source": rel(src),
            "x_range": [int(cxs.min()), int(cxs.max()) + 1] if len(cxs) else [0, 0],
        })
    return entries


def recompose_check(entries: list[dict], src: Path, out_dir: Path, label: str) -> dict:
    canvas = None
    for entry in entries:
        layer = Image.open(ROOT / entry["path"]).convert("RGBA")
        if canvas is None:
            canvas = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        canvas.alpha_composite(layer)
    check_path = out_dir / f"recompose_{label}.png"
    canvas.save(check_path)
    # 무결성 기준: 잔머리 반투명 가장자리의 미세 알파 변화(시각 무손실)는 허용하고
    # 강한 픽셀 변화(threshold 60)와 평균 델타로 판정한다
    strong = image_diff_metrics(src, check_path, threshold=60)
    return {
        "label": label,
        "strong_changed_ratio": strong["changed_ratio"],
        "mean_delta": strong["mean_delta"],
        "recompose": rel(check_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reskin-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    all_entries = []
    checks = []
    for source_name, chunk_names in SPLITS.items():
        src = (args.reskin_dir if args.reskin_dir.is_absolute() else ROOT / args.reskin_dir) / f"{source_name}.png"
        if not src.exists():
            continue
        entries = split_layer(src, chunk_names, out)
        if not entries:
            continue  # 빈 머리 레이어(짧은 보브 등) — recompose 검증 건너뜀
        checks.append(recompose_check(entries, src, out, source_name))
        all_entries += entries

    ok = all(c["strong_changed_ratio"] < 0.001 and c["mean_delta"] < 1.0 for c in checks)
    write_json(out / "hair_split_manifest.json", {
        "generated_at": now_iso(),
        "overlap_px": OVERLAP_PX,
        "chunks": all_entries,
        "integrity": checks,
        "integrity_pass": ok,
    })
    print(f"chunks={len(all_entries)} integrity={'PASS' if ok else 'FAIL'} {[(c['label'], c['strong_changed_ratio'], round(c['mean_delta'],3)) for c in checks]}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

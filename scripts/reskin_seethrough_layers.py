#!/usr/bin/env python3
"""See-through 레이어 재스킨: 모양(알파)은 분해 결과, 픽셀은 원본 2048에서 가져온다.

- 안개 제거: 알파 < threshold → 0 (640 추론이 남기는 저알파 베일 제거)
- 픽셀 소유권: 그리기 순서 앞→뒤로 스캔하며 각 픽셀의 소유 레이어를 정한다.
  소유 영역 = 원본 RGB (원본 화질 그대로, 경계 오염 없음 — 소유권이 배타적이므로)
  비소유(가려진) 영역 = 분해 인페인팅 픽셀 유지 (업스케일된 640 화질)
- 산출: <out>/ 에 레이어별 재스킨 PNG + reskin_manifest.json

사용: python3 scripts/reskin_seethrough_layers.py \
        --manifest <layer_manifest.json> --original <2048 png> --out-dir <dir>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_seethrough_psd_candidate import effective_draw_order  # noqa: E402 — 기존 순서 규칙 재사용
from lib.vtube_io import load_json, now_iso, rel, write_json  # noqa: E402

EXTRA_ORDER = {
    "choker": 230, "ear_inner": 605, "earwear": 610, "raw_eyewear": 620,
    "nose_reference": 415, "raw_bottomwear": 205, "raw_legwear": 204, "raw_footwear": 203,
}
EXCLUDE = {"tail_reference", "wings_reference", "object_reference", "headwear_reference"}
HAZE_ALPHA = 28  # 이 미만의 알파는 안개로 보고 제거


def order_of(layer: dict) -> int:
    return EXTRA_ORDER.get(layer["original_part_id"], effective_draw_order(layer))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--haze-alpha", type=int, default=28, help="이 미만 알파는 안개로 제거 (얼룩 시 90 권장)")
    args = parser.parse_args()
    globals()["HAZE_ALPHA"] = args.haze_alpha

    manifest = load_json(args.manifest)
    layers = [l for l in manifest["layers"] if l["original_part_id"] not in EXCLUDE]
    layers.sort(key=order_of)

    original = np.asarray(Image.open(args.original).convert("RGBA"))
    size = original.shape[0]
    claimed = np.zeros((size, size), dtype=bool)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    out_entries = []
    # 앞(위)에서 뒤(아래)로 — 위 레이어가 픽셀을 먼저 소유한다
    loaded = []
    for layer in layers:
        path = Path(layer["output_path"])
        if not path.exists():
            continue
        arr = np.asarray(Image.open(path).convert("RGBA").resize((size, size), Image.LANCZOS)).copy()
        arr[..., 3] = np.where(arr[..., 3] < HAZE_ALPHA, 0, arr[..., 3])  # 안개 제거
        loaded.append((layer, arr))
    for layer, arr in reversed(loaded):  # reversed = 맨 앞 레이어부터
        visible = arr[..., 3] >= HAZE_ALPHA
        own = visible & ~claimed
        claimed |= own
        arr[own, 0:3] = original[own, 0:3]  # 소유 영역은 원본 픽셀
        layer["_own_ratio"] = round(float(own.mean()), 5)

    for layer, arr in loaded:
        out_path = args.out_dir / f"{layer['original_part_id']}.png"
        Image.fromarray(arr, "RGBA").save(out_path)
        out_entries.append(
            {
                "part_id": layer["original_part_id"],
                "path": rel(out_path),
                "draw_order": order_of(layer),
                "own_ratio": layer.get("_own_ratio", 0.0),
            }
        )

    write_json(
        args.out_dir / "reskin_manifest.json",
        {
            "generated_at": now_iso(),
            "source_manifest": rel(args.manifest),
            "original": rel(args.original),
            "haze_alpha": HAZE_ALPHA,
            "layers": out_entries,
        },
    )
    print(f"reskinned {len(out_entries)} layers -> {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

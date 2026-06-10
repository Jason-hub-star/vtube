#!/usr/bin/env python3
"""숨은 목 생성 — 목 분리(머리 이동 시 이음새) 해소의 업계 정석 1단계.

원본 목 레이어 콘텐츠를 가로 1.3×, 위로 +140px 연장한 `neck_under.png`를 만든다.
얼굴 뒤(목 바로 아래 draw order)에 깔리므로, 머리가 어느 방향으로 가도
틈 대신 목 피부가 보인다. 위 연장은 목 상단 행 픽셀의 스트레치(원본 색 보존).

사용: python3 scripts/build_hidden_neck.py \
        --neck experiments/autorig-template-001/seethrough_true_reskinned/neck.png \
        --out-dir experiments/autorig-template-001/hidden_neck
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, now_iso, rel, write_json  # noqa: E402

WIDEN = 1.3
EXTEND_UP_PX = 140


def bbox_of(path: Path) -> tuple[int, int, int, int]:
    alpha = np.asarray(Image.open(path).convert("RGBA"))[..., 3]
    ys, xs = np.where(alpha > 8)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", type=Path, required=True, help="진짜 마스터 2048 — 목 피부의 픽셀 원천")
    parser.add_argument("--mouth-line", type=Path, required=True, help="턱선 y 측정 기준")
    parser.add_argument("--clothes", type=Path, required=True, help="옷깃 상단 y 기준")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    master = np.asarray(Image.open(args.master).convert("RGBA"))
    mx0, my0, mx1, my1 = bbox_of(args.mouth_line)
    mouth_w = mx1 - mx0
    mouth_cx = (mx0 + mx1) / 2
    # 턱선 y: 입 아래 중앙 컬럼 최암부 (extract_mouth_states와 동일 측정)
    search = master[int(my1 + 12) : int(my1 + mouth_w), int(mouth_cx - mouth_w * 0.25) : int(mouth_cx + mouth_w * 0.25), :3]
    chin_line_y = int(my1 + 12 + int(np.argmin(search.mean(axis=(1, 2)))))
    _, cy0, _, _ = bbox_of(args.clothes)
    # 목 피부 사각형: 턱선 약간 위 ~ 옷깃 살짝 아래, 폭 = 입폭 × 1.3 (분해에서 목 레이어가 비어 마스터에서 직접 채취)
    y0 = max(0, chin_line_y - 12)
    y1 = min(master.shape[0], cy0 + 40)
    half_w = round(mouth_w * 0.65)
    x0 = int(mouth_cx - half_w)
    x1 = int(mouth_cx + half_w)
    region = master[y0:y1, x0:x1].copy()
    region[..., 3] = 255
    crop = Image.fromarray(region, "RGBA")

    # 가로 확장
    new_w = round(crop.width * WIDEN)
    widened = crop.resize((new_w, crop.height), Image.LANCZOS)

    # 위 연장: 상단 8행을 평균낸 띠를 위로 스트레치 (원본 피부색 보존)
    arr = np.asarray(widened)
    top_band = arr[: min(8, arr.shape[0])].astype(np.float64).mean(axis=0).astype(np.uint8)
    extension = np.tile(top_band[None, :, :], (EXTEND_UP_PX, 1, 1))
    extended = np.vstack([extension, arr])

    canvas = Image.new("RGBA", (master.shape[1], master.shape[0]), (0, 0, 0, 0))
    cx = (x0 + x1) / 2
    canvas.alpha_composite(Image.fromarray(extended, "RGBA"), (round(cx - new_w / 2), y0 - EXTEND_UP_PX))
    out_path = out / "neck_under.png"
    canvas.save(out_path)

    write_json(out / "hidden_neck_config.json", {
        "generated_at": now_iso(),
        "source": rel(args.master),
        "widen": WIDEN,
        "extend_up_px": EXTEND_UP_PX,
        "output": rel(out_path),
    })
    print(f"hidden neck: {rel(out_path)} (w x{WIDEN}, up +{EXTEND_UP_PX}px)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

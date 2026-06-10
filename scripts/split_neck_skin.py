#!/usr/bin/env python3
"""목 피부 분리 — 분해가 목을 clothes에 합쳐놓은 경우, 목 기둥을 잘라 별도 파트로.

프로 리깅 정석: 턱(머리 100%) → 목(부분 추종) → 가슴(고정)의 3단 그라데이션은
목이 별도 파트일 때만 가능하다. 머리 분할에서 검증한 "불투명 자기영역 + 페이드
꼬리" 기법을 세로로 적용: neck_skin은 아래로, clothes는 위로 꼬리를 남겨
재합성 무손실 + 움직일 때 틈 없음.

사용: python3 scripts/split_neck_skin.py \
        --clothes <reskinned clothes.png> --mouth-line <mouth_line.png> \
        --master <master.png> --out-dir <dir>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, now_iso, rel, write_json  # noqa: E402

NECK_HEIGHT_PX = 130   # 턱선 아래 목 기둥 높이 (이 아래는 가슴 = clothes 잔류)
NECK_HALF_W_RATIO = 0.85  # 입폭 대비 목 반폭 (목 측면 윤곽 포함하도록 넉넉히)
TAIL_PX = 28           # 세로 꼬리 (틈 커버)


def bbox_of(path: Path) -> tuple[int, int, int, int]:
    alpha = np.asarray(Image.open(path).convert("RGBA"))[..., 3]
    ys, xs = np.where(alpha > 8)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clothes", type=Path, required=True)
    parser.add_argument("--mouth-line", type=Path, required=True)
    parser.add_argument("--master", type=Path, required=True, help="턱선 측정용")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    clothes = np.asarray(Image.open(args.clothes).convert("RGBA")).copy()
    master = np.asarray(Image.open(args.master).convert("RGBA"))
    mx0, my0, mx1, my1 = bbox_of(args.mouth_line)
    mouth_w = mx1 - mx0
    mouth_cx = (mx0 + mx1) / 2
    search = master[int(my1 + 12) : int(my1 + mouth_w), int(mouth_cx - mouth_w * 0.25) : int(mouth_cx + mouth_w * 0.25), :3]
    chin_line_y = int(my1 + 12 + int(np.argmin(search.mean(axis=(1, 2)))))

    cut_y = chin_line_y + NECK_HEIGHT_PX  # 목/가슴 경계
    half_w = round(mouth_w * NECK_HALF_W_RATIO)
    x0 = int(mouth_cx - half_w)
    x1 = int(mouth_cx + half_w)

    h, w = clothes.shape[:2]
    # 목 기둥 마스크 (x 양측은 페더)
    col = np.zeros(w)
    col[x0:x1] = 1.0
    fx = min(24, half_w)
    col[x0 : x0 + fx] = np.linspace(0, 1, fx)
    col[x1 - fx : x1] = np.linspace(1, 0, fx)
    # 세로: neck_skin = cut_y 위 불투명 + 아래로 TAIL 페이드 / clothes = cut_y 아래 불투명 + 위로 TAIL 페이드
    row_neck = np.zeros(h)
    row_neck[:cut_y] = 1.0
    row_neck[cut_y : cut_y + TAIL_PX] = np.linspace(1, 0, TAIL_PX)
    row_clothes = 1.0 - np.clip(row_neck, 0, 1) * col.max()  # placeholder, 실제는 2D로 계산

    neck_w_mask = row_neck[:, None] * col[None, :]
    neck_skin = clothes.copy()
    neck_skin[..., 3] = (neck_skin[..., 3] * neck_w_mask).astype(np.uint8)
    # clothes 잔류분: 목 기둥 영역에서 neck이 가져간 만큼 빼되, 위로 꼬리 유지
    row_cl = np.ones(h)
    row_cl[: cut_y - TAIL_PX] = 0.0
    row_cl[cut_y - TAIL_PX : cut_y] = np.linspace(0, 1, TAIL_PX)
    clothes_keep = 1.0 - col[None, :] * (1.0 - row_cl[:, None])
    clothes_out = clothes.copy()
    clothes_out[..., 3] = (clothes_out[..., 3] * clothes_keep).astype(np.uint8)

    Image.fromarray(neck_skin, "RGBA").save(out / "neck_skin.png")
    Image.fromarray(clothes_out, "RGBA").save(out / "clothes_trimmed.png")

    write_json(out / "neck_split_config.json", {
        "generated_at": now_iso(),
        "chin_line_y": chin_line_y, "cut_y": cut_y, "x_range": [x0, x1],
        "neck_height_px": NECK_HEIGHT_PX, "tail_px": TAIL_PX,
        "outputs": [rel(out / "neck_skin.png"), rel(out / "clothes_trimmed.png")],
    })
    a = neck_skin[..., 3]
    print(f"neck_skin: 알파픽셀 {int((a > 24).sum())}, cut_y={cut_y}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

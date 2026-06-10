#!/usr/bin/env python3
"""입 내부(동일세션 시트의 interior 셀)를 원본 입라인 기준으로 추출·배치한다.

(자기리뷰에서 발견된 재현성 구멍 봉합 — 이전엔 인라인 매직넘버로 수행되던 단계)
산출: <out-dir>/mouth_interior.png — 입 워프 베이크의 internals 입력.

사용: python3 scripts/place_mouth_interior.py \
        --sheet experiments/autorig-template-001/raw_sheets/mouth_states_true.png \
        --out-dir experiments/autorig-template-001/mouth_interior_true
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, now_iso, rel, write_json  # noqa: E402
from run_autorig_sheet_pilot import chroma_alpha, despill  # noqa: E402
from run_mouth_open_experiment import bbox_of  # noqa: E402

DEFAULT_CELL = "1024,2048,1024,2048"  # 시트의 interior 단독 셀 (2,2) — y0,y1,x0,x1
WIDTH_FACTOR = 0.98                   # 원본 입 폭 대비 내부 폭
TOP_OFFSET_RATIO = -0.33              # 입라인 높이 대비 상단 오프셋 (002 실측 -16px/48px — 캐릭터 무관 비율)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet", type=Path, required=True)
    parser.add_argument("--mouth-line", type=Path, default=ROOT / "experiments/autorig-template-001/seethrough_true_reskinned/mouth_line.png")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--cell", default=DEFAULT_CELL, help="interior 셀 y0,y1,x0,x1 (시트 규격 변경 시)")
    parser.add_argument("--top-offset-ratio", type=float, default=TOP_OFFSET_RATIO)
    args = parser.parse_args()
    out = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    sheet = np.asarray(Image.open(args.sheet).convert("RGB").resize((2048, 2048), Image.LANCZOS))
    y0, y1, x0, x1 = (int(v) for v in args.cell.split(","))
    cell = sheet[y0:y1, x0:x1]
    alpha = chroma_alpha(cell, (255, 0, 255))
    mask = alpha > 0.5
    ys, xs = np.where(mask)
    rgba = np.dstack([despill(cell), (alpha * 255).astype(np.uint8)])[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
    part = Image.fromarray(rgba, "RGBA")

    mx0, my0, mx1, my1 = bbox_of(args.mouth_line)
    mouth_w = mx1 - mx0
    mouth_h = max(my1 - my0, 1)
    lip_y = (my0 + my1) // 2
    top_offset = round(mouth_h * args.top_offset_ratio)  # 입 크기 비율 — 캐릭터 무관
    tw = round(mouth_w * WIDTH_FACTOR)
    part = part.resize((tw, round(part.height * tw / part.width)), Image.LANCZOS)
    canvas = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    canvas.alpha_composite(part, (round((mx0 + mx1) / 2 - part.width / 2), lip_y + top_offset))
    out_path = out / "mouth_interior.png"
    canvas.save(out_path)

    write_json(out / "mouth_interior_config.json", {
        "generated_at": now_iso(),
        "sheet": rel(args.sheet),
        "cell": args.cell,
        "width_factor": WIDTH_FACTOR,
        "top_offset_ratio": args.top_offset_ratio,
        "top_offset_px": top_offset,
        "output": rel(out_path),
    })
    print(f"interior: {rel(out_path)} ({part.size})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

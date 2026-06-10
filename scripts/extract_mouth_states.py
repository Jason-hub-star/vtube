#!/usr/bin/env python3
"""v21 최종 입 성공패턴용 상태 스프라이트 추출: 4상태 시트 → 풀캔버스 레이어 4장.

- 2x2 시트에서 closed/small/mid/wide 패치 추출 (크로마 제거 + despill)
- 패치 경계 페더링 (얼굴 피부에 녹아들게)
- 4장 모두 동일 변환으로 원본 mouth_line에 정렬 (상태 간 정합 유지)
사용: python3 scripts/extract_mouth_states.py --sheet <png> --out-dir <dir>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, now_iso, rel, write_json  # noqa: E402
from run_autorig_sheet_pilot import chroma_alpha, despill  # noqa: E402
from run_mouth_open_experiment import bbox_of  # noqa: E402

STATES = [("closed", 0, 0), ("small", 0, 1), ("mid", 1, 0), ("wide", 1, 1)]
LIP_WIDTH_IN_PATCH = 0.65   # (트림 후) 패치 폭 대비 입술 폭 추정
LIP_Y_IN_PATCH = 0.17       # (트림 후) 패치 높이 대비 입라인 위치 추정
SCALE_MARGIN = 1.06
FEATHER_PX = 18
TRIM_TOP = 0.30             # 패치 상단 피부(코 근처) 잘라내기 — 경계 띠가 얼굴을 가로지르지 않게
TRIM_SIDE = 0.10


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet", type=Path, required=True)
    parser.add_argument("--mouth-line", type=Path, default=ROOT / "experiments/autorig-template-001/seethrough_true_reskinned/mouth_line.png")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    sheet = np.asarray(Image.open(args.sheet).convert("RGB").resize((2048, 2048), Image.LANCZOS))
    mx0, my0, mx1, my1 = bbox_of(args.mouth_line)
    mouth_w = mx1 - mx0
    mouth_cx = (mx0 + mx1) / 2
    lip_y = (my0 + my1) / 2

    # 톤 매칭 기준: 원본 조립의 입 주변 피부색 (턱 위 좁은 밴드)
    assembly = np.asarray(
        Image.open(ROOT / "experiments/autorig-template-001/reports/full_assembly/hybrid_true_origeyes.png").convert("RGB")
    )
    skin_band = assembly[int(my1 + 8) : int(my1 + 30), int(mx0) : int(mx1)].reshape(-1, 3)
    face_skin = np.median(skin_band, axis=0)

    written = []
    shared = None  # 첫 상태(closed)의 변환을 전 상태에 공유 — 상태 간 정합
    for name, row, col in STATES:
        cell = sheet[row * 1024 : (row + 1) * 1024, col * 1024 : (col + 1) * 1024]
        alpha = chroma_alpha(cell, (255, 0, 255))
        mask = alpha > 0.5
        ys, xs = np.where(mask)
        x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
        rgba = np.dstack([despill(cell), (alpha * 255).astype(np.uint8)])[y0:y1, x0:x1]
        # 입 중심으로 트림 (생성 피부가 얼굴을 넓게 덮지 않도록)
        ph, pw = rgba.shape[:2]
        rgba = rgba[int(ph * TRIM_TOP) :, int(pw * TRIM_SIDE) : int(pw * (1 - TRIM_SIDE))]
        # 톤 매칭: 패치 피부색(상단 모서리 밴드 중앙값)을 원본 피부색에 정합 — 턱 이중톤 제거
        corner = rgba[: max(6, rgba.shape[0] // 10), :, :3].reshape(-1, 3).astype(np.float64)
        patch_skin = np.median(corner, axis=0)
        gain = np.clip(face_skin / np.maximum(patch_skin, 1.0), 0.85, 1.18)
        rgba = rgba.copy()
        rgba[..., :3] = np.clip(rgba[..., :3].astype(np.float64) * gain, 0, 255).astype(np.uint8)
        patch = Image.fromarray(rgba, "RGBA")
        # 페더: 알파를 블러한 값과 min — 경계가 피부로 녹아든다
        a = patch.getchannel("A")
        blurred = a.filter(ImageFilter.GaussianBlur(FEATHER_PX))
        patch.putalpha(Image.fromarray(np.minimum(np.asarray(a), np.asarray(blurred))))
        if shared is None:
            scale = (mouth_w * SCALE_MARGIN) / (patch.width * LIP_WIDTH_IN_PATCH)
            shared = {"scale": scale, "ref_w": patch.width, "ref_h": patch.height}
        scale = shared["scale"]
        new_size = (round(patch.width * scale), round(patch.height * scale))
        patch = patch.resize(new_size, Image.LANCZOS)
        canvas = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
        px = round(mouth_cx - patch.width / 2)
        py = round(lip_y - patch.height * LIP_Y_IN_PATCH)
        canvas.alpha_composite(patch, (px, py))
        path = out / f"mouth_state_{name}.png"
        canvas.save(path)
        written.append(path.name)

    write_json(out / "mouth_states_config.json", {
        "generated_at": now_iso(),
        "sheet": rel(args.sheet),
        "lip_width_in_patch": LIP_WIDTH_IN_PATCH,
        "lip_y_in_patch": LIP_Y_IN_PATCH,
        "scale_margin": SCALE_MARGIN,
        "feather_px": FEATHER_PX,
        "written": written,
    })
    print(f"states: {written} -> {rel(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
SCALE_MARGIN = 0.97         # v21 교훈: wide-open 절제 — 활짝 입이 턱선을 침범하지 않게
CHIN_GUARD_PX = 6           # 턱선 위 보호 마진 (이 아래로는 패치 알파 강제 0)
FEATHER_PX = 18
TRIM_TOP = 0.30             # 패치 상단 피부(코 근처) 잘라내기 — 경계 띠가 얼굴을 가로지르지 않게
TRIM_SIDE = 0.10
FADE_BOTTOM_START = 0.60    # (트림 후 높이 비율) 여기부터 알파 페이드 — 원본 턱선이 비치게
FADE_BOTTOM_FULL = 0.82     # 여기서 완전 투명


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet", type=Path, required=True)
    parser.add_argument("--mouth-line", type=Path, default=ROOT / "experiments/autorig-template-001/seethrough_true_reskinned/mouth_line.png")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--assembly", type=Path,
                        default=ROOT / "experiments/autorig-template-001/reports/full_assembly/hybrid_true_origeyes.png",
                        help="중립 어셈블리 — 톤매칭 피부 샘플·턱선 측정 기준 (캐릭터별 교체)")
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
        Image.open(args.assembly).convert("RGB")
    )
    skin_band = assembly[int(my1 + 8) : int(my1 + 30), int(mx0) : int(mx1)].reshape(-1, 3)
    face_skin = np.median(skin_band, axis=0)

    # 원본 턱선(검은 스트로크) y 측정: 입 아래 중앙 컬럼들에서 가장 어두운 행
    search = assembly[int(my1 + 12) : int(my1 + mouth_w), int(mouth_cx - mouth_w * 0.25) : int(mouth_cx + mouth_w * 0.25)]
    lum = search.mean(axis=(1, 2))
    chin_line_y = int(my1 + 12 + int(np.argmin(lum)))
    print(f"chin line y = {chin_line_y} (입라인 {int(lip_y)}, 보호 컷 {chin_line_y - CHIN_GUARD_PX})")

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
        # 하단 페이드 (적응형): 이 상태의 입술/내부 콘텐츠 실제 하단을 측정해
        # 그 바로 아래부터 투명화 — 피부는 최소만 남기고 원본 턱선을 살린다
        fh, fw = rgba.shape[:2]
        skin_med = np.median(rgba[: max(6, fh // 10), :, :3].reshape(-1, 3).astype(np.float64), axis=0)
        dist = np.sqrt(((rgba[..., :3].astype(np.float64) - skin_med) ** 2).sum(axis=-1))
        content = (dist > 48) & (rgba[..., 3] > 64)
        # 입술 성분 분리 (003 이중 턱선 V 사건): 생성 셀마다 캐릭터 얼굴 윤곽 V 스트로크가
        # 통째로 딸려 들어오는데, 입술 블롭과는 항상 "분리된 연결 성분"이다 — 중앙 시드에서
        # flood-grow한 성분만 입술 콘텐츠로 인정한다. (행 갭·폭 프로파일·컬럼 컷은 전부 실패:
        # V팔은 대각이라 행이 연속이고, 아펙스는 수평이라 행 폭이 넓다)
        content[0, :] = content[-1, :] = content[:, 0] = content[:, -1] = False  # roll 랩 누설 가드
        seed = np.zeros_like(content)
        seed[: int(fh * 0.75), int(fw * 0.40) : int(fw * 0.60)] = content[: int(fh * 0.75), int(fw * 0.40) : int(fw * 0.60)]
        grown = seed
        while True:
            nxt = (grown | np.roll(grown, 1, 0) | np.roll(grown, -1, 0) | np.roll(grown, 1, 1) | np.roll(grown, -1, 1)) & content
            if nxt.sum() == grown.sum():
                break
            grown = nxt
        if grown[:, 1].any() or grown[:, -2].any():
            print(f"[warn] {name}: 입술 성분이 패치 가장자리에 닿음 — 윤곽 스트로크 누설 의심")
        rows = np.where(grown[:, int(fw * 0.2) : int(fw * 0.8)].any(axis=1))[0]
        lip_top = int(rows.min()) if len(rows) else int(fh * 0.15)
        lip_bottom = int(rows.max()) if len(rows) else int(fh * 0.55)
        below = np.where(content[:, int(fw * 0.2) : int(fw * 0.8)].any(axis=1))[0]
        below = below[below > lip_bottom + 3]
        stroke_top = int(below.min()) if len(below) else None  # 윤곽 스트로크 시작 — 하단 페이드 클램프용
        cols = np.where(grown[lip_top : lip_bottom + 1].any(axis=0))[0]
        lip_x0 = int(cols.min()) if len(cols) else int(fw * 0.2)
        lip_x1 = int(cols.max()) if len(cols) else int(fw * 0.8)

        def ramp_1d(size: int, keep0: int, keep1: int, soft: int, soft_end: int | None = None) -> np.ndarray:
            r = np.zeros(size, dtype=np.float64)
            r[max(0, keep0) : min(size, keep1)] = 1.0
            a0 = max(0, keep0 - soft)
            if keep0 > a0:
                r[a0:keep0] = np.linspace(0.0, 1.0, keep0 - a0)
            b1 = min(size, keep1 + (soft if soft_end is None else soft_end))
            if b1 > keep1:
                r[keep1:b1] = np.linspace(1.0, 0.0, b1 - keep1)
            return r

        # 사방 밀착: 입술 콘텐츠 + 최소 마진만 불투명, 그 밖은 짧은 페이드 (원본 턱선·뺨·인중 노출)
        # 패치 내 턱선이 검출됐으면 하단 페이드가 그 위에서 완전히 끝나도록 소프트 길이 클램프
        soft_bottom = max(8, fh // 20)
        if stroke_top is not None:
            soft_bottom = max(3, min(soft_bottom, stroke_top - (lip_bottom + 3) - 4))
        ry = ramp_1d(fh, lip_top - max(6, fh // 30), lip_bottom + 3, max(8, fh // 20), soft_bottom)
        rx = ramp_1d(fw, lip_x0 - 8, lip_x1 + 8, 16)
        rgba[..., 3] = (rgba[..., 3].astype(np.float64) * ry[:, None] * rx[None, :]).astype(np.uint8)
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
        # 턱선 보호: 턱선 위 가드라인 아래는 어떤 상태든 알파 강제 0 (10px 페더)
        arr = np.asarray(canvas).copy()
        guard = chin_line_y - CHIN_GUARD_PX
        fade = np.ones(2048, dtype=np.float64)
        fade[max(0, guard - 10) : guard] = np.linspace(1.0, 0.0, guard - max(0, guard - 10))
        fade[guard:] = 0.0
        arr[..., 3] = (arr[..., 3].astype(np.float64) * fade[:, None]).astype(np.uint8)
        canvas = Image.fromarray(arr, "RGBA")
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

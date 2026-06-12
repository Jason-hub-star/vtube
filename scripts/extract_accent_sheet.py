#!/usr/bin/env python3
"""액센트 시트(2×2: blush/gloom/tear/sweat) → 어셈블리 정렬 오버레이 4장 (004 사이클).

오버레이 자산이라 정렬은 부착 시점 결정론 — 원본 눈/얼굴/입 bbox 실측에서
파생한 배치 공식(볼=눈 아래, 그늘=이마, 눈물=눈꼬리, 땀=관자놀이)으로 스케일·배치.
프리셋 품질은 H2 육안 게이트가 판정.

사용: python3 scripts/extract_accent_sheet.py --sheet <accent.png> \
        --reskin-dir <seethrough_true_reskinned> --out-dir <dir>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.sheet_overlay import (  # noqa: E402
    cell_content, cell_of, half_centers, layer_bbox, load_sheet, mask_bbox, place_content,
)
from lib.vtube_io import ROOT, now_iso, rel, write_json  # noqa: E402

# MASTER-SPEC §3.3 셀 배치 (row, col)
ACCENTS = [("blush", 0, 0), ("gloom", 0, 1), ("tear", 1, 0), ("sweat", 1, 1)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet", type=Path, required=True)
    parser.add_argument("--reskin-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    # 기준 기하 (전부 원본 레이어 알파 실측)
    eyes = sorted(layer_bbox(args.reskin_dir / f"{s}_eye_white.png") for s in ("L", "R"))
    eye_centers = [((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) for b in eyes]
    eye_span = eye_centers[1][0] - eye_centers[0][0]
    eye_h = max(b[3] - b[1] for b in eyes)
    eye_bottom = max(b[3] for b in eyes)
    eye_top = min(b[1] for b in eyes)
    eye_w = max(b[2] - b[0] for b in eyes)
    face = layer_bbox(args.reskin_dir / "face_base.png")
    face_cx, face_w = (face[0] + face[2]) / 2, face[2] - face[0]
    mouth = layer_bbox(args.reskin_dir / "mouth_line.png")
    # 볼 라인: 눈 아래 60% 지점 (눈 침범·입 접촉 둘 다 회피 — 004 실측 보정)
    cheek_y = eye_bottom + 0.60 * (mouth[1] - eye_bottom)
    brow_top = min(layer_bbox(args.reskin_dir / f"{s}_brow.png")[1] for s in ("L", "R"))
    outer_eye = eyes[1]  # 뷰어 우측 눈 — 눈물/땀 부착측

    sheet = load_sheet(args.sheet)
    written, placements = [], {}

    def extract(name: str, row: int, col: int):
        cell = cell_of(sheet, row, col, rows=2, cols=2)
        rgba, mask = cell_content(cell)
        if mask is None:
            raise SystemExit(f"{name}: 셀에 콘텐츠 없음")
        return rgba, mask

    for name, row, col in ACCENTS:
        rgba, mask = extract(name, row, col)
        x0, y0, x1, y1 = mask_bbox(mask)
        crop = rgba[y0:y1, x0:x1]
        ch, cw = crop.shape[:2]
        if name == "blush":
            # 볼 패치를 좌/우 따로 각 눈 중심 x의 볼 라인에 배치 (쌍 간격 매핑은 패치가
            # 세로로 길어 눈을 침범 — 004 1차 합성 판정). 폭 = 눈 폭 95%, 공통 스케일.
            mid = (x0 + x1) // 2
            halves = []
            for sl in (mask[:, :mid], mask[:, mid:]):
                if not sl.any():
                    raise SystemExit("blush: 좌/우 분리 실패")
            scale = None
            overlay = None
            for side, (hx0, hx1) in enumerate(((x0, mid), (mid, x1))):
                part = mask[:, hx0:hx1]
                px0, py0, px1, py1 = mask_bbox(part)
                patch = rgba[py0:py1, hx0 + px0 : hx0 + px1]
                if scale is None:
                    scale = (eye_w * 0.95) / patch.shape[1]
                ph, pw = patch.shape[:2]
                piece = place_content(patch, scale, (pw / 2, ph / 2), (eye_centers[side][0], cheek_y))
                if overlay is None:
                    overlay = piece
                else:
                    overlay.alpha_composite(piece)
            path = out / f"accent_{name}.png"
            overlay.save(path)
            written.append(path.name)
            placements[name] = {"scale": round(scale, 4), "dst": [round(eye_centers[0][0]), round(cheek_y)]}
            print(f"{name}: scale {scale:.3f} dst {placements[name]['dst']}")
            continue
        if name == "gloom":
            # 이마 그늘: 머리 꼭대기부터 눈 위 1/3까지 드리움 (오버레이 — 머리 위 draw order)
            dst = (face_cx, face[1] + 0.02 * (face[3] - face[1]))
            scale = max((eye_top + 0.35 * eye_h - dst[1]) / ch, 0.05)
            src = (cw / 2, 0.0)
        elif name == "tear":
            # 눈물: 높이 = 눈높이 180% (실물감), 바깥 눈꼬리 아래
            scale = (eye_h * 1.8) / ch
            src = (cw / 2, 0.0)
            dst = (outer_eye[2] - 0.1 * (outer_eye[2] - outer_eye[0]), eye_bottom - 0.1 * eye_h)
        else:  # sweat
            # 땀방울: 높이 = 눈높이 120%, 관자놀이 (눈썹 높이, 얼굴 가장자리 안쪽)
            scale = (eye_h * 1.2) / ch
            src = (cw / 2, 0.0)
            dst = (face[2] - 0.04 * face_w, brow_top - 0.5 * eye_h)
        overlay = place_content(crop, scale, src, dst)
        path = out / f"accent_{name}.png"
        overlay.save(path)
        written.append(path.name)
        placements[name] = {"scale": round(scale, 4), "dst": [round(dst[0]), round(dst[1])]}
        print(f"{name}: scale {scale:.3f} dst {placements[name]['dst']}")

    write_json(out / "accent_manifest.json", {
        "generated_at": now_iso(), "sheet": rel(args.sheet),
        "accents": [n for n, _, _ in ACCENTS], "placements": placements, "written": written,
    })
    print(f"accent: {len(written)}장 -> {rel(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

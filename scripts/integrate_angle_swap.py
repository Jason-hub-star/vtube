#!/usr/bin/env python3
"""각도 작화를 본체 위벨 리그에 비파괴 통합 (ANGLE-SWAP-002).

원본 rig_v0_project(50파트·표정·입)를 통째 복사해 rig_v0_angle_project를 만들고,
좌4+우4 각도 작화 sprite를 주입한다. ParamAngleX를 ±80으로 넓혀:
  - 중앙 라이브 밴드(|X|≤14): 기존 50파트(표정·입·의사3D 메시)가 그대로 작동
  - 외곽 작화 밴드(16~80): 각도 작화로 하드 스왑, 라이브 리그는 페이드 0
rig.js partOpacity가 파트별 곡선을 곱하므로(L194), 라이브 파트에 ParamAngleX
크로스페이드 곡선 1개씩 더해도 기존 표정/입 곡선과 충돌 없이 곱셈 합성된다.

런타임 코드 변경 0 — sprite 폴백(draw_pixi)·임의 파라미터 opacity 곡선(rig.js) 재사용.

사용: python3 scripts/integrate_angle_swap.py \
        --src experiments/autorig-character-004/rig_v0_project \
        --angle-parts experiments/autorig-character-004/angle_swap_project/parts \
        --out experiments/autorig-character-004/rig_v0_angle_project
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import numpy as np
import scipy.ndimage as ndi
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.rig_keyforms import curve  # noqa: E402
from lib.rig_mesh import alpha_stats  # noqa: E402
from lib.sheet_overlay import place_content  # noqa: E402
from lib.vtube_io import ROOT, load_json, now_iso, write_json  # noqa: E402

CANVAS = 2048
HEAD_BAND_PX = 220        # 머리꼭대기 아래 절대 밴드(머리 폭/중심 실측용)
MIN_COMPONENT_RATIO = 0.05  # 최대 컴포넌트 대비 이 비율 미만 알파 덩어리는 제거(유령 파편)
ANGLE_MAX = 80.0          # 완전 측면 (정면=0). 좌=-, 우=+
# 라이브 변형 리그(본체 메시 ParamAngleX 키폼 ±30)를 풀범위로 살림 — 평소 회전=살아있는
# 변형+표정. 작화는 메시가 못 가는 극단(±34 너머)에만. 사진스왑 체감 최소화.
LIVE_FULL = 26.0          # 라이브 풀가시 반폭 (|X|≤26 → 메시 변형+표정 라이브)
LIVE_FADE = 34.0          # 이 너머 라이브 0 → 작화가 받음
EPS = 1.5                 # 밴드 경계 램프(도)
# 작화: 극단 각도만 (40/60/80°). 밴드 경계(절대각): 라이브↔a2=34, a2↔a3=50, a3↔a4=66, a4=80
ARTWORK_ANGLES = [2, 3, 4]            # a1(20°)은 라이브 메시가 커버 → 작화 미사용
ARTWORK_EDGES = [LIVE_FADE, 50.0, 66.0, ANGLE_MAX]
ANGLE_DRAW_BASE = 800     # 본체 top draw_order(712)보다 위 → 옆모습이 정면 위에 덮임


def live_crossfade_curve(pid: str) -> dict:
    """라이브 파트: 중앙 ±LIVE_FULL 풀가시, ±LIVE_FADE에서 0 (양방향 대칭)."""
    f, z = LIVE_FULL, LIVE_FADE
    pts = [(-ANGLE_MAX, 0.0), (-z, 0.0), (-f, 1.0),
           (f, 1.0), (z, 0.0), (ANGLE_MAX, 0.0)]
    return curve(pid, "ParamAngleX", pts)


def band_curve(pid: str, lo: float, hi: float) -> dict:
    """작화 파트: |X|∈[lo,hi]에서만 표시 (하드 밴드, 입 4상태 스냅 패턴)."""
    pts = {-ANGLE_MAX: 0.0, ANGLE_MAX: 0.0}
    if lo - EPS > -ANGLE_MAX:
        pts.setdefault(lo - EPS, 0.0)
    pts[lo] = 1.0
    pts[hi] = 1.0
    if hi + EPS < ANGLE_MAX:
        pts.setdefault(hi + EPS, 0.0)
    return curve(pid, "ParamAngleX", sorted(pts.items()))


def head_anchor_and_width(alpha: np.ndarray) -> tuple[float, float, int]:
    """인물 머리꼭대기 중심(x)·top(y) + 절대 밴드 머리 폭."""
    ys, xs = np.where(alpha > 128)
    y0 = int(ys.min())
    band = ys < y0 + HEAD_BAND_PX
    cx = float(xs[band].mean())
    bx = xs[band]
    return cx, float(y0), int(bx.max() - bx.min())


def clean_small_components(alpha: np.ndarray) -> np.ndarray:
    """최대 컴포넌트 대비 MIN_COMPONENT_RATIO 미만 알파 덩어리 제거(유령 파편)."""
    labels, n = ndi.label(alpha > 128)
    if n <= 1:
        return alpha
    sizes = ndi.sum(np.ones_like(labels), labels, index=range(1, n + 1))
    keep = {i + 1 for i, s in enumerate(sizes) if s >= sizes.max() * MIN_COMPONENT_RATIO}
    mask = np.isin(labels, list(keep))
    return (alpha * mask).astype(np.uint8)


def align_angle_png(src: Path, scale: float, dst_anchor: tuple[float, float]) -> Image.Image:
    """작화 PNG: 작은 파편 제거 + 머리앵커를 본체 dst_anchor에 scale 맞춰 재배치."""
    img = np.array(Image.open(src).convert("RGBA"))
    img[..., 3] = clean_small_components(img[..., 3])
    cx, top, _ = head_anchor_and_width(img[..., 3])
    return place_content(img, scale, (cx, top), dst_anchor, canvas=CANVAS)


def build_angle_parts(angle_parts_dir: Path, out_parts: Path,
                      scale: float, dst_anchor: tuple[float, float]) -> tuple[list, list, list]:
    """극단 각도 작화(좌 a2..a4 + 우 미러)만 sprite 파트로. a1(20°)은 라이브 메시가 커버.
    각 작화를 본체 머리 앵커·크기에 정렬하고 유령 파편 제거 후 ±34 너머 밴드에 배치."""
    parts, meshes, opacity = [], [], []
    order = ANGLE_DRAW_BASE
    # (접두, 부호, 소스파일포맷)
    sides = [("angle_left", -1.0, "head_angle_{}.png"),
             ("angle_right", +1.0, "head_angle_right_{}.png")]
    for prefix, sign, fmt in sides:
        for j, k in enumerate(ARTWORK_ANGLES):  # a2,a3,a4 → 밴드 슬롯 0,1,2
            src = angle_parts_dir / fmt.format(k)
            if not src.exists():
                raise SystemExit(f"각도 작화 없음: {src} — extract/mirror 먼저")
            pid = f"{prefix}_{k}"
            dst = out_parts / f"{pid}.png"
            align_angle_png(src, scale, dst_anchor).save(dst)
            bbox, coverage = alpha_stats(dst)
            order += 1
            parts.append({
                "id": pid, "display_name": f"Angle {prefix[6:]} {k}",
                "source_path": f"parts/{pid}.png", "bbox": bbox,
                "alpha_coverage": coverage, "draw_order": order, "folder": "AngleSwap",
                "deformer_node": None})
            meshes.append({"part_id": pid, "vertices": [], "triangles": [], "uvs": [],
                           "mesh_path": f"meshes/{pid}.json"})
            lo, hi = ARTWORK_EDGES[j], ARTWORK_EDGES[j + 1]   # |X| 밴드
            opacity.append(band_curve(pid, sign * hi, sign * lo) if sign < 0
                           else band_curve(pid, sign * lo, sign * hi))
    return parts, meshes, opacity


def measure_body_head(src: Path) -> tuple[float, float, int]:
    """본체 정면 실루엣 합성(rest pose) → 머리 중심·top·절대밴드 폭."""
    char = load_json(src / "character.json")
    canvas = Image.new("RGBA", tuple(char["canvas_size"]), (0, 0, 0, 0))
    for p in sorted(char["parts"], key=lambda x: x["draw_order"]):
        canvas.alpha_composite(Image.open(src / p["source_path"]).convert("RGBA"))
    cx, top, head_w = head_anchor_and_width(np.array(canvas)[..., 3])
    return cx, top, head_w


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, required=True, help="원본 rig_v0_project")
    parser.add_argument("--angle-parts", type=Path, required=True,
                        help="head_angle_1..4 + head_angle_right_1..4 가 있는 parts")
    parser.add_argument("--out", type=Path, required=True, help="통합 출력 프로젝트")
    args = parser.parse_args()
    src = args.src if args.src.is_absolute() else ROOT / args.src
    angle_parts = args.angle_parts if args.angle_parts.is_absolute() else ROOT / args.angle_parts
    out = args.out if args.out.is_absolute() else ROOT / args.out
    if not (src / "character.json").exists():
        raise SystemExit(f"원본 character.json 없음: {src}")

    # 비파괴: 원본 통째 복사 → 출력에서만 수정
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(src, out)
    char = load_json(out / "character.json")

    # 1) 라이브 50파트에 ParamAngleX 크로스페이드 곡선 추가 (곱셈 합성)
    live_ids = [p["id"] for p in char["parts"]]
    for pid in live_ids:
        char["part_opacity_keyframes"].append(live_crossfade_curve(pid))

    # 2) 각도 작화 8파트 주입 (본체 머리 앵커·크기에 정렬, 유령 파편 제거)
    body_cx, body_top, body_hw = measure_body_head(src)
    ref_alpha = np.array(Image.open(angle_parts / "head_angle_1.png").convert("RGBA"))[..., 3]
    _, _, angle_hw = head_anchor_and_width(ref_alpha)
    scale = body_hw / max(angle_hw, 1)
    print(f"본체 머리: cx {body_cx:.0f} top {body_top:.0f} w {body_hw} | "
          f"작화 w {angle_hw} → scale {scale:.3f}")
    angle_parts_out, angle_meshes, angle_opacity = build_angle_parts(
        angle_parts, out / "parts", scale, (body_cx, body_top))
    char["parts"].extend(angle_parts_out)
    char["meshes"].extend(angle_meshes)
    char["part_opacity_keyframes"].extend(angle_opacity)
    # 빈 메시(sprite) JSON 기록 — mesh_path 참조 무결성
    for m in angle_meshes:
        write_json(out / m["mesh_path"], {"part_id": m["part_id"], "vertices": [],
                                          "triangles": [], "uvs": []})

    # 3) ParamAngleX 범위 ±80으로 확장
    for prm in char["parameters"]:
        if prm["id"] == "ParamAngleX":
            prm["min"], prm["max"], prm["default"] = -ANGLE_MAX, ANGLE_MAX, 0.0

    char["experiment_id"] = char.get("experiment_id", "") + "+angle-swap-002"
    char["generated_at"] = now_iso()
    char.setdefault("notes", []).append(
        "ANGLE-SWAP-002 통합 — 좌4+우4 각도 작화 sprite, ParamAngleX ±80, "
        f"라이브밴드 |X|≤{LIVE_FULL}(±{LIVE_FADE} 페이드)=메시변형+표정, 작화밴드 {ARTWORK_EDGES}(극단 40/60/80°)")
    write_json(out / "character.json", char)

    print(f"통합 완료: {len(live_ids)}라이브 + {len(angle_parts_out)}작화 = {len(char['parts'])}파트")
    print(f"  ParamAngleX ±{ANGLE_MAX:.0f}, 라이브밴드 ±{LIVE_FULL:.0f}(±{LIVE_FADE:.0f}페이드), 작화밴드 {ARTWORK_EDGES}")
    print(f"  띄우기: python3 scripts/mini_cubism_preview_server.py --project {args.out} --port 8065")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

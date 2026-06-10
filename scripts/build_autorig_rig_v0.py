#!/usr/bin/env python3
"""P3 자동 리깅 v0: 하이브리드 레이어 → mini_cubism 리그(character.json) 자동 생성.

입력: 재스킨 가시 레이어(reskin_manifest) + 슬롯 생성 숨은 레이어(감은꺼풀/입 내부)
구조: v21 supported-rig 성공패턴의 스키마·수치를 그대로 이식
  - 디포머 트리: root → head_angle → (eye_L/eye_R/mouth/front_hair)
  - 파라미터 7종 (EyeOpen 0.27 클램프, MouthOpenY 0.85 클램프)
  - 눈 깜빡임/입 열기 = 불투명도 키프레임 스왑, 머리/눈동자 = 디포머 트랜스폼

사용: python3 scripts/build_autorig_rig_v0.py \
        --reskin-manifest <reskin_manifest.json> \
        --hidden-eye-dir <normalized_layers/eye_small_01> \
        --hidden-mouth-dir <normalized_layers/mouth_small_01> \
        --out-dir <project dir>
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, load_json, now_iso, rel, write_json  # noqa: E402

CANVAS = 2048

# 파트 → 폴더/디포머 배정 규칙
def folder_of(pid: str) -> str:
    if "eye" in pid or "iris" in pid or "lash" in pid:
        return "Eye"
    if "mouth" in pid:
        return "Mouth"
    if "brow" in pid or "face" in pid or "nose" in pid or "ear" in pid:
        return "Face"
    if "hair" in pid:
        return "Hair"
    return "Body"


def deformer_of(pid: str) -> str:
    if pid.startswith("L_") and ("eye" in pid or "iris" in pid or "lash" in pid) or pid.startswith("eye_L_"):
        return "eye_L_warp"
    if pid.startswith("R_") and ("eye" in pid or "iris" in pid or "lash" in pid) or pid.startswith("eye_R_"):
        return "eye_R_warp"
    if "mouth" in pid:
        return "mouth_warp"
    if pid == "front_hair":
        return "front_hair_warp"
    if "brow" in pid or "face" in pid or "nose" in pid or "ear" in pid:
        return "head_angle_warp"
    if pid.startswith("hair_front_"):
        return "front_hair_warp"
    if pid.startswith("hair_back_"):
        return "back_hair_warp"
    if "hair" in pid:
        return "root_warp"  # 통짜 hair (덩어리 미사용 시)
    return "body_warp"  # 몸/의상: BodyAngle·Breath 담당


def grid_mesh(part_id: str, bbox: list[int], cols: int, rows: int) -> dict:
    x0, y0 = bbox[0], bbox[1]
    x1, y1 = bbox[0] + bbox[2], bbox[1] + bbox[3]
    xs = np.linspace(x0, x1, cols)
    ys = np.linspace(y0, y1, rows)
    vertices = [[round(float(x), 1), round(float(y), 1)] for y in ys for x in xs]
    triangles = []
    for r in range(rows - 1):
        for c in range(cols - 1):
            i = r * cols + c
            triangles.append([i, i + cols, i + 1])
            triangles.append([i + 1, i + cols, i + cols + 1])
    uvs = [[round(v[0] / CANVAS, 6), round(v[1] / CANVAS, 6)] for v in vertices]
    return {"part_id": part_id, "vertices": vertices, "triangles": triangles, "uvs": uvs, "mesh_path": f"meshes/{part_id}.json"}


def alpha_stats(path: Path) -> tuple[list[int], float]:
    """bbox는 v21/런타임 규약대로 [x, y, w, h]."""
    img = Image.open(path).convert("RGBA")
    alpha = np.asarray(img)[..., 3]
    mask = alpha > 8
    if not mask.any():
        return [0, 0, 4, 4], 0.0
    ys, xs = np.where(mask)
    x0, y0 = int(xs.min()), int(ys.min())
    return [x0, y0, int(xs.max()) + 1 - x0, int(ys.max()) + 1 - y0], round(float(mask.mean()), 6)


def pad_bounds(bbox: list[int], pad: int) -> list[int]:
    x, y, w, h = bbox
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(CANVAS, x + w + pad), min(CANVAS, y + h + pad)
    return [x0, y0, x1 - x0, y1 - y0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reskin-manifest", type=Path, required=True)
    parser.add_argument("--hidden-eye-dir", type=Path, required=True)
    parser.add_argument("--hidden-mouth-dir", type=Path, required=True)
    parser.add_argument("--arap-eye-dir", type=Path, default=None, help="ARAP 깜빡임 패치 디렉토리 (지정 시 생성 감은꺼풀 대신 원본 워프 5단계)")
    parser.add_argument("--warp-mouth-dir", type=Path, default=None, help="입 워프 패치 디렉토리 (지정 시 내부 3레이어 스왑 대신 원본 워프 5단계)")
    parser.add_argument("--mouth-states-dir", type=Path, default=None, help="v21 최종 패턴: 풀 입 상태 스프라이트 4장 (closed/small/mid/wide) — warp보다 우선")
    parser.add_argument("--hair-chunks-dir", type=Path, default=None, help="머리 덩어리 5장 (front L/C/R + back L/R) — 통짜 hair 치환 + 물리 스프링 활성")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--experiment-id", default="autorig-rig-v0")
    args = parser.parse_args()
    use_arap = args.arap_eye_dir is not None and args.arap_eye_dir.exists()
    use_mouth_states = args.mouth_states_dir is not None and args.mouth_states_dir.exists()
    use_hair_chunks = args.hair_chunks_dir is not None and args.hair_chunks_dir.exists()
    use_mouth_warp = (not use_mouth_states) and args.warp_mouth_dir is not None and args.warp_mouth_dir.exists()

    out = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    (out / "parts").mkdir(parents=True, exist_ok=True)
    (out / "meshes").mkdir(parents=True, exist_ok=True)

    reskin = load_json(args.reskin_manifest)
    sources: list[tuple[str, Path, int]] = []  # (part_id, path, draw_order)
    for layer in sorted(reskin["layers"], key=lambda x: x["draw_order"]):
        if use_hair_chunks and layer["part_id"] in ("front_hair", "back_hair"):
            continue  # 덩어리로 치환
        sources.append((layer["part_id"], ROOT / layer["path"], layer["draw_order"]))
    if use_hair_chunks:
        for name, order in (("hair_back_L", 100), ("hair_back_R", 101),
                            ("hair_front_L", 700), ("hair_front_C", 701), ("hair_front_R", 702)):
            sources.append((name, args.hair_chunks_dir / f"{name}.png", order))
    # 숨은 레이어: 감은꺼풀은 눈 위(앞), 입 내부는 mouth_line 바로 아래
    hidden = []
    if use_mouth_states:
        # v21 최종 입 성공패턴: 풀 상태 스프라이트 크로스페이드 (분리 내부 레이어 폐기)
        # closed 상태는 원본 mouth_line이 담당 (픽셀-가이드 원칙: 중립은 100% 원본)
        for i, name in enumerate(("small", "mid", "wide")):
            hidden.append((f"mouth_state_{name}", args.mouth_states_dir / f"mouth_state_{name}.png", 412 + i * 2))
    elif use_mouth_warp:
        order = 408
        for step in ("025", "050", "075", "100"):
            hidden.append((f"mouth_warp_{step}", args.warp_mouth_dir / f"mouth_warp_{step}.png", order))
            order += 1
    else:
        hidden += [
            ("mouth_inner", args.hidden_mouth_dir / "mouth_inner.png", 405),
            ("mouth_teeth", args.hidden_mouth_dir / "mouth_teeth.png", 406),
            ("mouth_tongue", args.hidden_mouth_dir / "mouth_tongue.png", 407),
        ]
    if use_arap:
        # 픽셀-가이드 원칙: 깜빡임은 원본 워프 패치 (생성 감은꺼풀 미사용)
        order = 536
        for side in ("L", "R"):
            for step in ("025", "050", "075", "100"):
                hidden.append((f"eye_{side}_arap_{step}", args.arap_eye_dir / f"eye_{side}_arap_{step}.png", order))
                order += 1
    else:
        hidden += [
            ("eye_L_closed_lid", args.hidden_eye_dir / "eye_L_closed_lid.png", 545),
            ("eye_R_closed_lid", args.hidden_eye_dir / "eye_R_closed_lid.png", 546),
        ]
    for pid, path, order in hidden:
        if not path.exists():
            raise SystemExit(f"숨은 레이어 없음: {path}")
        sources.append((pid, path, order))
    sources.sort(key=lambda s: s[2])

    # v0.1: 생성 입 내부를 "원본 mouth_line bbox"에서 파생한 위치/크기로 재정합한다.
    # (옛 v22 좌표 그대로 쓰면 과대 — 픽셀-가이드 원칙: 위치·크기는 원본에서)
    mouth_line_src = next((s for s in sources if s[0] == "mouth_line"), None)
    mouth_ref_bbox = None
    if mouth_line_src is not None:
        mouth_ref_bbox, _ = alpha_stats(mouth_line_src[1])

    def realign_mouth_internal(src: Path, width_factor: float, top_offset_factor: float) -> Path:
        """입 내부 레이어를 원본 입라인 기준으로 재배치한 새 PNG를 만든다."""
        mx, my, mw, mh = mouth_ref_bbox
        img = Image.open(src).convert("RGBA")
        arr = np.asarray(img)
        mask = arr[..., 3] > 8
        ys, xs = np.where(mask)
        crop = img.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
        target_w = max(8, round(mw * width_factor))
        scale = target_w / crop.width
        crop = crop.resize((target_w, max(4, round(crop.height * scale))), Image.LANCZOS)
        canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
        cx = mx + mw / 2
        top = my + round(mh * top_offset_factor)
        canvas.alpha_composite(crop, (round(cx - crop.width / 2), top))
        out_path = src.parent / f"realigned_{src.name}"
        canvas.save(out_path)
        return out_path

    if mouth_ref_bbox is not None:
        factors = {"mouth_inner": (1.0, 0.0), "mouth_teeth": (0.8, 0.05), "mouth_tongue": (0.7, 0.35)}
        sources = [
            (pid, realign_mouth_internal(path, *factors[pid]) if pid in factors else path, order)
            for pid, path, order in sources
        ]

    parts, meshes = [], []
    bbox_by_id: dict[str, list[int]] = {}
    for pid, src, order in sources:
        dest = out / "parts" / f"{pid}.png"
        shutil.copyfile(src, dest)
        bbox, coverage = alpha_stats(dest)
        bbox_by_id[pid] = bbox
        parts.append(
            {
                "id": pid,
                "display_name": pid,
                "source_path": f"parts/{pid}.png",
                "original_source_path": str(src),
                "bbox": bbox,
                "alpha_coverage": coverage,
                "draw_order": order,
                "folder": folder_of(pid),
                "deformer_node": deformer_of(pid),
            }
        )
        big = pid in ("face_base", "back_hair", "front_hair", "clothes")
        mesh = grid_mesh(pid, bbox, 6 if big else 5, 6 if big else 4)
        meshes.append(mesh)
        write_json(out / mesh["mesh_path"], mesh)

    def union_bbox(*pids: str) -> list[int]:
        boxes = [bbox_by_id[p] for p in pids if p in bbox_by_id]
        x0 = min(b[0] for b in boxes)
        y0 = min(b[1] for b in boxes)
        x1 = max(b[0] + b[2] for b in boxes)
        y1 = max(b[1] + b[3] for b in boxes)
        return [x0, y0, x1 - x0, y1 - y0]

    body_bounds = pad_bounds(union_bbox("neck", "clothes", "L_arm", "R_arm", "choker", "raw_bottomwear"), 40)
    eye_l_bounds = pad_bounds(union_bbox("L_eye_white", "L_iris", "L_upper_lash", "eye_L_closed_lid"), 30)
    eye_r_bounds = pad_bounds(union_bbox("R_eye_white", "R_iris", "R_upper_lash", "eye_R_closed_lid"), 30)
    mouth_bounds = pad_bounds(union_bbox("mouth_line", "mouth_inner", "mouth_teeth"), 40)
    head_bounds = pad_bounds(union_bbox("face_base", "front_hair", "L_brow", "R_brow", "mouth_line"), 60)
    if use_hair_chunks:
        hair_bounds = pad_bounds(union_bbox("hair_front_L", "hair_front_C", "hair_front_R"), 30)
        back_hair_bounds = pad_bounds(union_bbox("hair_back_L", "hair_back_R"), 30)
    else:
        hair_bounds = pad_bounds(bbox_by_id["front_hair"], 30)
        back_hair_bounds = pad_bounds(bbox_by_id.get("back_hair", [0, 0, CANVAS, CANVAS]), 30)

    def center(b):
        return [round(b[0] + b[2] / 2), round(b[1] + b[3] / 2)]

    # 런타임은 deformer.child_ids로 파트를 매칭한다 (deformer_node 필드는 메타데이터일 뿐)
    children: dict[str, list[str]] = {}
    for part in parts:
        children.setdefault(part["deformer_node"], []).append(part["id"])

    deformers = [
        {"id": "root_warp", "type": "warp", "parent_id": None, "child_ids": children.get("root_warp", []), "bounds": [0, 0, CANVAS, CANVAS], "pivot": [1024, 1024]},
        {"id": "body_warp", "type": "warp", "parent_id": "root_warp", "child_ids": children.get("body_warp", []), "bounds": body_bounds, "pivot": center(body_bounds)},
        {"id": "head_angle_warp", "type": "warp", "parent_id": "root_warp", "child_ids": children.get("head_angle_warp", []), "bounds": head_bounds, "pivot": center(head_bounds)},
        {"id": "eye_L_warp", "type": "warp", "parent_id": "head_angle_warp", "child_ids": children.get("eye_L_warp", []), "bounds": eye_l_bounds, "pivot": center(eye_l_bounds)},
        {"id": "eye_R_warp", "type": "warp", "parent_id": "head_angle_warp", "child_ids": children.get("eye_R_warp", []), "bounds": eye_r_bounds, "pivot": center(eye_r_bounds)},
        {"id": "mouth_warp", "type": "warp", "parent_id": "head_angle_warp", "child_ids": children.get("mouth_warp", []), "bounds": mouth_bounds, "pivot": center(mouth_bounds)},
        {"id": "front_hair_warp", "type": "warp", "parent_id": "head_angle_warp", "child_ids": children.get("front_hair_warp", []), "bounds": hair_bounds, "pivot": center(hair_bounds)},
        {"id": "back_hair_warp", "type": "warp", "parent_id": "root_warp", "child_ids": children.get("back_hair_warp", []), "bounds": back_hair_bounds, "pivot": center(back_hair_bounds)},
    ]

    parameters = [
        {"id": "ParamAngleX", "min": -30, "max": 30, "default": 0, "key_values": [-30, 0, 30]},
        {"id": "ParamBodyAngleX", "min": -10, "max": 10, "default": 0, "key_values": [-10, 0, 10]},
        {"id": "ParamBodyAngleY", "min": -10, "max": 10, "default": 0, "key_values": [-10, 0, 10]},
        {"id": "ParamBreath", "min": 0, "max": 1, "default": 0, "key_values": [0, 1]},
        {"id": "ParamEyeBallX", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
        {"id": "ParamEyeBallY", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
        {"id": "ParamEyeLOpen", "min": 0.27, "max": 1, "default": 1, "key_values": [0.27, 0.5, 1]},
        {"id": "ParamEyeROpen", "min": 0.27, "max": 1, "default": 1, "key_values": [0.27, 0.5, 1]},
        {"id": "ParamHairFront", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
        {"id": "ParamMouthOpenY", "min": 0, "max": 0.85, "default": 0.0, "key_values": [0, 0.5, 0.85]},
    ]

    def binding(param, key, target, tx=0.0, ty=0.0, sx=1.0, sy=1.0):
        return {"parameter_id": param, "key_value": key, "target_id": target, "delta_type": "deformer_transform",
                "deltas": {"translate": [tx, ty], "scale": [sx, sy], "rotate": 0, "opacity": 1}}

    def binding_r(param, key, target, tx=0.0, ty=0.0, sx=1.0, sy=1.0, rotate=0.0):
        b = binding(param, key, target, tx=tx, ty=ty, sx=sx, sy=sy)
        b["deltas"]["rotate"] = rotate
        return b

    keyform_bindings = [
        binding("ParamAngleX", -30, "head_angle_warp", tx=-22),
        binding("ParamAngleX", 30, "head_angle_warp", tx=22),
        binding_r("ParamBodyAngleX", -10, "body_warp", tx=-8, rotate=-1.2),
        binding_r("ParamBodyAngleX", 10, "body_warp", tx=8, rotate=1.2),
        binding("ParamBodyAngleY", -10, "body_warp", ty=-5),
        binding("ParamBodyAngleY", 10, "body_warp", ty=5),
        binding("ParamBreath", 1, "body_warp", ty=-2, sy=1.012),
        binding("ParamEyeBallX", -1, "L_iris", tx=-7.5),
        binding("ParamEyeBallX", 1, "L_iris", tx=7.5),
        binding("ParamEyeBallX", -1, "R_iris", tx=-7.5),
        binding("ParamEyeBallX", 1, "R_iris", tx=7.5),
        binding("ParamEyeBallY", -1, "L_iris", ty=-4.5),
        binding("ParamEyeBallY", 1, "L_iris", ty=4.5),
        binding("ParamEyeBallY", -1, "R_iris", ty=-4.5),
        binding("ParamEyeBallY", 1, "R_iris", ty=4.5),
        # 깜빡임 형태는 ARAP 패치가 담당, 워프는 미세 눌림만 (validator: 파라미터당 바인딩 필수)
        binding("ParamEyeLOpen", 0.27, "eye_L_warp", sy=0.97),
        binding("ParamEyeROpen", 0.27, "eye_R_warp", sy=0.97),
        binding("ParamHairFront", 1, "front_hair_warp", tx=10),
        binding("ParamMouthOpenY", 0.5, "mouth_warp", ty=0.8, sy=1.01),
        binding("ParamMouthOpenY", 0.85, "mouth_warp", ty=1.6, sy=1.02),
    ]

    def curve(part, param, points):
        return {"part_id": part, "parameter_id": param, "mode": "linear",
                "keyframes": [{"value": v, "opacity": o} for v, o in points]}

    part_opacity_keyframes = []
    if use_arap:
        # 워프 패치 t ↔ EyeOpen 값 매핑: v = 1 - t·(1-0.27)
        v25, v50, v75, v100 = 0.8175, 0.635, 0.4525, 0.27
        for side in ("L", "R"):
            param = f"ParamEye{side}Open"
            part_opacity_keyframes += [
                curve(f"eye_{side}_arap_025", param, [(v50, 0.0), (v25, 1.0), (1.0, 0.0)]),
                curve(f"eye_{side}_arap_050", param, [(v75, 0.0), (v50, 1.0), (v25, 0.0)]),
                curve(f"eye_{side}_arap_075", param, [(v100, 0.0), (v75, 1.0), (v50, 0.0)]),
                curve(f"eye_{side}_arap_100", param, [(v100, 1.0), (v75, 0.0), (1.0, 0.0)]),
            ]
    else:
        open_curve = [(0.27, 0.0), (0.5, 0.55), (0.8, 0.95), (1.0, 1.0)]
        closed_curve = [(0.27, 1.0), (0.5, 0.35), (0.65, 0.0), (1.0, 0.0)]
        for side in ("L", "R"):
            param = f"ParamEye{side}Open"
            for pid in (f"{side}_eye_white", f"{side}_iris", f"{side}_upper_lash", f"{side}_lower_lash"):
                if pid in bbox_by_id:
                    part_opacity_keyframes.append(curve(pid, param, open_curve))
            part_opacity_keyframes.append(curve(f"eye_{side}_closed_lid", param, closed_curve))
    if use_mouth_states:
        # v21 최종 패턴 커브 그대로 이식 (mouth_closed_smile/small_open/mid_teeth/wide_teeth_tongue)
        part_opacity_keyframes += [
            curve("mouth_line", "ParamMouthOpenY", [(0.0, 1.0), (0.22, 0.88), (0.4, 0.3), (0.55, 0.0), (1.0, 0.0)]),
            curve("mouth_state_small", "ParamMouthOpenY", [(0.0, 0.0), (0.18, 0.2), (0.35, 0.9), (0.55, 0.4), (0.68, 0.0), (1.0, 0.0)]),
            curve("mouth_state_mid", "ParamMouthOpenY", [(0.0, 0.0), (0.38, 0.0), (0.58, 0.95), (0.78, 0.35), (0.9, 0.0), (1.0, 0.0)]),
            curve("mouth_state_wide", "ParamMouthOpenY", [(0.0, 0.0), (0.65, 0.0), (0.82, 0.72), (1.0, 1.0)]),
        ]
    elif use_mouth_warp:
        # 워프 패치 t ↔ MouthOpenY 매핑: v = t * 0.85
        m25, m50, m75, m100 = 0.2125, 0.425, 0.6375, 0.85
        part_opacity_keyframes += [
            curve("mouth_warp_025", "ParamMouthOpenY", [(0.0, 0.0), (m25, 1.0), (m50, 0.0)]),
            curve("mouth_warp_050", "ParamMouthOpenY", [(m25, 0.0), (m50, 1.0), (m75, 0.0)]),
            curve("mouth_warp_075", "ParamMouthOpenY", [(m50, 0.0), (m75, 1.0), (m100, 0.0)]),
            curve("mouth_warp_100", "ParamMouthOpenY", [(m75, 0.0), (m100, 1.0)]),
        ]
    else:
        part_opacity_keyframes += [
            curve("mouth_line", "ParamMouthOpenY", [(0.0, 1.0), (0.25, 0.85), (0.45, 0.0), (0.85, 0.0)]),
            curve("mouth_inner", "ParamMouthOpenY", [(0.0, 0.0), (0.2, 0.15), (0.45, 0.9), (0.85, 1.0)]),
            curve("mouth_teeth", "ParamMouthOpenY", [(0.0, 0.0), (0.3, 0.4), (0.85, 0.9)]),
            curve("mouth_tongue", "ParamMouthOpenY", [(0.0, 0.0), (0.45, 0.3), (0.85, 0.8)]),
        ]

    # Phase C: 물리 스프링 — v0-3 검증 프로파일 이식 (덩어리 사용 시)
    physics_profiles = []
    if use_hair_chunks:
        physics_profiles = [
            {
                "id": "front_hair_soft_spring",
                "targets": ["hair_front_L", "hair_front_C", "hair_front_R"],
                "anchor": "top_center", "mass": 0.8, "stiffness": 0.13, "damping": 0.82, "drag": 0.03,
                "max_offset": [34, 28], "rotate_factor": 0.055,
                "input_weights": {"ParamAngleX": [-24, 3], "ParamBodyAngleX": [-8, 2], "ParamHairFront": [24, 0]},
                "part_weights": {"hair_front_L": 1.0, "hair_front_C": 0.7, "hair_front_R": 1.0},
            },
            {
                "id": "back_hair_heavy_spring",
                "targets": ["hair_back_L", "hair_back_R"],
                "anchor": "top_center", "mass": 1.4, "stiffness": 0.08, "damping": 0.88, "drag": 0.04,
                "max_offset": [24, 34], "rotate_factor": 0.03,
                "input_weights": {"ParamAngleX": [-18, 8], "ParamBodyAngleX": [-6, 3]},
                "part_weights": {"hair_back_L": 1.0, "hair_back_R": 1.0},
            },
            {
                "id": "accessory_quick_spring",
                "targets": [pid for pid in ("choker", "earwear") if pid in bbox_by_id],
                "anchor": "center", "mass": 0.5, "stiffness": 0.2, "damping": 0.72, "drag": 0.02,
                "max_offset": [16, 14], "rotate_factor": 0.08,
                "input_weights": {"ParamAngleX": [-12, 4]},
                "part_weights": {"choker": 0.35, "earwear": 0.9},
            },
        ]
        physics_profiles = [p for p in physics_profiles if p["targets"]]

    character = {
        "schema_version": 1,
        "project_kind": "mini_cubism_v0",
        "experiment_id": args.experiment_id,
        "generated_at": now_iso(),
        "source_selection": {
            "visible_layers": rel(args.reskin_manifest),
            "hidden_layers": [str(args.hidden_eye_dir), str(args.hidden_mouth_dir)],
            "recipe": "hybrid: visible=decomposition+original reskin, hidden=slot generation (v21 success pattern)",
        },
        "canvas_size": [CANVAS, CANVAS],
        "parts": parts,
        "meshes": meshes,
        "deformers": deformers,
        "parameters": parameters,
        "keyform_bindings": keyform_bindings,
        "physics_profiles": physics_profiles,
        "part_opacity_keyframes": part_opacity_keyframes,
        "glue": [],
        "notes": ["AUTORIG P3 v0 — 자동 생성 리그"],
        "unsupported_parameters": [],
    }
    write_json(out / "character.json", character)
    mini_rig = {
        "schema_version": 1,
        "project_kind": "mini_cubism_rig_v0",
        "mesh_overrides": {},
        "keyform_overrides": [],
        "clipping": {"enabled": True, "pairs": {"L_eye_white": ["L_iris"], "R_eye_white": ["R_iris"]}},
        "eye_socket_covers": {"enabled": False},
        "notes": ["autorig v0"],
    }
    write_json(out / "mini_rig.json", mini_rig)
    print(f"rig: parts={len(parts)} meshes={len(meshes)} deformers={len(deformers)} params={len(parameters)} bindings={len(keyform_bindings)} opacity_curves={len(part_opacity_keyframes)}")
    print(f"project: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

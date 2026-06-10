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
    if pid.startswith("L_") and ("eye" in pid or "iris" in pid or "lash" in pid) or pid == "eye_L_closed_lid":
        return "eye_L_warp"
    if pid.startswith("R_") and ("eye" in pid or "iris" in pid or "lash" in pid) or pid == "eye_R_closed_lid":
        return "eye_R_warp"
    if "mouth" in pid:
        return "mouth_warp"
    if pid == "front_hair":
        return "front_hair_warp"
    if "brow" in pid or "face" in pid or "nose" in pid or "ear" in pid:
        return "head_angle_warp"
    return "root_warp"


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
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--experiment-id", default="autorig-rig-v0")
    args = parser.parse_args()

    out = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    (out / "parts").mkdir(parents=True, exist_ok=True)
    (out / "meshes").mkdir(parents=True, exist_ok=True)

    reskin = load_json(args.reskin_manifest)
    sources: list[tuple[str, Path, int]] = []  # (part_id, path, draw_order)
    for layer in sorted(reskin["layers"], key=lambda x: x["draw_order"]):
        sources.append((layer["part_id"], ROOT / layer["path"], layer["draw_order"]))
    # 숨은 레이어: 감은꺼풀은 눈 위(앞), 입 내부는 mouth_line 바로 아래
    hidden = [
        ("eye_L_closed_lid", args.hidden_eye_dir / "eye_L_closed_lid.png", 545),
        ("eye_R_closed_lid", args.hidden_eye_dir / "eye_R_closed_lid.png", 546),
        ("mouth_inner", args.hidden_mouth_dir / "mouth_inner.png", 405),
        ("mouth_teeth", args.hidden_mouth_dir / "mouth_teeth.png", 406),
        ("mouth_tongue", args.hidden_mouth_dir / "mouth_tongue.png", 407),
    ]
    for pid, path, order in hidden:
        if not path.exists():
            raise SystemExit(f"숨은 레이어 없음: {path}")
        sources.append((pid, path, order))
    sources.sort(key=lambda s: s[2])

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

    eye_l_bounds = pad_bounds(union_bbox("L_eye_white", "L_iris", "L_upper_lash", "eye_L_closed_lid"), 30)
    eye_r_bounds = pad_bounds(union_bbox("R_eye_white", "R_iris", "R_upper_lash", "eye_R_closed_lid"), 30)
    mouth_bounds = pad_bounds(union_bbox("mouth_line", "mouth_inner", "mouth_teeth"), 40)
    head_bounds = pad_bounds(union_bbox("face_base", "front_hair", "L_brow", "R_brow", "mouth_line"), 60)
    hair_bounds = pad_bounds(bbox_by_id["front_hair"], 30)

    def center(b):
        return [round(b[0] + b[2] / 2), round(b[1] + b[3] / 2)]

    # 런타임은 deformer.child_ids로 파트를 매칭한다 (deformer_node 필드는 메타데이터일 뿐)
    children: dict[str, list[str]] = {}
    for part in parts:
        children.setdefault(part["deformer_node"], []).append(part["id"])

    deformers = [
        {"id": "root_warp", "type": "warp", "parent_id": None, "child_ids": children.get("root_warp", []), "bounds": [0, 0, CANVAS, CANVAS], "pivot": [1024, 1024]},
        {"id": "head_angle_warp", "type": "warp", "parent_id": "root_warp", "child_ids": children.get("head_angle_warp", []), "bounds": head_bounds, "pivot": center(head_bounds)},
        {"id": "eye_L_warp", "type": "warp", "parent_id": "head_angle_warp", "child_ids": children.get("eye_L_warp", []), "bounds": eye_l_bounds, "pivot": center(eye_l_bounds)},
        {"id": "eye_R_warp", "type": "warp", "parent_id": "head_angle_warp", "child_ids": children.get("eye_R_warp", []), "bounds": eye_r_bounds, "pivot": center(eye_r_bounds)},
        {"id": "mouth_warp", "type": "warp", "parent_id": "head_angle_warp", "child_ids": children.get("mouth_warp", []), "bounds": mouth_bounds, "pivot": center(mouth_bounds)},
        {"id": "front_hair_warp", "type": "warp", "parent_id": "head_angle_warp", "child_ids": children.get("front_hair_warp", []), "bounds": hair_bounds, "pivot": center(hair_bounds)},
    ]

    parameters = [
        {"id": "ParamAngleX", "min": -30, "max": 30, "default": 0, "key_values": [-30, 0, 30]},
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

    keyform_bindings = [
        binding("ParamAngleX", -30, "head_angle_warp", tx=-22),
        binding("ParamAngleX", 30, "head_angle_warp", tx=22),
        binding("ParamEyeBallX", -1, "L_iris", tx=-7.5),
        binding("ParamEyeBallX", 1, "L_iris", tx=7.5),
        binding("ParamEyeBallX", -1, "R_iris", tx=-7.5),
        binding("ParamEyeBallX", 1, "R_iris", tx=7.5),
        binding("ParamEyeBallY", -1, "L_iris", ty=-4.5),
        binding("ParamEyeBallY", 1, "L_iris", ty=4.5),
        binding("ParamEyeBallY", -1, "R_iris", ty=-4.5),
        binding("ParamEyeBallY", 1, "R_iris", ty=4.5),
        binding("ParamEyeLOpen", 0.27, "eye_L_warp", sy=0.5),
        binding("ParamEyeROpen", 0.27, "eye_R_warp", sy=0.5),
        binding("ParamHairFront", 1, "front_hair_warp", tx=10),
        binding("ParamMouthOpenY", 0.5, "mouth_warp", ty=0.8, sy=1.01),
        binding("ParamMouthOpenY", 0.85, "mouth_warp", ty=1.6, sy=1.02),
    ]

    def curve(part, param, points):
        return {"part_id": part, "parameter_id": param, "mode": "linear",
                "keyframes": [{"value": v, "opacity": o} for v, o in points]}

    open_curve = [(0.27, 0.0), (0.5, 0.55), (0.8, 0.95), (1.0, 1.0)]
    closed_curve = [(0.27, 1.0), (0.5, 0.35), (0.65, 0.0), (1.0, 0.0)]
    part_opacity_keyframes = []
    for side in ("L", "R"):
        param = f"ParamEye{side}Open"
        for pid in (f"{side}_eye_white", f"{side}_iris", f"{side}_upper_lash", f"{side}_lower_lash"):
            if pid in bbox_by_id:
                part_opacity_keyframes.append(curve(pid, param, open_curve))
        part_opacity_keyframes.append(curve(f"eye_{side}_closed_lid", param, closed_curve))
    part_opacity_keyframes += [
        curve("mouth_line", "ParamMouthOpenY", [(0.0, 1.0), (0.25, 0.85), (0.45, 0.0), (0.85, 0.0)]),
        curve("mouth_inner", "ParamMouthOpenY", [(0.0, 0.0), (0.2, 0.15), (0.45, 0.9), (0.85, 1.0)]),
        curve("mouth_teeth", "ParamMouthOpenY", [(0.0, 0.0), (0.3, 0.4), (0.85, 0.9)]),
        curve("mouth_tongue", "ParamMouthOpenY", [(0.0, 0.0), (0.45, 0.3), (0.85, 0.8)]),
    ]

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
        "physics_profiles": [],
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

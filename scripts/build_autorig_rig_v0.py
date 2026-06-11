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
import math
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.rig_keyforms import attach_mouth_height_keyforms, binding, binding_r, build_keyform_bindings, build_opacity_curves, build_parameters, build_physics_profiles  # noqa: E402
from lib.vtube_io import ROOT, load_json, now_iso, rel, write_json  # noqa: E402
from run_arap_blink_experiment import blink_mesh, eye_bbox_from_layer  # noqa: E402

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
    if pid == "shoulder_hair":
        return "back_hair_warp"  # clothes에서 분리한 어깨 가닥 — 머리 본체와 함께 움직인다
    if "hair" in pid:
        return "root_warp"  # 통짜 hair (덩어리 미사용 시)
    if pid == "neck_under":
        return "body_warp"  # 숨은 목 = 몸 고정 배경판 (머리를 따라가면 어긋남이 노출된다)
    if pid in ("neck", "neck_skin", "choker"):
        return "neck_warp"  # 목 부분 추종 (머리 격자 페이드 + 몸 바인딩) — 턱→목→가슴 3단 그라데이션
    return "body_warp"  # 몸/의상: BodyAngle·Breath 담당


def build_vertex_weights(meshes: list[dict], bbox_by_id: dict) -> list[dict]:
    """물리 정점 가중 (v0-3 검증 포맷) — 뿌리(상단) 0 → 끝(하단) 1.

    CLOTH-PHYS-001: clothes 포함 — 상단(목 접합)이 가중 0이라 neck_skin과의
    등변위가 보장되고, 밑단만 드레이프 스프링을 탄다.
    """
    out = []
    for pid in ("hair_front_L", "hair_front_C", "hair_front_R", "hair_back_L", "hair_back_R", "clothes"):
        if pid not in bbox_by_id:
            continue
        x, y, w, h = bbox_by_id[pid]
        mesh = next(m for m in meshes if m["part_id"] == pid)
        weights = [round(max(0.0, min(1.0, (vy - y) / max(h, 1))), 4) for _, vy in mesh["vertices"]]
        out.append({"part_id": pid, "weight_kind": "root_to_tip_vertical", "weights": weights})
    return out


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
    parser.add_argument("--hidden-eye-dir", type=Path, default=None, help="레거시 생성 감은꺼풀 (ARAP 미사용 시에만 필수)")
    parser.add_argument("--hidden-mouth-dir", type=Path, default=None, help="레거시 생성 입 내부 (mouth-states/warp 미사용 시에만 필수)")
    parser.add_argument("--arap-eye-dir", type=Path, default=None, help="ARAP 깜빡임 패치 디렉토리 (지정 시 생성 감은꺼풀 대신 원본 워프 5단계)")
    parser.add_argument("--warp-mouth-dir", type=Path, default=None, help="입 워프 패치 디렉토리 (지정 시 내부 3레이어 스왑 대신 원본 워프 5단계)")
    parser.add_argument("--mouth-states-dir", type=Path, default=None, help="v21 최종 패턴: 풀 입 상태 스프라이트 4장 (closed/small/mid/wide) — warp보다 우선")
    parser.add_argument("--hair-chunks-dir", type=Path, default=None, help="머리 덩어리 5장 (front L/C/R + back L/R) — 통짜 hair 치환 + 물리 스프링 활성")
    parser.add_argument("--hidden-neck-dir", type=Path, default=None, help="숨은 목 (neck_under.png) — 목 분리 이음새 방지")
    parser.add_argument("--neck-split-dir", type=Path, default=None, help="목 피부 분리 (neck_skin + clothes_trimmed) — 분해가 목을 clothes에 합친 경우")
    parser.add_argument("--shoulder-hair-dir", type=Path, default=None, help="어깨 가닥 분리 (shoulder_hair + clothes_filled) — 분해가 머리카락을 clothes에 구운 경우")
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

    use_neck_split = args.neck_split_dir is not None and (args.neck_split_dir / "neck_skin.png").exists()
    use_shoulder = args.shoulder_hair_dir is not None and (args.shoulder_hair_dir / "shoulder_hair.png").exists()
    reskin = load_json(args.reskin_manifest)
    sources: list[tuple[str, Path, int]] = []  # (part_id, path, draw_order)
    clothes_order = 210
    for layer in sorted(reskin["layers"], key=lambda x: x["draw_order"]):
        if use_hair_chunks and layer["part_id"] in ("front_hair", "back_hair"):
            continue  # 덩어리로 치환
        if layer["part_id"] == "clothes" and (use_neck_split or use_shoulder):
            clothes_order = layer["draw_order"]
            # 분리 체인: clothes → (목 분리) clothes_trimmed → (어깨 가닥 분리) clothes_filled
            clothes_path = args.shoulder_hair_dir / "clothes_filled.png" if use_shoulder \
                else args.neck_split_dir / "clothes_trimmed.png"
            sources.append(("clothes", clothes_path, clothes_order))
            continue
        sources.append((layer["part_id"], ROOT / layer["path"], layer["draw_order"]))
    if use_neck_split:
        sources.append(("neck_skin", args.neck_split_dir / "neck_skin.png", clothes_order + 1))
    if use_shoulder:
        # 어깨 가닥은 목 피부 위에 그려진다 (마스터에서 최전면 — clothes+2)
        sources.append(("shoulder_hair", args.shoulder_hair_dir / "shoulder_hair.png", clothes_order + 2))
    if use_hair_chunks:
        for name, order in (("hair_back_L", 100), ("hair_back_R", 101),
                            ("hair_front_L", 700), ("hair_front_C", 701), ("hair_front_R", 702)):
            sources.append((name, args.hair_chunks_dir / f"{name}.png", order))
    # 숨은 레이어: 감은꺼풀은 눈 위(앞), 입 내부는 mouth_line 바로 아래
    hidden = []
    if args.hidden_neck_dir is not None and (args.hidden_neck_dir / "neck_under.png").exists():
        hidden.append(("neck_under", args.hidden_neck_dir / "neck_under.png", 199))  # 원본 목(200) 바로 뒤
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
        if args.hidden_mouth_dir is None:
            raise SystemExit("--mouth-states-dir/--warp-mouth-dir 없이는 --hidden-mouth-dir가 필요해요")
        hidden += [
            ("mouth_inner", args.hidden_mouth_dir / "mouth_inner.png", 405),
            ("mouth_teeth", args.hidden_mouth_dir / "mouth_teeth.png", 406),
            ("mouth_tongue", args.hidden_mouth_dir / "mouth_tongue.png", 407),
        ]
    blink_cfg = {}
    if use_arap:
        # 픽셀-가이드 원칙: 깜빡임은 원본 항등 패치 1장 + 정점 키폼 2개 (EYE-NATURAL-002)
        # — 구 4단계 크로스페이드는 전환 구간 겹침 잔상(주인님 보고: 어지러움)으로 폐기
        blink_cfg = load_json(args.arap_eye_dir / "arap_blink_config.json")
        for order, side in ((536, "L"), (537, "R")):
            hidden.append((f"eye_{side}_blink", args.arap_eye_dir / f"eye_{side}_arap_000.png", order))
        # EXPR-002 눈웃음: 같은 항등 패치, 곡선 A 키폼 — 깜빡임 위에 그림
        for order, side in ((538, "L"), (539, "R")):
            hidden.append((f"eye_{side}_smile", args.arap_eye_dir / f"eye_{side}_arap_000.png", order))
    else:
        if args.hidden_eye_dir is None:
            raise SystemExit("--arap-eye-dir 없이는 --hidden-eye-dir가 필요해요")
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
        if use_arap and (pid.endswith("_blink") or pid.endswith("_smile")):
            # EYE-NATURAL-002/EXPR-002: 경계 곡선 행 정점 키폼 메시 — 일반 격자/컬링 비적용
            side = "L" if pid.startswith("eye_L") else "R"
            is_smile = pid.endswith("_smile")
            eye_bbox = eye_bbox_from_layer(ROOT / blink_cfg[f"eye_white_{side}"])
            mesh = blink_mesh(
                pid, "ParamEyeSmile" if is_smile else f"ParamEye{side}Open", eye_bbox,
                skin_band=float(blink_cfg.get("skin_band", 0.9)),
                lower_rise=float(blink_cfg.get("lower_rise", 0.2)),
                lower_band=float(blink_cfg.get("lower_band", 0.35)),
                canvas=CANVAS, pad=int(blink_cfg.get("patch_pad", 26)),
                smile=(float(blink_cfg.get("smile_lid_center", 0.34)),
                       float(blink_cfg.get("smile_low_center", 0.42))) if is_smile else None)
            meshes.append(mesh)
            write_json(out / mesh["mesh_path"], mesh)
            continue
        big = pid in ("face_base", "back_hair", "front_hair", "clothes", "shoulder_hair") or pid.startswith(("hair_front_", "hair_back_"))
        if pid in ("face_base", "clothes", "neck_skin"):
            cols = rows = 9  # 목-어깨 접합부를 지나는 파트 — fade 보간이 고와야 분리가 안 보인다
        else:
            cols = rows = 6 if big else 5
            rows = rows if big else 4
        mesh = grid_mesh(pid, bbox, cols, rows)
        # 렌더 비용 절감: 알파가 완전히 빈 삼각형 제거 (bbox 모서리 투명 영역)
        part_alpha = np.asarray(Image.open(dest).convert("RGBA"))[..., 3]
        def tri_active(tri):
            pts = [mesh["vertices"][i] for i in tri]
            cx = sum(p[0] for p in pts) / 3
            cy = sum(p[1] for p in pts) / 3
            for sx, sy in pts + [[cx, cy]]:
                xi = min(int(sx), part_alpha.shape[1] - 1)
                yi = min(int(sy), part_alpha.shape[0] - 1)
                y0s, y1s = max(0, yi - 40), min(part_alpha.shape[0], yi + 40)
                x0s, x1s = max(0, xi - 40), min(part_alpha.shape[1], xi + 40)
                if (part_alpha[y0s:y1s, x0s:x1s] > 8).any():
                    return True
            return False
        culled = [tri for tri in mesh["triangles"] if tri_active(tri)]
        if culled:  # 전멸 시(완전 빈 파트) 원본 유지 — validator 요구
            mesh["triangles"] = culled
        meshes.append(mesh)
        write_json(out / mesh["mesh_path"], mesh)

    if use_mouth_states:
        # MOUTH-KEYFORM-001: 상태 스프라이트를 공통 입높이로 워프 — 크로스페이드 교차점 윤곽 정렬
        for pid in attach_mouth_height_keyforms(meshes, bbox_by_id):
            mesh = next(m for m in meshes if m["part_id"] == pid)
            write_json(out / mesh["mesh_path"], mesh)

    def union_bbox(*pids: str) -> list[int]:
        # 빈 파트(알파 0 → [0,0,4,4])는 제외 — 원점으로 bounds가 끌려가는 것 방지
        boxes = [bbox_by_id[p] for p in pids if p in bbox_by_id and bbox_by_id[p][2] > 4]
        if not boxes:
            boxes = [[0, 0, CANVAS, CANVAS]]
        x0 = min(b[0] for b in boxes)
        y0 = min(b[1] for b in boxes)
        x1 = max(b[0] + b[2] for b in boxes)
        y1 = max(b[1] + b[3] for b in boxes)
        return [x0, y0, x1 - x0, y1 - y0]

    body_bounds = pad_bounds(union_bbox("neck", "clothes", "L_arm", "R_arm", "choker", "raw_bottomwear"), 40)
    # MESH-DEFORM: head 격자가 턱·목 상단을 덮어야 edge-pin 연속이 목으로 이어진다
    def extend_down(b: list[int], px: int) -> list[int]:
        return [b[0], b[1], b[2], min(CANVAS - b[1], b[3] + px)]

    eye_l_bounds = pad_bounds(union_bbox("L_eye_white", "L_iris", "L_upper_lash", "eye_L_closed_lid"), 30)
    eye_r_bounds = pad_bounds(union_bbox("R_eye_white", "R_iris", "R_upper_lash", "eye_R_closed_lid"), 30)
    mouth_bounds = pad_bounds(union_bbox("mouth_line", "mouth_inner", "mouth_teeth"), 40)
    head_bounds = pad_bounds(union_bbox("face_base", "front_hair", "L_brow", "R_brow", "mouth_line"), 60)  # 하향 연장 금지: 턱은 가장자리 핀 근처라 적게 움직여야 목이 따라갈 수 있다 (공식 의사3D)
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

    # 이식성 검사: 명명 규칙에 안 걸려 body_warp 폴백에 떨어진 미지의 파트 경고 (LOCK-001)
    KNOWN_BODY = {"neck", "neck_under", "choker", "clothes", "L_arm", "R_arm",
                  "raw_bottomwear", "raw_legwear", "raw_footwear", "body", "torso"}
    unmatched_parts = sorted(
        p["id"] for p in parts
        if p["deformer_node"] == "body_warp" and p["id"] not in KNOWN_BODY
    )
    if unmatched_parts:
        print(f"[경고] 명명 규칙 미매칭 → body_warp 폴백: {unmatched_parts} (deformer_of 패턴 확인 필요)")

    neck_bounds = pad_bounds(union_bbox("neck", "neck_skin", "choker", "neck_under"), 30)
    # CHAIN-001: 공식 "首の位置" 등가 — 머리·목·뒷머리가 몸 스웨이에 통째로 탑승하는 비고정 상위 워프.
    # head_angle_warp는 edge-pin(의사3D)이라 몸 추종을 직접 바인딩하면 윤곽이 안 움직인다.
    def union_bounds(*bs):
        x0 = min(b[0] for b in bs)
        y0 = min(b[1] for b in bs)
        x1 = max(b[0] + b[2] for b in bs)
        y1 = max(b[1] + b[3] for b in bs)
        return [x0, y0, x1 - x0, y1 - y0]

    # CHAIN-001 v3: 접합부 연속의 원리 = "목·가슴·배경판이 접합부에서 같은 변위로 만난다".
    # upper는 균일 +8 운반 (머리·목 전체), 대신 body 격자 상단을 얼굴 높이까지 연장해
    # edge-pin 페이드가 접합부가 아닌 얼굴 높이에서 일어나게 → 가슴도 접합부에서 풀 +8.
    # (v2의 "목만 0으로 점감"은 가슴이 접합부에서 ~5px 움직여 부호만 바뀐 슬립이었다)
    upper_bounds = pad_bounds(union_bounds(head_bounds, neck_bounds), 40)
    head_cy = head_bounds[1] + head_bounds[3] // 2
    if body_bounds[1] > head_cy:
        body_bounds = [body_bounds[0], head_cy, body_bounds[2], body_bounds[3] + (body_bounds[1] - head_cy)]
    # BODY-SWAY-001 v3: 몸 피벗 = 골반(바닥 중앙) — BodyAngleX/Z 진자 회전의 축
    body_pivot = [center(body_bounds)[0], body_bounds[1] + body_bounds[3]]
    deformers = [
        # lattice/edge_pinned: FFD 격자 (공식 워프 메커니즘). edge_pinned=경계 연결, false=전역 이동.
        {"id": "root_warp", "type": "warp", "parent_id": None, "child_ids": children.get("root_warp", []), "bounds": [0, 0, CANVAS, CANVAS], "pivot": [1024, 1024], "lattice": {"cols": 3, "rows": 3}, "edge_pinned": False},
        {"id": "body_warp", "type": "warp", "parent_id": "root_warp", "child_ids": children.get("body_warp", []), "bounds": body_bounds, "pivot": body_pivot, "lattice": {"cols": 5, "rows": 5}, "edge_pinned": True},
        {"id": "upper_warp", "type": "warp", "parent_id": "root_warp", "child_ids": children.get("upper_warp", []), "bounds": upper_bounds, "pivot": center(upper_bounds), "lattice": {"cols": 3, "rows": 3}, "edge_pinned": False},
        {"id": "head_angle_warp", "type": "warp", "parent_id": "upper_warp", "child_ids": children.get("head_angle_warp", []), "bounds": head_bounds, "pivot": center(head_bounds), "lattice": {"cols": 7, "rows": 7}, "edge_pinned": True},
        # 목 = head 자식 (머리 격자 페이드 → 위는 머리, 아래로 갈수록 감쇠하는 그라데이션)
        # 몸 추종은 upper_warp 상속 (자체 BodyAngle 바인딩은 이중 적용이라 제거 — CHAIN-001)
        # NECK-PIN-001: 위 가장자리도 핀 — 공식 首の曲面 구조 (양끝 고정, 중간만 휨).
        # 위가 자유로우면 목 자체 바인딩(±5)이 face_base 소유의 윗목 픽셀과 경계에서 어긋난다
        # (주인님 리그 모드 스크린샷: 목 중앙 가로 분리선 = 참수선)
        {"id": "neck_warp", "type": "warp", "parent_id": "head_angle_warp", "child_ids": children.get("neck_warp", []), "bounds": neck_bounds, "pivot": center(neck_bounds), "lattice": {"cols": 5, "rows": 6}, "edge_pinned": True},
        {"id": "eye_L_warp", "type": "warp", "parent_id": "head_angle_warp", "child_ids": children.get("eye_L_warp", []), "bounds": eye_l_bounds, "pivot": center(eye_l_bounds), "lattice": {"cols": 5, "rows": 5}, "edge_pinned": True},
        {"id": "eye_R_warp", "type": "warp", "parent_id": "head_angle_warp", "child_ids": children.get("eye_R_warp", []), "bounds": eye_r_bounds, "pivot": center(eye_r_bounds), "lattice": {"cols": 5, "rows": 5}, "edge_pinned": True},
        {"id": "mouth_warp", "type": "warp", "parent_id": "head_angle_warp", "child_ids": children.get("mouth_warp", []), "bounds": mouth_bounds, "pivot": center(mouth_bounds), "lattice": {"cols": 5, "rows": 5}, "edge_pinned": True},
        {"id": "front_hair_warp", "type": "warp", "parent_id": "head_angle_warp", "child_ids": children.get("front_hair_warp", []), "bounds": hair_bounds, "pivot": center(hair_bounds), "lattice": {"cols": 5, "rows": 5}, "edge_pinned": True},
        # 뒷머리 = 통짜 머리 감쇠 추종 (공식: 後ろ髪の曲面 ← AngleX/Y, 얼굴 체인 소속).
        # 부모는 root (upper 자식이면 upper bounds와 부분 겹침 → 머리카락 내부 시어) —
        # 몸 추종은 자체 BodyAngle 바인딩으로 균일하게. 핀 해제: 실루엣이 움직여야 체감,
        # 하단 스윕은 몸 뒤 draw order라 안전. pivot은 head 피벗 (AngleZ 호가 목 중심).
        {"id": "back_hair_warp", "type": "warp", "parent_id": "root_warp", "child_ids": children.get("back_hair_warp", []), "bounds": back_hair_bounds, "pivot": center(head_bounds), "lattice": {"cols": 5, "rows": 5}, "edge_pinned": False},
    ]

    # 파라미터/바인딩/커브/물리 수치는 lib/rig_keyforms.py (2026-06-11 500줄 룰 분리)
    parameters = build_parameters()
    keyform_bindings = build_keyform_bindings()
    # BODY-SWAY-001 BodyAngleZ 기울기: body는 자기 피벗 회전, 운반 대상(upper·뒷머리)은
    # "그 회전이 자기 높이에 만드는 수평 변위"만큼 균일 tx (X 스웨이의 운반 패턴과 동형 —
    # 부분 겹침 회전을 직접 주면 내부 시어, CHAIN-001 교훈)
    # BODY-SWAY-001 v3: 몸 = 골반(바닥 중앙) 피벗 진자 — 골반 0 → 가슴·어깨로 갈수록
    # 크게 기우는 높이 그라데이션 (균일 평행이동은 유기성 부재 — "종이인형" 판정).
    # 등변위 기준점 = 접합부(목 하단): X 회전각은 접합부 변위가 정확히 ±8이 되게 역산,
    # 운반(upper/back_hair)은 그 ±8을 균일 tx로 — 접합부 일치가 구조적으로 보장된다.
    junction_y = neck_bounds[1] + neck_bounds[3]
    # 접합부 실효 변위로 각도 역산: body 격자는 edge-pin이라 접합부 변위가
    # "핀 행(0)과 내부 행(풀 회전 변위) 사이 보간"이다 — 이 보간 계수까지 넣어 정확히 ±8.
    row_ys = [body_bounds[1] + body_bounds[3] * i / 4 for i in range(5)]
    seg = next(i for i in range(4) if row_ys[i] <= junction_y <= row_ys[i + 1])
    frac = (junction_y - row_ys[seg]) / max(row_ys[seg + 1] - row_ys[seg], 1)
    arm_of = lambda i: 0.0 if i in (0, 4) else body_pivot[1] - row_ys[i]  # noqa: E731 — 핀 행은 변위 0
    eff_arm = max(arm_of(seg) * (1 - frac) + arm_of(seg + 1) * frac, 1.0)
    # SHOULDER-TRACK-001 v2: 진폭 상향 — 풀 스웨이 8px는 2048 캔버스에서 비가시 (주인님 "작동 안 함")
    sway_px = 18
    sway_deg = round(math.degrees(math.asin(min(sway_px / eff_arm, 0.5))), 2)
    tilt_deg = 2.2
    dx_carry = round(eff_arm * math.sin(math.radians(tilt_deg)), 1)
    keyform_bindings += [
        binding_r("ParamBodyAngleX", -10, "body_warp", rotate=-sway_deg),
        binding_r("ParamBodyAngleX", 10, "body_warp", rotate=sway_deg),
        binding("ParamBodyAngleX", -10, "upper_warp", tx=-sway_px),
        binding("ParamBodyAngleX", 10, "upper_warp", tx=sway_px),
        binding("ParamBodyAngleX", -10, "back_hair_warp", tx=-sway_px),
        binding("ParamBodyAngleX", 10, "back_hair_warp", tx=sway_px),
        binding_r("ParamBodyAngleZ", -10, "body_warp", rotate=-tilt_deg),
        binding_r("ParamBodyAngleZ", 10, "body_warp", rotate=tilt_deg),
        binding("ParamBodyAngleZ", -10, "upper_warp", tx=-dx_carry),
        binding("ParamBodyAngleZ", 10, "upper_warp", tx=dx_carry),
        binding("ParamBodyAngleZ", -10, "back_hair_warp", tx=-dx_carry),
        binding("ParamBodyAngleZ", 10, "back_hair_warp", tx=dx_carry),
    ]

    part_opacity_keyframes = build_opacity_curves(use_arap, use_mouth_states, use_mouth_warp, bbox_by_id)

    physics_profiles = build_physics_profiles(use_hair_chunks, bbox_by_id)

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
        "vertex_weights": build_vertex_weights(meshes, bbox_by_id),
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
        "render_mode": "mesh",  # MESH-DEFORM-001 (sprite로 바꾸면 폴백)
        "notes": ["autorig v0"],
    }
    write_json(out / "mini_rig.json", mini_rig)
    print(f"rig: parts={len(parts)} meshes={len(meshes)} deformers={len(deformers)} params={len(parameters)} bindings={len(keyform_bindings)} opacity_curves={len(part_opacity_keyframes)}")
    print(f"project: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

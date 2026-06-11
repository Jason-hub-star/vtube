"""리그 키폼 데이터 빌더 — build_autorig_rig_v0에서 기계적 분리 (2026-06-11 정비, 500줄 룰).

파라미터 정의 / 키폼 바인딩 / 파트 불투명 커브 / 물리 프로파일.
전부 순수 데이터 생성 함수 — 픽셀·파일 접근 없음. 수치의 출처는 evidence log
(v21 입 패턴, CHAIN-001, v0-3 물리 이식) — 변경 시 해당 엔트리를 함께 갱신할 것.
"""

from __future__ import annotations


def build_parameters() -> list[dict]:
    return [
        {"id": "ParamAngleX", "min": -30, "max": 30, "default": 0, "key_values": [-30, 0, 30]},
        {"id": "ParamAngleY", "min": -30, "max": 30, "default": 0, "key_values": [-30, 0, 30]},
        {"id": "ParamAngleZ", "min": -30, "max": 30, "default": 0, "key_values": [-30, 0, 30]},
        {"id": "ParamBodyAngleX", "min": -10, "max": 10, "default": 0, "key_values": [-10, 0, 10]},
        {"id": "ParamBodyAngleY", "min": -10, "max": 10, "default": 0, "key_values": [-10, 0, 10]},
        {"id": "ParamBodyAngleZ", "min": -10, "max": 10, "default": 0, "key_values": [-10, 0, 10]},  # BODY-SWAY-001 몸 기울기
        {"id": "ParamBreath", "min": 0, "max": 1, "default": 0, "key_values": [0, 1]},
        {"id": "ParamEyeBallX", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
        {"id": "ParamEyeBallY", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
        {"id": "ParamEyeLOpen", "min": 0.27, "max": 1, "default": 1, "key_values": [0.27, 0.5, 1]},
        {"id": "ParamEyeROpen", "min": 0.27, "max": 1, "default": 1, "key_values": [0.27, 0.5, 1]},
        {"id": "ParamBrowLY", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
        {"id": "ParamBrowRY", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
        {"id": "ParamHairFront", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
        {"id": "ParamHairBack", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
        {"id": "ParamMouthOpenY", "min": 0, "max": 0.85, "default": 0.0, "key_values": [0, 0.5, 0.85]},
        # EXPR-002 눈웃음 (곡선 A — 주인님 후보 선택 2026-06-11, smile_candidates 리포트)
        {"id": "ParamEyeSmile", "min": 0, "max": 1, "default": 0, "key_values": [0, 1]},
    ]


def binding(param, key, target, tx=0.0, ty=0.0, sx=1.0, sy=1.0):
    return {"parameter_id": param, "key_value": key, "target_id": target, "delta_type": "deformer_transform",
            "deltas": {"translate": [tx, ty], "scale": [sx, sy], "rotate": 0, "opacity": 1}}


def binding_r(param, key, target, tx=0.0, ty=0.0, sx=1.0, sy=1.0, rotate=0.0):
    b = binding(param, key, target, tx=tx, ty=ty, sx=sx, sy=sy)
    b["deltas"]["rotate"] = rotate
    return b


def build_keyform_bindings() -> list[dict]:
    return [
        binding("ParamAngleX", -30, "head_angle_warp", tx=-22),
        binding("ParamAngleX", 30, "head_angle_warp", tx=22),
        binding("ParamAngleY", -30, "head_angle_warp", ty=-12),
        binding("ParamAngleY", 30, "head_angle_warp", ty=12),
        # 목 자체 바인딩: 머리 미세 추종 (몸 추종은 upper_warp 상속 — CHAIN-001에서 이중 적용 제거)
        binding("ParamAngleX", -30, "neck_warp", tx=-5),
        binding("ParamAngleX", 30, "neck_warp", tx=5),
        binding("ParamAngleY", -30, "neck_warp", ty=-3),
        binding("ParamAngleY", 30, "neck_warp", ty=3),
        binding_r("ParamAngleZ", -30, "neck_warp", rotate=-3),  # 공식 首の曲面: 갸우뚱 목 동조
        binding_r("ParamAngleZ", 30, "neck_warp", rotate=3),
        binding_r("ParamAngleZ", -30, "head_angle_warp", rotate=-10),
        binding_r("ParamAngleZ", 30, "head_angle_warp", rotate=10),
        # CHAIN-001 upper_warp = 공식 首の位置: 몸 스웨이·호흡이 머리·목·뒷머리를 통째로 운반
        # (진폭은 body_warp와 동일 — 목 경계 상대 슬립 0)
        binding("ParamBodyAngleX", -10, "upper_warp", tx=-8),
        binding("ParamBodyAngleX", 10, "upper_warp", tx=8),
        binding("ParamBodyAngleY", -10, "upper_warp", ty=-5),
        binding("ParamBodyAngleY", 10, "upper_warp", ty=5),
        binding("ParamBreath", 1, "upper_warp", ty=-2),
        # CHAIN-001 뒷머리 감쇠 추종 (head ±22의 60%) + 갸우뚱 호 + 흔들림 파라미터
        binding("ParamAngleX", -30, "back_hair_warp", tx=-13),
        binding("ParamAngleX", 30, "back_hair_warp", tx=13),
        binding("ParamAngleY", -30, "back_hair_warp", ty=-7),
        binding("ParamAngleY", 30, "back_hair_warp", ty=7),
        binding_r("ParamAngleZ", -30, "back_hair_warp", rotate=-5),
        binding_r("ParamAngleZ", 30, "back_hair_warp", rotate=5),
        binding("ParamHairBack", -1, "back_hair_warp", tx=-10),
        binding("ParamHairBack", 1, "back_hair_warp", tx=10),
        # 뒷머리 몸 탑승 (upper 미소속이라 자체 바인딩 — 전체 균일이라 내부 시어 없음)
        binding("ParamBodyAngleX", -10, "back_hair_warp", tx=-8),
        binding("ParamBodyAngleX", 10, "back_hair_warp", tx=8),
        binding("ParamBodyAngleY", -10, "back_hair_warp", ty=-5),
        binding("ParamBodyAngleY", 10, "back_hair_warp", ty=5),
        binding("ParamBreath", 1, "back_hair_warp", ty=-2),
        # BODY-SWAY-001: rotate ±1.2 제거 — 운반(upper/back_hair)은 tx만이라 회전분이 접합부
        # 슬립이 됐다 (상시 스웨이로 노출, "참수" 보고). 몸 기울기는 BodyAngleZ가 전담.
        binding("ParamBodyAngleX", -10, "body_warp", tx=-8),
        binding("ParamBodyAngleX", 10, "body_warp", tx=8),
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
        binding("ParamBrowLY", -1, "L_brow", ty=8),
        binding("ParamBrowLY", 1, "L_brow", ty=-8),
        binding("ParamBrowRY", -1, "R_brow", ty=8),
        binding("ParamBrowRY", 1, "R_brow", ty=-8),
        # 깜빡임 형태는 ARAP 패치가 담당, 워프는 미세 눌림만 (validator: 파라미터당 바인딩 필수)
        binding("ParamEyeLOpen", 0.27, "eye_L_warp", sy=0.97),
        binding("ParamEyeROpen", 0.27, "eye_R_warp", sy=0.97),
        binding("ParamHairFront", -1, "front_hair_warp", tx=-10),  # 음수 키 부재 시 -1쪽이 무동작이었다 (CHAIN-001 정비)
        binding("ParamHairFront", 1, "front_hair_warp", tx=10),
        binding("ParamMouthOpenY", 0.5, "mouth_warp", ty=0.8, sy=1.01),
        binding("ParamMouthOpenY", 0.85, "mouth_warp", ty=1.6, sy=1.02),
    ]


def attach_mouth_height_keyforms(meshes: list[dict], bbox_by_id: dict) -> list[str]:
    """입 상태 스프라이트에 연속 입높이 정점 키폼 부착 (MOUTH-KEYFORM-001 — 눈 패턴 이식).

    크로스페이드 잔상의 원인은 겹치는 두 상태의 기하 불일치 — 모든 상태를 공통
    입높이 함수 H(v)에 맞춰 세로 워프시키면, 어느 v에서든 겹치는 쌍의 높이가 같아
    교차 지점 윤곽이 일치한다 (입은 외형 변화라 스프라이트 유지 — 기하만 정렬).
    H(v) = 각 상태의 가시 피크에서 자기 실측 높이를 지나는 구간별 선형.
    앵커 = 자기 bbox 상단 (윗입술 고정, 개방은 턱이 아래로 떨어지는 방향).
    """
    peaks = [("mouth_state_small", 0.35), ("mouth_state_mid", 0.58), ("mouth_state_wide", 0.85)]
    if any(pid not in bbox_by_id for pid, _ in peaks):
        return []
    heights = {pid: max(bbox_by_id[pid][3], 1) for pid, _ in peaks}
    # 등장 직전(0.18)의 타깃 = small의 55% — 닫힌 입선에서 자라나는 연출
    breakpoints = [(0.18, heights["mouth_state_small"] * 0.55)] + [(v, heights[pid]) for pid, v in peaks]
    attached = []
    for pid, _peak in peaks:
        mesh = next((m for m in meshes if m["part_id"] == pid), None)
        if mesh is None:
            continue
        top = bbox_by_id[pid][1]
        keys = []
        for v, target in breakpoints:
            s = target / heights[pid]
            keys.append({"value": v, "vertices": [[x, round(top + (y - top) * s, 1)] for x, y in mesh["vertices"]]})
        mesh["vertex_keyforms"] = {"parameter_id": "ParamMouthOpenY", "keys": keys}
        attached.append(pid)
    return attached


def curve(part, param, points):
    return {"part_id": part, "parameter_id": param, "mode": "linear",
            "keyframes": [{"value": v, "opacity": o} for v, o in points]}


def build_opacity_curves(use_arap: bool, use_mouth_states: bool, use_mouth_warp: bool, bbox_by_id: dict) -> list[dict]:
    part_opacity_keyframes = []
    if use_arap:
        # EYE-NATURAL-002: 깜빡임 패치 1장 + 정점 키폼 (메시 vertex_keyforms가 감김 담당).
        # 완전 열림(v=1)에서만 숨김 — 0.97~1.0 페이드 구간은 워프 t≤0.04 ≈ 항등이라
        # 밑의 생눈과 픽셀이 같아 전환이 보이지 않는다 (크로스페이드 잔상 폐기).
        for side in ("L", "R"):
            part_opacity_keyframes.append(
                curve(f"eye_{side}_blink", f"ParamEye{side}Open", [(0.27, 1.0), (0.97, 1.0), (1.0, 0.0)]))
            # EXPR-002 눈웃음 패치: 페이드는 워프≈항등인 0~0.06 구간에만 (잔상 원리 동일).
            # 수동 발동 전용 — 트래킹 자동 연동은 육안 합격 후에만 (EXPR-001 롤백 교훈)
            part_opacity_keyframes.append(
                curve(f"eye_{side}_smile", "ParamEyeSmile", [(0.0, 0.0), (0.06, 1.0), (1.0, 1.0)]))
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
        # MOUTH-SNAP-001: 겹침 없는 하드 밴드 — 크로스페이드(다른 작화 두 장의 투명도 혼합 =
        # 반투명 이빨 잔상)는 원리적 한계라 폐기. 경계값(0.24/0.47/0.72)에서 양쪽 상태가
        # 같은 H(v) 높이로 워프돼 있어(attach_mouth_height_keyforms) 윤곽은 연속, 내용만 스왑.
        # 근본 해결(부품형 입 — 입술 키폼 + 입안 클리핑)은 004 MOUTH-PARTS-001.
        part_opacity_keyframes += [
            curve("mouth_line", "ParamMouthOpenY", [(0.0, 1.0), (0.24, 1.0), (0.245, 0.0), (1.0, 0.0)]),
            curve("mouth_state_small", "ParamMouthOpenY", [(0.0, 0.0), (0.24, 0.0), (0.245, 1.0), (0.47, 1.0), (0.475, 0.0), (1.0, 0.0)]),
            curve("mouth_state_mid", "ParamMouthOpenY", [(0.0, 0.0), (0.47, 0.0), (0.475, 1.0), (0.72, 1.0), (0.725, 0.0), (1.0, 0.0)]),
            curve("mouth_state_wide", "ParamMouthOpenY", [(0.0, 0.0), (0.72, 0.0), (0.725, 1.0), (1.0, 1.0)]),
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
    return part_opacity_keyframes


def build_body_sway_springs() -> list[dict]:
    """BODY-SWAY-001: 파라미터 스프링 — 출력이 파트가 아니라 BodyAngle 파라미터를 구동.

    strong20 실측 1위 패턴(물리 출력 카테고리 body_angle 123개)의 이식. 머리 움직임의
    잔여 에너지가 스프링-댐퍼를 거쳐 몸을 반 박자 늦게 따라가게 하고(follow-through),
    멈추면 잔진동이 천천히 가라앉는다. Breath 입력으로 정지 상태에도 미세 스웨이.
    output_parameter가 있는 프로파일은 런타임 stepPhysics가 매 스텝 해당 파라미터에
    offset[0]을 쓴다 — BodyAngle 바인딩(body/upper/back_hair)이 전부 자동 동행.
    """
    return [
        {"id": "body_sway_spring", "targets": [], "output_parameter": "ParamBodyAngleX",
         "stiffness": 0.05, "damping": 0.92, "drag": 0.0, "max_offset": [10, 0],
         "input_weights": {"ParamAngleX": [7.0, 0], "ParamBreath": [1.2, 0]}},
        {"id": "body_tilt_spring", "targets": [], "output_parameter": "ParamBodyAngleZ",
         "stiffness": 0.045, "damping": 0.93, "drag": 0.0, "max_offset": [8, 0],
         "input_weights": {"ParamAngleZ": [5.0, 0], "ParamBreath": [-0.8, 0]}},
    ]


def build_physics_profiles(use_hair_chunks: bool, bbox_by_id: dict) -> list[dict]:
    # Phase C: 물리 스프링 — v0-3 검증 프로파일 이식 (덩어리 사용 시)
    if not use_hair_chunks:
        return build_body_sway_springs()
    physics_profiles = [
        {
            "id": "front_hair_soft_spring",
            "targets": ["hair_front_L", "hair_front_C", "hair_front_R"],
            "anchor": "top_center", "mass": 0.8, "stiffness": 0.13, "damping": 0.82, "drag": 0.03,
            "max_offset": [34, 28], "rotate_factor": 0.055,
            "input_weights": {"ParamAngleX": [-24, 3], "ParamAngleY": [0, 6], "ParamBodyAngleX": [-8, 2], "ParamHairFront": [24, 0]},
            "part_weights": {"hair_front_L": 1.0, "hair_front_C": 0.7, "hair_front_R": 1.0},
        },
        {
            "id": "back_hair_heavy_spring",
            "targets": ["hair_back_L", "hair_back_R"] + (["shoulder_hair"] if "shoulder_hair" in bbox_by_id else []),
            "anchor": "top_center", "mass": 1.4, "stiffness": 0.08, "damping": 0.88, "drag": 0.04,
            "max_offset": [24, 34], "rotate_factor": 0.03,
            "input_weights": {"ParamAngleX": [-18, 8], "ParamAngleY": [0, 8], "ParamBodyAngleX": [-6, 3]},
            "part_weights": {"hair_back_L": 1.0, "hair_back_R": 1.0, "shoulder_hair": 0.7},
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
    return [p for p in physics_profiles if p["targets"]] + build_body_sway_springs()

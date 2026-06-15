"""리그 키폼 데이터 빌더 — build_autorig_rig_v0에서 기계적 분리 (2026-06-11 정비, 500줄 룰).

파라미터 정의 / 키폼 바인딩 / 파트 불투명 커브 / 물리 프로파일.
전부 순수 데이터 생성 함수 — 픽셀·파일 접근 없음. 수치의 출처는 evidence log
(v21 입 패턴, CHAIN-001, v0-3 물리 이식) — 변경 시 해당 엔트리를 함께 갱신할 것.
"""

from __future__ import annotations


# 004 사이클: 표정 시트(EXPR-003)·액센트 시트 셀 이름 — 추출기와 곡선·파트 명명의 SSOT
EXPRESSION_NAMES = ("smile", "wink", "surprise", "jito", "squeeze", "heart")
ACCENT_PARAMS = {"blush": "ParamCheek", "gloom": "ParamGloom", "tear": "ParamTear", "sweat": "ParamSweat"}
MOUTH_PART_IDS = ("mouth_parts_interior", "mouth_parts_teeth", "mouth_parts_tongue",
                  "mouth_parts_upper_lip", "mouth_parts_lower_lip")
# MOUTH-LIP-RIDE-001 (004 H2 4차): 닫힘(마스터 미소선)과 열림(시트 윗입술)이 다른 작화라
# 스왑 경계에서 윗입술이 점프 = "미소선 밑에 새 입". 미소선(mouth_line)을 윗입술로 승격하면
# 닫힘/열림이 같은 작화 → 미소곡선이 제자리에서 그대로 열린다. 시트 윗입술 부품은 폐기,
# 아래 4종만 미소선 아래로 펼친다 (입안 윗경계는 미소선이 가린다).
MOUTH_LOWER_IDS = ("mouth_parts_interior", "mouth_parts_teeth",
                   "mouth_parts_tongue", "mouth_parts_lower_lip")
# MOUTH-LIP-PARTS (004 H2 5차, 주인님 "입 시트로 일관 처리"): 윗입술(고정)+아랫입술(개폐)+입안.
# 입안 3종은 윗입술~아랫입술 사이라 닫힘에선 안 보이게 opacity 페이드. 아랫입술(lower_lip)은
# 항상 켜진 채 H(v)로 닫힘(윗입술에 붙음)~열림(하강) — 닫힘=윗입술+아랫입술이 위벨 미소.
MOUTH_CAVITY_IDS = ("mouth_parts_interior", "mouth_parts_teeth", "mouth_parts_tongue")
# 표정 활성 시 숨길 기본 눈 계열 (존재하는 것만 곡선 부착)
BASE_EYE_PART_IDS = ("L_eye_white", "R_eye_white", "L_iris", "R_iris",
                     "L_upper_lash", "R_upper_lash", "L_lower_lash", "R_lower_lash",
                     "L_brow", "R_brow", "eye_L_blink", "eye_R_blink", "eye_L_smile", "eye_R_smile")


def build_parameters(use_eye_expr: bool = False, use_accents: bool = False) -> list[dict]:
    extra = []
    if use_eye_expr:
        # 표정 셀렉터: 0=없음, k=EXPRESSION_NAMES[k-1] (하드 밴드 — MOUTH-SNAP 패턴)
        extra.append({"id": "ParamEyeExpr", "min": 0, "max": 6, "default": 0,
                      "key_values": [0, 1, 2, 3, 4, 5, 6]})
    if use_accents:
        for param in ("ParamCheek", "ParamGloom", "ParamTear", "ParamSweat"):
            extra.append({"id": param, "min": 0, "max": 1, "default": 0, "key_values": [0, 1]})
    return extra + [
        {"id": "ParamAngleX", "min": -30, "max": 30, "default": 0, "key_values": [-30, 0, 30]},
        {"id": "ParamAngleY", "min": -30, "max": 30, "default": 0, "key_values": [-30, 0, 30]},
        {"id": "ParamAngleZ", "min": -30, "max": 30, "default": 0, "key_values": [-30, 0, 30]},
        {"id": "ParamBodyAngleX", "min": -10, "max": 10, "default": 0, "key_values": [-10, 0, 10]},
        {"id": "ParamBodyAngleY", "min": -10, "max": 10, "default": 0, "key_values": [-10, 0, 10]},
        {"id": "ParamBodyAngleZ", "min": -10, "max": 10, "default": 0, "key_values": [-10, 0, 10]},  # BODY-SWAY-001 몸 기울기
        # SHOULDER-TRACK-001 입력 채널 — 디포머 무바인딩, 몸 스프링의 입력 전용
        # (트래킹이 자유롭게 쓰고, 스프링이 노이즈를 거른 뒤 BodyAngle을 구동)
        {"id": "ParamBodyTrackX", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
        {"id": "ParamBodyTrackZ", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
        {"id": "ParamBreath", "min": 0, "max": 1, "default": 0, "key_values": [0, 1]},
        {"id": "ParamEyeBallX", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
        {"id": "ParamEyeBallY", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
        {"id": "ParamEyeLOpen", "min": 0.27, "max": 1, "default": 1, "key_values": [0.27, 0.5, 1]},
        {"id": "ParamEyeROpen", "min": 0.27, "max": 1, "default": 1, "key_values": [0.27, 0.5, 1]},
        {"id": "ParamBrowLY", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
        {"id": "ParamBrowRY", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
        {"id": "ParamHairFront", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
        {"id": "ParamHairBack", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
        {"id": "ParamMouthOpenY", "min": 0, "max": 1, "default": 0.0, "key_values": [0, 0.5, 1]},
        {"id": "ParamMouthForm", "min": -1, "max": 1, "default": 0.0, "key_values": [-1, 0, 1]},
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
        # HEAD-Z-PIVOT-001: Z 기울임은 전용 비핀 회전 디포머 (edge-pin 격자에 넣으면
        # 실루엣 고정 + 내부 시어 — 004 H2 "기준점이 목" 판정). 피벗 = 턱 관절.
        binding_r("ParamAngleZ", -30, "head_z_warp", rotate=-10),
        binding_r("ParamAngleZ", 30, "head_z_warp", rotate=10),
        # ANGLE-FORESHORTEN-001: 돌릴 때 머리 윤곽을 가로 12% 압축 = 원근 단축(foreshortening).
        # edge-pin head_angle_warp는 윤곽 고정이라 sx 무효 → 비핀 head_z_warp(얼굴+앞머리)에
        # 부여, back_hair_warp도 동기 압축(아래)해야 앞/뒷머리 이음새 유지. 어깨가닥은 압축 제외
        # (deformer_of → upper_warp). Izumi 분석 근거(각도=메시 원근변형). 8062 캡처·정합 PASS 확인.
        binding("ParamAngleX", -30, "head_z_warp", sx=0.88),
        binding("ParamAngleX", 30, "head_z_warp", sx=0.88),
        # ANGLE-FORESHORTEN-001 R4: 끄덕임(AngleY)도 세로 원근 단축 — 끄덕일 때 얼굴 세로 압축.
        # X의 sx와 대칭(비핀 head_z_warp). back_hair_warp 동기(아래). 위벨은 머리카락이 정수리를
        # 덮어 체감 작지만 얼굴 보이는 캐릭터(005)엔 큼. 8062 캡처(sy 0.78 강테스트)로 작동 확증.
        binding("ParamAngleY", -30, "head_z_warp", sy=0.85),
        binding("ParamAngleY", 30, "head_z_warp", sy=0.85),
        # CHAIN-001 upper_warp = 공식 首の位置: 몸 스웨이·호흡이 머리·목·뒷머리를 통째로 운반
        # (진폭은 body_warp와 동일 — 목 경계 상대 슬립 0)
        # BodyAngleX 운반(tx)은 빌더가 sway_px로 부여 (몸 진자 회전의 접합부 실효 변위와 결합)
        binding("ParamBodyAngleY", -10, "upper_warp", ty=-8),
        binding("ParamBodyAngleY", 10, "upper_warp", ty=8),
        binding("ParamBreath", 1, "upper_warp", ty=-2),
        # CHAIN-001 뒷머리 감쇠 추종 (head ±22의 60%) + 갸우뚱 호 + 흔들림 파라미터
        # ANGLE-FORESHORTEN-001: 뒷머리도 head_z_warp와 동기 가로압축(sx=0.88) — 안 하면
        # 앞머리·얼굴만 좁아져 뒷머리 이음새 29px 터짐(정합 FAIL). 둘 다 턱관절 피벗이라 동축.
        binding("ParamAngleX", -30, "back_hair_warp", tx=-13, sx=0.88),
        binding("ParamAngleX", 30, "back_hair_warp", tx=13, sx=0.88),
        # R4: 뒷머리도 head_z_warp와 세로 동기 압축(sy=0.85) — 앞/뒷머리 세로 이음새 유지.
        binding("ParamAngleY", -30, "back_hair_warp", ty=-7, sy=0.85),
        binding("ParamAngleY", 30, "back_hair_warp", ty=7, sy=0.85),
        # HEAD-Z-PIVOT-001 후속 (RIG-COHESION-001 실측: ±5는 앞/뒷머리 29px 어긋남):
        # Z 회전은 머리와 완전 동률 — 피벗 동일(턱 관절)이라 정적 어긋남 0, 지연은 물리 스프링 담당
        binding_r("ParamAngleZ", -30, "back_hair_warp", rotate=-10),
        binding_r("ParamAngleZ", 30, "back_hair_warp", rotate=10),
        binding("ParamHairBack", -1, "back_hair_warp", tx=-10),
        binding("ParamHairBack", 1, "back_hair_warp", tx=10),
        # 뒷머리 몸 탑승 (upper 미소속이라 자체 바인딩 — 전체 균일이라 내부 시어 없음; X는 빌더)
        binding("ParamBodyAngleY", -10, "back_hair_warp", ty=-8),
        binding("ParamBodyAngleY", 10, "back_hair_warp", ty=8),
        binding("ParamBreath", 1, "back_hair_warp", ty=-2),
        # BODY-SWAY-001 v3: body_warp의 BodyAngleX는 빌더가 기하 계산으로 부여 —
        # 골반 피벗 진자 회전 (균일 평행이동은 "종이인형 슬라이드" — 유기성 부재 판정)
        binding("ParamBodyAngleY", -10, "body_warp", ty=-8),
        binding("ParamBodyAngleY", 10, "body_warp", ty=8),
        # RIG-COHESION-001: sy 1.012는 골반 피벗 스케일이라 가슴 높이에서 ~13px 상승 —
        # 목·어깨가닥 접합 슬립의 주범. 호흡은 ty 중심 + 미세 sy (접합 슬립 ≤3px)
        binding("ParamBreath", 1, "body_warp", ty=-2, sy=1.002),
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
        binding("ParamMouthOpenY", 1, "mouth_warp", ty=1.6, sy=1.02),
        binding("ParamMouthForm", -1, "mouth_warp", ty=0.5, sx=0.96, sy=0.99),
        binding("ParamMouthForm", 1, "mouth_warp", ty=-0.3, sx=1.08, sy=1.01),
        # ANGLE-FORESHORTEN-001 라운드2: 2D 착시 정교화 (Izumi 비대칭 원근 근사).
        # 먼 눈 좁히기 — 돌아가는 쪽(먼) 눈만 가로 압축. +30=eye_R(image-left)이 먼 눈,
        # -30=eye_L(image-right)이 먼 눈. 회전 방향따라 비대칭이 뒤집힘(8062 캡처 좌우 확인).
        binding("ParamAngleX", 30, "eye_R_warp", sx=0.82),
        binding("ParamAngleX", -30, "eye_L_warp", sx=0.82),
        # 입 패럴랙스 — 입이 머리 윤곽(±22)보다 더 쏠림(±6 추가) = 앞면 입체 단서.
        binding("ParamAngleX", 30, "mouth_warp", tx=6),
        binding("ParamAngleX", -30, "mouth_warp", tx=-6),
        # 코 돌출(R3) — 가장 앞으로 튀어나온 특징이라 윤곽보다 가장 크게 쏠림(±8).
        binding("ParamAngleX", 30, "nose_warp", tx=8),
        binding("ParamAngleX", -30, "nose_warp", tx=-8),
    ]


def attach_cheek_keyforms(meshes: list[dict]) -> list[str]:
    """ANGLE-FORESHORTEN-001 R3: 얼굴 메시 먼쪽 볼 정점을 AngleX에서 안으로 압축(비대칭 원근).
    +30=image-left(저x) 볼 압축, -30=image-right(고x) 볼 압축. Izumi 頬 분리 등가 효과를
    파츠 분리 없이 vertex_keyforms로. 외곽+중하단 가중(이마·코는 거의 안 움직임). 머리카락이
    볼을 덮는 캐릭터는 체감 작지만 무해(정합 PASS)·범용.
    """
    import statistics
    face = next((m for m in meshes if m["part_id"] == "face_base"), None)
    if not face or not face.get("vertices"):
        return []
    V = [list(p) for p in face["vertices"]]
    xs = [x for x, _ in V]
    ys = [y for _, y in V]
    cx = statistics.median(xs)
    xr = max(xs) - min(xs)
    ymid = (min(ys) + max(ys)) / 2
    yh = max((max(ys) - min(ys)) / 2, 1)

    def compress(sign: int) -> list[list[float]]:
        out = []
        for x, y in V:
            far = (x < cx) if sign > 0 else (x > cx)
            yw = max(0.0, (y - ymid) / yh)              # 중하단 가중(턱·볼)
            ow = abs(x - cx) / max(xr * 0.5, 1)         # 외곽 가중
            if far and abs(x - cx) > xr * 0.20:
                out.append([x + (cx - x) * 0.16 * yw * ow, y])
            else:
                out.append([x, y])
        return out

    face["vertex_keyforms"] = {"parameter_id": "ParamAngleX", "keys": [
        {"value": -30, "vertices": compress(-1)},
        {"value": 0, "vertices": [list(p) for p in V]},
        {"value": 30, "vertices": compress(1)}]}
    return ["face_base"]


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


def attach_mouth_parts_keyforms(meshes: list[dict], bbox_by_id: dict, anchor_y: float) -> list[str]:
    """부품형 입 연속 개폐 (MOUTH-LIP-RIDE-001) — 미소선(윗입술) 아래로 펼치는 세로 스케일 H(v).

    하부 4종(입안·이빨·혀·아랫입술)이 공통 앵커=미소선 중심·공통 H(v)를 공유 →
    위쪽은 미소선에 고정되고 아래로만 펼쳐진다. 윗입술은 미소선이 담당(키폼 없음, 항상 고정).
    어느 v에서든 부품 간 상대 기하 불변이라 클립 정합이 구조적으로 보장된다.
    v=0 의 0.04는 '미소선 두께로 붕괴' — opacity 페이드(0~0.14)와 겹쳐 닫힘에서 안 보인다.
    """
    H = [(0.0, 0.04), (0.25, 0.30), (0.55, 0.62), (1.0, 1.0)]
    attached = []
    for pid in MOUTH_LOWER_IDS:
        mesh = next((m for m in meshes if m["part_id"] == pid), None)
        if mesh is None or pid not in bbox_by_id:
            continue
        keys = [{"value": v,
                 "vertices": [[x, round(anchor_y + (y - anchor_y) * h, 1)] for x, y in mesh["vertices"]]}
                for v, h in H]
        mesh["vertex_keyforms"] = {"parameter_id": "ParamMouthOpenY", "keys": keys}
        attached.append(pid)
    return attached


def attach_mouthform_line_keyforms(meshes: list[dict], bbox_by_id: dict) -> list[str]:
    """MouthForm 입꼬리 정점 키폼 — 닫힌 입선의 꼬리만 올리고(+1)/내린다(-1).

    정점 키폼은 메시당 파라미터 1개 (런타임 keyformBaseVertices 계약) — 부품형 입은
    MouthOpenY를 쓰므로, Form의 정점 키폼은 닫힌 mouth_line 전담. 열린 입의 Form은
    기존 mouth_warp 디포머 바인딩 근사 유지.
    """
    target = "mouth_parts_upper_lip" if "mouth_parts_upper_lip" in bbox_by_id else "mouth_line"
    mesh = next((m for m in meshes if m["part_id"] == target), None)
    if mesh is None or target not in bbox_by_id:
        return []
    x, _y, w, _h = bbox_by_id[target]
    cx = x + w / 2
    keys = []
    for v, amp in ((-1, 6.0), (0, 0.0), (1, -7.0)):  # 화면 y는 아래가 + — 음수 amp가 입꼬리 올림
        keys.append({"value": v, "vertices": [
            [vx, round(vy + amp * (abs(vx - cx) / max(w / 2, 1)) ** 1.6, 1)] for vx, vy in mesh["vertices"]]})
    mesh["vertex_keyforms"] = {"parameter_id": "ParamMouthForm", "keys": keys}
    return [target]


def curve(part, param, points):
    return {"part_id": part, "parameter_id": param, "mode": "linear",
            "keyframes": [{"value": v, "opacity": o} for v, o in points]}


def build_opacity_curves(use_arap: bool, use_mouth_states: bool, use_mouth_warp: bool, bbox_by_id: dict,
                         use_mouth_parts: bool = False, use_eye_expr: bool = False,
                         use_accents: bool = False) -> list[dict]:
    part_opacity_keyframes = []
    if use_eye_expr:
        # EXPR-003 표정 셀렉터: k 밴드에서 해당 오버레이만 표시 + 기본 눈 계열 숨김
        # (런타임은 파트별 곡선을 곱연산 — rig.js partOpacity — 이라 기존 깜빡임 곡선과 합성 가능)
        for k, name in enumerate(EXPRESSION_NAMES, start=1):
            part_opacity_keyframes.append(curve(
                f"eye_expr_{name}", "ParamEyeExpr",
                [(k - 0.55, 0.0), (k - 0.45, 1.0), (k + 0.45, 1.0), (k + 0.55, 0.0)]))
        hide = [(0.0, 1.0), (0.45, 1.0), (0.55, 0.0), (6.0, 0.0)]
        for pid in BASE_EYE_PART_IDS:
            if pid in bbox_by_id:
                part_opacity_keyframes.append(curve(pid, "ParamEyeExpr", hide))
    if use_accents:
        for name, param in ACCENT_PARAMS.items():
            if f"accent_{name}" in bbox_by_id:
                peak = 0.92 if name == "gloom" else 1.0  # 그늘은 살짝 투명 — 머리 위 오버레이
                part_opacity_keyframes.append(curve(f"accent_{name}", param, [(0.0, 0.0), (1.0, peak)]))
    if use_mouth_parts:
        # MOUTH-LIP-PARTS: 마스터 입선(mouth_line)은 위치 참조용으로 sources에 남되 항상 숨김 —
        # 다문 선 한 줄이라 윗입술로 부적합, 시트 upper_lip이 윗입술. (전 MouthOpenY값 opacity 0)
        part_opacity_keyframes.append(curve("mouth_line", "ParamMouthOpenY", [(0.0, 0.0), (1.0, 0.0)]))
        # 윗입술(upper_lip)·아랫입술(lower_lip)은 항상 켜짐(곡선 없음=1) — 닫힘에서 둘이 만나 위벨 미소.
        # 입안 3종만 살짝 벌릴 때 페이드 인(닫힘엔 윗/아랫입술 사이 붕괴+opacity 0).
        for pid in MOUTH_CAVITY_IDS:
            if pid in bbox_by_id:
                part_opacity_keyframes.append(
                    curve(pid, "ParamMouthOpenY", [(0.0, 0.0), (0.06, 0.0), (0.14, 1.0), (1.0, 1.0)]))
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
    if use_mouth_parts:
        pass  # 위에서 처리 (부품형 입이 상태 스왑 곡선을 대체)
    elif use_mouth_states:
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
    # SHOULDER-TRACK-001: 입력 = ParamBodyTrack* (어깨 실측, 없으면 드라이브가 머리 기반 폴백 주입).
    # 강성을 올려 1:1에 가깝게 — 스프링은 지연 추종 연출 + Pose 노이즈 필터 역할만.
    return [
        {"id": "body_sway_spring", "targets": [], "output_parameter": "ParamBodyAngleX",
         "stiffness": 0.12, "damping": 0.85, "drag": 0.0, "max_offset": [10, 0],
         "input_weights": {"ParamBodyTrackX": [9.0, 0], "ParamBreath": [1.2, 0]}},
        {"id": "body_tilt_spring", "targets": [], "output_parameter": "ParamBodyAngleZ",
         "stiffness": 0.10, "damping": 0.86, "drag": 0.0, "max_offset": [8, 0],
         "input_weights": {"ParamBodyTrackZ": [8.0, 0], "ParamBreath": [-0.8, 0]}},
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
            # ANGLE-FORESHORTEN-001: shoulder_hair는 upper_warp(몸추종)로 이동했으므로 머리카락
            # 물리에서 제외 — 디포머(몸)/물리(머리) 모순 방지. 어깨 앵커라 정적이 자연스럽다.
            "targets": ["hair_back_L", "hair_back_R"],
            "anchor": "top_center", "mass": 1.4, "stiffness": 0.08, "damping": 0.88, "drag": 0.04,
            "max_offset": [24, 34], "rotate_factor": 0.03,
            "input_weights": {"ParamAngleX": [-18, 8], "ParamAngleY": [0, 8], "ParamBodyAngleX": [-6, 3]},
            "part_weights": {"hair_back_L": 1.0, "hair_back_R": 1.0},
        },
        # CLOTH-PHYS-001: 옷 드레이프 — 공식 스커트 그룹 실측 정박 (all57 분석):
        # 입력 = BodyAngleX(X)+BodyAngleZ(Angle) weight 100/100 (Hiyori·koharu·tsumiki·miara·Rice 6모델 균일).
        # Breath 직접 입력은 공식 선례 0건 — body_sway_spring 체이닝으로 간접 전달된다.
        # 반응 속도: 공식 스커트 Delay 0.6 vs 뒷머리 0.8 → 뒷머리 stiffness 0.08 × 0.75 = 0.06.
        # 진폭: 공식 반경×Mobility 비율(10×0.9/15×0.95≈0.63) × 뒷머리 24px ≈ 15px → 14px 보수 시작.
        # damping/mass는 엔진 고유 상수(공식 대응물 없음) — H2-mini 육안 게이트에서 튜닝.
        {
            "id": "clothes_drape_spring",
            "targets": ["clothes"] if "clothes" in bbox_by_id else [],
            "anchor": "top_center", "mass": 1.6, "stiffness": 0.06, "damping": 0.90, "drag": 0.04,
            "max_offset": [14, 6], "rotate_factor": 0.0,
            "input_weights": {"ParamBodyAngleX": [-10, 0], "ParamBodyAngleZ": [-10, 0]},
            "part_weights": {"clothes": 1.0},
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

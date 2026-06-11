"""EXPR-001 표정 자산 생성 — 볼 홍조 오버레이, 입꼬리 정점 키폼.

빌더(build_autorig_rig_v0)에서 사용. 수치 출처: evidence log "EXPR-001".
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


def make_cheek_blush(face_path: Path, eye_boxes: list, dest: Path) -> None:
    """볼 홍조 오버레이 PNG — 피부 중앙값을 붉은 쪽으로 섞은 부드러운 타원 2개.

    위치는 눈 bbox에서 결정론적으로 파생 (눈 아래 0.55h). 생성 픽셀이지만
    단색 그라데이션 오버레이라 스타일 드리프트 없음 (eye socket cover 전례).
    """
    face = np.asarray(Image.open(face_path).convert("RGBA"))
    canvas = np.zeros_like(face)
    yy, xx = np.mgrid[0:face.shape[0], 0:face.shape[1]].astype(np.float64)
    for x0, y0, x1, y1 in eye_boxes:
        w, h = x1 - x0, y1 - y0
        cx, cy = (x0 + x1) / 2, y1 + h * 0.55
        rx, ry = w * 0.62, h * 0.42
        d2 = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
        mask = d2 < 1
        if not mask.any():
            continue
        region = face[mask]
        opaque = region[:, 3] > 200
        skin = np.median(region[opaque][:, :3], axis=0) if opaque.any() else np.array([240, 200, 195])
        tint = (skin * 0.45 + np.array([255, 105, 125]) * 0.55).astype(np.uint8)
        alpha = np.zeros(face.shape[:2])
        alpha[mask] = (1 - d2[mask]) ** 2 * 165
        stronger = alpha > canvas[..., 3]
        canvas[stronger, :3] = tint
        canvas[stronger, 3] = alpha[stronger].astype(np.uint8)
    canvas[..., 3] = np.minimum(canvas[..., 3], face[..., 3])  # 얼굴 알파 밖으로 안 나감
    Image.fromarray(canvas, "RGBA").save(dest)


def attach_mouth_form_keyforms(mesh: dict, bbox: list) -> None:
    """mouth_line 메시에 입꼬리 키폼 부착 — +1 양끝 올림(미소), -1 내림.

    중앙 30%는 고정, 꼬리로 갈수록 제곱 프로파일로 상승 — 컬럼 통째 이동이라
    스트로크가 곡선으로 휜다 (구멍 없음: 밑은 seethrough 복원 피부).
    """
    x, y, w, h = bbox
    cx = x + w / 2
    half = max(w / 2, 1e-6)

    def shifted(sign: float) -> list:
        verts = []
        for vx, vy in mesh["vertices"]:
            wx = max(-1.0, min(1.0, (vx - cx) / half))
            lift = (max(0.0, abs(wx) - 0.3) / 0.7) ** 2
            dy = -sign * lift * h * (0.55 if sign > 0 else 0.4)
            dx = wx * lift * w * 0.03 * sign
            verts.append([round(vx + dx, 1), round(vy + dy, 1)])
        return verts

    mesh["vertex_keyforms"] = {
        "parameter_id": "ParamMouthForm",
        "keys": [
            {"value": -1.0, "vertices": shifted(-1.0)},
            {"value": 0.0, "vertices": [list(v) for v in mesh["vertices"]]},  # 명시적 항등 키 필수
            {"value": 1.0, "vertices": shifted(1.0)},
        ],
    }

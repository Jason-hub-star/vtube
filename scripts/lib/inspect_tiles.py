"""rig 인스펙터 동적 스윕 측정 타일 — inspect_autorig_rig에서 기계적 분리 (2026-06-12 자기리뷰, 500줄 룰).

고정 격자 + 파라미터 영향 파트 bbox 측정점. 무반응(dead) 판정의 커버리지를 결정한다 —
변경 시 evidence log AUTORIG-CHARACTER-004-FULLRUN-MOUTH-PARTS-EXPR-001 래칫 항목 참조.
"""

from __future__ import annotations

from typing import Any

def dynamic_tiles(canvas: list[int], parts: list[dict[str, Any]] | None = None) -> list[dict[str, int]]:
    width, height = int(canvas[0]), int(canvas[1])
    tiles = []
    for y in (0.28, 0.42, 0.56, 0.70):
        for x in (0.32, 0.44, 0.56, 0.68):
            tiles.append({"x": max(0, int(width * x) - 32), "y": max(0, int(height * y) - 32), "w": 64, "h": 64})
    # 고정 격자는 소형 부위(눈·입·눈썹)와 평탄 영역 변화를 놓친다 (003 실측: 해시는 전부
    # 변하는데 Δ=0 보고) — 파라미터 영향 파트의 bbox 중심 타일을 추가
    seen: set[tuple[int, int]] = set()
    for part in parts or []:
        pid = str(part.get("id", "")).lower()
        if not any(k in pid for k in ("eye", "iris", "mouth", "brow", "neck", "hair", "shoulder", "clothes", "accent", "expr")):
            continue
        x, y, w, h = part.get("bbox", [0, 0, 0, 0])
        if w <= 4:
            continue
        # 004 실측: 중심 1점은 빈 중앙(볼터치 좌/우 쌍의 bbox 중심 = 콧등)과 끝점 변형
        # (MouthForm 입꼬리 — 중앙은 의도적 고정)을 놓친다 → 가로 분할점 + 입꼬리 끝점 추가
        points = [(0.5, 0.5)]
        if w > 120:
            points += [(0.25, 0.5), (0.75, 0.5)]
        if "mouth" in pid:
            points += [(0.04, 0.5), (0.96, 0.5)]
        for fx, fy in points:
            cx, cy = int(x + w * fx), int(y + h * fy)
            key = (cx // 48, cy // 48)
            if key in seen:
                continue
            seen.add(key)
            tiles.append({"x": max(0, cx - 32), "y": max(0, cy - 32), "w": 64, "h": 64})
    return tiles[:64]

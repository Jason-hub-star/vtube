"""리그 메시 기하 헬퍼 — build_autorig_rig_v0에서 기계적 분리 (2026-06-12 자기리뷰, 500줄 룰).

격자 메시 생성 / 알파 bbox / bounds 패딩 / 물리 정점 가중 — 전부 순수 함수.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

CANVAS = 2048


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

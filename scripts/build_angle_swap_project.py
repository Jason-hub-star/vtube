#!/usr/bin/env python3
"""각도 스왑 미니 프로젝트 빌더 (ANGLE-SWAP-001) — 5각도 작화 + ParamAngleX opacity 스왑.

extract_angle_sheet가 만든 head_angle_0..4.png를 sprite 파트로 묶고, 입 4상태 스냅
패턴(rig_keyforms.curve)을 ParamAngleX에 이식해 각도 구간별 하드 밴드 스왑한다.
런타임 변경 0 — partOpacity가 임의 파라미터 곡선을, draw_pixi가 메시 없는 sprite를 지원.

좌향 전용 검증 미니: AngleX 0(정면)~ANGLE_MIN(측면). 표정/눈/입 없음.

사용: python3 scripts/build_angle_swap_project.py --project experiments/autorig-character-004/angle_swap_project
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.rig_keyforms import curve  # noqa: E402
from lib.rig_mesh import alpha_stats  # noqa: E402
from lib.vtube_io import ROOT, now_iso, write_json  # noqa: E402

CANVAS = 2048
ANGLE_MIN = -80.0   # 완전 측면 (정면=0)


def angle_opacity_curve(pid: str, i: int, n: int, edges: list[float]) -> dict:
    """각도 i를 [edges[i+1], edges[i]] 구간에서만 표시 (하드 밴드 스냅, 입 4상태 패턴)."""
    lo, hi = edges[i + 1], edges[i]   # lo < hi (둘 다 ≤ 0)
    amin, amax = edges[-1], edges[0]  # ANGLE_MIN, 0
    eps = 0.4
    pts = []
    # 측면 끝(amin): 마지막 각도만 on
    pts.append((amin, 1.0 if i == n - 1 else 0.0))
    if lo > amin + eps:
        pts.append((lo - eps, 0.0))
    pts.append((lo, 1.0))
    pts.append((hi, 1.0))
    if hi < amax - eps:
        pts.append((hi + eps, 0.0))
    # 정면 끝(amax=0): 첫 각도만 on
    pts.append((amax, 1.0 if i == 0 else 0.0))
    pts = sorted(dict(pts).items())  # value 오름차순, 중복 제거
    return curve(pid, "ParamAngleX", pts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--cols", type=int, default=5)
    args = parser.parse_args()
    project = args.project if args.project.is_absolute() else ROOT / args.project
    parts_dir = project / "parts"
    pngs = sorted(parts_dir.glob("head_angle_*.png"), key=lambda p: int(p.stem.split("_")[-1]))
    if len(pngs) != args.cols:
        raise SystemExit(f"각도 PNG {len(pngs)}장 != cols {args.cols} — extract_angle_sheet 먼저")

    n = len(pngs)
    edges = list(np.linspace(0.0, ANGLE_MIN, n + 1))  # [0, -16, -32, -48, -64, -80]
    parts, meshes, opacity = [], [], []
    for i, png in enumerate(pngs):
        pid = png.stem
        bbox, coverage = alpha_stats(png)
        parts.append({
            "id": pid, "display_name": f"Head Angle {i}", "source_path": f"parts/{pid}.png",
            "bbox": bbox, "alpha_coverage": coverage, "draw_order": 10 + i, "folder": "Head",
            "deformer_node": "root_warp"})
        # 메시 없음 → draw_pixi sprite 폴백 (각도 통째 스왑, 정점 변형 불필요)
        meshes.append({"part_id": pid, "vertices": [], "triangles": [], "uvs": [],
                       "mesh_path": f"meshes/{pid}.json"})
        opacity.append(angle_opacity_curve(pid, i, n, edges))

    deformers = [{"id": "root_warp", "type": "warp", "parent_id": None,
                  "child_ids": [p["id"] for p in parts], "bounds": [0, 0, CANVAS, CANVAS],
                  "pivot": [CANVAS // 2, CANVAS // 2], "lattice": {"cols": 2, "rows": 2},
                  "edge_pinned": False}]
    parameters = [{"id": "ParamAngleX", "min": ANGLE_MIN, "max": 0.0, "default": 0.0,
                   "key_values": list(edges[::-1])}]

    character = {
        "schema_version": 1, "project_kind": "mini_cubism_v0",
        "experiment_id": "angle-swap-001", "generated_at": now_iso(),
        "canvas_size": [CANVAS, CANVAS],
        "parts": parts, "meshes": meshes, "deformers": deformers,
        "parameters": parameters, "keyform_bindings": [],
        "physics_profiles": [], "vertex_weights": [],
        "part_opacity_keyframes": opacity, "glue": [],
        "notes": ["ANGLE-SWAP-001 검증 미니 — 좌향 5각도 ParamAngleX opacity 스왑"],
        "unsupported_parameters": [],
    }
    (project / "meshes").mkdir(exist_ok=True)
    write_json(project / "character.json", character)
    write_json(project / "mini_rig.json", {
        "schema_version": 1, "project_kind": "mini_cubism_rig_v0",
        "mesh_overrides": {}, "keyform_overrides": [],
        "clipping": {"enabled": False, "pairs": {}},
        "render_mode": "sprite", "notes": ["angle-swap 검증"]})
    print(f"angle_swap 프로젝트: parts={len(parts)} edges={[round(e) for e in edges]}")
    print(f"  ParamAngleX 0(정면)~{ANGLE_MIN}(측면), 5각도 하드 밴드 스왑")
    print(f"  띄우기: python3 scripts/mini_cubism_preview_server.py --project {args.project} --port 8064")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

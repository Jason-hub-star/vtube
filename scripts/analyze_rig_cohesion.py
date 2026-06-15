#!/usr/bin/env python3
"""RIG-COHESION-001: 리그 유기성 분석 — 인접 부위 쌍의 파라미터별 상대 변위(어긋남) 측정.

런타임(rig.js deformedVertices)과 동일 수식의 결정론 재현: 부위 변위 = 체인 디포머별
격자 변위의 합. 격자 컨트롤 포인트는 바인딩 변환(피벗 기준 회전·스케일 + 이동)으로
움직이고, 핀 가장자리는 0, 점 변위는 쌍선형 보간. 정점 키폼·물리 스프링은 범위 밖
(물리는 과도 지연이 설계 의도 — 정착 오프셋은 clothes A/B 검증기가 측정).

측정점 = 두 부위 알파가 6px 이내로 만나는 실제 이음새 픽셀 (bbox 겹침이 아니라).
함께 움직여야 할(co-move) 쌍 목록을 파라미터 min/max로 스윕해 mean/max 어긋남을 보고.

사용: python3 scripts/analyze_rig_cohesion.py --project <rig_v0_project> --out-dir <dir>
      [--check]  # 임계 검사 모드 (P5 게이트): 쌍별 허용치 초과 시 exit 1
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import scipy.ndimage as ndi
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, load_json, now_iso, write_json  # noqa: E402

SWEEP_PARAMS = ["ParamAngleX", "ParamAngleY", "ParamAngleZ", "ParamBodyAngleX",
                "ParamBodyAngleY", "ParamBodyAngleZ", "ParamBreath", "ParamHairFront", "ParamHairBack"]
# 함께 움직여야 할 쌍 + 허용 어긋남 px (의도된 시차는 크게: 앞/뒷머리 X·Y는 공식 후두부 감쇠 패턴)
PAIRS: list[tuple[str, str, dict[str, float]]] = [
    # HairFront/Back은 한쪽만 움직이는 수동 스윙 파라미터 — 상대 변위 ±10이 사양
    ("hair_front_L", "hair_back_L", {"ParamAngleX": 12.0, "ParamAngleY": 6.0,
                                     "ParamHairFront": 12.0, "ParamHairBack": 12.0, "default": 4.0}),
    ("hair_front_R", "hair_back_R", {"ParamAngleX": 12.0, "ParamAngleY": 6.0,
                                     "ParamHairFront": 12.0, "ParamHairBack": 12.0, "default": 4.0}),
    ("hair_front_L", "face_base", {"ParamHairFront": 12.0, "default": 5.0}),
    ("hair_front_C", "face_base", {"ParamHairFront": 12.0, "default": 5.0}),
    ("hair_front_R", "face_base", {"ParamHairFront": 12.0, "default": 5.0}),
    ("hair_back_L", "face_base", {"ParamAngleX": 12.0, "ParamHairBack": 12.0, "default": 6.0}),
    ("hair_back_R", "face_base", {"ParamAngleX": 12.0, "ParamHairBack": 12.0, "default": 6.0}),
    ("face_base", "neck_skin", {"default": 6.0}),
    # BodyAngleZ 7: CHAIN-001 v3 균일 운반 vs 골반 회전 그라데이션의 설계 근사 —
    # 접합선(junction_y)에선 정확하고 밴드 가장자리에서 커진다 (스프링 실효 진폭 ±8에선 ≤5px)
    ("neck_skin", "clothes", {"ParamAngleZ": 5.0, "ParamBodyAngleZ": 7.0, "default": 4.0}),
    ("clothes", "raw_bottomwear", {"default": 3.0}),
    ("clothes", "raw_legwear", {"default": 3.0}),
    ("raw_bottomwear", "raw_legwear", {"default": 3.0}),
    ("raw_legwear", "raw_footwear", {"default": 3.0}),
    # 어깨 가닥은 머리 소속 — 머리 회전·스윙 시 정지한 옷 위를 쓸고 지나가는 게 물리적으로 맞다
    ("shoulder_hair", "clothes", {"ParamAngleX": 14.0, "ParamAngleY": 8.0, "ParamAngleZ": 55.0,
                                  "ParamBodyAngleZ": 10.0, "ParamHairBack": 12.0, "default": 6.0}),
    ("clothes", "L_arm", {"default": 4.0}),
    ("clothes", "R_arm", {"default": 4.0}),
]
MAX_POINTS = 80


def lattice_displacement(deformer: dict, transform: dict, x: float, y: float) -> tuple[float, float]:
    bx, by, bw, bh = deformer["bounds"]
    if x < bx or y < by or x > bx + bw or y > by + bh:
        return 0.0, 0.0
    cols = deformer.get("lattice", {}).get("cols", 5)
    rows = deformer.get("lattice", {}).get("rows", 5)
    pins = deformer.get("pin_edges")
    if pins is None:
        pins = ["top", "bottom", "left", "right"] if deformer.get("edge_pinned") else []
    px, py = deformer.get("pivot", [1024, 1024])
    rad = math.radians(transform["rotate"])
    cos, sin = math.cos(rad), math.sin(rad)
    sx, sy = transform["scale"]
    tx, ty = transform["translate"]

    def cp_disp(r: int, c: int) -> tuple[float, float]:
        if (("top" in pins and r == 0) or ("bottom" in pins and r == rows - 1)
                or ("left" in pins and c == 0) or ("right" in pins and c == cols - 1)):
            return 0.0, 0.0
        cx = bx + bw * c / (cols - 1)
        cy = by + bh * r / (rows - 1)
        dx, dy = cx - px, cy - py
        nx = px + (dx * cos - dy * sin) * sx + tx
        ny = py + (dx * sin + dy * cos) * sy + ty
        return nx - cx, ny - cy

    u = min(max((x - bx) / max(bw, 1e-6) * (cols - 1), 0), cols - 1 - 1e-6)
    v = min(max((y - by) / max(bh, 1e-6) * (rows - 1), 0), rows - 1 - 1e-6)
    c0, r0 = int(u), int(v)
    fu, fv = u - c0, v - r0
    d00, d01 = cp_disp(r0, c0), cp_disp(r0, c0 + 1)
    d10, d11 = cp_disp(r0 + 1, c0), cp_disp(r0 + 1, c0 + 1)
    return (
        (d00[0] * (1 - fu) + d01[0] * fu) * (1 - fv) + (d10[0] * (1 - fu) + d11[0] * fu) * fv,
        (d00[1] * (1 - fu) + d01[1] * fu) * (1 - fv) + (d10[1] * (1 - fu) + d11[1] * fu) * fv,
    )


class Replay:
    def __init__(self, character: dict):
        self.character = character
        self.deformers = {d["id"]: d for d in character["deformers"]}
        self.defaults = {p["id"]: p.get("default", 0) for p in character["parameters"]}
        self.bind_by_target: dict[str, dict[str, list[dict]]] = {}
        for b in character["keyform_bindings"]:
            self.bind_by_target.setdefault(b["target_id"], {}).setdefault(b["parameter_id"], []).append(b)
        self.chain_of: dict[str, list[dict]] = {}
        for part in character["parts"]:
            leaf = next((d for d in character["deformers"] if part["id"] in d.get("child_ids", [])), None)
            chain = []
            while leaf is not None:
                chain.insert(0, leaf)
                leaf = self.deformers.get(leaf.get("parent_id"))
            self.chain_of[part["id"]] = chain

    def transform(self, target: str, values: dict) -> dict:
        out = {"translate": [0.0, 0.0], "scale": [1.0, 1.0], "rotate": 0.0}
        for param_id, binds in self.bind_by_target.get(target, {}).items():
            default = self.defaults.get(param_id, 0)
            keys = sorted([{"k": default, "d": None}] + [{"k": b["key_value"], "d": b["deltas"]} for b in binds],
                          key=lambda e: e["k"])
            v = values.get(param_id, default)
            tf = self._sample(keys, v)
            out["translate"][0] += tf[0]; out["translate"][1] += tf[1]
            out["rotate"] += tf[2]
            out["scale"][0] *= tf[3]; out["scale"][1] *= tf[4]
        return out

    @staticmethod
    def _from_deltas(d: dict | None) -> tuple[float, float, float, float, float]:
        if d is None:
            return 0.0, 0.0, 0.0, 1.0, 1.0
        t = d.get("translate", [0, 0]); s = d.get("scale", [1, 1])
        return t[0] or 0, t[1] or 0, d.get("rotate", 0) or 0, 1 if s[0] is None else s[0], 1 if s[1] is None else s[1]

    def _sample(self, keys: list[dict], v: float) -> tuple[float, ...]:
        if v <= keys[0]["k"]:
            return self._from_deltas(keys[0]["d"])
        if v >= keys[-1]["k"]:
            return self._from_deltas(keys[-1]["d"])
        for lo, hi in zip(keys, keys[1:]):
            if lo["k"] <= v <= hi["k"]:
                t = (v - lo["k"]) / max(hi["k"] - lo["k"], 1e-9)
                a, b = self._from_deltas(lo["d"]), self._from_deltas(hi["d"])
                return tuple(a[i] + (b[i] - a[i]) * t for i in range(5))
        return self._from_deltas(None)

    def part_disp(self, part_id: str, pts: np.ndarray, values: dict) -> np.ndarray:
        out = np.zeros_like(pts, dtype=float)
        for deformer in self.chain_of.get(part_id, []):
            tf = self.transform(deformer["id"], values)
            for i, (x, y) in enumerate(pts):
                dx, dy = lattice_displacement(deformer, tf, float(x), float(y))
                out[i, 0] += dx; out[i, 1] += dy
        direct = self.transform(part_id, values)  # 파트 직접 바인딩(눈썹류)은 강체 translate
        out += np.array(direct["translate"])
        return out


def seam_points(project: Path, a: str, b: str) -> np.ndarray | None:
    pa, pb = project / "parts" / f"{a}.png", project / "parts" / f"{b}.png"
    if not pa.exists() or not pb.exists():
        return None
    ma = np.asarray(Image.open(pa).convert("RGBA"))[..., 3] > 8
    mb = np.asarray(Image.open(pb).convert("RGBA"))[..., 3] > 8
    band = (ma & ndi.binary_dilation(mb, iterations=6)) | (mb & ndi.binary_dilation(ma, iterations=6))
    ys, xs = np.where(band)
    if len(xs) < 8:
        return None
    step = max(1, len(xs) // MAX_POINTS)
    return np.stack([xs[::step], ys[::step]], axis=1)[:MAX_POINTS]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--check", action="store_true", help="허용치 초과 시 exit 1 (P5 게이트)")
    args = parser.parse_args()
    project = args.project if args.project.is_absolute() else ROOT / args.project
    out = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    character = load_json(project / "character.json")
    replay = Replay(character)
    params = {p["id"]: p for p in character["parameters"]}

    rows, failures = [], []
    for a, b, limits in PAIRS:
        pts = seam_points(project, a, b)
        if pts is None:
            continue
        for pid in SWEEP_PARAMS:
            if pid not in params:
                continue
            for v in (params[pid]["min"], params[pid]["max"]):
                if v == params[pid].get("default", 0):
                    continue
                values = {pid: v}
                rel = replay.part_disp(a, pts, values) - replay.part_disp(b, pts, values)
                mag = np.hypot(rel[:, 0], rel[:, 1])
                limit = limits.get(pid, limits["default"])
                row = {"pair": f"{a}|{b}", "param": pid, "value": v,
                       "mean_px": round(float(mag.mean()), 2), "max_px": round(float(mag.max()), 2),
                       "limit_px": limit, "ok": bool(mag.mean() <= limit)}
                rows.append(row)
                if not row["ok"]:
                    failures.append(row)

    rows.sort(key=lambda r: -r["mean_px"])
    # 정점 키폼(볼 등) 파트는 메시 정점 보간이라 이 seam-점 해석 재현 밖 — 침묵 갭 방지 경고.
    # (런타임 캡처 pose_sweep/capture_pose가 실제 렌더로 검증함. ANGLE-FORESHORTEN R3 자기리뷰)
    vk_parts = sorted({m["part_id"] for m in character.get("meshes", []) if m.get("vertex_keyforms")})
    status = "FAIL" if (args.check and failures) else "PASS"
    write_json(out / "rig_cohesion_report.json", {
        "generated_at": now_iso(), "project": str(project), "status": status,
        "checked_rows": len(rows), "failures": failures, "worst": rows[:20],
        "vertex_keyform_parts_not_analytically_covered": vk_parts,
    })
    if vk_parts:
        print(f"[경고] 정점키폼 파트 {vk_parts} — 해석 게이트 밖, 런타임 캡처로 검증 필요")
    print(f"{'쌍':28s} {'파라미터':16s} {'값':>5s} {'mean':>7s} {'max':>7s} {'허용':>5s}")
    for r in rows[:14]:
        flag = "" if r["ok"] else "  ← FAIL"
        print(f"{r['pair']:28s} {r['param']:16s} {r['value']:5.0f} {r['mean_px']:7.2f} {r['max_px']:7.2f} {r['limit_px']:5.1f}{flag}")
    print(f"status: {status} (rows {len(rows)}, fail {len(failures)})")
    return 1 if status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""MOUTH-LIP-RIDE-001 검증: 미소선=윗입술 부품형 입의 윤곽 연속·클립 누출 0을 수치로 검사 (P5).

blink 검증기(EYE-NATURAL-002)가 정점 키폼 보간의 런타임 픽셀 등가성을 이미 증명했으므로,
여기서는 그 등가성 위에서 성립하는 구조 불변량을 검사한다:
  1. 하부 4종(입안·이빨·혀·아랫입술) 전부 ParamMouthOpenY 정점 키폼 + 동일 키 값 세트
  2. 모든 키 v에서 부품·정점 공통의 세로 붕괴비 h(v) (±0.6px) & x 불변 + 공통 앵커(미소선 중심)
     → 어느 v에서든 부품 간 상대 기하 불변 = 윤곽 연속(±1px)의 구조적 보장
  3. 이빨/혀 알파 ⊆ 입안(솔리드) 알파 1px 팽창 — 균일 변환이라 전 v에서 클립 누출 0
  4. 미소선+하부 합집합 알파의 중앙 60% 컬럼에 내부 세로 갭 ≤ 2px (윗입술↔입안 이음새 없음)
  5. 미소선=윗입술 불변: mouth_line은 MouthOpenY opacity 곡선이 없어야 한다(항상 켜짐), 하부 4종은 페이드 곡선 보유
  6. MouthForm 입꼬리 키폼: 중앙 ±0.5px 고정, 꼬리 진폭 ≤ 10px

사용: python3 scripts/validate_mouth_parts_keyforms.py --project <rig_v0_project> --out-dir <dir>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import scipy.ndimage as ndi
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.rig_keyforms import MOUTH_LOWER_IDS  # noqa: E402
from lib.vtube_io import ROOT, load_json, now_iso, write_json  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    project = args.project if args.project.is_absolute() else ROOT / args.project
    out = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    character = load_json(project / "character.json")
    checks: list[dict] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})
        print(f"{'PASS' if ok else 'FAIL'} {name} {detail}")

    meshes = {m["part_id"]: m for m in character["meshes"]}
    missing = [pid for pid in MOUTH_LOWER_IDS if pid not in meshes]
    if missing:
        check("parts_present", False, f"부품 메시 없음: {missing}")
    else:
        check("parts_present", True)
        specs = {pid: meshes[pid].get("vertex_keyforms") or {} for pid in MOUTH_LOWER_IDS}
        key_sets = {pid: tuple(k["value"] for k in s.get("keys", [])) for pid, s in specs.items()}
        same_keys = len(set(key_sets.values())) == 1 and all(
            s.get("parameter_id") == "ParamMouthOpenY" for s in specs.values())
        check("uniform_keyform_keys", same_keys, f"키 세트: {sorted(set(key_sets.values()))}")

        # 공통 붕괴비 h(v): 모든 부품·정점에서 (key_y - anchor)/(base_y - anchor) 동일
        if same_keys:
            max_dev = 0.0
            x_moved = 0.0
            for pid in MOUTH_LOWER_IDS:
                base = np.asarray(meshes[pid]["vertices"], dtype=float)
                for key in specs[pid]["keys"]:
                    kv = np.asarray(key["vertices"], dtype=float)
                    x_moved = max(x_moved, float(np.abs(kv[:, 0] - base[:, 0]).max()))
                    # 선형성 검사: spread = key_y - base_y 가 base_y에 대해 선형이면
                    # 균일 세로 스케일 (앵커 공통 여부는 아래 부품 간 기울기 산포가 판정)
                    spread = kv[:, 1] - base[:, 1]
                    fit = np.polyfit(base[:, 1], spread, 1)
                    resid = float(np.abs(spread - np.polyval(fit, base[:, 1])).max())
                    max_dev = max(max_dev, resid)
            check("uniform_vertical_scale", max_dev <= 0.6 and x_moved <= 0.01,
                  f"세로 선형 잔차 max {max_dev:.3f}px, x 이동 {x_moved:.3f}px")
            # 부품 간 공통 h + 공통 앵커: spread = (h-1)·(base_y - anchor) 이므로
            # 기울기(h-1)만 같고 앵커가 다르면 키 v에서 부품 간 일정 오프셋 = 이음새 —
            # 절편에서 앵커를 역산해 산포까지 검사한다 (자기리뷰: 기울기 단독 검사의 구멍)
            slopes_by_v: dict[float, list[float]] = {}
            anchors_by_v: dict[float, list[float]] = {}
            for pid in MOUTH_LOWER_IDS:
                base = np.asarray(meshes[pid]["vertices"], dtype=float)
                for key in specs[pid]["keys"]:
                    kv = np.asarray(key["vertices"], dtype=float)
                    slope, intercept = np.polyfit(base[:, 1], kv[:, 1] - base[:, 1], 1)
                    slopes_by_v.setdefault(key["value"], []).append(float(slope))
                    if abs(slope) > 1e-4:
                        anchors_by_v.setdefault(key["value"], []).append(float(-intercept / slope))
            slope_dev = max(max(s) - min(s) for s in slopes_by_v.values())
            check("shared_h_across_parts", slope_dev <= 0.01, f"부품 간 h 산포 {slope_dev:.4f}")
            anchor_devs = [max(a) - min(a) for a in anchors_by_v.values() if len(a) >= 2]
            anchor_dev = max(anchor_devs) if anchor_devs else 0.0
            check("shared_anchor_across_parts", anchor_dev <= 1.5, f"부품 간 앵커 산포 {anchor_dev:.2f}px")

        # 알파 포함관계: 이빨/혀 ⊆ 입안 1px 팽창 (클립 누출 0)
        interior_a = np.asarray(Image.open(project / "parts/mouth_parts_interior.png").convert("RGBA"))[..., 3] > 8
        interior_d = ndi.binary_dilation(interior_a, iterations=1)
        for pid in ("mouth_parts_teeth", "mouth_parts_tongue"):
            a = np.asarray(Image.open(project / f"parts/{pid}.png").convert("RGBA"))[..., 3] > 8
            leak = int((a & ~interior_d).sum())
            check(f"clip_leak_{pid.rsplit('_', 1)[1]}", leak == 0, f"누출 {leak}px")

        # 미소선(윗입술)+하부 합집합 세로 연속성: 중앙 60% 컬럼 내부 갭 ≤ 2px (윗입술↔입안 이음새 포함)
        union = np.zeros_like(interior_a)
        for pid in (*MOUTH_LOWER_IDS, "mouth_line"):
            pp = project / f"parts/{pid}.png"
            if pp.exists():
                union |= np.asarray(Image.open(pp).convert("RGBA"))[..., 3] > 8
        xs = np.where(union.any(axis=0))[0]
        x0, x1 = xs.min(), xs.max()
        lo, hi = int(x0 + 0.2 * (x1 - x0)), int(x0 + 0.8 * (x1 - x0))
        worst_gap = 0
        for x in range(lo, hi + 1):
            col = np.where(union[:, x])[0]
            if len(col) >= 2:
                runs = np.diff(col)
                worst_gap = max(worst_gap, int(runs.max()) - 1)
        check("vertical_continuity", worst_gap <= 2, f"중앙 컬럼 최악 내부 갭 {worst_gap}px")

    # MOUTH-LIP-RIDE-001 핵심 불변: 미소선(윗입술)은 MouthOpenY opacity 곡선이 없어야(항상 켜짐 →
    # 미소곡선이 제자리 유지), 하부 4종은 페이드 곡선 보유. 미소선이 사라지면 윗입술 점프 = 회귀.
    curves = {(c["part_id"], c["parameter_id"]): c for c in character.get("part_opacity_keyframes", [])}
    line_stays = ("mouth_line", "ParamMouthOpenY") not in curves
    lowers_fade = all(curves.get((pid, "ParamMouthOpenY")) for pid in MOUTH_LOWER_IDS)
    check("lip_ride_smile_line_persists", line_stays and lowers_fade,
          f"미소선 MouthOpenY 곡선 {'없음(OK)' if line_stays else '있음(FAIL—사라짐)'}, 하부 페이드 {lowers_fade}")

    # MouthForm 입꼬리 키폼
    ml = next((m for m in character["meshes"] if m["part_id"] == "mouth_line"), None)
    spec = (ml or {}).get("vertex_keyforms") or {}
    if spec.get("parameter_id") == "ParamMouthForm":
        base = np.asarray(ml["vertices"], dtype=float)
        amps = [float(np.abs(np.asarray(k["vertices"], dtype=float)[:, 1] - base[:, 1]).max()) for k in spec["keys"]]
        xs_ = base[:, 0]
        cx = (xs_.min() + xs_.max()) / 2
        center_idx = np.abs(xs_ - cx) < (xs_.max() - xs_.min()) * 0.1
        center_amp = max(float(np.abs(np.asarray(k["vertices"], dtype=float)[center_idx, 1] - base[center_idx, 1]).max())
                         for k in spec["keys"]) if center_idx.any() else 0.0
        check("mouthform_corner_keyforms", max(amps) <= 10.0 and center_amp <= 0.5,
              f"꼬리 진폭 max {max(amps):.1f}px, 중앙 {center_amp:.2f}px")
    else:
        check("mouthform_corner_keyforms", False, "mouth_line MouthForm 정점 키폼 없음")

    status = "PASS" if all(c["ok"] for c in checks) else "FAIL"
    write_json(out / "mouth_parts_validation.json", {
        "generated_at": now_iso(), "project": str(project), "status": status, "checks": checks})
    print(f"status: {status}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

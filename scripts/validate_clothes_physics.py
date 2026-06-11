#!/usr/bin/env python3
"""CLOTH-PHYS-001 검증: 옷 드레이프 스프링이 밑단만 지연시키고 목 접합은 등변위인지.

A/B 대조 — 같은 리그에서 옷 스프링·가중만 제거한 컨트롤 프로젝트를 즉석 생성해
동일 측정을 두 번 돌린다. 골반 진자 때문에 밑단은 스프링 없이도 상부보다 덜 움직이므로,
스프링의 픽셀 기여는 (컨트롤 밑단 시프트 - 활성 밑단 시프트)로만 분리 증명된다.

검사 (TrackX=1 정착 상태):
  1. spring_active — clothes_drape_spring 오프셋 |x| >= 3px (스프링 가동 증명)
  2. sway_visible — 목 밴드 시프트 >= 5px (스웨이 자체가 일어났는지)
  3. junction_slip — 목 밴드 vs 옷 상단 밴드 시프트 차(상단 가중 보정) <= 1.5px (참수 무회귀)
  4. drape_pixel_effect — 컨트롤·활성 밑단 시프트 차 = 스프링 오프셋 × 밑단 가중 ±2.5px
  5. control_consistency — 두 런의 목 밴드 시프트 차 <= 1.5px (몸 체인 동일성 보증)

측정은 30px+ 멀티밴드 컬럼 프로파일 시프트 (좁은 밴드 상관 오측정 교훈 반영).
프로파일 분산이 빈약하면 PASS 대신 UNRELIABLE로 보고한다 (texture-poor 가드).

사용: python3 scripts/validate_clothes_physics.py \
        --project experiments/autorig-character-003/rig_v0_project \
        --out-dir experiments/autorig-character-003/reports/clothes_physics
"""

from __future__ import annotations

import argparse
import base64
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, load_json, now_iso, write_json  # noqa: E402
from lib.vtube_proc import terminate, wait_for_server  # noqa: E402

PLAYWRIGHT = ROOT / "experiments/live2d-strong-model-pattern-001/probe_sandbox/strong20/Samples/TypeScript/Demo/node_modules/playwright"
PORT = 8071
SETTLE_STEPS = 120  # __miniStepPhysics 4초 상당(정착 ~40스텝) — 벽시계 대기는 타이머 스로틀로 비결정적.
# 매 스텝 draw()가 동기 호출되므로 스텝 수가 곧 렌더 횟수다 — 과대 설정 금지.
MAX_SHIFT = 28

# 밴드 캡처+스냅샷은 단일 evaluate(동기 블록) — 프레임 간 위상 차이가 밴드별 측정에 섞이지 않게.
NODE = r"""
const fs = require('fs');
const config = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const { chromium } = require(config.pw);
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
  await page.goto(config.url, { waitUntil: 'load', timeout: 30000 });
  await page.waitForFunction(() => window.__miniProbe, null, { timeout: 20000 });
  await page.evaluate(() => window.__miniProbe.waitReady(20000));
  await page.evaluate(() => window.__miniClearSelection());
  const grab = () => page.evaluate((bands) => {
    const out = { __snapshot: window.__miniSnapshot() };
    for (const [name, r] of Object.entries(bands)) {
      out[name] = window.__miniProbe.regionPixelsBase64(r[0], r[1], r[2], r[3]);
    }
    return out;
  }, config.bands);
  const result = { backend: await page.evaluate(() => window.__miniBackend?.() || 'canvas') };
  await page.evaluate((n) => {
    window.__miniResetPhysics();
    for (let i = 0; i < n; i += 1) window.__miniStepPhysics(1 / 30);
  }, config.settle_steps);
  result.neutral = await grab();
  await page.evaluate((n) => {
    window.__miniProbe.setParameterValues({ ParamBodyTrackX: 1 });
    for (let i = 0; i < n; i += 1) window.__miniStepPhysics(1 / 30);
  }, config.settle_steps);
  result.displaced = await grab();
  await browser.close();
  fs.writeFileSync(config.out, JSON.stringify(result));
})();
"""


def decode(b64: str, w: int, h: int) -> np.ndarray:
    return np.frombuffer(base64.b64decode(b64), dtype=np.uint8).reshape(h, w, 4).astype(float)


def column_profile(band: np.ndarray) -> np.ndarray:
    """RGBA 4채널 컬럼 평균을 세로로 이어붙인 프로파일 — 실루엣(알파)과 내부 명암 둘 다 사용."""
    return np.concatenate([band[..., ch].mean(axis=0) for ch in range(4)])


def profile_shift(neutral: np.ndarray, displaced: np.ndarray) -> tuple[float, float]:
    """수평 시프트 추정 (SSD 최소 + 포물선 서브픽셀). 반환: (shift_px, 프로파일 표준편차)."""
    n_cols = neutral.shape[0] // 4
    costs = []
    shifts = range(-MAX_SHIFT, MAX_SHIFT + 1)
    for s in shifts:
        a0, a1 = max(0, s), min(n_cols, n_cols + s)
        total, count = 0.0, 0
        for ch in range(4):
            seg_n = neutral[ch * n_cols + a0 - s:ch * n_cols + a1 - s]
            seg_d = displaced[ch * n_cols + a0:ch * n_cols + a1]
            total += float(((seg_n - seg_d) ** 2).mean())
            count += 1
        costs.append(total / count)
    costs = np.array(costs)
    i = int(costs.argmin())
    best = float(list(shifts)[i])
    if 0 < i < len(costs) - 1:
        denom = costs[i - 1] - 2 * costs[i] + costs[i + 1]
        if denom > 1e-9:
            best += 0.5 * float(costs[i - 1] - costs[i + 1]) / float(denom)
    # 신뢰도는 채널별 std의 최댓값 — 내부 밴드는 알파가 평탄(255)해서 평균을 끌어내린다
    return best, float(neutral.reshape(4, -1).std(axis=1).max())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--renderer", choices=["canvas", "pixi"], default="pixi")
    args = parser.parse_args()
    out = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    project_dir = args.project if args.project.is_absolute() else ROOT / args.project
    character = load_json(project_dir / "character.json")
    canvas_w, canvas_h = character["canvas_size"]

    def mesh_bbox(part_id: str) -> tuple[int, int, int, int]:
        mesh = next(m for m in character["meshes"] if m["part_id"] == part_id)
        xs = [v[0] for v in mesh["vertices"]]
        ys = [v[1] for v in mesh["vertices"]]
        return int(min(xs)), int(min(ys)), int(max(xs) - min(xs)), int(max(ys) - min(ys))

    ns = mesh_bbox("neck_skin")
    cl = mesh_bbox("clothes")
    pad = 40
    x0 = max(0, ns[0] - pad)
    xw = min(canvas_w, ns[0] + ns[2] + pad) - x0
    hem_y = int(cl[1] + cl[3] * 0.83)
    hem_h = int(cl[3] * 0.10)
    # 밑단 밴드 x창은 팔 안쪽 순수 옷 영역으로 제한 — 팔/머리 실루엣은 옷 스프링 비대상이라
    # 강한 엣지가 SSD를 지배해 옷 주름 이동을 0으로 오측정한다 (이 스크립트 v1 실패 원인).
    r_arm = mesh_bbox("R_arm")
    l_arm = mesh_bbox("L_arm")
    hem_x0 = r_arm[0] + r_arm[2] + 20
    hem_x1 = l_arm[0] - 20
    bands = {
        "neck": [x0, int(ns[1] + ns[3] * 0.25), xw, max(30, int(ns[3] * 0.5))],
        "clothes_top": [x0, ns[1] + ns[3] + 8, xw, 110],
        "hem": [hem_x0, hem_y, hem_x1 - hem_x0, min(hem_h, canvas_h - hem_y)],
    }
    hem_center_w = (bands["hem"][1] + bands["hem"][3] / 2 - cl[1]) / max(cl[3], 1)
    top_center_w = (bands["clothes_top"][1] + bands["clothes_top"][3] / 2 - cl[1]) / max(cl[3], 1)

    # 컨트롤 프로젝트: 옷 스프링·가중만 제거한 동일 리그.
    # 파트 이미지는 하드링크 — 서버 safe_join이 프로젝트 밖으로 resolve되는 심링크를 403으로 막는다.
    control_dir = out / "control_project"
    if control_dir.exists():
        shutil.rmtree(control_dir)
    control_dir.mkdir(parents=True)
    import os
    for entry in project_dir.iterdir():
        if entry.name in ("character.json", "reports"):
            continue
        if entry.is_dir():
            shutil.copytree(entry, control_dir / entry.name, copy_function=os.link)
        else:
            os.link(entry, control_dir / entry.name)
    control = json.loads((project_dir / "character.json").read_text())
    control["physics_profiles"] = [p for p in control["physics_profiles"] if p["id"] != "clothes_drape_spring"]
    control["vertex_weights"] = [v for v in control["vertex_weights"] if v["part_id"] != "clothes"]
    write_json(control_dir / "character.json", control)

    runner = out / "clothes_physics_runner.js"
    runner.write_text(NODE, encoding="utf-8")

    def run_capture(label: str, proj: Path) -> dict:
        raw_out = out / f"clothes_physics_raw_{label}.json"
        config_path = out / f"clothes_physics_config_{label}.json"
        write_json(config_path, {
            "pw": str(PLAYWRIGHT),
            "url": f"http://127.0.0.1:{PORT}/" + ("?renderer=pixi" if args.renderer == "pixi" else ""),
            "bands": bands, "settle_steps": SETTLE_STEPS, "out": str(raw_out),
        })
        server = subprocess.Popen(
            ["python3", str(ROOT / "scripts/mini_cubism_preview_server.py"), "--project", str(proj), "--port", str(PORT)],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            wait_for_server("127.0.0.1", PORT)
            subprocess.run(["node", str(runner), str(config_path)], check=True, timeout=420)
        finally:
            terminate(server)
        raw = json.loads(raw_out.read_text())
        shifts, stds = {}, {}
        for name, (bx, by, bw, bh) in bands.items():
            neutral = decode(raw["neutral"][name], bw, bh)
            displaced = decode(raw["displaced"][name], bw, bh)
            Image.fromarray(neutral.astype(np.uint8), "RGBA").save(out / f"band_{name}_{label}_neutral.png")
            Image.fromarray(displaced.astype(np.uint8), "RGBA").save(out / f"band_{name}_{label}_displaced.png")
            shifts[name], stds[name] = profile_shift(column_profile(neutral), column_profile(displaced))
        return {"raw": raw, "shifts": shifts, "stds": stds}

    active = run_capture("active", project_dir)
    ctrl = run_capture("control", control_dir)

    spring = active["raw"]["displaced"]["__snapshot"]["physics"].get("clothes_drape_spring")
    body_angle = active["raw"]["displaced"]["__snapshot"]["parameters"].get("ParamBodyAngleX")
    offset_x = float(spring["offset"][0]) if spring else 0.0
    slip = abs(active["shifts"]["neck"] - active["shifts"]["clothes_top"] - offset_x * top_center_w)
    drape_effect = ctrl["shifts"]["hem"] - active["shifts"]["hem"]
    expected_effect = -offset_x * hem_center_w
    checks = {
        "spring_active": abs(offset_x) >= 3.0,
        "sway_visible": abs(active["shifts"]["neck"]) >= 5.0,
        "junction_slip": slip <= 1.5,
        "drape_pixel_effect": abs(drape_effect - expected_effect) <= 2.5 and abs(drape_effect) >= 3.0,
        "control_consistency": abs(active["shifts"]["neck"] - ctrl["shifts"]["neck"]) <= 1.5,
    }
    reliable = all(v >= 2.0 for run in (active, ctrl) for v in run["stds"].values())
    status = ("PASS" if all(checks.values()) else "FAIL") if reliable else "UNRELIABLE"
    report = {
        "test_id": "CLOTH-PHYS-001-drape-and-junction",
        "generated_at": now_iso(),
        "renderer": active["raw"]["backend"],
        "claim": "옷 밑단은 몸 스웨이를 스프링만큼 늦게 따르고(A/B 분리 증명), 목 접합(가중~0)은 등변위",
        "physics": {"clothes_spring_offset": spring["offset"] if spring else None,
                    "body_angle_x_settled": body_angle},
        "shifts_px": {"active": {k: round(v, 2) for k, v in active["shifts"].items()},
                      "control": {k: round(v, 2) for k, v in ctrl["shifts"].items()}},
        "profile_std": {"active": {k: round(v, 2) for k, v in active["stds"].items()},
                        "control": {k: round(v, 2) for k, v in ctrl["stds"].items()}},
        "band_weights": {"clothes_top": round(top_center_w, 3), "hem": round(hem_center_w, 3)},
        "slip_px": round(slip, 2),
        "drape_effect_px": round(drape_effect, 2),
        "expected_effect_px": round(expected_effect, 2),
        "checks": checks,
        "thresholds": {"spring_active_px": 3.0, "junction_slip_px": 1.5, "effect_match_px": 2.5, "profile_std_min": 2.0},
        "status": status,
    }
    shutil.rmtree(control_dir)  # 풀해상도 파트 하드링크 — 매 런 재생성되는 파생물이라 보존 불필요
    write_json(out / "clothes_physics_report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

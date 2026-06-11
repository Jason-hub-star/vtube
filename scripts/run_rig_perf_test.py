#!/usr/bin/env python3
"""리그 런타임 성능 테스트 — 상태별 렌더 시간(스케일 1.0/0.55, 중앙값), 물리 비용, 재생 FPS.

산출: experiments/autorig-template-001/reports/rig_perf_report.json + md
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, now_iso, rel, write_json  # noqa: E402
from lib.vtube_proc import terminate, wait_for_server  # noqa: E402

PLAYWRIGHT = ROOT / "experiments/live2d-strong-model-pattern-001/probe_sandbox/strong20/Samples/TypeScript/Demo/node_modules/playwright"
PREVIEW_PORT = 8067
DRIVE_PORT = 8068

NODE = r"""
const fs = require('fs');
const config = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const { chromium } = require(config.pw);

const STATES = {
  neutral: {},
  head_turn: { ParamAngleX: 30 },
  nod: { ParamAngleY: -30 },
  tilt: { ParamAngleZ: 30 },
  gaze_turn: { ParamAngleX: 30, ParamEyeBallX: 1 },
  blink: { ParamEyeLOpen: 0.27, ParamEyeROpen: 0.27 },
  mouth: { ParamMouthOpenY: 0.85 },
  combo: { ParamAngleX: 25, ParamAngleY: -15, ParamAngleZ: 10, ParamMouthOpenY: 0.6, ParamBodyAngleX: 8 },
};
const RESET = { ParamAngleX:0, ParamAngleY:0, ParamAngleZ:0, ParamEyeBallX:0, ParamEyeLOpen:1, ParamEyeROpen:1, ParamMouthOpenY:0, ParamBodyAngleX:0 };

async function measureScale(browser, base, scale, renderer) {
  const page = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
  const query = '/?render_scale=' + scale + (renderer === 'pixi' ? '&renderer=pixi' : '');
  await page.goto(base + query, { waitUntil: 'load', timeout: 30000 });
  await page.waitForFunction(() => window.__miniProbe, null, { timeout: 20000 });
  await page.evaluate(() => window.__miniProbe.waitReady(20000));
  await page.evaluate(() => window.__miniClearSelection());
  const result = {};
  result.backend = await page.evaluate(() => (window.__miniBackend ? window.__miniBackend() : 'canvas'));
  for (const [name, vals] of Object.entries(STATES)) {
    const times = await page.evaluate(async ({ reset, vals }) => {
      const samples = [];
      for (let i = 0; i < 6; i += 1) {
        window.__miniSetParameters(reset);
        const t0 = performance.now();
        window.__miniSetParameters({ ...reset, ...vals });
        samples.push(performance.now() - t0);
        await new Promise((r) => setTimeout(r, 30));
      }
      samples.sort((a, b) => a - b);
      return samples;
    }, { reset: RESET, vals });
    result[name] = Math.round(times[Math.floor(times.length / 2)] * 10) / 10; // 중앙값
  }
  // 물리 스텝 비용 (드로우 포함)
  result.physics_step = await page.evaluate(async () => {
    window.__miniSetParameters({ ParamAngleX: 30 });
    const t0 = performance.now();
    for (let i = 0; i < 10; i += 1) window.__miniStepPhysics(1 / 30);
    return Math.round(((performance.now() - t0) / 10) * 10) / 10;
  });
  // 실효 FPS: rAF 루프에서 머리·입 진동 — GPU 백엔드는 setParameters 타이밍이 CPU 제출만
  // 재므로 (GPU 비동기), 프레임 카운트가 정직한 처리량이다
  result.raf_fps = await page.evaluate(async () => {
    const t0 = performance.now();
    let frames = 0;
    await new Promise((resolve) => {
      const tick = (now) => {
        const t = (now - t0) / 1000;
        window.__miniSetParameters({
          ParamAngleX: Math.sin(t * 6.28) * 30,
          ParamAngleZ: Math.cos(t * 6.28) * 10,
          ParamMouthOpenY: (Math.sin(t * 12.6) + 1) / 2,
        });
        frames += 1;
        if (now - t0 < 2000) requestAnimationFrame(tick); else resolve();
      };
      requestAnimationFrame(tick);
    });
    return Math.round(frames / ((performance.now() - t0) / 1000));
  });
  await page.close();
  return result;
}

(async () => {
  const browser = await chromium.launch({ headless: true, args: config.launch_args || [] });
  const out = { scales: {}, replay: {}, errors: [] };
  try {
    // pixi는 좌표계가 항상 풀해상도 — render_scale 축이 무의미하므로 1.0만
    const scaleList = config.renderer === 'pixi' ? [1] : [1, 0.55];
    for (const scale of scaleList) {
      out.scales[scale.toFixed(scale === 1 ? 1 : 2)] = await measureScale(browser, config.preview, scale, config.renderer);
    }
    // 재생 실효 FPS (드라이브, 0.55 내장)
    const drive = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
    await drive.goto(config.drive + '/drive?replay=1&auto=1&speed=1', { waitUntil: 'load', timeout: 30000 });
    await drive.waitForFunction(() => window.__driveReport?.frames_applied > 0, null, { timeout: 60000 });
    const t0 = Date.now();
    await drive.waitForFunction(() => window.__driveReport.done === true, null, { timeout: 90000 });
    const wall = (Date.now() - t0) / 1000;
    const frames = await drive.evaluate(() => window.__driveReport.frames_applied);
    out.replay = { frames, wall_s: Math.round(wall * 100) / 100, effective_fps: Math.round(frames / Math.max(wall, 0.1)) };
    await drive.close();
  } catch (e) { out.errors.push(String(e)); }
  await browser.close();
  fs.writeFileSync(config.out, JSON.stringify(out, null, 2));
})();
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=ROOT / "experiments/autorig-template-001/rig_v0_project")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "experiments/autorig-template-001/reports")
    parser.add_argument("--renderer", choices=["canvas", "pixi"], default="canvas", help="렌더 백엔드 (PIXI-RENDER-001)")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "" if args.renderer == "canvas" else f"_{args.renderer}"
    raw_out = args.out_dir / f"rig_perf{suffix}_raw.json"
    runner = args.out_dir / "rig_perf_runner.js"
    runner.write_text(NODE, encoding="utf-8")
    config_path = args.out_dir / "rig_perf_config.json"
    write_json(config_path, {
        "pw": str(PLAYWRIGHT),
        "preview": f"http://127.0.0.1:{PREVIEW_PORT}",
        "drive": f"http://127.0.0.1:{DRIVE_PORT}",
        "renderer": args.renderer,
        # 실 GPU(ANGLE Metal) 우선 — SwiftShader는 2048² 소프트웨어 합성이 ~1s/frame이라 FPS가 허수
        "launch_args": ["--enable-gpu", "--use-angle=metal"] if args.renderer == "pixi" else [],
        "out": str(raw_out),
    })

    preview = subprocess.Popen(
        ["python3", str(ROOT / "scripts/mini_cubism_preview_server.py"), "--project", str(args.project), "--port", str(PREVIEW_PORT)],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    drive = subprocess.Popen(
        ["python3", str(ROOT / "scripts/run_mini_cubism_webcam_drive.py"), "--project", str(args.project), "--port", str(DRIVE_PORT), "--no-open"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        wait_for_server("127.0.0.1", PREVIEW_PORT)
        wait_for_server("127.0.0.1", DRIVE_PORT)
        subprocess.run(["node", str(runner), str(config_path)], check=True, timeout=420)
    finally:
        terminate(preview)
        terminate(drive)

    raw = json.loads(raw_out.read_text())
    report = {
        "generated_at": now_iso(),
        "test_id": "rig_perf_test",
        "renderer": args.renderer,
        "render_ms_median": raw["scales"],
        "replay": raw["replay"],
        "errors": raw["errors"],
    }
    write_json(args.out_dir / f"rig_perf{suffix}_report.json", report)
    scale_keys = list(raw["scales"].keys())
    lines = ["# Rig Performance Report", "", f"Generated: {report['generated_at']}", f"Renderer: {args.renderer}", "",
             "| 상태 | " + " | ".join(f"scale {key} (ms)" for key in scale_keys) + " |",
             "|---|" + "---:|" * len(scale_keys)]
    for name in raw["scales"][scale_keys[0]]:
        lines.append(f"| {name} | " + " | ".join(str(raw["scales"][key].get(name, "-")) for key in scale_keys) + " |")
    lines += ["", f"재생: {raw['replay']}"]
    (args.out_dir / f"rig_perf{suffix}_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not raw["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

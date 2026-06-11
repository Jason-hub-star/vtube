#!/usr/bin/env python3
"""MESH-DEFORM 검증 스모크: 중립 항등성 / 변형 상태 상이 / 목 이음새 / 렌더 시간.

(자기리뷰에서 /tmp 일회용이던 검증을 리포 스크립트로 승격 — 재현 가능)
산출: experiments/autorig-template-001/reports/mesh_deform_verify.json + 캡처
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
PORT = 8066

NODE = r"""
const fs = require('fs');
const config = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const { chromium } = require(config.pw);
(async () => {
  const browser = await chromium.launch({ headless: true, args: config.launch_args || [] });
  const page = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
  const out = { neutral: {}, hashes: {}, neck: {}, timing: {}, errors: [] };
  try {
    await page.goto(config.base + (config.query || ''), { waitUntil: 'load', timeout: 30000 });
    await page.waitForFunction(() => window.__miniProbe, null, { timeout: 20000 });
    await page.evaluate(() => window.__miniProbe.waitReady(20000));
    await page.evaluate(() => window.__miniClearSelection());
    out.backend = await page.evaluate(() => (window.__miniBackend ? window.__miniBackend() : 'canvas'));
    out.neutral.mesh = await page.evaluate(() => { window.__miniRig().render_mode='mesh'; window.__miniSetParameters({}); return window.__miniProbe.canvasHash(); });
    out.neutral.sprite = await page.evaluate(() => { window.__miniRig().render_mode='sprite'; window.__miniSetParameters({}); return window.__miniProbe.canvasHash(); });
    await page.evaluate(() => { window.__miniRig().render_mode='mesh'; window.__miniSetParameters({}); });
    const reset = { ParamAngleX:0, ParamAngleY:0, ParamAngleZ:0, ParamMouthOpenY:0, ParamEyeLOpen:1, ParamEyeROpen:1, ParamEyeBallX:0, ParamEyeSmile:0, ParamCheek:0, ParamMouthForm:0 };
    const states = { head_turn:{ParamAngleX:30}, nod:{ParamAngleY:-30}, tilt:{ParamAngleZ:30}, gaze_turn:{ParamAngleX:30,ParamEyeBallX:1}, combo:{ParamAngleX:25,ParamAngleY:-15,ParamMouthOpenY:0.6}, smile:{ParamEyeSmile:1,ParamCheek:1,ParamMouthForm:0.8} };
    for (const [name, vals] of Object.entries(states)) {
      await page.evaluate((v) => window.__miniSetParameters(v), { ...reset, ...vals }); // 워밍업
      const t = await page.evaluate((v) => { const t0=performance.now(); window.__miniSetParameters(v); return performance.now()-t0; }, { ...reset, ...vals });
      out.timing[name] = Math.round(t*10)/10;
      out.hashes[name] = await page.evaluate(() => window.__miniProbe.canvasHash());
      await page.screenshot({ path: config.captures + '/verify_' + name + '.png' });
    }
    await page.evaluate((v) => window.__miniSetParameters(v), { ...reset, ParamAngleX: 30, ParamAngleY: 30 });
    out.neck.head_max = await page.evaluate(() => window.__miniProbe.regionAlphaCount(880, 980, 290, 130, 30));
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
    suffix = "" if args.renderer == "canvas" else f"_{args.renderer}"
    captures = args.out_dir / f"mesh_deform_verify{suffix}"
    captures.mkdir(parents=True, exist_ok=True)
    raw_out = args.out_dir / f"mesh_deform_verify{suffix}_raw.json"

    runner = captures / "verify_runner.js"
    runner.write_text(NODE, encoding="utf-8")
    config_path = captures / "verify_config.json"
    write_json(config_path, {
        "pw": str(PLAYWRIGHT),
        "base": f"http://127.0.0.1:{PORT}/",
        "query": "?renderer=pixi" if args.renderer == "pixi" else "",
        # headless에서 하드웨어 GL이 없으면 WebGL 초기화 실패 — SwiftShader 강제
        "launch_args": ["--use-angle=swiftshader"] if args.renderer == "pixi" else [],
        "captures": str(captures),
        "out": str(raw_out),
    })

    server = subprocess.Popen(
        ["python3", str(ROOT / "scripts/mini_cubism_preview_server.py"), "--project", str(args.project), "--port", str(PORT)],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        wait_for_server("127.0.0.1", PORT)
        subprocess.run(["node", str(runner), str(config_path)], check=True, timeout=300)
    finally:
        terminate(server)

    raw = json.loads(raw_out.read_text())
    checks = {
        "backend_match": raw.get("backend", "canvas") == args.renderer,  # pixi silent 폴백 검출
        "neutral_identity": raw["neutral"]["mesh"] == raw["neutral"]["sprite"],
        "states_distinct": len(set(raw["hashes"].values())) == len(raw["hashes"]),
        "neck_transparent_zero": raw["neck"].get("head_max") == 0,
        "no_errors": not raw["errors"],
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    write_json(args.out_dir / f"mesh_deform_verify{suffix}.json", {
        "generated_at": now_iso(),
        "status": status,
        "renderer": args.renderer,
        "checks": checks,
        "timing_ms": raw["timing"],
        "raw": rel(raw_out),
    })
    print(json.dumps({"status": status, "checks": checks, "timing_ms": raw["timing"]}, ensure_ascii=False))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

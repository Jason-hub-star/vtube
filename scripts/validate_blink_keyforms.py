#!/usr/bin/env python3
"""EYE-NATURAL-002 검증: 정점 키폼 깜빡임이 기준 커튼 워프와 픽셀 일치하는지 (잔상 0 증명).

구 크로스페이드는 키 사이 값에서 두 베이크 프레임이 반투명으로 겹쳐 잔상(주인님 보고:
어지러움)이 생겼다. 정점 키폼은 임의 v에서 렌더가 curtain_warp(t=(1-v)/0.73) 단일
프레임과 일치해야 한다 — 키포인트가 아닌 v들에서 런타임 추출 픽셀과 기준 워프를 비교.

사용: python3 scripts/validate_blink_keyforms.py \
        --project experiments/autorig-character-003/rig_v0_project \
        --arap-config experiments/autorig-character-003/arap_blink_layers/arap_blink_config.json \
        --out-dir experiments/autorig-character-003/reports/eye_natural_001
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, load_json, now_iso, rel, write_json  # noqa: E402
from lib.vtube_proc import terminate, wait_for_server  # noqa: E402
from run_arap_blink_experiment import curtain_warp, eye_bbox_from_layer  # noqa: E402

PLAYWRIGHT = ROOT / "experiments/live2d-strong-model-pattern-001/probe_sandbox/strong20/Samples/TypeScript/Demo/node_modules/playwright"
PORT = 8069
# 키포인트(0.27/1.0)가 아닌 중간값들 — 구 방식이라면 크로스페이드 잔상이 생기는 지점
TEST_VALUES = [0.9, 0.72, 0.51, 0.35]
BG = (244, 240, 232)  # 프리뷰 배경 #f4f0e8

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
  const out = { backend: await page.evaluate(() => window.__miniBackend?.() || 'canvas'), captures: [] };
  for (const v of config.values) {
    await page.evaluate((v) => window.__miniSetParameters({ ParamEyeLOpen: v, ParamEyeROpen: v }), v);
    for (const [side, region] of Object.entries(config.regions)) {
      const b64 = await page.evaluate((r) => window.__miniProbe.regionPixelsBase64(r[0], r[1], r[2], r[3]), region);
      out.captures.push({ v, side, region, b64 });
    }
  }
  await browser.close();
  fs.writeFileSync(config.out, JSON.stringify(out));
})();
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--arap-config", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--renderer", choices=["canvas", "pixi"], default="pixi")
    args = parser.parse_args()
    out = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    cfg = load_json(args.arap_config)
    base = np.asarray(Image.open(ROOT / cfg["assembly"]).convert("RGBA"))
    lower_rise = float(cfg.get("lower_rise", 0.2))
    lower_band = float(cfg.get("lower_band", 0.35))
    skin_band = float(cfg.get("skin_band", 0.9))

    bboxes, regions = {}, {}
    for side in ("L", "R"):
        bbox = eye_bbox_from_layer(ROOT / cfg[f"eye_white_{side}"])
        x0, lash_top, x1, y1 = bbox
        h = y1 - lash_top
        # 비교 영역: 눈 밴드 + 아래 밴드 (위 피부 밴드는 앞머리/눈썹 파트가 위에 그려져 제외)
        ry0 = lash_top - round(h * 0.1)
        ry1 = min(base.shape[0], y1 + round(h * lower_band))
        bboxes[side] = bbox
        regions[side] = [x0, ry0, x1 - x0, ry1 - ry0]

    runner = out / "blink_keyforms_runner.js"
    runner.write_text(NODE, encoding="utf-8")
    raw_out = out / "blink_keyforms_raw.json"
    config_path = out / "blink_keyforms_config.json"
    write_json(config_path, {
        "pw": str(PLAYWRIGHT),
        "url": f"http://127.0.0.1:{PORT}/" + ("?renderer=pixi" if args.renderer == "pixi" else ""),
        "values": TEST_VALUES, "regions": regions, "out": str(raw_out),
    })
    server = subprocess.Popen(
        ["python3", str(ROOT / "scripts/mini_cubism_preview_server.py"), "--project", str(args.project), "--port", str(PORT)],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        wait_for_server("127.0.0.1", PORT)
        subprocess.run(["node", str(runner), str(config_path)], check=True, timeout=180)
    finally:
        terminate(server)

    raw = json.loads(raw_out.read_text())
    rows, worst = [], {"mean": 0.0, "strong": 0.0}
    for cap in raw["captures"]:
        v = cap["v"]
        side = cap["side"]
        x, y, w, h = cap["region"]
        got = np.frombuffer(base64.b64decode(cap["b64"]), dtype=np.uint8).reshape(h, w, 4).astype(int)
        t = (1.0 - v) / (1.0 - 0.27)
        ref_full = curtain_warp(base, bboxes[side], t, skin_band=skin_band, lower_rise=lower_rise, lower_band=lower_band)
        # ±1px 세로 시프트 허용 — 삼각형/리샘플 필터링 차이 흡수 (잔상은 5px+ 스케일이라 무관)
        diffs = []
        for dy in (-1, 0, 1):
            ref = ref_full[y + dy:y + dy + h, x:x + w].astype(int)
            a = ref[..., 3:4] / 255.0
            ref_rgb = (ref[..., :3] * a + np.array(BG) * (1 - a)).astype(int)
            diffs.append(np.abs(got[..., :3] - ref_rgb).max(-1))
        diff = np.minimum(np.minimum(diffs[0], diffs[1]), diffs[2])
        mean = float(diff.mean())
        strong = float((diff > 40).mean())
        rows.append({"v": v, "side": side, "mean_delta": round(mean, 3), "strong_ratio": round(strong, 5)})
        worst["mean"] = max(worst["mean"], mean)
        worst["strong"] = max(worst["strong"], strong)
        Image.fromarray(got.astype(np.uint8), "RGBA").save(out / f"runtime_{side}_v{int(v * 100):03d}.png")
    # 임계: 메시 x샘플(10px) 보간 오차 허용 — 크로스페이드 잔상은 strong 수 % 단위로 나타난다
    status = "PASS" if worst["mean"] < 4.0 and worst["strong"] < 0.02 else "FAIL"
    report = {
        "test_id": "EYE-NATURAL-002-keyform-exactness",
        "generated_at": now_iso(),
        "renderer": raw["backend"],
        "claim": "임의 중간 v에서 렌더 = 기준 curtain_warp(t) 단일 프레임 (크로스페이드 잔상 0)",
        "values": TEST_VALUES,
        "rows": rows,
        "worst": {"mean_delta": round(worst["mean"], 3), "strong_ratio": round(worst["strong"], 5)},
        "thresholds": {"mean_delta": 4.0, "strong_ratio": 0.02},
        "status": status,
    }
    write_json(out / "blink_keyforms_report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

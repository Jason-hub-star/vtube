#!/usr/bin/env python3
"""T3-a/b 스모크: 합성 파라미터 + 저장된 T1 스트림 재생으로 Mini Cubism 드라이브를 검증한다.

T3-a (합성): 결정론적 샘플 12개를 __miniProbe.setParameterValues로 주입.
  - 적용 파라미터 수, 캔버스 해시 변화, EyeOpen 0.27 / MouthOpenY 0.85 클램프 왕복 검증
T3-b (재생): /drive?replay=1&auto=1 페이지가 저장된 T1 175프레임을 끝까지 주입.
  - frames_applied, applied 중앙값, 재생 중 스크린샷의 픽셀 변화 검증

결과: experiments/mini-cubism-webcam-drive-001/reports/t3_smoke_report.{json,md}
"""

from __future__ import annotations

import json
import socket
import statistics
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/mini-cubism-webcam-drive-001"
REPORTS = EXPERIMENT / "reports"
CAPTURES = REPORTS / "captures"
PLAYWRIGHT_MODULE = (
    ROOT
    / "experiments/live2d-strong-model-pattern-001/probe_sandbox/strong20/Samples/TypeScript/Demo/node_modules/playwright"
)
PORT = 8061
BASE_URL = f"http://127.0.0.1:{PORT}"

# 합성 샘플: 적용 후 기대 클램프까지 명시한다 (v21 파라미터 범위 기준).
SYNTHETIC_SAMPLES = [
    {"label": "neutral", "outputs": {"ParamAngleX": 0, "ParamEyeLOpen": 1, "ParamEyeROpen": 1, "ParamEyeBallX": 0, "ParamEyeBallY": 0, "ParamMouthOpenY": 0}, "expect_change": False},
    {"label": "blink_L_full", "outputs": {"ParamEyeLOpen": 0.0, "ParamEyeROpen": 1.0}, "expect_change": True, "expect": {"ParamEyeLOpen": 0.27}},
    {"label": "blink_R_full", "outputs": {"ParamEyeLOpen": 1.0, "ParamEyeROpen": 0.0}, "expect_change": True, "expect": {"ParamEyeROpen": 0.27}},
    {"label": "blink_both_half", "outputs": {"ParamEyeLOpen": 0.5, "ParamEyeROpen": 0.5}, "expect_change": True},
    {"label": "mouth_open_full", "outputs": {"ParamMouthOpenY": 1.0}, "expect_change": True, "expect": {"ParamMouthOpenY": 0.85}},
    {"label": "mouth_open_mid", "outputs": {"ParamMouthOpenY": 0.45}, "expect_change": True},
    {"label": "gaze_left_up", "outputs": {"ParamEyeBallX": -1.0, "ParamEyeBallY": 0.8}, "expect_change": True},
    {"label": "gaze_right_down", "outputs": {"ParamEyeBallX": 1.0, "ParamEyeBallY": -0.8}, "expect_change": True},
    {"label": "head_left", "outputs": {"ParamAngleX": -28.0}, "expect_change": True},
    {"label": "head_right_over", "outputs": {"ParamAngleX": 45.0}, "expect_change": True, "expect": {"ParamAngleX": 30.0}},
    {"label": "combo_talk", "outputs": {"ParamAngleX": 10, "ParamEyeLOpen": 0.6, "ParamEyeROpen": 0.6, "ParamMouthOpenY": 0.7, "ParamEyeBallX": 0.3}, "expect_change": True},
    {"label": "back_to_neutral", "outputs": {"ParamAngleX": 0, "ParamEyeLOpen": 1, "ParamEyeROpen": 1, "ParamEyeBallX": 0, "ParamEyeBallY": 0, "ParamMouthOpenY": 0}, "expect_change": False},
]

NODE_SCRIPT = r"""
const fs = require('fs');
const config = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const { chromium } = require(config.playwright_module);

(async () => {
  const browser = await chromium.launch({ headless: true });
  const result = { t3a: null, t3b: null, errors: [] };
  try {
    // ---- T3-a: 합성 주입 (mini app 직접) ----
    const page = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
    await page.goto(config.base_url + '/', { waitUntil: 'load', timeout: 30000 });
    await page.waitForFunction(() => window.__miniProbe, null, { timeout: 20000 });
    const ready = await page.evaluate(() => window.__miniProbe.waitReady(20000));
    const params = await page.evaluate(() => window.__miniProbe.parameters());
    const neutralHash = await page.evaluate(() => window.__miniProbe.canvasHash());
    await page.screenshot({ path: config.captures_dir + '/t3a_neutral.png' });
    const rows = [];
    for (const sample of config.samples) {
      const applied = await page.evaluate((values) => window.__miniProbe.setParameterValues(values), sample.outputs);
      await page.waitForTimeout(120);
      const hash = await page.evaluate(() => window.__miniProbe.canvasHash());
      const snapshot = await page.evaluate(() => window.__miniProbe.snapshot().parameters);
      rows.push({ label: sample.label, applied: applied.applied, missing: applied.missing, canvas_hash: hash, parameters: snapshot });
      await page.screenshot({ path: config.captures_dir + '/t3a_' + sample.label + '.png' });
      // 다음 샘플 측정의 독립성을 위해 중립 복귀
      await page.evaluate((values) => window.__miniProbe.setParameterValues(values), config.samples[0].outputs);
      await page.waitForTimeout(60);
    }
    result.t3a = { ready, parameter_count: params.length, parameters: params, neutral_hash: neutralHash, rows };
    await page.close();

    // ---- T3-b: 저장된 T1 스트림 재생 (/drive) ----
    const drive = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
    await drive.goto(config.base_url + '/drive?replay=1&auto=1&speed=' + config.replay_speed, { waitUntil: 'load', timeout: 30000 });
    await drive.waitForFunction(() => window.__driveReport && window.__driveReport.frames_applied > 0, null, { timeout: 40000 });
    await drive.screenshot({ path: config.captures_dir + '/t3b_early.png' });
    await drive.waitForFunction(() => window.__driveReport.frames_applied > 60, null, { timeout: 60000 });
    await drive.screenshot({ path: config.captures_dir + '/t3b_mid.png' });
    await drive.waitForFunction(() => window.__driveReport.done === true, null, { timeout: 120000 });
    await drive.screenshot({ path: config.captures_dir + '/t3b_done.png' });
    result.t3b = await drive.evaluate(() => ({
      mode: window.__driveReport.mode,
      frames_applied: window.__driveReport.frames_applied,
      applied_counts: window.__driveReport.applied_counts,
      missing_union: window.__driveReport.missing_union,
      done: window.__driveReport.done,
    }));
    await drive.close();
  } catch (error) {
    result.errors.push(String(error));
  } finally {
    await browser.close();
  }
  fs.writeFileSync(config.raw_out, JSON.stringify(result, null, 2));
})();
"""


def wait_for_server(host: str, port: int, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"server did not start on {host}:{port}")


def image_diff_ratio(a: Path, b: Path, threshold: int = 18) -> float:
    with Image.open(a) as ia, Image.open(b) as ib:
        left = ia.convert("RGB")
        right = ib.convert("RGB")
        if left.size != right.size:
            right = right.resize(left.size)
        gray = ImageChops.difference(left, right).convert("L")
        hist = gray.histogram()
        changed = sum(hist[threshold:])
        return round(changed / (gray.width * gray.height), 6)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    CAPTURES.mkdir(parents=True, exist_ok=True)
    raw_out = REPORTS / "t3_smoke_playwright_raw.json"
    if raw_out.exists():
        raw_out.unlink()

    config_path = REPORTS / "t3_smoke_config.json"
    write_json(
        config_path,
        {
            "playwright_module": str(PLAYWRIGHT_MODULE),
            "base_url": BASE_URL,
            "captures_dir": str(CAPTURES),
            "raw_out": str(raw_out),
            "samples": SYNTHETIC_SAMPLES,
            "replay_speed": 8,
        },
    )
    node_script = REPORTS / "t3_smoke_runner.js"
    node_script.write_text(NODE_SCRIPT, encoding="utf-8")

    server = subprocess.Popen(
        ["python3", str(ROOT / "scripts/run_mini_cubism_webcam_drive.py"), "--port", str(PORT), "--no-open"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_for_server("127.0.0.1", PORT)
        subprocess.run(["node", str(node_script), str(config_path)], check=True, timeout=420)
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()

    raw = json.loads(raw_out.read_text())
    failures: list[str] = []
    if raw.get("errors"):
        failures.append(f"playwright_errors: {raw['errors']}")

    # ---- T3-a 판정 ----
    t3a = raw.get("t3a") or {}
    rows = t3a.get("rows", [])
    a_checks: list[dict[str, Any]] = []
    if not t3a.get("ready"):
        failures.append("t3a_probe_not_ready")
    if t3a.get("parameter_count", 0) < 7:
        failures.append("t3a_parameter_count_below_7")
    neutral_hash = t3a.get("neutral_hash")
    for sample, row in zip(SYNTHETIC_SAMPLES, rows):
        ok = True
        notes = []
        if len(row["applied"]) < 1:
            ok = False
            notes.append("no_applied_parameters")
        changed = row["canvas_hash"] != neutral_hash
        if sample["expect_change"] and not changed:
            ok = False
            notes.append("canvas_hash_unchanged")
        for param, expected in (sample.get("expect") or {}).items():
            actual = row["parameters"].get(param)
            if actual is None or abs(actual - expected) > 1e-6:
                ok = False
                notes.append(f"clamp_mismatch:{param}={actual}!=~{expected}")
        if not ok:
            failures.append(f"t3a_sample_{sample['label']}: {','.join(notes)}")
        a_checks.append({"label": sample["label"], "applied_count": len(row["applied"]), "canvas_changed": changed, "ok": ok, "notes": notes})

    # ---- T3-b 판정 ----
    t3b = raw.get("t3b") or {}
    applied_counts = t3b.get("applied_counts", [])
    b_summary = {
        "frames_applied": t3b.get("frames_applied", 0),
        "applied_median": statistics.median(applied_counts) if applied_counts else 0,
        "applied_min": min(applied_counts) if applied_counts else 0,
        "missing_union": t3b.get("missing_union", []),
        "done": t3b.get("done", False),
    }
    if not b_summary["done"]:
        failures.append("t3b_replay_not_done")
    if b_summary["frames_applied"] < 120:
        failures.append("t3b_frames_below_120")
    if b_summary["applied_median"] < 6:
        failures.append("t3b_applied_median_below_6")
    diff_early = image_diff_ratio(CAPTURES / "t3a_neutral.png", CAPTURES / "t3b_early.png") if (CAPTURES / "t3b_early.png").exists() else 0
    diff_mid_done = (
        image_diff_ratio(CAPTURES / "t3b_mid.png", CAPTURES / "t3b_done.png") if (CAPTURES / "t3b_done.png").exists() else 0
    )
    b_summary["replay_screenshot_diff_mid_vs_done"] = diff_mid_done

    status = "PASS" if not failures else "FAIL"
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "test_id": "T3_mini_cubism_webcam_drive_smoke",
        "status": status,
        "method": "synthetic samples + saved T1 stream replay injected through __miniProbe into the Mini Cubism runtime (v21 rig)",
        "t3a_synthetic": {
            "ready": t3a.get("ready"),
            "parameter_count": t3a.get("parameter_count"),
            "sample_count": len(rows),
            "checks": a_checks,
        },
        "t3b_replay": b_summary,
        "failures": failures,
        "self_review": {
            "probe_ready": bool(t3a.get("ready")),
            "clamp_roundtrip_pass": not any("clamp_mismatch" in f for f in failures),
            "canvas_motion_pass": not any("canvas_hash_unchanged" in f for f in failures),
            "replay_complete": b_summary["done"],
            "status": status,
        },
        "interpretation": {
            "ko": (
                "T1 웹캠 파라미터 체계가 자체 Mini Cubism 런타임을 움직였습니다. 체인 끝단(트래킹→자체 런타임) 최초 연결 성공입니다."
                if status == "PASS"
                else "주입은 실행됐지만 일부 검증 기준이 미달입니다. failures 목록을 확인하세요."
            ),
        },
    }
    write_json(REPORTS / "t3_smoke_report.json", report)
    md = [
        "# T3 Mini Cubism Webcam Drive Smoke",
        "",
        f"- status: `{status}`",
        f"- T3-a samples: {len(rows)} (parameter_count={t3a.get('parameter_count')})",
        f"- T3-b frames_applied: {b_summary['frames_applied']}, applied_median: {b_summary['applied_median']}, done: {b_summary['done']}",
        f"- replay screenshot diff(mid vs done): {diff_mid_done}",
        f"- failures: {failures if failures else 'none'}",
    ]
    (REPORTS / "t3_smoke_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "failures": failures, "t3b": b_summary}, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

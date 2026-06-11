#!/usr/bin/env python3
"""Capture animated Mini Cubism Physics v0.3 motion sweeps."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
BUNDLED_NODE = Path("/Users/family/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")
BUNDLED_PLAYWRIGHT = Path(
    "/Users/family/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/playwright@1.60.0/node_modules/playwright"
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def free_port(host: str = "127.0.0.1") -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def wait_for_server(url: str, proc: subprocess.Popen[str], timeout: float = 20.0) -> None:
    start = time.time()
    last_error = ""
    while time.time() - start < timeout:
        if proc.poll() is not None:
            output = proc.stdout.read() if proc.stdout else ""
            raise RuntimeError(f"preview server exited early\n{output}")
        try:
            with urlopen(url, timeout=1.0) as response:
                if response.status == 200:
                    return
        except URLError as exc:
            last_error = str(exc)
        time.sleep(0.2)
    raise RuntimeError(f"preview server did not become ready: {last_error}")


def node_binary() -> str:
    if BUNDLED_NODE.exists():
        return str(BUNDLED_NODE)
    found = shutil.which("node")
    if found:
        return found
    raise RuntimeError("node binary not found")


def playwright_module() -> str:
    if BUNDLED_PLAYWRIGHT.exists():
        return str(BUNDLED_PLAYWRIGHT)
    return "playwright"


def scenario_frames() -> list[dict[str, Any]]:
    mouth_values = [0, 0.5, 1, 0.5, 0] * 4
    eye_values = [1, 0.5, 0, 0.5, 1] * 4
    angle_frames = []
    for frame in range(36):
        phase = frame / 35
        if phase < 0.33:
            value = phase / 0.33 * 30
        elif phase < 0.66:
            value = 30 - ((phase - 0.33) / 0.33) * 60
        else:
            value = -30 + ((phase - 0.66) / 0.34) * 30
        angle_frames.append({"ParamAngleX": round(value, 3), "ParamHairFront": round(value / 30, 3)})

    settle_frames = []
    for frame in range(48):
        if frame < 8:
            settle_frames.append({"ParamAngleX": 30, "ParamHairFront": 1})
        else:
            settle_frames.append({"ParamAngleX": 0, "ParamHairFront": 0})

    tilt_frames = []
    for frame in range(32):
        phase = frame / 31
        if phase < 0.5:
            value = -15 + phase / 0.5 * 30
        else:
            value = 15 - (phase - 0.5) / 0.5 * 15
        tilt_frames.append({"ParamAngleZ": round(value, 3), "ParamHairFront": round(value / 15, 3), "ParamHairBack": round(value / 18, 3)})

    return [
        {"name": "angle_swing", "frames": angle_frames},
        {"name": "head_tilt", "frames": tilt_frames},
        {"name": "hair_settle", "frames": settle_frames},
        {"name": "mouth_talk", "frames": [{"ParamMouthOpenY": value} for value in mouth_values]},
        {"name": "eye_blink", "frames": [{"ParamEyeLOpen": value, "ParamEyeROpen": value} for value in eye_values]},
    ]


def browser_script() -> str:
    return r"""
const fs = require("fs");
const path = require("path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");

const config = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));

function safeName(value) {
  return String(value).replace(/[^a-zA-Z0-9._-]/g, "_");
}

function hashData(data) {
  let hash = 2166136261 >>> 0;
  const step = 16;
  for (let i = 0; i < data.length; i += step) {
    hash ^= data[i];
    hash = Math.imul(hash, 16777619) >>> 0;
  }
  return hash.toString(16).padStart(8, "0");
}

async function canvasMetrics(page) {
  return await page.evaluate(() => {
    const canvas = document.querySelector("#preview-canvas");
    const ctx = canvas.getContext("2d");
    const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    let nonBackground = 0;
    let left = canvas.width;
    let top = canvas.height;
    let right = 0;
    let bottom = 0;
    for (let i = 0; i < data.length; i += 4) {
      const pixel = i / 4;
      const x = pixel % canvas.width;
      const y = Math.floor(pixel / canvas.width);
      const a = data[i + 3];
      const isBackground =
        Math.abs(data[i] - 32) <= 2 &&
        Math.abs(data[i + 1] - 33) <= 2 &&
        Math.abs(data[i + 2] - 36) <= 2;
      if (!isBackground && a > 0) {
        nonBackground += 1;
        if (x < left) left = x;
        if (y < top) top = y;
        if (x > right) right = x;
        if (y > bottom) bottom = y;
      }
    }
    return {
      width: canvas.width,
      height: canvas.height,
      hash: hashData(data),
      nonBackground,
      contentBounds: nonBackground ? [left, top, right + 1, bottom + 1] : null,
    };

    function hashData(data) {
      let hash = 2166136261 >>> 0;
      const step = 16;
      for (let i = 0; i < data.length; i += step) {
        hash ^= data[i];
        hash = Math.imul(hash, 16777619) >>> 0;
      }
      return hash.toString(16).padStart(8, "0");
    }
  });
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 960, height: 820 } });
  const results = [];
    try {
    await page.goto(config.url, { waitUntil: "networkidle" });
    await page.waitForSelector("#preview-canvas");
    await page.evaluate(() => window.__miniClearSelection && window.__miniClearSelection());
    for (const scenario of config.scenarios) {
      await page.evaluate(() => window.__miniResetPhysics && window.__miniResetPhysics());
      const scenarioDir = path.join(config.framesDir, safeName(scenario.name));
      fs.mkdirSync(scenarioDir, { recursive: true });
      const frames = [];
      for (let index = 0; index < scenario.frames.length; index += 1) {
        await page.evaluate((values) => window.__miniSetParameters(values), scenario.frames[index]);
        await page.evaluate(() => window.__miniStepPhysics(1 / 30));
        await page.waitForTimeout(20);
        const framePath = path.join(scenarioDir, `${String(index).padStart(3, "0")}.png`);
        await page.locator("#preview-canvas").screenshot({ path: framePath });
        frames.push({
          index,
          parameters: scenario.frames[index],
          screenshot: framePath,
          metrics: await canvasMetrics(page),
          snapshot: await page.evaluate(() => window.__miniSnapshot()),
        });
      }
      results.push({ name: scenario.name, frames });
    }
  } finally {
    await browser.close();
  }
  fs.writeFileSync(config.resultPath, JSON.stringify({ ok: true, results }, null, 2));
})().catch((error) => {
  fs.writeFileSync(config.resultPath, JSON.stringify({ ok: false, error: String(error.stack || error) }, null, 2));
  process.exit(1);
});
"""


def run_browser_capture(url: str, out_dir: Path) -> dict[str, Any]:
    frames_dir = out_dir / "frames"
    result_path = out_dir / "motion_capture_result.json"
    config_path = out_dir / "motion_capture_config.json"
    script_path = out_dir / "motion_capture.cjs"
    config = {
        "url": url,
        "framesDir": str(frames_dir),
        "resultPath": str(result_path),
        "scenarios": scenario_frames(),
    }
    write_json(config_path, config)
    script_path.write_text(browser_script())
    env = os.environ.copy()
    env["PLAYWRIGHT_MODULE"] = playwright_module()
    completed = subprocess.run(
        [node_binary(), str(script_path), str(config_path)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = result_path.read_text() if result_path.exists() else completed.stderr
        raise RuntimeError(f"motion capture failed\n{detail}\n{completed.stderr}")
    return load_json(result_path)


def build_gif(frames: list[dict[str, Any]], out_path: Path) -> None:
    images: list[Image.Image] = []
    for frame in frames:
        image = Image.open(frame["screenshot"]).convert("RGB")
        image.thumbnail((520, 520), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (520, 520), "#202124")
        canvas.paste(image, ((520 - image.width) // 2, (520 - image.height) // 2))
        images.append(canvas)
    if not images:
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(out_path, save_all=True, append_images=images[1:], duration=70, loop=0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    out_dir = Path(args.out).resolve()
    reports_dir = out_dir / "reports"
    gifs_dir = out_dir / "gifs"
    out_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    if not (project / "character.json").exists():
        raise SystemExit(f"missing character.json: {project}")

    port = free_port(args.host)
    url = f"http://{args.host}:{port}/"
    server = subprocess.Popen(
        [
            sys.executable,
            str(ROOT / "scripts" / "mini_cubism_preview_server.py"),
            "--project",
            str(project),
            "--host",
            args.host,
            "--port",
            str(port),
        ],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_for_server(f"{url}api/project", server)
        browser_result = run_browser_capture(url, out_dir)
        if not browser_result.get("ok"):
            raise RuntimeError(browser_result.get("error", "unknown browser failure"))
        scenario_reports = []
        for scenario in browser_result["results"]:
            gif_path = gifs_dir / f"{scenario['name']}.gif"
            build_gif(scenario["frames"], gif_path)
            scenario_reports.append({**scenario, "gif": str(gif_path)})
        report = {
            "schema_version": 1,
            "generated_at": now(),
            "project": str(project),
            "status": "CAPTURED_PENDING_SCORE",
            "scenarios": scenario_reports,
        }
        report_path = reports_dir / "motion_sweep_report.json"
        write_json(report_path, report)
        print(json.dumps({"ok": True, "status": report["status"], "report": str(report_path)}, indent=2))
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

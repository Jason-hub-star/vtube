#!/usr/bin/env python3
"""Capture and score Mini Cubism preview poses automatically."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
BUNDLED_NODE = Path("/Users/family/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")
BUNDLED_PLAYWRIGHT = Path(
    "/Users/family/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/playwright@1.60.0/node_modules/playwright"
)

POSES: list[dict[str, Any]] = [
    {"name": "neutral", "parameters": {}},
    {"name": "angle_left", "parameters": {"ParamAngleX": -30}},
    {"name": "angle_right", "parameters": {"ParamAngleX": 30}},
    {"name": "eye_l_close", "parameters": {"ParamEyeLOpen": 0}},
    {"name": "eye_r_close", "parameters": {"ParamEyeROpen": 0}},
    {"name": "mouth_open", "parameters": {"ParamMouthOpenY": 1}},
    {"name": "hair_swing", "parameters": {"ParamHairFront": 1}},
]

VIEWPORTS = [
    {"name": "desktop", "width": 1440, "height": 1000},
    {"name": "mobile", "width": 390, "height": 844},
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


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

async function setPose(page, parameters) {
  await page.evaluate((values) => {
    const project = window.__miniProject;
    const nextValues = {};
    for (const spec of project?.parameters || []) {
      nextValues[spec.id] = spec.default;
    }
    Object.assign(nextValues, values || {});
    if (window.__miniSetParameters) {
      window.__miniSetParameters(nextValues);
      return;
    }
    const rows = Array.from(document.querySelectorAll(".param-row"));
    for (const row of rows) {
      const input = row.querySelector("input");
      if (!input) continue;
      const paramId = row.dataset.paramId;
      if (!Object.prototype.hasOwnProperty.call(nextValues, paramId)) continue;
      input.value = String(nextValues[paramId]);
      input.dispatchEvent(new Event("input", { bubbles: true }));
    }
  }, parameters || {});
  await page.waitForTimeout(120);
}

async function canvasMetrics(page, captureNeutral) {
  return await page.evaluate((shouldCaptureNeutral) => {
    const canvas = document.querySelector("#preview-canvas");
    const ctx = canvas.getContext("2d");
    const image = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = image.data;
    const neutral = window.__neutralCanvasData || null;
    let nonBackground = 0;
    let alphaPixels = 0;
    let diffPixels = 0;
    let totalAbsDiff = 0;
    let left = canvas.width;
    let top = canvas.height;
    let right = 0;
    let bottom = 0;
    for (let i = 0; i < data.length; i += 4) {
      const pixel = i / 4;
      const x = pixel % canvas.width;
      const y = Math.floor(pixel / canvas.width);
      const a = data[i + 3];
      if (a > 0) alphaPixels += 1;
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
      if (neutral) {
        const dr = Math.abs(data[i] - neutral[i]);
        const dg = Math.abs(data[i + 1] - neutral[i + 1]);
        const db = Math.abs(data[i + 2] - neutral[i + 2]);
        const da = Math.abs(data[i + 3] - neutral[i + 3]);
        const diff = dr + dg + db + da;
        totalAbsDiff += diff;
        if (diff > 24) diffPixels += 1;
      }
    }
    if (shouldCaptureNeutral) {
      window.__neutralCanvasData = new Uint8ClampedArray(data);
    }
    return {
      width: canvas.width,
      height: canvas.height,
      hash: hashData(data),
      nonBackground,
      alphaPixels,
      diffPixels,
      totalAbsDiff,
      changedRatio: diffPixels / (canvas.width * canvas.height),
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
  }, captureNeutral);
}

function verdictFor(poseName, metrics, neutralMetrics) {
  const messages = [];
  if (metrics.nonBackground < 1000) messages.push("canvas appears blank");
  if (!metrics.contentBounds) messages.push("content bounds missing");
  if (metrics.contentBounds) {
    const [left, top, right, bottom] = metrics.contentBounds;
    const margin = Math.max(metrics.width, metrics.height) * 0.02;
    if (left < -margin || top < -margin || right > metrics.width + margin || bottom > metrics.height + margin) {
      messages.push("content bounds exceed canvas");
    }
  }
  if (neutralMetrics && neutralMetrics.nonBackground > 0) {
    const alphaRatio = metrics.nonBackground / neutralMetrics.nonBackground;
    if (alphaRatio < 0.65) messages.push("visible content dropped too much");
  }
  if (poseName !== "neutral" && metrics.changedRatio < 0.0002) {
    messages.push("pose barely differs from neutral");
  }
  if (messages.some((item) => item.includes("blank") || item.includes("exceed"))) return { verdict: "FAIL", messages };
  if (messages.length) return { verdict: "REVISE", messages };
  return { verdict: "PASS", messages };
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const results = [];
  try {
    for (const viewport of config.viewports) {
      const page = await browser.newPage({ viewport: { width: viewport.width, height: viewport.height } });
      page.on("console", (message) => {
        if (message.type() === "error") console.error(`[browser:${viewport.name}] ${message.text()}`);
      });
      await page.goto(config.url, { waitUntil: "networkidle" });
      await page.waitForSelector("#preview-canvas");
      await page.waitForFunction(() => Boolean(window.__miniSetParameters && window.__miniClearSelection));
      await page.evaluate(() => window.__miniClearSelection());
      await page.evaluate(async () => {
        window.__miniProject = await fetch("/api/project").then((response) => response.json());
      });
      if (config.showOverlays) {
        for (const label of ["Mesh", "Deformers"]) {
          const button = page.getByRole("button", { name: label });
          if (await button.count()) await button.first().click();
        }
      }

      let neutralMetrics = null;
      const viewportResults = [];
      for (const pose of config.poses) {
        await setPose(page, pose.parameters);
        const metrics = await canvasMetrics(page, pose.name === "neutral");
        if (pose.name === "neutral") {
          neutralMetrics = { ...metrics };
        }
        const screenshot = path.join(config.outDir, `${safeName(viewport.name)}_${safeName(pose.name)}.png`);
        const scored = verdictFor(pose.name, metrics, neutralMetrics);
        if (config.captureElement === "canvas") {
          await page.locator("#preview-canvas").screenshot({ path: screenshot });
        } else {
          await page.screenshot({ path: screenshot, fullPage: true });
        }
        viewportResults.push({
          pose: pose.name,
          parameters: pose.parameters,
          screenshot,
          metrics,
          verdict: scored.verdict,
          messages: scored.messages,
        });
      }
      await page.close();
      results.push({ viewport, poses: viewportResults });
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


def run_browser_capture(
    url: str,
    out_dir: Path,
    exclude_poses: set[str] | None = None,
    capture_element: str = "canvas",
    show_overlays: bool = False,
) -> dict[str, Any]:
    exclude_poses = exclude_poses or set()
    result_path = out_dir / "playwright_result.json"
    config_path = out_dir / "playwright_config.json"
    script_path = out_dir / "playwright_pose_sweep.cjs"
    config = {
        "url": url,
        "outDir": str(out_dir),
        "resultPath": str(result_path),
        "poses": [pose for pose in POSES if pose["name"] not in exclude_poses],
        "viewports": VIEWPORTS,
        "captureElement": capture_element,
        "showOverlays": show_overlays,
    }
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n")
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
        raise RuntimeError(f"playwright pose sweep failed\n{detail}\n{completed.stderr}")
    return load_json(result_path)


def score_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    all_pose_results = [pose for viewport in results for pose in viewport["poses"]]
    present_poses = {pose["pose"] for pose in all_pose_results}
    pass_count = sum(1 for item in all_pose_results if item["verdict"] == "PASS")
    revise_count = sum(1 for item in all_pose_results if item["verdict"] == "REVISE")
    fail_count = sum(1 for item in all_pose_results if item["verdict"] == "FAIL")
    changed = [
        item
        for item in all_pose_results
        if item["pose"] != "neutral" and item["metrics"]["changedRatio"] >= 0.0002 and item["verdict"] != "FAIL"
    ]
    desktop_changed = {
        item["pose"]
        for viewport in results
        if viewport["viewport"]["name"] == "desktop"
        for item in viewport["poses"]
        if item["pose"] != "neutral" and item["metrics"]["changedRatio"] >= 0.0002
    }
    has_angle = not ({"angle_left", "angle_right"} & present_poses) or bool({"angle_left", "angle_right"} & desktop_changed)
    has_mouth = "mouth_open" not in present_poses or "mouth_open" in desktop_changed
    has_hair = "hair_swing" not in present_poses or "hair_swing" in desktop_changed
    required_changed = len({pose for pose in present_poses if pose != "neutral"})
    changed_enough = len({item["pose"] for item in changed}) >= min(required_changed, 3)
    status = "PASS" if fail_count == 0 and changed_enough and has_angle and has_mouth and has_hair else "REVISE"
    score = pass_count * 10 + revise_count * 4 - fail_count * 15
    desktop_motion = {
        item["pose"]: item["metrics"]["changedRatio"]
        for viewport in results
        if viewport["viewport"]["name"] == "desktop"
        for item in viewport["poses"]
        if item["pose"] in {"angle_left", "angle_right", "eye_l_close", "eye_r_close", "mouth_open", "hair_swing"}
    }
    score += min(18, int(desktop_motion.get("angle_left", 0) * 180))
    score += min(18, int(desktop_motion.get("angle_right", 0) * 180))
    score += min(14, int(desktop_motion.get("eye_l_close", 0) * 250))
    score += min(14, int(desktop_motion.get("eye_r_close", 0) * 250))
    score += min(22, int(desktop_motion.get("mouth_open", 0) * 9000))
    score += min(22, int(desktop_motion.get("hair_swing", 0) * 260))
    return {
        "status": status,
        "score": score,
        "counts": {"PASS": pass_count, "REVISE": revise_count, "FAIL": fail_count},
        "changed_pose_count": len({item["pose"] for item in changed}),
        "desktop_changed_poses": sorted(desktop_changed),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--exclude-pose", action="append", default=[])
    parser.add_argument("--capture-element", choices=["canvas", "page"], default="canvas")
    parser.add_argument("--show-overlays", action="store_true")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    out_dir = Path(args.out).resolve()
    screenshots_dir = out_dir / "screenshots"
    reports_dir = out_dir / "reports"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
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
        browser_result = run_browser_capture(
            url,
            screenshots_dir,
            set(args.exclude_pose),
            capture_element=args.capture_element,
            show_overlays=args.show_overlays,
        )
        if not browser_result.get("ok"):
            raise RuntimeError(browser_result.get("error", "unknown browser failure"))
        summary = score_summary(browser_result["results"])
        report = {
            "schema_version": 1,
            "generated_at": now(),
            "project": str(project),
            "url": url,
            "status": summary["status"],
            "score": summary["score"],
            "summary": summary,
            "results": browser_result["results"],
        }
        report_path = reports_dir / "pose_sweep_report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"ok": True, "status": report["status"], "score": report["score"], "report": str(report_path)}, indent=2))
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

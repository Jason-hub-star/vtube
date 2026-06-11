#!/usr/bin/env python3
"""Capture face-focused Mini Cubism QA evidence."""

from __future__ import annotations

import argparse
import json
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

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
BUNDLED_NODE = Path("/Users/family/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")
BUNDLED_PLAYWRIGHT = Path(
    "/Users/family/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/playwright@1.60.0/node_modules/playwright"
)
FACE_CROP = (640, 360, 1460, 980)


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


def poses() -> list[dict[str, Any]]:
    return [
        {"name": "neutral", "parameters": {}},
        {"name": "angle_left", "parameters": {"ParamAngleX": -30}},
        {"name": "angle_right", "parameters": {"ParamAngleX": 30}},
        {"name": "eye_look_left", "parameters": {"ParamEyeBallX": -1}},
        {"name": "eye_look_right", "parameters": {"ParamEyeBallX": 1}},
        {"name": "eye_look_up", "parameters": {"ParamEyeBallY": 1}},
        {"name": "brow_raise", "parameters": {"ParamBrowLY": 1, "ParamBrowRY": 1}},
        {"name": "brow_down", "parameters": {"ParamBrowLY": -1, "ParamBrowRY": -1}},
        {"name": "smile", "parameters": {"ParamMouthForm": 1, "ParamCheek": 1}},
        {"name": "frown", "parameters": {"ParamMouthForm": -1}},
        {"name": "mouth_open", "parameters": {"ParamMouthOpenY": 1, "ParamCheek": 0.4}},
        {"name": "blink", "parameters": {"ParamEyeLOpen": 0, "ParamEyeROpen": 0}},
    ]


def browser_script() -> str:
    return r"""
const fs = require("fs");
const path = require("path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");

const config = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));

async function metrics(page) {
  return await page.evaluate(() => {
    const canvas = document.querySelector("#preview-canvas");
    const ctx = canvas.getContext("2d");
    const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    let hash = 2166136261 >>> 0;
    let nonBackground = 0;
    for (let i = 0; i < data.length; i += 16) {
      hash ^= data[i];
      hash = Math.imul(hash, 16777619) >>> 0;
    }
    for (let i = 0; i < data.length; i += 4) {
      const isBackground = Math.abs(data[i] - 32) <= 2 && Math.abs(data[i + 1] - 33) <= 2 && Math.abs(data[i + 2] - 36) <= 2;
      if (!isBackground && data[i + 3] > 0) nonBackground += 1;
    }
    return { hash: hash.toString(16).padStart(8, "0"), nonBackground };
  });
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 980, height: 860 } });
  const results = [];
  try {
    await page.goto(config.url, { waitUntil: "networkidle" });
    await page.waitForSelector("#preview-canvas");
    for (const label of ["Mesh", "Deformers"]) {
      const button = page.getByRole("button", { name: label });
      if (await button.count()) await button.first().click();
    }
    for (const pose of config.poses) {
      await page.evaluate(() => window.__miniResetPhysics && window.__miniResetPhysics());
      await page.evaluate((values) => window.__miniSetParameters(values), pose.parameters);
      await page.waitForTimeout(60);
      const screenshot = path.join(config.framesDir, `${pose.name}.png`);
      await page.locator("#preview-canvas").screenshot({ path: screenshot });
      results.push({
        name: pose.name,
        parameters: pose.parameters,
        screenshot,
        metrics: await metrics(page),
        snapshot: await page.evaluate(() => window.__miniSnapshot()),
      });
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


def font(size: int) -> ImageFont.ImageFont:
    for candidate in ["/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"]:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def crop_face(frame: Path, out: Path) -> None:
    image = Image.open(frame).convert("RGB")
    image.crop(FACE_CROP).save(out)


def build_contact_sheet(results: list[dict[str, Any]], out: Path, crops_dir: Path) -> None:
    cols = 4
    cell_w = 280
    cell_h = 260
    header_h = 70
    rows = (len(results) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, header_h + rows * cell_h), "#f4f0e8")
    draw = ImageDraw.Draw(sheet)
    draw.text((18, 14), "Mini Cubism Face QA v1", fill="#202124", font=font(25))
    draw.text((18, 46), "Close-up face parameter evidence, not final art approval.", fill="#5f6368", font=font(13))
    small = font(14)
    for index, result in enumerate(results):
        x = (index % cols) * cell_w
        y = header_h + (index // cols) * cell_h
        draw.rectangle([x + 8, y + 8, x + cell_w - 8, y + cell_h - 8], fill="#ffffff", outline="#d6d0c8")
        crop_path = crops_dir / f"{result['name']}.png"
        tile = Image.open(crop_path).convert("RGB")
        tile.thumbnail((cell_w - 30, cell_h - 55), Image.Resampling.LANCZOS)
        sheet.paste(tile, (x + (cell_w - tile.width) // 2, y + 14))
        draw.text((x + 16, y + cell_h - 34), result["name"], fill="#202124", font=small)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def build_gif(results: list[dict[str, Any]], crops_dir: Path, out: Path) -> None:
    sequence = ["neutral", "eye_look_left", "eye_look_right", "brow_raise", "smile", "mouth_open", "blink", "neutral"]
    existing = {item["name"] for item in results}
    frames = []
    for name in sequence:
        if name not in existing:
            continue
        image = Image.open(crops_dir / f"{name}.png").convert("RGB")
        image.thumbnail((520, 520), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (520, 520), "#202124")
        canvas.paste(image, ((520 - image.width) // 2, (520 - image.height) // 2))
        frames.append(canvas)
    if frames:
        out.parent.mkdir(parents=True, exist_ok=True)
        frames[0].save(out, save_all=True, append_images=frames[1:], duration=420, loop=0)


def run_browser_capture(url: str, out_dir: Path) -> dict[str, Any]:
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    config_path = out_dir / "face_capture_config.json"
    result_path = out_dir / "face_capture_result.json"
    script_path = out_dir / "face_capture.cjs"
    write_json(config_path, {"url": url, "framesDir": str(frames_dir), "resultPath": str(result_path), "poses": poses()})
    script_path.write_text(browser_script())
    env = {"PLAYWRIGHT_MODULE": playwright_module(), **dict(**__import__("os").environ)}
    completed = subprocess.run([node_binary(), str(script_path), str(config_path)], cwd=ROOT, env=env, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        detail = result_path.read_text() if result_path.exists() else completed.stderr
        raise RuntimeError(f"face capture failed\n{detail}\n{completed.stderr}")
    return load_json(result_path)


def score(project: dict[str, Any], results: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    parameters = {item.get("id") for item in project.get("parameters", [])}
    required = {"ParamEyeBallX", "ParamEyeBallY", "ParamBrowLY", "ParamBrowRY", "ParamMouthForm", "ParamCheek"}
    parts = {item.get("id") for item in project.get("parts", [])}
    face_parts = {"nose_bridge", "nose_tip", "mouth_corner_L", "mouth_corner_R", "eye_shadow_L", "eye_shadow_R"}
    hashes = {item.get("metrics", {}).get("hash") for item in results}
    checks = [
        {"check": "required_face_parameters", "status": "PASS" if required <= parameters else "FAIL", "missing": sorted(required - parameters)},
        {"check": "required_face_parts", "status": "PASS" if face_parts <= parts else "FAIL", "missing": sorted(face_parts - parts)},
        {"check": "pose_visual_variation", "status": "PASS" if len(hashes) >= 8 else "FAIL", "distinct_hashes": len(hashes)},
        {"check": "nonblank_frames", "status": "PASS" if all(item.get("metrics", {}).get("nonBackground", 0) > 1000 for item in results) else "FAIL"},
    ]
    return ("PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL", checks)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    project_dir = Path(args.project).resolve()
    out_dir = Path(args.out).resolve()
    reports_dir = out_dir / "reports"
    crops_dir = out_dir / "face_crops"
    out_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    crops_dir.mkdir(parents=True, exist_ok=True)
    project = load_json(project_dir / "character.json")

    port = free_port(args.host)
    url = f"http://{args.host}:{port}/"
    server = subprocess.Popen(
        [sys.executable, str(ROOT / "scripts" / "mini_cubism_preview_server.py"), "--project", str(project_dir), "--host", args.host, "--port", str(port)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_for_server(f"{url}api/project", server)
        capture = run_browser_capture(url, out_dir)
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)

    if not capture.get("ok"):
        raise RuntimeError(capture.get("error", "unknown face capture failure"))
    for item in capture["results"]:
        crop_face(Path(item["screenshot"]), crops_dir / f"{item['name']}.png")
    contact_sheet = out_dir / "face_contact_sheet.png"
    best_gif = out_dir / "face_motion.gif"
    build_contact_sheet(capture["results"], contact_sheet, crops_dir)
    build_gif(capture["results"], crops_dir, best_gif)
    status, checks = score(project, capture["results"])
    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": status,
        "project": str(project_dir),
        "poses": capture["results"],
        "checks": checks,
        "contact_sheet": str(contact_sheet),
        "best_motion": str(best_gif),
        "interpretation": "Face QA proves parameter-level local preview variation, not final face art quality.",
    }
    write_json(reports_dir / "face_qa_report.json", report)
    summary = (
        "# Mini Cubism Face QA v1\n\n"
        f"- Status: `{status}`\n"
        f"- Contact sheet: `{contact_sheet}`\n"
        f"- Face GIF: `{best_gif}`\n"
        "- Review choices: 유지 / 눈동자 약하게 / 표정 더 크게 / 얼굴 파츠 다시 생성\n"
    )
    (out_dir / "face_review_summary.md").write_text(summary)
    print(json.dumps({"ok": status == "PASS", "status": status, "report": str(reports_dir / "face_qa_report.json")}, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

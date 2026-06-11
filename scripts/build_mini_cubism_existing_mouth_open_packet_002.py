#!/usr/bin/env python3
"""Capture existing-mouth-only MouthOpenY evidence for Character 002 Mini Cubism."""

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

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROJECT = (
    ROOT
    / "experiments"
    / "cubism-v2-new-character-002"
    / "model_edit_v8_existing_mouth_tuned_preview"
    / "mini_cubism_diagnostic_project"
)
DEFAULT_OUT = (
    ROOT
    / "experiments"
    / "cubism-v2-new-character-002"
    / "reports"
    / "model_edit_v8_existing_mouth_tuned_preview"
    / "existing_mouth_open_packet"
)
BUNDLED_NODE = Path("/Users/family/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")
BUNDLED_PLAYWRIGHT = Path(
    "/Users/family/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/playwright@1.60.0/node_modules/playwright"
)
MOUTH_VALUES = [
    ("mouthopen_0_00_closed", 0.0, "closed smile"),
    ("mouthopen_0_20_tiny", 0.2, "tiny opening"),
    ("mouthopen_0_40_soft", 0.4, "soft transition"),
    ("mouthopen_0_60_mid", 0.6, "mid transition"),
    ("mouthopen_0_80_open", 0.8, "open"),
    ("mouthopen_1_00_full", 1.0, "full existing small open"),
]


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


def browser_script() -> str:
    return r"""
const fs = require("fs");
const path = require("path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");

const config = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));

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
    return { width: canvas.width, height: canvas.height, hash: hashData(data) };

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
  const page = await browser.newPage({ viewport: { width: 1100, height: 900 } });
  const frames = [];
  try {
    await page.goto(config.url, { waitUntil: "networkidle" });
    await page.waitForSelector("#preview-canvas");
    await page.waitForFunction(() => Boolean(window.__miniSetParameters && window.__miniSnapshot));
    await page.evaluate(() => window.__miniClearSelection && window.__miniClearSelection());
    for (const frame of config.frames) {
      const values = {
        ParamAngleX: 0,
        ParamEyeLOpen: 1,
        ParamEyeROpen: 1,
        ParamMouthOpenY: frame.mouthOpen,
        ParamHairFront: 0,
      };
      await page.evaluate(() => window.__miniResetPhysics && window.__miniResetPhysics());
      await page.evaluate((parameters) => window.__miniSetParameters(parameters), values);
      await page.waitForTimeout(80);
      const screenshot = path.join(config.framesDir, `${frame.id}.png`);
      await page.locator("#preview-canvas").screenshot({ path: screenshot });
      frames.push({
        ...frame,
        parameters: values,
        screenshot,
        metrics: await canvasMetrics(page),
        snapshot: await page.evaluate(() => window.__miniSnapshot()),
      });
    }
  } finally {
    await browser.close();
  }
  fs.writeFileSync(config.resultPath, JSON.stringify({ ok: true, frames }, null, 2));
})().catch((error) => {
  fs.writeFileSync(config.resultPath, JSON.stringify({ ok: false, error: String(error.stack || error) }, null, 2));
  process.exit(1);
});
"""


def run_browser_capture(url: str, out_dir: Path) -> dict[str, Any]:
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    result_path = out_dir / "existing_mouth_open_browser_result.json"
    config_path = out_dir / "existing_mouth_open_browser_config.json"
    script_path = out_dir / "existing_mouth_open_capture.cjs"
    config = {
        "url": url,
        "framesDir": str(frames_dir),
        "resultPath": str(result_path),
        "frames": [{"id": frame_id, "mouthOpen": value, "label": label} for frame_id, value, label in MOUTH_VALUES],
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
        raise RuntimeError(f"existing mouth capture failed\n{detail}\n{completed.stderr}")
    return load_json(result_path)


def font(size: int) -> ImageFont.ImageFont:
    for candidate in [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def fit_image(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    fitted = image.copy().convert("RGB")
    fitted.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "#202124")
    canvas.paste(fitted, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2))
    return canvas


def mouth_crop(image: Image.Image) -> Image.Image:
    width, height = image.size
    return image.crop((int(width * 0.32), int(height * 0.34), int(width * 0.68), int(height * 0.62)))


def active_mouth_parts(frame: dict[str, Any]) -> list[str]:
    part_opacity = frame.get("snapshot", {}).get("part_opacity", {})
    active = []
    for part_id in ["mouth_closed_smile", "mouth_small_open", "mouth_inner", "mouth_teeth", "mouth_tongue"]:
        if float(part_opacity.get(part_id, 0)) >= 0.05:
            active.append(f"{part_id}:{float(part_opacity.get(part_id, 0)):.2f}")
    return active


def changed_ratio(a_path: Path, b_path: Path) -> float:
    a = Image.open(a_path).convert("RGB")
    b = Image.open(b_path).convert("RGB")
    if a.size != b.size:
        b = b.resize(a.size, Image.Resampling.BILINEAR)
    changed = 0
    total = a.width * a.height
    ap = a.load()
    bp = b.load()
    for y in range(a.height):
        for x in range(a.width):
            if sum(abs(ap[x, y][i] - bp[x, y][i]) for i in range(3)) > 18:
                changed += 1
    return changed / total if total else 0.0


def build_contact_sheet(frames: list[dict[str, Any]], out_path: Path) -> None:
    cols = 3
    cell_w = 430
    cell_h = 560
    margin = 28
    header_h = 72
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (margin * 2 + cell_w * cols, margin * 2 + header_h + cell_h * rows), "#151719")
    draw = ImageDraw.Draw(sheet)
    title_font = font(24)
    label_font = font(18)
    small_font = font(14)
    draw.text((margin, margin), "Character 002 Existing MouthOpenY v8 Packet", fill="#f1f3f4", font=title_font)
    draw.text(
        (margin, margin + 34),
        "Existing generated active mouth PNGs only: mouth_closed_smile -> mouth_small_open.",
        fill="#b8c0c8",
        font=small_font,
    )
    for index, frame in enumerate(frames):
        col = index % cols
        row = index // cols
        x = margin + col * cell_w
        y = margin + header_h + row * cell_h
        image = Image.open(frame["screenshot"]).convert("RGB")
        full = fit_image(image, (cell_w - 24, 300))
        close = fit_image(mouth_crop(image), (cell_w - 24, 138))
        draw.rounded_rectangle((x + 6, y + 6, x + cell_w - 6, y + cell_h - 6), radius=8, fill="#202124", outline="#3a3f45")
        draw.text((x + 18, y + 18), f"MouthOpenY {frame['mouthOpen']:.2f}", fill="#f1f3f4", font=label_font)
        draw.text((x + 18, y + 44), frame["label"], fill="#b8c0c8", font=small_font)
        sheet.paste(full, (x + 12, y + 76))
        draw.text((x + 18, y + 380), "mouth close-up", fill="#b8c0c8", font=small_font)
        sheet.paste(close, (x + 12, y + 404))
        active = ", ".join(active_mouth_parts(frame))
        if len(active) > 54:
            active = active[:51] + "..."
        draw.text((x + 18, y + 536), active, fill="#d7dadc", font=small_font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Character 002 Existing MouthOpenY v8 Packet",
        "",
        f"- Status: `{report['status']}`",
        f"- Project: `{report['project']}`",
        f"- Contact sheet: `{report['contact_sheet']}`",
        "",
        "## Decision",
        "",
        "- Uses existing generated mouth art only.",
        "- Active mouth parts are `mouth_closed_smile` and `mouth_small_open`.",
        "- Helper parts remain hidden/reference-only; rejected O/wide states remain excluded.",
        "",
        "## Frames",
        "",
        "| MouthOpenY | Label | Active mouth opacity | Changed vs closed | Screenshot |",
        "|---:|---|---|---:|---|",
    ]
    for frame in report["frames"]:
        lines.append(
            f"| {frame['mouthOpen']:.2f} | {frame['label']} | `{', '.join(frame['active_mouth_parts'])}` | "
            f"{frame['changed_ratio_vs_closed']:.6f} | `{frame['screenshot']}` |"
        )
    path.write_text("\n".join(lines) + "\n")


def build_report(project: Path, out_dir: Path, browser_result: dict[str, Any]) -> dict[str, Any]:
    if not browser_result.get("ok"):
        raise RuntimeError(browser_result.get("error", "unknown browser failure"))
    frames = browser_result["frames"]
    closed_path = Path(frames[0]["screenshot"])
    for frame in frames:
        frame["active_mouth_parts"] = active_mouth_parts(frame)
        frame["changed_ratio_vs_closed"] = changed_ratio(closed_path, Path(frame["screenshot"]))
        frame["screenshot"] = str(Path(frame["screenshot"]))
    contact_sheet = out_dir / "existing_mouth_open_contact_sheet.png"
    build_contact_sheet(frames, contact_sheet)
    return {
        "schema_version": 1,
        "generated_at": now(),
        "status": "PASS_EXISTING_MOUTH_OPEN_CAPTURED",
        "project": str(project),
        "contact_sheet": str(contact_sheet),
        "frames": frames,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=str(DEFAULT_PROJECT))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
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
        report = build_report(project, out_dir, browser_result)
        report_path = out_dir / "existing_mouth_open_report.json"
        md_path = out_dir / "existing_mouth_open_report.md"
        write_json(report_path, report)
        write_markdown(report, md_path)
        print(
            json.dumps(
                {
                    "ok": True,
                    "status": report["status"],
                    "report": str(report_path),
                    "markdown": str(md_path),
                    "contact_sheet": report["contact_sheet"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
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

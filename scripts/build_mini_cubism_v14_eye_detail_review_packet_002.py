#!/usr/bin/env python3
"""Capture Character 002 v14 eye-detail/in-between review packet."""

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
    / "experiments/cubism-v2-new-character-002/model_edit_v14_eye_detail_inbetween_preview/mini_cubism_diagnostic_project"
)
DEFAULT_OUT = ROOT / "experiments/cubism-v2-new-character-002/reports/model_edit_v14_eye_detail_inbetween_preview/eye_detail_review_packet"
BUNDLED_NODE = Path("/Users/family/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")
BUNDLED_PLAYWRIGHT = Path(
    "/Users/family/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/playwright@1.60.0/node_modules/playwright"
)


FRAMES = [
    {"id": "open_center", "label": "open / centered iris", "eyeOpen": 1.00, "eyeBallX": 0.0, "eyeBallY": 0.0},
    {"id": "open_left", "label": "open / eyeball left", "eyeOpen": 1.00, "eyeBallX": -1.0, "eyeBallY": 0.0},
    {"id": "open_right", "label": "open / eyeball right", "eyeOpen": 1.00, "eyeBallX": 1.0, "eyeBallY": 0.0},
    {"id": "open_up", "label": "open / eyeball up", "eyeOpen": 1.00, "eyeBallX": 0.0, "eyeBallY": -1.0},
    {"id": "open_down", "label": "open / eyeball down", "eyeOpen": 1.00, "eyeBallX": 0.0, "eyeBallY": 1.0},
    {"id": "eyeopen_080", "label": "in-between 0.80", "eyeOpen": 0.80, "eyeBallX": 0.0, "eyeBallY": 0.0},
    {"id": "eyeopen_065", "label": "in-between 0.65", "eyeOpen": 0.65, "eyeBallX": 0.0, "eyeBallY": 0.0},
    {"id": "eyeopen_050", "label": "in-between 0.50", "eyeOpen": 0.50, "eyeBallX": 0.0, "eyeBallY": 0.0},
    {"id": "eyeopen_038", "label": "in-between 0.38", "eyeOpen": 0.38, "eyeBallX": 0.0, "eyeBallY": 0.0},
    {"id": "eyeopen_027", "label": "natural close 0.27", "eyeOpen": 0.27, "eyeBallX": 0.0, "eyeBallY": 0.0},
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


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
    return { width: canvas.width, height: canvas.height, nonBackground, contentBounds: nonBackground ? [left, top, right + 1, bottom + 1] : null };
  });
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1180, height: 920 } });
  const frames = [];
  try {
    await page.goto(config.url, { waitUntil: "networkidle" });
    await page.waitForSelector("#preview-canvas");
    await page.waitForFunction(() => Boolean(window.__miniSetParameters && window.__miniSnapshot));
    await page.evaluate(() => window.__miniClearSelection && window.__miniClearSelection());
    for (const frame of config.frames) {
      const values = {
        ParamAngleX: 0,
        ParamEyeLOpen: frame.eyeOpen,
        ParamEyeROpen: frame.eyeOpen,
        ParamEyeBallX: frame.eyeBallX,
        ParamEyeBallY: frame.eyeBallY,
        ParamMouthOpenY: 0,
        ParamHairFront: 0,
      };
      await page.evaluate(() => window.__miniResetPhysics && window.__miniResetPhysics());
      await page.evaluate((parameters) => window.__miniSetParameters(parameters), values);
      await page.waitForTimeout(100);
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
    result_path = out_dir / "eye_detail_browser_result.json"
    config_path = out_dir / "eye_detail_browser_config.json"
    script_path = out_dir / "eye_detail_capture.cjs"
    config = {
        "url": url,
        "framesDir": str(frames_dir),
        "resultPath": str(result_path),
        "frames": FRAMES,
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
        raise RuntimeError(f"eye detail capture failed\n{detail}\n{completed.stderr}")
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


def eye_crop(image: Image.Image) -> Image.Image:
    width, height = image.size
    box = (
        int(width * 0.18),
        int(height * 0.15),
        int(width * 0.82),
        int(height * 0.50),
    )
    return image.crop(box)


def active_eye_parts(frame: dict[str, Any], threshold: float = 0.15) -> list[str]:
    part_opacity = frame.get("snapshot", {}).get("part_opacity", {})
    active: list[str] = []
    for part_id in [
        "eye_L_white",
        "eye_L_iris",
        "eye_L_pupil",
        "eye_L_highlight",
        "eye_L_lid_inbetween_080",
        "eye_L_lid_inbetween_065",
        "eye_L_lid_inbetween_038",
        "eye_L_half_closed_lid",
        "eye_L_mostly_closed_lid",
        "eye_L_closed_lid",
        "eye_R_white",
        "eye_R_iris",
        "eye_R_pupil",
        "eye_R_highlight",
        "eye_R_lid_inbetween_080",
        "eye_R_lid_inbetween_065",
        "eye_R_lid_inbetween_038",
        "eye_R_half_closed_lid",
        "eye_R_mostly_closed_lid",
        "eye_R_closed_lid",
    ]:
        if float(part_opacity.get(part_id, 0)) >= threshold:
            active.append(part_id)
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
    cell_w = 350
    cell_h = 520
    cols = 5
    rows = 2
    margin = 28
    header_h = 72
    sheet = Image.new("RGB", (margin * 2 + cell_w * cols, margin * 2 + header_h + cell_h * rows), "#151719")
    draw = ImageDraw.Draw(sheet)
    title_font = font(24)
    label_font = font(17)
    small_font = font(13)
    draw.text((margin, margin), "Character 002 v14 Eye Detail + EyeOpen In-Between Review", fill="#f1f3f4", font=title_font)
    draw.text((margin, margin + 36), "v13 success pattern preserved: EyeOpen min 0.27, MouthOpenY max 0.85. Eye detail split is diagnostic.", fill="#b8c0c8", font=small_font)
    for index, frame in enumerate(frames):
        col = index % cols
        row = index // cols
        x = margin + col * cell_w
        y = margin + header_h + row * cell_h
        image = Image.open(frame["screenshot"]).convert("RGB")
        full = fit_image(image, (cell_w - 22, 250))
        crop = fit_image(eye_crop(image), (cell_w - 22, 120))
        draw.rounded_rectangle((x + 6, y + 6, x + cell_w - 6, y + cell_h - 6), radius=8, fill="#202124", outline="#3a3f45")
        draw.text((x + 16, y + 16), frame["label"], fill="#f1f3f4", font=label_font)
        draw.text((x + 16, y + 40), f"EyeOpen {frame['eyeOpen']:.2f}  EyeBall ({frame['eyeBallX']:.1f}, {frame['eyeBallY']:.1f})", fill="#b8c0c8", font=small_font)
        sheet.paste(full, (x + 11, y + 66))
        draw.text((x + 16, y + 320), "eye close-up", fill="#b8c0c8", font=small_font)
        sheet.paste(crop, (x + 11, y + 340))
        active = ", ".join(active_eye_parts(frame))
        if len(active) > 70:
            active = active[:67] + "..."
        draw.text((x + 16, y + 468), active, fill="#d7dadc", font=small_font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Character 002 v14 Eye Detail Review Packet",
        "",
        f"- Status: `{report['status']}`",
        f"- Project: `{report['project']}`",
        f"- Contact sheet: `{report['contact_sheet']}`",
        f"- Generated at: `{report['generated_at']}`",
        "",
        "## Decision",
        "",
        "- v14 preserves v13 diagnostic limits: `ParamEyeLOpen/ROpen` min `0.27`, `ParamMouthOpenY` max `0.85`.",
        "- `ParamEyeBallX/Y` now move derived iris/pupil/highlight parts.",
        "- This is still diagnostic layer-split evidence because the eye detail is derived from baked `eye_open` art.",
        "",
        "## Frames",
        "",
        "| Frame | EyeOpen | EyeBallX | EyeBallY | Changed vs center | Active eye parts | Screenshot |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for frame in report["frames"]:
        active = ", ".join(frame["active_eye_parts"])
        lines.append(
            f"| {frame['label']} | {frame['eyeOpen']:.2f} | {frame['eyeBallX']:.1f} | {frame['eyeBallY']:.1f} | "
            f"{frame['changed_ratio_vs_center']:.6f} | `{active}` | `{frame['screenshot']}` |"
        )
    path.write_text("\n".join(lines) + "\n")


def build_report(project: Path, out_dir: Path, browser_result: dict[str, Any]) -> dict[str, Any]:
    if not browser_result.get("ok"):
        raise RuntimeError(browser_result.get("error", "unknown browser failure"))
    frames = browser_result["frames"]
    center_path = Path(frames[0]["screenshot"])
    for frame in frames:
        frame["active_eye_parts"] = active_eye_parts(frame)
        frame["changed_ratio_vs_center"] = changed_ratio(center_path, Path(frame["screenshot"]))
        frame["screenshot"] = str(Path(frame["screenshot"]))
    contact_sheet = out_dir / "v14_eye_detail_review_contact_sheet.png"
    build_contact_sheet(frames, contact_sheet)
    project_json = load_json(project / "character.json")
    technical_pass = all(frame["metrics"]["nonBackground"] > 1000 for frame in frames)
    eye_ball_moved = all(frame["changed_ratio_vs_center"] > 0.00008 for frame in frames[1:5])
    close_changed = frames[-1]["changed_ratio_vs_center"] > 0.001
    status = "PASS_TECHNICAL_EYE_DETAIL_PACKET_READY" if technical_pass and eye_ball_moved and close_changed else "REVISE_TECHNICAL_EYE_DETAIL_PACKET"
    return {
        "schema_version": 1,
        "generated_at": now(),
        "status": status,
        "project": str(project),
        "contact_sheet": str(contact_sheet),
        "parameters": [item["id"] for item in project_json.get("parameters", [])],
        "checks": {
            "technical_nonblank": technical_pass,
            "eye_ball_moved_numeric": eye_ball_moved,
            "eye_close_changed_numeric": close_changed,
            "human_visual_qa": "REQUIRED",
        },
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
            str(ROOT / "scripts/mini_cubism_preview_server.py"),
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
        report_path = out_dir / "v14_eye_detail_review_report.json"
        md_path = out_dir / "v14_eye_detail_review_report.md"
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
                    "checks": report["checks"],
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

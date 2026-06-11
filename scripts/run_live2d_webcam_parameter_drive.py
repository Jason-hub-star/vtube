#!/usr/bin/env python3
"""Drive a Live2D Web model with the saved T1 webcam Cubism parameter stream."""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import statistics
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "live2d-strong-model-pattern-001"
REFERENCE_REPORTS = ROOT / "experiments" / "reference-model-structure-001" / "reports"
DEFAULT_STREAM = REFERENCE_REPORTS / "face_tracking_webcam_probe_raw.json"
DEFAULT_SANDBOX_REPORT = EXPERIMENT / "reports" / "strong20_runtime_probe_sandbox.json"
DEFAULT_OUT = EXPERIMENT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stream", type=Path, default=DEFAULT_STREAM)
    parser.add_argument("--sandbox-report", type=Path, default=DEFAULT_SANDBOX_REPORT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--port", type=int, default=5144)
    parser.add_argument("--model-index", type=int, default=0)
    parser.add_argument("--sample-count", type=int, default=12)
    parser.add_argument("--diff-threshold", type=int, default=18)
    parser.add_argument("--skip-npm-install", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path | str | None) -> str | None:
    if path is None:
        return None
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return p.resolve().as_posix()


def wait_for_server(host: str, port: int, timeout: float = 45.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"server did not start on {host}:{port}")


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def choose_frames(stream: dict[str, Any], sample_count: int) -> list[dict[str, Any]]:
    frames = [frame for frame in stream.get("frames", []) if frame.get("face_present") and frame.get("outputs")]
    if not frames:
        return []
    if len(frames) <= sample_count:
        return frames
    selected = []
    for i in range(sample_count):
        idx = round(i * (len(frames) - 1) / max(sample_count - 1, 1))
        selected.append(frames[idx])
    return selected


def build_playwright_spec(
    path: Path,
    stream_path: Path,
    frames_path: Path,
    out_dir: Path,
    base_url: str,
    model_index: int,
) -> None:
    spec = f"""
const fs = require('fs');
const path = require('path');
const {{ test, expect }} = require('@playwright/test');

const streamPath = {json.dumps(str(stream_path))};
const framesPath = {json.dumps(str(frames_path))};
const outDir = {json.dumps(str(out_dir))};
const baseUrl = {json.dumps(base_url)};
const modelIndex = {model_index};

test.setTimeout(240000);

test('drive Live2D model with saved webcam parameter stream', async ({{ page }}) => {{
  await page.setViewportSize({{ width: 1440, height: 1000 }});
  await page.goto(baseUrl, {{ waitUntil: 'domcontentloaded' }});
  await page.waitForFunction(() => window.__vtubeProbe, null, {{ timeout: 20000 }});
  let ready = await page.evaluate(() => window.__vtubeProbe.waitReady(20000));
  expect(ready).toBeTruthy();
  await page.evaluate((index) => window.__vtubeProbe.switchModel(index), modelIndex);
  ready = await page.evaluate(() => window.__vtubeProbe.waitReady(20000));
  expect(ready).toBeTruthy();
  const captureDir = path.join(outDir, 'webcam_parameter_drive');
  fs.mkdirSync(captureDir, {{ recursive: true }});

  const modelName = await page.evaluate(() => window.__vtubeProbe.currentModelName());
  const params = await page.evaluate(() => window.__vtubeProbe.parameters());
  const paramIds = new Set(params.map((p) => p.id));
  const defaultValues = Object.fromEntries(params.map((p) => [p.id, p.defaultValue]));
  await page.evaluate((values) => window.__vtubeProbe.setParameterValues(values), defaultValues);
  await page.waitForTimeout(650);
  const neutralPath = path.join(captureDir, 'neutral.png');
  await page.screenshot({{ path: neutralPath, fullPage: false }});

  const frames = JSON.parse(fs.readFileSync(framesPath, 'utf8'));
  const rows = [];

  for (let i = 0; i < frames.length; i++) {{
    const frame = frames[i];
    const outputs = frame.outputs || {{}};
    const filtered = Object.fromEntries(Object.entries(outputs).filter(([key]) => paramIds.has(key)));
    const applied = await page.evaluate((values) => window.__vtubeProbe.setParameterValues(values), filtered);
    await page.waitForTimeout(140);
    const shotPath = path.join(captureDir, `frame_${{String(i).padStart(2, '0')}}_${{Math.round(frame.t_ms || 0)}}ms.png`);
    await page.screenshot({{ path: shotPath, fullPage: false }});
    rows.push({{
      index: i,
      t_ms: frame.t_ms,
      input_output_count: Object.keys(outputs).length,
      matched_output_count: Object.keys(filtered).length,
      applied_count: applied ? applied.applied.length : 0,
      missing: applied ? applied.missing : [],
      outputs: filtered,
      screenshot_path: shotPath,
    }});
  }}

  const reportPath = path.join(outDir, 'reports', 'webcam_parameter_drive_playwright_raw.json');
  fs.mkdirSync(path.dirname(reportPath), {{ recursive: true }});
  fs.writeFileSync(reportPath, JSON.stringify({{
    generated_at: new Date().toISOString(),
    stream_path: streamPath,
    model_index: modelIndex,
    model_name: modelName,
    neutral_path: neutralPath,
    rows,
  }}, null, 2) + '\\n');
}});
"""
    path.write_text(spec, encoding="utf-8")


def image_diff_metrics(base_path: Path, target_path: Path, threshold: int) -> dict[str, Any]:
    with Image.open(base_path) as base_raw, Image.open(target_path) as target_raw:
        base = base_raw.convert("RGBA")
        target = target_raw.convert("RGBA")
        if base.size != target.size:
            target = target.resize(base.size)
        diff = ImageChops.difference(base, target)
        gray = diff.convert("L")
        width, height = gray.size
        hist = gray.histogram()
        changed = sum(hist[threshold:])
        total_delta = sum(level * count for level, count in enumerate(hist))
        max_delta = max((level for level, count in enumerate(hist) if count), default=0)
        pixel_count = width * height
        mask = gray.point(lambda px: 255 if px >= threshold else 0)
        bbox_raw = mask.getbbox()
        bbox = None
        if bbox_raw:
            x0, y0, x1, y1 = bbox_raw
            bbox = {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0}
        return {
            "image_size": [width, height],
            "changed_pixels": changed,
            "changed_ratio": round(changed / pixel_count, 6),
            "mean_delta": round(total_delta / pixel_count, 6),
            "max_delta": int(max_delta),
            "changed_bbox": bbox,
        }


def numeric_summary(values: list[float]) -> dict[str, Any]:
    clean = [float(v) for v in values if isinstance(v, (int, float))]
    if not clean:
        return {"count": 0}
    return {
        "count": len(clean),
        "min": round(min(clean), 6),
        "median": round(statistics.median(clean), 6),
        "max": round(max(clean), 6),
        "mean": round(statistics.fmean(clean), 6),
    }


def build_contact_sheet(image_paths: list[Path], labels: list[str], out_path: Path) -> None:
    thumbs: list[Image.Image] = []
    tile_w, tile_h = 360, 250
    label_h = 28
    for image_path, label in zip(image_paths, labels):
        with Image.open(image_path) as raw:
            image = raw.convert("RGB")
        image.thumbnail((tile_w, tile_h - label_h))
        canvas = Image.new("RGB", (tile_w, tile_h), "white")
        x = (tile_w - image.width) // 2
        canvas.paste(image, (x, label_h))
        draw = ImageDraw.Draw(canvas)
        try:
            font = ImageFont.truetype("Arial.ttf", 14)
        except OSError:
            font = ImageFont.load_default()
        draw.text((10, 7), label[:44], fill=(30, 41, 59), font=font)
        thumbs.append(canvas)
    cols = 4
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tile_w, rows * tile_h), (244, 246, 248))
    for idx, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((idx % cols) * tile_w, (idx // cols) * tile_h))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def postprocess(raw_path: Path, out_dir: Path, stream_path: Path, threshold: int) -> dict[str, Any]:
    raw = load_json(raw_path)
    neutral = Path(raw["neutral_path"])
    rows = []
    ratios = []
    applied_counts = []
    capture_paths = [neutral]
    labels = ["neutral"]
    for row in raw.get("rows", []):
        shot = Path(row["screenshot_path"])
        metrics = image_diff_metrics(neutral, shot, threshold)
        ratios.append(metrics["changed_ratio"])
        applied_counts.append(row.get("applied_count", 0))
        rows.append({**row, "screenshot_path": rel(shot), **metrics})
        capture_paths.append(shot)
        labels.append(f"{row['index']:02d} {row.get('t_ms', 0)}ms r={metrics['changed_ratio']}")

    contact_sheet = out_dir / "reports" / "webcam_parameter_drive_contact_sheet.png"
    build_contact_sheet(capture_paths, labels, contact_sheet)
    pass_condition = (
        len(rows) >= 8
        and min(applied_counts or [0]) >= 6
        and max(ratios or [0.0]) >= 0.001
        and numeric_summary(ratios).get("median", 0.0) >= 0.0002
    )
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "kind": "live2d_webcam_parameter_drive",
        "status": "PASS" if pass_condition else "FAIL",
        "method": "saved T1 webcam Cubism parameter frames applied to a real Live2D Web runtime model through __vtubeProbe.setParameterValues",
        "stream_path": rel(stream_path),
        "model_index": raw.get("model_index"),
        "model_name": raw.get("model_name"),
        "neutral_path": rel(neutral),
        "contact_sheet": rel(contact_sheet),
        "diff_threshold_luma": threshold,
        "summary": {
            "sample_count": len(rows),
            "applied_count": numeric_summary(applied_counts),
            "changed_ratio": numeric_summary(ratios),
            "max_changed_ratio": max(ratios or [0.0]),
        },
        "interpretation": {
            "ko": (
                "T1 웹캠 파라미터 스트림이 실제 Live2D Web runtime 모델의 렌더를 움직였습니다."
                if pass_condition
                else "T1 웹캠 파라미터 스트림 주입은 실행됐지만, 렌더 변화량 또는 적용 파라미터 수가 기준보다 부족합니다."
            ),
            "next": (
                "다음은 같은 스트림을 새 v2 rig preview 또는 Cubism-authored export에 연결해 G3 motion_visual을 검증하는 단계입니다."
                if pass_condition
                else "모델이 해당 표준 파라미터를 충분히 갖는지 확인하거나 다른 strong20 모델로 다시 실행하세요."
            ),
        },
        "rows": rows,
    }
    out_json = out_dir / "reports" / "webcam_parameter_drive_report.json"
    out_md = out_dir / "reports" / "webcam_parameter_drive_report.md"
    write_json(out_json, report)
    write_md(out_md, report)
    return report


def write_md(path: Path, report: dict[str, Any]) -> None:
    summary = report["summary"]
    lines = [
        "# Live2D Webcam Parameter Drive Report",
        "",
        f"- status: `{report['status']}`",
        f"- model: `{report['model_name']}`",
        f"- method: {report['method']}",
        f"- stream: `{report['stream_path']}`",
        f"- samples: `{summary['sample_count']}`",
        f"- changed_ratio median: `{summary['changed_ratio'].get('median')}`",
        f"- changed_ratio max: `{summary['changed_ratio'].get('max')}`",
        f"- applied_count min/median: `{summary['applied_count'].get('min')}` / `{summary['applied_count'].get('median')}`",
        f"- contact_sheet: `{report['contact_sheet']}`",
        "",
        "## Interpretation",
        "",
        f"- {report['interpretation']['ko']}",
        f"- next: {report['interpretation']['next']}",
        "",
        "## Frames",
        "",
        "| Frame | t_ms | Applied | Changed Ratio | Mean Delta | Screenshot |",
        "|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["rows"]:
        lines.append(
            f"| {row['index']} | {row.get('t_ms')} | {row.get('applied_count')} | {row.get('changed_ratio')} | "
            f"{row.get('mean_delta')} | `{row.get('screenshot_path')}` |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    stream = load_json(args.stream)
    frames = choose_frames(stream, args.sample_count)
    if not frames:
        raise SystemExit(f"no usable frames in stream: {args.stream}")

    sandbox = load_json(args.sandbox_report)
    demo_dir = ROOT / sandbox["demo_dir"]
    reports_dir = args.out_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    frames_path = reports_dir / "webcam_parameter_drive_selected_frames.json"
    raw_path = reports_dir / "webcam_parameter_drive_playwright_raw.json"
    spec_path = demo_dir / "webcam_parameter_drive.spec.cjs"
    if raw_path.exists():
        raw_path.unlink()
    write_json(frames_path, frames)
    build_playwright_spec(
        spec_path,
        args.stream.resolve(),
        frames_path.resolve(),
        args.out_dir.resolve(),
        f"http://127.0.0.1:{args.port}/?webcam_parameter_drive=1",
        args.model_index,
    )

    if not args.skip_npm_install and not (demo_dir / "node_modules" / "vite").exists():
        subprocess.run(["npm", "install"], cwd=demo_dir, check=True)
    if not args.skip_npm_install and not (demo_dir / "node_modules" / "@playwright" / "test").exists():
        subprocess.run(["npm", "install", "--no-save", "@playwright/test@1.60.0"], cwd=demo_dir, check=True)

    server = subprocess.Popen(
        ["npm", "run", "start", "--", "--host", "127.0.0.1", "--port", str(args.port)],
        cwd=demo_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_for_server("127.0.0.1", args.port)
        env = os.environ.copy()
        env["PLAYWRIGHT_HTML_OPEN"] = "never"
        subprocess.run(
            ["npx", "playwright", "test", str(spec_path), "--reporter=line"],
            cwd=demo_dir,
            env=env,
            check=True,
        )
        report = postprocess(raw_path, args.out_dir, args.stream, args.diff_threshold)
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "model": report["model_name"],
                    "summary": report["summary"],
                    "report": rel(args.out_dir / "reports" / "webcam_parameter_drive_report.json"),
                    "contact_sheet": report["contact_sheet"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0 if report["status"] == "PASS" else 1
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    raise SystemExit(main())

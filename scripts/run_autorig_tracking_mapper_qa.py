#!/usr/bin/env python3
"""AUTORIG Tracking-to-Rig Mapper QA: replay tracking streams into Mini Cubism."""
from __future__ import annotations
import argparse
import csv
import json
import math
import shutil
import socket
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any
from PIL import Image, ImageChops, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, load_json, now_iso, rel, write_json  # noqa: E402
from lib.vtube_proc import terminate, wait_for_server  # noqa: E402
DEFAULT_STREAM = ROOT / "experiments/reference-model-structure-001/reports/face_tracking_webcam_probe_raw.json"
PLAYWRIGHT = ROOT / "experiments/live2d-strong-model-pattern-001/probe_sandbox/strong20/Samples/TypeScript/Demo/node_modules/playwright"
REQUIRED = ["ParamAngleX", "ParamAngleY", "ParamAngleZ", "ParamEyeLOpen", "ParamEyeROpen", "ParamEyeBallX", "ParamEyeBallY", "ParamMouthOpenY", "ParamMouthForm"]
KNOWN_OPTIONAL_MISSING = {"ParamBodyTrackX", "ParamBodyTrackZ", "ParamHairFront", "ParamHairBack", "ParamBrowLY", "ParamBrowRY", "ParamEyeSmile"}
NODE = r"""
const fs = require("fs");
const config = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const { chromium } = require(config.playwright);
(async () => {
  const browser = await chromium.launch({ headless: true, args: config.launch_args || [] });
  const page = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
  const out = { generated_at: new Date().toISOString(), renderer_requested: config.renderer, renderer_backend: null, report: null, samples: [], errors: [] };
  try {
    await page.goto(config.url, { waitUntil: "load", timeout: 30000 });
    await page.waitForFunction(() => window.__driveReport && window.__driveReport.frames_applied > 0, null, { timeout: 40000 });
    for (const sample of config.samples) {
      await page.waitForFunction((minFrames) => window.__driveReport.frames_applied >= minFrames || window.__driveReport.done, sample.min_frames, { timeout: sample.timeout_ms || 60000 });
      const path = `${config.captures_dir}/${sample.name}.png`;
      await page.screenshot({ path });
      out.samples.push(await page.evaluate((payload) => ({
        name: payload.name,
        screenshot: payload.path,
        drive_report: { ...window.__driveReport },
        canvas_hash: document.querySelector("#model")?.contentWindow?.__miniProbe?.canvasHash?.() ?? null,
        backend: document.querySelector("#model")?.contentWindow?.__miniBackend?.() ?? null,
      }), { name: sample.name, path }));
    }
    await page.waitForFunction(() => window.__driveReport.done === true, null, { timeout: config.done_timeout_ms || 120000 });
    out.report = await page.evaluate(() => ({ ...window.__driveReport }));
    out.renderer_backend = await page.evaluate(() => document.querySelector("#model")?.contentWindow?.__miniBackend?.() ?? null);
  } catch (error) {
    out.errors.push(String(error && error.stack ? error.stack : error));
  } finally {
    await browser.close();
    fs.writeFileSync(config.out, JSON.stringify(out, null, 2));
  }
})();
"""
def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])
def node_bin() -> str:
    found = shutil.which("node")
    if not found:
        raise RuntimeError("node binary not found")
    return found
def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or (list(rows[0].keys()) if rows else ["empty"])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    return values[min(len(values) - 1, max(0, int(round((len(values) - 1) * q))))]
def project_ranges(character: dict[str, Any]) -> dict[str, tuple[float, float]]:
    return {p["id"]: (float(p.get("min", -math.inf)), float(p.get("max", math.inf))) for p in character.get("parameters", [])}
def output_frames(stream: dict[str, Any]) -> list[dict[str, Any]]:
    return [f for f in stream.get("frames", []) if f.get("face_present") and isinstance(f.get("outputs"), dict)]
def sampled_stream(stream: dict[str, Any], count: int | None) -> dict[str, Any]:
    frames = output_frames(stream)
    if not count or len(frames) <= count:
        return stream
    # Jitter is a frame-to-frame metric; keep a contiguous prefix for smoke runs
    # instead of sparse sampling that fabricates large deltas between distant frames.
    selected = frames[:count]
    first_t = selected[0].get("t_ms", 0)
    normalized = [{**f, "t_ms": int(f.get("t_ms", 0) - first_t)} for f in selected]
    return {**stream, "frames": normalized, "duration_ms": normalized[-1]["t_ms"] if normalized else 0}
def parameter_rows(frames: list[dict[str, Any]], ranges: dict[str, tuple[float, float]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    response, by_param = [], {p: [] for p in sorted({k for f in frames for k in f.get("outputs", {})})}
    for i, frame in enumerate(frames):
        outputs = frame.get("outputs", {})
        row = {"frame": i, "t_ms": frame.get("t_ms"), "face_present": frame.get("face_present")}
        for param, value in outputs.items():
            if isinstance(value, (int, float)) and math.isfinite(value):
                by_param.setdefault(param, []).append(float(value))
            row[param] = value
        response.append(row)
    range_rows = []
    for param, values in sorted(by_param.items()):
        lo, hi = ranges.get(param, (None, None))
        violations = 0
        if lo is not None and hi is not None:
            violations = sum(1 for v in values if v < lo - 1e-6 or v > hi + 1e-6)
        range_rows.append({"parameter": param, "present": int(bool(values)), "project_has_parameter": int(param in ranges), "min": round(min(values), 6) if values else "", "max": round(max(values), 6) if values else "", "span": round(max(values) - min(values), 6) if values else 0, "rig_min": lo if lo is not None else "", "rig_max": hi if hi is not None else "", "range_violations": violations})
    return response, range_rows
def jitter_rows(frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deltas: dict[str, list[float]] = {}
    totals = []
    for prev, cur in zip(frames, frames[1:]):
        row_total = 0.0
        for param, value in cur.get("outputs", {}).items():
            old = prev.get("outputs", {}).get(param)
            if isinstance(value, (int, float)) and isinstance(old, (int, float)):
                d = abs(float(value) - float(old))
                deltas.setdefault(param, []).append(d)
                if param in REQUIRED:
                    row_total += d
        totals.append(row_total)
    low_cut = percentile(totals, 0.35) if totals else 0
    rows = []
    for param, values in sorted(deltas.items()):
        low_values = [v for v, total in zip(values, totals) if total <= low_cut] or values
        rows.append({"parameter": param, "median_delta": round(statistics.median(values), 6), "p95_delta": round(percentile(values, 0.95), 6), "low_motion_p95_delta": round(percentile(low_values, 0.95), 6), "sample_count": len(values)})
    return rows
def image_diff(a: Path, b: Path) -> float:
    with Image.open(a).convert("RGB") as left, Image.open(b).convert("RGB") as right:
        if left.size != right.size:
            right = right.resize(left.size)
        gray = ImageChops.difference(left, right).convert("L")
        hist = gray.histogram()
        return round(sum(hist[18:]) / (gray.width * gray.height), 6)
def font(size: int) -> ImageFont.ImageFont:
    for path in ["/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()
def build_contact_sheet(paths: list[Path], out: Path) -> None:
    images = []
    for path in paths:
        image = Image.open(path).convert("RGB")
        image.thumbnail((420, 280), Image.Resampling.LANCZOS)
        images.append((path.stem, image.copy()))
    width, height = 420 * max(1, len(images)), 340
    sheet = Image.new("RGB", (width, height), "#f2f4f6")
    draw = ImageDraw.Draw(sheet)
    for i, (label, image) in enumerate(images):
        x = i * 420
        sheet.paste(image, (x + (420 - image.width) // 2, 20))
        draw.text((x + 16, 300), label, fill="#191f28", font=font(16))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
def build_gif(paths: list[Path], out: Path) -> None:
    frames = []
    for path in paths:
        image = Image.open(path).convert("RGB")
        image.thumbnail((520, 360), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (520, 360), "#202124")
        canvas.paste(image, ((520 - image.width) // 2, (360 - image.height) // 2))
        frames.append(canvas)
    if frames:
        out.parent.mkdir(parents=True, exist_ok=True)
        frames[0].save(out, save_all=True, append_images=frames[1:], duration=450, loop=0)
def run_replay(project: Path, stream: Path, out: Path, renderer: str, port: int, quick: bool) -> dict[str, Any]:
    captures = out / "captures"
    captures.mkdir(parents=True, exist_ok=True)
    raw = out / "playwright_raw.json"
    config = out / "playwright_config.json"
    runner = out / "tracking_mapper_runner.js"
    samples = [{"name": "early", "min_frames": 1, "timeout_ms": 40000}, {"name": "mid", "min_frames": 12 if quick else 60, "timeout_ms": 80000}, {"name": "done", "min_frames": 24 if quick else 120, "timeout_ms": 140000}]
    write_json(config, {"playwright": str(PLAYWRIGHT), "url": f"http://127.0.0.1:{port}/drive?replay=1&auto=1&speed={16 if quick else 8}", "captures_dir": str(captures), "out": str(raw), "renderer": renderer, "launch_args": ["--use-angle=swiftshader"] if renderer == "pixi" else [], "samples": samples})
    runner.write_text(NODE, encoding="utf-8")
    server = subprocess.Popen(["python3", str(ROOT / "scripts/run_mini_cubism_webcam_drive.py"), "--project", str(project), "--stream", str(stream), "--renderer", renderer, "--port", str(port), "--no-open"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        wait_for_server("127.0.0.1", port, timeout=30)
        result = subprocess.run([node_bin(), str(runner), str(config)], cwd=ROOT, capture_output=True, text=True, timeout=240 if quick else 420, check=False)
        if result.returncode != 0 and not raw.exists():
            write_json(raw, {"errors": [result.stderr[-2000:] or result.stdout[-2000:] or "playwright failed"]})
    finally:
        terminate(server)
    return load_json(raw, default={"errors": ["missing playwright raw"]})
def checks(frames: list[dict[str, Any]], range_rows: list[dict[str, Any]], jitter: list[dict[str, Any]], raw: dict[str, Any], quick: bool, distinct_visual: int) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    params = {r["parameter"]: r for r in range_rows}
    missing_required = [p for p in REQUIRED if not params.get(p, {}).get("present")]
    range_violations = sum(int(r["range_violations"]) for r in range_rows if r["project_has_parameter"])
    missing_project = [r["parameter"] for r in range_rows if not r["project_has_parameter"] and r["parameter"] not in KNOWN_OPTIONAL_MISSING]
    report = raw.get("report") or {}
    applied = report.get("applied_counts") or []
    median_applied = statistics.median(applied) if applied else 0
    missing_union = [p for p in report.get("missing_union", []) if p not in KNOWN_OPTIONAL_MISSING]
    spans = {p: float(params.get(p, {}).get("span") or 0) for p in REQUIRED}
    eye_span = max(spans.get("ParamEyeLOpen", 0), spans.get("ParamEyeROpen", 0))
    jitter_fail = []
    for row in jitter:
        limit = 4.0 if row["parameter"] in {"ParamAngleX", "ParamAngleY", "ParamAngleZ"} else 0.12
        if row["parameter"] in REQUIRED and float(row["low_motion_p95_delta"]) > limit:
            jitter_fail.append(row["parameter"])
    checks_out = [
        {"check": "stream_schema", "status": "PASS" if len(frames) >= (12 if quick else 30) and not missing_required else "FAIL", "value": len(frames), "missing_required": missing_required},
        {"check": "mapping_range", "status": "PASS" if range_violations == 0 and not missing_project else "FAIL", "value": range_violations, "missing_project": missing_project},
        {"check": "runtime_injection", "status": "PASS" if report.get("done") and report.get("frames_applied", 0) >= (24 if quick else 120) and median_applied >= 6 and not missing_union else "FAIL", "value": report.get("frames_applied", 0), "applied_median": median_applied, "missing_union": missing_union},
        {"check": "response_realism", "status": "PASS" if spans.get("ParamAngleX", 0) >= 8 and spans.get("ParamMouthOpenY", 0) >= 0.25 and eye_span >= 0.15 else "FAIL", "value": round(spans.get("ParamAngleX", 0), 4), "spans": spans},
        {"check": "jitter", "status": "PASS" if not jitter_fail else "FAIL", "value": len(jitter_fail), "failed_parameters": jitter_fail},
        {"check": "render_evidence", "status": "PASS" if distinct_visual >= 2 and not raw.get("errors") else "FAIL", "value": distinct_visual, "errors": raw.get("errors", [])},
    ]
    status = "PASS" if all(c["status"] == "PASS" for c in checks_out) else "FAIL"
    scores = {"frame_count": len(frames), "runtime_frames_applied": report.get("frames_applied", 0), "applied_median": median_applied, "distinct_visual_states": distinct_visual, "ParamAngleX_span": spans.get("ParamAngleX", 0), "ParamMouthOpenY_span": spans.get("ParamMouthOpenY", 0), "eye_open_span": eye_span}
    return status, checks_out, scores
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--stream", type=Path, default=DEFAULT_STREAM)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--renderer", choices=["pixi", "canvas"], default="pixi")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--sample-count", type=int, default=None)
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    project = args.project if args.project.is_absolute() else ROOT / args.project
    stream_path = args.stream if args.stream.is_absolute() else ROOT / args.stream
    out = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    character = load_json(project / "character.json")
    stream = sampled_stream(load_json(stream_path), args.sample_count or (48 if args.quick else None))
    qa_stream = out / "qa_replay_stream.json"
    write_json(qa_stream, stream)
    frames = output_frames(stream)
    response, ranges = parameter_rows(frames, project_ranges(character))
    jitter = jitter_rows(frames)
    write_csv(out / "parameter_response.csv", response)
    write_csv(out / "parameter_range_report.csv", ranges)
    write_csv(out / "jitter_score.csv", jitter)
    raw = run_replay(project.resolve(), qa_stream, out, args.renderer, args.port or free_port(), args.quick)
    captures = [Path(s["screenshot"]) for s in raw.get("samples", []) if s.get("screenshot") and Path(s["screenshot"]).exists()]
    if captures:
        build_contact_sheet(captures, out / "tracking_replay_contact_sheet.png")
        build_gif(captures, out / "tracking_replay.gif")
    diffs = [image_diff(captures[0], p) for p in captures[1:]] if len(captures) > 1 else []
    hashes = {s.get("canvas_hash") for s in raw.get("samples", []) if s.get("canvas_hash") is not None}
    distinct_visual = max(len(hashes), 1 + sum(1 for d in diffs if d > 0.001))
    status, check_rows, scores = checks(frames, ranges, jitter, raw, args.quick, distinct_visual)
    report = {"schema_version": 1, "generated_at": now_iso(), "status": status, "quick": args.quick, "project": rel(project), "stream": rel(stream_path), "renderer_requested": args.renderer, "renderer_backend": raw.get("renderer_backend"), "checks": check_rows, "scores": scores, "outputs": {"parameter_response": rel(out / "parameter_response.csv"), "parameter_range_report": rel(out / "parameter_range_report.csv"), "jitter_score": rel(out / "jitter_score.csv"), "contact_sheet": rel(out / "tracking_replay_contact_sheet.png"), "gif": rel(out / "tracking_replay.gif"), "playwright_raw": rel(out / "playwright_raw.json")}}
    write_json(out / "tracking_mapper_report.json", report)
    lines = ["# AUTORIG Tracking Mapper QA", "", f"Status: **{status}**", f"Project: `{rel(project)}`", f"Stream: `{rel(stream_path)}`", f"Renderer: `{raw.get('renderer_backend')}`", f"Quick: `{args.quick}`", "", "| check | status | value |", "|---|---|---:|"]
    for row in check_rows:
        lines.append(f"| {row['check']} | {row['status']} | {row.get('value', '')} |")
    (out / "tracking_mapper_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "status": status, "out_dir": str(out), "renderer_backend": raw.get("renderer_backend"), "scores": scores, "checks": check_rows}, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 1  # P5 게이트 계약: FAIL이면 비제로 종료
if __name__ == "__main__":
    raise SystemExit(main())

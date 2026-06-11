#!/usr/bin/env python3
"""Capture neutral/motion/extreme screenshots from the generated Live2D probe sandbox."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "live2d-strong-model-pattern-001"
DEFAULT_MANIFEST = EXPERIMENT / "reports" / "pilot_render_manifest.json"
DEFAULT_SANDBOX_REPORT = EXPERIMENT / "reports" / "pilot_runtime_probe_sandbox.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--sandbox-report", type=Path, default=DEFAULT_SANDBOX_REPORT)
    parser.add_argument("--out-dir", type=Path, default=EXPERIMENT)
    parser.add_argument("--port", type=int, default=5077)
    parser.add_argument("--skip-npm-install", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
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


def wait_for_server(url: str, timeout: float = 30.0) -> None:
    started = time.time()
    while time.time() - started < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status < 500:
                    return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError(f"server did not become ready: {url}")


def build_playwright_spec(path: Path, manifest_path: Path, out_dir: Path, base_url: str) -> None:
    spec = f"""
const fs = require('fs');
const path = require('path');
const {{ test }} = require('@playwright/test');

const manifest = JSON.parse(fs.readFileSync({json.dumps(str(manifest_path))}, 'utf8'));
const outDir = {json.dumps(str(out_dir))};
const baseUrl = {json.dumps(base_url)};
const categories = ['eye', 'mouth', 'hair', 'body_angle', 'arm'];

async function waitProbe(page) {{
  await page.waitForFunction(() => window.__vtubeProbe, null, {{ timeout: 15000 }});
}}

async function waitReady(page) {{
  const ready = await page.evaluate(() => window.__vtubeProbe.waitReady(15000));
  if (!ready) throw new Error('probe model did not become ready');
}}

async function capture(page, filePath) {{
  await page.screenshot({{ path: filePath, fullPage: false }});
}}

test('capture Live2D probe evidence', async ({{ page }}) => {{
  test.setTimeout(Math.max(240000, manifest.models.length * 120000 + 120000));
  const report = {{ models: [] }};
  const rawReportPath = path.join(outDir, 'reports', `${{manifest.kind}}_runtime_probe_playwright_raw.json`);
  await page.setViewportSize({{ width: 1280, height: 900 }});
  await page.goto(baseUrl, {{ waitUntil: 'load' }});
  await waitProbe(page);
  const names = await page.evaluate(() => window.__vtubeProbe.modelNames());
  for (let index = 0; index < manifest.models.length; index++) {{
    const model = manifest.models[index];
    const modelDir = path.join(outDir, 'captures', model.safe_id);
    fs.mkdirSync(modelDir, {{ recursive: true }});
    const item = {{
      id: model.id,
      safe_id: model.safe_id,
      name: model.name,
      expected_name: names[index],
      status: 'PASS',
      captures: {{}},
      categories: {{}},
      errors: [],
    }};
    try {{
      await page.evaluate((i) => window.__vtubeProbe.switchModel(i), index);
      await waitReady(page);
      await page.waitForTimeout(700);
      await page.evaluate(() => window.__vtubeProbe.clear());
      const neutral = path.join(modelDir, 'neutral.png');
      await capture(page, neutral);
      item.captures.neutral = neutral;

      const motionGroup = await page.evaluate(() => window.__vtubeProbe.startRepresentativeMotion());
      item.motion_group = motionGroup;
      for (const [label, delay] of [['20', 500], ['50', 1000], ['80', 1500]]) {{
        await page.waitForTimeout(delay);
        const filePath = path.join(modelDir, `motion_${{label}}.png`);
        await capture(page, filePath);
        item.captures[`motion_${{label}}`] = filePath;
      }}

      for (const category of categories) {{
        const categoryFiles = [];
        for (const position of ['min', 'default', 'max']) {{
          const matched = await page.evaluate(([c, p]) => window.__vtubeProbe.setCategory(c, p), [category, position]);
          item.categories[category] = item.categories[category] || {{ matched_parameters: matched }};
          await page.waitForTimeout(350);
          const filePath = path.join(modelDir, `extreme_${{category}}_${{position}}.png`);
          await capture(page, filePath);
          categoryFiles.push(filePath);
        }}
        item.captures[`extreme_${{category}}_frames`] = categoryFiles;
        await page.evaluate(() => window.__vtubeProbe.clear());
      }}
    }} catch (error) {{
      item.status = 'FAIL';
      item.errors.push(String(error));
    }}
    report.models.push(item);
    fs.writeFileSync(rawReportPath, JSON.stringify(report, null, 2));
  }}
  fs.writeFileSync(rawReportPath, JSON.stringify(report, null, 2));
}});
"""
    path.write_text(spec, encoding="utf-8")


def screenshot_is_nonblank(path: Path) -> bool:
    if not path.exists():
        return False
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        extrema = rgb.getextrema()
    return any(lo != hi or hi > 5 for lo, hi in extrema)


def combine_extreme_strips(raw: dict[str, Any]) -> None:
    for model in raw.get("models", []):
        captures = model.get("captures", {})
        for category in ("eye", "mouth", "hair", "body_angle", "arm"):
            frames = [Path(p) for p in captures.get(f"extreme_{category}_frames", [])]
            if len(frames) != 3 or not all(p.exists() for p in frames):
                continue
            images = [Image.open(p).convert("RGB") for p in frames]
            thumbs = []
            for label, image in zip(("min", "default", "max"), images, strict=True):
                image = image.copy()
                image.thumbnail((360, 260), Image.Resampling.LANCZOS)
                tile = Image.new("RGB", (380, 292), (245, 247, 250))
                draw = ImageDraw.Draw(tile)
                draw.text((12, 10), label, fill=(20, 30, 45))
                tile.paste(image, (10, 32))
                thumbs.append(tile)
            strip = Image.new("RGB", (sum(t.width for t in thumbs), max(t.height for t in thumbs)), (245, 247, 250))
            x = 0
            for tile in thumbs:
                strip.paste(tile, (x, 0))
                x += tile.width
            out = frames[0].parent / f"extreme_{category}.png"
            strip.save(out)
            captures[f"extreme_{category}"] = str(out)


def build_contact_sheet(raw: dict[str, Any], out_path: Path) -> None:
    entries = []
    for model in raw.get("models", []):
        neutral = Path(model.get("captures", {}).get("neutral", ""))
        if neutral.exists():
            img = Image.open(neutral).convert("RGB")
            img.thumbnail((260, 190), Image.Resampling.LANCZOS)
        else:
            img = Image.new("RGB", (260, 190), (30, 30, 30))
        entries.append((model.get("name", "unknown"), model.get("status", "FAIL"), img))
    cols = 2
    rows = max(1, (len(entries) + cols - 1) // cols)
    sheet = Image.new("RGB", (cols * 300, rows * 235), (245, 247, 250))
    draw = ImageDraw.Draw(sheet)
    for idx, (name, status, img) in enumerate(entries):
        x = (idx % cols) * 300
        y = (idx // cols) * 235
        draw.text((x + 8, y + 8), f"{name}: {status}", fill=(20, 30, 45))
        sheet.paste(img, (x + 8, y + 34))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def postprocess(manifest: dict[str, Any], raw_path: Path, out_dir: Path) -> dict[str, Any]:
    raw = load_json(raw_path)
    combine_extreme_strips(raw)
    for model in raw.get("models", []):
        captures = model.get("captures", {})
        files = []
        for value in captures.values():
            if isinstance(value, list):
                files.extend(Path(p) for p in value)
            elif isinstance(value, str):
                files.append(Path(value))
        existing = [p for p in files if p.exists()]
        nonblank = [p for p in existing if screenshot_is_nonblank(p)]
        if model.get("status") == "PASS" and (not existing or not nonblank):
            model["status"] = "FAIL"
            model.setdefault("errors", []).append("missing or blank screenshots")
        model["capture_count"] = len(existing)
        model["nonblank_capture_count"] = len(nonblank)
        model["captures"] = {
            key: ([rel(p) for p in value] if isinstance(value, list) else rel(value))
            for key, value in captures.items()
        }
    contact = out_dir / "reports" / f"{manifest['kind']}_contact_sheet.png"
    build_contact_sheet(raw, contact)
    report = {
        "schema_version": 1,
        "kind": manifest["kind"],
        "status": "PASS" if all(m.get("status") == "PASS" for m in raw.get("models", [])) else "FAIL",
        "summary": {
            "model_count": len(raw.get("models", [])),
            "pass_count": sum(1 for m in raw.get("models", []) if m.get("status") == "PASS"),
            "fail_count": sum(1 for m in raw.get("models", []) if m.get("status") != "PASS"),
        },
        "contact_sheet": rel(contact),
        "models": raw.get("models", []),
        "interpretation": [
            "Extreme parameter screenshots show parameter influence range, not natural motion quality.",
            "Official sample screenshots are local evidence only and must not be reused as our model assets.",
        ],
    }
    write_json(out_dir / "reports" / f"{manifest['kind']}_runtime_probe_report.json", report)
    lines = [
        f"# Live2D {manifest['kind']} Runtime Probe Report",
        "",
        f"- status: `{report['status']}`",
        f"- pass/fail: `{report['summary']['pass_count']}/{report['summary']['fail_count']}`",
        f"- contact_sheet: `{report['contact_sheet']}`",
        "",
        "| Model | Status | Captures | Motion group | Errors |",
        "|---|---:|---:|---|---|",
    ]
    for model in report["models"]:
        lines.append(
            f"| `{model.get('name')}` | {model.get('status')} | {model.get('capture_count', 0)} | "
            f"`{model.get('motion_group')}` | {'; '.join(model.get('errors', []))} |"
        )
    (out_dir / "reports" / f"{manifest['kind']}_runtime_probe_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main() -> int:
    args = parse_args()
    manifest = load_json(args.manifest)
    sandbox = load_json(args.sandbox_report)
    demo_dir = ROOT / sandbox["demo_dir"]
    out_dir = args.out_dir
    reports_dir = out_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_npm_install and not (demo_dir / "node_modules" / "vite").exists():
        subprocess.run(["npm", "install"], cwd=demo_dir, check=True)
    if not args.skip_npm_install and not (demo_dir / "node_modules" / "@playwright" / "test").exists():
        subprocess.run(["npm", "install", "--no-save", "@playwright/test@1.60.0"], cwd=demo_dir, check=True)

    spec_path = demo_dir / f"{manifest['kind']}_runtime_probe.spec.cjs"
    base_url = f"http://127.0.0.1:{args.port}/?probe={manifest['kind']}"
    build_playwright_spec(spec_path, args.manifest.resolve(), out_dir.resolve(), base_url)

    server = subprocess.Popen(
        ["npm", "run", "start", "--", "--host", "127.0.0.1", "--port", str(args.port)],
        cwd=demo_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_for_server(f"http://127.0.0.1:{args.port}/")
        raw_path = reports_dir / f"{manifest['kind']}_runtime_probe_playwright_raw.json"
        if raw_path.exists():
            raw_path.unlink()
        env = os.environ.copy()
        env["PLAYWRIGHT_HTML_OPEN"] = "never"
        subprocess.run(
            ["npx", "playwright", "test", str(spec_path), "--reporter=line"],
            cwd=demo_dir,
            env=env,
            check=True,
        )
        report = postprocess(manifest, raw_path, out_dir)
        print(json.dumps({
            "status": report["status"],
            "summary": report["summary"],
            "contact_sheet": report["contact_sheet"],
        }, ensure_ascii=False, indent=2))
        return 0 if report["status"] == "PASS" else 1
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    raise SystemExit(main())

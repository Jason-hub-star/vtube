#!/usr/bin/env python3
"""Run all57 Live2D representative-motion playback QA and build a matrix report."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageStat


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "live2d-strong-model-pattern-001"
DEFAULT_MANIFEST = EXPERIMENT / "reports" / "all57_render_manifest.json"
DEFAULT_SANDBOX = EXPERIMENT / "reports" / "all57_runtime_probe_sandbox.json"
DEFAULT_MANUAL = EXPERIMENT / "reports" / "all57_manual_operator_observations_20260608.json"
PLAYWRIGHT_MODULE = (
    EXPERIMENT
    / "probe_sandbox"
    / "strong20"
    / "Samples"
    / "TypeScript"
    / "Demo"
    / "node_modules"
    / "playwright"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--sandbox-report", type=Path, default=DEFAULT_SANDBOX)
    parser.add_argument("--manual-observations", type=Path, default=DEFAULT_MANUAL)
    parser.add_argument("--out-dir", type=Path, default=EXPERIMENT)
    parser.add_argument("--port", type=int, default=5130)
    parser.add_argument("--skip-npm-install", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="Debug limit; 0 means all entries.")
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


def wait_for_server(url: str, timeout: float = 45.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status < 500:
                    return
        except Exception:
            time.sleep(0.4)
    raise RuntimeError(f"server did not become ready: {url}")


def build_runtime_index(sandbox: dict[str, Any]) -> dict[str, int]:
    return {safe_id: idx for idx, safe_id in enumerate(sandbox.get("model_ids", []))}


def load_manual(path: Path) -> dict[int, dict[str, Any]]:
    if not path.exists():
        return {}
    data = load_json(path)
    return {int(item["rank"]): item for item in data.get("observations", []) if item.get("rank") is not None}


def build_playwright_script(
    script_path: Path,
    manifest_path: Path,
    runtime_index: dict[str, int],
    out_dir: Path,
    base_url: str,
    limit: int,
) -> None:
    js = f"""
const fs = require('fs');
const path = require('path');
const {{ chromium }} = require({json.dumps(str(PLAYWRIGHT_MODULE))});

const manifest = JSON.parse(fs.readFileSync({json.dumps(str(manifest_path))}, 'utf8'));
const runtimeIndex = {json.dumps(runtime_index)};
const outDir = {json.dumps(str(out_dir))};
const baseUrl = {json.dumps(base_url)};
const limit = {limit};

async function waitProbe(page) {{
  await page.waitForFunction(() => window.__vtubeProbe, null, {{ timeout: 30000 }});
}}

async function waitReady(page) {{
  const ready = await page.evaluate(() => window.__vtubeProbe.waitReady(20000));
  if (!ready) throw new Error('probe model did not become ready');
}}

async function screenshot(page, filePath) {{
  await page.screenshot({{ path: filePath, fullPage: false }});
}}

(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage({{ viewport: {{ width: 1280, height: 900 }} }});
  await page.goto(baseUrl, {{ waitUntil: 'load', timeout: 45000 }});
  await waitProbe(page);

  const models = limit > 0 ? manifest.models.slice(0, limit) : manifest.models;
  const report = {{ models: [] }};
  const rawPath = path.join(outDir, 'reports', 'all57_motion_playback_qa_raw.json');

  for (const model of models) {{
    const item = {{
      rank: model.rank,
      id: model.id,
      safe_id: model.safe_id,
      name: model.name,
      manifest_status: model.manifest_status,
      runtime_index: runtimeIndex[model.safe_id],
      status: 'PENDING',
      motion_group: null,
      captures: {{}},
      errors: [],
    }};

    if (model.manifest_status !== 'PASS' || item.runtime_index === undefined) {{
      item.status = 'NO_RUNTIME';
      item.errors.push((model.missing_required_paths || []).join(',') || 'runtime model not present in sandbox');
      report.models.push(item);
      fs.writeFileSync(rawPath, JSON.stringify(report, null, 2));
      continue;
    }}

    const modelDir = path.join(outDir, 'all57_motion_qa', model.safe_id);
    fs.mkdirSync(modelDir, {{ recursive: true }});

    try {{
      await page.evaluate((idx) => window.__vtubeProbe.switchModel(idx), item.runtime_index);
      await waitReady(page);
      await page.waitForTimeout(700);
      await page.evaluate(() => window.__vtubeProbe.clear());
      await page.waitForTimeout(350);
      const neutral = path.join(modelDir, 'neutral.png');
      await screenshot(page, neutral);
      item.captures.neutral = neutral;

      item.motion_group = await page.evaluate(() => window.__vtubeProbe.startRepresentativeMotion());
      for (const [label, waitMs] of [['motion_20', 450], ['motion_50', 900], ['motion_80', 1300]]) {{
        await page.waitForTimeout(waitMs);
        const filePath = path.join(modelDir, `${{label}}.png`);
        await screenshot(page, filePath);
        item.captures[label] = filePath;
      }}
      item.status = item.motion_group ? 'MOTION_CAPTURED' : 'NO_MOTION_GROUP';
    }} catch (error) {{
      item.status = 'FAIL_CAPTURE';
      item.errors.push(String(error));
    }}
    report.models.push(item);
    fs.writeFileSync(rawPath, JSON.stringify(report, null, 2));
  }}

  await browser.close();
  fs.writeFileSync(rawPath, JSON.stringify(report, null, 2));
}})().catch(error => {{
  console.error(error);
  process.exit(1);
}});
"""
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(js, encoding="utf-8")


def diff_metrics(a: Path, b: Path) -> dict[str, Any]:
    if not a.exists() or not b.exists():
        return {"present": False}
    with Image.open(a).convert("RGB") as img_a, Image.open(b).convert("RGB") as img_b:
        if img_a.size != img_b.size:
            img_b = img_b.resize(img_a.size)
        diff = ImageChops.difference(img_a, img_b)
        gray = diff.convert("L")
        bbox = gray.getbbox()
        stat = ImageStat.Stat(gray)
        mean_diff = float(stat.mean[0])
        threshold = 8
        histogram = gray.histogram()
        changed = sum(histogram[threshold + 1 :])
        total = img_a.size[0] * img_a.size[1]
    return {
        "present": True,
        "mean_diff": round(mean_diff, 4),
        "changed_ratio": round(changed / total, 6) if total else 0,
        "bbox": list(bbox) if bbox else None,
    }


def classify_motion(row: dict[str, Any]) -> str:
    if row["status"] == "NO_RUNTIME":
        return "NO_RUNTIME"
    if row["status"] == "FAIL_CAPTURE":
        return "FAIL_CAPTURE"
    if not row.get("motion_group"):
        return "NO_MOTION_GROUP"
    max_ratio = max((m.get("changed_ratio", 0) for m in row.get("motion_diffs", {}).values()), default=0)
    if max_ratio >= 0.02:
        return "MOTION_STRONG"
    if max_ratio >= 0.004:
        return "MOTION_VISIBLE"
    if max_ratio >= 0.0005:
        return "MOTION_SUBTLE_OR_EYE_ONLY"
    return "MOTION_STATIC"


def postprocess(raw_path: Path, manifest: dict[str, Any], manual: dict[int, dict[str, Any]], out_dir: Path) -> dict[str, Any]:
    raw = load_json(raw_path)
    rows = []
    for item in raw.get("models", []):
        captures = {key: Path(value) for key, value in item.get("captures", {}).items() if isinstance(value, str)}
        diffs = {}
        if "neutral" in captures:
            for key in ("motion_20", "motion_50", "motion_80"):
                if key in captures:
                    diffs[key] = diff_metrics(captures["neutral"], captures[key])
        item["motion_diffs"] = diffs
        item["captures"] = {key: rel(path) for key, path in captures.items()}
        item["qa_class"] = classify_motion(item)
        observed = manual.get(int(item.get("rank") or 0))
        if observed:
            item["manual_observation"] = {
                "manual_status": observed.get("manual_status"),
                "note_ko": observed.get("note_ko"),
            }
        rows.append(item)

    class_counts = {}
    for row in rows:
        class_counts[row["qa_class"]] = class_counts.get(row["qa_class"], 0) + 1
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "kind": "all57_motion_playback_qa_matrix",
        "status": "PASS" if rows else "FAIL",
        "inputs": {
            "manifest": rel(DEFAULT_MANIFEST),
            "manual_observations": rel(DEFAULT_MANUAL) if DEFAULT_MANUAL.exists() else None,
        },
        "summary": {
            "model_count": len(rows),
            "runtime_capable_count": sum(1 for row in rows if row.get("manifest_status") == "PASS"),
            "no_runtime_count": sum(1 for row in rows if row.get("qa_class") == "NO_RUNTIME"),
            "class_counts": class_counts,
        },
        "thresholds": {
            "MOTION_STRONG": "max changed_ratio >= 0.02",
            "MOTION_VISIBLE": "max changed_ratio >= 0.004",
            "MOTION_SUBTLE_OR_EYE_ONLY": "max changed_ratio >= 0.0005",
            "MOTION_STATIC": "motion group exists but changed_ratio < 0.0005",
        },
        "rows": rows,
    }
    out_json = out_dir / "reports" / "all57_motion_playback_qa_matrix.json"
    out_md = out_dir / "reports" / "all57_motion_playback_qa_matrix.md"
    write_json(out_json, report)
    write_md(out_md, report)
    return report


def write_md(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# All57 Motion Playback QA Matrix",
        "",
        "## Summary",
        "",
        f"- status: `{report['status']}`",
        f"- model_count: `{report['summary']['model_count']}`",
        f"- runtime_capable_count: `{report['summary']['runtime_capable_count']}`",
        f"- no_runtime_count: `{report['summary']['no_runtime_count']}`",
        "",
        "## Class Counts",
        "",
        "| Class | Count |",
        "|---|---:|",
    ]
    for key, value in sorted(report["summary"]["class_counts"].items()):
        lines.append(f"| {key} | {value} |")
    lines += [
        "",
        "## Matrix",
        "",
        "| Rank | Model | Manifest | Motion Group | Max Changed Ratio | QA Class | Manual |",
        "|---:|---|---|---|---:|---|---|",
    ]
    for row in report["rows"]:
        ratios = [m.get("changed_ratio", 0) for m in row.get("motion_diffs", {}).values()]
        manual_status = row.get("manual_observation", {}).get("manual_status", "")
        lines.append(
            f"| {row.get('rank')} | `{row.get('name')}` | {row.get('manifest_status')} | "
            f"{row.get('motion_group') or ''} | {max(ratios) if ratios else 0} | {row.get('qa_class')} | {manual_status} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    manifest = load_json(args.manifest)
    sandbox = load_json(args.sandbox_report)
    demo_dir = ROOT / sandbox["demo_dir"]
    if not args.skip_npm_install and not (demo_dir / "node_modules" / "vite").exists():
        subprocess.run(["npm", "install"], cwd=demo_dir, check=True)

    base_url = f"http://127.0.0.1:{args.port}/"
    server = subprocess.Popen(
        ["npm", "run", "start", "--", "--host", "127.0.0.1", "--port", str(args.port)],
        cwd=demo_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_for_server(base_url)
        script_path = args.out_dir / "reports" / "all57_motion_playback_qa_playwright.js"
        raw_path = args.out_dir / "reports" / "all57_motion_playback_qa_raw.json"
        build_playwright_script(
            script_path,
            args.manifest.resolve(),
            build_runtime_index(sandbox),
            args.out_dir.resolve(),
            base_url,
            args.limit,
        )
        subprocess.run(["node", str(script_path)], cwd=ROOT, check=True)
        report = postprocess(raw_path, manifest, load_manual(args.manual_observations), args.out_dir)
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
    print(
        json.dumps(
            {
                "status": report["status"],
                "json": rel(args.out_dir / "reports" / "all57_motion_playback_qa_matrix.json"),
                "markdown": rel(args.out_dir / "reports" / "all57_motion_playback_qa_matrix.md"),
                "summary": report["summary"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

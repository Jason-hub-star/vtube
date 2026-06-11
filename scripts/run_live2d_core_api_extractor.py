#!/usr/bin/env python3
"""Extract Core-backed runtime structure from the Live2D strong model sandbox."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "live2d-strong-model-pattern-001"
DEFAULT_MANIFEST = EXPERIMENT / "reports" / "strong20_render_manifest.json"
DEFAULT_SANDBOX_REPORT = EXPERIMENT / "reports" / "strong20_runtime_probe_sandbox.json"
DEFAULT_OUT = EXPERIMENT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--sandbox-report", type=Path, default=DEFAULT_SANDBOX_REPORT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--port", type=int, default=5102)
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


def wait_for_server(url: str, timeout: float = 30.0) -> None:
    host_port = url.split("//", 1)[1].split("/", 1)[0]
    host, port_str = host_port.rsplit(":", 1)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, int(port_str)), timeout=1):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"server did not start: {url}")


def build_playwright_spec(path: Path, manifest_path: Path, out_dir: Path, base_url: str) -> None:
    spec = f"""
const fs = require('fs');
const path = require('path');
const {{ test, expect }} = require('@playwright/test');

const manifest = JSON.parse(fs.readFileSync({json.dumps(str(manifest_path))}, 'utf8'));
const outDir = {json.dumps(str(out_dir))};
const baseUrl = {json.dumps(base_url)};

test.setTimeout(240000);

test('extract Cubism Core-backed snapshots', async ({{ page }}) => {{
  await page.goto(baseUrl, {{ waitUntil: 'domcontentloaded' }});
  await page.waitForFunction(() => window.__vtubeProbe, null, {{ timeout: 20000 }});
  const ready = await page.evaluate(() => window.__vtubeProbe.waitReady(20000));
  expect(ready).toBeTruthy();
  const names = await page.evaluate(() => window.__vtubeProbe.modelNames());
  const rows = [];

  for (let index = 0; index < manifest.models.length; index++) {{
    const model = manifest.models[index];
    if (model.manifest_status && model.manifest_status !== 'PASS') {{
      rows.push({{ id: model.id, safe_id: model.safe_id, status: 'SKIPPED_MANIFEST_FAIL' }});
      continue;
    }}
    await page.evaluate((i) => window.__vtubeProbe.switchModel(i), index);
    const modelReady = await page.evaluate(() => window.__vtubeProbe.waitReady(20000));
    await page.waitForTimeout(500);
    const snapshot = await page.evaluate(() => window.__vtubeProbe.coreSnapshot());
    if (!modelReady || !snapshot) {{
      rows.push({{ id: model.id, safe_id: model.safe_id, status: 'FAIL_NO_CORE_SNAPSHOT' }});
      continue;
    }}

    const snapshotDir = path.join(outDir, 'core_api', model.safe_id);
    fs.mkdirSync(snapshotDir, {{ recursive: true }});
    const snapshotPath = path.join(snapshotDir, 'core_snapshot.json');
    fs.writeFileSync(snapshotPath, JSON.stringify({{
      schema_version: 1,
      generated_at: new Date().toISOString(),
      model_id: model.id,
      safe_id: model.safe_id,
      model_name: model.name,
      sandbox_model_name: names[index],
      policy: {{
        asset_reuse: 'FORBIDDEN',
        content: 'runtime IDs, counts, order, masks, and geometry bounds only'
      }},
      snapshot
    }}, null, 2) + '\\n');

    rows.push({{
      id: model.id,
      safe_id: model.safe_id,
      name: model.name,
      sandbox_model_name: names[index],
      status: 'PASS',
      snapshot_path: snapshotPath,
      counts: snapshot.counts,
      canvas: snapshot.canvas,
      masked_drawable_ids: snapshot.drawables.filter((item) => item.maskCount > 0).map((item) => item.id),
      inverted_mask_drawable_ids: snapshot.drawables.filter((item) => item.invertedMask).map((item) => item.id),
      draw_order_min: Math.min(...snapshot.drawables.map((item) => item.drawOrder ?? 0)),
      draw_order_max: Math.max(...snapshot.drawables.map((item) => item.drawOrder ?? 0)),
      render_order_min: Math.min(...snapshot.drawables.map((item) => item.renderOrder ?? 0)),
      render_order_max: Math.max(...snapshot.drawables.map((item) => item.renderOrder ?? 0)),
    }});
  }}

  const reportPath = path.join(outDir, 'reports', 'strong20_core_api_extractor_playwright_raw.json');
  fs.mkdirSync(path.dirname(reportPath), {{ recursive: true }});
  fs.writeFileSync(reportPath, JSON.stringify({{
    generated_at: new Date().toISOString(),
    status: rows.every((row) => row.status === 'PASS') ? 'PASS' : 'WARN',
    model_count: rows.length,
    models: rows
  }}, null, 2) + '\\n');
}});
"""
    path.write_text(spec, encoding="utf-8")


def numeric_summary(values: list[float]) -> dict[str, Any]:
    clean = sorted(float(v) for v in values if isinstance(v, (int, float)))
    if not clean:
        return {"count": 0}
    mid = len(clean) // 2
    median = clean[mid] if len(clean) % 2 else (clean[mid - 1] + clean[mid]) / 2
    return {
        "count": len(clean),
        "min": clean[0],
        "median": median,
        "max": clean[-1],
        "mean": sum(clean) / len(clean),
    }


def postprocess(raw_path: Path, out_dir: Path) -> dict[str, Any]:
    raw = load_json(raw_path)
    rows = raw.get("models", [])
    pass_rows = [row for row in rows if row.get("status") == "PASS"]
    masked = [row.get("counts", {}).get("maskedDrawables", 0) for row in pass_rows]
    inverted = [row.get("counts", {}).get("invertedMaskDrawables", 0) for row in pass_rows]
    offscreens = [row.get("counts", {}).get("offscreens", 0) for row in pass_rows]
    drawables = [row.get("counts", {}).get("drawables", 0) for row in pass_rows]
    parameters = [row.get("counts", {}).get("parameters", 0) for row in pass_rows]
    parts = [row.get("counts", {}).get("parts", 0) for row in pass_rows]

    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "kind": "live2d_official_cubism_core_api_extractor",
        "status": "PASS" if len(pass_rows) == len(rows) and rows else "WARN",
        "method": "Cubism SDK for Web sandbox probe using Live2DCubismCore-backed Framework model getters",
        "policy": {
            "asset_reuse": "FORBIDDEN",
            "saved_content": "IDs, numeric values, draw/render order, mask links, vertex bounds, and counts only",
        },
        "summary": {
            "model_count": len(rows),
            "pass_count": len(pass_rows),
            "fail_or_skip_count": len(rows) - len(pass_rows),
            "parameters": numeric_summary(parameters),
            "parts": numeric_summary(parts),
            "drawables": numeric_summary(drawables),
            "masked_drawables": numeric_summary(masked),
            "inverted_mask_drawables": numeric_summary(inverted),
            "offscreens": numeric_summary(offscreens),
        },
        "models": [
            {
                **row,
                "snapshot_path": rel(row.get("snapshot_path")),
            }
            for row in rows
        ],
    }
    out_json = out_dir / "reports" / "strong20_core_api_extractor_report.json"
    out_md = out_dir / "reports" / "strong20_core_api_extractor_report.md"
    write_json(out_json, report)
    write_core_md(out_md, report)
    return report


def write_core_md(path: Path, report: dict[str, Any]) -> None:
    summary = report["summary"]
    lines = [
        "# Strong20 Official Cubism Core API Extractor",
        "",
        "## Summary",
        "",
        f"- status: `{report['status']}`",
        f"- method: {report['method']}",
        f"- models: `{summary['pass_count']}/{summary['model_count']}` PASS",
        f"- parameter median: `{summary['parameters'].get('median')}`",
        f"- part median: `{summary['parts'].get('median')}`",
        f"- drawable median: `{summary['drawables'].get('median')}`",
        f"- masked drawable median: `{summary['masked_drawables'].get('median')}`",
        f"- offscreen median: `{summary['offscreens'].get('median')}`",
        "",
        "## Model Rows",
        "",
        "| Model | Status | Param | Part | Drawable | Masked | Inverted | Offscreen | Snapshot |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["models"]:
        counts = row.get("counts", {}) or {}
        lines.append(
            "| {model} | {status} | {parameters} | {parts} | {drawables} | {masked} | {inverted} | {offscreens} | `{snapshot}` |".format(
                model=row.get("safe_id") or row.get("id"),
                status=row.get("status"),
                parameters=counts.get("parameters", ""),
                parts=counts.get("parts", ""),
                drawables=counts.get("drawables", ""),
                masked=counts.get("maskedDrawables", ""),
                inverted=counts.get("invertedMaskDrawables", ""),
                offscreens=counts.get("offscreens", ""),
                snapshot=row.get("snapshot_path", ""),
            )
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "- 이 리포트는 CMO3 편집 구조가 아니라 Cubism runtime/Core-backed drawable 상태를 본다.",
        "- mask/draw order 위험 판단은 이 extractor의 `masked_drawable_ids`, `drawOrder`, `renderOrder`, `offscreen` 값을 우선 근거로 보강한다.",
        "- 저장된 값은 구조 ID와 숫자뿐이며 공식 샘플의 텍스처/이미지 자산은 재사용하지 않는다.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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

    spec_path = demo_dir / f"{manifest['kind']}_core_api_extractor.spec.cjs"
    raw_path = reports_dir / "strong20_core_api_extractor_playwright_raw.json"
    if raw_path.exists():
        raw_path.unlink()
    build_playwright_spec(spec_path, args.manifest.resolve(), out_dir.resolve(), f"http://127.0.0.1:{args.port}/?core=extract")

    server = subprocess.Popen(
        ["npm", "run", "start", "--", "--host", "127.0.0.1", "--port", str(args.port)],
        cwd=demo_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_for_server(f"http://127.0.0.1:{args.port}/")
        env = os.environ.copy()
        env["PLAYWRIGHT_HTML_OPEN"] = "never"
        subprocess.run(
            ["npx", "playwright", "test", str(spec_path), "--reporter=line"],
            cwd=demo_dir,
            env=env,
            check=True,
        )
        report = postprocess(raw_path, out_dir)
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "summary": report["summary"],
                    "report": rel(out_dir / "reports" / "strong20_core_api_extractor_report.json"),
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

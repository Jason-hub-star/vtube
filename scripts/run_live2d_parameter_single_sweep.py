#!/usr/bin/env python3
"""Run single-parameter min/max sweeps for strong20 Live2D reference models."""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import statistics
import subprocess
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "live2d-strong-model-pattern-001"
DEFAULT_MANIFEST = EXPERIMENT / "reports" / "strong20_render_manifest.json"
DEFAULT_SANDBOX_REPORT = EXPERIMENT / "reports" / "strong20_runtime_probe_sandbox.json"
DEFAULT_OUT = EXPERIMENT

PREFERRED_PARAMETERS = [
    "ParamAngleX",
    "ParamAngleY",
    "ParamEyeLOpen",
    "ParamEyeROpen",
    "ParamEyeBallX",
    "ParamMouthOpenY",
    "ParamMouthForm",
    "ParamHairFront",
    "ParamHairSide",
    "ParamHairBack",
    "ParamBodyAngleX",
    "ParamBodyAngleY",
    "ParamAngleZ",
    "ParamEyeBallY",
    "ParamEyeLSmile",
    "ParamEyeRSmile",
    "ParamBodyAngleZ",
    "ParamBreath",
    "ParamArmLA",
    "ParamArmRA",
    "ParamArmLB",
    "ParamArmRB",
    "ParamHandChangeR",
    "ParamHandChangeL",
    "ParamA",
    "ParamI",
    "ParamU",
    "ParamE",
    "ParamO",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--sandbox-report", type=Path, default=DEFAULT_SANDBOX_REPORT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--port", type=int, default=5103)
    parser.add_argument("--max-parameters-per-model", type=int, default=8)
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


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def parameter_category(param_id: str) -> str:
    lower = param_id.lower()
    if "eye" in lower or "iris" in lower:
        return "eye"
    if "mouth" in lower or lower in {"parama", "parami", "paramu", "parame", "paramo"}:
        return "mouth"
    if "hair" in lower:
        return "hair"
    if "angle" in lower or "body" in lower or "breath" in lower:
        return "body_angle"
    if "arm" in lower or "hand" in lower or "shoulder" in lower:
        return "arm"
    return "other"


def build_playwright_spec(path: Path, manifest_path: Path, out_dir: Path, base_url: str, max_params: int) -> None:
    spec = f"""
const fs = require('fs');
const path = require('path');
const {{ test, expect }} = require('@playwright/test');

const manifest = JSON.parse(fs.readFileSync({json.dumps(str(manifest_path))}, 'utf8'));
const outDir = {json.dumps(str(out_dir))};
const baseUrl = {json.dumps(base_url)};
const preferred = {json.dumps(PREFERRED_PARAMETERS)};
const maxParams = {max_params};

function safeName(value) {{
  return String(value).replace(/[^A-Za-z0-9_.-]+/g, '_');
}}

function chooseParameters(params) {{
  const byId = new Map(params.map((p) => [p.id, p]));
  const chosen = [];
  const seen = new Set();
  for (const id of preferred) {{
    if (byId.has(id) && !seen.has(id)) {{
      chosen.push(byId.get(id));
      seen.add(id);
    }}
  }}
  if (chosen.length < maxParams) {{
    const fallback = params.filter((p) => {{
      const v = p.id.toLowerCase();
      return v.includes('eye') || v.includes('mouth') || v.includes('hair') || v.includes('angle') || v.includes('body') || v.includes('arm') || v.includes('hand');
    }});
    for (const item of fallback) {{
      if (chosen.length >= maxParams) break;
      if (!seen.has(item.id)) {{
        chosen.push(item);
        seen.add(item.id);
      }}
    }}
  }}
  return chosen.slice(0, maxParams);
}}

test.setTimeout(900000);

test('single parameter min max sweep', async ({{ page }}) => {{
  await page.goto(baseUrl, {{ waitUntil: 'domcontentloaded' }});
  await page.waitForFunction(() => window.__vtubeProbe, null, {{ timeout: 20000 }});
  const ready = await page.evaluate(() => window.__vtubeProbe.waitReady(20000));
  expect(ready).toBeTruthy();
  const rows = [];

  for (let index = 0; index < manifest.models.length; index++) {{
    const model = manifest.models[index];
    if (model.manifest_status && model.manifest_status !== 'PASS') {{
      rows.push({{ id: model.id, safe_id: model.safe_id, status: 'SKIPPED_MANIFEST_FAIL' }});
      continue;
    }}
    await page.evaluate((i) => window.__vtubeProbe.switchModel(i), index);
    const modelReady = await page.evaluate(() => window.__vtubeProbe.waitReady(20000));
    if (!modelReady) {{
      rows.push({{ id: model.id, safe_id: model.safe_id, status: 'FAIL_MODEL_NOT_READY' }});
      continue;
    }}
    await page.evaluate(() => window.__vtubeProbe.clear());
    await page.waitForTimeout(450);
    const params = await page.evaluate(() => window.__vtubeProbe.parameters());
    const selected = chooseParameters(params);
    const captureDir = path.join(outDir, 'parameter_single_sweep', model.safe_id);
    fs.mkdirSync(captureDir, {{ recursive: true }});
    const neutralPath = path.join(captureDir, 'neutral.png');
    await page.screenshot({{ path: neutralPath, fullPage: false }});

    for (const param of selected) {{
      for (const position of ['min', 'max']) {{
        await page.evaluate(([id, pos]) => window.__vtubeProbe.setParameter(id, pos), [param.id, position]);
        await page.waitForTimeout(320);
        const targetPath = path.join(captureDir, `${{safeName(param.id)}}_${{position}}.png`);
        await page.screenshot({{ path: targetPath, fullPage: false }});
        rows.push({{
          id: model.id,
          safe_id: model.safe_id,
          name: model.name,
          status: 'PASS',
          parameter_id: param.id,
          parameter_index: param.index,
          position,
          min: param.min,
          max: param.max,
          defaultValue: param.defaultValue,
          neutral_path: neutralPath,
          target_path: targetPath,
        }});
      }}
      await page.waitForFunction(() => window.__vtubeProbe, null, {{ timeout: 20000 }});
      await page.evaluate(() => window.__vtubeProbe.clear());
      await page.waitForTimeout(120);
    }}
  }}

  const reportPath = path.join(outDir, 'reports', 'strong20_parameter_single_sweep_playwright_raw.json');
  fs.mkdirSync(path.dirname(reportPath), {{ recursive: true }});
  fs.writeFileSync(reportPath, JSON.stringify({{
    generated_at: new Date().toISOString(),
    status: rows.some((row) => row.status === 'PASS') ? 'PASS' : 'FAIL',
    model_count: manifest.models.length,
    rows
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
        mask = gray.point(lambda px: 255 if px >= threshold else 0)
        raw_bbox = mask.getbbox()
        bbox = None
        if raw_bbox:
            x0, y0, x1, y1 = raw_bbox
            bbox = {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0}
        pixel_count = width * height
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
    clean.sort()
    return {
        "count": len(clean),
        "min": round(clean[0], 6),
        "median": round(statistics.median(clean), 6),
        "max": round(clean[-1], 6),
        "mean": round(statistics.fmean(clean), 6),
    }


def postprocess(raw_path: Path, out_dir: Path, threshold: int) -> dict[str, Any]:
    raw = load_json(raw_path)
    rows = []
    for row in raw.get("rows", []):
        if row.get("status") != "PASS":
            rows.append(row)
            continue
        metrics = image_diff_metrics(Path(row["neutral_path"]), Path(row["target_path"]), threshold)
        rows.append(
            {
                **row,
                "category": parameter_category(row["parameter_id"]),
                "neutral_path": rel(row["neutral_path"]),
                "target_path": rel(row["target_path"]),
                **metrics,
            }
        )

    pass_rows = [row for row in rows if row.get("status") == "PASS"]
    by_category: dict[str, Any] = {}
    for category in sorted({row["category"] for row in pass_rows}):
        category_rows = [row for row in pass_rows if row["category"] == category]
        by_category[category] = {
            "sample_count": len(category_rows),
            "parameter_count": len({row["parameter_id"] for row in category_rows}),
            "changed_ratio": numeric_summary([row["changed_ratio"] for row in category_rows]),
            "top_parameters": [
                {
                    "model_id": row["id"],
                    "parameter_id": row["parameter_id"],
                    "position": row["position"],
                    "changed_ratio": row["changed_ratio"],
                    "changed_bbox": row["changed_bbox"],
                }
                for row in sorted(category_rows, key=lambda item: item["changed_ratio"], reverse=True)[:12]
            ],
        }
    by_parameter: dict[str, Any] = {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pass_rows:
        grouped[row["parameter_id"]].append(row)
    for parameter_id, parameter_rows in sorted(grouped.items()):
        by_parameter[parameter_id] = {
            "category": parameter_category(parameter_id),
            "model_count": len({row["id"] for row in parameter_rows}),
            "sample_count": len(parameter_rows),
            "changed_ratio": numeric_summary([row["changed_ratio"] for row in parameter_rows]),
        }

    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "kind": "live2d_strong20_parameter_single_sweep",
        "status": "PASS" if pass_rows else "FAIL",
        "method": "one parameter at min/max while other parameters stay neutral/default",
        "diff_threshold_luma": threshold,
        "summary": {
            "model_count": len({row.get("id") for row in pass_rows}),
            "sample_count": len(pass_rows),
            "parameter_count": len(by_parameter),
            "category_counts": dict(Counter(row["category"] for row in pass_rows)),
        },
        "summary_by_category": by_category,
        "summary_by_parameter": by_parameter,
        "rows": rows,
    }
    out_json = out_dir / "reports" / "strong20_parameter_single_sweep_report.json"
    out_md = out_dir / "reports" / "strong20_parameter_single_sweep_report.md"
    write_json(out_json, report)
    write_md(out_md, report)
    return report


def write_md(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Strong20 Parameter Single Sweep",
        "",
        "## Summary",
        "",
        f"- status: `{report['status']}`",
        f"- method: {report['method']}",
        f"- models: `{report['summary']['model_count']}`",
        f"- samples: `{report['summary']['sample_count']}`",
        f"- parameters: `{report['summary']['parameter_count']}`",
        "",
        "## Category Summary",
        "",
        "| Category | Samples | Parameters | Median Changed | Max Changed |",
        "|---|---:|---:|---:|---:|",
    ]
    for category, item in sorted(report["summary_by_category"].items()):
        changed = item["changed_ratio"]
        lines.append(
            f"| {category} | {item['sample_count']} | {item['parameter_count']} | {changed.get('median')} | {changed.get('max')} |"
        )
    lines += [
        "",
        "## Production Use",
        "",
        "- 이 리포트는 category 묶음 sweep보다 강한 근거다. 각 파라미터 하나만 움직였을 때의 화면 영향 범위를 본다.",
        "- 새 모델에서는 eye/mouth/hair/body_angle 파라미터가 bbox를 명확히 바꾸는지 G3에서 확인한다.",
        "- 변화량이 너무 작으면 Cubism keyform/deformer가 부족한 것이고, 변화량이 너무 넓으면 draw order/overhang 위험을 확인한다.",
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

    spec_path = demo_dir / f"{manifest['kind']}_parameter_single_sweep.spec.cjs"
    raw_path = reports_dir / "strong20_parameter_single_sweep_playwright_raw.json"
    if raw_path.exists():
        raw_path.unlink()
    build_playwright_spec(
        spec_path,
        args.manifest.resolve(),
        out_dir.resolve(),
        f"http://127.0.0.1:{args.port}/?single_param=sweep",
        args.max_parameters_per_model,
    )

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
        report = postprocess(raw_path, out_dir, args.diff_threshold)
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "summary": report["summary"],
                    "report": rel(out_dir / "reports" / "strong20_parameter_single_sweep_report.json"),
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

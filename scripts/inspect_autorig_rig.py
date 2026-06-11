#!/usr/bin/env python3
"""AUTORIG Rig Inspector: graph, influence, junction scores, and AI context."""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, load_json, now_iso, rel, write_json  # noqa: E402
from lib.vtube_proc import terminate, wait_for_server  # noqa: E402
from mini_cubism_preview_server import default_mini_rig  # noqa: E402

PLAYWRIGHT = ROOT / "experiments/live2d-strong-model-pattern-001/probe_sandbox/strong20/Samples/TypeScript/Demo/node_modules/playwright"
INTERESTING_GROUPS = ("neck", "body", "head", "hair", "shoulder", "clothes", "cloth")

NODE_DYNAMIC = r"""
const fs = require("fs");
const config = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const { chromium } = require(config.playwright);

function slug(text) { return String(text).replace(/[^a-zA-Z0-9_-]/g, "_"); }
function decodeBase64(raw) {
  const bin = atob(raw);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i += 1) out[i] = bin.charCodeAt(i);
  return out;
}
async function sampleTiles(page) {
  return await page.evaluate((tiles) => {
    const result = [];
    for (const tile of tiles) {
      const raw = window.__miniProbe.regionPixelsBase64(tile.x, tile.y, tile.w, tile.h);
      result.push({ tile, raw });
    }
    return result;
  }, config.tiles);
}
function tileDelta(a, b) {
  let total = 0;
  let count = 0;
  let changed = 0;
  for (let i = 0; i < a.length && i < b.length; i += 16) {
    const d = Math.abs(a[i] - b[i]) + Math.abs(a[i + 1] - b[i + 1]) + Math.abs(a[i + 2] - b[i + 2]) + Math.abs(a[i + 3] - b[i + 3]);
    total += d / 4;
    count += 1;
    if (d > 12) changed += 1;
  }
  return { mean_abs: count ? total / count : 0, changed_ratio: count ? changed / count : 0 };
}

(async () => {
  const out = { generated_at: new Date().toISOString(), renderer_requested: config.renderer, backend: null, neutral_hash: null, states: [], errors: [] };
  let browser = null;
  try {
    browser = await chromium.launch({ headless: true, args: config.launch_args || [] });
    const page = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
    await page.goto(config.base + config.query, { waitUntil: "load", timeout: 30000 });
    await page.waitForFunction(() => window.__miniProbe, null, { timeout: 20000 });
    await page.evaluate(() => window.__miniProbe.waitReady(20000));
    await page.evaluate(() => window.__miniClearSelection && window.__miniClearSelection());
    out.backend = await page.evaluate(() => window.__miniBackend ? window.__miniBackend() : "canvas");
    await page.evaluate((defaults) => window.__miniSetParameters(defaults), config.defaults);
    out.neutral_hash = await page.evaluate(() => window.__miniProbe.canvasHash());
    const neutralTiles = (await sampleTiles(page)).map((item) => ({ tile: item.tile, bytes: decodeBase64(item.raw) }));
    await page.screenshot({ path: `${config.captures}/dynamic_neutral.png` });
    for (const state of config.states) {
      const values = { ...config.defaults, [state.parameter_id]: state.value };
      await page.evaluate((payload) => window.__miniSetParameters(payload), values);
      const hash = await page.evaluate(() => window.__miniProbe.canvasHash());
      const tiles = await sampleTiles(page);
      let mean = 0;
      let ratio = 0;
      for (let i = 0; i < tiles.length; i += 1) {
        const d = tileDelta(neutralTiles[i].bytes, decodeBase64(tiles[i].raw));
        mean += d.mean_abs;
        ratio += d.changed_ratio;
      }
      const capture = `${config.captures}/dynamic_${slug(state.parameter_id)}_${slug(state.label)}.png`;
      await page.screenshot({ path: capture });
      out.states.push({
        parameter_id: state.parameter_id,
        label: state.label,
        value: state.value,
        canvas_hash: hash,
        pixel_delta_mean_abs: tiles.length ? mean / tiles.length : 0,
        changed_sample_ratio: tiles.length ? ratio / tiles.length : 0,
        capture,
      });
    }
  } catch (error) {
    out.errors.push(String(error && error.stack ? error.stack : error));
  } finally {
    if (browser) await browser.close();
    fs.writeFileSync(config.out, JSON.stringify(out, null, 2));
  }
})();
"""


def bbox_gap(a: list[float], b: list[float]) -> float:
    ax0, ay0, aw, ah = a
    bx0, by0, bw, bh = b
    ax1, ay1 = ax0 + aw, ay0 + ah
    bx1, by1 = bx0 + bw, by0 + bh
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return math.hypot(dx, dy)


def bbox_contact(a: list[float], b: list[float], tolerance: float = 24) -> float:
    ax0, ay0, aw, ah = a
    bx0, by0, bw, bh = b
    ax1, ay1 = ax0 + aw, ay0 + ah
    bx1, by1 = bx0 + bw, by0 + bh
    x_overlap = max(0, min(ax1, bx1) - max(ax0, bx0))
    y_overlap = max(0, min(ay1, by1) - max(ay0, by0))
    vertical_touch = abs(ax1 - bx0) <= tolerance or abs(bx1 - ax0) <= tolerance
    horizontal_touch = abs(ay1 - by0) <= tolerance or abs(by1 - ay0) <= tolerance
    return max(y_overlap if vertical_touch else 0, x_overlap if horizontal_touch else 0, min(x_overlap, y_overlap))


def interesting(part_id: str) -> bool:
    low = part_id.lower()
    return any(group in low for group in INTERESTING_GROUPS)


def delta_magnitude(deltas: dict[str, Any] | None) -> float:
    d = deltas or {}
    translate = d.get("translate") or [0, 0]
    scale = d.get("scale") or [1, 1]
    return (
        abs(float(translate[0] or 0))
        + abs(float(translate[1] or 0))
        + abs(float(d.get("rotate") or 0)) * 2
        + abs(float(scale[0] if scale[0] is not None else 1) - 1) * 80
        + abs(float(scale[1] if scale[1] is not None else 1) - 1) * 80
        + abs(float(d.get("opacity", 1)) - 1) * 60
    )


def delta_vector(deltas: dict[str, Any] | None) -> tuple[float, float, float, float, float]:
    d = deltas or {}
    translate = d.get("translate") or [0, 0]
    scale = d.get("scale") or [1, 1]
    return (
        float(translate[0] or 0),
        float(translate[1] or 0),
        float(d.get("rotate") or 0),
        float(scale[0] if scale[0] is not None else 1) - 1,
        float(scale[1] if scale[1] is not None else 1) - 1,
    )


def vec_distance(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    weights = (1, 1, 2, 80, 80)
    return sum(abs((a[i] - b[i]) * weights[i]) for i in range(len(weights)))


def effective_bindings(character: dict[str, Any], rig: dict[str, Any]) -> list[dict[str, Any]]:
    base = character.get("keyform_bindings") or []
    overrides = rig.get("keyform_overrides") or []
    if not overrides:
        return list(base)
    override_keys = {(b.get("parameter_id"), b.get("target_id"), b.get("key_value")) for b in overrides}
    return [b for b in base if (b.get("parameter_id"), b.get("target_id"), b.get("key_value")) not in override_keys] + overrides


class Inspector:
    def __init__(self, project: Path, character: dict[str, Any], rig: dict[str, Any]) -> None:
        self.project = project
        self.character = character
        self.rig = rig
        self.parts = {p["id"]: p for p in character.get("parts", [])}
        self.meshes = {m.get("part_id"): m for m in character.get("meshes", [])}
        self.deformers = {d["id"]: d for d in character.get("deformers", [])}
        self.parameters = {p["id"]: p for p in character.get("parameters", [])}
        self.bindings = effective_bindings(character, rig)
        self.bindings_by_param: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.bindings_by_target_param: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for binding in self.bindings:
            self.bindings_by_param[binding.get("parameter_id")].append(binding)
            self.bindings_by_target_param[(binding.get("target_id"), binding.get("parameter_id"))].append(binding)
        self.children_by_deformer: dict[str | None, list[str]] = defaultdict(list)
        for deformer in self.deformers.values():
            self.children_by_deformer[deformer.get("parent_id")].append(deformer["id"])

    def primary_deformer(self, part_id: str) -> str | None:
        for preferred in ("Eye_L", "Eye_R", "Mouth", "Hair_Front", "Hair_Back"):
            d = self.deformers.get(preferred)
            if d and part_id in (d.get("child_ids") or []):
                return preferred
        for deformer in self.deformers.values():
            if part_id in (deformer.get("child_ids") or []) and deformer["id"] != "Root":
                if "hair" in part_id and "Head_X" in self.deformers:
                    return "Head_X"
                return deformer["id"]
        return None

    def deformer_chain(self, deformer_id: str | None) -> list[str]:
        chain: list[str] = []
        current = self.deformers.get(deformer_id or "")
        seen = set()
        while current and current["id"] not in seen:
            seen.add(current["id"])
            chain.insert(0, current["id"])
            current = self.deformers.get(current.get("parent_id"))
        return chain

    def part_chain(self, part_id: str) -> list[str]:
        return self.deformer_chain(self.primary_deformer(part_id))

    def subtree_parts(self, deformer_id: str) -> set[str]:
        out = set(self.deformers.get(deformer_id, {}).get("child_ids") or [])
        for child in self.children_by_deformer.get(deformer_id, []):
            out |= self.subtree_parts(child)
        return out

    def binding_vector_for_target(self, target_id: str, parameter_id: str) -> tuple[float, float, float, float, float]:
        rows = self.bindings_by_target_param.get((target_id, parameter_id), [])
        if not rows:
            return (0, 0, 0, 0, 0)
        row = max(rows, key=lambda item: delta_magnitude(item.get("deltas")))
        return delta_vector(row.get("deltas"))

    def part_vector_for_param(self, part_id: str, parameter_id: str) -> tuple[float, float, float, float, float]:
        targets = self.part_chain(part_id) + [part_id]
        result = [0.0, 0.0, 0.0, 0.0, 0.0]
        for target in targets:
            vec = self.binding_vector_for_target(target, parameter_id)
            for i, value in enumerate(vec):
                result[i] += value
        return tuple(result)  # type: ignore[return-value]

    def influence_rows(self) -> list[dict[str, Any]]:
        rows = []
        physics_by_param: dict[str, set[str]] = defaultdict(set)
        for profile in self.character.get("physics_profiles") or []:
            for param in (profile.get("input_weights") or {}).keys():
                physics_by_param[param].add(profile.get("id"))
            if profile.get("output_parameter"):
                physics_by_param[profile["output_parameter"]].add(profile.get("id"))
        for parameter_id, param in sorted(self.parameters.items()):
            targets = {b.get("target_id") for b in self.bindings_by_param.get(parameter_id, [])}
            deformer_targets = {t for t in targets if t in self.deformers}
            part_targets = {t for t in targets if t in self.parts}
            indirect_parts = set(part_targets)
            for target in deformer_targets:
                indirect_parts |= self.subtree_parts(target)
            rows.append({
                "parameter_id": parameter_id,
                "min": param.get("min"),
                "max": param.get("max"),
                "default": param.get("default"),
                "target_count": len(targets),
                "part_influence_count": len(indirect_parts),
                "deformer_influence_count": len(deformer_targets),
                "physics_influence_count": len(physics_by_param.get(parameter_id, set())),
                "direct_delta_magnitude": round(sum(delta_magnitude(b.get("deltas")) for b in self.bindings_by_param.get(parameter_id, [])), 4),
                "targets": "|".join(sorted(str(t) for t in targets if t)),
                "parts": "|".join(sorted(indirect_parts)),
            })
        return rows

    def part_chain_rows(self) -> list[dict[str, Any]]:
        direct_counts = defaultdict(int)
        for binding in self.bindings:
            if binding.get("target_id") in self.parts:
                direct_counts[binding.get("target_id")] += 1
        physics_counts = defaultdict(int)
        for profile in self.character.get("physics_profiles") or []:
            for target in profile.get("targets") or []:
                physics_counts[target] += 1
        rows = []
        for part_id, part in sorted(self.parts.items()):
            mesh = self.meshes.get(part_id) or {}
            rows.append({
                "part_id": part_id,
                "folder": part.get("folder"),
                "draw_order": part.get("draw_order"),
                "primary_deformer": self.primary_deformer(part_id) or "",
                "deformer_chain": ">".join(self.part_chain(part_id)),
                "direct_binding_count": direct_counts[part_id],
                "physics_profile_count": physics_counts[part_id],
                "bbox": json.dumps(part.get("bbox")),
                "vertex_count": len(mesh.get("vertices") or []),
                "triangle_count": len(mesh.get("triangles") or []),
            })
        return rows

    def junction_rows(self) -> list[dict[str, Any]]:
        rows = []
        parts = list(self.parts.values())
        physics_parts = {target for profile in self.character.get("physics_profiles") or [] for target in profile.get("targets") or []}
        for i, a in enumerate(parts):
            for b in parts[i + 1:]:
                gap = bbox_gap(a["bbox"], b["bbox"])
                contact = bbox_contact(a["bbox"], b["bbox"])
                draw_gap = abs(float(a.get("draw_order", 0)) - float(b.get("draw_order", 0)))
                if not ((gap <= 80 and draw_gap <= 250) or (interesting(a["id"]) and interesting(b["id"]) and gap <= 160)):
                    continue
                chain_a = self.part_chain(a["id"])
                chain_b = self.part_chain(b["id"])
                shared = 0
                for left, right in zip(chain_a, chain_b):
                    if left != right:
                        break
                    shared += 1
                chain_den = max(len(chain_a), len(chain_b), 1)
                chain_component = (1 - shared / chain_den) * 35
                common_params = [pid for pid in self.parameters if self.part_vector_for_param(a["id"], pid) != (0, 0, 0, 0, 0) or self.part_vector_for_param(b["id"], pid) != (0, 0, 0, 0, 0)]
                delta_component = 0.0
                if common_params:
                    delta_component = min(30, sum(vec_distance(self.part_vector_for_param(a["id"], pid), self.part_vector_for_param(b["id"], pid)) for pid in common_params) / len(common_params))
                draw_component = min(12, draw_gap / 25)
                physics_component = 12 if ((a["id"] in physics_parts) != (b["id"] in physics_parts)) else 0
                contact_component = max(0, 11 - min(contact, 220) / 20)
                score = max(0, min(100, chain_component + delta_component + draw_component + physics_component + contact_component))
                rows.append({
                    "part_a": a["id"],
                    "part_b": b["id"],
                    "score": round(score, 3),
                    "bbox_gap": round(gap, 3),
                    "contact_length": round(contact, 3),
                    "draw_order_gap": round(draw_gap, 3),
                    "shared_chain_depth": shared,
                    "chain_a": ">".join(chain_a),
                    "chain_b": ">".join(chain_b),
                    "physics_a": int(a["id"] in physics_parts),
                    "physics_b": int(b["id"] in physics_parts),
                })
        return sorted(rows, key=lambda row: row["score"], reverse=True)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def dot_escape(text: str) -> str:
    return str(text).replace("\\", "\\\\").replace('"', '\\"')


def write_graph(out_dir: Path, inspector: Inspector, influence: list[dict[str, Any]]) -> dict[str, Any]:
    lines = ["digraph rig {", '  graph [rankdir=LR, bgcolor="white"];', '  node [shape=box, style="rounded,filled", fontname="Helvetica"];']
    for deformer in inspector.deformers.values():
        lines.append(f'  "d:{dot_escape(deformer["id"])}" [label="{dot_escape(deformer["id"])}", fillcolor="#e8f3ff"];')
        if deformer.get("parent_id"):
            lines.append(f'  "d:{dot_escape(deformer["parent_id"])}" -> "d:{dot_escape(deformer["id"])}" [color="#3182f6"];')
        for child in deformer.get("child_ids") or []:
            lines.append(f'  "d:{dot_escape(deformer["id"])}" -> "p:{dot_escape(child)}" [color="#8b95a1"];')
    for part in inspector.parts.values():
        lines.append(f'  "p:{dot_escape(part["id"])}" [label="{dot_escape(part["id"])}", fillcolor="#f9fafb"];')
    for row in influence:
        param_id = row["parameter_id"]
        lines.append(f'  "param:{dot_escape(param_id)}" [label="{dot_escape(param_id)}", fillcolor="#fff3bf"];')
        for target in filter(None, str(row["targets"]).split("|")):
            prefix = "d" if target in inspector.deformers else "p"
            lines.append(f'  "param:{dot_escape(param_id)}" -> "{prefix}:{dot_escape(target)}" [color="#f59f00"];')
    for profile in inspector.character.get("physics_profiles") or []:
        node = f'phys:{profile.get("id")}'
        lines.append(f'  "{dot_escape(node)}" [label="{dot_escape(profile.get("id"))}", fillcolor="#e6fcf5"];')
        for target in profile.get("targets") or []:
            lines.append(f'  "{dot_escape(node)}" -> "p:{dot_escape(target)}" [color="#0ca678"];')
    lines.append("}")
    dot_path = out_dir / "rig_graph.dot"
    dot_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    dot_bin = shutil.which("dot")
    svg_path = out_dir / "rig_graph.svg"
    if dot_bin:
        result = subprocess.run([dot_bin, "-Tsvg", str(dot_path), "-o", str(svg_path)], capture_output=True, text=True, check=False)
        return {"graphviz_available": True, "svg_created": result.returncode == 0, "svg": rel(svg_path) if result.returncode == 0 else None, "stderr": result.stderr[-1000:]}
    return {"graphviz_available": False, "svg_created": False, "svg": None}


def dynamic_tiles(canvas: list[int]) -> list[dict[str, int]]:
    width, height = int(canvas[0]), int(canvas[1])
    tiles = []
    for y in (0.28, 0.42, 0.56, 0.70):
        for x in (0.32, 0.44, 0.56, 0.68):
            tiles.append({"x": max(0, int(width * x) - 32), "y": max(0, int(height * y) - 32), "w": 64, "h": 64})
    return tiles


def run_dynamic(project: Path, out_dir: Path, character: dict[str, Any], renderer: str, port: int) -> dict[str, Any]:
    captures = out_dir / "dynamic_captures"
    captures.mkdir(parents=True, exist_ok=True)
    defaults = {p["id"]: p.get("default", 0) for p in character.get("parameters", [])}
    states = []
    for param in character.get("parameters", []):
        values = [param.get("min"), param.get("max")]
        for label, value in zip(("min", "max"), values):
            if value is not None and float(value) != float(param.get("default", 0)):
                states.append({"parameter_id": param["id"], "label": label, "value": value})
    config_path = out_dir / "dynamic_config.json"
    raw_path = out_dir / "dynamic_motion_report.json"
    runner_path = out_dir / "dynamic_runner.js"
    runner_path.write_text(NODE_DYNAMIC, encoding="utf-8")
    write_json(config_path, {
        "playwright": str(PLAYWRIGHT),
        "base": f"http://127.0.0.1:{port}/",
        "query": "?renderer=pixi" if renderer == "pixi" else "",
        "renderer": renderer,
        "launch_args": ["--use-angle=swiftshader"] if renderer == "pixi" else [],
        "defaults": defaults,
        "states": states,
        "tiles": dynamic_tiles(character.get("canvas_size") or [2048, 2048]),
        "captures": str(captures),
        "out": str(raw_path),
    })
    server = subprocess.Popen(
        ["python3", str(ROOT / "scripts/mini_cubism_preview_server.py"), "--project", str(project), "--port", str(port)],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        wait_for_server("127.0.0.1", port, timeout=30)
        result = subprocess.run(["node", str(runner_path), str(config_path)], cwd=ROOT, capture_output=True, text=True, timeout=300, check=False)
        if not raw_path.exists():
            write_json(raw_path, {"generated_at": now_iso(), "renderer_requested": renderer, "states": [], "errors": [result.stderr[-2000:] or result.stdout[-2000:] or "dynamic runner produced no report"]})
    except Exception as error:  # noqa: BLE001
        write_json(raw_path, {"generated_at": now_iso(), "renderer_requested": renderer, "states": [], "errors": [str(error)]})
    finally:
        terminate(server)
    return load_json(raw_path)


def ai_context(inspector: Inspector, influence: list[dict[str, Any]], chains: list[dict[str, Any]], junctions: list[dict[str, Any]], dynamic: dict[str, Any] | None) -> dict[str, Any]:
    mesh_metrics = {pid: {"vertex_count": len((mesh or {}).get("vertices") or []), "triangle_count": len((mesh or {}).get("triangles") or [])} for pid, mesh in inspector.meshes.items()}
    return {
        "project": rel(inspector.project),
        "generated_at": now_iso(),
        "counts": {
            "parts": len(inspector.parts),
            "meshes": len(inspector.meshes),
            "deformers": len(inspector.deformers),
            "parameters": len(inspector.parameters),
            "keyform_bindings": len(inspector.bindings),
            "physics_profiles": len(inspector.character.get("physics_profiles") or []),
        },
        "parameters": list(inspector.parameters.values()),
        "deformer_tree": [{"id": d["id"], "parent_id": d.get("parent_id"), "child_ids": d.get("child_ids") or [], "bounds": d.get("bounds"), "lattice": d.get("lattice")} for d in inspector.deformers.values()],
        "parts": [{**{k: p.get(k) for k in ("id", "folder", "draw_order", "bbox", "deformer_node")}, **mesh_metrics.get(pid, {})} for pid, p in inspector.parts.items()],
        "influence_by_parameter": influence,
        "part_chains": chains,
        "physics_profiles": inspector.character.get("physics_profiles") or [],
        "junction_scores": junctions[:80],
        "dynamic_available": bool(dynamic),
        "dynamic_summary": {
            "backend": dynamic.get("backend") if dynamic else None,
            "states": len(dynamic.get("states", [])) if dynamic else 0,
            "errors": dynamic.get("errors", []) if dynamic else [],
        },
    }


def write_summary(path: Path, context: dict[str, Any], tooling: dict[str, Any], junctions: list[dict[str, Any]]) -> None:
    counts = context["counts"]
    lines = [
        "# AUTORIG Rig Inspector Summary",
        "",
        f"Generated: {context['generated_at']}",
        f"Project: `{context['project']}`",
        "",
        "## Counts",
        "",
        "| item | count |",
        "|---|---:|",
    ]
    for key, value in counts.items():
        lines.append(f"| {key} | {value} |")
    lines += [
        "",
        "## Tooling",
        "",
        f"- Graphviz available: `{tooling.get('graphviz_available')}`",
        f"- SVG created: `{tooling.get('svg_created')}`",
        f"- Dynamic states measured: `{context['dynamic_summary']['states']}`",
        "",
        "## Highest Junction Scores",
        "",
        "| score | part_a | part_b | bbox_gap | contact_length |",
        "|---:|---|---|---:|---:|",
    ]
    for row in junctions[:20]:
        lines.append(f"| {row['score']} | `{row['part_a']}` | `{row['part_b']}` | {row['bbox_gap']} | {row['contact_length']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--character", type=Path, default=None)
    parser.add_argument("--mini-rig", type=Path, default=None)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--dynamic", action="store_true")
    parser.add_argument("--renderer", choices=["canvas", "pixi"], default="canvas")
    parser.add_argument("--port", type=int, default=8074)
    args = parser.parse_args()

    project = args.project if args.project.is_absolute() else ROOT / args.project
    character_path = args.character or project / "character.json"
    rig_path = args.mini_rig or project / "mini_rig.json"
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    character = load_json(character_path)
    rig = load_json(rig_path, default=default_mini_rig())
    inspector = Inspector(project.resolve(), character, rig)

    influence = inspector.influence_rows()
    chains = inspector.part_chain_rows()
    junctions = inspector.junction_rows()
    write_csv(out_dir / "parameter_influence.csv", influence)
    write_csv(out_dir / "part_chain.csv", chains)
    write_csv(out_dir / "junction_risk_scores.csv", junctions)
    tooling = write_graph(out_dir, inspector, influence)
    dynamic = run_dynamic(project.resolve(), out_dir, character, args.renderer, args.port) if args.dynamic else None
    context = ai_context(inspector, influence, chains, junctions, dynamic)
    write_json(out_dir / "ai_rig_context.json", context)
    write_json(out_dir / "summary.json", {"generated_at": now_iso(), "project": rel(project), "outputs": {name: rel(out_dir / name) for name in ["rig_graph.dot", "parameter_influence.csv", "part_chain.csv", "junction_risk_scores.csv", "ai_rig_context.json", "summary.md"]}, "tooling": tooling})
    write_summary(out_dir / "summary.md", context, tooling, junctions)
    print(json.dumps({"ok": True, "out_dir": str(out_dir), "counts": context["counts"], "dynamic": bool(dynamic)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

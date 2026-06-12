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
from lib.vtube_image import bbox_contact, bbox_gap  # noqa: E402
from lib.vtube_io import ROOT, load_json, now_iso, rel, write_json  # noqa: E402
from lib.vtube_proc import terminate, wait_for_server  # noqa: E402
from mini_cubism_preview_server import default_mini_rig  # noqa: E402
PLAYWRIGHT = ROOT / "experiments/live2d-strong-model-pattern-001/probe_sandbox/strong20/Samples/TypeScript/Demo/node_modules/playwright"
NODE_DYNAMIC_TEMPLATE = ROOT / "scripts/templates/rig_inspector_dynamic_runner.js"
INTERESTING_GROUPS = ("neck", "body", "head", "hair", "shoulder", "clothes", "cloth")
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
    def resolve_parts(self, queries: list[str]) -> list[str]:
        out: list[str] = []
        for query in queries:
            if query in self.parts:
                out.append(query)
            else:
                out.extend(pid for pid in sorted(self.parts) if query.lower() in pid.lower())
        return sorted(dict.fromkeys(out))
    def param_ids_for_parts(self, part_ids: list[str]) -> set[str]:
        return {pid for part_id in part_ids for pid in self.parameters if self.part_vector_for_param(part_id, pid) != (0, 0, 0, 0, 0)}
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
def dynamic_tiles(canvas: list[int], parts: list[dict[str, Any]] | None = None) -> list[dict[str, int]]:
    width, height = int(canvas[0]), int(canvas[1])
    tiles = []
    for y in (0.28, 0.42, 0.56, 0.70):
        for x in (0.32, 0.44, 0.56, 0.68):
            tiles.append({"x": max(0, int(width * x) - 32), "y": max(0, int(height * y) - 32), "w": 64, "h": 64})
    # 고정 격자는 소형 부위(눈·입·눈썹)와 평탄 영역 변화를 놓친다 (003 실측: 해시는 전부
    # 변하는데 Δ=0 보고) — 파라미터 영향 파트의 bbox 중심 타일을 추가
    seen: set[tuple[int, int]] = set()
    for part in parts or []:
        pid = str(part.get("id", "")).lower()
        if not any(k in pid for k in ("eye", "iris", "mouth", "brow", "neck", "hair", "shoulder", "clothes", "accent", "expr")):
            continue
        x, y, w, h = part.get("bbox", [0, 0, 0, 0])
        if w <= 4:
            continue
        # 004 실측: 중심 1점은 빈 중앙(볼터치 좌/우 쌍의 bbox 중심 = 콧등)과 끝점 변형
        # (MouthForm 입꼬리 — 중앙은 의도적 고정)을 놓친다 → 가로 분할점 + 입꼬리 끝점 추가
        points = [(0.5, 0.5)]
        if w > 120:
            points += [(0.25, 0.5), (0.75, 0.5)]
        if "mouth" in pid:
            points += [(0.04, 0.5), (0.96, 0.5)]
        for fx, fy in points:
            cx, cy = int(x + w * fx), int(y + h * fy)
            key = (cx // 48, cy // 48)
            if key in seen:
                continue
            seen.add(key)
            tiles.append({"x": max(0, cx - 32), "y": max(0, cy - 32), "w": 64, "h": 64})
    return tiles[:64]
def run_dynamic(project: Path, out_dir: Path, character: dict[str, Any], renderer: str, port: int, sample_limit: int | None = None, priority_params: set[str] | None = None) -> dict[str, Any]:
    captures = out_dir / "dynamic_captures"
    captures.mkdir(parents=True, exist_ok=True)
    defaults = {p["id"]: p.get("default", 0) for p in character.get("parameters", [])}
    # 물리 소유 파라미터(스프링 output): 직접 주입은 물리 티커가 한 프레임 내 덮어써서
    # "무반응"으로 오판된다 (BODY-SWAY-001 소유권) — 입력 채널(Track*) 상태로만 측정.
    physics_owned = sorted({p.get("output_parameter") for p in character.get("physics_profiles", []) if p.get("output_parameter")})
    states = []
    for param in character.get("parameters", []):
        if param["id"] in physics_owned:
            continue
        values = [param.get("min"), param.get("max")]
        for label, value in zip(("min", "max"), values):
            if value is not None and float(value) != float(param.get("default", 0)):
                states.append({"parameter_id": param["id"], "label": label, "value": value})
    if sample_limit is not None:
        priority_params = priority_params or set()
        states = sorted(states, key=lambda s: (s["parameter_id"] not in priority_params, s["parameter_id"], s["label"]))[:max(0, sample_limit)]
    config_path = out_dir / "dynamic_config.json"
    raw_path = out_dir / "dynamic_motion_report.json"
    runner_path = out_dir / "dynamic_runner.js"
    runner_path.write_text(NODE_DYNAMIC_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
    write_json(config_path, {
        "playwright": str(PLAYWRIGHT),
        "base": f"http://127.0.0.1:{port}/",
        "query": "?renderer=pixi" if renderer == "pixi" else "",
        "renderer": renderer,
        "launch_args": ["--use-angle=swiftshader"] if renderer == "pixi" else [],
        "defaults": defaults,
        "states": states,
        "tiles": dynamic_tiles(character.get("canvas_size") or [2048, 2048], character.get("parts")),
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
    report = load_json(raw_path)
    report["dynamic_sample_limit"] = sample_limit
    report["configured_states"] = len(states)
    report["physics_owned_parameters"] = physics_owned  # 직접 측정 제외 — Track* 입력 채널로 검증
    write_json(raw_path, report)
    return report
def focus_report(inspector: Inspector, focus_parts: list[str], influence: list[dict[str, Any]], chains: list[dict[str, Any]], junctions: list[dict[str, Any]]) -> dict[str, Any]:
    focus_set = set(focus_parts)
    params = inspector.param_ids_for_parts(focus_parts)
    return {
        "queries_resolved": focus_parts,
        "parameters": [row for row in influence if row["parameter_id"] in params],
        "part_chains": [row for row in chains if row["part_id"] in focus_set],
        "junction_scores": [row for row in junctions if row["part_a"] in focus_set or row["part_b"] in focus_set],
        "related_parts": sorted({row["part_a"] if row["part_b"] in focus_set else row["part_b"] for row in junctions if row["part_a"] in focus_set or row["part_b"] in focus_set}),
    }
def compare_report(left: dict[str, Any], right: dict[str, Any], left_j: list[dict[str, Any]], right_j: list[dict[str, Any]]) -> dict[str, Any]:
    def ids(ctx: dict[str, Any], key: str) -> set[str]:
        return {item["id"] for item in ctx[key]}
    def pair_key(row: dict[str, Any]) -> str:
        return "|".join(sorted([row["part_a"], row["part_b"]]))
    right_by_pair = {pair_key(row): row for row in right_j}
    deltas = []
    for key, row in {pair_key(row): row for row in left_j}.items():
        other = right_by_pair.get(key)
        if other:
            deltas.append({"pair": key, "left_score": row["score"], "right_score": other["score"], "delta": round(row["score"] - other["score"], 3)})
    return {
        "left_project": left["project"],
        "right_project": right["project"],
        "count_delta": {k: left["counts"].get(k, 0) - right["counts"].get(k, 0) for k in sorted(set(left["counts"]) | set(right["counts"]))},
        "parts_added_in_left": sorted(ids(left, "parts") - ids(right, "parts")),
        "parts_missing_in_left": sorted(ids(right, "parts") - ids(left, "parts")),
        "parameters_added_in_left": sorted(ids(left, "parameters") - ids(right, "parameters")),
        "parameters_missing_in_left": sorted(ids(right, "parameters") - ids(left, "parameters")),
        "junction_score_deltas": sorted(deltas, key=lambda row: abs(row["delta"]), reverse=True)[:80],
    }
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
def write_summary(path: Path, context: dict[str, Any], tooling: dict[str, Any], junctions: list[dict[str, Any]], focus: dict[str, Any] | None = None, compare: dict[str, Any] | None = None) -> None:
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
        f"- Focus parts: `{len(focus.get('queries_resolved', [])) if focus else 0}`",
        f"- Compare target: `{compare.get('right_project') if compare else ''}`",
        "",
        "## Highest Junction Scores",
        "",
        "| score | part_a | part_b | bbox_gap | contact_length |",
        "|---:|---|---|---:|---:|",
    ]
    for row in junctions[:20]:
        lines.append(f"| {row['score']} | `{row['part_a']}` | `{row['part_b']}` | {row['bbox_gap']} | {row['contact_length']} |")
    if focus:
        lines += ["", "## Focus Parts", "", "| part_id | chain | direct_bindings | physics_profiles |", "|---|---|---:|---:|"]
        for row in focus["part_chains"]:
            lines.append(f"| `{row['part_id']}` | `{row['deformer_chain']}` | {row['direct_binding_count']} | {row['physics_profile_count']} |")
    if compare:
        lines += ["", "## Compare Counts", "", "| item | left_minus_right |", "|---|---:|"]
        for key, value in compare["count_delta"].items():
            lines.append(f"| {key} | {value} |")
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
    parser.add_argument("--dynamic-sample-limit", type=int, default=None)
    parser.add_argument("--focus-part", action="append", default=[])
    parser.add_argument("--compare", type=Path, default=None, help="Compare --project against another project directory.")
    parser.add_argument("--fail-on-dead", action="store_true", help="동적 스윕에서 무반응 상태(Δ<0.05) 발견 시 비정상 종료 — 파이프라인 P5 게이트용")
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
    focus_parts = inspector.resolve_parts(args.focus_part)
    focus = focus_report(inspector, focus_parts, influence, chains, junctions) if focus_parts else None
    write_csv(out_dir / "parameter_influence.csv", influence)
    write_csv(out_dir / "part_chain.csv", chains)
    write_csv(out_dir / "junction_risk_scores.csv", junctions)
    if focus:
        write_json(out_dir / "focus_part_report.json", focus)
        write_csv(out_dir / "focus_junction_scores.csv", focus["junction_scores"])
    tooling = write_graph(out_dir, inspector, influence)
    dynamic = run_dynamic(project.resolve(), out_dir, character, args.renderer, args.port, args.dynamic_sample_limit, inspector.param_ids_for_parts(focus_parts)) if args.dynamic else None
    context = ai_context(inspector, influence, chains, junctions, dynamic)
    context["focus_parts"] = focus_parts
    context["dynamic_sample_limit"] = args.dynamic_sample_limit
    compare = None
    if args.compare:
        right_project = args.compare if args.compare.is_absolute() else ROOT / args.compare
        right = Inspector(right_project.resolve(), load_json(right_project / "character.json"), load_json(right_project / "mini_rig.json", default=default_mini_rig()))
        right_influence, right_chains, right_junctions = right.influence_rows(), right.part_chain_rows(), right.junction_rows()
        right_context = ai_context(right, right_influence, right_chains, right_junctions, None)
        compare = compare_report(context, right_context, junctions, right_junctions)
        write_json(out_dir / "compare_report.json", compare)
        write_csv(out_dir / "compare_junction_score_deltas.csv", compare["junction_score_deltas"])
    write_json(out_dir / "ai_rig_context.json", context)
    output_names = ["rig_graph.dot", "parameter_influence.csv", "part_chain.csv", "junction_risk_scores.csv", "ai_rig_context.json", "summary.md"]
    if focus:
        output_names += ["focus_part_report.json", "focus_junction_scores.csv"]
    if compare:
        output_names += ["compare_report.json", "compare_junction_score_deltas.csv"]
    if dynamic:
        output_names += ["dynamic_motion_report.json"]
    write_json(out_dir / "summary.json", {"generated_at": now_iso(), "project": rel(project), "outputs": {name: rel(out_dir / name) for name in output_names}, "tooling": tooling})
    write_summary(out_dir / "summary.md", context, tooling, junctions, focus, compare)
    # 무반응 판정: 타일별 최대 델타 기준 — 전 타일 평균은 타일 수에 희석된다 (004 실측:
    # 볼터치/눈물/땀은 커버 타일 0개로 Δ=0, 타일을 늘리면 BrowLY 0.064가 희석 사망). 구 리포트 폴백 유지.
    def is_dead(s: dict) -> bool:
        if "pixel_delta_tile_max" in s:
            return s["pixel_delta_tile_max"] < 0.5
        return s.get("pixel_delta_mean_abs", 1) < 0.05
    dead = [f"{s['parameter_id']}/{s['label']}" for s in (dynamic or {}).get("states", []) if is_dead(s)]
    print(json.dumps({"ok": not (args.fail_on_dead and dead), "out_dir": str(out_dir), "counts": context["counts"], "dynamic": bool(dynamic), "dead_states": dead, "focus_parts": focus_parts, "compare": bool(compare)}, ensure_ascii=False, indent=2))
    return 1 if (args.fail_on_dead and dead) else 0
if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Summarize Live2D part success patterns and Cubism v2 tier specs."""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "live2d-strong-model-pattern-001"
DEFAULT_MANIFEST = EXPERIMENT / "reports" / "pilot_render_manifest.json"
DEFAULT_RUNTIME = EXPERIMENT / "reports" / "pilot_runtime_probe_report.json"

CATEGORIES = ("eye", "mouth", "hair", "body_angle", "arm", "physics", "mask_pose_expression", "psd_layering")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--runtime-report", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--out-dir", type=Path, default=EXPERIMENT)
    parser.add_argument("--skip-cmo3-inspector", action="store_true")
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


def cat_for_param(param_id: str) -> str | None:
    v = param_id.lower()
    if "eye" in v or "brow" in v or "cheek" in v:
        return "eye"
    if "mouth" in v or v in {"parama", "parami", "paramu", "parame", "paramo"}:
        return "mouth"
    if "hair" in v or "kami" in v:
        return "hair"
    if "anglex" in v or "angley" in v or "anglez" in v or "bodyangle" in v or v in {"paramallx", "paramally", "paramallrotate"}:
        return "body_angle"
    if "arm" in v or "hand" in v or "shoulder" in v:
        return "arm"
    return None


def cat_for_name(name: str) -> str | None:
    v = name.lower()
    if any(token in v for token in ("eye", "눈", "눈썹", "brow", "まゆ")):
        return "eye"
    if any(token in v for token in ("mouth", "입", "口")):
        return "mouth"
    if any(token in v for token in ("hair", "머리", "髪", "kami")):
        return "hair"
    if any(token in v for token in ("body", "몸", "목", "neck", "torso")):
        return "body_angle"
    if any(token in v for token in ("arm", "hand", "shoulder", "팔", "손")):
        return "arm"
    return None


def motion_parameter_ids(model: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for item in model["local_paths"].get("motion3_json", []):
        path = ROOT / item
        if not path.exists():
            continue
        try:
            data = load_json(path)
        except Exception:
            continue
        for curve in data.get("Curves", []):
            if curve.get("Target") == "Parameter" and curve.get("Id"):
                out.add(curve["Id"])
    return out


def physics_summary(model: dict[str, Any]) -> dict[str, Any]:
    path_value = model["local_paths"].get("physics3_json")
    if not path_value:
        return {"present": False, "group_count": 0, "input_ids": [], "output_ids": []}
    path = ROOT / path_value
    if not path.exists():
        return {"present": False, "group_count": 0, "input_ids": [], "output_ids": []}
    data = load_json(path)
    input_ids = set()
    output_ids = set()
    settings = data.get("PhysicsSettings", [])
    for setting in settings:
        for entry in setting.get("Input", []):
            source = entry.get("Source", {})
            if source.get("Id"):
                input_ids.add(source["Id"])
        for entry in setting.get("Output", []):
            dest = entry.get("Destination", {})
            if dest.get("Id"):
                output_ids.add(dest["Id"])
    return {
        "present": True,
        "group_count": len(settings),
        "input_ids": sorted(input_ids),
        "output_ids": sorted(output_ids),
    }


def run_cmo3_inspector(model: dict[str, Any], out_dir: Path, skip: bool) -> dict[str, Any]:
    cmo3_value = model["local_paths"].get("cmo3")
    if not cmo3_value:
        return {"status": "MISSING", "error": "no cmo3 path"}
    cmo3 = ROOT / cmo3_value
    model_dir = out_dir / "cmo3" / model["safe_id"]
    out_json = model_dir / "cmo3_structure_report.json"
    out_md = model_dir / "cmo3_structure_report.md"
    if not skip:
        subprocess.run(
            [
                "node",
                str(ROOT / "scripts" / "inspect_cmo3_structure.mjs"),
                "--cmo3",
                str(cmo3),
                "--out-json",
                str(out_json),
                "--out-md",
                str(out_md),
            ],
            cwd=ROOT,
            check=True,
        )
    if out_json.exists():
        report = load_json(out_json)
        return {
            "status": report.get("status"),
            "json": rel(out_json),
            "markdown": rel(out_md),
            "counts": {
                "art_meshes": report.get("art_meshes", {}).get("count", 0),
                "parts": report.get("parts", {}).get("count", 0),
                "parameters": report.get("parameters", {}).get("count", 0),
                "warp_deformers": report.get("deformers", {}).get("warp_count", 0),
                "rotation_deformers": report.get("deformers", {}).get("rotation_count", 0),
                "keyform_bindings": report.get("keyforms", {}).get("binding_count", 0),
                "keyform_grids": report.get("keyforms", {}).get("grid_count", 0),
                "glue": report.get("counts", {}).get("CGlueSource", {}).get("definitions", 0),
            },
            "parameter_ids": report.get("parameters", {}).get("ids", []),
            "part_names": report.get("parts", {}).get("names", []),
            "warp_names": report.get("deformers", {}).get("warp_names", []),
            "rotation_names": report.get("deformers", {}).get("rotation_names", []),
        }
    return {"status": "MISSING", "error": f"missing inspector output: {out_json}"}


def model_pattern(model: dict[str, Any], runtime_item: dict[str, Any] | None, cmo3: dict[str, Any]) -> dict[str, Any]:
    params = cmo3.get("parameter_ids", [])
    parts = cmo3.get("part_names", [])
    warp_names = cmo3.get("warp_names", [])
    rotation_names = cmo3.get("rotation_names", [])
    motion_ids = motion_parameter_ids(model)
    physics = physics_summary(model)
    by_category: dict[str, dict[str, Any]] = {}
    for category in CATEGORIES:
        by_category[category] = {
            "parameter_ids": sorted([pid for pid in params if cat_for_param(pid) == category]),
            "motion_parameter_ids": sorted([pid for pid in motion_ids if cat_for_param(pid) == category]),
            "part_names": sorted([name for name in parts if cat_for_name(name) == category]),
            "warp_deformer_names": sorted([name for name in warp_names if cat_for_name(name) == category]),
            "rotation_deformer_names": sorted([name for name in rotation_names if cat_for_name(name) == category]),
        }
    by_category["physics"] = {
        "group_count": physics["group_count"],
        "input_ids": physics["input_ids"],
        "output_ids": physics["output_ids"],
        "output_categories": sorted({cat_for_param(pid) or "other" for pid in physics["output_ids"]}),
    }
    by_category["mask_pose_expression"] = {
        "has_pose": bool(model["local_paths"].get("pose3_json")),
        "expression_count": len(model["local_paths"].get("exp3_json", [])),
        "glue_count": cmo3.get("counts", {}).get("glue", 0),
    }
    by_category["psd_layering"] = {
        "psd_count": len(model["local_paths"].get("psd", [])),
        "has_psd": bool(model["local_paths"].get("psd", [])),
    }
    return {
        "id": model["id"],
        "safe_id": model["safe_id"],
        "name": model["name"],
        "profile_key": model.get("official_profile_key"),
        "learning_target": model.get("expected_learning_target"),
        "runtime_status": runtime_item.get("status") if runtime_item else "NOT_RUN",
        "cmo3_status": cmo3.get("status"),
        "structure_counts": cmo3.get("counts", {}),
        "categories": by_category,
        "evidence": {
            "runtime_capture_dir": rel(EXPERIMENT / "captures" / model["safe_id"]),
            "cmo3_report": cmo3.get("json"),
        },
    }


def numeric_summary(values: list[int]) -> dict[str, float | int | None]:
    if not values:
        return {"min": None, "median": None, "max": None, "mean": None}
    return {
        "min": min(values),
        "median": statistics.median(values),
        "max": max(values),
        "mean": round(statistics.mean(values), 2),
    }


def build_patterns(patterns: list[dict[str, Any]]) -> dict[str, Any]:
    sections = {}
    for category in CATEGORIES:
        param_counts = []
        motion_counts = []
        part_counts = []
        deformer_counts = []
        examples = []
        for pattern in patterns:
            cat = pattern["categories"].get(category, {})
            if category == "physics":
                param_counts.append(int(cat.get("group_count", 0)))
                examples.append({
                    "model": pattern["name"],
                    "physics_groups": cat.get("group_count", 0),
                    "outputs": cat.get("output_ids", [])[:12],
                })
                continue
            if category in {"mask_pose_expression", "psd_layering"}:
                examples.append({"model": pattern["name"], **cat})
                continue
            param_counts.append(len(cat.get("parameter_ids", [])))
            motion_counts.append(len(cat.get("motion_parameter_ids", [])))
            part_counts.append(len(cat.get("part_names", [])))
            deformer_counts.append(len(cat.get("warp_deformer_names", [])) + len(cat.get("rotation_deformer_names", [])))
            examples.append({
                "model": pattern["name"],
                "params": cat.get("parameter_ids", [])[:12],
                "motion_params": cat.get("motion_parameter_ids", [])[:12],
                "parts": cat.get("part_names", [])[:8],
            })
        sections[category] = {
            "parameter_or_group_count": numeric_summary(param_counts),
            "motion_parameter_count": numeric_summary(motion_counts),
            "part_count": numeric_summary(part_counts),
            "named_deformer_count": numeric_summary(deformer_counts),
            "examples": examples[:8],
            "decision": category_decision(category),
        }
    return sections


def category_decision(category: str) -> str:
    return {
        "eye": "Use separate eye open/smile/eyeball/brow parameters; verify neutral and extreme eye screenshots.",
        "mouth": "Use MouthOpen/Form plus vowel/lip-sync references when available; Kei is the mouth baseline.",
        "hair": "Use front/side/back hair parameters and physics outputs; Miku/Hiyori are primary hair baselines.",
        "body_angle": "Use AngleX/Y/Z and BodyAngleX/Y/Z as standard motion axes; avoid treating extreme sweep as natural pose.",
        "arm": "Keep optional for v2_min, but include arm/hand/shoulder variants in v2_standard when the design needs gestures.",
        "physics": "Require physics groups for hair/body secondary motion; use output category coverage as the main quality signal.",
        "mask_pose_expression": "Use mask/pose/expression only when design needs it; do not force rich-sample complexity into v2_min.",
        "psd_layering": "Use PSD/material split examples as taxonomy guidance only; do not reuse official art assets.",
    }[category]


def tier_spec(patterns: list[dict[str, Any]], sections: dict[str, Any]) -> dict[str, Any]:
    counts = [p["structure_counts"] for p in patterns if p.get("cmo3_status") in {"PASS", "WARN"}]
    observed = {
        key: numeric_summary([int(c.get(key, 0)) for c in counts])
        for key in ("art_meshes", "parts", "parameters", "warp_deformers", "rotation_deformers", "keyform_bindings", "glue")
    }
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "observed_reference_ranges": observed,
        "tiers": {
            "v2_min": {
                "part_count": "20-25",
                "goal": "pass deformer/keyform/physics gate",
                "minimums": {"parameters": 12, "warp_deformers": 8, "keyform_bindings": 20, "physics_groups": 2},
                "usage": "technical gate only; not final production target",
            },
            "v2_standard": {
                "part_count": "50-70",
                "goal": "natural eye/mouth/hair/body-angle motion",
                "minimums": {"parameters": 25, "warp_deformers": 35, "rotation_deformers": 8, "keyform_bindings": 120, "physics_groups": 4},
                "usage": "first production candidate default",
            },
            "v2_rich": {
                "part_count": "90+",
                "goal": "official-core-sample-like expression richness",
                "minimums": {"parameters": 50, "warp_deformers": 60, "rotation_deformers": 20, "keyform_bindings": 220, "physics_groups": 8},
                "recommended": "at least two of mask/pose/expression when the design needs rich interactions",
            },
        },
        "category_decisions": {category: section["decision"] for category, section in sections.items()},
        "default_choice": "v2_standard",
    }


def write_patterns_md(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Live2D Part Success Patterns",
        "",
        f"- kind: `{report['kind']}`",
        f"- model_count: `{report['summary']['model_count']}`",
        f"- cmo3_pass_or_warn: `{report['summary']['cmo3_pass_or_warn']}`",
        "",
    ]
    for category, section in report["sections"].items():
        lines.extend([
            f"## {category}",
            "",
            f"- decision: {section['decision']}",
            f"- parameter_or_group_count: `{section['parameter_or_group_count']}`",
            f"- motion_parameter_count: `{section['motion_parameter_count']}`",
            f"- part_count: `{section['part_count']}`",
            "",
            "| Model | Example |",
            "|---|---|",
        ])
        for example in section["examples"][:5]:
            lines.append(f"| `{example.get('model')}` | `{json.dumps(example, ensure_ascii=False)[:180]}` |")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_tier_md(spec: dict[str, Any], path: Path) -> None:
    lines = [
        "# Cubism v2 Tier Spec",
        "",
        f"- default_choice: `{spec['default_choice']}`",
        "- source: official sample success-pattern analysis; not source-model reconstruction",
        "",
        "## Observed Reference Ranges",
        "",
        "| Metric | Range |",
        "|---|---|",
    ]
    for key, value in spec["observed_reference_ranges"].items():
        lines.append(f"| {key} | `{value}` |")
    lines.extend(["", "## Tiers", ""])
    for tier, data in spec["tiers"].items():
        lines.extend([
            f"### {tier}",
            "",
            f"- part_count: `{data['part_count']}`",
            f"- goal: {data['goal']}",
            f"- minimums: `{data['minimums']}`",
            f"- usage: {data.get('usage', data.get('recommended', ''))}",
            "",
        ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    manifest = load_json(args.manifest)
    runtime = load_json(args.runtime_report) if args.runtime_report.exists() else {"models": []}
    runtime_by_id = {item.get("id"): item for item in runtime.get("models", [])}
    cmo3_items = []
    patterns = []
    for model in manifest["models"]:
        cmo3 = run_cmo3_inspector(model, args.out_dir, args.skip_cmo3_inspector)
        cmo3_items.append({"id": model["id"], "name": model["name"], **cmo3})
        patterns.append(model_pattern(model, runtime_by_id.get(model["id"]), cmo3))

    batch = {
        "schema_version": 1,
        "kind": manifest["kind"],
        "summary": {
            "model_count": len(cmo3_items),
            "cmo3_pass_or_warn": sum(1 for item in cmo3_items if item.get("status") in {"PASS", "WARN"}),
            "cmo3_fail_or_missing": sum(1 for item in cmo3_items if item.get("status") not in {"PASS", "WARN"}),
        },
        "models": cmo3_items,
    }
    write_json(args.out_dir / "reports" / "cmo3_structure_batch_summary.json", batch)
    batch_lines = [
        "# CMO3 Structure Batch Summary",
        "",
        f"- kind: `{batch['kind']}`",
        f"- pass_or_warn/fail: `{batch['summary']['cmo3_pass_or_warn']}/{batch['summary']['cmo3_fail_or_missing']}`",
        "",
        "| Model | Status | Counts | Report |",
        "|---|---:|---|---|",
    ]
    for item in cmo3_items:
        batch_lines.append(f"| `{item['name']}` | {item.get('status')} | `{item.get('counts')}` | `{item.get('json')}` |")
    (args.out_dir / "reports" / "cmo3_structure_batch_summary.md").write_text("\n".join(batch_lines) + "\n", encoding="utf-8")

    sections = build_patterns(patterns)
    pattern_report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "kind": manifest["kind"],
        "summary": {
            "model_count": len(patterns),
            "cmo3_pass_or_warn": batch["summary"]["cmo3_pass_or_warn"],
        },
        "sections": sections,
        "models": patterns,
        "policy": "local evidence only; do not reuse official art or textures",
    }
    spec = tier_spec(patterns, sections)
    write_json(args.out_dir / "reports" / "part_success_patterns.json", pattern_report)
    write_patterns_md(pattern_report, args.out_dir / "reports" / "part_success_patterns.md")
    write_json(args.out_dir / "reports" / "cubism_v2_tier_spec.json", spec)
    write_tier_md(spec, args.out_dir / "reports" / "cubism_v2_tier_spec.md")
    print(json.dumps({
        "kind": manifest["kind"],
        "patterns": rel(args.out_dir / "reports" / "part_success_patterns.json"),
        "tier_spec": rel(args.out_dir / "reports" / "cubism_v2_tier_spec.json"),
        "cmo3_summary": batch["summary"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

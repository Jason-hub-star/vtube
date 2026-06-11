#!/usr/bin/env python3
"""Build detailed deformer hierarchy tables for all FULL_STRUCTURE CMO3 references."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_EXP = ROOT / "experiments" / "reference-model-structure-001"
DEFAULT_CATALOG = REFERENCE_EXP / "catalog.official_combined.json"
DEFAULT_ANALYSIS_DIR = REFERENCE_EXP / "official_combined_analysis" / "models"
DEFAULT_OUT_DIR = REFERENCE_EXP / "reports"


PARAM_DESC_TO_ID = {
    "PARAM_ANGLE_X": "ParamAngleX",
    "PARAM_ANGLE_Y": "ParamAngleY",
    "PARAM_ANGLE_Z": "ParamAngleZ",
    "PARAM_BODY_ANGLE_X": "ParamBodyAngleX",
    "PARAM_BODY_ANGLE_Y": "ParamBodyAngleY",
    "PARAM_BODY_ANGLE_Z": "ParamBodyAngleZ",
    "PARAM_EYE_L_OPEN": "ParamEyeLOpen",
    "PARAM_EYE_R_OPEN": "ParamEyeROpen",
    "PARAM_EYE_BALL_X": "ParamEyeBallX",
    "PARAM_EYE_BALL_Y": "ParamEyeBallY",
    "PARAM_MOUTH_FORM": "ParamMouthForm",
    "PARAM_MOUTH_OPEN_Y": "ParamMouthOpenY",
    "PARAM_BREATH": "ParamBreath",
    "PARAM_HAIR_FRONT": "ParamHairFront",
    "PARAM_HAIR_SIDE": "ParamHairSide",
    "PARAM_HAIR_BACK": "ParamHairBack",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--analysis-dir", type=Path, default=DEFAULT_ANALYSIS_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
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


def categorize_name(name: str | None, params: list[str]) -> str:
    text = f"{name or ''} {' '.join(params)}".lower()
    if any(k in text for k in ("eye", "目", "まつげ", "eyeball", "瞳", "白目")):
        return "eye"
    if any(k in text for k in ("mouth", "口", "lip", "teeth", "tongue")):
        return "mouth"
    if any(k in text for k in ("hair", "髪", "前髪", "横髪", "後ろ髪", "kami")):
        return "hair"
    if any(k in text for k in ("body", "体", "胸", "上半身", "呼吸", "breath", "bust")):
        return "body"
    if any(k in text for k in ("arm", "hand", "shoulder", "腕", "手", "肩")):
        return "arm"
    if any(k in text for k in ("brow", "眉")):
        return "brow"
    if any(k in text for k in ("face", "顔", "鼻", "ear", "耳", "neck", "首")):
        return "face"
    if any(k in text for k in ("cloth", "服", "制服", "スカート", "scarf", "リボン", "衣")):
        return "clothing"
    if any(k in text for k in ("effect", "涙", "tear", "照れ")):
        return "effect"
    return "other"


def normalize_param(description: str | None) -> str | None:
    if not description:
        return None
    return PARAM_DESC_TO_ID.get(description, description)


def safe_sources(report: dict[str, Any], key: str) -> list[dict[str, Any]]:
    return report.get(key, {}).get("sources", []) or []


def build_grid_bindings(report: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for binding in report.get("keyforms", {}).get("bindings", []) or []:
        grid = binding.get("gridRef")
        if grid:
            out[grid].append(binding)
    return out


def source_name(source: dict[str, Any]) -> str:
    return source.get("localName") or source.get("idstr") or source.get("xsId") or "unnamed"


def build_model_rows(entry: dict[str, Any], report_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    report = load_json(report_path)
    warp = report.get("deformers", {}).get("warp_sources", []) or []
    rotation = report.get("deformers", {}).get("rotation_sources", []) or []
    art_meshes = report.get("art_meshes", {}).get("sources", []) or []
    grid_bindings = build_grid_bindings(report)

    nodes = []
    by_guid = {}
    by_source_ref = {}
    for source in warp:
        node = {"type": "warp", **source}
        nodes.append(node)
        if source.get("sourceGuidRef"):
            by_guid[source["sourceGuidRef"]] = node
        if source.get("xsId"):
            by_source_ref[source["xsId"]] = node
    for source in rotation:
        node = {"type": "rotation", **source}
        nodes.append(node)
        if source.get("sourceGuidRef"):
            by_guid[source["sourceGuidRef"]] = node
        if source.get("xsId"):
            by_source_ref[source["xsId"]] = node

    child_deformers: dict[str, list[dict[str, Any]]] = defaultdict(list)
    child_art_meshes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for node in nodes:
        parent = node.get("targetDeformerRef")
        if parent:
            child_deformers[parent].append(node)
    for art in art_meshes:
        parent = art.get("targetDeformerRef")
        if parent:
            child_art_meshes[parent].append(art)

    def depth_for(node: dict[str, Any]) -> int:
        depth = 0
        seen = set()
        parent = node.get("targetDeformerRef")
        while parent and parent in by_guid and parent not in seen:
            seen.add(parent)
            depth += 1
            parent = by_guid[parent].get("targetDeformerRef")
        return depth

    rows = []
    for node in nodes:
        bindings = grid_bindings.get(node.get("keyformGridRef"), [])
        params = [normalize_param(binding.get("description")) for binding in bindings]
        params = sorted({param for param in params if param})
        node_guid = node.get("sourceGuidRef") or node.get("xsId")
        child_def = child_deformers.get(node_guid, [])
        child_art = child_art_meshes.get(node_guid, [])
        parent_node = by_guid.get(node.get("targetDeformerRef"))
        row = {
            "model_id": entry.get("id"),
            "model_name": entry.get("name"),
            "deformer_source_ref": node.get("xsId"),
            "deformer_guid_ref": node.get("sourceGuidRef"),
            "deformer_ref": node_guid,
            "deformer_type": node.get("type"),
            "deformer_name": source_name(node),
            "category": categorize_name(source_name(node), params),
            "depth": depth_for(node),
            "parent_deformer_ref": node.get("targetDeformerRef") if parent_node else None,
            "parent_deformer_name": source_name(parent_node) if parent_node else None,
            "parent_part_ref": node.get("parentPartRef"),
            "grid_ref": node.get("keyformGridRef"),
            "keyform_count": node.get("keyformCount") or 0,
            "binding_count": len(bindings),
            "bound_parameters": params,
            "child_deformer_count": len(child_def),
            "child_artmesh_count": len(child_art),
            "child_deformer_samples": [source_name(item) for item in child_def[:8]],
            "child_artmesh_samples": [source_name(item) for item in child_art[:8]],
        }
        rows.append(row)

    category_counts = Counter(row["category"] for row in rows)
    depths = [row["depth"] for row in rows]
    keyformed = [row for row in rows if row["binding_count"] or row["keyform_count"]]
    summary = {
        "model_id": entry.get("id"),
        "model_name": entry.get("name"),
        "report": rel(report_path),
        "warp_count": len(warp),
        "rotation_count": len(rotation),
        "deformer_count": len(rows),
        "keyformed_deformer_count": len(keyformed),
        "max_depth": max(depths) if depths else 0,
        "median_depth": median(depths) if depths else 0,
        "deformer_guid_count": sum(1 for node in nodes if node.get("sourceGuidRef")),
        "category_counts": dict(sorted(category_counts.items())),
    }
    return rows, summary


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    catalog = load_json(args.catalog)
    full = [entry for entry in catalog.get("models", []) if entry.get("analysis_mode") == "FULL_STRUCTURE"]
    all_rows = []
    summaries = []
    missing_reports = []
    for entry in full:
        report_path = args.analysis_dir / entry["id"] / "cmo3_structure_report.json"
        if not report_path.exists():
            missing_reports.append({"id": entry["id"], "expected_report": rel(report_path)})
            continue
        rows, summary = build_model_rows(entry, report_path)
        all_rows.extend(rows)
        summaries.append(summary)

    category_counts = Counter(row["category"] for row in all_rows)
    type_counts = Counter(row["deformer_type"] for row in all_rows)
    depths = [row["depth"] for row in all_rows]
    keyform_counts = [row["keyform_count"] for row in all_rows]
    child_art_counts = [row["child_artmesh_count"] for row in all_rows]
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "kind": "all34_cmo3_deformer_hierarchy_table",
        "status": "PASS" if len(summaries) == 34 and not missing_reports else "PARTIAL",
        "inputs": {
            "catalog": rel(args.catalog),
            "analysis_dir": rel(args.analysis_dir),
        },
        "summary": {
            "full_structure_expected": len(full),
            "model_count": len(summaries),
            "missing_report_count": len(missing_reports),
            "deformer_row_count": len(all_rows),
            "type_counts": dict(sorted(type_counts.items())),
            "category_counts": dict(sorted(category_counts.items())),
            "max_depth": max(depths) if depths else 0,
            "median_depth": median(depths) if depths else 0,
            "mean_keyform_count": round(mean(keyform_counts), 3) if keyform_counts else 0,
            "mean_child_artmesh_count": round(mean(child_art_counts), 3) if child_art_counts else 0,
        },
        "production_interpretation": {
            "v2_standard_recommended_chain": [
                "root placement/scale deformer",
                "body angle warp/rotation group",
                "neck/head angle group",
                "face local warp group",
                "eye L/R local warp groups",
                "mouth local warp group",
                "hair front/side/back physics-ready warp groups",
                "simple shoulder/arm rotation groups",
            ],
            "use_for_new_model": "Use rows by category to decide which deformers must exist before CMO3 structure gate; do not copy official art or exact character design.",
        },
        "missing_reports": missing_reports,
        "models": summaries,
        "rows": all_rows,
    }


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# All34 CMO3 Deformer Hierarchy Table",
        "",
        "## Summary",
        "",
        f"- status: `{payload['status']}`",
        f"- model_count: `{payload['summary']['model_count']}` / `{payload['summary']['full_structure_expected']}`",
        f"- deformer rows: `{payload['summary']['deformer_row_count']}`",
        f"- max depth: `{payload['summary']['max_depth']}`",
        f"- median depth: `{payload['summary']['median_depth']}`",
        "",
        "## Category Counts",
        "",
        "| Category | Count |",
        "|---|---:|",
    ]
    for key, value in sorted(payload["summary"]["category_counts"].items()):
        lines.append(f"| {key} | {value} |")
    lines += [
        "",
        "## Model Summary",
        "",
        "| Model | Warp | Rotation | Total | Keyformed | Max Depth | Main Categories |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for model in payload["models"]:
        cats = ", ".join(f"{k}:{v}" for k, v in model["category_counts"].items())
        lines.append(
            f"| `{model['model_name']}` | {model['warp_count']} | {model['rotation_count']} | "
            f"{model['deformer_count']} | {model['keyformed_deformer_count']} | {model['max_depth']} | {cats} |"
        )
    lines += [
        "",
        "## Deformer Rows",
        "",
        "| Model | Type | Depth | Category | Deformer | Parent | Keyforms | Bindings | Parameters | Child Def | Child ArtMesh |",
        "|---|---|---:|---|---|---|---:|---:|---|---:|---:|",
    ]
    for row in payload["rows"]:
        params = ", ".join(row["bound_parameters"][:6])
        lines.append(
            f"| `{row['model_name']}` | {row['deformer_type']} | {row['depth']} | {row['category']} | "
            f"`{row['deformer_name']}` | `{row['parent_deformer_name'] or ''}` | {row['keyform_count']} | "
            f"{row['binding_count']} | {params} | {row['child_deformer_count']} | {row['child_artmesh_count']} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    payload = build_payload(args)
    out_json = args.out_dir / "all34_cmo3_deformer_hierarchy_table.json"
    out_md = args.out_dir / "all34_cmo3_deformer_hierarchy_table.md"
    write_json(out_json, payload)
    write_md(out_md, payload)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "json": rel(out_json),
                "markdown": rel(out_md),
                "summary": payload["summary"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

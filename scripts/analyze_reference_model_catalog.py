#!/usr/bin/env python3
"""Batch-analyze reference Live2D model structure from a catalog.

This tool is intentionally local-only. It never downloads public model assets.
The catalog can list broad public candidates, but only entries with safe
analysis modes and existing local paths are inspected.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = ROOT / "experiments" / "reference-model-structure-001"
ALLOWED_MODES = {"FULL_STRUCTURE", "RUNTIME_ONLY", "METADATA_ONLY"}
LOCAL_PATH_KEYS = {
    "cmo3",
    "moc3",
    "model3_json",
    "physics3_json",
    "motion3_json",
    "cdi3_json",
    "exp3_json",
    "pose3_json",
    "psd",
}
UNSAFE_LICENSE_HINTS = {"UNKNOWN", "UNVERIFIED", "SUSPECTED_REUPLOAD", "UNCLEAR"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalog",
        default=str(DEFAULT_EXPERIMENT / "catalog.json"),
        help="Reference model catalog JSON.",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_EXPERIMENT),
        help="Output experiment directory.",
    )
    parser.add_argument(
        "--skip-cmo3-inspector",
        action="store_true",
        help="Do not run scripts/inspect_cmo3_structure.mjs.",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def resolve_local_path(value: str | None, base: Path) -> Path | None:
    if not value:
        return None
    p = Path(value).expanduser()
    if p.is_absolute():
        return p.resolve()
    candidate = (base / p).resolve()
    if candidate.exists():
        return candidate
    return (ROOT / p).resolve()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_catalog(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, dict) and isinstance(raw.get("models"), list):
        return raw["models"]
    if isinstance(raw, list):
        return raw
    raise ValueError("catalog must be a list or an object with a 'models' list")


def has_path(entry: dict[str, Any], key: str) -> bool:
    local_paths = entry.get("local_paths") or {}
    value = local_paths.get(key)
    if isinstance(value, list):
        return any(bool(v) for v in value)
    return bool(value)


def infer_has_flags(entry: dict[str, Any]) -> dict[str, bool]:
    return {
        "has_cmo3": bool(entry.get("has_cmo3")) or has_path(entry, "cmo3"),
        "has_moc3": bool(entry.get("has_moc3")) or has_path(entry, "moc3"),
        "has_model3_json": bool(entry.get("has_model3_json")) or has_path(entry, "model3_json"),
        "has_physics3_json": bool(entry.get("has_physics3_json")) or has_path(entry, "physics3_json"),
        "has_psd": bool(entry.get("has_psd")) or has_path(entry, "psd"),
    }


def safe_analysis_mode(entry: dict[str, Any]) -> tuple[str, list[str]]:
    mode = entry.get("analysis_mode", "METADATA_ONLY")
    notes: list[str] = []
    if mode not in ALLOWED_MODES:
        notes.append(f"invalid analysis_mode={mode}; forced METADATA_ONLY")
        mode = "METADATA_ONLY"

    license_status = str(entry.get("license_status", "UNKNOWN")).upper()
    if license_status in UNSAFE_LICENSE_HINTS and mode != "METADATA_ONLY":
        notes.append(f"license_status={license_status}; forced METADATA_ONLY")
        mode = "METADATA_ONLY"
    return mode, notes


def load_json_if_exists(path: Path | None) -> tuple[Any | None, str | None]:
    if not path:
        return None, None
    if not path.exists():
        return None, f"missing file: {path}"
    try:
        return load_json(path), None
    except Exception as exc:  # noqa: BLE001
        return None, f"failed to parse {path}: {exc}"


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def summarize_model3(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {"present": False, "error": "model3 JSON was not an object"}
    refs = data.get("FileReferences") or {}
    groups = data.get("Groups") or []
    motions = refs.get("Motions") or {}
    expressions = refs.get("Expressions") or []
    textures = refs.get("Textures") or []
    return {
        "present": True,
        "version": data.get("Version"),
        "moc": refs.get("Moc"),
        "texture_count": len(textures) if isinstance(textures, list) else 0,
        "has_physics": bool(refs.get("Physics")),
        "has_pose": bool(refs.get("Pose")),
        "has_display_info": bool(refs.get("DisplayInfo")),
        "has_user_data": bool(refs.get("UserData")),
        "expression_count": len(expressions) if isinstance(expressions, list) else 0,
        "motion_group_count": len(motions) if isinstance(motions, dict) else 0,
        "motion_count": sum(len(v) for v in motions.values() if isinstance(v, list))
        if isinstance(motions, dict)
        else 0,
        "group_count": len(groups) if isinstance(groups, list) else 0,
        "parameter_ids": sorted(
            {
                item if isinstance(item, str) else item.get("Id")
                for group in groups
                if isinstance(group, dict)
                for item in as_list(group.get("Ids"))
                if isinstance(item, (str, dict))
            }
        ),
        "file_references": refs,
    }


def summarize_physics3(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {"present": False, "error": "physics3 JSON was not an object"}
    settings = data.get("PhysicsSettings") or data.get("PhysicsSetting") or []
    if not isinstance(settings, list):
        settings = []
    inputs = 0
    outputs = 0
    vertices = 0
    groups = []
    for idx, item in enumerate(settings):
        if not isinstance(item, dict):
            continue
        item_inputs = item.get("Input") or []
        item_outputs = item.get("Output") or []
        item_vertices = item.get("Vertices") or []
        inputs += len(item_inputs) if isinstance(item_inputs, list) else 0
        outputs += len(item_outputs) if isinstance(item_outputs, list) else 0
        vertices += len(item_vertices) if isinstance(item_vertices, list) else 0
        groups.append(
            {
                "index": idx,
                "id": item.get("Id"),
                "input_count": len(item_inputs) if isinstance(item_inputs, list) else 0,
                "output_count": len(item_outputs) if isinstance(item_outputs, list) else 0,
                "vertex_count": len(item_vertices) if isinstance(item_vertices, list) else 0,
            }
        )
    return {
        "present": True,
        "version": data.get("Version"),
        "physics_group_count": len(settings),
        "physics_input_count": inputs,
        "physics_output_count": outputs,
        "physics_vertex_count": vertices,
        "groups": groups,
    }


def summarize_cdi3(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {"present": False, "error": "cdi3 JSON was not an object"}
    params = data.get("Parameters") or []
    parts = data.get("Parts") or []
    return {
        "present": True,
        "parameter_display_count": len(params) if isinstance(params, list) else 0,
        "part_display_count": len(parts) if isinstance(parts, list) else 0,
    }


def summarize_json_files(paths: dict[str, Path | None]) -> dict[str, Any]:
    errors: list[str] = []
    model3, err = load_json_if_exists(paths.get("model3_json"))
    if err:
        errors.append(err)
    physics3, err = load_json_if_exists(paths.get("physics3_json"))
    if err:
        errors.append(err)
    cdi3, err = load_json_if_exists(paths.get("cdi3_json"))
    if err:
        errors.append(err)
    return {
        "model3": summarize_model3(model3) if model3 is not None else {"present": False},
        "physics3": summarize_physics3(physics3) if physics3 is not None else {"present": False},
        "cdi3": summarize_cdi3(cdi3) if cdi3 is not None else {"present": False},
        "motion3_count": len(as_list(paths.get("motion3_json"))) if paths.get("motion3_json") else 0,
        "exp3_count": len(as_list(paths.get("exp3_json"))) if paths.get("exp3_json") else 0,
        "pose3_present": bool(paths.get("pose3_json") and paths["pose3_json"].exists()),
        "errors": errors,
    }


def summarize_moc3(path: Path | None) -> dict[str, Any]:
    if not path:
        return {"present": False}
    if not path.exists():
        return {"present": False, "error": f"missing file: {path}"}
    summary: dict[str, Any] = {
        "present": True,
        "path": rel(path),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "py_moc3_status": "NOT_AVAILABLE",
    }
    try:
        from moc3 import Moc3  # type: ignore
    except Exception as exc:  # noqa: BLE001
        summary["py_moc3_error"] = str(exc)
        return summary

    try:
        moc = Moc3.from_file(str(path))
        summary.update(
            {
                "py_moc3_status": "PASS",
                "parameter_count": len(getattr(moc, "parameter_ids", []) or []),
                "art_mesh_count": len(getattr(moc, "art_mesh_ids", []) or []),
                "parameter_ids": list(getattr(moc, "parameter_ids", []) or []),
                "art_mesh_ids_sample": list(getattr(moc, "art_mesh_ids", []) or [])[:50],
            }
        )
    except Exception as exc:  # noqa: BLE001
        summary["py_moc3_status"] = "FAIL"
        summary["py_moc3_error"] = str(exc)
    return summary


def run_cmo3_inspector(cmo3: Path, report_dir: Path, skip: bool) -> dict[str, Any]:
    out_json = report_dir / "cmo3_structure_report.json"
    out_md = report_dir / "cmo3_structure_report.md"
    if skip:
        return {"status": "SKIPPED", "json": rel(out_json), "markdown": rel(out_md)}
    if not cmo3.exists():
        return {"status": "MISSING", "error": f"missing file: {cmo3}"}
    cmd = [
        "node",
        str(ROOT / "scripts" / "inspect_cmo3_structure.mjs"),
        "--cmo3",
        str(cmo3),
        "--out-json",
        str(out_json),
        "--out-md",
        str(out_md),
    ]
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
    result = {
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "returncode": proc.returncode,
        "json": rel(out_json),
        "markdown": rel(out_md),
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }
    if out_json.exists():
        try:
            report = load_json(out_json)
            result["cmo3_status"] = report.get("status")
            result["counts"] = {
                "art_meshes": report.get("art_meshes", {}).get("count", 0),
                "parts": report.get("parts", {}).get("count", 0),
                "parameters": report.get("parameters", {}).get("count", 0),
                "warp_deformers": report.get("deformers", {}).get("warp_count", 0),
                "rotation_deformers": report.get("deformers", {}).get("rotation_count", 0),
                "keyform_bindings": report.get("keyforms", {}).get("binding_count", 0),
                "keyform_grids": report.get("keyforms", {}).get("grid_count", 0),
                "glue": report.get("counts", {}).get("CGlueSource", {}).get("definitions", 0),
                "masks": sum(
                    report.get("counts", {}).get(tag, {}).get("definitions", 0)
                    for tag in ("CClippingMaskSource", "CClippingMaskGuid", "CInvertedMaskSource")
                ),
            }
            result["parameter_ids"] = report.get("parameters", {}).get("ids", [])
            result["part_names"] = report.get("parts", {}).get("names", [])
        except Exception as exc:  # noqa: BLE001
            result["report_parse_error"] = str(exc)
    return result


def resolve_paths(entry: dict[str, Any], catalog_dir: Path) -> dict[str, Any]:
    raw_paths = entry.get("local_paths") or {}
    paths: dict[str, Any] = {}
    for key in LOCAL_PATH_KEYS:
        value = raw_paths.get(key)
        if isinstance(value, list):
            paths[key] = [resolve_local_path(v, catalog_dir) for v in value if v]
        else:
            paths[key] = resolve_local_path(value, catalog_dir)
    return paths


def first_path(paths: dict[str, Any], key: str) -> Path | None:
    value = paths.get(key)
    if isinstance(value, list):
        return value[0] if value else None
    return value


def path_manifest(paths: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in paths.items():
        if isinstance(value, list):
            out[key] = [
                {
                    "path": rel(p),
                    "exists": p.exists(),
                    "size_bytes": p.stat().st_size if p.exists() else None,
                }
                for p in value
                if p
            ]
        elif value:
            out[key] = {
                "path": rel(value),
                "exists": value.exists(),
                "size_bytes": value.stat().st_size if value.exists() else None,
            }
    return out


def count_name_hints(*items: list[str]) -> dict[str, int]:
    text = " ".join(" ".join(x or "" for x in seq) for seq in items).lower()
    return {
        "hair": sum(token in text for token in ["hair", "kami", "bang", "front_hair", "back_hair"]),
        "eye": sum(token in text for token in ["eye", "iris", "pupil", "まばたき"]),
        "mouth": sum(token in text for token in ["mouth", "lip", "口"]),
        "body": sum(token in text for token in ["body", "torso", "neck", "bust"]),
        "arm": sum(token in text for token in ["arm", "hand", "elbow"]),
    }


def reuse_decision(mode: str, counts: dict[str, int], runtime: dict[str, Any], entry: dict[str, Any]) -> str:
    explicit = entry.get("reuse_decision")
    if explicit in {"KEEP", "REFERENCE_ONLY", "IGNORE"}:
        return explicit
    if mode == "METADATA_ONLY":
        return "IGNORE"
    if counts.get("warp_deformers", 0) > 0 and counts.get("keyform_bindings", 0) > 0:
        return "KEEP"
    if runtime.get("physics3", {}).get("physics_group_count", 0) > 0:
        return "REFERENCE_ONLY"
    return "REFERENCE_ONLY"


def analyze_entry(
    entry: dict[str, Any],
    catalog_dir: Path,
    out_dir: Path,
    skip_cmo3_inspector: bool,
) -> dict[str, Any]:
    model_id = entry.get("id")
    if not model_id:
        raise ValueError("catalog entry missing id")
    mode, safety_notes = safe_analysis_mode(entry)
    flags = infer_has_flags(entry)
    paths = resolve_paths(entry, catalog_dir)
    report_dir = out_dir / "models" / model_id

    runtime = {"model3": {"present": False}, "physics3": {"present": False}, "cdi3": {"present": False}, "errors": []}
    cmo3_result: dict[str, Any] = {"status": "NOT_REQUESTED"}
    moc3_result: dict[str, Any] = {"present": False}

    if mode in {"FULL_STRUCTURE", "RUNTIME_ONLY"}:
        runtime = summarize_json_files(paths)
        moc3_result = summarize_moc3(first_path(paths, "moc3"))
    if mode == "FULL_STRUCTURE":
        cmo3_path = first_path(paths, "cmo3")
        if cmo3_path:
            cmo3_result = run_cmo3_inspector(cmo3_path, report_dir, skip_cmo3_inspector)
        else:
            cmo3_result = {"status": "MISSING", "error": "FULL_STRUCTURE entry has no local cmo3 path"}

    counts = cmo3_result.get("counts") or {
        "art_meshes": moc3_result.get("art_mesh_count", 0),
        "parts": 0,
        "parameters": moc3_result.get("parameter_count", 0)
        or len(runtime.get("model3", {}).get("parameter_ids", [])),
        "warp_deformers": 0,
        "rotation_deformers": 0,
        "keyform_bindings": 0,
        "keyform_grids": 0,
        "glue": 0,
        "masks": 0,
    }
    parameter_ids = cmo3_result.get("parameter_ids") or moc3_result.get("parameter_ids") or runtime.get("model3", {}).get("parameter_ids", [])
    part_names = cmo3_result.get("part_names") or []
    hints = count_name_hints(parameter_ids, part_names)
    decision = reuse_decision(mode, counts, runtime, entry)

    model_report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "id": model_id,
        "name": entry.get("name"),
        "source_url": entry.get("source_url"),
        "source_type": entry.get("source_type"),
        "license_status": entry.get("license_status"),
        "analysis_mode": mode,
        "official_profile_key": entry.get("official_profile_key"),
        "analysis_safety_notes": safety_notes,
        **flags,
        "local_paths": path_manifest(paths),
        "cmo3": cmo3_result,
        "moc3": moc3_result,
        "runtime_json": runtime,
        "structure_counts": counts,
        "feature_presence": {
            "mask": counts.get("masks", 0) > 0,
            "glue": counts.get("glue", 0) > 0,
            "pose": bool(runtime.get("model3", {}).get("has_pose") or runtime.get("pose3_present")),
            "expression": bool(runtime.get("model3", {}).get("expression_count", 0) or runtime.get("exp3_count", 0)),
            "motion": bool(runtime.get("model3", {}).get("motion_count", 0) or runtime.get("motion3_count", 0)),
            "physics": bool(runtime.get("model3", {}).get("has_physics") or runtime.get("physics3", {}).get("physics_group_count", 0)),
        },
        "structure_hints": hints,
        "reuse_decision": decision,
        "notes": entry.get("notes", []),
        "structure_report_path": cmo3_result.get("json"),
    }
    write_json(report_dir / "reference_model_report.json", model_report)
    write_model_markdown(report_dir / "reference_model_report.md", model_report)
    return model_report


def write_model_markdown(path: Path, report: dict[str, Any]) -> None:
    counts = report["structure_counts"]
    runtime = report["runtime_json"]
    features = report["feature_presence"]
    notes = "\n".join(f"- {n}" for n in as_list(report.get("notes"))) or "- none"
    safety = "\n".join(f"- {n}" for n in report.get("analysis_safety_notes", [])) or "- none"
    text = f"""# Reference Model Report: {report.get('name') or report['id']}

Generated: {report['generated_at']}

Source: {report.get('source_url') or 'local only'}

Analysis mode: **{report['analysis_mode']}**

Reuse decision: **{report['reuse_decision']}**

## Safety Notes

{safety}

## Structure Counts

| Item | Count |
|---|---:|
| ArtMesh | {counts.get('art_meshes', 0)} |
| Part | {counts.get('parts', 0)} |
| Parameter | {counts.get('parameters', 0)} |
| Warp Deformer | {counts.get('warp_deformers', 0)} |
| Rotation Deformer | {counts.get('rotation_deformers', 0)} |
| KeyformBinding | {counts.get('keyform_bindings', 0)} |
| Physics Group | {runtime.get('physics3', {}).get('physics_group_count', 0)} |
| Physics Input | {runtime.get('physics3', {}).get('physics_input_count', 0)} |
| Physics Output | {runtime.get('physics3', {}).get('physics_output_count', 0)} |

## Feature Presence

| Feature | Present |
|---|---:|
| Mask | {features['mask']} |
| Glue | {features['glue']} |
| Pose | {features['pose']} |
| Expression | {features['expression']} |
| Motion | {features['motion']} |
| Physics | {features['physics']} |

## Notes

{notes}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def aggregate(reports: list[dict[str, Any]], out_dir: Path) -> dict[str, Any]:
    rows = []
    for report in reports:
        counts = report["structure_counts"]
        runtime = report["runtime_json"]
        features = report["feature_presence"]
        rows.append(
            {
                "id": report["id"],
                "name": report.get("name"),
                "analysis_mode": report["analysis_mode"],
                "reuse_decision": report["reuse_decision"],
                "license_status": report.get("license_status"),
                "official_profile_key": report.get("official_profile_key"),
                "art_meshes": counts.get("art_meshes", 0),
                "parts": counts.get("parts", 0),
                "parameters": counts.get("parameters", 0),
                "warp_deformers": counts.get("warp_deformers", 0),
                "rotation_deformers": counts.get("rotation_deformers", 0),
                "keyform_bindings": counts.get("keyform_bindings", 0),
                "physics_groups": runtime.get("physics3", {}).get("physics_group_count", 0),
                "physics_inputs": runtime.get("physics3", {}).get("physics_input_count", 0),
                "physics_outputs": runtime.get("physics3", {}).get("physics_output_count", 0),
                "mask": features["mask"],
                "glue": features["glue"],
                "pose": features["pose"],
                "expression": features["expression"],
                "motion": features["motion"],
                "physics": features["physics"],
                "hair_hint": report["structure_hints"]["hair"],
                "eye_hint": report["structure_hints"]["eye"],
                "mouth_hint": report["structure_hints"]["mouth"],
                "body_hint": report["structure_hints"]["body"],
                "arm_hint": report["structure_hints"]["arm"],
                "report": rel(out_dir / "models" / report["id"] / "reference_model_report.json"),
            }
        )
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tool": "analyze_reference_model_catalog.py",
        "summary": {
            "model_count": len(reports),
            "full_structure_count": sum(r["analysis_mode"] == "FULL_STRUCTURE" for r in reports),
            "runtime_only_count": sum(r["analysis_mode"] == "RUNTIME_ONLY" for r in reports),
            "metadata_only_count": sum(r["analysis_mode"] == "METADATA_ONLY" for r in reports),
            "keep_count": sum(r["reuse_decision"] == "KEEP" for r in reports),
            "reference_only_count": sum(r["reuse_decision"] == "REFERENCE_ONLY" for r in reports),
            "ignore_count": sum(r["reuse_decision"] == "IGNORE" for r in reports),
        },
        "comparison": rows,
        "interpretation": [
            "This catalog records structure and reusable rigging patterns only.",
            "It must not be used to copy another model's image assets, texture atlas, or PSD layers.",
            "METADATA_ONLY entries prove that the safety gate blocked local analysis.",
        ],
    }


def write_summary_markdown(path: Path, report: dict[str, Any]) -> None:
    rows = "\n".join(
        "| {id} | {mode} | {decision} | {art} | {params} | {warp} | {rot} | {key} | {phys} | {mask} | {glue} | {pose} | {expr} | {motion} | {hair}/{eye}/{mouth}/{body}/{arm} |".format(
            id=row["id"],
            mode=row["analysis_mode"],
            decision=row["reuse_decision"],
            art=row["art_meshes"],
            params=row["parameters"],
            warp=row["warp_deformers"],
            rot=row["rotation_deformers"],
            key=row["keyform_bindings"],
            phys=row["physics_groups"],
            mask=row["mask"],
            glue=row["glue"],
            pose=row["pose"],
            expr=row["expression"],
            motion=row["motion"],
            hair=row["hair_hint"],
            eye=row["eye_hint"],
            mouth=row["mouth_hint"],
            body=row["body_hint"],
            arm=row["arm_hint"],
        )
        for row in report["comparison"]
    )
    text = f"""# Reference Model Structure Summary

Generated: {report['generated_at']}

## Counts

| Item | Count |
|---|---:|
| Models | {report['summary']['model_count']} |
| FULL_STRUCTURE | {report['summary']['full_structure_count']} |
| RUNTIME_ONLY | {report['summary']['runtime_only_count']} |
| METADATA_ONLY | {report['summary']['metadata_only_count']} |
| KEEP | {report['summary']['keep_count']} |
| REFERENCE_ONLY | {report['summary']['reference_only_count']} |
| IGNORE | {report['summary']['ignore_count']} |

## Comparison

| ID | Mode | Decision | ArtMesh | Param | Warp | Rotation | KeyBinding | Physics | Mask | Glue | Pose | Expr | Motion | Hair/Eye/Mouth/Body/Arm hints |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
{rows}

## Recommendation

- Use `KEEP` entries as rig-structure references for deformer/keyform authoring.
- Use `REFERENCE_ONLY` entries for parameter naming, runtime JSON, and physics shape hints.
- Keep `METADATA_ONLY` entries out of local analysis until license and provenance are verified.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    catalog_path = Path(args.catalog).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    raw = load_json(catalog_path)
    entries = normalize_catalog(raw)
    reports = [
        analyze_entry(entry, catalog_path.parent, out_dir, args.skip_cmo3_inspector)
        for entry in entries
    ]
    summary = aggregate(reports, out_dir)
    write_json(out_dir / "reports" / "reference_model_structure_summary.json", summary)
    write_summary_markdown(out_dir / "reports" / "reference_model_structure_summary.md", summary)
    print(json.dumps({"ok": True, "models": len(reports), "summary": rel(out_dir / "reports" / "reference_model_structure_summary.json")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

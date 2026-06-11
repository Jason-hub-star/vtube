#!/usr/bin/env python3
"""Build Cubism v2 production design tables from the 57 Live2D references."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "reference-model-structure-001"
DEFAULT_SUMMARY = EXPERIMENT / "reports" / "reference_model_structure_summary.combined.json"
DEFAULT_OUT = EXPERIMENT / "reports"

TAXONOMY_CATEGORIES = (
    "face_base",
    "eye_group",
    "eye_L",
    "eye_R",
    "brow_group",
    "brow_L",
    "brow_R",
    "mouth_group",
    "front_hair",
    "side_hair_L",
    "side_hair_R",
    "back_hair",
    "neck",
    "upper_body",
    "shoulder_arm",
    "hand",
    "accessory",
    "effect",
    "clothing",
    "other",
)

PARAMETER_CATEGORIES = (
    "head_angle",
    "body_angle",
    "eye_open",
    "eye_ball",
    "brow",
    "mouth",
    "vowel_lipsync",
    "hair",
    "arm_hand",
    "breath",
    "accessory",
    "effect_expression",
    "other",
)

DESIGN_SECTIONS = ("eye", "mouth", "hair", "body_angle", "arm", "physics", "mask_pose_expression", "psd_layering")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
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


def abs_path(path: str | Path | None) -> Path | None:
    if not path:
        return None
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def existing_path(value: Any) -> Path | None:
    if not value:
        return None
    if isinstance(value, dict):
        if value.get("exists") is False:
            return None
        return abs_path(value.get("path"))
    if isinstance(value, str):
        return abs_path(value)
    return None


def path_list(value: Any) -> list[Path]:
    if not value:
        return []
    if isinstance(value, list):
        out = []
        for item in value:
            p = existing_path(item)
            if p and p.exists():
                out.append(p)
        return out
    p = existing_path(value)
    return [p] if p and p.exists() else []


def norm(value: str) -> str:
    return value.lower().replace("_", "").replace("-", "").replace(" ", "")


def has_any(value: str, tokens: tuple[str, ...]) -> bool:
    v = value.lower()
    compact = norm(value)
    return any(token in v or token in compact for token in tokens)


def side_left(value: str) -> bool:
    return has_any(value, ("left", " l", "_l", "paraml", "l_", "왼", "左"))


def side_right(value: str) -> bool:
    return has_any(value, ("right", " r", "_r", "paramr", "r_", "오른", "右"))


def taxonomy_category(name: str) -> str:
    v = name.lower()
    if has_any(v, ("brow", "eyebrow", "눈썹", "まゆ", "眉")):
        return "brow_L" if side_left(name) else "brow_R" if side_right(name) else "brow_group"
    if has_any(v, ("eye", "eyeball", "iris", "pupil", "눈", "目", "眼")):
        return "eye_L" if side_left(name) else "eye_R" if side_right(name) else "eye_group"
    if has_any(v, ("mouth", "lip", "teeth", "tongue", "입", "口", "歯", "舌")):
        return "mouth_group"
    if has_any(v, ("front hair", "hairfront", "앞머리", "前髪")):
        return "front_hair"
    if has_any(v, ("side hair", "hairside", "옆머리", "横髪")):
        return "side_hair_L" if side_left(name) else "side_hair_R" if side_right(name) else "side_hair_L"
    if has_any(v, ("back hair", "hairback", "뒷머리", "後ろ髪")):
        return "back_hair"
    if has_any(v, ("hair", "머리", "髪", "kami")):
        return "front_hair"
    if has_any(v, ("neck", "목", "首")):
        return "neck"
    if has_any(v, ("arm", "shoulder", "팔", "어깨", "腕", "肩")):
        return "shoulder_arm"
    if has_any(v, ("hand", "finger", "손", "指", "手")):
        return "hand"
    if has_any(v, ("body", "torso", "upper", "몸", "体", "胴")):
        return "upper_body"
    if has_any(v, ("cloth", "dress", "skirt", "shirt", "jacket", "服", "스커트", "치마", "옷")):
        return "clothing"
    if has_any(v, ("accessory", "ribbon", "acc", "hat", "tail", "ear", "장식", "리본", "帽", "耳", "尻尾")):
        return "accessory"
    if has_any(v, ("effect", "magic", "ef", "이펙트", "마법", "エフェクト", "魔法")):
        return "effect"
    if has_any(v, ("face", "head", "nose", "cheek", "ear", "얼굴", "머리", "鼻", "頬", "顔")):
        return "face_base"
    return "other"


def parameter_category(param_id: str) -> str:
    v = norm(param_id)
    if any(x in v for x in ("paramanglex", "paramangley", "paramanglez")):
        return "head_angle"
    if "bodyangle" in v or "parambody" in v or "paramall" in v or "bodyud" in v:
        return "body_angle"
    if "eye" in v and ("open" in v or "smile" in v or "size" in v):
        return "eye_open"
    if "eyeball" in v or "eyeform" in v:
        return "eye_ball"
    if "brow" in v:
        return "brow"
    if any(v == x for x in ("parama", "parami", "paramu", "parame", "paramo")) or any(x in v for x in ("vowel", "lipsync")):
        return "vowel_lipsync"
    if "mouth" in v or "inmouth" in v:
        return "mouth"
    if "hair" in v or "kami" in v or "rollfuwa" in v:
        return "hair"
    if "arm" in v or "hand" in v or "shoulder" in v or "finger" in v:
        return "arm_hand"
    if "breath" in v:
        return "breath"
    if any(x in v for x in ("acc", "ribbon", "skirt", "tail", "ear", "hat", "book", "bust")):
        return "accessory"
    if any(x in v for x in ("joy", "anger", "fear", "surp", "cry", "tear", "cheek", "red", "magic", "effect", "on")):
        return "effect_expression"
    return "other"


def design_section_for_param(param_id: str) -> str | None:
    cat = parameter_category(param_id)
    return {
        "eye_open": "eye",
        "eye_ball": "eye",
        "brow": "eye",
        "mouth": "mouth",
        "vowel_lipsync": "mouth",
        "hair": "hair",
        "head_angle": "body_angle",
        "body_angle": "body_angle",
        "arm_hand": "arm",
    }.get(cat)


def design_section_for_name(name: str) -> str | None:
    cat = taxonomy_category(name)
    if cat in {"eye_group", "eye_L", "eye_R", "brow_group", "brow_L", "brow_R"}:
        return "eye"
    if cat == "mouth_group":
        return "mouth"
    if cat in {"front_hair", "side_hair_L", "side_hair_R", "back_hair"}:
        return "hair"
    if cat in {"face_base", "neck", "upper_body"}:
        return "body_angle"
    if cat in {"shoulder_arm", "hand"}:
        return "arm"
    return None


def numeric_summary(values: list[int | float], include_zero: bool = True) -> dict[str, Any]:
    vals = [v for v in values if include_zero or v > 0]
    vals = sorted(vals)
    if not vals:
        return {"n": 0, "min": None, "p25": None, "median": None, "p75": None, "max": None, "mean": None}
    def pct(p: float) -> float:
        if len(vals) == 1:
            return float(vals[0])
        idx = (len(vals) - 1) * p
        lo = math.floor(idx)
        hi = math.ceil(idx)
        if lo == hi:
            return float(vals[lo])
        return float(vals[lo] + (vals[hi] - vals[lo]) * (idx - lo))
    return {
        "n": len(vals),
        "min": vals[0],
        "p25": round(pct(0.25), 2),
        "median": round(statistics.median(vals), 2),
        "p75": round(pct(0.75), 2),
        "max": vals[-1],
        "mean": round(statistics.mean(vals), 2),
    }


def load_cmo3_report(report: dict[str, Any]) -> dict[str, Any] | None:
    cmo3_json = report.get("structure_report_path") or report.get("cmo3", {}).get("json")
    path = abs_path(cmo3_json)
    if path and path.exists():
        return load_json(path)
    return None


def parameter_ids(report: dict[str, Any], cmo3: dict[str, Any] | None) -> list[str]:
    ids: list[str] = []
    if cmo3:
        ids.extend(cmo3.get("parameters", {}).get("ids", []))
    ids.extend(report.get("moc3", {}).get("parameter_ids", []) or [])
    ids.extend(report.get("runtime_json", {}).get("model3", {}).get("parameter_ids", []) or [])
    seen = []
    for pid in ids:
        if pid and pid not in seen:
            seen.append(pid)
    return seen


def motion_parameter_ids(report: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for path in path_list(report.get("local_paths", {}).get("motion3_json")):
        try:
            data = load_json(path)
        except Exception:
            continue
        for curve in data.get("Curves", []):
            if curve.get("Target") == "Parameter" and curve.get("Id"):
                out.add(curve["Id"])
    return out


def physics_ids(report: dict[str, Any]) -> dict[str, Any]:
    runtime = report.get("runtime_json", {}).get("physics3", {})
    out = {
        "present": bool(runtime.get("present")),
        "group_count": int(runtime.get("physics_group_count", 0) or 0),
        "input_count": int(runtime.get("physics_input_count", 0) or 0),
        "output_count": int(runtime.get("physics_output_count", 0) or 0),
        "input_ids": [],
        "output_ids": [],
    }
    physics_path = existing_path(report.get("local_paths", {}).get("physics3_json"))
    if not physics_path or not physics_path.exists():
        return out
    try:
        data = load_json(physics_path)
    except Exception:
        return out
    input_ids = set()
    output_ids = set()
    for setting in data.get("PhysicsSettings", []):
        for entry in setting.get("Input", []):
            pid = entry.get("Source", {}).get("Id")
            if pid:
                input_ids.add(pid)
        for entry in setting.get("Output", []):
            pid = entry.get("Destination", {}).get("Id")
            if pid:
                output_ids.add(pid)
    out["input_ids"] = sorted(input_ids)
    out["output_ids"] = sorted(output_ids)
    return out


def infer_taxonomy_from_runtime(parameter_ids_value: list[str], physics_output_ids: list[str]) -> Counter:
    counts: Counter[str] = Counter()
    all_ids = list(parameter_ids_value) + list(physics_output_ids)
    cats = Counter(parameter_category(pid) for pid in all_ids)
    if cats["head_angle"] or cats["body_angle"]:
        counts["face_base"] += 1
        counts["neck"] += 1 if cats["body_angle"] else 0
        counts["upper_body"] += 1 if cats["body_angle"] else 0
    if cats["eye_open"] or cats["eye_ball"]:
        counts["eye_group"] += 1
        # Runtime parameters usually expose L/R even when source parts are grouped.
        if any("eyel" in norm(pid) or "left" in pid.lower() for pid in all_ids if parameter_category(pid) in {"eye_open", "eye_ball"}):
            counts["eye_L"] += 1
        if any("eyer" in norm(pid) or "right" in pid.lower() for pid in all_ids if parameter_category(pid) in {"eye_open", "eye_ball"}):
            counts["eye_R"] += 1
    if cats["brow"]:
        counts["brow_group"] += 1
        if any("browl" in norm(pid) for pid in all_ids):
            counts["brow_L"] += 1
        if any("browr" in norm(pid) for pid in all_ids):
            counts["brow_R"] += 1
    if cats["mouth"] or cats["vowel_lipsync"]:
        counts["mouth_group"] += 1
    if cats["hair"]:
        hair_ids = [pid for pid in all_ids if parameter_category(pid) == "hair"]
        if any("front" in norm(pid) for pid in hair_ids):
            counts["front_hair"] += 1
        if any("side" in norm(pid) for pid in hair_ids):
            counts["side_hair_L"] += 1
            counts["side_hair_R"] += 1
        if any("back" in norm(pid) for pid in hair_ids):
            counts["back_hair"] += 1
        if not any(counts[k] for k in ("front_hair", "side_hair_L", "side_hair_R", "back_hair")):
            counts["front_hair"] += 1
    if cats["arm_hand"]:
        counts["shoulder_arm"] += 1
    if cats["accessory"]:
        counts["accessory"] += 1
    if cats["effect_expression"]:
        counts["effect"] += 1
    return counts


def model_design_row(summary_row: dict[str, Any]) -> dict[str, Any]:
    report_path = abs_path(summary_row.get("report"))
    report = load_json(report_path) if report_path and report_path.exists() else {}
    cmo3 = load_cmo3_report(report)
    params = parameter_ids(report, cmo3)
    motion_params = motion_parameter_ids(report)
    physics = physics_ids(report)
    parts = cmo3.get("parts", {}).get("names", []) if cmo3 else []
    warp_names = cmo3.get("deformers", {}).get("warp_names", []) if cmo3 else []
    rotation_names = cmo3.get("deformers", {}).get("rotation_names", []) if cmo3 else []
    counts = report.get("structure_counts", {}) or {}

    taxonomy_counts = Counter(taxonomy_category(name) for name in parts)
    parameter_counts = Counter(parameter_category(pid) for pid in params)
    motion_parameter_counts = Counter(parameter_category(pid) for pid in motion_params)
    taxonomy_evidence_type = "CMO3_PART_NAMES"
    if not parts:
        taxonomy_evidence_type = "RUNTIME_PARAMETER_INFERRED"
        taxonomy_counts = infer_taxonomy_from_runtime(params, physics["output_ids"])
    deformer_counts = Counter()
    for name in warp_names:
        section = design_section_for_name(name)
        if section:
            deformer_counts[f"{section}_warp"] += 1
    for name in rotation_names:
        section = design_section_for_name(name)
        if section:
            deformer_counts[f"{section}_rotation"] += 1
    keyform_counts = Counter()
    if cmo3:
        for binding in cmo3.get("keyforms", {}).get("bindings", []):
            section = design_section_for_param(binding.get("description") or "")
            if section:
                keyform_counts[section] += 1

    confidence = "FULL_STRUCTURE" if summary_row.get("analysis_mode") == "FULL_STRUCTURE" else "RUNTIME_INFERRED"
    return {
        "id": summary_row.get("id"),
        "name": summary_row.get("name"),
        "official_profile_key": summary_row.get("official_profile_key"),
        "analysis_mode": summary_row.get("analysis_mode"),
        "confidence": confidence,
        "reuse_decision": summary_row.get("reuse_decision"),
        "counts": {
            "art_meshes": int(counts.get("art_meshes", summary_row.get("art_meshes", 0)) or 0),
            "parts": int(counts.get("parts", summary_row.get("parts", 0)) or 0),
            "parameters": int(counts.get("parameters", summary_row.get("parameters", 0)) or 0),
            "warp_deformers": int(counts.get("warp_deformers", summary_row.get("warp_deformers", 0)) or 0),
            "rotation_deformers": int(counts.get("rotation_deformers", summary_row.get("rotation_deformers", 0)) or 0),
            "keyform_bindings": int(counts.get("keyform_bindings", summary_row.get("keyform_bindings", 0)) or 0),
            "glue": int(counts.get("glue", summary_row.get("glue", 0)) or 0),
            "masks": int(counts.get("masks", summary_row.get("mask", 0)) or 0),
        },
        "feature_presence": report.get("feature_presence", {}),
        "taxonomy_counts": {cat: taxonomy_counts.get(cat, 0) for cat in TAXONOMY_CATEGORIES},
        "taxonomy_evidence_type": taxonomy_evidence_type,
        "taxonomy_names": {
            cat: [name for name in parts if taxonomy_category(name) == cat][:20]
            for cat in TAXONOMY_CATEGORIES
            if taxonomy_counts.get(cat, 0)
        },
        "parameter_counts": {cat: parameter_counts.get(cat, 0) for cat in PARAMETER_CATEGORIES},
        "parameter_ids_by_category": {
            cat: sorted([pid for pid in params if parameter_category(pid) == cat])[:80]
            for cat in PARAMETER_CATEGORIES
            if parameter_counts.get(cat, 0)
        },
        "motion_parameter_counts": {cat: motion_parameter_counts.get(cat, 0) for cat in PARAMETER_CATEGORIES},
        "motion_parameter_ids_by_category": {
            cat: sorted([pid for pid in motion_params if parameter_category(pid) == cat])[:80]
            for cat in PARAMETER_CATEGORIES
            if motion_parameter_counts.get(cat, 0)
        },
        "deformer_counts_by_section": dict(deformer_counts),
        "keyform_counts_by_section": dict(keyform_counts),
        "physics": {
            **physics,
            "output_categories": dict(Counter(parameter_category(pid) for pid in physics["output_ids"])),
            "output_ids_by_category": {
                cat: sorted([pid for pid in physics["output_ids"] if parameter_category(pid) == cat])[:80]
                for cat in PARAMETER_CATEGORIES
                if any(parameter_category(pid) == cat for pid in physics["output_ids"])
            },
        },
        "evidence": {
            "reference_model_report": rel(report_path) if report_path else None,
            "cmo3_structure_report": rel(abs_path(report.get("structure_report_path"))) if report.get("structure_report_path") else None,
        },
    }


def build_taxonomy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    category_summary = {}
    for cat in TAXONOMY_CATEGORIES:
        full_values = [r["taxonomy_counts"].get(cat, 0) for r in rows if r["analysis_mode"] == "FULL_STRUCTURE"]
        any_values = [r["taxonomy_counts"].get(cat, 0) for r in rows]
        models = [r["id"] for r in rows if r["taxonomy_counts"].get(cat, 0) > 0]
        category_summary[cat] = {
            "model_count_with_evidence": len(models),
            "full_structure_count_stats": numeric_summary(full_values),
            "all57_count_stats": numeric_summary(any_values),
            "example_models": models[:10],
        }
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "all57 references; runtime-only rows cannot prove source part taxonomy",
        "category_summary": category_summary,
        "models": [
            {
                "id": r["id"],
                "name": r["name"],
                "analysis_mode": r["analysis_mode"],
                "confidence": r["confidence"],
                "taxonomy_evidence_type": r["taxonomy_evidence_type"],
                "taxonomy_counts": r["taxonomy_counts"],
                "taxonomy_names": r["taxonomy_names"],
            }
            for r in rows
        ],
    }


def build_parameter_map(rows: list[dict[str, Any]]) -> dict[str, Any]:
    categories = {}
    for cat in PARAMETER_CATEGORIES:
        ids = Counter()
        motion_ids = Counter()
        for row in rows:
            for pid in row["parameter_ids_by_category"].get(cat, []):
                ids[pid] += 1
            for pid in row.get("motion_parameter_ids_by_category", {}).get(cat, []):
                motion_ids[pid] += 1
        categories[cat] = {
            "model_count_with_parameter": sum(1 for r in rows if r["parameter_counts"].get(cat, 0) > 0),
            "model_count_with_motion_use": sum(1 for r in rows if r["motion_parameter_counts"].get(cat, 0) > 0),
            "parameter_count_stats": numeric_summary([r["parameter_counts"].get(cat, 0) for r in rows]),
            "top_parameter_ids": ids.most_common(30),
            "top_motion_parameter_ids": motion_ids.most_common(30),
        }
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "all57 references using CMO3, py-moc3, model3 groups, and motion3 curves when available",
        "categories": categories,
        "required_parameters_for_v2_standard": [
            "ParamAngleX",
            "ParamAngleY",
            "ParamAngleZ",
            "ParamBodyAngleX",
            "ParamBodyAngleY",
            "ParamEyeLOpen",
            "ParamEyeROpen",
            "ParamEyeBallX",
            "ParamEyeBallY",
            "ParamMouthOpenY",
            "ParamMouthForm",
            "ParamBreath",
        ],
        "recommended_parameters_for_v2_standard": [
            "ParamBrowL/R Angle/Form/Y",
            "ParamHairFront",
            "ParamHairSide",
            "ParamHairBack",
            "ParamArmL/R or ParamHandL/R when gestures are included",
        ],
        "models": [
            {
                "id": r["id"],
                "name": r["name"],
                "analysis_mode": r["analysis_mode"],
                "parameter_counts": r["parameter_counts"],
                "motion_parameter_counts": r["motion_parameter_counts"],
                "parameter_ids_by_category": r["parameter_ids_by_category"],
                "motion_parameter_ids_by_category": r["motion_parameter_ids_by_category"],
            }
            for r in rows
        ],
    }


def eligible_full_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        r for r in rows
        if r["analysis_mode"] == "FULL_STRUCTURE"
        and r["counts"]["art_meshes"] >= 20
        and r["counts"]["parameters"] >= 10
        and r["counts"]["warp_deformers"] > 0
        and r["counts"]["keyform_bindings"] >= 20
    ]


def build_deformer_floor(rows: list[dict[str, Any]]) -> dict[str, Any]:
    full = [r for r in rows if r["analysis_mode"] == "FULL_STRUCTURE"]
    eligible = eligible_full_rows(rows)
    metric_keys = ("art_meshes", "parts", "parameters", "warp_deformers", "rotation_deformers", "keyform_bindings", "glue")
    metrics = {
        key: {
            "full_structure_all": numeric_summary([r["counts"].get(key, 0) for r in full]),
            "rig_floor_eligible": numeric_summary([r["counts"].get(key, 0) for r in eligible]),
        }
        for key in metric_keys
    }
    section_floor = {}
    for section in ("eye", "mouth", "hair", "body_angle", "arm"):
        warp_key = f"{section}_warp"
        rot_key = f"{section}_rotation"
        section_floor[section] = {
            "warp_named_deformer_stats": numeric_summary([r["deformer_counts_by_section"].get(warp_key, 0) for r in eligible]),
            "rotation_named_deformer_stats": numeric_summary([r["deformer_counts_by_section"].get(rot_key, 0) for r in eligible]),
            "keyform_binding_stats": numeric_summary([r["keyform_counts_by_section"].get(section, 0) for r in eligible]),
            "models_with_named_deformers": sum(
                1 for r in eligible
                if r["deformer_counts_by_section"].get(warp_key, 0) + r["deformer_counts_by_section"].get(rot_key, 0) > 0
            ),
            "models_with_keyform_bindings": sum(1 for r in eligible if r["keyform_counts_by_section"].get(section, 0) > 0),
        }
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "FULL_STRUCTURE only; runtime-only models are excluded from deformer/keyform floor calculations",
        "full_structure_count": len(full),
        "rig_floor_eligible_count": len(eligible),
        "excluded_from_floor": [
            {"id": r["id"], "counts": r["counts"]}
            for r in full if r not in eligible
        ],
        "metrics": metrics,
        "section_floor": section_floor,
        "models": [
            {
                "id": r["id"],
                "name": r["name"],
                "counts": r["counts"],
                "deformer_counts_by_section": r["deformer_counts_by_section"],
                "keyform_counts_by_section": r["keyform_counts_by_section"],
                "evidence": r["evidence"],
            }
            for r in full
        ],
    }


def build_physics_design(rows: list[dict[str, Any]]) -> dict[str, Any]:
    present = [r for r in rows if r["physics"]["present"]]
    output_categories = Counter()
    for r in present:
        output_categories.update(r["physics"]["output_categories"])
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "all57 runtime physics where physics3.json exists",
        "summary": {
            "model_count": len(rows),
            "physics_present_count": len(present),
            "group_count_stats": numeric_summary([r["physics"]["group_count"] for r in present], include_zero=False),
            "input_count_stats": numeric_summary([r["physics"]["input_count"] for r in present], include_zero=False),
            "output_count_stats": numeric_summary([r["physics"]["output_count"] for r in present], include_zero=False),
            "output_category_frequency": dict(output_categories),
        },
        "tier_guidance": {
            "v2_min": "2 groups: hair front/side/back merged plus breath/body secondary motion if the design has medium hair.",
            "v2_standard": "4-6 groups: front hair, side hair L/R, back hair, body/breath, accessory if present.",
            "v2_rich": "8+ groups: split hair strands, ribbons/accessories, skirt/clothing, bust/body, and effect-secondary motion when needed.",
        },
        "models": [
            {
                "id": r["id"],
                "name": r["name"],
                "analysis_mode": r["analysis_mode"],
                "physics": r["physics"],
            }
            for r in rows
        ],
    }


def parameter_category_evidence(parameter_map: dict[str, Any], category: str) -> dict[str, Any]:
    info = parameter_map["categories"].get(category, {})
    return {
        "model_count_with_parameter": info.get("model_count_with_parameter", 0),
        "model_count_with_motion_use": info.get("model_count_with_motion_use", 0),
        "parameter_count_stats": info.get("parameter_count_stats", {}),
        "top_parameter_ids": info.get("top_parameter_ids", [])[:10],
        "top_motion_parameter_ids": info.get("top_motion_parameter_ids", [])[:10],
    }


def deformer_section_evidence(deformer_floor: dict[str, Any], section: str) -> dict[str, Any]:
    info = deformer_floor["section_floor"].get(section, {})
    return {
        "warp_named_deformer_stats": info.get("warp_named_deformer_stats", {}),
        "rotation_named_deformer_stats": info.get("rotation_named_deformer_stats", {}),
        "keyform_binding_stats": info.get("keyform_binding_stats", {}),
        "models_with_named_deformers": info.get("models_with_named_deformers", 0),
        "models_with_keyform_bindings": info.get("models_with_keyform_bindings", 0),
    }


def build_parameter_map_detail(parameter_map: dict[str, Any]) -> list[dict[str, Any]]:
    entries = [
        {
            "production_name": "ParamAngleX",
            "section": "body_angle",
            "required_level": "REQUIRED",
            "standard_range": [-30, 30],
            "keyform_positions": [-30, 0, 30],
            "connected_parts": ["face_base", "eye_L", "eye_R", "brow_L_R", "mouth_group", "front_hair"],
            "source_category": "head_angle",
            "qa_probe": "G3에서 neutral 대비 좌/우 extreme strip을 확인한다.",
            "notes_ko": "얼굴 좌우 회전의 핵심 파라미터다. 눈/입/앞머리 keyform이 같이 반응해야 한다.",
        },
        {
            "production_name": "ParamAngleY",
            "section": "body_angle",
            "required_level": "REQUIRED",
            "standard_range": [-30, 30],
            "keyform_positions": [-30, 0, 30],
            "connected_parts": ["face_base", "eye_L", "eye_R", "mouth_group", "front_hair", "neck"],
            "source_category": "head_angle",
            "qa_probe": "G3에서 위/아래 extreme strip을 확인한다.",
            "notes_ko": "고개 상하 움직임이다. 턱/목/앞머리 겹침과 underpaint 노출을 같이 본다.",
        },
        {
            "production_name": "ParamAngleZ",
            "section": "body_angle",
            "required_level": "REQUIRED",
            "standard_range": [-30, 30],
            "keyform_positions": [-30, 0, 30],
            "connected_parts": ["head_root", "front_hair", "side_hair_L", "side_hair_R"],
            "source_category": "head_angle",
            "qa_probe": "G3에서 고개 기울임 extreme strip을 확인한다.",
            "notes_ko": "고개 기울임이다. rotation deformer와 hair physics 입력으로 연결한다.",
        },
        {
            "production_name": "ParamBodyAngleX",
            "section": "body_angle",
            "required_level": "REQUIRED",
            "standard_range": [-10, 10],
            "keyform_positions": [-10, 0, 10],
            "connected_parts": ["neck", "upper_body", "shoulder_arm"],
            "source_category": "body_angle",
            "qa_probe": "G3에서 몸 좌/우 extreme strip을 확인한다.",
            "notes_ko": "상체 좌우 회전이다. 얼굴 각도와 과하게 따로 놀면 실패다.",
        },
        {
            "production_name": "ParamBodyAngleY",
            "section": "body_angle",
            "required_level": "REQUIRED",
            "standard_range": [-10, 10],
            "keyform_positions": [-10, 0, 10],
            "connected_parts": ["neck", "upper_body", "shoulder_arm"],
            "source_category": "body_angle",
            "qa_probe": "G3에서 몸 상/하 움직임을 확인한다.",
            "notes_ko": "상체 상하 움직임이다. v2_standard에서는 작고 자연스럽게 제한한다.",
        },
        {
            "production_name": "ParamBodyAngleZ",
            "section": "body_angle",
            "required_level": "RECOMMENDED",
            "standard_range": [-10, 10],
            "keyform_positions": [-10, 0, 10],
            "connected_parts": ["upper_body", "shoulder_arm"],
            "source_category": "body_angle",
            "qa_probe": "G3에서 몸 기울임이 머리 기울임과 충돌하지 않는지 본다.",
            "notes_ko": "첫 production에서는 있으면 좋고, 복잡하면 v2_rich로 미룬다.",
        },
        {
            "production_name": "ParamEyeLOpen",
            "section": "eye",
            "required_level": "REQUIRED",
            "standard_range": [0, 1],
            "keyform_positions": [0, 0.5, 1],
            "connected_parts": ["eye_L"],
            "source_category": "eye_open",
            "qa_probe": "G3에서 왼쪽 눈 닫힘/반쯤/열림 strip을 확인한다.",
            "notes_ko": "왼쪽 눈 깜빡임 필수 파라미터다. 흰자/홍채가 뚫려 보이면 실패다.",
        },
        {
            "production_name": "ParamEyeROpen",
            "section": "eye",
            "required_level": "REQUIRED",
            "standard_range": [0, 1],
            "keyform_positions": [0, 0.5, 1],
            "connected_parts": ["eye_R"],
            "source_category": "eye_open",
            "qa_probe": "G3에서 오른쪽 눈 닫힘/반쯤/열림 strip을 확인한다.",
            "notes_ko": "오른쪽 눈 깜빡임 필수 파라미터다. 좌우 타이밍은 독립 검수한다.",
        },
        {
            "production_name": "ParamEyeBallX",
            "section": "eye",
            "required_level": "REQUIRED",
            "standard_range": [-1, 1],
            "keyform_positions": [-1, 0, 1],
            "connected_parts": ["eye_L", "eye_R"],
            "source_category": "eye_ball",
            "qa_probe": "G3에서 시선 좌/우가 눈 밖으로 나가지 않는지 본다.",
            "notes_ko": "홍채/하이라이트가 같이 움직여야 한다.",
        },
        {
            "production_name": "ParamEyeBallY",
            "section": "eye",
            "required_level": "REQUIRED",
            "standard_range": [-1, 1],
            "keyform_positions": [-1, 0, 1],
            "connected_parts": ["eye_L", "eye_R"],
            "source_category": "eye_ball",
            "qa_probe": "G3에서 시선 위/아래가 눈꺼풀과 충돌하지 않는지 본다.",
            "notes_ko": "눈 크기가 작은 디자인은 움직임 범위를 줄인다.",
        },
        {
            "production_name": "ParamMouthOpenY",
            "section": "mouth",
            "required_level": "REQUIRED",
            "standard_range": [0, 1],
            "keyform_positions": [0, 0.5, 1],
            "connected_parts": ["mouth_group"],
            "source_category": "mouth",
            "qa_probe": "G3에서 닫힘/반쯤/열림 입 모양을 확인한다.",
            "notes_ko": "입 안쪽, 치아/혀 optional, 입선이 같은 중심에 맞아야 한다.",
        },
        {
            "production_name": "ParamMouthForm",
            "section": "mouth",
            "required_level": "REQUIRED",
            "standard_range": [-1, 1],
            "keyform_positions": [-1, 0, 1],
            "connected_parts": ["mouth_group"],
            "source_category": "mouth",
            "qa_probe": "G3에서 웃음/중립/찡그림 형태를 확인한다.",
            "notes_ko": "립싱크 전 기본 표정 폭을 잡는 파라미터다.",
        },
        {
            "production_name": "ParamBreath",
            "section": "physics",
            "required_level": "REQUIRED",
            "standard_range": [0, 1],
            "keyform_positions": [0, 0.5, 1],
            "connected_parts": ["upper_body", "shoulder_arm", "front_hair"],
            "source_category": "breath",
            "qa_probe": "G3 motion에서 너무 크게 출렁이지 않는지 본다.",
            "notes_ko": "몸과 머리카락 physics 입력의 기본 리듬으로 쓴다.",
        },
        {
            "production_name": "ParamBrowL/R Angle/Form/Y",
            "section": "eye",
            "required_level": "RECOMMENDED",
            "standard_range": [-1, 1],
            "keyform_positions": [-1, 0, 1],
            "connected_parts": ["brow_L_R"],
            "source_category": "brow",
            "qa_probe": "G3 표정 strip에서 눈썹이 눈과 따로 뜨지 않는지 본다.",
            "notes_ko": "v2_standard에서 표정 품질을 올리는 권장 파라미터다.",
        },
        {
            "production_name": "ParamHairFront / ParamHairSide / ParamHairBack",
            "section": "hair",
            "required_level": "RECOMMENDED",
            "standard_range": [-1, 1],
            "keyform_positions": [-1, 0, 1],
            "connected_parts": ["front_hair", "side_hair_L", "side_hair_R", "back_hair"],
            "source_category": "hair",
            "qa_probe": "G3 hair extreme과 physics motion strip을 따로 확인한다.",
            "notes_ko": "머리카락은 deformer keyform과 physics output을 분리해서 검수한다.",
        },
        {
            "production_name": "ParamArmL/R or ParamHandL/R",
            "section": "arm",
            "required_level": "OPTIONAL_FOR_V2_STANDARD",
            "standard_range": [-1, 1],
            "keyform_positions": [-1, 0, 1],
            "connected_parts": ["shoulder_arm", "hand"],
            "source_category": "arm_hand",
            "qa_probe": "팔이 있는 디자인만 G3 arm strip을 확인한다.",
            "notes_ko": "단순 어깨/팔은 v2_standard 가능, 손가락/복잡한 손은 v2_rich로 미룬다.",
        },
        {
            "production_name": "ParamA/I/U/E/O",
            "section": "mouth",
            "required_level": "OPTIONAL_OR_V2_RICH",
            "standard_range": [0, 1],
            "keyform_positions": [0, 1],
            "connected_parts": ["mouth_group"],
            "source_category": "vowel_lipsync",
            "qa_probe": "립싱크 전용 모델을 만들 때만 모음 strip을 확인한다.",
            "notes_ko": "공식 샘플 중 일부만 강하게 쓰므로 첫 production 필수는 아니다.",
        },
    ]
    for entry in entries:
        entry["evidence"] = parameter_category_evidence(parameter_map, entry["source_category"])
    return entries


def build_deformer_hierarchy(deformer_floor: dict[str, Any]) -> list[dict[str, Any]]:
    nodes = [
        {
            "id": "root",
            "parent": None,
            "section": "global",
            "deformer_type": "root/container",
            "required_level": "REQUIRED",
            "controlled_parts": ["all visible parts"],
            "input_parameters": [],
            "v2_standard_floor": {"warp_deformers": 0, "rotation_deformers": 0, "keyform_bindings": 0},
            "notes_ko": "전체 위치 기준점이다. 실제 움직임은 하위 deformer에서 만든다.",
        },
        {
            "id": "body_root_warp",
            "parent": "root",
            "section": "body_angle",
            "deformer_type": "warp",
            "required_level": "REQUIRED",
            "controlled_parts": ["neck", "upper_body", "shoulder_arm"],
            "input_parameters": ["ParamBodyAngleX", "ParamBodyAngleY", "ParamBodyAngleZ"],
            "v2_standard_floor": {"warp_deformers": 5, "rotation_deformers": 2, "keyform_bindings": 45},
            "notes_ko": "상체 각도와 목 연결을 담당한다. underpaint 노출 검수를 같이 한다.",
        },
        {
            "id": "head_angle_warp",
            "parent": "body_root_warp",
            "section": "body_angle",
            "deformer_type": "warp",
            "required_level": "REQUIRED",
            "controlled_parts": ["face_base", "eye_L", "eye_R", "brow_L_R", "mouth_group", "front_hair"],
            "input_parameters": ["ParamAngleX", "ParamAngleY", "ParamAngleZ"],
            "v2_standard_floor": {"warp_deformers": 2, "rotation_deformers": 1, "keyform_bindings": 18},
            "notes_ko": "얼굴 전체 각도용이다. 눈/입 개별 deformer보다 상위에 둔다.",
        },
        {
            "id": "eye_L_warp",
            "parent": "head_angle_warp",
            "section": "eye",
            "deformer_type": "warp",
            "required_level": "REQUIRED",
            "controlled_parts": ["eye_L"],
            "input_parameters": ["ParamEyeLOpen", "ParamEyeBallX", "ParamEyeBallY"],
            "v2_standard_floor": {"warp_deformers": 4, "rotation_deformers": 0, "keyform_bindings": 15},
            "notes_ko": "왼쪽 눈 깜빡임과 시선을 담당한다.",
        },
        {
            "id": "eye_R_warp",
            "parent": "head_angle_warp",
            "section": "eye",
            "deformer_type": "warp",
            "required_level": "REQUIRED",
            "controlled_parts": ["eye_R"],
            "input_parameters": ["ParamEyeROpen", "ParamEyeBallX", "ParamEyeBallY"],
            "v2_standard_floor": {"warp_deformers": 4, "rotation_deformers": 0, "keyform_bindings": 15},
            "notes_ko": "오른쪽 눈 깜빡임과 시선을 담당한다.",
        },
        {
            "id": "brow_L_R_warp",
            "parent": "head_angle_warp",
            "section": "eye",
            "deformer_type": "warp",
            "required_level": "RECOMMENDED",
            "controlled_parts": ["brow_L_R"],
            "input_parameters": ["ParamBrowL/R Angle/Form/Y"],
            "v2_standard_floor": {"warp_deformers": 2, "rotation_deformers": 0, "keyform_bindings": 6},
            "notes_ko": "눈썹 표정용이다. 첫 production에서도 넣는 것을 권장한다.",
        },
        {
            "id": "mouth_warp",
            "parent": "head_angle_warp",
            "section": "mouth",
            "deformer_type": "warp",
            "required_level": "REQUIRED",
            "controlled_parts": ["mouth_group"],
            "input_parameters": ["ParamMouthOpenY", "ParamMouthForm"],
            "v2_standard_floor": {"warp_deformers": 1, "rotation_deformers": 0, "keyform_bindings": 6},
            "notes_ko": "입 열림과 형태 변화를 담당한다. 입 안쪽 alpha와 중심 정렬이 중요하다.",
        },
        {
            "id": "front_hair_warp",
            "parent": "head_angle_warp",
            "section": "hair",
            "deformer_type": "warp",
            "required_level": "REQUIRED",
            "controlled_parts": ["front_hair"],
            "input_parameters": ["ParamAngleX", "ParamAngleZ", "ParamHairFront"],
            "v2_standard_floor": {"warp_deformers": 4, "rotation_deformers": 0, "keyform_bindings": 3},
            "notes_ko": "앞머리는 얼굴 각도와 physics 양쪽 영향을 받는다.",
        },
        {
            "id": "side_hair_L_R_warp",
            "parent": "head_angle_warp",
            "section": "hair",
            "deformer_type": "warp",
            "required_level": "REQUIRED",
            "controlled_parts": ["side_hair_L", "side_hair_R"],
            "input_parameters": ["ParamAngleX", "ParamAngleZ", "ParamHairSide"],
            "v2_standard_floor": {"warp_deformers": 4, "rotation_deformers": 1, "keyform_bindings": 3},
            "notes_ko": "옆머리는 좌우 분리한다. 긴 머리면 L/R output도 분리한다.",
        },
        {
            "id": "back_hair_warp",
            "parent": "body_root_warp",
            "section": "hair",
            "deformer_type": "warp",
            "required_level": "REQUIRED",
            "controlled_parts": ["back_hair"],
            "input_parameters": ["ParamBodyAngleX", "ParamAngleZ", "ParamHairBack"],
            "v2_standard_floor": {"warp_deformers": 2, "rotation_deformers": 0, "keyform_bindings": 2},
            "notes_ko": "뒷머리는 몸/머리 움직임 사이에서 너무 늦지 않게 따라오게 한다.",
        },
        {
            "id": "shoulder_arm_rotation",
            "parent": "body_root_warp",
            "section": "arm",
            "deformer_type": "rotation",
            "required_level": "OPTIONAL_FOR_V2_STANDARD",
            "controlled_parts": ["shoulder_arm", "hand"],
            "input_parameters": ["ParamArmL/R or ParamHandL/R"],
            "v2_standard_floor": {"warp_deformers": 2, "rotation_deformers": 4, "keyform_bindings": 8},
            "notes_ko": "팔이 보이는 디자인만 넣는다. 복잡한 손동작은 v2_rich 범위다.",
        },
    ]
    for node in nodes:
        if node["section"] in deformer_floor["section_floor"]:
            node["evidence"] = deformer_section_evidence(deformer_floor, node["section"])
    return nodes


def build_physics_blueprint(parameter_map: dict[str, Any], physics_design: dict[str, Any]) -> dict[str, Any]:
    summary = physics_design["summary"]
    group_evidence = {
        "observed_group_count_stats": summary["group_count_stats"],
        "observed_input_count_stats": summary["input_count_stats"],
        "observed_output_count_stats": summary["output_count_stats"],
        "output_category_frequency": summary["output_category_frequency"],
        "hair_parameter_evidence": parameter_category_evidence(parameter_map, "hair"),
        "body_parameter_evidence": parameter_category_evidence(parameter_map, "body_angle"),
        "breath_parameter_evidence": parameter_category_evidence(parameter_map, "breath"),
        "arm_parameter_evidence": parameter_category_evidence(parameter_map, "arm_hand"),
    }
    return {
        "v2_standard_target_group_count": "4-6",
        "evidence": group_evidence,
        "groups": [
            {
                "id": "front_hair_physics",
                "required_level": "REQUIRED",
                "controlled_parts": ["front_hair"],
                "input_parameters": ["ParamAngleX", "ParamAngleZ", "ParamBodyAngleX", "ParamBreath"],
                "output_parameters": ["ParamHairFront"],
                "qa_probe": "G3 hair motion strip에서 앞머리가 얼굴을 뚫거나 눈을 과하게 덮지 않는지 본다.",
            },
            {
                "id": "side_hair_L_physics",
                "required_level": "REQUIRED",
                "controlled_parts": ["side_hair_L"],
                "input_parameters": ["ParamAngleX", "ParamAngleZ", "ParamBodyAngleX", "ParamBreath"],
                "output_parameters": ["ParamHairSideL 또는 ParamHairSide"],
                "qa_probe": "왼쪽 옆머리의 흔들림과 draw order를 본다.",
            },
            {
                "id": "side_hair_R_physics",
                "required_level": "REQUIRED",
                "controlled_parts": ["side_hair_R"],
                "input_parameters": ["ParamAngleX", "ParamAngleZ", "ParamBodyAngleX", "ParamBreath"],
                "output_parameters": ["ParamHairSideR 또는 ParamHairSide"],
                "qa_probe": "오른쪽 옆머리의 흔들림과 draw order를 본다.",
            },
            {
                "id": "back_hair_physics",
                "required_level": "REQUIRED",
                "controlled_parts": ["back_hair"],
                "input_parameters": ["ParamBodyAngleX", "ParamAngleZ", "ParamBreath"],
                "output_parameters": ["ParamHairBack"],
                "qa_probe": "뒷머리가 몸 움직임에 너무 늦거나 빠르게 따라오지 않는지 본다.",
            },
            {
                "id": "body_breath_physics",
                "required_level": "RECOMMENDED",
                "controlled_parts": ["upper_body", "shoulder_arm", "neck"],
                "input_parameters": ["ParamBreath", "ParamBodyAngleX", "ParamBodyAngleY"],
                "output_parameters": ["ParamBodyAngleX/ParamBodyAngleY 보조 또는 전용 sway parameter"],
                "qa_probe": "motion strip에서 몸이 과하게 출렁이지 않는지 본다.",
            },
            {
                "id": "accessory_or_arm_physics",
                "required_level": "OPTIONAL_FOR_V2_STANDARD",
                "controlled_parts": ["accessory", "shoulder_arm"],
                "input_parameters": ["ParamAngleX", "ParamAngleZ", "ParamBreath"],
                "output_parameters": ["ParamAccessory* 또는 ParamArm*"],
                "qa_probe": "장식/팔이 있는 디자인만 확인한다. 없으면 PASS가 아니라 NOT_APPLICABLE로 둔다.",
            },
        ],
    }


def build_acceptance_checklist() -> list[dict[str, Any]]:
    return [
        {
            "gate": "G0_CONCEPT",
            "label_ko": "캐릭터 고르기",
            "review_owner": "HUMAN",
            "input_artifacts": ["concept 후보 3-6개", "neutral front preview"],
            "pass_criteria": [
                "눈, 입, 머리카락, 목/상체가 명확히 보인다.",
                "팔/장식이 과하게 겹쳐서 필수 파츠 분리를 막지 않는다.",
                "v2_standard 50-70 파츠로 나눌 수 있는 디자인이다.",
            ],
            "fail_criteria": ["정면성이 낮다.", "머리/얼굴/몸 경계가 불명확하다.", "스타일이 후보 간 섞여 있다."],
            "issue_tags": ["style_mismatch", "clipping_risk", "overhang_issue"],
            "output": "selected_concept_id 또는 REJECT",
        },
        {
            "gate": "G1_PART_TAXONOMY",
            "label_ko": "파츠가 잘 나뉘었는지 보기",
            "review_owner": "HUMAN_PLUS_AUTO",
            "input_artifacts": ["20-25 또는 50-70 파츠 contact sheet", "part manifest", "alpha bbox report"],
            "pass_criteria": [
                "v2_standard 필수 그룹(face/eye L/R/brow/mouth/hair/body/underpaint)이 존재한다.",
                "각 파츠 alpha가 비어 있지 않고 crop/bbox가 화면 밖으로 잘리지 않는다.",
                "눈/입/머리카락 파츠가 단독으로 봐도 어느 부위인지 알 수 있다.",
            ],
            "fail_criteria": ["필수 파츠 누락", "alpha 테두리 오염", "좌우 눈/팔 misalignment", "underpaint 누락"],
            "issue_tags": ["missing_part", "bad_alpha", "misaligned", "underpaint_missing", "draw_order_issue"],
            "output": "G1_PASS이면 Cubism import pack 작성, 아니면 part regeneration/fix queue",
        },
        {
            "gate": "G2_STRUCTURE",
            "label_ko": "구조 자동검사",
            "review_owner": "AUTO",
            "input_artifacts": ["CMO3 inspector report", "Cubism project/export smoke", "physics3.json"],
            "pass_criteria": [
                "v2_standard minimum floor: parameters >=25, warp_deformers >=35, rotation_deformers >=8, keyform_bindings >=120, physics_groups >=4",
                "eye/mouth/hair/body_angle section keyform evidence가 0으로 퇴행하지 않는다.",
                "moc3/model3.json/physics3.json runtime bundle이 로드 가능하다.",
            ],
            "fail_criteria": ["warp/keyform이 0", "physics group 없음", "runtime 로드 실패", "inspector report 없음"],
            "issue_tags": ["structure_missing", "deformer_missing", "keyform_missing", "physics_missing"],
            "output": "G2_PASS/WARN/FAIL 자동 판정. 사람이 그림을 고치는 단계가 아니라 Cubism 구조 작업 단계로 되돌린다.",
        },
        {
            "gate": "G3_MOTION_VISUAL",
            "label_ko": "움직임 확인",
            "review_owner": "HUMAN_PLUS_AUTO",
            "input_artifacts": ["neutral/motion/extreme strip", "motion GIF", "viewport clipping report"],
            "pass_criteria": [
                "neutral, motion, extreme 캡처가 모두 nonblank이다.",
                "눈 닫힘, 입 열림, 머리카락 흔들림, 몸각도 extreme이 각각 보인다.",
                "viewport edge clipping과 심한 draw order 깨짐이 없다.",
            ],
            "fail_criteria": ["모델 미표시", "극단값에서 얼굴/머리카락이 잘림", "눈/입/머리카락 움직임이 보이지 않음"],
            "issue_tags": ["render_blank", "viewport_clipping", "draw_order_issue", "motion_too_small", "motion_too_large"],
            "output": "production candidate PASS/WARN/FAIL 및 수정 대상 파라미터 목록",
        },
    ]


def tier_spec(
    rows: list[dict[str, Any]],
    parameter_map: dict[str, Any],
    deformer_floor: dict[str, Any],
    physics_design: dict[str, Any],
) -> dict[str, Any]:
    eligible = eligible_full_rows(rows)
    phys_stats = physics_design["summary"]["group_count_stats"]
    observed = {
        key: numeric_summary([r["counts"].get(key, 0) for r in eligible])
        for key in ("art_meshes", "parts", "parameters", "warp_deformers", "rotation_deformers", "keyform_bindings")
    }
    return {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_sources": {
            "part_taxonomy_matrix": "all57_part_taxonomy_matrix.json",
            "parameter_map": "all57_parameter_map.json",
            "deformer_keyform_floor": "all57_deformer_keyform_floor.json",
            "physics_group_design": "all57_physics_group_design.json",
            "strong20_runtime_probe": "../../live2d-strong-model-pattern-001/reports/strong20_runtime_probe_report.json",
            "strong20_part_success_patterns": "../../live2d-strong-model-pattern-001/reports/part_success_patterns.md",
        },
        "source": {
            "all57_model_count": len(rows),
            "full_structure_count": sum(1 for r in rows if r["analysis_mode"] == "FULL_STRUCTURE"),
            "runtime_only_count": sum(1 for r in rows if r["analysis_mode"] == "RUNTIME_ONLY"),
            "rig_floor_eligible_count": len(eligible),
            "strong20_role": "real Web runtime render validation baseline; all57 role is production structure/statistics expansion",
        },
        "observed_rig_floor_eligible_ranges": observed,
        "physics_observed_ranges": phys_stats,
        "production_tiers": {
            "v2_min": {
                "role": "technical gate only; proves real Cubism deformer/keyform/physics authoring, not final beauty",
                "part_taxonomy": "20-25 source parts, grouped into face, eye L/R, mouth, front/side/back hair, neck, upper body, simple shoulder/arm",
                "minimum_floor": {
                    "parameters": 12,
                    "warp_deformers": 8,
                    "rotation_deformers": 1,
                    "keyform_bindings": 20,
                    "physics_groups": 2,
                },
                "verification": ["CMO3 inspector detects warp increase", "CMO3 inspector detects keyform increase", "at least one hair/body physics group renders in runtime"],
            },
            "v2_standard": {
                "role": "first production candidate default",
                "part_taxonomy": "50-70 source parts with separated eyes/brows/mouth, front/side/back hair clusters, neck/torso/shoulder/optional arms, underpaint where overhang occurs",
                "minimum_floor": {
                    "parameters": 25,
                    "warp_deformers": 35,
                    "rotation_deformers": 8,
                    "keyform_bindings": 120,
                    "physics_groups": 4,
                },
                "recommended_target": {
                    "parameters": "35-55",
                    "warp_deformers": "40-65",
                    "rotation_deformers": "12-25",
                    "keyform_bindings": "160-260",
                    "physics_groups": "4-6",
                },
                "verification": ["neutral/motion/extreme strip for eye, mouth, hair, body angle", "G1 taxonomy contact sheet", "G2 automatic CMO3 PASS/WARN with no zero deformer/keyform regression"],
            },
            "v2_rich": {
                "role": "official-core-like expression richness after v2_standard passes",
                "part_taxonomy": "90+ source parts with richer arm/hand, accessory, effect, mask/pose/expression, and split hair physics",
                "minimum_floor": {
                    "parameters": 50,
                    "warp_deformers": 60,
                    "rotation_deformers": 20,
                    "keyform_bindings": 220,
                    "physics_groups": 8,
                },
                "recommended_features": ["at least two of mask, pose, expression, accessory physics, effect secondary motion"],
                "verification": ["same v2_standard gates plus expression/pose/mask runtime smoke"],
            },
        },
        "v2_standard_production_part_taxonomy": {
            "target_part_count": "50-70 source PSD/material parts",
            "face_base": ["face base", "left/right cheek or face shadow optional", "nose optional"],
            "eye_L": ["eye white L", "iris/pupil L", "upper eyelid/lash L", "lower eyelid/shadow L"],
            "eye_R": ["eye white R", "iris/pupil R", "upper eyelid/lash R", "lower eyelid/shadow R"],
            "brow_L_R": ["brow L", "brow R"],
            "mouth_group": ["mouth line", "mouth inner", "upper/lower lip or mask", "teeth/tongue optional"],
            "hair": ["front hair clusters 3-8", "side hair L/R 2-6", "back hair 2-8", "long strand groups when present"],
            "body": ["neck", "upper body/torso", "shoulder L/R", "simple arm L/R if visible"],
            "underpaint": ["face/neck/hair/shoulder underpaint where angle motion exposes gaps"],
            "deferred_until_v2_rich": ["complex hands", "heavy props", "effect layers", "skirt/cloth secondary parts unless design requires them"],
        },
        "parameter_map_detail": build_parameter_map_detail(parameter_map),
        "deformer_hierarchy": build_deformer_hierarchy(deformer_floor),
        "physics_blueprint": build_physics_blueprint(parameter_map, physics_design),
        "acceptance_checklist_g0_g3": build_acceptance_checklist(),
        "next_model_production_rule": "Write taxonomy, parameter map, deformer/keyform floor, and physics group plan before generating character art.",
    }


def write_matrix_md(path: Path, report: dict[str, Any]) -> None:
    lines = ["# All57 Part Taxonomy Matrix", "", f"- generated_at: `{report['generated_at']}`", f"- scope: {report['scope']}", ""]
    lines.extend(["| Category | Models With Evidence | Full Structure Stats | Example Models |", "|---|---:|---|---|"])
    for cat, data in report["category_summary"].items():
        lines.append(f"| `{cat}` | {data['model_count_with_evidence']} | `{data['full_structure_count_stats']}` | `{', '.join(data['example_models'][:5])}` |")
    lines.extend(["", "## Model Matrix", "", "| Model | Mode | Confidence | Key Counts |", "|---|---|---|---|"])
    for row in report["models"]:
        nonzero = {k: v for k, v in row["taxonomy_counts"].items() if v}
        lines.append(f"| `{row['id']}` | `{row['analysis_mode']}` | `{row['confidence']}` | `{nonzero}` |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_parameter_md(path: Path, report: dict[str, Any]) -> None:
    lines = ["# All57 Parameter Map", "", f"- generated_at: `{report['generated_at']}`", f"- scope: {report['scope']}", ""]
    lines.extend(["| Category | Models | Motion Models | Count Stats | Top IDs | Top Motion IDs |", "|---|---:|---:|---|---|---|"])
    for cat, data in report["categories"].items():
        top = ", ".join(pid for pid, _ in data["top_parameter_ids"][:8])
        motion_top = ", ".join(pid for pid, _ in data["top_motion_parameter_ids"][:8])
        lines.append(f"| `{cat}` | {data['model_count_with_parameter']} | {data['model_count_with_motion_use']} | `{data['parameter_count_stats']}` | `{top}` | `{motion_top}` |")
    lines.extend(["", "## Required v2_standard Parameters", ""])
    lines.extend(f"- `{item}`" for item in report["required_parameters_for_v2_standard"])
    lines.extend(["", "## Recommended v2_standard Parameters", ""])
    lines.extend(f"- {item}" for item in report["recommended_parameters_for_v2_standard"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_deformer_md(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# All57 Deformer/Keyform Floor",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- scope: {report['scope']}",
        f"- full_structure_count: `{report['full_structure_count']}`",
        f"- rig_floor_eligible_count: `{report['rig_floor_eligible_count']}`",
        "",
        "## Global Metrics",
        "",
        "| Metric | Full Structure All | Rig Floor Eligible |",
        "|---|---|---|",
    ]
    for key, data in report["metrics"].items():
        lines.append(f"| `{key}` | `{data['full_structure_all']}` | `{data['rig_floor_eligible']}` |")
    lines.extend(["", "## Section Floor", "", "| Section | Warp Named Stats | Rotation Named Stats | Keyform Binding Stats | Models With Named Deformers | Models With Keyforms |", "|---|---|---|---|---:|---:|"])
    for section, data in report["section_floor"].items():
        lines.append(f"| `{section}` | `{data['warp_named_deformer_stats']}` | `{data['rotation_named_deformer_stats']}` | `{data['keyform_binding_stats']}` | {data['models_with_named_deformers']} | {data['models_with_keyform_bindings']} |")
    if report["excluded_from_floor"]:
        lines.extend(["", "## Excluded From Floor", ""])
        for item in report["excluded_from_floor"]:
            lines.append(f"- `{item['id']}`: `{item['counts']}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_physics_md(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# All57 Physics Group Design",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- scope: {report['scope']}",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Tier Guidance", ""])
    for tier, text in report["tier_guidance"].items():
        lines.append(f"- `{tier}`: {text}")
    lines.extend(["", "## Model Physics", "", "| Model | Mode | Groups | Inputs | Outputs | Output Categories |", "|---|---|---:|---:|---:|---|"])
    for row in report["models"]:
        p = row["physics"]
        lines.append(f"| `{row['id']}` | `{row['analysis_mode']}` | {p['group_count']} | {p['input_count']} | {p['output_count']} | `{p['output_categories']}` |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_spec_md(path: Path, spec: dict[str, Any]) -> None:
    lines = [
        "# Cubism v2 Production Design Spec",
        "",
        f"- generated_at: `{spec['generated_at']}`",
        f"- schema_version: `{spec['schema_version']}`",
        f"- all57_model_count: `{spec['source']['all57_model_count']}`",
        f"- full_structure/runtime_only: `{spec['source']['full_structure_count']}/{spec['source']['runtime_only_count']}`",
        f"- rig_floor_eligible_count: `{spec['source']['rig_floor_eligible_count']}`",
        f"- rule: {spec['next_model_production_rule']}",
        "",
        "## Evidence Sources",
        "",
        "| Source | Path |",
        "|---|---|",
    ]
    for key, value in spec["evidence_sources"].items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend([
        "",
        "## Observed Rig Ranges",
        "",
        "| Metric | Range |",
        "|---|---|",
    ])
    for key, value in spec["observed_rig_floor_eligible_ranges"].items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(["", "## Production Tiers", ""])
    for tier, data in spec["production_tiers"].items():
        lines.extend([
            f"### {tier}",
            "",
            f"- role: {data['role']}",
            f"- part_taxonomy: {data['part_taxonomy']}",
            f"- minimum_floor: `{data['minimum_floor']}`",
        ])
        if data.get("recommended_target"):
            lines.append(f"- recommended_target: `{data['recommended_target']}`")
        if data.get("recommended_features"):
            lines.append(f"- recommended_features: `{data['recommended_features']}`")
        lines.append(f"- verification: `{data['verification']}`")
        lines.append("")
    lines.extend(["## v2_standard Production Part Taxonomy", ""])
    taxonomy = spec["v2_standard_production_part_taxonomy"]
    lines.append(f"- target_part_count: `{taxonomy['target_part_count']}`")
    lines.extend(["", "| Group | Required Parts |", "|---|---|"])
    for key, value in taxonomy.items():
        if key == "target_part_count":
            continue
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend([
        "",
        "## Parameter Map Detail",
        "",
        "| Parameter | Level | Section | Range | Keyforms | Connected Parts | Evidence |",
        "|---|---|---|---|---|---|---|",
    ])
    for item in spec["parameter_map_detail"]:
        evidence = item["evidence"]
        evidence_text = (
            f"models {evidence['model_count_with_parameter']}, "
            f"motion {evidence['model_count_with_motion_use']}, "
            f"top {evidence['top_parameter_ids'][:3]}"
        )
        lines.append(
            f"| `{item['production_name']}` | `{item['required_level']}` | `{item['section']}` | "
            f"`{item['standard_range']}` | `{item['keyform_positions']}` | `{item['connected_parts']}` | `{evidence_text}` |"
        )
    lines.extend([
        "",
        "## Deformer Hierarchy",
        "",
        "| Node | Parent | Type | Level | Parameters | Parts | v2_standard Floor | Evidence |",
        "|---|---|---|---|---|---|---|---|",
    ])
    for node in spec["deformer_hierarchy"]:
        evidence = node.get("evidence")
        evidence_text = ""
        if evidence:
            evidence_text = (
                f"warp median {evidence['warp_named_deformer_stats'].get('median')}, "
                f"rotation median {evidence['rotation_named_deformer_stats'].get('median')}, "
                f"keyform median {evidence['keyform_binding_stats'].get('median')}"
            )
        lines.append(
            f"| `{node['id']}` | `{node['parent']}` | `{node['deformer_type']}` | `{node['required_level']}` | "
            f"`{node['input_parameters']}` | `{node['controlled_parts']}` | `{node['v2_standard_floor']}` | `{evidence_text}` |"
        )
    lines.extend([
        "",
        "## Physics Blueprint",
        "",
        f"- v2_standard_target_group_count: `{spec['physics_blueprint']['v2_standard_target_group_count']}`",
        f"- observed_group_count_stats: `{spec['physics_blueprint']['evidence']['observed_group_count_stats']}`",
        f"- observed_output_category_frequency: `{spec['physics_blueprint']['evidence']['output_category_frequency']}`",
        "",
        "| Group | Level | Inputs | Outputs | Parts | QA Probe |",
        "|---|---|---|---|---|---|",
    ])
    for group in spec["physics_blueprint"]["groups"]:
        lines.append(
            f"| `{group['id']}` | `{group['required_level']}` | `{group['input_parameters']}` | "
            f"`{group['output_parameters']}` | `{group['controlled_parts']}` | {group['qa_probe']} |"
        )
    lines.extend([
        "",
        "## G0-G3 Acceptance Checklist",
        "",
        "| Gate | Korean Label | Owner | Pass Criteria | Fail Criteria | Issue Tags | Output |",
        "|---|---|---|---|---|---|---|",
    ])
    for gate in spec["acceptance_checklist_g0_g3"]:
        lines.append(
            f"| `{gate['gate']}` | {gate['label_ko']} | `{gate['review_owner']}` | "
            f"`{gate['pass_criteria']}` | `{gate['fail_criteria']}` | `{gate['issue_tags']}` | {gate['output']} |"
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    summary = load_json(args.summary)
    rows = [model_design_row(row) for row in summary.get("comparison", [])]
    out = args.out_dir
    taxonomy = build_taxonomy(rows)
    parameter_map = build_parameter_map(rows)
    deformer_floor = build_deformer_floor(rows)
    physics_design = build_physics_design(rows)
    spec = tier_spec(rows, parameter_map, deformer_floor, physics_design)

    write_json(out / "all57_part_taxonomy_matrix.json", taxonomy)
    write_matrix_md(out / "all57_part_taxonomy_matrix.md", taxonomy)
    write_json(out / "all57_parameter_map.json", parameter_map)
    write_parameter_md(out / "all57_parameter_map.md", parameter_map)
    write_json(out / "all57_deformer_keyform_floor.json", deformer_floor)
    write_deformer_md(out / "all57_deformer_keyform_floor.md", deformer_floor)
    write_json(out / "all57_physics_group_design.json", physics_design)
    write_physics_md(out / "all57_physics_group_design.md", physics_design)
    write_json(out / "cubism_v2_production_design_spec.json", spec)
    write_spec_md(out / "cubism_v2_production_design_spec.md", spec)

    required_sections = {
        "taxonomy_categories": len(taxonomy["category_summary"]),
        "parameter_categories": len(parameter_map["categories"]),
        "deformer_eligible": deformer_floor["rig_floor_eligible_count"],
        "physics_present": physics_design["summary"]["physics_present_count"],
        "tier_count": len(spec["production_tiers"]),
    }
    print(json.dumps({
        "status": "PASS",
        "model_count": len(rows),
        "summary": summary.get("summary", {}),
        "required_sections": required_sections,
        "production_spec_schema_version": spec["schema_version"],
        "production_spec_v2_sections": {
            "parameter_map_detail": len(spec["parameter_map_detail"]),
            "deformer_hierarchy": len(spec["deformer_hierarchy"]),
            "physics_blueprint_groups": len(spec["physics_blueprint"]["groups"]),
            "acceptance_checklist_g0_g3": len(spec["acceptance_checklist_g0_g3"]),
        },
        "outputs": {
            "taxonomy": rel(out / "all57_part_taxonomy_matrix.md"),
            "parameter_map": rel(out / "all57_parameter_map.md"),
            "deformer_floor": rel(out / "all57_deformer_keyform_floor.md"),
            "physics": rel(out / "all57_physics_group_design.md"),
            "production_spec": rel(out / "cubism_v2_production_design_spec.md"),
        },
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

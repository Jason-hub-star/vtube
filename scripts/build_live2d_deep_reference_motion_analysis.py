#!/usr/bin/env python3
"""Build deeper Live2D reference motion and rig pattern analysis.

This script does not reuse model artwork. It reads existing local evidence:
runtime screenshots, model3/physics3/motion3 JSON, and CMO3 inspector reports.
The goal is to turn the strong20 baseline into measurable production guidance.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "live2d-strong-model-pattern-001"
DEFAULT_RENDER_MANIFEST = EXPERIMENT / "reports" / "strong20_render_manifest.json"
DEFAULT_RUNTIME_REPORT = EXPERIMENT / "reports" / "strong20_runtime_probe_report.json"
DEFAULT_CMO3_SUMMARY = EXPERIMENT / "reports" / "cmo3_structure_batch_summary.json"
DEFAULT_CORE_REPORT = EXPERIMENT / "reports" / "strong20_core_api_extractor_report.json"
DEFAULT_OUT = EXPERIMENT / "reports"


PARAM_TOKENS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("eye", ("eye", "eyeball", "iris", "pupil", "blink", "wink")),
    ("mouth", ("mouth", "lip", "jaw", "vowel")),
    ("hair", ("hair", "bang", "front", "side", "back", "twin", "tail")),
    ("body_angle", ("angle", "body", "breath", "bust", "head", "neck")),
    ("arm", ("arm", "hand", "shoulder")),
    ("physics", ("physics", "sway", "shake", "pendulum")),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render-manifest", type=Path, default=DEFAULT_RENDER_MANIFEST)
    parser.add_argument("--runtime-report", type=Path, default=DEFAULT_RUNTIME_REPORT)
    parser.add_argument("--cmo3-summary", type=Path, default=DEFAULT_CMO3_SUMMARY)
    parser.add_argument("--core-report", type=Path, default=DEFAULT_CORE_REPORT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--diff-threshold", type=int, default=18)
    return parser.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path | str | None) -> str | None:
    if not path:
        return None
    path = Path(path)
    if not path.is_absolute():
        return str(path)
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def abs_path(value: str | Path | None) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path


def existing_path(value: str | Path | None) -> Path | None:
    path = abs_path(value)
    if path and path.exists():
        return path
    return None


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def parameter_category(param_id: str) -> str:
    n = norm(param_id)
    for category, tokens in PARAM_TOKENS:
        if any(token in n for token in tokens):
            return category
    return "other"


def numeric_summary(values: list[float]) -> dict[str, Any]:
    clean = [float(v) for v in values if isinstance(v, (int, float)) and math.isfinite(v)]
    if not clean:
        return {"count": 0}
    clean.sort()

    def pct(p: float) -> float:
        if len(clean) == 1:
            return clean[0]
        idx = (len(clean) - 1) * p
        lo = math.floor(idx)
        hi = math.ceil(idx)
        if lo == hi:
            return clean[lo]
        return clean[lo] + (clean[hi] - clean[lo]) * (idx - lo)

    return {
        "count": len(clean),
        "min": round(clean[0], 6),
        "median": round(statistics.median(clean), 6),
        "p75": round(pct(0.75), 6),
        "p90": round(pct(0.90), 6),
        "max": round(clean[-1], 6),
        "mean": round(statistics.fmean(clean), 6),
    }


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


def build_visual_diff_sweep(runtime_report: dict[str, Any], threshold: int) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for model in runtime_report.get("models", []):
        model_id = model.get("id")
        captures = model.get("captures", {}) or {}
        neutral = existing_path(captures.get("neutral"))
        if not neutral:
            skipped.append({"model_id": model_id, "reason": "neutral_missing"})
            continue

        targets: list[tuple[str, str, str]] = []
        for key in ("motion_20", "motion_50", "motion_80"):
            if captures.get(key):
                targets.append(("motion", key, captures[key]))
        for category in ("eye", "mouth", "hair", "body_angle", "arm"):
            for frame_path in captures.get(f"extreme_{category}_frames", []) or []:
                pose = Path(frame_path).stem.replace(f"extreme_{category}_", "")
                targets.append((category, pose, frame_path))

        for category, pose, target_rel in targets:
            target = existing_path(target_rel)
            if not target:
                skipped.append({"model_id": model_id, "reason": f"target_missing:{target_rel}"})
                continue
            metrics = image_diff_metrics(neutral, target, threshold)
            rows.append(
                {
                    "model_id": model_id,
                    "category": category,
                    "pose": pose,
                    "neutral": rel(neutral),
                    "target": rel(target),
                    **metrics,
                }
            )

    by_category: dict[str, Any] = {}
    for category in sorted({row["category"] for row in rows}):
        category_rows = [row for row in rows if row["category"] == category]
        ranked = sorted(category_rows, key=lambda row: row["changed_ratio"], reverse=True)
        by_category[category] = {
            "samples": len(category_rows),
            "changed_ratio": numeric_summary([row["changed_ratio"] for row in category_rows]),
            "mean_delta": numeric_summary([row["mean_delta"] for row in category_rows]),
            "strongest_examples": [
                {
                    "model_id": row["model_id"],
                    "pose": row["pose"],
                    "changed_ratio": row["changed_ratio"],
                    "changed_bbox": row["changed_bbox"],
                }
                for row in ranked[:5]
            ],
        }

    return {
        "method": "neutral_vs_motion_or_extreme_pixel_diff",
        "diff_threshold_luma": threshold,
        "interpretation": "화면 변화량 계측이다. 자연스러운 모션 품질 판정은 motion 캡처와 별도 human/GIF 검수로 판단한다.",
        "summary_by_category": by_category,
        "rows": rows,
        "skipped": skipped,
    }


def build_parameter_influence_map(runtime_report: dict[str, Any], visual_diff: dict[str, Any]) -> dict[str, Any]:
    category_ratios: dict[tuple[str, str], list[float]] = defaultdict(list)
    category_bboxes: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in visual_diff.get("rows", []):
        if row["category"] == "motion":
            continue
        key = (row["model_id"], row["category"])
        category_ratios[key].append(row["changed_ratio"])
        if row.get("changed_bbox"):
            category_bboxes[key].append(row["changed_bbox"])

    rows: list[dict[str, Any]] = []
    for model in runtime_report.get("models", []):
        model_id = model.get("id")
        for category, payload in (model.get("categories", {}) or {}).items():
            params = payload.get("matched_parameters", []) or []
            stats = numeric_summary(category_ratios.get((model_id, category), []))
            for param_id in params:
                rows.append(
                    {
                        "model_id": model_id,
                        "parameter_id": param_id,
                        "category": category,
                        "inferred_from": "CATEGORY_EXTREME_SWEEP",
                        "confidence": "MEDIUM",
                        "changed_ratio_summary": stats,
                        "bbox_samples": category_bboxes.get((model_id, category), [])[:3],
                    }
                )

    by_parameter: dict[str, Any] = {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["parameter_id"]].append(row)
    for param_id, param_rows in sorted(grouped.items()):
        medians = [
            row["changed_ratio_summary"].get("median")
            for row in param_rows
            if row["changed_ratio_summary"].get("count", 0)
        ]
        by_parameter[param_id] = {
            "models": len({row["model_id"] for row in param_rows}),
            "category": parameter_category(param_id),
            "visual_influence_median": numeric_summary(medians),
        }

    return {
        "method": "runtime_probe_matched_parameters_plus_category_visual_diff",
        "limitation": "현재는 category sweep 기반 추정이다. 단일 parameter만 고정 sweep하는 Web/Core probe를 붙이면 confidence를 HIGH로 올릴 수 있다.",
        "parameter_count": len(by_parameter),
        "by_parameter": by_parameter,
        "rows": rows,
    }


def parse_physics3(path: Path) -> dict[str, Any]:
    data = load_json(path)
    settings = data.get("PhysicsSettings", []) or []
    group_rows: list[dict[str, Any]] = []
    output_categories = Counter()
    input_categories = Counter()
    delays: list[float] = []
    mobilities: list[float] = []
    accelerations: list[float] = []
    radii: list[float] = []
    scales: list[float] = []
    weights: list[float] = []

    for setting in settings:
        inputs = []
        outputs = []
        for item in setting.get("Input", []) or []:
            source_id = (((item.get("Source") or {}).get("Id")) or "")
            cat = parameter_category(source_id)
            input_categories[cat] += 1
            weights.append(float(item.get("Weight", 0) or 0))
            inputs.append(
                {
                    "id": source_id,
                    "category": cat,
                    "type": item.get("Type"),
                    "weight": item.get("Weight"),
                    "reflect": item.get("Reflect"),
                }
            )
        for item in setting.get("Output", []) or []:
            dest_id = (((item.get("Destination") or {}).get("Id")) or "")
            cat = parameter_category(dest_id)
            output_categories[cat] += 1
            if isinstance(item.get("Scale"), (int, float)):
                scales.append(float(item["Scale"]))
            if isinstance(item.get("Weight"), (int, float)):
                weights.append(float(item["Weight"]))
            outputs.append(
                {
                    "id": dest_id,
                    "category": cat,
                    "type": item.get("Type"),
                    "scale": item.get("Scale"),
                    "weight": item.get("Weight"),
                    "reflect": item.get("Reflect"),
                    "vertex_index": item.get("VertexIndex"),
                }
            )
        for vertex in setting.get("Vertices", []) or []:
            for key, target in (
                ("Delay", delays),
                ("Mobility", mobilities),
                ("Acceleration", accelerations),
                ("Radius", radii),
            ):
                if isinstance(vertex.get(key), (int, float)):
                    target.append(float(vertex[key]))
        group_rows.append(
            {
                "id": setting.get("Id"),
                "input_count": len(inputs),
                "output_count": len(outputs),
                "vertex_count": len(setting.get("Vertices", []) or []),
                "inputs": inputs,
                "outputs": outputs,
                "normalization": setting.get("Normalization"),
            }
        )

    return {
        "meta": data.get("Meta", {}),
        "group_count": len(settings),
        "input_categories": dict(input_categories),
        "output_categories": dict(output_categories),
        "response_proxy": {
            "delay": numeric_summary(delays),
            "mobility": numeric_summary(mobilities),
            "acceleration": numeric_summary(accelerations),
            "radius": numeric_summary(radii),
            "output_scale": numeric_summary(scales),
            "weight": numeric_summary(weights),
        },
        "groups": group_rows,
    }


def build_physics_response_curve(render_manifest: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for model in render_manifest.get("models", []):
        physics_path = existing_path((model.get("local_paths", {}) or {}).get("physics3_json"))
        if not physics_path:
            rows.append({"model_id": model.get("id"), "status": "MISSING_PHYSICS3_JSON"})
            continue
        parsed = parse_physics3(physics_path)
        rows.append(
            {
                "model_id": model.get("id"),
                "status": "PASS_STATIC_PHYSICS3_PROXY",
                "physics3_json": rel(physics_path),
                **parsed,
            }
        )

    output_category_counter = Counter()
    group_counts = []
    delays = []
    for row in rows:
        if row.get("status") != "PASS_STATIC_PHYSICS3_PROXY":
            continue
        output_category_counter.update(row.get("output_categories", {}))
        group_counts.append(row.get("group_count", 0))
        median_delay = row.get("response_proxy", {}).get("delay", {}).get("median")
        if isinstance(median_delay, (int, float)):
            delays.append(float(median_delay))
    return {
        "method": "physics3_json_static_input_output_and_vertex_response_proxy",
        "limitation": "실시간 물리 시뮬레이션 곡선이 아니라 physics3 설정값에서 지연/이동성/가속/출력 스케일을 요약한 proxy다.",
        "model_count": len(rows),
        "models_with_physics": sum(1 for row in rows if row.get("status") == "PASS_STATIC_PHYSICS3_PROXY"),
        "group_count_summary": numeric_summary(group_counts),
        "median_delay_summary": numeric_summary(delays),
        "output_categories": dict(output_category_counter),
        "rows": rows,
    }


def curve_values_from_segments(segments: list[Any]) -> list[float]:
    values: list[float] = []
    if len(segments) < 2:
        return values
    if isinstance(segments[1], (int, float)):
        values.append(float(segments[1]))
    i = 2
    while i < len(segments):
        segment_type = int(segments[i]) if isinstance(segments[i], (int, float)) else None
        if segment_type in (0, 2, 3) and i + 2 < len(segments):
            if isinstance(segments[i + 2], (int, float)):
                values.append(float(segments[i + 2]))
            i += 3
        elif segment_type == 1 and i + 6 < len(segments):
            for j in (2, 4, 6):
                if isinstance(segments[i + j], (int, float)):
                    values.append(float(segments[i + j]))
            i += 7
        else:
            # Fallback for malformed/unknown data: collect likely y-values.
            for j in range(i + 1, len(segments), 2):
                if isinstance(segments[j], (int, float)):
                    values.append(float(segments[j]))
            break
    return values


def parse_motion3(path: Path) -> list[dict[str, Any]]:
    data = load_json(path)
    rows: list[dict[str, Any]] = []
    for curve in data.get("Curves", []) or []:
        if curve.get("Target") != "Parameter":
            continue
        param_id = curve.get("Id")
        values = curve_values_from_segments(curve.get("Segments", []) or [])
        if not values:
            continue
        rows.append(
            {
                "parameter_id": param_id,
                "category": parameter_category(param_id or ""),
                "value_min": min(values),
                "value_max": max(values),
                "amplitude": max(values) - min(values),
                "key_value_count": len(values),
            }
        )
    return rows


def build_motion_curve_archetypes(render_manifest: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for model in render_manifest.get("models", []):
        motion_paths = (model.get("local_paths", {}) or {}).get("motion3_json", []) or []
        for motion_rel in motion_paths:
            motion_path = existing_path(motion_rel)
            if not motion_path:
                continue
            for curve in parse_motion3(motion_path):
                rows.append(
                    {
                        "model_id": model.get("id"),
                        "motion3_json": rel(motion_path),
                        **curve,
                    }
                )

    by_category: dict[str, Any] = {}
    for category in sorted({row["category"] for row in rows}):
        category_rows = [row for row in rows if row["category"] == category]
        by_param = Counter(row["parameter_id"] for row in category_rows)
        by_category[category] = {
            "curve_count": len(category_rows),
            "model_count": len({row["model_id"] for row in category_rows}),
            "amplitude": numeric_summary([row["amplitude"] for row in category_rows]),
            "top_parameters": by_param.most_common(12),
        }

    return {
        "method": "motion3_json_curve_amplitude_archetype_summary",
        "limitation": "motion3 곡선은 샘플 모션 의도다. tracking 자연스러움은 runtime visual/GIF 검수와 함께 봐야 한다.",
        "curve_count": len(rows),
        "motion_file_count": len({row["motion3_json"] for row in rows}),
        "summary_by_category": by_category,
        "rows_sample": rows[:5000],
    }


def load_cmo3_by_model(cmo3_summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for model in cmo3_summary.get("models", []) or []:
        path = existing_path(model.get("json"))
        if path:
            result[model.get("id")] = load_json(path)
    return result


def cmo3_count_value(counts: dict[str, Any], key: str) -> int:
    value = counts.get(key, 0)
    if isinstance(value, dict):
        return int(value.get("definitions", 0) or value.get("references", 0) or 0)
    if isinstance(value, (int, float, str)):
        try:
            return int(value)
        except ValueError:
            return 0
    return 0


def build_mask_draw_order_risk_map(
    render_manifest: dict[str, Any],
    runtime_report: dict[str, Any],
    cmo3_summary: dict[str, Any],
    visual_diff: dict[str, Any],
    core_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cmo3_by_model = load_cmo3_by_model(cmo3_summary)
    core_by_model = {row.get("id") or row.get("safe_id"): row for row in (core_report or {}).get("models", [])}
    diff_by_model_cat: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in visual_diff.get("rows", []):
        if row["category"] != "motion":
            diff_by_model_cat[(row["model_id"], row["category"])].append(row["changed_ratio"])

    runtime_by_id = {model.get("id"): model for model in runtime_report.get("models", []) or []}
    rows: list[dict[str, Any]] = []
    for model in render_manifest.get("models", []):
        model_id = model.get("id")
        cmo3 = cmo3_by_model.get(model_id, {})
        core_row = core_by_model.get(model_id, {})
        core_counts = core_row.get("counts", {}) or {}
        counts = cmo3.get("counts", {}) or {}
        local_paths = model.get("local_paths", {}) or {}
        mask_count = int(core_counts.get("maskedDrawables", 0) or cmo3_count_value(counts, "CClippingMaskSource"))
        inverted_mask_count = int(core_counts.get("invertedMaskDrawables", 0) or cmo3_count_value(counts, "CInvertedMaskSource"))
        offscreen_count = int(core_counts.get("offscreens", 0) or 0)
        masked_offscreen_count = int(core_counts.get("maskedOffscreens", 0) or 0)
        glue_count = cmo3_count_value(counts, "CGlueSource")
        exp_count = len(local_paths.get("exp3_json", []) or [])
        pose_present = bool(local_paths.get("pose3_json"))
        risk_reasons = []
        risk_score = 0
        if mask_count:
            risk_score += min(35, mask_count * 3)
            risk_reasons.append(f"mask_count={mask_count}")
        if inverted_mask_count:
            risk_score += min(20, inverted_mask_count * 8)
            risk_reasons.append(f"inverted_mask_count={inverted_mask_count}")
        if offscreen_count:
            risk_score += min(18, offscreen_count * 4)
            risk_reasons.append(f"core_offscreen_count={offscreen_count}")
        if masked_offscreen_count:
            risk_score += min(16, masked_offscreen_count * 8)
            risk_reasons.append(f"core_masked_offscreen_count={masked_offscreen_count}")
        if pose_present:
            risk_score += 8
            risk_reasons.append("pose3_json_present")
        if exp_count:
            risk_score += min(12, exp_count)
            risk_reasons.append(f"expression_count={exp_count}")
        if glue_count:
            risk_score += min(10, glue_count * 5)
            risk_reasons.append(f"glue_count={glue_count}")
        for category in ("hair", "eye", "mouth", "body_angle", "arm"):
            ratios = diff_by_model_cat.get((model_id, category), [])
            if ratios and max(ratios) >= 0.08:
                risk_score += 5
                risk_reasons.append(f"large_{category}_visual_sweep={round(max(ratios), 4)}")
        runtime_categories = runtime_by_id.get(model_id, {}).get("categories", {}) or {}
        if runtime_categories.get("arm", {}).get("matched_parameters"):
            risk_score += 4
            risk_reasons.append("arm_switch_or_motion_parameters_present")

        if risk_score >= 45:
            level = "HIGH"
        elif risk_score >= 20:
            level = "MEDIUM"
        else:
            level = "LOW"
        rows.append(
            {
                "model_id": model_id,
                "risk_level": level,
                "risk_score": risk_score,
                "mask_count": mask_count,
                "inverted_mask_count": inverted_mask_count,
                "offscreen_count": offscreen_count,
                "masked_offscreen_count": masked_offscreen_count,
                "glue_count": glue_count,
                "pose_present": pose_present,
                "expression_count": exp_count,
                "core_snapshot_path": core_row.get("snapshot_path"),
                "risk_reasons": risk_reasons,
            }
        )
    return {
        "method": "official_core_drawable_mask_counts_plus_cmo3_assets_plus_visual_sweep_risk_proxy"
        if core_report
        else "cmo3_mask_counts_plus_runtime_assets_plus_visual_sweep_risk_proxy",
        "core_report": rel(DEFAULT_CORE_REPORT) if core_report else None,
        "limitation": "Core extractor가 drawable mask/draw order/offscreen을 제공한다. 단, 사람 눈의 앞뒤 순서 자연스러움은 G3 visual strip과 함께 확인한다."
        if core_report
        else "정확한 drawable draw order와 per-drawable mask 연결은 Cubism Core drawable extractor가 붙으면 보강된다.",
        "risk_counts": dict(Counter(row["risk_level"] for row in rows)),
        "rows": rows,
    }


def build_official_core_extractor_gate(render_manifest: dict[str, Any], core_report: dict[str, Any] | None = None) -> dict[str, Any]:
    candidate_paths = [
        EXPERIMENT / "probe_sandbox" / "strong20" / "Core" / "live2dcubismcore.d.ts",
        EXPERIMENT / "probe_sandbox" / "strong20" / "Core" / "live2dcubismcore.js",
        EXPERIMENT / "probe_sandbox" / "strong20" / "Core" / "live2dcubismcore.min.js",
        ROOT
        / "experiments"
        / "reference-model-structure-001"
        / "official_github_samples"
        / "repos"
        / "live2d_cubism_web_samples"
        / "Core"
        / "live2dcubismcore.d.ts",
    ]
    existing = [path for path in candidate_paths if path.exists()]
    api_names: list[str] = []
    typed_surfaces: dict[str, list[str]] = {}
    for path in existing:
        if path.suffix == ".ts" or path.name.endswith(".d.ts"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            api_names.extend(sorted(set(re.findall(r"\bcsm[A-Za-z0-9_]+", text))))
            for class_name in ("Parameters", "Parts", "Drawables", "Offscreens", "CanvasInfo"):
                match = re.search(rf"class {class_name} \{{(?P<body>.*?)\n    \}}", text, re.S)
                if not match:
                    continue
                props = sorted(set(re.findall(r"\n\s{8}([A-Za-z][A-Za-z0-9_]+):", match.group("body"))))
                typed_surfaces[class_name] = props
        elif path.name.endswith(".js"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            api_names.extend(sorted(set(re.findall(r"\b_csmGet[A-Za-z0-9_]+", text))))
    relevant_core_exports = [
        name
        for name in api_names
        if any(token in name.lower() for token in ("parameter", "drawable", "canvas", "part", "mask", "dynamicflag"))
    ]
    model_count_with_moc3 = sum(1 for m in render_manifest.get("models", []) if (m.get("local_paths", {}) or {}).get("moc3"))
    extracted_status = None
    if core_report:
        summary = core_report.get("summary", {})
        if core_report.get("status") == "PASS" and summary.get("pass_count") == model_count_with_moc3:
            extracted_status = "PASS_CORE_API_EXTRACTED"
        else:
            extracted_status = "WARN_CORE_API_PARTIAL"
    status = extracted_status or ("READY_TO_IMPLEMENT_BROWSER_CORE_EXTRACTOR" if existing and model_count_with_moc3 else "BLOCKED")
    return {
        "method": "official_cubism_core_file_and_api_surface_gate",
        "status": status,
        "core_files_found": [rel(path) for path in existing],
        "models_with_moc3": model_count_with_moc3,
        "core_extractor_report": rel(DEFAULT_CORE_REPORT) if core_report else None,
        "core_extractor_summary": core_report.get("summary") if core_report else None,
        "typed_surfaces": typed_surfaces,
        "relevant_core_exports_sample": sorted(set(relevant_core_exports))[:120],
        "recommended_next_extractor": {
            "entrypoint": "Web sandbox page loads live2dcubismcore.js, reads moc3 ArrayBuffer, and emits parameter/drawable/mask canvas data.",
            "expected_fields": [
                "parameter ids/min/default/max/type",
                "part ids",
                "drawable ids/render order/draw order",
                "drawable vertex/index counts",
                "drawable masks and inverted masks",
                "dynamic flags after parameter update",
            ],
        },
        "interpretation": "CMO3 inspector는 편집 프로젝트 구조 분석에 강하고, Cubism Core extractor는 runtime drawable/parameter/mask 상태 분석의 공식 SDK 계열 보강책이다.",
    }


def build_markdown(report: dict[str, Any]) -> str:
    visual = report["visual_diff_sweep"]
    influence = report["parameter_influence_map"]
    physics = report["physics_response_curve"]
    motion = report["motion_curve_archetypes"]
    risk = report["mask_draw_order_risk_map"]
    core = report["official_cubism_core_extractor"]

    lines = [
        "# Live2D Deep Reference Motion Analysis",
        "",
        "## 결론",
        "",
        "- 기존 분석은 `CMO3 inspector + model3/physics3/motion3 JSON + Web runtime capture`라서 공식 Cubism runtime 흐름에 꽤 가깝다.",
        "- 더 공식적인 보강은 `Cubism Core`로 `.moc3` drawable/parameter/mask를 직접 읽는 extractor다.",
        "- 이번 리포트는 기존 strong20 캡처를 수치화해서 parameter influence, motion curve, physics proxy, mask/draw-order risk를 추가한다.",
        "",
        "## Visual Diff Sweep",
        "",
        f"- 방식: `{visual['method']}`",
        f"- diff threshold: `{visual['diff_threshold_luma']}`",
    ]
    for category, item in sorted(visual["summary_by_category"].items()):
        changed = item["changed_ratio"]
        lines.append(
            f"- `{category}`: samples={item['samples']}, median_changed={changed.get('median')}, p90={changed.get('p90')}, max={changed.get('max')}"
        )

    lines += [
        "",
        "## Parameter Influence",
        "",
        f"- parameter count: `{influence['parameter_count']}`",
        f"- 한계: {influence['limitation']}",
        "",
        "## Physics Response Proxy",
        "",
        f"- models with physics: `{physics['models_with_physics']}/{physics['model_count']}`",
        f"- physics group median: `{physics['group_count_summary'].get('median')}`",
        f"- median delay summary: `{physics['median_delay_summary'].get('median')}`",
        f"- output categories: `{physics['output_categories']}`",
        "",
        "## Motion Curve Archetypes",
        "",
        f"- motion files: `{motion['motion_file_count']}`",
        f"- curve count: `{motion['curve_count']}`",
    ]
    for category, item in sorted(motion["summary_by_category"].items()):
        amp = item["amplitude"]
        lines.append(
            f"- `{category}`: curves={item['curve_count']}, models={item['model_count']}, median_amp={amp.get('median')}, p90_amp={amp.get('p90')}"
        )

    lines += [
        "",
        "## Mask / Draw Order Risk",
        "",
        f"- risk counts: `{risk['risk_counts']}`",
        f"- 한계: {risk['limitation']}",
        "",
        "## Official Cubism Core Extractor Gate",
        "",
        f"- status: `{core['status']}`",
        f"- models with moc3: `{core['models_with_moc3']}`",
        f"- core files found: `{len(core['core_files_found'])}`",
        f"- extractor report: `{core.get('core_extractor_report')}`",
        "- 현재 보강: Web sandbox에서 Core-backed parameter/drawable/mask/dynamic flag snapshot을 직접 덤프한다.",
        "",
        "## Production 적용",
        "",
        "- `v2_standard` 파츠 설계에는 visual diff가 큰 eye/mouth/hair/body parameter를 우선 keyform 검수 대상으로 둔다.",
        "- physics는 hair/body 입력에서 hair/clothing 출력으로 이어지는 그룹을 기본값으로 삼는다.",
        "- mask/draw-order risk가 높은 구조는 새 모델에서 최소화하고, 필요한 경우 G3 motion visual에서 onion-skin/diff로 별도 확인한다.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    render_manifest = load_json(args.render_manifest)
    runtime_report = load_json(args.runtime_report)
    cmo3_summary = load_json(args.cmo3_summary)
    core_report = load_json(args.core_report) if args.core_report.exists() else None

    visual_diff = build_visual_diff_sweep(runtime_report, args.diff_threshold)
    parameter_influence = build_parameter_influence_map(runtime_report, visual_diff)
    physics_response = build_physics_response_curve(render_manifest)
    motion_archetypes = build_motion_curve_archetypes(render_manifest)
    mask_risk = build_mask_draw_order_risk_map(render_manifest, runtime_report, cmo3_summary, visual_diff, core_report)
    core_gate = build_official_core_extractor_gate(render_manifest, core_report)

    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "kind": "live2d_deep_reference_motion_analysis",
        "inputs": {
            "render_manifest": rel(args.render_manifest),
            "runtime_report": rel(args.runtime_report),
            "cmo3_summary": rel(args.cmo3_summary),
            "core_report": rel(args.core_report) if core_report else None,
        },
        "policy": {
            "asset_reuse": "FORBIDDEN",
            "evidence_scope": "local numeric/capture/reference reports only",
            "official_art_publication": "do not publish captured sample art outside local evidence",
        },
        "visual_diff_sweep": visual_diff,
        "parameter_influence_map": parameter_influence,
        "physics_response_curve": physics_response,
        "motion_curve_archetypes": motion_archetypes,
        "mask_draw_order_risk_map": mask_risk,
        "official_cubism_core_extractor": core_gate,
    }

    out_json = args.out_dir / "deep_reference_motion_analysis.json"
    out_md = args.out_dir / "deep_reference_motion_analysis.md"
    write_json(out_json, report)
    out_md.write_text(build_markdown(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "PASS",
                "json": rel(out_json),
                "markdown": rel(out_md),
                "visual_diff_rows": len(visual_diff.get("rows", [])),
                "parameter_count": parameter_influence.get("parameter_count"),
                "physics_models": physics_response.get("models_with_physics"),
                "motion_curves": motion_archetypes.get("curve_count"),
                "core_gate": core_gate.get("status"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

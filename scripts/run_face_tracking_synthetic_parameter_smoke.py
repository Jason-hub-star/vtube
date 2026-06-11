#!/usr/bin/env python3
"""Run T0 synthetic face-tracking to Cubism parameter conversion smoke."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "experiments" / "reference-model-structure-001" / "reports"
DEFAULT_MAP = REPORTS / "face_tracking_to_cubism_parameter_map.json"
DEFAULT_OUT_DIR = REPORTS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
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


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def normalize_centered(value: float, lo: float, hi: float) -> float:
    max_abs = max(abs(lo), abs(hi)) or 1.0
    return clamp(value / max_abs, -1.0, 1.0)


def remap_deadzone(value: float, deadzone: float, max_value: float) -> float:
    if value <= deadzone:
        return 0.0
    if max_value <= deadzone:
        return 1.0
    return clamp((value - deadzone) / (max_value - deadzone), 0.0, 1.0)


def avg(*values: float) -> float:
    return sum(values) / len(values) if values else 0.0


def synthetic_samples() -> list[dict[str, Any]]:
    base = {
        "head_yaw": 0.0,
        "head_pitch": 0.0,
        "head_roll": 0.0,
        "eyeBlinkLeft": 0.0,
        "eyeBlinkRight": 0.0,
        "eye_gaze_x": 0.0,
        "eye_gaze_y": 0.0,
        "jawOpen": 0.0,
        "mouthSmileLeft": 0.0,
        "mouthSmileRight": 0.0,
        "mouthFrownLeft": 0.0,
        "mouthFrownRight": 0.0,
        "time": 0.0,
    }

    def sample(sample_id: str, label_ko: str, **overrides: float) -> dict[str, Any]:
        values = dict(base)
        values.update(overrides)
        return {"id": sample_id, "label_ko": label_ko, "inputs": values}

    return [
        sample("neutral", "중립"),
        sample("head_left", "고개 왼쪽", head_yaw=-25),
        sample("head_right", "고개 오른쪽", head_yaw=25),
        sample("look_up", "고개 위", head_pitch=20),
        sample("look_down", "고개 아래", head_pitch=-20),
        sample("tilt_left", "고개 기울임 왼쪽", head_roll=-25),
        sample("tilt_right", "고개 기울임 오른쪽", head_roll=25),
        sample("blink_left", "왼눈 감기", eyeBlinkLeft=1),
        sample("blink_right", "오른눈 감기", eyeBlinkRight=1),
        sample("blink_both", "양눈 감기", eyeBlinkLeft=1, eyeBlinkRight=1),
        sample("gaze_left", "시선 왼쪽", eye_gaze_x=-1),
        sample("gaze_right", "시선 오른쪽", eye_gaze_x=1),
        sample("gaze_up", "시선 위", eye_gaze_y=1),
        sample("gaze_down", "시선 아래", eye_gaze_y=-1),
        sample("mouth_deadzone", "입 닫힘 deadzone", jawOpen=0.05),
        sample("mouth_open", "입 열기", jawOpen=0.85),
        sample("smile", "웃음", mouthSmileLeft=0.8, mouthSmileRight=0.8),
        sample("frown", "찡그림", mouthFrownLeft=0.7, mouthFrownRight=0.7),
        sample(
            "combined_stress",
            "복합 스트레스",
            head_yaw=18,
            head_pitch=-12,
            head_roll=11,
            eyeBlinkLeft=0.25,
            eyeBlinkRight=0.1,
            eye_gaze_x=0.55,
            eye_gaze_y=-0.45,
            jawOpen=0.62,
            mouthSmileLeft=0.55,
            mouthSmileRight=0.35,
            mouthFrownLeft=0.05,
            mouthFrownRight=0.1,
            time=0.75,
        ),
        sample("breath_peak", "숨 최대", time=0.25),
    ]


def convert_sample(inputs: dict[str, float]) -> dict[str, float]:
    head_yaw = inputs["head_yaw"]
    head_pitch = inputs["head_pitch"]
    head_roll = inputs["head_roll"]
    return {
        "ParamAngleX": clamp(normalize_centered(head_yaw, -25, 25) * 30, -30, 30),
        "ParamAngleY": clamp(normalize_centered(head_pitch, -20, 20) * 30, -30, 30),
        "ParamAngleZ": clamp(normalize_centered(head_roll, -25, 25) * 30, -30, 30),
        "ParamEyeLOpen": clamp(1 - inputs["eyeBlinkLeft"], 0, 1),
        "ParamEyeROpen": clamp(1 - inputs["eyeBlinkRight"], 0, 1),
        "ParamEyeBallX": clamp(inputs["eye_gaze_x"], -1, 1),
        "ParamEyeBallY": clamp(inputs["eye_gaze_y"], -1, 1),
        "ParamMouthOpenY": clamp(remap_deadzone(inputs["jawOpen"], 0.08, 0.85), 0, 1),
        "ParamMouthForm": clamp(
            avg(inputs["mouthSmileLeft"], inputs["mouthSmileRight"])
            - avg(inputs["mouthFrownLeft"], inputs["mouthFrownRight"]),
            -1,
            1,
        ),
        "ParamBodyAngleX": clamp(normalize_centered(head_yaw, -25, 25) * 10 * 0.65, -10, 10),
        "ParamBodyAngleY": clamp(normalize_centered(head_pitch, -20, 20) * 10 * 0.45, -10, 10),
        "ParamBodyAngleZ": clamp(normalize_centered(head_roll, -25, 25) * 10 * 0.5, -10, 10),
        "ParamBreath": clamp(0.5 + 0.5 * math.sin(inputs["time"] * math.tau), 0, 1),
    }


def output_ranges(mapping_spec: dict[str, Any]) -> dict[str, tuple[float, float]]:
    ranges: dict[str, tuple[float, float]] = {}
    for mapping in mapping_spec.get("mappings", []) or []:
        param = mapping.get("cubism_parameter")
        out_range = mapping.get("output_range")
        if not param or not isinstance(out_range, list) or len(out_range) != 2:
            continue
        if "/" in param:
            continue
        ranges[param] = (float(out_range[0]), float(out_range[1]))
    return ranges


def required_outputs(mapping_spec: dict[str, Any]) -> list[str]:
    outputs = list(
        mapping_spec.get("current_asset_readiness", {}).get("required_parameters_from_production_spec", [])
        or []
    )
    for mapping in mapping_spec.get("mappings", []) or []:
        if mapping.get("priority") != "REQUIRED":
            continue
        param = mapping.get("cubism_parameter")
        if param and "/" not in param and param not in outputs:
            outputs.append(param)
    return outputs


def analyze(mapping_spec: dict[str, Any]) -> dict[str, Any]:
    ranges = output_ranges(mapping_spec)
    required = required_outputs(mapping_spec)
    rows = []
    failures = []
    for sample in synthetic_samples():
        outputs = convert_sample(sample["inputs"])
        checks = {}
        for param, value in outputs.items():
            lo, hi = ranges.get(param, (-math.inf, math.inf))
            ok = math.isfinite(value) and lo <= value <= hi
            checks[param] = {
                "value": round(value, 6),
                "range": [lo, hi],
                "in_range": ok,
            }
            if not ok:
                failures.append(
                    {
                        "sample": sample["id"],
                        "parameter": param,
                        "value": value,
                        "range": [lo, hi],
                    }
                )
        missing_required = [param for param in required if param not in outputs]
        if missing_required:
            failures.append({"sample": sample["id"], "missing_required": missing_required})
        rows.append(
            {
                "sample_id": sample["id"],
                "label_ko": sample["label_ko"],
                "inputs": sample["inputs"],
                "outputs": {key: round(value, 6) for key, value in outputs.items()},
                "checks": checks,
                "missing_required": missing_required,
                "status": "PASS" if not missing_required and all(item["in_range"] for item in checks.values()) else "FAIL",
            }
        )

    required_coverage = {param: all(param in row["outputs"] for row in rows) for param in required}
    parameter_extrema = {}
    for param in sorted(rows[0]["outputs"]):
        values = [row["outputs"][param] for row in rows]
        parameter_extrema[param] = {"min": min(values), "max": max(values)}

    return {
        "rows": rows,
        "failures": failures,
        "required_outputs": required,
        "required_coverage": required_coverage,
        "parameter_extrema": parameter_extrema,
    }


def build_report(mapping_path: Path, mapping_spec: dict[str, Any]) -> dict[str, Any]:
    result = analyze(mapping_spec)
    status = "PASS" if not result["failures"] and all(result["required_coverage"].values()) else "FAIL"
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "test_id": "T0_static_sample_json",
        "status": status,
        "inputs": {
            "mapping_spec": rel(mapping_path),
        },
        "summary": {
            "sample_count": len(result["rows"]),
            "required_output_count": len(result["required_outputs"]),
            "failure_count": len(result["failures"]),
            "all_required_covered": all(result["required_coverage"].values()),
            "webcam_required": False,
        },
        "interpretation": {
            "ko": "웹캠 없이 synthetic tracking 값으로 Cubism parameter 변환 공식과 범위를 검증한다. 이 PASS는 live tracking 성공이 아니라 mapping smoke 성공이다.",
            "next": "T1_webcam_tracking_probe에서 실제 MediaPipe webcam/recorded-video 입력을 저장해야 live tracking 경로로 진입한다.",
        },
        "required_coverage": result["required_coverage"],
        "parameter_extrema": result["parameter_extrema"],
        "failures": result["failures"],
        "rows": result["rows"],
    }


def write_md(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Face Tracking Synthetic Parameter Smoke",
        "",
        "## Summary",
        "",
        f"- status: `{report['status']}`",
        f"- test: `{report['test_id']}`",
        f"- sample_count: `{report['summary']['sample_count']}`",
        f"- required_output_count: `{report['summary']['required_output_count']}`",
        f"- failure_count: `{report['summary']['failure_count']}`",
        f"- webcam_required: `{report['summary']['webcam_required']}`",
        "",
        "## Interpretation",
        "",
        f"- {report['interpretation']['ko']}",
        f"- next: {report['interpretation']['next']}",
        "",
        "## Required Coverage",
        "",
        "| Parameter | Covered |",
        "|---|---:|",
    ]
    for param, covered in sorted(report["required_coverage"].items()):
        lines.append(f"| `{param}` | `{covered}` |")
    lines += [
        "",
        "## Parameter Extrema",
        "",
        "| Parameter | Min | Max |",
        "|---|---:|---:|",
    ]
    for param, extrema in sorted(report["parameter_extrema"].items()):
        lines.append(f"| `{param}` | {extrema['min']} | {extrema['max']} |")
    lines += [
        "",
        "## Samples",
        "",
        "| Sample | Label | Status | Key Outputs |",
        "|---|---|---|---|",
    ]
    key_params = [
        "ParamAngleX",
        "ParamAngleY",
        "ParamAngleZ",
        "ParamEyeLOpen",
        "ParamEyeROpen",
        "ParamEyeBallX",
        "ParamEyeBallY",
        "ParamMouthOpenY",
        "ParamMouthForm",
        "ParamBodyAngleX",
        "ParamBodyAngleY",
        "ParamBreath",
    ]
    for row in report["rows"]:
        outputs = ", ".join(f"{param}={row['outputs'][param]}" for param in key_params if param in row["outputs"])
        lines.append(f"| `{row['sample_id']}` | {row['label_ko']} | `{row['status']}` | {outputs} |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    mapping_spec = load_json(args.map)
    report = build_report(args.map, mapping_spec)
    out_json = args.out_dir / "face_tracking_synthetic_parameter_smoke.json"
    out_md = args.out_dir / "face_tracking_synthetic_parameter_smoke.md"
    write_json(out_json, report)
    write_md(out_md, report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "json": rel(out_json),
                "markdown": rel(out_md),
                "summary": report["summary"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

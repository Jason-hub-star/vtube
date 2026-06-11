#!/usr/bin/env python3
"""Score Mini Cubism Physics v0.3 motion evidence."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_REQUIRED_SCENARIOS = {"angle_swing", "hair_settle", "mouth_talk", "eye_blink"}
DEFAULT_MOUTH_STATES = {
    "0": ["mouth_line"],
    "0.5": ["mouth_half_open"],
    "1": ["mouth_open"],
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def magnitude(value: list[float]) -> float:
    return math.sqrt(sum(float(item) ** 2 for item in value))


def scenario_map(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {scenario["name"]: scenario for scenario in report.get("scenarios", [])}


def required_scenarios(project: dict[str, Any]) -> set[str]:
    configured = project.get("physics_requirements", {}).get("required_scenarios")
    if configured:
        return set(configured)
    return DEFAULT_REQUIRED_SCENARIOS


def score_gifs(scenarios: dict[str, dict[str, Any]], required: set[str]) -> list[dict[str, Any]]:
    results = []
    for name in required:
        scenario = scenarios.get(name)
        gif = Path(scenario.get("gif", "")) if scenario else Path("__missing__")
        results.append({"check": f"{name}_gif_exists", "status": "PASS" if gif.exists() else "FAIL", "path": str(gif)})
    return results


def mouth_states(project: dict[str, Any]) -> dict[str, list[str]]:
    configured = project.get("mouth_visibility_groups", {}).get("states")
    return configured or DEFAULT_MOUTH_STATES


def score_mouth_keyposes(project: dict[str, Any], scenario: dict[str, Any] | None) -> dict[str, Any]:
    if not scenario:
        return {"check": "mouth_keypose_exclusive_opacity", "status": "FAIL", "messages": ["mouth_talk scenario missing"]}
    messages = []
    states = mouth_states(project)
    all_mouth_parts = sorted({part for parts in states.values() for part in parts})
    for frame in scenario.get("frames", []):
        value = frame.get("parameters", {}).get("ParamMouthOpenY")
        opacities = frame.get("snapshot", {}).get("part_opacity", {})
        state_key = str(value)
        expected = set(states.get(state_key, []))
        visible = {part for part in all_mouth_parts if opacities.get(part, 0) > 0.9}
        unexpected = visible - expected
        missing = expected - visible
        if unexpected or missing:
            messages.append(f"frame {frame.get('index')} expected {sorted(expected)}, got {sorted(visible)}")
    return {"check": "mouth_keypose_exclusive_opacity", "status": "PASS" if not messages else "FAIL", "messages": messages}


def score_eye_keyposes(project: dict[str, Any], scenario: dict[str, Any] | None) -> dict[str, Any]:
    messages = []
    bindings = project.get("keyform_bindings", [])
    for parameter_id, target_id in [("ParamEyeLOpen", "Eye_L"), ("ParamEyeROpen", "Eye_R")]:
        values = {item.get("key_value") for item in bindings if item.get("parameter_id") == parameter_id and item.get("target_id") == target_id}
        for expected in {0, 0.5}:
            if expected not in values:
                messages.append(f"{parameter_id}/{target_id} missing key_value {expected}")
    if not scenario:
        messages.append("eye_blink scenario missing")
    else:
        hashes = {frame.get("metrics", {}).get("hash") for frame in scenario.get("frames", [])}
        if len(hashes) < 3:
            messages.append("eye_blink has too few distinct visual states")
        hidden_parts = project.get("eye_visibility_groups", {}).get("closed_hidden_parts") or project.get("eye_closed_hidden_parts") or ["L_iris", "R_iris"]
        for frame in scenario.get("frames", []):
            if frame.get("metrics", {}).get("nonBackground", 0) < 1000:
                messages.append(f"eye_blink frame {frame.get('index')} appears blank")
            values = frame.get("parameters", {})
            opacities = frame.get("snapshot", {}).get("part_opacity", {})
            if values.get("ParamEyeLOpen") == 0:
                for part_id in [part for part in hidden_parts if part.endswith("_L") or part.startswith("L_")]:
                    if opacities.get(part_id, 1) > 0.05:
                        messages.append(f"eye_blink frame {frame.get('index')} leaves {part_id} opacity {opacities.get(part_id)}")
            if values.get("ParamEyeROpen") == 0:
                for part_id in [part for part in hidden_parts if part.endswith("_R") or part.startswith("R_")]:
                    if opacities.get(part_id, 1) > 0.05:
                        messages.append(f"eye_blink frame {frame.get('index')} leaves {part_id} opacity {opacities.get(part_id)}")
    return {"check": "eye_open_half_closed_keyposes", "status": "PASS" if not messages else "FAIL", "messages": messages}


def score_physics_targets(project: dict[str, Any], scenarios: dict[str, dict[str, Any]]) -> dict[str, Any]:
    messages = []
    requirements = project.get("physics_requirements", {})
    minimum_active = int(requirements.get("minimum_active_profiles", 3))
    minimum_targets = int(requirements.get("minimum_physics_targets", 3))
    target_stats: dict[str, dict[str, float]] = {}
    for scenario_name in ["angle_swing", "hair_settle"]:
        scenario = scenarios.get(scenario_name)
        if not scenario:
            messages.append(f"{scenario_name} missing")
            continue
        for frame in scenario.get("frames", []):
            for profile_id, state in frame.get("snapshot", {}).get("physics", {}).items():
                stats = target_stats.setdefault(profile_id, {"max_offset": 0, "max_velocity": 0})
                stats["max_offset"] = max(stats["max_offset"], magnitude(state.get("offset", [0, 0])))
                stats["max_velocity"] = max(stats["max_velocity"], magnitude(state.get("velocity", [0, 0])))
    active = [profile_id for profile_id, stats in target_stats.items() if stats["max_offset"] >= 0.5]
    project_parts = {part.get("id") for part in project.get("parts", [])}
    target_count = sum(1 for profile in project.get("physics_profiles", []) for target in profile.get("targets", []) if target in project_parts)
    if len(active) < minimum_active:
        messages.append(f"expected at least {minimum_active} active physics profiles, got {active}")
    if target_count < minimum_targets:
        messages.append(f"expected at least {minimum_targets} physics targets, got {target_count}")
    settle = scenarios.get("hair_settle")
    if settle:
        final = settle.get("frames", [])[-1]
        for profile_id, state in final.get("snapshot", {}).get("physics", {}).items():
            if magnitude(state.get("offset", [0, 0])) > 0.25 or magnitude(state.get("velocity", [0, 0])) > 0.25:
                messages.append(f"{profile_id} did not settle: {state}")
    return {
        "check": "spring_damper_profiles_active_and_settle",
        "status": "PASS" if not messages else "FAIL",
        "active_profiles": active,
        "minimum_active_profiles": minimum_active,
        "physics_target_count": target_count,
        "minimum_physics_targets": minimum_targets,
        "target_stats": target_stats,
        "messages": messages,
    }


def score_bounds(report: dict[str, Any]) -> dict[str, Any]:
    messages = []
    for scenario in report.get("scenarios", []):
        for frame in scenario.get("frames", []):
            metrics = frame.get("metrics", {})
            if metrics.get("nonBackground", 0) < 1000:
                messages.append(f"{scenario['name']} frame {frame.get('index')} appears blank")
            bounds = metrics.get("contentBounds")
            if not bounds:
                messages.append(f"{scenario['name']} frame {frame.get('index')} missing content bounds")
                continue
            left, top, right, bottom = bounds
            width = metrics.get("width", 2048)
            height = metrics.get("height", 2048)
            if left < 0 or top < 0 or right > width or bottom > height:
                messages.append(f"{scenario['name']} frame {frame.get('index')} bounds exceed canvas: {bounds}")
    return {"check": "nonblank_and_in_canvas", "status": "PASS" if not messages else "FAIL", "messages": messages[:20]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    args = parser.parse_args()

    run_dir = Path(args.run).resolve()
    report_path = run_dir / "reports" / "motion_sweep_report.json"
    if not report_path.exists():
        raise SystemExit(f"missing motion_sweep_report.json: {report_path}")
    motion_report = load_json(report_path)
    project = load_json(Path(motion_report["project"]) / "character.json")
    scenarios = scenario_map(motion_report)
    required = required_scenarios(project)

    checks: list[dict[str, Any]] = []
    missing = sorted(required - scenarios.keys())
    checks.append({"check": "required_scenarios", "status": "PASS" if not missing else "FAIL", "missing": missing})
    checks.extend(score_gifs(scenarios, required))
    checks.append(score_mouth_keyposes(project, scenarios.get("mouth_talk")))
    checks.append(score_eye_keyposes(project, scenarios.get("eye_blink")))
    checks.append(score_physics_targets(project, scenarios))
    checks.append(score_bounds(motion_report))

    status = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    report = {
        "schema_version": 1,
        "generated_at": now(),
        "run": str(run_dir),
        "project": motion_report["project"],
        "status": status,
        "checks": checks,
    }
    score_path = run_dir / "reports" / "physics_score_report.json"
    write_json(score_path, report)
    print(json.dumps({"ok": status == "PASS", "status": status, "report": str(score_path)}, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

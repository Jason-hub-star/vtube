#!/usr/bin/env python3
"""Generate and rank conservative Mini Cubism keyform tuning candidates."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PROFILES: list[dict[str, Any]] = [
    {"id": "balanced_weak", "angle": 0.75, "eye": 0.85, "mouth": 0.8, "hair": 0.75},
    {"id": "balanced_default", "angle": 1.0, "eye": 1.0, "mouth": 1.0, "hair": 1.0},
    {"id": "balanced_strong", "angle": 1.25, "eye": 1.15, "mouth": 1.2, "hair": 1.25},
    {"id": "head_subtle_mouth_clear", "angle": 0.65, "eye": 1.0, "mouth": 1.25, "hair": 0.9},
    {"id": "head_clear_hair_soft", "angle": 1.2, "eye": 1.0, "mouth": 1.0, "hair": 0.7},
    {"id": "eye_soft_expression", "angle": 0.9, "eye": 0.7, "mouth": 1.1, "hair": 0.9},
    {"id": "hair_expression", "angle": 0.95, "eye": 1.0, "mouth": 0.95, "hair": 1.45},
    {"id": "mouth_expression", "angle": 0.9, "eye": 1.0, "mouth": 1.45, "hair": 0.95},
    {"id": "overall_expressive", "angle": 1.4, "eye": 1.2, "mouth": 1.35, "hair": 1.35},
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def scale_from_neutral(value: float, factor: float, minimum: float = 0.04) -> float:
    scaled = 1 + ((value or 1) - 1) * factor
    return round(max(minimum, scaled), 4)


def tune_deltas(binding: dict[str, Any], profile: dict[str, Any]) -> None:
    deltas = binding.get("deltas", {})
    parameter_id = binding.get("parameter_id")
    translate = deltas.get("translate", [0, 0])
    scale = deltas.get("scale", [1, 1])
    rotate = deltas.get("rotate", 0)

    if parameter_id == "ParamAngleX":
        factor = profile["angle"]
        deltas["translate"] = [round(translate[0] * factor, 3), round(translate[1] * factor, 3)]
        deltas["rotate"] = round(rotate * factor, 3)
    elif parameter_id in {"ParamEyeLOpen", "ParamEyeROpen"}:
        factor = profile["eye"]
        deltas["scale"] = [scale_from_neutral(scale[0], factor), scale_from_neutral(scale[1], factor)]
    elif parameter_id == "ParamMouthOpenY":
        factor = profile["mouth"]
        deltas["translate"] = [round(translate[0] * factor, 3), round(translate[1] * factor, 3)]
        deltas["scale"] = [scale_from_neutral(scale[0], factor), scale_from_neutral(scale[1], factor)]
    elif parameter_id == "ParamHairFront":
        factor = profile["hair"]
        deltas["translate"] = [round(translate[0] * factor, 3), round(translate[1] * factor, 3)]
        deltas["rotate"] = round(rotate * factor, 3)
    binding["deltas"] = deltas


def copy_candidate_project(source_project: Path, candidate_project: Path) -> None:
    if candidate_project.exists():
        shutil.rmtree(candidate_project)
    shutil.copytree(
        source_project,
        candidate_project,
        ignore=shutil.ignore_patterns("reports/preview_evidence", "reports/validation_report.json"),
    )


def validate_project(project: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_mini_cubism_project.py"), "--project", str(project)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return {"status": "FAIL", "stdout": completed.stdout, "stderr": completed.stderr}
    return {"status": "PASS", "stdout": completed.stdout, "stderr": completed.stderr}


def run_pose_sweep(project: Path, out: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_mini_cubism_pose_sweep.py"),
            "--project",
            str(project),
            "--out",
            str(out),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    report_path = out / "reports" / "pose_sweep_report.json"
    if completed.returncode != 0 or not report_path.exists():
        return {"status": "FAIL", "score": -999, "stdout": completed.stdout, "stderr": completed.stderr}
    report = load_json(report_path)
    return {
        "status": report.get("status", "REVISE"),
        "score": report.get("score", 0),
        "summary": report.get("summary", {}),
        "report": str(report_path),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def build_candidate(source_project: Path, candidates_dir: Path, index: int, profile: dict[str, Any]) -> dict[str, Any]:
    candidate_id = f"candidate_{index:03d}"
    candidate_dir = candidates_dir / candidate_id
    candidate_project = candidate_dir / "mini_cubism_project"
    candidate_evidence = candidate_dir / "evidence"
    copy_candidate_project(source_project, candidate_project)
    character_path = candidate_project / "character.json"
    character = load_json(character_path)
    for binding in character.get("keyform_bindings", []):
        tune_deltas(binding, profile)
    character["auto_authoring_profile"] = {
        "schema_version": 1,
        "candidate_id": candidate_id,
        "profile": profile,
        "generated_at": now(),
        "source_project": str(source_project),
        "note": "Conservative keyform delta tuning; baseline project was not modified.",
    }
    write_json(character_path, character)

    validation = validate_project(candidate_project)
    if validation["status"] == "PASS":
        sweep = run_pose_sweep(candidate_project, candidate_evidence)
    else:
        sweep = {"status": "FAIL", "score": -999, "summary": {}, "report": None}

    result = {
        "candidate_id": candidate_id,
        "profile": profile,
        "project": str(candidate_project),
        "validation": validation["status"],
        "pose_sweep": sweep,
        "score": sweep.get("score", -999),
        "status": "PASS" if validation["status"] == "PASS" and sweep.get("status") == "PASS" else "REVISE",
    }
    reports_dir = candidate_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    write_json(reports_dir / "candidate_report.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-candidates", type=int, default=9)
    args = parser.parse_args()

    source_project = Path(args.project).resolve()
    out_dir = Path(args.out).resolve()
    candidates_dir = out_dir / "candidates"
    reports_dir = out_dir / "reports"
    candidates_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    if not (source_project / "character.json").exists():
        raise SystemExit(f"missing character.json: {source_project}")

    selected_profiles = PROFILES[: max(1, args.max_candidates)]
    results = [build_candidate(source_project, candidates_dir, index + 1, profile) for index, profile in enumerate(selected_profiles)]
    ranked = sorted(results, key=lambda item: item["score"], reverse=True)
    report = {
        "schema_version": 1,
        "generated_at": now(),
        "source_project": str(source_project),
        "status": "PASS" if ranked and ranked[0]["score"] > 0 else "REVISE",
        "best_candidate_id": ranked[0]["candidate_id"] if ranked else None,
        "best_candidate_project": ranked[0]["project"] if ranked else None,
        "ranked_candidates": ranked,
    }
    report_path = reports_dir / "candidate_score_report.json"
    write_json(report_path, report)
    print(
        json.dumps(
            {
                "ok": True,
                "status": report["status"],
                "best_candidate_id": report["best_candidate_id"],
                "report": str(report_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

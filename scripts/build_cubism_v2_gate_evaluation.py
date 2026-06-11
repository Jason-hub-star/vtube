#!/usr/bin/env python3
"""Evaluate whether the Cubism v2 review gate itself is calibrated.

This is a higher-level evaluation than the validator fixture unit test:

- golden set: official Live2D full-structure models should pass the v2 minimum structure gate.
- bad set: known shallow rig evidence should not pass.
- mutation set: deliberately broken tag fixtures should be detected.

The most important failure is a false pass: bad or mutated evidence observed as PASS.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "experiments" / "cubism-v2-gate-evaluation-001"
SUMMARY = ROOT / "experiments" / "reference-model-structure-001" / "reports" / "reference_model_structure_summary.combined.json"
SPEC = ROOT / "experiments" / "reference-model-structure-001" / "reports" / "cubism_success_pattern_spec.json"
SHALLOW_CMO3 = ROOT / "experiments" / "imagen-live2d-001" / "reports" / "cmo3_structure_report.json"
FIXTURE_SCORE = ROOT / "experiments" / "cubism-v2-validator-fixtures-001" / "reports" / "validator_fixture_score_report.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a Cubism v2 review-gate evaluation report.")
    parser.add_argument("--summary", type=Path, default=SUMMARY)
    parser.add_argument("--spec", type=Path, default=SPEC)
    parser.add_argument("--shallow-cmo3-report", type=Path, default=SHALLOW_CMO3)
    parser.add_argument("--fixture-score", type=Path, default=FIXTURE_SCORE)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--golden-limit", type=int, default=12)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def rel(path: Path | str | None) -> str | None:
    if not path:
        return None
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return p.resolve().as_posix()


def parse_min(value: Any, fallback: int) -> int:
    if isinstance(value, int):
        return value
    text = str(value or "")
    digits = ""
    for char in text:
        if char.isdigit():
            digits += char
        elif digits:
            break
    return int(digits) if digits else fallback


def thresholds(spec: dict[str, Any]) -> dict[str, int]:
    gate = spec.get("minimum_cubism_v2_pass_gate", {})
    return {
        "art_meshes": parse_min(gate.get("art_meshes"), 20),
        "parameters": parse_min(gate.get("parameters"), 15),
        "warp_deformers": parse_min(gate.get("warp_deformers"), 8),
        "rotation_deformers": parse_min(gate.get("rotation_deformers"), 1),
        "keyform_bindings": parse_min(gate.get("keyform_bindings"), 20),
        "physics_groups": 1,
    }


def observed_structure_class(values: dict[str, int], limits: dict[str, int]) -> str:
    required = {
        "art_meshes": values.get("art_meshes", 0),
        "parameters": values.get("parameters", 0),
        "warp_deformers": values.get("warp_deformers", 0),
        "rotation_deformers": values.get("rotation_deformers", 0),
        "keyform_bindings": values.get("keyform_bindings", 0),
        "physics_groups": values.get("physics_groups", 0),
    }
    return "PASS" if all(required[key] >= limits[key] for key in required) else "REVISE"


def official_golden_cases(summary: dict[str, Any], limits: dict[str, int], limit: int) -> list[dict[str, Any]]:
    rows = [
        row
        for row in summary.get("comparison", [])
        if row.get("analysis_mode") == "FULL_STRUCTURE"
        and row.get("license_status") == "OFFICIAL_TERMS_ACCEPTED_BY_USER"
        and row.get("warp_deformers", 0) >= limits["warp_deformers"]
        and row.get("keyform_bindings", 0) >= limits["keyform_bindings"]
        and row.get("physics_groups", 0) >= limits["physics_groups"]
    ]
    rows.sort(
        key=lambda row: (
            -int(row.get("keyform_bindings", 0)),
            -int(row.get("warp_deformers", 0)),
            row.get("id", ""),
        )
    )
    cases = []
    for row in rows[:limit]:
        values = {
            "art_meshes": int(row.get("art_meshes", 0)),
            "parameters": int(row.get("parameters", 0)),
            "warp_deformers": int(row.get("warp_deformers", 0)),
            "rotation_deformers": int(row.get("rotation_deformers", 0)),
            "keyform_bindings": int(row.get("keyform_bindings", 0)),
            "physics_groups": int(row.get("physics_groups", 0)),
        }
        observed = observed_structure_class(values, limits)
        cases.append(
            {
                "case_id": f"golden__{row.get('id')}",
                "set": "golden",
                "expected_class": "PASS",
                "observed_class": observed,
                "model_name": row.get("name"),
                "official_profile_key": row.get("official_profile_key"),
                "values": values,
                "status": "PASS" if observed == "PASS" else "FAIL",
                "source_report": row.get("report"),
            }
        )
    return cases


def cmo3_count(report: dict[str, Any], key: str) -> int:
    return int(report.get("counts", {}).get(key, {}).get("definitions", 0))


def shallow_bad_case(report: dict[str, Any], limits: dict[str, int]) -> dict[str, Any]:
    values = {
        "art_meshes": cmo3_count(report, "CArtMeshSource"),
        "parameters": cmo3_count(report, "CParameterSource"),
        "warp_deformers": cmo3_count(report, "CWarpDeformerSource"),
        "rotation_deformers": cmo3_count(report, "CRotationDeformerSource"),
        "keyform_bindings": cmo3_count(report, "KeyformBindingSource"),
        "physics_groups": cmo3_count(report, "CPhysicsSettingsSource"),
    }
    observed = observed_structure_class(values, limits)
    return {
        "case_id": "bad__imagen_live2d_shallow_rig",
        "set": "bad",
        "expected_class": "REVISE",
        "observed_class": observed,
        "model_name": report.get("experiment_id", "imagen-live2d-001"),
        "values": values,
        "status": "PASS" if observed != "PASS" else "FAIL",
        "source_report": rel(SHALLOW_CMO3),
    }


def mutation_cases(fixture_score: dict[str, Any]) -> list[dict[str, Any]]:
    cases = []
    for case in fixture_score.get("cases", []):
        if case.get("kind") != "issue_tag":
            continue
        observed_ok = case.get("status") == "PASS"
        cases.append(
            {
                "case_id": f"mutation__{case.get('case_id')}",
                "set": "mutation",
                "expected_class": "REVISE",
                "observed_class": "REVISE" if observed_ok else "PASS",
                "expected_tags": case.get("expected", []),
                "observed_tags": case.get("observed", []),
                "status": "PASS" if observed_ok else "FAIL",
                "source_case": case.get("case_id"),
            }
        )
    return cases


def confusion_matrix(cases: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    matrix: dict[str, Counter[str]] = defaultdict(Counter)
    for case in cases:
        matrix[case["expected_class"]][case["observed_class"]] += 1
    return {expected: dict(observed) for expected, observed in matrix.items()}


def score(cases: list[dict[str, Any]], set_name: str) -> dict[str, Any]:
    selected = [case for case in cases if case["set"] == set_name]
    passed = sum(1 for case in selected if case["status"] == "PASS")
    return {
        "passed": passed,
        "total": len(selected),
        "ratio": round(passed / len(selected), 4) if selected else None,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    scores = report["scores"]
    lines = [
        "# Cubism v2 검수기 평가판",
        "",
        f"- status: `{report['status']}`",
        f"- false_pass_count: `{report['false_pass_count']}`",
        f"- golden_score: `{scores['golden_score']['passed']}/{scores['golden_score']['total']}`",
        f"- bad_score: `{scores['bad_score']['passed']}/{scores['bad_score']['total']}`",
        f"- mutation_score: `{scores['mutation_score']['passed']}/{scores['mutation_score']['total']}`",
        f"- human_review_score: `{scores['human_review_score']}`",
        "",
        "## Confusion Matrix",
        "",
        "```json",
        json.dumps(report["confusion_matrix"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Cases",
    ]
    for case in report["cases"]:
        lines.append(
            f"- `{case['case_id']}` {case['set']}: expected `{case['expected_class']}` observed `{case['observed_class']}` => `{case['status']}`"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `false_pass_count`가 0이어야 새 모델 평가에 쓸 수 있습니다.",
            "- golden set은 좋은 공식 모델을 떨어뜨리지 않는지 봅니다.",
            "- bad/mutation set은 나쁜 모델을 PASS로 놓치지 않는지 봅니다.",
            "- human_review_score는 사람이 저장한 판정 데이터가 생긴 뒤 별도로 채웁니다.",
        ]
    )
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    args = parse_args()
    spec = load_json(args.spec)
    summary = load_json(args.summary)
    fixture_score = load_json(args.fixture_score)
    shallow = load_json(args.shallow_cmo3_report)
    limits = thresholds(spec)

    cases = []
    cases.extend(official_golden_cases(summary, limits, args.golden_limit))
    cases.append(shallow_bad_case(shallow, limits))
    cases.extend(mutation_cases(fixture_score))

    false_pass_count = sum(
        1 for case in cases if case["expected_class"] != "PASS" and case["observed_class"] == "PASS"
    )
    failed_cases = [case for case in cases if case["status"] != "PASS"]
    status = "PASS" if false_pass_count == 0 and not failed_cases else "FAIL"
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "thresholds": limits,
        "false_pass_count": false_pass_count,
        "failed_case_count": len(failed_cases),
        "scores": {
            "structure_score": score(cases, "golden"),
            "golden_score": score(cases, "golden"),
            "bad_score": score(cases, "bad"),
            "mutation_score": score(cases, "mutation"),
            "part_score": score(cases, "mutation"),
            "motion_score": "NOT_SCORED_NO_HUMAN_OR_RUNTIME_MOTION_SET",
            "human_review_score": "NOT_SCORED_NO_SAVED_HUMAN_CALIBRATION_SET",
        },
        "confusion_matrix": confusion_matrix(cases),
        "source_reports": {
            "official_summary": rel(args.summary),
            "success_pattern_spec": rel(args.spec),
            "shallow_cmo3_report": rel(args.shallow_cmo3_report),
            "fixture_score": rel(args.fixture_score),
        },
        "cases": cases,
    }

    reports_dir = args.out_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "gate_evaluation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    write_markdown(report, reports_dir / "gate_evaluation_report.md")

    print(f"Wrote {rel(reports_dir / 'gate_evaluation_report.json')}")
    print(json.dumps({"status": status, "false_pass_count": false_pass_count, "cases": len(cases)}, ensure_ascii=False))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

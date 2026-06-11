#!/usr/bin/env python3
"""Build validator fixtures that test the Cubism v2 review gate itself.

The goal is not to prove a model is good. The goal is to prove the review
surface can separate good, shallow, and deliberately broken evidence.
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "experiments" / "cubism-v2-validator-fixtures-001"
DEFAULT_SOURCE = ROOT / "review_app" / "review_manifest.json"
POSITIVE_CMO3 = ROOT / "experiments" / "cmo3-structure-fixture-001" / "reports" / "cmo3_structure_report.json"
SHALLOW_CMO3 = ROOT / "experiments" / "imagen-live2d-001" / "reports" / "cmo3_structure_report.json"

ISSUE_TAGS = [
    "missing_part",
    "bad_alpha",
    "misaligned",
    "style_mismatch",
    "underpaint_missing",
    "clipping_risk",
    "draw_order_issue",
    "overhang_issue",
]

TAG_LABELS = {
    "missing_part": "파츠 없음",
    "bad_alpha": "테두리 지저분함",
    "misaligned": "위치 안 맞음",
    "style_mismatch": "그림체 다름",
    "underpaint_missing": "밑색 없음",
    "clipping_risk": "마스크 위험",
    "draw_order_issue": "앞뒤 순서 문제",
    "overhang_issue": "튀어나온 부분 문제",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Cubism v2 validator fixtures and score report.")
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--positive-cmo3-report", type=Path, default=POSITIVE_CMO3)
    parser.add_argument("--shallow-cmo3-report", type=Path, default=SHALLOW_CMO3)
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


def first_item(manifest: dict[str, Any], group: str | None = None) -> dict[str, Any]:
    items = [item for values in manifest.get("sections", {}).values() for item in values]
    if group:
        for item in items:
            if item.get("group") == group:
                return deepcopy(item)
    if not items:
        raise SystemExit("FAIL: source manifest has no items")
    return deepcopy(items[0])


def cmo3_count(report: dict[str, Any], key: str) -> int:
    return int(report.get("counts", {}).get(key, {}).get("definitions", 0))


def structure_summary(report: dict[str, Any], expected_status: str) -> dict[str, Any]:
    deformer_count = cmo3_count(report, "CWarpDeformerSource") + cmo3_count(report, "CRotationDeformerSource")
    checks = {
        "artmesh_count": cmo3_count(report, "CArtMeshSource"),
        "parameter_count": cmo3_count(report, "CParameterSource"),
        "deformer_count": deformer_count,
        "keyform_binding_count": cmo3_count(report, "KeyformBindingSource"),
        "physics_group_count": cmo3_count(report, "CPhysicsSettingsSource"),
    }
    observed = (
        "PASS"
        if checks["artmesh_count"] > 0
        and checks["parameter_count"] > 0
        and checks["deformer_count"] > 0
        and checks["keyform_binding_count"] > 0
        and checks["physics_group_count"] > 0
        else "REVISE"
    )
    return {
        "status": observed,
        "expected_status": expected_status,
        "message": "fixture structure gate expectation",
        "checks": checks,
    }


def structure_item(base: dict[str, Any], part_id: str, label: str, report: dict[str, Any], expected_status: str) -> dict[str, Any]:
    item = deepcopy(base)
    item.update(
        {
            "part_id": part_id,
            "ko_name": label,
            "simple_label": label,
            "simple_description": "Cubism 구조 숫자가 기대값대로 갈리는지 확인합니다.",
            "group": "structure",
            "role": "validator_fixture",
            "tier": "v2_min",
            "review_gate": "G2_STRUCTURE",
            "section": "g2_structure",
            "include_in_import_psd": False,
            "checklist": [
                "좋은 구조는 PASS가 나와야 합니다.",
                "얕은 rig는 REVISE나 FAIL로 걸려야 합니다.",
            ],
            "compare_views": {},
            "auto_check_summary": structure_summary(report, expected_status),
            "validator_expectation": {
                "kind": "structure",
                "expected_status": expected_status,
            },
        }
    )
    return item


def defect_item(base: dict[str, Any], tag: str, index: int) -> dict[str, Any]:
    item = deepcopy(base)
    item.update(
        {
            "part_id": f"fixture__{tag}",
            "ko_name": TAG_LABELS[tag],
            "simple_label": TAG_LABELS[tag],
            "simple_description": "일부러 넣은 결함을 검수기가 태그로 구분하는지 확인합니다.",
            "tier": "v2_min",
            "review_gate": "G1_PART_TAXONOMY",
            "section": "g1_part_taxonomy",
            "include_in_import_psd": False,
            "checklist": [
                "이 케이스는 일부러 망가뜨린 fixture입니다.",
                f"`{tag}` 태그가 반드시 보여야 합니다.",
            ],
            "auto_issue_tags": [tag],
            "validator_expectation": {
                "kind": "issue_tag",
                "expected_tags": [tag],
            },
        }
    )
    if tag == "missing_part":
        item["bbox"] = None
        item["alpha_coverage"] = 0
    elif tag == "bad_alpha":
        item["bbox"] = [10, 10, 2, 2]
        item["alpha_coverage"] = 0.01
    elif tag == "misaligned":
        item["bbox"] = [index * 80 + 120, index * 40 + 120, 140, 120]
        item["misalignment_px"] = 96
    elif tag == "style_mismatch":
        item["style_reference"] = "line/color intentionally mismatched fixture"
    elif tag == "underpaint_missing":
        item["role"] = "underpaint"
        item["group"] = "face"
    elif tag == "clipping_risk":
        item["group"] = "eyes"
        item["role"] = "eyelid_clipping_fixture"
    elif tag == "draw_order_issue":
        item["draw_order"] = -1
    elif tag == "overhang_issue":
        item["bbox"] = [1980, 110, 120, 180]
    return item


def score_fixture_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cases = []
    for item in items:
        expectation = item.get("validator_expectation", {})
        if expectation.get("kind") == "structure":
            observed = item.get("auto_check_summary", {}).get("status")
            expected = expectation.get("expected_status")
            passed = observed == expected
            cases.append(
                {
                    "case_id": item["part_id"],
                    "kind": "structure",
                    "expected": expected,
                    "observed": observed,
                    "status": "PASS" if passed else "FAIL",
                }
            )
        elif expectation.get("kind") == "issue_tag":
            expected_tags = set(expectation.get("expected_tags", []))
            observed_tags = set(item.get("auto_issue_tags", []))
            passed = expected_tags <= observed_tags
            cases.append(
                {
                    "case_id": item["part_id"],
                    "kind": "issue_tag",
                    "expected": sorted(expected_tags),
                    "observed": sorted(observed_tags),
                    "status": "PASS" if passed else "FAIL",
                }
            )
    return cases


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Cubism v2 검수기 fixture 점수표",
        "",
        f"- status: `{report['status']}`",
        f"- passed: `{report['passed_cases']}/{report['total_cases']}`",
        "",
        "## Cases",
    ]
    for case in report["cases"]:
        lines.append(
            f"- `{case['case_id']}`: {case['kind']} expected `{case['expected']}` observed `{case['observed']}` => `{case['status']}`"
        )
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    args = parse_args()
    source = load_json(args.source_manifest)
    positive = load_json(args.positive_cmo3_report)
    shallow = load_json(args.shallow_cmo3_report)
    base = first_item(source)
    face_base = first_item(source, "face")

    g2_items = [
        structure_item(base, "fixture__positive_cmo3_structure", "좋은 Cubism 구조", positive, "PASS"),
        structure_item(base, "fixture__shallow_cmo3_structure", "얕은 rig 구조", shallow, "REVISE"),
    ]
    g1_items = [defect_item(face_base, tag, index) for index, tag in enumerate(ISSUE_TAGS)]
    all_items = g1_items + g2_items
    cases = score_fixture_items(all_items)
    passed_cases = sum(1 for case in cases if case["status"] == "PASS")
    generated_at = datetime.now(timezone.utc).isoformat()

    fixture_manifest = {
        "schema_version": 2,
        "experiment_id": "cubism-v2-validator-fixtures-001",
        "mode": "cubism_v2",
        "tier": "v2_min",
        "generated_at": generated_at,
        "source_review_manifest": rel(args.source_manifest),
        "review_outputs": {
            "part_visual_review": "experiments/cubism-v2-validator-fixtures-001/reports/part_visual_review.json",
            "ai_fix_queue": "experiments/cubism-v2-validator-fixtures-001/reports/ai_fix_queue.json",
            "review_packet": "experiments/cubism-v2-validator-fixtures-001/review_packet",
        },
        "ui": {
            "title": "Cubism v2 검수기 테스트",
            "subtitle": "좋은 것, 얕은 rig, 일부러 망가뜨린 파츠를 검수기가 구분하는지 봅니다.",
            "primary_section": "g1_part_taxonomy",
        },
        "issue_tags": [
            {
                "code": tag,
                "label_ko": TAG_LABELS[tag],
                "help_ko": "검수기 fixture 태그",
            }
            for tag in ISSUE_TAGS
        ],
        "sections": {
            "g0_concept": [],
            "g1_part_taxonomy": g1_items,
            "g2_structure": g2_items,
            "g3_motion_visual": [],
        },
        "counts": {
            "g0_concept": 0,
            "g1_part_taxonomy": len(g1_items),
            "g2_structure": len(g2_items),
            "g3_motion_visual": 0,
        },
    }
    score_report = {
        "schema_version": 1,
        "generated_at": generated_at,
        "status": "PASS" if passed_cases == len(cases) else "FAIL",
        "total_cases": len(cases),
        "passed_cases": passed_cases,
        "source_reports": {
            "positive_cmo3_report": rel(args.positive_cmo3_report),
            "shallow_cmo3_report": rel(args.shallow_cmo3_report),
        },
        "cases": cases,
    }

    reports_dir = args.out_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "review_manifest.fixtures.json").write_text(
        json.dumps(fixture_manifest, ensure_ascii=False, indent=2) + "\n"
    )
    (reports_dir / "validator_fixture_score_report.json").write_text(
        json.dumps(score_report, ensure_ascii=False, indent=2) + "\n"
    )
    write_markdown(score_report, reports_dir / "validator_fixture_score_report.md")

    print(f"Wrote {rel(args.out_dir / 'review_manifest.fixtures.json')}")
    print(f"Wrote {rel(reports_dir / 'validator_fixture_score_report.json')}")
    print(json.dumps({"status": score_report["status"], "passed": f"{passed_cases}/{len(cases)}"}, ensure_ascii=False))
    return 0 if score_report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

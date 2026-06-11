#!/usr/bin/env python3
"""Build a motion-readiness report for owned/collected official Live2D models."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "experiments" / "reference-model-structure-001" / "reports" / "reference_model_structure_summary.combined.json"
OUT_DIR = ROOT / "experiments" / "live2d-owned-model-motion-readiness-001" / "reports"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Classify Live2D reference models by motion-readiness.")
    parser.add_argument("--summary", type=Path, default=SUMMARY)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def classify(row: dict[str, Any]) -> tuple[str, list[str]]:
    reasons = []
    has_motion = bool(row.get("motion"))
    has_physics = bool(row.get("physics")) and int(row.get("physics_groups", 0) or 0) > 0
    has_source_structure = row.get("analysis_mode") == "FULL_STRUCTURE"
    has_deformers = int(row.get("warp_deformers", 0) or 0) > 0 or int(row.get("rotation_deformers", 0) or 0) > 0
    has_keyforms = int(row.get("keyform_bindings", 0) or 0) > 0

    if has_motion:
        reasons.append("motion3 있음")
    else:
        reasons.append("motion3 없음")
    if has_physics:
        reasons.append(f"physics group {row.get('physics_groups', 0)}개")
    else:
        reasons.append("physics 부족")
    if has_source_structure:
        reasons.append("편집 구조 분석 가능")
    else:
        reasons.append("runtime 구조만 확인")
    if has_deformers:
        reasons.append("deformer 있음")
    if has_keyforms:
        reasons.append("keyform 있음")

    if has_motion and has_physics and has_source_structure and has_deformers and has_keyforms:
        return "STRONG_MOTION_REFERENCE", reasons
    if has_motion and has_physics:
        return "RUNTIME_MOTION_CHECKABLE", reasons
    if has_source_structure and has_deformers and has_keyforms:
        return "STRUCTURE_GOOD_BUT_MOTION_MISSING", reasons
    return "NOT_MOTION_READY", reasons


def motion_score(row: dict[str, Any]) -> int:
    score = 0
    if row.get("motion"):
        score += 25
    if row.get("physics") and int(row.get("physics_groups", 0) or 0) > 0:
        score += 25
    if row.get("analysis_mode") == "FULL_STRUCTURE":
        score += 15
    if int(row.get("warp_deformers", 0) or 0) > 0:
        score += 10
    if int(row.get("rotation_deformers", 0) or 0) > 0:
        score += 5
    if int(row.get("keyform_bindings", 0) or 0) > 0:
        score += 10
    if int(row.get("parameters", 0) or 0) >= 25:
        score += 5
    if int(row.get("physics_groups", 0) or 0) >= 4:
        score += 5
    return score


def to_case(row: dict[str, Any]) -> dict[str, Any]:
    status, reasons = classify(row)
    return {
        "id": row.get("id"),
        "name": row.get("name"),
        "official_profile_key": row.get("official_profile_key"),
        "analysis_mode": row.get("analysis_mode"),
        "motion_readiness": status,
        "motion_score": motion_score(row),
        "reasons": reasons,
        "motion": bool(row.get("motion")),
        "physics": bool(row.get("physics")),
        "physics_groups": int(row.get("physics_groups", 0) or 0),
        "parameters": int(row.get("parameters", 0) or 0),
        "warp_deformers": int(row.get("warp_deformers", 0) or 0),
        "rotation_deformers": int(row.get("rotation_deformers", 0) or 0),
        "keyform_bindings": int(row.get("keyform_bindings", 0) or 0),
        "report": row.get("report"),
    }


def write_md(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# 보유 Live2D 모델 움직임 준비도",
        "",
        f"- total_models: `{report['summary']['total_models']}`",
        f"- strong_motion_reference: `{report['summary']['strong_motion_reference']}`",
        f"- runtime_motion_checkable: `{report['summary']['runtime_motion_checkable']}`",
        f"- structure_good_but_motion_missing: `{report['summary']['structure_good_but_motion_missing']}`",
        f"- not_motion_ready: `{report['summary']['not_motion_ready']}`",
        "",
        "## 결론",
        "",
        "- 레거시 이미지는 실패 fixture 용도일 뿐, 보유 모델 검수 대상이 아닙니다.",
        "- `STRONG_MOTION_REFERENCE` 모델은 구조와 motion/physics가 모두 있어 움직임 기준선으로 쓰기 좋습니다.",
        "- `RUNTIME_MOTION_CHECKABLE` 모델은 실제 렌더링 프리뷰로 움직임 확인은 가능하지만 편집 구조 학습은 제한됩니다.",
        "- 최종적으로 잘 움직이는지는 model3/moc3/motion3를 브라우저 Live2D player에 올려 눈으로 확인해야 합니다.",
        "",
        "## Top Strong Motion References",
    ]
    for item in report["top_strong_motion_references"]:
        lines.append(
            f"- `{item['name']}` score `{item['motion_score']}` / physics `{item['physics_groups']}` / "
            f"deformer `{item['warp_deformers']}+{item['rotation_deformers']}` / keyform `{item['keyform_bindings']}`"
        )
    lines.extend(["", "## Runtime Check Candidates"])
    for item in report["top_runtime_motion_candidates"]:
        lines.append(
            f"- `{item['name']}` score `{item['motion_score']}` / physics `{item['physics_groups']}` / mode `{item['analysis_mode']}`"
        )
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    args = parse_args()
    source = load_json(args.summary)
    rows = [to_case(row) for row in source.get("comparison", [])]
    rows.sort(key=lambda item: (-item["motion_score"], item["name"] or ""))
    counts = {
        "total_models": len(rows),
        "strong_motion_reference": sum(1 for item in rows if item["motion_readiness"] == "STRONG_MOTION_REFERENCE"),
        "runtime_motion_checkable": sum(1 for item in rows if item["motion_readiness"] == "RUNTIME_MOTION_CHECKABLE"),
        "structure_good_but_motion_missing": sum(1 for item in rows if item["motion_readiness"] == "STRUCTURE_GOOD_BUT_MOTION_MISSING"),
        "not_motion_ready": sum(1 for item in rows if item["motion_readiness"] == "NOT_MOTION_READY"),
    }
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_summary": str(args.summary.relative_to(ROOT)) if args.summary.is_absolute() else str(args.summary),
        "summary": counts,
        "top_strong_motion_references": [
            item for item in rows if item["motion_readiness"] == "STRONG_MOTION_REFERENCE"
        ][:15],
        "top_runtime_motion_candidates": [
            item for item in rows if item["motion_readiness"] == "RUNTIME_MOTION_CHECKABLE"
        ][:15],
        "models": rows,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "owned_model_motion_readiness.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    write_md(report, args.out_dir / "owned_model_motion_readiness.md")
    print(f"Wrote {(args.out_dir / 'owned_model_motion_readiness.json').relative_to(ROOT)}")
    print(json.dumps(counts, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

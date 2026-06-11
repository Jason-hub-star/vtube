#!/usr/bin/env python3
"""Build a success-pattern baseline from official profiles and measured reports."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "reference-model-structure-001"
SECTIONS = ["eye", "mouth", "hair", "body_angle", "physics", "mask", "psd_layering", "motion_pose"]
OFFICIAL_SOURCE_TYPES = {"OFFICIAL_SAMPLE_ZIP", "OFFICIAL_GITHUB_SAMPLE"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profiles",
        default=str(EXPERIMENT / "reports" / "official_sample_profiles.json"),
        help="Official sample profile JSON.",
    )
    parser.add_argument(
        "--summary",
        default=str(EXPERIMENT / "reports" / "reference_model_structure_summary.json"),
        help="Measured structure summary JSON.",
    )
    parser.add_argument("--models-dir", default=str(EXPERIMENT / "models"), help="Per-model report directory.")
    parser.add_argument("--out-dir", default=str(EXPERIMENT / "reports"), help="Output reports directory.")
    parser.add_argument("--include-non-official", action="store_true", help="Include non-official seed/local model reports.")
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


def load_model_reports(models_dir: Path, official_only: bool = True) -> list[dict[str, Any]]:
    reports = []
    for path in sorted(models_dir.glob("*/reference_model_report.json")):
        report = load_json(path)
        if official_only and report.get("source_type") not in OFFICIAL_SOURCE_TYPES:
            continue
        reports.append(report)
    return reports


def summarize_reports(reports: list[dict[str, Any]]) -> dict[str, Any]:
    if not reports:
        return {
            "model_count": 0,
            "art_meshes_max": 0,
            "parameters_max": 0,
            "warp_deformers_max": 0,
            "rotation_deformers_max": 0,
            "keyform_bindings_max": 0,
            "physics_groups_max": 0,
            "motion_count_total": 0,
            "expression_count_total": 0,
            "pose_count": 0,
            "psd_count_total": 0,
            "mask_models": 0,
            "glue_models": 0,
            "example_models": [],
        }
    counts = [r.get("structure_counts", {}) for r in reports]
    runtimes = [r.get("runtime_json", {}) for r in reports]
    return {
        "model_count": len(reports),
        "art_meshes_max": max(c.get("art_meshes", 0) for c in counts),
        "parameters_max": max(c.get("parameters", 0) for c in counts),
        "warp_deformers_max": max(c.get("warp_deformers", 0) for c in counts),
        "rotation_deformers_max": max(c.get("rotation_deformers", 0) for c in counts),
        "keyform_bindings_max": max(c.get("keyform_bindings", 0) for c in counts),
        "physics_groups_max": max(rt.get("physics3", {}).get("physics_group_count", 0) for rt in runtimes),
        "physics_inputs_max": max(rt.get("physics3", {}).get("physics_input_count", 0) for rt in runtimes),
        "physics_outputs_max": max(rt.get("physics3", {}).get("physics_output_count", 0) for rt in runtimes),
        "motion_count_total": sum(rt.get("motion3_count", 0) or rt.get("model3", {}).get("motion_count", 0) for rt in runtimes),
        "expression_count_total": sum(rt.get("exp3_count", 0) or rt.get("model3", {}).get("expression_count", 0) for rt in runtimes),
        "pose_count": sum(1 for rt in runtimes if rt.get("pose3_present") or rt.get("model3", {}).get("has_pose")),
        "psd_count_total": sum(
            len((r.get("local_paths", {}).get("psd") or []))
            if isinstance(r.get("local_paths", {}).get("psd"), list)
            else int(bool(r.get("local_paths", {}).get("psd")))
            for r in reports
        ),
        "mask_models": sum(1 for r in reports if r.get("feature_presence", {}).get("mask")),
        "glue_models": sum(1 for r in reports if r.get("feature_presence", {}).get("glue")),
        "example_models": [r.get("id") for r in reports[:8]],
    }


def build_baseline(profiles: dict[str, Any], model_reports: list[dict[str, Any]]) -> dict[str, Any]:
    by_profile: dict[str, list[dict[str, Any]]] = defaultdict(list)
    missing_profile = []
    for report in model_reports:
        key = report.get("official_profile_key") or "OFFICIAL_PROFILE_MISSING"
        if key == "OFFICIAL_PROFILE_MISSING":
            missing_profile.append(report.get("id"))
        by_profile[key].append(report)

    profile_map = {p["profile_key"]: p for p in profiles.get("profiles", [])}
    section_items: dict[str, list[dict[str, Any]]] = {section: [] for section in SECTIONS}
    for key, profile in profile_map.items():
        measured = summarize_reports(by_profile.get(key, []))
        for section, decision in profile.get("expected_success_pattern", {}).items():
            if section not in section_items:
                continue
            section_items[section].append(
                {
                    "profile_key": key,
                    "model": profile.get("display_name"),
                    "decision": decision,
                    "official_learning_target": profile.get("official_learning_target", []),
                    "measured_structure_values": measured,
                    "source_note": profile.get("official_description"),
                }
            )

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_url": profiles.get("source_url"),
        "model_report_count": len(model_reports),
        "sections": section_items,
        "missing_profile_model_ids": missing_profile,
        "new_image_generation_requirements": [
            "완전 신규 2048 정면 단일 원본 캐릭터",
            "눈 흰자/홍채/속눈썹이 분리되기 쉬운 크고 명확한 눈",
            "입 라인이 작게 묻히지 않고 ParamMouthOpenY/Form 기준 keyform을 만들 수 있는 얼굴",
            "앞머리/옆머리/뒷머리 흐름이 구분되는 헤어 실루엣",
            "ParamAngleX/Y와 BodyAngleX/Y에서 overhang이 적도록 목/어깨/상체가 가려지지 않는 구조",
            "초기 모델에서는 무거운 clipping/mask/rich effect를 최소화",
            "텍스트, 라벨, 잘린 팔, 과도한 장식, 복잡한 손가락 겹침 금지",
        ],
        "minimal_cubism_rig_gate": {
            "scope": ["eye", "mouth", "hair", "body_angle"],
            "required_delta": ["warp_deformers > 0", "keyform_bindings > 0"],
            "required_evidence": [
                "before/after cmo3_structure_report.json",
                "deformer hierarchy screenshot",
                "eye/mouth/hair/body angle parameter extreme screenshots",
                "draw order and overhang review note",
            ],
        },
        "interpretation": [
            "Official samples teach structure and rigging patterns only.",
            "Do not reuse official sample images, textures, PSD layers, or character designs.",
            "Use KEEP entries to define the minimum new-model rig checklist.",
        ],
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    chunks = [
        "# Reference Rig Pattern Baseline",
        "",
        f"Generated: {report['generated_at']}",
        "",
        f"Source: {report.get('source_url')}",
        "",
        "This baseline learns structure and rigging patterns only. It must not be used to copy official sample art, textures, PSD layers, or character designs.",
        "",
    ]
    for section in SECTIONS:
        items = report["sections"].get(section, [])
        chunks.extend([f"## {section}", ""])
        if not items:
            chunks.extend(["- NO_PATTERN_FOUND", ""])
            continue
        chunks.append("| Model | Decision | Learning Target | Measured Max Counts |")
        chunks.append("|---|---|---|---|")
        for item in items:
            measured = item["measured_structure_values"]
            target = ", ".join(item.get("official_learning_target", []))
            counts = (
                f"models={measured.get('model_count', 0)}, "
                f"art={measured.get('art_meshes_max', 0)}, "
                f"param={measured.get('parameters_max', 0)}, "
                f"warp={measured.get('warp_deformers_max', 0)}, "
                f"rot={measured.get('rotation_deformers_max', 0)}, "
                f"key={measured.get('keyform_bindings_max', 0)}, "
                f"phys={measured.get('physics_groups_max', 0)}, "
                f"motion={measured.get('motion_count_total', 0)}, "
                f"psd={measured.get('psd_count_total', 0)}"
            )
            chunks.append(f"| {item['model']} | {item['decision']} | {target} | {counts} |")
        chunks.append("")

    chunks.extend(
        [
            "## New Image Generation Requirements",
            "",
            *[f"- {item}" for item in report["new_image_generation_requirements"]],
            "",
            "## Minimal Cubism Rig Gate",
            "",
            f"- Scope: {', '.join(report['minimal_cubism_rig_gate']['scope'])}",
            *[f"- Delta: {item}" for item in report["minimal_cubism_rig_gate"]["required_delta"]],
            *[f"- Evidence: {item}" for item in report["minimal_cubism_rig_gate"]["required_evidence"]],
            "",
        ]
    )
    if report["missing_profile_model_ids"]:
        chunks.extend(["## Missing Profile Model IDs", ""])
        chunks.extend(f"- `{item}`" for item in report["missing_profile_model_ids"])
        chunks.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(chunks), encoding="utf-8")


def main() -> None:
    args = parse_args()
    profiles = load_json(Path(args.profiles).expanduser().resolve())
    model_reports = load_model_reports(
        Path(args.models_dir).expanduser().resolve(),
        official_only=not args.include_non_official,
    )
    report = build_baseline(profiles, model_reports)
    out_dir = Path(args.out_dir).expanduser().resolve()
    write_json(out_dir / "reference_rig_pattern_baseline.json", report)
    write_markdown(out_dir / "reference_rig_pattern_baseline.md", report)
    empty_required = [section for section in ("eye", "mouth", "hair", "body_angle") if not report["sections"].get(section)]
    print(
        json.dumps(
            {
                "ok": not empty_required,
                "model_reports": len(model_reports),
                "empty_required_sections": empty_required,
                "json": rel(out_dir / "reference_rig_pattern_baseline.json"),
                "markdown": rel(out_dir / "reference_rig_pattern_baseline.md"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if empty_required:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

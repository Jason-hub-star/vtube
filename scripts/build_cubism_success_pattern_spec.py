#!/usr/bin/env python3
"""Build the Cubism-first success pattern spec from measured official baselines."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "reference-model-structure-001"


CORE_PROFILES = {
    "mark",
    "hiyori",
    "kei",
    "mao",
    "miku",
    "haru",
    "haru_greeter",
    "koharu",
    "haruto",
    "rice",
    "ren",
    "tsumiki",
    "unitychan",
}


SECTION_TO_PROFILES = {
    "eye": ["mark", "hiyori", "mao", "tsumiki", "unitychan"],
    "mouth": ["kei", "hiyori", "mao", "nito", "mark"],
    "hair": ["hiyori", "mao", "miku", "rice"],
    "body_angle": ["hiyori", "mao", "haru", "chitose", "izumi", "ren"],
    "physics": ["hiyori", "miku", "mao", "ren", "miara", "natori"],
    "psd_layering": ["haru_greeter", "koharu", "haruto", "unitychan"],
    "mask": ["ren", "rice", "tsumiki", "unitychan", "gantzert_felixander"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--summary",
        default=str(EXPERIMENT / "reports" / "reference_model_structure_summary.combined.json"),
        help="Combined structure summary JSON.",
    )
    parser.add_argument(
        "--baseline",
        default=str(EXPERIMENT / "reports" / "reference_rig_pattern_baseline.combined.json"),
        help="Pattern baseline JSON.",
    )
    parser.add_argument("--out-dir", default=str(EXPERIMENT / "reports"), help="Output report directory.")
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


def rows_by_profile(summary: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in summary.get("comparison", []):
        key = row.get("official_profile_key") or "OFFICIAL_PROFILE_MISSING"
        out[key].append(row)
    return out


def nz(values: list[int]) -> list[int]:
    return [v for v in values if v > 0]


def median_or(values: list[int], default: int = 0) -> int:
    filtered = nz(values)
    if not filtered:
        return default
    return int(statistics.median(filtered))


def max_for_profiles(by_profile: dict[str, list[dict[str, Any]]], profiles: list[str], key: str) -> int:
    values = [int(row.get(key, 0) or 0) for profile in profiles for row in by_profile.get(profile, [])]
    return max(values) if values else 0


def core_stats(summary: dict[str, Any]) -> dict[str, Any]:
    rows = [
        row
        for row in summary.get("comparison", [])
        if row.get("analysis_mode") == "FULL_STRUCTURE" and row.get("official_profile_key") in CORE_PROFILES
    ]
    return {
        "model_count": len(rows),
        "art_meshes_median": median_or([row.get("art_meshes", 0) for row in rows]),
        "parameters_median": median_or([row.get("parameters", 0) for row in rows]),
        "warp_deformers_median": median_or([row.get("warp_deformers", 0) for row in rows]),
        "rotation_deformers_median": median_or([row.get("rotation_deformers", 0) for row in rows]),
        "keyform_bindings_median": median_or([row.get("keyform_bindings", 0) for row in rows]),
        "physics_groups_median": median_or([row.get("physics_groups", 0) for row in rows]),
        "art_meshes_min_nonzero": min(nz([row.get("art_meshes", 0) for row in rows]) or [0]),
        "parameters_min_nonzero": min(nz([row.get("parameters", 0) for row in rows]) or [0]),
        "warp_deformers_min_nonzero": min(nz([row.get("warp_deformers", 0) for row in rows]) or [0]),
        "keyform_bindings_min_nonzero": min(nz([row.get("keyform_bindings", 0) for row in rows]) or [0]),
    }


def build_spec(summary: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    by_profile = rows_by_profile(summary)
    stats = core_stats(summary)
    section_reference_max = {
        section: {
            "profiles": profiles,
            "max_art_meshes": max_for_profiles(by_profile, profiles, "art_meshes"),
            "max_parameters": max_for_profiles(by_profile, profiles, "parameters"),
            "max_warp_deformers": max_for_profiles(by_profile, profiles, "warp_deformers"),
            "max_rotation_deformers": max_for_profiles(by_profile, profiles, "rotation_deformers"),
            "max_keyform_bindings": max_for_profiles(by_profile, profiles, "keyform_bindings"),
            "max_physics_groups": max_for_profiles(by_profile, profiles, "physics_groups"),
        }
        for section, profiles in SECTION_TO_PROFILES.items()
    }
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_summary": summary.get("summary", {}),
        "core_official_full_structure_stats": stats,
        "section_reference_max": section_reference_max,
        "position": {
            "deprecated_active_model_fixation": "Do not keep optimizing imagen-live2d-001 as the main production path.",
            "legacy_model_role": "Use imagen-live2d-001 only as a shallow-rig failure fixture unless it is manually rerigged in Cubism.",
            "new_model_rule": "Design the next model from Cubism rig requirements first; image resolution is secondary.",
            "asset_policy": "Do not reuse official sample art, textures, PSD layers, or character designs.",
        },
        "cubism_version_policy": {
            "authoring_target": "Cubism Editor 5.3-compatible project structure",
            "runtime_mvp_policy": "Avoid relying on heavy 5.3 rich drawing until the basic model loads in target runtime.",
            "first_pass_feature_scope": ["eye", "mouth", "hair", "body_angle", "basic_physics"],
            "deferred_scope": ["offscreen rendering", "alpha blend mask effects", "heavy clipping effects", "complex arm switching"],
        },
        "image_policy": {
            "resolution": "1024, 1536, or 2048 are all acceptable; choose by downstream split/import stability.",
            "generation_order": [
                "Cubism part/deformer spec",
                "single-source matched character prompt",
                "part split and alpha cleanup plan",
                "Cubism import material pack",
                "manual Cubism deformer/keyform authoring",
            ],
            "hard_requirements": [
                "front-facing or near-front upper-body character",
                "clear separated eyes, mouth, face outline, front/side/back hair masses",
                "neck and shoulder area visible enough for body angle deformation",
                "arms not covering mouth, eyes, or hair silhouette in the first pass",
                "minimal text, props, extreme accessories, and heavy transparent effects",
            ],
        },
        "minimum_cubism_v2_pass_gate": {
            "art_meshes": ">= 20",
            "parameters": ">= 15",
            "warp_deformers": ">= 8",
            "rotation_deformers": ">= 1",
            "keyform_bindings": ">= 20",
            "physics_groups": ">= 1 when hair is medium/long; optional for bald/very short hair",
            "must_pass_comparator": [
                "--expect-warp-increase",
                "--expect-keyform-binding-increase",
            ],
        },
        "standard_target_not_minimum": {
            "art_meshes": "50-120 for first solid avatar; official rich samples go much higher",
            "parameters": "25-60 before optional expressions",
            "warp_deformers": "25-60",
            "rotation_deformers": "5-25",
            "keyform_bindings": "90-250",
            "physics_groups": "2-8",
        },
        "part_taxonomy": {
            "eye": [
                "eye white L/R",
                "iris/pupil L/R",
                "upper eyelid L/R",
                "lower eyelid or lash L/R",
                "brow L/R",
            ],
            "mouth": [
                "mouth line",
                "upper lip or upper mouth mask",
                "lower lip or lower mouth mask",
                "mouth inner",
                "teeth/tongue optional",
            ],
            "hair": [
                "front hair clumps",
                "side hair L/R",
                "back hair",
                "long strand/twin-tail groups when present",
            ],
            "body_angle": [
                "face base",
                "head container",
                "neck",
                "upper body/torso",
                "shoulders",
                "arms/hands optional for v2.1",
            ],
        },
        "parameter_spec": {
            "required": [
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
            "recommended": [
                "ParamBrowLY",
                "ParamBrowRY",
                "ParamHairFront",
                "ParamHairSideL",
                "ParamHairSideR",
                "ParamHairBack",
            ],
            "deferred": [
                "arm switching parameters",
                "clothing toggles",
                "rich effect opacity/mask parameters",
            ],
        },
        "deformer_keyform_spec": {
            "required_deformer_groups": [
                "root/body warp",
                "head/face warp",
                "eye L/R warp",
                "mouth warp",
                "front hair warp",
                "side/back hair warp",
                "neck/body angle warp",
                "at least one rotation deformer for head, hair, or body",
            ],
            "required_keyforms": [
                "AngleX -30/0/+30",
                "AngleY -30/0/+30",
                "AngleZ -10/0/+10",
                "EyeOpen L/R 0/0.5/1",
                "MouthOpenY 0/0.5/1",
                "MouthForm -1/0/+1",
                "Hair swing left/neutral/right",
                "BodyAngleX -10/0/+10",
            ],
        },
        "physics_spec": {
            "inputs": ["ParamAngleX", "ParamAngleY", "ParamAngleZ", "ParamBodyAngleX"],
            "outputs": ["front hair", "side hair", "back hair", "optional accessory"],
            "first_pass_groups": "front hair, side hair, back hair, optional accessory",
        },
        "evidence_gate": [
            "before/after cmo3 structure report",
            "compare_cmo3_structure_reports.py with warp and keyform expectations",
            "Cubism GUI screenshots for eye, mouth, hair, angle extremes",
            "draw order and overhang note",
            "runtime model3/moc3 export smoke only after CMO3 structure passes",
        ],
        "baseline_sections_seen": {
            key: len(value) for key, value in baseline.get("sections", {}).items()
        },
    }


def write_markdown(path: Path, spec: dict[str, Any]) -> None:
    stats = spec["core_official_full_structure_stats"]
    chunks = [
        "# Cubism Success Pattern Spec",
        "",
        f"Generated: {spec['generated_at']}",
        "",
        "This is the Cubism-first baseline for the next Vtube model. It learns structure only and must not copy official sample art, textures, PSD layers, or character designs.",
        "",
        "## Position",
        "",
        f"- `imagen-live2d-001`: {spec['position']['legacy_model_role']}",
        f"- New model rule: {spec['position']['new_model_rule']}",
        f"- Asset policy: {spec['position']['asset_policy']}",
        "",
        "## Official Core Stats",
        "",
        "| Metric | Value |",
        "|---|---:|",
        *[f"| {key} | {value} |" for key, value in stats.items()],
        "",
        "## Minimum Cubism v2 Pass Gate",
        "",
        "| Item | Gate |",
        "|---|---|",
        *[f"| {key} | {value} |" for key, value in spec["minimum_cubism_v2_pass_gate"].items() if key != "must_pass_comparator"],
        "",
        "Comparator:",
        "",
        *[f"- `{item}`" for item in spec["minimum_cubism_v2_pass_gate"]["must_pass_comparator"]],
        "",
        "## Standard Target",
        "",
        "| Item | Target |",
        "|---|---|",
        *[f"| {key} | {value} |" for key, value in spec["standard_target_not_minimum"].items()],
        "",
        "## Image Policy",
        "",
        f"- Resolution: {spec['image_policy']['resolution']}",
        "",
        "Generation order:",
        "",
        *[f"- {item}" for item in spec["image_policy"]["generation_order"]],
        "",
        "Hard requirements:",
        "",
        *[f"- {item}" for item in spec["image_policy"]["hard_requirements"]],
        "",
        "## Part Taxonomy",
        "",
    ]
    for section, items in spec["part_taxonomy"].items():
        chunks.extend([f"### {section}", "", *[f"- {item}" for item in items], ""])
    chunks.extend(["## Parameters", "", "Required:", ""])
    chunks.extend(f"- `{item}`" for item in spec["parameter_spec"]["required"])
    chunks.extend(["", "Recommended:", ""])
    chunks.extend(f"- `{item}`" for item in spec["parameter_spec"]["recommended"])
    chunks.extend(["", "## Deformer And Keyform Spec", "", "Required deformer groups:", ""])
    chunks.extend(f"- {item}" for item in spec["deformer_keyform_spec"]["required_deformer_groups"])
    chunks.extend(["", "Required keyforms:", ""])
    chunks.extend(f"- {item}" for item in spec["deformer_keyform_spec"]["required_keyforms"])
    chunks.extend(["", "## Physics Spec", ""])
    chunks.append(f"- Inputs: {', '.join(spec['physics_spec']['inputs'])}")
    chunks.append(f"- Outputs: {', '.join(spec['physics_spec']['outputs'])}")
    chunks.append(f"- First pass groups: {spec['physics_spec']['first_pass_groups']}")
    chunks.extend(["", "## Evidence Gate", ""])
    chunks.extend(f"- {item}" for item in spec["evidence_gate"])
    chunks.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(chunks), encoding="utf-8")


def main() -> None:
    args = parse_args()
    summary = load_json(Path(args.summary).expanduser().resolve())
    baseline = load_json(Path(args.baseline).expanduser().resolve())
    spec = build_spec(summary, baseline)
    out_dir = Path(args.out_dir).expanduser().resolve()
    write_json(out_dir / "cubism_success_pattern_spec.json", spec)
    write_markdown(out_dir / "cubism_success_pattern_spec.md", spec)
    print(
        json.dumps(
            {
                "ok": True,
                "json": rel(out_dir / "cubism_success_pattern_spec.json"),
                "markdown": rel(out_dir / "cubism_success_pattern_spec.md"),
                "minimum_gate": spec["minimum_cubism_v2_pass_gate"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

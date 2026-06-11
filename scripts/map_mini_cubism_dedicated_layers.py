#!/usr/bin/env python3
"""Gate See-through layers against the Mini Cubism dedicated v1 taxonomy."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = ROOT / "experiments/mini-cubism-dedicated-model-v1-001"

ROLE_TO_SPEC_HINTS = {
    "front_hair": ["front_bang_L", "front_bang_CL", "front_bang_C", "front_bang_CR", "front_bang_R"],
    "back_hair": ["back_hair_base", "back_hair_L", "back_hair_C", "back_hair_R"],
    "face": ["face_base"],
    "neck": ["neck"],
    "mouth_line": ["mouth_closed_line"],
    "iris": ["iris_L", "iris_R"],
    "eye_white": ["eye_white_L", "eye_white_R"],
    "upper_lash": ["upper_lash_L", "upper_lash_R"],
    "brow": ["brow_L", "brow_R"],
    "ears": ["ear_L", "ear_R", "ear_inner_L", "ear_inner_R"],
    "accessory": ["choker_base", "choker_gem"],
    "arm": ["arm_L", "arm_R", "sleeve_L", "sleeve_R"],
    "clothes": ["body_base", "chest", "shoulder_L", "shoulder_R"],
}

ORIGINAL_TO_SPEC_HINTS = {
    "L_iris": ["iris_L"],
    "R_iris": ["iris_R"],
    "L_eye_white": ["eye_white_L"],
    "R_eye_white": ["eye_white_R"],
    "L_upper_lash": ["upper_lash_L"],
    "R_upper_lash": ["upper_lash_R"],
    "L_brow": ["brow_L"],
    "R_brow": ["brow_R"],
    "L_arm": ["arm_L", "sleeve_L"],
    "R_arm": ["arm_R", "sleeve_R"],
    "L_ear_outer": ["ear_L"],
    "R_ear_outer": ["ear_R"],
    "ear_inner": ["ear_inner_L", "ear_inner_R"],
    "choker": ["choker_base", "choker_gem"],
    "mouth_line": ["mouth_closed_line"],
    "face_base": ["face_base"],
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def group_counts(mapped_spec_parts: set[str], part_groups: dict[str, list[str]]) -> dict[str, int]:
    return {
        "parts": len(mapped_spec_parts),
        "hair_parts": len(mapped_spec_parts.intersection(part_groups["hair_physics"])),
        "eye_parts": len(mapped_spec_parts.intersection(part_groups["eyes_keypose"])),
        "mouth_parts": len(mapped_spec_parts.intersection(part_groups["mouth_keypose"])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Map dedicated See-through layer candidates to the Mini Cubism v1 part taxonomy.")
    parser.add_argument("--experiment", default=str(DEFAULT_EXPERIMENT))
    args = parser.parse_args()

    exp = Path(args.experiment).resolve()
    manifest_path = exp / "layer_manifest.json"
    spec_path = exp / "part_spec_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing layer split manifest: {manifest_path}")
    if not spec_path.exists():
        raise FileNotFoundError(f"Missing dedicated part spec: {spec_path}")

    manifest = load_json(manifest_path)
    spec = load_json(spec_path)
    part_groups = spec["part_groups"]
    required = spec["required_counts"]

    mapped_candidates = []
    mapped_spec_parts: set[str] = set()
    for layer in manifest.get("layers", []):
        if not layer.get("production_candidate"):
            continue
        role = layer.get("role") or ""
        original = layer.get("original_part_id") or ""
        hints = ORIGINAL_TO_SPEC_HINTS.get(original) or ROLE_TO_SPEC_HINTS.get(role, [])
        hints = [part for part in hints if part in {p for group in part_groups.values() for p in group}]
        if not hints:
            continue
        mapped_spec_parts.update(hints)
        mapped_candidates.append(
            {
                "layer_name": layer.get("layer_name"),
                "original_part_id": layer.get("original_part_id"),
                "role": role,
                "source_path": layer.get("output_path"),
                "candidate_is_coarse": len(hints) > 1,
                "suggested_spec_targets": hints,
            }
        )

    counts = group_counts(mapped_spec_parts, part_groups)
    physics_target_pool = (
        set(part_groups.get("hair_physics", []))
        | set(part_groups.get("clothes_accessory_physics", []))
        | {part for part in part_groups.get("face_ear", []) if part.startswith("ear_")}
    )
    physics_targets = set(mapped_spec_parts).intersection(physics_target_pool)
    counts["physics_targets"] = len(physics_targets)
    counts["normalized_layers"] = manifest.get("counts", {}).get("normalized_layers", len(manifest.get("layers", [])))
    counts["production_candidates"] = manifest.get("counts", {}).get("production_candidates")

    floors = {
        "parts": spec.get("minimum_part_count", 60),
        "hair_parts": required["hair_parts"],
        "eye_parts": required["eye_parts"],
        "mouth_parts": required["mouth_parts"],
        "physics_targets": required["physics_targets"],
    }
    failures = {key: {"actual": counts.get(key, 0), "required": value} for key, value in floors.items() if counts.get(key, 0) < value}
    status = "PASS_DEDICATED_LAYER_MAPPING" if not failures else "REVISE_LAYER_SPLIT_BELOW_DEDICATED_FLOOR"

    report = {
        "schema_version": 1,
        "experiment_id": exp.name,
        "generated_at": now(),
        "status": status,
        "source_layer_manifest": str(manifest_path),
        "source_part_spec_manifest": str(spec_path),
        "counts": counts,
        "required_floors": floors,
        "failed_floors": failures,
        "mapped_candidates": mapped_candidates,
        "mapped_spec_parts": sorted(mapped_spec_parts),
        "missing_spec_parts": sorted({p for group in part_groups.values() for p in group} - mapped_spec_parts),
        "interpretation": [
            "See-through layer split succeeded, but current output is coarse candidate evidence.",
            "Do not build the dedicated Mini Cubism rig from these layers as if it had 60+ separated parts.",
            "Next automatic action should refine decomposition or generate dedicated keypose assets for missing eye/mouth/hair splits.",
        ],
    }
    write_json(exp / "reports" / "dedicated_part_mapping_report.json", report)
    print(json.dumps({"status": status, "counts": counts, "failed_floors": failures}, ensure_ascii=False, indent=2))
    return 0 if status.startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate Mini Cubism targeted split candidate manifest."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "experiments/mini-cubism-dedicated-model-v1-001/targeted_split_v1/targeted_layer_manifest.json"
REQUIRED_GROUPS = {
    "body_anchor",
    "face_ear",
    "hair_physics",
    "eyes_keypose",
    "mouth_keypose",
    "clothes_accessory_physics",
}


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        fail(f"missing manifest: {path}")
    return json.loads(path.read_text())


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def nonempty_alpha(path: Path) -> tuple[bool, list[int] | None]:
    image = Image.open(path).convert("RGBA")
    if image.size != (2048, 2048):
        fail(f"not full-canvas 2048 PNG: {path} size={image.size}")
    bbox = image.getchannel("A").getbbox()
    return bbox is not None, list(bbox) if bbox else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Mini Cubism targeted split candidates.")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    args = parser.parse_args()

    manifest_path = resolve(args.manifest)
    manifest = load_json(manifest_path)
    layers = manifest.get("layers", [])
    groups = manifest.get("part_groups", {})
    required_counts = {
        "parts": 60,
        "hair_parts": 18,
        "eye_parts": 16,
        "mouth_parts": 8,
        "physics_targets": 12,
    }
    if set(groups) != REQUIRED_GROUPS:
        fail(f"part_groups mismatch: {sorted(groups)}")

    seen: set[str] = set()
    empty = []
    missing_files = []
    invalid_canvas = []
    for layer in layers:
        part_id = layer.get("part_id")
        if not part_id:
            fail("layer missing part_id")
        if part_id in seen:
            fail(f"duplicate part_id: {part_id}")
        seen.add(part_id)
        for field in ["output_path", "bbox", "alpha_coverage", "group", "canvas_size", "derivation_mode"]:
            if field not in layer:
                fail(f"{part_id} missing {field}")
        path = resolve(layer["output_path"])
        if not path.exists():
            missing_files.append(str(path))
            continue
        ok, bbox = nonempty_alpha(path)
        if not ok:
            empty.append(part_id)
        if layer.get("canvas_size") != [2048, 2048]:
            invalid_canvas.append(part_id)

    if missing_files:
        fail(f"missing part files: {missing_files[:5]}")
    if empty:
        fail(f"empty alpha parts: {empty}")
    if invalid_canvas:
        fail(f"invalid canvas metadata: {invalid_canvas}")

    all_group_parts = {part for parts in groups.values() for part in parts}
    missing_spec_parts = sorted(all_group_parts - seen)
    counts = {
        "parts": len(seen),
        "hair_parts": len(seen.intersection(groups["hair_physics"])),
        "eye_parts": len(seen.intersection(groups["eyes_keypose"])),
        "mouth_parts": len(seen.intersection(groups["mouth_keypose"])),
        "physics_targets": len(
            seen.intersection(
                set(groups["hair_physics"])
                | set(groups["clothes_accessory_physics"])
                | {part for part in groups["face_ear"] if part.startswith("ear_")}
            )
        ),
    }
    floor_failures = {key: {"actual": counts[key], "required": req} for key, req in required_counts.items() if counts[key] < req}
    if missing_spec_parts:
        floor_failures["missing_spec_parts"] = {"actual": len(missing_spec_parts), "required": 0}

    mouth_groups = manifest.get("mouth_visibility_groups", {}).get("states", {})
    seen_mouth_state: dict[str, str] = {}
    mouth_overlap = []
    for state, parts in mouth_groups.items():
        for part in parts:
            if part in seen_mouth_state:
                mouth_overlap.append(part)
            seen_mouth_state[part] = state
    required_mouth = set(groups["mouth_keypose"])
    missing_mouth_keypose = sorted(required_mouth - set(seen_mouth_state))
    if mouth_overlap:
        floor_failures["mouth_visibility_overlap"] = {"parts": sorted(set(mouth_overlap))}
    if missing_mouth_keypose:
        floor_failures["mouth_visibility_missing"] = {"parts": missing_mouth_keypose}

    hidden = set(manifest.get("eye_closed_hidden_parts", []))
    required_hidden = {"iris_L", "iris_R", "pupil_L", "pupil_R", "catchlight_L", "catchlight_R"}
    missing_hidden = sorted(required_hidden - hidden)
    if missing_hidden:
        floor_failures["eye_closed_hidden_missing"] = {"parts": missing_hidden}

    status = "PASS" if not floor_failures else "FAIL"
    report = {
        "schema_version": 1,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "manifest": str(manifest_path),
        "status": status,
        "counts": counts,
        "required_counts": required_counts,
        "floor_failures": floor_failures,
        "checks": {
            "full_canvas_2048": True,
            "nonempty_alpha": not empty,
            "unique_part_ids": True,
            "mouth_visibility_exclusive": "mouth_visibility_overlap" not in floor_failures,
            "eye_closed_hidden_targets": "eye_closed_hidden_missing" not in floor_failures,
        },
    }
    out = manifest_path.parent.parent / "reports" / "targeted_split_validation_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"ok": status == "PASS", "status": status, "report": str(out), "counts": counts, "floor_failures": floor_failures}, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

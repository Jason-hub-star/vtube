#!/usr/bin/env python3
"""Validate the Mini Cubism dedicated model part spec manifest."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="experiments/mini-cubism-dedicated-model-v1-001/part_spec_manifest.json")
    parser.add_argument("--out", default="experiments/mini-cubism-dedicated-model-v1-001/reports/part_spec_validation_report.json")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = root / out_path

    manifest = load_json(manifest_path)
    groups = manifest.get("part_groups", {})
    missing_groups = sorted(REQUIRED_GROUPS - set(groups.keys()))
    if missing_groups:
        fail(f"missing groups: {missing_groups}")

    parts = [part for group_parts in groups.values() for part in group_parts]
    duplicates = sorted({part for part in parts if parts.count(part) > 1})
    required = manifest.get("required_counts", {})
    checks = {
        "part_count": len(parts) >= manifest.get("minimum_part_count", 60),
        "hair_parts": len(groups.get("hair_physics", [])) >= required.get("hair_parts", 18),
        "eye_parts": len(groups.get("eyes_keypose", [])) >= required.get("eye_parts", 16),
        "mouth_parts": len(groups.get("mouth_keypose", [])) >= required.get("mouth_parts", 8),
        "physics_targets": (
            len(groups.get("hair_physics", []))
            + len(groups.get("clothes_accessory_physics", []))
            + len([part for part in groups.get("face_ear", []) if part.startswith("ear_")])
        )
        >= required.get("physics_targets", 12),
        "no_duplicate_parts": not duplicates,
        "has_physics_profiles": len(manifest.get("physics_profiles", [])) >= 6,
        "has_required_parameters": all(
            parameter in manifest.get("parameters", [])
            for parameter in ["ParamAngleX", "ParamEyeLOpen", "ParamEyeROpen", "ParamMouthOpenY", "ParamMouthForm"]
        ),
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    report = {
        "schema_version": 1,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "manifest": str(manifest_path),
        "status": status,
        "counts": {
            "parts": len(parts),
            "hair_parts": len(groups.get("hair_physics", [])),
            "eye_parts": len(groups.get("eyes_keypose", [])),
            "mouth_parts": len(groups.get("mouth_keypose", [])),
            "physics_profiles": len(manifest.get("physics_profiles", [])),
        },
        "checks": checks,
        "duplicates": duplicates,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"ok": status == "PASS", "status": status, "report": str(out_path), "counts": report["counts"]}, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

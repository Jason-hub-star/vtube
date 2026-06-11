#!/usr/bin/env python3
"""Build a Mini Cubism candidate that hides helper/underpaint patches at neutral."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path("/Users/family/jason/Vtube")
PACK = ROOT / "experiments/cubism-v2-new-character-001/material_pack_v0"
MANIFEST_PATH = PACK / "layer_manifest.json"
SNAPSHOT_MANIFEST = PACK / "layer_manifest.clean_neutral_opacity_candidate_v1.json"
REPORT_JSON = PACK / "reports/clean_neutral_opacity_candidate_report.json"
REPORT_MD = PACK / "reports/clean_neutral_opacity_candidate_report.md"


HELPER_OPACITY_KEYFRAMES = {
    "body_underpaint": ("ParamBodyAngleX", [(-10, 0.45), (0, 0), (10, 0.45)]),
    "neck_shadow_underpaint": ("ParamBodyAngleX", [(-10, 0.45), (0, 0), (10, 0.45)]),
    "arm_L_underpaint": ("ParamBodyAngleX", [(-10, 0.45), (0, 0), (10, 0.45)]),
    "arm_R_underpaint": ("ParamBodyAngleX", [(-10, 0.45), (0, 0), (10, 0.45)]),
    "hair_back_underpaint": ("ParamAngleX", [(-30, 0.5), (0, 0), (30, 0.5)]),
    "face_underpaint_L": ("ParamAngleX", [(-30, 0.55), (0, 0), (30, 0.55)]),
    "face_underpaint_R": ("ParamAngleX", [(-30, 0.55), (0, 0), (30, 0.55)]),
    "eye_L_underpaint": ("ParamEyeBallX", [(-1, 0.45), (0, 0), (1, 0.45)]),
    "eye_R_underpaint": ("ParamEyeBallX", [(-1, 0.45), (0, 0), (1, 0.45)]),
    "face_shadow_L": ("ParamAngleX", [(-30, 0.35), (0, 0), (30, 0)]),
    "face_shadow_R": ("ParamAngleX", [(-30, 0), (0, 0), (30, 0.35)]),
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def build() -> dict[str, Any]:
    manifest = load_json(MANIFEST_PATH)
    updated = json.loads(json.dumps(manifest))
    existing = {
        (row.get("part_id"), row.get("parameter_id"))
        for row in updated.get("part_opacity_keyframes", [])
    }
    added = []
    for part_id, (parameter_id, pairs) in HELPER_OPACITY_KEYFRAMES.items():
        if (part_id, parameter_id) in existing:
            continue
        keyform = {
            "part_id": part_id,
            "parameter_id": parameter_id,
            "mode": "linear",
            "keyframes": [{"value": value, "opacity": opacity} for value, opacity in pairs],
            "purpose": "hide helper/underpaint patches at neutral; reveal only during angle/gaze preview",
        }
        updated.setdefault("part_opacity_keyframes", []).append(keyform)
        added.append(keyform)
    updated["status"] = "CLEAN_NEUTRAL_OPACITY_CANDIDATE_V1"
    updated["clean_neutral_opacity_candidate"] = {
        "schema_version": 1,
        "generated_at": now(),
        "source_manifest": rel(MANIFEST_PATH),
        "snapshot_manifest": rel(SNAPSHOT_MANIFEST),
        "method": "add neutral-hidden opacity keyframes for helper underpaint and face shadow layers",
        "production_decision": "VISUAL_REVIEW_REQUIRED_NOT_PROMOTED",
    }
    write_json(SNAPSHOT_MANIFEST, updated)
    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "BUILT_CLEAN_NEUTRAL_OPACITY_CANDIDATE_V1",
        "snapshot_manifest": rel(SNAPSHOT_MANIFEST),
        "added_keyframes": added,
        "counts": {
            "added_keyframes": len(added),
            "total_part_opacity_keyframes": len(updated.get("part_opacity_keyframes", [])),
        },
        "interpretation": [
            "Face blotches in Mini Cubism are likely helper underpaint/face shadow layers visible at neutral.",
            "This candidate hides those helper layers at neutral while allowing limited visibility at angle/gaze extremes.",
            "This is a preview/QA candidate and should be visually reviewed before promotion.",
        ],
    }
    write_json(REPORT_JSON, report)
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Clean Neutral Opacity Candidate v1",
                "",
                f"- status: `{report['status']}`",
                f"- added keyframes: `{report['counts']['added_keyframes']}`",
                f"- total part opacity keyframes: `{report['counts']['total_part_opacity_keyframes']}`",
                f"- snapshot manifest: `{report['snapshot_manifest']}`",
                "",
                "This is a Mini Cubism visual QA candidate, not production approval.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report


def main() -> int:
    report = build()
    print(json.dumps({"ok": True, "status": report["status"], "counts": report["counts"], "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

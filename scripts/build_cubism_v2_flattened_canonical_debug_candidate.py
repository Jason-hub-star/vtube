#!/usr/bin/env python3
"""Build a visual-only debug candidate with a flattened canonical overlay.

This is intentionally not a production material pack. It isolates whether the
Mini Cubism preview is broken or whether the separated face/eye/mouth layers are
visually corrupt by hiding those detailed overlays and drawing the selected
canonical image on top.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "experiments/cubism-v2-new-character-001/material_pack_v0"
SOURCE_MANIFEST = PACK / "layer_manifest.group_position_clean_candidate_v1.json"
CANONICAL = PACK / "canonical/candidate_002_2048_rgba.png"
OUT_LAYERS = PACK / "production_layers_flattened_canonical_debug_v1"
OUT_MANIFEST = PACK / "layer_manifest.flattened_canonical_debug_v1.json"
OUT_PACK = PACK / "flattened_canonical_debug_pack_v1"
REPORT = PACK / "reports/flattened_canonical_debug_candidate_report.json"

PROBLEM_PART_PREFIXES = (
    "eye_",
    "mouth_",
    "brow_",
    "cheek_",
    "nose",
    "face_shadow_",
    "face_underpaint_",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def is_problem_face_part(part_id: str) -> bool:
    return part_id.startswith(PROBLEM_PART_PREFIXES)


def hidden_keyframe(part_id: str) -> dict[str, Any]:
    return {
        "part_id": part_id,
        "parameter_id": "ParamAngleX",
        "mode": "linear",
        "keyframes": [
            {"value": -30, "opacity": 0},
            {"value": 0, "opacity": 0},
            {"value": 30, "opacity": 0},
        ],
        "purpose": "visual debug only: hide broken generated face/eye/mouth detail overlays",
    }


def main() -> int:
    manifest = load_json(SOURCE_MANIFEST)
    OUT_LAYERS.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    overlay_path = OUT_LAYERS / "99_canonical_flattened_debug_overlay.png"
    shutil.copy2(CANONICAL, overlay_path)

    layers = list(manifest["layers"])
    overlay_layer = {
        "part_id": "canonical_flattened_debug_overlay",
        "layer_name": "99_canonical_flattened_debug_overlay",
        "label_ko": "진단용 원본 전체 오버레이",
        "group": "face_base",
        "feasibility": "DEBUG_ONLY",
        "source_type": "CANONICAL_FLATTENED_OVERLAY",
        "source_bbox": [0, 0, 2048, 2048],
        "bbox": [0, 0, 2048, 2048],
        "draw_order_band": "debug_top",
        "draw_order": 9999,
        "deformer_node": "root_warp",
        "parameters": [],
        "physics_groups": [],
        "risk_tags": ["debug_only", "not_production_split"],
        "status": "DEBUG_VISUAL_ONLY",
        "include_in_import_psd": True,
        "output_path": str(overlay_path.relative_to(ROOT)),
        "merged_into": None,
        "notes": "Visual diagnosis only. This layer proves whether Mini Cubism rendering is clean when the broken separated face layers are not visible.",
        "canvas_size": [2048, 2048],
    }
    layers.append(overlay_layer)

    problem_parts = [item["part_id"] for item in layers if is_problem_face_part(item.get("part_id", ""))]
    existing_opacity = list(manifest.get("part_opacity_keyframes") or [])
    existing_targets = {item.get("part_id") for item in existing_opacity}
    for part_id in problem_parts:
        if part_id not in existing_targets:
            existing_opacity.append(hidden_keyframe(part_id))
        else:
            existing_opacity.append(hidden_keyframe(part_id))

    out_manifest = dict(manifest)
    out_manifest.update(
        {
            "status": "FLATTENED_CANONICAL_DEBUG_VISUAL_ONLY",
            "generated_at": now(),
            "source_manifest": str(SOURCE_MANIFEST),
            "layers": layers,
            "part_opacity_keyframes": existing_opacity,
            "debug_policy": {
                "production_candidate": False,
                "purpose": "Confirm visual corruption comes from separated face/eye/mouth layers, not the Mini Cubism renderer.",
                "hidden_problem_parts": problem_parts,
                "canonical_overlay_part": "canonical_flattened_debug_overlay",
            },
        }
    )
    OUT_MANIFEST.write_text(json.dumps(out_manifest, ensure_ascii=False, indent=2) + "\n")

    if OUT_PACK.exists():
        shutil.rmtree(OUT_PACK)
    OUT_PACK.mkdir(parents=True)
    (OUT_PACK / "layer_manifest.json").write_text(json.dumps(out_manifest, ensure_ascii=False, indent=2) + "\n")

    report = {
        "schema_version": 1,
        "status": "DEBUG_CANDIDATE_BUILT",
        "generated_at": now(),
        "source_manifest": str(SOURCE_MANIFEST),
        "out_manifest": str(OUT_MANIFEST),
        "debug_pack": str(OUT_PACK),
        "overlay_path": str(overlay_path),
        "problem_parts_hidden": problem_parts,
        "counts": {
            "layers": len(layers),
            "problem_parts_hidden": len(problem_parts),
            "part_opacity_keyframes": len(existing_opacity),
        },
        "decision": "VISUAL_DIAGNOSIS_ONLY_DO_NOT_PROMOTE",
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

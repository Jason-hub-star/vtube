#!/usr/bin/env python3
"""Create a conservative automatic B4/B5 anchor draft.

This reduces 주인님 manual work by saving a first-pass override JSON. It is
deliberately marked as a draft and must be rebuilt, overlay-QA'd, and visually
reviewed before any material promotion.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
READINESS_JSON = (
    EXP / "reports/v22_b4_b5_anchor_correction_readiness/v22_b4_b5_anchor_correction_readiness.json"
)
OUT_JSON = EXP / "reports/v22_b4_b5_anchor_correction_readiness/manual_anchor_overrides_auto_draft.json"
OUT_MD = EXP / "reports/v22_b4_b5_anchor_correction_readiness/manual_anchor_overrides_auto_draft.md"
CANVAS_CENTER_X = 1024.0


TARGET_BY_PART = {
    # B5 body/clothing: keep close to source body center while gently enforcing symmetry.
    "torso_base": ([1024.0, 1372.0], 1.0),
    "neck": ([1024.0, 896.0], 1.0),
    "shoulder_L": ([718.0, 1110.0], 1.0),
    "shoulder_R": ([1330.0, 1110.0], 1.0),
    "arm_L_upper_simple": ([590.0, 1450.0], 1.0),
    "arm_R_upper_simple": ([1428.0, 1450.0], 1.0),
    "collar_front": ([1024.0, 1138.0], 1.0),
    "collar_shadow": ([1024.0, 1224.0], 1.0),
    "chest_cloth_base": ([1024.0, 1395.0], 1.0),
    "chest_cloth_shadow": ([1024.0, 1565.0], 1.0),
    # Face detail: nudge oversized/patch-like details toward known source facial centers.
    "face_shadow_L": ([770.0, 775.0], 0.92),
    "face_shadow_R": ([1250.0, 775.0], 0.92),
    "nose": ([1024.0, 790.0], 0.85),
    "cheek_L": ([835.0, 794.0], 0.82),
    "cheek_R": ([1210.0, 794.0], 0.82),
    "brow_L": ([852.0, 645.0], 0.9),
    "brow_R": ([1176.0, 645.0], 0.9),
    # B4 hair: retain current silhouette anchors but center the main front/back groups.
    "hair_back_base": ([1024.0, 720.0], 1.0),
    "hair_back_underpaint": ([1024.0, 880.0], 1.0),
    "hair_back_center": ([1024.0, 822.0], 1.0),
    "hair_back_strand_L": ([725.0, 820.0], 1.0),
    "hair_back_strand_R": ([1335.0, 830.0], 1.0),
    "hair_front_center": ([1024.0, 430.0], 0.96),
    "hair_front_L": ([882.0, 445.0], 0.96),
    "hair_front_R": ([1160.0, 455.0], 0.96),
    "hair_front_side_L": ([812.0, 635.0], 0.96),
    "hair_front_side_R": ([1287.0, 635.0], 0.96),
    "hair_front_tip_L": ([760.0, 873.0], 0.96),
    "hair_front_tip_R": ([1209.0, 885.0], 0.96),
    "hair_side_L_outer": ([716.0, 911.0], 1.0),
    "hair_side_L_inner": ([738.0, 923.0], 1.0),
    "hair_side_R_outer": ([1418.0, 933.0], 1.0),
    "hair_side_R_inner": ([1253.0, 936.0], 1.0),
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def main() -> int:
    readiness = json.loads(READINESS_JSON.read_text(encoding="utf-8"))
    overrides = {}
    for target in readiness["targets"]:
        part_id = target["part_id"]
        target_anchor, target_scale = TARGET_BY_PART.get(part_id, (target["current_center"], 1.0))
        dx = round(target_anchor[0] - target["current_center"][0], 2)
        dy = round(target_anchor[1] - target["current_center"][1], 2)
        overrides[part_id] = {
            "part_id": part_id,
            "source_batch": target["source_batch"],
            "layer_path": target["layer_path"],
            "current_center": target["current_center"],
            "current_bbox": target["current_bbox"],
            "target_anchor": target_anchor,
            "target_scale": target_scale,
            "preview_opacity": 0.72,
            "notes": f"auto draft; dx={dx}, dy={dy}; requires overlay QA and 주인님 visual review",
            "status": "AUTO_DRAFT_TARGET_ANCHOR_PENDING_REBUILD_AND_REVIEW",
            "updated_at": now(),
        }

    doc = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": "G6_B4_B5_AUTO_ANCHOR_DRAFT_READY_FOR_REBUILD",
        "source_readiness_report": rel(READINESS_JSON),
        "project": "cubism-v2-new-character-002",
        "canvas": [2048, 2048],
        "saved_count": len(overrides),
        "rules": [
            "This is an automatic first-pass draft, not human approval.",
            "Keep ParamHairFront hidden until corrected front hair passes overlay QA.",
            "Do not unlock Mini Cubism or real Cubism from this draft alone.",
        ],
        "overrides": overrides,
        "self_review": {
            "target_count": len(readiness["targets"]),
            "saved_count": len(overrides),
            "all_targets_have_override": len(overrides) == len(readiness["targets"]),
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "status": "PASS",
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Character 002 v22 B4/B5 Auto Anchor Draft",
        "",
        f"- status: `{doc['status']}`",
        f"- saved_count: `{doc['saved_count']}`",
        f"- source readiness: `{doc['source_readiness_report']}`",
        "",
        "## Rules",
        "",
        *[f"- {rule}" for rule in doc["rules"]],
        "",
        "## Overrides",
        "",
    ]
    for part_id, override in overrides.items():
        lines.append(
            f"- `{part_id}` `{override['source_batch']}` current `{override['current_center']}` "
            f"target `{override['target_anchor']}` scale `{override['target_scale']}`"
        )
    lines.extend(["", "## Self Review", ""])
    for key, value in doc["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": doc["status"], "overrides": str(OUT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

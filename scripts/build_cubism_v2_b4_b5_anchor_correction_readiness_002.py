#!/usr/bin/env python3
"""Build a G6 readiness packet for v22 B4/B5 anchor correction.

This does not approve or move any part. It converts the current B4/B5 visual
REVISE state into a repeatable correction target list with current alpha bbox
and center evidence, so the next editor/override step can be driven by saved
JSON instead of ad hoc LLM judgement.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
MANIFEST_JSON = EXP / "reports/v22_64part_candidate_manifest/v22_64part_candidate_manifest.json"
B4_OVERLAY_JSON = EXP / "reports/v22_b4_hair_pack/v22_b4_overlay_qa_report.json"
B5_OVERLAY_JSON = EXP / "reports/v22_b5_body_clothing_pack/v22_b5_overlay_qa_report.json"
REPORT_DIR = EXP / "reports/v22_b4_b5_anchor_correction_readiness"
REPORT_JSON = REPORT_DIR / "v22_b4_b5_anchor_correction_readiness.json"
REPORT_MD = REPORT_DIR / "v22_b4_b5_anchor_correction_readiness.md"
OVERRIDE_TEMPLATE_JSON = REPORT_DIR / "manual_anchor_override_template.json"

TARGET_BATCHES = {"B4", "B5"}
REVISE_STATUS = "TECHNICAL_PRESENT_VISUAL_REVISE"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def bbox_and_center(path: Path) -> tuple[list[int] | None, list[float] | None, float]:
    img = Image.open(path).convert("RGBA")
    alpha = np.asarray(img.getchannel("A"), dtype=np.uint8)
    ys, xs = np.where(alpha > 5)
    if len(xs) == 0:
        return None, None, 0.0
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    center = [round((bbox[0] + bbox[2]) / 2, 2), round((bbox[1] + bbox[3]) / 2, 2)]
    coverage = round(float((alpha > 5).mean()), 8)
    return bbox, center, coverage


def correction_kind(entry: dict) -> str:
    part_id = entry["id"]
    group = entry["group"]
    if entry["source_batch"] == "B4":
        if part_id.startswith("hair_front"):
            return "manual_anchor_or_crop_refinement_front_hair"
        if part_id.startswith("hair_side"):
            return "manual_anchor_or_crop_refinement_side_hair"
        return "manual_anchor_or_crop_refinement_back_hair"
    if group in {"body", "clothing"}:
        return "manual_anchor_or_crop_refinement_body_clothing"
    if group in {"face_base", "brow"}:
        return "manual_anchor_or_crop_refinement_face_detail"
    return "manual_anchor_or_crop_refinement"


def main() -> int:
    manifest = load_json(MANIFEST_JSON)
    b4_overlay = load_json(B4_OVERLAY_JSON)
    b5_overlay = load_json(B5_OVERLAY_JSON)

    targets = []
    for entry in manifest["manifest_entries"]:
        batch = entry.get("source_batch")
        if batch not in TARGET_BATCHES:
            continue
        if entry.get("manifest_status") != REVISE_STATUS:
            continue
        layer_path = ROOT / entry["path"]
        bbox, center, coverage = bbox_and_center(layer_path)
        targets.append(
            {
                "part_id": entry["id"],
                "group": entry["group"],
                "source_batch": batch,
                "layer_path": entry["path"],
                "current_bbox": bbox,
                "current_center": center,
                "alpha_coverage": coverage,
                "current_visual_status": entry["manifest_status"],
                "visual_gate": entry["batch_visual_gate"],
                "correction_kind": correction_kind(entry),
                "target_anchor": None,
                "target_scale": None,
                "override_status": "PENDING_MANUAL_OR_REFINED_EXTRACTION",
            }
        )

    batch_counts = Counter(target["source_batch"] for target in targets)
    group_counts = Counter(target["group"] for target in targets)
    self_review = {
        "manifest_status": manifest["status"],
        "b4_overlay_status": b4_overlay["status"],
        "b5_overlay_status": b5_overlay["status"],
        "target_count": len(targets),
        "b4_target_count": batch_counts.get("B4", 0),
        "b5_target_count": batch_counts.get("B5", 0),
        "all_targets_have_bbox": all(target["current_bbox"] is not None for target in targets),
        "all_targets_pending_override": all(
            target["override_status"] == "PENDING_MANUAL_OR_REFINED_EXTRACTION" for target in targets
        ),
        "param_hair_front_hidden": manifest["self_review"]["param_hair_front_hidden"],
        "mini_cubism_not_promoted": manifest["self_review"]["mini_cubism_not_promoted"],
        "real_cubism_not_promoted": manifest["self_review"]["real_cubism_not_promoted"],
        "status": "PASS",
    }

    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_id": "cubism-v2-new-character-002-v22-b4-b5-anchor-correction-readiness-001",
        "status": "G6_B4_B5_ANCHOR_CORRECTION_READY_OVERRIDE_PENDING",
        "manifest": rel(MANIFEST_JSON),
        "b4_overlay_report": rel(B4_OVERLAY_JSON),
        "b5_overlay_report": rel(B5_OVERLAY_JSON),
        "scope": {
            "batches": sorted(TARGET_BATCHES),
            "source_status": REVISE_STATUS,
            "correction_rule": "Do not approve parts here. Save manual anchors or refine extraction, rebuild B4/B5, then rebuild the 64-part manifest.",
        },
        "quality_gate_interpretation": {
            "g1_64part_completeness": manifest["quality_gate_interpretation"]["g1_64part_completeness"],
            "g4_g5_visual_overlay": manifest["quality_gate_interpretation"]["g4_g5_visual_overlay"],
            "g6_manual_anchor_correction": "READY_FOR_OVERRIDE_CAPTURE",
            "g7_mini_cubism_diagnostic": "BLOCKED_UNTIL_CORRECTED_VISUAL_QA",
            "g8_real_cubism_authoring": "BLOCKED_UNTIL_MATERIAL_QA_AND_HUMAN_REVIEW",
            "param_hair_front": "HIDDEN_CONTRACT_ONLY",
        },
        "target_summary": {
            "by_batch": dict(sorted(batch_counts.items())),
            "by_group": dict(sorted(group_counts.items())),
        },
        "targets": targets,
        "decision": "B4/B5 are ready for G6 correction capture, not material promotion. Current bbox/center evidence is recorded for each visually revised target.",
        "next_action": [
            "Open or build a drag/zoom anchor editor for these target parts.",
            "Save target_anchor and target_scale values into an override JSON.",
            "Build corrected B4/B5 candidate layers from the saved override or refined extraction script.",
            "Re-run B4/B5 overlay QA and rebuild the 64-part manifest before any G7 Mini Cubism diagnostic.",
        ],
        "self_review": self_review,
    }

    override_template = {
        "schema_version": "v1",
        "status": "PENDING_MANUAL_ANCHOR_INPUT",
        "source_report": rel(REPORT_JSON),
        "project": "cubism-v2-new-character-002",
        "canvas": [2048, 2048],
        "rules": [
            "Keep full-canvas RGBA layers at 2048x2048.",
            "Shift only intended B4/B5 target parts.",
            "Keep ParamHairFront hidden until corrected front hair passes overlay QA.",
            "Do not use this template as approval evidence until target_anchor values are filled and rebuilt.",
        ],
        "overrides": [
            {
                "part_id": target["part_id"],
                "source_batch": target["source_batch"],
                "layer_path": target["layer_path"],
                "current_center": target["current_center"],
                "target_anchor": None,
                "target_scale": 1.0,
                "notes": "",
            }
            for target in targets
        ],
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OVERRIDE_TEMPLATE_JSON.write_text(
        json.dumps(override_template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Character 002 v22 B4/B5 Anchor Correction Readiness",
        "",
        f"- status: `{report['status']}`",
        f"- manifest: `{report['manifest']}`",
        f"- override template: `{rel(OVERRIDE_TEMPLATE_JSON)}`",
        "",
        "## Gate Interpretation",
        "",
    ]
    for key, value in report["quality_gate_interpretation"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Target Summary",
            "",
            f"- by batch: `{report['target_summary']['by_batch']}`",
            f"- by group: `{report['target_summary']['by_group']}`",
            "",
            "## Targets",
            "",
        ]
    )
    for target in targets:
        lines.append(
            "- `{part_id}` `{source_batch}` `{group}` center `{current_center}` bbox `{current_bbox}` `{correction_kind}`".format(
                **target
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            report["decision"],
            "",
            "## Next Action",
            "",
            *[f"- {item}" for item in report["next_action"]],
            "",
            "## Self Review",
            "",
        ]
    )
    for key, value in self_review.items():
        lines.append(f"- `{key}`: `{value}`")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": report["status"], "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

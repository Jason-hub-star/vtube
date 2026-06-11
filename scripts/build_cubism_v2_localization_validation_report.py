#!/usr/bin/env python3
"""Summarize the manual semantic override localization split validation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path("/Users/family/jason/Vtube")
PACK = ROOT / "experiments/cubism-v2-new-character-001/material_pack_v0"
REPORT_JSON = PACK / "reports/part_localization_template_validation_report.json"
REPORT_MD = PACK / "reports/part_localization_template_validation_report.md"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def maybe_load(path: Path) -> dict[str, Any]:
    return load_json(path) if path.exists() else {}


def main() -> int:
    overrides_path = PACK / "reports/manual_semantic_overrides.json"
    template_path = PACK / "reports/part_localization_template.json"
    split_path = PACK / "reports/part_localization_split_report.json"
    semantic_path = PACK / "reports/semantic_purity_localization_split/semantic_purity_gate_report.json"
    mini_validation_path = PACK / "mini_cubism_project_material_localized_v1/reports/validation_report.json"
    manifest_path = PACK / "layer_manifest.json"
    localized_manifest_path = PACK / "layer_manifest.localization_template_split_v1.json"

    overrides = maybe_load(overrides_path)
    template = maybe_load(template_path)
    split = maybe_load(split_path)
    semantic = maybe_load(semantic_path)
    mini_validation = maybe_load(mini_validation_path)
    manifest = maybe_load(manifest_path)
    localized_manifest = maybe_load(localized_manifest_path)

    override_count = len(overrides.get("overrides", {}))
    template_count = len(template.get("parts", {}))
    split_status = split.get("status", "MISSING")
    semantic_status = semantic.get("status", "MISSING")
    mini_status = mini_validation.get("status", "MISSING")
    neutral_after = semantic.get("neutral_scores", {}).get("after_semantic_repair", {})
    pass_conditions = semantic.get("pass_conditions", {})

    raw_split_ready = (
        split_status.startswith("PASS")
        and semantic_status.startswith("PASS")
        and mini_status == "PASS"
    )
    status = "PASS_LOCALIZATION_SPLIT_PRODUCTION_READY" if raw_split_ready else "REVISE_LOCALIZATION_SPLIT_NEEDS_SEMANTIC_MASKING"

    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "inputs": {
            "manual_overrides": rel(overrides_path),
            "part_localization_template": rel(template_path),
            "layer_manifest": rel(manifest_path),
            "localized_manifest": rel(localized_manifest_path),
        },
        "outputs": {
            "split_report": rel(split_path),
            "split_contact_sheet": rel(PACK / "reports/part_localization_split_contact_sheet.png"),
            "localized_semantic_purity_report": rel(semantic_path),
            "mini_cubism_localized_project": rel(PACK / "mini_cubism_project_material_localized_v1"),
            "mini_cubism_validation_report": rel(mini_validation_path),
        },
        "metrics": {
            "manual_override_count": override_count,
            "template_part_count": template_count,
            "anchor_outside_roi_count": template.get("quality_notes", {}).get("anchor_outside_roi_count"),
            "localized_parts_applied": split.get("applied_parts"),
            "localized_parts_kept": split.get("kept_parts"),
            "semantic_status": semantic_status,
            "neutral_after_bad_ratio_visible": neutral_after.get("bad_ratio_visible"),
            "underpaint_before_top_owner_pixels": semantic.get("underpaint_leakage", {}).get("before", {}).get("total_underpaint_top_owner_pixels"),
            "underpaint_after_top_owner_pixels": semantic.get("underpaint_leakage", {}).get("after", {}).get("total_underpaint_top_owner_pixels"),
            "eye_mouth_after_status": semantic.get("eye_mouth_alignment", {}).get("after", {}).get("status"),
            "mini_cubism_status": mini_status,
            "mini_cubism_counts": mini_validation.get("counts"),
        },
        "pass_conditions": {
            "manual_overrides_present": override_count > 0,
            "template_generated": template_count > 0,
            "localized_split_applied": split_status.startswith("PASS"),
            "semantic_gate_passed": semantic_status.startswith("PASS"),
            "mini_cubism_project_validates": mini_status == "PASS",
            **{f"semantic_{key}": value for key, value in pass_conditions.items()},
        },
        "active_manifest_status": manifest.get("status"),
        "localized_manifest_status": localized_manifest.get("status"),
        "interpretation": [
            "Saved manual semantic labels can be converted into a reusable localization template.",
            "The template can regenerate current-candidate layers from ROI coordinates.",
            "The localized split opens as a Mini Cubism project, so paths/canvas/bboxes are structurally usable.",
            "The localized split is not production-ready by itself because the G1.5 semantic/neutral score remains above threshold.",
            "Use the template as a localization guide, then run semantic mask/underpaint repair instead of relying on raw ROI crop for final material approval.",
        ],
    }

    write_json(REPORT_JSON, report)
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Part Localization Template Validation",
                "",
                f"- status: `{status}`",
                f"- manual overrides: `{override_count}`",
                f"- template parts: `{template_count}`",
                f"- localized split: `{split_status}`",
                f"- G1.5 semantic check: `{semantic_status}`",
                f"- neutral after bad ratio: `{neutral_after.get('bad_ratio_visible')}`",
                f"- eye/mouth after status: `{semantic.get('eye_mouth_alignment', {}).get('after', {}).get('status')}`",
                f"- Mini Cubism localized project: `{mini_status}`",
                "",
                "## Interpretation",
                "",
                "- 위치 라벨은 분리 위치를 잡는 데 효과가 있다.",
                "- 하지만 단순 ROI crop만으로는 밑색/숨은 영역/큰 파츠 품질이 부족하다.",
                "- 다음 단계는 localization template를 seed로 쓰고, semantic owner map + underpaint repair를 다시 적용하는 것이다.",
                "",
                "## Artifacts",
                "",
                f"- `{report['outputs']['split_contact_sheet']}`",
                f"- `{report['outputs']['localized_semantic_purity_report']}`",
                f"- `{report['outputs']['mini_cubism_validation_report']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "status": status, "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

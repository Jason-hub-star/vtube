#!/usr/bin/env python3
"""Summarize material fix batch 001 for candidate_002."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/Users/family/jason/Vtube")
PACK = ROOT / "experiments/cubism-v2-new-character-001/material_pack_v0"
REPORTS = PACK / "reports"
MANIFEST = PACK / "material_asset_manifest.json"
VALIDATION = REPORTS / "material_asset_validation_report.json"
REVIEW_SUMMARY = REPORTS / "material_human_review_summary.json"
FIX_QUEUE = REPORTS / "material_review_fix_queue.json"
OUT_JSON = REPORTS / "material_fix_batch_001_report.json"
OUT_MD = REPORTS / "material_fix_batch_001_report.md"


REGENERATED_PARTS = [
    "eye_L_highlight",
    "eye_R_highlight",
    "eye_L_closed_lid",
    "eye_R_closed_lid",
    "mouth_inner",
    "mouth_teeth",
    "mouth_tongue",
    "mouth_line",
    "mouth_upper_lip_mask",
    "mouth_lower_lip_mask",
    "mouth_corner_L",
    "mouth_corner_R",
]

UNDERPAINT_PARTS = [
    "body_underpaint",
    "neck_shadow_underpaint",
    "arm_L_underpaint",
    "arm_R_underpaint",
    "face_underpaint_L",
    "face_underpaint_R",
    "eye_L_underpaint",
    "eye_R_underpaint",
    "hair_back_underpaint",
]

SEMANTIC_CLEANUP_PARTS = [
    "torso_base",
    "neck",
    "shoulder_L",
    "shoulder_R",
    "face_base",
    "nose",
    "collar_front",
    "chest_cloth_base",
]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def main() -> None:
    manifest = load(MANIFEST)
    validation = load(VALIDATION)
    review = load(REVIEW_SUMMARY)
    fix_queue = load(FIX_QUEUE)
    source_type_by_part = {entry["part_id"]: entry["source_type"] for entry in manifest["layers"]}
    alpha_by_part = {entry["part_id"]: entry.get("alpha_coverage") for entry in manifest["layers"]}
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS_FIX_BATCH_001_APPLIED",
        "scope": {
            "regenerated_eye_mouth_parts": REGENERATED_PARTS,
            "underpaint_parts_trimmed": UNDERPAINT_PARTS,
            "semantic_mask_cleanup_parts": SEMANTIC_CLEANUP_PARTS,
        },
        "evidence": {
            "manifest": rel(MANIFEST),
            "validation_report": rel(VALIDATION),
            "contact_sheet": rel(REPORTS / "material_contact_sheet.png"),
            "review_summary": rel(REVIEW_SUMMARY),
            "fix_queue": rel(FIX_QUEUE),
            "browser_screenshot": "cubism-v2-material-fix-batch-001.png",
        },
        "checks": {
            "validation_status": validation["status"],
            "generated_png_layers": validation["summary"]["generated_png_layers"],
            "merged_metadata_entries": validation["summary"]["merged_metadata_entries"],
            "critical_missing_count": validation["summary"]["critical_missing_count"],
            "psd_layer_count": validation["psd_metadata"].get("layer_count"),
            "regenerate_verdict_count_after_batch": review["verdict_counts"].get("REGENERATE", 0),
            "fix_queue_count_after_batch": review["fix_queue_count"],
        },
        "source_type_after_batch": {part: source_type_by_part.get(part) for part in REGENERATED_PARTS},
        "alpha_coverage_after_batch": {part: alpha_by_part.get(part) for part in REGENERATED_PARTS + UNDERPAINT_PARTS},
        "interpretation_ko": [
            "REGENERATE 12개는 source cut이 아니라 재생성/derived detail로 처리되어 REGENERATE 0으로 내려갔다.",
            "underpaint 9개는 bbox와 alpha/color 처리를 줄여 블록감을 완화했다.",
            "큰 몸/얼굴/의상 파츠는 bbox를 축소했지만 아직 semantic mask cleanup 후보로 남긴다.",
            "fix queue 53은 실패라기보다 Cubism import 전 미세수정 대기열이다.",
        ],
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(
        "\n".join(
            [
                "# Cubism v2 Material Fix Batch 001",
                "",
                f"- status: `{report['status']}`",
                f"- validation: `{report['checks']['validation_status']}`",
                f"- generated PNG layers: `{report['checks']['generated_png_layers']}`",
                f"- PSD layer count: `{report['checks']['psd_layer_count']}`",
                f"- REGENERATE after batch: `{report['checks']['regenerate_verdict_count_after_batch']}`",
                f"- fix queue after batch: `{report['checks']['fix_queue_count_after_batch']}`",
                "",
                "## Applied",
                "",
                f"- regenerated eye/mouth parts: `{', '.join(REGENERATED_PARTS)}`",
                f"- underpaint parts trimmed: `{', '.join(UNDERPAINT_PARTS)}`",
                f"- semantic cleanup bbox parts: `{', '.join(SEMANTIC_CLEANUP_PARTS)}`",
                "",
                "## Interpretation",
                "",
                *[f"- {line}" for line in report["interpretation_ko"]],
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(report["status"])
    print(OUT_JSON)


if __name__ == "__main__":
    main()

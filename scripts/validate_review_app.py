#!/usr/bin/env python3
"""Validate the part-purity review app data contracts."""

from __future__ import annotations

import json
import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "review_app" / "review_manifest.json"
REVIEW_PATH = ROOT / "experiments" / "part-purity-001" / "reports" / "part_visual_review.json"
FIX_QUEUE_PATH = ROOT / "experiments" / "part-purity-001" / "reports" / "ai_fix_queue.json"
CONCEPT_REVIEW_PATH = ROOT / "experiments" / "concept-regeneration-001" / "reports" / "part_visual_review.json"
CONCEPT_FIX_QUEUE_PATH = ROOT / "experiments" / "concept-regeneration-001" / "reports" / "ai_fix_queue.json"
CONCEPT_PSD_GATE_PATH = ROOT / "experiments" / "concept-regeneration-001" / "reports" / "psd_candidate_gate_report.json"
SEETHROUGH_REVIEW_PATH = ROOT / "experiments" / "see-through-layer-decomp-001" / "reports" / "part_visual_review.json"
SEETHROUGH_PSD_GATE_PATH = ROOT / "experiments" / "see-through-layer-decomp-001" / "reports" / "psd_candidate_gate_report.json"
MPS_EXPERIMENT_ID = "see-through-mps-compat-002"
LAYER_EXPERIMENT_SECTIONS = {
    "mps_compat_candidates": "see-through-mps-compat-002",
    "imagen_live2d_candidates": "imagen-live2d-001",
    "mini_cubism_dedicated_candidates": "mini-cubism-dedicated-model-v1-001",
}

REQUIRED_FIELDS = {
    "part_id",
    "ko_name",
    "group",
    "image_path",
    "canonical_path",
    "overlay_path",
    "bbox",
    "status",
    "include_in_import_psd",
    "allowed_features",
    "forbidden_contamination",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the review app manifest and saved review contracts.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    return parser.parse_args()


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> int:
    args = parse_args()
    manifest_path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    manifest = json.loads(manifest_path.read_text())
    counts = manifest.get("counts", {})
    cubism_v2 = manifest.get("mode") == "cubism_v2"
    mps_only = manifest.get("mode") == "mps_only"
    experiment_only = manifest.get("mode") == "experiment_only"
    if cubism_v2:
        required_sections = {"g0_concept", "g1_part_taxonomy", "g2_structure", "g3_motion_visual"}
        actual_sections = set(manifest.get("sections", {}))
        if actual_sections != required_sections:
            fail(f"Cubism v2 manifest has unexpected sections: {sorted(actual_sections)}")
        if manifest.get("tier") not in {"v2_min", "v2_standard", "v2_rich"}:
            fail(f"Cubism v2 manifest has invalid tier: {manifest.get('tier')}")
        if counts.get("g1_part_taxonomy", 0) <= 0:
            fail("Cubism v2 G1 part taxonomy is empty")
        expected_fixture_manifest = manifest.get("experiment_id") == "cubism-v2-validator-fixtures-001"
        if expected_fixture_manifest:
            if counts.get("g2_structure", 0) < 2:
                fail(f"Cubism v2 fixture manifest should have at least two G2 auto-check items: {counts.get('g2_structure')}")
        elif counts.get("g2_structure") != 1:
            fail(f"Cubism v2 G2 should have one auto-check item: {counts.get('g2_structure')}")
        tag_codes = {
            tag.get("code") if isinstance(tag, dict) else tag
            for tag in manifest.get("issue_tags", [])
        }
        for tag in {
            "missing_part",
            "bad_alpha",
            "misaligned",
            "style_mismatch",
            "underpaint_missing",
            "clipping_risk",
            "draw_order_issue",
            "overhang_issue",
        }:
            if tag not in tag_codes:
                fail(f"Cubism v2 issue tag missing: {tag}")
    elif mps_only:
        if set(manifest.get("sections", {})) != {"mps_compat_candidates"}:
            fail(f"MPS-only manifest has unexpected sections: {sorted(manifest.get('sections', {}))}")
        if counts.get("mps_compat_candidates", 0) < 29:
            fail(f"mps_compat_candidates count mismatch: {counts.get('mps_compat_candidates')}")
    elif experiment_only:
        sections = manifest.get("sections", {})
        if len(sections) != 1:
            fail(f"experiment-only manifest should have one section: {sorted(sections)}")
        section_name = next(iter(sections))
        if section_name not in LAYER_EXPERIMENT_SECTIONS:
            fail(f"unknown experiment-only section: {section_name}")
        if counts.get(section_name, 0) <= 0:
            fail(f"{section_name} is empty")
    else:
        if counts.get("production_parts") != 27:
            fail(f"production_parts count mismatch: {counts.get('production_parts')}")
        if counts.get("reference_mouth") != 10:
            fail(f"reference_mouth count mismatch: {counts.get('reference_mouth')}")
        if counts.get("reference_blink") != 3:
            fail(f"reference_blink count mismatch: {counts.get('reference_blink')}")
        if "concept_parts" in counts and counts.get("concept_parts") != 35:
            fail(f"concept_parts count mismatch: {counts.get('concept_parts')}")

    part_ids = set()
    production_sections = {"production_parts", "concept_parts"}
    for section, items in manifest.get("sections", {}).items():
        for item in items:
            missing = REQUIRED_FIELDS - item.keys()
            if missing:
                fail(f"{item.get('part_id')} missing fields: {sorted(missing)}")
            if cubism_v2:
                for field in ["tier", "review_gate", "simple_label", "simple_description", "checklist", "compare_views"]:
                    if field not in item:
                        fail(f"Cubism v2 item {item.get('part_id')} missing {field}")
                if item["review_gate"] not in {"G0_CONCEPT", "G1_PART_TAXONOMY", "G2_STRUCTURE", "G3_MOTION_VISUAL"}:
                    fail(f"Cubism v2 item {item.get('part_id')} has invalid gate: {item['review_gate']}")
                if item["review_gate"] == "G2_STRUCTURE":
                    summary = item.get("auto_check_summary")
                    if not summary:
                        fail(f"Cubism v2 G2 item {item.get('part_id')} missing auto_check_summary")
                    if summary.get("status") == "PASS" and not summary.get("checks"):
                        fail(f"Cubism v2 G2 item {item.get('part_id')} PASS without checks")
            if item["part_id"] in part_ids:
                fail(f"duplicate manifest part_id: {item['part_id']}")
            part_ids.add(item["part_id"])
            if mps_only and item.get("experiment_id") != MPS_EXPERIMENT_ID:
                fail(f"MPS-only item from wrong experiment: {item['part_id']} {item.get('experiment_id')}")
            if experiment_only:
                expected_experiment_id = LAYER_EXPERIMENT_SECTIONS.get(section)
                if expected_experiment_id and item.get("experiment_id") != expected_experiment_id:
                    fail(f"experiment-only item from wrong experiment: {item['part_id']} {item.get('experiment_id')}")
            if section not in production_sections and item["include_in_import_psd"]:
                fail(f"non-production item included in PSD: {item['part_id']}")
            if section == "production_parts" and not item["include_in_import_psd"]:
                fail(f"production item excluded from PSD: {item['part_id']}")

    experiment_ids = {"part-purity-001"}
    for section_items in manifest.get("sections", {}).values():
        for item in section_items:
            experiment_ids.add(item.get("experiment_id", "part-purity-001"))

    for experiment_id in sorted(experiment_ids):
        review_path = ROOT / "experiments" / experiment_id / "reports" / "part_visual_review.json"
        fix_queue_path = ROOT / "experiments" / experiment_id / "reports" / "ai_fix_queue.json"
        if not review_path.exists() or not fix_queue_path.exists():
            continue
        review = json.loads(review_path.read_text())
        queue = json.loads(fix_queue_path.read_text())
        queued_ids = {item["part_id"] for item in queue.get("items", [])}
        expected = {
            part_id
            for part_id, item in review.get("reviews", {}).items()
            if item.get("verdict") in {"X", "REVISE"}
        }
        if queued_ids != expected:
            fail(f"fix queue mismatch: queued={sorted(queued_ids)} expected={sorted(expected)}")
        for item in queue.get("items", []):
            for field in [
                "part_id",
                "ko_name",
                "failure_tags",
                "human_note",
                "source_image",
                "suggested_generation_mode",
                "negative_prompt_hints",
            ]:
                if field not in item:
                    fail(f"fix queue item {item.get('part_id')} missing {field}")

    if CONCEPT_PSD_GATE_PATH.exists():
        gate = json.loads(CONCEPT_PSD_GATE_PATH.read_text())
        accepted = gate.get("accepted_layers", [])
        if gate.get("accepted_layer_count") != len(accepted):
            fail("concept PSD gate accepted_layer_count mismatch")
        concept_reviews = json.loads(CONCEPT_REVIEW_PATH.read_text()).get("reviews", {}) if CONCEPT_REVIEW_PATH.exists() else {}
        for item in accepted:
            part_id = item["part_id"]
            namespaced_id = f"concept__{part_id}" if not part_id.startswith("concept__") else part_id
            verdict = concept_reviews.get(namespaced_id, {}).get("verdict")
            if verdict != "O":
                fail(f"concept PSD candidate includes non-O part: {part_id} verdict={verdict}")
        if gate.get("status") == "BLOCKED_NO_O_LAYERS" and gate.get("psd_metadata", {}).get("exists"):
            fail("concept PSD exists while gate is BLOCKED_NO_O_LAYERS")

    if SEETHROUGH_PSD_GATE_PATH.exists():
        gate = json.loads(SEETHROUGH_PSD_GATE_PATH.read_text())
        accepted = gate.get("accepted_layers", [])
        if gate.get("accepted_layer_count") != len(accepted):
            fail("See-through PSD gate accepted_layer_count mismatch")
        seethrough_reviews = json.loads(SEETHROUGH_REVIEW_PATH.read_text()).get("reviews", {}) if SEETHROUGH_REVIEW_PATH.exists() else {}
        for item in accepted:
            source_id = f"seethrough__{item['part_id']}" if not item["part_id"].startswith("seethrough__") else item["part_id"]
            direct_verdict = seethrough_reviews.get(item["part_id"], {}).get("verdict")
            source_verdict = seethrough_reviews.get(source_id, {}).get("verdict")
            if direct_verdict != "O" and source_verdict != "O":
                fail(f"See-through PSD candidate includes non-O part: {item['part_id']}")
        if gate.get("status") == "BLOCKED_NO_O_LAYERS" and gate.get("psd_metadata", {}).get("exists"):
            fail("See-through PSD exists while gate is BLOCKED_NO_O_LAYERS")

    print("Review app validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

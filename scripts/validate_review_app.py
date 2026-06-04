#!/usr/bin/env python3
"""Validate the part-purity review app data contracts."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "review_app" / "review_manifest.json"
REVIEW_PATH = ROOT / "experiments" / "part-purity-001" / "reports" / "part_visual_review.json"
FIX_QUEUE_PATH = ROOT / "experiments" / "part-purity-001" / "reports" / "ai_fix_queue.json"
CONCEPT_REVIEW_PATH = ROOT / "experiments" / "concept-regeneration-001" / "reports" / "part_visual_review.json"
CONCEPT_FIX_QUEUE_PATH = ROOT / "experiments" / "concept-regeneration-001" / "reports" / "ai_fix_queue.json"
CONCEPT_PSD_GATE_PATH = ROOT / "experiments" / "concept-regeneration-001" / "reports" / "psd_candidate_gate_report.json"
SEETHROUGH_REVIEW_PATH = ROOT / "experiments" / "see-through-layer-decomp-001" / "reports" / "part_visual_review.json"
SEETHROUGH_FIX_QUEUE_PATH = ROOT / "experiments" / "see-through-layer-decomp-001" / "reports" / "ai_fix_queue.json"
SEETHROUGH_PSD_GATE_PATH = ROOT / "experiments" / "see-through-layer-decomp-001" / "reports" / "psd_candidate_gate_report.json"

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


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text())
    counts = manifest.get("counts", {})
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
            if item["part_id"] in part_ids:
                fail(f"duplicate manifest part_id: {item['part_id']}")
            part_ids.add(item["part_id"])
            if section not in production_sections and item["include_in_import_psd"]:
                fail(f"non-production item included in PSD: {item['part_id']}")
            if section == "production_parts" and not item["include_in_import_psd"]:
                fail(f"production item excluded from PSD: {item['part_id']}")

    for review_path, fix_queue_path in [
        (REVIEW_PATH, FIX_QUEUE_PATH),
        (CONCEPT_REVIEW_PATH, CONCEPT_FIX_QUEUE_PATH),
        (SEETHROUGH_REVIEW_PATH, SEETHROUGH_FIX_QUEUE_PATH),
    ]:
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

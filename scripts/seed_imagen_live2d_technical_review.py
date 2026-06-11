#!/usr/bin/env python3
"""Seed safe technical review verdicts for Imagen Live2D candidates.

This script only writes non-promoting verdicts:

- empty production candidates -> X
- non-production/reference candidates -> REFERENCE_ONLY

It never writes O. Human visual review remains required before PSD promotion.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    return json.loads(path.read_text())


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def technical_verdict(layer: dict[str, Any]) -> dict[str, Any] | None:
    part_id = layer["layer_name"]
    production = bool(layer.get("production_candidate"))
    bbox = layer.get("bbox")
    alpha = float(layer.get("alpha_coverage") or 0)
    original = layer.get("original_part_id", part_id)

    if production and (not bbox or alpha <= 0):
        return {
            "part_id": part_id,
            "verdict": "X",
            "issue_tags": ["alpha_dirty", "wrong_shape"],
            "human_note": f"자동 기술 seed: production 후보 `{original}`의 alpha가 비어 있어 PSD 후보로 쓸 수 없음. 재생성/ROI cleanup 필요.",
            "updated_at": now(),
        }
    if not production:
        tags = []
        note = "자동 기술 seed: production schema 후보가 아니므로 PSD에서 제외하고 참고용으로만 보존."
        if not bbox or alpha <= 0:
            tags = ["alpha_dirty"]
            note = "자동 기술 seed: 비어 있는 reference/non-production 후보이므로 PSD에서 제외."
        return {
            "part_id": part_id,
            "verdict": "REFERENCE_ONLY",
            "issue_tags": tags,
            "human_note": note,
            "updated_at": now(),
        }
    return None


def build_fix_queue(review_doc: dict[str, Any], manifest: dict[str, Any], review_path: Path) -> dict[str, Any]:
    layers = {layer["layer_name"]: layer for layer in manifest.get("layers", [])}
    items = []
    for part_id, review in review_doc.get("reviews", {}).items():
        if review.get("verdict") not in {"X", "REVISE"}:
            continue
        layer = layers.get(part_id, {})
        tags = review.get("issue_tags", [])
        items.append(
            {
                "part_id": part_id,
                "original_part_id": layer.get("original_part_id", part_id),
                "experiment_id": manifest.get("experiment_id"),
                "ko_name": layer.get("ko_name", layer.get("original_part_id", part_id)),
                "section": "imagen_live2d_candidates",
                "group": layer.get("role", "unknown"),
                "verdict": review.get("verdict"),
                "failure_tags": tags,
                "human_note": review.get("human_note", ""),
                "source_image": layer.get("output_path"),
                "canonical_image": layer.get("canonical_path"),
                "overlay_image": None,
                "include_in_import_psd": False,
                "suggested_generation_mode": "roi_cleanup_or_regenerate",
                "negative_prompt_hints": [
                    "clean alpha, transparent background, no stray residue"
                    if tag == "alpha_dirty"
                    else "match canonical silhouette, proportions, and placement"
                    for tag in tags
                ],
            }
        )
    items.sort(key=lambda item: (item["group"], item["part_id"]))
    return {
        "schema_version": 1,
        "experiment_id": manifest.get("experiment_id"),
        "generated_at": now(),
        "source_review": str(review_path.relative_to(ROOT)),
        "items": items,
        "counts": {"queued": len(items)},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed safe technical review verdicts for Imagen Live2D candidates.")
    parser.add_argument("--experiment-id", default="imagen-live2d-001")
    parser.add_argument("--overwrite", action="store_true", help="overwrite existing seeded or human reviews")
    args = parser.parse_args()

    exp = ROOT / "experiments" / args.experiment_id
    manifest_path = exp / "layer_manifest.json"
    review_path = exp / "reports" / "part_visual_review.json"
    fix_queue_path = exp / "reports" / "ai_fix_queue.json"
    manifest = load_json(manifest_path, {"layers": []})
    existing = load_json(
        review_path,
        {
            "schema_version": 1,
            "experiment_id": args.experiment_id,
            "created_at": now(),
            "reviews": {},
        },
    )
    reviews = existing.get("reviews", {})
    seeded = []
    skipped_existing = []
    for layer in manifest.get("layers", []):
        verdict = technical_verdict(layer)
        if verdict is None:
            continue
        if layer["layer_name"] in reviews and not args.overwrite:
            skipped_existing.append(layer["layer_name"])
            continue
        reviews[layer["layer_name"]] = verdict
        seeded.append(layer["layer_name"])

    review_doc = {
        "schema_version": 1,
        "experiment_id": args.experiment_id,
        "created_at": existing.get("created_at", now()),
        "updated_at": now(),
        "source_manifest": str(manifest_path.relative_to(ROOT)),
        "reviews": reviews,
        "note": "Technical seed only. No O verdicts are written by this script.",
    }
    save_json(review_path, review_doc)
    fix_queue = build_fix_queue(review_doc, manifest, review_path)
    save_json(fix_queue_path, fix_queue)
    print(
        json.dumps(
            {
                "experiment_id": args.experiment_id,
                "seeded": len(seeded),
                "skipped_existing": len(skipped_existing),
                "review_count": len(reviews),
                "fix_queue_count": fix_queue["counts"]["queued"],
                "review_path": str(review_path.relative_to(ROOT)),
                "fix_queue_path": str(fix_queue_path.relative_to(ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

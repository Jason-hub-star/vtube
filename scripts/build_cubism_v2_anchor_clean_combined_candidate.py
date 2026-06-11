#!/usr/bin/env python3
"""Combine anchor-position repair layers with clean-neutral opacity policy."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path("/Users/family/jason/Vtube")
PACK = ROOT / "experiments/cubism-v2-new-character-001/material_pack_v0"
ANCHOR_MANIFEST = PACK / "layer_manifest.anchor_position_repair_candidate_v1.json"
CLEAN_MANIFEST = PACK / "layer_manifest.clean_neutral_opacity_candidate_v1.json"
OUT_MANIFEST = PACK / "layer_manifest.anchor_clean_combined_candidate_v1.json"
REPORT_JSON = PACK / "reports/anchor_clean_combined_candidate_report.json"
REPORT_MD = PACK / "reports/anchor_clean_combined_candidate_report.md"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def merge_keyframes(anchor_doc: dict[str, Any], clean_doc: dict[str, Any]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in anchor_doc.get("part_opacity_keyframes", []):
        key = (row.get("part_id"), row.get("parameter_id"))
        seen.add(key)
        merged.append(row)
    for row in clean_doc.get("part_opacity_keyframes", []):
        key = (row.get("part_id"), row.get("parameter_id"))
        if key in seen:
            continue
        seen.add(key)
        merged.append(row)
    return merged


def build() -> dict[str, Any]:
    anchor = load_json(ANCHOR_MANIFEST)
    clean = load_json(CLEAN_MANIFEST)
    combined = json.loads(json.dumps(anchor))
    combined["status"] = "ANCHOR_CLEAN_COMBINED_CANDIDATE_V1"
    combined["part_opacity_keyframes"] = merge_keyframes(anchor, clean)
    combined["anchor_clean_combined_candidate"] = {
        "schema_version": 1,
        "generated_at": now(),
        "anchor_source_manifest": rel(ANCHOR_MANIFEST),
        "clean_opacity_source_manifest": rel(CLEAN_MANIFEST),
        "method": "use anchor-position-repair layer paths and merge clean-neutral helper opacity keyframes",
        "production_decision": "VISUAL_REVIEW_REQUIRED_NOT_PROMOTED",
    }
    write_json(OUT_MANIFEST, combined)

    anchor_methods = {}
    for layer in combined.get("layers", []):
        method = layer.get("anchor_position_repair_method") or "NO_ANCHOR_METHOD"
        anchor_methods[method] = anchor_methods.get(method, 0) + 1
    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "BUILT_ANCHOR_CLEAN_COMBINED_CANDIDATE_V1",
        "snapshot_manifest": rel(OUT_MANIFEST),
        "counts": {
            "layers": len(combined.get("layers", [])),
            "import_layers": len([row for row in combined.get("layers", []) if row.get("include_in_import_psd")]),
            "part_opacity_keyframes": len(combined.get("part_opacity_keyframes", [])),
            "anchor_methods": anchor_methods,
        },
        "interpretation": [
            "This combines 8065-style anchor position repair with 8066-style clean-neutral opacity hiding.",
            "Use it as the next visual review target. Do not promote until 주인님 confirms face/eye/mouth placement and blotches are acceptable.",
        ],
    }
    write_json(REPORT_JSON, report)
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Anchor + Clean-Neutral Combined Candidate v1",
                "",
                f"- status: `{report['status']}`",
                f"- import layers: `{report['counts']['import_layers']}`",
                f"- part opacity keyframes: `{report['counts']['part_opacity_keyframes']}`",
                f"- snapshot manifest: `{report['snapshot_manifest']}`",
                "",
                "This is the candidate to compare against `8065` and `8066`.",
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

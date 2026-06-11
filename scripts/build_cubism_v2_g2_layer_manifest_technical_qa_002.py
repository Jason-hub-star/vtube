#!/usr/bin/env python3
"""Run G2 layer-manifest technical QA for character 002 v22.

This validates the corrected 64-part PNG manifest only. It does not perform
visual acceptance, material promotion, Mini Cubism promotion, or real Cubism
authoring.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
MANIFEST_JSON = EXP / "reports/v22_64part_corrected_b4_b5_manifest/v22_64part_corrected_b4_b5_manifest.json"
PREP_JSON = EXP / "reports/v22_g2_g5_material_qa_prep/v22_g2_g5_material_qa_prep_packet.json"
SPEC_JSON = EXP / "reports/v22_64part_generation_spec/v22_64part_generation_spec.json"
REPORT_DIR = EXP / "reports/v22_g2_layer_manifest_technical_qa"
REPORT_JSON = REPORT_DIR / "v22_g2_layer_manifest_technical_qa_report.json"
REPORT_MD = REPORT_DIR / "v22_g2_layer_manifest_technical_qa_report.md"
CANVAS = [2048, 2048]

FORBIDDEN_REUSE_MARKERS = [
    "model_edit_",
    "generated_mouth_v",
    "generated_eye",
    "material_pack_first_v0/normalized_layers",
    "cubism-v2-new-character-001",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def bbox_and_alpha(path: Path) -> tuple[list[int] | None, float]:
    img = Image.open(path).convert("RGBA")
    arr = np.asarray(img.getchannel("A"), dtype=np.uint8)
    ys, xs = np.where(arr > 5)
    if len(xs) == 0:
        return None, 0.0
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    coverage = round(float((arr > 5).mean()), 8)
    return bbox, coverage


def path_has_forbidden_reuse(path: str | None) -> bool:
    if not path:
        return False
    return any(marker in path for marker in FORBIDDEN_REUSE_MARKERS)


def main() -> int:
    manifest = load_json(MANIFEST_JSON)
    prep = load_json(PREP_JSON)
    spec = load_json(SPEC_JSON)
    entries = manifest["manifest_entries"]
    spec_ids = [part["id"] for part in spec["parts"]]
    manifest_ids = [entry["id"] for entry in entries]

    errors: list[dict] = []
    warnings: list[dict] = []
    checked_entries: list[dict] = []
    missing_ids = sorted(set(spec_ids) - set(manifest_ids))
    extra_ids = sorted(set(manifest_ids) - set(spec_ids))
    duplicate_ids = sorted([part_id for part_id, count in Counter(manifest_ids).items() if count > 1])

    for part_id in missing_ids:
        errors.append({"part_id": part_id, "code": "MISSING_REQUIRED_PART"})
    for part_id in extra_ids:
        errors.append({"part_id": part_id, "code": "EXTRA_UNEXPECTED_PART"})
    for part_id in duplicate_ids:
        errors.append({"part_id": part_id, "code": "DUPLICATE_PART_ID"})

    for entry in entries:
        part_id = entry["id"]
        path_value = entry.get("path")
        png_path = ROOT / path_value if path_value else None
        check = {
            "id": part_id,
            "group": entry.get("group"),
            "source_batch": entry.get("source_batch"),
            "path": path_value,
            "mode": None,
            "size": None,
            "bbox": None,
            "alpha_coverage": 0.0,
            "sha256": None,
            "status": "PASS",
            "issues": [],
        }
        required_string_fields = ["group", "deformer_node", "draw_order_band", "manifest_status", "batch_visual_gate"]
        for field in required_string_fields:
            if not entry.get(field):
                check["issues"].append(f"MISSING_{field.upper()}")
        if not isinstance(entry.get("parameters"), list) or not entry["parameters"]:
            check["issues"].append("MISSING_PARAMETERS")
        if path_value is None or png_path is None or not png_path.exists():
            check["issues"].append("PNG_MISSING")
        elif path_has_forbidden_reuse(path_value):
            check["issues"].append("FORBIDDEN_REUSE_PATH")
        if png_path and png_path.exists():
            img = Image.open(png_path)
            check["mode"] = img.mode
            check["size"] = list(img.size)
            check["bbox"], check["alpha_coverage"] = bbox_and_alpha(png_path)
            check["sha256"] = sha256(png_path)
            if img.mode != "RGBA":
                check["issues"].append("PNG_NOT_RGBA")
            if list(img.size) != CANVAS:
                check["issues"].append("PNG_NOT_FULL_CANVAS_2048")
            if check["bbox"] is None:
                check["issues"].append("EMPTY_ALPHA")
            if entry.get("bbox") != check["bbox"]:
                check["issues"].append("BBOX_METADATA_MISMATCH")
            if abs(float(entry.get("alpha_coverage", 0.0)) - float(check["alpha_coverage"])) > 0.00000001:
                check["issues"].append("ALPHA_COVERAGE_METADATA_MISMATCH")
        if check["issues"]:
            check["status"] = "FAIL"
            errors.append({"part_id": part_id, "code": "ENTRY_TECHNICAL_QA_FAIL", "issues": check["issues"]})
        checked_entries.append(check)

    group_counts = Counter(entry["group"] for entry in entries)
    if dict(group_counts) != spec["part_groups"]:
        errors.append({"code": "GROUP_COUNTS_MISMATCH", "actual": dict(group_counts), "expected": spec["part_groups"]})

    source_batch_counts = Counter(entry["source_batch"] for entry in entries)
    draw_order_band_counts = Counter(entry["draw_order_band"] for entry in entries)
    path_reuse_hits = [entry for entry in checked_entries if "FORBIDDEN_REUSE_PATH" in entry["issues"]]
    locks = spec["locked_success_baseline"]
    active_controls_expected = [
        "ParamAngleX",
        "ParamEyeBallX",
        "ParamEyeBallY",
        "ParamEyeLOpen",
        "ParamEyeROpen",
        "ParamMouthOpenY",
    ]
    lock_checks = {
        "active_controls_match_v21_supported_subset": locks["active_controls"] == active_controls_expected,
        "param_hair_front_hidden": "ParamHairFront" in locks["hidden_unsupported_controls"],
        "eye_open_027_policy_present": "0.27" in locks["eye_open_visual_policy"],
        "mouth_open_085_policy_present": "0.85" in locks["mouth_open_policy"],
        "mini_cubism_not_real_cubism": "not real Cubism" in locks["diagnostic_scope"],
    }
    for key, value in lock_checks.items():
        if not value:
            errors.append({"code": "LOCK_CHECK_FAIL", "check": key})

    status = "G2_LAYER_MANIFEST_TECHNICAL_QA_PASS_MATERIAL_STILL_BLOCKED" if not errors else "G2_LAYER_MANIFEST_TECHNICAL_QA_FAIL"
    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": status,
        "corrected_manifest": rel(MANIFEST_JSON),
        "g2_g5_prep_packet": rel(PREP_JSON),
        "spec": rel(SPEC_JSON),
        "checked_entries": checked_entries,
        "summary": {
            "manifest_status": manifest["status"],
            "prep_status": prep["status"],
            "spec_status": spec["status"],
            "required_part_count": len(spec_ids),
            "manifest_entry_count": len(entries),
            "unique_manifest_part_count": len(set(manifest_ids)),
            "missing_part_count": len(missing_ids),
            "extra_part_count": len(extra_ids),
            "duplicate_part_count": len(duplicate_ids),
            "failed_entry_count": sum(1 for entry in checked_entries if entry["status"] != "PASS"),
            "group_counts": dict(sorted(group_counts.items())),
            "source_batch_counts": dict(sorted(source_batch_counts.items())),
            "draw_order_band_counts": dict(sorted(draw_order_band_counts.items())),
            "forbidden_reuse_path_hit_count": len(path_reuse_hits),
            "sha256_recorded_count": sum(1 for entry in checked_entries if entry["sha256"]),
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g3_visual_overlay_status": "BLOCKED_REVIEW_REQUIRED",
            "g4_psd_import_prep_status": "PREP_ONLY_BLOCKED",
            "g5_material_acceptance_status": "BLOCKED",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
        "lock_checks": lock_checks,
        "errors": errors,
        "warnings": warnings,
        "decision": (
            "G2 layer-manifest technical QA passes for the corrected 64-part manifest, but this is technical evidence only. "
            "It does not promote visual QA, material acceptance, Mini Cubism, or real Cubism."
            if not errors
            else "G2 layer-manifest technical QA failed; fix entry issues before continuing."
        ),
        "next_action": [
            "Keep G3 visual overlay QA blocked until B4/B5 hard and hold review rows are resolved.",
            "Do not build/promote import_ready.psd from this QA alone.",
            "Keep ParamHairFront hidden and G7/G8 blocked.",
        ],
        "self_review": {
            "all_required_parts_present": len(missing_ids) == 0,
            "no_extra_parts": len(extra_ids) == 0,
            "no_duplicate_ids": len(duplicate_ids) == 0,
            "all_entries_pass": all(entry["status"] == "PASS" for entry in checked_entries),
            "group_counts_match_spec": dict(group_counts) == spec["part_groups"],
            "forbidden_reuse_path_hit_count": len(path_reuse_hits),
            "sha256_recorded_count": sum(1 for entry in checked_entries if entry["sha256"]),
            "lock_checks_all_pass": all(lock_checks.values()),
            "material_pass_blocked": True,
            "visual_promotion_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "status": "PASS" if not errors else "FAIL",
        },
    }
    save_json(REPORT_JSON, report)

    lines = [
        "# Character 002 v22 G2 Layer Manifest Technical QA",
        "",
        f"- status: `{report['status']}`",
        f"- corrected manifest: `{report['corrected_manifest']}`",
        f"- G2-G5 prep packet: `{report['g2_g5_prep_packet']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Lock Checks", ""])
    for key, value in report["lock_checks"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Errors", ""])
    lines.append("_none_" if not errors else "\n".join(f"- `{item}`" for item in errors))
    lines.extend(["", "## Self Review", ""])
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", "", report["decision"], "", "## Next Action", ""])
    lines.extend(f"- {item}" for item in report["next_action"])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": status, "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

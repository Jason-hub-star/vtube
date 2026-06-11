#!/usr/bin/env python3
"""Build a v22 64-part manifest variant with the P0 torso v2 candidate."""

from __future__ import annotations

import importlib.util
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
BASE_SCRIPT = ROOT / "scripts/build_cubism_v2_64part_corrected_b4_b5_manifest_002.py"
P0_REPORT = EXP / "reports/v22_g3_p0_torso_minipass_v2/v22_g3_p0_torso_minipass_v2_report.json"
P0_B5_DIR = EXP / "v22_b5_p0_torso_minipass_v2_candidate/normalized_layers"
REPORT_DIR = EXP / "reports/v22_64part_p0_torso_v2_manifest"
REPORT_JSON = REPORT_DIR / "v22_64part_p0_torso_v2_manifest.json"
REPORT_MD = REPORT_DIR / "v22_64part_p0_torso_v2_manifest.md"
CONTACT_SHEET = REPORT_DIR / "v22_64part_p0_torso_v2_manifest_contact_sheet.png"


def load_base_module():
    spec = importlib.util.spec_from_file_location("v22_corrected_manifest", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = load_base_module()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def refresh_counts(manifest: dict) -> None:
    entries = manifest["manifest_entries"]
    manifest["self_review"]["visual_gate_counts"] = dict(
        Counter(entry.get("batch_visual_gate", "UNKNOWN") for entry in entries)
    )
    manifest["self_review"]["status_counts"] = dict(Counter(entry["manifest_status"] for entry in entries))
    manifest["self_review"]["b5_p0_torso_v2_candidate_count"] = sum(
        1
        for entry in entries
        if entry["id"] == "torso_base"
        and entry.get("batch_visual_gate") == "P0_TORSO_MINIPASS_V2_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED"
    )
    manifest["self_review"]["b5_torso_review_candidate"] = True


def build_manifest() -> dict:
    p0_report = load_json(P0_REPORT)
    p0_self_review = p0_report["self_review"]
    if p0_report["status"] != "P0_TORSO_MINIPASS_V2_CANDIDATE_READY_FOR_G3_REVIEW":
        raise RuntimeError(f"P0 torso v2 report is not ready: {p0_report['status']}")
    if not p0_self_review["torso_improvement_candidate"]:
        raise RuntimeError("P0 torso v2 is not marked as an improvement candidate")

    BASE.LAYER_DIR_OVERRIDES["B5"] = P0_B5_DIR
    manifest = BASE.build_manifest()
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    manifest["manifest_id"] = "cubism-v2-new-character-002-v22-64part-p0-torso-v2-manifest-001"
    manifest["status"] = "G3_P0_TORSO_V2_64PART_MANIFEST_TECHNICAL_PASS_REVIEW_REQUIRED"
    manifest["batch_status"]["B5"]["source_note"] = "overridden_by_p0_torso_v2_candidate"
    manifest["batch_status"]["B5"]["p0_torso_v2_report"] = rel(P0_REPORT)
    manifest["batch_status"]["B5"]["layer_dir"] = rel(P0_B5_DIR)

    for entry in manifest["manifest_entries"]:
        if entry["id"] == "torso_base":
            entry["batch_visual_gate"] = "P0_TORSO_MINIPASS_V2_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED"
            entry["manifest_status"] = "TECHNICAL_PRESENT_B5_P0_TORSO_V2_REVIEW_REQUIRED"
            entry["p0_torso_metrics"] = p0_report["torso_metrics"]

    manifest["quality_gate_interpretation"].update(
        {
            "g3_p0_torso_status": "P0_TORSO_V2_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED",
            "g4_g5_visual_overlay": "REVIEW_REQUIRED_FOR_P0_TORSO_V2_AND_REMAINING_B4_B5",
            "g5_material_acceptance": "BLOCKED_UNTIL_G3_VISUAL_ACCEPTANCE",
            "param_hair_front": "HIDDEN_CONTRACT_ONLY",
        }
    )
    manifest["decision"] = (
        "This 64-part manifest variant replaces only B5 torso_base with the P0 torso v2 improvement candidate. "
        "It is technically complete, but remains G3 review-required and cannot promote material PASS, "
        "ParamHairFront, Mini Cubism, or real Cubism."
    )
    manifest["next_action"] = [
        "Run P0 torso v2 manifest overlay QA.",
        "Use the overlay QA to continue G3 blocker reduction for P0 torso and P1 B4 secondary hair rows.",
        "Keep material PASS, ParamHairFront, G4/G5 promotion, G7 Mini Cubism, and G8 real Cubism blocked.",
    ]
    manifest["self_review"].update(
        {
            "p0_torso_v2_report_status": p0_report["status"],
            "p0_torso_v2_verdict": p0_report["torso_metrics"]["verdict"],
            "p0_torso_alpha_sum_ratio": p0_report["torso_metrics"]["alpha_sum_ratio"],
            "g3_visual_overlay_status": "REVIEW_REQUIRED",
            "material_pass_blocked": True,
            "validator_only_promotion_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "not_owner_approval": True,
            "status": "PASS",
        }
    )
    refresh_counts(manifest)
    return manifest


def write_markdown(manifest: dict) -> None:
    lines = [
        "# Character 002 v22 64-Part P0 Torso v2 Manifest",
        "",
        f"- status: `{manifest['status']}`",
        f"- G0 status: `{manifest['g0_status']}`",
        f"- contact sheet: `{rel(CONTACT_SHEET)}`",
        "",
        "## Gate Interpretation",
        "",
    ]
    for key, value in manifest["quality_gate_interpretation"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Self Review", ""])
    for key, value in manifest["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", "", manifest["decision"], "", "## Next Action", ""])
    lines.extend(f"- {item}" for item in manifest["next_action"])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    manifest = build_manifest()
    BASE.CONTACT_SHEET = CONTACT_SHEET
    BASE.draw_contact_sheet(manifest)
    manifest["contact_sheet"] = rel(CONTACT_SHEET)
    save_json(REPORT_JSON, manifest)
    write_markdown(manifest)
    print(json.dumps({"status": manifest["status"], "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

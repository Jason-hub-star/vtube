#!/usr/bin/env python3
"""Build a v22 64-part manifest variant with generated G4 torso_base selected."""

from __future__ import annotations

import importlib.util
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
BASE_SCRIPT = ROOT / "scripts/build_cubism_v2_64part_corrected_b4_b5_manifest_002.py"
TORSO_ROUTE = (
    EXP
    / "reports/v22_g4_torso_base_regen_overlay_qa/v22_g4_torso_base_regen_overlay_qa_report.json"
)
TORSO_CANDIDATE = EXP / "v22_g4_torso_base_regen_candidate/normalized_layers/torso_base.png"
REPORT_DIR = EXP / "reports/v22_64part_g4_torso_selected_manifest"
REPORT_JSON = REPORT_DIR / "v22_64part_g4_torso_selected_manifest.json"
REPORT_MD = REPORT_DIR / "v22_64part_g4_torso_selected_manifest.md"
CONTACT_SHEET = REPORT_DIR / "v22_64part_g4_torso_selected_manifest_contact_sheet.png"


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
    manifest["self_review"]["b5_generated_torso_selected_count"] = sum(
        1
        for entry in entries
        if entry["id"] == "torso_base"
        and entry.get("batch_visual_gate")
        == "G4_TORSO_BASE_GENERATED_REBUILD_INPUT_REVIEW_REQUIRED"
    )
    manifest["self_review"]["b5_torso_review_candidate"] = True


def build_manifest() -> dict:
    route = load_json(TORSO_ROUTE)
    if route["status"] != "G4_TORSO_BASE_REGEN_OVERLAY_QA_ROUTE_READY_MATERIAL_BLOCKED":
        raise RuntimeError(f"Torso route is not ready: {route['status']}")
    expected_route = "USE_GENERATED_TORSO_FOR_NEXT_MANIFEST_REBUILD_KEEP_G5_BLOCKED"
    if route["qa"]["route"] != expected_route:
        raise RuntimeError(f"Unexpected torso route: {route['qa']['route']}")
    if not TORSO_CANDIDATE.exists():
        raise RuntimeError(f"Missing torso candidate: {TORSO_CANDIDATE}")

    manifest = BASE.build_manifest()
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    manifest["manifest_id"] = "cubism-v2-new-character-002-v22-64part-g4-torso-selected-manifest-001"
    manifest["status"] = "G4_TORSO_SELECTED_64PART_MANIFEST_TECHNICAL_PASS_REVIEW_REQUIRED"
    manifest["batch_status"]["B5"]["source_note"] = "overridden_by_b5_provisional_layers_plus_generated_g4_torso"
    manifest["batch_status"]["B5"]["g4_torso_route_report"] = rel(TORSO_ROUTE)
    manifest["batch_status"]["B5"]["generated_torso_candidate"] = rel(TORSO_CANDIDATE)

    replaced_count = 0
    for entry in manifest["manifest_entries"]:
        if entry["id"] != "torso_base":
            continue
        replaced_count += 1
        metrics = route["candidate_metrics"]["generated"]
        entry["path"] = rel(TORSO_CANDIDATE)
        entry["mode"] = metrics["mode"]
        entry["size"] = metrics["size"]
        entry["bbox"] = metrics["bbox"]
        entry["alpha_coverage"] = metrics["alpha_coverage"]
        entry["batch_visual_gate"] = "G4_TORSO_BASE_GENERATED_REBUILD_INPUT_REVIEW_REQUIRED"
        entry["manifest_status"] = "TECHNICAL_PRESENT_B5_G4_GENERATED_TORSO_REVIEW_REQUIRED"
        entry["g4_torso_route"] = {
            "route": route["qa"]["route"],
            "technical_verdict": route["qa"]["technical_verdict"],
            "visual_verdict": route["qa"]["visual_verdict"],
            "generated_vs_p0_bottom_extension_px": route["candidate_metrics"][
                "generated_vs_p0_bottom_extension_px"
            ],
            "generated_alpha_ratio_to_old": route["candidate_metrics"]["generated_alpha_ratio_to_old"],
        }

    if replaced_count != 1:
        raise RuntimeError(f"Expected to replace exactly one torso_base entry, replaced {replaced_count}")

    manifest["quality_gate_interpretation"].update(
        {
            "g4_torso_selection": "GENERATED_TORSO_SELECTED_FOR_NEXT_REBUILD_REVIEW_REQUIRED",
            "g4_g5_visual_overlay": "REVIEW_REQUIRED_FOR_GENERATED_TORSO_AND_REMAINING_B4_B5",
            "g5_material_acceptance": "BLOCKED_PENDING_NEXT_OVERLAY_QA_AND_SEPARATE_G5_ACCEPTANCE",
            "param_hair_front": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_diagnostic": "BLOCKED_UNTIL_VISUAL_QA_ACCEPTS_B1_B5",
            "g8_real_cubism_authoring": "BLOCKED_UNTIL_MATERIAL_QA_AND_VISUAL_REVIEW",
        }
    )
    manifest["decision"] = (
        "This 64-part manifest variant replaces only B5 torso_base with the generated G4 torso candidate selected by "
        "focused overlay QA. It is technically complete and ready for overlay review, but does not promote material PASS, "
        "ParamHairFront, Mini Cubism, or real Cubism."
    )
    manifest["next_action"] = [
        "Run G4 torso-selected manifest overlay QA.",
        "If overlay QA remains review-required, build a focused reduction packet instead of unlocking G5.",
        "Keep material PASS, ParamHairFront, G7 Mini Cubism, and G8 real Cubism blocked.",
    ]
    manifest["self_review"].update(
        {
            "g4_torso_route_status": route["status"],
            "g4_torso_route": route["qa"]["route"],
            "generated_torso_candidate": rel(TORSO_CANDIDATE),
            "generated_torso_alpha_coverage": route["candidate_metrics"]["generated"]["alpha_coverage"],
            "generated_torso_bbox": route["candidate_metrics"]["generated"]["bbox"],
            "generated_vs_p0_bottom_extension_px": route["candidate_metrics"][
                "generated_vs_p0_bottom_extension_px"
            ],
            "generated_alpha_ratio_to_old": route["candidate_metrics"]["generated_alpha_ratio_to_old"],
            "g4_torso_selected_replacement_count": replaced_count,
            "g4_visual_overlay_status": "REVIEW_REQUIRED",
            "g5_material_acceptance_status": "BLOCKED_PENDING_NEXT_OVERLAY_QA_AND_SEPARATE_G5_ACCEPTANCE",
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
        "# Character 002 v22 64-Part G4 Torso-Selected Manifest",
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

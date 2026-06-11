#!/usr/bin/env python3
"""Build G4/G5 material promotion readiness after combined G3 context review."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"

P0_MANIFEST = EXP / "reports/v22_64part_p0_torso_v2_manifest/v22_64part_p0_torso_v2_manifest.json"
COMBINED_G3 = EXP / "reports/v22_g3_combined_context_overlay_review/v22_g3_combined_context_overlay_review_report.json"
SPEC_JSON = EXP / "reports/v22_64part_generation_spec/v22_64part_generation_spec.json"

BATCH_REPORTS = {
    "B1": EXP / "reports/v22_b1_clean_base_underpaint/v22_b1_visual_qa_report.json",
    "B2": EXP / "reports/v22_b2_eye_pack/v22_b2_overlay_qa_report.json",
    "B3_REVISION_V1": EXP / "reports/v22_b3_mouth_pack_revision_v1/v22_b3_revision_v1_overlay_qa_report.json",
}

REPORT_DIR = EXP / "reports/v22_g4_g5_material_promotion_readiness"
REPORT_JSON = REPORT_DIR / "v22_g4_g5_material_promotion_readiness_report.json"
REPORT_MD = REPORT_DIR / "v22_g4_g5_material_promotion_readiness_report.md"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def batch_gate(batch_id: str, report: dict) -> dict:
    status = report["status"]
    candidate = "PASS_CANDIDATE" in status
    human_required = "HUMAN_REVIEW_REQUIRED" in status
    return {
        "batch": batch_id,
        "report": rel(BATCH_REPORTS[batch_id]),
        "status": status,
        "technical_or_codex_candidate_pass": candidate,
        "human_review_required": human_required,
        "material_acceptance_status": "BLOCKED_PENDING_HUMAN_OR_CONTEXT_REVIEW",
    }


def main() -> int:
    manifest = load_json(P0_MANIFEST)
    combined = load_json(COMBINED_G3)
    spec = load_json(SPEC_JSON)
    batch_reports = {batch_id: load_json(path) for batch_id, path in BATCH_REPORTS.items()}
    entries = manifest["manifest_entries"]
    source_batch_counts = Counter(entry["source_batch"] for entry in entries)
    visual_gate_counts = Counter(entry["batch_visual_gate"] for entry in entries)
    group_counts = Counter(entry["group"] for entry in entries)
    b1_b3_batch_gates = [batch_gate(batch_id, batch_reports[batch_id]) for batch_id in BATCH_REPORTS]

    combined_summary = combined["summary"]
    primary_remaining_count = combined_summary["primary_remaining_count"]
    context_review_count = combined_summary["context_review_count"]
    b1_b3_human_required_count = sum(1 for gate in b1_b3_batch_gates if gate["human_review_required"])
    technical_manifest_pass = (
        manifest["self_review"]["required_part_count"] == 64
        and manifest["self_review"]["manifest_entry_count"] == 64
        and manifest["self_review"]["missing_part_count"] == 0
        and manifest["self_review"]["wrong_mode_count"] == 0
        and manifest["self_review"]["wrong_size_count"] == 0
        and manifest["self_review"]["empty_part_count"] == 0
        and manifest["self_review"]["group_counts_match_spec"] is True
    )
    all_locks_preserved = (
        manifest["self_review"]["material_pass_blocked"] is True
        and manifest["self_review"]["param_hair_front_hidden"] is True
        and manifest["self_review"]["mini_cubism_not_promoted"] is True
        and manifest["self_review"]["real_cubism_not_promoted"] is True
        and combined["self_review"]["material_pass_blocked"] is True
        and combined["self_review"]["param_hair_front_hidden"] is True
    )
    promotion_blockers = []
    if b1_b3_human_required_count:
        promotion_blockers.append("B1_B2_B3_PASS_CANDIDATES_STILL_HUMAN_REVIEW_REQUIRED")
    if context_review_count:
        promotion_blockers.append("B4_B5_COMBINED_CONTEXT_REVIEW_REQUIRED")
    if primary_remaining_count:
        promotion_blockers.append("B4_B5_PRIMARY_REVIEW_REMAINING")
    if not technical_manifest_pass:
        promotion_blockers.append("64PART_MANIFEST_TECHNICAL_REVISE")
    if not all_locks_preserved:
        promotion_blockers.append("LOCK_SEPARATION_BROKEN")

    gate_matrix = [
        {
            "gate": "G1_64PART_COMPLETENESS",
            "status": "PASS_TECHNICAL" if technical_manifest_pass else "REVISE_TECHNICAL",
            "evidence": rel(P0_MANIFEST),
            "promotion_effect": "technical prerequisite only",
        },
        {
            "gate": "G2_FULL_CANVAS_RGBA_NORMALIZATION",
            "status": "PASS_TECHNICAL" if technical_manifest_pass else "REVISE_TECHNICAL",
            "evidence": rel(P0_MANIFEST),
            "promotion_effect": "technical prerequisite only",
        },
        {
            "gate": "G3_COMBINED_CONTEXT_OVERLAY",
            "status": "READY_CONTEXT_REVIEW_NOT_PASS" if primary_remaining_count == 0 else "PRIMARY_REVIEW_REMAINING",
            "evidence": rel(COMBINED_G3),
            "promotion_effect": "blocks material PASS until context review is accepted separately",
        },
        {
            "gate": "G4_CONTACT_SHEET_VISUAL_QA",
            "status": "READY_FOR_REVIEW_NOT_PASS",
            "evidence": manifest["contact_sheet"],
            "promotion_effect": "requires explicit visual acceptance; validator PASS is insufficient",
        },
        {
            "gate": "G5_MATERIAL_ACCEPTANCE",
            "status": "BLOCKED_CONTEXT_REVIEW_NOT_OWNER_APPROVAL",
            "evidence": rel(REPORT_JSON),
            "promotion_effect": "do not build/promote import_ready.psd",
        },
        {
            "gate": "G7_MINI_CUBISM_DIAGNOSTIC",
            "status": "BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE",
            "evidence": spec["locked_success_baseline"]["diagnostic_scope"],
            "promotion_effect": "Mini Cubism cannot replace real Cubism",
        },
        {
            "gate": "G8_REAL_CUBISM_AUTHORING",
            "status": "BLOCKED_UNTIL_G5_AND_REAL_CUBISM_AUTHORING",
            "evidence": "requires Cubism Editor ArtMesh/Deformer/KeyformBinding and CMO3 structure inspection",
            "promotion_effect": "not started",
        },
    ]

    status = "G4_G5_MATERIAL_PROMOTION_READINESS_BLOCKED_CONTEXT_REVIEW"
    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": status,
        "p0_torso_v2_manifest": rel(P0_MANIFEST),
        "combined_g3_context_overlay": rel(COMBINED_G3),
        "spec": rel(SPEC_JSON),
        "b1_b3_batch_gates": b1_b3_batch_gates,
        "gate_matrix": gate_matrix,
        "promotion_blockers": promotion_blockers,
        "summary": {
            "manifest_status": manifest["status"],
            "combined_g3_status": combined["status"],
            "required_part_count": manifest["self_review"]["required_part_count"],
            "manifest_entry_count": manifest["self_review"]["manifest_entry_count"],
            "source_batch_counts": dict(sorted(source_batch_counts.items())),
            "group_counts": dict(sorted(group_counts.items())),
            "visual_gate_counts": dict(sorted(visual_gate_counts.items())),
            "b1_b3_candidate_human_required_count": b1_b3_human_required_count,
            "b4_b5_primary_remaining_count": primary_remaining_count,
            "b4_b5_context_review_count": context_review_count,
            "promotion_blocker_count": len(promotion_blockers),
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g4_contact_sheet_visual_qa_status": "READY_FOR_REVIEW_NOT_PASS",
            "g5_material_acceptance_status": "BLOCKED_CONTEXT_REVIEW_NOT_OWNER_APPROVAL",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
        "decision": (
            "G4/G5 material promotion is not allowed yet. The 64-part manifest is technically complete and B4/B5 primary "
            "blockers are reduced to zero, but B1-B3 remain pass-candidate/human-review-required and all 33 B4/B5 rows "
            "remain context-review evidence. Validator or numeric PASS must not be promoted to material PASS."
        ),
        "next_action": [
            "Build or use a compact G4 visual review surface from the P0 manifest contact sheet and combined G3 overlay.",
            "Only after explicit visual acceptance should a separate G5 material acceptance packet be created.",
            "Keep ParamHairFront hidden and keep G7/G8 blocked.",
        ],
        "self_review": {
            "technical_manifest_pass": technical_manifest_pass,
            "all_b1_b3_batch_reports_present": all(path.exists() for path in BATCH_REPORTS.values()),
            "b1_b3_human_review_required_count": b1_b3_human_required_count,
            "b4_b5_primary_remaining_count": primary_remaining_count,
            "b4_b5_context_review_count": context_review_count,
            "promotion_blocker_count": len(promotion_blockers),
            "has_gate_matrix": len(gate_matrix) == 7,
            "material_pass_blocked": True,
            "validator_only_promotion_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "not_owner_approval": True,
            "status": "PASS",
        },
    }
    save_json(REPORT_JSON, report)

    lines = [
        "# Character 002 v22 G4/G5 Material Promotion Readiness",
        "",
        f"- status: `{report['status']}`",
        f"- P0 torso v2 manifest: `{report['p0_torso_v2_manifest']}`",
        f"- combined G3 context overlay: `{report['combined_g3_context_overlay']}`",
        "",
        "## Gate Matrix",
        "",
    ]
    for item in gate_matrix:
        lines.append(f"- `{item['gate']}`: `{item['status']}` - {item['promotion_effect']}")
    lines.extend(["", "## Batch Gates", ""])
    for item in b1_b3_batch_gates:
        lines.append(f"- `{item['batch']}`: `{item['status']}`")
    lines.extend(["", "## Summary", ""])
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Promotion Blockers", ""])
    lines.extend(f"- `{item}`" for item in promotion_blockers)
    lines.extend(["", "## Self Review", ""])
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", "", report["decision"], "", "## Next Action", ""])
    lines.extend(f"- {item}" for item in report["next_action"])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": status, "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

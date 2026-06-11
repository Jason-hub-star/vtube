#!/usr/bin/env python3
"""Build the v22 G4 visual decision packet for character 002.

This creates a machine-checkable decision template for the five compact G4
review items. It intentionally keeps all decisions pending and keeps material
promotion blocked until a separate evidence-backed acceptance step exists.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"

G4_SURFACE_JSON = EXP / "reports/v22_g4_compact_visual_review_surface/v22_g4_compact_visual_review_surface_report.json"
G4_G5_READINESS_JSON = EXP / "reports/v22_g4_g5_material_promotion_readiness/v22_g4_g5_material_promotion_readiness_report.json"

REPORT_DIR = EXP / "reports/v22_g4_visual_decision_packet"
REPORT_JSON = REPORT_DIR / "v22_g4_visual_decision_packet.json"
REPORT_MD = REPORT_DIR / "v22_g4_visual_decision_packet.md"
DECISION_TEMPLATE_JSON = REPORT_DIR / "v22_g4_visual_decision_template.json"
SMOKE_DECISIONS_JSON = REPORT_DIR / "v22_g4_visual_decision_smoke.json"

PENDING = "PENDING_VISUAL_REVIEW"
ALLOWED_DECISIONS = [
    PENDING,
    "ACCEPT_VISUAL_CANDIDATE_KEEP_MATERIAL_BLOCKED",
    "REVISE_BEFORE_G5",
    "REGENERATE_BATCH_OR_CONTEXT",
]

EXPECTED_REVIEW_ITEMS = [
    "B1_CLEAN_BASE_UNDERPAINT",
    "B2_EYE_PACK",
    "B3_MOUTH_PACK_REVISION_V1",
    "B4_B5_COMBINED_CONTEXT",
    "G1_G2_64PART_CONTACT",
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


def decision_scope(item_id: str) -> str:
    if item_id.startswith("B1_"):
        return "clean_base_underpaint_visual_acceptance"
    if item_id.startswith("B2_"):
        return "eye_pack_visual_acceptance"
    if item_id.startswith("B3_"):
        return "mouth_pack_visual_acceptance"
    if item_id == "B4_B5_COMBINED_CONTEXT":
        return "combined_hair_body_context_visual_acceptance"
    return "technical_manifest_contact_visual_order_acceptance"


def next_actions(item_id: str) -> dict:
    if item_id == "B4_B5_COMBINED_CONTEXT":
        return {
            "if_accept": "Keep B4/B5 as visual candidates only; G5 remains blocked until a separate material acceptance packet exists.",
            "if_revise": "Return to focused B4/B5 context rows and adjust only the failing masks, anchors, draw order, or mini-pass target.",
            "if_regenerate": "Regenerate the failing B4 or B5 batch/context only; do not restart B1-B3.",
        }
    if item_id == "G1_G2_64PART_CONTACT":
        return {
            "if_accept": "Treat the contact sheet as visually ordered enough for G4 review only; this is not material PASS.",
            "if_revise": "Revise manifest display/order or obvious wrong-layer presentation before G5.",
            "if_regenerate": "Rebuild the affected manifest source rows, preserving existing PASS candidates.",
        }
    return {
        "if_accept": "Keep this batch as a visual candidate; G5 remains blocked until the full five-item G4 packet is accepted separately.",
        "if_revise": "Apply focused mask/anchor/source cleanup for this batch before G5.",
        "if_regenerate": "Regenerate this batch only; do not restart unrelated B batches.",
    }


def build_decision_rows(surface: dict) -> list[dict]:
    items = {row["id"]: row for row in surface["review_items"]}
    rows = []
    for item_id in EXPECTED_REVIEW_ITEMS:
        source = items[item_id]
        actions = next_actions(item_id)
        rows.append(
            {
                "id": item_id,
                "title": source["title"],
                "decision_scope": decision_scope(item_id),
                "source_status": source["source_status"],
                "review_gate": source["review_gate"],
                "image": source["image"],
                "report": source["report"],
                "visual_decision": PENDING,
                "allowed_visual_decisions": ALLOWED_DECISIONS,
                "review_note": "",
                "next_if_accept": actions["if_accept"],
                "next_if_revise": actions["if_revise"],
                "next_if_regenerate": actions["if_regenerate"],
                "material_promotion": "BLOCKED",
                "requires_separate_g5_acceptance": True,
            }
        )
    return rows


def build_template(rows: list[dict]) -> dict:
    return {
        "schema_version": "v1",
        "generated_at": now(),
        "status": "G4_VISUAL_DECISION_TEMPLATE_PENDING_REVIEW",
        "source_packet": rel(REPORT_JSON),
        "instructions": (
            "Fill visual_decision only with one of allowed_visual_decisions. "
            "No value in this template grants material PASS by itself."
        ),
        "allowed_visual_decisions": ALLOWED_DECISIONS,
        "decisions": [
            {
                "id": row["id"],
                "title": row["title"],
                "visual_decision": row["visual_decision"],
                "allowed_visual_decisions": row["allowed_visual_decisions"],
                "review_note": row["review_note"],
            }
            for row in rows
        ],
        "locks": {
            "material_pass_status": "BLOCKED",
            "g5_material_acceptance_status": "BLOCKED_CONTEXT_REVIEW_NOT_OWNER_APPROVAL",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
    }


def build_smoke_decisions(rows: list[dict]) -> dict:
    return {
        "schema_version": "v1",
        "generated_at": now(),
        "status": "G4_VISUAL_DECISION_SMOKE_PENDING_ONLY",
        "source_packet": rel(REPORT_JSON),
        "decisions": [
            {
                "id": row["id"],
                "visual_decision": PENDING,
                "review_note": "smoke validation keeps all rows pending",
            }
            for row in rows
        ],
    }


def self_review(report: dict, surface: dict, readiness: dict, template: dict, smoke: dict) -> dict:
    rows = report["visual_decision_items"]
    row_ids = [row["id"] for row in rows]
    source_images = [ROOT / row["image"] for row in rows]
    source_reports = [ROOT / row["report"] for row in rows]
    allowed_values_ok = all(
        row["visual_decision"] in row["allowed_visual_decisions"]
        and row["allowed_visual_decisions"] == ALLOWED_DECISIONS
        for row in rows
    )
    smoke_values_ok = all(row["visual_decision"] in ALLOWED_DECISIONS for row in smoke["decisions"])
    return {
        "surface_status": surface["status"],
        "readiness_status": readiness["status"],
        "decision_item_count": len(rows),
        "expected_review_items_present": row_ids == EXPECTED_REVIEW_ITEMS,
        "allowed_visual_decision_values_checked": allowed_values_ok,
        "smoke_decision_values_checked": smoke_values_ok,
        "all_decisions_pending": all(row["visual_decision"] == PENDING for row in rows),
        "all_source_images_exist": all(path.exists() for path in source_images),
        "all_source_reports_exist": all(path.exists() for path in source_reports),
        "decision_template_exists": DECISION_TEMPLATE_JSON.exists(),
        "smoke_decisions_exists": SMOKE_DECISIONS_JSON.exists(),
        "template_decision_count": len(template["decisions"]),
        "smoke_decision_count": len(smoke["decisions"]),
        "requires_visual_acceptance": True,
        "requires_separate_g5_acceptance": True,
        "material_pass_blocked": True,
        "validator_only_promotion_blocked": True,
        "param_hair_front_hidden": True,
        "mini_cubism_not_promoted": True,
        "real_cubism_not_promoted": True,
        "not_owner_approval": True,
        "status": "PASS",
    }


def write_markdown(report: dict) -> None:
    lines = [
        "# Character 002 v22 G4 Visual Decision Packet",
        "",
        f"- status: `{report['status']}`",
        f"- source surface: `{report['g4_compact_visual_review_surface']}`",
        f"- decision template: `{report['decision_template']}`",
        f"- smoke decisions: `{report['smoke_decisions']}`",
        f"- material PASS: `{report['summary']['material_pass_status']}`",
        f"- G5 material acceptance: `{report['summary']['g5_material_acceptance_status']}`",
        f"- ParamHairFront: `{report['summary']['param_hair_front_status']}`",
        f"- G7 Mini Cubism: `{report['summary']['g7_mini_cubism_status']}`",
        f"- G8 real Cubism: `{report['summary']['g8_real_cubism_status']}`",
        "",
        "## Decision Items",
        "",
    ]
    for row in report["visual_decision_items"]:
        lines.extend(
            [
                f"### {row['id']}",
                "",
                f"- title: `{row['title']}`",
                f"- source status: `{row['source_status']}`",
                f"- review gate: `{row['review_gate']}`",
                f"- visual decision: `{row['visual_decision']}`",
                f"- allowed decisions: `{', '.join(row['allowed_visual_decisions'])}`",
                f"- if accept: {row['next_if_accept']}",
                f"- if revise: {row['next_if_revise']}",
                f"- if regenerate: {row['next_if_regenerate']}",
                "",
            ]
        )
    lines.extend(["## Summary", ""])
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Self Review", ""])
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", "", report["decision"], "", "## Next Action", ""])
    lines.extend(f"- {item}" for item in report["next_action"])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    surface = load_json(G4_SURFACE_JSON)
    readiness = load_json(G4_G5_READINESS_JSON)
    rows = build_decision_rows(surface)
    template = build_template(rows)
    smoke = build_smoke_decisions(rows)
    save_json(DECISION_TEMPLATE_JSON, template)
    save_json(SMOKE_DECISIONS_JSON, smoke)

    status = "G4_VISUAL_DECISION_PACKET_READY_PENDING_REVIEW_MATERIAL_BLOCKED"
    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": status,
        "g4_compact_visual_review_surface": rel(G4_SURFACE_JSON),
        "g4_g5_material_promotion_readiness": rel(G4_G5_READINESS_JSON),
        "review_sheet": surface["review_sheet"],
        "decision_template": rel(DECISION_TEMPLATE_JSON),
        "smoke_decisions": rel(SMOKE_DECISIONS_JSON),
        "allowed_visual_decisions": ALLOWED_DECISIONS,
        "visual_decision_items": rows,
        "summary": {
            "decision_item_count": len(rows),
            "pending_visual_review_count": sum(1 for row in rows if row["visual_decision"] == PENDING),
            "accepted_visual_candidate_count": 0,
            "revise_before_g5_count": 0,
            "regenerate_batch_or_context_count": 0,
            "b4_b5_primary_remaining_count": surface["summary"]["b4_b5_primary_remaining_count"],
            "b4_b5_context_review_count": surface["summary"]["b4_b5_context_review_count"],
            "promotion_blocker_count": readiness["summary"]["promotion_blocker_count"],
            "g4_visual_review_status": "PENDING_VISUAL_REVIEW_NOT_PASS",
            "g5_material_acceptance_status": "BLOCKED_CONTEXT_REVIEW_NOT_OWNER_APPROVAL",
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
        "decision": (
            "The G4 visual decision packet is ready with five pending review rows. "
            "It records the allowed decisions and follow-up routes, but does not grant material PASS."
        ),
        "next_action": [
            "Use the decision template or a later UI to record G4 visual decisions.",
            "If rows are accepted, create a separate G5 material acceptance packet rather than promoting from this G4 packet.",
            "If any row is revise or regenerate, apply only that focused follow-up path.",
            "Keep ParamHairFront hidden, and keep G7/G8 blocked.",
        ],
    }
    report["self_review"] = self_review(report, surface, readiness, template, smoke)
    save_json(REPORT_JSON, report)
    write_markdown(report)

    print(json.dumps({"status": status, "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

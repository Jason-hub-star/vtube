#!/usr/bin/env python3
"""Build blocked G2-G5 material QA prep packet for character 002 v22.

The packet records what can be prepared after the corrected 64-part manifest
while preserving the visual/material/rig gate separation.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
MANIFEST_JSON = EXP / "reports/v22_64part_corrected_b4_b5_manifest/v22_64part_corrected_b4_b5_manifest.json"
TRIAGE_JSON = EXP / "reports/v22_64part_corrected_b4_b5_manifest/v22_corrected_b4_b5_codex_visual_triage.json"
REPORT_DIR = EXP / "reports/v22_g2_g5_material_qa_prep"
REPORT_JSON = REPORT_DIR / "v22_g2_g5_material_qa_prep_packet.json"
REPORT_MD = REPORT_DIR / "v22_g2_g5_material_qa_prep_packet.md"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    manifest = load_json(MANIFEST_JSON)
    triage = load_json(TRIAGE_JSON)
    entries = manifest["manifest_entries"]
    source_batch_counts = Counter(entry["source_batch"] for entry in entries)
    group_counts = Counter(entry["group"] for entry in entries)
    triage_entries = triage["triage_entries"]
    hard_review_parts = [entry["part_id"] for entry in triage_entries if entry["bucket"] == "HARD_REVIEW"]
    hold_review_parts = [entry["part_id"] for entry in triage_entries if entry["bucket"] == "HOLD_REVIEW"]
    auto_candidate_parts = [entry["part_id"] for entry in triage_entries if entry["bucket"] == "AUTO_CANDIDATE"]

    status = "G2_G5_MATERIAL_QA_PREP_PACKET_READY_BLOCKED_BY_CODEX_TRIAGE"
    prep_scope = [
        {
            "gate": "G2_LAYER_MANIFEST_TECHNICAL_QA",
            "status": "PREP_READY",
            "allowed_work": "Validate 64 full-canvas RGBA entries, group counts, layer paths, bbox, alpha coverage, and draw-order bands.",
        },
        {
            "gate": "G3_VISUAL_OVERLAY_QA",
            "status": "BLOCKED_REVIEW_REQUIRED",
            "allowed_work": "Use corrected B4/B5 overlay QA and Codex triage as visual review input; do not promote material PASS.",
        },
        {
            "gate": "G4_PSD_IMPORT_PREP",
            "status": "PREP_ONLY_BLOCKED",
            "allowed_work": "Prepare import ordering/checklist only; do not build or promote import_ready.psd from review-required B4/B5.",
        },
        {
            "gate": "G5_MATERIAL_ACCEPTANCE",
            "status": "BLOCKED",
            "allowed_work": "Wait for resolved B4/B5 hard/hold review or an explicit later promotion gate.",
        },
    ]
    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": status,
        "corrected_manifest": rel(MANIFEST_JSON),
        "codex_visual_triage": rel(TRIAGE_JSON),
        "prep_scope": prep_scope,
        "blockers": {
            "hard_review_parts": hard_review_parts,
            "hold_review_part_count": len(hold_review_parts),
            "auto_candidate_part_count": len(auto_candidate_parts),
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
        "summary": {
            "manifest_status": manifest["status"],
            "triage_status": triage["status"],
            "required_part_count": manifest["self_review"]["required_part_count"],
            "manifest_entry_count": manifest["self_review"]["manifest_entry_count"],
            "source_batch_counts": dict(sorted(source_batch_counts.items())),
            "group_counts": dict(sorted(group_counts.items())),
            "auto_candidate_count": triage["summary"]["auto_candidate_count"],
            "hold_review_count": triage["summary"]["hold_review_count"],
            "hard_review_count": triage["summary"]["hard_review_count"],
            "ready_gate_count": sum(1 for item in prep_scope if item["status"] == "PREP_READY"),
            "blocked_or_prep_only_gate_count": sum(1 for item in prep_scope if item["status"] != "PREP_READY"),
        },
        "decision": (
            "G2-G5 material QA can be prepared as a checklist and technical validation packet, but the corrected B4/B5 "
            "Codex triage blocks material acceptance, ParamHairFront, Mini Cubism, and real Cubism."
        ),
        "next_action": [
            "Run only G2 layer-manifest technical QA from the corrected 64-part manifest.",
            "Resolve B4/B5 hard and hold review rows before G4 PSD promotion or G5 material acceptance.",
            "Keep G7/G8 blocked until G5 material acceptance has independent visual evidence.",
        ],
        "self_review": {
            "manifest_status": manifest["status"],
            "triage_status": triage["status"],
            "manifest_entry_count": manifest["self_review"]["manifest_entry_count"],
            "triage_entry_count": triage["summary"]["triage_entry_count"],
            "hard_review_count": len(hard_review_parts),
            "hold_review_count": len(hold_review_parts),
            "auto_candidate_count": len(auto_candidate_parts),
            "has_g2_g5_scope": len(prep_scope) == 4,
            "technical_prep_ready": True,
            "material_pass_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "not_owner_approval": True,
            "status": "PASS",
        },
    }
    save_json(REPORT_JSON, report)

    lines = [
        "# Character 002 v22 G2-G5 Material QA Prep Packet",
        "",
        f"- status: `{report['status']}`",
        f"- corrected manifest: `{report['corrected_manifest']}`",
        f"- Codex visual triage: `{report['codex_visual_triage']}`",
        "",
        "## Scope",
        "",
    ]
    for item in prep_scope:
        lines.append(f"- `{item['gate']}`: `{item['status']}` - {item['allowed_work']}")
    lines.extend(["", "## Summary", ""])
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Blockers", ""])
    for key, value in report["blockers"].items():
        lines.append(f"- `{key}`: `{value}`")
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

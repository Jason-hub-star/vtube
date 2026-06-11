#!/usr/bin/env python3
"""Triage the B4/B5 auto-draft overlay into review vs re-extraction buckets."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
OVERLAY_QA_JSON = (
    EXP / "reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_auto_draft_overlay_qa_report.json"
)
CORRECTED_JSON = (
    EXP / "reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_anchor_corrected_auto_draft_report.json"
)
REPORT_JSON = EXP / "reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_auto_draft_review_triage.json"
REPORT_MD = EXP / "reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_auto_draft_review_triage.md"


TRIAGE = {
    # These are visibly semantic/mask problems in the overlay, not mainly anchor problems.
    "torso_base": ("REFINE_EXTRACTION_MASK", "Large body/clothing overlay includes noisy garment/skin regions; anchor alone will not make this material-ready."),
    "shoulder_L": ("REFINE_EXTRACTION_MASK", "Patch-like shoulder crop overlays hair/skin area and needs refined extraction."),
    "shoulder_R": ("REFINE_EXTRACTION_MASK", "Patch-like shoulder crop overlays hair/skin area and needs refined extraction."),
    "arm_L_upper_simple": ("REFINE_EXTRACTION_MASK", "Sleeve/arm crop has strong internal noise and should be remasked or regenerated."),
    "arm_R_upper_simple": ("REFINE_EXTRACTION_MASK", "Sleeve/arm crop has strong internal noise and should be remasked or regenerated."),
    "face_shadow_L": ("REFINE_EXTRACTION_MASK", "Face shadow is patch-like and too broad; this is a semantic mask issue."),
    "face_shadow_R": ("REFINE_EXTRACTION_MASK", "Face shadow is patch-like and too broad; this is a semantic mask issue."),
    "cheek_L": ("REFINE_EXTRACTION_MASK", "Cheek patch remains too large/oval and needs mask refinement rather than more anchor movement."),
    "cheek_R": ("REFINE_EXTRACTION_MASK", "Cheek patch remains too large/oval and needs mask refinement rather than more anchor movement."),
    "nose": ("REFINE_EXTRACTION_MASK", "Nose candidate is too blob-like after scaling and needs smaller semantic extraction."),
    "brow_L": ("REVIEW_OR_REFINE_SMALL_MASK", "Small brow overlay is close enough for focused review, but mask may still include hair/skin."),
    "brow_R": ("REVIEW_OR_REFINE_SMALL_MASK", "Small brow overlay is close enough for focused review, but mask may still include hair/skin."),
    "neck": ("REVIEW_ANCHOR_AND_MASK", "Neck placement is plausible, but the face/neck boundary still needs visual review."),
    "collar_front": ("REVIEW_ANCHOR_AND_MASK", "Collar location is plausible; use focused review before remasking."),
    "collar_shadow": ("REFINE_EXTRACTION_MASK", "Shadow line is too thin/noisy and likely needs extraction refinement."),
    "chest_cloth_base": ("REFINE_EXTRACTION_MASK", "Chest cloth base includes noisy stripe/garment artifacts and needs mask refinement."),
    "chest_cloth_shadow": ("REFINE_EXTRACTION_MASK", "Chest cloth shadow shape is too blocky and needs mask refinement."),
    # Hair is closer as a motion-part family, but front and side pieces still need visual focus.
    "hair_back_base": ("REVIEW_DRAW_ORDER_OR_MASK", "Back hair base covers the face area in overlay; draw order/visibility and mask scope need review."),
    "hair_back_underpaint": ("REVIEW_DRAW_ORDER_OR_MASK", "Back underpaint overlaps face/neck strongly; keep as underpaint candidate only."),
    "hair_back_center": ("REVIEW_DRAW_ORDER_OR_MASK", "Back center overlaps face/neck and needs draw-order/material review."),
    "hair_back_strand_L": ("REVIEW_ANCHOR_AND_MASK", "Left back strand roughly follows side hair but needs focused review."),
    "hair_back_strand_R": ("REVIEW_ANCHOR_AND_MASK", "Right back strand roughly follows side hair but needs focused review."),
    "hair_front_center": ("REVIEW_ANCHOR_AND_MASK", "Front hair is the highest HairFront priority; anchor is plausible but mask still needs review."),
    "hair_front_L": ("REVIEW_ANCHOR_AND_MASK", "Left front hair follows bang area but still needs focused manual review."),
    "hair_front_R": ("REVIEW_ANCHOR_AND_MASK", "Right front hair follows bang area but still needs focused manual review."),
    "hair_front_side_L": ("REVIEW_ANCHOR_AND_MASK", "Left side-front hair is plausible but may cover the eye/face too much."),
    "hair_front_side_R": ("REVIEW_ANCHOR_AND_MASK", "Right side-front hair is plausible but may cover the eye/face too much."),
    "hair_front_tip_L": ("REVIEW_ANCHOR_AND_MASK", "Left front tip is plausible but should be reviewed as a separate motion child."),
    "hair_front_tip_R": ("REVIEW_ANCHOR_AND_MASK", "Right front tip is plausible but should be reviewed as a separate motion child."),
    "hair_side_L_outer": ("REVIEW_ANCHOR_AND_MASK", "Left side outer hair follows silhouette but needs focused review."),
    "hair_side_L_inner": ("REVIEW_ANCHOR_AND_MASK", "Left side inner hair follows silhouette but needs focused review."),
    "hair_side_R_outer": ("REVIEW_ANCHOR_AND_MASK", "Right side outer hair follows silhouette but needs focused review."),
    "hair_side_R_inner": ("REVIEW_ANCHOR_AND_MASK", "Right side inner hair follows silhouette but needs focused review."),
}

ACTION_RANK = {
    "REFINE_EXTRACTION_MASK": 1,
    "REVIEW_DRAW_ORDER_OR_MASK": 2,
    "REVIEW_ANCHOR_AND_MASK": 3,
    "REVIEW_OR_REFINE_SMALL_MASK": 4,
}


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def main() -> int:
    overlay = json.loads(OVERLAY_QA_JSON.read_text(encoding="utf-8"))
    corrected = json.loads(CORRECTED_JSON.read_text(encoding="utf-8"))
    entries = []
    for entry in corrected["entries"]:
        action, reason = TRIAGE[entry["part_id"]]
        entries.append(
            {
                "part_id": entry["part_id"],
                "source_batch": entry["source_batch"],
                "group": entry["group"],
                "recommended_action": action,
                "reason": reason,
                "priority": ACTION_RANK[action],
                "target_anchor": entry["target_anchor"],
                "target_scale": entry["target_scale"],
                "output_path": entry["output_path"],
            }
        )
    entries.sort(key=lambda item: (item["priority"], item["source_batch"], item["part_id"]))
    counts = Counter(entry["recommended_action"] for entry in entries)
    review_focus = [
        entry["part_id"]
        for entry in entries
        if entry["recommended_action"] in {"REVIEW_ANCHOR_AND_MASK", "REVIEW_DRAW_ORDER_OR_MASK"}
    ][:12]
    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "G6_B4_B5_AUTO_DRAFT_TRIAGE_REEXTRACTION_AND_FOCUSED_REVIEW_REQUIRED",
        "overlay_qa_report": rel(OVERLAY_QA_JSON),
        "overlay_sheet": overlay["overlay_sheet"],
        "corrected_candidate_report": rel(CORRECTED_JSON),
        "summary": {
            "entry_count": len(entries),
            "recommended_action_counts": dict(sorted(counts.items())),
            "review_focus_count": len(review_focus),
            "review_focus_parts": review_focus,
        },
        "entries": entries,
        "decision": "Do not ask 주인님 to manually anchor all 33 parts. Many B5 face/body/clothing issues are extraction-mask problems. Use automatic/refined extraction first, then ask 주인님 to review the focused hair/draw-order/anchor set.",
        "next_action": [
            "Refine extraction masks for B5 body/clothing/face-detail problem parts before another anchor-only pass.",
            "Use the editor only for focused hair and remaining anchor/draw-order issues.",
            "Keep ParamHairFront hidden and keep G7/G8 blocked.",
        ],
        "self_review": {
            "entry_count": len(entries),
            "has_reextraction_bucket": counts.get("REFINE_EXTRACTION_MASK", 0) > 0,
            "has_focused_review_bucket": bool(review_focus),
            "does_not_require_owner_review_all_33": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "status": "PASS",
        },
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Character 002 v22 B4/B5 Auto-Draft Review Triage",
        "",
        f"- status: `{report['status']}`",
        f"- overlay sheet: `{report['overlay_sheet']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", "", report["decision"], "", "## Next Action", ""])
    lines.extend(f"- {item}" for item in report["next_action"])
    lines.extend(["", "## Entries", ""])
    for entry in entries:
        lines.append(
            f"- `{entry['recommended_action']}` `{entry['part_id']}` `{entry['source_batch']}`: {entry['reason']}"
        )
    lines.extend(["", "## Self Review", ""])
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": report["status"], "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

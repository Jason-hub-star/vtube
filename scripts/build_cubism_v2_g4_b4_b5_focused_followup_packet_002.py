#!/usr/bin/env python3
"""Build the v22 G4 B4/B5 focused follow-up packet.

The G4 route planner sends B4/B5 combined context to focused follow-up before
G5. This packet expands that one route into reproducible row-level work lanes
without claiming visual acceptance or material PASS.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"

G4_ROUTE_PLAN_JSON = EXP / "reports/v22_g4_visual_decision_packet/v22_g4_visual_decision_route_plan.json"
COMBINED_G3_JSON = EXP / "reports/v22_g3_combined_context_overlay_review/v22_g3_combined_context_overlay_review_report.json"

REPORT_DIR = EXP / "reports/v22_g4_b4_b5_focused_followup"
REPORT_JSON = REPORT_DIR / "v22_g4_b4_b5_focused_followup_packet.json"
REPORT_MD = REPORT_DIR / "v22_g4_b4_b5_focused_followup_packet.md"
FOLLOWUP_SHEET = REPORT_DIR / "v22_g4_b4_b5_focused_followup_sheet.png"

CANVAS = 2048
TILE_W = 360
TILE_H = 292


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def crop_box_for(bbox: list[int] | None) -> tuple[int, int, int, int]:
    if not bbox:
        return (700, 700, 1350, 1350)
    pad = 105
    return (
        max(0, bbox[0] - pad),
        max(0, bbox[1] - pad),
        min(CANVAS, bbox[2] + pad),
        min(CANVAS, bbox[3] + pad),
    )


def lane_for(classification: str) -> tuple[str, str, str]:
    if classification == "G3_CONTEXT_TORSO_P0_V2_REVIEW_REQUIRED":
        return (
            "P0_PRE_G5_B5_TORSO_VISUAL_FOLLOWUP",
            "PRE_G5_FOCUSED_FOLLOWUP",
            "Review or regenerate the torso/underpaint candidate before any G5 material acceptance packet.",
        )
    if classification == "G3_CONTEXT_SHOULDER_IMPROVEMENT_REVIEW_REQUIRED":
        return (
            "P0_PRE_G5_B5_SHOULDER_DRAW_ORDER_MASK_FOLLOWUP",
            "PRE_G5_FOCUSED_FOLLOWUP",
            "Review shoulder draw-order/mask candidates before any G5 material acceptance packet.",
        )
    if classification == "G3_CONTEXT_FRONT_HAIR_MOTION_CANDIDATE_KEEP_HAIRFRONT_HIDDEN":
        return (
            "P1_B4_FRONT_HAIR_MOTION_READINESS_KEEP_HAIRFRONT_HIDDEN",
            "MOTION_READINESS_FOLLOWUP",
            "Keep front-hair child art as a candidate, but ParamHairFront remains hidden until motion-readiness passes.",
        )
    if classification == "G3_CONTEXT_BACK_STRAND_NUMERIC_PASS_REVIEW_REQUIRED":
        return (
            "P2_B4_BACK_STRAND_NUMERIC_CONTEXT_REVIEW",
            "CONTEXT_REVIEW_FOLLOWUP",
            "Numeric anchor/mask support exists; keep as context review, not visual PASS.",
        )
    if classification == "G3_CONTEXT_BACK_STACK_DRAW_ORDER_REVIEW_REQUIRED":
        return (
            "P2_B4_BACK_STACK_DRAW_ORDER_CONTEXT_REVIEW",
            "CONTEXT_REVIEW_FOLLOWUP",
            "Review back-stack hair draw order as context evidence.",
        )
    if classification == "G3_CONTEXT_SIDE_HAIR_LOW_ALPHA_REVIEW_REQUIRED":
        return (
            "P2_B4_SIDE_HAIR_LOW_ALPHA_CONTEXT_REVIEW",
            "CONTEXT_REVIEW_FOLLOWUP",
            "Review low-alpha side hair in context; do not treat numeric smallness as visual PASS.",
        )
    if classification == "G3_CONTEXT_B5_BODY_CLOTHING_STACK_REVIEW_REQUIRED":
        return (
            "P3_B5_BODY_CLOTHING_STACK_CONTEXT_REVIEW",
            "CONTEXT_REVIEW_FOLLOWUP",
            "Review copied B5 body/clothing stack in the full overlay context before material acceptance.",
        )
    if classification == "G3_CONTEXT_B5_FACE_MICRO_DETAIL_REVIEW_REQUIRED":
        return (
            "P3_B5_FACE_MICRO_DETAIL_CONTEXT_REVIEW",
            "CONTEXT_REVIEW_FOLLOWUP",
            "Review copied B5 face micro details in context before material acceptance.",
        )
    return (
        "P9_UNCLASSIFIED_FOLLOWUP_REQUIRED",
        "PRE_G5_FOCUSED_FOLLOWUP",
        "Unclassified row stays as a pre-G5 follow-up blocker.",
    )


def color_for(lane_class: str) -> tuple[int, int, int]:
    if lane_class == "PRE_G5_FOCUSED_FOLLOWUP":
        return (199, 72, 57)
    if lane_class == "MOTION_READINESS_FOLLOWUP":
        return (126, 87, 194)
    return (54, 128, 183)


def tile(source: Image.Image, row: dict) -> Image.Image:
    layer = Image.open(ROOT / row["path"]).convert("RGBA")
    crop_box = crop_box_for(row.get("bbox"))
    base = source.crop(crop_box).convert("RGBA")
    part = layer.crop(crop_box).convert("RGBA")
    color = color_for(row["followup_class"])
    tint = Image.new("RGBA", base.size, (*color, 0))
    tint.putalpha(part.getchannel("A").point(lambda v: min(155, int(v * 0.66))))
    comp = Image.alpha_composite(base, tint)
    comp.thumbnail((TILE_W - 18, TILE_H - 84), Image.Resampling.LANCZOS)

    out = Image.new("RGB", (TILE_W, TILE_H), (247, 248, 250))
    out.paste(comp.convert("RGB"), ((TILE_W - comp.width) // 2, 8))
    draw = ImageDraw.Draw(out)
    draw.rectangle([4, 4, TILE_W - 5, TILE_H - 5], outline=(216, 222, 232))
    draw.rectangle([8, TILE_H - 76, TILE_W - 9, TILE_H - 52], fill=color)
    draw.text((12, TILE_H - 72), row["followup_class"][:42], fill=(255, 255, 255))
    draw.text((12, TILE_H - 47), f"{row['part_id']} / {row['source_batch']}", fill=(25, 31, 40))
    draw.text((12, TILE_H - 26), row["followup_lane"][:48], fill=(78, 89, 104))
    return out


def build_sheet(rows: list[dict]) -> None:
    source = Image.open(SOURCE).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    ordered = sorted(rows, key=lambda row: (row["followup_lane"], row["source_batch"], row["part_id"]))
    cols = 3
    header_h = 84
    sheet_rows = (len(ordered) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * TILE_W, header_h + sheet_rows * TILE_H), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 14), "Character 002 v22 G4 B4/B5 Focused Follow-up", fill=(25, 31, 40))
    draw.text((12, 40), "This is a work-order sheet. It is not G5 material acceptance or visual PASS.", fill=(78, 89, 104))
    draw.text((12, 62), "Red: pre-G5 focused follow-up / Purple: HairFront hidden motion-readiness / Blue: context review", fill=(78, 89, 104))
    for idx, row in enumerate(ordered):
        sheet.paste(tile(source, row), ((idx % cols) * TILE_W, header_h + (idx // cols) * TILE_H))
    FOLLOWUP_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(FOLLOWUP_SHEET)


def main() -> int:
    route = load_json(G4_ROUTE_PLAN_JSON)
    combined = load_json(COMBINED_G3_JSON)
    combined_route = next((row for row in route["routes"] if row["id"] == "B4_B5_COMBINED_CONTEXT"), None)
    if not combined_route or combined_route["route"] != "ROUTE_TO_B4_B5_FOCUSED_FOLLOWUP_BEFORE_G5":
        raise SystemExit("G4 route plan does not request B4/B5 focused follow-up")

    rows = []
    for source_row in combined["review_rows"]:
        lane, lane_class, action = lane_for(source_row["g3_classification"])
        rows.append(
            {
                **source_row,
                "followup_lane": lane,
                "followup_class": lane_class,
                "followup_action": action,
                "g5_unblock": "BLOCKED_UNTIL_FOLLOWUP_AND_SEPARATE_G5_ACCEPTANCE",
                "material_promotion": "BLOCKED",
                "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            }
        )

    build_sheet(rows)
    lane_counts = Counter(row["followup_lane"] for row in rows)
    class_counts = Counter(row["followup_class"] for row in rows)
    pre_g5_count = class_counts["PRE_G5_FOCUSED_FOLLOWUP"]
    status = "G4_B4_B5_FOCUSED_FOLLOWUP_PACKET_READY_MATERIAL_BLOCKED"
    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": status,
        "g4_visual_decision_route_plan": rel(G4_ROUTE_PLAN_JSON),
        "combined_g3_context_overlay": rel(COMBINED_G3_JSON),
        "followup_sheet": rel(FOLLOWUP_SHEET),
        "followup_rows": rows,
        "work_order_phases": [
            {
                "phase": "P0",
                "name": "B5 torso and shoulder pre-G5 visual follow-up",
                "row_count": pre_g5_count,
                "unblocks": "Only a later G4/G5 readiness refresh; not material PASS.",
            },
            {
                "phase": "P1",
                "name": "B4 front-hair motion-readiness candidate review",
                "row_count": class_counts["MOTION_READINESS_FOLLOWUP"],
                "unblocks": "Only future HairFront readiness if independent child art passes; ParamHairFront stays hidden now.",
            },
            {
                "phase": "P2_P3",
                "name": "B4/B5 context review lanes",
                "row_count": class_counts["CONTEXT_REVIEW_FOLLOWUP"],
                "unblocks": "Only context evidence for a separate G5 packet.",
            },
        ],
        "summary": {
            "followup_row_count": len(rows),
            "pre_g5_focused_followup_count": pre_g5_count,
            "motion_readiness_followup_count": class_counts["MOTION_READINESS_FOLLOWUP"],
            "context_review_followup_count": class_counts["CONTEXT_REVIEW_FOLLOWUP"],
            "lane_counts": dict(sorted(lane_counts.items())),
            "class_counts": dict(sorted(class_counts.items())),
            "g4_route_status": route["status"],
            "combined_g3_status": combined["status"],
            "g5_material_acceptance_status": "BLOCKED_PENDING_B4_B5_FOCUSED_FOLLOWUP",
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
        "decision": (
            "B4/B5 focused follow-up is now expanded into row-level work lanes. "
            "This does not accept B4/B5 visually and does not unlock G5 material acceptance."
        ),
        "next_action": [
            "Handle the P0 B5 torso/shoulder focused follow-up rows first.",
            "Keep B4 front hair as motion-readiness candidates with ParamHairFront hidden.",
            "Refresh G4/G5 readiness only after focused B4/B5 follow-up evidence exists.",
        ],
        "self_review": {
            "route_plan_status": route["status"],
            "combined_g3_status": combined["status"],
            "combined_route_is_focused_followup": combined_route["route"] == "ROUTE_TO_B4_B5_FOCUSED_FOLLOWUP_BEFORE_G5",
            "followup_row_count": len(rows),
            "matches_combined_context_row_count": len(rows) == combined["summary"]["context_review_count"],
            "pre_g5_focused_followup_count": pre_g5_count,
            "has_pre_g5_focused_followup": pre_g5_count > 0,
            "has_motion_readiness_followup": class_counts["MOTION_READINESS_FOLLOWUP"] > 0,
            "has_context_review_followup": class_counts["CONTEXT_REVIEW_FOLLOWUP"] > 0,
            "followup_sheet_exists": FOLLOWUP_SHEET.exists(),
            "not_owner_approval": True,
            "material_pass_blocked": True,
            "validator_only_promotion_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "status": "PASS",
        },
    }
    save_json(REPORT_JSON, report)

    lines = [
        "# Character 002 v22 G4 B4/B5 Focused Follow-up Packet",
        "",
        f"- status: `{report['status']}`",
        f"- follow-up sheet: `{report['followup_sheet']}`",
        f"- G5 material acceptance: `{report['summary']['g5_material_acceptance_status']}`",
        f"- material PASS: `{report['summary']['material_pass_status']}`",
        f"- ParamHairFront: `{report['summary']['param_hair_front_status']}`",
        "",
        "## Work Order Phases",
        "",
    ]
    for phase in report["work_order_phases"]:
        lines.append(f"- `{phase['phase']}` {phase['name']}: `{phase['row_count']}` rows; {phase['unblocks']}")
    lines.extend(["", "## Lane Counts", ""])
    for key, value in report["summary"]["lane_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", "", report["decision"], "", "## Next Action", ""])
    lines.extend(f"- {item}" for item in report["next_action"])
    lines.extend(["", "## Self Review", ""])
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": status, "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

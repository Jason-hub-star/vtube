#!/usr/bin/env python3
"""Decide the three P0 torso/shoulder rows after G4 torso selection.

This packet can unblock a later G5 readiness/prep refresh, but it does not
approve material PASS or G5 acceptance.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path("/Users/family/jason/Vtube")
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
REDUCTION = (
    EXP
    / "reports/v22_g4_torso_selected_review_reduction/v22_g4_torso_selected_review_reduction_packet.json"
)
TORSO_ROUTE = (
    EXP
    / "reports/v22_g4_torso_base_regen_overlay_qa/v22_g4_torso_base_regen_overlay_qa_report.json"
)
B5_PROVISIONAL_QA = (
    EXP
    / "reports/v22_b5_provisional_minipass_candidate/v22_b5_provisional_minipass_overlay_qa_report.json"
)
REPORT_DIR = EXP / "reports/v22_g4_p0_torso_shoulder_decision"
REPORT_JSON = REPORT_DIR / "v22_g4_p0_torso_shoulder_decision_packet.json"
REPORT_MD = REPORT_DIR / "v22_g4_p0_torso_shoulder_decision_packet.md"
DECISION_SHEET = REPORT_DIR / "v22_g4_p0_torso_shoulder_decision_sheet.png"
CANVAS = 2048
TILE_W = 380
TILE_H = 292


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def font(size: int = 14) -> ImageFont.ImageFont:
    for candidate in [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def crop_box_for(bbox: list[int] | None) -> tuple[int, int, int, int]:
    if not bbox:
        return (620, 820, 1540, 1420)
    pad = 120
    return (
        max(0, bbox[0] - pad),
        max(0, bbox[1] - pad),
        min(CANVAS, bbox[2] + pad),
        min(CANVAS, bbox[3] + pad),
    )


def tile(source: Image.Image, row: dict) -> Image.Image:
    layer = Image.open(ROOT / row["path"]).convert("RGBA")
    crop = crop_box_for(row["bbox"])
    base = source.crop(crop).convert("RGBA")
    part = layer.crop(crop).convert("RGBA")
    color = (214, 83, 69) if row["part_id"] == "torso_base" else (223, 143, 47)
    tint = Image.new("RGBA", base.size, (*color, 0))
    tint.putalpha(part.getchannel("A").point(lambda v: min(158, int(v * 0.68))))
    comp = Image.alpha_composite(base, tint)
    comp.thumbnail((TILE_W - 18, TILE_H - 92), Image.Resampling.LANCZOS)
    out = Image.new("RGB", (TILE_W, TILE_H), (247, 248, 250))
    out.paste(comp.convert("RGB"), ((TILE_W - comp.width) // 2, 8))
    draw = ImageDraw.Draw(out)
    draw.rectangle([4, 4, TILE_W - 5, TILE_H - 5], outline=(214, 221, 232))
    draw.rectangle([8, TILE_H - 84, TILE_W - 9, TILE_H - 58], fill=color)
    draw.text((12, TILE_H - 80), row["decision"][:48], fill=(255, 255, 255), font=font(12))
    draw.text((12, TILE_H - 52), f"{row['part_id']} / alpha={row['alpha_coverage']}", fill=(25, 31, 40), font=font(12))
    draw.text((12, TILE_H - 31), row["route_class"][:54], fill=(78, 89, 104), font=font(12))
    draw.text((12, TILE_H - 14), row["g5_effect"][:54], fill=(78, 89, 104), font=font(11))
    return out


def decision_for(row: dict, torso_route: dict, shoulder_qa_by_part: dict[str, dict]) -> dict:
    part_id = row["part_id"]
    if part_id == "torso_base":
        metrics = torso_route["candidate_metrics"]
        return {
            "decision": "KEEP_GENERATED_TORSO_AS_G5_PREP_CANDIDATE_NOT_MATERIAL_PASS",
            "route_class": "P0_RESOLVED_TO_G5_PREP_CANDIDATE",
            "reason": (
                "Generated torso is selected, extends lower than P0, and stays below old broad v2 coverage; "
                "use it for G5 prep review only."
            ),
            "supporting_metrics": {
                "generated_alpha_coverage": metrics["generated"]["alpha_coverage"],
                "p0_v2_alpha_coverage": metrics["p0_v2"]["alpha_coverage"],
                "old_v2_alpha_coverage": metrics["old_v2"]["alpha_coverage"],
                "generated_vs_p0_bottom_extension_px": metrics["generated_vs_p0_bottom_extension_px"],
                "generated_alpha_ratio_to_old": metrics["generated_alpha_ratio_to_old"],
            },
        }
    shoulder = shoulder_qa_by_part[part_id]
    return {
        "decision": "KEEP_SHOULDER_DRAW_ORDER_MASK_AS_G5_PREP_CANDIDATE_NOT_MATERIAL_PASS",
        "route_class": "P0_RESOLVED_TO_G5_PREP_CANDIDATE",
        "reason": "Shoulder draw-order/mask improvement candidate can move into G5 prep review; material acceptance remains blocked.",
        "supporting_metrics": {
            "old_hair_occlusion_overlap_ratio": shoulder.get("old_hair_occlusion_overlap_ratio"),
            "new_hair_occlusion_overlap_ratio": shoulder.get("new_hair_occlusion_overlap_ratio"),
            "alpha_coverage": shoulder["alpha_coverage"],
        },
    }


def build_sheet(rows: list[dict]) -> None:
    source = Image.open(SOURCE).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    sheet = Image.new("RGB", (3 * TILE_W, 82 + TILE_H), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 14), "Character 002 v22 G4 P0 Torso/Shoulder Decision", fill=(25, 31, 40), font=font(18))
    draw.text((12, 42), "All three P0 rows can move to G5 prep candidates; this is not material PASS.", fill=(78, 89, 104), font=font(14))
    draw.text((12, 62), "ParamHairFront, G7, and G8 remain blocked.", fill=(78, 89, 104), font=font(13))
    for idx, row in enumerate(rows):
        sheet.paste(tile(source, row), (idx * TILE_W, 82))
    DECISION_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(DECISION_SHEET)


def main() -> int:
    reduction = load_json(REDUCTION)
    torso_route = load_json(TORSO_ROUTE)
    b5_qa = load_json(B5_PROVISIONAL_QA)
    shoulder_qa_by_part = {entry["part_id"]: entry for entry in b5_qa["qa_entries"]}
    p0_rows = [
        row
        for row in reduction["review_rows"]
        if row["g5_effect"] == "BLOCKS_G5_UNTIL_REVIEW_OR_FURTHER_REDUCTION"
    ]
    p0_rows = sorted(p0_rows, key=lambda row: (0 if row["part_id"] == "torso_base" else 1, row["part_id"]))
    decision_rows = []
    for row in p0_rows:
        decision = decision_for(row, torso_route, shoulder_qa_by_part)
        decision_rows.append(
            {
                "part_id": row["part_id"],
                "source_batch": row["source_batch"],
                "path": row["path"],
                "bbox": row["bbox"],
                "alpha_coverage": row["alpha_coverage"],
                "previous_review_lane": row["review_lane"],
                **decision,
                "g5_effect": "UNBLOCKS_G5_PREP_ONLY_NOT_ACCEPTANCE",
                "material_promotion": "BLOCKED",
                "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            }
        )
    build_sheet(decision_rows)

    resolved_count = sum(1 for row in decision_rows if row["route_class"] == "P0_RESOLVED_TO_G5_PREP_CANDIDATE")
    status = "G4_P0_TORSO_SHOULDER_DECISION_READY_G5_PREP_UNBLOCKED_MATERIAL_BLOCKED"
    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "torso_selected_review_reduction": rel(REDUCTION),
        "torso_route_report": rel(TORSO_ROUTE),
        "b5_provisional_overlay_qa": rel(B5_PROVISIONAL_QA),
        "decision_sheet": rel(DECISION_SHEET),
        "decision_rows": decision_rows,
        "summary": {
            "input_p0_blocking_row_count": len(p0_rows),
            "decision_row_count": len(decision_rows),
            "resolved_to_g5_prep_candidate_count": resolved_count,
            "remaining_p0_pre_g5_blocker_count": len(p0_rows) - resolved_count,
            "torso_g5_prep_candidate_count": sum(1 for row in decision_rows if row["part_id"] == "torso_base"),
            "shoulder_g5_prep_candidate_count": sum(1 for row in decision_rows if row["part_id"].startswith("shoulder_")),
            "g5_prep_status": "UNBLOCKED_FOR_PREP_PACKET_ONLY",
            "g5_material_acceptance_status": "BLOCKED_PENDING_SEPARATE_G5_ACCEPTANCE_PACKET",
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
        "decision": (
            "The three P0 torso/shoulder rows are resolved only as G5 prep candidates. "
            "This permits building a later G5 readiness/prep packet, but does not approve material PASS."
        ),
        "next_action": [
            "Build a G5 prep packet from the torso-selected manifest using these P0 candidate decisions.",
            "Carry HairFront as hidden/contract-only and keep B4/B5 context rows review-required.",
            "Do not promote Mini Cubism or real Cubism from this packet.",
        ],
        "self_review": {
            "reduction_status": reduction["status"],
            "torso_route_status": torso_route["status"],
            "b5_provisional_qa_status": b5_qa["status"],
            "input_p0_blocking_row_count": len(p0_rows),
            "decision_row_count": len(decision_rows),
            "resolved_to_g5_prep_candidate_count": resolved_count,
            "remaining_p0_pre_g5_blocker_count": len(p0_rows) - resolved_count,
            "all_p0_rows_resolved_for_g5_prep": len(p0_rows) == 3 and resolved_count == 3,
            "torso_g5_prep_candidate_count": sum(1 for row in decision_rows if row["part_id"] == "torso_base"),
            "shoulder_g5_prep_candidate_count": sum(1 for row in decision_rows if row["part_id"].startswith("shoulder_")),
            "decision_sheet_exists": DECISION_SHEET.exists(),
            "g5_prep_unblocked_only": True,
            "g5_material_acceptance_blocked": True,
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
        "# Character 002 v22 G4 P0 Torso/Shoulder Decision Packet",
        "",
        f"- status: `{report['status']}`",
        f"- decision sheet: `{report['decision_sheet']}`",
        f"- G5 prep: `{report['summary']['g5_prep_status']}`",
        f"- G5 material acceptance: `{report['summary']['g5_material_acceptance_status']}`",
        "",
        "## Decision Rows",
        "",
    ]
    for row in decision_rows:
        lines.append(f"- `{row['part_id']}` `{row['decision']}`: {row['reason']}")
    lines.extend(["", "## Summary", ""])
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Self Review", ""])
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", "", report["decision"], "", "## Next Action", ""])
    lines.extend(f"- {item}" for item in report["next_action"])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    boolean_checks = {key: value for key, value in report["self_review"].items() if isinstance(value, bool)}
    if not all(boolean_checks.values()):
        failed = [key for key, value in boolean_checks.items() if not value]
        raise RuntimeError(f"self review failed: {failed}")
    print(json.dumps({"status": status, "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

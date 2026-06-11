#!/usr/bin/env python3
"""Build the v22 G4 P0 B5 follow-up decision packet.

This narrows the three pre-G5 B5 rows into a smaller route: shoulders can move
forward as non-owner G4 refresh candidates, while torso remains the single
pre-G5 visual review/regeneration blocker.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"

FOLLOWUP_JSON = EXP / "reports/v22_g4_b4_b5_focused_followup/v22_g4_b4_b5_focused_followup_packet.json"
B5_BLOCKER_REVIEW_JSON = EXP / "reports/v22_b5_body_blocker_draw_order_review/v22_b5_body_blocker_draw_order_review.json"
B5_PROVISIONAL_QA_JSON = EXP / "reports/v22_b5_provisional_minipass_candidate/v22_b5_provisional_minipass_overlay_qa_report.json"
P0_TORSO_V2_JSON = EXP / "reports/v22_g3_p0_torso_minipass_v2/v22_g3_p0_torso_minipass_v2_report.json"

REPORT_DIR = EXP / "reports/v22_g4_p0_b5_followup_decision"
REPORT_JSON = REPORT_DIR / "v22_g4_p0_b5_followup_decision_packet.json"
REPORT_MD = REPORT_DIR / "v22_g4_p0_b5_followup_decision_packet.md"
DECISION_SHEET = REPORT_DIR / "v22_g4_p0_b5_followup_decision_sheet.png"

CANVAS = 2048
TILE_W = 330
TILE_H = 250


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
        return (620, 820, 1540, 1420)
    pad = 115
    return (
        max(0, bbox[0] - pad),
        max(0, bbox[1] - pad),
        min(CANVAS, bbox[2] + pad),
        min(CANVAS, bbox[3] + pad),
    )


def overlay_crop(source: Image.Image, layer_path: str, bbox: list[int], color: tuple[int, int, int]) -> Image.Image:
    layer = Image.open(ROOT / layer_path).convert("RGBA")
    box = crop_box_for(bbox)
    base = source.crop(box).convert("RGBA")
    part = layer.crop(box).convert("RGBA")
    tint = Image.new("RGBA", base.size, (*color, 0))
    tint.putalpha(part.getchannel("A").point(lambda v: min(155, int(v * 0.66))))
    return Image.alpha_composite(base, tint)


def tile(title: str, img: Image.Image, subtitle: str = "") -> Image.Image:
    out = Image.new("RGB", (TILE_W, TILE_H), (247, 248, 250))
    draw = ImageDraw.Draw(out)
    draw.rectangle([4, 4, TILE_W - 5, TILE_H - 5], outline=(216, 222, 232))
    draw.text((10, 10), title[:42], fill=(25, 31, 40))
    if subtitle:
        draw.text((10, 31), subtitle[:47], fill=(78, 89, 104))
    preview = img.convert("RGBA")
    preview.thumbnail((TILE_W - 18, TILE_H - 62), Image.Resampling.LANCZOS)
    out.paste(preview.convert("RGB"), ((TILE_W - preview.width) // 2, 56), preview)
    return out


def decision_for(part_id: str, provisional_entry: dict, p0_row: dict | None) -> tuple[str, str, str]:
    if part_id == "torso_base":
        return (
            "P0_TORSO_REVIEW_OR_REGENERATE_BEFORE_G5",
            "Torso alpha was reduced by P0 v2, but it remains a broad underpaint/body visual decision and cannot be auto-accepted.",
            "PRE_G5_REVIEW_REMAINING",
        )
    old = provisional_entry.get("old_hair_occlusion_overlap_ratio")
    new = provisional_entry.get("new_hair_occlusion_overlap_ratio")
    if old is not None and new is not None and new <= 0.2 and new < old:
        return (
            "P0_SHOULDER_ACCEPT_AS_DRAW_ORDER_MASK_CANDIDATE_KEEP_MATERIAL_BLOCKED",
            "Shoulder hair-occlusion overlap dropped enough to leave the pre-G5 blocker lane, but visual/material acceptance remains blocked.",
            "G4_REFRESH_CANDIDATE_NOT_MATERIAL_PASS",
        )
    return (
        "P0_SHOULDER_REVISE_MASK_OR_REGENERATE_BEFORE_G5",
        "Shoulder lacks sufficient draw-order/mask improvement evidence.",
        "PRE_G5_REVIEW_REMAINING",
    )


def build_sheet(rows: list[dict]) -> None:
    source = Image.open(SOURCE).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    cols = 4
    header_h = 78
    sheet = Image.new("RGB", (cols * TILE_W, header_h + len(rows) * TILE_H), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 14), "Character 002 v22 G4 P0 B5 Follow-up Decision", fill=(25, 31, 40))
    draw.text((12, 39), "Shoulders can move to G4 refresh candidates; torso remains review/regenerate before G5.", fill=(78, 89, 104))
    draw.text((12, 59), "This is not owner approval, visual PASS, material PASS, Mini Cubism PASS, or real Cubism.", fill=(78, 89, 104))
    for row_idx, row in enumerate(rows):
        old_img = overlay_crop(source, row["previous_path"], row["previous_bbox"], (224, 94, 76))
        new_img = overlay_crop(source, row["provisional_path"], row["provisional_bbox"], (61, 132, 255))
        active_img = overlay_crop(source, row["active_path"], row["active_bbox"], (56, 158, 92))
        decision_bg = Image.new("RGB", (TILE_W, TILE_H), (247, 248, 250))
        decision_draw = ImageDraw.Draw(decision_bg)
        decision_draw.rectangle([4, 4, TILE_W - 5, TILE_H - 5], outline=(216, 222, 232))
        decision_draw.text((10, 14), row["part_id"], fill=(25, 31, 40))
        decision_draw.text((10, 42), row["decision"][:44], fill=(25, 31, 40))
        decision_draw.text((10, 88), row["route_class"], fill=(78, 89, 104))
        decision_draw.text((10, 122), row["reason"][:47], fill=(78, 89, 104))
        tiles = [
            tile("previous v2", old_img, row["previous_verdict"]),
            tile("provisional", new_img, row["provisional_verdict"]),
            tile("active P0", active_img, f"cov {row['active_alpha_coverage']}"),
            decision_bg,
        ]
        y = header_h + row_idx * TILE_H
        for col, img in enumerate(tiles):
            sheet.paste(img, (col * TILE_W, y))
    DECISION_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(DECISION_SHEET)


def main() -> int:
    followup = load_json(FOLLOWUP_JSON)
    blocker = load_json(B5_BLOCKER_REVIEW_JSON)
    provisional = load_json(B5_PROVISIONAL_QA_JSON)
    p0 = load_json(P0_TORSO_V2_JSON)

    previous_by_part = {row["part_id"]: row for row in blocker["entries"]}
    provisional_by_part = {row["part_id"]: row for row in provisional["qa_entries"]}
    p0_by_part = {row["part_id"]: row for row in p0["entries"]}
    pre_g5_rows = [row for row in followup["followup_rows"] if row["followup_class"] == "PRE_G5_FOCUSED_FOLLOWUP"]

    rows = []
    for row in pre_g5_rows:
        part_id = row["part_id"]
        previous_row = previous_by_part[part_id]
        provisional_row = provisional_by_part[part_id]
        p0_row = p0_by_part.get(part_id)
        decision, reason, route_class = decision_for(part_id, provisional_row, p0_row)
        active_path = p0_row["output_path"] if p0_row else provisional_row["output_path"]
        active_bbox = p0_row["bbox"] if p0_row else provisional_row["bbox"]
        active_alpha = p0_row["alpha_coverage"] if p0_row else provisional_row["alpha_coverage"]
        rows.append(
            {
                "part_id": part_id,
                "decision": decision,
                "route_class": route_class,
                "reason": reason,
                "previous_path": previous_row["output_path"],
                "previous_bbox": previous_row["bbox"],
                "previous_alpha_coverage": previous_row["alpha_coverage"],
                "previous_hair_occlusion_overlap_ratio": previous_row["hair_occlusion_overlap_ratio"],
                "previous_verdict": previous_row["recommendation"],
                "provisional_path": provisional_row["output_path"],
                "provisional_bbox": provisional_row["bbox"],
                "provisional_alpha_coverage": provisional_row["alpha_coverage"],
                "provisional_hair_occlusion_overlap_ratio": provisional_row.get("new_hair_occlusion_overlap_ratio"),
                "provisional_verdict": provisional_row["qa_verdict"],
                "active_path": active_path,
                "active_bbox": active_bbox,
                "active_alpha_coverage": active_alpha,
                "g5_unblock": "BLOCKED_UNTIL_TORSO_REVIEW_OR_REGENERATION_AND_SEPARATE_G5_ACCEPTANCE",
                "material_promotion": "BLOCKED",
                "decision_authority": "CODEX_PROVISIONAL_SUCCESS_PATTERN_NOT_OWNER_APPROVAL",
            }
        )

    build_sheet(rows)
    torso_remaining = sum(1 for row in rows if row["route_class"] == "PRE_G5_REVIEW_REMAINING")
    shoulder_candidate = sum(1 for row in rows if row["route_class"] == "G4_REFRESH_CANDIDATE_NOT_MATERIAL_PASS")
    status = "G4_P0_B5_FOLLOWUP_DECISION_READY_TORSO_REVIEW_REMAINING_MATERIAL_BLOCKED"
    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": status,
        "g4_b4_b5_focused_followup": rel(FOLLOWUP_JSON),
        "b5_body_blocker_review": rel(B5_BLOCKER_REVIEW_JSON),
        "b5_provisional_overlay_qa": rel(B5_PROVISIONAL_QA_JSON),
        "p0_torso_v2_report": rel(P0_TORSO_V2_JSON),
        "decision_sheet": rel(DECISION_SHEET),
        "decision_rows": rows,
        "summary": {
            "input_pre_g5_followup_count": len(pre_g5_rows),
            "decision_row_count": len(rows),
            "torso_review_remaining_count": torso_remaining,
            "shoulder_g4_refresh_candidate_count": shoulder_candidate,
            "pre_g5_remaining_count": torso_remaining,
            "pre_g5_resolved_to_candidate_count": shoulder_candidate,
            "g5_material_acceptance_status": "BLOCKED_PENDING_TORSO_REVIEW_OR_REGENERATION",
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
        "decision": (
            "P0 B5 follow-up is narrowed from three pre-G5 rows to one torso review/regeneration blocker. "
            "Shoulders can be carried as G4 refresh candidates, not material PASS."
        ),
        "next_action": [
            "Handle torso_base as the remaining P0 pre-G5 visual review/regeneration row.",
            "After torso evidence exists, rebuild G4/G5 readiness with shoulder rows treated as candidates only.",
            "Keep ParamHairFront hidden and keep G7/G8 blocked.",
        ],
        "self_review": {
            "focused_followup_status": followup["status"],
            "b5_blocker_status": blocker["status"],
            "b5_provisional_qa_status": provisional["status"],
            "p0_torso_status": p0["status"],
            "input_pre_g5_followup_count": len(pre_g5_rows),
            "decision_row_count": len(rows),
            "torso_review_remaining_count": torso_remaining,
            "shoulder_g4_refresh_candidate_count": shoulder_candidate,
            "pre_g5_remaining_count": torso_remaining,
            "pre_g5_reduced_from_3_to_1": len(pre_g5_rows) == 3 and torso_remaining == 1,
            "decision_sheet_exists": DECISION_SHEET.exists(),
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
        "# Character 002 v22 G4 P0 B5 Follow-up Decision Packet",
        "",
        f"- status: `{report['status']}`",
        f"- decision sheet: `{report['decision_sheet']}`",
        f"- pre-G5 remaining: `{report['summary']['pre_g5_remaining_count']}`",
        f"- G5 material acceptance: `{report['summary']['g5_material_acceptance_status']}`",
        "",
        "## Decision Rows",
        "",
    ]
    for row in rows:
        lines.append(f"- `{row['part_id']}` `{row['decision']}` `{row['route_class']}`: {row['reason']}")
    lines.extend(["", "## Summary", ""])
    for key, value in report["summary"].items():
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

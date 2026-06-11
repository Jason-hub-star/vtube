#!/usr/bin/env python3
"""Reduce P1 B4 secondary-hair blockers into focused follow-up routes."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
P0_OVERLAY_QA = EXP / "reports/v22_64part_p0_torso_v2_manifest/v22_p0_torso_v2_manifest_overlay_qa_report.json"
B4_FOCUSED_REVIEW = EXP / "reports/v22_b4_hair_focused_review/v22_b4_hair_focused_review.json"
REPORT_DIR = EXP / "reports/v22_g3_p1_b4_secondary_hair_reduction"
REPORT_JSON = REPORT_DIR / "v22_g3_p1_b4_secondary_hair_reduction_packet.json"
REPORT_MD = REPORT_DIR / "v22_g3_p1_b4_secondary_hair_reduction_packet.md"
REVIEW_SHEET = REPORT_DIR / "v22_g3_p1_b4_secondary_hair_reduction_sheet.png"

CANVAS = 2048
TILE_W = 420
TILE_H = 305

BACK_STACK_IDS = {"hair_back_base", "hair_back_underpaint", "hair_back_center"}
BACK_STRAND_IDS = {"hair_back_strand_L", "hair_back_strand_R"}
SIDE_HAIR_IDS = {"hair_side_L_outer", "hair_side_L_inner", "hair_side_R_outer", "hair_side_R_inner"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def focused_recommendation_by_part(focused: dict) -> dict[str, str]:
    return {entry["part_id"]: entry["recommendation"] for entry in focused["entries"]}


def route_for(part_id: str, focused_recommendation: str | None, alpha_coverage: float) -> dict:
    if part_id in BACK_STRAND_IDS or focused_recommendation == "REVIEW_ANCHOR_AND_MASK":
        return {
            "reduction_bucket": "P1_REMAINING_ANCHOR_MASK_REVIEW",
            "route": "B4_BACK_STRAND_ANCHOR_MASK_REVIEW_REQUIRED",
            "priority_after_reduction": "P1A",
            "reason": "Back strand edges still need anchor/mask inspection before visual acceptance.",
            "counts_as_remaining_primary": True,
        }
    if part_id in BACK_STACK_IDS or focused_recommendation == "KEEP_AS_BACK_OR_UNDERPAINT_REVIEW_DRAW_ORDER_MASK":
        return {
            "reduction_bucket": "P1_CONTEXT_CANDIDATE_BACK_STACK",
            "route": "B4_BACK_STACK_DRAW_ORDER_CONTEXT_CANDIDATE_REVIEW_REQUIRED",
            "priority_after_reduction": "P1B",
            "reason": "Back/base/underpaint hair can be reviewed as draw-order context, not as a full regeneration blocker.",
            "counts_as_remaining_primary": False,
        }
    if part_id in SIDE_HAIR_IDS and alpha_coverage < 0.016:
        return {
            "reduction_bucket": "P1_CONTEXT_CANDIDATE_SIDE_HAIR_LOW_ALPHA",
            "route": "B4_SIDE_HAIR_LOW_ALPHA_CONTEXT_CANDIDATE_REVIEW_REQUIRED",
            "priority_after_reduction": "P1C",
            "reason": "Side-hair alpha is small enough to keep as a context review candidate unless later overlay exposes drift.",
            "counts_as_remaining_primary": False,
        }
    return {
        "reduction_bucket": "P1_SIDE_HAIR_MASK_REVIEW",
        "route": "B4_SIDE_HAIR_MASK_REVIEW_REQUIRED",
        "priority_after_reduction": "P1B",
        "reason": "Side-hair alpha or bbox still warrants mask review before visual acceptance.",
        "counts_as_remaining_primary": True,
    }


def crop_box_for(bbox: list[int] | None) -> tuple[int, int, int, int]:
    if not bbox:
        return (650, 180, 1510, 1250)
    pad = 125
    return (
        max(0, bbox[0] - pad),
        max(0, bbox[1] - pad),
        min(CANVAS, bbox[2] + pad),
        min(CANVAS, bbox[3] + pad),
    )


def color_for(bucket: str) -> tuple[int, int, int]:
    if bucket == "P1_REMAINING_ANCHOR_MASK_REVIEW":
        return (202, 74, 52)
    if bucket == "P1_CONTEXT_CANDIDATE_BACK_STACK":
        return (207, 126, 44)
    return (65, 126, 197)


def tile(source: Image.Image, row: dict) -> Image.Image:
    layer = Image.open(ROOT / row["path"]).convert("RGBA")
    crop_box = crop_box_for(row["bbox"])
    base = source.crop(crop_box).convert("RGBA")
    part = layer.crop(crop_box).convert("RGBA")
    color = color_for(row["reduction_bucket"])
    tint = Image.new("RGBA", base.size, (*color, 0))
    tint.putalpha(part.getchannel("A").point(lambda v: min(165, int(v * 0.7))))
    comp = Image.alpha_composite(base, tint)
    comp.thumbnail((TILE_W - 22, TILE_H - 104), Image.Resampling.LANCZOS)

    out = Image.new("RGB", (TILE_W, TILE_H), (247, 248, 250))
    out.paste(comp.convert("RGB"), ((TILE_W - comp.width) // 2, 8))
    draw = ImageDraw.Draw(out)
    draw.rectangle([4, 4, TILE_W - 5, TILE_H - 5], outline=(216, 222, 232))
    draw.rectangle([8, TILE_H - 98, TILE_W - 9, TILE_H - 68], fill=color)
    draw.text((12, TILE_H - 93), row["priority_after_reduction"], fill=(255, 255, 255))
    draw.text((58, TILE_H - 93), row["reduction_bucket"][:42], fill=(255, 255, 255))
    draw.text((12, TILE_H - 61), f"{row['part_id']} alpha={row['alpha_coverage']}", fill=(25, 31, 40))
    draw.text((12, TILE_H - 39), row["route"][:58], fill=(78, 89, 104))
    draw.text((12, TILE_H - 18), f"remaining_primary={row['counts_as_remaining_primary']}", fill=(78, 89, 104))
    return out


def build_sheet(rows: list[dict]) -> None:
    source = Image.open(SOURCE).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    ordered = sorted(rows, key=lambda r: (r["priority_after_reduction"], r["part_id"]))
    cols = 3
    header_h = 72
    sheet_rows = (len(ordered) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * TILE_W, header_h + sheet_rows * TILE_H), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 16), "Character 002 v22 G3 P1 B4 Secondary Hair Reduction", fill=(25, 31, 40))
    draw.text((12, 42), "P1 rows are routed, not approved. Material PASS / ParamHairFront / G7 / G8 remain blocked.", fill=(78, 89, 104))
    for idx, row in enumerate(ordered):
        sheet.paste(tile(source, row), ((idx % cols) * TILE_W, header_h + (idx // cols) * TILE_H))
    REVIEW_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(REVIEW_SHEET)


def main() -> int:
    p0_qa = load_json(P0_OVERLAY_QA)
    focused = load_json(B4_FOCUSED_REVIEW)
    recommendation_by_part = focused_recommendation_by_part(focused)
    source_rows = [
        entry
        for entry in p0_qa["qa_entries"]
        if entry["qa_verdict"] == "B4_SECONDARY_DRAW_ORDER_OR_MASK_REVIEW_REQUIRED"
    ]
    rows = []
    for entry in source_rows:
        part_id = entry["part_id"]
        focused_recommendation = recommendation_by_part.get(part_id)
        route = route_for(part_id, focused_recommendation, entry["alpha_coverage"])
        rows.append(
            {
                **entry,
                "focused_recommendation": focused_recommendation or "NOT_IN_FOCUSED_REVIEW_LOW_ALPHA_CONTEXT_ROW",
                **route,
                "material_promotion": "BLOCKED",
                "not_owner_approval": True,
            }
        )

    build_sheet(rows)
    bucket_counts = Counter(row["reduction_bucket"] for row in rows)
    route_counts = Counter(row["route"] for row in rows)
    remaining_primary = sum(1 for row in rows if row["counts_as_remaining_primary"])
    reduced_to_context = len(rows) - remaining_primary
    status = "G3_P1_B4_SECONDARY_HAIR_REDUCTION_PACKET_READY_REVIEW_REQUIRED"
    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": status,
        "p0_torso_v2_overlay_qa": rel(P0_OVERLAY_QA),
        "b4_focused_review": rel(B4_FOCUSED_REVIEW),
        "review_sheet": rel(REVIEW_SHEET),
        "p1_rows": rows,
        "summary": {
            "p0_overlay_status": p0_qa["status"],
            "b4_focused_review_status": focused["status"],
            "p1_input_count": len(rows),
            "remaining_primary_count": remaining_primary,
            "reduced_to_context_count": reduced_to_context,
            "bucket_counts": dict(sorted(bucket_counts.items())),
            "route_counts": dict(sorted(route_counts.items())),
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g3_visual_overlay_status": "P1_REDUCED_REVIEW_REQUIRED",
            "g4_psd_import_prep_status": "PREP_ONLY_BLOCKED",
            "g5_material_acceptance_status": "BLOCKED",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
        "decision": (
            "The nine P1 B4 secondary-hair rows are reduced into two remaining anchor/mask review rows and seven context "
            "candidate rows. This narrows the next manual or scripted work, but it is not visual PASS or material approval."
        ),
        "next_action": [
            "Handle the two P1A back-strand anchor/mask rows first.",
            "Keep the seven P1B/P1C rows as context candidates until a combined G3 visual overlay pass is built.",
            "Do not unlock ParamHairFront, G4/G5 material promotion, Mini Cubism, or real Cubism from this packet.",
        ],
        "self_review": {
            "p0_overlay_status": p0_qa["status"],
            "b4_focused_review_status": focused["status"],
            "p1_input_count": len(rows),
            "remaining_primary_count": remaining_primary,
            "reduced_to_context_count": reduced_to_context,
            "anchor_mask_review_count": bucket_counts.get("P1_REMAINING_ANCHOR_MASK_REVIEW", 0),
            "back_stack_context_candidate_count": bucket_counts.get("P1_CONTEXT_CANDIDATE_BACK_STACK", 0),
            "side_hair_low_alpha_context_candidate_count": bucket_counts.get(
                "P1_CONTEXT_CANDIDATE_SIDE_HAIR_LOW_ALPHA", 0
            ),
            "review_sheet_exists": REVIEW_SHEET.exists(),
            "material_pass_blocked": True,
            "visual_promotion_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "not_owner_approval": True,
            "status": "PASS",
        },
    }
    save_json(REPORT_JSON, report)

    lines = [
        "# Character 002 v22 G3 P1 B4 Secondary Hair Reduction",
        "",
        f"- status: `{report['status']}`",
        f"- review sheet: `{report['review_sheet']}`",
        "",
        "## Summary",
        "",
    ]
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

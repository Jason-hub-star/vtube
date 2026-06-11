#!/usr/bin/env python3
"""Build a combined G3 context overlay after P0/P1A blocker reduction."""

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
P1_REDUCTION = EXP / "reports/v22_g3_p1_b4_secondary_hair_reduction/v22_g3_p1_b4_secondary_hair_reduction_packet.json"
P1A_PROBE = EXP / "reports/v22_g3_p1a_b4_back_strand_anchor_mask_probe/v22_g3_p1a_b4_back_strand_anchor_mask_probe_report.json"
REPORT_DIR = EXP / "reports/v22_g3_combined_context_overlay_review"
REPORT_JSON = REPORT_DIR / "v22_g3_combined_context_overlay_review_report.json"
REPORT_MD = REPORT_DIR / "v22_g3_combined_context_overlay_review_report.md"
OVERLAY_SHEET = REPORT_DIR / "v22_g3_combined_context_overlay_review.png"

CANVAS = 2048
TILE_W = 380
TILE_H = 326
FACE_MICRO_PARTS = {"face_shadow_L", "face_shadow_R", "nose", "cheek_L", "cheek_R", "brow_L", "brow_R"}


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
    pad = 115
    return (
        max(0, bbox[0] - pad),
        max(0, bbox[1] - pad),
        min(CANVAS, bbox[2] + pad),
        min(CANVAS, bbox[3] + pad),
    )


def p1_route_by_part(p1: dict) -> dict[str, dict]:
    return {row["part_id"]: row for row in p1["p1_rows"]}


def p1a_entry_by_part(p1a: dict) -> dict[str, dict]:
    return {row["part_id"]: row for row in p1a["entries"]}


def classify(entry: dict, p1_routes: dict[str, dict], p1a_entries: dict[str, dict]) -> tuple[str, str, str]:
    part_id = entry["part_id"]
    verdict = entry["qa_verdict"]
    if verdict == "B4_FRONT_HAIR_MOTION_CANDIDATE_REVIEW_REQUIRED":
        return (
            "G3_CONTEXT_FRONT_HAIR_MOTION_CANDIDATE_KEEP_HAIRFRONT_HIDDEN",
            "CONTEXT_REVIEW",
            "Front-hair child candidate can stay for motion-readiness review, but ParamHairFront remains hidden.",
        )
    if verdict == "B4_SECONDARY_DRAW_ORDER_OR_MASK_REVIEW_REQUIRED":
        if part_id in p1a_entries and p1a_entries[part_id]["probe_verdict"] == (
            "P1A_BACK_STRAND_ANCHOR_MASK_NUMERIC_PASS_CONTEXT_REVIEW_REQUIRED"
        ):
            return (
                "G3_CONTEXT_BACK_STRAND_NUMERIC_PASS_REVIEW_REQUIRED",
                "CONTEXT_REVIEW",
                "Back-strand anchor/mask numeric probe passed; keep as context review, not visual PASS.",
            )
        route = p1_routes.get(part_id, {})
        if route.get("route") == "B4_BACK_STACK_DRAW_ORDER_CONTEXT_CANDIDATE_REVIEW_REQUIRED":
            return (
                "G3_CONTEXT_BACK_STACK_DRAW_ORDER_REVIEW_REQUIRED",
                "CONTEXT_REVIEW",
                "Back/base/underpaint hair is a draw-order context candidate.",
            )
        if route.get("route") == "B4_SIDE_HAIR_LOW_ALPHA_CONTEXT_CANDIDATE_REVIEW_REQUIRED":
            return (
                "G3_CONTEXT_SIDE_HAIR_LOW_ALPHA_REVIEW_REQUIRED",
                "CONTEXT_REVIEW",
                "Side hair has low alpha footprint and is held as context review.",
            )
        return (
            "G3_PRIMARY_B4_SECONDARY_HAIR_REVIEW_REMAINING",
            "PRIMARY_REVIEW",
            "B4 secondary hair still lacks reduction evidence.",
        )
    if verdict == "B5_TORSO_P0_V2_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED":
        return (
            "G3_CONTEXT_TORSO_P0_V2_REVIEW_REQUIRED",
            "CONTEXT_REVIEW",
            "P0 torso v2 is an improvement candidate, still visual-review required.",
        )
    if verdict == "B5_SHOULDER_DRAW_ORDER_MASK_IMPROVEMENT_REVIEW_REQUIRED":
        return (
            "G3_CONTEXT_SHOULDER_IMPROVEMENT_REVIEW_REQUIRED",
            "CONTEXT_REVIEW",
            "Shoulder draw-order/mask candidate improved, still needs context review.",
        )
    if verdict == "B5_COPIED_LAYER_REVIEW_REQUIRED":
        if part_id in FACE_MICRO_PARTS:
            return (
                "G3_CONTEXT_B5_FACE_MICRO_DETAIL_REVIEW_REQUIRED",
                "CONTEXT_REVIEW",
                "Copied B5 face micro detail needs context review, not primary blocker treatment.",
            )
        return (
            "G3_CONTEXT_B5_BODY_CLOTHING_STACK_REVIEW_REQUIRED",
            "CONTEXT_REVIEW",
            "Copied B5 body/clothing stack needs context review before material acceptance.",
        )
    return ("G3_UNKNOWN_REVIEW_REQUIRED", "PRIMARY_REVIEW", "Unclassified QA row remains review-required.")


def color_for(classification: str) -> tuple[int, int, int]:
    if "PRIMARY" in classification:
        return (202, 74, 52)
    if "FRONT_HAIR" in classification:
        return (126, 87, 194)
    if "B5" in classification or "TORSO" in classification or "SHOULDER" in classification:
        return (42, 152, 95)
    return (65, 126, 197)


def tile(source: Image.Image, row: dict) -> Image.Image:
    layer = Image.open(ROOT / row["path"]).convert("RGBA")
    crop_box = crop_box_for(row["bbox"])
    base = source.crop(crop_box).convert("RGBA")
    part = layer.crop(crop_box).convert("RGBA")
    color = color_for(row["g3_classification"])
    tint = Image.new("RGBA", base.size, (*color, 0))
    tint.putalpha(part.getchannel("A").point(lambda v: min(155, int(v * 0.68))))
    comp = Image.alpha_composite(base, tint)
    comp.thumbnail((TILE_W - 20, TILE_H - 84), Image.Resampling.LANCZOS)

    out = Image.new("RGB", (TILE_W, TILE_H), (247, 248, 250))
    out.paste(comp.convert("RGB"), ((TILE_W - comp.width) // 2, 8))
    draw = ImageDraw.Draw(out)
    draw.rectangle([4, 4, TILE_W - 5, TILE_H - 5], outline=(216, 222, 232))
    draw.rectangle([8, TILE_H - 78, TILE_W - 9, TILE_H - 54], fill=color)
    draw.text((12, TILE_H - 74), row["review_class"], fill=(255, 255, 255))
    draw.text((12, TILE_H - 48), f"{row['part_id']} {row['source_batch']}", fill=(25, 31, 40))
    draw.text((12, TILE_H - 27), row["g3_classification"][:54], fill=(78, 89, 104))
    return out


def build_sheet(rows: list[dict]) -> None:
    source = Image.open(SOURCE).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    ordered = sorted(rows, key=lambda row: (row["review_class"], row["source_batch"], row["part_id"]))
    cols = 3
    header_h = 70
    sheet_rows = (len(ordered) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * TILE_W, header_h + sheet_rows * TILE_H), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 16), "Character 002 v22 G3 Combined Context Overlay Review", fill=(25, 31, 40))
    draw.text((12, 42), "Primary blockers reduced; context review required before material PASS", fill=(78, 89, 104))
    for idx, row in enumerate(ordered):
        sheet.paste(tile(source, row), ((idx % cols) * TILE_W, header_h + (idx // cols) * TILE_H))
    OVERLAY_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OVERLAY_SHEET)


def main() -> int:
    p0 = load_json(P0_OVERLAY_QA)
    p1 = load_json(P1_REDUCTION)
    p1a = load_json(P1A_PROBE)
    p1_routes = p1_route_by_part(p1)
    p1a_entries = p1a_entry_by_part(p1a)

    rows = []
    for entry in p0["qa_entries"]:
        classification, review_class, reason = classify(entry, p1_routes, p1a_entries)
        row = {
            **entry,
            "g3_classification": classification,
            "review_class": review_class,
            "classification_reason": reason,
            "material_promotion": "BLOCKED",
            "not_owner_approval": True,
        }
        if entry["part_id"] in p1a_entries:
            row["p1a_probe_verdict"] = p1a_entries[entry["part_id"]]["probe_verdict"]
            row["path"] = p1a_entries[entry["part_id"]]["output_path"]
        rows.append(row)

    build_sheet(rows)
    class_counts = Counter(row["g3_classification"] for row in rows)
    review_counts = Counter(row["review_class"] for row in rows)
    primary_remaining = review_counts.get("PRIMARY_REVIEW", 0)
    status = (
        "G3_COMBINED_CONTEXT_OVERLAY_REVIEW_READY_MATERIAL_BLOCKED"
        if primary_remaining == 0
        else "G3_COMBINED_CONTEXT_OVERLAY_HAS_PRIMARY_REVIEW_REMAINING"
    )
    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": status,
        "p0_torso_v2_overlay_qa": rel(P0_OVERLAY_QA),
        "p1_b4_secondary_hair_reduction": rel(P1_REDUCTION),
        "p1a_back_strand_probe": rel(P1A_PROBE),
        "overlay_sheet": rel(OVERLAY_SHEET),
        "review_rows": rows,
        "summary": {
            "qa_entry_count": len(rows),
            "primary_remaining_count": primary_remaining,
            "context_review_count": review_counts.get("CONTEXT_REVIEW", 0),
            "classification_counts": dict(sorted(class_counts.items())),
            "review_class_counts": dict(sorted(review_counts.items())),
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g3_visual_overlay_status": "COMBINED_CONTEXT_REVIEW_REQUIRED_NOT_PASS",
            "g4_psd_import_prep_status": "PREP_ONLY_BLOCKED",
            "g5_material_acceptance_status": "BLOCKED",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
        "decision": (
            "P0 and P1A reductions leave no primary B4/B5 blocker rows in this combined review sheet, but all rows remain "
            "context-review evidence. This is not material PASS and does not unlock ParamHairFront, Mini Cubism, or real Cubism."
            if primary_remaining == 0
            else "Some primary review rows remain and must be handled before G3 context review can be compacted."
        ),
        "next_action": [
            "Use this combined overlay as the G3 context-review surface before any G4/G5 material promotion attempt.",
            "Keep ParamHairFront hidden until real independent front hair child art passes motion-readiness review.",
            "Do not promote Mini Cubism or real Cubism from this context overlay.",
        ],
        "self_review": {
            "p0_overlay_status": p0["status"],
            "p1_reduction_status": p1["status"],
            "p1a_probe_status": p1a["status"],
            "qa_entry_count": len(rows),
            "primary_remaining_count": primary_remaining,
            "context_review_count": review_counts.get("CONTEXT_REVIEW", 0),
            "overlay_sheet_exists": OVERLAY_SHEET.exists(),
            "material_pass_blocked": True,
            "visual_promotion_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "not_owner_approval": True,
            "status": "PASS" if primary_remaining == 0 else "REVISE",
        },
    }
    save_json(REPORT_JSON, report)

    lines = [
        "# Character 002 v22 G3 Combined Context Overlay Review",
        "",
        f"- status: `{report['status']}`",
        f"- overlay sheet: `{report['overlay_sheet']}`",
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
    return 0 if primary_remaining == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

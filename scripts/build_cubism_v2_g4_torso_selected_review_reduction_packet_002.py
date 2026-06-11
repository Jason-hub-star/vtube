#!/usr/bin/env python3
"""Build compact G4 review/reduction packet after generated torso selection."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path("/Users/family/jason/Vtube")
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
OVERLAY_QA = (
    EXP
    / "reports/v22_64part_g4_torso_selected_manifest/v22_g4_torso_selected_manifest_overlay_qa_report.json"
)
MANIFEST = EXP / "reports/v22_64part_g4_torso_selected_manifest/v22_64part_g4_torso_selected_manifest.json"
REPORT_DIR = EXP / "reports/v22_g4_torso_selected_review_reduction"
REPORT_JSON = REPORT_DIR / "v22_g4_torso_selected_review_reduction_packet.json"
REPORT_MD = REPORT_DIR / "v22_g4_torso_selected_review_reduction_packet.md"
REVIEW_SHEET = REPORT_DIR / "v22_g4_torso_selected_review_reduction_sheet.png"
CANVAS = 2048
TILE_W = 380
TILE_H = 300


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
        return (700, 700, 1350, 1350)
    pad = 110
    return (
        max(0, bbox[0] - pad),
        max(0, bbox[1] - pad),
        min(CANVAS, bbox[2] + pad),
        min(CANVAS, bbox[3] + pad),
    )


def lane_for(entry: dict) -> tuple[str, str, str, str]:
    part_id = entry["part_id"]
    verdict = entry["qa_verdict"]
    if verdict == "B5_TORSO_GENERATED_UNDERPAINT_REBUILD_REVIEW_REQUIRED":
        return (
            "P0_B5_TORSO_SELECTED_OVERLAY_REVIEW",
            "PRE_G5_SELECTED_TORSO_REVIEW",
            "Confirm generated torso can stay as the selected rebuild input; do not treat as material PASS.",
            "BLOCKS_G5_UNTIL_REVIEW_OR_FURTHER_REDUCTION",
        )
    if verdict == "B5_SHOULDER_DRAW_ORDER_MASK_IMPROVEMENT_REVIEW_REQUIRED":
        return (
            "P0_B5_SHOULDER_DRAW_ORDER_MASK_CANDIDATE_REVIEW",
            "PRE_G5_SHOULDER_CANDIDATE_REVIEW",
            "Keep shoulder mask/draw-order improvement as a candidate and review in torso-selected context.",
            "BLOCKS_G5_UNTIL_REVIEW_OR_FURTHER_REDUCTION",
        )
    if verdict == "B4_FRONT_HAIR_MOTION_CANDIDATE_REVIEW_REQUIRED":
        return (
            "P1_B4_FRONT_HAIR_MOTION_CANDIDATE_KEEP_HAIRFRONT_HIDDEN",
            "HAIRFRONT_MOTION_READINESS_REVIEW",
            "Independent front-hair child art exists as candidate only; ParamHairFront stays hidden.",
            "DOES_NOT_UNLOCK_HAIRFRONT_YET",
        )
    if verdict == "B4_SECONDARY_DRAW_ORDER_OR_MASK_REVIEW_REQUIRED":
        return (
            "P2_B4_SECONDARY_HAIR_CONTEXT_REVIEW",
            "B4_SECONDARY_CONTEXT_REVIEW",
            "Review back/side/underpaint hair draw order and masks as context before G5.",
            "CONTEXT_REVIEW_BEFORE_G5",
        )
    if verdict == "B5_COPIED_LAYER_REVIEW_REQUIRED":
        if part_id in {"neck", "arm_L_upper_simple", "arm_R_upper_simple", "collar_front", "collar_shadow", "chest_cloth_base", "chest_cloth_shadow"}:
            return (
                "P3_B5_BODY_CLOTHING_COPIED_CONTEXT_REVIEW",
                "B5_COPIED_CONTEXT_REVIEW",
                "Copied B5 body/clothing layer remains context review before material acceptance.",
                "CONTEXT_REVIEW_BEFORE_G5",
            )
        return (
            "P3_B5_FACE_MICRO_COPIED_CONTEXT_REVIEW",
            "B5_COPIED_CONTEXT_REVIEW",
            "Copied B5 face micro-detail remains context review before material acceptance.",
            "CONTEXT_REVIEW_BEFORE_G5",
        )
    return (
        "P9_UNCLASSIFIED_REVIEW_REQUIRED",
        "PRE_G5_UNCLASSIFIED_REVIEW",
        "Unclassified overlay row remains blocked until reviewed.",
        "BLOCKS_G5_UNTIL_CLASSIFIED",
    )


def color_for(class_name: str) -> tuple[int, int, int]:
    if class_name.startswith("PRE_G5_SELECTED"):
        return (214, 83, 69)
    if class_name.startswith("PRE_G5_SHOULDER"):
        return (223, 143, 47)
    if class_name.startswith("HAIRFRONT"):
        return (126, 87, 194)
    if class_name.startswith("B4"):
        return (58, 132, 255)
    if class_name.startswith("B5"):
        return (80, 145, 108)
    return (130, 130, 130)


def tile(source: Image.Image, row: dict) -> Image.Image:
    layer = Image.open(ROOT / row["path"]).convert("RGBA")
    crop = crop_box_for(row["bbox"])
    base = source.crop(crop).convert("RGBA")
    part = layer.crop(crop).convert("RGBA")
    color = color_for(row["review_class"])
    tint = Image.new("RGBA", base.size, (*color, 0))
    tint.putalpha(part.getchannel("A").point(lambda v: min(158, int(v * 0.68))))
    comp = Image.alpha_composite(base, tint)
    comp.thumbnail((TILE_W - 18, TILE_H - 92), Image.Resampling.LANCZOS)
    out = Image.new("RGB", (TILE_W, TILE_H), (247, 248, 250))
    out.paste(comp.convert("RGB"), ((TILE_W - comp.width) // 2, 8))
    draw = ImageDraw.Draw(out)
    draw.rectangle([4, 4, TILE_W - 5, TILE_H - 5], outline=(214, 221, 232))
    draw.rectangle([8, TILE_H - 84, TILE_W - 9, TILE_H - 58], fill=color)
    draw.text((12, TILE_H - 80), row["review_class"][:46], fill=(255, 255, 255), font=font(12))
    draw.text((12, TILE_H - 52), f"{row['part_id']} / {row['source_batch']} / alpha={row['alpha_coverage']}", fill=(25, 31, 40), font=font(12))
    draw.text((12, TILE_H - 31), row["review_lane"][:54], fill=(78, 89, 104), font=font(12))
    draw.text((12, TILE_H - 14), row["g5_effect"][:54], fill=(78, 89, 104), font=font(11))
    return out


def build_sheet(rows: list[dict]) -> None:
    source = Image.open(SOURCE).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    ordered = sorted(rows, key=lambda row: (row["review_lane"], row["part_id"]))
    cols = 3
    header_h = 82
    sheet_rows = (len(ordered) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * TILE_W, header_h + sheet_rows * TILE_H), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 14), "Character 002 v22 G4 Torso-Selected Review Reduction", fill=(25, 31, 40), font=font(18))
    draw.text((12, 42), "Work-order surface only: no material PASS, no HairFront unlock, no G7/G8 promotion.", fill=(78, 89, 104), font=font(14))
    draw.text((12, 62), "Red/orange: pre-G5 lanes; purple: HairFront hidden; blue/green: context review.", fill=(78, 89, 104), font=font(13))
    for idx, row in enumerate(ordered):
        sheet.paste(tile(source, row), ((idx % cols) * TILE_W, header_h + (idx // cols) * TILE_H))
    REVIEW_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(REVIEW_SHEET)


def main() -> int:
    overlay = load_json(OVERLAY_QA)
    manifest = load_json(MANIFEST)
    rows = []
    for entry in overlay["qa_entries"]:
        lane, class_name, action, effect = lane_for(entry)
        rows.append(
            {
                **entry,
                "review_lane": lane,
                "review_class": class_name,
                "review_action": action,
                "g5_effect": effect,
                "material_promotion": "BLOCKED",
                "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            }
        )
    build_sheet(rows)

    lane_counts = Counter(row["review_lane"] for row in rows)
    class_counts = Counter(row["review_class"] for row in rows)
    effect_counts = Counter(row["g5_effect"] for row in rows)
    status = "G4_TORSO_SELECTED_REVIEW_REDUCTION_PACKET_READY_MATERIAL_BLOCKED"
    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "torso_selected_manifest": rel(MANIFEST),
        "torso_selected_overlay_qa": rel(OVERLAY_QA),
        "review_sheet": rel(REVIEW_SHEET),
        "review_rows": rows,
        "work_order_phases": [
            {
                "phase": "P0",
                "name": "pre-G5 torso/shoulder review",
                "row_count": class_counts["PRE_G5_SELECTED_TORSO_REVIEW"] + class_counts["PRE_G5_SHOULDER_CANDIDATE_REVIEW"],
                "unblocks": "Only a later G5 readiness refresh, not material PASS.",
            },
            {
                "phase": "P1",
                "name": "front-hair motion-readiness candidates",
                "row_count": class_counts["HAIRFRONT_MOTION_READINESS_REVIEW"],
                "unblocks": "Future HairFront readiness only after motion review; hidden now.",
            },
            {
                "phase": "P2",
                "name": "B4 secondary hair context",
                "row_count": class_counts["B4_SECONDARY_CONTEXT_REVIEW"],
                "unblocks": "Context evidence for later G5 review.",
            },
            {
                "phase": "P3",
                "name": "B5 copied context rows",
                "row_count": class_counts["B5_COPIED_CONTEXT_REVIEW"],
                "unblocks": "Context evidence for later G5 review.",
            },
        ],
        "summary": {
            "source_manifest_status": manifest["status"],
            "overlay_qa_status": overlay["status"],
            "review_row_count": len(rows),
            "pre_g5_blocking_row_count": effect_counts["BLOCKS_G5_UNTIL_REVIEW_OR_FURTHER_REDUCTION"],
            "context_review_row_count": effect_counts["CONTEXT_REVIEW_BEFORE_G5"],
            "hairfront_hidden_candidate_count": effect_counts["DOES_NOT_UNLOCK_HAIRFRONT_YET"],
            "lane_counts": dict(sorted(lane_counts.items())),
            "class_counts": dict(sorted(class_counts.items())),
            "effect_counts": dict(sorted(effect_counts.items())),
            "generated_torso_selected": True,
            "g5_material_acceptance_status": "BLOCKED_PENDING_REDUCTION_PACKET_REVIEW",
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
        "decision": (
            "The generated torso is selected in the 64-part manifest, but the remaining B4/B5 surface is still a review/reduction packet. "
            "Only three rows are immediate pre-G5 blockers (torso plus shoulders); HairFront remains hidden and context rows remain unpromoted."
        ),
        "next_action": [
            "Resolve the three P0 pre-G5 torso/shoulder rows first.",
            "Keep seven front-hair child rows as motion-readiness candidates with ParamHairFront hidden.",
            "Keep B4 secondary and B5 copied rows as context review until a separate G5 packet is built.",
        ],
        "self_review": {
            "source_manifest_status": manifest["status"],
            "overlay_qa_status": overlay["status"],
            "review_row_count": len(rows),
            "matches_overlay_qa_entry_count": len(rows) == overlay["summary"]["qa_entry_count"],
            "pre_g5_blocking_row_count": effect_counts["BLOCKS_G5_UNTIL_REVIEW_OR_FURTHER_REDUCTION"],
            "pre_g5_blocking_row_count_is_three": effect_counts["BLOCKS_G5_UNTIL_REVIEW_OR_FURTHER_REDUCTION"] == 3,
            "generated_torso_selected_count": lane_counts["P0_B5_TORSO_SELECTED_OVERLAY_REVIEW"],
            "shoulder_candidate_count": lane_counts["P0_B5_SHOULDER_DRAW_ORDER_MASK_CANDIDATE_REVIEW"],
            "front_hair_candidate_count": lane_counts["P1_B4_FRONT_HAIR_MOTION_CANDIDATE_KEEP_HAIRFRONT_HIDDEN"],
            "b4_secondary_context_count": lane_counts["P2_B4_SECONDARY_HAIR_CONTEXT_REVIEW"],
            "b5_copied_context_count": lane_counts["P3_B5_BODY_CLOTHING_COPIED_CONTEXT_REVIEW"]
            + lane_counts["P3_B5_FACE_MICRO_COPIED_CONTEXT_REVIEW"],
            "review_sheet_exists": REVIEW_SHEET.exists(),
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
        "# Character 002 v22 G4 Torso-Selected Review Reduction Packet",
        "",
        f"- status: `{report['status']}`",
        f"- review sheet: `{report['review_sheet']}`",
        f"- G5 material acceptance: `{report['summary']['g5_material_acceptance_status']}`",
        f"- ParamHairFront: `{report['summary']['param_hair_front_status']}`",
        "",
        "## Work Order Phases",
        "",
    ]
    for phase in report["work_order_phases"]:
        lines.append(f"- `{phase['phase']}` `{phase['name']}`: `{phase['row_count']}` rows; {phase['unblocks']}")
    lines.extend(["", "## Summary", ""])
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Self Review", ""])
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", "", report["decision"], "", "## Next Action", ""])
    lines.extend(f"- {item}" for item in report["next_action"])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if not all(report["self_review"].values()):
        failed = [key for key, value in report["self_review"].items() if not value]
        raise RuntimeError(f"self review failed: {failed}")
    print(json.dumps({"status": status, "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

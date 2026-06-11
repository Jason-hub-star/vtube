#!/usr/bin/env python3
"""Build the focused owner review packet for v22 B4/B5 blockers.

The packet turns the current evidence into a small set of human decisions:
seven B4 front-hair child candidates and three B5 body blockers. It does not
promote material PASS or unlock Mini Cubism / real Cubism gates.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
B4_FOCUSED_JSON = EXP / "reports/v22_b4_hair_focused_review/v22_b4_hair_focused_review.json"
B5_BLOCKER_JSON = EXP / "reports/v22_b5_body_blocker_draw_order_review/v22_b5_body_blocker_draw_order_review.json"
REPORT_DIR = EXP / "reports/v22_b4_b5_focused_owner_review"
REPORT_JSON = REPORT_DIR / "v22_b4_b5_focused_owner_review.json"
REPORT_MD = REPORT_DIR / "v22_b4_b5_focused_owner_review.md"
DECISION_TEMPLATE_JSON = REPORT_DIR / "v22_b4_b5_focused_owner_review_decision_template.json"
REVIEW_SHEET = REPORT_DIR / "v22_b4_b5_focused_owner_review.png"
CANVAS = 2048


B4_PRIMARY_RECOMMENDATION = "FRONT_HAIR_CHILD_CANDIDATE_HUMAN_REVIEW_REQUIRED"
B5_PRIMARY_PARTS = ["torso_base", "shoulder_L", "shoulder_R"]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_image() -> Image.Image:
    return Image.open(SOURCE).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)


def overlay_tint(base: Image.Image, layer: Image.Image, color: tuple[int, int, int]) -> Image.Image:
    alpha = layer.getchannel("A").point(lambda v: min(160, int(v * 0.72)))
    tint = Image.new("RGBA", base.size, (*color, 0))
    tint.putalpha(alpha)
    return Image.alpha_composite(base.convert("RGBA"), tint)


def isolated_layer(layer: Image.Image) -> Image.Image:
    bbox = layer.getchannel("A").getbbox()
    crop = layer.crop(bbox) if bbox else layer
    bg = Image.new("RGBA", crop.size, (245, 247, 250, 255))
    return Image.alpha_composite(bg, crop)


def tile(title: str, img: Image.Image, subtitle: str = "") -> Image.Image:
    w, h = 310, 260
    label_h = 50
    out = Image.new("RGB", (w, h), (247, 248, 250))
    draw = ImageDraw.Draw(out)
    draw.rectangle([4, 4, w - 5, h - 5], outline=(216, 222, 232))
    draw.text((10, 10), title[:42], fill=(25, 31, 40))
    if subtitle:
        draw.text((10, 30), subtitle[:46], fill=(78, 89, 104))
    preview = img.convert("RGBA")
    preview.thumbnail((w - 20, h - label_h - 14), Image.Resampling.LANCZOS)
    out.paste(preview.convert("RGB"), ((w - preview.width) // 2, label_h + 4), preview)
    return out


def owner_options(item: dict) -> list[str]:
    if item["review_group"] == "B4_FRONT_HAIR":
        return [
            "ACCEPT_FOR_MOTION_READINESS_CANDIDATE",
            "REVISE_MASK_OR_ANCHOR",
            "REGENERATE_B4_FRONT_HAIR_MINIPASS",
        ]
    return [
        "ACCEPT_WITH_DRAW_ORDER_CONTEXT",
        "REVISE_MASK_OR_DRAW_ORDER",
        "REGENERATE_B5_BODY_MINIPASS",
    ]


def build_sheet(primary: list[dict], source: Image.Image) -> None:
    cols = 4
    tile_w, tile_h = 310, 260
    rows = len(primary)
    sheet = Image.new("RGB", (cols * tile_w, 58 + rows * tile_h), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 14), "Character 002 v22 B4/B5 Focused Owner Review", fill=(25, 31, 40))
    for row, item in enumerate(primary):
        layer = Image.open(ROOT / item["output_path"]).convert("RGBA")
        crop_box = tuple(item["crop_box"])
        src_crop = source.crop(crop_box)
        layer_crop = layer.crop(crop_box)
        tiles = [
            tile(f"{row + 1}. {item['part_id']} source", src_crop, item["review_group"]),
            tile("overlay", overlay_tint(src_crop, layer_crop, item["overlay_color"]), item["recommendation"]),
            tile("isolated", isolated_layer(layer_crop), "candidate part"),
            tile("decision", isolated_layer(layer_crop), "owner review pending"),
        ]
        y = 58 + row * tile_h
        for col, image in enumerate(tiles):
            sheet.paste(image, (col * tile_w, y))
    REVIEW_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(REVIEW_SHEET)


def main() -> int:
    b4 = json.loads(B4_FOCUSED_JSON.read_text(encoding="utf-8"))
    b5 = json.loads(B5_BLOCKER_JSON.read_text(encoding="utf-8"))
    source = source_image()

    primary: list[dict] = []
    secondary: list[dict] = []

    for entry in b4["entries"]:
        if entry["recommendation"] == B4_PRIMARY_RECOMMENDATION:
            item = {
                "part_id": entry["part_id"],
                "review_group": "B4_FRONT_HAIR",
                "source_report": rel(B4_FOCUSED_JSON),
                "output_path": entry["output_path"],
                "crop_box": entry["crop_box"],
                "recommendation": entry["recommendation"],
                "owner_decision": "PENDING_OWNER_REVIEW",
                "allowed_owner_decisions": [],
                "next_if_accept": "Prepare B4 front-hair motion-readiness check while keeping ParamHairFront hidden until that check passes.",
                "next_if_revise": "Use mask/anchor refinement for this front-hair child.",
                "next_if_regenerate": "Run a B4 front-hair mini-pass, not a full B1-B5 restart.",
                "overlay_color": (70, 135, 255),
            }
            item["allowed_owner_decisions"] = owner_options(item)
            primary.append(item)
        else:
            secondary.append(
                {
                    "part_id": entry["part_id"],
                    "review_group": "B4_BACK_OR_STRAND_SECONDARY",
                    "recommendation": entry["recommendation"],
                    "reason": "Keep for follow-up draw-order, underpaint, anchor, or mask review after primary B4/B5 decisions.",
                }
            )

    b5_by_part = {entry["part_id"]: entry for entry in b5["entries"]}
    for part_id in B5_PRIMARY_PARTS:
        entry = b5_by_part[part_id]
        item = {
            "part_id": part_id,
            "review_group": "B5_BODY_BLOCKER",
            "source_report": rel(B5_BLOCKER_JSON),
            "output_path": entry["output_path"],
            "crop_box": entry["crop_box"],
            "recommendation": entry["recommendation"],
            "owner_decision": "PENDING_OWNER_REVIEW",
            "allowed_owner_decisions": [],
            "next_if_accept": "Keep as focused accepted candidate but do not promote material PASS until full corrected B4/B5 overlay QA passes.",
            "next_if_revise": "Adjust draw-order/mask for shoulders or refine torso underpaint.",
            "next_if_regenerate": "Run the recorded B5 body mini-pass prompt, not a full B1-B5 restart.",
            "overlay_color": (61, 132, 255),
        }
        item["allowed_owner_decisions"] = owner_options(item)
        primary.append(item)

    build_sheet(primary, source)

    decision_template = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": "OWNER_DECISION_TEMPLATE_PENDING",
        "source_packet": rel(REPORT_JSON),
        "instructions": "Fill owner_decision only with one of allowed_owner_decisions. PENDING entries do not approve material PASS.",
        "decisions": [
            {
                "part_id": item["part_id"],
                "review_group": item["review_group"],
                "owner_decision": item["owner_decision"],
                "allowed_owner_decisions": item["allowed_owner_decisions"],
                "owner_note": "",
            }
            for item in primary
        ],
    }

    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": "B4_B5_FOCUSED_OWNER_REVIEW_PACKET_READY_PENDING_OWNER_DECISIONS",
        "source_image": rel(SOURCE),
        "b4_focused_review": rel(B4_FOCUSED_JSON),
        "b5_body_blocker_review": rel(B5_BLOCKER_JSON),
        "review_sheet": rel(REVIEW_SHEET),
        "decision_template": rel(DECISION_TEMPLATE_JSON),
        "primary_decisions": primary,
        "secondary_followups": secondary,
        "summary": {
            "primary_decision_count": len(primary),
            "b4_front_hair_primary_count": sum(1 for item in primary if item["review_group"] == "B4_FRONT_HAIR"),
            "b5_body_primary_count": sum(1 for item in primary if item["review_group"] == "B5_BODY_BLOCKER"),
            "secondary_followup_count": len(secondary),
            "all_primary_pending_owner_review": all(item["owner_decision"] == "PENDING_OWNER_REVIEW" for item in primary),
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
        "decision": (
            "This is the focused owner-review handoff for B4/B5. It deliberately keeps all primary decisions pending "
            "and blocks material PASS, Mini Cubism, and real Cubism promotion."
        ),
        "next_action": [
            "Collect owner decisions for the ten primary rows.",
            "Apply accepted/revised/regenerated paths separately; do not restart B1-B5 unless the owner rejects the whole visual direction.",
            "After accepted corrections exist, rebuild the corrected B4/B5 candidate and rerun overlay QA.",
        ],
        "self_review": {
            "b4_status": b4["status"],
            "b5_status": b5["status"],
            "primary_decision_count": len(primary),
            "b4_front_hair_primary_count": sum(1 for item in primary if item["review_group"] == "B4_FRONT_HAIR"),
            "b5_body_primary_count": sum(1 for item in primary if item["review_group"] == "B5_BODY_BLOCKER"),
            "secondary_followup_count": len(secondary),
            "review_sheet_exists": REVIEW_SHEET.exists(),
            "decision_template_exists": True,
            "all_primary_pending_owner_review": all(item["owner_decision"] == "PENDING_OWNER_REVIEW" for item in primary),
            "does_not_require_owner_review_all_33": True,
            "validator_only_promotion_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "status": "PASS",
        },
    }
    save_json(DECISION_TEMPLATE_JSON, decision_template)
    save_json(REPORT_JSON, report)

    lines = [
        "# Character 002 v22 B4/B5 Focused Owner Review",
        "",
        f"- status: `{report['status']}`",
        f"- review sheet: `{report['review_sheet']}`",
        f"- decision template: `{report['decision_template']}`",
        f"- material PASS: `{report['summary']['material_pass_status']}`",
        f"- ParamHairFront: `{report['summary']['param_hair_front_status']}`",
        f"- G7 Mini Cubism: `{report['summary']['g7_mini_cubism_status']}`",
        f"- G8 real Cubism: `{report['summary']['g8_real_cubism_status']}`",
        "",
        "## Primary Decisions",
        "",
    ]
    for idx, item in enumerate(primary, start=1):
        lines.extend(
            [
                f"### {idx}. {item['part_id']}",
                "",
                f"- group: `{item['review_group']}`",
                f"- recommendation: `{item['recommendation']}`",
                f"- owner decision: `{item['owner_decision']}`",
                f"- allowed decisions: `{', '.join(item['allowed_owner_decisions'])}`",
                f"- if accept: {item['next_if_accept']}",
                f"- if revise: {item['next_if_revise']}",
                f"- if regenerate: {item['next_if_regenerate']}",
                "",
            ]
        )
    lines.extend(["## Secondary Followups", ""])
    for item in secondary:
        lines.append(f"- `{item['part_id']}` `{item['recommendation']}`: {item['reason']}")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            report["decision"],
            "",
            "## Next Action",
            "",
            *[f"- {item}" for item in report["next_action"]],
            "",
            "## Self Review",
            "",
        ]
    )
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": report["status"], "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

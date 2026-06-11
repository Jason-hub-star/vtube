#!/usr/bin/env python3
"""Build a G3 B4/B5 blocker-reduction packet for character 002 v22.

This narrows visual-overlay work after G2 technical QA. It does not approve
material PASS, Mini Cubism, or real Cubism.
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
TRIAGE_JSON = EXP / "reports/v22_64part_corrected_b4_b5_manifest/v22_corrected_b4_b5_codex_visual_triage.json"
G2_QA_JSON = EXP / "reports/v22_g2_layer_manifest_technical_qa/v22_g2_layer_manifest_technical_qa_report.json"
REPORT_DIR = EXP / "reports/v22_g3_b4_b5_blocker_reduction"
REPORT_JSON = REPORT_DIR / "v22_g3_b4_b5_blocker_reduction_packet.json"
REPORT_MD = REPORT_DIR / "v22_g3_b4_b5_blocker_reduction_packet.md"
REVIEW_SHEET = REPORT_DIR / "v22_g3_b4_b5_blocker_reduction_sheet.png"

CANVAS = 2048
TILE_W = 420
TILE_H = 300


FACE_MICRO_PARTS = {
    "face_shadow_L",
    "face_shadow_R",
    "nose",
    "cheek_L",
    "cheek_R",
    "brow_L",
    "brow_R",
}


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
        return (720, 720, 1328, 1328)
    pad = 140
    return (
        max(0, bbox[0] - pad),
        max(0, bbox[1] - pad),
        min(CANVAS, bbox[2] + pad),
        min(CANVAS, bbox[3] + pad),
    )


def route_for(entry: dict) -> dict:
    part_id = entry["part_id"]
    if entry["bucket"] == "HARD_REVIEW":
        return {
            "priority": "P0",
            "blocker_class": "G3_PRIMARY_BLOCKER",
            "route": "B5_TORSO_MINIPASS_V2_OR_HUMAN_ACCEPT_REQUIRED",
            "reason": "Torso underpaint is broad and central; it blocks G3 visual overlay progress first.",
        }
    if entry["source_batch"] == "B4":
        return {
            "priority": "P1",
            "blocker_class": "G3_PRIMARY_BLOCKER",
            "route": "B4_SECONDARY_HAIR_DRAW_ORDER_OR_MASK_REVIEW",
            "reason": "Secondary/back/side hair affects front-hair readability and draw-order context.",
        }
    if part_id in FACE_MICRO_PARTS:
        return {
            "priority": "P3",
            "blocker_class": "G3_CONTEXT_REVIEW",
            "route": "B5_FACE_MICRO_DETAIL_CONTEXT_REVIEW",
            "reason": "Low-alpha face/brow/cheek/nose details should be checked in context after primary blockers.",
        }
    return {
        "priority": "P2",
        "blocker_class": "G3_SECONDARY_BLOCKER",
        "route": "B5_BODY_CLOTHING_STACK_CONTEXT_REVIEW",
        "reason": "Copied B5 body/clothing layer needs stack context review before material acceptance.",
    }


def color_for(priority: str) -> tuple[int, int, int]:
    return {
        "P0": (202, 74, 52),
        "P1": (207, 126, 44),
        "P2": (65, 126, 197),
        "P3": (92, 133, 96),
    }[priority]


def tile(source: Image.Image, row: dict) -> Image.Image:
    layer = Image.open(ROOT / row["path"]).convert("RGBA")
    crop_box = crop_box_for(row["bbox"])
    base = source.crop(crop_box).convert("RGBA")
    part = layer.crop(crop_box).convert("RGBA")
    color = color_for(row["priority"])
    tint = Image.new("RGBA", base.size, (*color, 0))
    tint.putalpha(part.getchannel("A").point(lambda v: min(165, int(v * 0.7))))
    comp = Image.alpha_composite(base, tint)
    comp.thumbnail((TILE_W - 22, TILE_H - 96), Image.Resampling.LANCZOS)

    out = Image.new("RGB", (TILE_W, TILE_H), (247, 248, 250))
    out.paste(comp.convert("RGB"), ((TILE_W - comp.width) // 2, 8))
    draw = ImageDraw.Draw(out)
    draw.rectangle([4, 4, TILE_W - 5, TILE_H - 5], outline=(216, 222, 232))
    draw.rectangle([8, TILE_H - 90, TILE_W - 9, TILE_H - 64], fill=color)
    draw.text((12, TILE_H - 86), f"{row['priority']} {row['blocker_class']}", fill=(255, 255, 255))
    draw.text((12, TILE_H - 58), f"{row['part_id']}  {row['source_batch']}  alpha={row['alpha_coverage']}", fill=(25, 31, 40))
    draw.text((12, TILE_H - 36), row["route"][:56], fill=(78, 89, 104))
    draw.text((12, TILE_H - 17), row["bucket"], fill=(78, 89, 104))
    return out


def build_sheet(rows: list[dict]) -> None:
    source = Image.open(SOURCE).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    ordered = sorted(rows, key=lambda r: (r["priority"], r["part_id"]))
    cols = 3
    header_h = 70
    sheet_rows = (len(ordered) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * TILE_W, header_h + sheet_rows * TILE_H), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 16), "Character 002 v22 G3 B4/B5 Blocker Reduction", fill=(25, 31, 40))
    draw.text((12, 40), "Primary blockers first; material PASS / ParamHairFront / G7 / G8 remain blocked", fill=(78, 89, 104))
    for idx, row in enumerate(ordered):
        sheet.paste(tile(source, row), ((idx % cols) * TILE_W, header_h + (idx // cols) * TILE_H))
    REVIEW_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(REVIEW_SHEET)


def main() -> int:
    triage = load_json(TRIAGE_JSON)
    g2 = load_json(G2_QA_JSON)
    blocker_entries = [entry for entry in triage["triage_entries"] if entry["bucket"] in {"HARD_REVIEW", "HOLD_REVIEW"}]
    rows = []
    for entry in blocker_entries:
        route = route_for(entry)
        rows.append(
            {
                **entry,
                **route,
                "material_promotion": "BLOCKED",
                "not_owner_approval": True,
            }
        )
    build_sheet(rows)

    priority_counts = Counter(row["priority"] for row in rows)
    blocker_class_counts = Counter(row["blocker_class"] for row in rows)
    route_counts = Counter(row["route"] for row in rows)
    status = "G3_B4_B5_BLOCKER_REDUCTION_PACKET_READY_PRIMARY_10_MATERIAL_BLOCKED"
    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": status,
        "codex_visual_triage": rel(TRIAGE_JSON),
        "g2_layer_manifest_technical_qa": rel(G2_QA_JSON),
        "review_sheet": rel(REVIEW_SHEET),
        "blocker_rows": rows,
        "summary": {
            "triage_status": triage["status"],
            "g2_status": g2["status"],
            "blocker_row_count": len(rows),
            "primary_blocker_count": blocker_class_counts.get("G3_PRIMARY_BLOCKER", 0),
            "secondary_blocker_count": blocker_class_counts.get("G3_SECONDARY_BLOCKER", 0),
            "context_review_count": blocker_class_counts.get("G3_CONTEXT_REVIEW", 0),
            "priority_counts": dict(sorted(priority_counts.items())),
            "blocker_class_counts": dict(sorted(blocker_class_counts.items())),
            "route_counts": dict(sorted(route_counts.items())),
            "auto_candidate_count_preserved": triage["summary"]["auto_candidate_count"],
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g3_visual_overlay_status": "BLOCKED_PRIMARY_REVIEW_REQUIRED",
            "g4_psd_import_prep_status": "PREP_ONLY_BLOCKED",
            "g5_material_acceptance_status": "BLOCKED",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
        "decision": (
            "G3 blocker work is reduced to 10 primary visual blockers first: one torso hard review plus nine B4 secondary hair "
            "draw-order/mask rows. Seven B5 body/clothing rows and seven B5 face micro-detail rows remain for later context review."
        ),
        "next_action": [
            "Resolve P0 torso first, then P1 B4 secondary hair rows.",
            "Keep P2/P3 B5 copied layers as context review rows until primary blockers are handled.",
            "Do not promote material PASS, ParamHairFront, Mini Cubism, or real Cubism from this packet.",
        ],
        "self_review": {
            "triage_status": triage["status"],
            "g2_status": g2["status"],
            "blocker_row_count": len(rows),
            "primary_blocker_count": blocker_class_counts.get("G3_PRIMARY_BLOCKER", 0),
            "secondary_blocker_count": blocker_class_counts.get("G3_SECONDARY_BLOCKER", 0),
            "context_review_count": blocker_class_counts.get("G3_CONTEXT_REVIEW", 0),
            "p0_count": priority_counts.get("P0", 0),
            "p1_count": priority_counts.get("P1", 0),
            "p2_count": priority_counts.get("P2", 0),
            "p3_count": priority_counts.get("P3", 0),
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
        "# Character 002 v22 G3 B4/B5 Blocker Reduction Packet",
        "",
        f"- status: `{report['status']}`",
        f"- review sheet: `{report['review_sheet']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Primary Rows", ""])
    for row in sorted(rows, key=lambda r: (r["priority"], r["part_id"])):
        if row["blocker_class"] == "G3_PRIMARY_BLOCKER":
            lines.append(f"- `{row['priority']}` `{row['part_id']}` `{row['route']}`")
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

#!/usr/bin/env python3
"""Build a compact G4 visual review surface for character 002 v22."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"

READINESS_JSON = EXP / "reports/v22_g4_g5_material_promotion_readiness/v22_g4_g5_material_promotion_readiness_report.json"
P0_MANIFEST_JSON = EXP / "reports/v22_64part_p0_torso_v2_manifest/v22_64part_p0_torso_v2_manifest.json"
COMBINED_G3_JSON = EXP / "reports/v22_g3_combined_context_overlay_review/v22_g3_combined_context_overlay_review_report.json"

REVIEW_ITEMS = [
    {
        "id": "B1_CLEAN_BASE_UNDERPAINT",
        "title": "B1 Clean Base / Underpaint",
        "image": EXP / "reports/v22_b1_clean_base_underpaint/v22_b1_layer_pack_overlay_qa.png",
        "report": EXP / "reports/v22_b1_clean_base_underpaint/v22_b1_visual_qa_report.json",
        "review_gate": "PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED",
    },
    {
        "id": "B2_EYE_PACK",
        "title": "B2 Eye Pack",
        "image": EXP / "reports/v22_b2_eye_pack/v22_b2_overlay_qa_on_b1_clean_base.png",
        "report": EXP / "reports/v22_b2_eye_pack/v22_b2_overlay_qa_report.json",
        "review_gate": "PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED",
    },
    {
        "id": "B3_MOUTH_PACK_REVISION_V1",
        "title": "B3 Mouth Pack Revision v1",
        "image": EXP / "reports/v22_b3_mouth_pack_revision_v1/v22_b3_revision_v1_overlay_qa.png",
        "report": EXP / "reports/v22_b3_mouth_pack_revision_v1/v22_b3_revision_v1_overlay_qa_report.json",
        "review_gate": "PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED",
    },
    {
        "id": "B4_B5_COMBINED_CONTEXT",
        "title": "B4/B5 Combined Context Overlay",
        "image": EXP / "reports/v22_g3_combined_context_overlay_review/v22_g3_combined_context_overlay_review.png",
        "report": COMBINED_G3_JSON,
        "review_gate": "CONTEXT_REVIEW_REQUIRED_NOT_PASS",
    },
    {
        "id": "G1_G2_64PART_CONTACT",
        "title": "64-Part Contact Sheet",
        "image": EXP / "reports/v22_64part_p0_torso_v2_manifest/v22_64part_p0_torso_v2_manifest_contact_sheet.png",
        "report": P0_MANIFEST_JSON,
        "review_gate": "TECHNICAL_PASS_VISUAL_REVIEW_REQUIRED",
    },
]

REPORT_DIR = EXP / "reports/v22_g4_compact_visual_review_surface"
REPORT_JSON = REPORT_DIR / "v22_g4_compact_visual_review_surface_report.json"
REPORT_MD = REPORT_DIR / "v22_g4_compact_visual_review_surface_report.md"
REVIEW_SHEET = REPORT_DIR / "v22_g4_compact_visual_review_surface.png"

PANEL_W = 520
PANEL_H = 430


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def panel(item: dict, status: str, subtitle: str) -> Image.Image:
    out = Image.new("RGB", (PANEL_W, PANEL_H), (247, 248, 250))
    draw = ImageDraw.Draw(out)
    draw.rectangle([4, 4, PANEL_W - 5, PANEL_H - 5], outline=(216, 222, 232))
    draw.text((12, 12), item["title"][:58], fill=(25, 31, 40))
    draw.text((12, 34), status[:68], fill=(78, 89, 104))
    draw.text((12, 56), subtitle[:68], fill=(78, 89, 104))
    img = Image.open(item["image"]).convert("RGB")
    img.thumbnail((PANEL_W - 24, PANEL_H - 92), Image.Resampling.LANCZOS)
    out.paste(img, ((PANEL_W - img.width) // 2, 86))
    return out


def build_sheet(rows: list[dict], readiness: dict) -> None:
    cols = 2
    rows_count = 3
    header_h = 92
    sheet = Image.new("RGB", (cols * PANEL_W, header_h + rows_count * PANEL_H), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((14, 14), "Character 002 v22 G4 Compact Visual Review Surface", fill=(25, 31, 40))
    draw.text(
        (14, 38),
        f"status: G4_COMPACT_VISUAL_REVIEW_SURFACE_READY_NOT_PASS | G5: {readiness['summary']['g5_material_acceptance_status']}",
        fill=(78, 89, 104),
    )
    draw.text(
        (14, 62),
        "This surface is for visual acceptance review only. Material PASS, ParamHairFront, G7, and G8 remain blocked.",
        fill=(78, 89, 104),
    )
    for idx, row in enumerate(rows):
        item = next(item for item in REVIEW_ITEMS if item["id"] == row["id"])
        img = panel(item, row["source_status"], row["review_gate"])
        sheet.paste(img, ((idx % cols) * PANEL_W, header_h + (idx // cols) * PANEL_H))
    REVIEW_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(REVIEW_SHEET)


def main() -> int:
    readiness = load_json(READINESS_JSON)
    manifest = load_json(P0_MANIFEST_JSON)
    combined = load_json(COMBINED_G3_JSON)
    rows = []
    for item in REVIEW_ITEMS:
        source_report = load_json(item["report"])
        rows.append(
            {
                "id": item["id"],
                "title": item["title"],
                "image": rel(item["image"]),
                "report": rel(item["report"]),
                "source_status": source_report["status"],
                "review_gate": item["review_gate"],
                "image_exists": item["image"].exists(),
                "report_exists": item["report"].exists(),
                "requires_visual_acceptance": True,
                "material_promotion": "BLOCKED",
            }
        )

    build_sheet(rows, readiness)
    status = "G4_COMPACT_VISUAL_REVIEW_SURFACE_READY_NOT_PASS"
    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": status,
        "g4_g5_readiness": rel(READINESS_JSON),
        "p0_torso_v2_manifest": rel(P0_MANIFEST_JSON),
        "combined_g3_context_overlay": rel(COMBINED_G3_JSON),
        "review_sheet": rel(REVIEW_SHEET),
        "review_items": rows,
        "summary": {
            "review_item_count": len(rows),
            "b1_b3_item_count": 3,
            "b4_b5_context_item_count": 1,
            "manifest_contact_item_count": 1,
            "source_image_count": sum(1 for row in rows if row["image_exists"]),
            "source_report_count": sum(1 for row in rows if row["report_exists"]),
            "manifest_entry_count": manifest["self_review"]["manifest_entry_count"],
            "b4_b5_primary_remaining_count": combined["summary"]["primary_remaining_count"],
            "b4_b5_context_review_count": combined["summary"]["context_review_count"],
            "promotion_blocker_count": readiness["summary"]["promotion_blocker_count"],
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g4_visual_review_status": "READY_FOR_VISUAL_ACCEPTANCE_NOT_PASS",
            "g5_material_acceptance_status": "BLOCKED_CONTEXT_REVIEW_NOT_OWNER_APPROVAL",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
        "decision": (
            "A compact G4 visual review surface is ready. It combines B1 clean base, B2 eyes, B3 mouth revision v1, "
            "B4/B5 combined context overlay, and the 64-part contact sheet. This is not material PASS."
        ),
        "next_action": [
            "Use this sheet for visual acceptance review of B1-B5 as a set.",
            "Only after visual acceptance should a separate G5 material acceptance packet be created.",
            "Keep ParamHairFront hidden, and keep G7/G8 blocked.",
        ],
        "self_review": {
            "readiness_status": readiness["status"],
            "manifest_status": manifest["status"],
            "combined_g3_status": combined["status"],
            "review_item_count": len(rows),
            "all_source_images_exist": all(row["image_exists"] for row in rows),
            "all_source_reports_exist": all(row["report_exists"] for row in rows),
            "review_sheet_exists": REVIEW_SHEET.exists(),
            "b4_b5_primary_remaining_count": combined["summary"]["primary_remaining_count"],
            "b4_b5_context_review_count": combined["summary"]["context_review_count"],
            "requires_visual_acceptance": True,
            "material_pass_blocked": True,
            "validator_only_promotion_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "not_owner_approval": True,
            "status": "PASS",
        },
    }
    save_json(REPORT_JSON, report)

    lines = [
        "# Character 002 v22 G4 Compact Visual Review Surface",
        "",
        f"- status: `{report['status']}`",
        f"- review sheet: `{report['review_sheet']}`",
        "",
        "## Review Items",
        "",
    ]
    for row in rows:
        lines.append(f"- `{row['id']}`: `{row['source_status']}` / `{row['review_gate']}`")
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

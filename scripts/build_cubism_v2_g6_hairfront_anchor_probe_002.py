#!/usr/bin/env python3
"""Build a G6 HairFront anchor/motion-envelope probe packet.

This prepares reproducible anchor evidence for the seven HairFront candidates
after the pre-G7 preview triage. It is not owner approval, not G5 material
acceptance, not ParamHairFront activation, not G7 Mini Cubism, and not real
Cubism readiness.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path("/Users/family/jason/Vtube")
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SOURCE_IMAGE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
ACCEPTANCE = (
    EXP
    / "reports/v22_g5_hairfront_motion_readiness_acceptance/v22_g5_hairfront_motion_readiness_acceptance_packet.json"
)
PREVIEW = (
    EXP
    / "reports/v22_g5_hairfront_motion_readiness_preview/v22_g5_hairfront_motion_readiness_preview_packet.json"
)
TRIAGE = (
    EXP
    / "reports/v22_g5_hairfront_preview_codex_triage/v22_g5_hairfront_preview_codex_triage_packet.json"
)
REPORT_DIR = EXP / "reports/v22_g6_hairfront_anchor_probe"
REPORT_JSON = REPORT_DIR / "v22_g6_hairfront_anchor_probe_packet.json"
REPORT_MD = REPORT_DIR / "v22_g6_hairfront_anchor_probe_packet.md"
CONTACT_SHEET = REPORT_DIR / "v22_g6_hairfront_anchor_probe_sheet.png"

CANVAS = 2048
TILE_W = 480
TILE_H = 430
COLS = 4

STATUS = "G6_HAIRFRONT_ANCHOR_PROBE_READY_REVIEW_REQUIRED_PARAM_HIDDEN"
PROBE_VERDICT = "ANCHOR_PROBE_READY_REVIEW_REQUIRED_NOT_MATERIAL_PASS"


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


def union_bbox(boxes: list[list[int]]) -> list[int]:
    return [
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    ]


def shifted_bbox(bbox: list[int], dx: int, dy: int) -> list[int]:
    return [bbox[0] + dx, bbox[1] + dy, bbox[2] + dx, bbox[3] + dy]


def clamp_crop(bbox: list[int], pad: int = 110) -> tuple[int, int, int, int]:
    return (
        max(0, bbox[0] - pad),
        max(0, bbox[1] - pad),
        min(CANVAS, bbox[2] + pad),
        min(CANVAS, bbox[3] + pad),
    )


def canvas_margin(bbox: list[int]) -> int:
    return min(bbox[0], bbox[1], CANVAS - bbox[2], CANVAS - bbox[3])


def anchor_for(bbox: list[int]) -> list[int]:
    return [round((bbox[0] + bbox[2]) / 2), round((bbox[1] + bbox[3]) / 2)]


def draw_rect(draw: ImageDraw.ImageDraw, bbox: list[int], crop: tuple[int, int, int, int], color: tuple[int, int, int, int], width: int) -> None:
    x0, y0, _, _ = crop
    local = [bbox[0] - x0, bbox[1] - y0, bbox[2] - x0, bbox[3] - y0]
    for offset in range(width):
        draw.rectangle(
            [local[0] - offset, local[1] - offset, local[2] + offset, local[3] + offset],
            outline=color,
        )


def draw_cross(draw: ImageDraw.ImageDraw, anchor: list[int], crop: tuple[int, int, int, int], color: tuple[int, int, int, int]) -> None:
    x0, y0, _, _ = crop
    x = anchor[0] - x0
    y = anchor[1] - y0
    draw.line([x - 18, y, x + 18, y], fill=color, width=4)
    draw.line([x, y - 18, x, y + 18], fill=color, width=4)


def probe_rows(acceptance: dict, preview: dict) -> list[dict]:
    poses = preview["pose_frames"]
    rows = []
    for row in acceptance["hairfront_rows"]:
        bbox = row["bbox"]
        shifted = [shifted_bbox(bbox, pose["dx"], pose["dy"]) for pose in poses]
        envelope = union_bbox(shifted)
        rows.append(
            {
                "row_id": row["row_id"],
                "path": row["path"],
                "bbox": bbox,
                "anchor_center": anchor_for(bbox),
                "motion_envelope_bbox": envelope,
                "motion_envelope_margin_to_canvas": canvas_margin(envelope),
                "pose_shift_count": len(poses),
                "alpha_coverage": row["alpha_coverage"],
                "png_exists": row["png_exists"],
                "independent_part_candidate": row["independent_part_candidate"],
                "anchor_probe_verdict": PROBE_VERDICT,
                "manual_anchor_override_status": "AVAILABLE_IF_VISUAL_REVIEW_REQUIRES_CORRECTION",
                "param_hairfront_activation": "BLOCKED_KEEP_HIDDEN_CONTRACT_ONLY",
                "material_acceptance": "BLOCKED_PENDING_G5_MATERIAL_ACCEPTANCE",
            }
        )
    return rows


def build_sheet(rows: list[dict]) -> None:
    source = Image.open(SOURCE_IMAGE).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    rows_count = (len(rows) + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * TILE_W, rows_count * TILE_H + 82), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 12), "Character 002 v22 G6 HairFront Anchor Probe", fill=(25, 31, 40), font=font(18))
    draw.text(
        (12, 42),
        "BBox/envelope/anchor evidence only: ParamHairFront hidden, no material or G7 acceptance.",
        fill=(78, 89, 104),
        font=font(13),
    )
    for idx, row in enumerate(rows):
        layer = Image.open(ROOT / row["path"]).convert("RGBA")
        base = source.copy()
        base.alpha_composite(layer)
        crop_box = clamp_crop(row["motion_envelope_bbox"])
        crop = base.crop(crop_box)
        cdraw = ImageDraw.Draw(crop, "RGBA")
        draw_rect(cdraw, row["motion_envelope_bbox"], crop_box, (40, 118, 220, 255), 4)
        draw_rect(cdraw, row["bbox"], crop_box, (46, 160, 67, 255), 4)
        draw_cross(cdraw, row["anchor_center"], crop_box, (230, 73, 63, 255))
        crop.thumbnail((TILE_W - 24, TILE_H - 96), Image.Resampling.LANCZOS)
        tile = Image.new("RGB", (TILE_W, TILE_H), (247, 248, 250))
        tile.paste(crop.convert("RGB"), ((TILE_W - crop.width) // 2, 10))
        tdraw = ImageDraw.Draw(tile)
        tdraw.rectangle([4, 4, TILE_W - 5, TILE_H - 5], outline=(214, 221, 232))
        tdraw.rectangle([8, TILE_H - 78, TILE_W - 9, TILE_H - 48], fill=(48, 116, 176))
        tdraw.text((14, TILE_H - 71), row["row_id"], fill=(255, 255, 255), font=font(13))
        tdraw.text(
            (14, TILE_H - 40),
            f"anchor={row['anchor_center']} margin={row['motion_envelope_margin_to_canvas']}",
            fill=(25, 31, 40),
            font=font(12),
        )
        tdraw.text((14, TILE_H - 18), "blue=envelope green=bbox red=anchor", fill=(78, 89, 104), font=font(11))
        sheet.paste(tile, ((idx % COLS) * TILE_W, 82 + (idx // COLS) * TILE_H))
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET)


def main() -> int:
    acceptance = load_json(ACCEPTANCE)
    preview = load_json(PREVIEW)
    triage = load_json(TRIAGE)
    rows = probe_rows(acceptance, preview)
    build_sheet(rows)

    min_margin = min(row["motion_envelope_margin_to_canvas"] for row in rows)
    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": STATUS,
        "source_hairfront_acceptance": rel(ACCEPTANCE),
        "source_preview_packet": rel(PREVIEW),
        "source_triage_packet": rel(TRIAGE),
        "source_statuses": {
            "acceptance": acceptance["status"],
            "preview": preview["status"],
            "triage": triage["status"],
        },
        "contact_sheet": rel(CONTACT_SHEET),
        "probe_verdict": PROBE_VERDICT,
        "hairfront_rows": rows,
        "summary": {
            "hairfront_row_count": len(rows),
            "anchor_probe_row_count": len(rows),
            "anchor_center_count": sum(1 for row in rows if row["anchor_center"]),
            "motion_envelope_count": sum(1 for row in rows if row["motion_envelope_bbox"]),
            "pose_shift_count": preview["summary"]["pose_frame_count"],
            "technical_frame_pass_count": triage["summary"]["technical_frame_pass_count"],
            "shifted_bbox_canvas_violation_count": triage["summary"][
                "shifted_bbox_canvas_violation_count"
            ],
            "motion_envelope_min_margin_to_canvas": min_margin,
            "contact_sheet_exists": CONTACT_SHEET.exists(),
            "manual_anchor_override_ready_count": len(rows),
            "manual_anchor_override_saved_count": 0,
            "codex_visual_acceptance_pass_count": 0,
            "motion_readiness_pass_count": 0,
            "param_hairfront_activation_count": 0,
            "material_acceptance_pass_count": 0,
            "owner_approval_count": 0,
            "g6_anchor_correction_status": "READY_IF_VISUAL_REVIEW_REQUIRES_CORRECTION",
            "g5_material_acceptance_status": "BLOCKED_HAIRFRONT_ANCHOR_PROBE_REVIEW_REQUIRED",
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE",
            "g8_real_cubism_status": "BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE",
        },
        "gate_matrix": {
            "G6_HAIRFRONT_ANCHOR_PROBE": "READY_REVIEW_REQUIRED_NOT_MATERIAL_PASS",
            "G6_MANUAL_ANCHOR_CORRECTION": "AVAILABLE_IF_VISUAL_REVIEW_REQUIRES_CORRECTION",
            "G5_MATERIAL_ACCEPTANCE": "BLOCKED_HAIRFRONT_ANCHOR_PROBE_REVIEW_REQUIRED",
            "G7_MINI_CUBISM_DIAGNOSTIC": "BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE",
            "G8_REAL_CUBISM_AUTHORING": "BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE",
        },
        "locks": {
            "v21_eye_open_lower_bound": 0.27,
            "v21_mouth_open_y_max": 0.85,
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "validator_only_promotion_blocked": True,
            "codex_visual_not_owner_approval": True,
            "material_pass_status": "BLOCKED",
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "not_owner_approval": True,
        },
        "decision": (
            "Seven HairFront candidates now have reproducible anchor centers and motion-envelope "
            "bboxes for G6 correction/review. This prepares correction evidence only; G5 material "
            "acceptance, motion-readiness PASS, ParamHairFront activation, G7, and real Cubism "
            "remain blocked."
        ),
        "next_action": [
            "Use the anchor probe sheet to decide whether each HairFront row needs manual anchor correction or regeneration.",
            "If continuing autonomously, build a correction input packet that can store override JSON without claiming material acceptance.",
            "Keep ParamHairFront hidden until a separate material decision gate explicitly passes.",
        ],
        "self_review": {
            "acceptance_status": acceptance["status"],
            "preview_status": preview["status"],
            "triage_status": triage["status"],
            "hairfront_row_count": len(rows),
            "anchor_probe_row_count": len(rows),
            "anchor_center_count": sum(1 for row in rows if row["anchor_center"]),
            "motion_envelope_count": sum(1 for row in rows if row["motion_envelope_bbox"]),
            "pose_shift_count": preview["summary"]["pose_frame_count"],
            "technical_frame_pass_count": triage["summary"]["technical_frame_pass_count"],
            "shifted_bbox_canvas_violation_count": triage["summary"][
                "shifted_bbox_canvas_violation_count"
            ],
            "contact_sheet_exists": CONTACT_SHEET.exists(),
            "manual_anchor_override_ready_count": len(rows),
            "manual_anchor_override_saved_count": 0,
            "codex_visual_acceptance_pass_count": 0,
            "motion_readiness_pass_count": 0,
            "param_hairfront_activation_count": 0,
            "material_acceptance_pass_count": 0,
            "owner_approval_count": 0,
            "g5_material_not_accepted": True,
            "validator_only_promotion_blocked": True,
            "codex_visual_not_owner_approval": True,
            "material_pass_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "not_owner_approval": True,
            "status": "PASS",
        },
    }

    save_json(REPORT_JSON, report)

    lines = [
        "# Character 002 v22 G6 HairFront Anchor Probe",
        "",
        f"- status: `{report['status']}`",
        f"- probe verdict: `{report['probe_verdict']}`",
        f"- contact sheet: `{report['contact_sheet']}`",
        f"- G5 material acceptance: `{report['summary']['g5_material_acceptance_status']}`",
        f"- ParamHairFront: `{report['summary']['param_hair_front_status']}`",
        "",
        "## Counts",
        "",
        f"- hairfront_row_count: `{report['summary']['hairfront_row_count']}`",
        f"- anchor_probe_row_count: `{report['summary']['anchor_probe_row_count']}`",
        f"- anchor_center_count: `{report['summary']['anchor_center_count']}`",
        f"- motion_envelope_count: `{report['summary']['motion_envelope_count']}`",
        f"- technical_frame_pass_count: `{report['summary']['technical_frame_pass_count']}`",
        f"- shifted_bbox_canvas_violation_count: `{report['summary']['shifted_bbox_canvas_violation_count']}`",
        f"- manual_anchor_override_ready_count: `{report['summary']['manual_anchor_override_ready_count']}`",
        f"- manual_anchor_override_saved_count: `{report['summary']['manual_anchor_override_saved_count']}`",
        f"- motion_readiness_pass_count: `{report['summary']['motion_readiness_pass_count']}`",
        f"- param_hairfront_activation_count: `{report['summary']['param_hairfront_activation_count']}`",
        f"- material_acceptance_pass_count: `{report['summary']['material_acceptance_pass_count']}`",
        "",
        "## HairFront Rows",
        "",
    ]
    for row in rows:
        lines.append(
            f"- `{row['row_id']}`: anchor `{row['anchor_center']}`, "
            f"envelope `{row['motion_envelope_bbox']}`, "
            f"margin `{row['motion_envelope_margin_to_canvas']}`"
        )
    lines.extend(["", "## Next Action", ""])
    for action in report["next_action"]:
        lines.append(f"- {action}")
    lines.extend(
        [
            "",
            "## Self Review",
            "",
            "```json",
            json.dumps(report["self_review"], ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {REPORT_JSON}")
    print(f"Wrote {REPORT_MD}")
    print(f"Wrote {CONTACT_SHEET}")
    print(STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

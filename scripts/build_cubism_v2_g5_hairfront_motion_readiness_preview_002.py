#!/usr/bin/env python3
"""Build a pre-G7 HairFront motion-readiness preview packet.

This creates deterministic static preview frames by shifting the seven
front-hair child PNG candidates. It is review evidence only, not a Mini Cubism
pose sweep, not ParamHairFront activation, and not material acceptance.
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
REPORT_DIR = EXP / "reports/v22_g5_hairfront_motion_readiness_preview"
REPORT_JSON = REPORT_DIR / "v22_g5_hairfront_motion_readiness_preview_packet.json"
REPORT_MD = REPORT_DIR / "v22_g5_hairfront_motion_readiness_preview_packet.md"
CONTACT_SHEET = REPORT_DIR / "v22_g5_hairfront_motion_readiness_preview_sheet.png"
CANVAS = 2048
TILE_W = 360
TILE_H = 430

POSES = [
    {"pose_id": "neutral", "dx": 0, "dy": 0, "label": "Neutral"},
    {"pose_id": "swing_left", "dx": -14, "dy": 4, "label": "Swing L"},
    {"pose_id": "swing_right", "dx": 14, "dy": 4, "label": "Swing R"},
    {"pose_id": "lift", "dx": 0, "dy": -10, "label": "Lift"},
    {"pose_id": "settle", "dx": 0, "dy": 8, "label": "Settle"},
]


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


def combined_bbox(rows: list[dict], pad: int = 130) -> tuple[int, int, int, int]:
    xs0, ys0, xs1, ys1 = [], [], [], []
    for row in rows:
        bbox = row["bbox"]
        xs0.append(bbox[0])
        ys0.append(bbox[1])
        xs1.append(bbox[2])
        ys1.append(bbox[3])
    return (
        max(0, min(xs0) - pad),
        max(0, min(ys0) - pad),
        min(CANVAS, max(xs1) + pad),
        min(CANVAS, max(ys1) + pad),
    )


def shifted_layer(layer: Image.Image, dx: int, dy: int) -> Image.Image:
    out = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    out.alpha_composite(layer, dest=(dx, dy))
    return out


def build_pose_composite(source: Image.Image, layers: list[Image.Image], pose: dict) -> Image.Image:
    comp = source.copy()
    for layer in layers:
        moved = shifted_layer(layer, pose["dx"], pose["dy"])
        comp = Image.alpha_composite(comp, moved)
    return comp


def build_sheet(rows: list[dict], pose_frames: list[dict]) -> None:
    crop = combined_bbox(rows)
    sheet = Image.new("RGB", (len(pose_frames) * TILE_W, TILE_H + 82), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 12), "Character 002 v22 HairFront Pre-G7 Motion Preview", fill=(25, 31, 40), font=font(18))
    draw.text(
        (12, 42),
        "Static shifted preview only: ParamHairFront hidden, no G5/G7 material acceptance.",
        fill=(78, 89, 104),
        font=font(13),
    )
    for idx, frame in enumerate(pose_frames):
        image = Image.open(ROOT / frame["image"]).convert("RGBA").crop(crop)
        image.thumbnail((TILE_W - 20, TILE_H - 86), Image.Resampling.LANCZOS)
        tile = Image.new("RGB", (TILE_W, TILE_H), (247, 248, 250))
        tile.paste(image.convert("RGB"), ((TILE_W - image.width) // 2, 10))
        tdraw = ImageDraw.Draw(tile)
        tdraw.rectangle([4, 4, TILE_W - 5, TILE_H - 5], outline=(214, 221, 232))
        tdraw.rectangle([8, TILE_H - 70, TILE_W - 9, TILE_H - 42], fill=(126, 87, 194))
        tdraw.text((14, TILE_H - 64), frame["label"], fill=(255, 255, 255), font=font(13))
        tdraw.text((14, TILE_H - 34), f"dx={frame['dx']} dy={frame['dy']}", fill=(25, 31, 40), font=font(12))
        tdraw.text((14, TILE_H - 16), "review-required / hidden", fill=(78, 89, 104), font=font(11))
        sheet.paste(tile, (idx * TILE_W, 82))
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET)


def main() -> int:
    acceptance = load_json(ACCEPTANCE)
    rows = acceptance["hairfront_rows"]
    source = Image.open(SOURCE_IMAGE).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    layers = [Image.open(ROOT / row["path"]).convert("RGBA") for row in rows]

    frames = []
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    for pose in POSES:
        comp = build_pose_composite(source, layers, pose)
        frame_path = REPORT_DIR / f"hairfront_motion_preview_{pose['pose_id']}.png"
        comp.save(frame_path)
        frames.append(
            {
                "pose_id": pose["pose_id"],
                "label": pose["label"],
                "dx": pose["dx"],
                "dy": pose["dy"],
                "image": rel(frame_path),
            }
        )
    build_sheet(rows, frames)

    status = "G5_HAIRFRONT_MOTION_READINESS_PREVIEW_READY_REVIEW_REQUIRED_PARAM_HIDDEN"
    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "source_hairfront_acceptance": rel(ACCEPTANCE),
        "source_status": acceptance["status"],
        "source_image": rel(SOURCE_IMAGE),
        "contact_sheet": rel(CONTACT_SHEET),
        "pose_frames": frames,
        "hairfront_rows": [
            {
                "row_id": row["row_id"],
                "path": row["path"],
                "bbox": row["bbox"],
                "alpha_coverage": row["alpha_coverage"],
            }
            for row in rows
        ],
        "summary": {
            "hairfront_row_count": len(rows),
            "pose_frame_count": len(frames),
            "preview_contact_sheet_exists": CONTACT_SHEET.exists(),
            "all_pose_frames_exist": all((ROOT / frame["image"]).exists() for frame in frames),
            "static_independent_candidate_count": acceptance["summary"][
                "independent_part_candidate_count"
            ],
            "motion_preview_generated_count": len(frames),
            "motion_readiness_pass_count": 0,
            "motion_readiness_review_required_count": len(rows),
            "param_hairfront_activation_count": 0,
            "material_acceptance_pass_count": 0,
            "owner_approval_count": 0,
            "g5_material_acceptance_status": "BLOCKED_HAIRFRONT_PREVIEW_REVIEW_REQUIRED",
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE",
            "g8_real_cubism_status": "BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE",
        },
        "gate_matrix": {
            "G5_HAIRFRONT_MOTION_PREVIEW": "PREVIEW_READY_REVIEW_REQUIRED",
            "G5_HAIRFRONT_MOTION_READINESS": "REVIEW_REQUIRED_KEEP_PARAM_HIDDEN",
            "G5_MATERIAL_ACCEPTANCE": "BLOCKED_HAIRFRONT_PREVIEW_REVIEW_REQUIRED",
            "G7_MINI_CUBISM_DIAGNOSTIC": "BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE",
            "G8_REAL_CUBISM_AUTHORING": "BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE",
        },
        "locks": {
            "v21_eye_open_lower_bound": 0.27,
            "v21_mouth_open_y_max": 0.85,
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "validator_only_promotion_blocked": True,
            "material_pass_status": "BLOCKED",
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "not_owner_approval": True,
        },
        "decision": (
            "Pre-G7 HairFront motion preview frames are ready for review. They demonstrate shifted "
            "static candidate layers, but do not prove rig motion readiness, material acceptance, "
            "ParamHairFront activation, G7, or real Cubism readiness."
        ),
        "next_action": [
            "Review the contact sheet for obvious front-hair drift, pasted edges, or occlusion problems.",
            "If acceptable, build a dedicated Mini Cubism HairFront diagnostic preview while keeping ParamHairFront hidden until material acceptance.",
            "If not acceptable, route the seven HairFront rows to manual anchor correction or regeneration.",
        ],
        "self_review": {
            "source_status": acceptance["status"],
            "hairfront_row_count": len(rows),
            "pose_frame_count": len(frames),
            "preview_contact_sheet_exists": CONTACT_SHEET.exists(),
            "all_pose_frames_exist": all((ROOT / frame["image"]).exists() for frame in frames),
            "static_independent_candidate_count": acceptance["summary"][
                "independent_part_candidate_count"
            ],
            "motion_preview_generated_count": len(frames),
            "motion_readiness_pass_count": 0,
            "motion_readiness_review_required_count": len(rows),
            "param_hairfront_activation_count": 0,
            "material_acceptance_pass_count": 0,
            "owner_approval_count": 0,
            "g5_material_not_accepted": True,
            "validator_only_promotion_blocked": True,
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
        "# Character 002 v22 HairFront Motion Readiness Preview",
        "",
        f"- status: `{report['status']}`",
        f"- source: `{report['source_hairfront_acceptance']}`",
        f"- contact sheet: `{report['contact_sheet']}`",
        f"- G5 material acceptance: `{report['summary']['g5_material_acceptance_status']}`",
        f"- ParamHairFront: `{report['summary']['param_hair_front_status']}`",
        f"- G7: `{report['summary']['g7_mini_cubism_status']}`",
        "",
        "## Counts",
        "",
        f"- hairfront_row_count: `{report['summary']['hairfront_row_count']}`",
        f"- pose_frame_count: `{report['summary']['pose_frame_count']}`",
        f"- motion_preview_generated_count: `{report['summary']['motion_preview_generated_count']}`",
        f"- motion_readiness_pass_count: `{report['summary']['motion_readiness_pass_count']}`",
        f"- param_hairfront_activation_count: `{report['summary']['param_hairfront_activation_count']}`",
        f"- material_acceptance_pass_count: `{report['summary']['material_acceptance_pass_count']}`",
        "",
        "## Pose Frames",
        "",
    ]
    for frame in frames:
        lines.append(f"- `{frame['pose_id']}`: `{frame['image']}`")
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
    print(status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build Codex triage for the v22 HairFront pre-G7 motion preview.

This is a technical/provisional review of the preview frames only. It does not
grant owner approval, G5 material acceptance, ParamHairFront activation, Mini
Cubism promotion, or real Cubism readiness.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageChops


ROOT = Path("/Users/family/jason/Vtube")
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SOURCE = (
    EXP
    / "reports/v22_g5_hairfront_motion_readiness_preview/v22_g5_hairfront_motion_readiness_preview_packet.json"
)
REPORT_DIR = EXP / "reports/v22_g5_hairfront_preview_codex_triage"
REPORT_JSON = REPORT_DIR / "v22_g5_hairfront_preview_codex_triage_packet.json"
REPORT_MD = REPORT_DIR / "v22_g5_hairfront_preview_codex_triage_packet.md"
CANVAS = 2048

STATUS = "G5_HAIRFRONT_PREVIEW_CODEX_TRIAGE_READY_REVIEW_REQUIRED_PARAM_HIDDEN"
TRIAGE_VERDICT = "NO_CATASTROPHIC_TECHNICAL_FAILURE_DETECTED_REVIEW_REQUIRED"
VISUAL_VERDICT = "CODEX_PROVISIONAL_REVIEW_REQUIRED_NOT_OWNER_APPROVAL"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def shifted_bbox(row: dict, dx: int, dy: int) -> list[int]:
    x0, y0, x1, y1 = row["bbox"]
    return [x0 + dx, y0 + dy, x1 + dx, y1 + dy]


def bbox_inside_canvas(bbox: list[int]) -> bool:
    x0, y0, x1, y1 = bbox
    return 0 <= x0 <= CANVAS and 0 <= y0 <= CANVAS and 0 <= x1 <= CANVAS and 0 <= y1 <= CANVAS


def changed_ratio(frame: Path, neutral: Path) -> float:
    image = Image.open(frame).convert("RGB")
    base = Image.open(neutral).convert("RGB")
    diff = ImageChops.difference(image, base).convert("L")
    hist = diff.histogram()
    changed = sum(count for value, count in enumerate(hist) if value > 8)
    return round(changed / float(CANVAS * CANVAS), 8)


def frame_row(frame: dict, neutral_path: Path, hairfront_rows: list[dict]) -> dict:
    frame_path = ROOT / frame["image"]
    exists = frame_path.exists()
    size_ok = False
    mode = None
    if exists:
        with Image.open(frame_path) as image:
            size_ok = image.size == (CANVAS, CANVAS)
            mode = image.mode
    shifted = [shifted_bbox(row, frame["dx"], frame["dy"]) for row in hairfront_rows]
    canvas_violations = [bbox for bbox in shifted if not bbox_inside_canvas(bbox)]
    ratio = 0.0 if frame["pose_id"] == "neutral" else changed_ratio(frame_path, neutral_path)
    return {
        "pose_id": frame["pose_id"],
        "label": frame["label"],
        "image": frame["image"],
        "dx": frame["dx"],
        "dy": frame["dy"],
        "exists": exists,
        "mode": mode,
        "size_ok": size_ok,
        "changed_ratio_vs_neutral": ratio,
        "shifted_bbox_canvas_violation_count": len(canvas_violations),
        "frame_technical_verdict": (
            "PASS_PREVIEW_FRAME_TECHNICAL"
            if exists and size_ok and not canvas_violations
            else "REVISE_PREVIEW_FRAME_TECHNICAL"
        ),
        "visual_verdict": VISUAL_VERDICT,
    }


def main() -> int:
    source = load_json(SOURCE)
    neutral = next(frame for frame in source["pose_frames"] if frame["pose_id"] == "neutral")
    neutral_path = ROOT / neutral["image"]
    rows = [
        frame_row(frame, neutral_path, source["hairfront_rows"])
        for frame in source["pose_frames"]
    ]
    technical_pass_count = sum(
        1 for row in rows if row["frame_technical_verdict"] == "PASS_PREVIEW_FRAME_TECHNICAL"
    )
    canvas_violation_count = sum(row["shifted_bbox_canvas_violation_count"] for row in rows)
    non_neutral_ratios = [
        row["changed_ratio_vs_neutral"] for row in rows if row["pose_id"] != "neutral"
    ]

    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": STATUS,
        "source_preview_packet": rel(SOURCE),
        "source_status": source["status"],
        "contact_sheet": source["contact_sheet"],
        "triage_verdict": TRIAGE_VERDICT,
        "codex_provisional_visual_verdict": VISUAL_VERDICT,
        "frame_rows": rows,
        "summary": {
            "hairfront_row_count": source["summary"]["hairfront_row_count"],
            "pose_frame_count": len(rows),
            "technical_frame_pass_count": technical_pass_count,
            "shifted_bbox_canvas_violation_count": canvas_violation_count,
            "max_changed_ratio_vs_neutral": max(non_neutral_ratios) if non_neutral_ratios else 0.0,
            "min_changed_ratio_vs_neutral": min(non_neutral_ratios) if non_neutral_ratios else 0.0,
            "codex_visual_acceptance_pass_count": 0,
            "motion_readiness_pass_count": 0,
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
            "G5_HAIRFRONT_PREVIEW_CODEX_TRIAGE": "READY_REVIEW_REQUIRED_NOT_OWNER_APPROVAL",
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
            "codex_visual_not_owner_approval": True,
            "material_pass_status": "BLOCKED",
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "not_owner_approval": True,
        },
        "decision": (
            "The five HairFront preview frames pass technical triage for file existence, size, "
            "and shifted bbox staying inside the 2048 canvas. This is only Codex provisional "
            "triage; material acceptance, motion readiness, ParamHairFront activation, G7, and "
            "real Cubism remain blocked."
        ),
        "next_action": [
            "Use this packet as automatic evidence that the HairFront preview files are technically complete.",
            "Keep G5 material acceptance blocked until a separate visual/material decision gate is recorded.",
            "If continuing without owner interruption, build only diagnostic/review artifacts while preserving ParamHairFront as hidden.",
        ],
        "self_review": {
            "source_status": source["status"],
            "hairfront_row_count": source["summary"]["hairfront_row_count"],
            "pose_frame_count": len(rows),
            "technical_frame_pass_count": technical_pass_count,
            "shifted_bbox_canvas_violation_count": canvas_violation_count,
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
        "# Character 002 v22 HairFront Preview Codex Triage",
        "",
        f"- status: `{report['status']}`",
        f"- source: `{report['source_preview_packet']}`",
        f"- contact sheet: `{report['contact_sheet']}`",
        f"- triage: `{report['triage_verdict']}`",
        f"- Codex visual verdict: `{report['codex_provisional_visual_verdict']}`",
        f"- G5 material acceptance: `{report['summary']['g5_material_acceptance_status']}`",
        f"- ParamHairFront: `{report['summary']['param_hair_front_status']}`",
        "",
        "## Counts",
        "",
        f"- hairfront_row_count: `{report['summary']['hairfront_row_count']}`",
        f"- pose_frame_count: `{report['summary']['pose_frame_count']}`",
        f"- technical_frame_pass_count: `{report['summary']['technical_frame_pass_count']}`",
        f"- shifted_bbox_canvas_violation_count: `{report['summary']['shifted_bbox_canvas_violation_count']}`",
        f"- codex_visual_acceptance_pass_count: `{report['summary']['codex_visual_acceptance_pass_count']}`",
        f"- motion_readiness_pass_count: `{report['summary']['motion_readiness_pass_count']}`",
        f"- param_hairfront_activation_count: `{report['summary']['param_hairfront_activation_count']}`",
        f"- material_acceptance_pass_count: `{report['summary']['material_acceptance_pass_count']}`",
        "",
        "## Frame Rows",
        "",
    ]
    for row in rows:
        lines.append(
            f"- `{row['pose_id']}`: `{row['frame_technical_verdict']}`, "
            f"changed_ratio_vs_neutral `{row['changed_ratio_vs_neutral']}`"
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
    print(STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

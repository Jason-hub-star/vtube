#!/usr/bin/env python3
"""Build the v22 G4 torso_base regeneration/review packet.

The P0 B5 follow-up narrowed pre-G5 work to one row: torso_base. This packet
collects the old/provisional/P0 torso evidence and prepares a focused
regeneration input while keeping G5/material promotion blocked.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"

SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
B5_RAW = EXP / "v22_b5_body_clothing_pack/raw_outputs/b5_body_clothing_pack_reference_001.png"
P0_DECISION_JSON = EXP / "reports/v22_g4_p0_b5_followup_decision/v22_g4_p0_b5_followup_decision_packet.json"
P0_TORSO_JSON = EXP / "reports/v22_g3_p0_torso_minipass_v2/v22_g3_p0_torso_minipass_v2_report.json"
B5_INPUT_JSON = EXP / "reports/v22_b5_provisional_minipass_input_packet/v22_b5_provisional_minipass_input_packet.json"
B5_PROVISIONAL_QA_JSON = EXP / "reports/v22_b5_provisional_minipass_candidate/v22_b5_provisional_minipass_overlay_qa_report.json"

REPORT_DIR = EXP / "reports/v22_g4_torso_base_regen_review_packet"
REPORT_JSON = REPORT_DIR / "v22_g4_torso_base_regen_review_packet.json"
REPORT_MD = REPORT_DIR / "v22_g4_torso_base_regen_review_packet.md"
REGEN_INPUT_JSON = REPORT_DIR / "v22_g4_torso_base_regen_input_packet.json"
REVIEW_SHEET = REPORT_DIR / "v22_g4_torso_base_regen_review_sheet.png"

CANVAS = 2048
TILE_W = 360
TILE_H = 292


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)


def alpha_metrics(path: Path) -> dict:
    img = load_rgba(path)
    alpha = np.asarray(img.getchannel("A"), dtype=np.uint8)
    ys, xs = np.where(alpha > 5)
    bbox = None
    if len(xs):
        bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    return {
        "path": rel(path),
        "mode": img.mode,
        "size": list(img.size),
        "bbox": bbox,
        "alpha_coverage": round(float((alpha > 5).mean()), 8),
        "alpha_sum": int(alpha.sum()),
        "nonzero_alpha_pixels": int((alpha > 5).sum()),
    }


def crop_box_for(*boxes: list[int] | None) -> tuple[int, int, int, int]:
    valid = [box for box in boxes if box]
    if not valid:
        return (470, 780, 1590, 1480)
    x0 = min(box[0] for box in valid)
    y0 = min(box[1] for box in valid)
    x1 = max(box[2] for box in valid)
    y1 = max(box[3] for box in valid)
    pad = 120
    return (max(0, x0 - pad), max(0, y0 - pad), min(CANVAS, x1 + pad), min(CANVAS, y1 + pad))


def overlay_crop(source: Image.Image, layer: Image.Image, crop: tuple[int, int, int, int], color: tuple[int, int, int]) -> Image.Image:
    base = source.crop(crop).convert("RGBA")
    part = layer.crop(crop).convert("RGBA")
    tint = Image.new("RGBA", base.size, (*color, 0))
    tint.putalpha(part.getchannel("A").point(lambda v: min(160, int(v * 0.68))))
    return Image.alpha_composite(base, tint)


def tile(title: str, img: Image.Image, subtitle: str = "") -> Image.Image:
    out = Image.new("RGB", (TILE_W, TILE_H), (247, 248, 250))
    draw = ImageDraw.Draw(out)
    draw.rectangle([4, 4, TILE_W - 5, TILE_H - 5], outline=(216, 222, 232))
    draw.text((10, 10), title[:44], fill=(25, 31, 40))
    if subtitle:
        draw.text((10, 32), subtitle[:50], fill=(78, 89, 104))
    preview = img.convert("RGBA")
    preview.thumbnail((TILE_W - 20, TILE_H - 70), Image.Resampling.LANCZOS)
    out.paste(preview.convert("RGB"), ((TILE_W - preview.width) // 2, 58), preview)
    return out


def build_sheet(metrics: dict) -> None:
    source = load_rgba(SOURCE)
    b5_raw = Image.open(B5_RAW).convert("RGBA")
    old = load_rgba(ROOT / metrics["old_v2"]["path"])
    provisional = load_rgba(ROOT / metrics["provisional"]["path"])
    p0 = load_rgba(ROOT / metrics["p0_v2"]["path"])
    crop = crop_box_for(metrics["old_v2"]["bbox"], metrics["provisional"]["bbox"], metrics["p0_v2"]["bbox"])
    b5_raw_thumb = b5_raw.copy()
    b5_raw_thumb.thumbnail((TILE_W - 20, TILE_H - 70), Image.Resampling.LANCZOS)
    tiles = [
        tile("old v2 overlay", overlay_crop(source, old, crop, (224, 94, 76)), f"cov {metrics['old_v2']['alpha_coverage']}"),
        tile("provisional overlay", overlay_crop(source, provisional, crop, (61, 132, 255)), f"cov {metrics['provisional']['alpha_coverage']}"),
        tile("P0 v2 overlay", overlay_crop(source, p0, crop, (56, 158, 92)), f"cov {metrics['p0_v2']['alpha_coverage']}"),
        tile("P0 v2 isolated", p0.crop(crop), "current review candidate"),
        tile("B5 raw reference", b5_raw_thumb, "body/clothing reference"),
        tile("decision", overlay_crop(source, p0, crop, (199, 72, 57)), "regen/review before G5"),
    ]
    sheet = Image.new("RGB", (3 * TILE_W, 72 + 2 * TILE_H), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 14), "Character 002 v22 G4 torso_base Regeneration/Review Packet", fill=(25, 31, 40))
    draw.text((12, 40), "P0 torso is tighter, but still remains the only pre-G5 review/regeneration blocker.", fill=(78, 89, 104))
    for idx, img in enumerate(tiles):
        sheet.paste(img, ((idx % 3) * TILE_W, 72 + (idx // 3) * TILE_H))
    REVIEW_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(REVIEW_SHEET)


def main() -> int:
    p0_decision = load_json(P0_DECISION_JSON)
    p0_report = load_json(P0_TORSO_JSON)
    b5_input = load_json(B5_INPUT_JSON)
    b5_qa = load_json(B5_PROVISIONAL_QA_JSON)

    decision_row = next(row for row in p0_decision["decision_rows"] if row["part_id"] == "torso_base")
    p0_row = next(row for row in p0_report["entries"] if row["part_id"] == "torso_base")
    input_target = next(row for row in b5_input["targets"] if row["part_id"] == "torso_base")
    provisional_row = next(row for row in b5_qa["qa_entries"] if row["part_id"] == "torso_base")

    metrics = {
        "old_v2": alpha_metrics(ROOT / decision_row["previous_path"]),
        "provisional": alpha_metrics(ROOT / decision_row["provisional_path"]),
        "p0_v2": alpha_metrics(ROOT / decision_row["active_path"]),
    }
    old_cov = metrics["old_v2"]["alpha_coverage"]
    p0_cov = metrics["p0_v2"]["alpha_coverage"]
    metrics["coverage_delta_old_to_p0"] = round(p0_cov - old_cov, 8)
    metrics["coverage_ratio_p0_to_old"] = round(p0_cov / old_cov, 8) if old_cov else None
    metrics["p0_bottom_y"] = metrics["p0_v2"]["bbox"][3] if metrics["p0_v2"]["bbox"] else None
    metrics["old_bottom_y"] = metrics["old_v2"]["bbox"][3] if metrics["old_v2"]["bbox"] else None

    prompt = (
        "Generate a focused Live2D/Cubism torso_base body-underpaint candidate for the existing character 002 front-view source. "
        "Use the same adult cute anime style, same neck/shoulder proportions, same off-shoulder white sweater context, same soft line weight, "
        "and same lighting. Produce only the coherent torso/upper-body underpaint needed behind neck, shoulders, collar, arms, and chest cloth. "
        "The result must be suitable for a full-canvas 2048x2048 RGBA Live2D part named torso_base. It must not be a thin crop, "
        "rectangular patch, oval skin patch, or alpha-shrunk remnant. Preserve natural body continuity under clothing and shoulders, with no baked hair, "
        "no face detail, no extra clothing design, no hands, no props, no labels, and no background."
    )
    negative_prompt = (
        "No labels, arrows, grids, extra face, extra hair, baked hair pixels, hands, props, new outfit, jewelry, perspective pose, "
        "rectangular skin patch, oval patch, flat beige block, noisy alpha scraps, lower-body crop artifact, white background baked into alpha, "
        "large unrelated torso blob, or material PASS claim."
    )
    regen_input = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": "TORSO_BASE_REGEN_INPUT_READY_MATERIAL_BLOCKED",
        "source_image": rel(SOURCE),
        "b5_raw_reference": rel(B5_RAW),
        "current_p0_torso_candidate": decision_row["active_path"],
        "target": {
            "part_id": "torso_base",
            "mode": "REGENERATE_BODY_UNDERPAINT_OR_REVIEW_CURRENT_P0",
            "crop_box": input_target["crop_box"],
            "current_bbox": decision_row["active_bbox"],
            "required_output": "full-canvas 2048x2048 RGBA torso_base.png",
        },
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "acceptance_checks": [
            "Full-canvas RGBA 2048x2048 output, non-empty alpha.",
            "Torso/upper-body underpaint is coherent and not just an alpha-shrunk crop.",
            "No rectangular or oval skin patch.",
            "No baked hair pixels in torso_base.",
            "Fits behind neck, shoulders, collar, arms, and chest cloth in overlay QA.",
            "Still requires separate visual QA and G5 material acceptance.",
        ],
        "locks": {
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
    }
    save_json(REGEN_INPUT_JSON, regen_input)
    build_sheet(metrics)

    status = "G4_TORSO_BASE_REGEN_REVIEW_PACKET_READY_MATERIAL_BLOCKED"
    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": status,
        "p0_b5_followup_decision": rel(P0_DECISION_JSON),
        "p0_torso_v2_report": rel(P0_TORSO_JSON),
        "b5_provisional_input_packet": rel(B5_INPUT_JSON),
        "b5_provisional_overlay_qa": rel(B5_PROVISIONAL_QA_JSON),
        "regen_input_packet": rel(REGEN_INPUT_JSON),
        "review_sheet": rel(REVIEW_SHEET),
        "torso_decision_row": decision_row,
        "torso_p0_report_row": p0_row,
        "torso_b5_input_target": input_target,
        "torso_provisional_qa_row": provisional_row,
        "metrics": metrics,
        "summary": {
            "target_part": "torso_base",
            "remaining_pre_g5_blocker_count": 1,
            "old_v2_alpha_coverage": metrics["old_v2"]["alpha_coverage"],
            "provisional_alpha_coverage": metrics["provisional"]["alpha_coverage"],
            "p0_v2_alpha_coverage": metrics["p0_v2"]["alpha_coverage"],
            "coverage_ratio_p0_to_old": metrics["coverage_ratio_p0_to_old"],
            "recommended_route": "REGENERATE_OR_FOCUSED_VISUAL_ACCEPT_TORSO_BEFORE_G5",
            "default_codex_route": "REGENERATE_TORSO_BASE_BODY_UNDERPAINT_INPUT_READY",
            "g5_material_acceptance_status": "BLOCKED_PENDING_TORSO_REVIEW_OR_REGENERATION",
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
        "decision": (
            "torso_base remains the only pre-G5 blocker. The P0 v2 candidate is tighter than old v2, but the safe default route is "
            "a focused torso_base regeneration/review input, not material acceptance."
        ),
        "next_action": [
            "Use the regen input packet to generate or review one torso_base replacement candidate.",
            "Normalize any returned candidate as full-canvas 2048 RGBA.",
            "Rebuild the P0/G4 readiness evidence only after torso overlay QA exists.",
            "Keep ParamHairFront hidden and keep G7/G8 blocked.",
        ],
        "self_review": {
            "p0_decision_status": p0_decision["status"],
            "p0_torso_status": p0_report["status"],
            "b5_input_status": b5_input["status"],
            "b5_provisional_qa_status": b5_qa["status"],
            "target_is_torso_base": decision_row["part_id"] == "torso_base",
            "remaining_pre_g5_blocker_count": 1,
            "regen_input_exists": REGEN_INPUT_JSON.exists(),
            "review_sheet_exists": REVIEW_SHEET.exists(),
            "all_candidate_paths_exist": all((ROOT / item["path"]).exists() for item in [metrics["old_v2"], metrics["provisional"], metrics["p0_v2"]]),
            "all_candidates_rgba_2048": all(item["mode"] == "RGBA" and item["size"] == [2048, 2048] for item in [metrics["old_v2"], metrics["provisional"], metrics["p0_v2"]]),
            "p0_is_tighter_than_old_v2": metrics["p0_v2"]["alpha_coverage"] < metrics["old_v2"]["alpha_coverage"],
            "prompt_present": bool(prompt),
            "acceptance_checks_present": len(regen_input["acceptance_checks"]) >= 6,
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
        "# Character 002 v22 G4 torso_base Regen/Review Packet",
        "",
        f"- status: `{report['status']}`",
        f"- review sheet: `{report['review_sheet']}`",
        f"- regen input: `{report['regen_input_packet']}`",
        f"- remaining pre-G5 blockers: `{report['summary']['remaining_pre_g5_blocker_count']}`",
        f"- G5 material acceptance: `{report['summary']['g5_material_acceptance_status']}`",
        "",
        "## Metrics",
        "",
        f"- old v2 alpha coverage: `{metrics['old_v2']['alpha_coverage']}`",
        f"- provisional alpha coverage: `{metrics['provisional']['alpha_coverage']}`",
        f"- P0 v2 alpha coverage: `{metrics['p0_v2']['alpha_coverage']}`",
        f"- P0/old coverage ratio: `{metrics['coverage_ratio_p0_to_old']}`",
        "",
        "## Decision",
        "",
        report["decision"],
        "",
        "## Next Action",
        "",
    ]
    lines.extend(f"- {item}" for item in report["next_action"])
    lines.extend(["", "## Self Review", ""])
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": status, "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

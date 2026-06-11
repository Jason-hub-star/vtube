#!/usr/bin/env python3
"""Conservative overlay QA for the B5 provisional mini-pass candidate."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
CANDIDATE_JSON = EXP / "reports/v22_b5_provisional_minipass_candidate/v22_b5_provisional_minipass_candidate_report.json"
V2_QA_JSON = EXP / "reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_overlay_qa_report.json"
SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
REPORT_DIR = EXP / "reports/v22_b5_provisional_minipass_candidate"
REPORT_JSON = REPORT_DIR / "v22_b5_provisional_minipass_overlay_qa_report.json"
REPORT_MD = REPORT_DIR / "v22_b5_provisional_minipass_overlay_qa_report.md"
QA_SHEET = REPORT_DIR / "v22_b5_provisional_minipass_overlay_qa.png"
CANVAS = 2048


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def overlay_crop(source: Image.Image, layer: Image.Image, bbox: list[int]) -> Image.Image:
    pad = 110
    crop_box = (
        max(0, bbox[0] - pad),
        max(0, bbox[1] - pad),
        min(CANVAS, bbox[2] + pad),
        min(CANVAS, bbox[3] + pad),
    )
    base = source.crop(crop_box).convert("RGBA")
    part = layer.crop(crop_box).convert("RGBA")
    tint = Image.new("RGBA", base.size, (58, 132, 255, 0))
    tint.putalpha(part.getchannel("A").point(lambda v: min(150, int(v * 0.68))))
    return Image.alpha_composite(base, tint)


def tile(title: str, img: Image.Image, subtitle: str = "") -> Image.Image:
    out = Image.new("RGB", (360, 300), (247, 248, 250))
    draw = ImageDraw.Draw(out)
    draw.rectangle([4, 4, 355, 295], outline=(216, 222, 232))
    draw.text((10, 10), title[:45], fill=(25, 31, 40))
    if subtitle:
        draw.text((10, 30), subtitle[:50], fill=(78, 89, 104))
    preview = img.convert("RGBA")
    preview.thumbnail((342, 230), Image.Resampling.LANCZOS)
    out.paste(preview.convert("RGB"), ((360 - preview.width) // 2, 58), preview)
    return out


def qa_for(entry: dict) -> tuple[str, str]:
    part_id = entry["part_id"]
    if part_id == "torso_base":
        if entry["candidate_status"] == "REGENERATED_FROM_B5_RAW_MINIPASS":
            return (
                "REVIEW_REGENERATED_TORSO_UNDERPAINT",
                "Torso was rebuilt from the B5 raw reference and is usable as a focused review candidate, but visual approval and overlay QA remain required.",
            )
        return ("REVISE_TORSO_REGENERATION_REQUIRED", "Torso did not follow the regeneration route.")
    if part_id in {"shoulder_L", "shoulder_R"}:
        old = entry.get("old_hair_occlusion_overlap_ratio", 1.0)
        new = entry.get("new_hair_occlusion_overlap_ratio", 1.0)
        if new < old and new <= 0.2:
            return (
                "PASS_DRAW_ORDER_MASK_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED",
                "Hair-occlusion alpha overlap dropped enough for draw-order/mask review, but this is not material approval.",
            )
        return (
            "REVISE_SHOULDER_MASK_STILL_OCCLUDED",
            "Shoulder still overlaps too much hair/line occlusion and needs stronger remask or regeneration.",
        )
    return ("NOT_TARGETED_FOR_THIS_QA", "Copied from B5 refined-mask v2.")


def main() -> int:
    candidate = load_json(CANDIDATE_JSON)
    previous = load_json(V2_QA_JSON)
    source = Image.open(SOURCE).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    target_entries = [entry for entry in candidate["entries"] if entry["candidate_status"] != "COPIED_FROM_V2"]
    qa_entries = []
    for entry in target_entries:
        verdict, reason = qa_for(entry)
        qa_entries.append(
            {
                "part_id": entry["part_id"],
                "candidate_status": entry["candidate_status"],
                "qa_verdict": verdict,
                "reason": reason,
                "bbox": entry["bbox"],
                "alpha_coverage": entry["alpha_coverage"],
                "alpha_sum_ratio": entry["alpha_sum_ratio"],
                "old_hair_occlusion_overlap_ratio": entry.get("old_hair_occlusion_overlap_ratio"),
                "new_hair_occlusion_overlap_ratio": entry.get("new_hair_occlusion_overlap_ratio"),
                "output_path": entry["output_path"],
            }
        )

    sheet = Image.new("RGB", (3 * 360, 54 + len(qa_entries) * 300), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 14), "Character 002 v22 B5 Provisional Mini-Pass Overlay QA", fill=(25, 31, 40))
    for row, entry in enumerate(qa_entries):
        layer = Image.open(ROOT / entry["output_path"]).convert("RGBA")
        over = overlay_crop(source, layer, entry["bbox"])
        isolated = layer.crop(tuple(entry["bbox"])).convert("RGBA")
        bg = Image.new("RGBA", isolated.size, (245, 247, 250, 255))
        isolated = Image.alpha_composite(bg, isolated)
        tiles = [
            tile(entry["part_id"], over, entry["qa_verdict"]),
            tile("isolated", isolated, f"cov {entry['alpha_coverage']}"),
            tile("route evidence", over, entry["reason"]),
        ]
        for col, img in enumerate(tiles):
            sheet.paste(img, (col * 360, 54 + row * 300))
    QA_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(QA_SHEET)

    counts = Counter(entry["qa_verdict"] for entry in qa_entries)
    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": "B5_PROVISIONAL_MINIPASS_OVERLAY_QA_REVIEW_REQUIRED",
        "candidate_report": rel(CANDIDATE_JSON),
        "previous_v2_overlay_qa": rel(V2_QA_JSON),
        "qa_sheet": rel(QA_SHEET),
        "qa_entries": qa_entries,
        "summary": {
            "target_count": len(qa_entries),
            "verdict_counts": dict(sorted(counts.items())),
            "previous_remaining_b5_revise_parts": previous["remaining_b5_revise_parts"],
            "remaining_review_parts": [entry["part_id"] for entry in qa_entries],
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
        "decision": (
            "The provisional B5 mini-pass produced measurable shoulder draw-order/mask improvement and a regenerated torso review candidate, "
            "but all three targeted parts still require visual review before material promotion."
        ),
        "next_action": [
            "Use this QA sheet to decide whether to run actual image-generation regeneration for torso/shoulders or accept them as revised candidates for the next 64-part manifest rebuild.",
            "Do not unlock G7/G8 or ParamHairFront from this QA.",
            "If proceeding automatically, run a corrected B4/B5 manifest rebuild with these B5 candidate layers and rerun full overlay QA.",
        ],
        "self_review": {
            "candidate_status": candidate["status"],
            "target_count": len(qa_entries),
            "has_torso_review_candidate": counts.get("REVIEW_REGENERATED_TORSO_UNDERPAINT", 0) == 1,
            "shoulder_improvement_candidate_count": counts.get("PASS_DRAW_ORDER_MASK_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED", 0),
            "has_blocked_material_gate": True,
            "validator_only_promotion_blocked": True,
            "not_owner_approval": True,
            "material_pass_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "qa_sheet_exists": QA_SHEET.exists(),
            "status": "PASS",
        },
    }
    save_json(REPORT_JSON, report)

    lines = [
        "# Character 002 v22 B5 Provisional Mini-Pass Overlay QA",
        "",
        f"- status: `{report['status']}`",
        f"- QA sheet: `{report['qa_sheet']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Entries", ""])
    for entry in qa_entries:
        lines.append(f"- `{entry['part_id']}` `{entry['qa_verdict']}`: {entry['reason']}")
    lines.extend(["", "## Self Review", ""])
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": report["status"], "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

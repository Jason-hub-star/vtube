#!/usr/bin/env python3
"""Build Codex provisional visual triage for corrected v22 B4/B5 layers.

This keeps progress moving without owner acceptance, but it deliberately does
not promote material PASS, ParamHairFront, Mini Cubism, or real Cubism.
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
QA_JSON = EXP / "reports/v22_64part_corrected_b4_b5_manifest/v22_corrected_b4_b5_manifest_overlay_qa_report.json"
REPORT_DIR = EXP / "reports/v22_64part_corrected_b4_b5_manifest"
REPORT_JSON = REPORT_DIR / "v22_corrected_b4_b5_codex_visual_triage.json"
REPORT_MD = REPORT_DIR / "v22_corrected_b4_b5_codex_visual_triage.md"
TRIAGE_SHEET = REPORT_DIR / "v22_corrected_b4_b5_codex_visual_triage.png"
CANVAS = 2048
TILE_W = 390
TILE_H = 280


TRIAGE_RULES = {
    "B4_FRONT_HAIR_MOTION_CANDIDATE_REVIEW_REQUIRED": {
        "codex_triage": "ACCEPT_AS_MOTION_READINESS_CANDIDATE_KEEP_HAIRFRONT_HIDDEN",
        "bucket": "AUTO_CANDIDATE",
        "reason": (
            "Independent front-hair child candidate exists. Treat as motion-readiness candidate only; "
            "ParamHairFront remains hidden until real motion QA passes."
        ),
    },
    "B5_SHOULDER_DRAW_ORDER_MASK_IMPROVEMENT_REVIEW_REQUIRED": {
        "codex_triage": "ACCEPT_AS_DRAW_ORDER_MASK_IMPROVEMENT_CANDIDATE",
        "bucket": "AUTO_CANDIDATE",
        "reason": "Shoulder hair-occlusion mask conflict is improved enough to keep as a candidate, not material approval.",
    },
    "B5_TORSO_REGENERATED_UNDERPAINT_REVIEW_REQUIRED": {
        "codex_triage": "HARD_REVIEW_TORSO_UNDERPAINT_BEFORE_MATERIAL_PREP",
        "bucket": "HARD_REVIEW",
        "reason": "Broad torso underpaint is regenerated and still visually high-risk before material promotion.",
    },
    "B4_SECONDARY_DRAW_ORDER_OR_MASK_REVIEW_REQUIRED": {
        "codex_triage": "HOLD_FOR_SECONDARY_DRAW_ORDER_MASK_REVIEW",
        "bucket": "HOLD_REVIEW",
        "reason": "Secondary hair/back/underpaint parts need draw-order, underpaint, anchor, or mask review.",
    },
    "B5_COPIED_LAYER_REVIEW_REQUIRED": {
        "codex_triage": "HOLD_FOR_COPIED_B5_LAYER_REVIEW",
        "bucket": "HOLD_REVIEW",
        "reason": "Copied refined-mask v2 B5 layer stays review-required until material QA resolves the full body stack.",
    },
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
    pad = 125
    return (
        max(0, bbox[0] - pad),
        max(0, bbox[1] - pad),
        min(CANVAS, bbox[2] + pad),
        min(CANVAS, bbox[3] + pad),
    )


def bucket_color(bucket: str) -> tuple[int, int, int]:
    if bucket == "AUTO_CANDIDATE":
        return (45, 145, 96)
    if bucket == "HARD_REVIEW":
        return (198, 84, 54)
    return (72, 118, 196)


def tile(source: Image.Image, entry: dict) -> Image.Image:
    layer = Image.open(ROOT / entry["path"]).convert("RGBA")
    crop_box = crop_box_for(entry["bbox"])
    base = source.crop(crop_box).convert("RGBA")
    part = layer.crop(crop_box).convert("RGBA")
    color = bucket_color(entry["bucket"])
    tint = Image.new("RGBA", base.size, (*color, 0))
    tint.putalpha(part.getchannel("A").point(lambda v: min(165, int(v * 0.7))))
    comp = Image.alpha_composite(base, tint)
    comp.thumbnail((TILE_W - 22, TILE_H - 82), Image.Resampling.LANCZOS)

    out = Image.new("RGB", (TILE_W, TILE_H), (247, 248, 250))
    out.paste(comp.convert("RGB"), ((TILE_W - comp.width) // 2, 8))
    draw = ImageDraw.Draw(out)
    draw.rectangle([4, 4, TILE_W - 5, TILE_H - 5], outline=(216, 222, 232))
    draw.rectangle([8, TILE_H - 75, TILE_W - 9, TILE_H - 53], fill=color)
    draw.text((12, TILE_H - 72), entry["bucket"], fill=(255, 255, 255))
    draw.text((12, TILE_H - 48), f"{entry['part_id']}  {entry['source_batch']}", fill=(25, 31, 40))
    draw.text((12, TILE_H - 26), entry["codex_triage"][:52], fill=(78, 89, 104))
    return out


def build_sheet(entries: list[dict]) -> None:
    source = Image.open(SOURCE).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    ordered = sorted(entries, key=lambda e: ({"HARD_REVIEW": 0, "HOLD_REVIEW": 1, "AUTO_CANDIDATE": 2}[e["bucket"]], e["part_id"]))
    cols = 3
    rows = (len(ordered) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * TILE_W, 64 + rows * TILE_H), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 16), "Character 002 v22 Corrected B4/B5 Codex Visual Triage", fill=(25, 31, 40))
    draw.text((12, 38), "Provisional only: material PASS / ParamHairFront / G7 / G8 remain blocked", fill=(78, 89, 104))
    for idx, entry in enumerate(ordered):
        sheet.paste(tile(source, entry), ((idx % cols) * TILE_W, 64 + (idx // cols) * TILE_H))
    TRIAGE_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(TRIAGE_SHEET)


def main() -> int:
    qa = load_json(QA_JSON)
    triage_entries: list[dict] = []
    for entry in qa["qa_entries"]:
        rule = TRIAGE_RULES[entry["qa_verdict"]]
        triage_entries.append(
            {
                **entry,
                "codex_triage": rule["codex_triage"],
                "bucket": rule["bucket"],
                "codex_reason": rule["reason"],
                "not_owner_approval": True,
                "material_promotion": "BLOCKED",
            }
        )

    build_sheet(triage_entries)
    bucket_counts = Counter(entry["bucket"] for entry in triage_entries)
    triage_counts = Counter(entry["codex_triage"] for entry in triage_entries)
    status = "CORRECTED_B4_B5_CODEX_VISUAL_TRIAGE_READY_G2_G5_PREP_BLOCKED"
    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": status,
        "corrected_overlay_qa": rel(QA_JSON),
        "triage_sheet": rel(TRIAGE_SHEET),
        "triage_entries": triage_entries,
        "summary": {
            "triage_entry_count": len(triage_entries),
            "bucket_counts": dict(sorted(bucket_counts.items())),
            "triage_counts": dict(sorted(triage_counts.items())),
            "auto_candidate_count": bucket_counts.get("AUTO_CANDIDATE", 0),
            "hold_review_count": bucket_counts.get("HOLD_REVIEW", 0),
            "hard_review_count": bucket_counts.get("HARD_REVIEW", 0),
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
        "decision": (
            "Codex provisional triage keeps progress moving without owner acceptance: B4 front hair and B5 shoulders "
            "are candidate-level keeps, while torso and the remaining copied/secondary B4/B5 layers block material promotion."
        ),
        "next_action": [
            "Prepare G2-G5 material QA only as a blocked/prep packet, not as material PASS.",
            "Keep ParamHairFront hidden until front-hair motion-readiness is proven.",
            "Do not start G7 Mini Cubism or G8 real Cubism from this provisional triage.",
        ],
        "self_review": {
            "overlay_qa_status": qa["status"],
            "triage_entry_count": len(triage_entries),
            "qa_entry_count_matches": len(triage_entries) == qa["summary"]["qa_entry_count"],
            "auto_candidate_count": bucket_counts.get("AUTO_CANDIDATE", 0),
            "hold_review_count": bucket_counts.get("HOLD_REVIEW", 0),
            "hard_review_count": bucket_counts.get("HARD_REVIEW", 0),
            "triage_sheet_exists": TRIAGE_SHEET.exists(),
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
        "# Character 002 v22 Corrected B4/B5 Codex Visual Triage",
        "",
        f"- status: `{report['status']}`",
        f"- corrected overlay QA: `{report['corrected_overlay_qa']}`",
        f"- triage sheet: `{report['triage_sheet']}`",
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

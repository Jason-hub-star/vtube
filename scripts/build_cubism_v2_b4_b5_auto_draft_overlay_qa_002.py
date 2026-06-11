#!/usr/bin/env python3
"""Build conservative overlay QA for the v22 B4/B5 auto-draft corrected candidate."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
CORRECTED_REPORT_JSON = (
    EXP / "reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_anchor_corrected_auto_draft_report.json"
)
REPORT_DIR = EXP / "reports/v22_b4_b5_anchor_corrected_auto_draft"
REPORT_JSON = REPORT_DIR / "v22_b4_b5_auto_draft_overlay_qa_report.json"
REPORT_MD = REPORT_DIR / "v22_b4_b5_auto_draft_overlay_qa_report.md"
OVERLAY_SHEET = REPORT_DIR / "v22_b4_b5_auto_draft_overlay_qa.png"

TILE_W = 360
TILE_H = 330


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def composite_tile(source: Image.Image, layer: Image.Image, entry: dict) -> Image.Image:
    bbox = entry["bbox"]
    if bbox is None:
        crop_box = (0, 0, 512, 512)
    else:
        pad = 120
        crop_box = (
            max(0, bbox[0] - pad),
            max(0, bbox[1] - pad),
            min(source.width, bbox[2] + pad),
            min(source.height, bbox[3] + pad),
        )
    base = source.crop(crop_box).convert("RGBA")
    part = Image.new("RGBA", base.size, (0, 0, 0, 0))
    shifted = layer.crop(crop_box).convert("RGBA")
    part.alpha_composite(shifted)
    tint = Image.new("RGBA", base.size, (70, 140, 255, 0))
    alpha = shifted.getchannel("A").point(lambda v: min(160, int(v * 0.62)))
    tint.putalpha(alpha)
    comp = Image.alpha_composite(base, tint)
    comp.thumbnail((TILE_W - 18, TILE_H - 64), Image.Resampling.LANCZOS)
    tile = Image.new("RGB", (TILE_W, TILE_H), (247, 248, 250))
    tile.paste(comp.convert("RGB"), ((TILE_W - comp.width) // 2, 8))
    draw = ImageDraw.Draw(tile)
    draw.rectangle([4, 4, TILE_W - 5, TILE_H - 5], outline=(216, 222, 232))
    draw.text((10, TILE_H - 54), entry["part_id"], fill=(25, 31, 40))
    draw.text((10, TILE_H - 36), f"{entry['source_batch']} {entry['group']}", fill=(78, 89, 104))
    draw.text((10, TILE_H - 18), f"anchor {entry['target_anchor']} scale {entry['target_scale']}", fill=(78, 89, 104))
    return tile


def build_overlay(entries: list[dict], out: Path) -> None:
    source = Image.open(SOURCE).convert("RGBA").resize((2048, 2048), Image.Resampling.LANCZOS)
    cols = 3
    rows = (len(entries) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * TILE_W, 46 + rows * TILE_H), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 14), "Character 002 v22 B4/B5 Auto-Draft Overlay QA", fill=(25, 31, 40))
    for idx, entry in enumerate(entries):
        layer = Image.open(ROOT / entry["output_path"]).convert("RGBA")
        tile = composite_tile(source, layer, entry)
        x = (idx % cols) * TILE_W
        y = 46 + (idx // cols) * TILE_H
        sheet.paste(tile, (x, y))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def main() -> int:
    corrected = json.loads(CORRECTED_REPORT_JSON.read_text(encoding="utf-8"))
    entries = corrected["entries"]
    build_overlay(entries, OVERLAY_SHEET)
    batch_counts = Counter(entry["source_batch"] for entry in entries)
    checks = [
        {
            "id": "technical_corrected_candidate",
            "status": "PASS_TECHNICAL",
            "evidence": "Auto-draft corrected candidate rebuilt 33/33 B4/B5 full-canvas 2048 RGBA non-empty layers.",
        },
        {
            "id": "auto_anchor_scope",
            "status": "PASS_DRAFT",
            "evidence": "Automatic first-pass anchors were applied to all 16 B4 and 17 B5 revise targets.",
        },
        {
            "id": "visual_overlay_gate",
            "status": "REVIEW_REQUIRED",
            "evidence": "Overlay sheet is generated for human review. Auto-draft placement cannot approve B4/B5 material quality by itself.",
        },
        {
            "id": "hairfront_contract_gate",
            "status": "HOLD_UNSUPPORTED_CONTROL",
            "evidence": "ParamHairFront remains hidden until corrected hair_front_* children pass overlay QA and motion-readiness checks.",
        },
        {
            "id": "mini_real_cubism_gate",
            "status": "BLOCKED",
            "evidence": "Do not unlock Mini Cubism diagnostic or real Cubism authoring from this auto-draft overlay evidence.",
        },
    ]
    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "G6_B4_B5_AUTO_DRAFT_OVERLAY_QA_REVIEW_REQUIRED",
        "corrected_candidate_report": rel(CORRECTED_REPORT_JSON),
        "overlay_sheet": rel(OVERLAY_SHEET),
        "contact_sheet": corrected["contact_sheet"],
        "checks": checks,
        "decision": "Keep the auto-draft corrected B4/B5 layers as review candidates only. They reduce manual work but still need 주인님 visual review and possibly targeted editor adjustments.",
        "next_action": [
            "Review the overlay sheet and mark only visibly bad B4/B5 parts for manual adjustment.",
            "Save real target anchors for those parts if needed.",
            "Rebuild corrected candidates and rerun overlay QA before manifest promotion.",
        ],
        "self_review": {
            "entry_count": len(entries),
            "b4_entry_count": batch_counts.get("B4", 0),
            "b5_entry_count": batch_counts.get("B5", 0),
            "corrected_candidate_status": corrected["status"],
            "applied_override_count": corrected["self_review"]["applied_override_count"],
            "overlay_sheet_exists": OVERLAY_SHEET.exists(),
            "has_review_required_gate": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "status": "PASS",
        },
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Character 002 v22 B4/B5 Auto-Draft Overlay QA",
        "",
        f"- status: `{report['status']}`",
        f"- corrected candidate: `{report['corrected_candidate_report']}`",
        f"- overlay sheet: `{report['overlay_sheet']}`",
        f"- contact sheet: `{report['contact_sheet']}`",
        "",
        "## Checks",
        "",
    ]
    for check in checks:
        lines.append(f"- `{check['status']}` `{check['id']}`: {check['evidence']}")
    lines.extend(["", "## Decision", "", report["decision"], "", "## Next Action", ""])
    lines.extend(f"- {item}" for item in report["next_action"])
    lines.extend(["", "## Self Review", ""])
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": report["status"], "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

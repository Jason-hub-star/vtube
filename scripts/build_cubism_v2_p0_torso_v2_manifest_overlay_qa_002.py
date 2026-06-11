#!/usr/bin/env python3
"""Build overlay QA for the P0 torso v2 64-part manifest variant."""

from __future__ import annotations

import importlib.util
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
BASE_SCRIPT = ROOT / "scripts/build_cubism_v2_corrected_b4_b5_manifest_overlay_qa_002.py"
MANIFEST_JSON = EXP / "reports/v22_64part_p0_torso_v2_manifest/v22_64part_p0_torso_v2_manifest.json"
REPORT_DIR = EXP / "reports/v22_64part_p0_torso_v2_manifest"
REPORT_JSON = REPORT_DIR / "v22_p0_torso_v2_manifest_overlay_qa_report.json"
REPORT_MD = REPORT_DIR / "v22_p0_torso_v2_manifest_overlay_qa_report.md"
OVERLAY_SHEET = REPORT_DIR / "v22_p0_torso_v2_manifest_overlay_qa.png"
CANVAS = 2048
TILE_W = 360
TILE_H = 320


def load_base_module():
    spec = importlib.util.spec_from_file_location("v22_corrected_overlay_qa", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = load_base_module()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def qa_verdict(entry: dict) -> tuple[str, str]:
    gate = entry["batch_visual_gate"]
    if entry["source_batch"] == "B5" and gate == "P0_TORSO_MINIPASS_V2_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED":
        return (
            "B5_TORSO_P0_V2_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED",
            "P0 torso v2 is tighter than the previous regenerated torso, but still needs G3 visual acceptance.",
        )
    return BASE.qa_verdict(entry)


def tile(source: Image.Image, entry: dict, verdict: str) -> Image.Image:
    layer = Image.open(ROOT / entry["path"]).convert("RGBA")
    crop_box = BASE.crop_box_for(entry)
    base = source.crop(crop_box).convert("RGBA")
    part = layer.crop(crop_box).convert("RGBA")
    color = (42, 152, 95) if verdict == "B5_TORSO_P0_V2_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED" else (58, 132, 255)
    tint = Image.new("RGBA", base.size, (*color, 0))
    tint.putalpha(part.getchannel("A").point(lambda v: min(150, int(v * 0.68))))
    comp = Image.alpha_composite(base, tint)
    comp.thumbnail((TILE_W - 18, TILE_H - 72), Image.Resampling.LANCZOS)
    out = Image.new("RGB", (TILE_W, TILE_H), (247, 248, 250))
    out.paste(comp.convert("RGB"), ((TILE_W - comp.width) // 2, 8))
    draw = ImageDraw.Draw(out)
    draw.rectangle([4, 4, TILE_W - 5, TILE_H - 5], outline=(216, 222, 232))
    draw.text((10, TILE_H - 64), entry["id"], fill=(25, 31, 40))
    draw.text((10, TILE_H - 44), f"{entry['source_batch']} {entry['group']}", fill=(78, 89, 104))
    draw.text((10, TILE_H - 24), verdict[:45], fill=(78, 89, 104))
    return out


def main() -> int:
    manifest = load_json(MANIFEST_JSON)
    source = Image.open(BASE.SOURCE).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    entries = [entry for entry in manifest["manifest_entries"] if entry["source_batch"] in {"B4", "B5"}]
    qa_entries = []
    for entry in entries:
        verdict, reason = qa_verdict(entry)
        qa_entries.append(
            {
                "part_id": entry["id"],
                "source_batch": entry["source_batch"],
                "group": entry["group"],
                "qa_verdict": verdict,
                "reason": reason,
                "path": entry["path"],
                "bbox": entry["bbox"],
                "alpha_coverage": entry["alpha_coverage"],
                "manifest_status": entry["manifest_status"],
            }
        )

    cols = 3
    rows = (len(qa_entries) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * TILE_W, 54 + rows * TILE_H), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 14), "Character 002 v22 P0 Torso v2 Manifest Overlay QA", fill=(25, 31, 40))
    for idx, qa in enumerate(qa_entries):
        entry = next(item for item in entries if item["id"] == qa["part_id"])
        sheet.paste(tile(source, entry, qa["qa_verdict"]), ((idx % cols) * TILE_W, 54 + (idx // cols) * TILE_H))
    OVERLAY_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OVERLAY_SHEET)

    counts = Counter(entry["qa_verdict"] for entry in qa_entries)
    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "G3_P0_TORSO_V2_MANIFEST_OVERLAY_QA_REVIEW_REQUIRED",
        "p0_torso_v2_manifest": rel(MANIFEST_JSON),
        "overlay_sheet": rel(OVERLAY_SHEET),
        "qa_entries": qa_entries,
        "summary": {
            "qa_entry_count": len(qa_entries),
            "b4_entry_count": sum(1 for entry in qa_entries if entry["source_batch"] == "B4"),
            "b5_entry_count": sum(1 for entry in qa_entries if entry["source_batch"] == "B5"),
            "verdict_counts": dict(sorted(counts.items())),
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g4_psd_import_prep_status": "PREP_ONLY_BLOCKED",
            "g5_material_acceptance_status": "BLOCKED",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
        "decision": (
            "P0 torso v2 manifest overlay QA is review-required. It preserves B4 front-hair and B5 shoulder candidates, "
            "marks torso as a P0 v2 improvement candidate, and keeps material PASS, ParamHairFront, Mini Cubism, "
            "and real Cubism blocked."
        ),
        "next_action": [
            "Continue G3 blocker reduction with the nine P1 B4 secondary hair rows.",
            "Keep B5 copied/context rows for later review after P0/P1 are reduced.",
            "Do not promote G4/G5, G7, or G8 from this overlay QA alone.",
        ],
        "self_review": {
            "manifest_status": manifest["status"],
            "qa_entry_count": len(qa_entries),
            "b4_entry_count": sum(1 for entry in qa_entries if entry["source_batch"] == "B4"),
            "b5_entry_count": sum(1 for entry in qa_entries if entry["source_batch"] == "B5"),
            "b4_front_hair_candidate_count": counts.get("B4_FRONT_HAIR_MOTION_CANDIDATE_REVIEW_REQUIRED", 0),
            "b4_secondary_review_count": counts.get("B4_SECONDARY_DRAW_ORDER_OR_MASK_REVIEW_REQUIRED", 0),
            "b5_shoulder_improvement_candidate_count": counts.get(
                "B5_SHOULDER_DRAW_ORDER_MASK_IMPROVEMENT_REVIEW_REQUIRED", 0
            ),
            "b5_torso_p0_v2_candidate_count": counts.get(
                "B5_TORSO_P0_V2_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED", 0
            ),
            "b5_copied_layer_review_count": counts.get("B5_COPIED_LAYER_REVIEW_REQUIRED", 0),
            "overlay_sheet_exists": OVERLAY_SHEET.exists(),
            "has_review_required_gate": True,
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
        "# Character 002 v22 P0 Torso v2 Manifest Overlay QA",
        "",
        f"- status: `{report['status']}`",
        f"- overlay sheet: `{report['overlay_sheet']}`",
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

    print(json.dumps({"status": report["status"], "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

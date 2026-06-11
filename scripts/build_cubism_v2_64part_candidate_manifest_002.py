#!/usr/bin/env python3
"""Build the v22 64-part candidate manifest from B1-B5 evidence.

This is a G1 completeness manifest, not material approval. It deliberately
preserves visual gate states such as B4/B5 overlay REVISE and keeps Mini Cubism
and real Cubism success separate.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SPEC_JSON = EXP / "reports/v22_64part_generation_spec/v22_64part_generation_spec.json"
G0_JSON = EXP / "reports/v22_64part_generation_input_packet/v22_g0_existing_source_review.json"
REPORT_DIR = EXP / "reports/v22_64part_candidate_manifest"
REPORT_JSON = REPORT_DIR / "v22_64part_candidate_manifest.json"
REPORT_MD = REPORT_DIR / "v22_64part_candidate_manifest.md"
CONTACT_SHEET = REPORT_DIR / "v22_64part_candidate_manifest_contact_sheet.png"
CANVAS = 2048

BATCH_REPORTS = {
    "B1": {
        "layer_report": EXP / "reports/v22_b1_clean_base_underpaint/v22_b1_layer_pack_report.json",
        "visual_report": EXP / "reports/v22_b1_clean_base_underpaint/v22_b1_visual_qa_report.json",
        "layer_dir": EXP / "v22_b1_clean_base_underpaint/normalized_layers",
        "visual_gate": "PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED",
    },
    "B2": {
        "layer_report": EXP / "reports/v22_b2_eye_pack/v22_b2_layer_pack_report.json",
        "visual_report": EXP / "reports/v22_b2_eye_pack/v22_b2_overlay_qa_report.json",
        "layer_dir": EXP / "v22_b2_eye_pack/normalized_layers",
        "visual_gate": "PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED",
    },
    "B3_REVISION_V1": {
        "layer_report": EXP / "reports/v22_b3_mouth_pack_revision_v1/v22_b3_revision_v1_layer_pack_report.json",
        "visual_report": EXP / "reports/v22_b3_mouth_pack_revision_v1/v22_b3_revision_v1_overlay_qa_report.json",
        "layer_dir": EXP / "v22_b3_mouth_pack_revision_v1/normalized_layers",
        "visual_gate": "PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED",
    },
    "B4": {
        "layer_report": EXP / "reports/v22_b4_hair_pack/v22_b4_layer_pack_report.json",
        "visual_report": EXP / "reports/v22_b4_hair_pack/v22_b4_overlay_qa_report.json",
        "layer_dir": EXP / "v22_b4_hair_pack/normalized_layers",
        "visual_gate": "REVISE_ANCHOR_OR_EXTRACTION",
    },
    "B5": {
        "layer_report": EXP / "reports/v22_b5_body_clothing_pack/v22_b5_layer_pack_report.json",
        "visual_report": EXP / "reports/v22_b5_body_clothing_pack/v22_b5_overlay_qa_report.json",
        "layer_dir": EXP / "v22_b5_body_clothing_pack/normalized_layers",
        "visual_gate": "REVISE_ANCHOR_OR_EXTRACTION",
    },
}

PART_SOURCE_BATCH = {
    # B1 clean bases and underpaints.
    "body_underpaint": "B1",
    "neck_shadow_underpaint": "B1",
    "arm_L_underpaint": "B1",
    "arm_R_underpaint": "B1",
    "face_base": "B1",
    "face_underpaint_L": "B1",
    "face_underpaint_R": "B1",
    "eye_L_underpaint": "B1",
    "eye_R_underpaint": "B1",
    # B2 eyes.
    "eye_L_white": "B2",
    "eye_L_iris": "B2",
    "eye_L_pupil": "B2",
    "eye_L_highlight": "B2",
    "eye_L_upper_lash": "B2",
    "eye_L_lower_lash": "B2",
    "eye_L_closed_lid": "B2",
    "eye_R_white": "B2",
    "eye_R_iris": "B2",
    "eye_R_pupil": "B2",
    "eye_R_highlight": "B2",
    "eye_R_upper_lash": "B2",
    "eye_R_lower_lash": "B2",
    "eye_R_closed_lid": "B2",
    # B3 mouth revision v1.
    "mouth_line": "B3_REVISION_V1",
    "mouth_inner": "B3_REVISION_V1",
    "mouth_upper_lip_mask": "B3_REVISION_V1",
    "mouth_lower_lip_mask": "B3_REVISION_V1",
    "mouth_teeth": "B3_REVISION_V1",
    "mouth_tongue": "B3_REVISION_V1",
    "mouth_corner_L": "B3_REVISION_V1",
    "mouth_corner_R": "B3_REVISION_V1",
    # B4 hair.
    "hair_back_base": "B4",
    "hair_back_underpaint": "B4",
    "hair_back_strand_L": "B4",
    "hair_back_strand_R": "B4",
    "hair_back_center": "B4",
    "hair_front_center": "B4",
    "hair_front_L": "B4",
    "hair_front_R": "B4",
    "hair_front_side_L": "B4",
    "hair_front_side_R": "B4",
    "hair_front_tip_L": "B4",
    "hair_front_tip_R": "B4",
    "hair_side_L_outer": "B4",
    "hair_side_L_inner": "B4",
    "hair_side_R_outer": "B4",
    "hair_side_R_inner": "B4",
    # B5 body, clothing, brow, and face details.
    "torso_base": "B5",
    "neck": "B5",
    "shoulder_L": "B5",
    "shoulder_R": "B5",
    "arm_L_upper_simple": "B5",
    "arm_R_upper_simple": "B5",
    "collar_front": "B5",
    "collar_shadow": "B5",
    "chest_cloth_base": "B5",
    "chest_cloth_shadow": "B5",
    "brow_L": "B5",
    "brow_R": "B5",
    "nose": "B5",
    "cheek_L": "B5",
    "cheek_R": "B5",
    "face_shadow_L": "B5",
    "face_shadow_R": "B5",
}

VISUAL_GATE_BY_BATCH = {
    "B1": "PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED",
    "B2": "PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED",
    "B3_REVISION_V1": "PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED",
    "B4": "REVISE_ANCHOR_OR_EXTRACTION",
    "B5": "REVISE_ANCHOR_OR_EXTRACTION",
}


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def alpha_coverage(path: Path) -> float:
    img = Image.open(path).convert("RGBA")
    arr = np.asarray(img.getchannel("A"), dtype=np.uint8)
    return float((arr > 5).mean())


def bbox_from_alpha(path: Path) -> list[int] | None:
    img = Image.open(path).convert("RGBA")
    arr = np.asarray(img.getchannel("A"), dtype=np.uint8)
    ys, xs = np.where(arr > 5)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def image_mode_size(path: Path) -> tuple[str, list[int]]:
    img = Image.open(path)
    return img.mode, list(img.size)


def build_manifest() -> dict:
    spec = load_json(SPEC_JSON)
    g0 = load_json(G0_JSON)
    batch_status = {}
    for batch_id, cfg in BATCH_REPORTS.items():
        layer_report = load_json(cfg["layer_report"])
        visual_report = load_json(cfg["visual_report"])
        batch_status[batch_id] = {
            "layer_report": rel(cfg["layer_report"]),
            "layer_status": layer_report["status"],
            "layer_self_review_status": layer_report.get("self_review", {}).get("status"),
            "visual_report": rel(cfg["visual_report"]),
            "visual_status": visual_report["status"],
            "visual_self_review_status": visual_report.get("self_review", {}).get("status"),
            "visual_gate": cfg["visual_gate"],
        }

    entries = []
    missing = []
    wrong_mode = []
    wrong_size = []
    empty = []
    for part in spec["parts"]:
        part_id = part["id"]
        batch_id = PART_SOURCE_BATCH.get(part_id)
        if not batch_id:
            missing.append(part_id)
            entries.append({**part, "manifest_status": "MISSING_SOURCE_BATCH"})
            continue
        layer_path = BATCH_REPORTS[batch_id]["layer_dir"] / f"{part_id}.png"
        exists = layer_path.exists()
        mode = None
        size = None
        bbox = None
        coverage = 0.0
        if exists:
            mode, size = image_mode_size(layer_path)
            bbox = bbox_from_alpha(layer_path)
            coverage = round(alpha_coverage(layer_path), 8)
            if mode != "RGBA":
                wrong_mode.append(part_id)
            if size != [CANVAS, CANVAS]:
                wrong_size.append(part_id)
            if bbox is None:
                empty.append(part_id)
        else:
            missing.append(part_id)
        visual_gate = VISUAL_GATE_BY_BATCH[batch_id]
        part_status = "TECHNICAL_PRESENT_VISUAL_REVISE" if visual_gate.startswith("REVISE") else "TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED"
        if not exists or mode != "RGBA" or size != [CANVAS, CANVAS] or bbox is None:
            part_status = "TECHNICAL_INCOMPLETE"
        entries.append(
            {
                **part,
                "source_batch": batch_id,
                "path": rel(layer_path) if exists else None,
                "exists": exists,
                "mode": mode,
                "size": size,
                "bbox": bbox,
                "alpha_coverage": coverage,
                "batch_visual_gate": visual_gate,
                "manifest_status": part_status,
            }
        )

    group_counts = Counter(entry["group"] for entry in entries if entry.get("exists"))
    required_group_counts = spec["part_groups"]
    visual_gate_counts = Counter(entry.get("batch_visual_gate", "UNKNOWN") for entry in entries)
    status_counts = Counter(entry["manifest_status"] for entry in entries)
    duplicate_ids = [part_id for part_id, count in Counter(entry["id"] for entry in entries).items() if count > 1]
    complete_technical = not missing and not wrong_mode and not wrong_size and not empty and not duplicate_ids
    has_revise_parts = any(entry["manifest_status"] == "TECHNICAL_PRESENT_VISUAL_REVISE" for entry in entries)

    return {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest_id": "cubism-v2-new-character-002-v22-64part-candidate-manifest-001",
        "status": "G1_64PART_MANIFEST_COMPLETE_TECHNICAL_PASS_VISUAL_REVISE_BLOCKED"
        if complete_technical and has_revise_parts
        else "G1_64PART_MANIFEST_REVISE_TECHNICAL_INCOMPLETE",
        "spec": rel(SPEC_JSON),
        "g0_source_review": rel(G0_JSON),
        "g0_status": g0["status"],
        "canvas": [CANVAS, CANVAS],
        "batch_status": batch_status,
        "manifest_entries": entries,
        "quality_gate_interpretation": {
            "g1_64part_completeness": "PASS_TECHNICAL" if complete_technical else "REVISE_TECHNICAL",
            "g2_full_canvas_rgba": "PASS_TECHNICAL" if not wrong_mode and not wrong_size and not empty else "REVISE_TECHNICAL",
            "g4_g5_visual_overlay": "BLOCKED_REVISE" if has_revise_parts else "PASS_CANDIDATE_HUMAN_REQUIRED",
            "g6_manual_anchor_correction": "REQUIRED_FOR_B4_B5",
            "g7_mini_cubism_diagnostic": "BLOCKED_UNTIL_VISUAL_QA_ACCEPTS_B1_B5",
            "g8_real_cubism_authoring": "BLOCKED_UNTIL_MATERIAL_QA_AND_HUMAN_REVIEW",
            "param_hair_front": "HIDDEN_CONTRACT_ONLY",
        },
        "self_review": {
            "required_part_count": len(spec["parts"]),
            "manifest_entry_count": len(entries),
            "unique_manifest_part_count": len({entry["id"] for entry in entries}),
            "missing_part_count": len(missing),
            "wrong_mode_count": len(wrong_mode),
            "wrong_size_count": len(wrong_size),
            "empty_part_count": len(empty),
            "duplicate_part_count": len(duplicate_ids),
            "group_counts": dict(group_counts),
            "required_group_counts": required_group_counts,
            "group_counts_match_spec": dict(group_counts) == required_group_counts,
            "visual_gate_counts": dict(visual_gate_counts),
            "status_counts": dict(status_counts),
            "has_b4_revise_parts": any(entry["source_batch"] == "B4" and entry["manifest_status"].endswith("REVISE") for entry in entries),
            "has_b5_revise_parts": any(entry["source_batch"] == "B5" and entry["manifest_status"].endswith("REVISE") for entry in entries),
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "status": "PASS" if complete_technical and has_revise_parts else "REVISE",
        },
        "decision": "The v22 64 required part IDs are technically present as 2048 RGBA candidates, but B4 and B5 overlay QA are REVISE. Do not promote to material PASS, Mini Cubism diagnostics, or real Cubism authoring.",
        "next_action": [
            "Refine B4/B5 anchors or crop assignments, or run manual anchor correction for visually misaligned parts.",
            "Keep ParamHairFront hidden until corrected hair_front_* children pass overlay QA.",
            "After B1-B5 visual QA and 주인님 review accept corrected parts, rebuild this manifest and proceed to G2-G5 material QA.",
        ],
    }


def draw_contact_sheet(manifest: dict) -> None:
    entries = manifest["manifest_entries"]
    cols = 8
    thumb = 210
    label_h = 66
    rows = math.ceil(len(entries) / cols)
    sheet = Image.new("RGB", (cols * thumb, rows * (thumb + label_h)), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, entry in enumerate(entries):
        row, col = divmod(idx, cols)
        x = col * thumb
        y = row * (thumb + label_h)
        fill = (230, 245, 230) if "PASS_CANDIDATE" in entry["manifest_status"] else (255, 235, 220)
        draw.rectangle((x, y, x + thumb, y + label_h), fill=fill)
        draw.text((x + 5, y + 5), entry["id"][:28], fill=(20, 20, 20))
        draw.text((x + 5, y + 24), entry["source_batch"], fill=(50, 50, 50))
        draw.text((x + 5, y + 43), entry["batch_visual_gate"][:24], fill=(80, 60, 40))
        if entry.get("path"):
            img = Image.open(ROOT / entry["path"]).convert("RGBA")
            bg = Image.new("RGBA", (CANVAS, CANVAS), (244, 238, 226, 255))
            bg.alpha_composite(img)
            sheet.paste(bg.convert("RGB").resize((thumb, thumb), Image.Resampling.LANCZOS), (x, y + label_h))
        else:
            draw.rectangle((x, y + label_h, x + thumb, y + label_h + thumb), fill=(255, 210, 210))
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET)


def write_markdown(manifest: dict) -> None:
    lines = [
        "# Character 002 v22 64-Part Candidate Manifest",
        "",
        f"- status: `{manifest['status']}`",
        f"- spec: `{manifest['spec']}`",
        f"- G0 status: `{manifest['g0_status']}`",
        f"- contact sheet: `{rel(CONTACT_SHEET)}`",
        "",
        "## Gate Interpretation",
        "",
    ]
    for key, value in manifest["quality_gate_interpretation"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Batch Status", ""])
    for batch_id, status in manifest["batch_status"].items():
        lines.append(
            f"- `{batch_id}`: layer `{status['layer_status']}`, visual `{status['visual_status']}`, gate `{status['visual_gate']}`"
        )
    lines.extend(["", "## Manifest Summary", ""])
    for key, value in manifest["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Parts", ""])
    for entry in manifest["manifest_entries"]:
        lines.append(
            f"- `{entry['id']}` `{entry['group']}` `{entry['source_batch']}` `{entry['manifest_status']}` `{entry.get('path')}`"
        )
    lines.extend(["", "## Decision", "", manifest["decision"], "", "## Next Action", ""])
    lines.extend(f"- {item}" for item in manifest["next_action"])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    draw_contact_sheet(manifest)
    manifest["contact_sheet"] = rel(CONTACT_SHEET)
    REPORT_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(manifest)
    print(json.dumps({"status": manifest["status"], "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

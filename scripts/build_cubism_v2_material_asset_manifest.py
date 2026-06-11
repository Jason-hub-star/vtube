#!/usr/bin/env python3
"""Build the material asset manifest for candidate_002."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cubism_v2_material_asset_lib import (
    CANONICAL_2048,
    CANVAS,
    G1_PLAN,
    LAYER_MANIFEST_PATH,
    LAYERS_DIR,
    MANIFEST_PATH,
    MATERIAL_PACK,
    MERGED_DIR,
    PASTE_OFFSET,
    REPORTS,
    ROOT,
    SOURCE_CANDIDATE,
    band_order,
    canvas_bbox,
    create_subject_rgba,
    load_json,
    now_iso,
    rel,
    save_json,
    sha256,
    source_bbox,
)


SOURCE_BOXES: dict[str, list[int]] = {
    "body_underpaint": source_bbox(300, 900, 480, 420),
    "torso_base": source_bbox(285, 900, 540, 480),
    "neck": source_bbox(430, 760, 230, 185),
    "neck_shadow_underpaint": source_bbox(420, 800, 240, 160),
    "shoulder_L": source_bbox(140, 885, 390, 250),
    "shoulder_R": source_bbox(585, 885, 390, 250),
    "arm_L_upper_simple": source_bbox(115, 900, 260, 548),
    "arm_R_upper_simple": source_bbox(810, 900, 220, 548),
    "arm_L_underpaint": source_bbox(145, 925, 210, 460),
    "arm_R_underpaint": source_bbox(820, 925, 175, 460),
    "face_base": source_bbox(335, 365, 430, 455),
    "face_shadow_L": source_bbox(335, 445, 205, 300),
    "face_shadow_R": source_bbox(560, 445, 205, 300),
    "face_underpaint_L": source_bbox(335, 405, 205, 365),
    "face_underpaint_R": source_bbox(560, 405, 205, 365),
    "nose": source_bbox(520, 605, 60, 70),
    "cheek_L": source_bbox(355, 590, 95, 65),
    "cheek_R": source_bbox(650, 590, 95, 65),
    "eye_L_white": source_bbox(380, 505, 165, 95),
    "eye_L_iris": source_bbox(435, 520, 72, 75),
    "eye_L_pupil": source_bbox(455, 540, 36, 40),
    "eye_L_highlight": source_bbox(455, 525, 42, 42),
    "eye_L_upper_lash": source_bbox(370, 485, 180, 62),
    "eye_L_lower_lash": source_bbox(390, 570, 140, 45),
    "eye_L_closed_lid": source_bbox(375, 505, 170, 95),
    "eye_L_underpaint": source_bbox(382, 505, 155, 95),
    "eye_R_white": source_bbox(610, 505, 165, 95),
    "eye_R_iris": source_bbox(650, 520, 72, 75),
    "eye_R_pupil": source_bbox(670, 540, 36, 40),
    "eye_R_highlight": source_bbox(668, 525, 42, 42),
    "eye_R_upper_lash": source_bbox(600, 485, 180, 62),
    "eye_R_lower_lash": source_bbox(620, 570, 140, 45),
    "eye_R_closed_lid": source_bbox(605, 505, 170, 95),
    "eye_R_underpaint": source_bbox(612, 505, 155, 95),
    "brow_L": source_bbox(360, 450, 200, 58),
    "brow_R": source_bbox(590, 450, 200, 58),
    "mouth_line": source_bbox(458, 670, 185, 85),
    "mouth_inner": source_bbox(470, 680, 160, 88),
    "mouth_upper_lip_mask": source_bbox(466, 668, 168, 72),
    "mouth_lower_lip_mask": source_bbox(466, 695, 168, 70),
    "mouth_teeth": source_bbox(486, 692, 130, 36),
    "mouth_tongue": source_bbox(492, 716, 118, 44),
    "mouth_corner_L": source_bbox(438, 673, 80, 76),
    "mouth_corner_R": source_bbox(582, 673, 80, 76),
    "hair_back_base": source_bbox(170, 55, 760, 925),
    "hair_back_underpaint": source_bbox(205, 100, 690, 860),
    "hair_back_strand_L": source_bbox(175, 410, 230, 590),
    "hair_back_strand_R": source_bbox(700, 410, 230, 590),
    "hair_back_center": source_bbox(390, 60, 330, 830),
    "hair_front_center": source_bbox(405, 95, 275, 400),
    "hair_front_L": source_bbox(305, 140, 230, 420),
    "hair_front_R": source_bbox(560, 140, 230, 420),
    "hair_front_side_L": source_bbox(250, 240, 190, 560),
    "hair_front_side_R": source_bbox(655, 240, 190, 560),
    "hair_front_tip_L": source_bbox(285, 665, 180, 280),
    "hair_front_tip_R": source_bbox(625, 665, 180, 280),
    "hair_side_L_outer": source_bbox(175, 250, 235, 780),
    "hair_side_L_inner": source_bbox(300, 330, 165, 600),
    "hair_side_R_outer": source_bbox(700, 250, 235, 780),
    "hair_side_R_inner": source_bbox(630, 330, 165, 600),
    "collar_front": source_bbox(365, 920, 360, 150),
    "collar_shadow": source_bbox(350, 900, 390, 90),
    "chest_cloth_base": source_bbox(285, 985, 530, 335),
    "chest_cloth_shadow": source_bbox(255, 965, 585, 190),
}

REGENERATED_DETAIL_PARTS = {
    "eye_L_highlight",
    "eye_R_highlight",
    "mouth_line",
    "mouth_corner_L",
    "mouth_corner_R",
}


COLOR_CONDITIONS = {
    "hair": "hair",
    "face_base": "skin",
    "body": "skin",
    "brow": "dark",
    "mouth": "dark",
}


def section_rows(plan: dict[str, Any]) -> list[dict[str, Any]]:
    sections = plan["sections"]
    return (
        sections["direct_extraction_parts"]["safe"]
        + sections["direct_extraction_parts"]["risk"]
        + sections["auxiliary_generated_parts"]
        + sections["underpaint_parts"]
        + sections["simplify_or_merge_parts"]
    )


def mask_hint(row: dict[str, Any]) -> dict[str, Any]:
    part_id = row["part_id"]
    group = row["group"]
    hint: dict[str, Any] = {"mask_shape": "rect", "color_condition": None}
    if row["feasibility"] == "DERIVED_KEYPOSE_REQUIRED":
        hint["source_type"] = "DERIVED_KEYPOSE"
    elif row["feasibility"] == "UNDERPAINT_REQUIRED":
        hint["source_type"] = "UNDERPAINT"
    elif row["feasibility"] == "SIMPLIFY_OR_MERGE":
        hint["source_type"] = "MERGED_METADATA"
    elif part_id in REGENERATED_DETAIL_PARTS:
        hint["source_type"] = "DERIVED_KEYPOSE"
    else:
        hint["source_type"] = "SOURCE_CUT"

    if group == "hair":
        hint.update({"mask_shape": "rounded", "color_condition": "hair", "fallback_color": [125, 82, 82]})
    elif group in {"face_base", "body"}:
        hint.update({"mask_shape": "ellipse" if "face" in part_id else "rounded", "color_condition": "skin", "fallback_color": [239, 190, 170]})
    elif group in {"eye_L", "eye_R"}:
        hint.update({"mask_shape": "ellipse", "fallback_color": [246, 218, 210]})
        if any(token in part_id for token in ["upper_lash", "lower_lash"]):
            hint["color_condition"] = "dark"
        elif "white" in part_id or "highlight" in part_id:
            hint["color_condition"] = "light"
    elif group == "brow":
        hint.update({"mask_shape": "rounded", "color_condition": "dark", "fallback_color": [70, 39, 43]})
    elif group == "mouth":
        hint.update({"mask_shape": "rounded", "color_condition": "dark", "fallback_color": [120, 52, 61]})
    elif group == "clothing":
        hint.update({"mask_shape": "rounded", "color_condition": "light", "fallback_color": [247, 229, 218]})

    if part_id in {"cheek_L", "cheek_R"}:
        hint.update({"mask_shape": "ellipse", "color_condition": "pink", "fallback_color": [235, 153, 151]})
    if part_id.endswith("_underpaint") or row["feasibility"] == "UNDERPAINT_REQUIRED":
        hint["color_condition"] = None
    if part_id in {"eye_L_iris", "eye_R_iris", "eye_L_pupil", "eye_R_pupil"}:
        hint["color_condition"] = None
    return hint


def make_entry(row: dict[str, Any]) -> dict[str, Any]:
    part_id = row["part_id"]
    if part_id not in SOURCE_BOXES:
        raise KeyError(f"missing source bbox for {part_id}")
    src_bbox = SOURCE_BOXES[part_id]
    bbox = canvas_bbox(src_bbox)
    hint = mask_hint(row)
    include = hint["source_type"] != "MERGED_METADATA"
    base = {
        "part_id": part_id,
        "layer_name": f"{row['index']:02d}_{part_id}",
        "label_ko": row["label_ko"],
        "group": row["group"],
        "feasibility": row["feasibility"],
        "source_type": hint["source_type"],
        "source_bbox": src_bbox,
        "bbox": bbox.as_list(),
        "draw_order_band": row["draw_order_band"],
        "draw_order": band_order(row["draw_order_band"]) * 100 + row["index"],
        "deformer_node": row["deformer_node"],
        "parameters": row["parameters"],
        "physics_groups": row.get("physics_groups", []),
        "risk_tags": row["risk_tags"],
        "status": "DRAFT_PENDING_QA" if include else "MERGED_METADATA_ONLY",
        "include_in_import_psd": include,
        "output_path": rel(LAYERS_DIR / f"{row['index']:02d}_{part_id}.png") if include else None,
        "merged_into": None,
        "notes": row["material_action_ko"],
        **hint,
    }
    if not include:
        base["merged_into"] = "collar_front" if part_id == "collar_shadow" else "chest_cloth_base"
        base["metadata_path"] = rel(MERGED_DIR / f"{part_id}.json")
    return base


def build_manifest() -> dict[str, Any]:
    MATERIAL_PACK.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    MERGED_DIR.mkdir(parents=True, exist_ok=True)
    create_subject_rgba()
    plan = load_json(G1_PLAN)
    rows = section_rows(plan)
    entries = [make_entry(row) for row in rows]
    entries.sort(key=lambda item: item["draw_order"])
    generated = [entry for entry in entries if entry["include_in_import_psd"]]
    merged = [entry for entry in entries if not entry["include_in_import_psd"]]
    manifest = {
        "schema_version": 1,
        "generated_at": now_iso(),
        "experiment_id": "cubism-v2-new-character-001",
        "pack_id": "material_pack_v0",
        "status": "PASS_MANIFEST_READY",
        "source": {
            "candidate": rel(SOURCE_CANDIDATE),
            "source_sha256": sha256(SOURCE_CANDIDATE),
            "source_size": list(SOURCE_CANDIDATE and (1086, 1448)),
            "canvas_size": list(CANVAS),
            "paste_offset": list(PASTE_OFFSET),
            "canonical_2048": rel(CANONICAL_2048),
        },
        "inputs": {
            "g1_material_plan": rel(G1_PLAN),
        },
        "summary": {
            "taxonomy_parts": len(entries),
            "generated_layer_target": len(generated),
            "merged_metadata_target": len(merged),
            "expected_direct_or_risk": 46,
            "expected_auxiliary": 7,
            "expected_underpaint": 9,
            "expected_merge": 2,
        },
        "layers": entries,
    }
    save_json(MANIFEST_PATH, manifest)
    save_json(LAYER_MANIFEST_PATH, manifest)
    for entry in merged:
        save_json(ROOT / entry["metadata_path"], entry)
    save_json(
        REPORTS / "material_asset_manifest_report.json",
        {
            "status": manifest["status"],
            "manifest": rel(MANIFEST_PATH),
            "layer_manifest": rel(LAYER_MANIFEST_PATH),
            "summary": manifest["summary"],
        },
    )
    (REPORTS / "material_asset_manifest_report.md").write_text(
        "\n".join(
            [
                "# Cubism v2 Material Asset Manifest",
                "",
                f"- status: `{manifest['status']}`",
                f"- manifest: `{rel(MANIFEST_PATH)}`",
                f"- source: `{rel(SOURCE_CANDIDATE)}`",
                f"- canonical 2048: `{rel(CANONICAL_2048)}`",
                f"- taxonomy parts: `{len(entries)}`",
                f"- generated layer target: `{len(generated)}`",
                f"- merged metadata target: `{len(merged)}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    manifest = build_manifest()
    print(manifest["status"])
    print(MANIFEST_PATH)


if __name__ == "__main__":
    main()

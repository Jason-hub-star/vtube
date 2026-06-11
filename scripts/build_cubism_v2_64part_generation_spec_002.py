#!/usr/bin/env python3
"""Build the v22 64-part generation spec for character 002.

This is a planning/evidence artifact, not an image generation runner.
It locks the current v21 success pattern before expanding to a full
Live2D/Cubism v2_standard production part set.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PART_SPEC_PATH = (
    ROOT
    / "experiments/reference-model-structure-001/reports/"
    / "cubism_v2_new_model_v2_standard_part_spec.json"
)
OUT_DIR = (
    ROOT
    / "experiments/cubism-v2-new-character-002/reports/"
    / "v22_64part_generation_spec"
)


EXPECTED_COUNTS = {
    "body": 10,
    "face_base": 8,
    "eye_L": 8,
    "eye_R": 8,
    "brow": 2,
    "mouth": 8,
    "hair": 16,
    "clothing": 4,
}


SOURCE_REFS = {
    "project_status": "docs/status/PROJECT-STATUS.md",
    "material_pack_first_plan": "docs/ref/CUBISM-V2-MATERIAL-PACK-FIRST-GENERATION.md",
    "confirmed_64part_spec": str(PART_SPEC_PATH.relative_to(ROOT)),
    "v21_success_replay": (
        "experiments/cubism-v2-new-character-002/reports/"
        "model_edit_v21_supported_rig_smoke_preview/"
        "success_pattern_replay_v1/success_pattern_replay_report.md"
    ),
    "v21_clean_contact_sheet": (
        "experiments/cubism-v2-new-character-002/reports/"
        "model_edit_v21_supported_rig_smoke_preview/"
        "supported_pose_sweep_clean_replay_v2/"
        "v21_supported_pose_sweep_clean_contact_sheet.png"
    ),
    "manual_eye_anchor_overrides": (
        "experiments/cubism-v2-new-character-002/reports/"
        "model_edit_v19_generated_eye_preview/manual_eye_detail_anchor_v1/"
        "manual_eye_detail_anchor_overrides.json"
    ),
}


GENERATION_BATCHES = [
    {
        "id": "B0_source_identity",
        "purpose": "Lock one same-character source before any split asset is accepted.",
        "outputs": [
            "new_character_002_source_front",
            "source_palette_reference",
            "source_identity_notes",
        ],
        "rules": [
            "adult cute female character identity remains fixed across all following assets",
            "front or near-front upper-body pose with visible neck, shoulders, torso, eyes, mouth, and readable hair groups",
            "no labels, guides, text, props covering eyes/mouth/hair, or accessory changes between sheets",
        ],
    },
    {
        "id": "B1_clean_base_underpaint",
        "purpose": "Create clean bases at generation time instead of patching baked pixels later.",
        "outputs": [
            "face_base",
            "face_underpaint_L",
            "face_underpaint_R",
            "eye_L_underpaint",
            "eye_R_underpaint",
            "mouth_base_clean_reference",
            "body_underpaint",
            "neck_shadow_underpaint",
            "arm_L_underpaint",
            "arm_R_underpaint",
            "hair_back_underpaint",
        ],
        "rules": [
            "face_base has no open-eye, iris, pupil, eye-white, lash, mouth-line, teeth, or tongue remnants",
            "underpaint preserves skin/hair gradients and occlusion, with no rectangular patch boundary",
            "do not promote procedural cover patches or late mask surgery as production clean base",
        ],
    },
    {
        "id": "B2_eye_pack",
        "purpose": "Generate production eye parts and blink in-betweens as one coordinated eye packet.",
        "outputs": [
            "eye_L_white",
            "eye_L_iris",
            "eye_L_pupil",
            "eye_L_highlight",
            "eye_L_upper_lash",
            "eye_L_lower_lash",
            "eye_L_closed_lid",
            "eye_R_white",
            "eye_R_iris",
            "eye_R_pupil",
            "eye_R_highlight",
            "eye_R_upper_lash",
            "eye_R_lower_lash",
            "eye_R_closed_lid",
            "eye_open_reference",
            "eye_half_closed_reference",
            "eye_mostly_closed_reference",
            "eye_closed_reference",
        ],
        "rules": [
            "eye whites stay fixed for EyeBallX/Y; iris, pupil, and highlight move together from the same anchor",
            "split iris/pupil/highlight may pass only if they are generated as a coherent packet and anchor-locked",
            "if split details drift or create crossed eyes, fall back to a coherent iris-detail diagnostic asset and regenerate the production split",
            "EyeOpen visual clamp target starts from v21 pattern: natural close is around 0.27, not hard 0.0",
        ],
    },
    {
        "id": "B3_mouth_pack",
        "purpose": "Generate mouth rig parts as a coordinated smile-open material packet.",
        "outputs": [
            "mouth_line",
            "mouth_inner",
            "mouth_upper_lip_mask",
            "mouth_lower_lip_mask",
            "mouth_teeth",
            "mouth_tongue",
            "mouth_corner_L",
            "mouth_corner_R",
            "mouth_closed_smile_reference",
            "mouth_small_open_reference",
            "mouth_mid_teeth_reference",
            "mouth_wide_teeth_tongue_reference",
        ],
        "rules": [
            "teeth/tongue/inner must be drawn naturally inside the same mouth opening, not pasted as separate centered overlays",
            "wide-open reference must be proportion-limited; reject oversized round mouth shapes",
            "ParamMouthOpenY max remains visually clamped around 0.85 until a better mouth packet is approved",
            "ParamMouthForm is not active in v21 diagnostic unless a real production mouth-form set is generated",
        ],
    },
    {
        "id": "B4_hair_pack",
        "purpose": "Create independent front/back/side hair children so HairFront can become real.",
        "outputs": [
            "hair_back_base",
            "hair_back_strand_L",
            "hair_back_strand_R",
            "hair_back_center",
            "hair_front_center",
            "hair_front_L",
            "hair_front_R",
            "hair_front_side_L",
            "hair_front_side_R",
            "hair_front_tip_L",
            "hair_front_tip_R",
            "hair_side_L_outer",
            "hair_side_L_inner",
            "hair_side_R_outer",
            "hair_side_R_inner",
        ],
        "rules": [
            "ParamHairFront stays unsupported until real hair_front_* child parts exist and move independently",
            "front bangs must preserve face/eye occlusion consistency across clean base and eye packets",
            "side/back hair parts must leave underpaint coverage for angle and physics motion",
        ],
    },
    {
        "id": "B5_body_clothing_pack",
        "purpose": "Complete torso, neck, shoulder, arm, and clothing layers for standard body motion.",
        "outputs": [
            "torso_base",
            "neck",
            "shoulder_L",
            "shoulder_R",
            "arm_L_upper_simple",
            "arm_R_upper_simple",
            "collar_front",
            "collar_shadow",
            "chest_cloth_base",
            "chest_cloth_shadow",
            "brow_L",
            "brow_R",
            "nose",
            "cheek_L",
            "cheek_R",
            "face_shadow_L",
            "face_shadow_R",
        ],
        "rules": [
            "keep first v2_standard scope simple: no complex hands, large props, heavy effects, or rich vowel set",
            "nose must remain visible as its own subtle part; do not lose it during face cleanup",
            "body and clothing parts must support breath and body-angle motion without visible holes",
        ],
    },
    {
        "id": "B6_manifest_normalize_validate",
        "purpose": "Normalize and validate only after raw evidence is preserved.",
        "outputs": [
            "raw_outputs/",
            "normalized_layers/",
            "generation_manifest.json",
            "layer_manifest.json",
            "technical_validation_report.json",
            "contact_sheet.png",
            "overlay_qa_report.md",
            "manual_anchor_overrides.json",
        ],
        "rules": [
            "keep raw generated files; never delete rejected evidence",
            "normalize to full-canvas RGBA, default 2048x2048 unless the Cubism authoring plan explicitly chooses another allowed size",
            "all crop outputs need full-canvas placement plus ROI/anchor metadata",
        ],
    },
]


QUALITY_GATES = [
    {
        "id": "G0_source_identity",
        "status_to_reach": "PASS_READY_FOR_64PART_GENERATION",
        "checks": [
            "same character accepted by 주인님",
            "style/outfit accepted enough for production split",
            "hair, eyes, mouth, neck, shoulders, torso are readable",
        ],
    },
    {
        "id": "G1_64part_completeness",
        "status_to_reach": "PASS_64_PARTS_PRESENT",
        "checks": [
            "64 required part IDs present in manifest",
            "group counts match v2_standard spec",
            "no duplicate IDs or missing underpaint placeholders",
        ],
    },
    {
        "id": "G2_full_canvas_rgba",
        "status_to_reach": "PASS_NORMALIZED_FULL_CANVAS",
        "checks": [
            "each PNG is RGBA",
            "each layer has shared full-canvas dimensions",
            "non-empty alpha and bbox metadata exist",
        ],
    },
    {
        "id": "G3_technical_validators",
        "status_to_reach": "PASS_READY_FOR_VISUAL_QA",
        "checks": [
            "validate_cubism_v2_keypose_pngs.py passes for required keypose PNGs",
            "64-part manifest validator passes",
            "PSD input validator passes before import attempt",
        ],
    },
    {
        "id": "G4_contact_sheet_visual_qa",
        "status_to_reach": "PASS_HUMAN_VISUAL_QA_REQUIRED_OR_ACCEPTED",
        "checks": [
            "contact sheet shows no patch borders, baked residues, or identity drift",
            "eye size/location and mouth location are coherent",
            "mouth teeth/tongue/inner read naturally",
        ],
    },
    {
        "id": "G5_overlay_qa",
        "status_to_reach": "PASS_OVERLAY_QA_OR_REVISE",
        "checks": [
            "clean bases do not contain eye/mouth remnants",
            "closed-eye states do not reveal original open-eye pixels",
            "mouth open states do not reveal circular patch boundaries",
        ],
    },
    {
        "id": "G6_manual_anchor_correction",
        "status_to_reach": "PASS_ANCHOR_LOCKED_OR_REVISE",
        "checks": [
            "use drag/zoom editor when eye, mouth, or hair parts are visually misaligned",
            "save explicit override JSON with target anchors and applied deltas",
            "rebuild full-canvas layers from overrides, then rerun contact sheet",
        ],
    },
    {
        "id": "G7_mini_cubism_diagnostic",
        "status_to_reach": "PASS_DIAGNOSTIC_ONLY",
        "checks": [
            "Mini Cubism supported controls pass validator and pose sweep",
            "unsupported controls are hidden or marked contract-only",
            "diagnostic PASS is not promoted to real Cubism authoring success",
        ],
    },
    {
        "id": "G8_real_cubism_authoring_readiness",
        "status_to_reach": "READY_FOR_CUBISM_EDITOR_AUTHORING",
        "checks": [
            "PSD candidate uses psd-tools path and passes input validation",
            "actual Cubism Editor import smoke is captured",
            "CMO3 structure gate targets warp >=35, rotation >=8, keyform bindings >=120, physics groups >=4",
        ],
    },
]


SUCCESS_PATTERNS = [
    {
        "id": "same_character_material_pack_first",
        "signal": "source, clean bases, eyes, mouth, hair, and body are generated as one coordinated identity set",
        "distinguishes_from_failure": "not a pretty front image followed by late erasing/patching",
    },
    {
        "id": "clean_base_generated_not_patched",
        "signal": "face_base and underpaints have natural gradients and no baked eye/mouth pixels",
        "distinguishes_from_failure": "no rectangular skin patches or socket cover stains",
    },
    {
        "id": "eye_detail_anchor_locked",
        "signal": "eye whites are fixed; iris, pupil, and highlight share the same EyeBall delta and target anchor",
        "distinguishes_from_failure": "not partial original eye movement, moving whites, or split detail drift",
    },
    {
        "id": "mouth_generated_as_packet",
        "signal": "inner, teeth, tongue, lips, line, and corners belong to the same opening and scale",
        "distinguishes_from_failure": "not tiny centered mouth swaps or pasted helper overlays",
    },
    {
        "id": "real_hairfront_children",
        "signal": "hair_front_* parts exist and can move independently before ParamHairFront is shown",
        "distinguishes_from_failure": "not a fake slider with no moving front hair art",
    },
    {
        "id": "evidence_separation",
        "signal": "technical PASS, human visual PASS, Mini Cubism PASS, and Cubism structure PASS are recorded separately",
        "distinguishes_from_failure": "not treating validator or Mini Cubism preview as final production rig success",
    },
]


FAILURE_PATTERNS = [
    {
        "id": "late_patch_clean_base",
        "verdict": "FAIL_VISUAL_QA",
        "signals": ["rectangular skin boundary", "stain around sockets", "open-eye or mouth remnants in face_base"],
        "recovery": "regenerate or model-native repaint clean base; do not widen cover patches",
    },
    {
        "id": "moving_eye_white",
        "verdict": "FAIL_RIG_POLICY",
        "signals": ["eye white follows EyeBallX/Y", "whole baked eye slides inside face"],
        "recovery": "keep white fixed; move only anchor-locked iris/pupil/highlight detail",
    },
    {
        "id": "split_eye_detail_drift",
        "verdict": "REVISE_OR_REGENERATE",
        "signals": ["pupil/highlight detach from iris", "cross-eyed gaze", "only a small part of original eye moves"],
        "recovery": "use manual anchor correction and regenerate production split as a coherent eye packet",
    },
    {
        "id": "oversized_or_centered_mouth",
        "verdict": "REVISE_OR_REGENERATE",
        "signals": ["wide open mouth too large", "round patch boundary", "tiny mouth opens at center only"],
        "recovery": "regenerate smile-open mouth packet with bounded max open and visible teeth/tongue",
    },
    {
        "id": "pasted_mouth_internals",
        "verdict": "FAIL_VISUAL_QA",
        "signals": ["teeth/tongue/inner look like overlays", "internals do not follow mouth shape"],
        "recovery": "generate internals inside coordinated mouth opening, then split cleanly",
    },
    {
        "id": "fake_hairfront_slider",
        "verdict": "UNSUPPORTED_CONTROL_HIDE",
        "signals": ["ParamHairFront exists but no independent front hair child parts move"],
        "recovery": "hide in diagnostic preview until hair_front_* parts exist",
    },
    {
        "id": "validator_only_promotion",
        "verdict": "BLOCKED_FROM_PRODUCTION",
        "signals": ["PNG validator passes but contact sheet or human review says REVISE/FAIL"],
        "recovery": "keep technical PASS separate and return to visual/overlay QA",
    },
    {
        "id": "mini_cubism_as_real_cubism",
        "verdict": "BLOCKED_FROM_PRODUCTION_CLAIM",
        "signals": ["Mini Cubism pose sweep PASS used as final rig proof"],
        "recovery": "author real Cubism deformers/keyforms, then run CMO3 structure inspection",
    },
]


def load_part_spec() -> dict:
    data = json.loads(PART_SPEC_PATH.read_text(encoding="utf-8"))
    parts = data["parts"]
    counts = Counter(part["group"] for part in parts)
    assert len(parts) == 64, len(parts)
    assert dict(counts) == EXPECTED_COUNTS, counts
    assert len({part["id"] for part in parts}) == 64
    return data


def build_spec(part_spec: dict) -> dict:
    parts = part_spec["parts"]
    return {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "spec_id": "cubism-v2-new-character-002-v22-64part-generation-spec",
        "status": "PASS_SPEC_READY_FOR_IMAGE_GENERATION_PLANNING",
        "target": {
            "experiment_id": "cubism-v2-new-character-002",
            "version": "v22_64part_generation_spec",
            "tier": "v2_standard",
            "part_count": 64,
            "default_canvas": "2048x2048 RGBA full-canvas after normalization",
            "production_target": "Live2D/Cubism PSD, ArtMesh, Deformer, Keyform, CMO3/runtime validation",
            "not_target": "PNG frame-swap production runtime",
        },
        "source_refs": SOURCE_REFS,
        "locked_success_baseline": {
            "current_preview": "v21 supported-control Mini Cubism rig smoke",
            "active_controls": [
                "ParamAngleX",
                "ParamEyeBallX",
                "ParamEyeBallY",
                "ParamEyeLOpen",
                "ParamEyeROpen",
                "ParamMouthOpenY",
            ],
            "hidden_unsupported_controls": ["ParamHairFront"],
            "eye_open_visual_policy": "natural close around 0.27; do not expose harder close as default visual target until new assets approve it",
            "mouth_open_policy": "clamp wide open around 0.85 until regenerated smile-open packet passes visual QA",
            "diagnostic_scope": "Mini Cubism PASS is local diagnostic evidence only, not real Cubism authoring success",
        },
        "part_groups": EXPECTED_COUNTS,
        "parts": parts,
        "generation_batches": GENERATION_BATCHES,
        "quality_gates": QUALITY_GATES,
        "success_patterns": SUCCESS_PATTERNS,
        "failure_patterns": FAILURE_PATTERNS,
        "required_outputs": [
            "raw_outputs/",
            "normalized_layers/",
            "generation_manifest.json",
            "layer_manifest.json",
            "technical_validation_report.json",
            "64part_completeness_report.json",
            "contact_sheet.png",
            "overlay_qa_report.md",
            "human_visual_review.md",
            "manual_anchor_overrides.json when used",
            "mini_cubism_diagnostic_project/ after visual QA only",
            "import_ready_candidate.psd after material QA",
            "cubism_import_smoke.json after actual Cubism Editor import",
            "cmo3_structure_report.json after real Cubism authoring",
        ],
        "self_review": {
            "part_count": len(parts),
            "group_counts": dict(Counter(part["group"] for part in parts)),
            "no_duplicate_part_ids": len({part["id"] for part in parts}) == len(parts),
            "has_real_hairfront_scope": all(
                pid in {part["id"] for part in parts}
                for pid in ["hair_front_center", "hair_front_L", "hair_front_R", "hair_front_tip_L", "hair_front_tip_R"]
            ),
            "has_eye_detail_split_scope": all(
                pid in {part["id"] for part in parts}
                for pid in ["eye_L_iris", "eye_L_pupil", "eye_L_highlight", "eye_R_iris", "eye_R_pupil", "eye_R_highlight"]
            ),
            "has_mouth_internal_scope": all(
                pid in {part["id"] for part in parts}
                for pid in ["mouth_inner", "mouth_teeth", "mouth_tongue"]
            ),
            "status": "PASS",
        },
    }


def md_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def write_markdown(spec: dict, path: Path) -> None:
    lines: list[str] = []
    lines.append("# Character 002 v22 64-Part Generation Spec")
    lines.append("")
    lines.append(f"- status: `{spec['status']}`")
    lines.append(f"- generated_at: `{spec['generated_at']}`")
    lines.append(f"- target: `{spec['target']['tier']}` / `{spec['target']['part_count']}` parts")
    lines.append(f"- default canvas: `{spec['target']['default_canvas']}`")
    lines.append("- production target: Live2D/Cubism PSD, real deformers/keyforms, CMO3/runtime validation")
    lines.append("- not target: PNG frame-swap production")
    lines.append("")
    lines.append("## Locked v21 Success Baseline")
    lines.append("")
    baseline = spec["locked_success_baseline"]
    lines.append(f"- current: `{baseline['current_preview']}`")
    lines.append(f"- active controls: `{', '.join(baseline['active_controls'])}`")
    lines.append(f"- hidden unsupported controls: `{', '.join(baseline['hidden_unsupported_controls'])}`")
    lines.append(f"- eye policy: {baseline['eye_open_visual_policy']}")
    lines.append(f"- mouth policy: {baseline['mouth_open_policy']}")
    lines.append(f"- diagnostic scope: {baseline['diagnostic_scope']}")
    lines.append("")
    lines.append("## 64-Part Counts")
    lines.append("")
    for group, count in spec["part_groups"].items():
        lines.append(f"- `{group}`: `{count}`")
    lines.append("")
    lines.append("## Generation Batches")
    lines.append("")
    for batch in spec["generation_batches"]:
        lines.append(f"### {batch['id']}")
        lines.append("")
        lines.append(batch["purpose"])
        lines.append("")
        lines.append("Outputs:")
        lines.append(md_list([f"`{item}`" for item in batch["outputs"]]))
        lines.append("")
        lines.append("Rules:")
        lines.append(md_list(batch["rules"]))
        lines.append("")
    lines.append("## Quality Gates")
    lines.append("")
    for gate in spec["quality_gates"]:
        lines.append(f"### {gate['id']} -> `{gate['status_to_reach']}`")
        lines.append("")
        lines.append(md_list(gate["checks"]))
        lines.append("")
    lines.append("## Success Patterns")
    lines.append("")
    for item in spec["success_patterns"]:
        lines.append(f"- `{item['id']}`: {item['signal']} / distinguishes from: {item['distinguishes_from_failure']}")
    lines.append("")
    lines.append("## Failure Patterns")
    lines.append("")
    for item in spec["failure_patterns"]:
        lines.append(f"- `{item['id']}` -> `{item['verdict']}`")
        lines.append(f"  - signals: {', '.join(item['signals'])}")
        lines.append(f"  - recovery: {item['recovery']}")
    lines.append("")
    lines.append("## Required Outputs")
    lines.append("")
    lines.append(md_list([f"`{item}`" for item in spec["required_outputs"]]))
    lines.append("")
    lines.append("## Source References")
    lines.append("")
    for key, value in spec["source_refs"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    lines.append("## Self Review")
    lines.append("")
    for key, value in spec["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    part_spec = load_part_spec()
    spec = build_spec(part_spec)
    json_path = OUT_DIR / "v22_64part_generation_spec.json"
    md_path = OUT_DIR / "v22_64part_generation_spec.md"
    json_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(spec, md_path)
    print(f"status={spec['status']}")
    print(f"json={json_path}")
    print(f"markdown={md_path}")


if __name__ == "__main__":
    main()

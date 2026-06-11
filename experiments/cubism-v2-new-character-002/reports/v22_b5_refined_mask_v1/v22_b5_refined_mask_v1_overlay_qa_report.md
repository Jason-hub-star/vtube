# Character 002 v22 B5 Refined Mask v1 Overlay QA

- status: `B5_REFINED_MASK_V1_OVERLAY_QA_REVISE_REEXTRACTION_OR_HUMAN_REVIEW_REQUIRED`
- refined mask report: `experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v1/v22_b5_refined_mask_v1_report.json`
- overlay sheet: `experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v1/v22_b5_refined_mask_v1_overlay_qa.png`

## Checks

- `PASS_TECHNICAL` `technical_refined_mask_pack`: B5 refined-mask v1 generated 17/17 full-canvas 2048 RGBA non-empty candidates, with 13 targeted mask refinements and 4 copied auto-draft controls.
- `PASS_TECHNICAL` `json_override_rebuild_path`: The B5 refined candidates were built downstream of the auto-draft JSON override path, proving repeatable regeneration instead of one-off manual edits.
- `IMPROVED_CANDIDATE_REVIEW_REQUIRED` `face_detail_mask_reduction`: Nose, cheek, and face-shadow masks are smaller/softer than the previous auto-draft overlay, but still require visual review and may need another semantic mask pass.
- `REVISE_EXTRACTION_MASK` `body_clothing_mask_quality`: Torso and shoulder/body regions still read as broad overlay patches in the QA sheet. Anchor movement is not the main issue; extraction-mask semantics need more refinement or regeneration.
- `BLOCKED` `material_promotion_gate`: Do not promote B5 material quality from this v1. Validator and full-canvas PNG checks are technical evidence only.
- `BLOCKED` `g7_g8_gate`: Mini Cubism diagnostic and real Cubism authoring remain blocked until B4/B5 visual QA and 주인님 review accept corrected materials.

## Focused Revise Parts

- `torso_base`
- `shoulder_L`
- `shoulder_R`
- `face_shadow_L`
- `face_shadow_R`
- `nose`

## Possible Review Parts

- `cheek_L`
- `cheek_R`
- `chest_cloth_shadow`
- `collar_shadow`
- `arm_L_upper_simple`
- `arm_R_upper_simple`

## Decision

Keep B5 refined-mask v1 as useful intermediate evidence, not as material PASS. Continue automatic mask/extraction refinement for the focused revise parts before asking 주인님 for broad B5 approval.

## Next Action

- Run a smaller v2 refinement for torso/shoulders/face shadows/nose.
- Keep B4 hair focused review separate from B5 body/clothing mask refinement.
- Rebuild the combined B4/B5 corrected candidate only after B5 focused revise parts improve.

## Self Review

- `refined_report_status`: `B5_REFINED_MASK_V1_CANDIDATE_READY_FOR_OVERLAY_REVIEW`
- `refined_mask_count`: `13`
- `copied_from_auto_draft_count`: `4`
- `has_revise_gate`: `True`
- `has_blocked_material_gate`: `True`
- `validator_only_promotion_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`

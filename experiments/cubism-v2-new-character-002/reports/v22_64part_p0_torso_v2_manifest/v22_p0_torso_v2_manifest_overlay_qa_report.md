# Character 002 v22 P0 Torso v2 Manifest Overlay QA

- status: `G3_P0_TORSO_V2_MANIFEST_OVERLAY_QA_REVIEW_REQUIRED`
- overlay sheet: `experiments/cubism-v2-new-character-002/reports/v22_64part_p0_torso_v2_manifest/v22_p0_torso_v2_manifest_overlay_qa.png`

## Summary

- `qa_entry_count`: `33`
- `b4_entry_count`: `16`
- `b5_entry_count`: `17`
- `verdict_counts`: `{'B4_FRONT_HAIR_MOTION_CANDIDATE_REVIEW_REQUIRED': 7, 'B4_SECONDARY_DRAW_ORDER_OR_MASK_REVIEW_REQUIRED': 9, 'B5_COPIED_LAYER_REVIEW_REQUIRED': 14, 'B5_SHOULDER_DRAW_ORDER_MASK_IMPROVEMENT_REVIEW_REQUIRED': 2, 'B5_TORSO_P0_V2_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED': 1}`
- `material_pass_status`: `BLOCKED`
- `param_hair_front_status`: `HIDDEN_CONTRACT_ONLY`
- `g4_psd_import_prep_status`: `PREP_ONLY_BLOCKED`
- `g5_material_acceptance_status`: `BLOCKED`
- `g7_mini_cubism_status`: `BLOCKED`
- `g8_real_cubism_status`: `BLOCKED`

## Self Review

- `manifest_status`: `G3_P0_TORSO_V2_64PART_MANIFEST_TECHNICAL_PASS_REVIEW_REQUIRED`
- `qa_entry_count`: `33`
- `b4_entry_count`: `16`
- `b5_entry_count`: `17`
- `b4_front_hair_candidate_count`: `7`
- `b4_secondary_review_count`: `9`
- `b5_shoulder_improvement_candidate_count`: `2`
- `b5_torso_p0_v2_candidate_count`: `1`
- `b5_copied_layer_review_count`: `14`
- `overlay_sheet_exists`: `True`
- `has_review_required_gate`: `True`
- `material_pass_blocked`: `True`
- `validator_only_promotion_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `not_owner_approval`: `True`
- `status`: `PASS`

## Decision

P0 torso v2 manifest overlay QA is review-required. It preserves B4 front-hair and B5 shoulder candidates, marks torso as a P0 v2 improvement candidate, and keeps material PASS, ParamHairFront, Mini Cubism, and real Cubism blocked.

## Next Action

- Continue G3 blocker reduction with the nine P1 B4 secondary hair rows.
- Keep B5 copied/context rows for later review after P0/P1 are reduced.
- Do not promote G4/G5, G7, or G8 from this overlay QA alone.

# Character 002 v22 G4 Torso-Selected Manifest Overlay QA

- status: `G4_TORSO_SELECTED_MANIFEST_OVERLAY_QA_REVIEW_REQUIRED_MATERIAL_BLOCKED`
- overlay sheet: `experiments/cubism-v2-new-character-002/reports/v22_64part_g4_torso_selected_manifest/v22_g4_torso_selected_manifest_overlay_qa.png`

## Summary

- `qa_entry_count`: `33`
- `b4_entry_count`: `16`
- `b5_entry_count`: `17`
- `verdict_counts`: `{'B4_FRONT_HAIR_MOTION_CANDIDATE_REVIEW_REQUIRED': 7, 'B4_SECONDARY_DRAW_ORDER_OR_MASK_REVIEW_REQUIRED': 9, 'B5_COPIED_LAYER_REVIEW_REQUIRED': 14, 'B5_SHOULDER_DRAW_ORDER_MASK_IMPROVEMENT_REVIEW_REQUIRED': 2, 'B5_TORSO_GENERATED_UNDERPAINT_REBUILD_REVIEW_REQUIRED': 1}`
- `generated_torso_review_count`: `1`
- `material_pass_status`: `BLOCKED`
- `g5_material_acceptance_status`: `BLOCKED_PENDING_OVERLAY_REDUCTION_OR_SEPARATE_G5_ACCEPTANCE`
- `param_hair_front_status`: `HIDDEN_CONTRACT_ONLY`
- `g7_mini_cubism_status`: `BLOCKED`
- `g8_real_cubism_status`: `BLOCKED`

## Self Review

- `manifest_status`: `G4_TORSO_SELECTED_64PART_MANIFEST_TECHNICAL_PASS_REVIEW_REQUIRED`
- `qa_entry_count`: `33`
- `b4_entry_count`: `16`
- `b5_entry_count`: `17`
- `generated_torso_review_count`: `1`
- `b4_front_hair_candidate_count`: `7`
- `b4_secondary_review_count`: `9`
- `b5_shoulder_improvement_candidate_count`: `2`
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

G4 torso-selected manifest overlay QA is review-required. The generated torso is now the selected B5 torso rebuild candidate, but B4 front-hair motion candidates, B4 secondary rows, B5 shoulders, and copied B5 context rows still keep G5/material blocked.

## Next Action

- Build a compact G4 torso-selected review/reduction packet that separates remaining B4/B5 review lanes.
- Do not unlock G5 until the remaining overlay review lanes are accepted or reduced.
- Keep ParamHairFront hidden, and keep G7/G8 blocked.

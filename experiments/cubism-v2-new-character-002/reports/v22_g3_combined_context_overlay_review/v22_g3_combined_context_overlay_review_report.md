# Character 002 v22 G3 Combined Context Overlay Review

- status: `G3_COMBINED_CONTEXT_OVERLAY_REVIEW_READY_MATERIAL_BLOCKED`
- overlay sheet: `experiments/cubism-v2-new-character-002/reports/v22_g3_combined_context_overlay_review/v22_g3_combined_context_overlay_review.png`

## Summary

- `qa_entry_count`: `33`
- `primary_remaining_count`: `0`
- `context_review_count`: `33`
- `classification_counts`: `{'G3_CONTEXT_B5_BODY_CLOTHING_STACK_REVIEW_REQUIRED': 7, 'G3_CONTEXT_B5_FACE_MICRO_DETAIL_REVIEW_REQUIRED': 7, 'G3_CONTEXT_BACK_STACK_DRAW_ORDER_REVIEW_REQUIRED': 3, 'G3_CONTEXT_BACK_STRAND_NUMERIC_PASS_REVIEW_REQUIRED': 2, 'G3_CONTEXT_FRONT_HAIR_MOTION_CANDIDATE_KEEP_HAIRFRONT_HIDDEN': 7, 'G3_CONTEXT_SHOULDER_IMPROVEMENT_REVIEW_REQUIRED': 2, 'G3_CONTEXT_SIDE_HAIR_LOW_ALPHA_REVIEW_REQUIRED': 4, 'G3_CONTEXT_TORSO_P0_V2_REVIEW_REQUIRED': 1}`
- `review_class_counts`: `{'CONTEXT_REVIEW': 33}`
- `material_pass_status`: `BLOCKED`
- `param_hair_front_status`: `HIDDEN_CONTRACT_ONLY`
- `g3_visual_overlay_status`: `COMBINED_CONTEXT_REVIEW_REQUIRED_NOT_PASS`
- `g4_psd_import_prep_status`: `PREP_ONLY_BLOCKED`
- `g5_material_acceptance_status`: `BLOCKED`
- `g7_mini_cubism_status`: `BLOCKED`
- `g8_real_cubism_status`: `BLOCKED`

## Self Review

- `p0_overlay_status`: `G3_P0_TORSO_V2_MANIFEST_OVERLAY_QA_REVIEW_REQUIRED`
- `p1_reduction_status`: `G3_P1_B4_SECONDARY_HAIR_REDUCTION_PACKET_READY_REVIEW_REQUIRED`
- `p1a_probe_status`: `G3_P1A_B4_BACK_STRAND_ANCHOR_MASK_NUMERIC_PASS_CONTEXT_REVIEW_REQUIRED`
- `qa_entry_count`: `33`
- `primary_remaining_count`: `0`
- `context_review_count`: `33`
- `overlay_sheet_exists`: `True`
- `material_pass_blocked`: `True`
- `visual_promotion_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `not_owner_approval`: `True`
- `status`: `PASS`

## Decision

P0 and P1A reductions leave no primary B4/B5 blocker rows in this combined review sheet, but all rows remain context-review evidence. This is not material PASS and does not unlock ParamHairFront, Mini Cubism, or real Cubism.

## Next Action

- Use this combined overlay as the G3 context-review surface before any G4/G5 material promotion attempt.
- Keep ParamHairFront hidden until real independent front hair child art passes motion-readiness review.
- Do not promote Mini Cubism or real Cubism from this context overlay.

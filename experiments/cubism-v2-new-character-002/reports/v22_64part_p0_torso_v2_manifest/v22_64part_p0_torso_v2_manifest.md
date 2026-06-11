# Character 002 v22 64-Part P0 Torso v2 Manifest

- status: `G3_P0_TORSO_V2_64PART_MANIFEST_TECHNICAL_PASS_REVIEW_REQUIRED`
- G0 status: `PASS_READY_FOR_64PART_GENERATION`
- contact sheet: `experiments/cubism-v2-new-character-002/reports/v22_64part_p0_torso_v2_manifest/v22_64part_p0_torso_v2_manifest_contact_sheet.png`

## Gate Interpretation

- `g1_64part_completeness`: `PASS_TECHNICAL`
- `g2_full_canvas_rgba`: `PASS_TECHNICAL`
- `g4_g5_visual_overlay`: `REVIEW_REQUIRED_FOR_P0_TORSO_V2_AND_REMAINING_B4_B5`
- `g6_manual_anchor_correction`: `PROVISIONAL_B4_B5_CORRECTED_CANDIDATE_READY_FOR_REVIEW`
- `g7_mini_cubism_diagnostic`: `BLOCKED_UNTIL_VISUAL_QA_ACCEPTS_B1_B5`
- `g8_real_cubism_authoring`: `BLOCKED_UNTIL_MATERIAL_QA_AND_VISUAL_REVIEW`
- `param_hair_front`: `HIDDEN_CONTRACT_ONLY`
- `g3_p0_torso_status`: `P0_TORSO_V2_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED`
- `g5_material_acceptance`: `BLOCKED_UNTIL_G3_VISUAL_ACCEPTANCE`

## Self Review

- `required_part_count`: `64`
- `manifest_entry_count`: `64`
- `unique_manifest_part_count`: `64`
- `missing_part_count`: `0`
- `wrong_mode_count`: `0`
- `wrong_size_count`: `0`
- `empty_part_count`: `0`
- `duplicate_part_count`: `0`
- `group_counts`: `{'body': 10, 'face_base': 8, 'eye_L': 8, 'eye_R': 8, 'brow': 2, 'mouth': 8, 'hair': 16, 'clothing': 4}`
- `required_group_counts`: `{'body': 10, 'face_base': 8, 'eye_L': 8, 'eye_R': 8, 'brow': 2, 'mouth': 8, 'hair': 16, 'clothing': 4}`
- `group_counts_match_spec`: `True`
- `visual_gate_counts`: `{'PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED': 31, 'P0_TORSO_MINIPASS_V2_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED': 1, 'B5_COPIED_FROM_REFINED_MASK_V2_REVIEW_REQUIRED': 14, 'PASS_DRAW_ORDER_MASK_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED': 2, 'B4_SECONDARY_DRAW_ORDER_OR_MASK_REVIEW_REQUIRED': 9, 'B4_FRONT_HAIR_MOTION_READINESS_CANDIDATE_REVIEW_REQUIRED': 7}`
- `status_counts`: `{'TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED': 31, 'TECHNICAL_PRESENT_B5_P0_TORSO_V2_REVIEW_REQUIRED': 1, 'TECHNICAL_PRESENT_B5_COPIED_REVIEW_REQUIRED': 14, 'TECHNICAL_PRESENT_B5_DRAW_ORDER_MASK_IMPROVEMENT_REVIEW_REQUIRED': 2, 'TECHNICAL_PRESENT_B4_SECONDARY_REVIEW_REQUIRED': 9, 'TECHNICAL_PRESENT_B4_FRONT_HAIR_MOTION_CANDIDATE_REVIEW_REQUIRED': 7}`
- `b4_entry_count`: `16`
- `b5_entry_count`: `17`
- `b4_front_hair_motion_candidate_count`: `7`
- `b5_provisional_target_count`: `3`
- `b5_shoulder_improvement_candidate_count`: `2`
- `b5_torso_review_candidate`: `True`
- `material_pass_blocked`: `True`
- `validator_only_promotion_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`
- `p0_torso_v2_report_status`: `P0_TORSO_MINIPASS_V2_CANDIDATE_READY_FOR_G3_REVIEW`
- `p0_torso_v2_verdict`: `P0_TORSO_MINIPASS_V2_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED`
- `p0_torso_alpha_sum_ratio`: `0.357488`
- `g3_visual_overlay_status`: `REVIEW_REQUIRED`
- `not_owner_approval`: `True`
- `b5_p0_torso_v2_candidate_count`: `1`

## Decision

This 64-part manifest variant replaces only B5 torso_base with the P0 torso v2 improvement candidate. It is technically complete, but remains G3 review-required and cannot promote material PASS, ParamHairFront, Mini Cubism, or real Cubism.

## Next Action

- Run P0 torso v2 manifest overlay QA.
- Use the overlay QA to continue G3 blocker reduction for P0 torso and P1 B4 secondary hair rows.
- Keep material PASS, ParamHairFront, G4/G5 promotion, G7 Mini Cubism, and G8 real Cubism blocked.

# Character 002 v22 64-Part G4 Torso-Selected Manifest

- status: `G4_TORSO_SELECTED_64PART_MANIFEST_TECHNICAL_PASS_REVIEW_REQUIRED`
- G0 status: `PASS_READY_FOR_64PART_GENERATION`
- contact sheet: `experiments/cubism-v2-new-character-002/reports/v22_64part_g4_torso_selected_manifest/v22_64part_g4_torso_selected_manifest_contact_sheet.png`

## Gate Interpretation

- `g1_64part_completeness`: `PASS_TECHNICAL`
- `g2_full_canvas_rgba`: `PASS_TECHNICAL`
- `g4_g5_visual_overlay`: `REVIEW_REQUIRED_FOR_GENERATED_TORSO_AND_REMAINING_B4_B5`
- `g6_manual_anchor_correction`: `PROVISIONAL_B4_B5_CORRECTED_CANDIDATE_READY_FOR_REVIEW`
- `g7_mini_cubism_diagnostic`: `BLOCKED_UNTIL_VISUAL_QA_ACCEPTS_B1_B5`
- `g8_real_cubism_authoring`: `BLOCKED_UNTIL_MATERIAL_QA_AND_VISUAL_REVIEW`
- `param_hair_front`: `HIDDEN_CONTRACT_ONLY`
- `g4_torso_selection`: `GENERATED_TORSO_SELECTED_FOR_NEXT_REBUILD_REVIEW_REQUIRED`
- `g5_material_acceptance`: `BLOCKED_PENDING_NEXT_OVERLAY_QA_AND_SEPARATE_G5_ACCEPTANCE`

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
- `visual_gate_counts`: `{'PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED': 31, 'G4_TORSO_BASE_GENERATED_REBUILD_INPUT_REVIEW_REQUIRED': 1, 'B5_COPIED_FROM_REFINED_MASK_V2_REVIEW_REQUIRED': 14, 'PASS_DRAW_ORDER_MASK_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED': 2, 'B4_SECONDARY_DRAW_ORDER_OR_MASK_REVIEW_REQUIRED': 9, 'B4_FRONT_HAIR_MOTION_READINESS_CANDIDATE_REVIEW_REQUIRED': 7}`
- `status_counts`: `{'TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED': 31, 'TECHNICAL_PRESENT_B5_G4_GENERATED_TORSO_REVIEW_REQUIRED': 1, 'TECHNICAL_PRESENT_B5_COPIED_REVIEW_REQUIRED': 14, 'TECHNICAL_PRESENT_B5_DRAW_ORDER_MASK_IMPROVEMENT_REVIEW_REQUIRED': 2, 'TECHNICAL_PRESENT_B4_SECONDARY_REVIEW_REQUIRED': 9, 'TECHNICAL_PRESENT_B4_FRONT_HAIR_MOTION_CANDIDATE_REVIEW_REQUIRED': 7}`
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
- `g4_torso_route_status`: `G4_TORSO_BASE_REGEN_OVERLAY_QA_ROUTE_READY_MATERIAL_BLOCKED`
- `g4_torso_route`: `USE_GENERATED_TORSO_FOR_NEXT_MANIFEST_REBUILD_KEEP_G5_BLOCKED`
- `generated_torso_candidate`: `experiments/cubism-v2-new-character-002/v22_g4_torso_base_regen_candidate/normalized_layers/torso_base.png`
- `generated_torso_alpha_coverage`: `0.1204493`
- `generated_torso_bbox`: `[520, 880, 1539, 1688]`
- `generated_vs_p0_bottom_extension_px`: `346`
- `generated_alpha_ratio_to_old`: `0.87191864`
- `g4_torso_selected_replacement_count`: `1`
- `g4_visual_overlay_status`: `REVIEW_REQUIRED`
- `g5_material_acceptance_status`: `BLOCKED_PENDING_NEXT_OVERLAY_QA_AND_SEPARATE_G5_ACCEPTANCE`
- `not_owner_approval`: `True`
- `b5_generated_torso_selected_count`: `1`

## Decision

This 64-part manifest variant replaces only B5 torso_base with the generated G4 torso candidate selected by focused overlay QA. It is technically complete and ready for overlay review, but does not promote material PASS, ParamHairFront, Mini Cubism, or real Cubism.

## Next Action

- Run G4 torso-selected manifest overlay QA.
- If overlay QA remains review-required, build a focused reduction packet instead of unlocking G5.
- Keep material PASS, ParamHairFront, G7 Mini Cubism, and G8 real Cubism blocked.

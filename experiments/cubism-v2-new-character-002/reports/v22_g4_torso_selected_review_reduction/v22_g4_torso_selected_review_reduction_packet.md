# Character 002 v22 G4 Torso-Selected Review Reduction Packet

- status: `G4_TORSO_SELECTED_REVIEW_REDUCTION_PACKET_READY_MATERIAL_BLOCKED`
- review sheet: `experiments/cubism-v2-new-character-002/reports/v22_g4_torso_selected_review_reduction/v22_g4_torso_selected_review_reduction_sheet.png`
- G5 material acceptance: `BLOCKED_PENDING_REDUCTION_PACKET_REVIEW`
- ParamHairFront: `HIDDEN_CONTRACT_ONLY`

## Work Order Phases

- `P0` `pre-G5 torso/shoulder review`: `3` rows; Only a later G5 readiness refresh, not material PASS.
- `P1` `front-hair motion-readiness candidates`: `7` rows; Future HairFront readiness only after motion review; hidden now.
- `P2` `B4 secondary hair context`: `9` rows; Context evidence for later G5 review.
- `P3` `B5 copied context rows`: `14` rows; Context evidence for later G5 review.

## Summary

- `source_manifest_status`: `G4_TORSO_SELECTED_64PART_MANIFEST_TECHNICAL_PASS_REVIEW_REQUIRED`
- `overlay_qa_status`: `G4_TORSO_SELECTED_MANIFEST_OVERLAY_QA_REVIEW_REQUIRED_MATERIAL_BLOCKED`
- `review_row_count`: `33`
- `pre_g5_blocking_row_count`: `3`
- `context_review_row_count`: `23`
- `hairfront_hidden_candidate_count`: `7`
- `lane_counts`: `{'P0_B5_SHOULDER_DRAW_ORDER_MASK_CANDIDATE_REVIEW': 2, 'P0_B5_TORSO_SELECTED_OVERLAY_REVIEW': 1, 'P1_B4_FRONT_HAIR_MOTION_CANDIDATE_KEEP_HAIRFRONT_HIDDEN': 7, 'P2_B4_SECONDARY_HAIR_CONTEXT_REVIEW': 9, 'P3_B5_BODY_CLOTHING_COPIED_CONTEXT_REVIEW': 7, 'P3_B5_FACE_MICRO_COPIED_CONTEXT_REVIEW': 7}`
- `class_counts`: `{'B4_SECONDARY_CONTEXT_REVIEW': 9, 'B5_COPIED_CONTEXT_REVIEW': 14, 'HAIRFRONT_MOTION_READINESS_REVIEW': 7, 'PRE_G5_SELECTED_TORSO_REVIEW': 1, 'PRE_G5_SHOULDER_CANDIDATE_REVIEW': 2}`
- `effect_counts`: `{'BLOCKS_G5_UNTIL_REVIEW_OR_FURTHER_REDUCTION': 3, 'CONTEXT_REVIEW_BEFORE_G5': 23, 'DOES_NOT_UNLOCK_HAIRFRONT_YET': 7}`
- `generated_torso_selected`: `True`
- `g5_material_acceptance_status`: `BLOCKED_PENDING_REDUCTION_PACKET_REVIEW`
- `material_pass_status`: `BLOCKED`
- `param_hair_front_status`: `HIDDEN_CONTRACT_ONLY`
- `g7_mini_cubism_status`: `BLOCKED`
- `g8_real_cubism_status`: `BLOCKED`

## Self Review

- `source_manifest_status`: `G4_TORSO_SELECTED_64PART_MANIFEST_TECHNICAL_PASS_REVIEW_REQUIRED`
- `overlay_qa_status`: `G4_TORSO_SELECTED_MANIFEST_OVERLAY_QA_REVIEW_REQUIRED_MATERIAL_BLOCKED`
- `review_row_count`: `33`
- `matches_overlay_qa_entry_count`: `True`
- `pre_g5_blocking_row_count`: `3`
- `pre_g5_blocking_row_count_is_three`: `True`
- `generated_torso_selected_count`: `1`
- `shoulder_candidate_count`: `2`
- `front_hair_candidate_count`: `7`
- `b4_secondary_context_count`: `9`
- `b5_copied_context_count`: `14`
- `review_sheet_exists`: `True`
- `not_owner_approval`: `True`
- `material_pass_blocked`: `True`
- `validator_only_promotion_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`

## Decision

The generated torso is selected in the 64-part manifest, but the remaining B4/B5 surface is still a review/reduction packet. Only three rows are immediate pre-G5 blockers (torso plus shoulders); HairFront remains hidden and context rows remain unpromoted.

## Next Action

- Resolve the three P0 pre-G5 torso/shoulder rows first.
- Keep seven front-hair child rows as motion-readiness candidates with ParamHairFront hidden.
- Keep B4 secondary and B5 copied rows as context review until a separate G5 packet is built.

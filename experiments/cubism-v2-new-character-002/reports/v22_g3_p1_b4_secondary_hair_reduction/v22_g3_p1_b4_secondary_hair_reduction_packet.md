# Character 002 v22 G3 P1 B4 Secondary Hair Reduction

- status: `G3_P1_B4_SECONDARY_HAIR_REDUCTION_PACKET_READY_REVIEW_REQUIRED`
- review sheet: `experiments/cubism-v2-new-character-002/reports/v22_g3_p1_b4_secondary_hair_reduction/v22_g3_p1_b4_secondary_hair_reduction_sheet.png`

## Summary

- `p0_overlay_status`: `G3_P0_TORSO_V2_MANIFEST_OVERLAY_QA_REVIEW_REQUIRED`
- `b4_focused_review_status`: `B4_HAIR_FOCUSED_REVIEW_READY_PARAMHAIRFRONT_STILL_HIDDEN`
- `p1_input_count`: `9`
- `remaining_primary_count`: `2`
- `reduced_to_context_count`: `7`
- `bucket_counts`: `{'P1_CONTEXT_CANDIDATE_BACK_STACK': 3, 'P1_CONTEXT_CANDIDATE_SIDE_HAIR_LOW_ALPHA': 4, 'P1_REMAINING_ANCHOR_MASK_REVIEW': 2}`
- `route_counts`: `{'B4_BACK_STACK_DRAW_ORDER_CONTEXT_CANDIDATE_REVIEW_REQUIRED': 3, 'B4_BACK_STRAND_ANCHOR_MASK_REVIEW_REQUIRED': 2, 'B4_SIDE_HAIR_LOW_ALPHA_CONTEXT_CANDIDATE_REVIEW_REQUIRED': 4}`
- `material_pass_status`: `BLOCKED`
- `param_hair_front_status`: `HIDDEN_CONTRACT_ONLY`
- `g3_visual_overlay_status`: `P1_REDUCED_REVIEW_REQUIRED`
- `g4_psd_import_prep_status`: `PREP_ONLY_BLOCKED`
- `g5_material_acceptance_status`: `BLOCKED`
- `g7_mini_cubism_status`: `BLOCKED`
- `g8_real_cubism_status`: `BLOCKED`

## Self Review

- `p0_overlay_status`: `G3_P0_TORSO_V2_MANIFEST_OVERLAY_QA_REVIEW_REQUIRED`
- `b4_focused_review_status`: `B4_HAIR_FOCUSED_REVIEW_READY_PARAMHAIRFRONT_STILL_HIDDEN`
- `p1_input_count`: `9`
- `remaining_primary_count`: `2`
- `reduced_to_context_count`: `7`
- `anchor_mask_review_count`: `2`
- `back_stack_context_candidate_count`: `3`
- `side_hair_low_alpha_context_candidate_count`: `4`
- `review_sheet_exists`: `True`
- `material_pass_blocked`: `True`
- `visual_promotion_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `not_owner_approval`: `True`
- `status`: `PASS`

## Decision

The nine P1 B4 secondary-hair rows are reduced into two remaining anchor/mask review rows and seven context candidate rows. This narrows the next manual or scripted work, but it is not visual PASS or material approval.

## Next Action

- Handle the two P1A back-strand anchor/mask rows first.
- Keep the seven P1B/P1C rows as context candidates until a combined G3 visual overlay pass is built.
- Do not unlock ParamHairFront, G4/G5 material promotion, Mini Cubism, or real Cubism from this packet.

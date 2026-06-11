# Character 002 v22 G3 B4/B5 Blocker Reduction Packet

- status: `G3_B4_B5_BLOCKER_REDUCTION_PACKET_READY_PRIMARY_10_MATERIAL_BLOCKED`
- review sheet: `experiments/cubism-v2-new-character-002/reports/v22_g3_b4_b5_blocker_reduction/v22_g3_b4_b5_blocker_reduction_sheet.png`

## Summary

- `triage_status`: `CORRECTED_B4_B5_CODEX_VISUAL_TRIAGE_READY_G2_G5_PREP_BLOCKED`
- `g2_status`: `G2_LAYER_MANIFEST_TECHNICAL_QA_PASS_MATERIAL_STILL_BLOCKED`
- `blocker_row_count`: `24`
- `primary_blocker_count`: `10`
- `secondary_blocker_count`: `7`
- `context_review_count`: `7`
- `priority_counts`: `{'P0': 1, 'P1': 9, 'P2': 7, 'P3': 7}`
- `blocker_class_counts`: `{'G3_CONTEXT_REVIEW': 7, 'G3_PRIMARY_BLOCKER': 10, 'G3_SECONDARY_BLOCKER': 7}`
- `route_counts`: `{'B4_SECONDARY_HAIR_DRAW_ORDER_OR_MASK_REVIEW': 9, 'B5_BODY_CLOTHING_STACK_CONTEXT_REVIEW': 7, 'B5_FACE_MICRO_DETAIL_CONTEXT_REVIEW': 7, 'B5_TORSO_MINIPASS_V2_OR_HUMAN_ACCEPT_REQUIRED': 1}`
- `auto_candidate_count_preserved`: `9`
- `material_pass_status`: `BLOCKED`
- `param_hair_front_status`: `HIDDEN_CONTRACT_ONLY`
- `g3_visual_overlay_status`: `BLOCKED_PRIMARY_REVIEW_REQUIRED`
- `g4_psd_import_prep_status`: `PREP_ONLY_BLOCKED`
- `g5_material_acceptance_status`: `BLOCKED`
- `g7_mini_cubism_status`: `BLOCKED`
- `g8_real_cubism_status`: `BLOCKED`

## Primary Rows

- `P0` `torso_base` `B5_TORSO_MINIPASS_V2_OR_HUMAN_ACCEPT_REQUIRED`
- `P1` `hair_back_base` `B4_SECONDARY_HAIR_DRAW_ORDER_OR_MASK_REVIEW`
- `P1` `hair_back_center` `B4_SECONDARY_HAIR_DRAW_ORDER_OR_MASK_REVIEW`
- `P1` `hair_back_strand_L` `B4_SECONDARY_HAIR_DRAW_ORDER_OR_MASK_REVIEW`
- `P1` `hair_back_strand_R` `B4_SECONDARY_HAIR_DRAW_ORDER_OR_MASK_REVIEW`
- `P1` `hair_back_underpaint` `B4_SECONDARY_HAIR_DRAW_ORDER_OR_MASK_REVIEW`
- `P1` `hair_side_L_inner` `B4_SECONDARY_HAIR_DRAW_ORDER_OR_MASK_REVIEW`
- `P1` `hair_side_L_outer` `B4_SECONDARY_HAIR_DRAW_ORDER_OR_MASK_REVIEW`
- `P1` `hair_side_R_inner` `B4_SECONDARY_HAIR_DRAW_ORDER_OR_MASK_REVIEW`
- `P1` `hair_side_R_outer` `B4_SECONDARY_HAIR_DRAW_ORDER_OR_MASK_REVIEW`

## Self Review

- `triage_status`: `CORRECTED_B4_B5_CODEX_VISUAL_TRIAGE_READY_G2_G5_PREP_BLOCKED`
- `g2_status`: `G2_LAYER_MANIFEST_TECHNICAL_QA_PASS_MATERIAL_STILL_BLOCKED`
- `blocker_row_count`: `24`
- `primary_blocker_count`: `10`
- `secondary_blocker_count`: `7`
- `context_review_count`: `7`
- `p0_count`: `1`
- `p1_count`: `9`
- `p2_count`: `7`
- `p3_count`: `7`
- `review_sheet_exists`: `True`
- `material_pass_blocked`: `True`
- `visual_promotion_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `not_owner_approval`: `True`
- `status`: `PASS`

## Decision

G3 blocker work is reduced to 10 primary visual blockers first: one torso hard review plus nine B4 secondary hair draw-order/mask rows. Seven B5 body/clothing rows and seven B5 face micro-detail rows remain for later context review.

## Next Action

- Resolve P0 torso first, then P1 B4 secondary hair rows.
- Keep P2/P3 B5 copied layers as context review rows until primary blockers are handled.
- Do not promote material PASS, ParamHairFront, Mini Cubism, or real Cubism from this packet.

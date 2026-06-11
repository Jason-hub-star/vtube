# Character 002 v22 G4 B4/B5 Focused Follow-up Packet

- status: `G4_B4_B5_FOCUSED_FOLLOWUP_PACKET_READY_MATERIAL_BLOCKED`
- follow-up sheet: `experiments/cubism-v2-new-character-002/reports/v22_g4_b4_b5_focused_followup/v22_g4_b4_b5_focused_followup_sheet.png`
- G5 material acceptance: `BLOCKED_PENDING_B4_B5_FOCUSED_FOLLOWUP`
- material PASS: `BLOCKED`
- ParamHairFront: `HIDDEN_CONTRACT_ONLY`

## Work Order Phases

- `P0` B5 torso and shoulder pre-G5 visual follow-up: `3` rows; Only a later G4/G5 readiness refresh; not material PASS.
- `P1` B4 front-hair motion-readiness candidate review: `7` rows; Only future HairFront readiness if independent child art passes; ParamHairFront stays hidden now.
- `P2_P3` B4/B5 context review lanes: `23` rows; Only context evidence for a separate G5 packet.

## Lane Counts

- `P0_PRE_G5_B5_SHOULDER_DRAW_ORDER_MASK_FOLLOWUP`: `2`
- `P0_PRE_G5_B5_TORSO_VISUAL_FOLLOWUP`: `1`
- `P1_B4_FRONT_HAIR_MOTION_READINESS_KEEP_HAIRFRONT_HIDDEN`: `7`
- `P2_B4_BACK_STACK_DRAW_ORDER_CONTEXT_REVIEW`: `3`
- `P2_B4_BACK_STRAND_NUMERIC_CONTEXT_REVIEW`: `2`
- `P2_B4_SIDE_HAIR_LOW_ALPHA_CONTEXT_REVIEW`: `4`
- `P3_B5_BODY_CLOTHING_STACK_CONTEXT_REVIEW`: `7`
- `P3_B5_FACE_MICRO_DETAIL_CONTEXT_REVIEW`: `7`

## Decision

B4/B5 focused follow-up is now expanded into row-level work lanes. This does not accept B4/B5 visually and does not unlock G5 material acceptance.

## Next Action

- Handle the P0 B5 torso/shoulder focused follow-up rows first.
- Keep B4 front hair as motion-readiness candidates with ParamHairFront hidden.
- Refresh G4/G5 readiness only after focused B4/B5 follow-up evidence exists.

## Self Review

- `route_plan_status`: `G4_VISUAL_DECISION_ROUTE_PLAN_READY_FOR_FOCUSED_FOLLOWUP_MATERIAL_BLOCKED`
- `combined_g3_status`: `G3_COMBINED_CONTEXT_OVERLAY_REVIEW_READY_MATERIAL_BLOCKED`
- `combined_route_is_focused_followup`: `True`
- `followup_row_count`: `33`
- `matches_combined_context_row_count`: `True`
- `pre_g5_focused_followup_count`: `3`
- `has_pre_g5_focused_followup`: `True`
- `has_motion_readiness_followup`: `True`
- `has_context_review_followup`: `True`
- `followup_sheet_exists`: `True`
- `not_owner_approval`: `True`
- `material_pass_blocked`: `True`
- `validator_only_promotion_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`

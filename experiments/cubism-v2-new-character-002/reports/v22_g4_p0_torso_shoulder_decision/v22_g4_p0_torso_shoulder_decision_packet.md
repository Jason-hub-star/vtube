# Character 002 v22 G4 P0 Torso/Shoulder Decision Packet

- status: `G4_P0_TORSO_SHOULDER_DECISION_READY_G5_PREP_UNBLOCKED_MATERIAL_BLOCKED`
- decision sheet: `experiments/cubism-v2-new-character-002/reports/v22_g4_p0_torso_shoulder_decision/v22_g4_p0_torso_shoulder_decision_sheet.png`
- G5 prep: `UNBLOCKED_FOR_PREP_PACKET_ONLY`
- G5 material acceptance: `BLOCKED_PENDING_SEPARATE_G5_ACCEPTANCE_PACKET`

## Decision Rows

- `torso_base` `KEEP_GENERATED_TORSO_AS_G5_PREP_CANDIDATE_NOT_MATERIAL_PASS`: Generated torso is selected, extends lower than P0, and stays below old broad v2 coverage; use it for G5 prep review only.
- `shoulder_L` `KEEP_SHOULDER_DRAW_ORDER_MASK_AS_G5_PREP_CANDIDATE_NOT_MATERIAL_PASS`: Shoulder draw-order/mask improvement candidate can move into G5 prep review; material acceptance remains blocked.
- `shoulder_R` `KEEP_SHOULDER_DRAW_ORDER_MASK_AS_G5_PREP_CANDIDATE_NOT_MATERIAL_PASS`: Shoulder draw-order/mask improvement candidate can move into G5 prep review; material acceptance remains blocked.

## Summary

- `input_p0_blocking_row_count`: `3`
- `decision_row_count`: `3`
- `resolved_to_g5_prep_candidate_count`: `3`
- `remaining_p0_pre_g5_blocker_count`: `0`
- `torso_g5_prep_candidate_count`: `1`
- `shoulder_g5_prep_candidate_count`: `2`
- `g5_prep_status`: `UNBLOCKED_FOR_PREP_PACKET_ONLY`
- `g5_material_acceptance_status`: `BLOCKED_PENDING_SEPARATE_G5_ACCEPTANCE_PACKET`
- `material_pass_status`: `BLOCKED`
- `param_hair_front_status`: `HIDDEN_CONTRACT_ONLY`
- `g7_mini_cubism_status`: `BLOCKED`
- `g8_real_cubism_status`: `BLOCKED`

## Self Review

- `reduction_status`: `G4_TORSO_SELECTED_REVIEW_REDUCTION_PACKET_READY_MATERIAL_BLOCKED`
- `torso_route_status`: `G4_TORSO_BASE_REGEN_OVERLAY_QA_ROUTE_READY_MATERIAL_BLOCKED`
- `b5_provisional_qa_status`: `B5_PROVISIONAL_MINIPASS_OVERLAY_QA_REVIEW_REQUIRED`
- `input_p0_blocking_row_count`: `3`
- `decision_row_count`: `3`
- `resolved_to_g5_prep_candidate_count`: `3`
- `remaining_p0_pre_g5_blocker_count`: `0`
- `all_p0_rows_resolved_for_g5_prep`: `True`
- `torso_g5_prep_candidate_count`: `1`
- `shoulder_g5_prep_candidate_count`: `2`
- `decision_sheet_exists`: `True`
- `g5_prep_unblocked_only`: `True`
- `g5_material_acceptance_blocked`: `True`
- `not_owner_approval`: `True`
- `material_pass_blocked`: `True`
- `validator_only_promotion_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`

## Decision

The three P0 torso/shoulder rows are resolved only as G5 prep candidates. This permits building a later G5 readiness/prep packet, but does not approve material PASS.

## Next Action

- Build a G5 prep packet from the torso-selected manifest using these P0 candidate decisions.
- Carry HairFront as hidden/contract-only and keep B4/B5 context rows review-required.
- Do not promote Mini Cubism or real Cubism from this packet.

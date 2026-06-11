# Character 002 v22 G4 P0 B5 Follow-up Decision Packet

- status: `G4_P0_B5_FOLLOWUP_DECISION_READY_TORSO_REVIEW_REMAINING_MATERIAL_BLOCKED`
- decision sheet: `experiments/cubism-v2-new-character-002/reports/v22_g4_p0_b5_followup_decision/v22_g4_p0_b5_followup_decision_sheet.png`
- pre-G5 remaining: `1`
- G5 material acceptance: `BLOCKED_PENDING_TORSO_REVIEW_OR_REGENERATION`

## Decision Rows

- `torso_base` `P0_TORSO_REVIEW_OR_REGENERATE_BEFORE_G5` `PRE_G5_REVIEW_REMAINING`: Torso alpha was reduced by P0 v2, but it remains a broad underpaint/body visual decision and cannot be auto-accepted.
- `shoulder_L` `P0_SHOULDER_ACCEPT_AS_DRAW_ORDER_MASK_CANDIDATE_KEEP_MATERIAL_BLOCKED` `G4_REFRESH_CANDIDATE_NOT_MATERIAL_PASS`: Shoulder hair-occlusion overlap dropped enough to leave the pre-G5 blocker lane, but visual/material acceptance remains blocked.
- `shoulder_R` `P0_SHOULDER_ACCEPT_AS_DRAW_ORDER_MASK_CANDIDATE_KEEP_MATERIAL_BLOCKED` `G4_REFRESH_CANDIDATE_NOT_MATERIAL_PASS`: Shoulder hair-occlusion overlap dropped enough to leave the pre-G5 blocker lane, but visual/material acceptance remains blocked.

## Summary

- `input_pre_g5_followup_count`: `3`
- `decision_row_count`: `3`
- `torso_review_remaining_count`: `1`
- `shoulder_g4_refresh_candidate_count`: `2`
- `pre_g5_remaining_count`: `1`
- `pre_g5_resolved_to_candidate_count`: `2`
- `g5_material_acceptance_status`: `BLOCKED_PENDING_TORSO_REVIEW_OR_REGENERATION`
- `material_pass_status`: `BLOCKED`
- `param_hair_front_status`: `HIDDEN_CONTRACT_ONLY`
- `g7_mini_cubism_status`: `BLOCKED`
- `g8_real_cubism_status`: `BLOCKED`

## Self Review

- `focused_followup_status`: `G4_B4_B5_FOCUSED_FOLLOWUP_PACKET_READY_MATERIAL_BLOCKED`
- `b5_blocker_status`: `B5_BODY_BLOCKER_DRAW_ORDER_REVIEW_READY_HUMAN_DECISION_REQUIRED`
- `b5_provisional_qa_status`: `B5_PROVISIONAL_MINIPASS_OVERLAY_QA_REVIEW_REQUIRED`
- `p0_torso_status`: `P0_TORSO_MINIPASS_V2_CANDIDATE_READY_FOR_G3_REVIEW`
- `input_pre_g5_followup_count`: `3`
- `decision_row_count`: `3`
- `torso_review_remaining_count`: `1`
- `shoulder_g4_refresh_candidate_count`: `2`
- `pre_g5_remaining_count`: `1`
- `pre_g5_reduced_from_3_to_1`: `True`
- `decision_sheet_exists`: `True`
- `not_owner_approval`: `True`
- `material_pass_blocked`: `True`
- `validator_only_promotion_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`

## Decision

P0 B5 follow-up is narrowed from three pre-G5 rows to one torso review/regeneration blocker. Shoulders can be carried as G4 refresh candidates, not material PASS.

## Next Action

- Handle torso_base as the remaining P0 pre-G5 visual review/regeneration row.
- After torso evidence exists, rebuild G4/G5 readiness with shoulder rows treated as candidates only.
- Keep ParamHairFront hidden and keep G7/G8 blocked.

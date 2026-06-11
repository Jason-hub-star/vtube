# Character 002 v22 B4/B5 Codex Provisional Decisions

- status: `CODEX_PROVISIONAL_DECISIONS_READY_NO_OWNER_APPROVAL`
- source packet: `experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_focused_owner_review.json`

## Summary

- `decision_count`: `10`
- `pending_count`: `0`
- `accepted_count`: `7`
- `revise_count`: `2`
- `regenerate_count`: `1`
- `route_policy_counts`: `{'B4_FRONT_HAIR_PROVISIONAL_ACCEPT_KEEP_HAIRFRONT_HIDDEN': 7, 'B5_TORSO_REGENERATE_MINIPASS': 1, 'B5_SHOULDER_REVISE_DRAW_ORDER_OR_MASK': 2}`
- `material_pass_status`: `BLOCKED`
- `param_hair_front_status`: `HIDDEN_CONTRACT_ONLY`
- `g7_mini_cubism_status`: `BLOCKED`
- `g8_real_cubism_status`: `BLOCKED`

## Decision

Proceed without owner acceptance by using the current success patterns as provisional routing: B4 front hair moves to motion-readiness candidate checks with HairFront hidden; torso regenerates; shoulders revise draw-order or mask.

## Rows

- `hair_front_L` `ACCEPT_FOR_MOTION_READINESS_CANDIDATE` `B4_FRONT_HAIR_PROVISIONAL_ACCEPT_KEEP_HAIRFRONT_HIDDEN`: Codex provisional: real independent hair_front_* child art exists, so continue to motion-readiness candidate checks while keeping ParamHairFront hidden.
- `hair_front_R` `ACCEPT_FOR_MOTION_READINESS_CANDIDATE` `B4_FRONT_HAIR_PROVISIONAL_ACCEPT_KEEP_HAIRFRONT_HIDDEN`: Codex provisional: real independent hair_front_* child art exists, so continue to motion-readiness candidate checks while keeping ParamHairFront hidden.
- `hair_front_center` `ACCEPT_FOR_MOTION_READINESS_CANDIDATE` `B4_FRONT_HAIR_PROVISIONAL_ACCEPT_KEEP_HAIRFRONT_HIDDEN`: Codex provisional: real independent hair_front_* child art exists, so continue to motion-readiness candidate checks while keeping ParamHairFront hidden.
- `hair_front_side_L` `ACCEPT_FOR_MOTION_READINESS_CANDIDATE` `B4_FRONT_HAIR_PROVISIONAL_ACCEPT_KEEP_HAIRFRONT_HIDDEN`: Codex provisional: real independent hair_front_* child art exists, so continue to motion-readiness candidate checks while keeping ParamHairFront hidden.
- `hair_front_side_R` `ACCEPT_FOR_MOTION_READINESS_CANDIDATE` `B4_FRONT_HAIR_PROVISIONAL_ACCEPT_KEEP_HAIRFRONT_HIDDEN`: Codex provisional: real independent hair_front_* child art exists, so continue to motion-readiness candidate checks while keeping ParamHairFront hidden.
- `hair_front_tip_L` `ACCEPT_FOR_MOTION_READINESS_CANDIDATE` `B4_FRONT_HAIR_PROVISIONAL_ACCEPT_KEEP_HAIRFRONT_HIDDEN`: Codex provisional: real independent hair_front_* child art exists, so continue to motion-readiness candidate checks while keeping ParamHairFront hidden.
- `hair_front_tip_R` `ACCEPT_FOR_MOTION_READINESS_CANDIDATE` `B4_FRONT_HAIR_PROVISIONAL_ACCEPT_KEEP_HAIRFRONT_HIDDEN`: Codex provisional: real independent hair_front_* child art exists, so continue to motion-readiness candidate checks while keeping ParamHairFront hidden.
- `torso_base` `REGENERATE_B5_BODY_MINIPASS` `B5_TORSO_REGENERATE_MINIPASS`: Codex provisional: broad torso underpaint/body patch remains a hard visual blocker; run focused B5 body mini-pass instead of accepting it.
- `shoulder_L` `REVISE_MASK_OR_DRAW_ORDER` `B5_SHOULDER_REVISE_DRAW_ORDER_OR_MASK`: Codex provisional: shoulder overlap is heavily affected by hair occlusion/draw order, so revise draw-order or mask before regenerating.
- `shoulder_R` `REVISE_MASK_OR_DRAW_ORDER` `B5_SHOULDER_REVISE_DRAW_ORDER_OR_MASK`: Codex provisional: shoulder overlap is heavily affected by hair occlusion/draw order, so revise draw-order or mask before regenerating.

## Self Review

- `all_primary_parts_present`: `True`
- `no_pending_decisions`: `True`
- `b4_front_hair_count`: `7`
- `b5_body_blocker_count`: `3`
- `not_owner_approval`: `True`
- `material_pass_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`

# Character 002 v22 B4/B5 Owner Decision Route Plan

- status: `B4_B5_OWNER_DECISION_ROUTE_PLAN_READY_FOR_REVISION_WORK`
- decision source: `CODEX_PROVISIONAL_DECISION_FILE`
- decisions path: `experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_focused_codex_provisional_decisions.json`

## Summary

- `primary_decision_count`: `10`
- `decision_row_count`: `10`
- `pending_count`: `0`
- `accepted_count`: `7`
- `revise_count`: `2`
- `regenerate_count`: `1`
- `invalid_decision_count`: `0`
- `route_counts`: `{'ACCEPT_FOR_B4_FRONT_HAIR_MOTION_READINESS_CANDIDATE': 7, 'ROUTE_TO_B5_BODY_MINIPASS_REGENERATION': 1, 'ROUTE_TO_B5_DRAW_ORDER_OR_MASK_REFINEMENT': 2}`
- `material_pass_status`: `BLOCKED`
- `param_hair_front_status`: `HIDDEN_CONTRACT_ONLY`
- `g7_mini_cubism_status`: `BLOCKED`
- `g8_real_cubism_status`: `BLOCKED`

## Decision

Owner decisions are routed into focused B4/B5 follow-up work only. This report never promotes material PASS, ParamHairFront, Mini Cubism, or real Cubism by itself.

## Next Action

- Apply only the focused revise/regenerate routes listed in this report.
- Rebuild corrected B4/B5 candidates and rerun overlay QA.
- Keep ParamHairFront hidden until accepted front-hair child candidates pass motion-readiness.

## Routes

- `hair_front_L` `ACCEPT_FOR_MOTION_READINESS_CANDIDATE` -> `ACCEPT_FOR_B4_FRONT_HAIR_MOTION_READINESS_CANDIDATE`: Keep as a front-hair child candidate, but keep ParamHairFront hidden until motion-readiness and later QA pass.
- `hair_front_R` `ACCEPT_FOR_MOTION_READINESS_CANDIDATE` -> `ACCEPT_FOR_B4_FRONT_HAIR_MOTION_READINESS_CANDIDATE`: Keep as a front-hair child candidate, but keep ParamHairFront hidden until motion-readiness and later QA pass.
- `hair_front_center` `ACCEPT_FOR_MOTION_READINESS_CANDIDATE` -> `ACCEPT_FOR_B4_FRONT_HAIR_MOTION_READINESS_CANDIDATE`: Keep as a front-hair child candidate, but keep ParamHairFront hidden until motion-readiness and later QA pass.
- `hair_front_side_L` `ACCEPT_FOR_MOTION_READINESS_CANDIDATE` -> `ACCEPT_FOR_B4_FRONT_HAIR_MOTION_READINESS_CANDIDATE`: Keep as a front-hair child candidate, but keep ParamHairFront hidden until motion-readiness and later QA pass.
- `hair_front_side_R` `ACCEPT_FOR_MOTION_READINESS_CANDIDATE` -> `ACCEPT_FOR_B4_FRONT_HAIR_MOTION_READINESS_CANDIDATE`: Keep as a front-hair child candidate, but keep ParamHairFront hidden until motion-readiness and later QA pass.
- `hair_front_tip_L` `ACCEPT_FOR_MOTION_READINESS_CANDIDATE` -> `ACCEPT_FOR_B4_FRONT_HAIR_MOTION_READINESS_CANDIDATE`: Keep as a front-hair child candidate, but keep ParamHairFront hidden until motion-readiness and later QA pass.
- `hair_front_tip_R` `ACCEPT_FOR_MOTION_READINESS_CANDIDATE` -> `ACCEPT_FOR_B4_FRONT_HAIR_MOTION_READINESS_CANDIDATE`: Keep as a front-hair child candidate, but keep ParamHairFront hidden until motion-readiness and later QA pass.
- `torso_base` `REGENERATE_B5_BODY_MINIPASS` -> `ROUTE_TO_B5_BODY_MINIPASS_REGENERATION`: Run a focused B5 body mini-pass only.
- `shoulder_L` `REVISE_MASK_OR_DRAW_ORDER` -> `ROUTE_TO_B5_DRAW_ORDER_OR_MASK_REFINEMENT`: Refine B5 draw order or mask; do not restart the full material pipeline.
- `shoulder_R` `REVISE_MASK_OR_DRAW_ORDER` -> `ROUTE_TO_B5_DRAW_ORDER_OR_MASK_REFINEMENT`: Refine B5 draw order or mask; do not restart the full material pipeline.

## Self Review

- `allowed_decision_values_checked`: `True`
- `all_primary_parts_present`: `True`
- `all_route_rows_present`: `True`
- `all_decisions_non_pending`: `True`
- `all_primary_accepted`: `False`
- `has_pending_blocker`: `False`
- `has_revise_or_regenerate_path`: `True`
- `material_pass_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`

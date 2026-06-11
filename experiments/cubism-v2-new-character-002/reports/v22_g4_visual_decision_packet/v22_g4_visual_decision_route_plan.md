# Character 002 v22 G4 Visual Decision Route Plan

- status: `G4_VISUAL_DECISION_ROUTE_PLAN_READY_FOR_FOCUSED_FOLLOWUP_MATERIAL_BLOCKED`
- decision source: `CODEX_PROVISIONAL_VISUAL_DECISION_FILE`
- decisions path: `experiments/cubism-v2-new-character-002/reports/v22_g4_visual_decision_packet/v22_g4_codex_provisional_visual_decisions.json`

## Summary

- `decision_item_count`: `5`
- `decision_row_count`: `5`
- `pending_count`: `0`
- `accepted_visual_candidate_count`: `4`
- `revise_before_g5_count`: `1`
- `regenerate_batch_or_context_count`: `0`
- `invalid_decision_count`: `0`
- `route_counts`: `{'KEEP_AS_G4_VISUAL_CANDIDATE': 4, 'ROUTE_TO_B4_B5_FOCUSED_FOLLOWUP_BEFORE_G5': 1}`
- `g4_visual_review_status`: `ROUTE_PLANNED_NOT_MATERIAL_PASS`
- `g5_material_acceptance_status`: `BLOCKED_PENDING_FOCUSED_G4_FOLLOWUP`
- `material_pass_status`: `BLOCKED`
- `param_hair_front_status`: `HIDDEN_CONTRACT_ONLY`
- `g7_mini_cubism_status`: `BLOCKED`
- `g8_real_cubism_status`: `BLOCKED`

## Decision

G4 visual decisions are routed into focused follow-up or G5 packet prep only. This route plan never promotes material PASS, ParamHairFront, Mini Cubism, or real Cubism by itself.

## Next Action

- Apply only the focused G4 follow-up routes listed in this report.
- For the current Codex provisional path, resolve B4/B5 combined context before G5.
- Keep ParamHairFront hidden until independent front-hair child art passes motion-readiness.

## Routes

- `B1_CLEAN_BASE_UNDERPAINT` `ACCEPT_VISUAL_CANDIDATE_KEEP_MATERIAL_BLOCKED` -> `KEEP_AS_G4_VISUAL_CANDIDATE`: Keep this item as a G4 visual candidate while material PASS remains blocked.
- `B2_EYE_PACK` `ACCEPT_VISUAL_CANDIDATE_KEEP_MATERIAL_BLOCKED` -> `KEEP_AS_G4_VISUAL_CANDIDATE`: Keep this item as a G4 visual candidate while material PASS remains blocked.
- `B3_MOUTH_PACK_REVISION_V1` `ACCEPT_VISUAL_CANDIDATE_KEEP_MATERIAL_BLOCKED` -> `KEEP_AS_G4_VISUAL_CANDIDATE`: Keep this item as a G4 visual candidate while material PASS remains blocked.
- `B4_B5_COMBINED_CONTEXT` `REVISE_BEFORE_G5` -> `ROUTE_TO_B4_B5_FOCUSED_FOLLOWUP_BEFORE_G5`: Use the focused B4/B5 context rows for mask, anchor, draw-order, or mini-pass follow-up before G5.
- `G1_G2_64PART_CONTACT` `ACCEPT_VISUAL_CANDIDATE_KEEP_MATERIAL_BLOCKED` -> `KEEP_AS_G4_VISUAL_CANDIDATE`: Keep this item as a G4 visual candidate while material PASS remains blocked.

## Self Review

- `allowed_visual_decision_values_checked`: `True`
- `all_expected_rows_present`: `True`
- `all_decisions_non_pending`: `True`
- `all_g4_items_accepted`: `False`
- `has_pending_blocker`: `False`
- `has_focused_followup_path`: `True`
- `not_owner_approval`: `True`
- `material_pass_blocked`: `True`
- `validator_only_promotion_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`

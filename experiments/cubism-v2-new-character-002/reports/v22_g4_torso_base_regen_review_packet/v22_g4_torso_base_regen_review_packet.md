# Character 002 v22 G4 torso_base Regen/Review Packet

- status: `G4_TORSO_BASE_REGEN_REVIEW_PACKET_READY_MATERIAL_BLOCKED`
- review sheet: `experiments/cubism-v2-new-character-002/reports/v22_g4_torso_base_regen_review_packet/v22_g4_torso_base_regen_review_sheet.png`
- regen input: `experiments/cubism-v2-new-character-002/reports/v22_g4_torso_base_regen_review_packet/v22_g4_torso_base_regen_input_packet.json`
- remaining pre-G5 blockers: `1`
- G5 material acceptance: `BLOCKED_PENDING_TORSO_REVIEW_OR_REGENERATION`

## Metrics

- old v2 alpha coverage: `0.14019799`
- provisional alpha coverage: `0.20855403`
- P0 v2 alpha coverage: `0.05906725`
- P0/old coverage ratio: `0.4213131`

## Decision

torso_base remains the only pre-G5 blocker. The P0 v2 candidate is tighter than old v2, but the safe default route is a focused torso_base regeneration/review input, not material acceptance.

## Next Action

- Use the regen input packet to generate or review one torso_base replacement candidate.
- Normalize any returned candidate as full-canvas 2048 RGBA.
- Rebuild the P0/G4 readiness evidence only after torso overlay QA exists.
- Keep ParamHairFront hidden and keep G7/G8 blocked.

## Self Review

- `p0_decision_status`: `G4_P0_B5_FOLLOWUP_DECISION_READY_TORSO_REVIEW_REMAINING_MATERIAL_BLOCKED`
- `p0_torso_status`: `P0_TORSO_MINIPASS_V2_CANDIDATE_READY_FOR_G3_REVIEW`
- `b5_input_status`: `B5_PROVISIONAL_MINIPASS_INPUT_PACKET_READY`
- `b5_provisional_qa_status`: `B5_PROVISIONAL_MINIPASS_OVERLAY_QA_REVIEW_REQUIRED`
- `target_is_torso_base`: `True`
- `remaining_pre_g5_blocker_count`: `1`
- `regen_input_exists`: `True`
- `review_sheet_exists`: `True`
- `all_candidate_paths_exist`: `True`
- `all_candidates_rgba_2048`: `True`
- `p0_is_tighter_than_old_v2`: `True`
- `prompt_present`: `True`
- `acceptance_checks_present`: `True`
- `not_owner_approval`: `True`
- `material_pass_blocked`: `True`
- `validator_only_promotion_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`

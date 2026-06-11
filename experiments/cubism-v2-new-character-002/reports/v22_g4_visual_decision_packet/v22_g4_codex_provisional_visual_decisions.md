# Character 002 v22 G4 Codex Provisional Visual Decisions

- status: `G4_CODEX_PROVISIONAL_VISUAL_DECISIONS_READY_NO_OWNER_APPROVAL`
- source packet: `experiments/cubism-v2-new-character-002/reports/v22_g4_visual_decision_packet/v22_g4_visual_decision_packet.json`

## Summary

- `decision_count`: `5`
- `pending_count`: `0`
- `accepted_visual_candidate_count`: `4`
- `revise_before_g5_count`: `1`
- `regenerate_batch_or_context_count`: `0`
- `route_policy_counts`: `{'B1_CLEAN_BASE_UNDERPAINT_ACCEPT_CANDIDATE_KEEP_MATERIAL_BLOCKED': 1, 'B2_EYE_PACK_ACCEPT_CANDIDATE_KEEP_MATERIAL_BLOCKED': 1, 'B3_MOUTH_PACK_REVISION_V1_ACCEPT_CANDIDATE_KEEP_MATERIAL_BLOCKED': 1, 'B4_B5_CONTEXT_REVIEW_REVISE_BEFORE_G5': 1, 'G1_G2_64PART_CONTACT_ACCEPT_CANDIDATE_KEEP_MATERIAL_BLOCKED': 1}`
- `g4_visual_review_status`: `CODEX_PROVISIONAL_REVIEW_READY_NOT_OWNER_APPROVAL`
- `g5_material_acceptance_status`: `BLOCKED_CONTEXT_REVIEW_NOT_OWNER_APPROVAL`
- `material_pass_status`: `BLOCKED`
- `param_hair_front_status`: `HIDDEN_CONTRACT_ONLY`
- `g7_mini_cubism_status`: `BLOCKED`
- `g8_real_cubism_status`: `BLOCKED`

## Decision

Codex provisionally keeps B1, B2, B3, and the 64-part contact sheet as visual candidates while routing B4/B5 combined context to focused revision before G5.

## Rows

- `B1_CLEAN_BASE_UNDERPAINT` `ACCEPT_VISUAL_CANDIDATE_KEEP_MATERIAL_BLOCKED` `B1_CLEAN_BASE_UNDERPAINT_ACCEPT_CANDIDATE_KEEP_MATERIAL_BLOCKED`: Source report is already a pass-candidate or technical contact candidate, so keep it as a visual candidate while material PASS remains blocked.
- `B2_EYE_PACK` `ACCEPT_VISUAL_CANDIDATE_KEEP_MATERIAL_BLOCKED` `B2_EYE_PACK_ACCEPT_CANDIDATE_KEEP_MATERIAL_BLOCKED`: Source report is already a pass-candidate or technical contact candidate, so keep it as a visual candidate while material PASS remains blocked.
- `B3_MOUTH_PACK_REVISION_V1` `ACCEPT_VISUAL_CANDIDATE_KEEP_MATERIAL_BLOCKED` `B3_MOUTH_PACK_REVISION_V1_ACCEPT_CANDIDATE_KEEP_MATERIAL_BLOCKED`: Source report is already a pass-candidate or technical contact candidate, so keep it as a visual candidate while material PASS remains blocked.
- `B4_B5_COMBINED_CONTEXT` `REVISE_BEFORE_G5` `B4_B5_CONTEXT_REVIEW_REVISE_BEFORE_G5`: B4/B5 still has 33 context-review rows, so keep it out of G5 material acceptance and route focused follow-up only.
- `G1_G2_64PART_CONTACT` `ACCEPT_VISUAL_CANDIDATE_KEEP_MATERIAL_BLOCKED` `G1_G2_64PART_CONTACT_ACCEPT_CANDIDATE_KEEP_MATERIAL_BLOCKED`: Source report is already a pass-candidate or technical contact candidate, so keep it as a visual candidate while material PASS remains blocked.

## Self Review

- `source_packet_status`: `G4_VISUAL_DECISION_PACKET_READY_PENDING_REVIEW_MATERIAL_BLOCKED`
- `decision_count`: `5`
- `all_expected_rows_present`: `True`
- `allowed_visual_decision_values_checked`: `True`
- `no_pending_decisions`: `True`
- `has_b4_b5_revise_gate`: `True`
- `not_owner_approval`: `True`
- `material_pass_blocked`: `True`
- `validator_only_promotion_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`

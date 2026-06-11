# Character 002 v22 B5 Provisional Mini-Pass Overlay QA

- status: `B5_PROVISIONAL_MINIPASS_OVERLAY_QA_REVIEW_REQUIRED`
- QA sheet: `experiments/cubism-v2-new-character-002/reports/v22_b5_provisional_minipass_candidate/v22_b5_provisional_minipass_overlay_qa.png`

## Summary

- `target_count`: `3`
- `verdict_counts`: `{'PASS_DRAW_ORDER_MASK_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED': 2, 'REVIEW_REGENERATED_TORSO_UNDERPAINT': 1}`
- `previous_remaining_b5_revise_parts`: `['torso_base', 'shoulder_L', 'shoulder_R']`
- `remaining_review_parts`: `['torso_base', 'shoulder_L', 'shoulder_R']`
- `material_pass_status`: `BLOCKED`
- `param_hair_front_status`: `HIDDEN_CONTRACT_ONLY`
- `g7_mini_cubism_status`: `BLOCKED`
- `g8_real_cubism_status`: `BLOCKED`

## Entries

- `torso_base` `REVIEW_REGENERATED_TORSO_UNDERPAINT`: Torso was rebuilt from the B5 raw reference and is usable as a focused review candidate, but visual approval and overlay QA remain required.
- `shoulder_L` `PASS_DRAW_ORDER_MASK_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED`: Hair-occlusion alpha overlap dropped enough for draw-order/mask review, but this is not material approval.
- `shoulder_R` `PASS_DRAW_ORDER_MASK_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED`: Hair-occlusion alpha overlap dropped enough for draw-order/mask review, but this is not material approval.

## Self Review

- `candidate_status`: `B5_PROVISIONAL_MINIPASS_CANDIDATE_READY_FOR_OVERLAY_QA`
- `target_count`: `3`
- `has_torso_review_candidate`: `True`
- `shoulder_improvement_candidate_count`: `2`
- `has_blocked_material_gate`: `True`
- `validator_only_promotion_blocked`: `True`
- `not_owner_approval`: `True`
- `material_pass_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `qa_sheet_exists`: `True`
- `status`: `PASS`

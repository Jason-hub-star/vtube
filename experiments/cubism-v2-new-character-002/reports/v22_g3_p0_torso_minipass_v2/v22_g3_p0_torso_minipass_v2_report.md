# Character 002 v22 P0 Torso Minipass v2

- status: `P0_TORSO_MINIPASS_V2_CANDIDATE_READY_FOR_G3_REVIEW`
- QA sheet: `experiments/cubism-v2-new-character-002/reports/v22_g3_p0_torso_minipass_v2/v22_g3_p0_torso_minipass_v2_overlay_qa.png`
- contact sheet: `experiments/cubism-v2-new-character-002/reports/v22_g3_p0_torso_minipass_v2/v22_g3_p0_torso_minipass_v2_contact_sheet.png`

## Torso Metrics

- `old_bbox`: `[534, 915, 1547, 1927]`
- `new_bbox`: `[504, 874, 1500, 1342]`
- `old_alpha_coverage`: `0.20855403`
- `new_alpha_coverage`: `0.05906725`
- `old_alpha_sum`: `169789605`
- `new_alpha_sum`: `60697770`
- `alpha_sum_ratio`: `0.357488`
- `verdict`: `P0_TORSO_MINIPASS_V2_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED`
- `improvement_candidate`: `True`

## Self Review

- `g3_blocker_status`: `G3_B4_B5_BLOCKER_REDUCTION_PACKET_READY_PRIMARY_10_MATERIAL_BLOCKED`
- `current_b5_status`: `B5_PROVISIONAL_MINIPASS_CANDIDATE_READY_FOR_OVERLAY_QA`
- `entry_count`: `17`
- `all_layers_rgba`: `True`
- `all_layers_2048`: `True`
- `all_layers_nonempty`: `True`
- `torso_improvement_candidate`: `True`
- `old_alpha_coverage`: `0.20855403`
- `new_alpha_coverage`: `0.05906725`
- `alpha_sum_ratio`: `0.357488`
- `qa_sheet_exists`: `True`
- `contact_sheet_exists`: `True`
- `material_pass_blocked`: `True`
- `visual_promotion_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `not_owner_approval`: `True`
- `status`: `PASS`

## Decision

P0 torso minipass v2 is an improvement candidate because its alpha is tighter and derived from the B5 raw skin/upper-torso area, but it remains review-required and cannot promote material PASS.

## Next Action

- Use the v2 torso QA sheet to decide whether to rebuild the corrected 64-part manifest with this torso candidate.
- Keep G3 visual overlay blocked until P0 and P1 rows are resolved.
- Do not promote material PASS, ParamHairFront, Mini Cubism, or real Cubism from this candidate.

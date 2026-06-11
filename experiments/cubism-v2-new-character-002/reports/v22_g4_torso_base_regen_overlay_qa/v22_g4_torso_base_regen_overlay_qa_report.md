# v22 G4 torso_base Regen Overlay QA

- status: `G4_TORSO_BASE_REGEN_OVERLAY_QA_ROUTE_READY_MATERIAL_BLOCKED`
- QA sheet: `experiments/cubism-v2-new-character-002/reports/v22_g4_torso_base_regen_overlay_qa/v22_g4_torso_base_regen_overlay_qa.png`
- route: `USE_GENERATED_TORSO_FOR_NEXT_MANIFEST_REBUILD_KEEP_G5_BLOCKED`
- visual verdict: `ROUTE_GENERATED_TORSO_TO_NEXT_REBUILD_REVIEW_REQUIRED`
- material promotion: `BLOCKED`

## Metrics

- generated bbox: `[520, 880, 1539, 1688]`
- generated alpha coverage: `0.1204493`
- P0 v2 alpha coverage: `0.05906725`
- old v2 alpha coverage: `0.13814282`
- generated_vs_p0_bottom_extension_px: `346`
- generated_alpha_ratio_to_old: `0.87191864`

## Locks

- `not_owner_approval`: `True`
- `validator_only_promotion_blocked`: `True`
- `material_pass_status`: `BLOCKED`
- `g5_status`: `BLOCKED_PENDING_NEXT_MANIFEST_REBUILD_AND_SEPARATE_G5_ACCEPTANCE`
- `param_hair_front_status`: `HIDDEN_CONTRACT_ONLY`
- `g7_mini_cubism_status`: `BLOCKED`
- `g8_real_cubism_status`: `BLOCKED`

## Next Action

- Build a G4 torso-selected 64-part manifest variant that replaces only B5 torso_base with the generated candidate.
- Rerun corrected B4/B5 overlay QA against that manifest before any G5 material acceptance packet.
- Keep ParamHairFront hidden and keep G7/G8 blocked.

## Self Review

- `status`: `True`
- `generated_candidate_status`: `True`
- `generated_full_canvas_exists`: `True`
- `generated_full_canvas_rgba_2048`: `True`
- `generated_non_empty`: `True`
- `transparent_corners`: `True`
- `crop_contains_generated_bbox`: `True`
- `generated_extends_lower_than_p0`: `True`
- `generated_top_close_to_p0`: `True`
- `coverage_between_p0_and_old`: `True`
- `generated_under_old_coverage`: `True`
- `route_selected`: `True`
- `qa_sheet_exists`: `True`
- `not_owner_approval`: `True`
- `validator_only_promotion_blocked`: `True`
- `material_pass_blocked`: `True`
- `g5_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`

# Character 002 v22 G3 P1A B4 Back-Strand Anchor/Mask Probe

- status: `G3_P1A_B4_BACK_STRAND_ANCHOR_MASK_NUMERIC_PASS_CONTEXT_REVIEW_REQUIRED`
- review sheet: `experiments/cubism-v2-new-character-002/reports/v22_g3_p1a_b4_back_strand_anchor_mask_probe/v22_g3_p1a_b4_back_strand_anchor_mask_probe_sheet.png`
- override JSON: `experiments/cubism-v2-new-character-002/reports/v22_g3_p1a_b4_back_strand_anchor_mask_probe/v22_g3_p1a_b4_back_strand_anchor_mask_probe_overrides.json`

## Summary

- `target_count`: `2`
- `numeric_pass_count`: `2`
- `anchor_numeric_pass_count`: `2`
- `mask_support_numeric_pass_count`: `2`
- `sha256_unchanged_count`: `2`
- `remaining_primary_after_probe_count`: `0`
- `context_candidate_after_probe_count`: `2`
- `material_pass_status`: `BLOCKED`
- `param_hair_front_status`: `HIDDEN_CONTRACT_ONLY`
- `g3_visual_overlay_status`: `CONTEXT_REVIEW_REQUIRED_NOT_VISUAL_PASS`
- `g4_psd_import_prep_status`: `PREP_ONLY_BLOCKED`
- `g5_material_acceptance_status`: `BLOCKED`
- `g7_mini_cubism_status`: `BLOCKED`
- `g8_real_cubism_status`: `BLOCKED`

## Self Review

- `p1_reduction_status`: `G3_P1_B4_SECONDARY_HAIR_REDUCTION_PACKET_READY_REVIEW_REQUIRED`
- `b4_focused_review_status`: `B4_HAIR_FOCUSED_REVIEW_READY_PARAMHAIRFRONT_STILL_HIDDEN`
- `target_count`: `2`
- `numeric_pass_count`: `2`
- `anchor_numeric_pass_count`: `2`
- `mask_support_numeric_pass_count`: `2`
- `sha256_unchanged_count`: `2`
- `remaining_primary_after_probe_count`: `0`
- `context_candidate_after_probe_count`: `2`
- `override_json_exists`: `True`
- `review_sheet_exists`: `True`
- `all_layers_rgba`: `True`
- `all_layers_2048`: `True`
- `all_layers_nonempty`: `True`
- `material_pass_blocked`: `True`
- `visual_promotion_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `not_owner_approval`: `True`
- `status`: `PASS`

## Decision

The two P1A back-strand rows have numeric anchor/mask support evidence and are copied unchanged into a probe candidate directory. This can lower them to context review, but it is not a visual PASS or material approval.

## Next Action

- Build a combined G3 context overlay that includes P0 torso v2, P1A back-strand context candidates, and the remaining B4/B5 context rows.
- Keep material PASS, ParamHairFront, Mini Cubism, and real Cubism blocked until combined visual QA is accepted separately.

# Character 002 v22 G4 Compact Visual Review Surface

- status: `G4_COMPACT_VISUAL_REVIEW_SURFACE_READY_NOT_PASS`
- review sheet: `experiments/cubism-v2-new-character-002/reports/v22_g4_compact_visual_review_surface/v22_g4_compact_visual_review_surface.png`

## Review Items

- `B1_CLEAN_BASE_UNDERPAINT`: `B1_CODEX_VISUAL_QA_PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED` / `PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- `B2_EYE_PACK`: `B2_CODEX_OVERLAY_QA_PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED` / `PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- `B3_MOUTH_PACK_REVISION_V1`: `B3_REVISION_V1_CODEX_OVERLAY_QA_PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED` / `PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- `B4_B5_COMBINED_CONTEXT`: `G3_COMBINED_CONTEXT_OVERLAY_REVIEW_READY_MATERIAL_BLOCKED` / `CONTEXT_REVIEW_REQUIRED_NOT_PASS`
- `G1_G2_64PART_CONTACT`: `G3_P0_TORSO_V2_64PART_MANIFEST_TECHNICAL_PASS_REVIEW_REQUIRED` / `TECHNICAL_PASS_VISUAL_REVIEW_REQUIRED`

## Summary

- `review_item_count`: `5`
- `b1_b3_item_count`: `3`
- `b4_b5_context_item_count`: `1`
- `manifest_contact_item_count`: `1`
- `source_image_count`: `5`
- `source_report_count`: `5`
- `manifest_entry_count`: `64`
- `b4_b5_primary_remaining_count`: `0`
- `b4_b5_context_review_count`: `33`
- `promotion_blocker_count`: `2`
- `material_pass_status`: `BLOCKED`
- `param_hair_front_status`: `HIDDEN_CONTRACT_ONLY`
- `g4_visual_review_status`: `READY_FOR_VISUAL_ACCEPTANCE_NOT_PASS`
- `g5_material_acceptance_status`: `BLOCKED_CONTEXT_REVIEW_NOT_OWNER_APPROVAL`
- `g7_mini_cubism_status`: `BLOCKED`
- `g8_real_cubism_status`: `BLOCKED`

## Self Review

- `readiness_status`: `G4_G5_MATERIAL_PROMOTION_READINESS_BLOCKED_CONTEXT_REVIEW`
- `manifest_status`: `G3_P0_TORSO_V2_64PART_MANIFEST_TECHNICAL_PASS_REVIEW_REQUIRED`
- `combined_g3_status`: `G3_COMBINED_CONTEXT_OVERLAY_REVIEW_READY_MATERIAL_BLOCKED`
- `review_item_count`: `5`
- `all_source_images_exist`: `True`
- `all_source_reports_exist`: `True`
- `review_sheet_exists`: `True`
- `b4_b5_primary_remaining_count`: `0`
- `b4_b5_context_review_count`: `33`
- `requires_visual_acceptance`: `True`
- `material_pass_blocked`: `True`
- `validator_only_promotion_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `not_owner_approval`: `True`
- `status`: `PASS`

## Decision

A compact G4 visual review surface is ready. It combines B1 clean base, B2 eyes, B3 mouth revision v1, B4/B5 combined context overlay, and the 64-part contact sheet. This is not material PASS.

## Next Action

- Use this sheet for visual acceptance review of B1-B5 as a set.
- Only after visual acceptance should a separate G5 material acceptance packet be created.
- Keep ParamHairFront hidden, and keep G7/G8 blocked.

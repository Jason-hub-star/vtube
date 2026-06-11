# Character 002 v22 G4/G5 Material Promotion Readiness

- status: `G4_G5_MATERIAL_PROMOTION_READINESS_BLOCKED_CONTEXT_REVIEW`
- P0 torso v2 manifest: `experiments/cubism-v2-new-character-002/reports/v22_64part_p0_torso_v2_manifest/v22_64part_p0_torso_v2_manifest.json`
- combined G3 context overlay: `experiments/cubism-v2-new-character-002/reports/v22_g3_combined_context_overlay_review/v22_g3_combined_context_overlay_review_report.json`

## Gate Matrix

- `G1_64PART_COMPLETENESS`: `PASS_TECHNICAL` - technical prerequisite only
- `G2_FULL_CANVAS_RGBA_NORMALIZATION`: `PASS_TECHNICAL` - technical prerequisite only
- `G3_COMBINED_CONTEXT_OVERLAY`: `READY_CONTEXT_REVIEW_NOT_PASS` - blocks material PASS until context review is accepted separately
- `G4_CONTACT_SHEET_VISUAL_QA`: `READY_FOR_REVIEW_NOT_PASS` - requires explicit visual acceptance; validator PASS is insufficient
- `G5_MATERIAL_ACCEPTANCE`: `BLOCKED_CONTEXT_REVIEW_NOT_OWNER_APPROVAL` - do not build/promote import_ready.psd
- `G7_MINI_CUBISM_DIAGNOSTIC`: `BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE` - Mini Cubism cannot replace real Cubism
- `G8_REAL_CUBISM_AUTHORING`: `BLOCKED_UNTIL_G5_AND_REAL_CUBISM_AUTHORING` - not started

## Batch Gates

- `B1`: `B1_CODEX_VISUAL_QA_PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- `B2`: `B2_CODEX_OVERLAY_QA_PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- `B3_REVISION_V1`: `B3_REVISION_V1_CODEX_OVERLAY_QA_PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED`

## Summary

- `manifest_status`: `G3_P0_TORSO_V2_64PART_MANIFEST_TECHNICAL_PASS_REVIEW_REQUIRED`
- `combined_g3_status`: `G3_COMBINED_CONTEXT_OVERLAY_REVIEW_READY_MATERIAL_BLOCKED`
- `required_part_count`: `64`
- `manifest_entry_count`: `64`
- `source_batch_counts`: `{'B1': 9, 'B2': 14, 'B3_REVISION_V1': 8, 'B4': 16, 'B5': 17}`
- `group_counts`: `{'body': 10, 'brow': 2, 'clothing': 4, 'eye_L': 8, 'eye_R': 8, 'face_base': 8, 'hair': 16, 'mouth': 8}`
- `visual_gate_counts`: `{'B4_FRONT_HAIR_MOTION_READINESS_CANDIDATE_REVIEW_REQUIRED': 7, 'B4_SECONDARY_DRAW_ORDER_OR_MASK_REVIEW_REQUIRED': 9, 'B5_COPIED_FROM_REFINED_MASK_V2_REVIEW_REQUIRED': 14, 'P0_TORSO_MINIPASS_V2_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED': 1, 'PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED': 31, 'PASS_DRAW_ORDER_MASK_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED': 2}`
- `b1_b3_candidate_human_required_count`: `3`
- `b4_b5_primary_remaining_count`: `0`
- `b4_b5_context_review_count`: `33`
- `promotion_blocker_count`: `2`
- `material_pass_status`: `BLOCKED`
- `param_hair_front_status`: `HIDDEN_CONTRACT_ONLY`
- `g4_contact_sheet_visual_qa_status`: `READY_FOR_REVIEW_NOT_PASS`
- `g5_material_acceptance_status`: `BLOCKED_CONTEXT_REVIEW_NOT_OWNER_APPROVAL`
- `g7_mini_cubism_status`: `BLOCKED`
- `g8_real_cubism_status`: `BLOCKED`

## Promotion Blockers

- `B1_B2_B3_PASS_CANDIDATES_STILL_HUMAN_REVIEW_REQUIRED`
- `B4_B5_COMBINED_CONTEXT_REVIEW_REQUIRED`

## Self Review

- `technical_manifest_pass`: `True`
- `all_b1_b3_batch_reports_present`: `True`
- `b1_b3_human_review_required_count`: `3`
- `b4_b5_primary_remaining_count`: `0`
- `b4_b5_context_review_count`: `33`
- `promotion_blocker_count`: `2`
- `has_gate_matrix`: `True`
- `material_pass_blocked`: `True`
- `validator_only_promotion_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `not_owner_approval`: `True`
- `status`: `PASS`

## Decision

G4/G5 material promotion is not allowed yet. The 64-part manifest is technically complete and B4/B5 primary blockers are reduced to zero, but B1-B3 remain pass-candidate/human-review-required and all 33 B4/B5 rows remain context-review evidence. Validator or numeric PASS must not be promoted to material PASS.

## Next Action

- Build or use a compact G4 visual review surface from the P0 manifest contact sheet and combined G3 overlay.
- Only after explicit visual acceptance should a separate G5 material acceptance packet be created.
- Keep ParamHairFront hidden and keep G7/G8 blocked.

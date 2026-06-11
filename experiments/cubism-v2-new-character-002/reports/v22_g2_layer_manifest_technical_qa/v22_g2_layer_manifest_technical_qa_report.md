# Character 002 v22 G2 Layer Manifest Technical QA

- status: `G2_LAYER_MANIFEST_TECHNICAL_QA_PASS_MATERIAL_STILL_BLOCKED`
- corrected manifest: `experiments/cubism-v2-new-character-002/reports/v22_64part_corrected_b4_b5_manifest/v22_64part_corrected_b4_b5_manifest.json`
- G2-G5 prep packet: `experiments/cubism-v2-new-character-002/reports/v22_g2_g5_material_qa_prep/v22_g2_g5_material_qa_prep_packet.json`

## Summary

- `manifest_status`: `G1_64PART_CORRECTED_B4_B5_MANIFEST_TECHNICAL_PASS_REVIEW_REQUIRED`
- `prep_status`: `G2_G5_MATERIAL_QA_PREP_PACKET_READY_BLOCKED_BY_CODEX_TRIAGE`
- `spec_status`: `PASS_SPEC_READY_FOR_IMAGE_GENERATION_PLANNING`
- `required_part_count`: `64`
- `manifest_entry_count`: `64`
- `unique_manifest_part_count`: `64`
- `missing_part_count`: `0`
- `extra_part_count`: `0`
- `duplicate_part_count`: `0`
- `failed_entry_count`: `0`
- `group_counts`: `{'body': 10, 'brow': 2, 'clothing': 4, 'eye_L': 8, 'eye_R': 8, 'face_base': 8, 'hair': 16, 'mouth': 8}`
- `source_batch_counts`: `{'B1': 9, 'B2': 14, 'B3_REVISION_V1': 8, 'B4': 16, 'B5': 17}`
- `draw_order_band_counts`: `{'body_back': 4, 'body_front': 2, 'body_mid': 4, 'brow_front': 2, 'clothing_front': 2, 'clothing_mid': 2, 'eye_back': 4, 'eye_front': 8, 'eye_mid': 4, 'face_back': 2, 'face_front': 5, 'face_mid': 1, 'hair_back': 5, 'hair_front': 7, 'hair_side': 4, 'mouth_back': 1, 'mouth_front': 5, 'mouth_mid': 2}`
- `forbidden_reuse_path_hit_count`: `0`
- `sha256_recorded_count`: `64`
- `material_pass_status`: `BLOCKED`
- `param_hair_front_status`: `HIDDEN_CONTRACT_ONLY`
- `g3_visual_overlay_status`: `BLOCKED_REVIEW_REQUIRED`
- `g4_psd_import_prep_status`: `PREP_ONLY_BLOCKED`
- `g5_material_acceptance_status`: `BLOCKED`
- `g7_mini_cubism_status`: `BLOCKED`
- `g8_real_cubism_status`: `BLOCKED`

## Lock Checks

- `active_controls_match_v21_supported_subset`: `True`
- `param_hair_front_hidden`: `True`
- `eye_open_027_policy_present`: `True`
- `mouth_open_085_policy_present`: `True`
- `mini_cubism_not_real_cubism`: `True`

## Errors

_none_

## Self Review

- `all_required_parts_present`: `True`
- `no_extra_parts`: `True`
- `no_duplicate_ids`: `True`
- `all_entries_pass`: `True`
- `group_counts_match_spec`: `True`
- `forbidden_reuse_path_hit_count`: `0`
- `sha256_recorded_count`: `64`
- `lock_checks_all_pass`: `True`
- `material_pass_blocked`: `True`
- `visual_promotion_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`

## Decision

G2 layer-manifest technical QA passes for the corrected 64-part manifest, but this is technical evidence only. It does not promote visual QA, material acceptance, Mini Cubism, or real Cubism.

## Next Action

- Keep G3 visual overlay QA blocked until B4/B5 hard and hold review rows are resolved.
- Do not build/promote import_ready.psd from this QA alone.
- Keep ParamHairFront hidden and G7/G8 blocked.

# Character 002 v22 G2-G5 Material QA Prep Packet

- status: `G2_G5_MATERIAL_QA_PREP_PACKET_READY_BLOCKED_BY_CODEX_TRIAGE`
- corrected manifest: `experiments/cubism-v2-new-character-002/reports/v22_64part_corrected_b4_b5_manifest/v22_64part_corrected_b4_b5_manifest.json`
- Codex visual triage: `experiments/cubism-v2-new-character-002/reports/v22_64part_corrected_b4_b5_manifest/v22_corrected_b4_b5_codex_visual_triage.json`

## Scope

- `G2_LAYER_MANIFEST_TECHNICAL_QA`: `PREP_READY` - Validate 64 full-canvas RGBA entries, group counts, layer paths, bbox, alpha coverage, and draw-order bands.
- `G3_VISUAL_OVERLAY_QA`: `BLOCKED_REVIEW_REQUIRED` - Use corrected B4/B5 overlay QA and Codex triage as visual review input; do not promote material PASS.
- `G4_PSD_IMPORT_PREP`: `PREP_ONLY_BLOCKED` - Prepare import ordering/checklist only; do not build or promote import_ready.psd from review-required B4/B5.
- `G5_MATERIAL_ACCEPTANCE`: `BLOCKED` - Wait for resolved B4/B5 hard/hold review or an explicit later promotion gate.

## Summary

- `manifest_status`: `G1_64PART_CORRECTED_B4_B5_MANIFEST_TECHNICAL_PASS_REVIEW_REQUIRED`
- `triage_status`: `CORRECTED_B4_B5_CODEX_VISUAL_TRIAGE_READY_G2_G5_PREP_BLOCKED`
- `required_part_count`: `64`
- `manifest_entry_count`: `64`
- `source_batch_counts`: `{'B1': 9, 'B2': 14, 'B3_REVISION_V1': 8, 'B4': 16, 'B5': 17}`
- `group_counts`: `{'body': 10, 'brow': 2, 'clothing': 4, 'eye_L': 8, 'eye_R': 8, 'face_base': 8, 'hair': 16, 'mouth': 8}`
- `auto_candidate_count`: `9`
- `hold_review_count`: `23`
- `hard_review_count`: `1`
- `ready_gate_count`: `1`
- `blocked_or_prep_only_gate_count`: `3`

## Blockers

- `hard_review_parts`: `['torso_base']`
- `hold_review_part_count`: `23`
- `auto_candidate_part_count`: `9`
- `material_pass_status`: `BLOCKED`
- `param_hair_front_status`: `HIDDEN_CONTRACT_ONLY`
- `g7_mini_cubism_status`: `BLOCKED`
- `g8_real_cubism_status`: `BLOCKED`

## Self Review

- `manifest_status`: `G1_64PART_CORRECTED_B4_B5_MANIFEST_TECHNICAL_PASS_REVIEW_REQUIRED`
- `triage_status`: `CORRECTED_B4_B5_CODEX_VISUAL_TRIAGE_READY_G2_G5_PREP_BLOCKED`
- `manifest_entry_count`: `64`
- `triage_entry_count`: `33`
- `hard_review_count`: `1`
- `hold_review_count`: `23`
- `auto_candidate_count`: `9`
- `has_g2_g5_scope`: `True`
- `technical_prep_ready`: `True`
- `material_pass_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `not_owner_approval`: `True`
- `status`: `PASS`

## Decision

G2-G5 material QA can be prepared as a checklist and technical validation packet, but the corrected B4/B5 Codex triage blocks material acceptance, ParamHairFront, Mini Cubism, and real Cubism.

## Next Action

- Run only G2 layer-manifest technical QA from the corrected 64-part manifest.
- Resolve B4/B5 hard and hold review rows before G4 PSD promotion or G5 material acceptance.
- Keep G7/G8 blocked until G5 material acceptance has independent visual evidence.

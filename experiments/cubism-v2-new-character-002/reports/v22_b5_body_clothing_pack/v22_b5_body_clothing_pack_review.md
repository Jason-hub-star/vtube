# Character 002 v22 B5 Body/Clothing Pack Review

- status: `B5_RAW_BODY_CLOTHING_PACK_CANDIDATE_READY_FOR_EXTRACTION_HUMAN_REVIEW_REQUIRED`
- source image: `experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png`
- B1 clean-base reference: `experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/raw_outputs/b1_clean_base_underpaint_reference_001.png`
- B5 raw image: `experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/raw_outputs/b5_body_clothing_pack_reference_001.png`
- contact sheet: `experiments/cubism-v2-new-character-002/reports/v22_b5_body_clothing_pack/v22_b5_body_clothing_pack_contact_sheet.png`
- imagegen mode: `built_in_image_gen`

## Expected B5 Parts

- `torso_base`
- `neck`
- `shoulder_L`
- `shoulder_R`
- `arm_L_upper_simple`
- `arm_R_upper_simple`
- `collar_front`
- `collar_shadow`
- `chest_cloth_base`
- `chest_cloth_shadow`
- `brow_L`
- `brow_R`
- `nose`
- `cheek_L`
- `cheek_R`
- `face_shadow_L`
- `face_shadow_R`

## Allowed Inputs

- `experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png`
- `experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/raw_outputs/b1_clean_base_underpaint_reference_001.png`
- `experiments/cubism-v2-new-character-002/reports/v22_64part_generation_spec/v22_64part_generation_spec.json`
- `experiments/cubism-v2-new-character-002/reports/v22_64part_generation_input_packet/v22_64part_generation_input_packet.json`
- `experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_visual_qa_report.json`

## Forbidden Existing Body/Clothing Assets

- `FORBIDDEN_AS_B5_INPUT` `experiments/cubism-v2-new-character-002/material_pack_first_v0/normalized_layers` exists `True`
- `FORBIDDEN_AS_B5_INPUT` `experiments/cubism-v2-new-character-002/model_edit_v13_scaled_eye_mouth_preview/mini_cubism_diagnostic_project/parts` exists `True`
- `FORBIDDEN_AS_B5_INPUT` `experiments/cubism-v2-new-character-002/model_edit_v21_supported_rig_smoke_preview/mini_cubism_diagnostic_project/parts` exists `True`
- `FORBIDDEN_AS_B5_INPUT` `experiments/cubism-v2-new-character-001/material_pack_v0/production_layers` exists `True`
- `FORBIDDEN_AS_B5_INPUT` `experiments/cubism-v2-new-character-001/material_pack_v0/production_layers_roi_semantic_remask_v1` exists `True`

## Visual Checks

- `PASS_RECORDED` `new_generation_no_existing_body_clothing_asset_reuse`: B5 raw sheet was generated via built-in imagegen after the no-existing-assets instruction; prior normalized/model_edit/body-clothing material folders are recorded as forbidden inputs.
- `PASS_CANDIDATE` `same_character_outfit_style`: The sheet keeps the white ribbed off-shoulder sweater, shoulder straps, soft skin shading, and simple upper-body design from the source.
- `PASS_CANDIDATE` `body_clothing_scope_visible`: Torso, neck, shoulders, simple sleeves/upper arms, collar, chest cloth, and cloth shadow candidates are visibly present.
- `PASS_CANDIDATE` `face_detail_scope_visible`: Left/right brows, subtle nose, cheek blush, and side face-shadow candidates are present as separate material references.
- `REVIEW_VISUALLY` `breath_body_angle_support`: The body/clothing pieces include underpaint-like coverage, but extraction/overlay QA must confirm breath and body-angle motion will not expose holes.
- `REVISE_BEFORE_LAYER_PROMOTION` `extraction_readiness`: The sheet is RGB on a light background and includes a full torso context pose; it must be extracted/masked before full-canvas RGBA B5 material can be claimed.
- `REQUIRED` `human_visual_review`: 주인님 must approve outfit identity, body proportions, face-detail subtlety, and body/clothing readability before B5 is promoted beyond raw candidate.

## Decision

Keep this as the v22 B5 newly generated body/clothing-pack raw candidate. It can feed B5 extraction planning, but it is not yet separated full-canvas RGBA material and does not prove body-motion or real Cubism success.

## Next Action

- Extract/normalize B5 components into full-canvas RGBA candidates for the 17 expected body, clothing, brow, nose, cheek, and face-shadow parts.
- Run B5 contact-sheet and overlay QA against the G0 source and B1 clean-base silhouette.
- Only after B1-B5 visual QA acceptance, build the 64-part manifest and continue to G1-G5 material QA.

## Self Review

- `source_exists`: `True`
- `b1_raw_exists`: `True`
- `b5_raw_exists`: `True`
- `built_in_imagegen_source_exists`: `True`
- `source_size`: `[1254, 1254]`
- `b1_raw_size`: `[1254, 1254]`
- `b5_raw_size`: `[1536, 1024]`
- `b5_mode`: `RGB`
- `expected_b5_part_count`: `17`
- `allowed_input_count`: `5`
- `forbidden_existing_body_clothing_asset_count`: `5`
- `visual_check_count`: `7`
- `has_human_required_gate`: `True`
- `has_breath_body_angle_review_gate`: `True`
- `has_face_detail_scope`: `True`
- `forbidden_assets_not_output_path`: `True`
- `status`: `PASS`

# Character 002 v22 B4 Hair Pack Review

- status: `B4_RAW_HAIR_PACK_CANDIDATE_READY_FOR_EXTRACTION_HUMAN_REVIEW_REQUIRED`
- source image: `experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png`
- B1 clean-base reference: `experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/raw_outputs/b1_clean_base_underpaint_reference_001.png`
- B4 raw image: `experiments/cubism-v2-new-character-002/v22_b4_hair_pack/raw_outputs/b4_hair_pack_reference_001.png`
- contact sheet: `experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_hair_pack_contact_sheet.png`
- imagegen mode: `built_in_image_gen`

## Expected B4 Parts

- `hair_back_base`
- `hair_back_strand_L`
- `hair_back_strand_R`
- `hair_back_center`
- `hair_front_center`
- `hair_front_L`
- `hair_front_R`
- `hair_front_side_L`
- `hair_front_side_R`
- `hair_front_tip_L`
- `hair_front_tip_R`
- `hair_side_L_outer`
- `hair_side_L_inner`
- `hair_side_R_outer`
- `hair_side_R_inner`
- `hair_back_underpaint`

## Allowed Inputs

- `experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png`
- `experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/raw_outputs/b1_clean_base_underpaint_reference_001.png`
- `experiments/cubism-v2-new-character-002/reports/v22_64part_generation_spec/v22_64part_generation_spec.json`
- `experiments/cubism-v2-new-character-002/reports/v22_64part_generation_input_packet/v22_64part_generation_input_packet.json`
- `experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_visual_qa_report.json`

## Forbidden Existing Hair Assets

- `FORBIDDEN_AS_B4_INPUT` `experiments/cubism-v2-new-character-002/material_pack_first_v0/normalized_layers` exists `True`
- `FORBIDDEN_AS_B4_INPUT` `experiments/cubism-v2-new-character-002/model_edit_v13_scaled_eye_mouth_preview/mini_cubism_diagnostic_project/parts` exists `True`
- `FORBIDDEN_AS_B4_INPUT` `experiments/cubism-v2-new-character-002/model_edit_v19_generated_eye_preview/mini_cubism_diagnostic_project/parts` exists `True`
- `FORBIDDEN_AS_B4_INPUT` `experiments/cubism-v2-new-character-002/model_edit_v20_manual_eye_anchor_preview/mini_cubism_diagnostic_project/parts` exists `True`
- `FORBIDDEN_AS_B4_INPUT` `experiments/cubism-v2-new-character-002/model_edit_v21_supported_rig_smoke_preview/mini_cubism_diagnostic_project/parts` exists `True`

## Visual Checks

- `PASS_RECORDED` `new_generation_no_existing_hair_asset_reuse`: B4 raw sheet was generated via built-in imagegen after the no-existing-assets instruction; prior normalized/model_edit parts are recorded as forbidden inputs.
- `PASS_CANDIDATE` `same_character_hair_style`: The sheet keeps warm brown long hair, crown swirl, glossy highlights, line thickness, and the source bang/side-lock silhouette.
- `PASS_CANDIDATE` `front_hair_children_visible`: Front-center, left/right bang, front-side, and tip candidates are visibly present as separable groups.
- `PASS_CANDIDATE` `side_back_hair_groups_visible`: Back base, side locks, and long strand groups are visible with usable strand boundaries for later physics extraction.
- `HOLD_UNSUPPORTED_CONTROL` `hairfront_contract_gate`: ParamHairFront stays hidden/contract-only until extracted hair_front_* full-canvas RGBA parts pass overlay and motion QA.
- `REVISE_BEFORE_LAYER_PROMOTION` `extraction_readiness`: The sheet is RGB on a light background and includes full-pose/context art; it must be extracted/masked before full-canvas RGBA B4 material can be claimed.
- `REQUIRED` `human_visual_review`: 주인님 must approve hairstyle identity, front bang occlusion, strand scale, and side/back hair readability before B4 is promoted beyond raw candidate.

## Decision

Keep this as the v22 B4 newly generated hair-pack raw candidate. It can feed B4 extraction planning, but it is not yet separated full-canvas RGBA hair material and does not unlock ParamHairFront or real Cubism success claims.

## Next Action

- Extract/normalize B4 components into full-canvas RGBA candidates for the 16 expected hair parts.
- Run B4 contact-sheet and overlay QA against the G0 source and B1 clean-base silhouette.
- Keep ParamHairFront hidden until hair_front_* child parts are extracted, aligned, and accepted by visual QA.

## Self Review

- `source_exists`: `True`
- `b1_raw_exists`: `True`
- `b4_raw_exists`: `True`
- `built_in_imagegen_source_exists`: `True`
- `source_size`: `[1254, 1254]`
- `b1_raw_size`: `[1254, 1254]`
- `b4_raw_size`: `[1536, 1024]`
- `b4_mode`: `RGB`
- `expected_b4_part_count`: `16`
- `allowed_input_count`: `5`
- `forbidden_existing_hair_asset_count`: `5`
- `visual_check_count`: `7`
- `has_human_required_gate`: `True`
- `has_hairfront_contract_gate`: `True`
- `has_front_hair_children_scope`: `True`
- `forbidden_assets_not_output_path`: `True`
- `status`: `PASS`

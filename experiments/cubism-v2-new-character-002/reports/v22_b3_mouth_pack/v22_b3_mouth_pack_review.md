# Character 002 v22 B3 Mouth Pack Review

- status: `B3_RAW_MOUTH_PACK_CANDIDATE_READY_FOR_EXTRACTION_HUMAN_REVIEW_REQUIRED`
- source image: `experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png`
- B1 clean-base reference: `experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/raw_outputs/b1_clean_base_underpaint_reference_001.png`
- B3 raw image: `experiments/cubism-v2-new-character-002/v22_b3_mouth_pack/raw_outputs/b3_mouth_pack_reference_001.png`
- contact sheet: `experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack/v22_b3_mouth_pack_contact_sheet.png`
- imagegen mode: `built_in_image_gen`

## Allowed Inputs

- `experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png`
- `experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/raw_outputs/b1_clean_base_underpaint_reference_001.png`
- `experiments/cubism-v2-new-character-002/reports/v22_64part_generation_input_packet/v22_64part_generation_input_packet.json`
- `experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_visual_qa_report.json`
- `experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_overlay_qa_report.json`

## Forbidden Existing Mouth Assets

- `FORBIDDEN_AS_B3_INPUT` `experiments/cubism-v2-new-character-002/generated_mouth_v10` exists `True`
- `FORBIDDEN_AS_B3_INPUT` `experiments/cubism-v2-new-character-002/generated_mouth_v11` exists `True`
- `FORBIDDEN_AS_B3_INPUT` `experiments/cubism-v2-new-character-002/generated_mouth_v12` exists `True`
- `FORBIDDEN_AS_B3_INPUT` `experiments/cubism-v2-new-character-002/model_edit_v4_mouth_alpha` exists `True`
- `FORBIDDEN_AS_B3_INPUT` `experiments/cubism-v2-new-character-002/model_edit_v4_strict_mouth` exists `True`
- `FORBIDDEN_AS_B3_INPUT` `experiments/cubism-v2-new-character-002/model_edit_v7_smooth_mouth_preview` exists `True`
- `FORBIDDEN_AS_B3_INPUT` `experiments/cubism-v2-new-character-002/model_edit_v8_existing_mouth_tuned_preview` exists `True`
- `FORBIDDEN_AS_B3_INPUT` `experiments/cubism-v2-new-character-002/model_edit_v9_all_mouth_enabled_preview` exists `True`
- `FORBIDDEN_AS_B3_INPUT` `experiments/cubism-v2-new-character-002/model_edit_v10_generated_mouth_eye_clamp_preview` exists `True`
- `FORBIDDEN_AS_B3_INPUT` `experiments/cubism-v2-new-character-002/model_edit_v11_generated_mouth_eye_clamp_preview` exists `True`
- `FORBIDDEN_AS_B3_INPUT` `experiments/cubism-v2-new-character-002/model_edit_v12_generated_mouth_eye_clamp_preview` exists `True`
- `FORBIDDEN_AS_B3_INPUT` `experiments/cubism-v2-new-character-002/model_edit_v13_scaled_eye_mouth_preview` exists `True`

## Visual Checks

- `PASS_RECORDED` `new_generation_no_existing_mouth_asset_reuse`: B3 raw sheet was generated via built-in imagegen after the no-existing-assets rule; prior generated/model_edit mouth folders are recorded as forbidden inputs.
- `PASS_CANDIDATE` `same_character_mouth_style`: The sheet keeps the source character's soft pink mouth style, subtle highlights, and adult-cute expression language.
- `PASS_CANDIDATE` `mouthopen_keypose_rows`: Closed, small-open, mid-open, and wide-open reference states are visibly present.
- `PASS_CANDIDATE` `coordinated_internals`: The visible open-mouth states draw inner mouth, teeth, and tongue as a coherent mouth packet instead of isolated helper overlays.
- `REVIEW_VISUALLY` `wide_mouth_limit`: The wide-open reference is expressive and coherent, but must be reviewed against the v21/v13 MouthOpenY max 0.85 restraint before promotion.
- `REVISE_BEFORE_LAYER_PROMOTION` `extraction_readiness`: The sheet is RGB on a white background with face crops in the top rows, so it needs extraction/masking before full-canvas RGBA B3 material can be claimed.
- `REQUIRED` `human_visual_review`: 주인님 must approve mouth style, anchor consistency, and wide-mouth restraint before B3 is promoted beyond raw candidate.

## Decision

Keep this as the v22 B3 newly generated mouth-pack raw candidate. It can feed B3 extraction planning, but it is not yet separated full-canvas RGBA mouth material and does not unlock Mini Cubism or real Cubism success claims.

## Next Action

- Extract/normalize B3 components into full-canvas RGBA candidates: mouth_line, inner, lip masks, teeth, tongue, corners, and four MouthOpenY reference states.
- Run B3 contact-sheet and overlay QA against the G0 source and B1 clean mouth base.
- If wide mouth is too large or internals look pasted after extraction, regenerate B3 instead of reusing old v10/v12/v13 mouth assets.

## Self Review

- `source_exists`: `True`
- `b1_raw_exists`: `True`
- `b3_raw_exists`: `True`
- `built_in_imagegen_source_exists`: `True`
- `source_size`: `(1254, 1254)`
- `b1_raw_size`: `(1254, 1254)`
- `b3_raw_size`: `(1254, 1254)`
- `b3_mode`: `RGB`
- `allowed_input_count`: `5`
- `forbidden_existing_mouth_asset_count`: `12`
- `visual_check_count`: `7`
- `has_human_required_gate`: `True`
- `has_wide_mouth_review_gate`: `True`
- `forbidden_assets_not_output_path`: `True`
- `status`: `PASS`

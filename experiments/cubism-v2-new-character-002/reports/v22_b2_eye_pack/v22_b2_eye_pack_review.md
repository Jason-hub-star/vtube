# Character 002 v22 B2 Eye Pack Review

- status: `B2_RAW_EYE_PACK_CANDIDATE_READY_FOR_EXTRACTION_HUMAN_REVIEW_REQUIRED`
- source image: `experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png`
- B1 clean-base reference: `experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/raw_outputs/b1_clean_base_underpaint_reference_001.png`
- B2 raw image: `experiments/cubism-v2-new-character-002/v22_b2_eye_pack/raw_outputs/b2_eye_pack_reference_001.png`
- contact sheet: `experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_eye_pack_contact_sheet.png`
- imagegen mode: `built_in_image_gen`

## Allowed Inputs

- `experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png`
- `experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/raw_outputs/b1_clean_base_underpaint_reference_001.png`
- `experiments/cubism-v2-new-character-002/reports/v22_64part_generation_input_packet/v22_64part_generation_input_packet.json`
- `experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_visual_qa_report.json`

## Forbidden Existing Eye Assets

- `FORBIDDEN_AS_B2_INPUT` `experiments/cubism-v2-new-character-002/generated_eye_v19` exists `True`
- `FORBIDDEN_AS_B2_INPUT` `experiments/cubism-v2-new-character-002/model_edit_v14_eye_detail_inbetween_preview/mini_cubism_diagnostic_project/parts` exists `True`
- `FORBIDDEN_AS_B2_INPUT` `experiments/cubism-v2-new-character-002/model_edit_v15_eye_nose_position_preview/mini_cubism_diagnostic_project/parts` exists `True`
- `FORBIDDEN_AS_B2_INPUT` `experiments/cubism-v2-new-character-002/model_edit_v19_generated_eye_preview/mini_cubism_diagnostic_project/parts` exists `True`
- `FORBIDDEN_AS_B2_INPUT` `experiments/cubism-v2-new-character-002/model_edit_v20_manual_eye_anchor_preview/mini_cubism_diagnostic_project/parts` exists `True`
- `FORBIDDEN_AS_B2_INPUT` `experiments/cubism-v2-new-character-002/model_edit_v21_supported_rig_smoke_preview/mini_cubism_diagnostic_project/parts` exists `True`

## Visual Checks

- `PASS_RECORDED` `new_generation_no_existing_eye_asset_reuse`: B2 raw sheet was generated via built-in imagegen after the no-existing-assets instruction; v19/v20/v21 eye directories are recorded as forbidden inputs.
- `PASS_CANDIDATE` `same_character_eye_style`: The sheet keeps lavender-purple irises, soft anime lash styling, and front-facing adult-cute expression consistent with the G0 source.
- `PASS_CANDIDATE` `eyeopen_keypose_rows`: Open, half-open, natural-close, and closed rows are visibly present for left/right eye pairs.
- `PASS_CANDIDATE` `fixed_white_and_locked_iris_cluster_scope`: The component area includes isolated sclera and coherent iris+pupil+highlight clusters, matching the v21 guardrail that whites stay fixed while iris detail moves together.
- `REVISE_BEFORE_LAYER_PROMOTION` `extraction_readiness`: The sheet is RGB on a white background with skin/hair context in the top pose rows, so it needs extraction/masking before full-canvas RGBA B2 material can be claimed.
- `REQUIRED` `human_visual_review`: 주인님 must approve the eye style and natural-close feel before B2 is promoted beyond raw candidate.

## Decision

Keep this as the v22 B2 newly generated eye-pack raw candidate. It can feed B2 extraction planning, but it is not yet separated full-canvas RGBA eye material and does not unlock Mini Cubism or real Cubism success claims.

## Next Action

- Extract/normalize B2 components into full-canvas RGBA candidates: eye_L/R_white, iris cluster, upper lash, lower lash, closed lid, eyelid shadow, and natural-close keypose support.
- Run B2 contact-sheet and overlay QA against the G0 source and B1 clean-base sockets.
- If iris/pupil/highlight drift or fixed whites fail in extraction, regenerate B2 instead of reusing old v19/v20/v21 eye assets.

## Self Review

- `source_exists`: `True`
- `b1_raw_exists`: `True`
- `b2_raw_exists`: `True`
- `built_in_imagegen_source_exists`: `True`
- `source_size`: `(1254, 1254)`
- `b1_raw_size`: `(1254, 1254)`
- `b2_raw_size`: `(1254, 1254)`
- `b2_mode`: `RGB`
- `allowed_input_count`: `4`
- `forbidden_existing_eye_asset_count`: `6`
- `visual_check_count`: `6`
- `has_human_required_gate`: `True`
- `forbidden_assets_not_output_path`: `True`
- `status`: `PASS`

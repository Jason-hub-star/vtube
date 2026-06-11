# Character 002 v22 B1 Clean Base Layer Pack

- status: `B1_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA`
- output layers: `experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/normalized_layers`
- contact sheet: `experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_layer_pack_contact_sheet.png`
- overlay sheet: `experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_layer_pack_overlay_qa.png`

## Outputs

- `face_base`: `PASS_LAYER_NONEMPTY`, coverage `0.111241`, bbox `[640, 350, 1381, 1239]`
- `face_underpaint_L`: `PASS_LAYER_NONEMPTY`, coverage `0.032362`, bbox `[640, 497, 975, 1078]`
- `face_underpaint_R`: `PASS_LAYER_NONEMPTY`, coverage `0.029257`, bbox `[1074, 497, 1381, 1078]`
- `eye_L_underpaint`: `PASS_LAYER_NONEMPTY`, coverage `0.009752`, bbox `[710, 580, 976, 776]`
- `eye_R_underpaint`: `PASS_LAYER_NONEMPTY`, coverage `0.009752`, bbox `[1073, 580, 1339, 776]`
- `mouth_base_clean_reference`: `PASS_LAYER_NONEMPTY`, coverage `0.0071`, bbox `[900, 790, 1151, 941]`
- `body_underpaint`: `PASS_LAYER_NONEMPTY`, coverage `0.266661`, bbox `[355, 1136, 1694, 2048]`
- `neck_shadow_underpaint`: `PASS_LAYER_NONEMPTY`, coverage `0.039044`, bbox `[802, 910, 1248, 1331]`
- `arm_L_underpaint`: `PASS_LAYER_NONEMPTY`, coverage `0.065003`, bbox `[352, 1182, 709, 2048]`
- `arm_R_underpaint`: `PASS_LAYER_NONEMPTY`, coverage `0.065643`, bbox `[1340, 1182, 1697, 2048]`
- `hair_back_underpaint`: `PASS_LAYER_NONEMPTY`, coverage `0.152597`, bbox `[336, 110, 1720, 1677]`

## Visual QA

- `manual_visual_review`: `REQUIRED`
- Do not promote this to B1 material PASS until contact-sheet and overlay QA are accepted.

## Limits

- Automatic masks are coarse and must not be treated as final Cubism ArtMesh geometry.
- This does not generate B2 eyes, B3 mouth expressions, B4 hair children, or B5 final body/clothing parts.
- Mini Cubism diagnostic and real Cubism authoring gates remain locked until later material QA passes.

## Next Action

- Run B1 overlay/contact-sheet visual QA.
- If accepted, use these B1 layers as clean-base inputs for B2 eye pack and B3 mouth pack generation.
- If rejected, regenerate or manually edit only the failing B1 layer areas; do not fall back to patch-style clean bases.

## Self Review

- `expected_output_count`: `11`
- `generated_output_count`: `11`
- `missing_output_count`: `0`
- `empty_output_count`: `0`
- `all_outputs_present`: `True`
- `all_outputs_nonempty`: `True`
- `canvas`: `[2048, 2048]`
- `status`: `PASS`

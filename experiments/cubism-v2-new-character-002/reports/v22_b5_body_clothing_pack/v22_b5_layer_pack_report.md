# Character 002 v22 B5 Body/Clothing Layer Pack

- status: `B5_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED`
- raw review: `experiments/cubism-v2-new-character-002/reports/v22_b5_body_clothing_pack/v22_b5_body_clothing_pack_review.json`
- B5 raw image: `experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/raw_outputs/b5_body_clothing_pack_reference_001.png`
- normalized layers: `experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers`
- contact sheet: `experiments/cubism-v2-new-character-002/reports/v22_b5_body_clothing_pack/v22_b5_layer_pack_contact_sheet.png`
- overlay sheet: `experiments/cubism-v2-new-character-002/reports/v22_b5_body_clothing_pack/v22_b5_layer_pack_overlay_qa.png`

## Expected Outputs

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

## Metrics

- `torso_base`: bbox `[604, 884, 1474, 1865]`, coverage `0.15899587`, center `[1039.0, 1374.5]`
- `neck`: bbox `[894, 701, 1179, 1090]`, coverage `0.01887441`, center `[1036.5, 895.5]`
- `shoulder_L`: bbox `[565, 993, 870, 1226]`, coverage `0.01319313`, center `[717.5, 1109.5]`
- `shoulder_R`: bbox `[1197, 996, 1456, 1229]`, coverage `0.0113492`, center `[1326.5, 1112.5]`
- `arm_L_upper_simple`: bbox `[485, 1112, 696, 1785]`, coverage `0.01842356`, center `[590.5, 1448.5]`
- `arm_R_upper_simple`: bbox `[1335, 1115, 1521, 1786]`, coverage `0.0163765`, center `[1428.0, 1450.5]`
- `collar_front`: bbox `[752, 1078, 1304, 1198]`, coverage `0.00627613`, center `[1028.0, 1138.0]`
- `collar_shadow`: bbox `[745, 1177, 1288, 1270]`, coverage `0.00278354`, center `[1016.5, 1223.5]`
- `chest_cloth_base`: bbox `[721, 1245, 1374, 1545]`, coverage `0.01906276`, center `[1047.5, 1395.0]`
- `chest_cloth_shadow`: bbox `[697, 1482, 1372, 1648]`, coverage `0.01092887`, center `[1034.5, 1565.0]`
- `brow_L`: bbox `[764, 628, 925, 661]`, coverage `0.00039005`, center `[844.5, 644.5]`
- `brow_R`: bbox `[1105, 628, 1262, 660]`, coverage `0.00039315`, center `[1183.5, 644.0]`
- `nose`: bbox `[991, 739, 1061, 841]`, coverage `0.00128794`, center `[1026.0, 790.0]`
- `cheek_L`: bbox `[725, 731, 935, 857]`, coverage `0.00489974`, center `[830.0, 794.0]`
- `cheek_R`: bbox `[1110, 731, 1320, 857]`, coverage `0.00492239`, center `[1215.0, 794.0]`
- `face_shadow_L`: bbox `[694, 650, 806, 899]`, coverage `0.00382805`, center `[750.0, 774.5]`
- `face_shadow_R`: bbox `[1165, 650, 1255, 896]`, coverage `0.00384521`, center `[1210.0, 773.0]`

## Decision

Keep this B5 extraction as full-canvas RGBA candidate evidence only. It does not prove body-motion, visual material PASS, Mini Cubism success, or real Cubism success before overlay QA and 주인님 review.

## Next Action

- Run B5 overlay QA and visual review against the G0 source silhouette.
- Use manual anchor correction or refined extraction if body/clothing/face detail parts are visually misaligned.
- Only after B1-B5 visual QA acceptance, build the v22 64-part manifest.

## Self Review

- `expected_output_count`: `17`
- `generated_output_count`: `17`
- `missing_output_count`: `0`
- `empty_output_count`: `0`
- `all_layers_rgba`: `True`
- `all_layers_2048`: `True`
- `forbidden_existing_body_clothing_asset_count`: `5`
- `forbidden_assets_not_output_path`: `True`
- `has_human_required_gate`: `True`
- `has_overlay_qa_requirement`: `True`
- `has_face_detail_scope`: `True`
- `status`: `PASS`

# Character 002 v22 B4 Hair Layer Pack

- status: `B4_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED`
- raw review: `experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_hair_pack_review.json`
- B4 raw image: `experiments/cubism-v2-new-character-002/v22_b4_hair_pack/raw_outputs/b4_hair_pack_reference_001.png`
- normalized layers: `experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers`
- contact sheet: `experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_layer_pack_contact_sheet.png`
- overlay sheet: `experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_layer_pack_overlay_qa.png`

## Expected Outputs

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

## Metrics

- `hair_back_base`: bbox `[644, 190, 1404, 1250]`, coverage `0.14233398`, center `[1024.0, 720.0]`
- `hair_back_strand_L`: bbox `[595, 440, 855, 1200]`, coverage `0.02609921`, center `[725.0, 820.0]`
- `hair_back_strand_R`: bbox `[1223, 450, 1445, 1210]`, coverage `0.02190447`, center `[1334.0, 830.0]`
- `hair_back_center`: bbox `[839, 435, 1213, 1210]`, coverage `0.0482862`, center `[1026.0, 822.5]`
- `hair_front_center`: bbox `[814, 222, 1234, 636]`, coverage `0.025141`, center `[1024.0, 429.0]`
- `hair_front_L`: bbox `[753, 279, 1010, 611]`, coverage `0.01265311`, center `[881.5, 445.0]`
- `hair_front_R`: bbox `[1010, 275, 1310, 635]`, coverage `0.01851439`, center `[1160.0, 455.0]`
- `hair_front_side_L`: bbox `[712, 375, 912, 895]`, coverage `0.01213694`, center `[812.0, 635.0]`
- `hair_front_side_R`: bbox `[1223, 375, 1351, 895]`, coverage `0.00768447`, center `[1287.0, 635.0]`
- `hair_front_tip_L`: bbox `[696, 690, 824, 1055]`, coverage `0.00586462`, center `[760.0, 872.5]`
- `hair_front_tip_R`: bbox `[1155, 690, 1263, 1080]`, coverage `0.00695109`, center `[1209.0, 885.0]`
- `hair_side_L_outer`: bbox `[696, 670, 737, 1151]`, coverage `0.00231504`, center `[716.5, 910.5]`
- `hair_side_L_inner`: bbox `[670, 712, 807, 1133]`, coverage `0.00722432`, center `[738.5, 922.5]`
- `hair_side_R_outer`: bbox `[1328, 675, 1509, 1190]`, coverage `0.01454306`, center `[1418.5, 932.5]`
- `hair_side_R_inner`: bbox `[1187, 712, 1319, 1159]`, coverage `0.01035833`, center `[1253.0, 935.5]`
- `hair_back_underpaint`: bbox `[734, 585, 1145, 1175]`, coverage `0.04447603`, center `[939.5, 880.0]`

## Decision

Keep this B4 extraction as full-canvas RGBA candidate evidence only. It creates real hair_front_* scope, but does not unlock ParamHairFront or material PASS before overlay QA and 주인님 review.

## Next Action

- Run B4 overlay QA and visual review against the G0 source silhouette.
- Use manual anchor correction if front/side/back hair parts are visually misaligned.
- Keep ParamHairFront hidden until independent front hair children are accepted.

## Self Review

- `expected_output_count`: `16`
- `generated_output_count`: `16`
- `missing_output_count`: `0`
- `empty_output_count`: `0`
- `all_layers_rgba`: `True`
- `all_layers_2048`: `True`
- `forbidden_existing_hair_asset_count`: `5`
- `forbidden_assets_not_output_path`: `True`
- `has_human_required_gate`: `True`
- `has_hairfront_contract_gate`: `True`
- `has_overlay_qa_requirement`: `True`
- `status`: `PASS`

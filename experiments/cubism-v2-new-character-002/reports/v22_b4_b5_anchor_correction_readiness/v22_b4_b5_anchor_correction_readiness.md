# Character 002 v22 B4/B5 Anchor Correction Readiness

- status: `G6_B4_B5_ANCHOR_CORRECTION_READY_OVERRIDE_PENDING`
- manifest: `experiments/cubism-v2-new-character-002/reports/v22_64part_candidate_manifest/v22_64part_candidate_manifest.json`
- override template: `experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_correction_readiness/manual_anchor_override_template.json`

## Gate Interpretation

- `g1_64part_completeness`: `PASS_TECHNICAL`
- `g4_g5_visual_overlay`: `BLOCKED_REVISE`
- `g6_manual_anchor_correction`: `READY_FOR_OVERRIDE_CAPTURE`
- `g7_mini_cubism_diagnostic`: `BLOCKED_UNTIL_CORRECTED_VISUAL_QA`
- `g8_real_cubism_authoring`: `BLOCKED_UNTIL_MATERIAL_QA_AND_HUMAN_REVIEW`
- `param_hair_front`: `HIDDEN_CONTRACT_ONLY`

## Target Summary

- by batch: `{'B4': 16, 'B5': 17}`
- by group: `{'body': 6, 'brow': 2, 'clothing': 4, 'face_base': 5, 'hair': 16}`

## Targets

- `torso_base` `B5` `body` center `[1039.0, 1374.5]` bbox `[604, 884, 1474, 1865]` `manual_anchor_or_crop_refinement_body_clothing`
- `neck` `B5` `body` center `[1036.5, 895.5]` bbox `[894, 701, 1179, 1090]` `manual_anchor_or_crop_refinement_body_clothing`
- `shoulder_L` `B5` `body` center `[717.5, 1109.5]` bbox `[565, 993, 870, 1226]` `manual_anchor_or_crop_refinement_body_clothing`
- `shoulder_R` `B5` `body` center `[1326.5, 1112.5]` bbox `[1197, 996, 1456, 1229]` `manual_anchor_or_crop_refinement_body_clothing`
- `arm_L_upper_simple` `B5` `body` center `[590.5, 1448.5]` bbox `[485, 1112, 696, 1785]` `manual_anchor_or_crop_refinement_body_clothing`
- `arm_R_upper_simple` `B5` `body` center `[1428.0, 1450.5]` bbox `[1335, 1115, 1521, 1786]` `manual_anchor_or_crop_refinement_body_clothing`
- `face_shadow_L` `B5` `face_base` center `[750.0, 774.5]` bbox `[694, 650, 806, 899]` `manual_anchor_or_crop_refinement_face_detail`
- `face_shadow_R` `B5` `face_base` center `[1210.0, 773.0]` bbox `[1165, 650, 1255, 896]` `manual_anchor_or_crop_refinement_face_detail`
- `nose` `B5` `face_base` center `[1026.0, 790.0]` bbox `[991, 739, 1061, 841]` `manual_anchor_or_crop_refinement_face_detail`
- `cheek_L` `B5` `face_base` center `[830.0, 794.0]` bbox `[725, 731, 935, 857]` `manual_anchor_or_crop_refinement_face_detail`
- `cheek_R` `B5` `face_base` center `[1215.0, 794.0]` bbox `[1110, 731, 1320, 857]` `manual_anchor_or_crop_refinement_face_detail`
- `brow_L` `B5` `brow` center `[844.5, 644.5]` bbox `[764, 628, 925, 661]` `manual_anchor_or_crop_refinement_face_detail`
- `brow_R` `B5` `brow` center `[1183.5, 644.0]` bbox `[1105, 628, 1262, 660]` `manual_anchor_or_crop_refinement_face_detail`
- `hair_back_base` `B4` `hair` center `[1024.0, 720.0]` bbox `[644, 190, 1404, 1250]` `manual_anchor_or_crop_refinement_back_hair`
- `hair_back_underpaint` `B4` `hair` center `[939.5, 880.0]` bbox `[734, 585, 1145, 1175]` `manual_anchor_or_crop_refinement_back_hair`
- `hair_back_strand_L` `B4` `hair` center `[725.0, 820.0]` bbox `[595, 440, 855, 1200]` `manual_anchor_or_crop_refinement_back_hair`
- `hair_back_strand_R` `B4` `hair` center `[1334.0, 830.0]` bbox `[1223, 450, 1445, 1210]` `manual_anchor_or_crop_refinement_back_hair`
- `hair_back_center` `B4` `hair` center `[1026.0, 822.5]` bbox `[839, 435, 1213, 1210]` `manual_anchor_or_crop_refinement_back_hair`
- `hair_front_center` `B4` `hair` center `[1024.0, 429.0]` bbox `[814, 222, 1234, 636]` `manual_anchor_or_crop_refinement_front_hair`
- `hair_front_L` `B4` `hair` center `[881.5, 445.0]` bbox `[753, 279, 1010, 611]` `manual_anchor_or_crop_refinement_front_hair`
- `hair_front_R` `B4` `hair` center `[1160.0, 455.0]` bbox `[1010, 275, 1310, 635]` `manual_anchor_or_crop_refinement_front_hair`
- `hair_front_side_L` `B4` `hair` center `[812.0, 635.0]` bbox `[712, 375, 912, 895]` `manual_anchor_or_crop_refinement_front_hair`
- `hair_front_side_R` `B4` `hair` center `[1287.0, 635.0]` bbox `[1223, 375, 1351, 895]` `manual_anchor_or_crop_refinement_front_hair`
- `hair_front_tip_L` `B4` `hair` center `[760.0, 872.5]` bbox `[696, 690, 824, 1055]` `manual_anchor_or_crop_refinement_front_hair`
- `hair_front_tip_R` `B4` `hair` center `[1209.0, 885.0]` bbox `[1155, 690, 1263, 1080]` `manual_anchor_or_crop_refinement_front_hair`
- `hair_side_L_outer` `B4` `hair` center `[716.5, 910.5]` bbox `[696, 670, 737, 1151]` `manual_anchor_or_crop_refinement_side_hair`
- `hair_side_L_inner` `B4` `hair` center `[738.5, 922.5]` bbox `[670, 712, 807, 1133]` `manual_anchor_or_crop_refinement_side_hair`
- `hair_side_R_outer` `B4` `hair` center `[1418.5, 932.5]` bbox `[1328, 675, 1509, 1190]` `manual_anchor_or_crop_refinement_side_hair`
- `hair_side_R_inner` `B4` `hair` center `[1253.0, 935.5]` bbox `[1187, 712, 1319, 1159]` `manual_anchor_or_crop_refinement_side_hair`
- `collar_front` `B5` `clothing` center `[1028.0, 1138.0]` bbox `[752, 1078, 1304, 1198]` `manual_anchor_or_crop_refinement_body_clothing`
- `collar_shadow` `B5` `clothing` center `[1016.5, 1223.5]` bbox `[745, 1177, 1288, 1270]` `manual_anchor_or_crop_refinement_body_clothing`
- `chest_cloth_base` `B5` `clothing` center `[1047.5, 1395.0]` bbox `[721, 1245, 1374, 1545]` `manual_anchor_or_crop_refinement_body_clothing`
- `chest_cloth_shadow` `B5` `clothing` center `[1034.5, 1565.0]` bbox `[697, 1482, 1372, 1648]` `manual_anchor_or_crop_refinement_body_clothing`

## Decision

B4/B5 are ready for G6 correction capture, not material promotion. Current bbox/center evidence is recorded for each visually revised target.

## Next Action

- Open or build a drag/zoom anchor editor for these target parts.
- Save target_anchor and target_scale values into an override JSON.
- Build corrected B4/B5 candidate layers from the saved override or refined extraction script.
- Re-run B4/B5 overlay QA and rebuild the 64-part manifest before any G7 Mini Cubism diagnostic.

## Self Review

- `manifest_status`: `G1_64PART_MANIFEST_COMPLETE_TECHNICAL_PASS_VISUAL_REVISE_BLOCKED`
- `b4_overlay_status`: `B4_CODEX_OVERLAY_QA_REVISE_ANCHOR_OR_EXTRACTION_HUMAN_REVIEW_REQUIRED`
- `b5_overlay_status`: `B5_CODEX_OVERLAY_QA_REVISE_ANCHOR_OR_EXTRACTION_HUMAN_REVIEW_REQUIRED`
- `target_count`: `33`
- `b4_target_count`: `16`
- `b5_target_count`: `17`
- `all_targets_have_bbox`: `True`
- `all_targets_pending_override`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`

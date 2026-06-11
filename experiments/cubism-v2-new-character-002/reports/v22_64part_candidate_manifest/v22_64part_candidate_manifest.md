# Character 002 v22 64-Part Candidate Manifest

- status: `G1_64PART_MANIFEST_COMPLETE_TECHNICAL_PASS_VISUAL_REVISE_BLOCKED`
- spec: `experiments/cubism-v2-new-character-002/reports/v22_64part_generation_spec/v22_64part_generation_spec.json`
- G0 status: `PASS_READY_FOR_64PART_GENERATION`
- contact sheet: `experiments/cubism-v2-new-character-002/reports/v22_64part_candidate_manifest/v22_64part_candidate_manifest_contact_sheet.png`

## Gate Interpretation

- `g1_64part_completeness`: `PASS_TECHNICAL`
- `g2_full_canvas_rgba`: `PASS_TECHNICAL`
- `g4_g5_visual_overlay`: `BLOCKED_REVISE`
- `g6_manual_anchor_correction`: `REQUIRED_FOR_B4_B5`
- `g7_mini_cubism_diagnostic`: `BLOCKED_UNTIL_VISUAL_QA_ACCEPTS_B1_B5`
- `g8_real_cubism_authoring`: `BLOCKED_UNTIL_MATERIAL_QA_AND_HUMAN_REVIEW`
- `param_hair_front`: `HIDDEN_CONTRACT_ONLY`

## Batch Status

- `B1`: layer `B1_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA`, visual `B1_CODEX_VISUAL_QA_PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED`, gate `PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- `B2`: layer `B2_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED`, visual `B2_CODEX_OVERLAY_QA_PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED`, gate `PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- `B3_REVISION_V1`: layer `B3_REVISION_V1_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED`, visual `B3_REVISION_V1_CODEX_OVERLAY_QA_PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED`, gate `PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- `B4`: layer `B4_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED`, visual `B4_CODEX_OVERLAY_QA_REVISE_ANCHOR_OR_EXTRACTION_HUMAN_REVIEW_REQUIRED`, gate `REVISE_ANCHOR_OR_EXTRACTION`
- `B5`: layer `B5_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED`, visual `B5_CODEX_OVERLAY_QA_REVISE_ANCHOR_OR_EXTRACTION_HUMAN_REVIEW_REQUIRED`, gate `REVISE_ANCHOR_OR_EXTRACTION`

## Manifest Summary

- `required_part_count`: `64`
- `manifest_entry_count`: `64`
- `unique_manifest_part_count`: `64`
- `missing_part_count`: `0`
- `wrong_mode_count`: `0`
- `wrong_size_count`: `0`
- `empty_part_count`: `0`
- `duplicate_part_count`: `0`
- `group_counts`: `{'body': 10, 'face_base': 8, 'eye_L': 8, 'eye_R': 8, 'brow': 2, 'mouth': 8, 'hair': 16, 'clothing': 4}`
- `required_group_counts`: `{'body': 10, 'face_base': 8, 'eye_L': 8, 'eye_R': 8, 'brow': 2, 'mouth': 8, 'hair': 16, 'clothing': 4}`
- `group_counts_match_spec`: `True`
- `visual_gate_counts`: `{'PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED': 31, 'REVISE_ANCHOR_OR_EXTRACTION': 33}`
- `status_counts`: `{'TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED': 31, 'TECHNICAL_PRESENT_VISUAL_REVISE': 33}`
- `has_b4_revise_parts`: `True`
- `has_b5_revise_parts`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`

## Parts

- `body_underpaint` `body` `B1` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/normalized_layers/body_underpaint.png`
- `torso_base` `body` `B5` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/torso_base.png`
- `neck` `body` `B5` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/neck.png`
- `neck_shadow_underpaint` `body` `B1` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/normalized_layers/neck_shadow_underpaint.png`
- `shoulder_L` `body` `B5` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/shoulder_L.png`
- `shoulder_R` `body` `B5` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/shoulder_R.png`
- `arm_L_upper_simple` `body` `B5` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/arm_L_upper_simple.png`
- `arm_R_upper_simple` `body` `B5` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/arm_R_upper_simple.png`
- `arm_L_underpaint` `body` `B1` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/normalized_layers/arm_L_underpaint.png`
- `arm_R_underpaint` `body` `B1` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/normalized_layers/arm_R_underpaint.png`
- `face_base` `face_base` `B1` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/normalized_layers/face_base.png`
- `face_shadow_L` `face_base` `B5` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/face_shadow_L.png`
- `face_shadow_R` `face_base` `B5` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/face_shadow_R.png`
- `face_underpaint_L` `face_base` `B1` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/normalized_layers/face_underpaint_L.png`
- `face_underpaint_R` `face_base` `B1` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/normalized_layers/face_underpaint_R.png`
- `nose` `face_base` `B5` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/nose.png`
- `cheek_L` `face_base` `B5` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/cheek_L.png`
- `cheek_R` `face_base` `B5` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/cheek_R.png`
- `eye_L_white` `eye_L` `B2` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_L_white.png`
- `eye_L_iris` `eye_L` `B2` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_L_iris.png`
- `eye_L_pupil` `eye_L` `B2` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_L_pupil.png`
- `eye_L_highlight` `eye_L` `B2` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_L_highlight.png`
- `eye_L_upper_lash` `eye_L` `B2` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_L_upper_lash.png`
- `eye_L_lower_lash` `eye_L` `B2` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_L_lower_lash.png`
- `eye_L_closed_lid` `eye_L` `B2` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_L_closed_lid.png`
- `eye_L_underpaint` `eye_L` `B1` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/normalized_layers/eye_L_underpaint.png`
- `eye_R_white` `eye_R` `B2` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_R_white.png`
- `eye_R_iris` `eye_R` `B2` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_R_iris.png`
- `eye_R_pupil` `eye_R` `B2` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_R_pupil.png`
- `eye_R_highlight` `eye_R` `B2` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_R_highlight.png`
- `eye_R_upper_lash` `eye_R` `B2` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_R_upper_lash.png`
- `eye_R_lower_lash` `eye_R` `B2` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_R_lower_lash.png`
- `eye_R_closed_lid` `eye_R` `B2` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_R_closed_lid.png`
- `eye_R_underpaint` `eye_R` `B1` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/normalized_layers/eye_R_underpaint.png`
- `brow_L` `brow` `B5` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/brow_L.png`
- `brow_R` `brow` `B5` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/brow_R.png`
- `mouth_line` `mouth` `B3_REVISION_V1` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b3_mouth_pack_revision_v1/normalized_layers/mouth_line.png`
- `mouth_inner` `mouth` `B3_REVISION_V1` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b3_mouth_pack_revision_v1/normalized_layers/mouth_inner.png`
- `mouth_upper_lip_mask` `mouth` `B3_REVISION_V1` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b3_mouth_pack_revision_v1/normalized_layers/mouth_upper_lip_mask.png`
- `mouth_lower_lip_mask` `mouth` `B3_REVISION_V1` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b3_mouth_pack_revision_v1/normalized_layers/mouth_lower_lip_mask.png`
- `mouth_teeth` `mouth` `B3_REVISION_V1` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b3_mouth_pack_revision_v1/normalized_layers/mouth_teeth.png`
- `mouth_tongue` `mouth` `B3_REVISION_V1` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b3_mouth_pack_revision_v1/normalized_layers/mouth_tongue.png`
- `mouth_corner_L` `mouth` `B3_REVISION_V1` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b3_mouth_pack_revision_v1/normalized_layers/mouth_corner_L.png`
- `mouth_corner_R` `mouth` `B3_REVISION_V1` `TECHNICAL_PRESENT_PASS_CANDIDATE_HUMAN_REQUIRED` `experiments/cubism-v2-new-character-002/v22_b3_mouth_pack_revision_v1/normalized_layers/mouth_corner_R.png`
- `hair_back_base` `hair` `B4` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_back_base.png`
- `hair_back_underpaint` `hair` `B4` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_back_underpaint.png`
- `hair_back_strand_L` `hair` `B4` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_back_strand_L.png`
- `hair_back_strand_R` `hair` `B4` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_back_strand_R.png`
- `hair_back_center` `hair` `B4` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_back_center.png`
- `hair_front_center` `hair` `B4` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_front_center.png`
- `hair_front_L` `hair` `B4` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_front_L.png`
- `hair_front_R` `hair` `B4` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_front_R.png`
- `hair_front_side_L` `hair` `B4` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_front_side_L.png`
- `hair_front_side_R` `hair` `B4` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_front_side_R.png`
- `hair_front_tip_L` `hair` `B4` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_front_tip_L.png`
- `hair_front_tip_R` `hair` `B4` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_front_tip_R.png`
- `hair_side_L_outer` `hair` `B4` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_side_L_outer.png`
- `hair_side_L_inner` `hair` `B4` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_side_L_inner.png`
- `hair_side_R_outer` `hair` `B4` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_side_R_outer.png`
- `hair_side_R_inner` `hair` `B4` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_side_R_inner.png`
- `collar_front` `clothing` `B5` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/collar_front.png`
- `collar_shadow` `clothing` `B5` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/collar_shadow.png`
- `chest_cloth_base` `clothing` `B5` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/chest_cloth_base.png`
- `chest_cloth_shadow` `clothing` `B5` `TECHNICAL_PRESENT_VISUAL_REVISE` `experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/chest_cloth_shadow.png`

## Decision

The v22 64 required part IDs are technically present as 2048 RGBA candidates, but B4 and B5 overlay QA are REVISE. Do not promote to material PASS, Mini Cubism diagnostics, or real Cubism authoring.

## Next Action

- Refine B4/B5 anchors or crop assignments, or run manual anchor correction for visually misaligned parts.
- Keep ParamHairFront hidden until corrected hair_front_* children pass overlay QA.
- After B1-B5 visual QA and 주인님 review accept corrected parts, rebuild this manifest and proceed to G2-G5 material QA.

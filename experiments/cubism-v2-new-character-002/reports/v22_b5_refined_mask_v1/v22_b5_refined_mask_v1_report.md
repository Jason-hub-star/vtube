# Character 002 v22 B5 Refined Mask v1

- status: `B5_REFINED_MASK_V1_CANDIDATE_READY_FOR_OVERLAY_REVIEW`
- output dir: `experiments/cubism-v2-new-character-002/v22_b5_refined_mask_v1/normalized_layers`
- overlay sheet: `experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v1/v22_b5_refined_mask_v1_overlay_qa.png`
- contact sheet: `experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v1/v22_b5_refined_mask_v1_contact_sheet.png`

## Decision

B5 refined-mask v1 reduces the 13 extraction-mask problem parts while preserving all gates. This is a candidate for overlay review, not material PASS.

## Next Action

- Review B5 refined-mask v1 overlay sheet.
- Merge accepted B5 refined masks into the B4/B5 corrected candidate only after visual review.
- Keep ParamHairFront hidden and keep G7/G8 blocked.

## Entries

- `REFINED_MASK_V1` `torso_base` cov `0.15770555` bbox `[592, 904, 1460, 1864]`
- `COPIED_FROM_AUTO_DRAFT` `neck` cov `0.01887441` bbox `[882, 701, 1167, 1090]`
- `REFINED_MASK_V1` `shoulder_L` cov `0.01271868` bbox `[567, 1002, 869, 1224]`
- `REFINED_MASK_V1` `shoulder_R` cov `0.01104689` bbox `[1201, 1000, 1457, 1226]`
- `REFINED_MASK_V1` `arm_L_upper_simple` cov `0.01823521` bbox `[485, 1115, 695, 1786]`
- `REFINED_MASK_V1` `arm_R_upper_simple` cov `0.01637411` bbox `[1334, 1116, 1521, 1786]`
- `COPIED_FROM_AUTO_DRAFT` `collar_front` cov `0.00627613` bbox `[748, 1078, 1300, 1198]`
- `REFINED_MASK_V1` `collar_shadow` cov `0.00243759` bbox `[753, 1178, 1295, 1269]`
- `REFINED_MASK_V1` `chest_cloth_base` cov `0.01802492` bbox `[698, 1246, 1350, 1546]`
- `REFINED_MASK_V1` `chest_cloth_shadow` cov `0.00590897` bbox `[733, 1481, 1288, 1641]`
- `COPIED_FROM_AUTO_DRAFT` `brow_L` cov `0.00030065` bbox `[779, 631, 924, 659]`
- `COPIED_FROM_AUTO_DRAFT` `brow_R` cov `0.00030589` bbox `[1103, 631, 1247, 659]`
- `REFINED_MASK_V1` `nose` cov `0.00088358` bbox `[996, 747, 1053, 832]`
- `REFINED_MASK_V1` `cheek_L` cov `0.0030582` bbox `[752, 744, 917, 844]`
- `REFINED_MASK_V1` `cheek_R` cov `0.00305676` bbox `[1129, 744, 1294, 844]`
- `REFINED_MASK_V1` `face_shadow_L` cov `0.0031786` bbox `[719, 659, 821, 888]`
- `REFINED_MASK_V1` `face_shadow_R` cov `0.00320244` bbox `[1208, 661, 1291, 888]`

## Self Review

- `entry_count`: `17`
- `refined_mask_count`: `13`
- `copied_from_auto_draft_count`: `4`
- `expected_refine_target_count`: `13`
- `all_layers_rgba`: `True`
- `all_layers_2048`: `True`
- `all_layers_nonempty`: `True`
- `overlay_sheet_exists`: `True`
- `contact_sheet_exists`: `True`
- `validator_only_promotion_blocked`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`

# Character 002 v22 B5 Refined Mask v2

- status: `B5_REFINED_MASK_V2_CANDIDATE_READY_FOR_OVERLAY_REVIEW`
- output dir: `experiments/cubism-v2-new-character-002/v22_b5_refined_mask_v2/normalized_layers`
- overlay sheet: `experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_overlay_qa.png`
- contact sheet: `experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_contact_sheet.png`

## Decision

B5 refined-mask v2 only changes the six focused v1 revise parts and keeps all gates blocked. This is a smaller candidate for overlay review, not material PASS.

## Next Action

- Run conservative v2 overlay QA.
- If v2 still reads patch-like, mark remaining parts for regeneration or human review instead of more anchor tweaking.
- Keep B4 hair focused review separate.

## Entries

- `REFINED_MASK_V2` `torso_base` cov `0.14019799` ratio `0.648455` bbox `[630, 990, 1429, 1864]`
- `COPIED_FROM_V1` `neck` cov `0.01887441` ratio `1.0` bbox `[882, 701, 1167, 1090]`
- `REFINED_MASK_V2` `shoulder_L` cov `0.01091456` ratio `0.473787` bbox `[577, 1011, 863, 1216]`
- `REFINED_MASK_V2` `shoulder_R` cov `0.00972676` ratio `0.495803` bbox `[1205, 1013, 1455, 1218]`
- `COPIED_FROM_V1` `arm_L_upper_simple` cov `0.01823521` ratio `1.0` bbox `[485, 1115, 695, 1786]`
- `COPIED_FROM_V1` `arm_R_upper_simple` cov `0.01637411` ratio `1.0` bbox `[1334, 1116, 1521, 1786]`
- `COPIED_FROM_V1` `collar_front` cov `0.00627613` ratio `1.0` bbox `[748, 1078, 1300, 1198]`
- `COPIED_FROM_V1` `collar_shadow` cov `0.00243759` ratio `1.0` bbox `[753, 1178, 1295, 1269]`
- `COPIED_FROM_V1` `chest_cloth_base` cov `0.01802492` ratio `1.0` bbox `[698, 1246, 1350, 1546]`
- `COPIED_FROM_V1` `chest_cloth_shadow` cov `0.00590897` ratio `1.0` bbox `[733, 1481, 1288, 1641]`
- `COPIED_FROM_V1` `brow_L` cov `0.00030065` ratio `1.0` bbox `[779, 631, 924, 659]`
- `COPIED_FROM_V1` `brow_R` cov `0.00030589` ratio `1.0` bbox `[1103, 631, 1247, 659]`
- `REFINED_MASK_V2` `nose` cov `0.00052786` ratio `0.213597` bbox `[1003, 757, 1046, 823]`
- `COPIED_FROM_V1` `cheek_L` cov `0.0030582` ratio `1.0` bbox `[752, 744, 917, 844]`
- `COPIED_FROM_V1` `cheek_R` cov `0.00305676` ratio `1.0` bbox `[1129, 744, 1294, 844]`
- `REFINED_MASK_V2` `face_shadow_L` cov `0.00281453` ratio `0.284959` bbox `[721, 678, 809, 883]`
- `REFINED_MASK_V2` `face_shadow_R` cov `0.00274563` ratio `0.279588` bbox `[1211, 680, 1291, 881]`

## Self Review

- `entry_count`: `17`
- `refined_mask_v2_count`: `6`
- `copied_from_v1_count`: `11`
- `expected_focused_target_count`: `6`
- `all_layers_rgba`: `True`
- `all_layers_2048`: `True`
- `all_layers_nonempty`: `True`
- `overlay_sheet_exists`: `True`
- `contact_sheet_exists`: `True`
- `validator_only_promotion_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`

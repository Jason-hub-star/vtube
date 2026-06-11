# Character 002 v22 B4/B5 Anchor Corrected Candidate

- status: `G6_B4_B5_AUTO_ANCHOR_DRAFT_CORRECTED_CANDIDATE_READY_FOR_OVERLAY_QA`
- mode: `auto_draft`
- overrides: `experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_correction_readiness/manual_anchor_overrides_auto_draft.json`
- output dir: `experiments/cubism-v2-new-character-002/v22_b4_b5_anchor_corrected_auto_draft/normalized_layers`
- contact sheet: `experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_anchor_corrected_auto_draft_contact_sheet.png`

## Decision

Automatic draft anchors were applied to all B4/B5 targets. This reduces manual workload but still requires overlay QA and 주인님 visual review before material promotion.

## Next Action

- Run B4/B5 overlay QA against corrected candidate layers.
- Keep ParamHairFront hidden until corrected hair_front_* children pass overlay QA.
- Rebuild the 64-part manifest only after corrected B4/B5 visual QA passes.

## Self Review

- `target_count`: `33`
- `entry_count`: `33`
- `saved_override_count`: `33`
- `applied_override_count`: `33`
- `copied_pending_override_count`: `0`
- `b4_entry_count`: `16`
- `b5_entry_count`: `17`
- `all_layers_rgba`: `True`
- `all_layers_2048`: `True`
- `all_layers_nonempty`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`

## Entries

- `torso_base` `B5` `ANCHOR_OVERRIDE_APPLIED` anchor `[1024.0, 1372.0]` scale `1.0`
- `neck` `B5` `ANCHOR_OVERRIDE_APPLIED` anchor `[1024.0, 896.0]` scale `1.0`
- `shoulder_L` `B5` `ANCHOR_OVERRIDE_APPLIED` anchor `[718.0, 1110.0]` scale `1.0`
- `shoulder_R` `B5` `ANCHOR_OVERRIDE_APPLIED` anchor `[1330.0, 1110.0]` scale `1.0`
- `arm_L_upper_simple` `B5` `ANCHOR_OVERRIDE_APPLIED` anchor `[590.0, 1450.0]` scale `1.0`
- `arm_R_upper_simple` `B5` `ANCHOR_OVERRIDE_APPLIED` anchor `[1428.0, 1450.0]` scale `1.0`
- `face_shadow_L` `B5` `ANCHOR_OVERRIDE_APPLIED` anchor `[770.0, 775.0]` scale `0.92`
- `face_shadow_R` `B5` `ANCHOR_OVERRIDE_APPLIED` anchor `[1250.0, 775.0]` scale `0.92`
- `nose` `B5` `ANCHOR_OVERRIDE_APPLIED` anchor `[1024.0, 790.0]` scale `0.85`
- `cheek_L` `B5` `ANCHOR_OVERRIDE_APPLIED` anchor `[835.0, 794.0]` scale `0.82`
- `cheek_R` `B5` `ANCHOR_OVERRIDE_APPLIED` anchor `[1210.0, 794.0]` scale `0.82`
- `brow_L` `B5` `ANCHOR_OVERRIDE_APPLIED` anchor `[852.0, 645.0]` scale `0.9`
- `brow_R` `B5` `ANCHOR_OVERRIDE_APPLIED` anchor `[1176.0, 645.0]` scale `0.9`
- `hair_back_base` `B4` `ANCHOR_OVERRIDE_APPLIED` anchor `[1024.0, 720.0]` scale `1.0`
- `hair_back_underpaint` `B4` `ANCHOR_OVERRIDE_APPLIED` anchor `[1024.0, 880.0]` scale `1.0`
- `hair_back_strand_L` `B4` `ANCHOR_OVERRIDE_APPLIED` anchor `[725.0, 820.0]` scale `1.0`
- `hair_back_strand_R` `B4` `ANCHOR_OVERRIDE_APPLIED` anchor `[1335.0, 830.0]` scale `1.0`
- `hair_back_center` `B4` `ANCHOR_OVERRIDE_APPLIED` anchor `[1024.0, 822.0]` scale `1.0`
- `hair_front_center` `B4` `ANCHOR_OVERRIDE_APPLIED` anchor `[1024.0, 430.0]` scale `0.96`
- `hair_front_L` `B4` `ANCHOR_OVERRIDE_APPLIED` anchor `[882.0, 445.0]` scale `0.96`
- `hair_front_R` `B4` `ANCHOR_OVERRIDE_APPLIED` anchor `[1160.0, 455.0]` scale `0.96`
- `hair_front_side_L` `B4` `ANCHOR_OVERRIDE_APPLIED` anchor `[812.0, 635.0]` scale `0.96`
- `hair_front_side_R` `B4` `ANCHOR_OVERRIDE_APPLIED` anchor `[1287.0, 635.0]` scale `0.96`
- `hair_front_tip_L` `B4` `ANCHOR_OVERRIDE_APPLIED` anchor `[760.0, 873.0]` scale `0.96`
- `hair_front_tip_R` `B4` `ANCHOR_OVERRIDE_APPLIED` anchor `[1209.0, 885.0]` scale `0.96`
- `hair_side_L_outer` `B4` `ANCHOR_OVERRIDE_APPLIED` anchor `[716.0, 911.0]` scale `1.0`
- `hair_side_L_inner` `B4` `ANCHOR_OVERRIDE_APPLIED` anchor `[738.0, 923.0]` scale `1.0`
- `hair_side_R_outer` `B4` `ANCHOR_OVERRIDE_APPLIED` anchor `[1418.0, 933.0]` scale `1.0`
- `hair_side_R_inner` `B4` `ANCHOR_OVERRIDE_APPLIED` anchor `[1253.0, 936.0]` scale `1.0`
- `collar_front` `B5` `ANCHOR_OVERRIDE_APPLIED` anchor `[1024.0, 1138.0]` scale `1.0`
- `collar_shadow` `B5` `ANCHOR_OVERRIDE_APPLIED` anchor `[1024.0, 1224.0]` scale `1.0`
- `chest_cloth_base` `B5` `ANCHOR_OVERRIDE_APPLIED` anchor `[1024.0, 1395.0]` scale `1.0`
- `chest_cloth_shadow` `B5` `ANCHOR_OVERRIDE_APPLIED` anchor `[1024.0, 1565.0]` scale `1.0`

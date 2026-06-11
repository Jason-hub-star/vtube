# Character 002 v22 HairFront Motion Readiness Preview

- status: `G5_HAIRFRONT_MOTION_READINESS_PREVIEW_READY_REVIEW_REQUIRED_PARAM_HIDDEN`
- source: `experiments/cubism-v2-new-character-002/reports/v22_g5_hairfront_motion_readiness_acceptance/v22_g5_hairfront_motion_readiness_acceptance_packet.json`
- contact sheet: `experiments/cubism-v2-new-character-002/reports/v22_g5_hairfront_motion_readiness_preview/v22_g5_hairfront_motion_readiness_preview_sheet.png`
- G5 material acceptance: `BLOCKED_HAIRFRONT_PREVIEW_REVIEW_REQUIRED`
- ParamHairFront: `HIDDEN_CONTRACT_ONLY`
- G7: `BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE`

## Counts

- hairfront_row_count: `7`
- pose_frame_count: `5`
- motion_preview_generated_count: `5`
- motion_readiness_pass_count: `0`
- param_hairfront_activation_count: `0`
- material_acceptance_pass_count: `0`

## Pose Frames

- `neutral`: `experiments/cubism-v2-new-character-002/reports/v22_g5_hairfront_motion_readiness_preview/hairfront_motion_preview_neutral.png`
- `swing_left`: `experiments/cubism-v2-new-character-002/reports/v22_g5_hairfront_motion_readiness_preview/hairfront_motion_preview_swing_left.png`
- `swing_right`: `experiments/cubism-v2-new-character-002/reports/v22_g5_hairfront_motion_readiness_preview/hairfront_motion_preview_swing_right.png`
- `lift`: `experiments/cubism-v2-new-character-002/reports/v22_g5_hairfront_motion_readiness_preview/hairfront_motion_preview_lift.png`
- `settle`: `experiments/cubism-v2-new-character-002/reports/v22_g5_hairfront_motion_readiness_preview/hairfront_motion_preview_settle.png`

## Next Action

- Review the contact sheet for obvious front-hair drift, pasted edges, or occlusion problems.
- If acceptable, build a dedicated Mini Cubism HairFront diagnostic preview while keeping ParamHairFront hidden until material acceptance.
- If not acceptable, route the seven HairFront rows to manual anchor correction or regeneration.

## Self Review

```json
{
  "source_status": "G5_HAIRFRONT_MOTION_READINESS_REVIEW_REQUIRED_PARAM_HIDDEN",
  "hairfront_row_count": 7,
  "pose_frame_count": 5,
  "preview_contact_sheet_exists": true,
  "all_pose_frames_exist": true,
  "static_independent_candidate_count": 7,
  "motion_preview_generated_count": 5,
  "motion_readiness_pass_count": 0,
  "motion_readiness_review_required_count": 7,
  "param_hairfront_activation_count": 0,
  "material_acceptance_pass_count": 0,
  "owner_approval_count": 0,
  "g5_material_not_accepted": true,
  "validator_only_promotion_blocked": true,
  "material_pass_blocked": true,
  "param_hair_front_hidden": true,
  "mini_cubism_not_promoted": true,
  "real_cubism_not_promoted": true,
  "not_owner_approval": true,
  "status": "PASS"
}
```

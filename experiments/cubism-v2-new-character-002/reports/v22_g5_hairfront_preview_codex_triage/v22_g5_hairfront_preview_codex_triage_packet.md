# Character 002 v22 HairFront Preview Codex Triage

- status: `G5_HAIRFRONT_PREVIEW_CODEX_TRIAGE_READY_REVIEW_REQUIRED_PARAM_HIDDEN`
- source: `experiments/cubism-v2-new-character-002/reports/v22_g5_hairfront_motion_readiness_preview/v22_g5_hairfront_motion_readiness_preview_packet.json`
- contact sheet: `experiments/cubism-v2-new-character-002/reports/v22_g5_hairfront_motion_readiness_preview/v22_g5_hairfront_motion_readiness_preview_sheet.png`
- triage: `NO_CATASTROPHIC_TECHNICAL_FAILURE_DETECTED_REVIEW_REQUIRED`
- Codex visual verdict: `CODEX_PROVISIONAL_REVIEW_REQUIRED_NOT_OWNER_APPROVAL`
- G5 material acceptance: `BLOCKED_HAIRFRONT_PREVIEW_REVIEW_REQUIRED`
- ParamHairFront: `HIDDEN_CONTRACT_ONLY`

## Counts

- hairfront_row_count: `7`
- pose_frame_count: `5`
- technical_frame_pass_count: `5`
- shifted_bbox_canvas_violation_count: `0`
- codex_visual_acceptance_pass_count: `0`
- motion_readiness_pass_count: `0`
- param_hairfront_activation_count: `0`
- material_acceptance_pass_count: `0`

## Frame Rows

- `neutral`: `PASS_PREVIEW_FRAME_TECHNICAL`, changed_ratio_vs_neutral `0.0`
- `swing_left`: `PASS_PREVIEW_FRAME_TECHNICAL`, changed_ratio_vs_neutral `0.04123998`
- `swing_right`: `PASS_PREVIEW_FRAME_TECHNICAL`, changed_ratio_vs_neutral `0.04140663`
- `lift`: `PASS_PREVIEW_FRAME_TECHNICAL`, changed_ratio_vs_neutral `0.03136849`
- `settle`: `PASS_PREVIEW_FRAME_TECHNICAL`, changed_ratio_vs_neutral `0.02912807`

## Next Action

- Use this packet as automatic evidence that the HairFront preview files are technically complete.
- Keep G5 material acceptance blocked until a separate visual/material decision gate is recorded.
- If continuing without owner interruption, build only diagnostic/review artifacts while preserving ParamHairFront as hidden.

## Self Review

```json
{
  "source_status": "G5_HAIRFRONT_MOTION_READINESS_PREVIEW_READY_REVIEW_REQUIRED_PARAM_HIDDEN",
  "hairfront_row_count": 7,
  "pose_frame_count": 5,
  "technical_frame_pass_count": 5,
  "shifted_bbox_canvas_violation_count": 0,
  "codex_visual_acceptance_pass_count": 0,
  "motion_readiness_pass_count": 0,
  "param_hairfront_activation_count": 0,
  "material_acceptance_pass_count": 0,
  "owner_approval_count": 0,
  "g5_material_not_accepted": true,
  "validator_only_promotion_blocked": true,
  "codex_visual_not_owner_approval": true,
  "material_pass_blocked": true,
  "param_hair_front_hidden": true,
  "mini_cubism_not_promoted": true,
  "real_cubism_not_promoted": true,
  "not_owner_approval": true,
  "status": "PASS"
}
```

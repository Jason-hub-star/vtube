# Character 002 v22 G6 HairFront Anchor Probe

- status: `G6_HAIRFRONT_ANCHOR_PROBE_READY_REVIEW_REQUIRED_PARAM_HIDDEN`
- probe verdict: `ANCHOR_PROBE_READY_REVIEW_REQUIRED_NOT_MATERIAL_PASS`
- contact sheet: `experiments/cubism-v2-new-character-002/reports/v22_g6_hairfront_anchor_probe/v22_g6_hairfront_anchor_probe_sheet.png`
- G5 material acceptance: `BLOCKED_HAIRFRONT_ANCHOR_PROBE_REVIEW_REQUIRED`
- ParamHairFront: `HIDDEN_CONTRACT_ONLY`

## Counts

- hairfront_row_count: `7`
- anchor_probe_row_count: `7`
- anchor_center_count: `7`
- motion_envelope_count: `7`
- technical_frame_pass_count: `5`
- shifted_bbox_canvas_violation_count: `0`
- manual_anchor_override_ready_count: `7`
- manual_anchor_override_saved_count: `0`
- motion_readiness_pass_count: `0`
- param_hairfront_activation_count: `0`
- material_acceptance_pass_count: `0`

## HairFront Rows

- `hair_front_center`: anchor `[1024, 430]`, envelope `[806, 221, 1242, 637]`, margin `221`
- `hair_front_L`: anchor `[884, 446]`, envelope `[745, 276, 1022, 613]`, margin `276`
- `hair_front_R`: anchor `[1160, 456]`, envelope `[1001, 272, 1320, 638]`, margin `272`
- `hair_front_side_L`: anchor `[811, 635]`, envelope `[701, 375, 921, 893]`, margin `375`
- `hair_front_side_R`: anchor `[1286, 635]`, envelope `[1211, 375, 1362, 893]`, margin `375`
- `hair_front_tip_L`: anchor `[760, 871]`, envelope `[684, 685, 835, 1055]`, margin `684`
- `hair_front_tip_R`: anchor `[1208, 884]`, envelope `[1142, 685, 1275, 1082]`, margin `685`

## Next Action

- Use the anchor probe sheet to decide whether each HairFront row needs manual anchor correction or regeneration.
- If continuing autonomously, build a correction input packet that can store override JSON without claiming material acceptance.
- Keep ParamHairFront hidden until a separate material decision gate explicitly passes.

## Self Review

```json
{
  "acceptance_status": "G5_HAIRFRONT_MOTION_READINESS_REVIEW_REQUIRED_PARAM_HIDDEN",
  "preview_status": "G5_HAIRFRONT_MOTION_READINESS_PREVIEW_READY_REVIEW_REQUIRED_PARAM_HIDDEN",
  "triage_status": "G5_HAIRFRONT_PREVIEW_CODEX_TRIAGE_READY_REVIEW_REQUIRED_PARAM_HIDDEN",
  "hairfront_row_count": 7,
  "anchor_probe_row_count": 7,
  "anchor_center_count": 7,
  "motion_envelope_count": 7,
  "pose_shift_count": 5,
  "technical_frame_pass_count": 5,
  "shifted_bbox_canvas_violation_count": 0,
  "contact_sheet_exists": true,
  "manual_anchor_override_ready_count": 7,
  "manual_anchor_override_saved_count": 0,
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

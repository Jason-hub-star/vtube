# Character 002 v22 G6 HairFront Anchor Correction Input

- status: `G6_HAIRFRONT_ANCHOR_CORRECTION_INPUT_READY_OVERRIDES_NOT_SAVED_PARAM_HIDDEN`
- verdict: `CORRECTION_INPUT_READY_NO_OVERRIDE_APPLIED_NOT_MATERIAL_PASS`
- source: `experiments/cubism-v2-new-character-002/reports/v22_g6_hairfront_anchor_probe/v22_g6_hairfront_anchor_probe_packet.json`
- override template: `experiments/cubism-v2-new-character-002/reports/v22_g6_hairfront_anchor_correction_input/manual_hairfront_anchor_overrides.template.json`
- G5 material acceptance: `BLOCKED_HAIRFRONT_CORRECTION_INPUT_REVIEW_REQUIRED`
- ParamHairFront: `HIDDEN_CONTRACT_ONLY`

## Counts

- correction_input_row_count: `7`
- override_template_entry_count: `7`
- current_anchor_count: `7`
- target_anchor_default_count: `7`
- zero_delta_default_count: `7`
- saved_override_count: `0`
- manual_anchor_override_ready_count: `7`
- manual_anchor_override_applied_count: `0`
- regeneration_route_ready_count: `7`
- material_acceptance_pass_count: `0`

## Rows

- `hair_front_center`: current `[1024, 430]`, target `[1024, 430]`, delta `[0, 0]`, status `TEMPLATE_PENDING_VISUAL_REVIEW`
- `hair_front_L`: current `[884, 446]`, target `[884, 446]`, delta `[0, 0]`, status `TEMPLATE_PENDING_VISUAL_REVIEW`
- `hair_front_R`: current `[1160, 456]`, target `[1160, 456]`, delta `[0, 0]`, status `TEMPLATE_PENDING_VISUAL_REVIEW`
- `hair_front_side_L`: current `[811, 635]`, target `[811, 635]`, delta `[0, 0]`, status `TEMPLATE_PENDING_VISUAL_REVIEW`
- `hair_front_side_R`: current `[1286, 635]`, target `[1286, 635]`, delta `[0, 0]`, status `TEMPLATE_PENDING_VISUAL_REVIEW`
- `hair_front_tip_L`: current `[760, 871]`, target `[760, 871]`, delta `[0, 0]`, status `TEMPLATE_PENDING_VISUAL_REVIEW`
- `hair_front_tip_R`: current `[1208, 884]`, target `[1208, 884]`, delta `[0, 0]`, status `TEMPLATE_PENDING_VISUAL_REVIEW`

## Next Action

- Serve or reuse a drag/zoom editor that writes a reviewed override JSON from this template.
- If visual review rejects a row instead of moving it, route that row to regeneration.
- After saved overrides exist, rebuild shifted full-canvas HairFront PNGs and rerun overlay/anchor probe QA.

## Self Review

```json
{
  "source_status": "G6_HAIRFRONT_ANCHOR_PROBE_READY_REVIEW_REQUIRED_PARAM_HIDDEN",
  "override_template_exists": true,
  "hairfront_row_count": 7,
  "correction_input_row_count": 7,
  "override_template_entry_count": 7,
  "current_anchor_count": 7,
  "target_anchor_default_count": 7,
  "zero_delta_default_count": 7,
  "saved_override_count": 0,
  "manual_anchor_override_ready_count": 7,
  "manual_anchor_override_applied_count": 0,
  "regeneration_route_ready_count": 7,
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

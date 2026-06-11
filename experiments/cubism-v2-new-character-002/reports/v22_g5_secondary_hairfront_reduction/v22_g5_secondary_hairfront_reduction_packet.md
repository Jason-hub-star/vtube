# Character 002 v22 G5 Secondary/HairFront Reduction

- status: `G5_SECONDARY_HAIRFRONT_REDUCTION_READY_MATERIAL_NOT_ACCEPTED`
- source: `experiments/cubism-v2-new-character-002/reports/v22_g5_primary6_codex_decisions/v22_g5_primary6_codex_decisions_packet.json`
- G5 material acceptance: `BLOCKED_HAIRFRONT_MOTION_READINESS_REMAINING_NOT_OWNER_APPROVAL`
- material pass: `BLOCKED`
- ParamHairFront: `HIDDEN_CONTRACT_ONLY`
- G7: `BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE`

## Counts

- reduction_row_count: `30`
- context_keep_count: `23`
- hairfront_defer_count: `7`
- followup_required_count: `7`
- g5_material_acceptance_remaining_count: `7`
- material_acceptance_pass_count: `0`

## Decisions

- context: `CODEX_PROVISIONAL_KEEP_AS_CONTEXT_NOT_MATERIAL_PASS`
- HairFront: `DEFER_HAIRFRONT_KEEP_PARAM_HIDDEN_CONTRACT_ONLY`

## Next Action

- Build a HairFront motion-readiness acceptance packet for the seven front-hair rows, keeping ParamHairFront hidden until it passes.
- Only after HairFront readiness is accepted should a separate G5 final material acceptance packet be considered.
- Do not start G7 Mini Cubism or real Cubism authoring from this reduction packet.

## Self Review

```json
{
  "source_status": "G5_PRIMARY6_CODEX_PROVISIONAL_DECISIONS_READY_MATERIAL_NOT_ACCEPTED",
  "source_remaining_material_acceptance_required_before_g7_count": 30,
  "reduction_row_count": 30,
  "context_keep_count": 23,
  "hairfront_defer_count": 7,
  "followup_required_count": 7,
  "material_acceptance_pass_count": 0,
  "owner_approval_count": 0,
  "g5_material_acceptance_remaining_count": 7,
  "source_counts_b4": 16,
  "source_counts_b5": 14,
  "has_context_decision_enum": true,
  "has_hairfront_decision_enum": true,
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

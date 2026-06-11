# Character 002 v22 G5 Primary6 Codex Decisions

- status: `G5_PRIMARY6_CODEX_PROVISIONAL_DECISIONS_READY_MATERIAL_NOT_ACCEPTED`
- source: `experiments/cubism-v2-new-character-002/reports/v22_g5_material_acceptance_reduction_route/v22_g5_material_acceptance_reduction_route_packet.json`
- G5 material acceptance: `BLOCKED_CONTEXT_HAIRFRONT_REMAINING_NOT_OWNER_APPROVAL`
- material pass: `BLOCKED`
- ParamHairFront: `HIDDEN_CONTRACT_ONLY`
- G7: `BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE`

## Counts

- primary6_decision_row_count: `6`
- primary6_codex_candidate_accept_count: `6`
- primary6_unresolved_count_after_decision: `0`
- owner_approval_count: `0`
- material_acceptance_pass_count: `0`
- remaining_material_acceptance_required_before_g7_count: `30`

## Decisions

- `B1_CLEAN_BASE_UNDERPAINT`: `CODEX_PROVISIONAL_ACCEPT_AS_G5_CANDIDATE_NOT_OWNER_APPROVAL`
- `B2_EYE_PACK`: `CODEX_PROVISIONAL_ACCEPT_AS_G5_CANDIDATE_NOT_OWNER_APPROVAL`
- `B3_MOUTH_PACK_REVISION_V1`: `CODEX_PROVISIONAL_ACCEPT_AS_G5_CANDIDATE_NOT_OWNER_APPROVAL`
- `torso_base`: `CODEX_PROVISIONAL_ACCEPT_AS_G5_CANDIDATE_NOT_OWNER_APPROVAL`
- `shoulder_L`: `CODEX_PROVISIONAL_ACCEPT_AS_G5_CANDIDATE_NOT_OWNER_APPROVAL`
- `shoulder_R`: `CODEX_PROVISIONAL_ACCEPT_AS_G5_CANDIDATE_NOT_OWNER_APPROVAL`

## Next Action

- Run a secondary context/HairFront reduction packet over the remaining 30 rows.
- Keep ParamHairFront hidden until the seven front-hair rows have independent motion-readiness acceptance.
- Do not start G7 Mini Cubism until G5 material acceptance is explicitly passed.

## Self Review

```json
{
  "source_status": "G5_MATERIAL_ACCEPTANCE_REDUCTION_ROUTE_READY_PRIMARY6_MATERIAL_NOT_ACCEPTED",
  "source_primary6_row_count": 6,
  "primary6_decision_row_count": 6,
  "primary6_codex_candidate_accept_count": 6,
  "primary6_revise_count": 0,
  "primary6_unresolved_count_after_decision": 0,
  "owner_approval_count": 0,
  "material_acceptance_pass_count": 0,
  "remaining_context_row_count": 23,
  "remaining_hairfront_contract_row_count": 7,
  "remaining_material_acceptance_required_before_g7_count": 30,
  "primary6_ids_match_expected": true,
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

# Character 002 v22 G5 Material Acceptance Reduction Route

- status: `G5_MATERIAL_ACCEPTANCE_REDUCTION_ROUTE_READY_PRIMARY6_MATERIAL_NOT_ACCEPTED`
- source: `experiments/cubism-v2-new-character-002/reports/v22_g5_material_acceptance_from_prep/v22_g5_material_acceptance_from_prep_packet.json`
- source verdict: `REVIEW_REQUIRED_MATERIAL_NOT_ACCEPTED`
- G5 material acceptance: `BLOCKED_PRIMARY6_REDUCTION_READY_MATERIAL_NOT_ACCEPTED`
- material pass: `BLOCKED`
- ParamHairFront: `HIDDEN_CONTRACT_ONLY`
- G7: `BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE`

## Counts

- total_route_row_count: `36`
- primary6_row_count: `6`
- secondary_context_row_count: `23`
- hairfront_contract_row_count: `7`
- primary6_unresolved_count: `6`
- total_unresolved_material_acceptance_count: `36`

## Primary6

- `B1_CLEAN_BASE_UNDERPAINT`: `P0_PRIMARY_B1_CLEAN_BASE_ACCEPTANCE` / `REVIEW_ACCEPT_OR_REVISE_CLEAN_BASE_UNDERPAINT`
- `B2_EYE_PACK`: `P0_PRIMARY_B2_EYE_ACCEPTANCE` / `REVIEW_ACCEPT_OR_REVISE_FIXED_WHITE_AND_COHERENT_EYE_DETAIL`
- `B3_MOUTH_PACK_REVISION_V1`: `P0_PRIMARY_B3_MOUTH_ACCEPTANCE` / `REVIEW_ACCEPT_OR_REVISE_COORDINATED_MOUTH_PACKET`
- `torso_base`: `P0_PRIMARY_B5_TORSO_ACCEPTANCE` / `REVIEW_ACCEPT_OR_REVISE_GENERATED_TORSO_UNDERPAINT`
- `shoulder_L`: `P0_PRIMARY_B5_SHOULDER_ACCEPTANCE` / `REVIEW_ACCEPT_OR_REVISE_SHOULDER_DRAW_ORDER_MASK`
- `shoulder_R`: `P0_PRIMARY_B5_SHOULDER_ACCEPTANCE` / `REVIEW_ACCEPT_OR_REVISE_SHOULDER_DRAW_ORDER_MASK`

## Next Action

- Build or apply a G5 primary6 accept/revise packet for B1, B2, B3, torso_base, shoulder_L, and shoulder_R.
- Use manual anchor correction only for rows that are visually misaligned after the primary6 pass.
- Keep HairFront hidden and keep G7/G8 blocked until material acceptance is explicitly passed.

## Self Review

```json
{
  "source_status": "G5_MATERIAL_ACCEPTANCE_PACKET_REVIEW_REQUIRED_MATERIAL_NOT_ACCEPTED",
  "source_verdict": "REVIEW_REQUIRED_MATERIAL_NOT_ACCEPTED",
  "source_material_acceptance_pass_count": 0,
  "total_route_row_count": 36,
  "primary6_row_count": 6,
  "secondary_context_row_count": 23,
  "hairfront_contract_row_count": 7,
  "primary6_unresolved_count": 6,
  "total_unresolved_material_acceptance_count": 36,
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

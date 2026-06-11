# Character 002 v22 G5 Material Acceptance From Prep

- status: `G5_MATERIAL_ACCEPTANCE_PACKET_REVIEW_REQUIRED_MATERIAL_NOT_ACCEPTED`
- verdict: `REVIEW_REQUIRED_MATERIAL_NOT_ACCEPTED`
- material acceptance: `BLOCKED_REVIEW_REQUIRED_MATERIAL_NOT_ACCEPTED`
- material pass: `BLOCKED`
- ParamHairFront: `HIDDEN_CONTRACT_ONLY`
- G7: `BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE`
- G8: `BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE`

## Counts

- material_acceptance_pass_count: `0`
- candidate_acceptance_row_count: `6`
- remaining_review_row_count: `30`
- hairfront_hidden_candidate_count: `7`
- context_review_row_count: `23`
- material_acceptance_required_before_g7_count: `36`

## Candidate Acceptance Rows

- `B1_CLEAN_BASE_UNDERPAINT`: `BLOCKED_HUMAN_VISUAL_ACCEPTANCE_REQUIRED`
- `B2_EYE_PACK`: `BLOCKED_HUMAN_VISUAL_ACCEPTANCE_REQUIRED`
- `B3_MOUTH_PACK_REVISION_V1`: `BLOCKED_HUMAN_VISUAL_ACCEPTANCE_REQUIRED`
- `torso_base`: `BLOCKED_SEPARATE_G5_ACCEPTANCE_REQUIRED`
- `shoulder_L`: `BLOCKED_SEPARATE_G5_ACCEPTANCE_REQUIRED`
- `shoulder_R`: `BLOCKED_SEPARATE_G5_ACCEPTANCE_REQUIRED`

## Remaining Review Classes

- `B4_SECONDARY_CONTEXT_REVIEW`: `9`
- `B5_COPIED_CONTEXT_REVIEW`: `14`
- `HAIRFRONT_MOTION_READINESS_REVIEW`: `7`

## Gate Matrix

- `G1_64PART_COMPLETENESS`: `PASS_TECHNICAL`
- `G2_FULL_CANVAS_RGBA_NORMALIZATION`: `PASS_TECHNICAL`
- `G3_TECHNICAL_VALIDATORS`: `PASS_TECHNICAL_MANIFEST_ONLY`
- `G4_VISUAL_QA`: `CANDIDATE_AND_CONTEXT_REVIEW_REQUIRED`
- `G5_MATERIAL_ACCEPTANCE`: `REVIEW_REQUIRED_MATERIAL_NOT_ACCEPTED`
- `G6_MANUAL_ANCHOR_CORRECTION`: `AVAILABLE_FOR_REJECTED_OR_MISALIGNED_ROWS`
- `G7_MINI_CUBISM_DIAGNOSTIC`: `BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE`
- `G8_REAL_CUBISM_AUTHORING`: `BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE`

## Next Action

- Use this packet to reduce the 36 material-acceptance-required rows instead of promoting validator PASS.
- Accept/revise/regenerate B1-B3 and P0 torso/shoulder rows separately, then rerun this G5 packet.
- Keep ParamHairFront hidden and keep G7/G8 blocked until G5 material acceptance is explicitly passed.

## Self Review

```json
{
  "g5_prep_status": "G5_PREP_PACKET_READY_FROM_TORSO_SELECTED_P0_DECISION_MATERIAL_ACCEPTANCE_BLOCKED",
  "manifest_status": "G4_TORSO_SELECTED_64PART_MANIFEST_TECHNICAL_PASS_REVIEW_REQUIRED",
  "technical_manifest_pass": true,
  "material_acceptance_pass_count": 0,
  "candidate_acceptance_row_count": 6,
  "b1_b3_candidate_human_required_count": 3,
  "p0_prep_candidate_count": 3,
  "p0_remaining_pre_g5_blocker_count": 0,
  "remaining_review_row_count": 30,
  "hairfront_hidden_candidate_count": 7,
  "context_review_row_count": 23,
  "material_acceptance_required_before_g7_count": 36,
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

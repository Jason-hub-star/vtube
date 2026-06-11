# Character 002 v22 B5 Refined Mask v2 Overlay QA

- status: `B5_REFINED_MASK_V2_OVERLAY_QA_REVISE_REGENERATE_OR_HUMAN_REVIEW_REQUIRED`
- v2 report: `experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_report.json`
- overlay sheet: `experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_overlay_qa.png`

## Checks

- `PASS_TECHNICAL` `technical_refined_mask_v2_pack`: B5 refined-mask v2 generated 17/17 full-canvas 2048 RGBA non-empty candidates, with six focused v2 refinements and eleven v1 copies.
- `IMPROVED_CANDIDATE_REVIEW_REQUIRED` `focused_mask_reduction`: Torso, shoulders, face shadows, and nose are narrower than v1 in the overlay sheet.
- `REVISE_REGENERATE_OR_REEXTRACT` `body_semantic_quality`: Torso and shoulders still read as broad body patches rather than clean source-matched B5 production parts. More alpha shrinking risks losing required body/clothing material.
- `REVIEW_REQUIRED` `face_detail_quality`: Nose and face shadows are smaller and may be reviewable, but should not be promoted without 주인님 visual acceptance.
- `BLOCKED` `material_promotion_gate`: B5 v2 remains candidate evidence only. Technical validators cannot promote it to material PASS.
- `BLOCKED` `g7_g8_gate`: Mini Cubism diagnostic and real Cubism authoring remain blocked until B4/B5 visual QA and human review accept corrected materials.

## Remaining B5 Revise Parts

- `torso_base`
- `shoulder_L`
- `shoulder_R`

## Possible Human Review Parts

- `nose`
- `face_shadow_L`
- `face_shadow_R`

## Decision

Keep B5 refined-mask v2 as the current best automatic mask-reduction candidate, but do not keep shrinking body masks blindly. Torso and shoulders should move to regeneration/re-extraction or human review; nose/face shadows can be reviewed as smaller candidates.

## Next Action

- Do not ask 주인님 to anchor all B5 parts.
- Use regeneration/re-extraction for torso_base and shoulder_L/R, or ask 주인님 for focused acceptance/rejection of those three.
- Review nose and face shadows as small candidates if needed.
- Keep B4 hair focused review separate and keep G7/G8 blocked.

## Self Review

- `v2_report_status`: `B5_REFINED_MASK_V2_CANDIDATE_READY_FOR_OVERLAY_REVIEW`
- `refined_mask_v2_count`: `6`
- `copied_from_v1_count`: `11`
- `has_revise_gate`: `True`
- `has_regenerate_or_reextract_gate`: `True`
- `has_blocked_material_gate`: `True`
- `validator_only_promotion_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`

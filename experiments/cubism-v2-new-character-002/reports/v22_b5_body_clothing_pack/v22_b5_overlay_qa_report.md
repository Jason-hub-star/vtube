# Character 002 v22 B5 Overlay QA

- status: `B5_CODEX_OVERLAY_QA_REVISE_ANCHOR_OR_EXTRACTION_HUMAN_REVIEW_REQUIRED`
- layer pack report: `experiments/cubism-v2-new-character-002/reports/v22_b5_body_clothing_pack/v22_b5_layer_pack_report.json`
- overlay sheet: `experiments/cubism-v2-new-character-002/reports/v22_b5_body_clothing_pack/v22_b5_layer_pack_overlay_qa.png`

## Checks

- `PASS_TECHNICAL` `technical_layer_pack`: B5 layer pack generated 17/17 full-canvas 2048 RGBA candidates with no missing or empty outputs.
- `PASS_CANDIDATE` `body_clothing_scope`: Torso, neck, shoulders, arms, collar, chest cloth, brow, nose, cheek, and face-shadow outputs exist as candidate PNGs.
- `REVISE_ANCHOR_OR_EXTRACTION` `body_clothing_overlay_alignment`: Overlay sheet shows torso/neck/arm/clothing candidates are visually misaligned or overlaid too heavily on the source body, so they need anchor correction or refined extraction before material PASS.
- `REVISE_ANCHOR_OR_EXTRACTION` `face_detail_overlay_alignment`: Brow/nose/cheek/face-shadow candidates exist, but current automatic face-detail placement is too large or patch-like on the face.
- `REVIEW_BLOCKED_UNTIL_ALIGNMENT` `breath_body_angle_gate`: Breath/body-angle support cannot be judged until body/clothing anchors and crop assignments are visually corrected.
- `REQUIRED` `human_visual_review`: 주인님 review is required after crop/anchor correction; technical PNG generation alone cannot approve B5 material.

## Decision

Do not promote B5 to material PASS. Keep the 17 RGBA body/clothing outputs as extraction candidates, but revise anchor placement/crop assignment before manifest promotion, Mini Cubism diagnostics, or real Cubism authoring.

## Next Action

- Use manual anchor correction or a refined extraction script for torso, neck, arms, clothing, and face-detail placement.
- Regenerate B5 only if crop refinement cannot make the parts read as source-matched body/clothing material.
- Keep B5 blocked from material PASS until overlay QA and 주인님 human review accept the corrected candidate.

## Self Review

- `b5_layer_pack_status`: `B5_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED`
- `b5_layer_self_review_status`: `PASS`
- `check_count`: `6`
- `has_revise_gate`: `True`
- `has_human_required_gate`: `True`
- `has_breath_body_angle_block`: `True`
- `status`: `PASS`

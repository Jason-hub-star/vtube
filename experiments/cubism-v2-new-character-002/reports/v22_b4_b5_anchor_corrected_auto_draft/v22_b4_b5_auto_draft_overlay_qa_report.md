# Character 002 v22 B4/B5 Auto-Draft Overlay QA

- status: `G6_B4_B5_AUTO_DRAFT_OVERLAY_QA_REVIEW_REQUIRED`
- corrected candidate: `experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_anchor_corrected_auto_draft_report.json`
- overlay sheet: `experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_auto_draft_overlay_qa.png`
- contact sheet: `experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_anchor_corrected_auto_draft_contact_sheet.png`

## Checks

- `PASS_TECHNICAL` `technical_corrected_candidate`: Auto-draft corrected candidate rebuilt 33/33 B4/B5 full-canvas 2048 RGBA non-empty layers.
- `PASS_DRAFT` `auto_anchor_scope`: Automatic first-pass anchors were applied to all 16 B4 and 17 B5 revise targets.
- `REVIEW_REQUIRED` `visual_overlay_gate`: Overlay sheet is generated for human review. Auto-draft placement cannot approve B4/B5 material quality by itself.
- `HOLD_UNSUPPORTED_CONTROL` `hairfront_contract_gate`: ParamHairFront remains hidden until corrected hair_front_* children pass overlay QA and motion-readiness checks.
- `BLOCKED` `mini_real_cubism_gate`: Do not unlock Mini Cubism diagnostic or real Cubism authoring from this auto-draft overlay evidence.

## Decision

Keep the auto-draft corrected B4/B5 layers as review candidates only. They reduce manual work but still need 주인님 visual review and possibly targeted editor adjustments.

## Next Action

- Review the overlay sheet and mark only visibly bad B4/B5 parts for manual adjustment.
- Save real target anchors for those parts if needed.
- Rebuild corrected candidates and rerun overlay QA before manifest promotion.

## Self Review

- `entry_count`: `33`
- `b4_entry_count`: `16`
- `b5_entry_count`: `17`
- `corrected_candidate_status`: `G6_B4_B5_AUTO_ANCHOR_DRAFT_CORRECTED_CANDIDATE_READY_FOR_OVERLAY_QA`
- `applied_override_count`: `33`
- `overlay_sheet_exists`: `True`
- `has_review_required_gate`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`

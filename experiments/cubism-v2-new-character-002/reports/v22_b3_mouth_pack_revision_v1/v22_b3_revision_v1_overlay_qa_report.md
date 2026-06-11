# Character 002 v22 B3 Revision v1 Overlay QA

- status: `B3_REVISION_V1_CODEX_OVERLAY_QA_PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- revision layer-pack report: `experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack_revision_v1/v22_b3_revision_v1_layer_pack_report.json`
- previous overlay QA: `experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack/v22_b3_overlay_qa_report.json`
- overlay sheet: `experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack_revision_v1/v22_b3_revision_v1_overlay_qa.png`

## Checks

- `PASS_RECORDED` `previous_failure_preserved`: Previous B3 overlay remains recorded as B3_CODEX_OVERLAY_QA_REVISE_EXTRACTION_OR_REGENERATE_HUMAN_REVIEW_REQUIRED; revision v1 does not overwrite that failed evidence.
- `PASS_TECHNICAL` `technical_layer_pack`: Revision v1 layer-pack self-review reports 12/12 expected outputs, 0 missing, 0 empty, all RGBA 2048.
- `PASS_CANDIDATE` `open_internals_overlay`: Revision v1 derives mouth_inner, teeth, and tongue from the same coherent wide-mouth crop, removing the previous large rectangular skin patch and reducing the pasted-helper look.
- `REVIEW_VISUALLY` `mouth_anchor_and_scale`: The open-mouth candidate is coherent but still needs 주인님 review for mouth anchor, expression size, and fit against the source face.
- `REVIEW_VISUALLY` `wide_reference_restraint`: Wide-open reference remains subject to the v21/v13 MouthOpenY 0.85 restraint before material promotion.
- `REQUIRED` `human_visual_review`: 주인님 human visual review is required before promoting B3 revision v1 beyond candidate.

## Decision

B3 revision v1 fixes the first extraction's obvious pasted-internals failure enough to continue as a candidate, but it is not final material PASS until 주인님 visual review accepts anchor, scale, and MouthOpenY restraint.

## Next Action

- Use B3 revision v1 as the current B3 candidate for human review or manual anchor correction.
- If 주인님 rejects mouth size/anchor or wide-open restraint, regenerate B3 or tune revision anchors without reusing v10/v12/v13 mouth PNGs.
- Do not proceed to Mini Cubism diagnostics from B3 until visual QA accepts the mouth candidate.

## Self Review

- `revision_layer_pack_status`: `B3_REVISION_V1_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED`
- `revision_layer_self_review_status`: `PASS`
- `previous_overlay_status`: `B3_CODEX_OVERLAY_QA_REVISE_EXTRACTION_OR_REGENERATE_HUMAN_REVIEW_REQUIRED`
- `check_count`: `6`
- `has_pass_candidate_gate`: `True`
- `has_human_required_gate`: `True`
- `has_review_visually_gate`: `True`
- `status`: `PASS`

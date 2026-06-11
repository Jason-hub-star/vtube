# Character 002 v22 B2 Overlay QA

- status: `B2_CODEX_OVERLAY_QA_PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- B2 layer-pack report: `experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_layer_pack_report.json`
- overlay sheet: `experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_overlay_qa_on_b1_clean_base.png`

## Checks

- `PASS_CANDIDATE` `open_eye_socket_alignment`: Open eye components land in the B1 clean socket region with left/right spacing consistent enough for extraction-candidate QA.
- `PASS_CANDIDATE` `fixed_white_policy_visible`: Sclera layers are socket-bound full-canvas layers; iris/pupil/highlight can move independently while whites remain fixed.
- `PASS_CANDIDATE` `iris_pupil_highlight_anchor_lock`: B2 layer-pack anchor checks record same-target placement for iris, pupil, and highlight clusters on both eyes.
- `PASS_CANDIDATE` `closed_lid_overlay`: Closed lid lines sit in the expected eye region on the B1 clean base; detailed blink keyform QA remains future Mini Cubism work.
- `REVISE_BEFORE_FINAL_MATERIAL_PASS` `matte_and_style_risk`: White-background extraction can leave soft matte halos and the generated component scale may need manual anchor tuning.
- `REQUIRED` `human_visual_review`: 주인님 human visual review is required before promoting B2 beyond candidate.

## Decision

B2 is acceptable as a candidate input for continuing B3 generation, but it is not final material PASS. Keep visual/human QA, Mini Cubism diagnostics, and real Cubism authoring separate.

## Next Action

- Generate a new B3 mouth-pack raw candidate without using existing v10/v12/v13 mouth assets.
- Keep B2 layer-pack available for later manual anchor correction if 주인님 rejects the overlay scale or socket feel.

## Self Review

- `has_b2_layer_pack_report`: `True`
- `b2_layer_pack_status`: `B2_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED`
- `b2_layer_self_review_status`: `PASS`
- `overlay_sheet_exists`: `True`
- `check_count`: `6`
- `has_human_required_gate`: `True`
- `has_revise_before_final_gate`: `True`
- `status`: `PASS`

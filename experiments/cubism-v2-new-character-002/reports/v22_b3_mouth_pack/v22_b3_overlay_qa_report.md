# Character 002 v22 B3 Overlay QA

- status: `B3_CODEX_OVERLAY_QA_REVISE_EXTRACTION_OR_REGENERATE_HUMAN_REVIEW_REQUIRED`
- B3 layer-pack report: `experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack/v22_b3_layer_pack_report.json`
- overlay sheet: `experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack/v22_b3_overlay_qa_on_b1_clean_base.png`

## Checks

- `PASS_TECHNICAL` `technical_layer_pack`: B3 layer-pack self-review reports 12/12 expected outputs, 0 missing, 0 empty, all RGBA 2048.
- `REVIEW_VISUALLY` `closed_line_overlay`: Closed mouth line can be positioned near the mouth anchor, but corners and subtle lip mask need visual tuning.
- `REVISE_EXTRACTION_OR_REGENERATE` `open_internals_overlay`: Inner mouth, teeth, tongue, and lip masks read as separate pasted elements in the overlay instead of one coordinated mouth opening.
- `REVIEW_VISUALLY` `wide_reference_restraint`: Raw wide reference is coherent, but it still needs MouthOpenY 0.85 restraint review before use.
- `REQUIRED` `human_visual_review`: 주인님 human visual review is required; Codex visual QA currently marks the extracted B3 internals as REVISE.

## Decision

Do not promote B3 layer-pack to material PASS. Keep the raw B3 sheet as useful evidence, but revise extraction or regenerate B3 before proceeding to Mini Cubism diagnostics.

## Next Action

- Revise B3 extraction around one coherent mouth opening, or regenerate a new B3 sheet if teeth/tongue/inner still look pasted.
- Do not reuse v10/v12/v13 mouth PNGs as a shortcut.
- B4 generation may proceed only as independent raw generation planning; B3 remains blocked for material PASS.

## Self Review

- `has_b3_layer_pack_report`: `True`
- `b3_layer_pack_status`: `B3_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED`
- `b3_layer_self_review_status`: `PASS`
- `overlay_sheet_exists`: `True`
- `check_count`: `5`
- `has_revise_gate`: `True`
- `has_human_required_gate`: `True`
- `status`: `PASS`

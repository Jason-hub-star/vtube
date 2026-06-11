# Character 002 v22 B4 Overlay QA

- status: `B4_CODEX_OVERLAY_QA_REVISE_ANCHOR_OR_EXTRACTION_HUMAN_REVIEW_REQUIRED`
- layer pack report: `experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_layer_pack_report.json`
- overlay sheet: `experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_layer_pack_overlay_qa.png`

## Checks

- `PASS_TECHNICAL` `technical_layer_pack`: B4 layer pack generated 16/16 full-canvas 2048 RGBA candidates with no missing or empty outputs.
- `PASS_CANDIDATE` `real_hairfront_children_scope`: hair_front_center/L/R/side/tip outputs exist as independent candidate PNGs, so the HairFront art scope is no longer purely imaginary.
- `REVISE_ANCHOR_OR_EXTRACTION` `front_hair_overlay_alignment`: Overlay sheet shows the current automatic front-hair placement is visually noisy on the face and needs manual anchor correction or crop refinement before material PASS.
- `REVISE_ANCHOR_OR_EXTRACTION` `back_side_hair_overlay_alignment`: Back/side hair candidates are real but the current composite does not align cleanly with the source silhouette and draw-order intent.
- `HOLD_UNSUPPORTED_CONTROL` `hairfront_contract_gate`: ParamHairFront must remain hidden/contract-only until front hair candidates pass visual overlay QA and motion-readiness checks.
- `REQUIRED` `human_visual_review`: 주인님 review is required after crop/anchor correction; technical PNG generation alone cannot approve B4 material.

## Decision

Do not promote B4 to material PASS. Keep the 16 RGBA hair outputs as extraction candidates, but revise anchor placement/crop assignment before enabling ParamHairFront or using B4 for Mini Cubism diagnostics.

## Next Action

- Use manual anchor correction or a refined extraction script for hair_front_* and side/back hair placement.
- Regenerate B4 only if crop refinement cannot make front/side/back hair read as the source hairstyle.
- Keep ParamHairFront hidden until corrected hair_front_* children pass overlay QA.

## Self Review

- `b4_layer_pack_status`: `B4_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED`
- `b4_layer_self_review_status`: `PASS`
- `check_count`: `6`
- `has_revise_gate`: `True`
- `has_human_required_gate`: `True`
- `has_hairfront_contract_gate`: `True`
- `status`: `PASS`

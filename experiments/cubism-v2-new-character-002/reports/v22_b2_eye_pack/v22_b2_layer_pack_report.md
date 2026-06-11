# Character 002 v22 B2 Eye Layer Pack

- status: `B2_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED`
- raw review: `experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_eye_pack_review.json`
- B2 raw image: `experiments/cubism-v2-new-character-002/v22_b2_eye_pack/raw_outputs/b2_eye_pack_reference_001.png`
- normalized layers: `experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers`
- contact sheet: `experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_layer_pack_contact_sheet.png`
- overlay sheet: `experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_layer_pack_overlay_qa.png`

## Expected Outputs

- expected: `18`
- generated: `18`
- missing: `[]`
- empty: `[]`

## Anchor Checks

- `eye_L`: `PASS_ANCHOR_LOCKED_SAME_TARGET` white `[786.0, 681.0]` iris `[795.5, 685.5]` pupil `[788.5, 691.5]` highlight `[788.0, 680.0]`
- `eye_R`: `PASS_ANCHOR_LOCKED_SAME_TARGET` white `[1216.0, 681.0]` iris `[1209.0, 686.0]` pupil `[1218.5, 692.0]` highlight `[1215.0, 680.0]`

## Limits

- RGB white-background sheet extraction can leave soft matte halos around lashes or skin context.
- Iris, pupil, and highlight were split by color masks from one generated cluster and must be reviewed for visual drift after motion tests.
- This does not activate Mini Cubism diagnostic and does not prove real Cubism rig success.

## Next Action

- Run overlay QA against the B1 clean-base sockets.
- If visual QA accepts B2, continue to B3 mouth-pack generation without using existing mouth assets unless 주인님 explicitly allows them.
- If B2 eye detail drifts, regenerate a new B2 sheet instead of importing v19/v20/v21 eye PNGs.

## Self Review

- `raw_review_status`: `B2_RAW_EYE_PACK_CANDIDATE_READY_FOR_EXTRACTION_HUMAN_REVIEW_REQUIRED`
- `expected_output_count`: `18`
- `generated_output_count`: `18`
- `missing_output_count`: `0`
- `empty_output_count`: `0`
- `all_layers_rgba`: `True`
- `all_layers_2048`: `True`
- `forbidden_existing_eye_asset_count`: `6`
- `forbidden_assets_not_output_path`: `True`
- `has_human_required_gate`: `True`
- `status`: `PASS`

# Character 002 v22 B1 Clean Base Review

- status: `B1_RAW_CLEAN_BASE_REFERENCE_READY_FOR_VISUAL_QA`
- source image: `experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png`
- B1 raw image: `experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/raw_outputs/b1_clean_base_underpaint_reference_001.png`
- contact sheet: `experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_clean_base_contact_sheet.png`
- imagegen mode: `built_in_image_gen`

## ROI Metrics

- `eye_L_feature_roi`: source `0.458381`, B1 `0.22251`, status `REVIEW_VISUALLY`
- `eye_R_feature_roi`: source `0.408421`, B1 `0.157004`, status `PASS_REDUCED_FEATURE_RESIDUE`
- `mouth_feature_roi`: source `0.004142`, B1 `0.0`, status `PASS_REDUCED_FEATURE_RESIDUE`

## Visual First Pass

- status: `CODEX_VISUAL_FIRST_PASS_PASS_RAW_REFERENCE`
- Open eyes, irises, eye whites, lashes, mouth line, teeth, and tongue are removed from the generated raw reference.
- Eye and mouth underpaint regions read as continuous skin gradients rather than the previous oval/rectangular patch failure.
- This is still a raw B1 reference image; it must be split/normalized before being treated as 64-part material.

## Limits

- Not a final full-canvas RGBA 64-part layer pack.
- Does not yet create all B1 expected outputs as separated layers.
- Does not unlock B2/B3/B4/B5 promotion by itself; it provides the clean-base reference needed for those generations.

## Next Action

- Use this B1 raw reference as the clean-base style/input when generating or splitting B1 expected outputs.
- Normalize/split B1 expected outputs into full-canvas RGBA layers.
- Run contact-sheet and overlay QA before accepting B1 as material PASS.

## Self Review

- `source_exists`: `True`
- `b1_raw_exists`: `True`
- `source_size`: `(1254, 1254)`
- `b1_raw_size`: `(1254, 1254)`
- `same_size_as_source`: `True`
- `roi_count`: `3`
- `roi_feature_residue_reduced`: `True`
- `status`: `PASS`

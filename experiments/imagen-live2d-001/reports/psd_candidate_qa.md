# See-through PSD Candidate QA

Generated: 2026-06-04T08:46:26.316463+00:00
Status: PASS_WITH_CUBISM_IMPORT

## Gate

- Only `O` See-through candidates with `production_candidate=true` are eligible.
- Raw See-through output is never trusted as production by itself.
- Cubism Editor actual import is still required.

- Accepted layers: 19
- Excluded layers: 13

## PSD Metadata

```json
{
  "exists": true,
  "valid_header": true,
  "channels": 3,
  "width": 2048,
  "height": 2048,
  "depth": 8,
  "color_mode": "RGB",
  "layer_mask_section_length": 10561556,
  "layer_count": 19
}
```

Cubism Editor actual import has passed and import_ready.psd may be trusted.

## Forced Review Caveat

- This pass used 주인님's temporary instruction to mark every current candidate as `O` and continue the pipeline.
- 주인님 also requested `front_hair` and both arms to pass, so forced production candidates were added for `front_hair`, `R_arm`, and `L_arm`.
- Cubism import smoke passed: the rebuilt PSD opened in Live2D Cubism Editor 5.3.01 and did not flatten into a single image.
- PSD metadata and Cubism evidence show 19 concrete layers.
- Treat this as a technical PSD import pass only. It is not final art-quality approval for mouth, hair, arms, clothes, neck, or face boundaries.

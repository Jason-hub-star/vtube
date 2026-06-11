# Mini Cubism Pack Splitter v0 Review Summary

- Status: BLOCK_MINI_CUBISM_PROMOTION_VISUAL_FAIL
- Local QA status: PASS_WITH_LOCAL_ADAPTER_PROBE
- Actual LayerD BiRefNet outputs: 4
- Actual SAM2 ROI outputs: 16
- PASS actual-model candidates: 3
- VISUAL_FAIL actual-model candidates: 15
- Mini Cubism promotion: blocked

## Why Blocked

SAM2 ROI refinement runs, but most accessory/keypose candidates are cropped, tiny fragments, or broad masks. These must not pass just because the model runtime succeeded.

## Next Automatic Action

Regenerate or re-layout accessory/keypose pack source assets with more spacing and full part visibility, then rerun SAM2 ROI refinement and actual-model QA.

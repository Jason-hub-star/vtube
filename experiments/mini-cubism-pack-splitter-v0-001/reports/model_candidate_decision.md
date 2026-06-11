# Mini Cubism Pack Model Candidate Decision

Generated: 2026-06-05T06:46:05.945702+00:00

## Verdict

Mini Cubism project promotion stays blocked. The model comparison is complete enough to choose roles, but accessory and keypose pack splitting still needs relayout/regeneration before rig promotion.

## Pack Decisions

| Pack | Primary | Fallback | Use | Blocker | Next action |
|---|---|---|---|---|---|
| `base_mannequin` | imagegen alpha base | none | Keep the two-piece rig underlayer: chest and pelvis covered, abdomen visible. | none | Use as the stable mannequin target for pack fitting. |
| `hair_pack` | ZhengPeng7/BiRefNet_HR | ZhengPeng7/BiRefNet | Full-pack alpha cleanup, then separate hair-specific splitter for front/side/back/tips. | No actual 18+ strand-level hair split yet. | Run hair band/contour splitter on the selected BiRefNet HR mask. |
| `outfit_pack` | ZhengPeng7/BiRefNet_HR | ZhengPeng7/BiRefNet | Full-pack alpha cleanup for outfit pieces; semantic Fashion SegFormer is not selected. | No proven semantic outfit label split from Fashion SegFormer. | Use geometry/ROI splitter for sleeves, top, frills, ribbons on BiRefNet HR alpha. |
| `accessory_pack` | ZhengPeng7/BiRefNet_HR | ZhengPeng7/BiRefNet | Use only as full-pack alpha cleanup for now. | Current SAM2 ROI outputs are cropped/fragments.<br>Small accessories are too dense for the current layout. | Regenerate or relayout accessory pack with larger spacing, then retry connected-component or SAM2 ROI. |
| `keypose_asset_pack` | ZhengPeng7/BiRefNet | ZhengPeng7/BiRefNet_HR | Use only as full-pack alpha cleanup for now; do not split final eye/mouth states from current SAM2 output. | Current SAM2 ROI outputs are cropped/fragments.<br>BiRefNet-matting over-expands keypose alpha. | Regenerate as separate eye keypose pack and mouth keypose pack with larger spacing and no overlap. |

## Model Decisions

| Model | Status | Decision | Actual outputs | Why |
|---|---:|---|---:|---|
| LayerD BiRefNet | RUNTIME_PASS_REVISE_MASK | REFERENCE_ONLY | 4 | Hair/outfit are usable candidates, but accessory/keypose masks are broad. |
| BiRefNet | PASS | SELECTED_STABLE_FALLBACK | 4 | All four packs passed runtime and simple mask gates with no broad-mask issues. |
| BiRefNet HR | PASS | SELECTED_PRIMARY_ALPHA | 4 | All four packs passed and it is the best default for full-pack alpha cleanup. |
| BiRefNet matting | RUNTIME_PASS_REVISE_MASK | OPTIONAL_EDGE_CLEANUP | 4 | Hair/outfit/accessory passed, but keypose became near full-canvas and must not be used there. |
| SAM2 tiny ROI | RUNTIME_PASS_VISUAL_FAIL | REJECT_CURRENT_OUTPUTS | 16 | Runtime passed, but strict visual QA detected cropped or fragment masks. |
| SAM2 large ROI | RUNTIME_PASS_VISUAL_FAIL | REJECT_CURRENT_OUTPUTS | 16 | Large model did not improve the ROI crop/fragment failure pattern. |
| Fashion SegFormer | BLOCKED_MODEL_PROBE | BLOCKED_NOT_SELECTED | 0 | The current HF repo cannot be loaded by the default Transformers image-segmentation pipeline. |
| AnimeInstance | BLOCKED_MODEL_PROBE | BLOCKED_NOT_SELECTED | 0 | The current HF repo is not directly loadable by Transformers without a custom legacy wrapper. |

## Practical Pipeline

1. Keep the current two-piece base mannequin.
2. Use `BiRefNet_HR` as the default alpha cleanup for hair and outfit packs.
3. Use `BiRefNet` or `BiRefNet_HR` only as full-pack alpha cleanup for accessory and keypose packs.
4. Do not use current SAM2 ROI outputs for production because they are cropped/fragments.
5. Regenerate or relayout accessory/keypose packs with larger spacing, then retry component/SAM2 splitting.
6. Build Mini Cubism only after the next QA report has no visual fail for accessory/keypose outputs.

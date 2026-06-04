# LIVE2D-KEYPOSE-SPEC-001

Date: 2026-06-03

## Decision

Production target is Live2D/Cubism style rigging, not PNG frame swapping.

The current mouth/blink experiments are placement and key-pose evidence. They prove where generated candidates fit on the canonical face and which pose states are visually usable. They do not define the final runtime animation method.

## Production Direction

Live2D production should use:

- PSD-ready separated parts
- Cubism Editor ArtMesh and Deformer setup
- standard Live2D parameters
- parameter keyforms for eye/mouth states
- EyeBlink and lip-sync style parameter driving

## Blink Mapping

Current blink assets:

- `/Users/family/jason/Vtube/experiments/blink-apply-review-001/layers/blink_half_corrected_full.png`
- `/Users/family/jason/Vtube/experiments/blink-apply-review-001/layers/blink_mostly_closed_corrected_full.png`
- `/Users/family/jason/Vtube/experiments/blink-apply-review-001/layers/blink_closed_corrected_full.png`

Live2D key-pose use:

| Current candidate | Live2D parameter target | Meaning |
|---|---|---|
| canonical open eye | `ParamEyeLOpen=1`, `ParamEyeROpen=1` | open |
| `blink_half_corrected_full.png` | `ParamEyeLOpen≈0.5`, `ParamEyeROpen≈0.5` | half blink reference |
| `blink_mostly_closed_corrected_full.png` | `ParamEyeLOpen≈0.2`, `ParamEyeROpen≈0.2` | mostly closed reference |
| `blink_closed_corrected_full.png` | `ParamEyeLOpen=0`, `ParamEyeROpen=0` | closed reference |

These PNGs are reference/key-pose guides for mesh deformation or replacement drawing in PSD/Cubism. They are not the production blink runtime mechanism.

## Mouth Mapping

Current mouth assets:

- `/Users/family/jason/Vtube/experiments/mouth-apply-delta-001/layers/*_corrected_full.png`

Live2D key-pose use:

| Current candidate type | Live2D parameter target | Meaning |
|---|---|---|
| neutral/smile | `ParamMouthOpenY≈0`, `ParamMouthForm>0` | smile/closed mouth |
| small open | `ParamMouthOpenY≈0.3` | small mouth open |
| wide/happy open | `ParamMouthOpenY≈0.7-1.0` | wide open |
| o vowel | `ParamMouthOpenY≈0.5`, `ParamMouthForm<0` | round mouth |

These mouth PNGs are placement/style references for PSD layer drawing and Cubism keyforms, not final frame-swap runtime assets.

## What Current Tests Prove

- Full-canvas placement can be reviewed without screenshot guessing.
- Manual visual correction can be stored as calibrated canvas coordinates.
- Mouth candidates are usable by user review.
- Blink staged candidates exist and can be aligned, but current saved placement is still `REVISE`.
- Numeric ROI and human visual review must remain separate.

## What Current Tests Do Not Prove

- They do not create Live2D ArtMesh.
- They do not create Deformers.
- They do not create `.moc3` or `.model3.json`.
- They do not prove Cubism import compatibility.
- They do not prove production blink animation.

## Next Tests

1. `PSD-LAYER-SCHEMA-001`
   - Define PSD layer names for face, eyes, eyelids, iris, lash, mouth states.
   - Include left/right eye separation.
   - Include hidden/overpaint areas needed for deformation.

2. `LIVE2D-PARAM-MAP-001`
   - Map current pose evidence to `ParamEyeLOpen`, `ParamEyeROpen`, `ParamMouthOpenY`, `ParamMouthForm`.
   - Create a keyform checklist for Cubism Editor.

3. `CUBISM-IMPORT-CHECKLIST-001`
   - Define what a human rigger must verify in Cubism Editor.
   - Include PSD import, ArtMesh, Deformer, parameter, EyeBlink settings.

4. `RIG-REFERENCE-PACK-001`
   - Package canonical, corrected mouth references, corrected blink references, ROI overlays, and reports for rigger handoff.

## Decision

Keep current generated assets as reference/key-pose evidence.

Do not present PNG frame swapping as the final Live2D production approach.

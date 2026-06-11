# Mini Cubism Preview Visual Status

- candidate: `model_edit_v4_strict_mouth`
- status: `REVISE_MANUAL_ALIGNMENT_REQUIRED`
- recorded_at: `2026-06-09`
- preview project: `experiments/cubism-v2-new-character-002/model_edit_v4_strict_mouth/mini_cubism_diagnostic_project`
- validator: Mini Cubism project contract PASS, visual alignment REVISE

## Finding

`face_base_clean` itself is clean enough for this pass: isolated ROI review did not show obvious baked open-eye or mouth residue. The visible issue in Mini Cubism preview is eye/mouth layer assembly alignment: the eye keypose layers read too large and the mouth placement reads off relative to the clean face.

## Decision

Do not restart character generation. Keep `model_edit_v4_strict_mouth` as the current material candidate and route to manual eye/mouth anchor + scale correction before rebuilding contact sheet, assembly QA, and Mini Cubism diagnostic preview.

# Cubism v2 Character 002 Layer Alpha Seed v5 Visual QA

- status: `REVISE_MINI_CUBISM_BLOCKED`
- candidate: `material_pack_first_v5_layer_alpha_seed_strict_expr`
- validator: `PASS_READY_FOR_VISUAL_QA`
- reviewed_at: `2026-06-09T02:06:45Z`

## Decision

Do not proceed to Mini Cubism diagnostic preview from this candidate.

The source/front character can stay, but the current local/source-inpaint cleanup path is not enough for production material quality. The next pass should regenerate or manually repaint clean-base assets with model-native/edit-based inpainting:

- `eye_L_clean_socket`
- `eye_R_clean_socket`
- `eye_L_closed_underpaint`
- `eye_R_closed_underpaint`
- `mouth_base_clean`

## Findings

- Mouth: strict expression alpha filtering greatly reduced the obvious oval patch boundary, but `mouth_base_clean_only` still leaves the original source mouth line visible.
- Eye: clean socket and underpaint overlays still look like smeared/inpainted patches around hair, eyelids, and skin.
- Mini Cubism: blocked until overlay QA clears these visual issues.

## Evidence

- `experiments/cubism-v2-new-character-002/reports/layer_alpha_seed_v5/overlay_qa/mouth_overlay_qa_sheet.png`
- `experiments/cubism-v2-new-character-002/reports/layer_alpha_seed_v5/overlay_qa/eye_overlay_qa_sheet.png`
- `experiments/cubism-v2-new-character-002/reports/layer_alpha_seed_v5/overlay_qa/face_overlay_qa_sheet.png`
- `experiments/cubism-v2-new-character-002/reports/layer_alpha_seed_v5/layer_alpha_seed_keypose_validation_report.json`
- `experiments/cubism-v2-new-character-002/reports/layer_alpha_seed_v5/layer_alpha_seed_overlay_qa_report.json`

# Cubism v2 Character 002 Model-Edit v3 Visual QA

- status: `REVISE_MINI_CUBISM_BLOCKED`
- candidate: `model_edit_v3_hybrid_eye_filtered_mouth_v2`
- validator: `PASS_READY_FOR_VISUAL_QA`

## Decision

Do not proceed to Mini Cubism diagnostic preview with the full mouth set yet.

The model-edited clean base fixed the original clean-base problem. The best current path is not restarting the character. Keep:

- `new_character_002_source_front`
- `model_edit_v2/model_edit_v3` clean base
- v0-style eye/mouth art direction from the good contact sheet

Next repair only the mouth expression alpha so the v0 mouth shapes keep their look without carrying skin patches.

## Findings

- Clean base: PASS for review. Baked eyes and mouth are removed without the old local-inpaint smear.
- Eyes: PASS for diagnostic review in v3 hybrid. The large oval eye patch boundary is gone.
- Mouth: REVISE. v0 mouth expression shapes are visually nice in the contact sheet, but still include visible skin-patch alpha in assembly.

## Evidence

- `experiments/cubism-v2-new-character-002/reports/model_edit_v3_hybrid/model_edit_v3_hybrid_contact_sheet.png`
- `experiments/cubism-v2-new-character-002/reports/model_edit_v3_hybrid/assembly_qa/face_assembly_qa_sheet.png`
- `experiments/cubism-v2-new-character-002/reports/model_edit_v3_hybrid/assembly_qa/mouth_assembly_qa_sheet.png`

# Next Agent Handoff

Updated: 2026-06-09

## Start Here

Read these first:

```text
/Users/family/jason/Vtube/AGENTS.md
/Users/family/jason/Vtube/docs/status/PROJECT-STATUS.md
/Users/family/jason/Vtube/vtube-validation-evidence-log.md
/Users/family/jason/Vtube/docs/ref/CUBISM-V2-MATERIAL-PACK-FIRST-GENERATION.md
/Users/family/jason/Vtube/experiments/reference-model-structure-001/reports/cubism_v2_new_model_v2_standard_part_spec.md
/Users/family/jason/Vtube/experiments/reference-model-structure-001/reports/cubism_v2_character_prompt_template.md
```

Address the user as `주인님` and work in Korean by default.

## Current Direction

The project is still Live2D/Cubism-first:

```text
official/reference model success patterns
-> Cubism v2 production spec schema v2
-> confirmed 64-part v2_standard source taxonomy
-> matched single-source character
-> PSD/material pack
-> real Cubism Warp/Rotation Deformer and Keyform authoring
-> CMO3 inspector and runtime validation
```

Do not switch the project into PNG frame-swap production. Mini Cubism is only local preview/QA evidence.

## Current State

The current blocker is material generation strategy, not model selection or parameter spec:

```text
cubism-v2-new-character-001 material pack import/structure: technical PASS
cubism-v2-new-character-001 face/eye/mouth visual QA: FAIL
local keypose PNG generation: validator PASS only, visual quality too low
cubism-v2-new-character-002 material-pack-first: technical PNG PASS, human review says regenerate clean bases
next default: regenerate/edit weak clean sockets, closed underpaint, and mouth_base_clean before Mini Cubism
```

Latest confirmed judgement:

- `cubism-v2-new-character-001` proved that material-pack-late repair causes baked-eye remnants, stains, and procedural patches.
- `local_generated_keypose_v1` created real 2048 RGBA PNG files and passed `validate_cubism_v2_keypose_pngs.py`, but the contact sheet is not visually acceptable.
- Do not treat local validator PASS as production material PASS.
- `cubism-v2-new-character-002` now has source/front, raw material sheets, 21 normalized 2048 RGBA candidates, validator PASS for the required 19 clean/keypose assets, and overlay QA `OVERLAY_QA_REVISE_MINI_CUBISM_BLOCKED`.
- Eye/mouth anchors were corrected and rerun, but 주인님 confirmed clean sockets/underpaint and `mouth_base_clean` still show visible pasted skin patch boundaries. Do not proceed to Mini Cubism until regenerated or edited clean-base assets pass overlay QA.

## Latest Useful URLs

These may be running from the prior session:

```text
http://127.0.0.1:8076/  # current Mini Cubism diagnostic preview if still alive
```

If the server is not running and you need the current failure fixture, restart 8076 with:

```bash
python3 scripts/mini_cubism_preview_server.py \
  --project experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_closed_underpaint_manual_bbox_v1 \
  --port 8076
```

## Important Files

New default planning document:

```text
/Users/family/jason/Vtube/docs/ref/CUBISM-V2-MATERIAL-PACK-FIRST-GENERATION.md
```

Current character-001 failure/fixture evidence:

```text
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/local_generated_keypose_v1/local_generated_keypose_contact_sheet.png
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/local_generated_keypose_v1/local_generated_keypose_validation_report.json
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/clean_socket_keypose_requirements.json
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-001/material_pack_v0
```

Failure/control candidates to keep but not promote:

```text
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-001/material_pack_v0/layer_manifest.anchor_position_repair_candidate_v1.json
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-001/material_pack_v0/layer_manifest.clean_neutral_opacity_candidate_v1.json
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-001/material_pack_v0/layer_manifest.group_position_clean_candidate_v1.json
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-001/material_pack_v0/layer_manifest.anchor_masked_clean_candidate_v1.json
```

Core production specs remain ready:

```text
/Users/family/jason/Vtube/experiments/reference-model-structure-001/reports/cubism_v2_production_design_spec.json
/Users/family/jason/Vtube/experiments/reference-model-structure-001/reports/cubism_v2_new_model_v2_standard_part_spec.json
/Users/family/jason/Vtube/experiments/reference-model-structure-001/reports/cubism_v2_character_prompt_template.md
/Users/family/jason/Vtube/experiments/reference-model-structure-001/reports/face_tracking_to_cubism_parameter_map.md
```

## Next Action

Continue `cubism-v2-new-character-002` from the material-pack-first technical candidate stage.

Current evidence:

```text
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/material_keypose_pack_closeups.raw.png
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/material_keypose_pack_fullface.raw.png
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/material_pack_first_v0/normalized_layers/
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/material_pack_first_keypose_validation_report.json
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/material_pack_first_contact_sheet.png
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/material_pack_first_visual_qa_report.md
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/material_pack_first_overlay_qa_report.md
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/material_pack_first_overlay_human_review_20260609.md
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/material_pack_first_v5_layer_alpha_seed_strict_expr/normalized_layers/
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/layer_alpha_seed_v5/layer_alpha_seed_keypose_validation_report.json
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/layer_alpha_seed_v5/layer_alpha_seed_visual_qa_report.md
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/model_edit_v3_hybrid/normalized_layers/
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/model_edit_v3_hybrid/model_edit_v3_visual_qa_report.md
```

Next minimum goal:

```text
1. Do not restart the whole character. Keep source_front/style and model-edited clean base.
2. Treat local/source-inpaint v1-v5 as visual REVISE evidence; model_edit_v3_hybrid improves clean base and eyes but mouth expression alpha still needs repair.
3. Next repair only mouth expression alpha: keep the good v0 mouth shapes, remove skin-patch alpha from `mouth_closed_smile`, `mouth_small_open`, `mouth_wide_open`, and `mouth_o_vowel`.
4. Rerun keypose validation and assembly/overlay QA.
5. Only after mouth assembly QA clears visible skin patches, build Mini Cubism diagnostic preview.
```

Suggested script names:

```text
/Users/family/jason/Vtube/scripts/build_cubism_v2_material_first_generation_spec.py
/Users/family/jason/Vtube/scripts/normalize_cubism_v2_material_first_outputs.py
```

Suggested output:

```text
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/material_pack_first_v0/normalized_layers/
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/material_pack_first_generation_spec.json
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/material_pack_first_keypose_validation_report.json
/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/material_pack_first_contact_sheet.png
```

## Do Not Do

- Do not promote `8065`, `8066`, `8067`, `8068`, `8069`, or `8070`.
- Do not promote `local_generated_keypose_v1`; it is technical validator evidence only.
- Do not treat Mini Cubism validator PASS as visual success.
- Do not start by patching `cubism-v2-new-character-001` unless 주인님 explicitly asks to continue that failure fixture.
- Do not generate one labeled 64-part sheet. Generate a coordinated source + material/keypose set.
- Do not delete evidence JSON, QA reports, generated manifests, or manual review JSON.
- Do not revert unrelated user or Claude changes.
- Do not proceed to real Cubism deformer/keyform authoring until face/eye/mouth material visual QA passes.

## Verification

Recent successful checks:

```bash
python3 -m py_compile scripts/generate_cubism_v2_keypose_pngs_from_pack_local.py
python3 scripts/validate_cubism_v2_keypose_pngs.py --input-dir experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/local_generated_keypose_v1/normalized_layers --out experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/local_generated_keypose_v1/local_generated_keypose_validation_report.json
bash /Users/family/jason/jason-agent-harness-template/scripts/check-harness.sh
```

Run during the next character-002 setup:

```bash
python3 -m py_compile scripts/build_cubism_v2_material_first_generation_spec.py
python3 scripts/validate_cubism_v2_keypose_pngs.py --input-dir experiments/cubism-v2-new-character-002/material_pack_first_v0/normalized_layers --out experiments/cubism-v2-new-character-002/reports/material_pack_first_keypose_validation_report.json
bash /Users/family/jason/jason-agent-harness-template/scripts/check-harness.sh
```

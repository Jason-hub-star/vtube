# See-through Cubism Handoff

Generated: 2026-06-04T08:46:26.316463+00:00
Status: PASS_WITH_CUBISM_IMPORT

## Files

- Candidate PSD: `import_ready_candidate.psd`
- Candidate layers: `psd_candidate_layers/`
- Visual review: `reports/part_visual_review.json`
- Gate report: `reports/psd_candidate_gate_report.json`

## Cubism Smoke Requirement

Create `reports/cubism_import_smoke.json` after opening the PSD in Cubism Editor:

```json
{ "cubism_import_success": true, "layers_flattened": false, "notes": "Layer list visible." }
```

## Current Smoke Result

- Cubism Editor 5.3.01 actual import smoke: PASS.
- Promoted PSD: `import_ready.psd`.
- Visible concrete Cubism/PSD layers: 19.
- Forced MVP candidates included: `front_hair`, `R_arm`, `L_arm`.
- FREE-limit MVP rig audit: PASS.
- MVP rig checklist: `reports/cubism_mvp_rig_smoke_checklist.md`.
- MVP rig plan JSON: `reports/cubism_mvp_rig_smoke_plan.json`.
- Saved CMO3 artifact: `cubism_mvp_rig.cmo3`.
- CMO3 structure report: `reports/cmo3_structure_report.json` and `reports/cmo3_structure_report.md`.
- MOC3 export smoke bundle: `moc3_export_smoke/`.
- Current validation: `reports/cubism_mvp_rig_validation.json` is `MOC3_EXPORT_SMOKE_PASS_PENDING_DEFORMER_KEYFORM_VALIDATION`.
- Current CMO3 structure status: WARN. The inspector confirms 19 `CArtMeshSource` entries and 27 `CParameterSource` entries, but 0 `CWarpDeformerSource`, 0 `CRotationDeformerSource`, and 0 `KeyformBindingSource` entries. This means the project has imported meshes and parameters, but not professional deformer/keyform rigging yet.

## Rigging Caution

This pack is allowed for a throwaway MVP rigging pass, but it is not final art-quality approval. `front_hair` is forced from canonical dark-pixel extraction, and `R_arm`/`L_arm` are forced from See-through handwear outputs. Before serious ArtMesh/Deformer work, re-check `mouth_line`, `clothes`, `neck`, `face_base`, hair, and arms in the review app and downgrade contaminated parts from forced `O` to `REVISE`.

## MVP Rig Output Targets

- Save Cubism project as `cubism_mvp_rig.cmo3`.
- Capture evidence screenshots under `reports/cubism_mvp_rig_evidence/`.
- Write final manual validation as `reports/cubism_mvp_rig_validation.json`.
- Re-run `node scripts/inspect_cmo3_structure.mjs --experiment-id imagen-live2d-001` after every Cubism save that changes rig structure.
- Runtime export smoke is already saved under `moc3_export_smoke/`; update the validation report after checking ArtMesh, Deformer, keyforms, draw order, and overhang in Cubism.

## Minimal Deformer Change Test

Baseline has been saved as:

- `reports/cmo3_structure_baseline_before_deformer_test.json`
- `reports/cmo3_structure_baseline_before_deformer_test.md`

After creating a small Warp Deformer in Cubism, save `cubism_mvp_rig.cmo3`, then run:

```bash
cd /Users/family/jason/Vtube
node scripts/inspect_cmo3_structure.mjs \
  --experiment-id imagen-live2d-001 \
  --out-json experiments/imagen-live2d-001/reports/cmo3_structure_after_deformer_test_current.json \
  --out-md experiments/imagen-live2d-001/reports/cmo3_structure_after_deformer_test_current.md

python3 scripts/compare_cmo3_structure_reports.py \
  --before experiments/imagen-live2d-001/reports/cmo3_structure_baseline_before_deformer_test.json \
  --after experiments/imagen-live2d-001/reports/cmo3_structure_after_deformer_test_current.json \
  --expect-warp-increase \
  --out-json experiments/imagen-live2d-001/reports/cmo3_structure_deformer_test_delta.json \
  --out-md experiments/imagen-live2d-001/reports/cmo3_structure_deformer_test_delta.md
```

If the Warp Deformer is really saved into `.cmo3`, the delta check should pass with `warp_deformers.delta > 0`.

The current `cubism_mvp_rig.cmo3` was copied from 주인님's saved file at `/Users/family/jason/URHYNIX/import_ready_candidate.cmo3`. Treat it as the tracked CMO3 baseline, then update validation after inspecting actual ArtMesh, Deformer, and keyform state inside Cubism.

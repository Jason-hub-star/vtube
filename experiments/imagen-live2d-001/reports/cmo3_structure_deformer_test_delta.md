# CMO3 Structure Delta Report

Generated: 2026-06-05T14:52:01.985681+00:00

Status: **FAIL_EXPECTATION_NOT_MET**

Before: `experiments/imagen-live2d-001/reports/cmo3_structure_baseline_before_deformer_test.json`

After: `experiments/imagen-live2d-001/reports/cmo3_structure_after_deformer_test_current.json`

## Count Deltas

| Item | Before | After | Delta |
|---|---:|---:|---:|
| art_meshes | 19 | 19 | 0 |
| parameters | 27 | 27 | 0 |
| parts | 1 | 1 | 0 |
| warp_deformers | 0 | 0 | 0 |
| rotation_deformers | 0 | 0 | 0 |
| keyform_grids | 20 | 20 | 0 |
| keyform_bindings | 0 | 0 | 0 |
| layers | 19 | 19 | 0 |

## Expectation Checks

| Check | Status | Message |
|---|---:|---|
| expected_warp_deformer_increase | FAIL | warp deformer delta = 0 |
| expected_keyform_binding_increase | FAIL | keyform binding delta = 0 |

## Name Deltas

No name-level changes.

## Interpretation

- This proves saved structure changes only.
- It does not prove final visual motion quality.
- Runtime/render and Cubism visual overhang validation remain separate gates.

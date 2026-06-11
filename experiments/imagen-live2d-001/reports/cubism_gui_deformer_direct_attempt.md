# Cubism GUI Deformer Direct Attempt

Date: 2026-06-04

## Goal

Try to create a Warp Deformer directly in Cubism Editor through macOS automation, then verify the saved `.cmo3` with `scripts/inspect_cmo3_structure.mjs`.

## Attempt

Opened:

```text
experiments/imagen-live2d-001/cubism_mvp_rig.cmo3
```

Automated menu path reached:

```text
모델링 > 디포머 > 워프 디포머 생성...
```

The Warp Deformer creation dialog opened. The UI was accessible enough to read menu names and dialog/window metadata, but button clicks were unreliable through Accessibility APIs. Coordinate clicks were also affected by foreground window focus and Retina coordinate scaling.

During the attempt, Cubism displayed:

```text
텍스쳐 아틀라스가 생성된 후에 호출해주세요.
```

## Result

The direct GUI automation attempt did not produce a saved CMO3 structure delta.

Evidence:

```bash
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

Delta status:

```text
FAIL_EXPECTATION_NOT_MET
```

## Decision

Do not use screenshot/coordinate-only Cubism GUI automation as the main rigging authoring path.

Keep GUI automation only as a secondary smoke helper. Prefer:

1. Cubism manual rigging for authoring.
2. CMO3 structure inspector for saved structure verification.
3. Programmatic positive fixtures for inspector regression tests.
4. Later runtime/render validation for motion quality.


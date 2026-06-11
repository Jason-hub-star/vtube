# Cubism v2 Material Pack Import Smoke

Status: `PASS_CUBISM_IMPORT_SMOKE`

Tested at: `2026-06-08T15:03:15+09:00`

## Result

`import_ready_candidate.psd` opened in Live2D Cubism Editor 5.3.01 as `import_ready_candidate`.

The PSD was not flattened into a single image. The Cubism Parts panel showed individual imported layer entries, including:

- `61_collar_front`
- `56_hair_front_tip_R`
- `55_hair_front_tip_L`
- `54_hair_front_side_R`
- `53_hair_front_side_L`
- `52_hair_front_R`
- `51_hair_front_L`
- `50_hair_front_center`
- `44_mouth_corner_R`
- `43_mouth_corner_L`
- `40_mouth_lower_lip_mask`
- `39_mouth_upper_lip_mask`

## Evidence

- Candidate PSD: `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-001/material_pack_v0/import_ready_candidate.psd`
- Source validation: `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-001/material_pack_v0/reports/material_asset_validation_report.json`
- Imported-layer screenshot: `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-001/material_pack_v0/reports/cubism_import_smoke_imported_layers.png`
- Cubism log: `/Users/family/Library/Live2D/Cubism5.3_Editor/logs/log.txt`

Key log lines:

```text
2026.06.08 at 15:01:49 KST INFO  java.io.PrintStream -1 write - Read Header:26
2026.06.08 at 15:01:49 KST INFO  java.io.PrintStream -1 write - Read ColorModeData:4
2026.06.08 at 15:01:49 KST INFO  java.io.PrintStream -1 write - Read ImageResources:98
2026.06.08 at 15:01:50 KST INFO  java.io.PrintStream -1 write - Read LayerAndMaskInfo:8737760
2026.06.08 at 15:01:50 KST INFO  java.io.PrintStream -1 write - Read ImageData:12582914
2026.06.08 at 15:01:50 KST INFO  java.io.PrintStream -1 write - load @PSDDocument : 86.45 msec
```

## Interpretation

This passes the Cubism import gate for the current PSD candidate:

- PSD metadata: 2048x2048, RGB, 8-bit, 62 layers.
- Cubism Editor loaded the PSD through the internal model setup flow.
- Individual layer entries are visible in the Parts panel.
- `import_ready_candidate.psd` was copied to `import_ready.psd` as the technical import-gate pass artifact.

This does not mean the character is rigged. The next production gates are still:

- human visual cleanup for the remaining semantic/mask issues,
- real ArtMesh creation,
- Warp/Rotation Deformer authoring,
- KeyformBinding creation,
- CMO3 inspector before/after comparison,
- runtime export smoke.

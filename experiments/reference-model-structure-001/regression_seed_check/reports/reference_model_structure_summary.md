# Reference Model Structure Summary

Generated: 2026-06-05T14:50:25.617654+00:00

## Counts

| Item | Count |
|---|---:|
| Models | 4 |
| FULL_STRUCTURE | 2 |
| RUNTIME_ONLY | 0 |
| METADATA_ONLY | 2 |
| KEEP | 1 |
| REFERENCE_ONLY | 1 |
| IGNORE | 2 |

## Comparison

| ID | Mode | Decision | ArtMesh | Param | Warp | Rotation | KeyBinding | Physics | Mask | Glue | Pose | Expr | Motion | Hair/Eye/Mouth/Body/Arm hints |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| local_cmo3_positive_fixture | FULL_STRUCTURE | KEEP | 7 | 23 | 13 | 1 | 23 | 0 | False | False | False | False | False | 1/1/1/2/0 |
| local_imagen_live2d_001 | FULL_STRUCTURE | REFERENCE_ONLY | 19 | 27 | 0 | 0 | 0 | 0 | False | False | False | False | False | 1/1/1/1/0 |
| live2d_official_sample_catalog | METADATA_ONLY | IGNORE | 0 | 0 | 0 | 0 | 0 | 0 | False | False | False | False | False | 0/0/0/0/0 |
| unverified_public_live2d_model_placeholder | METADATA_ONLY | IGNORE | 0 | 0 | 0 | 0 | 0 | 0 | False | False | False | False | False | 0/0/0/0/0 |

## Recommendation

- Use `KEEP` entries as rig-structure references for deformer/keyform authoring.
- Use `REFERENCE_ONLY` entries for parameter naming, runtime JSON, and physics shape hints.
- Keep `METADATA_ONLY` entries out of local analysis until license and provenance are verified.

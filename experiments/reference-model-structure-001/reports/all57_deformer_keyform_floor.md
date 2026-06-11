# All57 Deformer/Keyform Floor

- generated_at: `2026-06-07T22:40:44.431977+00:00`
- scope: FULL_STRUCTURE only; runtime-only models are excluded from deformer/keyform floor calculations
- full_structure_count: `34`
- rig_floor_eligible_count: `32`

## Global Metrics

| Metric | Full Structure All | Rig Floor Eligible |
|---|---|---|
| `art_meshes` | `{'n': 34, 'min': 1, 'p25': 71.5, 'median': 82.5, 'p75': 148.5, 'max': 299, 'mean': 113.15}` | `{'n': 32, 'min': 33, 'p25': 73.75, 'median': 86.5, 'p75': 155.75, 'max': 299, 'mean': 120.09}` |
| `parts` | `{'n': 34, 'min': 1, 'p25': 20.25, 'median': 21.5, 'p75': 30.25, 'max': 54, 'mean': 25.06}` | `{'n': 32, 'min': 17, 'p25': 21.0, 'median': 22.0, 'p75': 31.5, 'max': 54, 'mean': 26.56}` |
| `parameters` | `{'n': 34, 'min': 1, 'p25': 30.25, 'median': 43.5, 'p75': 69.0, 'max': 138, 'mean': 52.09}` | `{'n': 32, 'min': 25, 'p25': 31.0, 'median': 45.5, 'p75': 70.75, 'max': 138, 'mean': 54.47}` |
| `warp_deformers` | `{'n': 34, 'min': 0, 'p25': 39.0, 'median': 50.5, 'p75': 62.75, 'max': 156, 'mean': 58.18}` | `{'n': 32, 'min': 26, 'p25': 39.0, 'median': 51.0, 'p75': 63.75, 'max': 156, 'mean': 61.81}` |
| `rotation_deformers` | `{'n': 34, 'min': 0, 'p25': 7.5, 'median': 19.0, 'p75': 38.0, 'max': 145, 'mean': 30.65}` | `{'n': 32, 'min': 2, 'p25': 12.75, 'median': 20.0, 'p75': 41.5, 'max': 145, 'mean': 32.53}` |
| `keyform_bindings` | `{'n': 34, 'min': 0, 'p25': 152.75, 'median': 198.0, 'p75': 336.0, 'max': 559, 'mean': 241.29}` | `{'n': 32, 'min': 85, 'p25': 166.25, 'median': 217.5, 'p75': 349.0, 'max': 559, 'mean': 256.31}` |
| `glue` | `{'n': 34, 'min': 0, 'p25': 0.0, 'median': 0.0, 'p75': 5.5, 'max': 36, 'mean': 6.12}` | `{'n': 32, 'min': 0, 'p25': 0.0, 'median': 0.0, 'p75': 8.0, 'max': 36, 'mean': 6.5}` |

## Section Floor

| Section | Warp Named Stats | Rotation Named Stats | Keyform Binding Stats | Models With Named Deformers | Models With Keyforms |
|---|---|---|---|---:|---:|
| `eye` | `{'n': 32, 'min': 4, 'p25': 7.5, 'median': 12.0, 'p75': 13.25, 'max': 20, 'mean': 11.03}` | `{'n': 32, 'min': 0, 'p25': 0.0, 'median': 0.0, 'p75': 0.0, 'max': 2, 'mean': 0.22}` | `{'n': 32, 'min': 0, 'p25': 0.0, 'median': 42.0, 'p75': 60.25, 'max': 85, 'mean': 36.12}` | 32 | 23 |
| `mouth` | `{'n': 32, 'min': 0, 'p25': 1.0, 'median': 1.0, 'p75': 2.0, 'max': 5, 'mean': 1.47}` | `{'n': 32, 'min': 0, 'p25': 0.0, 'median': 0.0, 'p75': 0.0, 'max': 3, 'mean': 0.09}` | `{'n': 32, 'min': 0, 'p25': 0.0, 'median': 8.0, 'p75': 10.0, 'max': 35, 'mean': 7.12}` | 31 | 23 |
| `hair` | `{'n': 32, 'min': 0, 'p25': 8.75, 'median': 11.5, 'p75': 21.0, 'max': 63, 'mean': 16.56}` | `{'n': 32, 'min': 0, 'p25': 0.0, 'median': 0.0, 'p75': 0.5, 'max': 40, 'mean': 4.31}` | `{'n': 32, 'min': 0, 'p25': 0.0, 'median': 5.0, 'p75': 10.25, 'max': 26, 'mean': 6.22}` | 29 | 20 |
| `body_angle` | `{'n': 32, 'min': 3, 'p25': 5.0, 'median': 7.0, 'p75': 10.0, 'max': 18, 'mean': 7.78}` | `{'n': 32, 'min': 0, 'p25': 2.0, 'median': 2.0, 'p75': 4.0, 'max': 13, 'mean': 3.72}` | `{'n': 32, 'min': 0, 'p25': 0.0, 'median': 63.0, 'p75': 78.0, 'max': 146, 'mean': 54.03}` | 32 | 23 |
| `arm` | `{'n': 32, 'min': 0, 'p25': 0.0, 'median': 2.0, 'p75': 6.25, 'max': 30, 'mean': 4.41}` | `{'n': 32, 'min': 0, 'p25': 4.0, 'median': 6.0, 'p75': 14.25, 'max': 72, 'mean': 10.41}` | `{'n': 32, 'min': 0, 'p25': 0.0, 'median': 10.0, 'p75': 36.0, 'max': 164, 'mean': 29.59}` | 29 | 23 |

## Excluded From Floor

- `param_ctrl_pro_ko_seesaw_pc_pro_t02`: `{'art_meshes': 3, 'parts': 1, 'parameters': 1, 'warp_deformers': 0, 'rotation_deformers': 1, 'keyform_bindings': 2, 'glue': 0, 'masks': 0}`
- `param_ctrl_pro_ko_target_pc_pro_t02`: `{'art_meshes': 1, 'parts': 1, 'parameters': 27, 'warp_deformers': 0, 'rotation_deformers': 0, 'keyform_bindings': 0, 'glue': 0, 'masks': 0}`

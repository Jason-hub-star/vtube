# Cubism v2 Tier Spec

- default_choice: `v2_standard`
- source: official sample success-pattern analysis; not source-model reconstruction

## Observed Reference Ranges

| Metric | Range |
|---|---|
| art_meshes | `{'min': 57, 'median': 88.0, 'max': 262, 'mean': 117.65}` |
| parts | `{'min': 19, 'median': 24.0, 'max': 54, 'mean': 27.45}` |
| parameters | `{'min': 25, 'median': 44.0, 'max': 138, 'mean': 56.4}` |
| warp_deformers | `{'min': 27, 'median': 53.5, 'max': 128, 'mean': 62.35}` |
| rotation_deformers | `{'min': 2, 'median': 20.0, 'max': 107, 'mean': 29.8}` |
| keyform_bindings | `{'min': 85, 'median': 220.5, 'max': 497, 'mean': 253.45}` |
| glue | `{'min': 0, 'median': 0.0, 'max': 36, 'mean': 7.5}` |

## Tiers

### v2_min

- part_count: `20-25`
- goal: pass deformer/keyform/physics gate
- minimums: `{'parameters': 12, 'warp_deformers': 8, 'keyform_bindings': 20, 'physics_groups': 2}`
- usage: technical gate only; not final production target

### v2_standard

- part_count: `50-70`
- goal: natural eye/mouth/hair/body-angle motion
- minimums: `{'parameters': 25, 'warp_deformers': 35, 'rotation_deformers': 8, 'keyform_bindings': 120, 'physics_groups': 4}`
- usage: first production candidate default

### v2_rich

- part_count: `90+`
- goal: official-core-sample-like expression richness
- minimums: `{'parameters': 50, 'warp_deformers': 60, 'rotation_deformers': 20, 'keyform_bindings': 220, 'physics_groups': 8}`
- usage: at least two of mask/pose/expression when the design needs rich interactions

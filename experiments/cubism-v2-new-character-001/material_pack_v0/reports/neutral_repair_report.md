# Neutral Composite Repair

Status: `PASS_NEUTRAL_REPAIR_V1`

## Scores

- Before all visible: `0.448374`
- Before visibility only: `0.443789`
- After repair: `0.0`

## Top Problem Parts Before Repair

| Part | Score px | Bad owned | Extra owned | Missing in bbox |
|---|---:|---:|---:|---:|
| `hair_back_underpaint` | 204351 | 135357 | 67244 | 1750 |
| `body_underpaint` | 89095 | 45109 | 43455 | 531 |
| `chest_cloth_base` | 46279 | 35240 | 105 | 10934 |
| `torso_base` | 35878 | 1994 | 0 | 33884 |
| `arm_R_underpaint` | 35408 | 17790 | 17403 | 215 |
| `face_base` | 20877 | 20836 | 41 | 0 |
| `arm_L_upper_simple` | 16991 | 6138 | 16 | 10837 |
| `neck` | 15507 | 15479 | 28 | 0 |
| `hair_back_base` | 14608 | 111 | 0 | 14497 |
| `collar_front` | 9683 | 9454 | 229 | 0 |

## Outputs

- `neutral_composite_before.png`: `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-001/material_pack_v0/reports/neutral_repair/neutral_composite_before.png`
- `neutral_diff_overlay_before.png`: `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-001/material_pack_v0/reports/neutral_repair/neutral_diff_overlay_before.png`
- `neutral_composite_after.png`: `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-001/material_pack_v0/reports/neutral_repair/neutral_composite_after.png`
- `neutral_diff_overlay_after.png`: `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-001/material_pack_v0/reports/neutral_repair/neutral_diff_overlay_after.png`

## Meaning

This repair makes the separated material layers reconstruct the canonical neutral image before rigging.
It does not prove final ArtMesh, CMO3, or runtime export success.

# Cubism v2 Keypose PNG Validation

- status: `PASS_READY_FOR_VISUAL_QA`
- input_dir: `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/local_generated_keypose_v1/normalized_layers`
- required_size: `[2048, 2048]`
- required_mode: `RGBA`

## Summary

- total required: `19`
- found: `19`
- missing: `0`
- resize/normalize required: `0`
- alpha/mode repair required: `0`

## Asset Results

| asset_id | status | size | mode | alpha_bbox | resize decision | issues |
|---|---|---:|---|---|---|---|
| face_base_clean | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [608, 336, 1426, 1748] | `NO_RESIZE` | - |
| eye_L_clean_socket | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [794, 663, 1026, 765] | `NO_RESIZE` | - |
| eye_R_clean_socket | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [1046, 666, 1279, 769] | `NO_RESIZE` | - |
| eye_L_half_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [810, 680, 1010, 738] | `NO_RESIZE` | - |
| eye_R_half_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [1062, 684, 1263, 742] | `NO_RESIZE` | - |
| eye_L_mostly_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [810, 686, 1010, 732] | `NO_RESIZE` | - |
| eye_R_mostly_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [1062, 689, 1263, 735] | `NO_RESIZE` | - |
| eye_L_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [818, 687, 1002, 741] | `NO_RESIZE` | - |
| eye_R_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [1070, 690, 1255, 745] | `NO_RESIZE` | - |
| eye_L_closed_underpaint | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [794, 663, 1026, 765] | `NO_RESIZE` | - |
| eye_R_closed_underpaint | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [1046, 666, 1279, 769] | `NO_RESIZE` | - |
| mouth_base_clean | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [907, 773, 1157, 1129] | `NO_RESIZE` | - |
| mouth_closed_smile | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [965, 941, 1100, 976] | `NO_RESIZE` | - |
| mouth_small_open | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [988, 910, 1076, 1009] | `NO_RESIZE` | - |
| mouth_wide_open | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [966, 900, 1099, 1031] | `NO_RESIZE` | - |
| mouth_o_vowel | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [988, 878, 1076, 1031] | `NO_RESIZE` | - |
| mouth_inner | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [981, 837, 1084, 898] | `NO_RESIZE` | - |
| mouth_teeth | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [985, 857, 1070, 877] | `NO_RESIZE` | - |
| mouth_tongue | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [1002, 849, 1063, 882] | `NO_RESIZE` | - |

## Resize Rule

- 2048x2048 RGBA full-canvas aligned PNG: do not resize.
- Non-2048 output: do not stretch-resize directly; preserve aspect ratio and place into 2048x2048 transparent canvas using ROI/anchor evidence.
- RGB/full illustration output: alpha extraction is required before it can become a Cubism material layer.

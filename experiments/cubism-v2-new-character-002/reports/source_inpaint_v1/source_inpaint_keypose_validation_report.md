# Cubism v2 Keypose PNG Validation

- status: `PASS_READY_FOR_VISUAL_QA`
- input_dir: `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/material_pack_first_v1_source_inpaint/normalized_layers`
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
| face_base_clean | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [308, 26, 1740, 2048] | `NO_RESIZE` | - |
| eye_L_clean_socket | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [756, 563, 1015, 804] | `NO_RESIZE` | - |
| eye_R_clean_socket | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [1046, 563, 1305, 804] | `NO_RESIZE` | - |
| eye_L_half_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [764, 655, 967, 742] | `NO_RESIZE` | - |
| eye_R_half_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [1083, 680, 1287, 743] | `NO_RESIZE` | - |
| eye_L_mostly_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [766, 640, 975, 736] | `NO_RESIZE` | - |
| eye_R_mostly_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [1083, 692, 1286, 736] | `NO_RESIZE` | - |
| eye_L_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [761, 647, 986, 733] | `NO_RESIZE` | - |
| eye_R_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [1070, 643, 1290, 727] | `NO_RESIZE` | - |
| eye_L_closed_underpaint | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [756, 563, 1015, 804] | `NO_RESIZE` | - |
| eye_R_closed_underpaint | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [1046, 563, 1305, 804] | `NO_RESIZE` | - |
| mouth_base_clean | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [878, 735, 1169, 953] | `NO_RESIZE` | - |
| mouth_closed_smile | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [921, 785, 1149, 905] | `NO_RESIZE` | - |
| mouth_small_open | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [924, 785, 1147, 905] | `NO_RESIZE` | - |
| mouth_wide_open | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [915, 780, 1155, 909] | `NO_RESIZE` | - |
| mouth_o_vowel | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [924, 780, 1145, 910] | `NO_RESIZE` | - |
| mouth_inner | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [928, 791, 1143, 899] | `NO_RESIZE` | - |
| mouth_teeth | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [920, 812, 1150, 877] | `NO_RESIZE` | - |
| mouth_tongue | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [932, 788, 1137, 902] | `NO_RESIZE` | - |

## Resize Rule

- 2048x2048 RGBA full-canvas aligned PNG: do not resize.
- Non-2048 output: do not stretch-resize directly; preserve aspect ratio and place into 2048x2048 transparent canvas using ROI/anchor evidence.
- RGB/full illustration output: alpha extraction is required before it can become a Cubism material layer.

# Cubism v2 Keypose PNG Validation

- status: `PASS_READY_FOR_VISUAL_QA`
- input_dir: `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/model_edit_v4_strict_mouth/normalized_layers`
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
| face_base_clean | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [308, 19, 1740, 2048] | `NO_RESIZE` | - |
| eye_L_clean_socket | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [734, 602, 1026, 771] | `NO_RESIZE` | - |
| eye_R_clean_socket | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [1024, 603, 1316, 771] | `NO_RESIZE` | - |
| eye_L_half_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [764, 655, 967, 742] | `NO_RESIZE` | - |
| eye_R_half_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [1083, 680, 1287, 743] | `NO_RESIZE` | - |
| eye_L_mostly_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [766, 640, 975, 736] | `NO_RESIZE` | - |
| eye_R_mostly_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [1083, 692, 1286, 736] | `NO_RESIZE` | - |
| eye_L_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [761, 647, 986, 733] | `NO_RESIZE` | - |
| eye_R_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [1070, 643, 1290, 727] | `NO_RESIZE` | - |
| eye_L_closed_underpaint | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [734, 602, 1026, 771] | `NO_RESIZE` | - |
| eye_R_closed_underpaint | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [1024, 603, 1316, 771] | `NO_RESIZE` | - |
| mouth_base_clean | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [906, 765, 1164, 925] | `NO_RESIZE` | - |
| mouth_closed_smile | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [946, 794, 1143, 903] | `NO_RESIZE` | - |
| mouth_small_open | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [925, 787, 1139, 905] | `NO_RESIZE` | - |
| mouth_wide_open | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [936, 782, 1151, 903] | `NO_RESIZE` | - |
| mouth_o_vowel | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [928, 787, 1130, 910] | `NO_RESIZE` | - |
| mouth_inner | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [928, 791, 1143, 899] | `NO_RESIZE` | - |
| mouth_teeth | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [920, 812, 1150, 877] | `NO_RESIZE` | - |
| mouth_tongue | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [932, 788, 1137, 902] | `NO_RESIZE` | - |

## Resize Rule

- 2048x2048 RGBA full-canvas aligned PNG: do not resize.
- Non-2048 output: do not stretch-resize directly; preserve aspect ratio and place into 2048x2048 transparent canvas using ROI/anchor evidence.
- RGB/full illustration output: alpha extraction is required before it can become a Cubism material layer.

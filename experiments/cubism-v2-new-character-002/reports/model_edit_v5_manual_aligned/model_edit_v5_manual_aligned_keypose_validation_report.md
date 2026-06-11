# Cubism v2 Keypose PNG Validation

- status: `PASS_READY_FOR_VISUAL_QA`
- input_dir: `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/model_edit_v5_manual_aligned/normalized_layers`
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
| eye_L_clean_socket | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [766, 621, 994, 753] | `NO_RESIZE` | - |
| eye_R_clean_socket | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [1056, 621, 1284, 752] | `NO_RESIZE` | - |
| eye_L_half_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [790, 662, 948, 730] | `NO_RESIZE` | - |
| eye_R_half_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [1102, 682, 1261, 731] | `NO_RESIZE` | - |
| eye_L_mostly_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [791, 651, 954, 726] | `NO_RESIZE` | - |
| eye_R_mostly_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [1102, 691, 1260, 725] | `NO_RESIZE` | - |
| eye_L_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [787, 656, 963, 723] | `NO_RESIZE` | - |
| eye_R_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [1092, 653, 1264, 719] | `NO_RESIZE` | - |
| eye_L_closed_underpaint | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [766, 621, 994, 753] | `NO_RESIZE` | - |
| eye_R_closed_underpaint | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [1056, 621, 1284, 752] | `NO_RESIZE` | - |
| mouth_base_clean | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [918, 826, 1140, 964] | `NO_RESIZE` | - |
| mouth_closed_smile | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [952, 851, 1121, 945] | `NO_RESIZE` | - |
| mouth_small_open | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [934, 845, 1118, 946] | `NO_RESIZE` | - |
| mouth_wide_open | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [943, 841, 1128, 945] | `NO_RESIZE` | - |
| mouth_o_vowel | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [937, 845, 1111, 951] | `NO_RESIZE` | - |
| mouth_inner | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [937, 849, 1122, 942] | `NO_RESIZE` | - |
| mouth_teeth | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [930, 867, 1128, 923] | `NO_RESIZE` | - |
| mouth_tongue | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [940, 846, 1116, 944] | `NO_RESIZE` | - |

## Resize Rule

- 2048x2048 RGBA full-canvas aligned PNG: do not resize.
- Non-2048 output: do not stretch-resize directly; preserve aspect ratio and place into 2048x2048 transparent canvas using ROI/anchor evidence.
- RGB/full illustration output: alpha extraction is required before it can become a Cubism material layer.

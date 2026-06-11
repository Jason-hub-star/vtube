# Cubism v2 Keypose PNG Validation

- status: `REVISE`
- input_dir: `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-001/material_pack_v0/production_layers_face_detail_rebuild_v1`
- required_size: `[2048, 2048]`
- required_mode: `RGBA`

## Summary

- total required: `19`
- found: `5`
- missing: `14`
- resize/normalize required: `0`
- alpha/mode repair required: `0`

## Asset Results

| asset_id | status | size | mode | alpha_bbox | resize decision | issues |
|---|---|---:|---|---|---|---|
| face_base_clean | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| eye_L_clean_socket | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| eye_R_clean_socket | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| eye_L_half_closed_lid | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| eye_R_half_closed_lid | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| eye_L_mostly_closed_lid | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| eye_R_mostly_closed_lid | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| eye_L_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [818, 687, 1002, 741] | `NO_RESIZE` | - |
| eye_R_closed_lid | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [1070, 690, 1255, 745] | `NO_RESIZE` | - |
| eye_L_closed_underpaint | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| eye_R_closed_underpaint | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| mouth_base_clean | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| mouth_closed_smile | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| mouth_small_open | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| mouth_wide_open | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| mouth_o_vowel | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| mouth_inner | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [981, 837, 1084, 898] | `NO_RESIZE` | - |
| mouth_teeth | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [985, 857, 1070, 877] | `NO_RESIZE` | - |
| mouth_tongue | `PASS_READY_FOR_VISUAL_QA` | [2048, 2048] | RGBA | [1002, 849, 1063, 882] | `NO_RESIZE` | - |

## Resize Rule

- 2048x2048 RGBA full-canvas aligned PNG: do not resize.
- Non-2048 output: do not stretch-resize directly; preserve aspect ratio and place into 2048x2048 transparent canvas using ROI/anchor evidence.
- RGB/full illustration output: alpha extraction is required before it can become a Cubism material layer.

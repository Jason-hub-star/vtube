# Cubism v2 Keypose PNG Validation

- status: `REVISE`
- input_dir: `/Users/family/jason/Vtube/experiments/blink-apply-review-001/layers`
- required_size: `[2048, 2048]`
- required_mode: `RGBA`

## Summary

- total required: `19`
- found: `0`
- missing: `19`
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
| eye_L_closed_lid | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| eye_R_closed_lid | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| eye_L_closed_underpaint | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| eye_R_closed_underpaint | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| mouth_base_clean | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| mouth_closed_smile | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| mouth_small_open | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| mouth_wide_open | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| mouth_o_vowel | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| mouth_inner | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| mouth_teeth | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |
| mouth_tongue | `MISSING` | - | - | - | `NO_FILE` | required PNG not found |

## Resize Rule

- 2048x2048 RGBA full-canvas aligned PNG: do not resize.
- Non-2048 output: do not stretch-resize directly; preserve aspect ratio and place into 2048x2048 transparent canvas using ROI/anchor evidence.
- RGB/full illustration output: alpha extraction is required before it can become a Cubism material layer.

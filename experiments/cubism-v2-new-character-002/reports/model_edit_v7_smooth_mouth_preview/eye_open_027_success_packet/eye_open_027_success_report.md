# Character 002 EyeOpen 0.27 Success Packet

- Status: `PASS_MINI_CUBISM_EYE_OPEN_027_CAPTURED`
- Project: `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/model_edit_v7_smooth_mouth_preview/mini_cubism_diagnostic_project`
- Contact sheet: `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/model_edit_v7_smooth_mouth_preview/eye_open_027_success_packet/eye_open_027_contact_sheet.png`
- Generated at: `2026-06-09T04:11:47.432196+00:00`

## Decision

- `ParamEyeLOpen` / `ParamEyeROpen` around `0.27` is recorded as the current natural-close review threshold.
- `0.0` remains a technical full-close check, not the preferred natural expression target.
- This is Mini Cubism diagnostic/keypose evidence only, not real Cubism `.cmo3/.moc3` authoring success.

## Frames

| EyeOpen | Label | Active eye parts | Changed vs open | Screenshot |
|---:|---|---|---:|---|
| 1.00 | Open reference | `eye_L_open, eye_R_open` | 0.000000 | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/model_edit_v7_smooth_mouth_preview/eye_open_027_success_packet/frames/eyeopen_1_00_open.png` |
| 0.50 | Half keypose | `eye_L_half_closed_lid, eye_R_half_closed_lid` | 0.005739 | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/model_edit_v7_smooth_mouth_preview/eye_open_027_success_packet/frames/eyeopen_0_50_half.png` |
| 0.27 | Natural close threshold | `eye_L_half_closed_lid, eye_R_half_closed_lid` | 0.005730 | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/model_edit_v7_smooth_mouth_preview/eye_open_027_success_packet/frames/eyeopen_0_27_natural_close.png` |
| 0.00 | Technical full-close | `eye_L_closed_lid, eye_R_closed_lid, eye_L_closed_underpaint, eye_R_closed_underpaint` | 0.005844 | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/model_edit_v7_smooth_mouth_preview/eye_open_027_success_packet/frames/eyeopen_0_00_full_close.png` |

## Notes

- v7 active parameters are `ParamAngleX`, `ParamEyeLOpen`, `ParamEyeROpen`, `ParamMouthOpenY`, `ParamHairFront`.
- `ParamEyeBallX/Y` and `ParamMouthForm` are intentionally absent from the active v7 diagnostic preview.
- `ParamHairFront` remains contract-only until an independent front-hair part exists.

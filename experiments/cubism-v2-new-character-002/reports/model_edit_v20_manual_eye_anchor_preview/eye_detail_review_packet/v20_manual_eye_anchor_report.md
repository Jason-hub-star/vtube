# Character 002 v14 Eye Detail Review Packet

- Status: `PASS_TECHNICAL_EYE_DETAIL_PACKET_READY`
- Project: `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/model_edit_v20_manual_eye_anchor_preview/mini_cubism_diagnostic_project`
- Contact sheet: `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/model_edit_v20_manual_eye_anchor_preview/eye_detail_review_packet/v14_eye_detail_review_contact_sheet.png`
- Generated at: `2026-06-09T08:53:55.858186+00:00`

## Decision

- v14 preserves v13 diagnostic limits: `ParamEyeLOpen/ROpen` min `0.27`, `ParamMouthOpenY` max `0.85`.
- `ParamEyeBallX/Y` now move derived iris/pupil/highlight parts.
- This is still diagnostic layer-split evidence because the eye detail is derived from baked `eye_open` art.

## Frames

| Frame | EyeOpen | EyeBallX | EyeBallY | Changed vs center | Active eye parts | Screenshot |
|---|---:|---:|---:|---:|---|---|
| open / centered iris | 1.00 | 0.0 | 0.0 | 0.000000 | `eye_L_white, eye_L_iris, eye_R_white, eye_R_iris` | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/model_edit_v20_manual_eye_anchor_preview/eye_detail_review_packet/frames/open_center.png` |
| open / eyeball left | 1.00 | -1.0 | 0.0 | 0.002248 | `eye_L_white, eye_L_iris, eye_R_white, eye_R_iris` | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/model_edit_v20_manual_eye_anchor_preview/eye_detail_review_packet/frames/open_left.png` |
| open / eyeball right | 1.00 | 1.0 | 0.0 | 0.002261 | `eye_L_white, eye_L_iris, eye_R_white, eye_R_iris` | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/model_edit_v20_manual_eye_anchor_preview/eye_detail_review_packet/frames/open_right.png` |
| open / eyeball up | 1.00 | 0.0 | -1.0 | 0.001888 | `eye_L_white, eye_L_iris, eye_R_white, eye_R_iris` | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/model_edit_v20_manual_eye_anchor_preview/eye_detail_review_packet/frames/open_up.png` |
| open / eyeball down | 1.00 | 0.0 | 1.0 | 0.001818 | `eye_L_white, eye_L_iris, eye_R_white, eye_R_iris` | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/model_edit_v20_manual_eye_anchor_preview/eye_detail_review_packet/frames/open_down.png` |
| in-between 0.80 | 0.80 | 0.0 | 0.0 | 0.004053 | `eye_L_white, eye_L_iris, eye_L_lid_inbetween_080, eye_R_white, eye_R_iris, eye_R_lid_inbetween_080` | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/model_edit_v20_manual_eye_anchor_preview/eye_detail_review_packet/frames/eyeopen_080.png` |
| in-between 0.65 | 0.65 | 0.0 | 0.0 | 0.005121 | `eye_L_white, eye_L_iris, eye_L_lid_inbetween_080, eye_L_lid_inbetween_065, eye_L_half_closed_lid, eye_R_white, eye_R_iris, eye_R_lid_inbetween_080, eye_R_lid_inbetween_065, eye_R_half_closed_lid` | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/model_edit_v20_manual_eye_anchor_preview/eye_detail_review_packet/frames/eyeopen_065.png` |
| in-between 0.50 | 0.50 | 0.0 | 0.0 | 0.005498 | `eye_L_white, eye_L_iris, eye_L_lid_inbetween_065, eye_L_half_closed_lid, eye_L_mostly_closed_lid, eye_L_closed_lid, eye_R_white, eye_R_iris, eye_R_lid_inbetween_065, eye_R_half_closed_lid, eye_R_mostly_closed_lid, eye_R_closed_lid` | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/model_edit_v20_manual_eye_anchor_preview/eye_detail_review_packet/frames/eyeopen_050.png` |
| in-between 0.38 | 0.38 | 0.0 | 0.0 | 0.005857 | `eye_L_lid_inbetween_038, eye_L_half_closed_lid, eye_L_mostly_closed_lid, eye_L_closed_lid, eye_R_lid_inbetween_038, eye_R_half_closed_lid, eye_R_mostly_closed_lid, eye_R_closed_lid` | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/model_edit_v20_manual_eye_anchor_preview/eye_detail_review_packet/frames/eyeopen_038.png` |
| natural close 0.27 | 0.27 | 0.0 | 0.0 | 0.005857 | `eye_L_mostly_closed_lid, eye_L_closed_lid, eye_R_mostly_closed_lid, eye_R_closed_lid` | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/model_edit_v20_manual_eye_anchor_preview/eye_detail_review_packet/frames/eyeopen_027.png` |

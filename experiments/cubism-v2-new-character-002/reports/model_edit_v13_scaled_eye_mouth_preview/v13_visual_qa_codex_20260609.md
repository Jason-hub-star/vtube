# Character 002 v13 Visual QA

Date: 2026-06-09
Reviewer: Codex
Status: PASS_CURRENT_DIAGNOSTIC_CANDIDATE / PRODUCTION_VISUAL_REVIEW_STILL_REQUIRED

## Evidence

- Mini Cubism project: `model_edit_v13_scaled_eye_mouth_preview/mini_cubism_diagnostic_project`
- Scale report: `reports/model_edit_v13_scaled_eye_mouth_preview/mini_cubism_v13_scaled_eye_mouth_report.json`
- MouthOpenY packet: `reports/model_edit_v13_scaled_eye_mouth_preview/generated_mouth_open_packet/existing_mouth_open_contact_sheet.png`
- EyeOpen packet: `reports/model_edit_v13_scaled_eye_mouth_preview/eye_open_clamp_packet/eye_open_027_contact_sheet.png`

## Findings

- v13 scales the v12 eye parts by `0.94` and the active generated mouth parts by `0.92`.
- The result is visually better than v12 for the current diagnostic preview: the eyes still read clearly, while the mouth no longer feels as large at open states.
- `ParamEyeLOpen` and `ParamEyeROpen` remain clamped to min `0.27`.
- `ParamMouthOpenY` remains clamped to max `0.85`.
- Validator remains PASS with 21 parts, 21 meshes, 6 deformers, 5 parameters, and 7 keyform bindings.

## Decision

Use v13 as the current best Mini Cubism diagnostic candidate for Character 002. Keep v12 as the previous best unscaled baseline and keep v10/v11 as revision evidence.

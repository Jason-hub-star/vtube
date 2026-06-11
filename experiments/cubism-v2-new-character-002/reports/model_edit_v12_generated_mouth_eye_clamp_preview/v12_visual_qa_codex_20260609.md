# Character 002 v12 Visual QA

Date: 2026-06-09
Reviewer: Codex
Status: PASS_DIAGNOSTIC_CANDIDATE / PRODUCTION_VISUAL_REVIEW_STILL_REQUIRED

## Evidence

- Generated mouth sheet: `generated_mouth_v12/reports/generated_smile_mouth_contact_sheet.png`
- MouthOpenY packet: `reports/model_edit_v12_generated_mouth_eye_clamp_preview/generated_mouth_open_packet/existing_mouth_open_contact_sheet.png`
- Eye clamp packet: `reports/model_edit_v12_generated_mouth_eye_clamp_preview/eye_open_clamp_packet/eye_open_027_contact_sheet.png`
- Mini Cubism project: `model_edit_v12_generated_mouth_eye_clamp_preview/mini_cubism_diagnostic_project`

## Findings

- v12 is visually better than v10 and v11 for the active Mini Cubism diagnostic preview.
- The wide mouth is smaller and less shout-like than v10.
- `ParamMouthOpenY` is clamped to `0.85`; an input of `1.00` snapshots as `0.85`, preventing the most exaggerated full-open state.
- The closed, small, and mid mouth states keep the same smiling character read.
- Teeth are still simplified, but less disruptive than v10/v11 because the open mouth is smaller and the corners have more mouth-interior shadow.
- `ParamEyeLOpen` and `ParamEyeROpen` remain clamped to `0.27`; eye close visual QA remains PASS for this diagnostic.

## Decision

Use v12 as the current Character 002 Mini Cubism diagnostic candidate. This is not a final production mouth-art PASS for real Cubism authoring, but it is good enough to replace v10 for local diagnostic preview and continued motion/parameter testing.

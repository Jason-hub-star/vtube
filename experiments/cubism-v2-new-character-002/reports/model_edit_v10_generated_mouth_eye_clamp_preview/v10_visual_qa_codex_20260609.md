# Character 002 v10 Visual QA

Date: 2026-06-09
Reviewer: Codex
Status: REVISE_MOUTH / PASS_EYE_CLAMP

## Evidence

- Generated mouth sheet: `generated_mouth_v10/reports/generated_smile_mouth_contact_sheet.png`
- MouthOpenY packet: `reports/model_edit_v10_generated_mouth_eye_clamp_preview/generated_mouth_open_packet/existing_mouth_open_contact_sheet.png`
- Eye clamp packet: `reports/model_edit_v10_generated_mouth_eye_clamp_preview/eye_open_clamp_packet/eye_open_027_contact_sheet.png`

## Findings

- Eye clamp is working. In the v10 eye packet, an input of `EyeOpen 0.00` snapshots as `ParamEyeLOpen 0.27` and `ParamEyeROpen 0.27`, matching the accepted natural-close threshold.
- Eye visual state at `0.27` is acceptable for the current diagnostic. It reads as closed/natural enough and does not over-close into the previous hard full-close look.
- Mouth v10 is better than the previous existing-mouth-only packet. The closed, small, and mid states keep a smiling expression and no longer look like a tiny centered mouth.
- Mouth wide/full still needs revision. At `MouthOpenY 0.80-1.00`, the mouth reads too large for the face, and the teeth area is a flat white band rather than a naturally integrated upper teeth shape.
- Tongue is visible in the wide/full keypose, but the wide-open silhouette is still too graphic/patch-like for final acceptance.

## Decision

Keep v10 as the current generated-mouth diagnostic baseline, but do not promote mouth visual QA to final PASS. The next revision should reduce the wide-open mouth scale and improve teeth/tongue integration, or clamp the preview maximum below the full wide state until a better wide keypose is generated.

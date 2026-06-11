# Face Tracking to Cubism Parameter Map

## Summary

- status: `PASS`
- primary input provider: `MediaPipe Face Landmarker`
- actual webcam smoke: `False`
- required mappings: `11`
- optional mappings: `3`

## Reference Sources

- [MediaPipe Face Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker): webcam/video face landmarks, blendshape scores, and facial transformation matrices
- [Live2D Cubism standard parameter list](https://docs.live2d.com/ko/cubism-editor-manual/standard-parameter-list/): Cubism parameter IDs and standard output ranges
- [VTube Studio value-provider priority](https://github.com/DenchiSoft/VTubeStudio/wiki/Interaction-between-Animations%2C-Tracking%2C-Physics%2C-etc.): tracking/animation/expression/physics priority risk
- [nizima LIVE parameter settings](https://docs.live2d.com/nizimalive/en/manual/parameter/): webcam tracking, automatic blink, lip-sync, and motion-sync interaction notes

## Current Readiness

| Item | Value |
|---|---|
| tracking-friendly parameter floor | `True` |
| actual webcam tracking smoke | `False` |
| prompt mode | `single_master_png_first` |
| params without direct mapping | `none` |

## Mapping Table

| Input | Cubism Parameter | Output Range | Formula | Priority | QA |
|---|---|---|---|---|---|
| `head_yaw_from_facial_transformation_matrix` | `ParamAngleX` | `[-30, 30]` | `clamp(normalize_centered(head_yaw, -25, 25) * 30, -30, 30)` | `REQUIRED` | Turn face left/right; face, eyes, mouth, and front hair should follow without overhang. |
| `head_pitch_from_facial_transformation_matrix` | `ParamAngleY` | `[-30, 30]` | `clamp(normalize_centered(head_pitch, -20, 20) * 30, -30, 30)` | `REQUIRED` | Look up/down; chin, neck, mouth, and bangs should not tear or expose missing underpaint. |
| `head_roll_from_facial_transformation_matrix` | `ParamAngleZ` | `[-30, 30]` | `clamp(normalize_centered(head_roll, -25, 25) * 30, -30, 30)` | `REQUIRED` | Tilt head left/right; hair and neck should follow without draw-order inversion. |
| `eyeBlinkLeft` | `ParamEyeLOpen` | `[0, 1]` | `clamp(1 - eyeBlinkLeft, 0, 1)` | `REQUIRED` | Blink left eye; left eye should close fully and reopen without affecting the right eye. |
| `eyeBlinkRight` | `ParamEyeROpen` | `[0, 1]` | `clamp(1 - eyeBlinkRight, 0, 1)` | `REQUIRED` | Blink right eye; right eye should close fully and reopen without affecting the left eye. |
| `eye_gaze_x_from_landmarks_or_eyeLook blendshapes` | `ParamEyeBallX` | `[-1, 1]` | `clamp(eye_gaze_x, -1, 1)` | `REQUIRED` | Look left/right; both irises should move together and stay inside eye masks. |
| `eye_gaze_y_from_landmarks_or_eyeLook blendshapes` | `ParamEyeBallY` | `[-1, 1]` | `clamp(eye_gaze_y, -1, 1)` | `REQUIRED` | Look up/down; irises should stay clipped by eyelids and not float outside whites. |
| `jawOpen` | `ParamMouthOpenY` | `[0, 1]` | `clamp(remap_deadzone(jawOpen, 0.08, 0.85), 0, 1)` | `REQUIRED` | Open/close mouth; inner mouth should appear smoothly and close fully at rest. |
| `mouthSmileLeft/Right minus mouthFrownLeft/Right` | `ParamMouthForm` | `[-1, 1]` | `clamp(avg(mouthSmileLeft, mouthSmileRight) - avg(mouthFrownLeft, mouthFrownRight), -1, 1)` | `REQUIRED` | Smile/frown; mouth corners should move without breaking mouth-open keyforms. |
| `head_yaw_from_facial_transformation_matrix` | `ParamBodyAngleX` | `[-10, 10]` | `clamp(normalize_centered(head_yaw, -25, 25) * 10 * 0.65, -10, 10)` | `REQUIRED` | Turn head; body should follow subtly and never move more strongly than the head. |
| `head_pitch_from_facial_transformation_matrix` | `ParamBodyAngleY` | `[-10, 10]` | `clamp(normalize_centered(head_pitch, -20, 20) * 10 * 0.45, -10, 10)` | `REQUIRED` | Look up/down; torso should breathe/follow subtly without neck gap. |
| `head_roll_from_facial_transformation_matrix` | `ParamBodyAngleZ` | `[-10, 10]` | `clamp(normalize_centered(head_roll, -25, 25) * 10 * 0.5, -10, 10)` | `RECOMMENDED` | Tilt head; torso should tilt softly and preserve shoulder draw order. |
| `synthetic_breath_idle` | `ParamBreath` | `[0, 1]` | `0.5 + 0.5 * sin(time * breath_rate)` | `RECOMMENDED` | Idle for 10 seconds; breath should be visible but not distract from face tracking. |
| `audio_motionsync_or_vowel_classifier` | `ParamA/ParamI/ParamU/ParamE/ParamO` | `[0, 1]` | `optional; use only when v2_rich or motion-sync is enabled` | `OPTIONAL_V2_RICH` | Optional vowel test; not required for first v2_standard model. |

## Calibration Policy

- `neutral_capture_seconds`: 2
- `neutral_samples_min`: 45
- `centered_head_pose`: average yaw/pitch/roll during neutral capture becomes zero
- `blink`: measure open-eye baseline and closed-eye baseline; map tracking blink to Live2D open value with inversion
- `mouth`: apply closed-mouth deadzone to jawOpen before ParamMouthOpenY
- `body`: derive from head pose with damping; body must never overpower head motion

## Runtime Ownership Policy

- Tracking controls: `ParamAngleX`, `ParamAngleY`, `ParamAngleZ`, `ParamEyeLOpen`, `ParamEyeROpen`, `ParamEyeBallX`, `ParamEyeBallY`, `ParamMouthOpenY`, `ParamMouthForm`, `ParamBodyAngleX`, `ParamBodyAngleY`, `ParamBodyAngleZ`
- Physics controls: `ParamHairFront`, `ParamHairSide`, `ParamHairBack`, `secondary sway outputs`
- Idle controls: `ParamBreath`
- Risk: Face tracking, idle animation, expressions, and physics can compete for the same parameter in viewer apps. Keep ownership explicit.

## Pre-Character Generation Requirements

- Character prompt must keep both eyes, mouth, eyebrows, neck, shoulders, and simple arms visible.
- Do not hide mouth with hands, microphone, scarf, props, or bangs.
- Do not hide eyes with hair or accessories; blink tracking requires visible eyelids/lashes.
- Use standard Live2D parameter IDs so VTube Studio/nizima/other viewers can map tracking inputs predictably.
- Keep body motion simple; complex arm/hand tracking is deferred.

## Smoke Test Plan

| Test | Goal | Pass |
|---|---|---|
| `T0_static_sample_json` | Convert recorded/synthetic MediaPipe-like values into Cubism parameter values without webcam dependency. | All REQUIRED mappings produce finite values inside output ranges. |
| `T1_webcam_tracking_probe` | Use MediaPipe webcam/video to emit head pose, blink, gaze, jawOpen, and mouthForm proxy values. | At least 10 seconds of timestamped tracking frames are saved as JSON with no missing required channels. |
| `T2_reference_model_parameter_drive` | Drive a verified reference model before using a new character. | ParamAngleX/Y/Z, eye open, eye ball, mouth open/form visibly affect the model in screenshots/strip. |
| `T3_new_model_export_tracking_gate` | After Cubism authoring, prove the new model responds to tracking-derived values. | G3 motion strip includes head yaw/pitch/roll, blink L/R, eye gaze, mouth open, mouth form, and body damped follow. |

## Next Actions

- Create a MediaPipe webcam or recorded-video tracking smoke harness.
- Run T0 with synthetic values immediately after any mapping code is implemented.
- Run T1/T2 on a known-good official runtime model before generating production claims for the new character.
- Update the character prompt template only if G0 candidates hide eyes/mouth or make tracking-required parts ambiguous.

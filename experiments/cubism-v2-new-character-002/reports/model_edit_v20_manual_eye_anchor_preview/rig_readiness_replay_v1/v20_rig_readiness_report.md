# Character 002 v20 Rig Readiness

- Status: `READY_FOR_V21_SUPPORTED_CONTROL_RIG_SMOKE_WITH_HAIR_EXCLUDED`
- Project: `experiments/cubism-v2-new-character-002/model_edit_v20_manual_eye_anchor_preview/mini_cubism_diagnostic_project`
- Validator: `PASS`
- Pose sweep: `PASS` score `201`

## Supported Controls

| Parameter | Status | Targets | v21 action |
|---|---|---|---|
| `ParamAngleX` | `PARTIAL_DIAGNOSTIC` | `head_angle_warp` | include in v21 smoke, then validate through real Cubism deformer hierarchy later |
| `ParamEyeBallX` | `SUPPORTED_DIAGNOSTIC` | `eye_L_iris, eye_R_iris` | keep and tune movement strength only if 주인님 sees drift |
| `ParamEyeBallY` | `SUPPORTED_DIAGNOSTIC` | `eye_L_iris, eye_R_iris` | keep and tune movement strength only if 주인님 sees drift |
| `ParamEyeLOpen` | `SUPPORTED_DIAGNOSTIC_CLAMPED` | `eye_L_clean_socket, eye_L_closed_lid, eye_L_closed_underpaint, eye_L_half_closed_lid, eye_L_highlight, eye_L_iris, eye_L_lid_inbetween_038, eye_L_lid_inbetween_065, eye_L_lid_inbetween_080, eye_L_mostly_closed_lid, eye_L_open, eye_L_pupil, eye_L_warp, eye_L_white` | keep; use automation/canvas proof because UI pose sweep can under-report eye close |
| `ParamEyeROpen` | `SUPPORTED_DIAGNOSTIC_CLAMPED` | `eye_R_clean_socket, eye_R_closed_lid, eye_R_closed_underpaint, eye_R_half_closed_lid, eye_R_highlight, eye_R_iris, eye_R_lid_inbetween_038, eye_R_lid_inbetween_065, eye_R_lid_inbetween_080, eye_R_mostly_closed_lid, eye_R_open, eye_R_pupil, eye_R_warp, eye_R_white` | keep; use automation/canvas proof because UI pose sweep can under-report eye close |
| `ParamHairFront` | `UNSUPPORTED_CONTRACT_ONLY` | `front_hair_warp` | remove from active v21 smoke or create/separate real front hair parts first |
| `ParamMouthOpenY` | `SUPPORTED_DIAGNOSTIC_KEYPOSE` | `mouth_closed_smile, mouth_inner, mouth_mid_teeth_gen, mouth_small_open, mouth_teeth, mouth_tongue, mouth_warp, mouth_wide_teeth_tongue_gen` | keep for v21 smoke; production mouth still needs final visual acceptance |

## v21 Scope

Include:
- ParamAngleX local diagnostic motion
- ParamEyeBallX/Y generated iris detail motion
- ParamEyeLOpen/ROpen clamped keypose blink
- ParamMouthOpenY diagnostic mouth open

Exclude until assets exist:
- ParamHairFront

## Real Cubism Blockers

- ParamHairFront is contract-only because no independent front hair parts are present
- v20 has 36 diagnostic parts, below the confirmed v2_standard 64-part production target
- Mini Cubism diagnostic PASS does not prove real Cubism ArtMesh/Deformer/Keyform authoring
- mouth is still diagnostic keypose/crossfade and needs human visual acceptance before production mouth rigging

## Decision

Proceed to v21 Mini Cubism supported-control rig smoke, not final Cubism authoring, unless 주인님 first accepts v20 human visual QA.

# Cubism MVP Rig Smoke Checklist

Generated: 2026-06-04T08:55:55.410489+00:00
Status: READY_FOR_MANUAL_CUBISM_MVP_RIG
Source PSD: `experiments/imagen-live2d-001/import_ready.psd`

## FREE Limit Audit

| Item | Used | Limit | Result |
| --- | ---: | ---: | --- |
| `texture_files` | 1 | 1 | PASS |
| `texture_max_px` | 2048 | 2048 | PASS |
| `art_meshes_planned_one_per_layer` | 19 | 100 | PASS |
| `parameters_planned` | 8 | 30 | PASS |
| `deformers_planned` | 11 | 50 | PASS |
| `parts_folders_planned` | 6 | 30 | PASS |

## Parts Folder Setup

- `Hair`: `front_hair`, `back_hair`
- `Face`: `face_base`, `neck`
- `Eyes`: `L_eye_white`, `R_eye_white`, `L_iris`, `R_iris`, `L_upper_lash`, `R_upper_lash`, `L_brow`, `R_brow`
- `Mouth`: `mouth_line`
- `Body`: `clothes`, `L_arm`, `R_arm`
- `Accessory`: `choker`, `L_ear_outer`, `R_ear_outer`

## Deformer Plan

- `Root` (warp), parent `none`: none
- `Head_X` (warp), parent `Root`: `face_base`, `front_hair`, `back_hair`, `L_ear_outer`, `R_ear_outer`
- `Face_Base` (warp), parent `Head_X`: `face_base`, `neck`
- `Eye_L` (warp), parent `Head_X`: `L_eye_white`, `L_iris`, `L_upper_lash`
- `Eye_R` (warp), parent `Head_X`: `R_eye_white`, `R_iris`, `R_upper_lash`
- `Mouth` (warp), parent `Head_X`: `mouth_line`
- `Hair_Front` (rotation), parent `Head_X`: `front_hair`
- `Hair_Back` (warp), parent `Root`: `back_hair`
- `Body` (warp), parent `Root`: `clothes`, `choker`, `neck`
- `Arm_L` (rotation), parent `Body`: `L_arm`
- `Arm_R` (rotation), parent `Body`: `R_arm`

## MVP Parameter Keyforms

- `ParamAngleX` / 얼굴 좌우: range `[-30, 30]`, keyforms `[-30, 0, 30]`, targets `face_base`, `front_hair`, `back_hair`, `neck`, `clothes`. Head/face left-right drift only; keep deformation tiny because parts are forced-cleanup quality.
- `ParamEyeLOpen` / 왼쪽 눈 깜빡임: range `[0, 1]`, keyforms `[0, 1]`, targets `L_eye_white`, `L_iris`, `L_upper_lash`. Simple lash/white/iris squash or visibility test, not final eyelid art.
- `ParamEyeROpen` / 오른쪽 눈 깜빡임: range `[0, 1]`, keyforms `[0, 1]`, targets `R_eye_white`, `R_iris`, `R_upper_lash`. Simple lash/white/iris squash or visibility test, not final eyelid art.
- `ParamMouthOpenY` / 입 열림: range `[0, 1]`, keyforms `[0, 1]`, targets `mouth_line`. Tiny open/close vertical scale; current mouth_line is forced O and needs later ROI cleanup.
- `ParamHairFrontSwing` / 앞머리 흔들림: range `[-1, 1]`, keyforms `[-1, 0, 1]`, targets `front_hair`. Small horizontal/rotation sway; front_hair is forced canonical extraction.
- `ParamHairBackSwing` / 뒷머리 흔들림: range `[-1, 1]`, keyforms `[-1, 0, 1]`, targets `back_hair`. Small lower-hair sway only.
- `ParamArmLSwing` / 왼팔 흔들림: range `[-1, 1]`, keyforms `[-1, 0, 1]`, targets `L_arm`. Optional tiny sleeve/arm sway; this layer is forced from handwear-l.
- `ParamArmRSwing` / 오른팔 흔들림: range `[-1, 1]`, keyforms `[-1, 0, 1]`, targets `R_arm`. Optional tiny sleeve/arm sway; this layer is forced from handwear-r.

## Manual Cubism Steps

1. Open `import_ready.psd` in Cubism Editor FREE.
2. Confirm the Parts panel shows 19 individual layers, not one flattened image.
3. Create one simple ArtMesh per visible layer; do not exceed one mesh per layer for this smoke.
4. Create the deformer hierarchy above with small, conservative bounds.
5. Add only the MVP parameters listed above.
6. Keyform eyes, mouth, front/back hair, and optional arm swing with tiny movement.
7. Run visual validation: draw order, overhang, eye visibility, mouth shape, and forced front_hair/arm artifacts.
8. Save `cubism_mvp_rig.cmo3` in this experiment folder.
9. If Cubism FREE allows export and validation is not blocking, export a `.moc3` smoke under `moc3_export_smoke/`.

## Evidence To Capture

- Screenshot of Parts panel after ArtMesh creation.
- Screenshot of Deformer hierarchy.
- Screenshot of each MVP parameter at neutral and extreme keyforms.
- `reports/cubism_mvp_rig_validation.json` with PASS/REVISE/BLOCKED decisions.

## Caveat

This is a forced-O pipeline smoke. Passing this checklist proves the pipeline can reach a Cubism rigging surface, not that the avatar is production-quality.

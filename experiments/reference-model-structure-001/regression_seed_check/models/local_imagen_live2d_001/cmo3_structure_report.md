# CMO3 Structure Report

Generated: 2026-06-05T14:50:25.599Z

Status: **WARN**

Input:

- CMO3: `experiments/imagen-live2d-001/cubism_mvp_rig.cmo3`
- Size: 6599184 bytes
- SHA256: `9574f12eb3c099d39727043e4124409ec1a51e4e5da6b759dd39da6af1f49e3f`

## Checks

| Check | Status | Message |
|---|---:|---|
| main_xml_extracted | PASS | main.xml was extracted from the CAFF archive. |
| artmesh_present | PASS | 19 CArtMeshSource definition(s) found. |
| part_sources_present | PASS | 1 CPartSource definition(s) found. |
| parameters_present | PASS | 27 CParameterSource definition(s) found. |
| required_parameters_present | PASS | 16 configured parameter check(s) passed. |
| warp_deformers_present | WARN | 0 CWarpDeformerSource definition(s) found. |
| rotation_deformers_present | WARN | 0 CRotationDeformerSource definition(s) found. |
| keyform_bindings_present | WARN | 0 KeyformBindingSource definition(s) found. |

## Structure Counts

| XML Source | Definitions | References |
|---|---:|---:|
| CArtMeshSource | 19 | 95 |
| CPartSource | 1 | 3 |
| CWarpDeformerSource | 0 | 0 |
| CRotationDeformerSource | 0 | 0 |
| KeyformGridSource | 20 | 0 |
| KeyformBindingSource | 0 | 0 |
| CParameterSource | 27 | 0 |
| CPhysicsSettingsSource | 0 | 0 |
| CGlueSource | 0 | 0 |
| CClippingMaskSource | 0 | 0 |
| CClippingMaskGuid | 0 | 0 |
| CInvertedMaskSource | 0 | 0 |
| CLayer | 19 | 57 |
| CLayerGroup | 1 | 21 |
| CLayeredImage | 1 | 22 |
| CImageResource | 19 | 95 |
| GEditableMesh2 | 19 | 0 |

## Parameters

- `ParamAngleX`
- `ParamAngleY`
- `ParamAngleZ`
- `ParamEyeLOpen`
- `ParamEyeLSmile`
- `ParamEyeROpen`
- `ParamEyeRSmile`
- `ParamEyeBallX`
- `ParamEyeBallY`
- `ParamBrowLY`
- `ParamBrowRY`
- `ParamBrowLX`
- `ParamBrowRX`
- `ParamBrowLAngle`
- `ParamBrowRAngle`
- `ParamBrowLForm`
- `ParamBrowRForm`
- `ParamMouthForm`
- `ParamMouthOpenY`
- `ParamCheek`
- `ParamBodyAngleX`
- `ParamBodyAngleY`
- `ParamBodyAngleZ`
- `ParamBreath`
- `ParamHairFront`
- `ParamHairSide`
- `ParamHairBack`

## Parts

- `Root Part`

## ArtMeshes

- `front_hair`
- `L_brow`
- `R_brow`
- `L_upper_lash`
- `R_upper_lash`
- `L_iris`
- `R_iris`
- `L_eye_white`
- `R_eye_white`
- `mouth_line`
- `face_base`
- `L_ear_outer`
- `R_ear_outer`
- `choker`
- `L_arm`
- `R_arm`
- `clothes`
- `neck`
- `back_hair`

## Warp Deformers

- none

## Rotation Deformers

- none

## Interpretation

- This proves CMO3 structure presence, not final visual rig quality.
- It does not replace runtime render checks for keyform motion, draw order under motion, or overhang.
- Part and layer names are extracted dynamically from this CMO3; they are not image-specific hardcoded expectations.

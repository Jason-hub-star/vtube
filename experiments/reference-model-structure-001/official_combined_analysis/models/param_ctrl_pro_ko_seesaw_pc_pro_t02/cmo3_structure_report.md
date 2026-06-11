# CMO3 Structure Report

Generated: 2026-06-08T01:24:15.002Z

Status: **WARN**

Input:

- CMO3: `experiments/reference-model-structure-001/official_samples/extracted/param_ctrl_pro_ko/param_ctrl_pro_ko/koharu_haruto_pc_pro/seesaw_pc_pro_t02.cmo3`
- Size: 127482 bytes
- SHA256: `accc0203db6468d0e075f72f722a9f21a97c9c63048eade332665841f09cde89`

## Checks

| Check | Status | Message |
|---|---:|---|
| main_xml_extracted | PASS | main.xml was extracted from the CAFF archive. |
| artmesh_present | PASS | 3 CArtMeshSource definition(s) found. |
| part_sources_present | PASS | 1 CPartSource definition(s) found. |
| parameters_present | PASS | 1 CParameterSource definition(s) found. |
| required_parameters_present | WARN | Missing configured parameter(s): ParamAngleX, ParamAngleY, ParamAngleZ, ParamEyeLOpen, ParamEyeROpen, ParamEyeBallX, ParamEyeBallY, ParamMouthForm, ParamMouthOpenY, ParamBodyAngleX, ParamBodyAngleY, ParamBodyAngleZ, ParamBreath, ParamHairFront, ParamHairSide, ParamHairBack |
| warp_deformers_present | WARN | 0 CWarpDeformerSource definition(s) found. |
| rotation_deformers_present | PASS | 1 CRotationDeformerSource definition(s) found. |
| keyform_bindings_present | PASS | 2 KeyformBindingSource definition(s) found. |

## Structure Counts

| XML Source | Definitions | References |
|---|---:|---:|
| CArtMeshSource | 3 | 17 |
| CPartSource | 1 | 3 |
| CWarpDeformerSource | 0 | 0 |
| CRotationDeformerSource | 1 | 4 |
| KeyformGridSource | 5 | 4 |
| KeyformBindingSource | 2 | 8 |
| CParameterSource | 1 | 0 |
| CPhysicsSettingsSource | 0 | 0 |
| CGlueSource | 0 | 0 |
| CClippingMaskSource | 0 | 0 |
| CClippingMaskGuid | 0 | 0 |
| CInvertedMaskSource | 0 | 0 |
| CLayer | 3 | 9 |
| CLayerGroup | 1 | 5 |
| CLayeredImage | 1 | 6 |
| CImageResource | 4 | 16 |
| GEditableMesh2 | 3 | 0 |

## Parameters

- `ParamAngle`

## Parts

- `Root Part`

## ArtMeshes

- `시소의 그림자`
- `시소 보드`
- `시소의 다리`

## Warp Deformers

- none

## Rotation Deformers

- `회전`

## Interpretation

- This proves CMO3 structure presence, not final visual rig quality.
- It does not replace runtime render checks for keyform motion, draw order under motion, or overhang.
- Part and layer names are extracted dynamically from this CMO3; they are not image-specific hardcoded expectations.

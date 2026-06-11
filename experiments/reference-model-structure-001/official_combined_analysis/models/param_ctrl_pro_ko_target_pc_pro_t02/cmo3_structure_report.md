# CMO3 Structure Report

Generated: 2026-06-08T01:24:16.116Z

Status: **WARN**

Input:

- CMO3: `experiments/reference-model-structure-001/official_samples/extracted/param_ctrl_pro_ko/param_ctrl_pro_ko/rice_pc_pro/target_pc_pro_t02.cmo3`
- Size: 28235 bytes
- SHA256: `6a9d1de03c354ebece714eb44f12a6472c2f746de80cc5f4c5b3d19cb28eb9a7`

## Checks

| Check | Status | Message |
|---|---:|---|
| main_xml_extracted | PASS | main.xml was extracted from the CAFF archive. |
| artmesh_present | PASS | 1 CArtMeshSource definition(s) found. |
| part_sources_present | PASS | 1 CPartSource definition(s) found. |
| parameters_present | PASS | 27 CParameterSource definition(s) found. |
| required_parameters_present | PASS | 16 configured parameter check(s) passed. |
| warp_deformers_present | WARN | 0 CWarpDeformerSource definition(s) found. |
| rotation_deformers_present | WARN | 0 CRotationDeformerSource definition(s) found. |
| keyform_bindings_present | WARN | 0 KeyformBindingSource definition(s) found. |

## Structure Counts

| XML Source | Definitions | References |
|---|---:|---:|
| CArtMeshSource | 1 | 5 |
| CPartSource | 1 | 3 |
| CWarpDeformerSource | 0 | 0 |
| CRotationDeformerSource | 0 | 0 |
| KeyformGridSource | 2 | 0 |
| KeyformBindingSource | 0 | 0 |
| CParameterSource | 27 | 0 |
| CPhysicsSettingsSource | 0 | 0 |
| CGlueSource | 0 | 0 |
| CClippingMaskSource | 0 | 0 |
| CClippingMaskGuid | 0 | 0 |
| CInvertedMaskSource | 0 | 0 |
| CLayer | 1 | 3 |
| CLayerGroup | 1 | 3 |
| CLayeredImage | 1 | 4 |
| CImageResource | 1 | 5 |
| GEditableMesh2 | 1 | 0 |

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

- `target`

## Warp Deformers

- none

## Rotation Deformers

- none

## Interpretation

- This proves CMO3 structure presence, not final visual rig quality.
- It does not replace runtime render checks for keyform motion, draw order under motion, or overhang.
- Part and layer names are extracted dynamically from this CMO3; they are not image-specific hardcoded expectations.

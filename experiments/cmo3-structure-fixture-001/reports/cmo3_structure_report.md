# CMO3 Structure Report

Generated: 2026-06-04T10:22:46.080Z

Status: **PASS**

Input:

- CMO3: `experiments/cmo3-structure-fixture-001/rigged_positive_fixture.cmo3`
- Size: 48819 bytes
- SHA256: `9440cab64abc0e549a517c991d8623d7582ba58120435e22110be1f36d124299`

## Checks

| Check | Status | Message |
|---|---:|---|
| main_xml_extracted | PASS | main.xml was extracted from the CAFF archive. |
| artmesh_present | PASS | 7 CArtMeshSource definition(s) found. |
| part_sources_present | PASS | 1 CPartSource definition(s) found. |
| parameters_present | PASS | 23 CParameterSource definition(s) found. |
| required_parameters_present | PASS | 16 configured parameter check(s) passed. |
| warp_deformers_present | PASS | 13 CWarpDeformerSource definition(s) found. |
| rotation_deformers_present | PASS | 1 CRotationDeformerSource definition(s) found. |
| keyform_bindings_present | PASS | 23 KeyformBindingSource definition(s) found. |

## Structure Counts

| XML Source | Definitions | References |
|---|---:|---:|
| CArtMeshSource | 7 | 37 |
| CPartSource | 1 | 3 |
| CWarpDeformerSource | 13 | 58 |
| CRotationDeformerSource | 1 | 4 |
| KeyformGridSource | 22 | 45 |
| KeyformBindingSource | 23 | 98 |
| CParameterSource | 23 | 0 |
| CPhysicsSettingsSource | 5 | 0 |
| CGlueSource | 0 | 0 |
| CLayer | 7 | 21 |
| CLayerGroup | 1 | 9 |
| CLayeredImage | 1 | 10 |
| CImageResource | 7 | 35 |
| GEditableMesh2 | 7 | 0 |

## Parameters

- `ParamOpacity`
- `ParamAngleX`
- `ParamAngleY`
- `ParamAngleZ`
- `ParamBodyAngleX`
- `ParamBodyAngleY`
- `ParamBodyAngleZ`
- `ParamBreath`
- `ParamEyeLOpen`
- `ParamEyeROpen`
- `ParamEyeBallX`
- `ParamEyeBallY`
- `ParamBrowLY`
- `ParamBrowRY`
- `ParamMouthForm`
- `ParamMouthOpenY`
- `ParamHairFront`
- `ParamHairSide`
- `ParamHairBack`
- `ParamSkirt`
- `ParamShirt`
- `ParamPants`
- `ParamBust`

## Parts

- `Root Part`

## ArtMeshes

- `Face`
- `FrontHair`
- `BackHair`
- `Mouth`
- `Neck`
- `Topwear`
- `Bottomwear`

## Warp Deformers

- `Face Warp`
- `FrontHair Warp`
- `BackHair Warp`
- `Mouth Warp`
- `Neck Warp`
- `Topwear Warp`
- `Bottomwear Warp`
- `Body Warp Z`
- `Body Warp Y`
- `Breath`
- `Body X Warp`
- `Neck Warp`
- `FaceParallax`

## Rotation Deformers

- `Face Rotation`

## Interpretation

- This proves CMO3 structure presence, not final visual rig quality.
- It does not replace runtime render checks for keyform motion, draw order under motion, or overhang.
- Part and layer names are extracted dynamically from this CMO3; they are not image-specific hardcoded expectations.

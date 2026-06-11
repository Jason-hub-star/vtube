# CMO3 Structure Report

Generated: 2026-06-05T14:48:31.631Z

Status: **WARN**

Input:

- CMO3: `experiments/reference-model-structure-001/official_samples/extracted/mark_movie_pro_ko/mark_movie_pro_ko/mark_movie_pro_t02.cmo3`
- Size: 1543352 bytes
- SHA256: `e25b84b82bdf38d5b56a701328b1ed06a41af9673ee4615c128aead77f15910f`

## Checks

| Check | Status | Message |
|---|---:|---|
| main_xml_extracted | PASS | main.xml was extracted from the CAFF archive. |
| artmesh_present | PASS | 33 CArtMeshSource definition(s) found. |
| part_sources_present | PASS | 22 CPartSource definition(s) found. |
| parameters_present | PASS | 27 CParameterSource definition(s) found. |
| required_parameters_present | WARN | Missing configured parameter(s): ParamMouthForm |
| warp_deformers_present | PASS | 26 CWarpDeformerSource definition(s) found. |
| rotation_deformers_present | PASS | 13 CRotationDeformerSource definition(s) found. |
| keyform_bindings_present | PASS | 90 KeyformBindingSource definition(s) found. |

## Structure Counts

| XML Source | Definitions | References |
|---|---:|---:|
| CArtMeshSource | 33 | 870 |
| CPartSource | 22 | 45 |
| CWarpDeformerSource | 26 | 213 |
| CRotationDeformerSource | 13 | 52 |
| KeyformGridSource | 114 | 161 |
| KeyformBindingSource | 90 | 635 |
| CParameterSource | 27 | 0 |
| CPhysicsSettingsSource | 1 | 0 |
| CGlueSource | 0 | 0 |
| CClippingMaskSource | 0 | 0 |
| CClippingMaskGuid | 0 | 0 |
| CInvertedMaskSource | 0 | 0 |
| CLayer | 37 | 109 |
| CLayerGroup | 28 | 120 |
| CLayeredImage | 3 | 71 |
| CImageResource | 39 | 190 |
| GEditableMesh2 | 35 | 0 |

## Parameters

- `ParamAngleX`
- `ParamAngleY`
- `ParamAngleZ`
- `ParamEyeLOpen`
- `ParamEyeROpen`
- `ParamEyeBallX`
- `ParamEyeBallY`
- `ParamBrowLY`
- `ParamBrowRY`
- `ParamMouthOpenY`
- `ParamBodyAngleX`
- `ParamBreath`
- `ParamHairFront`
- `ParamHairSide`
- `ParamHairBack`
- `ParamArmR`
- `ParamArmL`
- `ParamRightLeg`
- `ParamLeftLeg`
- `ParamBodyAngleZ`
- `ParamBodyAngleY`
- `ParamPositionX`
- `ParamPositionY`
- `ParamBodyTransform`
- `ParamGrass`
- `ParamLine1`
- `ParamLine2`

## Parts

- `Root Part`
- `왼쪽 눈알`
- `왼쪽 눈 흰자`
- `오른쪽 눈알`
- `왼쪽 눈 흰자`
- `입 안`
- `앞머리`
- `왼쪽 눈`
- `오른쪽 눈`
- `옆머리`
- `입`
- `얼굴`
- `머리`
- `몸`
- `왼팔`
- `오른팔`
- `뒷머리`
- `코어`
- `오른쪽 눈썹`
- `왼쪽 눈썹`
- `떨림선`
- `풀`

## ArtMeshes

- `앞머리`
- `좌상 눈꺼풀`
- `왼쪽 눈 라인`
- `왼쪽 눈 동공`
- `오른쪽 눈꺼풀`
- `오른쪽 아래 눈꺼풀`
- `오른쪽 눈 라인`
- `오른쪽 눈 동공`
- `왼쪽 눈 흰자`
- `오른쪽 옆머리`
- `윗 입술`
- `앞니`
- `혀`
- `입 안`
- `몸통`
- `왼쪽 다리`
- `오른쪽 다리`
- `왼팔`
- `오른팔`
- `왼쪽 뒷머리`
- `오른쪽 귀`
- `윤곽`
- `왼쪽 귀`
- `왼쪽 옆머리`
- `왼쪽 눈 흰자`
- `잔머리`
- `아랫 입술`
- `왼쪽 아래 눈꺼풀`
- `바지`
- `오른쪽 구두`
- `왼쪽 구두`
- `오른쪽 눈썹`
- `왼쪽 눈썹`

## Warp Deformers

- `뒷머리 곡면 머리 흔들림`
- `입의 곡면`
- `동체의 곡면`
- `왼쪽 눈의 곡면`
- `오른쪽 눈의 곡면`
- `뒷머리 곡면 XY`
- `앞머리 곡면 머리 흔들림`
- `앞머리 곡면 XY`
- `얼굴의 곡면`
- `옆머리 곡면 머리 흔들림`
- `앞머리 곡면 Z`
- `잔머리 곡면 머리 흔들림`
- `잔머리 곡면 XY`
- `뒷머리 곡면 Z`
- `옆머리 곡면 Z`
- `옆머리 곡면 XY`
- `호흡`
- `몸의 곡면 Z`
- `몸의 곡면 Y`
- `두부의 변형`
- `동체의 변형`
- `왼쪽 눈썹의 곡면`
- `오른쪽 눈썹의 곡면`
- `바지의 곡면`
- `왼팔의 곡면`
- `오른팔의 곡면`

## Rotation Deformers

- `얼굴의 회전`
- `오른팔의 위치`
- `오른팔의 회전`
- `오른발의 회전`
- `왼팔의 회전`
- `왼팔의 위치`
- `왼발의 회전`
- `왼쪽 다리의 위치`
- `오른쪽 다리의 위치`
- `전체위치 XY`
- `눈꼬리선 위치 조정`
- `몸의 떨림선 위치 조정`
- `풀의 위치 조정`

## Interpretation

- This proves CMO3 structure presence, not final visual rig quality.
- It does not replace runtime render checks for keyform motion, draw order under motion, or overhang.
- Part and layer names are extracted dynamically from this CMO3; they are not image-specific hardcoded expectations.

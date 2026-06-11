# CMO3 Structure Report

Generated: 2026-06-06T15:09:46.637Z

Status: **WARN**

Input:

- CMO3: `experiments/reference-model-structure-001/official_samples/extracted/hiyori_pro_ko/hiyori_pro_ko/hiyori_pro_t11.cmo3`
- Size: 28878721 bytes
- SHA256: `1a8743015eeb56f6efa7e1ce0b78e05903452344b5151a6ef67a1ad80271b92c`

## Checks

| Check | Status | Message |
|---|---:|---|
| main_xml_extracted | PASS | main.xml was extracted from the CAFF archive. |
| artmesh_present | PASS | 140 CArtMeshSource definition(s) found. |
| part_sources_present | PASS | 27 CPartSource definition(s) found. |
| parameters_present | PASS | 70 CParameterSource definition(s) found. |
| required_parameters_present | WARN | Missing configured parameter(s): ParamHairSide |
| warp_deformers_present | PASS | 50 CWarpDeformerSource definition(s) found. |
| rotation_deformers_present | PASS | 54 CRotationDeformerSource definition(s) found. |
| keyform_bindings_present | PASS | 346 KeyformBindingSource definition(s) found. |

## Structure Counts

| XML Source | Definitions | References |
|---|---:|---:|
| CArtMeshSource | 140 | 2308 |
| CPartSource | 27 | 55 |
| CWarpDeformerSource | 50 | 421 |
| CRotationDeformerSource | 54 | 209 |
| KeyformGridSource | 297 | 570 |
| KeyformBindingSource | 346 | 4304 |
| CParameterSource | 70 | 0 |
| CPhysicsSettingsSource | 11 | 0 |
| CGlueSource | 26 | 52 |
| CClippingMaskSource | 0 | 0 |
| CClippingMaskGuid | 0 | 0 |
| CInvertedMaskSource | 0 | 0 |
| CLayer | 107 | 320 |
| CLayerGroup | 19 | 162 |
| CLayeredImage | 2 | 130 |
| CImageResource | 114 | 442 |
| GEditableMesh2 | 140 | 0 |

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
- `ParamArmLA`
- `ParamArmRA`
- `ParamArmLB`
- `ParamArmRB`
- `ParamHandLB`
- `ParamHandRB`
- `ParamHandL`
- `ParamHandR`
- `ParamShoulder`
- `ParamBustY`
- `ParamHairAhoge`
- `ParamLeg`
- `ParamHairFront`
- `ParamHairBack`
- `ParamSideupRibbon`
- `ParamRibbon`
- `ParamSkirt`
- `ParamSkirt2`
- `Param_Angle_Rotation_1_ArtMesh61`
- `Param_Angle_Rotation_2_ArtMesh61`
- `Param_Angle_Rotation_3_ArtMesh61`
- `Param_Angle_Rotation_4_ArtMesh61`
- `Param_Angle_Rotation_5_ArtMesh61`
- `Param_Angle_Rotation_6_ArtMesh61`
- `Param_Angle_Rotation_7_ArtMesh61`
- `Param_Angle_Rotation_1_ArtMesh62`
- `Param_Angle_Rotation_2_ArtMesh62`
- `Param_Angle_Rotation_3_ArtMesh62`
- `Param_Angle_Rotation_4_ArtMesh62`
- `Param_Angle_Rotation_5_ArtMesh62`
- `Param_Angle_Rotation_6_ArtMesh62`
- `Param_Angle_Rotation_7_ArtMesh62`
- `Param_Angle_Rotation_1_ArtMesh54`
- `Param_Angle_Rotation_2_ArtMesh54`
- `Param_Angle_Rotation_3_ArtMesh54`
- `Param_Angle_Rotation_4_ArtMesh54`
- `Param_Angle_Rotation_5_ArtMesh54`
- `Param_Angle_Rotation_6_ArtMesh54`
- `Param_Angle_Rotation_7_ArtMesh54`
- `Param_Angle_Rotation_1_ArtMesh55`
- `Param_Angle_Rotation_2_ArtMesh55`
- `Param_Angle_Rotation_3_ArtMesh55`
- `Param_Angle_Rotation_4_ArtMesh55`
- `Param_Angle_Rotation_5_ArtMesh55`
- `Param_Angle_Rotation_6_ArtMesh55`
- `Param_Angle_Rotation_7_ArtMesh55`

## Parts

- `Root Part`
- `[밑그림]`
- `코어`
- `뺨`
- `눈`
- `입`
- `귀`
- `옆머리`
- `뒷머리`
- `목`
- `팔A`
- `팔 B`
- `몸`
- `배경`
- `안구`
- `눈썹`
- `코`
- `얼굴`
- `앞머리`
- `사이드업 오른쪽 (회전)`
- `사이드업 오른쪽(스키닝)`
- `사이드 업 왼쪽(회전)`
- `사이드 업 왼쪽(스키닝)`
- `앞머리 오른쪽(회전)`
- `앞머리 오른쪽(스키닝)`
- `앞머리 왼쪽(회전)`
- `왼쪽 앞머리(스키닝)`

## ArtMeshes

- `가슴리본1`
- `가슴리본2`
- `가슴리본3`
- `옷깃`
- `쇄골`
- `옷깃 뒤`
- `몸통`
- `치마`
- `오른쪽 허벅지`
- `오른쪽 종아리`
- `왼쪽 허벅지`
- `왼쪽 종아리`
- `왼쪽 발`
- `오른쪽 발`
- `오른쪽 어깨 B`
- `오른쪽 손 앞면 B`
- `오른쪽 소매 B`
- `오른쪽 어깨 뒷면 B`
- `왼쪽 손 앞면 B`
- `왼쪽 소매 B`
- `왼쪽 손 뒷면 B`
- `왼쪽 엄지 B`
- `왼팔 윗면B`
- `오른쪽 앞 A`
- `오른쪽 팔 뒤 A`
- `오른쪽 팔 위 A`
- `오른쪽 엄지 A`
- `오른쪽 손 뒷면 A`
- `왼쪽 위 어깨 A`
- `왼쪽 손 앞면 A`
- `왼쪽 앞 어깨 A`
- `왼손 엄지 A`
- `왼쪽 뒷면 A`
- `목`
- `잔머리`
- `뒷 머리`
- `오른쪽 뻗친머리`
- `왼쪽 뻗친머리`
- `앞머리`
- `오른쪽 귀`
- `왼쪽 귀`
- `코`
- `화난 입2`
- `입술 하이라이트`
- `입술`
- `윗쪽 입술`
- `아랫쪽 입술`
- `입 안`
- `왼쪽 눈썹`
- `오른쪽 눈썹`
- `왼쪽 하이라이트1`
- `왼쪽 하이라이트2`
- `왼쪽 하이라이트 그림자`
- `왼쪽 눈동자`
- `오른쪽 하이라이트1`
- `오른쪽 하이라이트2`
- `오른쪽 하이라이트 그림자`
- `오른쪽 눈동자`
- `오른쪽 웃는 얼굴 보조개`
- `왼쪽 웃는 얼굴 보조개`
- `오른쪽 웃는 눈2`
- `오른쪽 웃는 눈`
- `오른쪽 속눈썹1`
- `오른쪽 속눈썹2`
- `오른쪽 속눈썹 3`
- `오른쪽 속눈썹4`
- `오른쪽 속눈썹 5`
- `오른쪽 속눈썹 6`
- `오른쪽 속눈썹 7`
- `쌍커플 R`
- `왼쪽 속눈썹 1`
- `왼쪽 속눈썹2`
- `왼쪽 속눈썹 3`
- `왼쪽 속눈썹4`
- `왼쪽 속눈썹 5`
- `왼쪽 속눈썹 6`
- `쌍커플 L`
- `왼쪽 흰자`
- `오른쪽 흰자`
- `왼쪽 웃음기 3`
- `왼쪽 웃는 눈 2`
- `오른쪽 속눈썹 그림자`
- `오른쪽 뺨의 하이라이트`
- `왼쪽 뺨의 하이라이트`
- `오른쪽 뺨의 선`
- `왼쪽 뺨의 선`
- `오른쪽 홍조`
- `왼쪽 홍조`
- `오른쪽 홍조`
- `왼쪽 홍조`
- `머리카락 그림자`
- `윤곽`
- `왼쪽 웃음기 1`
- `오른쪽 어깨 A`
- `왼쪽 어깨 A`
- `오른쪽 윗 어깨 B`
- `왼팔 뒷면 B`
- `오른쪽 손 뒷면 B`
- `왼쪽 어깨 B`
- `배경`
- `왼쪽 속눈썹 그림자`
- `오른쪽 엄지 B`
- `참고 밑그림`
- `사이드 업 오른쪽`
- `사이드 업 왼쪽`
- `머리리본 오른쪽1`
- `머리리본 오른쪽2`
- `머리리본 왼쪽1`
- `머리리본 왼쪽2`
- `왼쪽 앞머리`
- `앞머리 오른쪽`
- `사이드 업 오른쪽[0]`
- `사이드 업 오른쪽[1]`
- `사이드 업 오른쪽[2]`
- `사이드 업 오른쪽[3]`
- `사이드 업 오른쪽[4]`
- `사이드 업 오른쪽[5]`
- `사이드 업 오른쪽[6]`
- `사이드 업 왼쪽[0]`
- `사이드 업 왼쪽[1]`
- `사이드업 왼쪽[2]`
- `사이드 업 왼쪽[3]`
- `사이드업 왼쪽[4]`
- `사이드 업 왼쪽[5]`
- `사이드 업 왼쪽[6]`
- `앞머리 오른쪽[0]`
- `앞머리 오른쪽[1]`
- `앞머리 오른쪽[2]`
- `앞머리 오른쪽[3]`
- `앞머리 오른쪽[4]`
- `앞머리 오른쪽[5]`
- `앞머리 오른쪽[6]`
- `왼쪽 앞머리[0]`
- `왼쪽 앞머리[1]`
- `왼쪽 앞머리[2]`
- `왼쪽 앞머리[3]`
- `왼쪽 앞머리[4]`
- `앞머리 왼쪽[5]`
- `앞머리 왼쪽[6]`
- `평판용 이미지`

## Warp Deformers

- `스커트의 곡면`
- `리본의 곡면`
- `몸의 곡면 X`
- `옷깃 전면의 곡면`
- `옷깃 뒷면의 곡면`
- `오른발 곡면 Z`
- `왼발 곡면 Z`
- `오른쪽 겨드랑이의 곡면`
- `왼쪽 겨드랑이의 곡면`
- `오른쪽 상완 A의 곡면`
- `오른쪽 겨드랑이의 곡면`
- `왼쪽 겨드랑이의 곡면`
- `목의 곡면`
- `뒷머리의 곡면`
- `뒷머리의 곡면 Z`
- `뒷머리의 흔들림`
- `잔머리의 곡면`
- `앞머리의 곡면`
- `앞머리 곡면 Z`
- `앞머리의 흔들림`
- `왼쪽 귀의 곡면`
- `입의 곡면`
- `왼쪽 눈썩의 각도`
- `왼쪽 눈썹의 곡면`
- `오른쪽 눈썩의 각도`
- `오른쪽 눈썹의 곡면`
- `왼쪽 눈알 하이라이트 1의 위치`
- `왼쪽 눈알 하이라이트 그림자 위치`
- `오른쪽 눈알 위치`
- `왼쪽 눈의 곡면`
- `왼쪽 뺨의 곡면`
- `얼굴의 곡면`
- `머리카락의 흔들림`
- `머리카락의 곡면`
- `몸의 곡선Z`
- `오른쪽 뺨의 곡면`
- `오른쪽 눈썹의 위치`
- `왼쪽 눈썹의 위치`
- `호흡`
- `몸의 곡선Y`
- `오른쪽 눈의 곡면`
- `오른쪽 귀의 곡면`
- `오른쪽 눈알 하이라이트 그림자 위치`
- `왼쪽 눈알 위치`
- `오른쪽 눈알 하이라이트 1의 위치`
- `뒷머리 곡면 2`
- `오른쪽 리본의 곡면`
- `뒷머리 곡면 1`
- `왼쪽 리본 곡면`
- `스커트의 흔들림`

## Rotation Deformers

- `왼발의 위치`
- `왼발 회전 2`
- `왼발 회전 3`
- `오른발 회전1`
- `팔B 오른쪽 상단 팔 회전`
- `팔B 왼쪽 상단 팔 회전`
- `팔B 오른팔의 위치`
- `팔B 왼팔 위치`
- `팔B 오른쪽 뒷 팔의 회전`
- `팔B 오른손의 회전`
- `팔B 왼쪽 팔 뒷면의 회전`
- `팔B 왼손의 회전`
- `팔 A 왼팔의 회전`
- `팔 A 왼쪽 팔뚝 회전`
- `팔 A 왼팔의 위치`
- `팔 A 오른쪽 회전`
- `팔 A 오른쪽 팔뚝 회전`
- `팔 A 오른팔의 위치`
- `목의 위치`
- `얼굴 회전`
- `오른쪽 어깨`
- `왼쪽 어깨`
- `오른발 회전 2`
- `왼발 회전1`
- `오른발 회전 3`
- `오른쪽 다리의 위치`
- `회전 0_사이드 업 오른쪽`
- `회전 1_사이드 업 오른쪽`
- `회전 2_사이드 업 오른쪽`
- `회전 3_사이드 업 오른쪽`
- `회전 4_사이드 업 오른쪽`
- `회전 5_사이드 업 오른쪽`
- `회전 6_사이드 업 오른쪽`
- `회전 0_사이드 업 왼쪽`
- `회전 1_사이드 업 왼쪽`
- `회전 2_사이드 업 왼쪽`
- `회전 3_사이드 업 왼쪽`
- `회전 4_사이드 업 왼쪽`
- `회전 5_사이드 업 왼쪽`
- `회전 6_사이드 업 왼쪽`
- `회전0_앞머리 오른쪽`
- `회전1_앞머리 오른쪽`
- `회전2_앞머리 오른쪽`
- `회전3_앞머리 오른쪽`
- `회전4_앞머리 오른쪽`
- `회전5_앞머리 오른쪽`
- `회전6_앞머리 오른쪽`
- `회전0_앞머리 왼쪽`
- `회전1_앞머리 왼쪽`
- `회전2_앞머리왼쪽`
- `회전3_앞머리왼쪽`
- `회전 4_앞머리 왼쪽`
- `회전 5_앞머리 왼쪽`
- `회전 6_앞머리 왼쪽`

## Interpretation

- This proves CMO3 structure presence, not final visual rig quality.
- It does not replace runtime render checks for keyform motion, draw order under motion, or overhang.
- Part and layer names are extracted dynamically from this CMO3; they are not image-specific hardcoded expectations.

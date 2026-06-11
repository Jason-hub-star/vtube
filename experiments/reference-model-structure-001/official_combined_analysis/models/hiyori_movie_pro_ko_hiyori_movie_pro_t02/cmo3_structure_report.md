# CMO3 Structure Report

Generated: 2026-06-08T01:24:00.890Z

Status: **WARN**

Input:

- CMO3: `experiments/reference-model-structure-001/official_samples/extracted/hiyori_movie_pro_ko/hiyori_movie_pro_ko/hiyori_movie_pro_t02.cmo3`
- Size: 13895602 bytes
- SHA256: `9f7d78c5c30170c82d00f2d23cc9b446c6f095039b27489907e1bc582f9f43d9`

## Checks

| Check | Status | Message |
|---|---:|---|
| main_xml_extracted | PASS | main.xml was extracted from the CAFF archive. |
| artmesh_present | PASS | 149 CArtMeshSource definition(s) found. |
| part_sources_present | PASS | 36 CPartSource definition(s) found. |
| parameters_present | PASS | 78 CParameterSource definition(s) found. |
| required_parameters_present | WARN | Missing configured parameter(s): ParamHairSide |
| warp_deformers_present | PASS | 62 CWarpDeformerSource definition(s) found. |
| rotation_deformers_present | PASS | 56 CRotationDeformerSource definition(s) found. |
| keyform_bindings_present | PASS | 382 KeyformBindingSource definition(s) found. |

## Structure Counts

| XML Source | Definitions | References |
|---|---:|---:|
| CArtMeshSource | 149 | 4095 |
| CPartSource | 36 | 73 |
| CWarpDeformerSource | 62 | 512 |
| CRotationDeformerSource | 56 | 228 |
| KeyformGridSource | 339 | 632 |
| KeyformBindingSource | 382 | 4555 |
| CParameterSource | 78 | 0 |
| CPhysicsSettingsSource | 11 | 0 |
| CGlueSource | 25 | 50 |
| CClippingMaskSource | 0 | 0 |
| CClippingMaskGuid | 0 | 0 |
| CInvertedMaskSource | 0 | 0 |
| CLayer | 127 | 375 |
| CLayerGroup | 33 | 222 |
| CLayeredImage | 4 | 168 |
| CImageResource | 131 | 609 |
| GEditableMesh2 | 151 | 0 |

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
- `ParamUpperarmL`
- `ParamUpperarmR`
- `ParamWristL`
- `ParamWristR`
- `ParamWristLX`
- `ParamWristRX`
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
- `ParamBodyPosition`
- `ParamForearm`
- `ParamForearmR`
- `ParamUpperarmRY`
- `ParamUpperarmLY`
- `ParamAllPositionX`
- `ParamAllPositionY`
- `ParamAllRotate`
- `ParamForearmRY`
- `ParamForearmLY`
- `ParamAllScale`

## Parts

- `Root Part`
- `코어`
- `볼`
- `눈`
- `입`
- `귀`
- `옆머리`
- `뒷머리`
- `목`
- `오른팔`
- `몸`
- `눈알`
- `눈썹`
- `코`
- `얼굴`
- `앞머리`
- `오른쪽 사이드업(회전)`
- `오른쪽 사이드 업(스키닝)`
- `좌측 사이드업(회전)`
- `왼쪽 사이드업(스키닝)`
- `오른쪽 앞머리(회전)`
- `오른쪽 앞머리(스키닝)`
- `왼쪽 앞머리(회전)`
- `왼쪽 앞머리(스키닝)`
- `책상`
- `오른쪽 팔꿈치`
- `오른손`
- `오른쪽 팔뚝`
- `오른쪽 팔뚝`
- `오른손 배면`
- `왼팔`
- `왼손`
- `왼쪽 팔뚝`
- `왼쪽 팔꿈치`
- `왼팔`
- `왼손 뒷면`

## ArtMeshes

- `가슴리본01`
- `가슴리본 02`
- `가슴리본03`
- `뒷면 깃`
- `몸통`
- `스커트`
- `오른쪽 허벅지`
- `오른쪽 종아리`
- `왼쪽 허벅지`
- `왼쪽 종아리`
- `왼발`
- `오른발`
- `목`
- `잔머리`
- `뒷머리`
- `오른쪽 뻗친머리`
- `왼쪽 뻗친머리`
- `앞머리`
- `오른쪽 귀`
- `왼쪽 귀`
- `코`
- `입 화남 2`
- `입 하이라이트`
- `입술`
- `윗 입술`
- `아랫 입술`
- `입 안`
- `왼쪽 하이라이트 01`
- `왼쪽 하이라이트 02`
- `왼쪽 하이라이트 그림자`
- `왼쪽 눈동자`
- `오른쪽 하이라이트 01`
- `오른쪽 하이라이트 02`
- `오른쪽 하이라이트 그림자`
- `오른쪽 눈동자`
- `오른쪽 웃음 눈 보조개`
- `왼쪽 웃음 눈 보조개`
- `오른쪽 웃음눈 02`
- `오른쪽 웃음눈 01`
- `오른쪽 속눈썹 1`
- `오른쪽 속눈썹 2`
- `오른쪽 속눈썹 3`
- `오른쪽 속눈썹 4`
- `오른쪽 속눈썹 5`
- `오른쪽 속눈썹 6`
- `오른쪽 속눈썹 7`
- `오른쪽 쌍커플`
- `왼쪽 속눈썹 1`
- `왼쪽 속눈썹 2`
- `왼쪽 속눈썹 3`
- `왼쪽 속눈썹 4`
- `왼쪽 속눈썹 5`
- `왼쪽 속눈썹 6`
- `왼쪽 쌍커플`
- `오른쪽 흰자`
- `왼쪽 흰자`
- `왼쪽 웃음눈 03`
- `왼쪽 웃음눈 02`
- `오른쪽 속눈썹 그림자`
- `오른쪽 뺨 하이라이트`
- `왼쪽 뺨 하이라이트`
- `오른쪽 뺨 선`
- `왼쪽 뺨 선`
- `오른쪽 홍조`
- `왼쪽 홍조 01`
- `오른쪽 홍조 02`
- `왼쪽 홍조 02`
- `머리 그림자`
- `윤곽`
- `왼쪽 웃음눈 01`
- `왼쪽 속눈썹 그림자`
- `오른쪽 사이드 업`
- `왼쪽 사이드업`
- `머리 리본 오른쪽 01`
- `머리 리본 오른쪽 02`
- `머리 리본 왼쪽 01`
- `머리 리본 왼쪽 02`
- `왼쪽 앞머리`
- `오른쪽 앞머리`
- `오른쪽 사이드 업[0]`
- `오른쪽 사이드 업[1]`
- `오른쪽 사이드 업[2]`
- `오른쪽 사이드 업[3]`
- `우측 사이드 업[4]`
- `오른쪽 사이드 업[5]`
- `오른쪽 사이드 업[6]`
- `왼쪽 사이드 업[0]`
- `왼쪽 사이드 업[1]`
- `왼쪽 사이드 업[2]`
- `왼쪽 사이드 업[3]`
- `왼쪽 사이드 업[4]`
- `왼쪽 사이드 업[5]`
- `왼쪽 사이드 업[6]`
- `오른쪽 앞머리[0]`
- `오른쪽 앞머리[1]`
- `오른쪽 앞머리[2]`
- `오른쪽 앞머리[3]`
- `오른쪽 앞머리[4]`
- `오른쪽 앞머리[5]`
- `오른쪽 앞머리[6]`
- `왼쪽 앞머리[0]`
- `왼쪽 앞머리[1]`
- `왼쪽 앞머리[2]`
- `왼쪽 앞머리[3]`
- `왼쪽 앞머리[4]`
- `오른쪽 작은 손가락 뒷면`
- `오른쪽 약지 뒷면`
- `오른쪽 가운데 손가락과 집게 손가락 뒷면`
- `왼쪽 엄지`
- `왼쪽 약지 후면`
- `왼쪽 가운데 손가락과 집게 손가락 뒷면`
- `목 선화`
- `목 그림자`
- `오른쪽 엄지손가락`
- `왼쪽 새끼손가락 후면`
- `책상`
- `오른쪽 팔꿈치 채색 01`
- `오른쪽 팔꿈치 채색 02`
- `왼쪽 팔뚝 색칠01`
- `왼쪽 팔꿈치 채색`
- `오른 쪽손가락`
- `우약지`
- `우중지`
- `오른쪽 검지`
- `오른팔 가디건 소맷단 골지 선화`
- `오른팔 카디건 소매 끝, 그림자 감추기`
- `오른쪽 소매`
- `오른쪽 팔뚝 채색01`
- `오른쪽 팔뚝`
- `오른쪽 팔뚝`
- `오른쪽 새끼손가락`
- `왼쪽 약지`
- `왼쪽 중지`
- `왼손 집게손가락`
- `왼팔 카디건 소매 골지 선화`
- `왼팔 카디건 소매 그림자 감추기`
- `왼쪽 소매`
- `왼쪽 팔뚝`
- `왼팔`
- `오른쪽 어깨`
- `왼쪽 어깨`
- `왼쪽 앞머리[5]`
- `왼쪽 앞머리[6]`
- `왼쪽 옷깃`
- `오른쪽 옷깃`
- `가슴 천`
- `왼쪽 눈썹`
- `오른쪽 눈썹`
- `윤곽 선화`

## Warp Deformers

- `리본 곡면`
- `몸의 곡면 X`
- `뒷면 옷깃 몸 X`
- `오른발 곡면 Z`
- `왼발 곡면 Z`
- `왼쪽 어깨 위쪽 팔의 회전`
- `뒷머리 각도 XY`
- `뒷머리 각도 Z`
- `뒷머리의 흔들림`
- `잔머리 곡면`
- `앞머리 각도 XY`
- `앞머리 각도 Z`
- `앞머리 흔들림`
- `왼쪽 귀의 곡면`
- `입의 곡면`
- `왼쪽 눈썹의 각도`
- `왼쪽 눈썹 곡면`
- `오른쪽 눈썹의 각도`
- `오른쪽 눈썹 곡면`
- `왼쪽 눈알 하이라이트 01의 위치`
- `왼쪽 눈알 하이라이트 그림자 위치`
- `오른쪽 눈의 위치`
- `왼쪽 눈의 곡면`
- `왼쪽 뺨의 곡면`
- `얼굴의 곡면`
- `머리카락 흔들림`
- `머리카락 그림자의 곡면`
- `오른쪽 뺨의 곡면`
- `오른쪽 눈썹 위치`
- `왼쪽 눈썹 위치`
- `호흡`
- `오른쪽 눈의 곡면`
- `오른쪽 귀의 곡면`
- `오른쪽 눈알 하이라이트 그림자 위치`
- `왼쪽 눈의 위치`
- `오른쪽 눈알 하이라이트 01의 위치`
- `뒷머리 곡면 02`
- `오른쪽 리본 곡면`
- `뒷머리 곡면 01`
- `왼쪽 리본 곡면`
- `스커트의 흔들림`
- `머리 몸의 앞뒤`
- `몸의 앞뒤`
- `뒷면 옷깃 앞뒤`
- `몸통 윗팔의 회전`
- `뒷머리 앞뒤`
- `앞머리 앞뒤`
- `오른쪽 팔 Y`
- `오른쪽 소매끝 리브 곡면`
- `목 앞뒤`
- `목의 곡면`
- `왼쪽 옷깃 앞뒤`
- `오른쪽 옷깃 앞뒤`
- `가슴 천 앞뒤`
- `옷깃 전체 몸 X`
- `몸의 곡면 Z`
- `몸의 곡면 Y`
- `스커트의 곡면`
- `오른쪽 어깨 윗 팔의 회전`
- `왼쪽 윗팔 윗팔 Y`
- `왼쪽 팔 왼쪽 팔 Y`
- `오른쪽 팔 Y`

## Rotation Deformers

- `왼쪽 다리의 위치`
- `왼쪽 다리 회전 02`
- `왼쪽 다리 회전 03`
- `오른쪽 다리 회전 01`
- `머리 몸 X`
- `두부의 각도 Z`
- `오른팔 위치 윗팔 회전`
- `왼팔의 위치 윗팔 회전`
- `오른쪽 다리 회전 02`
- `왼쪽 다리 회전 01`
- `오른쪽 다리 회전 03`
- `오른쪽 다리의 위치`
- `회전 0_오른쪽 사이드 업`
- `회전 1_오른쪽 사이드 업`
- `회전 2_오른쪽 사이드 업`
- `회전 3_오른쪽 사이드 업`
- `회전 4_오른쪽 사이드 업`
- `회전 5_오른쪽사이드 업`
- `회전 6_오른쪽 사이드 업`
- `회전 0_왼쪽 사이드 업`
- `회전 1_왼쪽 사이드 업`
- `회전 2_왼쪽 사이드 업`
- `회전 3_왼쪽 사이드 업`
- `회전 4_왼쪽 사이드 업`
- `회전 5_왼쪽 사이드 업`
- `회전 6_왼쪽 사이드 업`
- `회전0_오른쪽 앞머리`
- `회전1_오른쪽 앞머리`
- `회전2_오른쪽 앞머리`
- `회전3_오른쪽 앞머리`
- `회전4_오른쪽 앞머리`
- `회전5_오른쪽 앞머리`
- `회전6_오른쪽 앞머리`
- `회전0_왼쪽 앞머리`
- `회전1_왼쪽 앞머리`
- `회전2_왼쪽 앞머리`
- `회전3_왼쪽 앞머리`
- `회전4_왼쪽 앞머리`
- `회전5_왼쪽 앞머리`
- `회전6_왼쪽 앞머리`
- `리본 앞뒤`
- `전체 회전`
- `책상 크기 조정`
- `전체의 확축`
- `전체 위치`
- `머리 몸의 앞뒤`
- `오른쪽 팔 몸 앞뒤`
- `오른쪽 팔, 위 팔의 회전`
- `오른팔 위치 몸 X`
- `오른쪽 전완의 회전`
- `오른손의 회전`
- `왼쪽 팔 몸 앞뒤`
- `왼쪽 팔 상완 회전`
- `왼팔의 위치 X`
- `왼쪽팔의 회전`
- `왼손의 회전`

## Interpretation

- This proves CMO3 structure presence, not final visual rig quality.
- It does not replace runtime render checks for keyform motion, draw order under motion, or overhang.
- Part and layer names are extracted dynamically from this CMO3; they are not image-specific hardcoded expectations.

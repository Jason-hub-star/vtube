# CMO3 Structure Report

Generated: 2026-06-06T15:10:19.316Z

Status: **WARN**

Input:

- CMO3: `experiments/reference-model-structure-001/official_samples/extracted/rice_pro_ko/rice_pro_ko/rice_pro_t03.cmo3`
- Size: 10606270 bytes
- SHA256: `97dac816b49514f5b097166bb0da6249b4841805d9dc28f853e147293341cf2c`

## Checks

| Check | Status | Message |
|---|---:|---|
| main_xml_extracted | PASS | main.xml was extracted from the CAFF archive. |
| artmesh_present | PASS | 183 CArtMeshSource definition(s) found. |
| part_sources_present | PASS | 31 CPartSource definition(s) found. |
| parameters_present | PASS | 96 CParameterSource definition(s) found. |
| required_parameters_present | WARN | Missing configured parameter(s): ParamAngleY, ParamMouthForm, ParamMouthOpenY, ParamBreath, ParamHairFront, ParamHairSide, ParamHairBack |
| warp_deformers_present | PASS | 58 CWarpDeformerSource definition(s) found. |
| rotation_deformers_present | PASS | 80 CRotationDeformerSource definition(s) found. |
| keyform_bindings_present | PASS | 306 KeyformBindingSource definition(s) found. |

## Structure Counts

| XML Source | Definitions | References |
|---|---:|---:|
| CArtMeshSource | 183 | 1876 |
| CPartSource | 31 | 63 |
| CWarpDeformerSource | 58 | 614 |
| CRotationDeformerSource | 80 | 363 |
| KeyformGridSource | 399 | 569 |
| KeyformBindingSource | 306 | 2264 |
| CParameterSource | 96 | 0 |
| CPhysicsSettingsSource | 9 | 0 |
| CGlueSource | 33 | 66 |
| CClippingMaskSource | 0 | 0 |
| CClippingMaskGuid | 0 | 0 |
| CInvertedMaskSource | 0 | 0 |
| CLayer | 103 | 308 |
| CLayerGroup | 8 | 126 |
| CLayeredImage | 1 | 113 |
| CImageResource | 106 | 420 |
| GEditableMesh2 | 183 | 0 |

## Parameters

- `ParamAngleX`
- `ParamAngleZ`
- `ParamEyeLOpen`
- `ParamEyeROpen`
- `ParamEyeBallX`
- `ParamEyeBallY`
- `ParamBodyAngleX`
- `ParamBodyAngleY`
- `ParamBodyAngleZ`
- `ParamHairFront01`
- `ParamArmR01`
- `ParamArmR02`
- `ParamArmR03`
- `ParamArmL01`
- `ParamArmL02`
- `ParamArmL03`
- `ParamSkirt`
- `ParamSkirtX`
- `ParamSkirtY`
- `ParamShoulderL`
- `ParamShoulderR`
- `ParamHairFront02`
- `Param_Angle_Rotation_1_ArtMesh82`
- `Param_Angle_Rotation_2_ArtMesh82`
- `Param_Angle_Rotation_3_ArtMesh82`
- `Param_Angle_Rotation_4_ArtMesh82`
- `Param_Angle_Rotation_5_ArtMesh82`
- `Param_Angle_Rotation_6_ArtMesh82`
- `Param_Angle_Rotation_7_ArtMesh82`
- `Param_Angle_Rotation_1_ArtMesh80`
- `Param_Angle_Rotation_2_ArtMesh80`
- `Param_Angle_Rotation_3_ArtMesh80`
- `Param_Angle_Rotation_4_ArtMesh80`
- `Param_Angle_Rotation_5_ArtMesh80`
- `Param_Angle_Rotation_6_ArtMesh80`
- `Param_Angle_Rotation_7_ArtMesh80`
- `Param_Angle_Rotation_8_ArtMesh80`
- `Param_Angle_Rotation_9_ArtMesh80`
- `Param_Angle_Rotation_1_ArtMesh81`
- `Param_Angle_Rotation_2_ArtMesh81`
- `Param_Angle_Rotation_3_ArtMesh81`
- `Param_Angle_Rotation_4_ArtMesh81`
- `Param_Angle_Rotation_5_ArtMesh81`
- `Param_Angle_Rotation_6_ArtMesh81`
- `Param_Angle_Rotation_7_ArtMesh81`
- `Param_Angle_Rotation_8_ArtMesh81`
- `Param_Angle_Rotation_9_ArtMesh81`
- `ParamHeadRibbon`
- `ParamBustRibbon01`
- `ParamBustRibbon02`
- `ParamBookPage`
- `ParamArmR02Y`
- `ParamMagicPowersA`
- `Param_Angle_Rotation_1_ArtMesh67`
- `Param_Angle_Rotation_2_ArtMesh67`
- `Param_Angle_Rotation_3_ArtMesh67`
- `Param_Angle_Rotation_4_ArtMesh67`
- `Param_Angle_Rotation_5_ArtMesh67`
- `Param_Angle_Rotation_1_ArtMesh20`
- `Param_Angle_Rotation_2_ArtMesh20`
- `Param_Angle_Rotation_3_ArtMesh20`
- `Param_Angle_Rotation_4_ArtMesh20`
- `Param_Angle_Rotation_5_ArtMesh20`
- `ParamCharge01`
- `ParamMagicARotation`
- `ParamCharge01On`
- `ParamMagicAOn`
- `ParamLegKnee`
- `ParamHandLightAOn`
- `ParamHandLightASize`
- `ParamLegR`
- `ParamLegRUpDw`
- `ParamMagicALight`
- `ParamArmR01Y`
- `ParamWaistRibbon02`
- `ParamWaistRibbon01`
- `ParamFlame`
- `ParamFlameShaking`
- `ParamFlameOn`
- `ParamFlameX`
- `ParamFlameY`
- `ParamMagicBOn`
- `ParamMagicBRotation`
- `ParamMagicBMove`
- `ParamHandLightBOn`
- `ParamHandLightBSize`
- `ParamMagicPowersBThicknesses`
- `ParamMagicPowersBOn`
- `ParamMagicPowersBSize`
- `ParamMagicBX`
- `ParamAllZ`
- `ParamEffectBX`
- `ParamEffectBY`
- `ParamEffectAX`
- `ParamEffectAY`
- `ParamArmChange`

## Parts

- `Root Part`
- `얼굴`
- `오른팔 차분`
- `오른팔`
- `몸`
- `왼팔`
- `뒷머리`
- `왼발`
- `머리칼`
- `오른쪽 눈`
- `왼쪽 눈`
- `모자`
- `코어`
- `뒷머리 A(회전)`
- `뒷머리 A(스키닝)`
- `뒷머리 C(회전)`
- `뒷머리 C(스키닝)`
- `뒷머리 B(회전)`
- `뒷머리 B(스키닝)`
- `오른쪽 옆머리(회전)`
- `오른쪽 옆머리(스키닝)`
- `왼쪽 옆머리(회전)`
- `왼쪽 옆머리(스키닝)`
- `파동 쌓기`
- `오른발`
- `눈썹`
- `불꽃`
- `마법진 A`
- `마법진 B`
- `파동 A`
- `파동 B`

## ArtMeshes

- `입`
- `코`
- `왼쪽 귀`
- `윤곽`
- `오른쪽 팔뚝 02`
- `오른손 02`
- `오른쪽 상단 팔 02`
- `오른손 엄지`
- `오른손 검지`
- `오른손 가운데 손가락`
- `오른손 약손가락`
- `오른손 엄지`
- `오른손`
- `오른쪽 상단 팔 01`
- `오른쪽 재킷`
- `목`
- `왼쪽 재킷`
- `몸통`
- `치마 주름 02`
- `스커트`
- `오른쪽 재킷 뒷면`
- `왼쪽 자켓 뒷면`
- `왼손 손가락`
- `책01`
- `페이지`
- `책 02`
- `왼쪽 팔뚝`
- `왼쪽 손목`
- `왼쪽 앞팔 뒷면`
- `왼팔`
- `뒷머리 C`
- `뒷머리 B`
- `뒷머리 A`
- `오른쪽 구두`
- `오른발`
- `왼발`
- `왼쪽 구두`
- `앞머리 01`
- `앞머리 02`
- `왼쪽 옆머리`
- `세 개로 땋기`
- `오른쪽 옆머리`
- `오른쪽 눈 속눈썹 01`
- `오른쪽 눈 속눈썹 02`
- `오른쪽 눈 속눈썹 03`
- `오른쪽 눈 속눈썹 04`
- `오른쪽 눈 속눈썹 05`
- `오른쪽 눈 쌍꺼풀`
- `오른쪽 눈알`
- `오른쪽 흰자 클리핑용`
- `왼쪽 눈 속눈썹 01`
- `왼쪽 눈 속눈썹 02`
- `왼쪽 눈 속눈썹 03`
- `왼쪽 눈 속눈썹 04`
- `왼쪽 눈 속눈썹 05`
- `왼쪽 눈 이중`
- `왼쪽 눈알`
- `좌백목 클리핑용`
- `오른쪽 눈썹 02`
- `베레모 리본`
- `베레모`
- `오른쪽 앞팔 뒷면`
- `오른쪽 손목`
- `오른쪽 팔뚝 01`
- `스커트 주름 01`
- `뒷머리 A[0]`
- `뒷머리 A [1]`
- `뒷머리 A [2]`
- `뒷머리 A[3]`
- `뒷머리 A[4]`
- `뒷머리 A[5]`
- `뒷머리 A[6]`
- `뒷머리 C[0]`
- `뒷머리 C [1]`
- `뒷머리 C [2]`
- `뒷머리 C[3]`
- `뒷머리 C[4]`
- `뒷머리 C[5]`
- `뒷머리 C[6]`
- `뒷머리 C[7]`
- `뒷머리 C[8]`
- `뒷머리 B[0]`
- `뒷머리 B [1]`
- `뒷머리 B [2]`
- `뒷머리 B[3]`
- `뒷머리 B[4]`
- `뒷머리 B[5]`
- `뒷머리 B[6]`
- `뒷머리 B[7]`
- `뒷머리 B[8]`
- `파동 원`
- `오른쪽 옆머리[0]`
- `오른쪽 옆머리[1]`
- `오른쪽 옆머리[2]`
- `오른쪽 옆머리[3]`
- `오른쪽 옆머리[4]`
- `왼쪽 옆머리[0]`
- `왼쪽 옆머리[1]`
- `왼쪽 옆머리[2]`
- `왼쪽 옆머리[3]`
- `오른쪽 앞팔 뒷면`
- `광 선10`
- `광 선09`
- `광 선08`
- `광 선07`
- `광 선06`
- `광 선05`
- `광 선04`
- `광 선03`
- `광 선02`
- `광 선01`
- `마법진`
- `광환(손)`
- `광환(파동)`
- `광환`
- `가슴리본 02`
- `가슴리본03`
- `가슴리본01`
- `가슴리본 01 그림자`
- `가슴리본 02 그림자`
- `가슴리본 03 그림자`
- `빛 지면`
- `빛 손바닥`
- `빛`
- `허리 리본`
- `왼쪽 뒤 리본`
- `오른쪽 뒷리본`
- `왼쪽 눈썹 02`
- `오른쪽 팔뚝 반전 마스크`
- `왼쪽 눈 반전 마스크`
- `오른쪽 눈 반전 마스크`
- `발밑 광 안`
- `발밑 광 앞`
- `파동01`
- `오른팔 라인`
- `왼쪽 눈알 HL`
- `오른쪽 눈알 HL`
- `오른쪽 눈썹 01`
- `왼쪽 눈썹 01`
- `불꽃 반전마스크 09`
- `불꽃 반전마스크08`
- `불꽃 반전마스크07`
- `불꽃 반전마스크06`
- `불꽃 불티 02`
- `불꽃 불티 01`
- `불꽃 불티 02`
- `불꽃 반전마스크05`
- `불꽃 베이스`
- `불꽃 하이라이트`
- `불꽃 반전마스크04`
- `불꽃 반전마스크 03`
- `불꽃 반전마스크 02`
- `불꽃 반전마스크01`
- `불꽃 하이라이트 불티 02`
- `불꽃 하이라이트 불티01`
- `마법진 연결 05`
- `마법진 연결 04`
- `마법진 연결 03`
- `마법진 연결 02`
- `마법진 연결01`
- `오른손 선`
- `왼쪽 옆머리[4]`
- `불꽃 불티 02`
- `코 칠`
- `오른쪽 눈 이중 비침`
- `왼쪽눈 쌍꺼풀 비침`
- `흩어짐01`
- `흩어짐02`
- `흩어짐03`
- `흩어짐04`
- `흩어짐05`
- `오른팔 라인`
- `오른쪽 손목`
- `불꽃 빛`
- `좌백목`
- `오른쪽 흰자`
- `파동 02 빛`
- `파동 02`
- `광 환 B`
- `원 파동 01`
- `원 파동 02`
- `뒷머리 A선`
- `Body`

## Warp Deformers

- `오른쪽 눈의 곡면`
- `오른쪽 눈의 위치`
- `왼쪽 눈의 곡면`
- `왼쪽 눈의 위치`
- `입의 곡면`
- `귀의 곡면`
- `앞머리 01의 곡면`
- `앞머리 01의 Z`
- `앞머리 01의 흔들림`
- `앞머리 02의 곡면`
- `앞머리 02의 Z`
- `앞머리 02의 흔들림`
- `땋은  곡면`
- `모자의 곡면`
- `모자 리본 곡면`
- `왼쪽 눈썹의 곡면`
- `오른쪽 눈썹의 곡면`
- `상의 오른쪽 곡면`
- `상의 왼쪽 곡면`
- `목의 곡면`
- `몸통 곡면`
- `뒷머리의 곡면`
- `뒷머리의 Z`
- `스커트의 곡면`
- `뒷머리 A(스키닝) 곡면`
- `오른발의 굴신`
- `왼발의 굴신`
- `오른발 곡면 XZ`
- `왼발 곡면 XZ`
- `왼쪽 구두의 굴신`
- `오른쪽 구두의 굴신`
- `오른쪽 팔뚝 차분의 Y`
- `오른쪽 팔뚝의 Y`
- `오른손의 곡면`
- `오른발의 위치`
- `오른쪽 신발 곡면 XZ`
- `스커트의 흔들림`
- `상의 오른쪽 어깨 위아래`
- `상의 왼쪽 어깨 위아래`
- `불꽃 변형`
- `마법진 B01의 표시`
- `마법진 B02의 표시`
- `마법진 B03의 표시`
- `마법진 B04의 표시`
- `마법진 B05의 표시`
- `마법진 B01 곡면`
- `마법진 B02 곡면`
- `마법진 B03 곡면`
- `마법진 B04 곡면`
- `마법진 B05의 곡면`
- `몸 Z`
- `몸 Y`
- `불꽃의 흔들림`
- `얼굴의 곡면`
- `오른쪽 팔, 차분의 곡면`
- `오른쪽 팔뚝 차분의 Y`
- `오른쪽 팔뚝의 Y`
- `오른팔의 곡면`

## Rotation Deformers

- `얼굴의 회전`
- `오른팔의 위치`
- `오른쪽 팔의 회전`
- `오른쪽 전완의 회전`
- `오른손의 회전`
- `우측 상완 차분의 회전`
- `오른쪽 팔뚝 차분의 회전`
- `오른손 차분의 회전`
- `왼쪽 팔의 회전`
- `좌전완의 회전`
- `왼손의 회전`
- `왼팔의 위치`
- `목의 위치`
- `회전 0_뒷머리 A`
- `회전1_뒷머리 A`
- `회전2_뒷머리 A`
- `회전 3_뒷머리 A`
- `회전 4_뒷머리 A`
- `회전 5_뒷머리 A`
- `회전 6_뒷머리 A`
- `회전 0_뒷머리 C`
- `회전1_뒷머리 C`
- `회전2_뒷머리 C`
- `회전 3_뒷머리 C`
- `회전 4_뒷머리 C`
- `회전 5_뒷머리 C`
- `회전 6_뒷머리 C`
- `회전 7_뒷머리 C`
- `회전 8_뒷머리 C`
- `회전 0_뒷머리 B`
- `회전1_뒷머리 B`
- `회전 2_뒷머리 B`
- `회전 3_뒷머리 B`
- `회전 4_뒷머리 B`
- `회전 5_뒷머리 B`
- `회전 6_뒷머리 B`
- `회전 7_뒷머리 B`
- `회전 8_뒷머리 B`
- `뒷머리의 Z`
- `회전 0_오른쪽 옆머리`
- `회전 1_오른쪽 옆머리`
- `회전 2_오른쪽 옆머리`
- `회전 3_오른쪽 옆머리`
- `회전 4_오른쪽 옆머리`
- `회전 0_왼쪽 옆머리`
- `회전 1_왼쪽 옆머리`
- `회전 2_왼쪽 옆머리`
- `회전 3_왼쪽 옆머리`
- `회전 4_왼쪽 옆머리`
- `오른쪽 옆머리 각도 X`
- `오른쪽 옆머리의 Z`
- `왼쪽 옆머리의 Z`
- `고임의 중심`
- `마법진 A 표시`
- `오른손 차분의 위치`
- `오른쪽 손목 Y 위치`
- `오른쪽 앞팔 Y 위치`
- `오른쪽 전완 차분의 Y 위치`
- `오른쪽 집게손가락의 위치`
- `우중지의 위치`
- `우약지의 위치`
- `오른쪽 작은 손가락의 위치`
- `오른쪽 엄지손가락 위치`
- `왼쪽 옆머리 각도 X`
- `허리 리본의 위치`
- `가슴 리본의 위치`
- `불꽃 표시`
- `불꽃의 위치`
- `광환 B의 확장`
- `파동 B의 확장`
- `파동 B 표시`
- `이펙트 B의 위치`
- `이펙트 A의 위치`
- `허리 리본 우측 회전`
- `허리 리본 왼쪽 회전`
- `상반신의 굴신`
- `전체 회전`
- `파동 B 각도 X`
- `오른팔 차분의 표시`
- `오른팔의 표시`

## Interpretation

- This proves CMO3 structure presence, not final visual rig quality.
- It does not replace runtime render checks for keyform motion, draw order under motion, or overhang.
- Part and layer names are extracted dynamically from this CMO3; they are not image-specific hardcoded expectations.

# CMO3 Structure Report

Generated: 2026-06-05T14:48:27.750Z

Status: **WARN**

Input:

- CMO3: `experiments/reference-model-structure-001/official_samples/extracted/kei_ko/kei_ko/kei_vowels_pro/kei_vowels_pro_t02.cmo3`
- Size: 2435621 bytes
- SHA256: `210e3849b0eec89f2546759c55d8e3fa35955fe67c74b6caf8b429c7a3e54f76`

## Checks

| Check | Status | Message |
|---|---:|---|
| main_xml_extracted | PASS | main.xml was extracted from the CAFF archive. |
| artmesh_present | PASS | 61 CArtMeshSource definition(s) found. |
| part_sources_present | PASS | 21 CPartSource definition(s) found. |
| parameters_present | PASS | 31 CParameterSource definition(s) found. |
| required_parameters_present | WARN | Missing configured parameter(s): ParamMouthForm |
| warp_deformers_present | PASS | 46 CWarpDeformerSource definition(s) found. |
| rotation_deformers_present | PASS | 2 CRotationDeformerSource definition(s) found. |
| keyform_bindings_present | PASS | 141 KeyformBindingSource definition(s) found. |

## Structure Counts

| XML Source | Definitions | References |
|---|---:|---:|
| CArtMeshSource | 61 | 1154 |
| CPartSource | 21 | 43 |
| CWarpDeformerSource | 46 | 404 |
| CRotationDeformerSource | 2 | 8 |
| KeyformGridSource | 131 | 232 |
| KeyformBindingSource | 141 | 1021 |
| CParameterSource | 31 | 0 |
| CPhysicsSettingsSource | 6 | 0 |
| CGlueSource | 1 | 2 |
| CClippingMaskSource | 0 | 0 |
| CClippingMaskGuid | 0 | 0 |
| CInvertedMaskSource | 0 | 0 |
| CLayer | 59 | 177 |
| CLayerGroup | 20 | 118 |
| CLayeredImage | 1 | 81 |
| CImageResource | 62 | 232 |
| GEditableMesh2 | 61 | 0 |

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
- `ParamBrowLForm`
- `ParamBrowRForm`
- `ParamCheek`
- `ParamBodyAngleX`
- `ParamBodyAngleY`
- `ParamBodyAngleZ`
- `ParamBreath`
- `ParamHairFront`
- `ParamHairSide`
- `ParamHairBack`
- `ParamHairSide2`
- `ParamHairFrontFuwa`
- `ParamHairSideFuwa`
- `ParamHairBackFuwa`
- `ParamA`
- `ParamE`
- `ParamI`
- `ParamO`
- `ParamU`
- `ParamMouthOpenY`

## Parts

- `Root Part`
- `왼쪽 옆머리`
- `오른쪽 옆머리`
- `앞머리`
- `오른쪽 눈`
- `얼굴`
- `왼쪽 귀`
- `오른쪽 귀`
- `목`
- `몸`
- `뒷머리`
- `왼쪽 눈썹`
- `오른쪽 눈썹`
- `오른쪽 눈알`
- `왼쪽 눈알`
- `왼쪽 눈`
- `[밑그림]`
- `뺨`
- `코`
- `입 모음만`
- `코어`

## ArtMeshes

- `오른쪽 옆머리`
- `앞머리`
- `왼쪽 눈썹`
- `오른쪽 속눈썹1`
- `오른쪽 속눈썹2`
- `오른쪽 속눈썹3`
- `오른쪽 흰자`
- `코 선`
- `코 그림자`
- `왼쪽 귀`
- `오른쪽 귀`
- `목`
- `몸`
- `왼쪽 어깨`
- `오른쪽 어깨`
- `뒷머리`
- `오른쪽 아이섀도 1`
- `오른쪽 속눈썹4`
- `오른쪽 속눈썹5`
- `오른쪽 속눈썹6`
- `오른쪽 눈꺼풀 그림자`
- `오른쪽 눈알 하이라이트`
- `오른쪽 눈알 하이라이트 2`
- `오른쪽 눈알`
- `왼쪽 아이섀도 1`
- `왼쪽 눈꺼풀 그림자`
- `왼쪽 흰자`
- `왼쪽 눈알`
- `왼쪽 눈알 하이라이트 2`
- `왼쪽 눈알 하이라이트`
- `왼쪽 속눈썹 6`
- `왼쪽 속눈썹 5`
- `왼쪽 속눈썹 4`
- `왼쪽 속눈썹 3`
- `왼쪽 속눈썹 2`
- `왼쪽 속눈썹 1`
- `옷깃`
- `옷깃 뒤`
- `오른쪽 눈썹`
- `목덜미`
- `코 하이라이트`
- `쑥스러움`
- `얼굴`
- `顔線`
- `왼쪽 뺨의 하이라이트`
- `왼쪽 뺨`
- `오른쪽 뺨의 하이라이트`
- `오른쪽 뺨`
- `왼쪽 옆머리2`
- `왼쪽 옆머리`
- `오른쪽 옆머리2`
- `밑그림`
- `입안`
- `혀`
- `아래 치아`
- `위 치아`
- `윗 입술`
- `아래 입술 하이라이트`
- `윗 입술 하이라이트`
- `아래 입술`
- `HIT_HEAD`

## Warp Deformers

- `얼굴의 곡면`
- `왼쪽 눈의 곡면`
- `오른쪽 눈의 곡면`
- `왼쪽 눈의 위치`
- `오른쪽 눈의 위치`
- `오른쪽 눈썹 곡면`
- `왼쪽 귀의 곡면`
- `오른쪽 귀의 곡면`
- `코의 곡면`
- `앞머리 곡면`
- `앞머리 곡면 Z`
- `앞머리 볼륨`
- `앞머리 흔들림`
- `오른쪽 옆머리 곡면`
- `오른쪽 옆머리 곡면 Z`
- `오른쪽 옆머리의 볼륨`
- `오른쪽 옆머리의 흔들림`
- `왼쪽 옆머리의 곡면`
- `왼쪽 옆머리 곡면 Z`
- `왼쪽 옆머리의 볼륨`
- `왼쪽 옆머리의 흔들림`
- `뒷머리의 곡면`
- `몸의 곡면`
- `목의 곡면`
- `몸의 곡면Z`
- `몸의 곡면Y`
- `왼쪽 눈썹 곡면`
- `뒷머리 곡면`
- `뺨의 곡면`
- `뒷머리의 흔들림`
- `뒷머리의 볼륨`
- `뒷머리의 곡면 Z`
- `뒷머리 흔들림`
- `뒷머리 볼륨`
- `뒷머리 곡면 Z`
- `호흡`
- `오른쪽 옆머리2 곡면`
- `오른쪽 옆머리2 곡면 Z`
- `오른쪽 옆머리2 볼륨`
- `오른쪽 옆머리2 흔들림`
- `왼쪽 옆머리2 곡면`
- `왼쪽 옆머리2 곡면 Z`
- `왼쪽 옆머리2 볼륨`
- `왼쪽 옆머리2 흔들림`
- `입의 곡면`
- `턱 곡면`

## Rotation Deformers

- `얼굴의 회전`
- `목 회전`

## Interpretation

- This proves CMO3 structure presence, not final visual rig quality.
- It does not replace runtime render checks for keyform motion, draw order under motion, or overhang.
- Part and layer names are extracted dynamically from this CMO3; they are not image-specific hardcoded expectations.

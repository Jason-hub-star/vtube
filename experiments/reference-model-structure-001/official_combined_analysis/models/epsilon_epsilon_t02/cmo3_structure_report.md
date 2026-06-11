# CMO3 Structure Report

Generated: 2026-06-08T01:23:57.651Z

Status: **WARN**

Input:

- CMO3: `experiments/reference-model-structure-001/official_samples/extracted/epsilon/Epsilon/Epsilon_t02.cmo3`
- Size: 12611955 bytes
- SHA256: `f142d80d83a7fc80568d9491cb4dd8991c807265902745467b85926513fe68f5`

## Checks

| Check | Status | Message |
|---|---:|---|
| main_xml_extracted | PASS | main.xml was extracted from the CAFF archive. |
| artmesh_present | PASS | 73 CArtMeshSource definition(s) found. |
| part_sources_present | PASS | 27 CPartSource definition(s) found. |
| parameters_present | PASS | 37 CParameterSource definition(s) found. |
| required_parameters_present | WARN | Missing configured parameter(s): ParamAngleX, ParamAngleY, ParamAngleZ, ParamEyeLOpen, ParamEyeROpen, ParamEyeBallX, ParamEyeBallY, ParamMouthForm, ParamMouthOpenY, ParamBodyAngleX, ParamBodyAngleY, ParamBodyAngleZ, ParamBreath, ParamHairFront, ParamHairSide, ParamHairBack |
| warp_deformers_present | PASS | 51 CWarpDeformerSource definition(s) found. |
| rotation_deformers_present | PASS | 12 CRotationDeformerSource definition(s) found. |
| keyform_bindings_present | PASS | 169 KeyformBindingSource definition(s) found. |

## Structure Counts

| XML Source | Definitions | References |
|---|---:|---:|
| CArtMeshSource | 73 | 887 |
| CPartSource | 27 | 55 |
| CWarpDeformerSource | 51 | 483 |
| CRotationDeformerSource | 12 | 48 |
| KeyformGridSource | 163 | 284 |
| KeyformBindingSource | 169 | 1291 |
| CParameterSource | 37 | 0 |
| CPhysicsSettingsSource | 2 | 0 |
| CGlueSource | 0 | 0 |
| CClippingMaskSource | 0 | 0 |
| CClippingMaskGuid | 0 | 0 |
| CInvertedMaskSource | 0 | 0 |
| CLayer | 4 | 71 |
| CLayerGroup | 4 | 12 |
| CLayeredImage | 4 | 16 |
| CImageResource | 77 | 215 |
| GEditableMesh2 | 73 | 0 |

## Parameters

- `PARAM_ANGLE_X`
- `PARAM_ANGLE_Y`
- `PARAM_ANGLE_Z`
- `PARAM_EYE_L_OPEN`
- `PARAM_EYE_L_SMILE`
- `PARAM_EYE_R_OPEN`
- `PARAM_EYE_R_SMILE`
- `PARAM_EYE_FORM`
- `PARAM_EYE_BALL_X`
- `PARAM_EYE_BALL_Y`
- `PARAM_BROW_L_Y`
- `PARAM_BROW_R_Y`
- `PARAM_BROW_L_X`
- `PARAM_BROW_R_X`
- `PARAM_BROW_L_ANGLE`
- `PARAM_BROW_R_ANGLE`
- `PARAM_BROW_L_FORM`
- `PARAM_BROW_R_FORM`
- `PARAM_MOUTH_FORM`
- `PARAM_MOUTH_OPEN_Y`
- `PARAM_TERE`
- `PARAM_TEAR`
- `PARAM_SWEAT`
- `PARAM_RAGE`
- `PARAM_BODY_ANGLE_X`
- `PARAM_BODY_ANGLE_Z`
- `PARAM_BODY_ANGLE_Y`
- `PARAM_ARM_L`
- `PARAM_ARM_R`
- `PARAM_BREATH`
- `PARAM_HAIR_FRONT`
- `PARAM_HAIR_SIDE`
- `PARAM_HAIR_SIDE_L`
- `PARAM_HAIR_SIDE_R`
- `PARAM_HAIR_BACK`
- `PARAM_HAIR_BACK_L`
- `PARAM_HAIR_BACK_R`

## Parts

- `Root Part`
- `[ 下絵 ]`
- `背景`
- `足`
- `体`
- `右腕`
- `左腕`
- `首`
- `服`
- `後ろ髪１`
- `横髪１`
- `後ろ髪２`
- `横髪２`
- `前髪１`
- `前髪２`
- `耳`
- `鼻`
- `口`
- `まゆ毛`
- `目玉`
- `表情エフェクト`
- `目`
- `顔デフォーマのみ`
- `顔`
- `頬`
- `コアパーツ`
- `ラフ`

## ArtMeshes

- `素体.png_`
- `ツインテロング.png_`

## Warp Deformers

- `首の曲面`
- `首の体の回転Z`
- `服の曲面`
- `スカートの曲面`
- `後ろ髪の曲面`
- `後ろ髪のZ`
- `後ろ髪の揺れ`
- `右横髪の曲面`
- `左横髪の曲面`
- `右横髪の揺れ`
- `左横髪の揺れ`
- `後ろ頭２の曲面`
- `右ロングツインテの曲面`
- `右ロングツインテのZ`
- `左ロングツインテの曲面`
- `左ロングツインテのZ`
- `右横髪２の曲面`
- `左横髪２の曲面`
- `右横髪２のZ`
- `左横髪２のZ`
- `前髪の曲面`
- `前髪の揺れ`
- `前髪２の曲面`
- `右耳の曲面`
- `左耳の曲面`
- `鼻の曲面`
- `口の曲面`
- `右まゆ毛の曲面`
- `左まゆ毛の曲面`
- `右まゆ毛の角度`
- `右まゆ毛の位置`
- `左まゆ毛の角度`
- `左まゆ毛の位置`
- `右目玉の曲面`
- `左目玉の曲面`
- `左涙の位置`
- `右涙の位置`
- `汗の曲面`
- `表情エフェクトの曲面`
- `青スジの曲面`
- `右目の曲面`
- `左目の曲面`
- `右目の変形`
- `左目の変形`
- `顔_cの曲面`
- `右頬の曲面`
- `左頬の曲面`
- `真ん中頬の曲面`
- `呼吸`
- `体のZ`
- `体の曲面Y`

## Rotation Deformers

- `右足の回転`
- `左足の回転`
- `右腕の回転`
- `右腕の回転1`
- `右腕の回転2`
- `左腕の回転`
- `左腕の回転1`
- `左腕の回転2`
- `首の回転`
- `顔の回転`
- `右腕の回転x`
- `左腕の回転x`

## Interpretation

- This proves CMO3 structure presence, not final visual rig quality.
- It does not replace runtime render checks for keyform motion, draw order under motion, or overhang.
- Part and layer names are extracted dynamically from this CMO3; they are not image-specific hardcoded expectations.

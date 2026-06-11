# CMO3 Structure Report

Generated: 2026-06-05T14:48:28.141Z

Status: **WARN**

Input:

- CMO3: `experiments/reference-model-structure-001/official_samples/extracted/koharu_haruto/koharu_haruto/é═éΘé╞/haruto_t01.cmo3`
- Size: 3805016 bytes
- SHA256: `1cfeb30ba4b99c30d2d0244d5ae90d0c57985b7417e7d7236b8a5727a0ac0e5f`

## Checks

| Check | Status | Message |
|---|---:|---|
| main_xml_extracted | PASS | main.xml was extracted from the CAFF archive. |
| artmesh_present | PASS | 87 CArtMeshSource definition(s) found. |
| part_sources_present | PASS | 19 CPartSource definition(s) found. |
| parameters_present | PASS | 51 CParameterSource definition(s) found. |
| required_parameters_present | WARN | Missing configured parameter(s): ParamAngleX, ParamAngleY, ParamAngleZ, ParamEyeLOpen, ParamEyeROpen, ParamEyeBallX, ParamEyeBallY, ParamMouthForm, ParamMouthOpenY, ParamBodyAngleX, ParamBodyAngleY, ParamBodyAngleZ, ParamBreath, ParamHairFront, ParamHairSide, ParamHairBack |
| warp_deformers_present | PASS | 58 CWarpDeformerSource definition(s) found. |
| rotation_deformers_present | PASS | 18 CRotationDeformerSource definition(s) found. |
| keyform_bindings_present | PASS | 215 KeyformBindingSource definition(s) found. |

## Structure Counts

| XML Source | Definitions | References |
|---|---:|---:|
| CArtMeshSource | 87 | 725 |
| CPartSource | 19 | 39 |
| CWarpDeformerSource | 58 | 474 |
| CRotationDeformerSource | 18 | 78 |
| KeyformGridSource | 182 | 363 |
| KeyformBindingSource | 215 | 1433 |
| CParameterSource | 51 | 0 |
| CPhysicsSettingsSource | 4 | 0 |
| CGlueSource | 0 | 0 |
| CClippingMaskSource | 0 | 0 |
| CClippingMaskGuid | 0 | 0 |
| CInvertedMaskSource | 0 | 0 |
| CLayer | 69 | 138 |
| CLayerGroup | 1 | 71 |
| CLayeredImage | 1 | 72 |
| CImageResource | 71 | 211 |
| GEditableMesh2 | 87 | 0 |

## Parameters

- `PARAM_ANGLE_X`
- `PARAM_ANGLE_Y`
- `PARAM_ANGLE_Z`
- `PARAM_EYE_L_OPEN`
- `PARAM_EYE_L_SMILE`
- `PARAM_EYE_R_OPEN`
- `PARAM_EYE_R_SMILE`
- `PARAM_EYE_BALL_X`
- `PARAM_EYE_BALL_Y`
- `PARAM_EYE_SIZE`
- `PARAM_EYE_HI`
- `PARAM_EYE_01`
- `PARAM_TEAR_L`
- `PARAM_TEAR_R`
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
- `PARAM_MOUTH_FORM_02`
- `PARAM_DROOL`
- `PARAM_CHEEK`
- `PARAM_BODY_ANGLE_X`
- `PARAM_BODY_ANGLE_Y`
- `PARAM_BODY_ANGLE_Z`
- `PARAM_BODY`
- `PARAM_BREATH`
- `PARAM_HAIR_FRONT`
- `PARAM_HAIR_SIDE`
- `PARAM_HAIR_BACK`
- `PARAM_HAIR_FLUFFY`
- `PARAM_HAIR_FLUFFY_02`
- `PARAM_NECKTIE`
- `PARAM_ARM_L_01`
- `PARAM_ARM_L_02`
- `PARAM_ARM_L_03`
- `PARAM_ARM_L`
- `PARAM_ARM_R_01`
- `PARAM_ARM_R_02`
- `PARAM_ARM_R_03`
- `PARAM_ARM_R`
- `PARAM_HAND_SWITCH_L`
- `PARAM_HAND_SWITCH_R`
- `PARAM_HAND_L`
- `PARAM_HAND_R`
- `PARAM_PONPON`

## Parts

- `Root Part`
- `[ 下絵 ]`
- `背景`
- `体`
- `アイテム`
- `腕`
- `首`
- `後ろ髪`
- `横髪`
- `前髪`
- `耳`
- `鼻`
- `口`
- `まゆ毛`
- `目玉`
- `目`
- `顔`
- `コア`
- `ラフ`

## ArtMeshes

- `_ネクタイ`
- `_胴体`
- `_スカート`
- `_右足`
- `_左足`
- `タンバリン　線`
- `タンバリン　線`
- `タンバリン　ふた`
- `タンバリン　ふた`
- `タンバリン　ふた`
- `タンバリン　シンバル`
- `タンバリン　シンバル`
- `タンバリン　シンバル`
- `タンバリン　面`
- `タンバリン　胴`
- `タンバリン　赤リボン`
- `タンバリン　リボン`
- `ポンポン`
- `ポンポン`
- `白旗`
- `赤旗`
- `_前腕　袖線`
- `_手3`
- `_前腕 袖青`
- `_前腕　袖裏`
- `_前腕 袖白`
- `肩線`
- `_前腕`
- `_腕`
- `_前腕　袖線`
- `_手3`
- `_前腕 袖青`
- `_前腕　袖裏`
- `_前腕 袖白`
- `肩線`
- `_前腕`
- `_腕`
- `_首`
- `_帽子淵`
- `後ろ髪はね_右`
- `後ろ髪はね_左`
- `_後頭部`
- `帽子`
- `_右横髪`
- `_左横髪`
- `_前髪毛`
- `_前髪`
- `_右耳`
- `_左耳`
- `_鼻`
- `_上唇`
- `よだれ`
- `_下唇`
- `_歯`
- `_口内`
- `左眉毛`
- `右眉毛`
- `_目　キラキラ`
- `_目　キラキラ`
- `_目　キラキラ`
- `_右目ハイライト`
- `_左目ハイライト`
- `_右目玉`
- `_左目玉`
- `_目　キラキラ`
- `涙`
- `_右下まつげ`
- `_右まつげ1`
- `_右まつげ2`
- `_右二重線`
- `_左下まつげ`
- `_左まつげ1`
- `_左まつげ2`
- `_左二重線`
- `_右上瞼`
- `_右下瞼`
- `_左上瞼`
- `_左下瞼`
- `_右白目`
- `_左白目`
- `涙`
- `_髪影`
- `_右輪郭線`
- `_左輪郭線`
- `_輪郭`
- `_左頬`
- `_右頬`

## Warp Deformers

- `体の曲面`
- `リボンの曲面`
- `スカートの曲面`
- `ポンポンの曲面`
- `ポンポンの曲面`
- `タンバリンの曲面`
- `アイテムの曲面`
- `タンバリン　リボンの曲面`
- `腕シワの曲面`
- `腕シワの曲面`
- `右後ろ髪の曲面`
- `右後ろ髪の曲面Z`
- `左後ろ髪の曲面`
- `左後ろ髪の曲面Z`
- `左後ろ髪の揺れ`
- `右後ろ髪の揺れ`
- `帽子の曲面`
- `後ろ髪の曲面`
- `後ろ髪の揺れ`
- `後ろ髪の曲面ふわ`
- `右横髪の曲面`
- `右横髪の曲面Z`
- `左横髪の曲面`
- `左横髪の曲面Z`
- `右横髪の曲面ふわ`
- `左横髪の曲面ふわ`
- `前髪の曲面`
- `前髪の曲面Z`
- `前髪の揺れ`
- `前髪の曲面ふわ`
- `左耳の曲面`
- `右耳の曲面`
- `鼻の曲面`
- `口の曲面`
- `よだれの曲面`
- `左まゆ毛の曲面`
- `左まゆ毛の位置`
- `左まゆ毛の角度`
- `右まゆ毛の曲面`
- `右まゆ毛の位置`
- `右まゆ毛の角度`
- `左目玉の曲面`
- `右目玉の曲面`
- `右目玉の縮小`
- `左目玉の曲面`
- `左目の曲面`
- `左目の曲面`
- `顔の曲面`
- `右頬の曲面`
- `左頬の曲面`
- `前髪の曲面`
- `顔の曲面1`
- `顔の曲面2`
- `呼吸`
- `体の曲面Z`
- `体の曲面Y`
- `下半身の曲面`
- `上半身の曲面`

## Rotation Deformers

- `左足の回転`
- `右足の回転`
- `タンバリンの回転`
- `白旗の回転01`
- `白旗の回転02`
- `白旗の回転01`
- `白旗の回転02`
- `タンバリン　リボンの回転`
- `腕の回転X`
- `上腕の回転`
- `前腕の回転`
- `腕の回転X`
- `上腕の回転`
- `前腕の回転`
- `首の回転`
- `涙の回転`
- `涙の回転`
- `顔の回転`

## Interpretation

- This proves CMO3 structure presence, not final visual rig quality.
- It does not replace runtime render checks for keyform motion, draw order under motion, or overhang.
- Part and layer names are extracted dynamically from this CMO3; they are not image-specific hardcoded expectations.

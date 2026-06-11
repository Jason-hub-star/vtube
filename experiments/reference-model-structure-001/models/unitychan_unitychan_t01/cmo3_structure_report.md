# CMO3 Structure Report

Generated: 2026-06-05T14:48:46.826Z

Status: **WARN**

Input:

- CMO3: `experiments/reference-model-structure-001/official_samples/extracted/unitychan/Unitychan/unitychan_t01.cmo3`
- Size: 3335550 bytes
- SHA256: `873cf53e7c453de4fa073707d0a6c22d6542ca5a45a679c84a8ecfa607d802cd`

## Checks

| Check | Status | Message |
|---|---:|---|
| main_xml_extracted | PASS | main.xml was extracted from the CAFF archive. |
| artmesh_present | PASS | 70 CArtMeshSource definition(s) found. |
| part_sources_present | PASS | 20 CPartSource definition(s) found. |
| parameters_present | PASS | 39 CParameterSource definition(s) found. |
| required_parameters_present | WARN | Missing configured parameter(s): ParamAngleX, ParamAngleY, ParamAngleZ, ParamEyeLOpen, ParamEyeROpen, ParamEyeBallX, ParamEyeBallY, ParamMouthForm, ParamMouthOpenY, ParamBodyAngleX, ParamBodyAngleY, ParamBodyAngleZ, ParamBreath, ParamHairFront, ParamHairSide, ParamHairBack |
| warp_deformers_present | PASS | 40 CWarpDeformerSource definition(s) found. |
| rotation_deformers_present | PASS | 15 CRotationDeformerSource definition(s) found. |
| keyform_bindings_present | PASS | 140 KeyformBindingSource definition(s) found. |

## Structure Counts

| XML Source | Definitions | References |
|---|---:|---:|
| CArtMeshSource | 70 | 536 |
| CPartSource | 20 | 41 |
| CWarpDeformerSource | 40 | 339 |
| CRotationDeformerSource | 15 | 78 |
| KeyformGridSource | 145 | 239 |
| KeyformBindingSource | 140 | 982 |
| CParameterSource | 39 | 0 |
| CPhysicsSettingsSource | 3 | 0 |
| CGlueSource | 0 | 0 |
| CClippingMaskSource | 0 | 0 |
| CClippingMaskGuid | 0 | 0 |
| CInvertedMaskSource | 0 | 0 |
| CLayer | 66 | 132 |
| CLayerGroup | 1 | 68 |
| CLayeredImage | 1 | 69 |
| CImageResource | 69 | 207 |
| GEditableMesh2 | 70 | 0 |

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
- `PARAM_EYE_BALL_FORM`
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
- `PARAM_CHEEK`
- `PARAM_ARM_L_01`
- `PARAM_ARM_L_02`
- `PARAM_HAND_L`
- `PARAM_ARM_R_01`
- `PARAM_ARM_R_02`
- `PARAM_HAND_R`
- `PARAM_LEG_L`
- `PARAM_LEG_R`
- `PARAM_BODY_ANGLE_X`
- `PARAM_BODY_ANGLE_Y`
- `PARAM_BODY_ANGLE_Z`
- `PARAM_BREATH`
- `PARAM_HAIR_FLUFFY`
- `PARAM_HAIR_FRONT`
- `PARAM_HAIR_BACK`
- `PARAM_BASE_X`
- `PARAM_BASE_Y`

## Parts

- `Root Part`
- `[ 下絵 ]`
- `背景`
- `足`
- `体`
- `右腕`
- `左腕`
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
- `頬`
- `ラフ`

## ArtMeshes

- `PIKOユニ_インポート_t02.jpg_`
- `_右足影`
- `_右足`
- `_左足影`
- `_左足`
- `_体後ろ左`
- `_体後ろ右`
- `_体`
- `_服裾`
- `_水着`
- `_服後ろ`
- `_右腕3`
- `_右腕2`
- `_右腕1`
- `_右手差分`
- `_右手`
- `_右袖裏`
- `_左腕3`
- `_左腕2`
- `_左腕1`
- `_左手差分`
- `_左手`
- `_左袖裏`
- `_首`
- `_後ろ髪`
- `_前髪3`
- `_前髪2`
- `_前髪1`
- `_左リボン前`
- `_左リボン後ろ`
- `_右リボン前`
- `_右リボン後ろ`
- `_左耳`
- `_右耳`
- `_口かぶせ`
- `_上口`
- `_下口`
- `_口中`
- `_左眉`
- `_右眉`
- `_左ハイライト`
- `_左ハイライト`
- `_右ハイライト`
- `_右ハイライト`
- `_左目玉`
- `_右目玉`
- `_左まつげ4`
- `_左まつげ3`
- `_左まつげ2`
- `_左まつげ1`
- `_右まつげ4`
- `_右まつげ3`
- `_右まつげ2`
- `_右まつげ1`
- `_左まつ毛5`
- `_右まつ毛5`
- `_左下まつげ`
- `_右下まつげ`
- `_右白目`
- `_左白目`
- `_右目クリッピング`
- `_左目クリッピング`
- `_バンダナ`
- `_輪郭`
- `_左頬ハイライト`
- `_左頬染`
- `_右頬ハイライト`
- `_右頬染`
- `_左頬`
- `_右頬`

## Warp Deformers

- `体の曲面Z`
- `体の曲面Y`
- `呼吸`
- `体の曲面X`
- `右腕の曲面`
- `左腕の曲面`
- `左腕の曲面1`
- `首の曲面`
- `後ろ髪の曲面`
- `後ろ髪の曲面Z`
- `後ろ髪のふわ`
- `前髪の曲面`
- `前髪の曲面Z`
- `前髪の揺れ`
- `前髪ふわ`
- `右リボンの曲面`
- `左リボンの曲面`
- `右リボンの揺れ`
- `左リボンの揺れ`
- `右耳の曲面`
- `左耳の曲面`
- `口の曲面`
- `右まゆ毛の曲面`
- `左まゆ毛の曲面`
- `右まゆ毛の角度`
- `左まゆ毛の角度`
- `右まゆ毛の位置`
- `左まゆ毛の位置`
- `右目玉の曲面`
- `左目玉の曲面`
- `右目玉ハイライト`
- `左目玉ハイライト`
- `右目玉の縮小`
- `左目玉の縮小`
- `右目の曲面`
- `右目の変形`
- `左目の曲面`
- `左目の変形`
- `顔の曲面`
- `頬の曲面`

## Rotation Deformers

- `左脚の回転X`
- `右脚の回転X`
- `右足の回転`
- `左足の回転`
- `全体位置`
- `右腕の回転X`
- `右腕の回転`
- `右腕の回転1`
- `右手の回転`
- `左腕の回転X`
- `左腕の回転`
- `左腕の回転1`
- `首の回転`
- `顔の回転`
- `顔の拡縮`

## Interpretation

- This proves CMO3 structure presence, not final visual rig quality.
- It does not replace runtime render checks for keyform motion, draw order under motion, or overhang.
- Part and layer names are extracted dynamically from this CMO3; they are not image-specific hardcoded expectations.

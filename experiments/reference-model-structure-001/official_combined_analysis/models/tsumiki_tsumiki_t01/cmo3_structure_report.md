# CMO3 Structure Report

Generated: 2026-06-08T01:24:21.851Z

Status: **WARN**

Input:

- CMO3: `experiments/reference-model-structure-001/official_samples/extracted/tsumiki/tsumiki/tsumiki_t01.cmo3`
- Size: 8456454 bytes
- SHA256: `7fd9fd627cbbaa61d212d21723a7c54f9d89b3d563f51ddba2e79b5703427275`

## Checks

| Check | Status | Message |
|---|---:|---|
| main_xml_extracted | PASS | main.xml was extracted from the CAFF archive. |
| artmesh_present | PASS | 89 CArtMeshSource definition(s) found. |
| part_sources_present | PASS | 22 CPartSource definition(s) found. |
| parameters_present | PASS | 46 CParameterSource definition(s) found. |
| required_parameters_present | WARN | Missing configured parameter(s): ParamAngleX, ParamAngleY, ParamAngleZ, ParamEyeLOpen, ParamEyeROpen, ParamEyeBallX, ParamEyeBallY, ParamMouthForm, ParamMouthOpenY, ParamBodyAngleX, ParamBodyAngleY, ParamBodyAngleZ, ParamBreath, ParamHairFront, ParamHairSide, ParamHairBack |
| warp_deformers_present | PASS | 67 CWarpDeformerSource definition(s) found. |
| rotation_deformers_present | PASS | 22 CRotationDeformerSource definition(s) found. |
| keyform_bindings_present | PASS | 240 KeyformBindingSource definition(s) found. |

## Structure Counts

| XML Source | Definitions | References |
|---|---:|---:|
| CArtMeshSource | 89 | 982 |
| CPartSource | 22 | 45 |
| CWarpDeformerSource | 67 | 579 |
| CRotationDeformerSource | 22 | 318 |
| KeyformGridSource | 200 | 397 |
| KeyformBindingSource | 240 | 2469 |
| CParameterSource | 46 | 0 |
| CPhysicsSettingsSource | 7 | 0 |
| CGlueSource | 0 | 0 |
| CClippingMaskSource | 0 | 0 |
| CClippingMaskGuid | 0 | 0 |
| CInvertedMaskSource | 0 | 0 |
| CLayer | 86 | 172 |
| CLayerGroup | 1 | 88 |
| CLayeredImage | 1 | 89 |
| CImageResource | 90 | 266 |
| GEditableMesh2 | 89 | 0 |

## Parameters

- `PARAM_ANGLE_X`
- `PARAM_ANGLE_Y`
- `PARAM_ANGLE_Z`
- `PARAM_EYE_L_OPEN`
- `PARAM_EYE_L_SMILE`
- `PARAM_EYE_R_OPEN`
- `PARAM_EYE_R_SMILE`
- `PARAM_EYE_FORM`
- `PARAM_TEAR`
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
- `PARAM_CHEEK_01`
- `PARAM_CHEEK_02`
- `PARAM_CHEEK_03`
- `PARAM_CHEEK_04`
- `PARAM_BODY_ANGLE_X`
- `PARAM_BODY_ANGLE_Y`
- `PARAM_BODY_ANGLE_Z`
- `PARAM_BREATH`
- `PARAM_UPBACK`
- `PARAM_BUST_Y`
- `PARAM_TIE`
- `PARAM_SKIRT`
- `PARAM_HAIR_FRONT`
- `PARAM_HAIR_SIDE`
- `PARAM_HAIR_BACK`
- `PARAM_HAIR_AHO`
- `PARAM_HAIR_TAIR`
- `PARAM_RIBON_L`
- `PARAM_RIBON_R`
- `PARAM_ARM`
- `PARAM_ARM_L`
- `PARAM_ARM_R`
- `PARAM_FINGER`
- `PARAM_LEG_L`

## Parts

- `Root Part`
- `[ 下絵 ]`
- `背景`
- `脚`
- `右腕`
- `左腕`
- `体`
- `首`
- `後ろ髪`
- `横髪`
- `前髪`
- `耳`
- `頬`
- `鼻`
- `口`
- `まゆ毛`
- `目玉`
- `目`
- `あほ毛`
- `顔`
- `コアパーツ`
- `ラフ`

## ArtMeshes

- `左ひざ下`
- `右ひざ下`
- `_右足`
- `_左足`
- `_右肩服裏`
- `_右肩`
- `_右肩服前`
- `_右ひじ（差分時非表示）`
- `_右手首（差分時非表示）`
- `_右人差し指（差分時非表示）`
- `_右親指（差分時非表示）`
- `_左肩服裏`
- `_左肩`
- `_左肩服前`
- `_左ひじ（差分時非表示`
- `_左手首（差分時非表示`
- `_左親指（差分時非表示`
- `_左人差し指（差分時非表示`
- `_スカート中央`
- `_スカート右`
- `_スカート左`
- `_後ろ襟`
- `_胴`
- `_胸`
- `_ネクタイ`
- `_右手前襟`
- `_左手前襟`
- `_首`
- `_後ろ髪`
- `_右テール`
- `_左テール`
- `_右リボン2`
- `_右リボン裏`
- `_右リボン1`
- `_左リボン2`
- `_左リボン裏`
- `_左リボン1`
- `_前髪`
- `_前髪影`
- `_右耳`
- `_左耳`
- `_頬（差分２）`
- `_頬（差分２）`
- `_頬（差分）`
- `_頬　通常`
- `_頬　通常`
- `_頬`
- `_頬`
- `_鼻`
- `_口中`
- `_歯`
- `_口隠し左`
- `_口隠し右`
- `_口影左`
- `_口影右`
- `_口上`
- `_口下`
- `_まゆげ右`
- `_まゆげ左`
- `_右目ハイライト`
- `_右瞳`
- `_左目ハイライト`
- `_左瞳`
- `左目涙`
- `右目涙`
- `_右白目`
- `_右下まつ毛`
- `_右横まつ毛2`
- `_右横まつ毛`
- `_右まつ毛4`
- `_右まつ毛3`
- `_右まつ毛2`
- `_右まつ毛1`
- `_右瞼`
- `_左白目`
- `_左下まつ毛`
- `_左横まつ毛2`
- `_左横まつ毛`
- `_左まつ毛5`
- `_左まつ毛4`
- `_左まつ毛3`
- `_左まつ毛2`
- `_左まつ毛1`
- `_左瞼`
- `_アホ毛（差分）`
- `_輪郭`
- `_もみあげ`
- `_輪郭線左`
- `_輪郭線右`

## Warp Deformers

- `左脚の曲面`
- `右脚の曲面`
- `右ひざ下の曲面`
- `左ひざ下の曲面`
- `膝下の曲面Y`
- `右ひざ下の曲面X`
- `左ひざ下の曲面X`
- `左ひざ下の曲面Z`
- `右ひざ下の曲面Z`
- `右肩の曲面`
- `左肩の曲面`
- `体の曲面`
- `胸の揺れ`
- `ネクタイの曲面`
- `ネクタイの回転Z`
- `ネクタイの揺れ`
- `スカート左の曲面`
- `スカート右の曲面`
- `スカート中央の曲面`
- `スカート左の揺れ`
- `スカート右の揺れ`
- `胸の曲面`
- `スカート中央の揺れ`
- `首の曲面`
- `後ろ髪の曲面`
- `左髪の曲面`
- `左髪の回転`
- `左テール揺れ`
- `左リボン1揺れ`
- `左リボン2揺れ`
- `右髪の曲面`
- `右髪の回転`
- `右テール揺れ`
- `右リボン1揺れ`
- `右リボン2揺れ`
- `前髪の曲面`
- `前髪のZ回転`
- `前髪の揺れ`
- `左耳の曲面`
- `右耳の曲面`
- `頬の曲面`
- `鼻の曲面`
- `口の曲面`
- `口内の曲面`
- `左まゆ毛の曲面`
- `右まゆ毛の曲面`
- `左まゆ毛の位置`
- `右まゆ毛の位置`
- `左まゆ毛の回転`
- `右まゆ毛の回転`
- `左目の位置`
- `左ハイライト位置`
- `右目の位置`
- `右ハイライト位置`
- `右目の曲面`
- `左目の曲面`
- `右目涙の曲面`
- `左目涙の曲面`
- `あほ毛の曲面`
- `あほ毛揺れ`
- `顔の曲面`
- `目の変形`
- `体の曲面Z`
- `体の曲面Y`
- `呼吸`
- `上半身の上体`
- `下半身の上体`

## Rotation Deformers

- `左脚の拡縮`
- `右脚の拡縮`
- `脚の回転`
- `右腕の拡縮`
- `右腕の回転`
- `右上腕の回転`
- `右前腕の回転`
- `右手の回転`
- `右人差し指の回転`
- `右親指の回転`
- `左腕の拡縮`
- `左腕の回転`
- `左上腕の回転`
- `左前腕の回転`
- `左手の回転`
- `左人差し指の回転`
- `左親指の回転`
- `首の位置`
- `首の上体`
- `あほ毛の位置`
- `顔の回転`
- `顔の拡縮`

## Interpretation

- This proves CMO3 structure presence, not final visual rig quality.
- It does not replace runtime render checks for keyform motion, draw order under motion, or overhang.
- Part and layer names are extracted dynamically from this CMO3; they are not image-specific hardcoded expectations.

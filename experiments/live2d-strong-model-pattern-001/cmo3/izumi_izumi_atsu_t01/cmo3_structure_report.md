# CMO3 Structure Report

Generated: 2026-06-06T15:10:23.540Z

Status: **WARN**

Input:

- CMO3: `experiments/reference-model-structure-001/official_samples/extracted/izumi/izumi/izumi_atsu_t01.cmo3`
- Size: 36439221 bytes
- SHA256: `adaa8c3b3b84ecfef326a47ca2d3d07eb2d613a4f4fa6b761370942d8cd695f0`

## Checks

| Check | Status | Message |
|---|---:|---|
| main_xml_extracted | PASS | main.xml was extracted from the CAFF archive. |
| artmesh_present | PASS | 77 CArtMeshSource definition(s) found. |
| part_sources_present | PASS | 21 CPartSource definition(s) found. |
| parameters_present | PASS | 30 CParameterSource definition(s) found. |
| required_parameters_present | WARN | Missing configured parameter(s): ParamAngleX, ParamAngleY, ParamAngleZ, ParamEyeLOpen, ParamEyeROpen, ParamEyeBallX, ParamEyeBallY, ParamMouthForm, ParamMouthOpenY, ParamBodyAngleX, ParamBodyAngleY, ParamBodyAngleZ, ParamBreath, ParamHairFront, ParamHairSide, ParamHairBack |
| warp_deformers_present | PASS | 39 CWarpDeformerSource definition(s) found. |
| rotation_deformers_present | PASS | 6 CRotationDeformerSource definition(s) found. |
| keyform_bindings_present | PASS | 171 KeyformBindingSource definition(s) found. |

## Structure Counts

| XML Source | Definitions | References |
|---|---:|---:|
| CArtMeshSource | 77 | 679 |
| CPartSource | 21 | 43 |
| CWarpDeformerSource | 39 | 356 |
| CRotationDeformerSource | 6 | 56 |
| KeyformGridSource | 143 | 280 |
| KeyformBindingSource | 171 | 1337 |
| CParameterSource | 30 | 0 |
| CPhysicsSettingsSource | 3 | 0 |
| CGlueSource | 0 | 0 |
| CClippingMaskSource | 0 | 0 |
| CClippingMaskGuid | 0 | 0 |
| CInvertedMaskSource | 0 | 0 |
| CLayer | 4 | 74 |
| CLayerGroup | 4 | 12 |
| CLayeredImage | 4 | 16 |
| CImageResource | 81 | 163 |
| GEditableMesh2 | 77 | 0 |

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
- `PARAM_TERE`
- `PARAM_BODY_ANGLE_X`
- `PARAM_BODY_ANGLE_Y`
- `PARAM_BODY_ANGLE_Z`
- `PARAM_ARM_L`
- `PARAM_ARM_R`
- `PARAM_BREATH`
- `PARAM_HAIR_FRONT`
- `PARAM_HAIR_SIDE`
- `PARAM_HAIR_BACK`

## Parts

- `Root Part`
- `[ 下絵 ]`
- `背景`
- `体`
- `首`
- `右腕`
- `左腕`
- `服`
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
- `コアパーツ`
- `ラフ`

## ArtMeshes

- `イラスト塗り_下絵.png_`
- `イラスト塗り_反転.png_`
- `下絵_ムービー用キャラ_アニメ塗り_バリエーション_03.jpg_`

## Warp Deformers

- `首の曲面`
- `首の曲面1`
- `服の曲面`
- `後ろ髪の曲面`
- `後ろ髪Z`
- `後ろ髪の揺れ`
- `右横髪の曲面`
- `左横髪の曲面`
- `左横髪の揺れ`
- `右横髪の揺れ`
- `前髪の曲面`
- `前髪の揺れ`
- `右耳の曲面`
- `左耳の曲面`
- `鼻の曲面`
- `鼻の曲面1`
- `口の曲面`
- `右まゆ毛の曲面`
- `左まゆ毛の曲面`
- `右まゆ毛の角度`
- `右まゆ毛の位置`
- `左まゆ毛の角度`
- `左まゆ毛の位置`
- `右目玉の曲面`
- `左目玉の曲面`
- `右目玉の縮小`
- `左目玉の縮小`
- `右目の曲面`
- `左目の曲面`
- `目_cの曲面`
- `髪影の曲面`
- `髪影の揺れ`
- `顔影横の曲面`
- `顔影横の揺れ`
- `左頬の曲面`
- `右頬の曲面`
- `呼吸`
- `体の回転Z`
- `体の回転Y`

## Rotation Deformers

- `首の回転`
- `右腕の回転`
- `右腕の回転2`
- `左腕の回転`
- `左腕の回転2`
- `顔の回転`

## Interpretation

- This proves CMO3 structure presence, not final visual rig quality.
- It does not replace runtime render checks for keyform motion, draw order under motion, or overhang.
- Part and layer names are extracted dynamically from this CMO3; they are not image-specific hardcoded expectations.

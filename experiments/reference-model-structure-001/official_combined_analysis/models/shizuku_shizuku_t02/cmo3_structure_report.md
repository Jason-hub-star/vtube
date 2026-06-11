# CMO3 Structure Report

Generated: 2026-06-08T01:24:21.290Z

Status: **WARN**

Input:

- CMO3: `experiments/reference-model-structure-001/official_samples/extracted/shizuku/shizuku/shizuku_t02.cmo3`
- Size: 41055649 bytes
- SHA256: `0352cbbc0f999c5542b2533d060bc625a569481917c82c23df8ee1e884b1b6b1`

## Checks

| Check | Status | Message |
|---|---:|---|
| main_xml_extracted | PASS | main.xml was extracted from the CAFF archive. |
| artmesh_present | PASS | 187 CArtMeshSource definition(s) found. |
| part_sources_present | PASS | 40 CPartSource definition(s) found. |
| parameters_present | PASS | 45 CParameterSource definition(s) found. |
| required_parameters_present | WARN | Missing configured parameter(s): ParamAngleX, ParamAngleY, ParamAngleZ, ParamEyeLOpen, ParamEyeROpen, ParamEyeBallX, ParamEyeBallY, ParamMouthForm, ParamMouthOpenY, ParamBodyAngleX, ParamBodyAngleY, ParamBodyAngleZ, ParamBreath, ParamHairFront, ParamHairSide, ParamHairBack |
| warp_deformers_present | PASS | 156 CWarpDeformerSource definition(s) found. |
| rotation_deformers_present | PASS | 27 CRotationDeformerSource definition(s) found. |
| keyform_bindings_present | PASS | 358 KeyformBindingSource definition(s) found. |

## Structure Counts

| XML Source | Definitions | References |
|---|---:|---:|
| CArtMeshSource | 187 | 1805 |
| CPartSource | 40 | 81 |
| CWarpDeformerSource | 156 | 1366 |
| CRotationDeformerSource | 27 | 304 |
| KeyformGridSource | 410 | 622 |
| KeyformBindingSource | 358 | 3375 |
| CParameterSource | 45 | 0 |
| CPhysicsSettingsSource | 3 | 0 |
| CGlueSource | 0 | 0 |
| CClippingMaskSource | 0 | 0 |
| CClippingMaskGuid | 0 | 0 |
| CInvertedMaskSource | 0 | 0 |
| CLayer | 8 | 156 |
| CLayerGroup | 8 | 24 |
| CLayeredImage | 8 | 32 |
| CImageResource | 171 | 347 |
| GEditableMesh2 | 187 | 0 |

## Parameters

- `PARAM_ANGLE_X`
- `PARAM_ANGLE_Y`
- `PARAM_ANGLE_Z`
- `PARAM_EYE_L_OPEN`
- `PARAM_EYE_R_OPEN`
- `PARAM_EYE_BALL_X`
- `PARAM_EYE_BALL_Y`
- `PARAM_EYE_BALL_FORM`
- `PARAM_EYE_BALL_KIRAKIRA`
- `PARAM_BROW_L_Y`
- `PARAM_BROW_R_Y`
- `PARAM_BROW_L_X`
- `PARAM_BROW_R_X`
- `PARAM_BROW_L_ANGLE`
- `PARAM_BROW_R_ANGLE`
- `PARAM_BROW_L_FORM`
- `PARAM_BROW_R_FORM`
- `PARAM_MOUTH_OPEN_Y`
- `PARAM_MOUTH_FORM`
- `PARAM_MOUTH_SIZE`
- `PARAM_TERE`
- `PARAM_BODY_X`
- `PARAM_BODY_Z`
- `PARAM_BODY_Y`
- `PARAM_BREATH`
- `PARAM_ARM_L`
- `PARAM_ARM_L_02`
- `PARAM_HAND_L`
- `PARAM_ARM_R`
- `PARAM_ARM_R_02`
- `PARAM_HAND_R`
- `PARAM_ARM_02_L_01`
- `PARAM_ARM_02_L_02`
- `PARAM_HAND_02_L`
- `PARAM_ARM_02_R_01`
- `PARAM_ARM_02_R_02`
- `PARAM_HAND_02_R`
- `PARAM_KAMIYURE_FRONT`
- `PARAM_KAMIYURE_BACK`
- `PARAM_KAMIYURE_SIDE_L`
- `PARAM_KAMIYURE_SIDE_R`
- `PARAM_KAMIYURE_TWIN_L`
- `PARAM_KAMIYURE_TWIN_R`
- `PARAM_DONYORI`
- `PARAM_DESK`

## Parts

- `Root Part`
- `[ 下絵 ]`
- `マグカップ・クッキー`
- `背景　家`
- `背景　学校`
- `背景`
- `キラキラ`
- `汗`
- `イライラ`
- `体`
- `首`
- `パジャマ`
- `制服※座標系はコアに移動`
- `右腕２ パジャマ`
- `左腕２ パジャマ`
- `右腕１ パジャマ`
- `左腕１ パジャマ`
- `右腕２`
- `左腕２`
- `右腕１`
- `左腕１`
- `ツインテール　後ろ`
- `ツインテール　右`
- `ツインテール　左`
- `下ろし髪　後ろ`
- `横髪`
- `前髪`
- `耳`
- `鼻`
- `口`
- `まゆ毛`
- `目玉`
- `目玉 ぐるぐる`
- `目玉 キラキラ`
- `目`
- `顔`
- `頬`
- `顔影`
- `コアパーツ`
- `ラフ`

## ArtMeshes

- `D_SKETCH.00`
- `D_SKETCH.02`
- `しずく腕.png_`
- `しずくパジャマ.png_`
- `部屋_夜.png_`
- `反転.png_`
- `新口.jpg_`

## Warp Deformers

- `体の曲面`
- `体の曲面1`
- `体の曲面2`
- `体の呼吸`
- `首の曲面`
- `首の曲面1`
- `パジャマの曲面`
- `パジャマ襟の曲面`
- `パジャマ　袖の曲面11`
- `パジャマ　袖の曲面10`
- `パジャマ　袖の曲面7`
- `パジャマ　袖の曲面6`
- `パジャマ　袖の曲面9`
- `パジャマ　袖の曲面8`
- `パジャマ右手の曲面`
- `パジャマ右手の曲面1`
- `パジャマ右手の曲面2`
- `パジャマ右手の曲面3`
- `パジャマ右手の曲面4`
- `パジャマ右手の曲面5`
- `パジャマ右手の曲面6`
- `パジャマ　袖の曲面`
- `パジャマ　袖の曲面1`
- `パジャマ　袖の曲面2`
- `パジャマ　袖の曲面3`
- `パジャマ　袖の曲面4`
- `パジャマ　袖の曲面5`
- `パジャマ　袖の曲面12`
- `パジャマ左手の曲面`
- `パジャマ左手の曲面1`
- `パジャマ左手の曲面2`
- `パジャマ左手の曲面3`
- `パジャマ左手の曲面4`
- `パジャマ左手の曲面5`
- `パジャマ左手の曲面6`
- `パジャマ左手の曲面7`
- `カーディガン　袖の曲面11`
- `カーディガン　袖の曲面10`
- `カーディガン　袖の曲面7`
- `カーディガン　袖の曲面6`
- `カーディガン　袖の曲面9`
- `カーディガン　袖の曲面8`
- `右手の曲面`
- `右手の曲面1`
- `右手の曲面2`
- `右手の曲面3`
- `右手の曲面4`
- `右手の曲面5`
- `右手の曲面6`
- `カーディガン　袖の曲面`
- `カーディガン　袖の曲面1`
- `カーディガン　袖の曲面2`
- `カーディガン　袖の曲面3`
- `カーディガン　袖の曲面4`
- `カーディガン　袖の曲面5`
- `カーディガン　袖の曲面12`
- `カーディガン　袖の曲面13`
- `左手の曲面`
- `左手の曲面1`
- `左手の曲面2`
- `左手の曲面3`
- `左手の曲面4`
- `左手の曲面5`
- `左手の曲面6`
- `左手の曲面7`
- `後ろ髪の曲面`
- `後ろ髪の曲面1`
- `ツインテール　右の曲面`
- `ツインテール　右の曲面2`
- `ツインテール　右の曲面3`
- `ツインテール　右の曲面1`
- `ツインテール　右の曲面4`
- `ツインテール　右の曲面5`
- `ツインテール　右の曲面6`
- `ツインテール　右の曲面7`
- `ツインテール　右の曲面8`
- `ツインテール　右の曲面9`
- `ツインテール　右の曲面10`
- `ツインテール　左の曲面`
- `ツインテール　左の曲面1`
- `ツインテール　左の曲面2`
- `ツインテール　左の曲面3`
- `ツインテール　左の曲面4`
- `ツインテール　左の曲面5`
- `ツインテール　左の曲面6`
- `ツインテール　左の曲面7`
- `ツインテール　左の曲面8`
- `ツインテール　左の曲面9`
- `下ろし髪　頭の曲面`
- `下ろし髪　頭の曲面Z`
- `下ろし髪　頭の揺れ`
- `下ろし髪　左の曲面`
- `下ろし髪　左の曲面Z`
- `下ろし髪　右の曲面`
- `下ろし髪　右の曲面Z`
- `下ろし髪　右の揺れ`
- `下ろし髪　左の揺れ`
- `横髪の曲面`
- `横髪の曲面1`
- `横髪の曲面3`
- `横髪の曲面4`
- `横髪の曲面2`
- `横髪の曲面5`
- `前髪の曲面`
- `前髪の曲面1`
- `耳の曲面`
- `耳の曲面1`
- `鼻の曲面`
- `口の曲面1`
- `口の曲面2`
- `口の曲面`
- `口の曲面3`
- `口の曲面4`
- `まゆ毛の曲面`
- `まゆ毛の曲面1`
- `まゆ毛の曲面2`
- `まゆ毛の曲面3`
- `まゆ毛の曲面4`
- `まゆ毛の曲面5`
- `目玉の曲面`
- `目玉の曲面1`
- `目玉の曲面2`
- `目玉の曲面3`
- `目玉の曲面4`
- `目玉の曲面6`
- `目玉の曲面7`
- `目玉の曲面8`
- `目玉の曲面5`
- `目玉の曲面9`
- `目の曲面`
- `目の曲面1`
- `目の曲面2`
- `目の曲面3`
- `顔の曲面`
- `頬の曲面`
- `頬の曲面1`
- `顔影の曲面`
- `顔影の曲面1`
- `リボンの曲面`
- `リボンの曲面1`
- `リボンの曲面2`
- `リボンの曲面3`
- `カーディガンの曲面`
- `カーディガンの曲面1`
- `カーディガンの曲面2`
- `カーディガンの曲面3`
- `カーディガンの曲面4`
- `カーディガンの曲面5`
- `シャツ　襟の曲面`
- `シャツ　襟の曲面1`
- `シャツ　襟の曲面2`
- `シャツ　襟の曲面3`
- `シャツ　襟の曲面4`
- `シャツ　襟の曲面5`
- `シャツの曲面`
- `シャツの曲面1`

## Rotation Deformers

- `背景　学校の回転`
- `パジャマ右手２の回転`
- `パジャマ　袖２の回転2`
- `パジャマ　袖２の回転3`
- `パジャマ左手２の回転`
- `パジャマ　袖の回転2`
- `パジャマ　袖の回転3`
- `パジャマ　袖の回転4`
- `パジャマ　袖の回転`
- `パジャマ　袖の回転1`
- `パジャマ左手の回転`
- `右手２の回転`
- `カーディガン　袖２の回転2`
- `カーディガン　袖２の回転3`
- `左手２の回転`
- `カーディガン　袖の回転2`
- `カーディガン　袖の回転3`
- `カーディガン　袖の回転4`
- `カーディガン　袖の回転`
- `カーディガン　袖の回転1`
- `左手の回転`
- `顔の回転`
- `カーディガン　袖２の回転`
- `カーディガン　袖２の回転1`
- `首の回転`
- `パジャマ　袖２の回転1`
- `パジャマ　袖２の回転`

## Interpretation

- This proves CMO3 structure presence, not final visual rig quality.
- It does not replace runtime render checks for keyform motion, draw order under motion, or overhang.
- Part and layer names are extracted dynamically from this CMO3; they are not image-specific hardcoded expectations.

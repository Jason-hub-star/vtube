# CMO3 Structure Report

Generated: 2026-06-06T15:10:21.696Z

Status: **WARN**

Input:

- CMO3: `experiments/reference-model-structure-001/official_samples/extracted/chitose/chitose/chitose_t01.cmo3`
- Size: 27825195 bytes
- SHA256: `1051d748f13f9b61b66e9d5b60aafecc17d3325d7a1c3a98e2339eaec1812c70`

## Checks

| Check | Status | Message |
|---|---:|---|
| main_xml_extracted | PASS | main.xml was extracted from the CAFF archive. |
| artmesh_present | PASS | 79 CArtMeshSource definition(s) found. |
| part_sources_present | PASS | 22 CPartSource definition(s) found. |
| parameters_present | PASS | 33 CParameterSource definition(s) found. |
| required_parameters_present | WARN | Missing configured parameter(s): ParamAngleX, ParamAngleY, ParamAngleZ, ParamEyeLOpen, ParamEyeROpen, ParamEyeBallX, ParamEyeBallY, ParamMouthForm, ParamMouthOpenY, ParamBodyAngleX, ParamBodyAngleY, ParamBodyAngleZ, ParamBreath, ParamHairFront, ParamHairSide, ParamHairBack |
| warp_deformers_present | PASS | 54 CWarpDeformerSource definition(s) found. |
| rotation_deformers_present | PASS | 13 CRotationDeformerSource definition(s) found. |
| keyform_bindings_present | PASS | 175 KeyformBindingSource definition(s) found. |

## Structure Counts

| XML Source | Definitions | References |
|---|---:|---:|
| CArtMeshSource | 79 | 714 |
| CPartSource | 22 | 45 |
| CWarpDeformerSource | 54 | 435 |
| CRotationDeformerSource | 13 | 64 |
| KeyformGridSource | 168 | 289 |
| KeyformBindingSource | 175 | 1402 |
| CParameterSource | 33 | 0 |
| CPhysicsSettingsSource | 2 | 0 |
| CGlueSource | 0 | 0 |
| CClippingMaskSource | 0 | 0 |
| CClippingMaskGuid | 0 | 0 |
| CInvertedMaskSource | 0 | 0 |
| CLayer | 1 | 66 |
| CLayerGroup | 1 | 3 |
| CLayeredImage | 1 | 4 |
| CImageResource | 80 | 197 |
| GEditableMesh2 | 79 | 0 |

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
- `PARAM_SWEAT`
- `PARAM_BODY_ANGLE_X`
- `PARAM_BODY_ANGLE_Y`
- `PARAM_BODY_ANGLE_Z`
- `PARAM_ARM_L_A`
- `PARAM_ARM_R_A`
- `PARAM_ARM_R_B`
- `PARAM_BREATH`
- `PARAM_HAIR_FRONT`
- `PARAM_HAIR_SIDE`
- `PARAM_HAIR_BACK`

## Parts

- `Root Part`
- `[ 下絵 ]`
- `背景`
- `体`
- `右腕B`
- `右腕A`
- `左腕A`
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
- `汗`
- `コア`
- `ラフ`

## ArtMeshes

- `下絵A.png_`
- `下絵B.png_`
- `笑顔.png_`
- `悲しむ.png_`
- `怒る.png_`
- `照れる.png_`
- `困る.png_`
- `驚く.png_`
- `とじ目.png_`
- `開き口1.png_`
- `開き口2.png_`
- `開き口3.png_`
- `反転.png_`

## Warp Deformers

- `パンツの曲面`
- `上着の曲面`
- `右腕Bの曲面`
- `右肘Bの曲面`
- `右手Bの曲面`
- `右腕Aの曲面`
- `右手Aの曲面`
- `左腕Aの曲面`
- `左肘Aの曲面`
- `左手Aの曲面`
- `首の曲面`
- `首の曲面X`
- `後ろ髪の曲面`
- `後ろ髪のZ`
- `後ろ髪の揺れ`
- `前髪の曲面`
- `前髪のZ`
- `前髪の揺れ`
- `前髪てっぺんの曲面`
- `右もみあげの曲面`
- `左もみあげの曲面`
- `前髪てっぺんの揺れ`
- `右耳の曲面`
- `左耳の曲面`
- `鼻の曲面`
- `口の曲面`
- `右まゆ毛の曲面`
- `右まゆ毛の位置`
- `右まゆ毛の角度`
- `右まゆ毛影の位置`
- `左まゆ毛の曲面`
- `左まゆ毛の位置`
- `左まゆ毛の角度`
- `左まゆ毛影の位置`
- `右目玉の曲面`
- `左目玉の曲面`
- `右目玉の縮小`
- `左目玉の縮小`
- `右目玉のハイライト`
- `左目玉のハイライト`
- `右目の曲面`
- `左目の曲面`
- `右目の変形`
- `左目の変形`
- `顔影の曲面`
- `顔影の揺れ`
- `顔影のZ`
- `右頬の曲面`
- `左頬の曲面`
- `汗の曲面`
- `体の回転Z`
- `体の回転Y`
- `呼吸`
- `体の回転X`

## Rotation Deformers

- `右腕Bの位置`
- `右腕Bの回転`
- `右肘Bの回転`
- `右手Bの回転`
- `右腕Aの位置`
- `右腕Aの回転`
- `右手Aの回転`
- `左腕Aの位置`
- `左腕Aの回転`
- `左肘Aの回転`
- `左手Aの回転`
- `首の回転`
- `顔の回転`

## Interpretation

- This proves CMO3 structure presence, not final visual rig quality.
- It does not replace runtime render checks for keyform motion, draw order under motion, or overhang.
- Part and layer names are extracted dynamically from this CMO3; they are not image-specific hardcoded expectations.

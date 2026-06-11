# CMO3 Structure Report

Generated: 2026-06-08T01:24:24.511Z

Status: **WARN**

Input:

- CMO3: `experiments/reference-model-structure-001/official_samples/extracted/tororo_hijiki/tororo_hijiki/hijiki/hijiki_t01.cmo3`
- Size: 4795141 bytes
- SHA256: `bc9da3c44e8f9b82f55f77e4db2e67b36b7fbf492ab7fd88909544627b78996d`

## Checks

| Check | Status | Message |
|---|---:|---|
| main_xml_extracted | PASS | main.xml was extracted from the CAFF archive. |
| artmesh_present | PASS | 57 CArtMeshSource definition(s) found. |
| part_sources_present | PASS | 19 CPartSource definition(s) found. |
| parameters_present | PASS | 31 CParameterSource definition(s) found. |
| required_parameters_present | WARN | Missing configured parameter(s): ParamAngleX, ParamAngleY, ParamAngleZ, ParamEyeLOpen, ParamEyeROpen, ParamEyeBallX, ParamEyeBallY, ParamMouthForm, ParamMouthOpenY, ParamBodyAngleX, ParamBodyAngleY, ParamBodyAngleZ, ParamBreath, ParamHairFront, ParamHairSide, ParamHairBack |
| warp_deformers_present | PASS | 36 CWarpDeformerSource definition(s) found. |
| rotation_deformers_present | PASS | 14 CRotationDeformerSource definition(s) found. |
| keyform_bindings_present | PASS | 121 KeyformBindingSource definition(s) found. |

## Structure Counts

| XML Source | Definitions | References |
|---|---:|---:|
| CArtMeshSource | 57 | 611 |
| CPartSource | 19 | 39 |
| CWarpDeformerSource | 36 | 314 |
| CRotationDeformerSource | 14 | 53 |
| KeyformGridSource | 126 | 214 |
| KeyformBindingSource | 121 | 946 |
| CParameterSource | 31 | 0 |
| CPhysicsSettingsSource | 1 | 0 |
| CGlueSource | 0 | 0 |
| CClippingMaskSource | 0 | 0 |
| CClippingMaskGuid | 0 | 0 |
| CInvertedMaskSource | 0 | 0 |
| CLayer | 1 | 49 |
| CLayerGroup | 1 | 3 |
| CLayeredImage | 1 | 4 |
| CImageResource | 51 | 103 |
| GEditableMesh2 | 57 | 0 |

## Parameters

- `PARAM_ANGLE_X`
- `PARAM_ANGLE_Y`
- `PARAM_ANGLE_Z`
- `PARAM_EYE_L_OPEN`
- `PARAM_EYE_R_OPEN`
- `PARAM_EYE_BALL_X`
- `PARAM_EYE_BALL_Y`
- `PARAM_EYE_FORM`
- `PARAM_MOUTH_FORM`
- `PARAM_MOUTH_OPEN_Y`
- `PARAM_TONGUE`
- `PARAM_EAR_R`
- `PARAM_EAR_R_MOVE`
- `PARAM_EAR_L`
- `PARAM_BODY_ANGLE_X`
- `PARAM_BODY_ANGLE_Y`
- `PARAM_BIG_FACE`
- `PARAM_BODY`
- `PARAM_BREATH`
- `PARAM_BLOW_R`
- `PARAM_BLOW_L`
- `PARAM_TAIL`
- `PARAM_TAIL_ANGRY`
- `PARAM_MUSTACHE_FRONT_R`
- `PARAM_MUSTACHE_FRONT_L`
- `PARAM_HAND_R`
- `PARAM_HAND_L`
- `PARAM_ARM_L`
- `PARAM_HAND_L_MOVE`
- `PARAM_ARM_R_MOVE`
- `ARM_R_MOVE_02`

## Parts

- `Root Part`
- `[ 下絵 ]`
- `背景`
- `しっぽ`
- `体`
- `左腕_02`
- `右腕_02`
- `左腕`
- `右腕`
- `胸`
- `耳`
- `鼻`
- `口`
- `まゆ毛`
- `目玉`
- `目`
- `顔`
- `コアパーツ`
- `ラフ`

## ArtMeshes

- `ねこ下絵.jpg_`
- `しっぽ`
- `しっぽ`
- `左手首_02`
- `左腕上腕_02`
- `左前腕_02`
- `右手首_02`
- `右前腕_02`
- `右腕上腕_02`
- `左手首`
- `左腕上腕`
- `左前腕`
- `右手首`
- `右前腕`
- `右腕上腕`
- `胸`
- `耳裏　R`
- `耳手前　L`
- `耳毛　L`
- `耳ピンク　L`
- `耳裏　L`
- `耳手前　R`
- `耳毛　R`
- `耳ピンク　R`
- `耳裏　R`
- `鼻`
- `上の歯`
- `舌`
- `マズル`
- `下唇`
- `下の歯`
- `口中`
- `アゴ`
- `ハイライト　L`
- `ハイライト　R`
- `黒目　L`
- `黒目　R`
- `睫毛　L`
- `下睫毛　L`
- `上睫毛　L`
- `睫毛　R`
- `下睫毛　R`
- `上睫毛　R`
- `下まぶた　R`
- `上まぶた　R`
- `眼球　R`
- `下まぶた　L`
- `上まぶた　L`
- `眼球　L`
- `顔`

## Warp Deformers

- `しっぽの曲面X`
- `右足の曲面`
- `左足の曲面`
- `体の曲面 Y`
- `体の曲面 X`
- `呼吸の曲面`
- `胸の曲面Z`
- `胸の曲面　前後`
- `胸の曲面XY`
- `胸の曲面X`
- `胸の上下`
- `右耳の曲面`
- `左耳の曲面`
- `鼻の曲面`
- `鼻の曲面　開閉`
- `口の曲面`
- `マズルの曲面`
- `マズルの曲面　開閉`
- `舌の曲面　上下`
- `舌の曲面`
- `右まゆ毛の曲面`
- `左まゆ毛の曲面`
- `右ひげの曲面`
- `左ひげの曲面`
- `右ひげの曲面　開閉`
- `左ひげの曲面　開閉`
- `右目玉の曲面`
- `左目玉の曲面`
- `右ハイライトの曲線`
- `左ハイライトの曲面`
- `右目の曲面`
- `左目の曲面`
- `右目の変形`
- `左目の変形`
- `体の回転Z`
- `体の回転Y`

## Rotation Deformers

- `しっぽの回転`
- `左前腕`
- `左手首の回転`
- `右腕上腕の回転`
- `右前腕の回転`
- `右手首の回転`
- `胸の呼吸`
- `顔の回転Y`
- `顔の角度Z`
- `顔の拡大`
- `顔の回転X`
- `顔の呼吸回転`
- `左腕の回転X`
- `右腕の回転X`

## Interpretation

- This proves CMO3 structure presence, not final visual rig quality.
- It does not replace runtime render checks for keyform motion, draw order under motion, or overhang.
- Part and layer names are extracted dynamically from this CMO3; they are not image-specific hardcoded expectations.

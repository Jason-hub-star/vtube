# CMO3 Structure Report

Generated: 2026-06-05T14:48:25.473Z

Status: **WARN**

Input:

- CMO3: `experiments/reference-model-structure-001/official_samples/extracted/haru/haru/haru_t01.cmo3`
- Size: 11944973 bytes
- SHA256: `d6f2a4a79eb234fb66be1c7eea864d5f382f08c2a36481924436e9c6d3173b5c`

## Checks

| Check | Status | Message |
|---|---:|---|
| main_xml_extracted | PASS | main.xml was extracted from the CAFF archive. |
| artmesh_present | PASS | 114 CArtMeshSource definition(s) found. |
| part_sources_present | PASS | 27 CPartSource definition(s) found. |
| parameters_present | PASS | 33 CParameterSource definition(s) found. |
| required_parameters_present | WARN | Missing configured parameter(s): ParamAngleX, ParamAngleY, ParamAngleZ, ParamEyeLOpen, ParamEyeROpen, ParamEyeBallX, ParamEyeBallY, ParamMouthForm, ParamMouthOpenY, ParamBodyAngleX, ParamBodyAngleY, ParamBodyAngleZ, ParamBreath, ParamHairFront, ParamHairSide, ParamHairBack |
| warp_deformers_present | PASS | 53 CWarpDeformerSource definition(s) found. |
| rotation_deformers_present | PASS | 34 CRotationDeformerSource definition(s) found. |
| keyform_bindings_present | PASS | 267 KeyformBindingSource definition(s) found. |

## Structure Counts

| XML Source | Definitions | References |
|---|---:|---:|
| CArtMeshSource | 114 | 977 |
| CPartSource | 27 | 55 |
| CWarpDeformerSource | 53 | 455 |
| CRotationDeformerSource | 34 | 340 |
| KeyformGridSource | 228 | 437 |
| KeyformBindingSource | 267 | 2223 |
| CParameterSource | 33 | 0 |
| CPhysicsSettingsSource | 2 | 0 |
| CGlueSource | 0 | 0 |
| CClippingMaskSource | 0 | 0 |
| CClippingMaskGuid | 0 | 0 |
| CInvertedMaskSource | 0 | 0 |
| CLayer | 4 | 105 |
| CLayerGroup | 4 | 12 |
| CLayeredImage | 4 | 16 |
| CImageResource | 111 | 220 |
| GEditableMesh2 | 114 | 0 |

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
- `PARAM_TERE`
- `PARAM_BODY_ANGLE_X`
- `PARAM_BODY_ANGLE_Y`
- `PARAM_BODY_ANGLE_Z`
- `PARAM_BREATH`
- `PARAM_ARM_L_A`
- `PARAM_ARM_R_A`
- `PARAM_ARM_L_B`
- `PARAM_ARM_R_B`
- `PARAM_BUST_Y`
- `PARAM_HAIR_FRONT`
- `PARAM_HAIR_BACK`

## Parts

- `Root Part`
- `[ 下絵 ]`
- `背景`
- `２　制服　右腕 B`
- `２　制服　左腕 B`
- `２　制服　右腕 A`
- `２　制服　左腕 A`
- `２　制服`
- `１　ワンピース　右腕 B`
- `１　ワンピース　左腕 B`
- `１　ワンピース　右腕 A`
- `１　ワンピース　左腕 A`
- `１　ワンピース`
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
- `コアパーツ`
- `ラフ`

## ArtMeshes

- `サンプル原画_01.jpg_`
- `ハル_原画_2.jpg_`

## Warp Deformers

- `２　胸部の曲面`
- `２　スカートの曲面`
- `２　胸の揺れ`
- `２　胸の曲面`
- `２　左足の曲面`
- `２　右足の曲面`
- `２　胴の曲面`
- `１　胸部の曲面`
- `１　スカートの曲面`
- `１　胸の揺れ`
- `１　胸の曲面`
- `１　左足の曲面`
- `１　右足の曲面`
- `首の曲面`
- `後ろ髪の曲面`
- `頭頂部の曲面`
- `左後ろ髪の曲面`
- `左後ろ髪の角度Z`
- `右後ろ髪の曲面`
- `右後ろ髪の角度Z`
- `左横髪の曲面`
- `左横髪の角度Z`
- `右横髪の曲面`
- `右横髪の角度Z`
- `前髪の曲面`
- `前髪の角度Z`
- `前髪の揺れ`
- `左耳の曲面`
- `右耳の曲面`
- `鼻の曲面`
- `口の曲面`
- `口内の曲面`
- `左まゆ毛の曲面`
- `左まゆ毛の位置`
- `左まゆ毛の角度`
- `右まゆ毛の曲面`
- `右まゆ毛の位置`
- `右まゆ毛の角度`
- `左目玉の位置`
- `左目玉のハイライト上`
- `左目玉のハイライト下`
- `右目玉の位置`
- `右目玉のハイライト上`
- `右目玉のハイライト下`
- `左目の曲面`
- `左目の変形`
- `右目の曲面`
- `右目の変形`
- `左頬の曲面`
- `右頬の曲面`
- `体の曲面Z`
- `体の曲面Y`
- `呼吸`

## Rotation Deformers

- `２　右腕B上腕の回転`
- `２　右腕B前腕の回転`
- `２　右腕B手首の回転`
- `２　左腕B上腕の回転`
- `２　左腕B前腕の回転`
- `２　左腕B手首の回転`
- `２　右腕A上腕の回転`
- `２　右腕A前腕の回転`
- `２　右腕A手首の回転`
- `２　左腕A上腕の回転`
- `２　左腕A前腕の回転`
- `２　左腕A手首の回転`
- `２　左足の回転`
- `２　右足の回転`
- `A　右腕２上腕の回転`
- `A　右腕２前腕の回転`
- `A　右腕２手首の回転`
- `１　左腕B上腕の回転`
- `１　左腕B前腕の回転`
- `１　左腕B手首の回転`
- `１　右腕A上腕の回転`
- `１　右腕A前腕の回転`
- `１　右腕A手首の回転`
- `１　左腕A上腕の回転`
- `１　左腕A前腕の回転`
- `１　左腕A手首の回転`
- `１　左足の回転`
- `１　右足の回転`
- `首の位置`
- `左腕Aの位置XZ`
- `右腕Aの位置XZ`
- `左腕Bの位置XZ`
- `右腕Bの位置XZ`
- `顔の回転`

## Interpretation

- This proves CMO3 structure presence, not final visual rig quality.
- It does not replace runtime render checks for keyform motion, draw order under motion, or overhang.
- Part and layer names are extracted dynamically from this CMO3; they are not image-specific hardcoded expectations.

# CMO3 Structure Report

Generated: 2026-06-06T15:10:20.717Z

Status: **WARN**

Input:

- CMO3: `experiments/reference-model-structure-001/official_samples/extracted/wanko/wanko/wanko_touch_t01.cmo3`
- Size: 3954855 bytes
- SHA256: `07ee5f56ed4e63a131be0c2585bddaa20c54c7bd004aa2db3ea7f1403fda1649`

## Checks

| Check | Status | Message |
|---|---:|---|
| main_xml_extracted | PASS | main.xml was extracted from the CAFF archive. |
| artmesh_present | PASS | 78 CArtMeshSource definition(s) found. |
| part_sources_present | PASS | 33 CPartSource definition(s) found. |
| parameters_present | PASS | 25 CParameterSource definition(s) found. |
| required_parameters_present | WARN | Missing configured parameter(s): ParamAngleX, ParamAngleY, ParamAngleZ, ParamEyeLOpen, ParamEyeROpen, ParamEyeBallX, ParamEyeBallY, ParamMouthForm, ParamMouthOpenY, ParamBodyAngleX, ParamBodyAngleY, ParamBodyAngleZ, ParamBreath, ParamHairFront, ParamHairSide, ParamHairBack |
| warp_deformers_present | PASS | 28 CWarpDeformerSource definition(s) found. |
| rotation_deformers_present | PASS | 6 CRotationDeformerSource definition(s) found. |
| keyform_bindings_present | PASS | 85 KeyformBindingSource definition(s) found. |

## Structure Counts

| XML Source | Definitions | References |
|---|---:|---:|
| CArtMeshSource | 78 | 480 |
| CPartSource | 33 | 67 |
| CWarpDeformerSource | 28 | 273 |
| CRotationDeformerSource | 6 | 25 |
| KeyformGridSource | 145 | 138 |
| KeyformBindingSource | 85 | 680 |
| CParameterSource | 25 | 0 |
| CPhysicsSettingsSource | 4 | 0 |
| CGlueSource | 0 | 0 |
| CClippingMaskSource | 0 | 0 |
| CClippingMaskGuid | 0 | 0 |
| CInvertedMaskSource | 0 | 0 |
| CLayer | 2 | 45 |
| CLayerGroup | 2 | 6 |
| CLayeredImage | 2 | 8 |
| CImageResource | 49 | 100 |
| GEditableMesh2 | 78 | 0 |

## Parameters

- `PARAM_ANGLE_X`
- `PARAM_ANGLE_Y`
- `PARAM_ANGLE_Z`
- `PARAM_EYE_L_OPEN`
- `PARAM_EYE_R_OPEN`
- `PARAM_MOUTH_FORM`
- `PARAM_MOUTH_OPEN_Y`
- `PARAM_TERE`
- `PARAM_BODY_ANGLE_X`
- `PARAM_BODY_ANGLE_Z`
- `PARAM_BODY_ANGLE_Y`
- `PARAM_BREATH`
- `PARAM_BOWL_LID`
- `PARAM_YUGE_01`
- `PARAM_YUGE_02`
- `PARAM_EFFECT`
- `PARAM_EAR_L`
- `PARAM_EAR_R`
- `PARAM_HAND_L`
- `PARAM_HAND_R`
- `PARAM_SWING`
- `PARAM_BOWL_SWING`
- `PARAM_FACE_01`
- `PARAM_BASE_X`
- `PARAM_BASE_Y`

## Parts

- `Root Part`
- `[ 下絵 ]`
- `背景`
- `お椀`
- `体`
- `耳`
- `鼻`
- `口`
- `まゆ毛`
- `目玉`
- `目`
- `顔`
- `頬`
- `エフェクト`
- `蕎麦６杯目`
- `ベニテングタケ`
- `蕎麦５杯目`
- `しいたけ`
- `みかん`
- `蕎麦４杯目`
- `王冠`
- `まゆげ`
- `蕎麦３杯目`
- `アフロ`
- `リボン`
- `蕎麦２杯目`
- `星`
- `ひげ`
- `蕎麦１杯目`
- `たんぽぽ`
- `コア　アイテム`
- `コア`
- `ラフ`

## ArtMeshes

- `わんこそば素材元.png_`
- `反転.png_`

## Warp Deformers

- `体の曲面`
- `呼吸`
- `体の曲面Z`
- `体の曲面Y`
- `右耳の曲面`
- `左耳の曲面`
- `鼻の曲面`
- `口の曲面`
- `口の変形`
- `右目の曲面`
- `左目の曲面`
- `しわの曲面`
- `左目の変形`
- `右目の変形`
- `あごの曲面`
- `顔の曲面`
- `右頬の曲面`
- `左頬の曲面`
- `アイテム左耳の曲面`
- `アイテム中心の曲面`
- `アイテム頭大の曲面`
- `アイテムおでこの曲面`
- `リボンの曲面`
- `王冠の曲面`
- `しいたけの曲面`
- `全体揺れ`
- `蕎麦の曲面顔`
- `顔の曲面`

## Rotation Deformers

- `お椀の回転`
- `顔の回転`
- `顔の回転1`
- `全体の位置`
- `箸位置の移動`
- `全体の回転`

## Interpretation

- This proves CMO3 structure presence, not final visual rig quality.
- It does not replace runtime render checks for keyform motion, draw order under motion, or overhang.
- Part and layer names are extracted dynamically from this CMO3; they are not image-specific hardcoded expectations.

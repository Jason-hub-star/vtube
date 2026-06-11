# CMO3 Structure Report

Generated: 2026-06-08T01:24:31.900Z

Status: **WARN**

Input:

- CMO3: `experiments/reference-model-structure-001/official_samples/extracted/gantzert_felixander/Gantzert_Felixander/Gantzert_Felixander_t01.cmo3`
- Size: 40753233 bytes
- SHA256: `dd579f1afb7971bea3e414f0848b12e2b463dae4e398cf6c25ba1b8fd037c175`

## Checks

| Check | Status | Message |
|---|---:|---|
| main_xml_extracted | PASS | main.xml was extracted from the CAFF archive. |
| artmesh_present | PASS | 249 CArtMeshSource definition(s) found. |
| part_sources_present | PASS | 21 CPartSource definition(s) found. |
| parameters_present | PASS | 74 CParameterSource definition(s) found. |
| required_parameters_present | WARN | Missing configured parameter(s): ParamAngleX, ParamAngleY, ParamAngleZ, ParamEyeLOpen, ParamEyeROpen, ParamEyeBallX, ParamEyeBallY, ParamMouthForm, ParamMouthOpenY, ParamBodyAngleX, ParamBodyAngleY, ParamBodyAngleZ, ParamBreath, ParamHairFront, ParamHairSide, ParamHairBack |
| warp_deformers_present | PASS | 52 CWarpDeformerSource definition(s) found. |
| rotation_deformers_present | PASS | 38 CRotationDeformerSource definition(s) found. |
| keyform_bindings_present | PASS | 537 KeyformBindingSource definition(s) found. |

## Structure Counts

| XML Source | Definitions | References |
|---|---:|---:|
| CArtMeshSource | 249 | 3234 |
| CPartSource | 21 | 43 |
| CWarpDeformerSource | 52 | 516 |
| CRotationDeformerSource | 38 | 280 |
| KeyformGridSource | 360 | 858 |
| KeyformBindingSource | 537 | 6942 |
| CParameterSource | 74 | 0 |
| CPhysicsSettingsSource | 0 | 0 |
| CGlueSource | 0 | 0 |
| CClippingMaskSource | 0 | 0 |
| CClippingMaskGuid | 0 | 0 |
| CInvertedMaskSource | 0 | 0 |
| CLayer | 140 | 280 |
| CLayerGroup | 1 | 142 |
| CLayeredImage | 1 | 143 |
| CImageResource | 154 | 448 |
| GEditableMesh2 | 249 | 0 |

## Parameters

- `PARAM_ANGLE_X`
- `PARAM_ANGLE_Y`
- `PARAM_ANGLE_Z`
- `PARAM_EYE_L_OPEN`
- `PARAM_EYE_R_OPEN`
- `PARAM_EYE_BALL_X`
- `PARAM_EYE_BALL_Y`
- `PARAM_BROW_FORM`
- `PARAM_MOUTH_FORM`
- `PARAM_MOUTH_OPEN_Y`
- `PARAM_BODY_ANGLE_X`
- `PARAM_BODY_ANGLE_Y`
- `PARAM_BODY_ANGLE_Z`
- `PARAM_BREATH`
- `PARAM_HAIR_FRONT`
- `PARAM_HAIR_SIDE`
- `PARAM_HAIR_BACK`
- `PARAM_HAIR_PLUS`
- `PARAM_BEARD`
- `PARAM_ERI_A`
- `PARAM_ERI_B`
- `PARAM_OUTER_A`
- `PARAM_OUTER_B`
- `PARAM_SUSO_A`
- `PARAM_SUSO_B`
- `PARAM_SUSO_PLUS`
- `PARAM_ARM_R_A`
- `PARAM_ARM_R_B`
- `PARAM_HAND_R`
- `PARAM_ARM_R_ANGLE_A`
- `PARAM_ARM_R_ANGLE_B`
- `PARAM_ARM_R_ANGLE_B_PLUS`
- `PARAM_ARM_R_ANGLE_C`
- `PARAM_ARM_R_ANGLE_D`
- `PARAM_BRADE_AFTER`
- `PARAM_BRADE_AFTER_ONOFF`
- `PARAM_BRADE`
- `PARAM_BRADE_LIGHT`
- `PARAM_ARM_L_A`
- `PARAM_ARM_L_B`
- `PARAM_HAND_L_ANGLE`
- `PARAM_HAND_L`
- `PARAM_DRAGON`
- `PARAM_DRAGON_ANGLE`
- `PARAM_GRAGON_HEAD`
- `PARAM_DRAGON_EYE_OPEN`
- `PARAM_DRAGON_EYE`
- `PARAM_DRAGON_WING`
- `PARAM_DRAGON_WING_B`
- `PARAM_DRAGON_WING_B2`
- `PARAM_DRAGON_WING_B3`
- `PARAM_DRAGON_FOAM`
- `PARAM_DRAGON_HAND`
- `PARAM_DRAGON_LEG`
- `PARAM_DRAGON_TAIL_A`
- `PARAM_DRAGON_TAIL_B`
- `PARAM_DRAGON_TURN`
- `PARAM_DRAGON_TURN_P`
- `PARAM_DRAGON_X`
- `PARAM_DRAGON_Y`
- `PARAM_DRAGON_FIRE_A`
- `PARAM_DRAGON_FIRE_B`
- `PARAM_DRAGON_FIRE`
- `PARAM_DRAGON_FIRE_SIZE`
- `PARAM_DRAGON_FIRE_START`
- `PARAM_DRAGON_FIRE_X`
- `PARAM_DRAGON_FIRE_Y`
- `PARAM_CLOUD_A`
- `PARAM_CLOUD_B`
- `PARAM_CLOUD_C`
- `PARAM_CLOUD_D`
- `PARAM_THUNDER`
- `PARAM_POSITION_X`
- `PARAM_POSITION_Y`

## Parts

- `Root Part`
- `[ 下絵 ]`
- `背景`
- `裾`
- `炎`
- `ドラゴン`
- `剣`
- `左腕`
- `右腕`
- `体`
- `首`
- `後ろ髪`
- `横髪`
- `前髪`
- `鼻`
- `口`
- `まゆ毛`
- `目`
- `顔`
- `コアパーツ`
- `ラフ`

## ArtMeshes

- `雷`
- `雷`
- `雲２E`
- `雲２D`
- `雲２C`
- `雲２B`
- `雲２A`
- `雲１C`
- `雲１B`
- `雲１A`
- `BG`
- `マスク_横裾`
- `左裾1_M`
- `左裾2_M`
- `マスク_右裾`
- `右裾_M`
- `マスク_後ろ裾`
- `後ろ裾_M`
- `左腰結び目`
- `右腰結び目_M`
- `右腰結び目`
- `左裾1`
- `左裾2`
- `右裾`
- `後ろ裾`
- `炎照り返し_右裾`
- `炎照り返し_後ろ裾`
- `炎照り返し_右肩`
- `炎照り返し_剣手前`
- `炎照り返し_剣`
- `炎照り返し_右腕手`
- `炎照り返し_右腕前腕`
- `炎照り返し_右腕上腕`
- `炎照り返し_体`
- `炎照り返し_横髪`
- `炎照り返し_前髪手前`
- `炎照り返し_前髪`
- `炎照り返し_顔`
- `炎照り返し_ドラゴン手前`
- `炎照り返し_ドラゴン首`
- `炎照り返し_ドラゴン奥`
- `竜_火花_溜め用`
- `竜_火花_溜め用`
- `竜_炎4_溜め用`
- `竜_火花`
- `竜_火花`
- `竜_火花`
- `竜_火花`
- `竜_火花`
- `竜_火花`
- `竜_炎4`
- `竜_炎4`
- `竜_炎3_追加`
- `竜_炎3`
- `竜_炎2`
- `竜_炎1`
- `竜_頭_M`
- `竜_胴体2_M`
- `竜_尾1_M`
- `竜_尾2_M`
- `竜_尾3_M`
- `マスク_ドラゴン手前`
- `竜_左手_M`
- `竜_左上腕_M`
- `マスク_ドラゴン首`
- `竜_首1_M`
- `竜_首2_M`
- `マスク_ドラゴン奥`
- `竜_胴体1_M`
- `竜_右上腕_M`
- `竜_右手_M`
- `竜_左手羽先_M`
- `竜_左手羽先`
- `竜_左手羽元_M`
- `竜_左手羽元`
- `竜_頭`
- `竜_目_M`
- `竜_目`
- `竜_左手`
- `竜_左上腕`
- `竜_首1`
- `竜_首2`
- `竜_左親指`
- `竜_胴体1`
- `竜_右羽爪`
- `竜_右手羽元`
- `竜_右手羽先`
- `竜_右羽マスク用_M`
- `竜_右羽マスク用`
- `竜_右上腕`
- `竜_右手`
- `竜_後ろ脚手前`
- `竜_胴体2`
- `竜_尾1`
- `竜_尾2`
- `竜_尾3`
- `竜_後ろ脚奥`
- `竜_右羽爪裏`
- `マスク_剣手前`
- `マスク_剣差分`
- `マスク_剣`
- `差分剣_M`
- `差分剣`
- `残像`
- `剣光２`
- `柄飾り表_M`
- `柄飾り手前_M`
- `柄飾り手前奥_M`
- `刃手前_M`
- `刃奥_M`
- `柄_M`
- `柄飾り奥_M`
- `柄飾り表`
- `柄飾り手前`
- `柄飾り手前奥`
- `刃手前`
- `刃奥`
- `柄`
- `柄飾り裏`
- `柄飾り奥`
- `マスク_左腕`
- `左腕金具_M`
- `左前腕_M`
- `左上腕_M`
- `左親指`
- `左人差し指`
- `左中指`
- `左薬指`
- `左小指`
- `左手`
- `左腕金具`
- `左前腕`
- `左上腕`
- `マスク_右腕上腕`
- `マスク_右腕前腕`
- `マスク_右腕手`
- `右手指マスク用_M`
- `右前腕_M`
- `右腕金具_M`
- `右上腕_M`
- `差分親指_M`
- `差分手前_M`
- `差分前腕_M`
- `差分親指`
- `差分手前`
- `差分前腕`
- `差分手裏`
- `右中指`
- `右人差し指`
- `右薬指`
- `右小指`
- `右手指マスク用`
- `右親指`
- `右手`
- `右腕金具`
- `右前腕`
- `右前腕　裏`
- `右上腕`
- `マスク_右肩`
- `マスク_体`
- `マスク_立ち襟`
- `左襟_M`
- `右襟_M`
- `右袖前_M`
- `左上着_M`
- `右上着_M`
- `左立ち襟1_M`
- `右立ち襟1_M`
- `左内裾_M`
- `左立ち襟1`
- `左立ち襟2`
- `右立ち襟1`
- `右立ち襟2`
- `左襟`
- `右襟`
- `左袖前`
- `右袖前`
- `左上着_左腕マスク用`
- `左上着`
- `左袖後ろ`
- `右上着_右腕マスク用`
- `右上着`
- `胴着`
- `左胸部`
- `右胸部`
- `右内裾`
- `左内裾`
- `腰布`
- `右脚`
- `左脚`
- `ハイネック_M`
- `ハイネック`
- `首`
- `マスク_後ろ髪`
- `後ろ髪1`
- `後ろ髪2`
- `後ろ髪3`
- `後頭部_M`
- `後頭部`
- `マスク_横髪`
- `左前髪2`
- `左前髪3_M`
- `左前髪3`
- `右前髪3`
- `マスク_前髪手前`
- `左前髪1_M`
- `左前髪1`
- `マスク_前髪`
- `左前髪4_M`
- `左前髪4`
- `左生え際`
- `右前髪1_M`
- `右前髪1`
- `右前髪2_M`
- `右前髪2`
- `鼻_M`
- `鼻`
- `上唇`
- `下唇`
- `歯`
- `口内`
- `左口横`
- `眉間_M`
- `左眉`
- `右眉`
- `眉間`
- `左上まつげ`
- `左目じり`
- `左頬_M`
- `左頬`
- `左目元`
- `左ハイライト`
- `左目玉`
- `左白目_M`
- `左白目`
- `右上まつげ`
- `右目じり`
- `右目元`
- `右頬_M`
- `右頬`
- `右ハイライト`
- `右目玉`
- `右白目_M`
- `右白目`
- `マスク_顔`
- `顎鬚1`
- `輪郭_M`
- `輪郭`
- `顎鬚2`

## Warp Deformers

- `裾の曲面`
- `右腰結び目の曲面`
- `左腰結び目の曲面`
- `後ろ裾の曲面`
- `竜の位置Y`
- `竜_反り`
- `竜_胴体の曲面`
- `竜_頭の曲面`
- `竜の角度`
- `竜_右翼の曲面`
- `竜_左翼の曲面`
- `竜_左手の曲面`
- `竜_左上腕の曲面`
- `竜_右手の曲面`
- `竜_右上腕の曲面`
- `竜_尾の曲面`
- `竜_目の位置`
- `剣光の透明度`
- `右前腕の角度`
- `右上腕の曲面`
- `右上腕の角度`
- `差分右手の角度`
- `差分右前腕の角度`
- `右腕振り`
- `腰の曲面`
- `腰布の曲面`
- `胴着の曲面`
- `左上着の揺れ`
- `左上着の曲面`
- `左上着襟の曲面`
- `右上着の揺れ`
- `右上着の曲面`
- `右襟の曲面`
- `右袖後ろの曲面`
- `右袖前の曲面`
- `ハイネックの曲面`
- `後ろ髪の曲面`
- `左襟の曲面`
- `左前髪の曲面`
- `右前髪の曲面`
- `髪追加揺れの曲面 左`
- `髪追加揺れの曲面 右`
- `鼻の曲面`
- `口の曲面`
- `口の変形`
- `まゆ毛の曲面`
- `目の曲面`
- `顔の曲面`
- `ひげの曲面`
- `体の回転Z`
- `体の曲面Y`
- `呼吸`

## Rotation Deformers

- `背景の回転`
- `裾の回転`
- `炎の回転`
- `炎の拡縮`
- `炎の位置`
- `照り返しの位置_右腕`
- `照り返しの位置`
- `竜の位置X`
- `竜の位置`
- `竜の位置回転`
- `竜の回転`
- `竜_左翼の位置`
- `竜_右翼の位置`
- `竜_右腕の回転`
- `竜_左腕の回転`
- `竜_頭の回転`
- `竜_翼の位置`
- `竜_左後ろ脚の回転`
- `竜_右後ろ脚の回転`
- `竜_尾の回転`
- `マスク_剣差分の透明度`
- `マスク_剣の透明度`
- `左腕の位置`
- `左腕の回転`
- `左前腕の回転`
- `左手の回転`
- `右腕の位置`
- `右腕の回転`
- `右手の回転`
- `右手の位置`
- `右前腕の回転`
- `右前腕の位置`
- `腰の回転`
- `右脚の回転`
- `左脚の回転`
- `顔の回転Z`
- `顔の位置`
- `全体の回転`

## Interpretation

- This proves CMO3 structure presence, not final visual rig quality.
- It does not replace runtime render checks for keyform motion, draw order under motion, or overhang.
- Part and layer names are extracted dynamically from this CMO3; they are not image-specific hardcoded expectations.

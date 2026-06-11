# CMO3 Structure Report

Generated: 2026-06-05T14:48:48.750Z

Status: **WARN**

Input:

- CMO3: `experiments/reference-model-structure-001/official_samples/extracted/miku_pro_jp/miku_pro_jp/miku_sample_t05.cmo3`
- Size: 18155959 bytes
- SHA256: `500a6c201878b71a8f8ba655ef584f65b7e7e8240e1cbd282f9554d45b40c287`

## Checks

| Check | Status | Message |
|---|---:|---|
| main_xml_extracted | PASS | main.xml was extracted from the CAFF archive. |
| artmesh_present | PASS | 116 CArtMeshSource definition(s) found. |
| part_sources_present | PASS | 26 CPartSource definition(s) found. |
| parameters_present | PASS | 59 CParameterSource definition(s) found. |
| required_parameters_present | WARN | Missing configured parameter(s): ParamHairSide |
| warp_deformers_present | PASS | 27 CWarpDeformerSource definition(s) found. |
| rotation_deformers_present | PASS | 38 CRotationDeformerSource definition(s) found. |
| keyform_bindings_present | PASS | 233 KeyformBindingSource definition(s) found. |

## Structure Counts

| XML Source | Definitions | References |
|---|---:|---:|
| CArtMeshSource | 116 | 1859 |
| CPartSource | 26 | 53 |
| CWarpDeformerSource | 27 | 262 |
| CRotationDeformerSource | 38 | 188 |
| KeyformGridSource | 229 | 400 |
| KeyformBindingSource | 233 | 1480 |
| CParameterSource | 59 | 0 |
| CPhysicsSettingsSource | 13 | 0 |
| CGlueSource | 22 | 44 |
| CClippingMaskSource | 0 | 0 |
| CClippingMaskGuid | 0 | 0 |
| CInvertedMaskSource | 0 | 0 |
| CLayer | 1 | 84 |
| CLayerGroup | 1 | 3 |
| CLayeredImage | 1 | 4 |
| CImageResource | 88 | 265 |
| GEditableMesh2 | 116 | 0 |

## Parameters

- `ParamAngleX`
- `ParamAngleY`
- `ParamAngleZ`
- `ParamEyeLOpen`
- `ParamEyeLSmile`
- `ParamEyeROpen`
- `ParamEyeRSmile`
- `ParamEyeBallX`
- `ParamEyeBallY`
- `ParamBrowLY`
- `ParamBrowRY`
- `ParamBrowLX`
- `ParamBrowRX`
- `ParamBrowLAngle`
- `ParamBrowRAngle`
- `ParamBrowLForm`
- `ParamBrowRForm`
- `ParamMouthForm`
- `ParamMouthOpenY`
- `ParamCheek`
- `ParamArmL`
- `ParamArmR`
- `ParamBodyAngleX`
- `ParamBodyAngleY`
- `ParamBodyAngleZ`
- `ParamBreath`
- `ParamHairFront`
- `ParamHairBack`
- `ParamHairBackL8`
- `ParamHairBackR6`
- `Param_Angle_Rotation_1_D_HAIR_BACK_10`
- `Param_Angle_Rotation_2_D_HAIR_BACK_10`
- `Param_Angle_Rotation_3_D_HAIR_BACK_10`
- `Param_Angle_Rotation_4_D_HAIR_BACK_10`
- `Param_Angle_Rotation_5_D_HAIR_BACK_10`
- `Param_Angle_Rotation_6_D_HAIR_BACK_10`
- `Param_Angle_Rotation_7_D_HAIR_BACK_10`
- `Param_Angle_Rotation_8_D_HAIR_BACK_10`
- `Param_Angle_Rotation_9_D_HAIR_BACK_10`
- `Param_Angle_Rotation_1_D_HAIR_BACK_00`
- `Param_Angle_Rotation_2_D_HAIR_BACK_00`
- `Param_Angle_Rotation_3_D_HAIR_BACK_00`
- `Param_Angle_Rotation_4_D_HAIR_BACK_00`
- `Param_Angle_Rotation_5_D_HAIR_BACK_00`
- `Param_Angle_Rotation_6_D_HAIR_BACK_00`
- `Param_Angle_Rotation_7_D_HAIR_BACK_00`
- `Param_Angle_Rotation_8_D_HAIR_BACK_00`
- `Param_Angle_Rotation_9_D_HAIR_BACK_00`
- `ParamHairFront2`
- `Param_Angle_Rotation_1_D_BODY_06`
- `Param_Angle_Rotation_2_D_BODY_06`
- `Param_Angle_Rotation_3_D_BODY_06`
- `Param_Angle_Rotation_4_D_BODY_06`
- `Param_Angle_Rotation_5_D_BODY_06`
- `Param_Angle_Rotation_6_D_BODY_06`
- `Param_Angle_Rotation_7_D_BODY_06`
- `Param`
- `Param2`
- `Param3`

## Parts

- `Root Part`
- `足`
- `体`
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
- `頬`
- `ヘッドセット`
- `D_HAIR_BACK_00(回転)`
- `D_HAIR_BACK_00(スキニング)`
- `D_HAIR_BACK_10(回転)`
- `D_HAIR_BACK_10(スキニング)`
- `D_BODY_06(回転)`
- `D_BODY_06(スキニング)`
- `[ 下絵 ]`
- `コアパーツ`
- `背景`

## ArtMeshes

- `下絵.png_`
- `反転下絵.png_`
- `D_HAIR_BACK_00[0]`
- `D_HAIR_BACK_00[1]`
- `D_HAIR_BACK_00[2]`
- `D_HAIR_BACK_00[3]`
- `D_HAIR_BACK_00[4]`
- `D_HAIR_BACK_00[5]`
- `D_HAIR_BACK_00[6]`
- `D_HAIR_BACK_00[7]`
- `D_HAIR_BACK_00[8]`
- `D_HAIR_BACK_10[0]`
- `D_HAIR_BACK_10[1]`
- `D_HAIR_BACK_10[2]`
- `D_HAIR_BACK_10[3]`
- `D_HAIR_BACK_10[4]`
- `D_HAIR_BACK_10[5]`
- `D_HAIR_BACK_10[6]`
- `D_HAIR_BACK_10[7]`
- `D_HAIR_BACK_10[8]`
- `D_BODY_06[0]`
- `D_BODY_06[1]`
- `D_BODY_06[2]`
- `D_BODY_06[3]`
- `D_BODY_06[4]`
- `D_BODY_06[5]`
- `D_BODY_06[6]`
- `<b xs.n="isVisible">true</b>
<b xs.n="isLocked">false</b>
<CPartGuid xs.n="parentGuid" xs.ref="#809" />
<KeyformGridSource xs.n="keyformGridSource" xs.ref="#1884" />
<carray_list xs.n="_extensions" count="3">
<CEditableMeshExtension>
<ACExtension xs.n="super">
<CExtensionGuid xs.n="guid" uuid="480d2a60-956f-4eb1-a7a2-8a02e24ece2e" note="(no debug info)" />
<CArtMeshSource xs.n="_owner" xs.ref="#1886" />
</ACExtension>
<GEditableMesh2 xs.n="editableMesh" nextPointUid="33" useDelaunayTriangulation="false">
<float-array xs.n="point" count="66">1174.6666 1704.0 1306.6666 1696.0 1472.0 1678.6666 1536.0 1810.6666 1592.0 1906.6666 1504.0 1981.3334 1365.3334 2029.3334 1228.0 2036.0 1114.6666 1984.0 1029.3334 1870.6666 1128.0 1786.6666 1436.0 1845.3334 1224.0 1828.0 1322.6666 1848.0 1122.5876 1866.7694 1173.4652 1806.242 1194.8188 1754.6527 1263.272 1765.2915 1314.7361 1772.6594 1372.111 1771.5646 1403.0455 1685.8958 1454.8701 1757.9719 1219.5624 1701.279 1246.7458 1727.4224 1281.1046 1793.1715 1071.9851 1927.3135 1225.7872 1920.9366 1401.9728 1933.9327 1435.0504 2005.2006 1280.3733 1931.991 1342.3591 1931.6931 1177.6119 1894.1877 1088.1307 1820.6094</float-array>
<byte-array xs.n="pointPriority" count="33">20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20</byte-array>
<short-array xs.n="edge" count="160">2 3 3 4 4 5 6 7 7 8 0 10 5 11 4 11 3 11 11 13 12 13 10 14 8 14 9 14 12 14 12 15 10 15 14 15 12 16 0 16 15 16 10 16 1 17 12 17 16 17 13 18 1 18 17 18 11 19 1 19 18 19 13 19 1 20 2 20 19 20 11 21 2 21 20 21 19 21 3 21 0 22 1 22 16 22 16 23 1 23 22 23 17 23 18 24 12 24 17 24 13 24 8 25 9 25 14 25 12 26 7 26 8 26 13 26 6 27 11 27 13 27 5 27 5 28 6 28 27 28 7 29 13 29 26 29 13 30 6 30 29 30 27 30 6 29 12 31 8 31 26 31 14 31 10 32 9 32 14 32</short-array>
<byte-array xs.n="edgePriority" count="80">30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30</byte-array>
<int-array xs.n="pointUid" count="33">0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32</int-array>
<GEditableMeshGuid xs.n="meshGuid" uuid="6b9c3d20-f8fe-47d8-a7fa-851b51801c05" note="(no debug info)" />
<CoordType xs.n="coordType">
<s xs.n="coordName">Basic Coord`
- `* Snapshot`

## Warp Deformers

- `呼吸`
- `体の曲面Z`
- `体の曲面Y`
- `首の曲面`
- `後ろ頭の曲面`
- `おくれ毛の曲面`
- `前髪の曲面`
- `前髪の曲面1`
- `鼻の曲面`
- `口の曲面`
- `口影かぶせの曲面`
- `右まゆ毛の曲面`
- `左まゆ毛の曲面`
- `右まゆ毛の位置`
- `右まゆ毛の角度`
- `左まゆ毛の位置`
- `左まゆ毛の角度`
- `右目玉の曲面`
- `左目玉の曲面`
- `右目の曲面`
- `左目の曲面`
- `髪影の曲面`
- `頬の曲面`
- `前髪の曲面2`
- `スカートの揺れ`
- `スカートの上下`
- `ベルトの揺れ`

## Rotation Deformers

- `右足の回転`
- `左足の回転`
- `左腕の回転`
- `右腕の回転`
- `首の回転`
- `顔の回転`
- `右ツインテの回転Z`
- `右ツインテの回転`
- `左ツインテの回転Z`
- `左ツインテの回転`
- `回転0_D_HAIR_BACK_00`
- `回転1_D_HAIR_BACK_00`
- `回転2_D_HAIR_BACK_00`
- `回転3_D_HAIR_BACK_00`
- `回転4_D_HAIR_BACK_00`
- `回転5_D_HAIR_BACK_00`
- `回転6_D_HAIR_BACK_00`
- `回転7_D_HAIR_BACK_00`
- `回転8_D_HAIR_BACK_00`
- `回転0_D_HAIR_BACK_10`
- `回転1_D_HAIR_BACK_10`
- `回転2_D_HAIR_BACK_10`
- `回転3_D_HAIR_BACK_10`
- `回転4_D_HAIR_BACK_10`
- `回転5_D_HAIR_BACK_10`
- `回転6_D_HAIR_BACK_10`
- `回転7_D_HAIR_BACK_10`
- `回転8_D_HAIR_BACK_10`
- `ネクタイの回転`
- `回転0_D_BODY_06`
- `回転1_D_BODY_06`
- `回転2_D_BODY_06`
- `回転3_D_BODY_06`
- `回転4_D_BODY_06`
- `回転5_D_BODY_06`
- `回転6_D_BODY_06`
- `スカートの位置`
- `ベルトの位置`

## Interpretation

- This proves CMO3 structure presence, not final visual rig quality.
- It does not replace runtime render checks for keyform motion, draw order under motion, or overhang.
- Part and layer names are extracted dynamically from this CMO3; they are not image-specific hardcoded expectations.

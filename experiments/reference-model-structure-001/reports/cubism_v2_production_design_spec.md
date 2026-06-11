# Cubism v2 Production Design Spec

- generated_at: `2026-06-07T22:40:44.432794+00:00`
- schema_version: `2`
- all57_model_count: `57`
- full_structure/runtime_only: `34/23`
- rig_floor_eligible_count: `32`
- rule: Write taxonomy, parameter map, deformer/keyform floor, and physics group plan before generating character art.

## Evidence Sources

| Source | Path |
|---|---|
| `part_taxonomy_matrix` | `all57_part_taxonomy_matrix.json` |
| `parameter_map` | `all57_parameter_map.json` |
| `deformer_keyform_floor` | `all57_deformer_keyform_floor.json` |
| `physics_group_design` | `all57_physics_group_design.json` |
| `strong20_runtime_probe` | `../../live2d-strong-model-pattern-001/reports/strong20_runtime_probe_report.json` |
| `strong20_part_success_patterns` | `../../live2d-strong-model-pattern-001/reports/part_success_patterns.md` |

## Observed Rig Ranges

| Metric | Range |
|---|---|
| `art_meshes` | `{'n': 32, 'min': 33, 'p25': 73.75, 'median': 86.5, 'p75': 155.75, 'max': 299, 'mean': 120.09}` |
| `parts` | `{'n': 32, 'min': 17, 'p25': 21.0, 'median': 22.0, 'p75': 31.5, 'max': 54, 'mean': 26.56}` |
| `parameters` | `{'n': 32, 'min': 25, 'p25': 31.0, 'median': 45.5, 'p75': 70.75, 'max': 138, 'mean': 54.47}` |
| `warp_deformers` | `{'n': 32, 'min': 26, 'p25': 39.0, 'median': 51.0, 'p75': 63.75, 'max': 156, 'mean': 61.81}` |
| `rotation_deformers` | `{'n': 32, 'min': 2, 'p25': 12.75, 'median': 20.0, 'p75': 41.5, 'max': 145, 'mean': 32.53}` |
| `keyform_bindings` | `{'n': 32, 'min': 85, 'p25': 166.25, 'median': 217.5, 'p75': 349.0, 'max': 559, 'mean': 256.31}` |

## Production Tiers

### v2_min

- role: technical gate only; proves real Cubism deformer/keyform/physics authoring, not final beauty
- part_taxonomy: 20-25 source parts, grouped into face, eye L/R, mouth, front/side/back hair, neck, upper body, simple shoulder/arm
- minimum_floor: `{'parameters': 12, 'warp_deformers': 8, 'rotation_deformers': 1, 'keyform_bindings': 20, 'physics_groups': 2}`
- verification: `['CMO3 inspector detects warp increase', 'CMO3 inspector detects keyform increase', 'at least one hair/body physics group renders in runtime']`

### v2_standard

- role: first production candidate default
- part_taxonomy: 50-70 source parts with separated eyes/brows/mouth, front/side/back hair clusters, neck/torso/shoulder/optional arms, underpaint where overhang occurs
- minimum_floor: `{'parameters': 25, 'warp_deformers': 35, 'rotation_deformers': 8, 'keyform_bindings': 120, 'physics_groups': 4}`
- recommended_target: `{'parameters': '35-55', 'warp_deformers': '40-65', 'rotation_deformers': '12-25', 'keyform_bindings': '160-260', 'physics_groups': '4-6'}`
- verification: `['neutral/motion/extreme strip for eye, mouth, hair, body angle', 'G1 taxonomy contact sheet', 'G2 automatic CMO3 PASS/WARN with no zero deformer/keyform regression']`

### v2_rich

- role: official-core-like expression richness after v2_standard passes
- part_taxonomy: 90+ source parts with richer arm/hand, accessory, effect, mask/pose/expression, and split hair physics
- minimum_floor: `{'parameters': 50, 'warp_deformers': 60, 'rotation_deformers': 20, 'keyform_bindings': 220, 'physics_groups': 8}`
- recommended_features: `['at least two of mask, pose, expression, accessory physics, effect secondary motion']`
- verification: `['same v2_standard gates plus expression/pose/mask runtime smoke']`

## v2_standard Production Part Taxonomy

- target_part_count: `50-70 source PSD/material parts`

| Group | Required Parts |
|---|---|
| `face_base` | `['face base', 'left/right cheek or face shadow optional', 'nose optional']` |
| `eye_L` | `['eye white L', 'iris/pupil L', 'upper eyelid/lash L', 'lower eyelid/shadow L']` |
| `eye_R` | `['eye white R', 'iris/pupil R', 'upper eyelid/lash R', 'lower eyelid/shadow R']` |
| `brow_L_R` | `['brow L', 'brow R']` |
| `mouth_group` | `['mouth line', 'mouth inner', 'upper/lower lip or mask', 'teeth/tongue optional']` |
| `hair` | `['front hair clusters 3-8', 'side hair L/R 2-6', 'back hair 2-8', 'long strand groups when present']` |
| `body` | `['neck', 'upper body/torso', 'shoulder L/R', 'simple arm L/R if visible']` |
| `underpaint` | `['face/neck/hair/shoulder underpaint where angle motion exposes gaps']` |
| `deferred_until_v2_rich` | `['complex hands', 'heavy props', 'effect layers', 'skirt/cloth secondary parts unless design requires them']` |

## Parameter Map Detail

| Parameter | Level | Section | Range | Keyforms | Connected Parts | Evidence |
|---|---|---|---|---|---|---|
| `ParamAngleX` | `REQUIRED` | `body_angle` | `[-30, 30]` | `[-30, 0, 30]` | `['face_base', 'eye_L', 'eye_R', 'brow_L_R', 'mouth_group', 'front_hair']` | `models 54, motion 46, top [('ParamAngleX', 31), ('ParamAngleZ', 31), ('ParamAngleY', 26)]` |
| `ParamAngleY` | `REQUIRED` | `body_angle` | `[-30, 30]` | `[-30, 0, 30]` | `['face_base', 'eye_L', 'eye_R', 'mouth_group', 'front_hair', 'neck']` | `models 54, motion 46, top [('ParamAngleX', 31), ('ParamAngleZ', 31), ('ParamAngleY', 26)]` |
| `ParamAngleZ` | `REQUIRED` | `body_angle` | `[-30, 30]` | `[-30, 0, 30]` | `['head_root', 'front_hair', 'side_hair_L', 'side_hair_R']` | `models 54, motion 46, top [('ParamAngleX', 31), ('ParamAngleZ', 31), ('ParamAngleY', 26)]` |
| `ParamBodyAngleX` | `REQUIRED` | `body_angle` | `[-10, 10]` | `[-10, 0, 10]` | `['neck', 'upper_body', 'shoulder_arm']` | `models 54, motion 46, top [('ParamBodyAngleX', 31), ('ParamBodyAngleZ', 31), ('ParamBodyAngleY', 27)]` |
| `ParamBodyAngleY` | `REQUIRED` | `body_angle` | `[-10, 10]` | `[-10, 0, 10]` | `['neck', 'upper_body', 'shoulder_arm']` | `models 54, motion 46, top [('ParamBodyAngleX', 31), ('ParamBodyAngleZ', 31), ('ParamBodyAngleY', 27)]` |
| `ParamBodyAngleZ` | `RECOMMENDED` | `body_angle` | `[-10, 10]` | `[-10, 0, 10]` | `['upper_body', 'shoulder_arm']` | `models 54, motion 46, top [('ParamBodyAngleX', 31), ('ParamBodyAngleZ', 31), ('ParamBodyAngleY', 27)]` |
| `ParamEyeLOpen` | `REQUIRED` | `eye` | `[0, 1]` | `[0, 0.5, 1]` | `['eye_L']` | `models 56, motion 48, top [('ParamEyeLOpen', 33), ('ParamEyeROpen', 33), ('PARAM_EYE_L_OPEN', 23)]` |
| `ParamEyeROpen` | `REQUIRED` | `eye` | `[0, 1]` | `[0, 0.5, 1]` | `['eye_R']` | `models 56, motion 48, top [('ParamEyeLOpen', 33), ('ParamEyeROpen', 33), ('PARAM_EYE_L_OPEN', 23)]` |
| `ParamEyeBallX` | `REQUIRED` | `eye` | `[-1, 1]` | `[-1, 0, 1]` | `['eye_L', 'eye_R']` | `models 51, motion 47, top [('ParamEyeBallX', 31), ('ParamEyeBallY', 31), ('PARAM_EYE_BALL_Y', 20)]` |
| `ParamEyeBallY` | `REQUIRED` | `eye` | `[-1, 1]` | `[-1, 0, 1]` | `['eye_L', 'eye_R']` | `models 51, motion 47, top [('ParamEyeBallX', 31), ('ParamEyeBallY', 31), ('PARAM_EYE_BALL_Y', 20)]` |
| `ParamMouthOpenY` | `REQUIRED` | `mouth` | `[0, 1]` | `[0, 0.5, 1]` | `['mouth_group']` | `models 51, motion 42, top [('ParamMouthOpenY', 25), ('PARAM_MOUTH_FORM', 23), ('PARAM_MOUTH_OPEN_Y', 23)]` |
| `ParamMouthForm` | `REQUIRED` | `mouth` | `[-1, 1]` | `[-1, 0, 1]` | `['mouth_group']` | `models 51, motion 42, top [('ParamMouthOpenY', 25), ('PARAM_MOUTH_FORM', 23), ('PARAM_MOUTH_OPEN_Y', 23)]` |
| `ParamBreath` | `REQUIRED` | `physics` | `[0, 1]` | `[0, 0.5, 1]` | `['upper_body', 'shoulder_arm', 'front_hair']` | `models 49, motion 41, top [('ParamBreath', 26), ('PARAM_BREATH', 23)]` |
| `ParamBrowL/R Angle/Form/Y` | `RECOMMENDED` | `eye` | `[-1, 1]` | `[-1, 0, 1]` | `['brow_L_R']` | `models 39, motion 32, top [('ParamBrowLY', 26), ('ParamBrowRY', 26), ('ParamBrowLForm', 23)]` |
| `ParamHairFront / ParamHairSide / ParamHairBack` | `RECOMMENDED` | `hair` | `[-1, 1]` | `[-1, 0, 1]` | `['front_hair', 'side_hair_L', 'side_hair_R', 'back_hair']` | `models 49, motion 35, top [('ParamHairBack', 26), ('ParamHairFront', 26), ('ParamHairSide', 18)]` |
| `ParamArmL/R or ParamHandL/R` | `OPTIONAL_FOR_V2_STANDARD` | `arm` | `[-1, 1]` | `[-1, 0, 1]` | `['shoulder_arm', 'hand']` | `models 49, motion 46, top [('PARAM_ARM_L', 16), ('PARAM_ARM_R', 14), ('PARAM_HAND_L', 10)]` |
| `ParamA/I/U/E/O` | `OPTIONAL_OR_V2_RICH` | `mouth` | `[0, 1]` | `[0, 1]` | `['mouth_group']` | `models 5, motion 3, top [('ParamA', 5), ('ParamE', 5), ('ParamI', 5)]` |

## Deformer Hierarchy

| Node | Parent | Type | Level | Parameters | Parts | v2_standard Floor | Evidence |
|---|---|---|---|---|---|---|---|
| `root` | `None` | `root/container` | `REQUIRED` | `[]` | `['all visible parts']` | `{'warp_deformers': 0, 'rotation_deformers': 0, 'keyform_bindings': 0}` | `` |
| `body_root_warp` | `root` | `warp` | `REQUIRED` | `['ParamBodyAngleX', 'ParamBodyAngleY', 'ParamBodyAngleZ']` | `['neck', 'upper_body', 'shoulder_arm']` | `{'warp_deformers': 5, 'rotation_deformers': 2, 'keyform_bindings': 45}` | `warp median 7.0, rotation median 2.0, keyform median 63.0` |
| `head_angle_warp` | `body_root_warp` | `warp` | `REQUIRED` | `['ParamAngleX', 'ParamAngleY', 'ParamAngleZ']` | `['face_base', 'eye_L', 'eye_R', 'brow_L_R', 'mouth_group', 'front_hair']` | `{'warp_deformers': 2, 'rotation_deformers': 1, 'keyform_bindings': 18}` | `warp median 7.0, rotation median 2.0, keyform median 63.0` |
| `eye_L_warp` | `head_angle_warp` | `warp` | `REQUIRED` | `['ParamEyeLOpen', 'ParamEyeBallX', 'ParamEyeBallY']` | `['eye_L']` | `{'warp_deformers': 4, 'rotation_deformers': 0, 'keyform_bindings': 15}` | `warp median 12.0, rotation median 0.0, keyform median 42.0` |
| `eye_R_warp` | `head_angle_warp` | `warp` | `REQUIRED` | `['ParamEyeROpen', 'ParamEyeBallX', 'ParamEyeBallY']` | `['eye_R']` | `{'warp_deformers': 4, 'rotation_deformers': 0, 'keyform_bindings': 15}` | `warp median 12.0, rotation median 0.0, keyform median 42.0` |
| `brow_L_R_warp` | `head_angle_warp` | `warp` | `RECOMMENDED` | `['ParamBrowL/R Angle/Form/Y']` | `['brow_L_R']` | `{'warp_deformers': 2, 'rotation_deformers': 0, 'keyform_bindings': 6}` | `warp median 12.0, rotation median 0.0, keyform median 42.0` |
| `mouth_warp` | `head_angle_warp` | `warp` | `REQUIRED` | `['ParamMouthOpenY', 'ParamMouthForm']` | `['mouth_group']` | `{'warp_deformers': 1, 'rotation_deformers': 0, 'keyform_bindings': 6}` | `warp median 1.0, rotation median 0.0, keyform median 8.0` |
| `front_hair_warp` | `head_angle_warp` | `warp` | `REQUIRED` | `['ParamAngleX', 'ParamAngleZ', 'ParamHairFront']` | `['front_hair']` | `{'warp_deformers': 4, 'rotation_deformers': 0, 'keyform_bindings': 3}` | `warp median 11.5, rotation median 0.0, keyform median 5.0` |
| `side_hair_L_R_warp` | `head_angle_warp` | `warp` | `REQUIRED` | `['ParamAngleX', 'ParamAngleZ', 'ParamHairSide']` | `['side_hair_L', 'side_hair_R']` | `{'warp_deformers': 4, 'rotation_deformers': 1, 'keyform_bindings': 3}` | `warp median 11.5, rotation median 0.0, keyform median 5.0` |
| `back_hair_warp` | `body_root_warp` | `warp` | `REQUIRED` | `['ParamBodyAngleX', 'ParamAngleZ', 'ParamHairBack']` | `['back_hair']` | `{'warp_deformers': 2, 'rotation_deformers': 0, 'keyform_bindings': 2}` | `warp median 11.5, rotation median 0.0, keyform median 5.0` |
| `shoulder_arm_rotation` | `body_root_warp` | `rotation` | `OPTIONAL_FOR_V2_STANDARD` | `['ParamArmL/R or ParamHandL/R']` | `['shoulder_arm', 'hand']` | `{'warp_deformers': 2, 'rotation_deformers': 4, 'keyform_bindings': 8}` | `warp median 2.0, rotation median 6.0, keyform median 10.0` |

## Physics Blueprint

- v2_standard_target_group_count: `4-6`
- observed_group_count_stats: `{'n': 44, 'min': 1, 'p25': 3.0, 'median': 6.0, 'p75': 11.0, 'max': 19, 'mean': 7.32}`
- observed_output_category_frequency: `{'hair': 196, 'other': 84, 'accessory': 64, 'effect_expression': 271, 'body_angle': 9, 'arm_hand': 9}`

| Group | Level | Inputs | Outputs | Parts | QA Probe |
|---|---|---|---|---|---|
| `front_hair_physics` | `REQUIRED` | `['ParamAngleX', 'ParamAngleZ', 'ParamBodyAngleX', 'ParamBreath']` | `['ParamHairFront']` | `['front_hair']` | G3 hair motion strip에서 앞머리가 얼굴을 뚫거나 눈을 과하게 덮지 않는지 본다. |
| `side_hair_L_physics` | `REQUIRED` | `['ParamAngleX', 'ParamAngleZ', 'ParamBodyAngleX', 'ParamBreath']` | `['ParamHairSideL 또는 ParamHairSide']` | `['side_hair_L']` | 왼쪽 옆머리의 흔들림과 draw order를 본다. |
| `side_hair_R_physics` | `REQUIRED` | `['ParamAngleX', 'ParamAngleZ', 'ParamBodyAngleX', 'ParamBreath']` | `['ParamHairSideR 또는 ParamHairSide']` | `['side_hair_R']` | 오른쪽 옆머리의 흔들림과 draw order를 본다. |
| `back_hair_physics` | `REQUIRED` | `['ParamBodyAngleX', 'ParamAngleZ', 'ParamBreath']` | `['ParamHairBack']` | `['back_hair']` | 뒷머리가 몸 움직임에 너무 늦거나 빠르게 따라오지 않는지 본다. |
| `body_breath_physics` | `RECOMMENDED` | `['ParamBreath', 'ParamBodyAngleX', 'ParamBodyAngleY']` | `['ParamBodyAngleX/ParamBodyAngleY 보조 또는 전용 sway parameter']` | `['upper_body', 'shoulder_arm', 'neck']` | motion strip에서 몸이 과하게 출렁이지 않는지 본다. |
| `accessory_or_arm_physics` | `OPTIONAL_FOR_V2_STANDARD` | `['ParamAngleX', 'ParamAngleZ', 'ParamBreath']` | `['ParamAccessory* 또는 ParamArm*']` | `['accessory', 'shoulder_arm']` | 장식/팔이 있는 디자인만 확인한다. 없으면 PASS가 아니라 NOT_APPLICABLE로 둔다. |

## G0-G3 Acceptance Checklist

| Gate | Korean Label | Owner | Pass Criteria | Fail Criteria | Issue Tags | Output |
|---|---|---|---|---|---|---|
| `G0_CONCEPT` | 캐릭터 고르기 | `HUMAN` | `['눈, 입, 머리카락, 목/상체가 명확히 보인다.', '팔/장식이 과하게 겹쳐서 필수 파츠 분리를 막지 않는다.', 'v2_standard 50-70 파츠로 나눌 수 있는 디자인이다.']` | `['정면성이 낮다.', '머리/얼굴/몸 경계가 불명확하다.', '스타일이 후보 간 섞여 있다.']` | `['style_mismatch', 'clipping_risk', 'overhang_issue']` | selected_concept_id 또는 REJECT |
| `G1_PART_TAXONOMY` | 파츠가 잘 나뉘었는지 보기 | `HUMAN_PLUS_AUTO` | `['v2_standard 필수 그룹(face/eye L/R/brow/mouth/hair/body/underpaint)이 존재한다.', '각 파츠 alpha가 비어 있지 않고 crop/bbox가 화면 밖으로 잘리지 않는다.', '눈/입/머리카락 파츠가 단독으로 봐도 어느 부위인지 알 수 있다.']` | `['필수 파츠 누락', 'alpha 테두리 오염', '좌우 눈/팔 misalignment', 'underpaint 누락']` | `['missing_part', 'bad_alpha', 'misaligned', 'underpaint_missing', 'draw_order_issue']` | G1_PASS이면 Cubism import pack 작성, 아니면 part regeneration/fix queue |
| `G2_STRUCTURE` | 구조 자동검사 | `AUTO` | `['v2_standard minimum floor: parameters >=25, warp_deformers >=35, rotation_deformers >=8, keyform_bindings >=120, physics_groups >=4', 'eye/mouth/hair/body_angle section keyform evidence가 0으로 퇴행하지 않는다.', 'moc3/model3.json/physics3.json runtime bundle이 로드 가능하다.']` | `['warp/keyform이 0', 'physics group 없음', 'runtime 로드 실패', 'inspector report 없음']` | `['structure_missing', 'deformer_missing', 'keyform_missing', 'physics_missing']` | G2_PASS/WARN/FAIL 자동 판정. 사람이 그림을 고치는 단계가 아니라 Cubism 구조 작업 단계로 되돌린다. |
| `G3_MOTION_VISUAL` | 움직임 확인 | `HUMAN_PLUS_AUTO` | `['neutral, motion, extreme 캡처가 모두 nonblank이다.', '눈 닫힘, 입 열림, 머리카락 흔들림, 몸각도 extreme이 각각 보인다.', 'viewport edge clipping과 심한 draw order 깨짐이 없다.']` | `['모델 미표시', '극단값에서 얼굴/머리카락이 잘림', '눈/입/머리카락 움직임이 보이지 않음']` | `['render_blank', 'viewport_clipping', 'draw_order_issue', 'motion_too_small', 'motion_too_large']` | production candidate PASS/WARN/FAIL 및 수정 대상 파라미터 목록 |
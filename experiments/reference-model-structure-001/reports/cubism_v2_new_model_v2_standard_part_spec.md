# Cubism v2 New Model v2_standard Part Spec

- generated_at: `2026-06-07T22:40:44.695230+00:00`
- status: `SPEC_CONFIRMED`
- target tier: `v2_standard`
- confirmed part count: `64`
- source production spec: `experiments/reference-model-structure-001/reports/cubism_v2_production_design_spec.json`

## Self Review

- status: `PASS`
- counts: `{'parts': 64, 'groups': {'body': 10, 'face_base': 8, 'eye_L': 8, 'eye_R': 8, 'brow': 2, 'mouth': 8, 'hair': 16, 'clothing': 4}, 'underpaint_parts': 9, 'physics_groups': ['back_hair_physics', 'body_breath_physics', 'front_hair_physics', 'side_hair_L_physics', 'side_hair_R_physics'], 'used_parameters': ['ParamAngleX', 'ParamAngleY', 'ParamAngleZ', 'ParamArmL/R or ParamHandL/R', 'ParamBodyAngleX', 'ParamBodyAngleY', 'ParamBreath', 'ParamBrowL/R Angle/Form/Y', 'ParamEyeBallX', 'ParamEyeBallY', 'ParamEyeLOpen', 'ParamEyeROpen', 'ParamHairBack', 'ParamHairFront', 'ParamHairSide', 'ParamMouthForm', 'ParamMouthOpenY']}`

| Check | Result |
|---|---:|
| `production_spec_schema_v2` | `True` |
| `part_count_50_to_70` | `True` |
| `exact_target_count_64` | `True` |
| `no_duplicate_part_ids` | `True` |
| `has_face_base` | `True` |
| `has_eye_L` | `True` |
| `has_eye_R` | `True` |
| `eye_symmetry` | `True` |
| `has_brows` | `True` |
| `has_mouth` | `True` |
| `has_hair` | `True` |
| `has_body_and_simple_arms` | `True` |
| `has_underpaint_parts` | `True` |
| `covers_required_parameters` | `True` |
| `has_v2_standard_physics_groups` | `True` |
| `avoids_v2_rich_scope` | `True` |

## 확정 파츠 목록

| # | Part ID | Group | Korean Label | Deformer | Parameters | Physics | QA Tags |
|---:|---|---|---|---|---|---|---|
| 1 | `body_underpaint` | `body` | 몸 밑색 | `body_root_warp` | `['ParamBodyAngleX', 'ParamBodyAngleY']` | `[]` | `['underpaint_missing']` |
| 2 | `torso_base` | `body` | 상체 기본 | `body_root_warp` | `['ParamBodyAngleX', 'ParamBodyAngleY', 'ParamBreath']` | `['body_breath_physics']` | `[]` |
| 3 | `neck` | `body` | 목 | `body_root_warp` | `['ParamAngleX', 'ParamBodyAngleX', 'ParamBodyAngleY']` | `['body_breath_physics']` | `[]` |
| 4 | `neck_shadow_underpaint` | `body` | 목 그림자 밑색 | `body_root_warp` | `['ParamAngleX', 'ParamBodyAngleX']` | `[]` | `['underpaint_missing']` |
| 5 | `shoulder_L` | `body` | 왼쪽 어깨 | `body_root_warp` | `['ParamBodyAngleX', 'ParamBreath']` | `['body_breath_physics']` | `[]` |
| 6 | `shoulder_R` | `body` | 오른쪽 어깨 | `body_root_warp` | `['ParamBodyAngleX', 'ParamBreath']` | `['body_breath_physics']` | `[]` |
| 7 | `arm_L_upper_simple` | `body` | 왼쪽 간단 팔 | `shoulder_arm_rotation` | `['ParamArmL/R or ParamHandL/R', 'ParamBodyAngleX']` | `[]` | `['misaligned']` |
| 8 | `arm_R_upper_simple` | `body` | 오른쪽 간단 팔 | `shoulder_arm_rotation` | `['ParamArmL/R or ParamHandL/R', 'ParamBodyAngleX']` | `[]` | `['misaligned']` |
| 9 | `arm_L_underpaint` | `body` | 왼팔 밑색 | `shoulder_arm_rotation` | `['ParamBodyAngleX']` | `[]` | `['underpaint_missing']` |
| 10 | `arm_R_underpaint` | `body` | 오른팔 밑색 | `shoulder_arm_rotation` | `['ParamBodyAngleX']` | `[]` | `['underpaint_missing']` |
| 11 | `face_base` | `face_base` | 얼굴 기본 | `head_angle_warp` | `['ParamAngleX', 'ParamAngleY', 'ParamAngleZ']` | `[]` | `[]` |
| 12 | `face_shadow_L` | `face_base` | 왼쪽 얼굴 그림자 | `head_angle_warp` | `['ParamAngleX', 'ParamAngleY']` | `[]` | `[]` |
| 13 | `face_shadow_R` | `face_base` | 오른쪽 얼굴 그림자 | `head_angle_warp` | `['ParamAngleX', 'ParamAngleY']` | `[]` | `[]` |
| 14 | `face_underpaint_L` | `face_base` | 왼쪽 얼굴 밑색 | `head_angle_warp` | `['ParamAngleX']` | `[]` | `['underpaint_missing']` |
| 15 | `face_underpaint_R` | `face_base` | 오른쪽 얼굴 밑색 | `head_angle_warp` | `['ParamAngleX']` | `[]` | `['underpaint_missing']` |
| 16 | `nose` | `face_base` | 코 | `head_angle_warp` | `['ParamAngleX', 'ParamAngleY']` | `[]` | `[]` |
| 17 | `cheek_L` | `face_base` | 왼쪽 볼 | `head_angle_warp` | `['ParamAngleX', 'ParamMouthForm']` | `[]` | `[]` |
| 18 | `cheek_R` | `face_base` | 오른쪽 볼 | `head_angle_warp` | `['ParamAngleX', 'ParamMouthForm']` | `[]` | `[]` |
| 19 | `eye_L_white` | `eye_L` | 왼쪽 눈 흰자 | `eye_L_warp` | `['ParamEyeLOpen', 'ParamEyeBallX', 'ParamEyeBallY']` | `[]` | `['bad_alpha']` |
| 20 | `eye_L_iris` | `eye_L` | 왼쪽 홍채 | `eye_L_warp` | `['ParamEyeLOpen', 'ParamEyeBallX', 'ParamEyeBallY']` | `[]` | `['misaligned']` |
| 21 | `eye_L_pupil` | `eye_L` | 왼쪽 동공 | `eye_L_warp` | `['ParamEyeLOpen', 'ParamEyeBallX', 'ParamEyeBallY']` | `[]` | `['misaligned']` |
| 22 | `eye_L_highlight` | `eye_L` | 왼쪽 눈 하이라이트 | `eye_L_warp` | `['ParamEyeLOpen', 'ParamEyeBallX', 'ParamEyeBallY']` | `[]` | `[]` |
| 23 | `eye_L_upper_lash` | `eye_L` | 왼쪽 위 속눈썹 | `eye_L_warp` | `['ParamEyeLOpen', 'ParamAngleY']` | `[]` | `['draw_order_issue']` |
| 24 | `eye_L_lower_lash` | `eye_L` | 왼쪽 아래 속눈썹 | `eye_L_warp` | `['ParamEyeLOpen', 'ParamAngleY']` | `[]` | `[]` |
| 25 | `eye_L_closed_lid` | `eye_L` | 왼쪽 감은 눈꺼풀 | `eye_L_warp` | `['ParamEyeLOpen']` | `[]` | `['clipping_risk']` |
| 26 | `eye_L_underpaint` | `eye_L` | 왼쪽 눈 밑색 | `eye_L_warp` | `['ParamEyeLOpen', 'ParamAngleX']` | `[]` | `['underpaint_missing']` |
| 27 | `eye_R_white` | `eye_R` | 오른쪽 눈 흰자 | `eye_R_warp` | `['ParamEyeROpen', 'ParamEyeBallX', 'ParamEyeBallY']` | `[]` | `['bad_alpha']` |
| 28 | `eye_R_iris` | `eye_R` | 오른쪽 홍채 | `eye_R_warp` | `['ParamEyeROpen', 'ParamEyeBallX', 'ParamEyeBallY']` | `[]` | `['misaligned']` |
| 29 | `eye_R_pupil` | `eye_R` | 오른쪽 동공 | `eye_R_warp` | `['ParamEyeROpen', 'ParamEyeBallX', 'ParamEyeBallY']` | `[]` | `['misaligned']` |
| 30 | `eye_R_highlight` | `eye_R` | 오른쪽 눈 하이라이트 | `eye_R_warp` | `['ParamEyeROpen', 'ParamEyeBallX', 'ParamEyeBallY']` | `[]` | `[]` |
| 31 | `eye_R_upper_lash` | `eye_R` | 오른쪽 위 속눈썹 | `eye_R_warp` | `['ParamEyeROpen', 'ParamAngleY']` | `[]` | `['draw_order_issue']` |
| 32 | `eye_R_lower_lash` | `eye_R` | 오른쪽 아래 속눈썹 | `eye_R_warp` | `['ParamEyeROpen', 'ParamAngleY']` | `[]` | `[]` |
| 33 | `eye_R_closed_lid` | `eye_R` | 오른쪽 감은 눈꺼풀 | `eye_R_warp` | `['ParamEyeROpen']` | `[]` | `['clipping_risk']` |
| 34 | `eye_R_underpaint` | `eye_R` | 오른쪽 눈 밑색 | `eye_R_warp` | `['ParamEyeROpen', 'ParamAngleX']` | `[]` | `['underpaint_missing']` |
| 35 | `brow_L` | `brow` | 왼쪽 눈썹 | `brow_L_R_warp` | `['ParamBrowL/R Angle/Form/Y', 'ParamAngleX']` | `[]` | `[]` |
| 36 | `brow_R` | `brow` | 오른쪽 눈썹 | `brow_L_R_warp` | `['ParamBrowL/R Angle/Form/Y', 'ParamAngleX']` | `[]` | `[]` |
| 37 | `mouth_line` | `mouth` | 입 선 | `mouth_warp` | `['ParamMouthOpenY', 'ParamMouthForm', 'ParamAngleX']` | `[]` | `['misaligned']` |
| 38 | `mouth_inner` | `mouth` | 입 안쪽 | `mouth_warp` | `['ParamMouthOpenY', 'ParamMouthForm']` | `[]` | `['bad_alpha']` |
| 39 | `mouth_upper_lip_mask` | `mouth` | 윗입술 마스크 | `mouth_warp` | `['ParamMouthOpenY', 'ParamMouthForm']` | `[]` | `['clipping_risk']` |
| 40 | `mouth_lower_lip_mask` | `mouth` | 아랫입술 마스크 | `mouth_warp` | `['ParamMouthOpenY', 'ParamMouthForm']` | `[]` | `['clipping_risk']` |
| 41 | `mouth_teeth` | `mouth` | 치아 | `mouth_warp` | `['ParamMouthOpenY']` | `[]` | `[]` |
| 42 | `mouth_tongue` | `mouth` | 혀 | `mouth_warp` | `['ParamMouthOpenY', 'ParamMouthForm']` | `[]` | `[]` |
| 43 | `mouth_corner_L` | `mouth` | 왼쪽 입꼬리 | `mouth_warp` | `['ParamMouthOpenY', 'ParamMouthForm']` | `[]` | `[]` |
| 44 | `mouth_corner_R` | `mouth` | 오른쪽 입꼬리 | `mouth_warp` | `['ParamMouthOpenY', 'ParamMouthForm']` | `[]` | `[]` |
| 45 | `hair_back_base` | `hair` | 뒷머리 기본 | `back_hair_warp` | `['ParamAngleX', 'ParamAngleZ', 'ParamHairBack']` | `['back_hair_physics']` | `[]` |
| 46 | `hair_back_underpaint` | `hair` | 뒷머리 밑색 | `back_hair_warp` | `['ParamAngleX', 'ParamHairBack']` | `[]` | `['underpaint_missing']` |
| 47 | `hair_back_strand_L` | `hair` | 왼쪽 뒷머리 가닥 | `back_hair_warp` | `['ParamHairBack', 'ParamAngleZ']` | `['back_hair_physics']` | `[]` |
| 48 | `hair_back_strand_R` | `hair` | 오른쪽 뒷머리 가닥 | `back_hair_warp` | `['ParamHairBack', 'ParamAngleZ']` | `['back_hair_physics']` | `[]` |
| 49 | `hair_back_center` | `hair` | 가운데 뒷머리 | `back_hair_warp` | `['ParamHairBack', 'ParamBreath']` | `['back_hair_physics']` | `[]` |
| 50 | `hair_front_center` | `hair` | 가운데 앞머리 | `front_hair_warp` | `['ParamAngleX', 'ParamAngleZ', 'ParamHairFront']` | `['front_hair_physics']` | `['draw_order_issue']` |
| 51 | `hair_front_L` | `hair` | 왼쪽 앞머리 | `front_hair_warp` | `['ParamAngleX', 'ParamAngleZ', 'ParamHairFront']` | `['front_hair_physics']` | `[]` |
| 52 | `hair_front_R` | `hair` | 오른쪽 앞머리 | `front_hair_warp` | `['ParamAngleX', 'ParamAngleZ', 'ParamHairFront']` | `['front_hair_physics']` | `[]` |
| 53 | `hair_front_side_L` | `hair` | 왼쪽 앞 옆머리 | `front_hair_warp` | `['ParamAngleX', 'ParamHairFront']` | `['front_hair_physics']` | `[]` |
| 54 | `hair_front_side_R` | `hair` | 오른쪽 앞 옆머리 | `front_hair_warp` | `['ParamAngleX', 'ParamHairFront']` | `['front_hair_physics']` | `[]` |
| 55 | `hair_front_tip_L` | `hair` | 왼쪽 앞머리 끝 | `front_hair_warp` | `['ParamHairFront', 'ParamAngleZ']` | `['front_hair_physics']` | `[]` |
| 56 | `hair_front_tip_R` | `hair` | 오른쪽 앞머리 끝 | `front_hair_warp` | `['ParamHairFront', 'ParamAngleZ']` | `['front_hair_physics']` | `[]` |
| 57 | `hair_side_L_outer` | `hair` | 왼쪽 바깥 옆머리 | `side_hair_L_R_warp` | `['ParamHairSide', 'ParamAngleX']` | `['side_hair_L_physics']` | `[]` |
| 58 | `hair_side_L_inner` | `hair` | 왼쪽 안쪽 옆머리 | `side_hair_L_R_warp` | `['ParamHairSide', 'ParamAngleX']` | `['side_hair_L_physics']` | `[]` |
| 59 | `hair_side_R_outer` | `hair` | 오른쪽 바깥 옆머리 | `side_hair_L_R_warp` | `['ParamHairSide', 'ParamAngleX']` | `['side_hair_R_physics']` | `[]` |
| 60 | `hair_side_R_inner` | `hair` | 오른쪽 안쪽 옆머리 | `side_hair_L_R_warp` | `['ParamHairSide', 'ParamAngleX']` | `['side_hair_R_physics']` | `[]` |
| 61 | `collar_front` | `clothing` | 앞깃 | `body_root_warp` | `['ParamBodyAngleX', 'ParamBreath']` | `['body_breath_physics']` | `[]` |
| 62 | `collar_shadow` | `clothing` | 깃 그림자 | `body_root_warp` | `['ParamBodyAngleX']` | `[]` | `[]` |
| 63 | `chest_cloth_base` | `clothing` | 가슴 의상 기본 | `body_root_warp` | `['ParamBodyAngleX', 'ParamBreath']` | `['body_breath_physics']` | `[]` |
| 64 | `chest_cloth_shadow` | `clothing` | 가슴 의상 그림자 | `body_root_warp` | `['ParamBodyAngleX']` | `[]` | `[]` |

## Deferred Until v2_rich

- complex hands/fingers
- heavy props
- large effects
- skirt/cloth secondary rig unless design requires it
- ParamA/I/U/E/O vowel rig unless lip-sync becomes a first release requirement

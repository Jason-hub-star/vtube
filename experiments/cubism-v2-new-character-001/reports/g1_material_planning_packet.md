# Cubism v2 G1 Material Planning Packet

- status: `PASS_MATERIAL_PLAN_READY`
- source candidate: `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-001/concepts/g0_adult_cute_female_candidate_002.png`
- taxonomy parts accounted: `64`
- direct extraction total: `46`
- auxiliary generated total: `7`
- underpaint total: `9`
- simplify/merge total: `2`
- initial PSD layer target: `62개 독립 레이어 + 2개 병합/metadata 추적. 필요하면 shadow 2개를 별도 레이어로 되돌려 64개까지 확장.`

## 결정 요약

- 원본에서 보이는 파츠는 46개다. 그중 30개는 바로 분리하고, 16개는 alpha/bbox/경계 정리 후 통과시킨다.
- 단일 PNG에서 보이지 않는 감은 눈, 열린 입 내부, 치아, 혀, 입술 마스크는 보조 생성한다.
- 몸/목/팔/얼굴/눈/뒷머리 밑색은 움직임 빈틈 방지용 underpaint로 만든다.
- 의상 그림자 2개는 처음부터 독립 리깅 파츠로 무리하지 않고 기본 의상 레이어에 병합한다.

## 1. 원본에서 직접 뽑을 파츠

### 1A. 바로 분리

| # | part_id | 그룹 | 한글명 | draw order | 주의 태그 | 제작 액션 |
|---|---|---|---|---|---|---|
| 2 | torso_base | body | 상체 기본 | body_mid | - | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 3 | neck | body | 목 | body_mid | - | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 5 | shoulder_L | body | 왼쪽 어깨 | body_mid | - | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 6 | shoulder_R | body | 오른쪽 어깨 | body_mid | - | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 11 | face_base | face_base | 얼굴 기본 | face_mid | - | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 16 | nose | face_base | 코 | face_front | - | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 19 | eye_L_white | eye_L | 왼쪽 눈 흰자 | eye_back | bad_alpha | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 20 | eye_L_iris | eye_L | 왼쪽 홍채 | eye_mid | misaligned | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 21 | eye_L_pupil | eye_L | 왼쪽 동공 | eye_mid | misaligned | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 22 | eye_L_highlight | eye_L | 왼쪽 눈 하이라이트 | eye_front | - | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 23 | eye_L_upper_lash | eye_L | 왼쪽 위 속눈썹 | eye_front | draw_order_issue | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 24 | eye_L_lower_lash | eye_L | 왼쪽 아래 속눈썹 | eye_front | - | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 27 | eye_R_white | eye_R | 오른쪽 눈 흰자 | eye_back | bad_alpha | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 28 | eye_R_iris | eye_R | 오른쪽 홍채 | eye_mid | misaligned | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 29 | eye_R_pupil | eye_R | 오른쪽 동공 | eye_mid | misaligned | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 30 | eye_R_highlight | eye_R | 오른쪽 눈 하이라이트 | eye_front | - | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 31 | eye_R_upper_lash | eye_R | 오른쪽 위 속눈썹 | eye_front | draw_order_issue | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 32 | eye_R_lower_lash | eye_R | 오른쪽 아래 속눈썹 | eye_front | - | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 45 | hair_back_base | hair | 뒷머리 기본 | hair_back | - | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 50 | hair_front_center | hair | 가운데 앞머리 | hair_front | draw_order_issue | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 51 | hair_front_L | hair | 왼쪽 앞머리 | hair_front | - | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 52 | hair_front_R | hair | 오른쪽 앞머리 | hair_front | - | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 53 | hair_front_side_L | hair | 왼쪽 앞 옆머리 | hair_front | - | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 54 | hair_front_side_R | hair | 오른쪽 앞 옆머리 | hair_front | - | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 57 | hair_side_L_outer | hair | 왼쪽 바깥 옆머리 | hair_side | - | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 58 | hair_side_L_inner | hair | 왼쪽 안쪽 옆머리 | hair_side | - | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 59 | hair_side_R_outer | hair | 오른쪽 바깥 옆머리 | hair_side | - | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 60 | hair_side_R_inner | hair | 오른쪽 안쪽 옆머리 | hair_side | - | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 61 | collar_front | clothing | 앞깃 | clothing_front | - | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |
| 63 | chest_cloth_base | clothing | 가슴 의상 기본 | clothing_mid | - | candidate_002 원본 PNG에서 alpha layer로 직접 분리한다. |

### 1B. 분리하되 정리 필요

| # | part_id | 그룹 | 한글명 | draw order | 주의 태그 | 제작 액션 |
|---|---|---|---|---|---|---|
| 7 | arm_L_upper_simple | body | 왼쪽 간단 팔 | body_front | misaligned | 원본에서 분리하되 bbox/alpha/경계 정리 후 G1 contact sheet에서 재검수한다. |
| 8 | arm_R_upper_simple | body | 오른쪽 간단 팔 | body_front | misaligned | 원본에서 분리하되 bbox/alpha/경계 정리 후 G1 contact sheet에서 재검수한다. |
| 12 | face_shadow_L | face_base | 왼쪽 얼굴 그림자 | face_front | - | 원본에서 분리하되 bbox/alpha/경계 정리 후 G1 contact sheet에서 재검수한다. |
| 13 | face_shadow_R | face_base | 오른쪽 얼굴 그림자 | face_front | - | 원본에서 분리하되 bbox/alpha/경계 정리 후 G1 contact sheet에서 재검수한다. |
| 17 | cheek_L | face_base | 왼쪽 볼 | face_front | - | 원본에서 분리하되 bbox/alpha/경계 정리 후 G1 contact sheet에서 재검수한다. |
| 18 | cheek_R | face_base | 오른쪽 볼 | face_front | - | 원본에서 분리하되 bbox/alpha/경계 정리 후 G1 contact sheet에서 재검수한다. |
| 35 | brow_L | brow | 왼쪽 눈썹 | brow_front | clipping_risk | 원본에서 분리하되 bbox/alpha/경계 정리 후 G1 contact sheet에서 재검수한다. |
| 36 | brow_R | brow | 오른쪽 눈썹 | brow_front | clipping_risk | 원본에서 분리하되 bbox/alpha/경계 정리 후 G1 contact sheet에서 재검수한다. |
| 37 | mouth_line | mouth | 입 선 | mouth_front | misaligned | 원본에서 분리하되 bbox/alpha/경계 정리 후 G1 contact sheet에서 재검수한다. |
| 43 | mouth_corner_L | mouth | 왼쪽 입꼬리 | mouth_front | misaligned | 원본에서 분리하되 bbox/alpha/경계 정리 후 G1 contact sheet에서 재검수한다. |
| 44 | mouth_corner_R | mouth | 오른쪽 입꼬리 | mouth_front | misaligned | 원본에서 분리하되 bbox/alpha/경계 정리 후 G1 contact sheet에서 재검수한다. |
| 47 | hair_back_strand_L | hair | 왼쪽 뒷머리 가닥 | hair_back | draw_order_issue | 원본에서 분리하되 bbox/alpha/경계 정리 후 G1 contact sheet에서 재검수한다. |
| 48 | hair_back_strand_R | hair | 오른쪽 뒷머리 가닥 | hair_back | draw_order_issue | 원본에서 분리하되 bbox/alpha/경계 정리 후 G1 contact sheet에서 재검수한다. |
| 49 | hair_back_center | hair | 가운데 뒷머리 | hair_back | draw_order_issue | 원본에서 분리하되 bbox/alpha/경계 정리 후 G1 contact sheet에서 재검수한다. |
| 55 | hair_front_tip_L | hair | 왼쪽 앞머리 끝 | hair_front | overhang_issue | 원본에서 분리하되 bbox/alpha/경계 정리 후 G1 contact sheet에서 재검수한다. |
| 56 | hair_front_tip_R | hair | 오른쪽 앞머리 끝 | hair_front | overhang_issue | 원본에서 분리하되 bbox/alpha/경계 정리 후 G1 contact sheet에서 재검수한다. |

## 2. 보조 생성할 파츠

| # | part_id | 그룹 | 한글명 | draw order | 주의 태그 | 제작 액션 |
|---|---|---|---|---|---|---|
| 25 | eye_L_closed_lid | eye_L | 왼쪽 감은 눈꺼풀 | eye_front | clipping_risk | 눈 ROI 스타일을 유지해 감은 눈 keypose 파츠로 보조 생성한다. |
| 33 | eye_R_closed_lid | eye_R | 오른쪽 감은 눈꺼풀 | eye_front | clipping_risk | 눈 ROI 스타일을 유지해 감은 눈 keypose 파츠로 보조 생성한다. |
| 38 | mouth_inner | mouth | 입 안쪽 | mouth_back | bad_alpha, clipping_risk | 입 ROI 기반으로 열린 입 내부 keypose 세트를 스타일 맞춰 보조 생성한다. |
| 39 | mouth_upper_lip_mask | mouth | 윗입술 마스크 | mouth_front | bad_alpha, clipping_risk | 입 열림용 마스크/입술 변형 보조 파츠로 생성한다. |
| 40 | mouth_lower_lip_mask | mouth | 아랫입술 마스크 | mouth_front | bad_alpha, clipping_risk | 입 열림용 마스크/입술 변형 보조 파츠로 생성한다. |
| 41 | mouth_teeth | mouth | 치아 | mouth_mid | bad_alpha, clipping_risk | 입 ROI 기반으로 열린 입 내부 keypose 세트를 스타일 맞춰 보조 생성한다. |
| 42 | mouth_tongue | mouth | 혀 | mouth_mid | bad_alpha, clipping_risk | 입 ROI 기반으로 열린 입 내부 keypose 세트를 스타일 맞춰 보조 생성한다. |

## 3. Underpaint 필요한 파츠

| # | part_id | 그룹 | 한글명 | draw order | 주의 태그 | 제작 액션 |
|---|---|---|---|---|---|---|
| 1 | body_underpaint | body | 몸 밑색 | body_back | underpaint_missing | 움직임에서 빈틈이 보이지 않게 원본 주변색 확장, inpaint, 수동 채색으로 만든다. |
| 4 | neck_shadow_underpaint | body | 목 그림자 밑색 | body_back | underpaint_missing | 움직임에서 빈틈이 보이지 않게 원본 주변색 확장, inpaint, 수동 채색으로 만든다. |
| 9 | arm_L_underpaint | body | 왼팔 밑색 | body_back | underpaint_missing | 움직임에서 빈틈이 보이지 않게 원본 주변색 확장, inpaint, 수동 채색으로 만든다. |
| 10 | arm_R_underpaint | body | 오른팔 밑색 | body_back | underpaint_missing | 움직임에서 빈틈이 보이지 않게 원본 주변색 확장, inpaint, 수동 채색으로 만든다. |
| 14 | face_underpaint_L | face_base | 왼쪽 얼굴 밑색 | face_back | underpaint_missing | 움직임에서 빈틈이 보이지 않게 원본 주변색 확장, inpaint, 수동 채색으로 만든다. |
| 15 | face_underpaint_R | face_base | 오른쪽 얼굴 밑색 | face_back | underpaint_missing | 움직임에서 빈틈이 보이지 않게 원본 주변색 확장, inpaint, 수동 채색으로 만든다. |
| 26 | eye_L_underpaint | eye_L | 왼쪽 눈 밑색 | eye_back | underpaint_missing | 움직임에서 빈틈이 보이지 않게 원본 주변색 확장, inpaint, 수동 채색으로 만든다. |
| 34 | eye_R_underpaint | eye_R | 오른쪽 눈 밑색 | eye_back | underpaint_missing | 움직임에서 빈틈이 보이지 않게 원본 주변색 확장, inpaint, 수동 채색으로 만든다. |
| 46 | hair_back_underpaint | hair | 뒷머리 밑색 | hair_back | underpaint_missing | 움직임에서 빈틈이 보이지 않게 원본 주변색 확장, inpaint, 수동 채색으로 만든다. |

## 4. 병합/단순화할 의상 디테일

| # | part_id | 그룹 | 한글명 | draw order | 주의 태그 | 제작 액션 |
|---|---|---|---|---|---|---|
| 62 | collar_shadow | clothing | 깃 그림자 | clothing_mid | - | 처음 PSD에서는 독립 파츠보다 기본 의상 레이어에 병합하고 metadata로만 추적한다. |
| 64 | chest_cloth_shadow | clothing | 가슴 의상 그림자 | clothing_front | - | 처음 PSD에서는 독립 파츠보다 기본 의상 레이어에 병합하고 metadata로만 추적한다. |

## 5. PSD / Material Pack 제작 순서

### P0_source_normalization

- 목표: candidate_002를 2048 full-canvas master로 고정하고 해시/크기/파일명을 기록한다.
- 대상: `none`
- 통과 확인: 원본 PNG, bbox guide, G1 report 경로가 manifest에 연결되어야 한다.

### P1_roi_bbox_lock

- 목표: 눈/입/얼굴/머리/몸 ROI와 guide box를 잠근다.
- 대상: `torso_base, neck, shoulder_L, shoulder_R, face_base, nose, eye_L_white, eye_L_iris, eye_L_pupil, eye_L_highlight, eye_L_upper_lash, eye_L_lower_lash, eye_R_white, eye_R_iris, eye_R_pupil, eye_R_highlight, eye_R_upper_lash, eye_R_lower_lash, hair_back_base, hair_front_center, hair_front_L, hair_front_R, hair_front_side_L, hair_front_side_R, hair_side_L_outer, hair_side_L_inner, hair_side_R_outer, hair_side_R_inner, collar_front, chest_cloth_base, arm_L_upper_simple, arm_R_upper_simple, face_shadow_L, face_shadow_R, cheek_L, cheek_R, brow_L, brow_R, mouth_line, mouth_corner_L, mouth_corner_R, hair_back_strand_L, hair_back_strand_R, hair_back_center, hair_front_tip_L, hair_front_tip_R`
- 통과 확인: mouth corrected ROI를 포함해 주요 그룹 bbox가 비어 있지 않아야 한다.

### P2_direct_visible_extraction

- 목표: 원본에서 보이는 안전 파츠를 full-canvas alpha layer로 분리한다.
- 대상: `torso_base, neck, shoulder_L, shoulder_R, face_base, nose, eye_L_white, eye_L_iris, eye_L_pupil, eye_L_highlight, eye_L_upper_lash, eye_L_lower_lash, eye_R_white, eye_R_iris, eye_R_pupil, eye_R_highlight, eye_R_upper_lash, eye_R_lower_lash, hair_back_base, hair_front_center, hair_front_L, hair_front_R, hair_front_side_L, hair_front_side_R, hair_side_L_outer, hair_side_L_inner, hair_side_R_outer, hair_side_R_inner, collar_front, chest_cloth_base`
- 통과 확인: 각 파츠 alpha bbox가 있고 canvas 크기가 2048x2048이어야 한다.

### P3_direct_risk_cleanup

- 목표: 얇은 선, 머리끝, 팔, 볼/그림자처럼 리스크가 있는 직접 파츠를 정리한다.
- 대상: `arm_L_upper_simple, arm_R_upper_simple, face_shadow_L, face_shadow_R, cheek_L, cheek_R, brow_L, brow_R, mouth_line, mouth_corner_L, mouth_corner_R, hair_back_strand_L, hair_back_strand_R, hair_back_center, hair_front_tip_L, hair_front_tip_R`
- 통과 확인: bad_alpha, crop, style_mismatch, misaligned 후보가 review packet에 표시되어야 한다.

### P4_derived_keypose_generation

- 목표: 감은 눈과 열린 입 내부 keypose 파츠를 보조 생성한다.
- 대상: `eye_L_closed_lid, eye_R_closed_lid, mouth_inner, mouth_upper_lip_mask, mouth_lower_lip_mask, mouth_teeth, mouth_tongue`
- 통과 확인: neutral vs derived 비교에서 위치가 맞고 입/눈 안쪽이 비어 있지 않아야 한다.

### P5_underpaint_generation

- 목표: 움직일 때 구멍이 보이지 않도록 몸/얼굴/눈/머리 밑색을 만든다.
- 대상: `body_underpaint, neck_shadow_underpaint, arm_L_underpaint, arm_R_underpaint, face_underpaint_L, face_underpaint_R, eye_L_underpaint, eye_R_underpaint, hair_back_underpaint`
- 통과 확인: layer alone vs composited 비교에서 underpaint가 밖으로 과하게 삐져나오지 않아야 한다.

### P6_clothing_simplify_merge

- 목표: 작은 의상 그림자는 기본 의상 레이어에 병합하고 별도 리깅 대상에서 제외한다.
- 대상: `collar_shadow, chest_cloth_shadow`
- 통과 확인: 병합한 디테일은 metadata에 남고 독립 deformer/keyform 요구사항으로 올라가지 않아야 한다.

### P7_full_canvas_layer_normalization

- 목표: 모든 결과를 full-canvas PNG/PSD layer 규격으로 맞춘다.
- 대상: `body_underpaint, torso_base, neck, neck_shadow_underpaint, shoulder_L, shoulder_R, arm_L_upper_simple, arm_R_upper_simple, arm_L_underpaint, arm_R_underpaint, face_base, face_shadow_L, face_shadow_R, face_underpaint_L, face_underpaint_R, nose, cheek_L, cheek_R, eye_L_white, eye_L_iris, eye_L_pupil, eye_L_highlight, eye_L_upper_lash, eye_L_lower_lash, eye_L_closed_lid, eye_L_underpaint, eye_R_white, eye_R_iris, eye_R_pupil, eye_R_highlight, eye_R_upper_lash, eye_R_lower_lash, eye_R_closed_lid, eye_R_underpaint, brow_L, brow_R, mouth_line, mouth_inner, mouth_upper_lip_mask, mouth_lower_lip_mask, mouth_teeth, mouth_tongue, mouth_corner_L, mouth_corner_R, hair_back_base, hair_back_underpaint, hair_back_strand_L, hair_back_strand_R, hair_back_center, hair_front_center, hair_front_L, hair_front_R, hair_front_side_L, hair_front_side_R, hair_front_tip_L, hair_front_tip_R, hair_side_L_outer, hair_side_L_inner, hair_side_R_outer, hair_side_R_inner, collar_front, collar_shadow, chest_cloth_base, chest_cloth_shadow`
- 통과 확인: 레이어 이름, alpha bbox, draw order band, source type이 manifest에 있어야 한다.

### P8_psd_layer_order_and_material_pack

- 목표: draw order band에 맞춰 PSD/material pack을 만든다.
- 대상: `body_underpaint, torso_base, neck, neck_shadow_underpaint, shoulder_L, shoulder_R, arm_L_upper_simple, arm_R_upper_simple, arm_L_underpaint, arm_R_underpaint, face_base, face_shadow_L, face_shadow_R, face_underpaint_L, face_underpaint_R, nose, cheek_L, cheek_R, eye_L_white, eye_L_iris, eye_L_pupil, eye_L_highlight, eye_L_upper_lash, eye_L_lower_lash, eye_L_closed_lid, eye_L_underpaint, eye_R_white, eye_R_iris, eye_R_pupil, eye_R_highlight, eye_R_upper_lash, eye_R_lower_lash, eye_R_closed_lid, eye_R_underpaint, brow_L, brow_R, mouth_line, mouth_inner, mouth_upper_lip_mask, mouth_lower_lip_mask, mouth_teeth, mouth_tongue, mouth_corner_L, mouth_corner_R, hair_back_base, hair_back_underpaint, hair_back_strand_L, hair_back_strand_R, hair_back_center, hair_front_center, hair_front_L, hair_front_R, hair_front_side_L, hair_front_side_R, hair_front_tip_L, hair_front_tip_R, hair_side_L_outer, hair_side_L_inner, hair_side_R_outer, hair_side_R_inner, collar_front, collar_shadow, chest_cloth_base, chest_cloth_shadow`
- 통과 확인: Cubism import smoke 전에 PSD layer count와 이름이 spec과 맞아야 한다.

### P9_g1_exit_review_packet

- 목표: 사람은 contact sheet 1장, 실패 후보, derived/underpaint 비교만 본다.
- 대상: `body_underpaint, torso_base, neck, neck_shadow_underpaint, shoulder_L, shoulder_R, arm_L_upper_simple, arm_R_upper_simple, arm_L_underpaint, arm_R_underpaint, face_base, face_shadow_L, face_shadow_R, face_underpaint_L, face_underpaint_R, nose, cheek_L, cheek_R, eye_L_white, eye_L_iris, eye_L_pupil, eye_L_highlight, eye_L_upper_lash, eye_L_lower_lash, eye_L_closed_lid, eye_L_underpaint, eye_R_white, eye_R_iris, eye_R_pupil, eye_R_highlight, eye_R_upper_lash, eye_R_lower_lash, eye_R_closed_lid, eye_R_underpaint, brow_L, brow_R, mouth_line, mouth_inner, mouth_upper_lip_mask, mouth_lower_lip_mask, mouth_teeth, mouth_tongue, mouth_corner_L, mouth_corner_R, hair_back_base, hair_back_underpaint, hair_back_strand_L, hair_back_strand_R, hair_back_center, hair_front_center, hair_front_L, hair_front_R, hair_front_side_L, hair_front_side_R, hair_front_tip_L, hair_front_tip_R, hair_side_L_outer, hair_side_L_inner, hair_side_R_outer, hair_side_R_inner, collar_front, collar_shadow, chest_cloth_base, chest_cloth_shadow`
- 통과 확인: G1 material QA가 PASS해야 Cubism Editor authoring으로 넘어간다.

## 6. Draw Order Band

- `body_back`: body_underpaint, neck_shadow_underpaint, arm_L_underpaint, arm_R_underpaint
- `hair_back`: hair_back_base, hair_back_underpaint, hair_back_strand_L, hair_back_strand_R, hair_back_center
- `body_mid`: torso_base, neck, shoulder_L, shoulder_R
- `body_front`: arm_L_upper_simple, arm_R_upper_simple
- `clothing_mid`: collar_shadow, chest_cloth_base
- `face_back`: face_underpaint_L, face_underpaint_R
- `face_mid`: face_base
- `face_front`: face_shadow_L, face_shadow_R, nose, cheek_L, cheek_R
- `eye_back`: eye_L_white, eye_L_underpaint, eye_R_white, eye_R_underpaint
- `eye_mid`: eye_L_iris, eye_L_pupil, eye_R_iris, eye_R_pupil
- `eye_front`: eye_L_highlight, eye_L_upper_lash, eye_L_lower_lash, eye_L_closed_lid, eye_R_highlight, eye_R_upper_lash, eye_R_lower_lash, eye_R_closed_lid
- `brow_front`: brow_L, brow_R
- `mouth_back`: mouth_inner
- `mouth_mid`: mouth_teeth, mouth_tongue
- `mouth_front`: mouth_line, mouth_upper_lip_mask, mouth_lower_lip_mask, mouth_corner_L, mouth_corner_R
- `hair_side`: hair_side_L_outer, hair_side_L_inner, hair_side_R_outer, hair_side_R_inner
- `hair_front`: hair_front_center, hair_front_L, hair_front_R, hair_front_side_L, hair_front_side_R, hair_front_tip_L, hair_front_tip_R
- `clothing_front`: collar_front, chest_cloth_shadow

## Self Review

| 항목 | 결과 | 근거 |
|---|---:|---|
| 원본에서 직접 뽑을 파츠 목록 확정 | PASS | 직접/위험 직접 46개 = 안전 30개 + 정리 필요 16개 |
| 보조 생성할 파츠 목록 확정 | PASS | 감은 눈/입 내부 keypose 7개 |
| underpaint 필요한 파츠 목록 확정 | PASS | 몸/목/팔/얼굴/눈/뒷머리 밑색 9개 |
| 병합/단순화할 의상 디테일 확정 | PASS | 의상 그림자/작은 디테일 2개 |
| 이후 PSD/material pack 제작 순서 확정 | PASS | 10단계 제작 순서와 draw order band를 생성함 |
| 64파트 taxonomy 전체 accounted | PASS | 46 + 7 + 9 + 2 = 64 |

## 다음 단계

이 패킷이 통과했으므로 다음 작업은 실제 material asset 생성이다. 먼저 direct visible 파츠부터 full-canvas alpha layer로 만들고, 그 다음 derived keypose와 underpaint를 만든다.

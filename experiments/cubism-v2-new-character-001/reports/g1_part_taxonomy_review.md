# Cubism v2 New Character G1 Part Taxonomy Review

- status: `PASS_WITH_DERIVED_PART_REQUIREMENTS`
- image: `experiments/cubism-v2-new-character-001/concepts/g0_adult_cute_female_candidate_002.png`
- visual_guide: `experiments/cubism-v2-new-character-001/reports/g1_part_taxonomy_visual_guide.png`
- total_parts: `64`
- direct_or_risk_visible: `46`
- requires_derived_or_underpaint: `16`
- simplify_or_merge: `2`
- decision: `KEEP_FOR_MATERIAL_PLANNING`

## Feasibility Counts

| Status | Count | Meaning |
|---|---:|---|
| `DERIVED_KEYPOSE_REQUIRED` | 7 | 감은 눈/입 안쪽처럼 보조 keypose 생성 필요 |
| `DIRECT_VISIBLE` | 30 | 원본에서 직접 분리 가능 |
| `DIRECT_VISIBLE_RISK` | 16 | 직접 분리 가능하지만 alpha/draw-order/정렬 주의 |
| `SIMPLIFY_OR_MERGE` | 2 | 첫 production에서는 병합/단순화 권장 |
| `UNDERPAINT_REQUIRED` | 9 | 움직임 빈틈 방지용 밑색 필요 |

## Group Summary

| Group | Counts |
|---|---|
| `body` | DIRECT_VISIBLE=4, DIRECT_VISIBLE_RISK=2, UNDERPAINT_REQUIRED=4 |
| `brow` | DIRECT_VISIBLE_RISK=2 |
| `clothing` | DIRECT_VISIBLE=2, SIMPLIFY_OR_MERGE=2 |
| `eye_L` | DERIVED_KEYPOSE_REQUIRED=1, DIRECT_VISIBLE=6, UNDERPAINT_REQUIRED=1 |
| `eye_R` | DERIVED_KEYPOSE_REQUIRED=1, DIRECT_VISIBLE=6, UNDERPAINT_REQUIRED=1 |
| `face_base` | DIRECT_VISIBLE=2, DIRECT_VISIBLE_RISK=4, UNDERPAINT_REQUIRED=2 |
| `hair` | DIRECT_VISIBLE=10, DIRECT_VISIBLE_RISK=5, UNDERPAINT_REQUIRED=1 |
| `mouth` | DERIVED_KEYPOSE_REQUIRED=5, DIRECT_VISIBLE_RISK=3 |

## Production Notes

- 단일 PNG에서 보이지 않는 mouth inner/teeth/tongue/closed lid/underpaint는 실패가 아니라 보조 생성 대상이다.
- 첫 v2_standard에서는 의상 그림자와 작은 디테일을 과분리하지 말고 base에 병합해도 된다.
- 앞머리와 옆머리 끝단은 G3에서 draw order/overhang을 반드시 확인한다.

## Part Rows

| # | Part | Group | Feasibility | Risks | Note |
|---:|---|---|---|---|---|
| 1 | `body_underpaint` | `body` | `UNDERPAINT_REQUIRED` | underpaint_missing | 움직임에서 빈틈을 막기 위해 원본 기반 확장/수동 밑색이 필요함 |
| 2 | `torso_base` | `body` | `DIRECT_VISIBLE` | - | 목/어깨/상체는 보이며 v2_standard 단순 몸 구조에 적합 |
| 3 | `neck` | `body` | `DIRECT_VISIBLE` | - | 목/어깨/상체는 보이며 v2_standard 단순 몸 구조에 적합 |
| 4 | `neck_shadow_underpaint` | `body` | `UNDERPAINT_REQUIRED` | underpaint_missing | 움직임에서 빈틈을 막기 위해 원본 기반 확장/수동 밑색이 필요함 |
| 5 | `shoulder_L` | `body` | `DIRECT_VISIBLE` | - | 목/어깨/상체는 보이며 v2_standard 단순 몸 구조에 적합 |
| 6 | `shoulder_R` | `body` | `DIRECT_VISIBLE` | - | 목/어깨/상체는 보이며 v2_standard 단순 몸 구조에 적합 |
| 7 | `arm_L_upper_simple` | `body` | `DIRECT_VISIBLE_RISK` | misaligned | 팔은 보이나 가디건 소매와 torso 경계가 합쳐져 단순 팔로 유지 권장 |
| 8 | `arm_R_upper_simple` | `body` | `DIRECT_VISIBLE_RISK` | misaligned | 팔은 보이나 가디건 소매와 torso 경계가 합쳐져 단순 팔로 유지 권장 |
| 9 | `arm_L_underpaint` | `body` | `UNDERPAINT_REQUIRED` | underpaint_missing | 움직임에서 빈틈을 막기 위해 원본 기반 확장/수동 밑색이 필요함 |
| 10 | `arm_R_underpaint` | `body` | `UNDERPAINT_REQUIRED` | underpaint_missing | 움직임에서 빈틈을 막기 위해 원본 기반 확장/수동 밑색이 필요함 |
| 11 | `face_base` | `face_base` | `DIRECT_VISIBLE` | - | 얼굴 기본형은 분리 가능 |
| 12 | `face_shadow_L` | `face_base` | `DIRECT_VISIBLE_RISK` | - | 얼굴/볼 shading은 보이나 별도 파츠로 과분리하면 스타일 mismatch 위험 |
| 13 | `face_shadow_R` | `face_base` | `DIRECT_VISIBLE_RISK` | - | 얼굴/볼 shading은 보이나 별도 파츠로 과분리하면 스타일 mismatch 위험 |
| 14 | `face_underpaint_L` | `face_base` | `UNDERPAINT_REQUIRED` | underpaint_missing | 움직임에서 빈틈을 막기 위해 원본 기반 확장/수동 밑색이 필요함 |
| 15 | `face_underpaint_R` | `face_base` | `UNDERPAINT_REQUIRED` | underpaint_missing | 움직임에서 빈틈을 막기 위해 원본 기반 확장/수동 밑색이 필요함 |
| 16 | `nose` | `face_base` | `DIRECT_VISIBLE` | - | 얼굴 기본형은 분리 가능 |
| 17 | `cheek_L` | `face_base` | `DIRECT_VISIBLE_RISK` | - | 얼굴/볼 shading은 보이나 별도 파츠로 과분리하면 스타일 mismatch 위험 |
| 18 | `cheek_R` | `face_base` | `DIRECT_VISIBLE_RISK` | - | 얼굴/볼 shading은 보이나 별도 파츠로 과분리하면 스타일 mismatch 위험 |
| 19 | `eye_L_white` | `eye_L` | `DIRECT_VISIBLE` | bad_alpha | 눈 흰자/홍채/동공/하이라이트/속눈썹이 비교적 명확함 |
| 20 | `eye_L_iris` | `eye_L` | `DIRECT_VISIBLE` | misaligned | 눈 흰자/홍채/동공/하이라이트/속눈썹이 비교적 명확함 |
| 21 | `eye_L_pupil` | `eye_L` | `DIRECT_VISIBLE` | misaligned | 눈 흰자/홍채/동공/하이라이트/속눈썹이 비교적 명확함 |
| 22 | `eye_L_highlight` | `eye_L` | `DIRECT_VISIBLE` | - | 눈 흰자/홍채/동공/하이라이트/속눈썹이 비교적 명확함 |
| 23 | `eye_L_upper_lash` | `eye_L` | `DIRECT_VISIBLE` | draw_order_issue | 눈 흰자/홍채/동공/하이라이트/속눈썹이 비교적 명확함 |
| 24 | `eye_L_lower_lash` | `eye_L` | `DIRECT_VISIBLE` | - | 눈 흰자/홍채/동공/하이라이트/속눈썹이 비교적 명확함 |
| 25 | `eye_L_closed_lid` | `eye_L` | `DERIVED_KEYPOSE_REQUIRED` | clipping_risk | 정면 open-eye PNG에는 감은 눈꺼풀이 없으므로 blink keypose 생성 필요 |
| 26 | `eye_L_underpaint` | `eye_L` | `UNDERPAINT_REQUIRED` | underpaint_missing | 움직임에서 빈틈을 막기 위해 원본 기반 확장/수동 밑색이 필요함 |
| 27 | `eye_R_white` | `eye_R` | `DIRECT_VISIBLE` | bad_alpha | 눈 흰자/홍채/동공/하이라이트/속눈썹이 비교적 명확함 |
| 28 | `eye_R_iris` | `eye_R` | `DIRECT_VISIBLE` | misaligned | 눈 흰자/홍채/동공/하이라이트/속눈썹이 비교적 명확함 |
| 29 | `eye_R_pupil` | `eye_R` | `DIRECT_VISIBLE` | misaligned | 눈 흰자/홍채/동공/하이라이트/속눈썹이 비교적 명확함 |
| 30 | `eye_R_highlight` | `eye_R` | `DIRECT_VISIBLE` | - | 눈 흰자/홍채/동공/하이라이트/속눈썹이 비교적 명확함 |
| 31 | `eye_R_upper_lash` | `eye_R` | `DIRECT_VISIBLE` | draw_order_issue | 눈 흰자/홍채/동공/하이라이트/속눈썹이 비교적 명확함 |
| 32 | `eye_R_lower_lash` | `eye_R` | `DIRECT_VISIBLE` | - | 눈 흰자/홍채/동공/하이라이트/속눈썹이 비교적 명확함 |
| 33 | `eye_R_closed_lid` | `eye_R` | `DERIVED_KEYPOSE_REQUIRED` | clipping_risk | 정면 open-eye PNG에는 감은 눈꺼풀이 없으므로 blink keypose 생성 필요 |
| 34 | `eye_R_underpaint` | `eye_R` | `UNDERPAINT_REQUIRED` | underpaint_missing | 움직임에서 빈틈을 막기 위해 원본 기반 확장/수동 밑색이 필요함 |
| 35 | `brow_L` | `brow` | `DIRECT_VISIBLE_RISK` | clipping_risk | 눈썹은 보이지만 앞머리와 가까워 draw order와 alpha 분리가 필요 |
| 36 | `brow_R` | `brow` | `DIRECT_VISIBLE_RISK` | clipping_risk | 눈썹은 보이지만 앞머리와 가까워 draw order와 alpha 분리가 필요 |
| 37 | `mouth_line` | `mouth` | `DIRECT_VISIBLE_RISK` | misaligned | 입 선은 보이나 작아 G1 crop과 G3 mouth form에서 위치 보정 필요 |
| 38 | `mouth_inner` | `mouth` | `DERIVED_KEYPOSE_REQUIRED` | bad_alpha, clipping_risk | 현재 미소 입에서는 내부/치아/혀가 충분히 보이지 않아 mouth open keypose 생성 필요 |
| 39 | `mouth_upper_lip_mask` | `mouth` | `DERIVED_KEYPOSE_REQUIRED` | bad_alpha, clipping_risk | 현재 미소 입에서는 내부/치아/혀가 충분히 보이지 않아 mouth open keypose 생성 필요 |
| 40 | `mouth_lower_lip_mask` | `mouth` | `DERIVED_KEYPOSE_REQUIRED` | bad_alpha, clipping_risk | 현재 미소 입에서는 내부/치아/혀가 충분히 보이지 않아 mouth open keypose 생성 필요 |
| 41 | `mouth_teeth` | `mouth` | `DERIVED_KEYPOSE_REQUIRED` | bad_alpha, clipping_risk | 현재 미소 입에서는 내부/치아/혀가 충분히 보이지 않아 mouth open keypose 생성 필요 |
| 42 | `mouth_tongue` | `mouth` | `DERIVED_KEYPOSE_REQUIRED` | bad_alpha, clipping_risk | 현재 미소 입에서는 내부/치아/혀가 충분히 보이지 않아 mouth open keypose 생성 필요 |
| 43 | `mouth_corner_L` | `mouth` | `DIRECT_VISIBLE_RISK` | misaligned | 입 선은 보이나 작아 G1 crop과 G3 mouth form에서 위치 보정 필요 |
| 44 | `mouth_corner_R` | `mouth` | `DIRECT_VISIBLE_RISK` | misaligned | 입 선은 보이나 작아 G1 crop과 G3 mouth form에서 위치 보정 필요 |
| 45 | `hair_back_base` | `hair` | `DIRECT_VISIBLE` | - | 앞머리/옆머리/뒷머리 그룹 경계가 비교적 명확함 |
| 46 | `hair_back_underpaint` | `hair` | `UNDERPAINT_REQUIRED` | underpaint_missing | 움직임에서 빈틈을 막기 위해 원본 기반 확장/수동 밑색이 필요함 |
| 47 | `hair_back_strand_L` | `hair` | `DIRECT_VISIBLE_RISK` | draw_order_issue | 뒷머리는 보이지만 옆머리/앞머리 뒤에 있어 underpaint와 draw order 확인 필요 |
| 48 | `hair_back_strand_R` | `hair` | `DIRECT_VISIBLE_RISK` | draw_order_issue | 뒷머리는 보이지만 옆머리/앞머리 뒤에 있어 underpaint와 draw order 확인 필요 |
| 49 | `hair_back_center` | `hair` | `DIRECT_VISIBLE_RISK` | draw_order_issue | 뒷머리는 보이지만 옆머리/앞머리 뒤에 있어 underpaint와 draw order 확인 필요 |
| 50 | `hair_front_center` | `hair` | `DIRECT_VISIBLE` | draw_order_issue | 앞머리/옆머리/뒷머리 그룹 경계가 비교적 명확함 |
| 51 | `hair_front_L` | `hair` | `DIRECT_VISIBLE` | - | 앞머리/옆머리/뒷머리 그룹 경계가 비교적 명확함 |
| 52 | `hair_front_R` | `hair` | `DIRECT_VISIBLE` | - | 앞머리/옆머리/뒷머리 그룹 경계가 비교적 명확함 |
| 53 | `hair_front_side_L` | `hair` | `DIRECT_VISIBLE` | - | 앞머리/옆머리/뒷머리 그룹 경계가 비교적 명확함 |
| 54 | `hair_front_side_R` | `hair` | `DIRECT_VISIBLE` | - | 앞머리/옆머리/뒷머리 그룹 경계가 비교적 명확함 |
| 55 | `hair_front_tip_L` | `hair` | `DIRECT_VISIBLE_RISK` | overhang_issue | 끝단은 보이나 어깨와 겹쳐 crop/alpha 리스크 있음 |
| 56 | `hair_front_tip_R` | `hair` | `DIRECT_VISIBLE_RISK` | overhang_issue | 끝단은 보이나 어깨와 겹쳐 crop/alpha 리스크 있음 |
| 57 | `hair_side_L_outer` | `hair` | `DIRECT_VISIBLE` | - | 앞머리/옆머리/뒷머리 그룹 경계가 비교적 명확함 |
| 58 | `hair_side_L_inner` | `hair` | `DIRECT_VISIBLE` | - | 앞머리/옆머리/뒷머리 그룹 경계가 비교적 명확함 |
| 59 | `hair_side_R_outer` | `hair` | `DIRECT_VISIBLE` | - | 앞머리/옆머리/뒷머리 그룹 경계가 비교적 명확함 |
| 60 | `hair_side_R_inner` | `hair` | `DIRECT_VISIBLE` | - | 앞머리/옆머리/뒷머리 그룹 경계가 비교적 명확함 |
| 61 | `collar_front` | `clothing` | `DIRECT_VISIBLE` | - | 가디건/블라우스/리본은 보이나 v2_standard에서는 단순 의상 파츠로 제한 |
| 62 | `collar_shadow` | `clothing` | `SIMPLIFY_OR_MERGE` | - | 그림자 전용 파츠는 첫 production에서 base에 병합하거나 최소화 권장 |
| 63 | `chest_cloth_base` | `clothing` | `DIRECT_VISIBLE` | - | 가디건/블라우스/리본은 보이나 v2_standard에서는 단순 의상 파츠로 제한 |
| 64 | `chest_cloth_shadow` | `clothing` | `SIMPLIFY_OR_MERGE` | - | 그림자 전용 파츠는 첫 production에서 base에 병합하거나 최소화 권장 |

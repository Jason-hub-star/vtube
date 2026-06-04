# White Wolf Goth VTuber Concept

이 문서는 주인님이 제공한 흰색 짐승귀 캐릭터 이미지를 참고해 새로 재생성할
Live2D 테스트 컨셉의 기준이다. 원본을 복제하지 않고, 같은 분위기의 새 캐릭터로
재해석한다.

## Concept Summary

- 컨셉명: White Wolf Goth
- 방향: 은백색 장발, 늑대/고양이계 짐승귀, 무표정에 가까운 차분한 인상
- 의상: 검정 민소매 상의, 흰색 털 숄/재킷, 금색 초커와 작은 장식
- 팔레트: 은백색, 차콜 블랙, 따뜻한 금색, 옅은 회색, 아주 약한 핑크 피부 톤
- 용도: Live2D/Cubism 파츠 순도 검증용 새 canonical과 PSD 재생성 테스트

## Must Keep

- 정면 또는 거의 정면 얼굴
- 양쪽 눈이 모두 보이는 구조
- 입은 기본 닫힌 상태
- 머리카락이 눈/속눈썹을 지나치게 덮지 않는 구조
- 짐승귀가 머리카락과 구분되는 실루엣
- 흰 털 숄은 의상과 분리 가능한 덩어리
- 2048x2048 canonical master

## Must Avoid

- 원본 이미지와 동일한 디자인 복제
- 손, 팔, 소품이 얼굴/입/눈을 가리는 포즈
- 머리카락이 홍채/동공/흰자를 가로지르는 구조
- 털 숄과 머리카락 경계가 지나치게 섞이는 구조
- 복잡한 레이스, 작은 체인, 많은 장식처럼 초기 PSD 분리에 불리한 요소
- 비대칭 포즈가 큰 어깨/몸통 구조

## Canonical Prompt Direction

```text
front-facing original 2D anime VTuber character, silver white long hair,
wolf-like animal ears, calm cool expression, black gothic sleeveless top,
white fluffy fur shoulder wrap, small gold choker ornaments, clean line art,
separated readable silhouette, both eyes visible, closed neutral mouth,
transparent or simple background, Live2D model sheet friendly, high resolution
```

Negative direction:

```text
no copied existing character, no busy jewelry, no hands covering face,
no hair covering pupils, no merged fur and hair, no cropped head,
no extreme pose, no painterly background, no extra characters
```

## Initial Production Parts

기존 27개 파츠를 기본으로 사용하되, 이 컨셉은 귀와 털 숄 때문에 다음 파츠를
추가 후보로 둔다.

### Required v1 Additions

| Part ID | Korean name | Reason |
| --- | --- | --- |
| `L_ear_outer` | 왼쪽 귀 바깥 | 머리카락과 따로 흔들릴 수 있음 |
| `R_ear_outer` | 오른쪽 귀 바깥 | 머리카락과 따로 흔들릴 수 있음 |
| `L_ear_inner` | 왼쪽 귀 안쪽 | 귀 내부 색/그림자 분리 |
| `R_ear_inner` | 오른쪽 귀 안쪽 | 귀 내부 색/그림자 분리 |
| `L_fur_shoulder` | 왼쪽 어깨 털 | 의상/머리카락과 오염 가능성이 큼 |
| `R_fur_shoulder` | 오른쪽 어깨 털 | 의상/머리카락과 오염 가능성이 큼 |
| `choker` | 초커 | 목/의상/장식과 분리 |
| `gold_ornaments` | 금색 장식 | 작지만 색상 분리가 쉬움 |

### Conditional Split Candidates

- `front_hair_center`, `front_hair_L`, `front_hair_R`
- `L_long_side_hair`, `R_long_side_hair`
- `back_hair_upper`, `back_hair_lower`
- `fur_shadow`, `fur_highlight`
- `upper_lip_line`, `lower_lip_line`
- `L_ear_shadow`, `R_ear_shadow`

## Review Focus

검수 페이지에서 특히 확인할 것:

- `R_upper_lash`, `L_upper_lash`: 은발 앞머리 픽셀이 섞이면 실패
- `L/R_eye_white`, `L/R_iris`, `L/R_pupil`: 눈 파츠끼리 섞이면 실패
- `L/R_ear_outer`: 머리카락 또는 피부가 붙어 있으면 수정
- `L/R_fur_shoulder`: 머리카락, 피부, 검정 의상이 섞이면 수정 또는 실패
- `front_hair`: 귀 내부/눈/얼굴 피부가 같이 들어가면 수정
- `mouth_inner`: 열린 입 reference가 아니라 production 입 안쪽만 포함

## Acceptance For Concept Test

- `canonical_front_2048.png`가 생성되어 있다.
- concept-specific part schema가 문서화되어 있다.
- `review_app`에서 새 컨셉 canonical과 후보 파츠를 볼 수 있다.
- `O/X/REVISE` 저장 시 `concept-regeneration-001/reports/ai_fix_queue.json`이 생성된다.
- PSD 재생성은 검수 통과 파츠만 대상으로 한다.
- 최종 PSD는 Cubism Editor 실제 import smoke를 남긴다.

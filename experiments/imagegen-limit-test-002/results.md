# imagegen VTuber 파츠 생성 한계 테스트 002 결과

작성일: 2026-06-02

## 생성 이미지

```text
generated/no_label_full_parts_sheet.png
generated/individual_eye_parts.png
generated/individual_mouth_parts.png
generated/individual_underpaint_parts.png
```

## 핵심 결론

```text
라벨 없는 생성은 라벨 오타/텍스트 오염 문제를 크게 줄인다.
전체 파츠 시트보다 파츠군별 개별 생성이 더 실용적이다.
눈/입/underpaint는 개별 생성했을 때 crop/mask 후보로 충분히 쓸 만하다.
imagegen 결과는 여전히 최종 레이어가 아니라 candidate로만 써야 한다.
```

## Test A: no_label_full_parts_sheet

### 관찰

```text
1차 parts_sheet보다 명확히 좋아졌다.
텍스트/라벨 오염이 줄어들어 crop/mask 후보로 쓰기 쉬워졌다.
하지만 너무 많은 파츠를 한 장에 요구하면 일부 파츠가 누락되거나 형태가 단순화된다.
canonical 캐릭터와 세부 의상/선 굵기가 완전히 같지는 않다.
```

### 판정

```text
용도: 전체 파츠 목록을 빠르게 훑는 후보 시트
채택: 참고용 또는 일부 crop 후보
위험: 최종 파츠 일관성은 부족
```

## Test B: individual_eye_parts

### 관찰

```text
전체 시트보다 좌우 눈 구조가 좋다.
눈 흰자, 홍채, 동공, 하이라이트, 속눈썹, 눈썹이 분리 후보로 잘 나온다.
여전히 좌우가 완전히 수학적으로 대칭은 아니다.
눈 파츠는 alpha crop + 좌우 보정 후 MVP 후보로 사용할 수 있다.
```

### 판정

```text
용도: 실제 파츠 후보로 유용
채택: crop/mask 후 사용 가능성 높음
위험: canonical 얼굴에 맞는 위치/크기 보정 필요
```

## Test C: individual_mouth_parts

### 관찰

```text
가장 실용적인 결과 중 하나다.
닫힌 입, 열린 입, 치아, 혀, 그림자, O-mouth, ah-mouth가 명확하다.
입 파츠는 원본 얼굴 위에 합성하기 쉬운 형태다.
표정/립싱크 후보로 사용 가능성이 높다.
```

### 판정

```text
용도: 실제 파츠 후보로 매우 유용
채택: crop/mask 후 우선 테스트 대상
위험: 원본 얼굴의 입 위치/비율과 맞추는 보정 필요
```

## Test D: individual_underpaint_parts

### 관찰

```text
underpaint 개별 생성은 매우 유용하다.
앞머리 뒤 이마, 머리 뒤 패치, 입안, 치아, 혀, 목 패치가 후보로 잘 나온다.
원본에 없는 영역을 새로 그리는 작업에는 imagegen이 강하다.
다만 canonical_front와 직접 합성하려면 색상/비율/경계 보정이 필요하다.
```

### 판정

```text
용도: underpaint 후보로 매우 유용
채택: crop/mask/색상 보정 후 사용 가능성 높음
위험: canonical과 경계가 어긋나면 티가 남
```

## 1차 테스트 대비 개선점

```text
라벨을 금지하면 텍스트 오염이 크게 줄어든다.
전체 시트보다 파츠군별 생성이 더 안정적이다.
입/눈/underpaint는 개별 생성 전략이 맞다.
한 번에 너무 많은 파츠를 요구하면 누락/단순화가 생긴다.
```

## 플랜 반영 사항

```text
imagegen parts는 전체 시트보다 파츠군별 생성으로 설계한다.
프롬프트에는 no text/no labels/no letters/no numbers를 기본 규칙으로 넣는다.
parts_face, parts_mouth, parts_hair, parts_body, underpaint를 따로 생성한다.
각 생성 결과는 candidate로 저장하고 evaluate 단계를 반드시 통과해야 한다.
```

## 다음 실험

```text
1. crop/mask 자동화 테스트
2. canonical_front 위에 mouth parts를 합성하는 테스트
3. canonical_front 위에 eye parts를 합성하는 테스트
4. underpaint patch를 원본에 합성하는 테스트
5. 여러 번 생성했을 때 같은 파츠군의 안정성 비교
```


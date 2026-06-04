# imagegen VTuber 파츠 생성 한계 테스트 001 결과

작성일: 2026-06-02

## 실행한 테스트

```text
Test A: canonical_front 생성
Test B: 같은 캐릭터의 parts_sheet 생성
Test C: 같은 캐릭터의 underpaint_sheet 생성
```

## Test A: canonical_front

### 관찰

```text
정면 반신 캐릭터 생성은 성공적이다.
흰 배경, 선명한 실루엣, 눈/앞머리/의상 구조가 잘 보인다.
앞머리, 긴 뒷머리, 손, 상의, 리본 등 파츠 분리 후보가 명확하다.
```

### 판정

```text
용도: canonical source로 사용 가능
후처리: 배경 제거, alpha mask, 파츠 분리 필요
위험: 손/팔은 간단한 sprite transform용으로는 복잡할 수 있음
```

## Test B: parts_sheet

### 관찰

```text
눈, 입, 머리, 몸, 의상 파츠를 격자로 분리해 생성하는 데 성공했다.
대부분의 파츠는 후보 이미지로 쓸 수 있다.
라벨 오타가 발생했다. 예: TEETH 계열 오타.
좌우 눈/속눈썹 파츠의 형태가 완전히 대칭/일관되지는 않다.
canonical_front와 의상 디테일이 일부 달라졌다.
파츠가 실제 alpha layer로 바로 쓰기에는 흰 배경에 붙어 있고, 정확한 crop/mask가 필요하다.
```

### 판정

```text
용도: part candidate sheet로 사용 가능
후처리: label 제거, crop, alpha mask, canonical 색상/선 굵기 보정 필요
위험: 그대로 PSD 레이어로 쓰면 일관성 문제와 좌우 불균형이 생김
```

## Test C: underpaint_sheet

### 관찰

```text
앞머리 없는 얼굴, 이마 패치, 머리 뒤쪽, 눈 흰자 확장, 입안, 목, 몸통 패치를 생성했다.
underpaint 용도에는 parts_sheet보다 더 유용하다.
입안 내부, 치아, 혀, 눈 흰자 확장 영역은 명확하게 나왔다.
하지만 canonical_front와 얼굴 표정/눈 모양이 다소 달라졌다.
몸통/어깨 패치는 원본 의상 구조와 직접 맞물리지는 않는다.
```

### 판정

```text
용도: underpaint 후보로 사용 가능
후처리: canonical_front 기준 위치/색상/형태 보정 필요
위험: 원본과 직접 합성하면 경계/비율 차이가 보일 수 있음
```

## imagegen에 맡길 수 있는 일

```text
canonical 정면 원화 생성
표정/헤어/의상 참고 시트 생성
파츠 후보 시트 생성
underpaint 후보 생성
입안/눈 흰자/이마/목 같은 숨은 영역 보충
Codex가 crop/mask할 수 있는 후보 이미지 생성
```

## imagegen에 맡기면 위험한 일

```text
최종 PSD 레이어 자동 생성
정확한 alpha segmentation
좌우 완전 대칭 파츠 생성
canonical과 100% 일관된 파츠 생성
라벨 없는 완벽한 production asset sheet 생성
Live2D ArtMesh/deformer/parameter 생성
```

## MVP 플랜에 반영할 결론

```text
imagegen은 완성 파츠 생성기가 아니라 후보 생성기다.
parts_sheet는 바로 쓰는 것이 아니라 crop/mask/검수 대상이다.
underpaint는 imagegen 활용 가치가 높다.
파츠 일관성은 Codex가 canonical_front 기준으로 비교하고 리포트해야 한다.
문서와 CLI에 imagegen 결과 검수 단계를 추가해야 한다.
```

## 다음 실험

```text
1. 라벨 없는 parts_sheet 생성 테스트
2. 한 파츠씩 개별 생성 테스트
3. canonical_front를 기준으로 eye/mouth/hair만 재생성하는 편집 테스트
4. 생성 결과를 자동 crop/mask할 수 있는지 이미지 후처리 스크립트 테스트
```


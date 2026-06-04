# imagegen VTuber 파츠 생성 한계 테스트 002

작성일: 2026-06-02

## 목적

1차 테스트에서 imagegen은 완성 파츠보다 후보 파츠와 underpaint 생성에 더 적합하다는 결론이 나왔다.

2차 테스트에서는 아래 질문을 검증한다.

```text
1. 라벨 없는 parts sheet를 만들면 오타/텍스트 오염 문제가 줄어드는가
2. 전체 파츠 시트보다 한 파츠군씩 개별 생성하는 것이 일관성이 좋은가
3. underpaint는 개별 생성할수록 실제 합성 후보로 좋아지는가
4. 생성 결과를 crop/mask 후보로 쓸 수 있을 만큼 배경과 파츠가 분리되는가
```

## 테스트 목록

```text
Test A: no_label_full_parts_sheet
Test B: individual_eye_parts
Test C: individual_mouth_parts
Test D: individual_underpaint_parts
```

## 공통 캐릭터 기준

```text
anime female VTuber
dark navy long hair
three distinct front bang chunks
small ahoge
golden eyes
black-and-white cropped jacket
teal ribbon at collar
clean cel shading
plain white background
front-facing Live2D production asset style
```

## 판정 기준

```text
텍스트/라벨 오염 여부
canonical 캐릭터와의 일관성
파츠 간 겹침 여부
흰 배경에서 crop/mask 가능성
좌우 파츠의 대칭성
underpaint 합성 가능성
```


# coordinate-align-001

작성일: 2026-06-02

## 목적

스크린샷을 AI가 직접 보고 감으로 위치를 조정하는 대신, 스크립트가 좌표와 마스크 수치로 eye/mouth 후보를 자동 정렬할 수 있는지 검증한다.

## 입력

```text
canonical:
  /Users/family/jason/Vtube/experiments/imagegen-limit-test-001/generated/canonical_front.png

candidate crops:
  /Users/family/jason/Vtube/experiments/validation-smoke-001/crops/mouth/*.png
  /Users/family/jason/Vtube/experiments/validation-smoke-001/crops/eye/*.png
```

## 실행 명령

```bash
python3 /Users/family/jason/Vtube/experiments/coordinate-align-001/scripts/coordinate_align_smoke.py
```

## 결과

```text
anchor_detection: PASS
mouth_coordinate_alignment: PASS
eye_semantic_classification: PASS
iris_coordinate_alignment: PASS
decision: keep-as-success-pattern
```

## 핵심 수치

```text
left iris: [686.75, 300.02]
right iris: [802.77, 299.32]
eye distance: 116.03px
mouth target center: [744.76, 373.93]
mouth target width: 48.73px

mouth placement error:
  all tested candidates <= 0.5px

iris placement error:
  both tested candidates <= 0.6px
```

## 성공패턴

```text
1. canonical에서 안정적인 anchor를 숫자로 검출한다.
2. 후보 파츠의 alpha bbox와 alpha center를 측정한다.
3. target width로 scale을 계산한다.
4. alpha center를 target anchor에 맞춰 paste한다.
5. placement_error_px를 기록한다.
6. screenshot은 최종 QA 보조로만 사용한다.
```

## 한계

```text
mouth target은 원본 입 직접 검출이 아니라 iris 거리 기반 얼굴 비율로 추정했다.
원본 canonical의 입이 너무 작은 선이라 mouth direct detection은 낮은 신뢰도다.
eye는 iris 후보 분류까지 통과했지만, full eye replacement는 eye_white/lash/lid grouping이 더 필요하다.
합성 이미지의 guide box/crosshair는 QA용 표시다.
```

## Evidence

```text
reports/coordinate_alignment_report.json
reports/qa_report.md
composites/mouth_aligned_*.png
composites/iris_aligned_*.png
```

## 다음 액션

```text
1. mouth 후보를 expression type별로 분류한다.
2. mouth style score를 추가한다.
3. eye_white/lash/lid grouping으로 full eye composite를 만든다.
4. 이 성공패턴을 avatar2d layer normalizer/previewer에 연결한다.
```

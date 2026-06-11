# Live2D Deep Reference Motion Analysis

## 결론

- 기존 분석은 `CMO3 inspector + model3/physics3/motion3 JSON + Web runtime capture`라서 공식 Cubism runtime 흐름에 꽤 가깝다.
- 더 공식적인 보강은 `Cubism Core`로 `.moc3` drawable/parameter/mask를 직접 읽는 extractor다.
- 이번 리포트는 기존 strong20 캡처를 수치화해서 parameter influence, motion curve, physics proxy, mask/draw-order risk를 추가한다.

## Visual Diff Sweep

- 방식: `neutral_vs_motion_or_extreme_pixel_diff`
- diff threshold: `18`
- `arm`: samples=60, median_changed=0.052191, p90=0.11352, max=0.178993
- `body_angle`: samples=60, median_changed=0.053997, p90=0.130882, max=0.206322
- `eye`: samples=60, median_changed=0.040494, p90=0.079862, max=0.181614
- `hair`: samples=60, median_changed=0.055084, p90=0.094052, max=0.19447
- `motion`: samples=60, median_changed=0.051918, p90=0.113439, max=0.141275
- `mouth`: samples=60, median_changed=0.051129, p90=0.089485, max=0.183648

## Parameter Influence

- parameter count: `215`
- 한계: 현재는 category sweep 기반 추정이다. 단일 parameter만 고정 sweep하는 Web/Core probe를 붙이면 confidence를 HIGH로 올릴 수 있다.

## Physics Response Proxy

- models with physics: `20/20`
- physics group median: `5.5`
- median delay summary: `0.95`
- output categories: `{'hair': 121, 'other': 52, 'body_angle': 123, 'arm': 3}`

## Motion Curve Archetypes

- motion files: `196`
- curve count: `8525`
- `arm`: curves=1315, models=18, median_amp=0.0, p90_amp=11.324
- `body_angle`: curves=1950, models=18, median_amp=1.0, p90_amp=30.0
- `eye`: curves=1475, models=20, median_amp=0.0, p90_amp=1.1048
- `hair`: curves=703, models=15, median_amp=0.0, p90_amp=1.0
- `mouth`: curves=420, models=17, median_amp=0.0, p90_amp=1.5005
- `other`: curves=2662, models=18, median_amp=0.0, p90_amp=1.06

## Mask / Draw Order Risk

- risk counts: `{'MEDIUM': 7, 'LOW': 7, 'HIGH': 6}`
- 한계: Core extractor가 drawable mask/draw order/offscreen을 제공한다. 단, 사람 눈의 앞뒤 순서 자연스러움은 G3 visual strip과 함께 확인한다.

## Official Cubism Core Extractor Gate

- status: `PASS_CORE_API_EXTRACTED`
- models with moc3: `20`
- core files found: `4`
- extractor report: `experiments/live2d-strong-model-pattern-001/reports/strong20_core_api_extractor_report.json`
- 현재 보강: Web sandbox에서 Core-backed parameter/drawable/mask/dynamic flag snapshot을 직접 덤프한다.

## Production 적용

- `v2_standard` 파츠 설계에는 visual diff가 큰 eye/mouth/hair/body parameter를 우선 keyform 검수 대상으로 둔다.
- physics는 hair/body 입력에서 hair/clothing 출력으로 이어지는 그룹을 기본값으로 삼는다.
- mask/draw-order risk가 높은 구조는 새 모델에서 최소화하고, 필요한 경우 G3 motion visual에서 onion-skin/diff로 별도 확인한다.

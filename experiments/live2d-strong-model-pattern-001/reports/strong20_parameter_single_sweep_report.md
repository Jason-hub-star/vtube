# Strong20 Parameter Single Sweep

## Summary

- status: `PASS`
- method: one parameter at min/max while other parameters stay neutral/default
- models: `20`
- samples: `320`
- parameters: `27`

## Category Summary

| Category | Samples | Parameters | Median Changed | Max Changed |
|---|---:|---:|---:|---:|
| body_angle | 108 | 9 | 0.026783 | 0.331323 |
| eye | 156 | 11 | 0.004109 | 0.331338 |
| hair | 22 | 3 | 0.040611 | 0.080211 |
| mouth | 34 | 4 | 0.024491 | 0.059225 |

## Production Use

- 이 리포트는 category 묶음 sweep보다 강한 근거다. 각 파라미터 하나만 움직였을 때의 화면 영향 범위를 본다.
- 새 모델에서는 eye/mouth/hair/body_angle 파라미터가 bbox를 명확히 바꾸는지 G3에서 확인한다.
- 변화량이 너무 작으면 Cubism keyform/deformer가 부족한 것이고, 변화량이 너무 넓으면 draw order/overhang 위험을 확인한다.

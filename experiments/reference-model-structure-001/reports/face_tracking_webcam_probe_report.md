# Face Tracking Webcam Probe Report

- status: `PASS`
- capture_class: `PASS_CAPTURE`
- frame_count: `175`
- valid_face_frame_count: `175`
- duration_ms: `10050`
- face_present_ratio: `1.0`
- movement_score: `89.213822`
- webcam_required: `True`

## Interpretation

- 내장 웹캠 입력이 Cubism v2 필수 파라미터로 변환되는 T1 smoke를 통과했습니다.
- next: 다음은 이 파라미터 스트림으로 Live2D Web Player 모델 또는 새 v2 rig preview를 구동하는 T2 테스트입니다.

## Required Coverage

| Parameter | Covered | Samples | Missing Frames |
|---|---:|---:|---:|
| `ParamAngleX` | `True` | 175 | 0 |
| `ParamAngleY` | `True` | 175 | 0 |
| `ParamAngleZ` | `True` | 175 | 0 |
| `ParamBodyAngleX` | `True` | 175 | 0 |
| `ParamBodyAngleY` | `True` | 175 | 0 |
| `ParamBreath` | `True` | 175 | 0 |
| `ParamEyeBallX` | `True` | 175 | 0 |
| `ParamEyeBallY` | `True` | 175 | 0 |
| `ParamEyeLOpen` | `True` | 175 | 0 |
| `ParamEyeROpen` | `True` | 175 | 0 |
| `ParamMouthForm` | `True` | 175 | 0 |
| `ParamMouthOpenY` | `True` | 175 | 0 |

## Parameter Extrema

| Parameter | Min | Max | Span |
|---|---:|---:|---:|
| `ParamAngleX` | -1.386768 | 30.0 | 31.386768 |
| `ParamAngleY` | -0.675062 | 6.598117 | 7.273179 |
| `ParamAngleZ` | -30.0 | 6.872167 | 36.872167 |
| `ParamBodyAngleX` | -0.300466 | 6.5 | 6.800466 |
| `ParamBodyAngleY` | -0.101259 | 0.989718 | 1.090977 |
| `ParamBreath` | 6e-06 | 0.999995 | 0.999989 |
| `ParamEyeBallX` | -0.29626 | 0.755059 | 1.051319 |
| `ParamEyeBallY` | -0.534765 | 0.037716 | 0.572482 |
| `ParamEyeLOpen` | 0.403766 | 0.942261 | 0.538495 |
| `ParamEyeROpen` | 0.468647 | 0.990802 | 0.522155 |
| `ParamMouthForm` | -0.250626 | 0.855198 | 1.105825 |
| `ParamMouthOpenY` | 0.0 | 1.0 | 1.0 |

## Failures / Warnings

- failures: `none`
- warnings: `none`

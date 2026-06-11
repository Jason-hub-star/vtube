# Face Tracking Synthetic Parameter Smoke

## Summary

- status: `PASS`
- test: `T0_static_sample_json`
- sample_count: `20`
- required_output_count: `12`
- failure_count: `0`
- webcam_required: `False`

## Interpretation

- 웹캠 없이 synthetic tracking 값으로 Cubism parameter 변환 공식과 범위를 검증한다. 이 PASS는 live tracking 성공이 아니라 mapping smoke 성공이다.
- next: T1_webcam_tracking_probe에서 실제 MediaPipe webcam/recorded-video 입력을 저장해야 live tracking 경로로 진입한다.

## Required Coverage

| Parameter | Covered |
|---|---:|
| `ParamAngleX` | `True` |
| `ParamAngleY` | `True` |
| `ParamAngleZ` | `True` |
| `ParamBodyAngleX` | `True` |
| `ParamBodyAngleY` | `True` |
| `ParamBreath` | `True` |
| `ParamEyeBallX` | `True` |
| `ParamEyeBallY` | `True` |
| `ParamEyeLOpen` | `True` |
| `ParamEyeROpen` | `True` |
| `ParamMouthForm` | `True` |
| `ParamMouthOpenY` | `True` |

## Parameter Extrema

| Parameter | Min | Max |
|---|---:|---:|
| `ParamAngleX` | -30 | 30 |
| `ParamAngleY` | -30 | 30 |
| `ParamAngleZ` | -30 | 30 |
| `ParamBodyAngleX` | -6.5 | 6.5 |
| `ParamBodyAngleY` | -4.5 | 4.5 |
| `ParamBodyAngleZ` | -5.0 | 5.0 |
| `ParamBreath` | 0 | 1 |
| `ParamEyeBallX` | -1 | 1 |
| `ParamEyeBallY` | -1 | 1 |
| `ParamEyeLOpen` | 0 | 1 |
| `ParamEyeROpen` | 0 | 1 |
| `ParamMouthForm` | -0.7 | 0.8 |
| `ParamMouthOpenY` | 0 | 1 |

## Samples

| Sample | Label | Status | Key Outputs |
|---|---|---|---|
| `neutral` | 중립 | `PASS` | ParamAngleX=0.0, ParamAngleY=0.0, ParamAngleZ=0.0, ParamEyeLOpen=1, ParamEyeROpen=1, ParamEyeBallX=0.0, ParamEyeBallY=0.0, ParamMouthOpenY=0, ParamMouthForm=0.0, ParamBodyAngleX=0.0, ParamBodyAngleY=0.0, ParamBreath=0.5 |
| `head_left` | 고개 왼쪽 | `PASS` | ParamAngleX=-30, ParamAngleY=0.0, ParamAngleZ=0.0, ParamEyeLOpen=1, ParamEyeROpen=1, ParamEyeBallX=0.0, ParamEyeBallY=0.0, ParamMouthOpenY=0, ParamMouthForm=0.0, ParamBodyAngleX=-6.5, ParamBodyAngleY=0.0, ParamBreath=0.5 |
| `head_right` | 고개 오른쪽 | `PASS` | ParamAngleX=30, ParamAngleY=0.0, ParamAngleZ=0.0, ParamEyeLOpen=1, ParamEyeROpen=1, ParamEyeBallX=0.0, ParamEyeBallY=0.0, ParamMouthOpenY=0, ParamMouthForm=0.0, ParamBodyAngleX=6.5, ParamBodyAngleY=0.0, ParamBreath=0.5 |
| `look_up` | 고개 위 | `PASS` | ParamAngleX=0.0, ParamAngleY=30, ParamAngleZ=0.0, ParamEyeLOpen=1, ParamEyeROpen=1, ParamEyeBallX=0.0, ParamEyeBallY=0.0, ParamMouthOpenY=0, ParamMouthForm=0.0, ParamBodyAngleX=0.0, ParamBodyAngleY=4.5, ParamBreath=0.5 |
| `look_down` | 고개 아래 | `PASS` | ParamAngleX=0.0, ParamAngleY=-30, ParamAngleZ=0.0, ParamEyeLOpen=1, ParamEyeROpen=1, ParamEyeBallX=0.0, ParamEyeBallY=0.0, ParamMouthOpenY=0, ParamMouthForm=0.0, ParamBodyAngleX=0.0, ParamBodyAngleY=-4.5, ParamBreath=0.5 |
| `tilt_left` | 고개 기울임 왼쪽 | `PASS` | ParamAngleX=0.0, ParamAngleY=0.0, ParamAngleZ=-30, ParamEyeLOpen=1, ParamEyeROpen=1, ParamEyeBallX=0.0, ParamEyeBallY=0.0, ParamMouthOpenY=0, ParamMouthForm=0.0, ParamBodyAngleX=0.0, ParamBodyAngleY=0.0, ParamBreath=0.5 |
| `tilt_right` | 고개 기울임 오른쪽 | `PASS` | ParamAngleX=0.0, ParamAngleY=0.0, ParamAngleZ=30, ParamEyeLOpen=1, ParamEyeROpen=1, ParamEyeBallX=0.0, ParamEyeBallY=0.0, ParamMouthOpenY=0, ParamMouthForm=0.0, ParamBodyAngleX=0.0, ParamBodyAngleY=0.0, ParamBreath=0.5 |
| `blink_left` | 왼눈 감기 | `PASS` | ParamAngleX=0.0, ParamAngleY=0.0, ParamAngleZ=0.0, ParamEyeLOpen=0, ParamEyeROpen=1, ParamEyeBallX=0.0, ParamEyeBallY=0.0, ParamMouthOpenY=0, ParamMouthForm=0.0, ParamBodyAngleX=0.0, ParamBodyAngleY=0.0, ParamBreath=0.5 |
| `blink_right` | 오른눈 감기 | `PASS` | ParamAngleX=0.0, ParamAngleY=0.0, ParamAngleZ=0.0, ParamEyeLOpen=1, ParamEyeROpen=0, ParamEyeBallX=0.0, ParamEyeBallY=0.0, ParamMouthOpenY=0, ParamMouthForm=0.0, ParamBodyAngleX=0.0, ParamBodyAngleY=0.0, ParamBreath=0.5 |
| `blink_both` | 양눈 감기 | `PASS` | ParamAngleX=0.0, ParamAngleY=0.0, ParamAngleZ=0.0, ParamEyeLOpen=0, ParamEyeROpen=0, ParamEyeBallX=0.0, ParamEyeBallY=0.0, ParamMouthOpenY=0, ParamMouthForm=0.0, ParamBodyAngleX=0.0, ParamBodyAngleY=0.0, ParamBreath=0.5 |
| `gaze_left` | 시선 왼쪽 | `PASS` | ParamAngleX=0.0, ParamAngleY=0.0, ParamAngleZ=0.0, ParamEyeLOpen=1, ParamEyeROpen=1, ParamEyeBallX=-1, ParamEyeBallY=0.0, ParamMouthOpenY=0, ParamMouthForm=0.0, ParamBodyAngleX=0.0, ParamBodyAngleY=0.0, ParamBreath=0.5 |
| `gaze_right` | 시선 오른쪽 | `PASS` | ParamAngleX=0.0, ParamAngleY=0.0, ParamAngleZ=0.0, ParamEyeLOpen=1, ParamEyeROpen=1, ParamEyeBallX=1, ParamEyeBallY=0.0, ParamMouthOpenY=0, ParamMouthForm=0.0, ParamBodyAngleX=0.0, ParamBodyAngleY=0.0, ParamBreath=0.5 |
| `gaze_up` | 시선 위 | `PASS` | ParamAngleX=0.0, ParamAngleY=0.0, ParamAngleZ=0.0, ParamEyeLOpen=1, ParamEyeROpen=1, ParamEyeBallX=0.0, ParamEyeBallY=1, ParamMouthOpenY=0, ParamMouthForm=0.0, ParamBodyAngleX=0.0, ParamBodyAngleY=0.0, ParamBreath=0.5 |
| `gaze_down` | 시선 아래 | `PASS` | ParamAngleX=0.0, ParamAngleY=0.0, ParamAngleZ=0.0, ParamEyeLOpen=1, ParamEyeROpen=1, ParamEyeBallX=0.0, ParamEyeBallY=-1, ParamMouthOpenY=0, ParamMouthForm=0.0, ParamBodyAngleX=0.0, ParamBodyAngleY=0.0, ParamBreath=0.5 |
| `mouth_deadzone` | 입 닫힘 deadzone | `PASS` | ParamAngleX=0.0, ParamAngleY=0.0, ParamAngleZ=0.0, ParamEyeLOpen=1, ParamEyeROpen=1, ParamEyeBallX=0.0, ParamEyeBallY=0.0, ParamMouthOpenY=0, ParamMouthForm=0.0, ParamBodyAngleX=0.0, ParamBodyAngleY=0.0, ParamBreath=0.5 |
| `mouth_open` | 입 열기 | `PASS` | ParamAngleX=0.0, ParamAngleY=0.0, ParamAngleZ=0.0, ParamEyeLOpen=1, ParamEyeROpen=1, ParamEyeBallX=0.0, ParamEyeBallY=0.0, ParamMouthOpenY=1, ParamMouthForm=0.0, ParamBodyAngleX=0.0, ParamBodyAngleY=0.0, ParamBreath=0.5 |
| `smile` | 웃음 | `PASS` | ParamAngleX=0.0, ParamAngleY=0.0, ParamAngleZ=0.0, ParamEyeLOpen=1, ParamEyeROpen=1, ParamEyeBallX=0.0, ParamEyeBallY=0.0, ParamMouthOpenY=0, ParamMouthForm=0.8, ParamBodyAngleX=0.0, ParamBodyAngleY=0.0, ParamBreath=0.5 |
| `frown` | 찡그림 | `PASS` | ParamAngleX=0.0, ParamAngleY=0.0, ParamAngleZ=0.0, ParamEyeLOpen=1, ParamEyeROpen=1, ParamEyeBallX=0.0, ParamEyeBallY=0.0, ParamMouthOpenY=0, ParamMouthForm=-0.7, ParamBodyAngleX=0.0, ParamBodyAngleY=0.0, ParamBreath=0.5 |
| `combined_stress` | 복합 스트레스 | `PASS` | ParamAngleX=21.6, ParamAngleY=-18.0, ParamAngleZ=13.2, ParamEyeLOpen=0.75, ParamEyeROpen=0.9, ParamEyeBallX=0.55, ParamEyeBallY=-0.45, ParamMouthOpenY=0.701299, ParamMouthForm=0.375, ParamBodyAngleX=4.68, ParamBodyAngleY=-2.7, ParamBreath=0 |
| `breath_peak` | 숨 최대 | `PASS` | ParamAngleX=0.0, ParamAngleY=0.0, ParamAngleZ=0.0, ParamEyeLOpen=1, ParamEyeROpen=1, ParamEyeBallX=0.0, ParamEyeBallY=0.0, ParamMouthOpenY=0, ParamMouthForm=0.0, ParamBodyAngleX=0.0, ParamBodyAngleY=0.0, ParamBreath=1 |

# Mini Cubism Eye Mode Validation

- Status: `REVISE`
- Project: `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/model_edit_v21_supported_rig_smoke_preview/mini_cubism_diagnostic_project`
- Mini rig present: `False`
- Mini rig keyform overrides: `0`
- Pixel threshold: `12`
- Eye ROI padding: `28`

## Contract Checks

- EyeBallX/Y target whitelist: `FAIL`
- EyeBallX/Y binding count: `8`
- EyeOpen target check: `PASS`
- Eye socket cover check: `FAIL`

## Mode Leakage

| Mode | Status | Outside changed pixels | Allowed changed pixels |
|---|---:|---:|---:|
| 중립 (`neutral`) | `PASS` | 0 | 0 |
| 눈동자 왼쪽 (`eye_ball_x_left`) | `PASS` | 0 | 9136 |
| 눈동자 오른쪽 (`eye_ball_x_right`) | `PASS` | 0 | 9152 |
| 눈동자 위 (`eye_ball_y_up`) | `PASS` | 0 | 7001 |
| 눈동자 아래 (`eye_ball_y_down`) | `PASS` | 0 | 7062 |
| 왼눈 닫힘 (`eye_l_closed`) | `PASS` | 0 | 11897 |
| 오른눈 닫힘 (`eye_r_closed`) | `PASS` | 0 | 11686 |
| 양눈 닫힘 (`both_eyes_closed`) | `PASS` | 0 | 23583 |

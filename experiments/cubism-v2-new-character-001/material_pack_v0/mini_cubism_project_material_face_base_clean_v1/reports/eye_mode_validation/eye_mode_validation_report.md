# Mini Cubism Eye Mode Validation

- Status: `PASS`
- Project: `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_face_base_clean_v1`
- Mini rig present: `True`
- Mini rig keyform overrides: `26`
- Pixel threshold: `12`
- Eye ROI padding: `28`

## Contract Checks

- EyeBallX/Y target whitelist: `PASS`
- EyeBallX/Y binding count: `24`
- EyeOpen target check: `PASS`
- Eye socket cover check: `PASS`

## Mode Leakage

| Mode | Status | Outside changed pixels | Allowed changed pixels |
|---|---:|---:|---:|
| 중립 (`neutral`) | `PASS` | 0 | 0 |
| 눈동자 왼쪽 (`eye_ball_x_left`) | `PASS` | 0 | 20193 |
| 눈동자 오른쪽 (`eye_ball_x_right`) | `PASS` | 0 | 19951 |
| 눈동자 위 (`eye_ball_y_up`) | `PASS` | 0 | 19650 |
| 눈동자 아래 (`eye_ball_y_down`) | `PASS` | 0 | 19847 |
| 왼눈 닫힘 (`eye_l_closed`) | `PASS` | 0 | 3405 |
| 오른눈 닫힘 (`eye_r_closed`) | `PASS` | 0 | 1885 |
| 양눈 닫힘 (`both_eyes_closed`) | `PASS` | 0 | 5290 |

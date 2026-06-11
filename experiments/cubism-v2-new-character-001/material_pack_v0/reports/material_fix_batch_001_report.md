# Cubism v2 Material Fix Batch 001

- status: `PASS_FIX_BATCH_001_APPLIED`
- validation: `PASS_MATERIAL_ASSET_DRAFT_READY`
- generated PNG layers: `62`
- PSD layer count: `62`
- REGENERATE after batch: `0`
- fix queue after batch: `53`

## Applied

- regenerated eye/mouth parts: `eye_L_highlight, eye_R_highlight, eye_L_closed_lid, eye_R_closed_lid, mouth_inner, mouth_teeth, mouth_tongue, mouth_line, mouth_upper_lip_mask, mouth_lower_lip_mask, mouth_corner_L, mouth_corner_R`
- underpaint parts trimmed: `body_underpaint, neck_shadow_underpaint, arm_L_underpaint, arm_R_underpaint, face_underpaint_L, face_underpaint_R, eye_L_underpaint, eye_R_underpaint, hair_back_underpaint`
- semantic cleanup bbox parts: `torso_base, neck, shoulder_L, shoulder_R, face_base, nose, collar_front, chest_cloth_base`

## Interpretation

- REGENERATE 12개는 source cut이 아니라 재생성/derived detail로 처리되어 REGENERATE 0으로 내려갔다.
- underpaint 9개는 bbox와 alpha/color 처리를 줄여 블록감을 완화했다.
- 큰 몸/얼굴/의상 파츠는 bbox를 축소했지만 아직 semantic mask cleanup 후보로 남긴다.
- fix queue 53은 실패라기보다 Cubism import 전 미세수정 대기열이다.

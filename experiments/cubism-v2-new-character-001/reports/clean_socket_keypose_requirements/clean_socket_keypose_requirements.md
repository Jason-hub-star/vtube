# Cubism v2 Clean Socket + Keypose Requirements

- status: `PASS_REQUIREMENTS_READY`
- generated_at: `2026-06-08T15:35:19.833086+00:00`
- decision: clean sockets and half/mostly/closed eye keyposes are now material requirements before rig tuning.

## Required Assets

| asset_id | group | kind | Korean | parameter target | reason |
|---|---|---|---|---|---|
| face_base_clean | face | clean_base | 눈/입 잔상이 없는 얼굴 기본 | ParamEyeLOpen, ParamEyeROpen, ParamMouthOpenY, ParamMouthForm | EyeOpen/MouthOpen keyposes cannot hide baked open eyes or mouth pixels in face_base. |
| eye_L_clean_socket | eye_L | clean_socket | 왼눈 깨끗한 눈구멍/피부 밑색 | ParamEyeLOpen | Closed eyelid must reveal skin/underpaint, not the original open eye. |
| eye_R_clean_socket | eye_R | clean_socket | 오른눈 깨끗한 눈구멍/피부 밑색 | ParamEyeROpen | Closed eyelid must reveal skin/underpaint, not the original open eye. |
| eye_L_half_closed_lid | eye_L | eye_keypose | 왼눈 반쯤 감은 눈꺼풀 | ParamEyeLOpen=0.5 | A mid keypose reduces eyelid squash artifacts between open and closed. |
| eye_R_half_closed_lid | eye_R | eye_keypose | 오른눈 반쯤 감은 눈꺼풀 | ParamEyeROpen=0.5 | A mid keypose reduces eyelid squash artifacts between open and closed. |
| eye_L_mostly_closed_lid | eye_L | eye_keypose | 왼눈 거의 감은 눈꺼풀 | ParamEyeLOpen=0.2 | Mostly-closed keypose prevents sudden popping near blink completion. |
| eye_R_mostly_closed_lid | eye_R | eye_keypose | 오른눈 거의 감은 눈꺼풀 | ParamEyeROpen=0.2 | Mostly-closed keypose prevents sudden popping near blink completion. |
| eye_L_closed_lid | eye_L | eye_keypose | 왼눈 완전히 감은 눈꺼풀/감은 눈 선 | ParamEyeLOpen=0 | Closed state is the final EyeOpen=0 target. |
| eye_R_closed_lid | eye_R | eye_keypose | 오른눈 완전히 감은 눈꺼풀/감은 눈 선 | ParamEyeROpen=0 | Closed state is the final EyeOpen=0 target. |
| eye_L_closed_underpaint | eye_L | underpaint | 왼눈 닫힘용 피부 밑색 | ParamEyeLOpen | Covers the eye socket under closed lids without using visible rectangular patches. |
| eye_R_closed_underpaint | eye_R | underpaint | 오른눈 닫힘용 피부 밑색 | ParamEyeROpen | Covers the eye socket under closed lids without using visible rectangular patches. |
| mouth_base_clean | mouth | clean_socket | 입 잔상이 없는 깨끗한 입 주변 피부/입 베이스 | ParamMouthOpenY, ParamMouthForm | MouthOpen keyposes cannot hide baked neutral/open mouth pixels naturally. |
| mouth_closed_smile | mouth | mouth_keypose | 닫힌 미소 입 | ParamMouthOpenY=0, ParamMouthForm>0 | Closed/smile state is the neutral mouth keypose. |
| mouth_small_open | mouth | mouth_keypose | 작게 열린 입 | ParamMouthOpenY=0.3 | Small-open state provides a stable in-between for speech. |
| mouth_wide_open | mouth | mouth_keypose | 크게 열린 입 | ParamMouthOpenY=0.8-1.0 | Wide-open state is needed for jaw-open and vowel extremes. |
| mouth_o_vowel | mouth | mouth_keypose | O 발음 입 | ParamMouthOpenY=0.5, ParamMouthForm<0 | Round-mouth state maps to MouthForm negative values. |
| mouth_inner | mouth | mouth_detail | 입 안쪽 | ParamMouthOpenY | Open mouth needs inner dark material behind teeth/tongue. |
| mouth_teeth | mouth | mouth_detail | 치아 | ParamMouthOpenY | Teeth should be an independent detail layer for open-mouth poses. |
| mouth_tongue | mouth | mouth_detail | 혀 | ParamMouthOpenY, ParamMouthForm | Tongue should be independent for wide/open vowel poses. |

## Imagen Prompt Plan

### Common Constraints

- Use the selected character reference exactly: same identity, same face proportions, same anime rendering style, same front-facing camera, same lighting.
- Generate Live2D/Cubism material, not a new character design and not a sprite sheet.
- No labels, no guides, no text, no colored boxes, no extra face marks, no new accessories.
- Prefer transparent background/full-canvas layer output when possible.
- If the image model cannot output a true layer, generate a clean high-resolution reference and route it through the normalization/alpha validation step before use.

### Prompt Templates

- `eye_clean_socket_prompt`: Create clean eye-socket skin material for the specified left/right eye area. Remove iris, pupil, white of eye, highlight, and open-eye lash artifacts. Preserve surrounding skin gradient, blush, eyelid fold, and hair occlusion style. Output only the clean material needed under closed eyelids.
- `eye_keypose_prompt`: Create a style-matched eyelid keypose for the specified eye: half closed, mostly closed, or fully closed. Preserve the original character style, lash thickness, eyelid curve, and left/right symmetry. Do not include the open iris/pupil/eye white.
- `mouth_clean_socket_prompt`: Create clean mouth-base material around the mouth area. Remove baked mouth line/open-mouth remnants while preserving face shading, chin, blush, and surrounding skin style.
- `mouth_keypose_prompt`: Create a style-matched mouth keypose for the specified state: closed smile, small open, wide open, or O vowel. Preserve the original mouth position, line style, lip softness, and anime shading.
- `detail_prompt`: Create separate mouth detail material for mouth_inner, teeth, or tongue. Keep it style-matched and usable as an independent Cubism layer.

## Resize / Normalization Policy

- Current material pack canvas: `[2048, 2048]`
- Required PNG mode: `RGBA`
- Policy: For the current material_pack_v0 pipeline, generated assets must be normalized to 2048x2048 full-canvas PNG before PSD/Mini Cubism use.

### Resize Decision

- If output is already 2048x2048 RGBA and aligned to the original canvas, do not resize.
- If output is not 2048x2048, do not stretch-resize directly. Normalize by preserving aspect ratio and placing into a 2048x2048 transparent canvas using ROI/anchor evidence.
- If output is an RGB full illustration instead of an RGBA layer, alpha extraction/masking is required before it can become a material layer.
- If output is a crop, keep the raw crop as reference and create a separate normalized full-canvas candidate with bbox/anchor metadata.

### Visual Fail Conditions

- Open-eye pixels visible under closed eyelid.
- Neutral/open state changed by a closed-only underpaint.
- Rectangular skin patch visible.
- Mouth closed/open state shows baked remnants from another mouth state.

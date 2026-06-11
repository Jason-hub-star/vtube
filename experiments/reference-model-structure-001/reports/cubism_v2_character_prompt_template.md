# Cubism v2 Character Prompt Template

## 목적

이 템플릿은 예쁜 단일 PNG를 바로 production으로 쓰기 위한 것이 아니라, 64파트 taxonomy, deformer hierarchy, physics blueprint를 만족하기 쉬운 Cubism-friendly master image를 만들기 위한 생성 기준이다.

## 입력 근거

- production spec: `experiments/reference-model-structure-001/reports/cubism_v2_production_design_spec.json`
- 64파트 spec: `experiments/reference-model-structure-001/reports/cubism_v2_new_model_v2_standard_part_spec.json`
- G0-G3 readiness: `experiments/reference-model-structure-001/reports/cubism_v2_new_model_pre_generation_readiness.json`

## 목표

- tier: `v2_standard`
- source image mode: `single_master_png_first`
- target part count: `64`
- physics target: `4-6`

## Compact Positive Prompt

```text
Live2D Cubism v2_standard VTuber character, front-facing upper-body, centered neutral pose.
A single clean master PNG for later PSD part separation and Cubism rigging.
Clear face base, both eyes fully visible, separated left and right eye groups, readable eyebrows, clear mouth not covered by anything.
Layer-friendly hair: separate front bangs, left side hair, right side hair, and back hair, clean strand groups for hair physics.
Visible neck, simple upper body, clear shoulders, simple upper arms, no complex hands, no large props.
Clean silhouette, minimal overlap, low clipping risk, underpaint-friendly design, simple draw order.
Consistent polished anime illustration style, clean line art, clean color separation.
```

## Negative Prompt

```text
side view, extreme pose, crossed arms, complex hands, weapon, large props, microphone covering mouth, face-covering bangs, eyes covered, mouth covered, messy hair overlap, transparent effects, heavy glow, motion blur, multiple characters, cropped head, cropped shoulders, text, labels, UI, watermark, logo, part diagram, exploded layer sheet
```

## Positive Prompt Sections

### goal

- Live2D Cubism v2_standard용 정면 상반신 VTuber 캐릭터
- single-source matched character design, one clean master PNG
- designed for later PSD part separation and Cubism rigging

### composition

- front-facing or near-front upper-body portrait
- centered composition, neutral pose, head and shoulders fully visible
- clean silhouette with clear head, neck, torso, shoulders, and simple upper arms
- symmetrical but natural design, no extreme pose

### face_and_eyes

- clear face base with both eyes fully visible
- left and right eye groups are visually separable
- distinct eye whites, iris, pupils, highlights, upper eyelids, lower eyelids, and lashes
- simple readable eyebrows separated from hair
- no hair or accessory covering the eyes

### mouth

- clearly readable mouth centered on the face
- mouth not covered by hair, hands, scarf, microphone, or accessories
- mouth shape suitable for open/close and form keyforms
- visible mouth line and inner mouth area

### hair

- layer-friendly hair design with clear front bangs, left side hair, right side hair, and back hair
- front hair clusters are cleanly grouped and do not heavily cover eyes or mouth
- side hair and back hair have separated strand groups suitable for physics
- no messy dense overlap around face edges

### body_and_arms

- visible neck, simple upper body, clear shoulders
- simple left and right upper arms visible without complex hand pose
- arms do not cross over the face, mouth, eyes, or center torso
- clothing has clean color regions and simple draw order

### rigging_friendly_constraints

- clean separated visual regions for face, eye groups, mouth, hair, neck, torso, shoulders, and arms
- minimal overlap between face, hair, mouth, eyes, and body
- low clipping risk, simple draw order, underpaint-friendly gaps
- consistent anime illustration style, clean line art, clean color separation

## 64파트 연결 요약

- total parts: `64`

| Group | Count |
|---|---:|
| `body` | 10 |
| `brow` | 2 |
| `clothing` | 4 |
| `eye_L` | 8 |
| `eye_R` | 8 |
| `face_base` | 8 |
| `hair` | 16 |
| `mouth` | 8 |

## 필수 Deformer/Parameter 힌트

이미지 생성 프롬프트가 직접 deformer를 만들지는 않는다. 대신 아래 구조가 가능하도록 눈/입/머리/몸 경계를 명확히 만든다.

- required parameters: `ParamAngleX`, `ParamAngleY`, `ParamAngleZ`, `ParamBodyAngleX`, `ParamBodyAngleY`, `ParamEyeLOpen`, `ParamEyeROpen`, `ParamEyeBallX`, `ParamEyeBallY`, `ParamMouthOpenY`, `ParamMouthForm`, `ParamBreath`
- required hierarchy nodes: `root`, `body_root_warp`, `head_angle_warp`, `eye_L_warp`, `eye_R_warp`, `mouth_warp`, `front_hair_warp`, `side_hair_L_R_warp`, `back_hair_warp`

## G0-G3 연결

| Gate | 쉬운 이름 | 프롬프트에서의 역할 |
|---|---|---|
| `G0_CONCEPT` | 캐릭터 고르기 | 이미지 생성 전 컨셉/구도 조건 |
| `G1_PART_TAXONOMY` | 파츠 나누기 | 64파트로 분리 가능한 시각 구조 조건 |
| `G2_STRUCTURE` | 구조 자동검사 | 리깅 구조를 만들 수 있게 겹침과 파츠 경계를 제한하는 조건 |
| `G3_MOTION_VISUAL` | 움직임 보기 | 눈/입/머리카락/몸각도 움직임이 보일 수 있는 형태 조건 |

## 생성 Variant

### 표준 안전형

- id: `v2_standard_safe_default`
- use_when: 첫 캐릭터 컨셉 후보 3-6개를 만들 때

```text
Live2D Cubism v2_standard VTuber character, front-facing upper-body, centered neutral pose.
A single clean master PNG for later PSD part separation and Cubism rigging.
Clear face base, both eyes fully visible, separated left and right eye groups, readable eyebrows, clear mouth not covered by anything.
Layer-friendly hair: separate front bangs, left side hair, right side hair, and back hair, clean strand groups for hair physics.
Visible neck, simple upper body, clear shoulders, simple upper arms, no complex hands, no large props.
Clean silhouette, minimal overlap, low clipping risk, underpaint-friendly design, simple draw order.
Consistent polished anime illustration style, clean line art, clean color separation.
```

### 파츠 분리 우선형

- id: `v2_standard_extra_clean_split`
- use_when: 머리카락/눈/입 분리가 실패했을 때

```text
Live2D Cubism v2_standard VTuber character, front-facing upper-body, centered neutral pose.
A single clean master PNG for later PSD part separation and Cubism rigging.
Clear face base, both eyes fully visible, separated left and right eye groups, readable eyebrows, clear mouth not covered by anything.
Layer-friendly hair: separate front bangs, left side hair, right side hair, and back hair, clean strand groups for hair physics.
Visible neck, simple upper body, clear shoulders, simple upper arms, no complex hands, no large props.
Clean silhouette, minimal overlap, low clipping risk, underpaint-friendly design, simple draw order.
Consistent polished anime illustration style, clean line art, clean color separation.
Extra clean separation between bangs, side hair, eyes, mouth, neck, shoulders, and torso. Fewer accessories, simpler clothing.
```

## 주인님 체크리스트

- 단일 PNG 1장을 먼저 만든다. 64개 파츠를 한 번에 그리라고 시키지 않는다.
- G0에서 정면 상반신, 눈/입/머리/몸 경계가 보이는지 본다.
- G1에서 64파트 taxonomy로 나눌 수 없는 디자인이면 이미지를 버리거나 재생성한다.
- G2/G3는 이미지가 아니라 이후 Cubism 구조/움직임 검증이다.
- 공식 샘플의 구조 패턴만 참고하고, 그림/텍스처/캐릭터 디자인은 복사하지 않는다.

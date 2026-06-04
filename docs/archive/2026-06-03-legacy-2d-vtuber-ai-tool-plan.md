# Codex 주도 AI 기반 2D VTuber 파츠팩 + 경량 리깅 프리뷰어 6주 MVP 계획

작성일: 2026-06-02

## 결론

이 프로젝트의 6주 MVP는 "AI가 Live2D 완성 모델을 자동 생성한다"가 아니라 "Codex가 2D VTuber 제작을 지휘하고, 기존 최신 OSS로 레이어 분해 baseline을 만들며, 파츠팩/경량 리깅 프리뷰어/QA 리포트/하네스를 만든다"로 정의해야 한다.

이유는 명확하다. Live2D Cubism SDK for Unity/Web은 Cubism Editor에서 이미 export된 `.moc3`, `.model3.json`, texture, physics, pose 같은 런타임 에셋을 앱에서 구동하는 SDK다. Raw PNG 파츠를 입력받아 mesh, deformer, weight, parameter를 자동 생성하는 리깅 엔진이 아니다.

따라서 MVP는 Cubism SDK를 핵심 자동화 경로에서 제외하고, See-through 계열 도구를 레이어 분해 baseline으로 평가한 뒤 자체 `rig2d.json`과 PixiJS/WebGL 기반 previewer를 만든다. Live2D/Cubism은 장기 호환 목표 또는 사람이 Cubism Editor에서 마무리하는 외부 경로로 둔다.

```text
사용자 이미지/프롬프트
→ GPT Image로 canonical 정면 레퍼런스 생성
→ Codex가 AvatarSpec/refpack 정리
→ See-through/ComfyUI-See-through로 semantic/depth layered PSD baseline 생성
→ imagegen으로 부족한 파츠 후보와 occlusion underpaint 후보 보강
→ 자체 검사기로 마스크/레이어/PSD 호환/좌우 분리/빈 레이어 검수
→ rig2d.json 생성
→ PixiJS/WebGL previewer에서 움직임 검수
→ MediaPipe 값으로 tracking smoke test
→ Codex가 QA 리포트와 제한된 보정 패치 제안
```

## 공식 문서와 근거

### GPT Image는 refpack 생성에 적합하지만, 완전한 다중 뷰 일관성은 보장하지 않는다

OpenAI Image Generation 문서는 이미지 생성, 이미지 입력, 편집, 반복 수정을 지원한다. 이 기능은 캐릭터 원화, 표정 시트, 헤어/의상 디테일 레퍼런스를 만드는 데 적합하다.

하지만 제작 소스를 정면/측면/후면 여러 장으로 분산하면 일관성 문제가 커진다. MVP에서는 `canonical_front.png` 한 장을 실제 파츠 제작의 기준으로 고정하고, 측면/후면/디테일 이미지는 참고 자료로만 사용한다.

imagegen은 "정확한 segmentation 엔진"이 아니라 "새 이미지를 그리거나 비어 있는 영역을 자연스럽게 채우는 생성/편집 엔진"으로 사용한다. 즉 눈, 입, 머리카락, 의상 같은 파츠 후보와 underpaint를 생성하는 데 적극 활용하고, 최종 레이어 정렬/마스크 검수/PSD 호환 규칙은 Codex와 별도 스크립트가 맡는다.

참고 URL:
- https://platform.openai.com/docs/guides/image-generation
- https://platform.openai.com/docs/api-reference/images

### Live2D 제작의 실제 입력은 파츠가 분리된 PSD다

Live2D 공식 문서는 모델링에 필요한 소재분리를 속눈썹, 눈알, 윤곽 같은 부품별 분리 작업으로 설명한다. 또한 크게 움직이는 부분이나 다른 파츠가 움직일 때 보이는 부분은 미리 넉넉히 그려 넣어야 한다고 설명한다.

Cubism Editor의 PSD import 문서는 PSD 레이어가 ArtMesh로 변환되어 캔버스에 배치된다고 설명한다. 가져오기용 PSD는 한 파츠가 한 레이어가 되도록 정리해야 하며, PSD는 RGB, 8bit/channel 조건을 만족해야 한다. 레이어 마스크, 클리핑 마스크, 선화/채색/필터 효과는 import 전에 각 파츠 레이어로 병합해야 한다.

따라서 MVP 산출물은 단순 PNG 묶음이 아니라 "나중에 PSD로 조립 가능한 레이어 명세"여야 한다.

참고 URL:
- https://docs.live2d.com/cubism-editor-manual/divide-the-material/
- https://docs.live2d.com/en/cubism-editor-manual/psd-import/
- https://docs.live2d.com/en/cubism-editor-manual/precautions-for-psd-data/

### Live2D 표준 파라미터 이름과 매핑 가능하게 설계한다

Live2D 공식 표준 파라미터 목록에는 `ParamAngleX`, `ParamAngleY`, `ParamAngleZ`, `ParamEyeLOpen`, `ParamEyeROpen`, `ParamMouthOpenY`, `ParamMouthForm` 같은 이름과 기본 범위가 있다. 자체 previewer는 내부적으로 쉬운 이름을 써도 되지만, `rig2d.json`에는 Live2D 표준 파라미터로 export/mapping할 수 있는 필드를 둔다.

참고 URL:
- https://docs.live2d.com/en/cubism-editor-manual/standard-parameter-list/

### Cubism SDK는 런타임 SDK이지 PNG 자동 리깅 엔진이 아니다

Live2D 공식 문서는 Cubism Editor에서 embedded data를 export하면 `.moc3`, `.model3.json`, texture atlas, physics, pose 같은 파일이 생성된다고 설명한다. Cubism SDK는 이 export된 데이터를 앱에서 표시하고 조작하는 쪽이다.

따라서 `PNG 파츠 + JSON → Cubism SDK → Live2D 모델`이라는 경로는 MVP 전제로 삼지 않는다.

참고 URL:
- https://www.live2d.com/en/cubism/about/
- https://www.live2d.com/en/sdk/about/
- https://docs.live2d.com/en/cubism-editor-manual/export-moc3-motion3-files/
- https://docs.live2d.com/en/cubism-sdk-manual/cubism-sdk-for-unity/

### PixiJS/WebGL은 자체 2D previewer에 적합하다

PixiJS는 웹 기반 2D 렌더링 엔진이고 Sprite, Container, Mesh 같은 렌더링 단위를 제공한다. MVP에서는 Sprite transform만으로 시작하고, 이후 Mesh deformation을 붙이는 식으로 확장한다.

참고 URL:
- https://pixijs.com/7.x/guides/components/sprites
- https://pixijs.com/8.x/guides/components/scene-objects/mesh

### MediaPipe는 tracking smoke test에 적합하다

MediaPipe Face Landmarker는 얼굴 랜드마크와 face blendshape 값을 제공한다. 공식 문서 기준 478개 3D face landmarks와 52개 blendshape score를 출력하므로, 눈 깜빡임, 입 열림, 머리 방향을 자체 `rig2d` parameter에 연결하는 smoke test에 적합하다.

참고 URL:
- https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker

### Unity와 unityctl은 2차 검수/장기 확장 경로로 둔다

Unity는 batch mode와 command line arguments를 지원하고, `unityctl`은 Unity scene/script/validate/screenshot 루프를 자동화하는 데 유용하다. 다만 6주 MVP의 1차 previewer는 웹으로 가볍게 만들고, Unity/unityctl은 나중에 runtime packaging, Unity 버전 preview, 모바일 테스트, 3D/VRM 확장에 사용한다.

참고 URL:
- https://docs.unity3d.com/Manual/CommandLineArguments.html
- https://github.com/Jason-hub-star/unityctl

## 제품 정의

### 만들지 않는 것

```text
Live2D Editor 자동 대체
Cubism Core 재구현
Cubism SDK에 raw PNG를 넣어 자동 리깅
완전 자동 AI 좌표/weight/deformer 수정 루프
3D VRM 자동 생성
```

### 만드는 것

```text
Codex가 지휘하는 2D VTuber 파츠팩 생성기
AvatarSpec JSON
GPT Image refpack 생성 프롬프트/기록
imagegen 파츠 후보/underpaint 생성 프롬프트
파츠 분리 및 underpaint 작업 구조
PSD 호환 레이어 명세
자체 rig2d.json
PixiJS/WebGL previewer
MediaPipe tracking smoke test
QA 리포트
제한된 자동 보정 + 수동 보정 UI
반복 가능한 harness
```

## Codex의 역할

이 MVP에서 Codex는 "완성 모델을 마법처럼 뽑는 엔진"이 아니라 제작 지휘관이다. Codex가 많이 개입할수록 프로젝트 성공 확률이 올라가도록 설계한다.

Codex가 담당하는 일:

```text
AvatarSpec 작성/수정
GPT Image 프롬프트 작성
imagegen 파츠별 생성/편집 프롬프트 작성
refpack 일관성 체크
파츠 누락 검사
occlusion underpaint 대상 찾기
inpainting prompt 작성
PSD 호환 레이어명/레이어 순서 검수
rig2d.json 생성
previewer 코드 작성
screenshot 기반 QA
validation_report.json 작성
낮은 위험 값만 자동 patch
고위험 보정은 manual_adjustments.json으로 제안
성공/실패 케이스를 harness로 저장
```

Codex에게 맡기지 않을 일:

```text
무제한 자동 좌표 수정
스크린샷만 보고 weight/deformer 정밀 계산
Cubism 내부 데이터 자동 생성
PSD import 성공 보장
실패 시 무한 재시도
저작권/라이선스 불명확한 에셋 사용 결정
```

## imagegen으로 생성할 이미지와 생성하지 않을 것

### imagegen으로 생성할 것

```text
canonical 정면 캐릭터 원화
표정 참고 시트
헤어 구조 참고 시트
의상/액세서리 참고 시트
눈/입/머리카락/의상 파츠 후보
앞머리 뒤 이마 같은 underpaint
입 벌림용 입안/치아/혀/그림자
눈동자 이동을 위한 눈 흰자/홍채/하이라이트
```

### imagegen으로 해결하지 않을 것

```text
정밀한 alpha mask 생성
원본 이미지에서 픽셀 단위로 정확한 segmentation
PSD 레이어 구조 자동 보장
ArtMesh/deformer/weight 생성
parameter keyform 생성
Live2D 모델 export
```

### 판단 기준

imagegen은 "새로 그려야 하는 것"에 강하고, segmentation/검수 스크립트는 "정확히 잘라야 하는 것"에 강하다. 따라서 MVP에서는 imagegen을 파츠 생성기와 underpaint 생성기로 사용하고, Codex가 레이어 구조와 검수 규칙을 고정한다.

### 2026-06-02 실험 결과 반영

`experiments/imagegen-limit-test-001`에서 canonical image, parts sheet, underpaint sheet를 생성해 본 결과, imagegen은 후보 이미지 생성에는 유용하지만 최종 PSD 레이어를 그대로 만들지는 못한다는 점이 확인됐다.

`experiments/imagegen-limit-test-002`에서는 라벨 없는 전체 파츠 시트와 파츠군별 개별 생성 결과를 비교했다. 라벨을 금지하면 텍스트 오염이 줄었고, 전체 파츠 시트보다 눈/입/underpaint처럼 파츠군별로 나누어 생성하는 편이 더 실용적이었다.

반영할 정책:

```text
imagegen 결과는 candidate로만 취급한다.
프롬프트에는 no text/no labels/no letters/no numbers를 기본 규칙으로 넣는다.
전체 parts_sheet보다 parts_face, parts_mouth, parts_hair, underpaint를 따로 생성한다.
parts_sheet는 crop/mask/색상/선 굵기 검수 후 채택한다.
underpaint는 활용 가치가 높지만 canonical_front와 위치/비율을 맞춰야 한다.
라벨이 포함된 asset sheet는 production layer로 바로 쓰지 않는다.
Codex가 canonical_front 기준으로 일관성 검수 리포트를 만든다.
```

### 2026-06-02 웹검색 반영: 레이어 분해는 See-through 계열을 baseline으로 둔다

2026년 기준 최신 흐름은 "한 장의 anime illustration을 semantic/depth 레이어 PSD로 분해"하는 See-through 계열이 가장 실용적이다. See-through는 단일 이미지에서 최대 23개 수준의 semantic layer와 drawing order를 추론하고 PSD를 출력한다. ComfyUI-See-through는 이를 ComfyUI 노드로 감싸 PSD export, depth PSD, low-VRAM 옵션을 제공한다.

중요한 점은 See-through 연구진도 이것을 완전한 Image-to-Live2D로 보지 않는다는 것이다. 레이어 분해는 자동화되지만, Live2D식 artistic decomposition, deformation mesh, physics parameter, motion curve는 별도의 리깅/검수 작업이 필요하다.

따라서 MVP의 레이어 생성 전략을 조정한다.

```text
1차 baseline:
  See-through 또는 ComfyUI-See-through로 canonical_front.png를 PSD/RGBA layer로 분해

보강:
  imagegen으로 mouth/eye/underpaint 후보를 개별 생성

자체 개발:
  layer manifest normalizer
  See-through layer quality checker
  empty/alpha/occlusion/draw-order 검사
  mouth/eye 후보 합성 smoke test
  rig2d parameter previewer
  QA report와 safe JSON patch
```

참고 URL:
- https://github.com/shitagaki-lab/see-through
- https://arxiv.org/abs/2602.03749
- https://github.com/jtydhr88/ComfyUI-See-through

### 2026-06-02 로컬 검증 반영: See-through는 아직 confirmed core path가 아니다

`experiments/validation-smoke-001`에서 See-through와 ComfyUI-See-through repo를 clone하고 로컬 Mac 환경을 확인했다. repo 확보와 entrypoint 확인은 가능했지만, 현재 주인님 Mac에서 canonical image를 직접 PSD/layer로 처리하는 데는 실패했다.

```text
확인됨:
  See-through repo clone 가능
  ComfyUI-See-through repo clone 가능
  ComfyUI-See-through nodes.py py_compile 통과

막힌 지점:
  NVIDIA/CUDA 없음
  See-through 본체 필수 dependency 미설치
  ComfyUI runtime 미설치
  실제 모델 다운로드 및 MPS/CPU 실행 가능성 미검증

판정:
  See-through는 현재 confirmed core path가 아니라 optional external baseline 또는 remote GPU validation 대상이다.
```

따라서 플랜의 우선순위는 조정한다.

```text
1차 로컬 baseline:
  imagegen 후보 crop/mask + 자체 layer normalizer + previewer

### 2026-06-02 production canvas 검증 반영: 실사용 기준은 2048x2048 상반신으로 분리한다

기존 `1536x1024` canonical 기반 실험은 좌표 정렬, full-canvas mouth layer, eye grouping 실패 같은 성공/실패 패턴을 확인하기 위한 evidence로 유지한다. 하지만 production 자산으로 승격하지 않는다.

새 실사용 기준 실험 `experiments/production-canvas-2048-001`에서는 상반신 VTuber master canvas를 `2048x2048`로 고정하고, canonical/mouth/blink 후보를 모두 같은 canvas로 정규화했다.

확인됨:

```text
resolution policy:
  2048x2048 상반신 master canvas 고정

canonical:
  imagegen source는 1254x1254로 생성됨
  script에서 2048x2048로 normalize
  눈/입 가시성은 좋지만 chroma-key edge fringe가 남아 human review 필요

anchor/ROI:
  mouth ROI 검출 가능
  eye ROI는 smoke에는 충분하지만 detector fallback이 들어가 안정 검출로 과장하면 안 됨

mouth:
  새 mouth sheet에서 5개 후보 crop
  2048x2048 full-canvas mouth layer 생성
  placement_error_px 수치상 PASS
  visual quality는 REVISE로 분리

blink:
  full eye replacement 없이 canonical eye ROI 안에 closed lid layer 생성
  visual alignment는 REVISE

preview/report:
  preview/index.html에서 crop/scale/place 없이 (0,0) overlay 가능
  공용 하네스 후보를 jason-agent-harness-template에 저장
```

따라서 다음 production 단계는 "2048 구조가 가능한가"가 아니라 "native 2048 또는 더 깨끗한 alpha canonical을 만들 수 있는가", "eye ROI detector fallback을 제거할 수 있는가", "mouth/blink 미술 품질을 사람 검수 PASS까지 올릴 수 있는가"로 좁힌다.

2차 검증:
  See-through/ComfyUI-See-through를 HuggingFace Space, ModelScope, cloud GPU, 또는 별도 ComfyUI 환경에서 검증
```

Evidence:
- `experiments/validation-smoke-001/reports/see_through_environment_report.md`

### 2026-06-02 로컬 검증 반영: 위치 조정은 screenshot이 아니라 좌표 기반으로 한다

`experiments/coordinate-align-001`에서 canonical image의 iris anchor를 자동 검출하고, mouth/iris 후보 crop의 alpha bbox와 alpha center를 이용해 좌표 기반 정렬을 테스트했다.

```text
결과:
  anchor_detection: PASS
  mouth_coordinate_alignment: PASS
  eye_semantic_classification: PASS
  iris_coordinate_alignment: PASS

핵심 수치:
  eye distance: 116.03px
  mouth target center: [744.76, 373.93]
  mouth placement error: <= 0.5px
  iris placement error: <= 0.6px
```

따라서 MVP의 검수/보정 원칙을 조정한다.

```text
좋은 방식:
  canonical anchor 검출
  candidate alpha bbox/center 측정
  target width 기반 scale 계산
  alpha center와 target anchor 정렬
  placement_error_px 기록
  screenshot은 최종 QA 보조로만 사용

피할 방식:
  AI가 screenshot만 보고 반복적으로 위치를 감으로 수정
  토큰을 많이 쓰는 시각 추론 루프
  수치 리포트 없이 "좋아 보임"으로 채택
```

Evidence:
- `experiments/coordinate-align-001/reports/coordinate_alignment_report.json`
- `experiments/coordinate-align-001/reports/qa_report.md`

### 2026-06-02 로컬 검증 반영: full eye sheet grouping은 실패했다

`experiments/eye-grouping-001`에서 `eye_white / iris / lash_or_lid` 후보를 semantic class로 나누고 canonical iris anchor 기준으로 full eye group을 조립했다. 기술적으로는 부품 분류와 overlay가 가능했지만, human review에서 위치와 미술 품질이 모두 부족하다고 판정했다.

```text
technical_grouping: PASS
coordinate_overlay: PASS
visual_alignment: FAIL
art_quality: FAIL
full_eye_composite: FAIL
decision: revise
```

따라서 이 경로는 성공패턴이 아니다.

```text
폐기:
  imagegen eye sheet의 eye_white/iris/lash를 단순 조립해 full eye replacement로 쓰는 전략

유지:
  iris-only coordinate placement
  anchor/bbox/alpha center 기반 수치 리포트

다음 설계:
  canonical 원본 눈 영역에서 eye geometry/mask를 먼저 추출
  blink/closed_lid는 canonical shape에 맞는 edit/inpaint 또는 수동 layer split 우선
```

Evidence:
- `experiments/eye-grouping-001/reports/eye_grouping_report.json`
- `experiments/eye-grouping-001/reports/qa_report.md`

### 2026-06-02 로컬 검증 반영: full-canvas layer를 우선한다

`experiments/full-canvas-layer-001`, `canonical-eye-001`, `blink-001`, `mouth-style-001`, `creature-schema-001`을 추가 실행했다. 핵심 결론은 "나중에 잘라 맞추기"보다 "처음부터 canonical과 같은 캔버스 좌표에 있는 레이어"가 더 안정적이라는 것이다.

```text
유지:
  full-canvas mouth layer
  canonical eye geometry/mask extraction
  mouth candidate scoring
  non-human anchor schema split

폐기:
  sheet closed-lid blink
  sheet eye parts full replacement

보류:
  See-through local Mac core path
```

테스트 결과:

```text
FCANVAS-001:
  full_canvas_layer: PASS
  no_runtime_place_needed: PASS
  visual_quality: REVISE

CANON-EYE-001:
  iris_center_delta: PASS
  eye_roi_bbox: PASS
  shape_mask_saved: PASS

BLINK-001:
  closed_lid_inside_roi: PASS
  no_full_eye_replacement: PASS
  visual_alignment: FAIL
  decision: discard

MOUTH-STYLE-001:
  expression_type_assignment: PASS
  shortlist_created: PASS
  rejected_candidates_recorded: PASS
  visual_quality: REVISE

CREATURE-SCHEMA-001:
  human_anime/dog_mascot/cat_mascot schema separated
  missing anchor rule defined
```

업데이트된 원칙:

```text
1. previewer 입력은 가능하면 full-canvas layer로 만든다.
2. crop/scale/place는 layer 생성 시점에 끝내고 runtime에는 반복하지 않는다.
3. 눈 전체 교체와 blink는 sheet 조립을 쓰지 않는다.
4. 눈은 canonical geometry/mask 또는 edit/inpaint/수동 split 경로로 간다.
5. 비인간 캐릭터는 human_anime anchor 공식을 재사용하지 않는다.
```

Evidence:
- `experiments/full-canvas-layer-001/reports/full_canvas_layer_report.json`
- `experiments/canonical-eye-001/reports/canonical_eye_geometry_report.json`
- `experiments/blink-001/reports/blink_report.json`
- `experiments/mouth-style-001/reports/mouth_candidate_score_report.json`
- `experiments/creature-schema-001/reports/anchor_schema_plan.md`

### Stretchy Studio와 Inochi2D는 경쟁 대상이 아니라 benchmark/export 경로다

Stretchy Studio는 See-through PSD를 받아 자동 리깅, mesh deformation, timeline, Spine export를 제공하려는 MIT OSS다. Inochi2D/Inochi Creator는 layered texture를 morph/transform/distort하는 오픈소스 2D puppetry 경로다.

MVP에서는 둘을 그대로 대체하려 하지 않는다. 대신 아래 기준으로 벤치마크한다.

```text
Stretchy Studio:
  PSD import 구조
  layer grouping
  auto-rig heuristic
  mesh deformation UX
  Spine JSON export 아이디어

Inochi2D:
  오픈 puppet format
  real-time 2D texture deformation 개념
  Live2D 외부 대안 경로
```

참고 URL:
- https://github.com/MangoLion/stretchystudio
- https://stretchy.studio/
- https://github.com/Inochi2D/inochi-creator

### PachiPakuGen은 눈/입 자동화의 우선순위를 올려준다

PachiPakuGen은 See-through PSD에서 눈깜빡임/입모양 소재를 만들기 위한 도구다. Windows/GPU/SAM3/RIFE 의존이 강해 바로 Mac 중심 파이프라인에 넣기는 어렵지만, 생산성 병목이 "mouth/eye shape 생성과 보정"에 있다는 점을 뒷받침한다.

MVP에는 PachiPakuGen 전체를 가져오지 않는다. 대신 아이디어만 반영한다.

```text
우선 구현:
  mouth_closed/mouth_a/mouth_i/mouth_u/mouth_e/mouth_o 후보 관리
  eye_open/eye_half/eye_closed 후보 관리
  canonical face 위 합성 preview
  mouth/eye crop margin과 alpha edge 검사

보류:
  SAM3 직접 통합
  RIFE 프레임 보간
  Windows/Tauri 전용 워크플로
```

참고 URL:
- https://github.com/kazuya-bros/PachiPakuGen

### Workflow-aware layer decomposition은 연구 추적 대상으로 둔다

Workflow-Aware Structured Layer Decomposition for Illustration Production과 Anime-layer-decomposition은 line art, flat color, shadow, highlight 같은 제작 workflow layer 분해 방향이다. 캐릭터 파츠 분리와는 결이 다르지만, 나중에 recolor/texture/edit UX를 만들 때 중요하다.

현재 repo 상태는 weight와 문서 업데이트가 아직 진행 중이라 즉시 생산 baseline으로 쓰기 어렵다. 6주 MVP에서는 research watchlist로 두고, layer style QA나 recolor 실험 때 재평가한다.

참고 URL:
- https://arxiv.org/abs/2603.14925
- https://github.com/zty0304/Anime-layer-decomposition

## 목표 산출물

```text
project/
  avatar.json
  refs/
    canonical_front.png
    canonical_front_clean_bg.png
    expression_refs.png
    hair_reference.png
    outfit_reference.png
    color_palette.png
    consistency_notes.json
  imagegen/
    prompts/
      canonical_front.prompt.txt
      parts_face.prompt.txt
      parts_mouth.prompt.txt
      parts_hair.prompt.txt
      parts_body.prompt.txt
      underpaint.prompt.txt
    outputs/
      part_candidates/
      underpaint_candidates/
    evaluation/
      candidate_report.json
      accepted_candidates.json
  external/
    see_through/
      canonical_front.psd
      layers/
      depth/
      layer_manifest_draft.json
      baseline_report.json
  masks/
    face_mask.png
    hair_front_mask.png
    hair_back_mask.png
    eye_l_mask.png
    eye_r_mask.png
    mouth_mask.png
    body_mask.png
  parts/
    face.png
    face_underpaint.png
    eyebrow_l.png
    eyebrow_r.png
    eye_l_white.png
    eye_l_iris.png
    eye_l_pupil.png
    eye_l_highlight.png
    eye_l_upper_lash.png
    eye_l_lower_lid.png
    eye_r_white.png
    eye_r_iris.png
    eye_r_pupil.png
    eye_r_highlight.png
    eye_r_upper_lash.png
    eye_r_lower_lid.png
    mouth_closed.png
    upper_lip.png
    lower_lip.png
    mouth_open_inner.png
    teeth.png
    tongue.png
    mouth_shadow.png
    hair_back.png
    hair_side_l.png
    hair_side_r.png
    hair_front_base.png
    bang_01.png
    bang_02.png
    bang_03.png
    ahoge.png
    neck.png
    torso.png
    arm_l_upper.png
    arm_l_lower.png
    hand_l.png
    arm_r_upper.png
    arm_r_lower.png
    hand_r.png
    outfit_top.png
    outfit_bottom.png
    accessory_01.png
  psd/
    layer_manifest.json
    import_psd_checklist.md
    export_layers/
  underpaint/
    face_base_no_hair.png
    forehead_under_bangs.png
    head_back_under_hair.png
    neck_under_chin.png
    body_under_outfit.png
  rig2d/
    rig2d.json
    draw_order.json
    parameters.json
    live2d_parameter_map.json
    anchors.json
    manual_adjustments.json
  previewer/
    index.html
    src/
    screenshots/
  reports/
    layer_quality_report.json
    validation_report.json
    qa_report.md
    ai_fix_suggestions.json
    oss_comparison.md
```

## 1주차: AvatarSpec + OSS baseline 평가 + Codex 작업 스키마

### 목표

모든 작업의 중앙 설계도인 `avatar.json`과 Codex가 읽고 쓸 수 있는 산출물 규칙을 만든다. 동시에 See-through/ComfyUI-See-through를 baseline 후보로 평가해 "직접 만들 영역"과 "외부 도구를 감싸 쓸 영역"을 확정한다.

### 해야 할 일

- `avatar.json` 스키마 정의
- `rig2d.json` 스키마 정의
- 파츠명, draw order, anchor, parameter 이름 표준화
- Live2D PSD import를 의식한 `layer_manifest.json` 정의
- 자체 parameter와 Live2D 표준 parameter 사이의 mapping 정의
- QA 리포트 포맷 정의
- 자동 보정 가능 항목과 수동 보정 항목 분리
- See-through 공식 repo와 ComfyUI-See-through 실행 조건 확인
- 현재 `canonical_front.png`로 See-through/ComfyUI-See-through baseline 가능성 판단
- `avatar2d evaluate-assets` 최소 CLI 설계
- 공용 하네스의 `autoresearch-loop` 형식으로 baseline experiment card 작성

### 예시

```json
{
  "character": {
    "name": "sample_vtuber",
    "style": "anime_2d",
    "canonical_view": "front_bust"
  },
  "source_policy": {
    "canonical_source": "refs/canonical_front.png",
    "reference_only": [
      "refs/expression_refs.png",
      "refs/hair_reference.png",
      "refs/outfit_reference.png"
    ]
  },
  "parts": {
    "required": [
      "face",
      "face_underpaint",
      "hair_back",
      "hair_front_base",
      "bang_01",
      "eye_l_white",
      "eye_l_iris",
      "eye_l_pupil",
      "eye_l_upper_lash",
      "eye_r_white",
      "eye_r_iris",
      "eye_r_pupil",
      "eye_r_upper_lash",
      "mouth_closed",
      "mouth_open_inner",
      "tongue",
      "teeth",
      "torso"
    ]
  },
  "parameters": {
    "internal": {
      "head": ["head_x", "head_y", "head_z"],
      "eyes": ["eye_l_open", "eye_r_open", "eye_x", "eye_y"],
      "mouth": ["mouth_open", "mouth_smile"],
      "body": ["body_x", "body_y"]
    },
    "live2d_map": {
      "head_x": "ParamAngleX",
      "head_y": "ParamAngleY",
      "head_z": "ParamAngleZ",
      "eye_l_open": "ParamEyeLOpen",
      "eye_r_open": "ParamEyeROpen",
      "mouth_open": "ParamMouthOpenY",
      "mouth_smile": "ParamMouthForm"
    }
  },
  "psd_policy": {
    "format": "PSD",
    "color_mode": "RGB",
    "channel_depth": "8bit/channel",
    "one_part_per_layer": true,
    "merge_masks_before_import": true
  },
  "automation_policy": {
    "safe_auto_patch": ["draw_order", "anchor_offset_small", "opacity", "layer_visibility"],
    "manual_review_required": ["mask_regeneration", "underpaint_regeneration", "mesh_deformation"]
  }
}
```

### 완료 기준

```text
샘플 avatar.json이 validate 된다.
비어 있는 프로젝트 폴더를 CLI로 만들 수 있다.
Codex가 다음 작업에 필요한 파일 경로를 추론하지 않고 읽을 수 있다.
layer_manifest.json과 live2d_parameter_map.json이 생성된다.
See-through/ComfyUI-See-through를 도입할지, 웹 데모/로컬/ComfyUI 중 어느 경로를 쓸지 결정한다.
baseline experiment card가 reports 또는 harness draft에 남는다.
```

## 2주차: canonical refpack + See-through PSD baseline + imagegen 보강 계획

### 목표

제작 소스는 정면 canonical 이미지 하나로 고정하고, See-through 계열로 PSD/RGBA layer baseline을 만든다. imagegen은 baseline에서 부족한 mouth/eye/underpaint 후보를 보강하는 용도로 제한한다.

### 해야 할 일

- `canonical_front.png` 생성
- `canonical_front_clean_bg.png` 생성
- 표정 참고 이미지 생성
- 헤어/의상 디테일 참고 이미지 생성
- See-through/ComfyUI-See-through로 canonical image 분해
- output PSD 또는 PNG layer들을 `external/see_through/` 아래 보관
- See-through layer 이름을 내부 표준 파츠명으로 매핑하는 `layer_manifest_draft.json` 생성
- 얼굴/눈/입/머리/몸/의상 파츠 후보 이미지 생성 계획 작성
- underpaint 후보 이미지 생성 계획 작성
- 생성 프롬프트와 수정 이력 기록
- Codex가 일관성 문제를 `consistency_notes.json`으로 정리

### imagegen 출력 계획

```text
refs/canonical_front.png:
  최종 제작 기준 정면 bust-up 또는 half-body 이미지

refs/expression_refs.png:
  neutral, smile, angry, surprised, sad, blink 참고

external/see_through/:
  canonical_front.psd 또는 PNG layer bundle
  depth map
  layer metadata

imagegen/outputs/part_candidates/parts_face.png:
  얼굴 베이스, 눈썹, 눈 흰자, 홍채, 동공, 하이라이트, 속눈썹 후보

imagegen/outputs/part_candidates/parts_mouth.png:
  닫힌 입, 윗입술, 아랫입술, 열린 입 내부, 치아, 혀, 그림자 후보

imagegen/outputs/part_candidates/parts_hair.png:
  뒷머리, 옆머리, 앞머리 덩어리, 개별 bang, ahoge 후보

imagegen/outputs/underpaint_candidates/underpaint_face.png:
  앞머리 뒤 이마, 목/턱 아래, 머리 뒤쪽 빈 영역 보충 후보
```

### imagegen 프롬프트 기본 규칙

```text
no text
no labels
no letters
no numbers
plain white background
generous spacing
no overlap
isolated parts
candidate asset sheet, not final PSD
```

### 생성 전략

```text
좋음:
  parts_face, parts_mouth, parts_hair, parts_body, underpaint를 따로 생성
  See-through 결과에서 부족한 mouth/eye/underpaint만 imagegen으로 보강

위험:
  한 장에 모든 파츠를 과도하게 요구
  라벨이 있는 파츠 시트 생성
  생성 결과를 바로 production layer로 채택
  See-through PSD를 검수 없이 production layer로 채택
```

### 중요한 제한

정면/측면/후면을 모두 제작 소스로 쓰지 않는다. GPT Image는 캐릭터 분위기와 디자인 확장에는 강하지만, 파츠 제작에 필요한 픽셀/구조 단위 다중 뷰 일관성을 보장하지 않는다.

imagegen으로 나온 파츠 후보를 그대로 최종 파츠로 확정하지 않는다. Codex가 canonical_front와 비교해 색상, 선 굵기, 위치, 누락 영역을 검수하고, 필요한 경우 마스크 기반 편집 또는 수동 보정 대상으로 돌린다.

### 완료 기준

```text
canonical_front.png 하나가 파츠 제작 기준으로 승인된다.
참고 이미지는 canonical_front와 다른 점이 notes에 기록된다.
See-through baseline layer bundle이 생성되거나, 실행 불가 사유가 기록된다.
Codex가 파츠 목록과 underpaint 필요 영역을 초안으로 만든다.
imagegen_plan.json에 생성할 파츠/underpaint 목록과 프롬프트가 기록된다.
candidate_report.json에 채택/보류/폐기 판정이 기록된다.
```

## 3주차: Layer Normalizer + Occlusion Underpaint + PSD 호환 정리

### 목표

See-through/imagegen/manual 후보를 하나의 내부 레이어 명세로 정규화한다. 단순히 이미지를 자르는 것이 아니라, 움직일 때 뒤가 비어 보이지 않도록 가려진 영역을 보충한다. 동시에 나중에 Live2D/Cubism Editor로 가져갈 수 있도록 PSD 호환 레이어 규칙을 지킨다.

### 해야 할 일

- See-through PSD/PNG layer를 내부 파츠명으로 정규화
- 얼굴, 머리, 눈, 입, 몸, 의상 파츠 분리 또는 채택
- mask 생성
- imagegen 파츠 후보를 canonical_front 기준으로 정렬/채택/폐기
- 가려진 영역 목록화
- GPT Image edit/inpainting용 prompt 작성
- underpaint 결과를 원본과 비교
- `psd/layer_manifest.json` 생성
- `psd/import_psd_checklist.md` 생성
- 실패한 파츠는 재생성 또는 수동 보정 대상으로 표시
- `reports/layer_quality_report.json` 생성

### PSD 호환 규칙

```text
한 파츠는 한 레이어로 export 가능해야 한다.
레이어명은 ASCII, 숫자, underscore 중심으로 통일한다.
선화/채색/그림자/필터는 import용 레이어에서는 병합한다.
레이어 마스크와 클리핑 마스크는 import 전에 적용/병합한다.
PSD는 RGB, 8bit/channel 조건을 목표로 한다.
작업용 PSD와 import용 PSD를 분리한다.
```

### 최소 파츠 체크리스트

```text
얼굴:
  face_base, face_underpaint, eyebrow_l, eyebrow_r

왼쪽 눈:
  eye_l_white, eye_l_iris, eye_l_pupil, eye_l_highlight,
  eye_l_upper_lash, eye_l_lower_lid

오른쪽 눈:
  eye_r_white, eye_r_iris, eye_r_pupil, eye_r_highlight,
  eye_r_upper_lash, eye_r_lower_lid

입:
  mouth_closed, upper_lip, lower_lip, mouth_open_inner,
  teeth, tongue, mouth_shadow

머리카락:
  hair_back, hair_side_l, hair_side_r, hair_front_base,
  bang_01, bang_02, bang_03, ahoge

몸/의상:
  neck, torso, arm_l_upper, arm_l_lower, hand_l,
  arm_r_upper, arm_r_lower, hand_r, outfit_top, outfit_bottom
```

### 필수 underpaint

```text
앞머리 뒤 이마
눈꺼풀 뒤 눈 흰자
눈동자 이동 영역
입 벌림용 입안/치아/혀/그림자
턱/목 연결부
머리카락 흔들림 뒤쪽 빈 영역
의상 파츠가 움직일 때 드러나는 몸통 일부
```

### 완료 기준

```text
필수 parts/*.png가 모두 존재한다.
각 파츠 alpha 영역이 비어 있지 않다.
See-through 채택/수정/폐기 레이어가 명시된다.
underpaint 대상과 결과가 reports에 기록된다.
눈/입/앞머리 움직임에서 큰 구멍이 없는지 정적 검사한다.
psd/layer_manifest.json이 모든 parts/*.png를 참조한다.
```

## 4주차: PixiJS/WebGL 자체 2D Previewer

### 목표

Unity/Cubism을 기다리지 않고, 웹에서 빠르게 파츠를 올려 움직여 볼 수 있는 자체 previewer를 만든다.

### 해야 할 일

- PixiJS 앱 생성
- `avatar.json`, `rig2d.json`, `draw_order.json` 로딩
- `psd/layer_manifest.json` 로딩
- PNG layer 렌더링
- anchor/pivot 적용
- translation/rotation/scale parameter 적용
- eye blink, mouth open, head sway 테스트
- Live2D 표준 parameter mapping 표시
- screenshot 저장
- 간단한 수동 보정 UI 추가
- Stretchy Studio의 PSD import/grouping/mesh UX를 참고하되, MVP는 sprite transform 중심으로 제한

### MVP 움직임 범위

```text
head_x: 얼굴/머리/눈/입 그룹 좌우 이동 및 회전
head_y: 얼굴/머리 그룹 상하 이동
head_z: 머리 전체 roll
eye_l_open / eye_r_open: 눈꺼풀 또는 eye mask 스케일
eye_x / eye_y: iris 위치
mouth_open: closed/open inner blend
body_x / body_y: 몸통 약한 반응
hair_sway: 앞머리/뒷머리 회전
```

### Live2D 표준 파라미터 매핑

```text
head_x -> ParamAngleX
head_y -> ParamAngleY
head_z -> ParamAngleZ
eye_l_open -> ParamEyeLOpen
eye_r_open -> ParamEyeROpen
mouth_open -> ParamMouthOpenY
mouth_smile -> ParamMouthForm
```

### 완료 기준

```text
npm run dev로 previewer가 실행된다.
샘플 avatar 프로젝트를 로딩한다.
슬라이더로 parameter를 움직일 수 있다.
각 슬라이더가 Live2D 표준 parameter와 어떻게 연결되는지 표시한다.
스크린샷을 저장한다.
draw order/anchor 오류를 리포트한다.
```

## 5주차: MediaPipe Tracking Smoke Test + QA Report

### 목표

실시간 완성 트래킹이 아니라, MediaPipe 값이 `rig2d` parameter에 연결되어 눈/입/머리가 실제로 움직이는지만 확인한다.

### 해야 할 일

- MediaPipe Face Landmarker 연결
- webcam 또는 sample JSON stream 입력
- blendshape/landmark 값을 자체 parameter로 매핑
- 움직임 범위 clamp
- previewer screenshot 시퀀스 저장
- validation_report.json 생성
- 사람이 바로 고칠 수 있는 qa_report.md 생성
- mouth/eye 후보 합성 smoke test 추가

### 검수 항목

```text
눈 깜빡임 값이 눈 파츠에 반영되는가
입 열림 값이 입 파츠에 반영되는가
머리 좌우 값이 과도하게 튀지 않는가
파츠가 화면 밖으로 나가지 않는가
draw order가 깨지지 않는가
underpaint 구멍이 드러나지 않는가
파츠 alpha edge가 지나치게 지저분하지 않은가
```

### 완료 기준

```text
tracking smoke test가 자동 실행된다.
성공/실패가 JSON으로 남는다.
대표 screenshot이 reports에 저장된다.
Codex가 QA 보고서를 요약할 수 있다.
```

## 6주차: Codex 진단 루프 + 수동 보정 UI + Harness화

### 목표

완전 자동 수정 루프를 만들지 않는다. 대신 Codex가 문제를 진단하고, 낮은 위험 값만 제한적으로 patch하며, 사람이 볼 수 있는 보정 UI와 리포트를 만든다.

### 해야 할 일

- `validation_report.json`과 screenshot을 기반으로 문제 분류
- `ai_fix_suggestions.json` 생성
- 안전한 항목만 자동 patch
- 고위험 수정은 `manual_adjustments.json`으로 제안
- previewer에 수동 보정 UI 추가
- 성공/실패 케이스를 harness로 저장
- Stretchy Studio/Inochi2D/PachiPakuGen 대비표 작성
- See-through baseline 재실행 절차와 실패 복구 절차 문서화

### 자동 patch 허용 항목

```text
draw_order 순서 변경
anchor 소폭 이동
opacity 조정
layer visibility 조정
parameter clamp 값 조정
```

### 수동 검토 필수 항목

```text
mask 재생성
underpaint 재생성
파츠 자체 이미지 수정
mesh deformation 추가
눈/입 구조 변경
캐릭터 디자인 변경
```

### 완료 기준

```text
QA 리포트가 인간 개발자에게 유용하다.
Codex가 다음 수정 작업을 명확히 제안한다.
자동 보정은 되돌릴 수 있는 JSON patch로만 수행된다.
previewer에서 사람이 수동 조정할 수 있다.
harness로 샘플 케이스를 재실행할 수 있다.
```

## Harness 저장 정책

주인님 작업 환경에서는 반복 가능한 검사기와 프리뷰어를 공용 자산으로 남겨야 한다.

저장 위치:

```text
/Users/family/jason/jason-agent-harness-template
```

저장 대상:

```text
avatar2d 프로젝트 템플릿
sample avatar fixture
validation script
previewer smoke test
See-through/ComfyUI-See-through baseline 실행 카드
GPT Image prompt template
imagegen part prompt template
underpaint checklist
PSD layer manifest checklist
Live2D standard parameter mapping checklist
QA report template
Codex/Claude 재실행 절차
```

저장 조건:

```text
샘플 입력으로 실행 가능
성공/실패 리포트가 생성됨
Codex와 Claude가 같은 절차로 재실행 가능
문서에 명령어와 기대 출력이 적혀 있음
```

## CLI 초안

```bash
avatar2d init sample_vtuber
avatar2d ref plan --spec avatar.json
avatar2d ref generate --spec avatar.json
avatar2d external see-through-import --project sample_vtuber --input canonical_front.png
avatar2d external see-through-evaluate --project sample_vtuber
avatar2d imagegen plan --spec avatar.json
avatar2d imagegen parts --spec avatar.json
avatar2d imagegen evaluate --project sample_vtuber
avatar2d layers normalize --project sample_vtuber
avatar2d parts extract --spec avatar.json
avatar2d parts underpaint --spec avatar.json
avatar2d psd manifest --project sample_vtuber
avatar2d preview dev --project sample_vtuber
avatar2d preview screenshot --project sample_vtuber
avatar2d track smoke --project sample_vtuber
avatar2d validate --project sample_vtuber
avatar2d fix suggest --project sample_vtuber
avatar2d fix apply-safe --project sample_vtuber
avatar2d harness export --project sample_vtuber
```

## 6주 로드맵 요약

| 주차 | 목표 | 핵심 산출물 |
|---|---|---|
| 1주차 | AvatarSpec + OSS baseline 평가 + Codex 작업 스키마 | `avatar.json`, `rig2d.json` schema, baseline experiment card |
| 2주차 | canonical refpack + See-through PSD baseline + imagegen 보강 계획 | `canonical_front.png`, `external/see_through/*`, `imagegen_plan.json` |
| 3주차 | Layer normalizer + occlusion underpaint + PSD 호환 정리 | `parts/*.png`, `masks/*.png`, `layer_quality_report.json`, `psd/layer_manifest.json` |
| 4주차 | PixiJS/WebGL previewer | 웹 previewer, Live2D parameter map, slider UI, screenshot |
| 5주차 | MediaPipe tracking smoke test | `validation_report.json`, screenshot sequence |
| 6주차 | Codex 진단 + 수동 보정 + harness | `qa_report.md`, `ai_fix_suggestions.json`, OSS 대비표, harness export |

## 최종 판단

6주 안에 가능한 MVP는 Live2D 완성 모델 자동 생성기가 아니다. 가능한 것은 Codex가 강하게 개입하고 See-through 계열 OSS를 baseline으로 활용하는 AI 제작 보조 시스템이다.

```text
위험한 목표:
AI가 PNG를 Live2D 모델로 자동 리깅한다.

현실적인 목표:
Codex가 레퍼런스, See-through layer baseline, imagegen 보강 파츠, underpaint, PSD 호환 레이어, rig2d, preview, QA를 지휘하고,
자체 경량 previewer에서 움직임 가능성을 검수한다.
```

이 구조라면 실패해도 버릴 것이 적다. `AvatarSpec`, `refpack`, `imagegen_plan`, `parts`, `psd/layer_manifest`, `rig2d`, `previewer`, `QA report`, `harness`는 이후 Live2D 수동 리깅 경로, 자체 2D 런타임, Unity 런타임, 3D VRM 확장에도 재사용할 수 있다.

# Vtube 검증 Evidence Log

작성일: 2026-06-02
최신 정리일: 2026-06-03

## 목적

`2d-vtuber-ai-tool-plan.md`의 주장을 실제 실험 근거 기준으로 분리한다. 웹검색으로 유망한 내용과 로컬에서 직접 검증한 내용을 섞지 않기 위해, 모든 핵심 가정은 아래 상태 중 하나로 관리한다.

```text
VERIFIED:
  현재 Vtube 폴더의 입력/출력/명령/스크린샷/리포트로 재확인 가능

OBSERVED:
  로컬 실험은 했지만 수치화/자동화/반복성 검증은 부족함

RESEARCHED:
  웹검색, 논문, 오픈소스 문서 기준으로 유망함
  아직 주인님 환경에서 실행하지 않음

UNVERIFIED:
  플랜상 필요하지만 아직 실험 없음

BLOCKED:
  실행 조건, 라이선스, 하드웨어, OS, 의존성 문제로 막힘

DISCARDED:
  실험 결과 플랜에서 제외
```

## 현재 Evidence 상태

| 항목 | 현재 상태 | 근거 | 플랜 반영 수준 |
|---|---:|---|---|
| Vtube 로컬 자산 목록 | VERIFIED | `find /Users/family/jason/Vtube`, PNG 크기/해시 확인 | 자산 baseline으로 사용 가능 |
| imagegen canonical 정면 생성 | OBSERVED | `experiments/imagegen-limit-test-001/results.md` | 후보 생성 전략에 반영 가능 |
| imagegen labeled parts sheet 한계 | OBSERVED | 라벨 오타, 좌우 불균형, canonical 불일치 관찰 | "최종 PSD로 바로 쓰지 않음" 근거로 사용 |
| imagegen no-label parts sheet 개선 | OBSERVED | `imagegen-limit-test-002` 결과 | no text/no labels 규칙 반영 가능 |
| imagegen eye/mouth/underpaint 개별 생성 | OBSERVED | `imagegen-limit-test-002` 결과 | 다음 crop/mask 실험 대상으로 사용 |
| imagegen crop/mask 자동화 가능성 | VERIFIED | `validation-smoke-001`에서 mouth 14개, eye 18개 crop/mask 생성 | smoke 통과, semantic 분류는 추가 필요 |
| canonical 위 mouth/eye 합성 가능성 | OBSERVED | `validation-smoke-001/composites/*` 생성 | mouth는 후속 가치 있음, eye는 분류/위치 보정 필요 |
| 좌표 기반 mouth/iris 자동 정렬 | VERIFIED | `coordinate-align-001`에서 anchor 검출, alpha center 정렬, placement error 측정 | 스크린샷 기반 조정보다 우선할 성공패턴 |
| full eye semantic grouping | DISCARDED | `eye-grouping-001` human review: 위치와 미술 품질 모두 부족 | naive sheet-part grouping은 production 경로에서 제외 |
| full-canvas mouth layer | OBSERVED | `full-canvas-layer-001`에서 canonical 크기 투명 mouth layer 생성 | previewer 입력 구조로 유지, 미술 품질은 REVISE |
| canonical eye geometry/mask | VERIFIED | `canonical-eye-001`에서 iris/eye ROI/mask 추출 | 눈 작업 기준 geometry로 유지 |
| sheet closed-lid blink | DISCARDED | `blink-001`에서 ROI 안에는 들어오지만 visual alignment FAIL | sheet blink 후보 폐기 |
| mouth candidate scoring | OBSERVED | `mouth-style-001`에서 expression type/shortlist/reject 생성 | 후보 축소용으로 유지, 승인 근거는 아님 |
| non-human anchor schema split | VERIFIED | `creature-schema-001`에서 human/dog/cat schema 분리 | 비인간 캐릭터에 human 공식 재사용 금지 |
| production 2048 canvas policy | VERIFIED | `production-canvas-2048-001/reports/resolution_spec_report.json` | 상반신 production master는 2048x2048로 고정 |
| production 2048 canonical master | OBSERVED | `production-canvas-2048-001/canonical/canonical_front_2048.png`, source 1254x1254 → 2048 normalize | visual review 필요, native 2048 생성은 미확인 |
| production 2048 anchor/ROI extraction | OBSERVED | `production-canvas-2048-001/reports/anchor_2048_report.json` | mouth ROI는 유지, eye ROI detector는 fallback이라 개선 필요 |
| production 2048 full-canvas mouth layers | OBSERVED | `production-canvas-2048-001/reports/mouth_gen_2048_report.json` | previewer 후보로 유지, human visual quality는 REVISE |
| production 2048 canonical-mask blink | OBSERVED | `production-canvas-2048-001/reports/blink_2048_report.json` | full eye replacement 없이 layer 생성, visual alignment는 REVISE |
| production 2048 preview/report harness | VERIFIED | `production-canvas-2048-001/preview/index.html`, `harness_2048_report.json`, shared harness file | Codex/Claude 재실행 후보로 사용 가능 |
| production 2048 next raw assets | OBSERVED | `asset-generation-2048-001/raw/*`, `reports/asset_manifest.json`, `reports/generated_assets_contact_sheet.png` | MOUTH-APPLY-DELTA, BLINK-STAGE, ALPHA-CLEANUP 입력 후보 |
| mouth A/B sheet after calibrated delta | VERIFIED | `mouth-apply-delta-001/reports/mouth_apply_delta_report.json`, `mouth_shortlist_report.json`, 주인님 visual review | calibrated `canvas_dx=-37.842`, `canvas_dy=6.307` 적용 후 훨씬 좋아졌고 사용 가능할 수 있는 수준. 주인님 결정으로 입 후보 10개 전부 사용. 개별 mouth offset은 rig preview에서 문제 보일 때만 fallback |
| blink staged full-canvas layers | OBSERVED | `blink-stage-001/reports/blink_stage_report.json`, `preview/index.html` | 3단계 `half/mostly_closed/closed` 생성, full-canvas PASS, eye ROI 3/3 PASS, coverage 단계성 PASS. human visual review 필요 |
| blink saved placement apply | OBSERVED | `blink-apply-review-001/reports/blink_apply_review_report.json`, `preview/index.html` | 저장된 blink 위치값을 3단계 full-canvas 레이어에 적용. full-canvas PASS, review 3/3 존재, numeric ROI는 0/3이라 visual 판단과 분리 필요 |
| Live2D key-pose production direction | VERIFIED | `live2d-keypose-spec-001/reports/live2d_keypose_spec.md` | 입/깜빡임 PNG는 프로덕션 frame-swap 자산이 아니라 Cubism ArtMesh/Deformer/parameter key-pose reference로 사용. production target은 `ParamEyeLOpen/ParamEyeROpen`, `ParamMouthOpenY/ParamMouthForm` 매핑 |
| Cubism import material pack v1 | VERIFIED | `experiments/cubism-material-pack-001/reports/validation_report.json`, `reports/cubism_import_smoke.json`, `import_ready.psd`, `layer_manifest.json`, `rigger_handoff.md` | production layer와 reference_pack 분리, mouth/blink 후보는 PSD 밖 reference로 유지. raw-minimal PSD writer는 Cubism parsing 실패(`error signature @ 0x00000026`), psd-tools writer는 Cubism Editor 5.3 import smoke PASS 후 `import_ready.psd`로 승격 |
| Vtube doc SSOT cleanup | VERIFIED | `experiments/doc-ssot-cleanup-001/reports/doc_ssot_cleanup_report.json` | 루트 플랜을 얇은 최신 진입점으로 교체, 옛 6주 MVP 플랜은 `docs/archive/2026-06-03-legacy-2d-vtuber-ai-tool-plan.md`로 보존 |
| See-through PSD layer baseline | BLOCKED | repo clone/entrypoint 확인, 로컬 Mac 직접 inference는 CUDA/dependency 조건으로 미통과 | confirmed core path로 쓰지 않음 |
| ComfyUI-See-through Mac 실행성 | BLOCKED | plugin clone/py_compile PASS, standalone은 ComfyUI runtime 미설치로 실패 | 별도 ComfyUI 또는 remote GPU Gate 필요 |
| See-through layer 품질 | UNVERIFIED | 현재 canonical으로 출력 없음 | 플랜 핵심 게이트 |
| Mac ComfyUI See-through branch | FAIL_MPS_MEMORY | `experiments/see-through-layer-decomp-001/reports/comfyui_setup_report.json`, `reports/comfyui_mps_crash_report.json`, `reports/comfyui_inference_report.json` | MPS runtime/custom node/model download는 통과했지만 GenerateLayers에서 MPS memory abort 또는 no layers output. 실제 decomposition은 Ubuntu CUDA로 전환 |
| Ubuntu CUDA See-through runbook | READY_TO_RUN | `docs/ref/UBUNTU-CUDA-SEETHROUGH-RUNBOOK.md` | Ubuntu CUDA에서 `*_layers.json` 생성 후 Mac review/PSD gate로 회수하는 절차 문서화 |
| Stretchy Studio 참고 가치 | RESEARCHED | GitHub/사이트 조사만 있음 | benchmark 후보로만 유지 |
| PachiPakuGen eye/mouth 자동화 가치 | RESEARCHED | GitHub 조사만 있음 | 아이디어만 반영, 도입은 보류 |
| PixiJS/WebGL previewer 구현성 | UNVERIFIED | 아직 코드 없음 | 4주차 전 최소 spike 필요 |
| MediaPipe tracking smoke | UNVERIFIED | 아직 코드 없음 | previewer 이후 검증 |
| Live2D PSD import 호환성 | RESEARCHED | 공식 문서 근거만 있음 | 실제 PSD export/import 체크 필요 |

## Legacy/Reference 검증 백로그

아래 Gate 목록은 2026-06-02 기준의 초기 검증 백로그다. 현재 production SSOT는 Live2D/Cubism 방향으로 조정되었으므로, 이 목록을 그대로 최신 플랜으로 사용하지 않는다.

현재 우선순위는:

```text
PSD-LAYER-SCHEMA-001
LIVE2D-PARAM-MAP-001
CUBISM-IMPORT-CHECKLIST-001
RIG-REFERENCE-PACK-001
```

## 완성도 높은 플랜을 위한 필수 검증

아래 검증을 통과하면 "가능해 보임"이 아니라 "실행 가능한 플랜"으로 바꿀 수 있다. 완벽한 플랜은 예측으로 나오지 않고, 실패 조건까지 기록된 evidence matrix에서 나온다.

### Gate 0: 자산 Baseline

목표:
현재 자산이 어떤 테스트의 입력인지 고정한다.

검증:
- 모든 PNG의 경로, 크기, 해시 기록
- 중복 raw/generated 파일 구분
- canonical source 하나 지정

통과 기준:
```text
asset_inventory.json 또는 markdown 표가 존재한다.
canonical_front 후보가 하나 지정된다.
같은 입력으로 다음 테스트를 재실행할 수 있다.
```

### Gate 1: imagegen 후보의 후처리 가능성

목표:
imagegen 결과가 "보기 좋은 그림"이 아니라 실제 파츠 후보로 쓸 수 있는지 검증한다.

검증:
- `individual_mouth_parts.png`에서 mouth 후보 자동 crop
- `individual_eye_parts.png`에서 eye 후보 자동 crop
- 흰 배경 제거 또는 alpha mask 생성
- canonical 얼굴 위에 mouth/eye를 합성
- 합성 screenshot 저장

통과 기준:
```text
최소 mouth 3개, eye 2개를 crop한다.
각 crop의 alpha 영역이 비어 있지 않다.
canonical 위 합성 screenshot에서 위치/스케일 조정이 가능하다.
수동 보정이 필요한 항목이 qa_report.md에 기록된다.
```

실패 시 플랜 조정:
```text
imagegen parts는 production 후보가 아니라 reference-only로 낮춘다.
mouth/eye는 See-through 또는 수동 제작 우선으로 전환한다.
```

### Gate 2: See-through/ComfyUI-See-through 실행성

목표:
웹검색 기반 주장을 주인님 환경의 실행 evidence로 바꾼다.

검증:
- See-through 또는 ComfyUI-See-through 설치 가능 여부 확인
- Mac에서 실행 가능한 경로 확인
- 현재 `canonical_front.png` 입력으로 PSD 또는 PNG layer 출력
- 출력 시간을 기록
- GPU/CPU/메모리/실패 로그 기록

통과 기준:
```text
external/see_through/ 아래 출력물이 존재한다.
실행 명령, 소요 시간, 실패 복구 방법이 기록된다.
출력 layer 개수와 각 layer alpha coverage가 기록된다.
```

실패 시 플랜 조정:
```text
See-through는 local baseline이 아니라 optional external tool로 낮춘다.
1차 MVP는 imagegen/manual crop + 자체 normalizer로 축소한다.
```

### Gate 3: See-through layer 품질 평가

목표:
See-through 출력이 실제 VTuber layer baseline으로 충분한지 검증한다.

검증:
- layer별 alpha coverage 측정
- 빈 레이어, 너무 작은 레이어, 전체 이미지에 가까운 레이어 탐지
- face/hair/eye/mouth/torso 계열로 매핑 가능 여부 판정
- draw order가 시각적으로 말이 되는지 screenshot 비교
- underpaint가 실제로 존재하는지 확인

통과 기준:
```text
필수 계열(face, hair, eye, mouth, torso) 중 4개 이상이 매핑 가능하다.
빈/노이즈 layer 비율이 허용 범위 안이다.
layer_quality_report.json이 생성된다.
채택/수정/폐기 layer 목록이 있다.
```

실패 시 플랜 조정:
```text
See-through는 underpaint/reference extraction 용도로만 사용한다.
PSD baseline 자동화 목표를 낮춘다.
```

### Gate 4: Layer Normalizer 가능성

목표:
See-through/imagegen/manual 후보를 같은 내부 규격으로 합칠 수 있는지 검증한다.

검증:
- `layer_manifest_draft.json`을 내부 `psd/layer_manifest.json`으로 변환
- layer name, source, bbox, alpha coverage, draw order 기록
- 누락 필수 파츠 목록 자동 산출
- PSD import checklist 생성

통과 기준:
```text
avatar2d layers normalize 또는 동등한 스크립트가 샘플 입력에서 동작한다.
필수 파츠 누락 목록이 자동으로 나온다.
layer_manifest.json이 모든 parts/*.png를 참조한다.
```

실패 시 플랜 조정:
```text
CLI 개발 전에 manifest schema를 더 작게 줄인다.
draw order와 anchor는 수동 JSON으로 시작한다.
```

### Gate 5: 경량 Previewer Spike

목표:
Live2D/Cubism 없이도 파츠 움직임을 검수할 수 있는지 확인한다.

검증:
- 최소 HTML/Canvas 또는 PixiJS previewer 생성
- face, hair, eye, mouth, torso 5계열 렌더링
- 슬라이더로 mouth_open, eye_open, head_x 이동
- screenshot 저장

통과 기준:
```text
로컬 브라우저에서 previewer가 열린다.
슬라이더 조작 전/후 screenshot이 저장된다.
layer draw order 문제가 qa_report에 기록된다.
```

실패 시 플랜 조정:
```text
PixiJS 대신 Canvas 2D로 더 작은 previewer를 먼저 만든다.
tracking smoke는 연기한다.
```

### Gate 6: MediaPipe Tracking Smoke

목표:
트래킹 완성도가 아니라 parameter 연결 가능성만 확인한다.

검증:
- sample JSON 또는 webcam으로 face blendshape/landmark 입력
- mouth_open, eye_l_open, eye_r_open, head_x에 매핑
- clamp와 smoothing 적용 전/후 비교

통과 기준:
```text
tracking input이 rig2d parameter로 변환된다.
튀는 값이 clamp된다.
대표 screenshot 또는 parameter log가 reports에 저장된다.
```

실패 시 플랜 조정:
```text
MVP에서는 tracking을 optional로 낮추고 previewer/manual QA를 우선한다.
```

### Gate 7: Harness 재실행성

목표:
Codex와 Claude가 같은 절차로 실험을 반복할 수 있게 만든다.

검증:
- 실험 카드 작성
- 명령어, 입력, 출력, 기대 결과 기록
- keep/discard 조건 기록
- 공용 하네스 후보를 `/Users/family/jason/jason-agent-harness-template`에 저장할 가치 평가

통과 기준:
```text
한 테스트를 새 세션에서 다시 실행할 수 있다.
결과가 reports에 남는다.
성공/실패 판단이 사람 감상에만 의존하지 않는다.
```

## 우선순위 테스트 순서

### Phase A: 지금 자산만으로 가능한 검증

```text
A1. asset_inventory 생성
A2. imagegen mouth crop/mask smoke
A3. imagegen eye crop/mask smoke
A4. canonical 위 mouth/eye 합성 screenshot
A5. crop/mask 결과 qa_report 작성
```

목표:
외부 OSS 설치 전에 현재 imagegen 자산의 실제 재사용성을 확정한다.

### Phase B: See-through baseline 검증

```text
B1. See-through/ComfyUI-See-through 실행 경로 선택
B2. canonical_front 입력으로 layer bundle 생성
B3. layer alpha/draw-order 품질 측정
B4. 내부 layer_manifest_draft 작성
B5. imagegen 후보와 See-through 출력 중 어느 쪽이 낫는지 비교
```

목표:
See-through를 MVP 핵심 baseline으로 둘지, optional reference tool로 낮출지 결정한다.

### Phase C: 자체 툴 개발 전 검증

```text
C1. layer_manifest schema 최소화
C2. layer normalizer spike
C3. previewer spike
C4. QA report 자동 생성
C5. harness export draft
```

목표:
코드 개발을 시작하기 전에 만들 도구의 입력/출력/판정 기준을 고정한다.

## 테스트 진행 기록 템플릿

새 실험은 아래 형식으로 계속 추가한다.

```yaml
id:
date:
owner:
status: UNVERIFIED
hypothesis:
input:
command:
output:
metric:
pass_condition:
fail_condition:
result:
evidence_files:
decision: keep | revise | discard
next_action:
```

## 진행 로그

| ID | 날짜 | 상태 | 가설 | 결과 | Evidence 파일 | 다음 액션 |
|---|---|---:|---|---|---|---|
| IMG-001 | 2026-06-02 | OBSERVED | imagegen으로 canonical/parts/underpaint 후보 생성 가능 | 후보 생성은 가능하나 final PSD는 불가 | `experiments/imagegen-limit-test-001/results.md` | crop/mask smoke |
| IMG-002 | 2026-06-02 | OBSERVED | no-label + 파츠군별 생성이 더 실용적 | mouth/eye/underpaint 후보가 더 좋음 | `experiments/imagegen-limit-test-002/results.md` | mouth/eye 합성 smoke |
| IMG-003 | 2026-06-02 | VERIFIED | imagegen mouth/eye PNG에서 실제 crop/mask 후보 생성 가능 | mouth 14개, eye 18개 crop/mask 생성 PASS | `experiments/validation-smoke-001/reports/crop_mask_composite_report.json` | semantic 분류 |
| IMG-004 | 2026-06-02 | OBSERVED | canonical 위에 mouth/eye 후보를 합성할 수 있다 | 합성 PNG 5개 생성. mouth는 유망, eye는 바로 production 불가 | `experiments/validation-smoke-001/composites/` | 위치/분류 보정 |
| ALIGN-001 | 2026-06-02 | VERIFIED | 스크립트가 좌표와 alpha bbox로 mouth/iris 후보를 자동 정렬할 수 있다 | anchor/mouth/iris 정렬 PASS. mouth error <= 0.5px, iris error <= 0.6px | `experiments/coordinate-align-001/reports/coordinate_alignment_report.json` | full eye grouping |
| EYE-001 | 2026-06-02 | DISCARDED | eye_white/iris/lash 후보를 semantic group으로 조립하면 full eye replacement가 되는가 | technical grouping은 됐지만 human review에서 위치/미술 품질 FAIL | `experiments/eye-grouping-001/reports/eye_grouping_report.json` | canonical eye geometry/mask 기반 재설계 |
| FCANVAS-001 | 2026-06-02 | OBSERVED | mouth crop을 canonical과 같은 full-canvas layer로 만들면 runtime placement가 필요 없어지는가 | full-canvas/no-runtime-place PASS, visual quality REVISE | `experiments/full-canvas-layer-001/reports/full_canvas_layer_report.json` | previewer smoke |
| CANON-EYE-001 | 2026-06-02 | VERIFIED | canonical 원본 눈에서 geometry/mask를 추출할 수 있는가 | iris delta/ROI/mask PASS | `experiments/canonical-eye-001/reports/canonical_eye_geometry_report.json` | canonical 기반 blink 재설계 |
| BLINK-001 | 2026-06-02 | DISCARDED | sheet closed-lid 후보만 canonical eye ROI 안에 얹으면 blink layer가 되는가 | ROI 안에는 들어오지만 visual alignment FAIL | `experiments/blink-001/reports/blink_report.json` | edit/inpaint 또는 수동 split |
| MOUTH-STYLE-001 | 2026-06-02 | OBSERVED | mouth 후보를 expression/style 기준으로 shortlist/reject할 수 있는가 | expression/shortlist/reject PASS, visual quality REVISE | `experiments/mouth-style-001/reports/mouth_candidate_score_report.json` | human review shortlist |
| CREATURE-SCHEMA-001 | 2026-06-02 | VERIFIED | 비인간 캐릭터 anchor schema를 human과 분리할 수 있는가 | human/dog/cat required anchors와 missing-anchor rule 정의 | `experiments/creature-schema-001/reports/anchor_schema_report.json` | 비인간 fixture 생성 전 대기 |
| DOC-SSOT-CLEANUP-001 | 2026-06-03 | VERIFIED | 문서가 많아져도 최신 생산 방향을 한 곳에서 복원할 수 있는가 | 루트 플랜을 얇은 SSOT 진입점으로 교체하고, 옛 6주 MVP 플랜을 archive로 이동 | `experiments/doc-ssot-cleanup-001/reports/doc_ssot_cleanup_report.json` | PSD/LIVE2D 문서 생성 |
| EXT-001 | 2026-06-02 | BLOCKED | See-through가 canonical을 유용한 PSD layer로 분해한다 | repo는 확보했지만 로컬 Mac 직접 처리 미통과 | `experiments/validation-smoke-001/reports/see_through_environment_report.md` | remote GPU 또는 ComfyUI 별도 Gate |
| LYR-001 | TBD | UNVERIFIED | layer normalizer로 후보들을 내부 manifest로 통합 가능 | 미실행 | TBD | schema spike |
| PRV-001 | TBD | UNVERIFIED | 경량 previewer로 파츠 움직임 검수 가능 | 미실행 | TBD | Canvas/Pixi spike |

## 플랜 확정 기준

아래 조건을 만족하면 `2d-vtuber-ai-tool-plan.md`의 6주 MVP를 evidence-backed plan으로 승격한다.

```text
1. imagegen 후보가 최소 mouth/eye 합성 smoke를 통과한다.
2. See-through 또는 대체 baseline의 실행 가능/불가능이 evidence로 기록된다.
3. layer_quality_report.json 또는 동등한 수동 리포트가 존재한다.
4. layer_manifest.json 초안이 실제 파일을 참조한다.
5. previewer spike가 최소 3개 parameter를 움직인다.
6. 실패한 항목이 플랜에서 낮은 우선순위 또는 보류로 이동한다.
7. 한 개 이상의 실험이 공용 하네스 후보로 재실행 가능하다.
```

## 지금 당장 가장 중요한 검증 3개

```text
1. full-canvas mouth layer를 previewer에 연결해 runtime placement 제거 검증
2. blink는 sheet 후보를 폐기하고 canonical edit/inpaint 또는 수동 split 경로 설계
3. See-through/ComfyUI-See-through를 remote GPU, HuggingFace Space, ModelScope, 또는 별도 ComfyUI 환경 중 어디서 검증할지 선택
```

좌표 기반 정렬 smoke 결과 기준으로 imagegen mouth/iris 보강 전략은 완전 폐기할 필요가 없다. 위치 조정은 스크린샷 기반 AI 판단이 아니라 anchor/bbox/alpha center/placement_error 기반으로 진행해야 한다. 다만 full eye replacement는 `eye-grouping-001`에서 실패했으므로 sheet-part semantic grouping 경로를 버리고 canonical eye geometry/mask 기반으로 다시 설계해야 한다. See-through 중심 플랜은 현재 로컬 Mac evidence 기준 optional 또는 remote-GPU validation 대상으로 낮춰야 한다.

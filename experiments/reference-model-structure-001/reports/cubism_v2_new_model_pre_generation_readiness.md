# Cubism v2 New Model Pre-generation Readiness

## 결론

- status: `READY_FOR_CHARACTER_GENERATION_CHECKLIST`
- 스킬화 결정: `UPDATE_EXISTING_SKILL_AND_HARNESS`
- 추가 모델 분석 결정: `DO_NOT_EXPAND_FULL_RUNTIME_BEYOND_STRONG20_FOR_V2_STANDARD_NOW`
- 파츠 spec 결정: `KEEP_64_PART_V2_STANDARD`
- 보조 런타임 메타데이터: `PASS`

## 왜 strong20 밖 전체 런타임 분석을 지금 안 늘리나

- all57은 이미 static structure/parameter/deformer/physics 설계표에 반영됐고, strong20은 runtime render/Core/single-parameter/motion/physics evidence를 모두 통과했다. v2_standard 첫 production 설계에는 충분하다.
- 더 분석할 때는 v2_rich/effect/비인간/측면/복잡한 팔처럼 새 모델 목표가 바뀔 때다.

## 단일 파라미터 Sweep 반영

- evidence: `experiments/live2d-strong-model-pattern-001/reports/strong20_parameter_single_sweep_report.json`
- samples: `320`
- parameters: `27`

| Category | Samples | Parameters | Median Changed | Max Changed |
|---|---:|---:|---:|---:|
| body_angle | 108 | 9 | 0.026783 | 0.331323 |
| eye | 156 | 11 | 0.004109 | 0.331338 |
| hair | 22 | 3 | 0.040611 | 0.080211 |
| mouth | 34 | 4 | 0.024491 | 0.059225 |

## 보조 런타임 메타데이터 반영

- evidence: `experiments/reference-model-structure-001/reports/all57_runtime_metadata_extras.json`
- cdi3: `50`
- pose3: `22`
- userdata3: `6`
- exp3 model groups: `19`
- hit area models: `25`
- motionsync3: `4`
- 결정: `DO_NOT_BLOCK_FIRST_CHARACTER_IMAGE`


## 새 캐릭터 생성 전 체크리스트

### G0_CONCEPT - 캐릭터 고르기

PASS:
- 정면 또는 거의 정면의 상반신 캐릭터다.
- 눈, 입, 앞머리, 옆머리, 뒷머리, 목, 어깨/팔 경계가 한눈에 보인다.
- 큰 소품, 복잡한 손가락, 얼굴을 가리는 장식, 강한 투명 이펙트를 넣지 않는다.
- 1024/1536/2048 중 하나를 쓸 수 있지만 해상도보다 파츠 분리 가능성이 우선이다.

FAIL:
- 옆얼굴/극단 포즈라 반대 방향 회전 keyform을 만들기 어렵다.
- 머리카락이 얼굴/눈/입을 과하게 덮어 mask가 필수다.
- 팔이 몸통과 복잡하게 겹쳐 shoulder/arm simple 범위를 넘는다.

### G1_PART_TAXONOMY - 파츠 나누기

PASS:
- 64파트 v2_standard taxonomy를 기준으로 face/eye/mouth/hair/body/clothing 후보가 모두 있다.
- 눈 L/R 각각 white/iris/pupil/highlight/lash/lid/underpaint가 있다.
- 입은 line/inner/lip masks/teeth/tongue/corners가 분리된다.
- 머리는 front/side/back이 분리되고 최소 5개 physics group에 연결 가능하다.
- underpaint 후보가 face/eye/hair/body에서 누락되지 않는다.

FAIL:
- 한 파츠가 여러 기능을 합쳐서 ParamEyeOpen/MouthOpenY/HairFront keyform을 분리하기 어렵다.
- alpha 테두리가 지저분하거나 bbox crop이 너무 빡빡하다.

### G2_STRUCTURE - 구조 자동검사

PASS:
- v2_standard floor: parameters >=25, warp >=35, rotation >=8, keyform >=120, physics_groups >=4.
- CMO3 inspector before/after 비교에서 warp/keyform 증가가 검출된다.
- Core/runtime export 후 Parameters/Parts/Drawables snapshot이 생성된다.

FAIL:
- ArtMesh/Parameter만 있고 Warp/Rotation Deformer나 KeyformBinding이 0에 가깝다.
- runtime은 보이지만 CMO3 구조가 shallow import 수준이다.

### G3_MOTION_VISUAL - 움직임 보기

PASS:
- 단일 파라미터 sweep에서 ParamAngleX/Y, ParamEyeLOpen/ROpen, ParamMouthOpenY/Form, ParamHairFront/Side가 nonblank 변화를 만든다.
- neutral vs extreme strip에서 눈/입/머리/몸각도 변화가 잘리고 겹치지 않는다.
- mask/draw-order risk가 높은 파츠는 onion-skin 또는 before/after strip으로 사람이 확인한다.

FAIL:
- 파라미터를 움직여도 화면 변화가 거의 없다.
- 움직임은 생기지만 눈/입/머리/팔이 서로 앞뒤 순서를 깨뜨린다.

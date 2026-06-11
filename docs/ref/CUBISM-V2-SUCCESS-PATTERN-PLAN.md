# Cubism v2 Success Pattern — 분석·기준치 레퍼런스

Updated: 2026-06-11 (문서 다이어트 — 플랜 절은 `docs/archive/2026-06-11-pre-autorig-leftovers/CUBISM-V2-SUCCESS-PATTERN-PLAN-planning-sections.md`로 분리)

공식 57모델 분석에서 도출한 **수치 기준·티어·택소노미·파라미터 표준**. AUTORIG 품질 사다리와
파라미터 ID 표준(트래킹 맵 재사용)의 근거 문서로 잔류한다. Cubism Editor 운영 플랜은 폐기·아카이브됨.

Primary source:

```text
/Users/family/jason/Vtube/experiments/reference-model-structure-001/reports/cubism_success_pattern_spec.md
```

## Minimum Gate

```text
ArtMesh >= 20
Parameter >= 15
Warp Deformer >= 8
Rotation Deformer >= 1
KeyformBinding >= 20
Physics Group >= 1 when hair is medium/long
```

## Model Tiers (품질 사다리)

```text
v2_min:
  20-25 parts
  goal: pass deformer/keyform/physics structure gate
  use when: proving the workflow works end to end

v2_standard:
  50-70 parts
  goal: natural eye, mouth, hair, and body/head angle motion
  use when: v2_min structure passes and the art direction is accepted

v2_rich:
  90+ parts
  goal: approach official core sample expressiveness
  use when: v2_standard passes visual and runtime evidence gates
```

```text
v2_min is not a finished broadcast model.
v2_standard is the first serious production candidate tier.
v2_rich is the official-sample-like expression tier.
```

Standard target:

```text
ArtMesh 50-120
Parameter 25-60
Warp Deformer 25-60
Rotation Deformer 5-25
KeyformBinding 90-250
Physics Group 2-8
```

(참고: AUTORIG rig v1.3 = 41파트·14파라미터·9워프 — v2_min 통과, v2_standard로 사다리 진행 중.)

## Part Taxonomy

Eye:

```text
eye white L/R
iris/pupil L/R
upper eyelid L/R
lower eyelid or lash L/R
brow L/R
```

Mouth:

```text
mouth line
upper lip or upper mouth mask
lower lip or lower mouth mask
mouth inner
teeth/tongue optional
```

Hair:

```text
front hair clumps
side hair L/R
back hair
long strand or twin-tail groups when present
```

Body angle:

```text
face base
head container
neck
upper body/torso
shoulders
arms/hands optional for v2.1
```

## Parameters (Cubism 표준 ID — 유지 결정의 근거)

Required:

```text
ParamAngleX
ParamAngleY
ParamAngleZ
ParamBodyAngleX
ParamBodyAngleY
ParamEyeLOpen
ParamEyeROpen
ParamEyeBallX
ParamEyeBallY
ParamMouthOpenY
ParamMouthForm
ParamBreath
```

Recommended:

```text
ParamBrowLY
ParamBrowRY
ParamHairFront
ParamHairSideL
ParamHairSideR
ParamHairBack
```

## Deformer And Keyform Scope (키폼 사다리 목표치)

Required deformer groups:

```text
root/body warp
head/face warp
eye L/R warp
mouth warp
front hair warp
side/back hair warp
neck/body angle warp
at least one rotation deformer for head, hair, or body
```

Required keyforms:

```text
AngleX -30/0/+30
AngleY -30/0/+30
AngleZ -10/0/+10
EyeOpen L/R 0/0.5/1
MouthOpenY 0/0.5/1
MouthForm -1/0/+1
Hair swing left/neutral/right
BodyAngleX -10/0/+10
```

## 이미지 생성 조건

현행 생성 조건의 SSOT는 `docs/ref/AUTORIG-MASTER-SPEC.md` (마스터 1장 + 입 4상태 시트 1장).
이 문서의 구 프롬프트 제약(정면 상반신·파트 실루엣 분리·단일 소스 등)은 MASTER-SPEC 조건표에 흡수됨.

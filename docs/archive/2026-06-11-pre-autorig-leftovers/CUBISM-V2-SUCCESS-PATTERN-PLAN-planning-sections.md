# Cubism v2 Success Pattern Plan — 플랜 절 (아카이브)

2026-06-11 문서 다이어트로 `docs/ref/CUBISM-V2-SUCCESS-PATTERN-PLAN.md`에서 분리.
잔류본에는 분석·기준치(게이트 수치/티어/택소노미/파라미터/키폼 스코프)만 남았다.
아래 절들은 Cubism Editor 수동 저작 경로(2026-06-10 폐기)의 운영 플랜이라 역사 보존용.

- Decision (002를 success-pattern-first로 설계) — 대체: AUTORIG 파이프라인 (`docs/ref/AUTORIG-PIPELINE-V1.md`)
- Material-Pack-First Addendum (16종 소재 목록) — 대체: 마스터 1장 + 입 시트 1장 (`docs/ref/AUTORIG-MASTER-SPEC.md`)
- Validation Gates (compare_cmo3_structure_reports) — CMO3 = Cubism Editor 산출물, 폐기 경로
- Review Strategy (G0–G3) — 대체: H1/H1.5/H2 관제탑 게이트 + P5 자동 검증 3종
- Harness And Skill Routing — 당시 라우팅 스냅샷 (같은 폴더의 VTUBE-HARNESS-SKILL-ROUTING-AUDIT.md 참조)

---

## Decision (2026-06-06)

The next Vtube model is designed from the official Cubism success-pattern spec first.
Do not start from `imagen-live2d-001`, and do not require 2048 resolution by default.

Legacy role:

```text
imagen-live2d-001 = shallow-rig failure fixture unless manually rerigged
Mini Cubism projects = local preview / taxonomy / physics references only
official samples = structure references only, no art/texture/PSD reuse
```

## Material-Pack-First Addendum

The next default character experiment is `cubism-v2-new-character-002` and should follow
`CUBISM-V2-MATERIAL-PACK-FIRST-GENERATION.md` (same archive folder).

Do not repeat the material-pack-late repair pattern from `cubism-v2-new-character-001`.

Generate a coordinated same-character set at the beginning:

```text
source front image
face_base_clean
eye_L/R_open
eye_L/R_clean_socket
eye_L/R_half_closed
eye_L/R_mostly_closed
eye_L/R_closed
eye_L/R_closed_underpaint
mouth_base_clean
mouth_closed
mouth_small_open
mouth_wide_open
mouth_o_vowel
mouth_inner
mouth_teeth
mouth_tongue
```

The open-eye assets are required because relying on the source image alone makes later eye separation fragile. The clean bases and keyposes must be style-matched before Mini Cubism or Cubism rigging starts.

(참고: 이 16종 목록은 2026-06-11 "생성 목록 확정"으로 마스터 1장 + 입 4상태 시트 1장으로 축소됨 — 눈 감김은 ARAP 워프, 가시 레이어는 분해+재스킨.)

## Validation Gates

Before image generation:

```text
part taxonomy selected
parameter list selected
deformer groups selected
first-pass physics scope selected
legacy fixtures explicitly excluded from default path
```

After Cubism authoring:

```bash
python3 scripts/compare_cmo3_structure_reports.py \
  --before <before-cmo3-structure-report.json> \
  --after <after-cmo3-structure-report.json> \
  --expect-warp-increase \
  --expect-keyform-binding-increase \
  --out-json <delta.json> \
  --out-md <delta.md>
```

Required visual evidence:

```text
eye parameter extremes
mouth parameter extremes
hair swing extremes
head/body angle extremes
draw order and overhang note
```

Runtime export smoke comes after the CMO3 structure gate passes.

## Review Strategy

Do not discard the unified review app. Discard only old standalone experiment preview pages.

```text
keep:
  /Users/family/jason/Vtube/review_app
  scripts/build_review_manifest.py pattern
  scripts/review_app_server.py

legacy/archive only:
  per-experiment preview/index.html pages
  forced all-O Imagen review as quality evidence
  Mini Cubism visual-fail contact sheets as production baselines
```

The current review surface should be reused with a Cubism v2-specific manifest.
The manifest should separate review into four gates:

```text
G0 concept:
  checks: single-source style match, front/near-front pose, clean silhouette
  output: concept_accept / concept_revise / concept_reject

G1 part taxonomy:
  checks: each required part exists, full-canvas alignment, alpha cleanliness, no missing underpaint
  output: part_keep / part_revise / part_reject with part_id

G2 Cubism structure:
  checks: ArtMesh/Parameter/Deformer/Keyform counts, before/after deltas
  output: structure_pass / structure_fail
  source: CMO3 reports, not visual-only review

G3 motion visual:
  checks: eye, mouth, hair, body/head angle extremes, draw order, overhang
  output: motion_keep / motion_revise / motion_reject
```

Review artifact policy:

```text
human visual FAIL never becomes production success
numeric/structure PASS and visual PASS stay separate
review_app saves human verdicts; CMO3 inspector saves structural verdicts
contact sheets are acceptable for broad visual review, but final Cubism gate needs GUI screenshots
```

For v2_min, review should be intentionally small:

```text
concept sheet: 3-6 candidates
part sheet: 20-25 required parts
motion sheet: eye/mouth/hair/body extremes only
no accessory/clothing/rich mask review in v2_min
```

For v2_standard:

```text
part sheet: 50-70 parts grouped by eye/mouth/hair/body/accessory
motion sheet: neutral + key extremes + physics settle frames
require visual pass before considering v2_rich
```

For v2_rich:

```text
review richer masks, expressions, arm/clothing toggles, and advanced effects
only after v2_standard passes structure and visual gates
```

## Harness And Skill Routing

Current default:

```text
skill: vtube-cubism-success-pattern-workflow
harness: vtube-cubism-success-pattern-spec
supporting harness: vtube-reference-model-structure
```

Legacy or fixture-only:

```text
vtube-imagen-cubism-mvp
vtube-imagen-cubism-mvp-success-pattern
vtube-comfyui-seethrough-mac
vtube-mini-cubism-hair-face-motion-v1
vtube-mini-cubism-face-v1
vtube-seethrough-70-custom-split-v2
```

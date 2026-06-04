# Concept Regeneration 001

이 실험은 White Wolf Goth 컨셉을 새로 생성해 Live2D 파츠 순도 검수와
Cubism PSD 재생성까지 테스트하기 위한 작업 공간이다.

## Source

- 컨셉 기준: `docs/ref/WHITE-WOLF-GOTH-CONCEPT.md`
- 공통 파츠 기준: `docs/ref/LIVE2D-PART-SCHEMA.md`
- 운영 계획: `docs/ref/LIVE2D-PART-PURITY-PIPELINE.md`

## Directory

```text
experiments/concept-regeneration-001/
  reference/
  canonical/
  production_layers_candidate/
  reference_pack/
  reports/
```

## Flow

1. `canonical/canonical_front_2048.png`를 만든다.
2. `production_layers_candidate/*.png`에 full-canvas 2048 파츠 후보를 만든다.
3. concept review manifest를 생성한다.
4. `review_app`에서 시각 검수한다.
5. `reports/part_visual_review.json`과 `reports/ai_fix_queue.json`을 저장한다.
6. `O` 통과 파츠만 PSD 후보로 사용한다.
7. Cubism Editor 실제 import smoke를 기록한다.

## Current Status

- Status: PASS_WITH_CUBISM_IMPORT
- Canonical: `canonical/canonical_front_2048.png`
- Bootstrap candidates: `production_layers_candidate/*.png`
- Review UI integration: `새 컨셉 파츠 35개` 탭
- Human review evidence: `reports/part_visual_review.json`
- AI fix queue: `reports/ai_fix_queue.json`
- PSD gate: `reports/psd_candidate_gate_report.json`
- PSD regeneration: `import_ready_candidate.psd` and `import_ready.psd`
- Cubism Editor import smoke: `reports/cubism_import_smoke.json`

## Current Queue Smoke

- `concept__R_upper_lash`: `X`, `hair_mixed`
- `concept__L_ear_outer`: `REVISE`, `hair_mixed`, `alpha_dirty`

These are bootstrap rough-mask failures used to verify that the review UI and
AI fix queue work for the new concept. They are not final production judgements.

## PSD Gate

Build the gated PSD candidate:

```bash
python3 scripts/build_concept_psd_candidate.py
```

Rules:

- Only `O` parts are copied to `psd_candidate_layers/`.
- `X`, `REVISE`, `REFERENCE_ONLY`, and unreviewed parts are excluded.
- If no part is `O`, `import_ready_candidate.psd` is not created.
- `import_ready.psd` is not promoted until Cubism Editor actual import smoke passes.

Current gate result:

```text
PASS_WITH_CUBISM_IMPORT
```

Current accepted PSD layers:

- `face_underpaint`
- `neck`
- `L_highlight`
- `R_highlight`
- `mouth_line`
- `choker`

Important: these are AI technical-smoke `O` parts for proving PSD/Cubism import,
not final visual approval for the complete 35-part concept model.

# Live2D Part Purity Pipeline

이 문서는 현재 `review_app` 검수 페이지를 중심으로 파츠 세분화, 파츠 순도 검증,
이미지 재생성, PSD 재생성을 반복하는 운영 계획이다.

## 목표

- Cubism에 넣을 `import_ready.psd`에는 production 파츠만 포함한다.
- 입 10개, 눈깜빡임 3개, overlay는 reference/evidence로만 사용한다.
- 주인님이 검수 페이지에서 직접 보고 `O`, `X`, `수정 필요`, `참고용`을 저장한다.
- AI는 사람이 저장한 `ai_fix_queue.json`만 읽고 다음 cleanup/regeneration 작업을 한다.
- 최종 승격 기준은 자동 metadata 통과가 아니라 Cubism Editor 실제 import와 파츠 시각 품질이다.

## Source Of Truth

| 용도 | 파일 |
| --- | --- |
| 파츠 기준/오염 기준 | `docs/ref/LIVE2D-PART-SCHEMA.md` |
| 검수 UI manifest | `review_app/review_manifest.json` |
| 이미지 생성/정리 대상 | `experiments/part-purity-001/part_generation_manifest.json` |
| 사람 검수 원본 | `experiments/part-purity-001/reports/part_visual_review.json` |
| AI 수정 큐 | `experiments/part-purity-001/reports/ai_fix_queue.json` |
| Cubism PSD 입력 | `experiments/cubism-material-pack-001/production_layers/*.png` |
| PSD 산출물 | `experiments/cubism-material-pack-001/import_ready.psd` |

## See-through / ComfyUI Branch

한 장짜리 완성 일러스트를 프롬프트만으로 깨끗한 Live2D 파츠로 다시 뽑는 방식은 한계가 있다.
따라서 `see-through-layer-decomp-001`은 See-through 계열 layer decomposition을 검증하는
별도 branch다. Mac Apple Silicon에서는 ComfyUI/노드/모델 로드는 확인했지만 실제
`GenerateLayers` inference가 MPS 메모리 한계로 실패했다. 실제 decomposition은 Ubuntu CUDA에서
실행하고, 결과 검수/PSD gate는 Mac에서 진행한다.

Mac setup smoke:

```bash
python3 scripts/setup_comfyui_seethrough_mac.py
```

Ubuntu CUDA 실행 문서:

```text
docs/ref/UBUNTU-CUDA-SEETHROUGH-RUNBOOK.md
```

Ubuntu에서 `*_layers.json`과 PNG가 생기면 Mac으로 가져와서:

```bash
python3 scripts/normalize_seethrough_outputs.py --layers-json <ComfyUI output *_layers.json>
python3 scripts/build_review_manifest.py
python3 scripts/review_app_server.py --port 8040
```

규칙:

- See-through raw layer는 production 성공으로 보지 않는다.
- `See-through 후보` 탭에서 사람이 `O/X/REVISE`를 저장한다.
- `semantic_too_coarse`는 Live2D 파츠 기준보다 너무 넓은 layer일 때 사용한다.
- `depth_order_wrong`은 앞/뒤 순서 또는 occlusion이 잘못된 후보에 사용한다.
- `O`인 production candidate만 `scripts/build_seethrough_psd_candidate.py`에서 PSD 후보가 된다.
- `import_ready.psd` 승격은 Cubism Editor 실제 import smoke 이후에만 가능하다.

## Current Page Usage

서버 실행:

```bash
python3 scripts/build_review_manifest.py
python3 scripts/review_app_server.py --port 8040
```

브라우저:

```text
http://127.0.0.1:8040/
```

검수 순서:

1. `PSD 파츠 27개` 탭에서 production 파츠를 하나씩 본다.
2. 기본 보기인 `확대 비교`에서 파츠가 실제 캐릭터 위치에서 깨끗한지 확인한다.
3. `파츠만 확대`에서 투명 PNG 자체에 다른 파츠가 섞였는지 확인한다.
4. 문제 없으면 `O 통과`를 누른다.
5. 버릴 수준이면 `X 실패`, cleanup 가능하면 `수정 필요`를 누른다.
6. 문제 태그를 고른다.
7. 메모를 짧게 적고 `검수 저장`을 누른다.
8. 오른쪽 `AI 수정 큐`에 들어간 항목만 다음 AI 작업 대상으로 삼는다.

판정 기준:

| 판정 | 의미 | 다음 단계 |
| --- | --- | --- |
| `O` | production 후보 유지 | PSD 재생성 후보 |
| `X` | 폐기 또는 재생성 | AI regenerate 우선 |
| `REVISE` | cleanup/inpaint 대상 | AI cleanup 우선 |
| `REFERENCE_ONLY` | PSD 제외 참고용 | reference pack 유지 |

## Part Segmentation Plan

현재 v1 production 파츠 27개는 Cubism import smoke를 위한 최소 파츠다. 다음 단계는
모든 파츠를 무조건 더 잘게 뽑는 것이 아니라, 순도 검수에서 문제가 확인된 파츠부터
세분화한다.

### Tier A: 먼저 정리할 필수 파츠

이 파츠들은 Cubism에서 표정과 시선 품질에 직접 영향을 준다.

- 눈: `L/R_eye_white`, `L/R_iris`, `L/R_pupil`, `L/R_highlight`, `L/R_upper_lash`, `L/R_lower_lash`
- 입: `mouth_line`, `mouth_inner`, `teeth`, `tongue`
- 얼굴: `face_base`, `face_underpaint`, `neck`
- 머리카락 경계: `front_hair`, `L/R_side_hair`, `back_hair`

### Tier B: 문제 발생 시 세분화할 후보

이 후보들은 v1 PSD에는 아직 전부 필요하지 않다. 단, 순도 검수에서 오염이 반복되면
개별 generation target으로 승격한다.

- 얼굴: 볼 홍조, 코 그림자, 얼굴 외곽선, 귀 좌우, 피부 그림자
- 머리카락: 앞머리 다발별 분리, 옆머리 좌우 세부 다발, 뒷머리 위/아래, 머리 하이라이트, 머리 그림자
- 눈: 눈꺼풀 덮개, 윗눈꺼풀 접힘선, 아랫눈꺼풀 접힘선, 눈 그림자
- 입: 윗입술선, 아랫입술선, 좌우 입꼬리, 윗니, 아랫니, 입 안쪽 그림자
- 의상: 목장식, 소매 좌우, 리본/장신구, 의상 그림자

세분화 승격 조건:

- 같은 파츠가 2회 이상 `hair_mixed`, `skin_mixed`, `eye_white_mixed`, `iris_mixed`를 받는다.
- 파츠가 Cubism deformation 중 다른 부위를 끌고 움직일 위험이 있다.
- bbox가 너무 타이트해서 Cubism Editor에서 파츠 가장자리가 잘린다.
- 한 레이어 안에 서로 다른 deformer를 써야 하는 요소가 섞여 있다.

## Purity Validation Gate

AI가 새 이미지를 만들면 바로 PSD로 승격하지 않는다.

1. 새 PNG를 `production_layers/` 후보 위치에 둔다.
2. `scripts/build_review_manifest.py`를 실행해 검수 manifest를 갱신한다.
3. 검수 페이지에서 해당 파츠를 다시 본다.
4. `O 통과`가 되기 전까지 `import_ready.psd` 승격 대상에서 제외한다.
5. `X`와 `수정 필요`는 `ai_fix_queue.json`에 남긴다.

실패 태그별 기본 처리:

| 태그 | 기본 처리 |
| --- | --- |
| `hair_mixed` | 마스크 재생성 또는 파츠 단독 재생성 |
| `skin_mixed` | 마스크 cleanup 후 필요 시 inpaint |
| `eye_white_mixed` | 눈 파츠를 흰자/홍채/동공/속눈썹으로 다시 분리 |
| `iris_mixed` | 홍채/동공/하이라이트 분리 재생성 |
| `line_cut` | bbox padding 확장 후 crop/regenerate |
| `alpha_dirty` | alpha cleanup |
| `bbox_too_tight` | 안전 여백을 둔 full-canvas PNG 재생성 |
| `missing_underpaint` | 숨겨질 밑색/언더페인트 추가 |
| `wrong_shape` | canonical reference 기준 재생성 |

## Image Generation And Cleanup Plan

AI 작업자는 `ai_fix_queue.json`만 읽고 다음 순서로 처리한다.

1. `X` 항목을 먼저 재생성한다.
2. `REVISE` 항목은 alpha cleanup, mask cleanup, inpaint 순서로 가볍게 고친다.
3. 고친 결과는 2048x2048 full-canvas PNG로 유지한다.
4. 파츠의 실제 픽셀 영역은 원래 bbox 주변에 있어야 한다.
5. reference mouth/blink 이미지는 production layer로 넣지 않는다.
6. 새 결과물은 별도 실험 폴더에 저장한 뒤 검수 페이지로 다시 본다.

권장 다음 실험:

```text
experiments/part-purity-002/
  production_layers_candidate/
  reports/
    generation_report.json
    cleanup_report.json
    qa_report.md
```

## PSD Regeneration Plan

파츠 검수 후 PSD를 다시 만들 때는 다음 gate를 통과해야 한다.

1. `part_visual_review.json`에서 production 파츠가 `O` 또는 명시적으로 허용된 `REVISE`인지 확인한다.
2. `X`, `DISCARDED`, `REFERENCE_ONLY` production 파츠는 PSD 후보에서 제외한다.
3. `scripts/build_cubism_material_pack.py --character-id vtube_001`로 pack을 재생성한다.
4. `scripts/validate_cubism_psd_inputs.py --pack experiments/cubism-material-pack-001`를 실행한다.
5. Python PSD metadata check를 통과해도 성공으로 보지 않는다.
6. Cubism Editor에서 실제 import smoke를 다시 기록한다.
7. 레이어가 flatten되지 않고 production parts로 보이면 `import_ready.psd`로 승격한다.

## White Wolf Goth Concept PSD Gate

`concept-regeneration-001`은 기존 보라머리 pack과 분리된 새 컨셉 실험이다.
이 실험은 다음 명령으로 PSD 후보를 만든다.

```bash
python3 scripts/build_concept_psd_candidate.py
```

규칙:

- `reports/part_visual_review.json`에서 `O`인 파츠만 PSD 후보가 된다.
- `X`, `REVISE`, `REFERENCE_ONLY`, 미검수 파츠는 제외된다.
- O 파츠가 하나도 없으면 `import_ready_candidate.psd`는 생성되지 않는다.
- `--promote`는 `reports/cubism_import_smoke.json`이 성공일 때만 `import_ready.psd`를 만든다.

현재 White Wolf Goth는 bootstrap 파츠 후보를 검수하는 단계라 `BLOCKED_NO_O_LAYERS`가 정상이다.

## Current Known Queue

현재 저장된 대표 문제:

- `R_upper_lash`: `X`, `hair_mixed`
- `mouth_inner`: `REVISE`, `bbox_too_tight`, `line_cut`

이 둘은 다음 `part-purity-002`에서 우선 처리한다.

## Acceptance

- 검수 페이지에서 production/reference/overlay가 분리되어 보인다.
- 모든 production 파츠는 사람 검수 결과가 있다.
- `ai_fix_queue.json`에는 `X`와 `REVISE`만 들어간다.
- 새 파츠 PNG는 다시 검수 페이지에서 확인된다.
- PSD 재생성 후 Cubism Editor 실제 import smoke가 남는다.

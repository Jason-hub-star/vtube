# Strong20 Official Cubism Core API Extractor

## Summary

- status: `PASS`
- method: Cubism SDK for Web sandbox probe using Live2DCubismCore-backed Framework model getters
- models: `20/20` PASS
- parameter median: `44.0`
- part median: `19.0`
- drawable median: `85.0`
- masked drawable median: `2.0`
- offscreen median: `0.0`

## Model Rows

| Model | Status | Param | Part | Drawable | Masked | Inverted | Offscreen | Snapshot |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| haru_greeter_pro_jp_haru_greeter_t05 | PASS | 42 | 19 | 84 | 10 | 0 | 0 | `experiments/live2d-strong-model-pattern-001/core_api/haru_greeter_pro_jp_haru_greeter_t05/core_snapshot.json` |
| koharu_haruto_haruto_t01 | PASS | 51 | 17 | 86 | 0 | 0 | 0 | `experiments/live2d-strong-model-pattern-001/core_api/koharu_haruto_haruto_t01/core_snapshot.json` |
| hiyori_pro_ko_hiyori_pro_t11 | PASS | 70 | 24 | 134 | 8 | 0 | 0 | `experiments/live2d-strong-model-pattern-001/core_api/hiyori_pro_ko_hiyori_pro_t11/core_snapshot.json` |
| kei_ko_kei_basic_free_t02 | PASS | 27 | 19 | 59 | 11 | 0 | 0 | `experiments/live2d-strong-model-pattern-001/core_api/kei_ko_kei_basic_free_t02/core_snapshot.json` |
| kei_ko_kei_vowels_pro_t02 | PASS | 31 | 19 | 59 | 11 | 0 | 0 | `experiments/live2d-strong-model-pattern-001/core_api/kei_ko_kei_vowels_pro_t02/core_snapshot.json` |
| koharu_haruto_koharu_t01 | PASS | 52 | 17 | 90 | 0 | 0 | 0 | `experiments/live2d-strong-model-pattern-001/core_api/koharu_haruto_koharu_t01/core_snapshot.json` |
| mao_pro_ko_mao_pro_t06 | PASS | 128 | 31 | 260 | 37 | 10 | 0 | `experiments/live2d-strong-model-pattern-001/core_api/mao_pro_ko_mao_pro_t06/core_snapshot.json` |
| miara_pro_en_miara_pro_t04 | PASS | 138 | 45 | 187 | 9 | 0 | 0 | `experiments/live2d-strong-model-pattern-001/core_api/miara_pro_en_miara_pro_t04/core_snapshot.json` |
| miku_pro_jp_miku_sample_t05 | PASS | 59 | 24 | 110 | 0 | 0 | 0 | `experiments/live2d-strong-model-pattern-001/core_api/miku_pro_jp_miku_sample_t05/core_snapshot.json` |
| natori_pro_ko_natori_pro_t06 | PASS | 96 | 32 | 176 | 9 | 0 | 0 | `experiments/live2d-strong-model-pattern-001/core_api/natori_pro_ko_natori_pro_t06/core_snapshot.json` |
| ren_pro_ko_ren_t01 | PASS | 73 | 51 | 198 | 4 | 3 | 24 | `experiments/live2d-strong-model-pattern-001/core_api/ren_pro_ko_ren_t01/core_snapshot.json` |
| rice_pro_ko_rice_pro_t03 | PASS | 96 | 30 | 178 | 12 | 7 | 0 | `experiments/live2d-strong-model-pattern-001/core_api/rice_pro_ko_rice_pro_t03/core_snapshot.json` |
| tsumiki_tsumiki_t01 | PASS | 46 | 19 | 89 | 5 | 0 | 0 | `experiments/live2d-strong-model-pattern-001/core_api/tsumiki_tsumiki_t01/core_snapshot.json` |
| wanko_wanko_touch_t01 | PASS | 25 | 15 | 33 | 0 | 0 | 0 | `experiments/live2d-strong-model-pattern-001/core_api/wanko_wanko_touch_t01/core_snapshot.json` |
| epsilon_epsilon_t02 | PASS | 37 | 20 | 66 | 0 | 0 | 0 | `experiments/live2d-strong-model-pattern-001/core_api/epsilon_epsilon_t02/core_snapshot.json` |
| chitose_chitose_t01 | PASS | 33 | 20 | 66 | 0 | 0 | 0 | `experiments/live2d-strong-model-pattern-001/core_api/chitose_chitose_t01/core_snapshot.json` |
| haru_haru_t01 | PASS | 33 | 19 | 84 | 0 | 0 | 0 | `experiments/live2d-strong-model-pattern-001/core_api/haru_haru_t01/core_snapshot.json` |
| tororo_hijiki_hijiki_t01 | PASS | 31 | 16 | 56 | 0 | 0 | 0 | `experiments/live2d-strong-model-pattern-001/core_api/tororo_hijiki_hijiki_t01/core_snapshot.json` |
| izumi_izumi_anime_t01 | PASS | 30 | 18 | 69 | 0 | 0 | 0 | `experiments/live2d-strong-model-pattern-001/core_api/izumi_izumi_anime_t01/core_snapshot.json` |
| izumi_izumi_atsu_t01 | PASS | 30 | 18 | 69 | 0 | 0 | 0 | `experiments/live2d-strong-model-pattern-001/core_api/izumi_izumi_atsu_t01/core_snapshot.json` |

## Interpretation

- 이 리포트는 CMO3 편집 구조가 아니라 Cubism runtime/Core-backed drawable 상태를 본다.
- mask/draw order 위험 판단은 이 extractor의 `masked_drawable_ids`, `drawOrder`, `renderOrder`, `offscreen` 값을 우선 근거로 보강한다.
- 저장된 값은 구조 ID와 숫자뿐이며 공식 샘플의 텍스처/이미지 자산은 재사용하지 않는다.

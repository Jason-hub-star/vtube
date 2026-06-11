# All57 Physics Group Design

- generated_at: `2026-06-07T22:40:44.432310+00:00`
- scope: all57 runtime physics where physics3.json exists

## Summary

- model_count: `57`
- physics_present_count: `44`
- group_count_stats: `{'n': 44, 'min': 1, 'p25': 3.0, 'median': 6.0, 'p75': 11.0, 'max': 19, 'mean': 7.32}`
- input_count_stats: `{'n': 44, 'min': 3, 'p25': 12.0, 'median': 18.0, 'p75': 33.25, 'max': 82, 'mean': 22.52}`
- output_count_stats: `{'n': 44, 'min': 2, 'p25': 3.75, 'median': 7.0, 'p75': 20.0, 'max': 63, 'mean': 14.8}`
- output_category_frequency: `{'hair': 196, 'other': 84, 'accessory': 64, 'effect_expression': 271, 'body_angle': 9, 'arm_hand': 9}`

## Tier Guidance

- `v2_min`: 2 groups: hair front/side/back merged plus breath/body secondary motion if the design has medium hair.
- `v2_standard`: 4-6 groups: front hair, side hair L/R, back hair, body/breath, accessory if present.
- `v2_rich`: 8+ groups: split hair strands, ribbons/accessories, skirt/clothing, bust/body, and effect-secondary motion when needed.

## Model Physics

| Model | Mode | Groups | Inputs | Outputs | Output Categories |
|---|---|---:|---:|---:|---|
| `chitose_chitose_t01` | `FULL_STRUCTURE` | 2 | 8 | 2 | `{'hair': 2}` |
| `epsilon_epsilon_t02` | `FULL_STRUCTURE` | 2 | 8 | 4 | `{'hair': 4}` |
| `haru_greeter_pro_jp_haru_greeter_t05` | `FULL_STRUCTURE` | 4 | 14 | 4 | `{'hair': 3, 'other': 1}` |
| `haru_haru_t01` | `FULL_STRUCTURE` | 2 | 8 | 2 | `{'hair': 2}` |
| `hiyori_movie_pro_ko_hiyori_movie_pro_t02` | `FULL_STRUCTURE` | 0 | 0 | 0 | `{}` |
| `kei_ko_kei_basic_free_t02` | `FULL_STRUCTURE` | 6 | 18 | 7 | `{'hair': 7}` |
| `kei_ko_kei_vowels_pro_t02` | `FULL_STRUCTURE` | 6 | 18 | 7 | `{'hair': 7}` |
| `koharu_haruto_haruto_t01` | `FULL_STRUCTURE` | 4 | 14 | 4 | `{'hair': 3, 'other': 1}` |
| `koharu_haruto_koharu_t01` | `FULL_STRUCTURE` | 5 | 16 | 5 | `{'hair': 3, 'other': 1, 'accessory': 1}` |
| `mao_pro_ko_mao_pro_t06` | `FULL_STRUCTURE` | 16 | 43 | 20 | `{'accessory': 5, 'hair': 10, 'other': 5}` |
| `mark_movie_pro_ko_mark_movie_pro_t02` | `FULL_STRUCTURE` | 0 | 0 | 0 | `{}` |
| `miara_pro_en_miara_pro_t04` | `FULL_STRUCTURE` | 19 | 82 | 63 | `{'accessory': 5, 'other': 8, 'hair': 12, 'effect_expression': 38}` |
| `natori_pro_ko_natori_pro_t06` | `FULL_STRUCTURE` | 11 | 34 | 12 | `{'other': 6, 'hair': 6}` |
| `param_ctrl_pro_ko_haruto_pc_pro_t02` | `FULL_STRUCTURE` | 0 | 0 | 0 | `{}` |
| `param_ctrl_pro_ko_koharu_pc_pro_t02` | `FULL_STRUCTURE` | 0 | 0 | 0 | `{}` |
| `param_ctrl_pro_ko_seesaw_pc_pro_t02` | `FULL_STRUCTURE` | 0 | 0 | 0 | `{}` |
| `param_ctrl_pro_ko_rice_pc_pro_t02` | `FULL_STRUCTURE` | 0 | 0 | 0 | `{}` |
| `param_ctrl_pro_ko_target_pc_pro_t02` | `FULL_STRUCTURE` | 0 | 0 | 0 | `{}` |
| `ren_pro_ko_ren_t01` | `FULL_STRUCTURE` | 16 | 33 | 20 | `{'body_angle': 3, 'other': 8, 'hair': 6, 'arm_hand': 3}` |
| `rice_pro_ko_rice_pro_t03` | `FULL_STRUCTURE` | 9 | 32 | 42 | `{'accessory': 5, 'hair': 2, 'effect_expression': 35}` |
| `shizuku_shizuku_t02` | `FULL_STRUCTURE` | 3 | 6 | 5 | `{'hair': 5}` |
| `tsumiki_tsumiki_t01` | `FULL_STRUCTURE` | 7 | 22 | 9 | `{'accessory': 2, 'hair': 4, 'effect_expression': 2, 'other': 1}` |
| `unitychan_unitychan_t01` | `FULL_STRUCTURE` | 3 | 12 | 3 | `{'hair': 3}` |
| `wanko_wanko_touch_t01` | `FULL_STRUCTURE` | 4 | 14 | 4 | `{'other': 2, 'accessory': 2}` |
| `hiyori_pro_ko_hiyori_pro_t11` | `FULL_STRUCTURE` | 11 | 34 | 35 | `{'accessory': 5, 'hair': 2, 'effect_expression': 28}` |
| `miku_pro_jp_miku_sample_t05` | `FULL_STRUCTURE` | 13 | 37 | 51 | `{'other': 3, 'hair': 23, 'effect_expression': 7}` |
| `tororo_hijiki_hijiki_t01` | `FULL_STRUCTURE` | 1 | 3 | 2 | `{'other': 2}` |
| `tororo_hijiki_tororo_t01` | `FULL_STRUCTURE` | 1 | 3 | 2 | `{'other': 2}` |
| `nito_nito_t01` | `FULL_STRUCTURE` | 0 | 0 | 0 | `{}` |
| `nito_ni-j.model3_runtime` | `RUNTIME_ONLY` | 0 | 0 | 0 | `{}` |
| `nito_nico.model3_runtime` | `RUNTIME_ONLY` | 0 | 0 | 0 | `{}` |
| `nito_nietzsche.model3_runtime` | `RUNTIME_ONLY` | 0 | 0 | 0 | `{}` |
| `nito_nipsilon.model3_runtime` | `RUNTIME_ONLY` | 0 | 0 | 0 | `{}` |
| `izumi_izumi_anime_t01` | `FULL_STRUCTURE` | 3 | 12 | 3 | `{'hair': 3}` |
| `izumi_izumi_atsu_t01` | `FULL_STRUCTURE` | 3 | 12 | 3 | `{'hair': 3}` |
| `izumi_izumi_illust_t01` | `FULL_STRUCTURE` | 3 | 12 | 3 | `{'hair': 3}` |
| `izumi_izumi_suisai_t01` | `FULL_STRUCTURE` | 3 | 12 | 3 | `{'hair': 3}` |
| `gantzert_felixander_gantzert_felixander_t01` | `FULL_STRUCTURE` | 0 | 0 | 0 | `{}` |
| `github_live2d_cubism_web_samples_samples_resources_haru_haru.model3` | `RUNTIME_ONLY` | 4 | 14 | 4 | `{'hair': 3, 'other': 1}` |
| `github_live2d_cubism_web_samples_samples_resources_hiyori_hiyori.model3` | `RUNTIME_ONLY` | 11 | 34 | 35 | `{'accessory': 5, 'hair': 2, 'effect_expression': 28}` |
| `github_live2d_cubism_web_samples_samples_resources_mao_mao.model3` | `RUNTIME_ONLY` | 16 | 43 | 20 | `{'accessory': 5, 'hair': 10, 'other': 5}` |
| `github_live2d_cubism_web_samples_samples_resources_mark_mark.model3` | `RUNTIME_ONLY` | 1 | 4 | 3 | `{'hair': 3}` |
| `github_live2d_cubism_web_samples_samples_resources_natori_natori.model3` | `RUNTIME_ONLY` | 11 | 34 | 12 | `{'other': 6, 'hair': 6}` |
| `github_live2d_cubism_web_samples_samples_resources_ren_ren.model3` | `RUNTIME_ONLY` | 16 | 33 | 20 | `{'body_angle': 3, 'other': 8, 'hair': 6, 'arm_hand': 3}` |
| `github_live2d_cubism_web_samples_samples_resources_rice_rice.model3` | `RUNTIME_ONLY` | 9 | 32 | 42 | `{'accessory': 5, 'hair': 2, 'effect_expression': 35}` |
| `github_live2d_cubism_web_samples_samples_resources_wanko_wanko.model3` | `RUNTIME_ONLY` | 4 | 14 | 4 | `{'other': 2, 'accessory': 2}` |
| `github_live2d_cubism_native_samples_samples_resources_haru_haru.model3` | `RUNTIME_ONLY` | 4 | 14 | 4 | `{'hair': 3, 'other': 1}` |
| `github_live2d_cubism_native_samples_samples_resources_hiyori_hiyori.model3` | `RUNTIME_ONLY` | 11 | 34 | 35 | `{'accessory': 5, 'hair': 2, 'effect_expression': 28}` |
| `github_live2d_cubism_native_samples_samples_resources_mao_mao.model3` | `RUNTIME_ONLY` | 16 | 43 | 20 | `{'accessory': 5, 'hair': 10, 'other': 5}` |
| `github_live2d_cubism_native_samples_samples_resources_mark_mark.model3` | `RUNTIME_ONLY` | 1 | 4 | 3 | `{'hair': 3}` |
| `github_live2d_cubism_native_samples_samples_resources_natori_natori.model3` | `RUNTIME_ONLY` | 11 | 34 | 12 | `{'other': 6, 'hair': 6}` |
| `github_live2d_cubism_native_samples_samples_resources_ren_ren.model3` | `RUNTIME_ONLY` | 16 | 33 | 20 | `{'body_angle': 3, 'other': 8, 'hair': 6, 'arm_hand': 3}` |
| `github_live2d_cubism_native_samples_samples_resources_rice_rice.model3` | `RUNTIME_ONLY` | 9 | 32 | 42 | `{'accessory': 5, 'hair': 2, 'effect_expression': 35}` |
| `github_live2d_cubism_native_samples_samples_resources_wanko_wanko.model3` | `RUNTIME_ONLY` | 4 | 14 | 4 | `{'other': 2, 'accessory': 2}` |
| `github_live2d_cubism_web_motionsync_samples_resources_kei_basic_kei_basic.model3` | `RUNTIME_ONLY` | 6 | 18 | 7 | `{'hair': 7}` |
| `github_live2d_cubism_web_motionsync_samples_resources_kei_vowels_kei_vowels.model3` | `RUNTIME_ONLY` | 6 | 18 | 7 | `{'hair': 7}` |
| `github_live2d_garage_cubism_web_ar_sample_assets_models_rice_rice.model3` | `RUNTIME_ONLY` | 9 | 32 | 42 | `{'accessory': 5, 'hair': 2, 'effect_expression': 35}` |

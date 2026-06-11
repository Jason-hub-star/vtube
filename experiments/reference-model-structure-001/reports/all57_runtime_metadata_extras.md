# Live2D All57 Runtime Metadata Extras

## 결론

- 새 캐릭터 컨셉/이미지 생성 전에 추가로 뽑을 만한 보조 정보는 있다.
- 다만 이것들은 첫 이미지 생성의 blocker가 아니라, 이후 runtime/export/운영 설계 체크리스트다.
- v2_standard 첫 모델은 64파트 taxonomy와 기존 deformer/keyform/physics spec을 유지한다.

## Coverage

| Item | Count |
|---|---:|
| model3_json | 50 |
| cdi3_json | 50 |
| pose3_json | 22 |
| userdata3_json | 6 |
| exp3_json_models | 19 |
| motionsync3_json | 4 |
| hit_area_models | 25 |
| lipsync_group_models | 39 |
| eyeblink_group_models | 47 |

## 평균값

| Item | Avg |
|---|---:|
| cdi_parameter_display_count | 59.42 |
| cdi_part_display_count | 28.24 |
| pose_group_count | 2 |
| expression_count | 7.84 |
| hit_area_count | 1.48 |

## 컨셉 생성 전에 반영할 점

- cdi3의 표시 이름과 그룹은 새 모델 파츠/파라미터 명명 규칙을 사람이 읽기 쉽게 만드는 데 사용한다.
- pose3는 v2_standard에서는 복잡한 팔/의상 전환을 미루고, simple shoulder/arm만 유지할 근거로 사용한다.
- exp3는 기본 표정 세트와 fade 0.5초 전후의 부드러운 전환 기준으로 사용한다.
- HitAreas는 runtime export 때 얼굴/몸 터치 영역을 model3.json에 넣을 체크리스트로 사용한다.
- MotionSync는 Kei 계열의 고급 립싱크 참조다. v2_standard 첫 모델에서는 LipSync group만 준비하고, motionsync3는 v2_rich/고급 립싱크 단계로 미룬다.

## 첫 이미지 생성의 blocker가 아닌 항목

- userdata3
- motionsync3
- pose3 arm switching
- rich expression pack

## 표정 파라미터 상위 패턴

| Parameter | Count |
|---|---:|
| ParamBrowLY | 84 |
| ParamBrowRY | 84 |
| ParamEyeLOpen | 82 |
| ParamEyeROpen | 82 |
| ParamBrowRX | 78 |
| ParamBrowLX | 76 |
| ParamBrowLAngle | 76 |
| ParamEyeLSmile | 74 |
| ParamEyeRSmile | 74 |
| PARAM_EYE_L_OPEN | 60 |
| PARAM_EYE_R_OPEN | 60 |
| PARAM_BROW_L_ANGLE | 60 |
| PARAM_BROW_R_ANGLE | 60 |
| PARAM_BROW_L_Y | 59 |
| PARAM_BROW_R_Y | 59 |
| PARAM_BROW_L_FORM | 59 |
| PARAM_BROW_R_FORM | 59 |
| ParamEyeBallForm | 59 |
| ParamBrowLForm | 58 |
| ParamBrowRForm | 58 |

## MotionSync

- MotionSync 보유 모델: kei_ko_kei_basic_free_t02, kei_ko_kei_vowels_pro_t02, github_live2d_cubism_web_motionsync_samples_resources_kei_basic_kei_basic.model3, github_live2d_cubism_web_motionsync_samples_resources_kei_vowels_kei_vowels.model3
- 공식 문서 기준 `.motionsync3.json`은 BlendRatio/SampleRate/Smoothing/AudioLevelEffectRatio 같은 고급 립싱크 설정을 담는다.
- 첫 v2_standard에서는 `LipSync` group과 `ParamMouthOpenY/ParamMouthForm`를 우선하고, vowels/MotionSync는 다음 단계로 둔다.

## 모델별 요약

| Model | CDI params | Pose groups | Expressions | HitAreas | UserData | MotionSync |
|---|---:|---:|---:|---:|---:|---:|
| chitose_chitose_t01 | 33 | 2 | 7 | 0 | 0 | 0 |
| epsilon_epsilon_t02 | 37 | 0 | 8 | 0 | 0 | 0 |
| haru_greeter_pro_jp_haru_greeter_t05 | 42 | 2 | 0 | 2 | 0 | 0 |
| haru_haru_t01 | 33 | 2 | 8 | 0 | 0 | 0 |
| hiyori_movie_pro_ko_hiyori_movie_pro_t02 | 0 | 0 | 0 | 0 | 0 | 0 |
| kei_ko_kei_basic_free_t02 | 27 | 0 | 0 | 1 | 0 | 1 |
| kei_ko_kei_vowels_pro_t02 | 31 | 0 | 0 | 1 | 0 | 1 |
| koharu_haruto_haruto_t01 | 51 | 0 | 0 | 0 | 0 | 0 |
| koharu_haruto_koharu_t01 | 52 | 0 | 0 | 0 | 0 | 0 |
| mao_pro_ko_mao_pro_t06 | 128 | 2 | 8 | 2 | 0 | 0 |
| mark_movie_pro_ko_mark_movie_pro_t02 | 0 | 0 | 0 | 0 | 0 | 0 |
| miara_pro_en_miara_pro_t04 | 138 | 0 | 0 | 0 | 0 | 0 |
| natori_pro_ko_natori_pro_t06 | 96 | 3 | 11 | 2 | 0 | 0 |
| param_ctrl_pro_ko_haruto_pc_pro_t02 | 0 | 0 | 0 | 0 | 0 | 0 |
| param_ctrl_pro_ko_koharu_pc_pro_t02 | 0 | 0 | 0 | 0 | 0 | 0 |
| param_ctrl_pro_ko_seesaw_pc_pro_t02 | 0 | 0 | 0 | 0 | 0 | 0 |
| param_ctrl_pro_ko_rice_pc_pro_t02 | 0 | 0 | 0 | 0 | 0 | 0 |
| param_ctrl_pro_ko_target_pc_pro_t02 | 0 | 0 | 0 | 0 | 0 | 0 |
| ren_pro_ko_ren_t01 | 73 | 0 | 5 | 2 | 0 | 0 |
| rice_pro_ko_rice_pro_t03 | 96 | 0 | 0 | 1 | 0 | 0 |
| shizuku_shizuku_t02 | 45 | 2 | 0 | 0 | 0 | 0 |
| tsumiki_tsumiki_t01 | 46 | 0 | 10 | 0 | 0 | 0 |
| unitychan_unitychan_t01 | 39 | 0 | 0 | 0 | 0 | 0 |
| wanko_wanko_touch_t01 | 25 | 0 | 0 | 0 | 0 | 0 |
| hiyori_pro_ko_hiyori_pro_t11 | 70 | 1 | 0 | 1 | 0 | 0 |
| miku_pro_jp_miku_sample_t05 | 59 | 0 | 0 | 0 | 0 | 0 |
| tororo_hijiki_hijiki_t01 | 31 | 2 | 0 | 0 | 0 | 0 |
| tororo_hijiki_tororo_t01 | 31 | 2 | 0 | 0 | 0 | 0 |
| nito_nito_t01 | 66 | 2 | 0 | 0 | 0 | 0 |
| nito_ni-j.model3_runtime | 66 | 2 | 0 | 0 | 0 | 0 |
| nito_nico.model3_runtime | 66 | 2 | 0 | 0 | 0 | 0 |
| nito_nietzsche.model3_runtime | 66 | 2 | 0 | 0 | 0 | 0 |
| nito_nipsilon.model3_runtime | 66 | 2 | 0 | 0 | 0 | 0 |
| izumi_izumi_anime_t01 | 30 | 0 | 7 | 0 | 0 | 0 |
| izumi_izumi_atsu_t01 | 30 | 0 | 7 | 0 | 0 | 0 |
| izumi_izumi_illust_t01 | 30 | 0 | 7 | 0 | 0 | 0 |
| izumi_izumi_suisai_t01 | 30 | 0 | 7 | 0 | 0 | 0 |
| gantzert_felixander_gantzert_felixander_t01 | 74 | 0 | 0 | 0 | 0 | 0 |
| github_live2d_cubism_web_samples_samples_resources_haru_haru.model3 | 42 | 2 | 8 | 2 | 1 | 0 |
| github_live2d_cubism_web_samples_samples_resources_hiyori_hiyori.model3 | 70 | 1 | 0 | 1 | 1 | 0 |
| github_live2d_cubism_web_samples_samples_resources_mao_mao.model3 | 132 | 2 | 8 | 2 | 0 | 0 |
| github_live2d_cubism_web_samples_samples_resources_mark_mark.model3 | 21 | 0 | 0 | 0 | 1 | 0 |
| github_live2d_cubism_web_samples_samples_resources_natori_natori.model3 | 96 | 3 | 11 | 2 | 0 | 0 |
| github_live2d_cubism_web_samples_samples_resources_ren_ren.model3 | 73 | 0 | 5 | 2 | 0 | 0 |
| github_live2d_cubism_web_samples_samples_resources_rice_rice.model3 | 96 | 0 | 0 | 1 | 0 | 0 |
| github_live2d_cubism_web_samples_samples_resources_wanko_wanko.model3 | 25 | 0 | 0 | 1 | 0 | 0 |
| github_live2d_cubism_native_samples_samples_resources_haru_haru.model3 | 42 | 2 | 8 | 2 | 1 | 0 |
| github_live2d_cubism_native_samples_samples_resources_hiyori_hiyori.model3 | 70 | 1 | 0 | 1 | 1 | 0 |
| github_live2d_cubism_native_samples_samples_resources_mao_mao.model3 | 132 | 2 | 8 | 2 | 0 | 0 |
| github_live2d_cubism_native_samples_samples_resources_mark_mark.model3 | 21 | 0 | 0 | 0 | 1 | 0 |
| github_live2d_cubism_native_samples_samples_resources_natori_natori.model3 | 96 | 3 | 11 | 2 | 0 | 0 |
| github_live2d_cubism_native_samples_samples_resources_ren_ren.model3 | 73 | 0 | 5 | 2 | 0 | 0 |
| github_live2d_cubism_native_samples_samples_resources_rice_rice.model3 | 96 | 0 | 0 | 1 | 0 | 0 |
| github_live2d_cubism_native_samples_samples_resources_wanko_wanko.model3 | 25 | 0 | 0 | 1 | 0 | 0 |
| github_live2d_cubism_web_motionsync_samples_resources_kei_basic_kei_basic.model3 | 27 | 0 | 0 | 1 | 0 | 1 |
| github_live2d_cubism_web_motionsync_samples_resources_kei_vowels_kei_vowels.model3 | 31 | 0 | 0 | 1 | 0 | 1 |
| github_live2d_garage_cubism_web_ar_sample_assets_models_rice_rice.model3 | 96 | 0 | 0 | 1 | 0 | 0 |

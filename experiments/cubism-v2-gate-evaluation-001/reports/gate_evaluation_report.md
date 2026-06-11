# Cubism v2 검수기 평가판

- status: `PASS`
- false_pass_count: `0`
- golden_score: `12/12`
- bad_score: `1/1`
- mutation_score: `8/8`
- human_review_score: `NOT_SCORED_NO_SAVED_HUMAN_CALIBRATION_SET`

## Confusion Matrix

```json
{
  "PASS": {
    "PASS": 12
  },
  "REVISE": {
    "REVISE": 9
  }
}
```

## Cases
- `golden__mao_pro_ko_mao_pro_t06` golden: expected `PASS` observed `PASS` => `PASS`
- `golden__ren_pro_ko_ren_t01` golden: expected `PASS` observed `PASS` => `PASS`
- `golden__miara_pro_en_miara_pro_t04` golden: expected `PASS` observed `PASS` => `PASS`
- `golden__natori_pro_ko_natori_pro_t06` golden: expected `PASS` observed `PASS` => `PASS`
- `golden__shizuku_shizuku_t02` golden: expected `PASS` observed `PASS` => `PASS`
- `golden__hiyori_pro_ko_hiyori_pro_t11` golden: expected `PASS` observed `PASS` => `PASS`
- `golden__rice_pro_ko_rice_pro_t03` golden: expected `PASS` observed `PASS` => `PASS`
- `golden__haru_haru_t01` golden: expected `PASS` observed `PASS` => `PASS`
- `golden__tsumiki_tsumiki_t01` golden: expected `PASS` observed `PASS` => `PASS`
- `golden__miku_pro_jp_miku_sample_t05` golden: expected `PASS` observed `PASS` => `PASS`
- `golden__haru_greeter_pro_jp_haru_greeter_t05` golden: expected `PASS` observed `PASS` => `PASS`
- `golden__koharu_haruto_koharu_t01` golden: expected `PASS` observed `PASS` => `PASS`
- `bad__imagen_live2d_shallow_rig` bad: expected `REVISE` observed `REVISE` => `PASS`
- `mutation__fixture__missing_part` mutation: expected `REVISE` observed `REVISE` => `PASS`
- `mutation__fixture__bad_alpha` mutation: expected `REVISE` observed `REVISE` => `PASS`
- `mutation__fixture__misaligned` mutation: expected `REVISE` observed `REVISE` => `PASS`
- `mutation__fixture__style_mismatch` mutation: expected `REVISE` observed `REVISE` => `PASS`
- `mutation__fixture__underpaint_missing` mutation: expected `REVISE` observed `REVISE` => `PASS`
- `mutation__fixture__clipping_risk` mutation: expected `REVISE` observed `REVISE` => `PASS`
- `mutation__fixture__draw_order_issue` mutation: expected `REVISE` observed `REVISE` => `PASS`
- `mutation__fixture__overhang_issue` mutation: expected `REVISE` observed `REVISE` => `PASS`

## Interpretation

- `false_pass_count`가 0이어야 새 모델 평가에 쓸 수 있습니다.
- golden set은 좋은 공식 모델을 떨어뜨리지 않는지 봅니다.
- bad/mutation set은 나쁜 모델을 PASS로 놓치지 않는지 봅니다.
- human_review_score는 사람이 저장한 판정 데이터가 생긴 뒤 별도로 채웁니다.

# Cubism v2 New Character G0 Concept Selection

## Summary

- status: `PASS_WITH_CANDIDATE_002`
- selected_candidate: `g0_adult_cute_female_candidate_002.png`
- concept: 성인 여성, 귀여운 느낌, 정면 상반신, Cubism v2_standard 친화형
- generation_mode: `single_master_png_first`
- target_next_gate: `G1_PART_TAXONOMY`

## Candidates

| Candidate | Decision | Notes |
|---|---|---|
| `g0_adult_cute_female_candidate_001.png` | `REFERENCE_ONLY` | 캐릭터성은 좋지만 목걸이, 귀걸이, 헤어핀, 레이스, 복잡한 의상 장식이 많아 첫 production G1 분리 리스크가 큼. |
| `g0_adult_cute_female_candidate_002.png` | `KEEP_FOR_G1` | 성인 여성 귀여운 인상 유지. 눈/입/얼굴/앞머리/옆머리/뒷머리/목/어깨/상체 경계가 비교적 명확하고 장식이 적어 v2_standard 첫 후보로 적합. |

## G0 Checklist

| Check | Candidate 002 |
|---|---:|
| 성인 여성으로 보임 | `PASS` |
| 귀여운 인상 | `PASS` |
| 정면 또는 거의 정면 | `PASS` |
| 눈이 양쪽 모두 명확함 | `PASS` |
| 입이 가려지지 않음 | `PASS` |
| 앞머리가 눈/입을 과하게 가리지 않음 | `PASS` |
| 옆머리/뒷머리 분리 힌트가 있음 | `PASS` |
| 목/어깨/상체 경계가 보임 | `PASS` |
| 복잡한 손/소품 없음 | `PASS` |
| G1 64파트 분리 가능성 | `LIKELY_PASS` |

## Risks For G1

- 앞머리 중앙이 이마와 겹쳐 있어 `front_bang_C` 분리 시 underpaint가 필요하다.
- 양쪽 옆머리 끝단이 어깨/가디건 위에 걸쳐 있어 draw order와 underpaint를 확인해야 한다.
- 가슴 리본과 단추는 v2_standard에서 clothing detail로 단순화하거나 production PSD에서 한두 파츠로만 유지하는 편이 안전하다.

## Decision

`candidate_002`를 첫 G1 part taxonomy 검수 대상으로 사용한다.

다음 단계는 이 이미지를 기준으로 64파트 taxonomy에 맞춘 G1 분리 가능성 검토와 material pack 계획을 만든다. 이 이미지는 아직 production 성공이 아니며, G1/G2/G3를 통과해야 한다.

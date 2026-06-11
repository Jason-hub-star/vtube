# All57 Manual Operator Observations 2026-06-08

## 해석

- 이 기록은 주인님이 all57 carousel player를 보면서 직접 알려준 상태다.
- 기존 all57 carousel은 모델 전환 후 representative motion을 `clear()`해서 중립/깜빡임 상태로 세웠다.
- 따라서 `눈만 움직임` 또는 `안 움직임`은 모델 고장 확정이 아니라, 새 `모션 재생` 버튼으로 재확인할 항목이다.
- `렌더링x` 중 5, 11, 14는 `model3.json`이 없는 CMO3-only 항목이라 Web Player에서 no-runtime이 맞다.

## 관찰표

| 번호 | 모델 | Manifest | 주인님 관찰 | 다음 판정 |
|---:|---|---|---|---|
| 1 | `chitose_t01` | PASS | 눈만 움직임 | 모션 재생 버튼으로 재확인 |
| 2 | `Epsilon_t02` | PASS | 눈만 움직임 | 모션 재생 버튼으로 재확인 |
| 3 | `haru_greeter_t05` | PASS | 작동 잘함 | KEEP reference |
| 4 | `haru_t01` | PASS | 눈만 움직임 | 모션 재생 버튼으로 재확인 |
| 5 | `hiyori_movie_pro_t02` | NO_RUNTIME | 렌더링x | Web runtime 없음, CMO3-only |
| 6 | `kei_basic_free_t02` | PASS | 움직임 | KEEP reference |
| 8 | `haruto_t01` | PASS | 안 움직임 | 모션 재생 버튼으로 재확인 |
| 9 | `koharu_t01` | PASS | 안 움직임 | 모션 재생 버튼으로 재확인 |
| 11 | `mark_movie_pro_t02` | NO_RUNTIME | 렌더링x | Web runtime 없음, CMO3-only |
| 14 | `haruto_pc_pro_t02` | NO_RUNTIME | 렌더링x | Web runtime 없음, CMO3-only |
| 22 | `tsumiki_t01` | PASS | 눈만 움직임 | 모션 재생 버튼으로 재확인 |
| 23 | `unitychan_t01` | PASS | 눈만 움직임 | 모션 재생 버튼으로 재확인 |
| 24 | `wanko_touch_t01` | PASS | 눈 움직임 | 모션 재생 버튼으로 재확인 |
| 25 | `hiyori_pro_t11` | PASS | 기록 끊김 | 주인님 재확인 필요 |

## 다음 사용법

1. 좌우 화살표로 모델을 고른다.
2. 기본 상태를 본다.
3. `모션 재생` 버튼을 누른다.
4. 그래도 안 움직이면 번호와 모델명을 알려준다.

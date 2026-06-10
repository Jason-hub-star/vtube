# AUTORIG 마스터 생성 사양 (P0)

Updated: 2026-06-11 · 시행착오(목 레이어 공백·눈없는 마스터·괴물 사건)에서 도출된 파이프라인 친화 조건. 매 캐릭터 재사용.

## 1. 마스터 이미지 조건표 — 각 조건이 지키는 단계

| # | 조건 | 보호하는 단계 | 위반 시 증상 (실측) |
|---|---|---|---|
| 1 | 정면 상반신, 캐릭터 1명, 손이 얼굴을 안 가림 | P1 분해 전체 | 분해 레이어 오염/누락 |
| 2 | **목·쇄골이 보임** (높은 깃·초커로 목을 다 덮지 않음) | 목 레이어 분해, 숨은 목 채취 | 002에서 목 레이어 공백 → 마스터 채취 우회 필요했음 |
| 3 | 앞머리가 눈을 가리지 않음 (눈썹 일부는 허용) | ARAP 깜빡임 (눈이 워프 소스) | 깜빡임 시 머리카락이 함께 일그러짐 |
| 4 | 눈 활짝 뜬 상태 | ARAP (감김은 워프가 생성 — 감은 눈 생성 불필요) | 반쯤 감긴 마스터 → 깜빡임 범위 부족 |
| 5 | 입 다묾 + 입선(미소선) 뚜렷한 검정 스트로크 | 입 상태 추출 기준점, 턱선 가드 측정 | 입선 흐릿 → mouth_line bbox 측정 실패 |
| 6 | 단순/단색 배경 (캐릭터 실루엣 명확) | P0 인물 bbox 검사, P1 분해 | 배경 오브젝트가 레이어로 섞임 |
| 7 | 2048×2048 (또는 정사각 업스케일 가능) | 전 단계 좌표계 | 좌표계 불일치 |
| 8 | 머리카락 덩어리 실루엣 구분 가능 (좌/중/우) | 머리 분할 + 물리 | 분할 경계가 덩어리를 가로지름 |

## 2. 마스터 생성 프롬프트 템플릿 (codex imagegen)

```bash
# 포그라운드 실행 필수 (백그라운드 스톨 — evidence log 교훈)
codex exec -C <root> -s workspace-write --skip-git-repo-check \
  -i <style_ref.png> -- "Generate a 2048x2048 front-facing upper-body portrait of \
<캐릭터 묘사>, single character centered, simple flat light background, \
neck and collarbones clearly visible, bangs not covering the eyes, eyes wide open, \
mouth closed with a clearly drawn dark smile line, \
hair in distinct left/center/right masses, anime illustration, clean lineart"
```

## 3. 입 4상태 시트 (마스터와 **동일 세션** — 유일한 추가 생성물)

생성 목록 확정 (2026-06-11): **마스터 1장 + 입 시트 1장. 끝.** 눈 감김=ARAP 워프, 가시 레이어=분해+재스킨. (구 12시트 스펙은 입 시트 규격 참고용으로만 축소.)

```bash
codex exec ... -i <true_master.png> -- "Using this exact character, generate a 2048x2048 \
sheet on pure magenta #FF00FF background, 2x2 grid of the character's mouth region \
with identical lip width and corner positions: \
top-left mouth closed (same as reference), top-right slightly open, \
bottom-left half open showing teeth, bottom-right wide open showing teeth and tongue. \
In the bottom-right cell include the full mouth interior. Same art style, same skin tone."
```

- 시트 셀 규약: 2×2 @ 1024px, interior는 (2,2) 셀 — `place_mouth_interior.py --cell` 기본값.
- 검수: 추출 후 4상태의 입꼬리 x좌표 편차 < 입폭 5% (extract가 공유 배치로 흡수하지만 생성 단계에서 맞을수록 좋음).

## 4. P0 자동 검증 (`scripts/validate_master_image.py`)

- **생성 직후**: 해상도/포맷, 인물 bbox(배경 대비) 단일성, 상반신 구도 비율(인물 폭 ≥ 캔버스 35%, 머리 위 여백 ≤ 25%).
- **분해 후(P2 끝, --manifest 모드)**: eye/mouth/face/hair/neck 계열 레이어 알파 점유 assert — 공백이면 해당 조건 위반을 지목하고 중단. (눈없는 마스터·목 공백 사건의 코드화)

## 5. 휴먼 게이트

- **H1 (생성 직후, 필수)**: 주인님 스타일 합격 — 불합격 시 재생성 (분해 20분을 아끼는 게이트).
- H1.5 (분해+재스킨 후): 어셈블리 배치 판정. H2 (리깅 후): 최종 움직임 판정.

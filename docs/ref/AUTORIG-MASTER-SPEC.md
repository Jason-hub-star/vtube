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
| 9 | **목-어깨 접합부에 가림 요소 — 얇은 초커·옷깃 (004부터 기본 적용)** | 목 그라데이션 접합 | 트인 목은 가장 어려운 접합면 — 프로 캐릭터들이 초커를 차는 실전 이유. 리깅(등변위 접합·목 분리·숨은 목)으로도 미세 잔존은 남는다 — 생성 가림이 마지막 1% (단, 조건 2와 양립: 목을 '다' 덮지 않는 얇은 것) |
| 10 | **리본·옷자락이 옷 본체와 색/윤곽으로 분리 가능하게 (004부터)** | 옷 물리 (CLOTH-PHYS-001 후속) | 공식 모델은 리본이 별도 파트(nito 襟リボン1~5 등)라 개별 찰랑임이 가능 — 003은 clothes 통짜라 밑단 전체 드레이프만 가능. 분리 가능 작화여야 개별 리본 스프링을 달 수 있다 |
| 11 | **입/표정 시트가 마스터 입꼬리와 일치 + 캐릭터 표정 성격 일관 (AUTORIG-TEMPLATE-001)** | 부품형 입 개폐, 표정 정합 | 마스터는 '다문 미소선' 한 줄뿐 — 입 시트가 그 입꼬리(올라간 곡선)와 안 맞으면 열 때 어긋남(004 입 5번 삽질의 근본). 캐릭터 `expression_style`을 입·눈 시트 생성에 주입해 성격(차분/활발)이 입 개방 정도를 결정하게 한다 |

## 1.5 캐릭터 스펙 (AUTORIG-TEMPLATE-001)

캐릭터 외형·표정 성격·색 힌트는 코드가 아니라 **`characters/<id>.yaml`** 에 둔다. 캐릭터를 추가할 때 이 파일만 복사·수정하면 생성 코드를 건드리지 않는다.

- 필수: `id`, `name`, `ip_named`(1차), `ip_desc`(IP 거부 폴백), `appearance.{hair,eyes,outfit}`, `expression_style`.
- 선택: `colors.{hair_rgb,clothing_rgb}`(색 분리 임계 힌트 — 실측이 최종), `constraints`.
- `expression_style`이 입·눈 시트 프롬프트에 주입돼 캐릭터 성격이 표정에 반영된다 (위벨="차분한 미소, 활짝 안 웃음").
- 로드/검증: `scripts/lib/character_spec.py`. 생성: `generate_master_sheets.py --character-spec characters/<id>.yaml`.
- 튜닝 자동화: 색 임계(`split_shoulder_hair`), 입 OVERLAP(`extract_mouth_parts`), 목 높이(`split_neck_skin`)는 캐릭터 색·입·얼굴 실측에서 자동 파생 — 캐릭터별 코드 수정 불필요.

## 2. 마스터 생성 프롬프트 템플릿 (현재: `generate_master_sheets.py` 템플릿 + 스펙 주입)

```bash
# 포그라운드 실행 필수 (백그라운드 스톨 — evidence log 교훈)
codex exec -C <root> -s workspace-write --skip-git-repo-check \
  -i <style_ref.png> -- "Generate a 2048x2048 front-facing upper-body portrait of \
<캐릭터 묘사>, single character centered, simple flat light background, \
neck and collarbones clearly visible, wearing a thin dark choker, \
bangs not covering the eyes, eyes wide open, \
mouth closed with a clearly drawn dark smile line, \
hair in distinct left/center/right masses, anime illustration, clean lineart"
```

## 3. 입 4상태 시트 (마스터와 **동일 세션**)

생성 목록 확정 (2026-06-11 개정): **마스터 1장 + 입 시트 1장 + 눈 표정 시트 1장 + 액센트 시트 1장.**
눈 깜빡임=ARAP 워프(가림 동작), **표정=동일세션 생성 시트(외형 변화 — 워프 눈웃음 "그저그렇" 판정으로 재분류)**, 가시 레이어=분해+재스킨. (구 12시트 스펙은 시트 규격 참고용으로만 축소.)

```bash
codex exec ... -i <true_master.png> -- "Using this exact character, generate a 2048x2048 \
sheet on pure magenta #FF00FF background, 2x2 grid of the character's mouth region \
with identical lip width and corner positions: \
top-left mouth closed (same as reference), top-right slightly open, \
bottom-left half open showing teeth, bottom-right wide open showing teeth and tongue. \
In the bottom-right cell include the full mouth interior. Same art style, same skin tone. \
Mouth region only — do not draw the chin or the face outline."
```

- 시트 셀 규약: 2×2 @ 1024px, interior는 (2,2) 셀 — `place_mouth_interior.py --cell` 기본값.
- **004 부품형 입 (MOUTH-PARTS-001 예약 — 잔상 근본 해결)**: 4상태 크로스페이드/스냅은
  "다른 작화의 교체"라는 구조적 한계(반투명/팝 이빨)가 있다. 004부터는 wide 셀(2,2)에서
  **부품 분리 추출**해 공식 구조로 리깅: 윗입술·아랫입술 스트로크(정점 키폼으로 개폐 —
  닫힘 위치는 원본 입선 실측) + 입안·이빨·혀(입술 개구 마스크로 클리핑 — 눈 클리핑 기계 재사용).
  매 프레임 그림이 한 벌이라 잔상이 구조적으로 불가능. 생성 조건 추가: wide 셀은
  윗입술/아랫입술 스트로크가 끊기지 않게, 입안은 진한 단색으로 채워서, 이빨·혀는
  구분 가능한 색으로 (separable parts: distinct upper lip stroke, lower lip stroke,
  dark interior fill, teeth, tongue).
- 알려진 생성 특성: 셀에 입만 아니라 **얼굴 윤곽선(턱 V)이 통째로 딸려온다** — 추출기가 연결성분 분리로 자동 제거하므로 재생성 사유 아님. 프롬프트에 "mouth region only, do not draw the chin or face outline"을 넣으면 줄어들지만 보장은 안 됨.
- 검수: 추출 후 4상태의 입꼬리 x좌표 편차 < 입폭 5% (extract가 공유 배치로 흡수하지만 생성 단계에서 맞을수록 좋음).

## 3.2 눈 표정 시트 (마스터와 **동일 세션** — EXPR-003, 2026-06-11 주인님 확정)

워프는 픽셀 재배치만 가능 — 눈웃음 같은 표정은 속눈썹 스트로크 작화가 달라지는 **외형 변화**라
생성 상태가 정답이다 (입 4상태와 같은 원리). 셀 = **두 눈 영역(눈썹 포함)** 한 쌍 — 윙크처럼
좌우 비대칭 표정과 정렬 일관성 때문에 눈 하나가 아니라 쌍으로 받는다.

```bash
codex exec ... -i <true_master.png> -- "Using this exact character, generate a 2048x2048 \
sheet on pure magenta #FF00FF background, 2x3 grid (2 rows, 3 columns) of the character's \
both-eyes region including eyebrows, identical eye positions, sizes and spacing in every cell: \
row1-col1 both eyes closed in happy smiling arcs (^^), \
row1-col2 left eye closed in a smiling arc and right eye open exactly as the reference, \
row1-col3 both eyes wide open in surprise with small pupils, \
row2-col1 both eyes half-lidded and unimpressed (jito-me), \
row2-col2 both eyes squeezed tightly shut (><), \
row2-col3 both eyes open with heart-shaped pupils. \
Same art style, same colors. Eyes region only — do not draw the nose, hair or face outline."
```

- 셀 규약: 2행×3열 @ 682×1024px. 셀 → 표정: smile/wink_L/surprise + jito/squeeze/heart.
- 윙크 R은 wink_L 좌우 반전이 아니라 **wink_L 셀의 감은 눈 + 놀람 아닌 기준 뜬 눈 조합**으로 합성 (반전은 비대칭 작화를 깨뜨림).
- 알려진 생성 특성(입 시트와 동일): 주변 윤곽·콧대가 딸려올 수 있음 — 추출기 연결성분 분리 대상, 재생성 사유 아님.

## 3.3 액센트 시트 (마스터와 **동일 세션**)

```bash
codex exec ... -i <true_master.png> -- "Using this exact character's art style, generate a \
2048x2048 sheet on pure magenta #FF00FF background, 2x2 grid: \
top-left a pair of soft pink anime blush patches matching the character's skin tone, \
top-right a vertical dark-blue gloom shading patch (forehead shadow), \
bottom-left a single large anime tear drop, bottom-right a single anime sweat drop. \
Flat painterly style matching the reference, each item centered in its cell."
```

- 셀 규약: 2×2 @ 1024px — blush/gloom/tear/sweat. 오버레이 파트라 정렬 기준은 부착 시점에 결정론(눈 bbox 파생).
- 1차 리그 배선은 blush(ParamCheek)·gloom만 — tear/sweat는 자산 확보만 (배선은 차기).

## 3.4 표정 시트 P0 검증 (004 풀런 시 `validate_master_image.py` 확장 구현)

- 시트 공통: 마젠타 배경 비율, 그리드 셀별 콘텐츠 존재.
- 눈 표정 시트: 셀별 눈 콘텐츠 bbox **폭 편차 < 기준 눈 폭 ±10%**, 좌우 눈 간격 편차 < 5% — 동일성(같은 캐릭터의 같은 눈)이 생성 품질의 관건.

## 3.5 파이프라인 자동 방어 (생성 조건 아님 — 재생성 판단 오염 금지)

아래는 생성물에 결함이 있어도 파이프라인이 자동 처리하므로 **H1 불합격 사유가 아니다**:

- 입 시트에 얼굴 윤곽선 포함 → 추출기가 연결성분 분리로 컷 (`extract_mouth_states.py`)
- 어깨·가슴 위 머리카락 가닥이 분해 시 clothes에 구워짐 → 자동 분리+재도색 (`split_shoulder_hair.py`)
- 분해가 목 피부를 clothes에 합침 → 자동 분리 (`split_neck_skin.py`)
- 목 레이어 공백 → 숨은 목 배경판 자동 생성 (`build_hidden_neck.py`)

## 4. P0 자동 검증 (`scripts/validate_master_image.py`)

- **생성 직후**: 해상도/포맷, 인물 bbox(배경 대비) 단일성, 상반신 구도 비율(인물 폭 ≥ 캔버스 35%, 머리 위 여백 ≤ 25%).
- **분해 후(P2 끝, --manifest 모드)**: eye/mouth/face/hair/neck 계열 레이어 알파 점유 assert — 공백이면 해당 조건 위반을 지목하고 중단. (눈없는 마스터·목 공백 사건의 코드화)

## 5. 휴먼 게이트

- **H1 (생성 직후, 필수)**: 주인님 스타일 합격 — 불합격 시 재생성 (분해 20분을 아끼는 게이트).
- H1.5 (분해+재스킨 후): 어셈블리 배치 판정. H2 (리깅 후): 최종 움직임 판정.

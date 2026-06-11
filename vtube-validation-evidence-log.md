# Vtube 검증 Evidence Log

작성일: 2026-06-02
최신 정리일: 2026-06-10

## 2026-06-11 RIG-HEALTH-001 — 인스펙터 기반 리깅 건강도 전수 검사 (무반응 0건)

- 도구: `inspect_autorig_rig.py` (그래프/영향도/접합 위험 점수/동적 스윕) — 003 풀 검사.
- **측정기 결함 2건 발견·수정** (도구를 믿기 전에 도구부터 검증): ① 고정 격자 타일이 소형 부위(눈·입·눈썹)와 평탄 영역을 못 봄 — 해시는 전부 변하는데 Δ=0 보고 → 파라미터 영향 파트 bbox 중심 타일 추가 (Mouth 0.011→1.57, EyeSmile→11.8) ② **물리 소유 파라미터(BodyAngleX/Z)는 직접 주입이 33ms 티커에 즉시 덮어써져 "무반응" 오판** → 직접 측정에서 제외하고 Track 입력 채널 경유로 검증 (TrackZ 화면 10% 변화 = 경로 작동 입증). 인스펙터 bbox 헬퍼는 lib/vtube_image로 이동 (496줄, 500룰 준수).
- **건강 판정: 29개 직접 측정 상태 전부 반응 — 죽은 바인딩 0건.** 약한 반응은 눈썹 max(0.73)뿐 — 위치 이동(±8px)만 있고 모양 변형이 없는 기존 갭의 수치 확인.
- 접합 위험 점수 상위 검토: clothes↔hair_front(76) = 앞머리 가닥이 가슴 위에서 머리 추종 — 공식 모델 동일 거동, 위험 아님. neck_under↔neck_skin(54) = 숨은 배경판 설계 의도.
- 교훈: **건강도 도구의 "무반응" 보고는 먼저 측정기를 의심** — 해시(전역)와 타일(국소)이 모순이면 타일 배치 문제, 물리 소유 파라미터는 입력 채널로만 측정 가능.

## 2026-06-11 SHOULDER-TRACK-001 — 어깨 실측 트래킹 1:1 매핑 (MediaPipe Pose)

- 주인님 요청: 어깨·목 실측 트래킹과 모델 1:1 매핑 (몸이 머리의 메아리인 한계 해소).
- 구조: PoseLandmarker(lite, GPU→CPU 폴백, Face와 병행) 어깨 11/12 → 채널(기울기 roll·중심 cx/cy, 어깨폭 정규화) → **입력 채널 파라미터 ParamBodyTrackX/Z**(디포머 무바인딩, 19종) → 몸 스프링(강성 0.12/0.10으로 상향 — 1:1 추종 + Pose 노이즈 필터 역할) → BodyAngleX/Z. 어깨 상하는 BodyAngleY 직결(0.3 EMA).
- 1:1 의미: 어깨 기울이면 몸 기울고(roll/18→TrackZ), 좌우 이동하면 스웨이(cx/어깨폭×2.2→TrackX), 으쓱하면 몸이 오르내림(cy×14→BodyAngleY). 머리와 독립.
- 안전장치 (TREMBLE 교훈): ① 자동 중립(첫 유효 샘플) + 보정 버튼 정밀 중립(어깨 인식 샘플만 평균 — 미인식 보정 오염 방지) ② X/Z는 스프링이 지터를 거름 ③ Y는 EMA ④ Pose 미인식/로드 실패 시 기존 머리 기반 폴백 자동.
- 검증: validator PASS(19파라미터), pixi verify 6/6, fake-webcam 페이지 스모크(카메라 ON·JS 에러 0), 스프링 1:1 동역학 — TrackX=1 주입 시 BodyAngleX 1초 내 9.0 수렴.
- 한계 명시: 실웹캠 어깨 인식 품질·매핑 게인(2.2/18/14)은 주인님 실사용 판정 대상 — 수치는 보정 가능 상수.
- **v2 (주인님 "육안상 작동 안 함" + 리그 모드 목 분리선 스크린샷)**: ① 진폭 — 풀 스웨이 8px(2048 캔버스)는 비가시 → **18px 상향** (sway_px 변수화, 진자 각·운반 tx 전부 결합 재계산; 으쓱 Y ±5→±8, Z 1.5→2.2°). 접합부 프로파일 재실측: 18px 균일, 슬립 0 유지. ② **NECK-PIN-001**: 목 분리선의 정체 = 파트 경계(윗목=face_base 소유, 아랫목=neck_skin)에서 목 자체 바인딩(±5)이 위 가장자리 비고정으로 어긋남 → neck_warp를 공식 首の曲面 구조로 (전 가장자리 핀, 중간만 휨). 머리 30°·몸 기울임 캡처에서 분리선 소멸. 교훈: **부분 추종 워프는 "이웃 파트와 만나는 모든 변"을 핀** — 안 그러면 그 변이 참수선이 된다. ③ 메시 밀도는 움직임 량과 무관 (주인님 질문 — 밀도는 변형 부드러움 담당).

## 2026-06-11 BODY-SWAY-001 — 몸 모션 1단: 파라미터 스프링 아이들 스웨이 + BodyAngleZ 기울기

- 문제: 몸이 "머리 요의 65% 즉시 복사"뿐 — 즉시 추종(판때기), 정지 시 완전 정지, 기울기 축 부재.
- **파라미터 스프링** (strong20 1위 패턴 — 물리 출력 body_angle 123개의 이식): 스프링 출력이 파트가 아니라 파라미터를 구동. `build_body_sway_springs()` — body_sway_spring(AngleX 7.0 + Breath 1.2 → ParamBodyAngleX, stiffness 0.05/damping 0.92), body_tilt_spring(AngleZ 5.0 + Breath −0.8 → ParamBodyAngleZ). 런타임 stepPhysics가 매 스텝 output_parameter에 기록 — BodyAngle 바인딩 전체(body/upper/back_hair)가 자동 동행, 접합부 등변위 보존.
- **소유권 차단**: `physicsOwnedParameters()` — 트래킹/재생의 직주입(yaw×0.65)이 스프링 출력을 덮어쓰지 않게 probe.setParameterValues에서 무시 (구 스트림 호환). 슬라이더(수동)는 그대로.
- **ParamBodyAngleZ 신설** (17종): body_warp rotate ±1.5° + 운반 대상은 "그 회전이 자기 높이에 만드는 수평 변위"만큼 균일 tx (upper/back_hair — 빌더가 피벗 거리에서 산출; 부분 겹침 회전 직접 부여는 내부 시어, CHAIN-001 교훈 준수).
- 검증: validator PASS(59바인딩), pixi verify 6/6(body_tilt 상태 추가), 동역학 스모크 — AngleX 30 입력 시 출렁이며 ~7.0 안착(지연 추종), 해제 시 −3.8 오버슈트 후 감쇠(잔여 에너지 스웨이), Breath만으로 정지 시 미세 스웨이, 직주입 차단 확인.
- 다음 단계 (별건): ③ MediaPipe Pose 어깨 실측 추적 — 노이즈 리스크라 강평활·히스테리시스 전제.
- **v2 보정 (주인님 "참수" 보고)**: 상시 스웨이가 숨은 접합 슬립 2개를 노출 — ① BodyAngleX의 body rotate ±1.2°가 tx-only 운반과 어긋남 (CHAIN-001 때부터 있었으나 간헐 노출) → **회전 제거, 순수 tx ±8로 전 체인 완전 일치** (기울기는 BodyAngleZ 전담) ② Z 운반 변위를 머리 높이 기준으로 계산한 오류 → **접합부(목 하단) 기준으로 수정** (등변위 원칙은 항상 접합부에서 — v3 원리 재확인). 생성 가림(004 초커, 스펙 9번)은 그대로 마지막 1% 담당.
- **v3 진자 전환 (주인님 "몸·어깨·가슴이 유기적이지 않음" — 균일 평행이동의 한계)**: 몸을 **골반(바닥 중앙) 피벗 진자 회전**으로 — 골반 0 → 어깨로 갈수록 크게 기우는 높이 그라데이션. 등변위는 유지: X 회전각은 "접합부 실효 변위 = ±8"이 되게 역산 (edge-pin 격자라 접합부 변위가 핀 행과 내부 행 사이 보간임을 계수에 반영 — 0.53°), 운반은 그 ±8 균일 tx. Z도 같은 피벗 (실효 운반 22.7px@풀). 교훈: **운반 일치의 기준은 "바인딩 수치"가 아니라 "격자 통과 후 실효 변위"** — edge-pin 보간 계수를 빼면 1~2px 잔존 슬립이 남는다.
- **v3 사후 검증 (주인님 "근거 있나" 추궁 — 가설 규율)**: ① 레퍼런스: strong20 구조 리포트에서 **6/20 공식 모델이 体の回転(회전 디포머) 보유** (chitose는 X/Y/Z 풀세트) — 진자 회전은 공식 패턴 맞음. ② 픽셀 실측: BodyAngleX 0→10 행별 시프트 프로파일(y950~1370, 30px 밴드) — **접합부 관통 전 구간 균일 8px, 슬립 0** (첫 측정의 "목3/가슴12"는 24px 협대역 상관 노이즈 — 텍스처 빈약 밴드의 교차상관은 신뢰 불가, 30px+ 다중 밴드 프로파일로 잴 것). ③ 명시 한계: 어깨·목 실측 트래킹은 없음 — 몸은 머리+호흡 기반 물리 추정 (Pose 트래킹은 ③ 별건).

## 2026-06-11 MOUTH-SNAP-001 — 입 잔상 해소: 하드 밴드 스냅 (크로스페이드 폐기) + 004 부품형 입 예약

- 주인님 보고: 기하 정렬 후에도 잔상 — 원인은 윤곽이 아니라 **내용 혼합** (small/mid가 50/50 겹칠 때 반투명 이빨이 입술 위로 비침). 서로 다른 작화 두 장의 투명도 혼합은 원리적 한계.
- 즉각 조치 (003): 크로스페이드 → **겹침 없는 하드 밴드** (closed<0.24 / small<0.47 / mid<0.72 / wide). 경계에서 양쪽 상태가 같은 H(v) 높이로 워프돼 있어(MOUTH-KEYFORM-001) 윤곽은 연속, 내용만 즉시 스왑 — 스냅식 입은 실전 버튜버 표준 연출. 8단계 스윕: 전 프레임 단일·선명, 혼합 0.
- 근본 해결 예약 (004, MOUTH-PARTS-001 — MASTER-SPEC §3): wide 셀에서 부품 분리 추출(윗/아랫입술 스트로크·입안·이빨·혀) → 입술 정점 키폼 개폐 + 입안·이빨은 입술 개구 마스크 클리핑(눈 클리핑 기계 재사용). 매 프레임 그림 한 벌 = 잔상 구조적 불가능. 생성 조건 추가됨(separable parts).
- 교훈: **잔상 2층 구조 — 기하 불일치(키폼 정렬로 해결)와 내용 혼합(겹침 제거로만 해결).** 상태 교체 체계의 종착지는 결국 부품 분해다.

## 2026-06-11 MOUTH-KEYFORM-001 — 입 크로스페이드에 눈 패턴 이식 (핸드오프 기하 정렬)

- 동기 (주인님): 입 페이드아웃을 눈 성공패턴(정점 키폼)으로 개선할 수 있나.
- 원리: 입은 외형 변화(이빨·혀 신규 작화)라 통째 키폼화 불가 — 스프라이트 유지. 그러나 잔상의 원인은 겹침이 아니라 **겹치는 두 상태의 기하 불일치**(실측 높이 small 33/mid 42/wide 81px) → 모든 상태를 **공통 입높이 함수 H(v)** 에 맞춰 세로 워프(정점 키폼, 런타임 무수정)하면 어느 v에서든 겹치는 쌍의 높이가 같아 윤곽이 일치한다. 공식 모델의 실제 입 구조(메시 키폼 연속 + 내부 불투명도 스왑)와 동형.
- 구현: `lib/rig_keyforms.attach_mouth_height_keyforms` — H 브레이크포인트 = 각 상태 가시 피크에서 자기 실측 높이 (0.18→small 55%·0.35→small·0.58→mid·0.85→wide), 앵커 = 자기 bbox 상단(윗입술 고정), 상태 3종 메시에 다중 키 부착. mouth_line(닫힘)은 무수정 — bbox가 음영 포함이라 앵커 부적합 + v21 커브 합격 상태 보존.
- 검증: validator PASS, pixi verify 5/5, MouthOpenY 8단계 스윕 캡처 — 입이 연속으로 자라고 전환 교차점(0.15/0.38/0.72) 이중 윤곽 없음.
- 교훈: **상태 스프라이트 체계에서 잔상을 없애는 일반해 = "전환 중 겹치는 쌍을 같은 기하로 워프"** — 상태를 키폼으로 대체할 수 없을 때도 눈 패턴의 핵심(기하 일치)은 이식된다.

## 2026-06-11 EXPR-003 — 표정 = 동일세션 생성 시트로 전환 (눈웃음 재분류: 가림이 아니라 외형 변화)

- 주인님 판정: 워프 눈웃음(곡선 A) "그저그렇네" → 생성 시 표정 기준점을 함께 뽑는 방향 제안, 확정.
- 재분류: 눈웃음은 속눈썹 스트로크 작화 자체가 바뀌는 **외형 변화** — 워프(픽셀 재배치)의 상한이 낮다. 입에서 입증된 원리("외형 변화는 워프 금지, 동일세션 생성 상태가 정답")가 눈 표정에도 적용된다. 깜빡임은 가림이 맞아 키폼 유지.
- 생성 목록 개정 (MASTER-SPEC §3.2~3.4): 마스터 + 입 시트 + **눈 표정 시트 2×3**(눈웃음·윙크L·놀람 / 반개 지토메·>< 찡긋·하트눈 — 셀=두 눈+눈썹 쌍, 윙크R은 셀 조합 합성·반전 금지) + **액센트 시트 2×2**(홍조·그늘·눈물·땀 — 1차 배선은 홍조·그늘만). 선정 기준 = 방송 리액션 빈도; 눈물·동공실종·화난눈 보류, 입 표정(ω·뾰로통)은 입 시트 v2 별건.
- P0 확장 예약: 눈 셀 bbox 폭 편차 ±10%·간격 편차 5% (동일성 검증) — 004 풀런 시 구현.
- 워프 눈웃음(EXPR-002 곡선 A)은 생성 셀 실패 시 폴백으로 존치.

## 2026-06-11 EXPR-002 — 눈웃음 재도전: 후보 비교 선택 방식 (곡선 A, 수동 발동 전용)

- EXPR-001 실패 교훈 적용: 곡선 수치를 추측해 박지 않고, **후보 4종(∩ 얕음/깊음/중간 + ∪ 니코니코)을 실제 조립본에 렌더해 주인님 선택을 먼저 받음** (`build_eye_smile_candidates.py` → smile_candidates 리포트). 주인님 선택: **A — 얕은 ^^ (lid_center 0.34, low_center 0.42)**.
- 구현: `smile_lines(lid_center, low_center)` 매개변수화 (0.45 미만=∩, 초과=∪, 눈꼬리 45% 고정) — blink_mesh smile 모드(키 정방향: EyeSmile 1=감김), 곡선 수치는 arap_blink_config SSOT(`smile_lid_center/low_center`, 파이프라인 명시). 파트 +2(eye_L/R_smile — 항등 패치 재사용), 파라미터 +1(ParamEyeSmile, 16종).
- **수동 발동 전용**: 프리뷰 eye 그룹 슬라이더만. 트래킹 자동 연동·드라이브 버튼은 육안 합격 후 별건 (떨림 진범이 자동발동 깜빡임이었으므로).
- 검증: validator PASS(38파트), pixi verify 5/5, 런타임 스윕(0/0.5/1) 캡처 — 중간값 자연 보간·A 곡선 일치.
- 교훈: **수치 취향이 갈리는 형상은 후보 스트립 → 선택 → 박제 순서가 옳다** (추측-실패-롤백 루프 절약).

## 2026-06-11 EXPR-001·TREMBLE-001 롤백 — 주인님 판정: 셋 다 실패 + 수정 후 눈이 완전히 안 감김

- 주인님 판정: 표정 3종(눈웃음·입꼬리·홍조) 시각 실패, TREMBLE-001 수정 후 눈이 전처럼 완전히 닫히지 않고 부자연.
- 닫힘 회귀 원인 추정: convert 열림 데드존 상한 0.75가 과대 — 실제 감을 때 eyeBlink가 0.75에 못 미치는 사람은 EyeOpen이 0.27까지 못 내려간다 (개인차 미보정). 히스테리시스 blink 진입(0.7)·복귀(0.8) 임계도 같은 개인차 문제.
- 조치: ba81eff(EXPR-001)·396bb68·d43bf8b(TREMBLE-001) 코드 리버트 — 리그는 주인님 승인 상태(EYE-NATURAL-002, 36파트·15파라미터)로 복원. 증거 엔트리는 보존 (이 기록 포함).
- 재시도 시 반영할 것: ① 트래킹 눈 매핑은 **중립 보정 버튼처럼 개인 캘리브레이션**(열림/감음 실측 범위로 정규화) 후에만 데드존을 적용 ② 표정은 한 번에 하나씩, 주인님 육안 게이트 통과 후 다음으로 ③ 홍조는 절차식 대신 생성 자산 후보.
- **롤백 후 주인님 확인 (2026-06-11): 떨림 소멸.** → 떨림의 진범은 깜빡임 패치(EyeOpen 0.85~0.94 상시 걸침은 실용상 비가시)가 아니라 **표정 자동발동의 데드존 경계 깜빡임** (노이즈가 EyeSmile 0~0.05를 오가며 눈웃음 패치를 반투명 토글). 교훈: 자동발동 표정 채널은 도입 시점부터 히스테리시스/강평활 필수, 그리고 새 기능 도입 직후 떨림이 보이면 그 기능부터 끄고 재현 확인.

## 2026-06-11 TREMBLE-001 — 눈 떨림: 트래킹이 "완전 열림"을 못 만든다 (히스테리시스로 해결)

- 주인님 보고: 눈이 실시간으로 떨리고, 감았다 뜨면 기본값으로 돌아가려는 듯한 현상.
- 실측 (저장 T1 스트림 175프레임): **ParamEyeLOpen 최대 0.942 — 1.0에 못 닿는다.** MediaPipe eyeBlink는 눈을 떠도 0.06~0.15라 1−blink가 0.85~0.94에서 진동 → ① 깜빡임 패치가 상시 t≈0.1 걸침(노이즈가 꺼풀을 직접 흔듦) ② 패치 표시 경계(0.97)를 오가며 눈동자가 중립↔시선 스냅("기본값으로 돌아가려는" 정체).
- 수정 (drive 페이지): ① convert에 열림 데드존 `1−remapDeadzone(blink, 0.12, 0.75)` ② **apply에 3상태 히스테리시스** — open(1.0 고정)→v<0.7 blink(즉각 추적)→v>0.8 opening(0.45 이징 복귀, 스냅 팝 방지). 고정 스냅(>0.88→1)은 폐기 — 구버전 스트림이 0.84~0.91로 경계를 타서 더 튀었다. ③ 표정 신호(EyeSmile/Cheek/MouthForm) 0.15 강평활 + 0.04 데드존 — 자동 발동 경계의 깜빡거림 제거.
- 검증 (재생 모드 헤드리스, canvas 측정 서버): 열림 구간 EyeLOpen 트레이스 전부 정확히 1.0 (수정 전 0.84~0.91 진동), 진짜 깜빡임 1회는 그대로 통과 (과필터 아님).
- 교훈: **트래킹 출력의 "정지 상태"가 파라미터 극값에 정확히 안착하는지부터 본다** — 안착 못 하면 어떤 렌더 경로든 떨린다. 상태 전환형 안정화(히스테리시스)는 고정 임계 스냅보다 소스 무관이다. apply()에 넣으면 웹캠·재생 양쪽을 한 번에 다룬다.

## 2026-06-11 EXPR-001 — 표정 1차: 미소(눈웃음·홍조·입꼬리) + 윙크, 트래킹 자동 + 프리셋 병행

- 주인님 선택: 세트 = 미소+윙크, 발동 = 트래킹 자동 + 수동 프리셋 둘 다 (2026-06-11).
- **지속 추가 가능 구조**: 표정 = `expressions.json` 프리셋(파라미터 묶음 + fade_ms, 공식 .exp3 등가) — 이후 표정 추가는 JSON 1개. 파라미터 3종 신설 (ParamEyeSmile 0..1 / ParamCheek 0..1 / ParamMouthForm −1..1, 총 18종).
- **눈웃음**: EYE-NATURAL-002 정점 키폼 기반 재사용 — `smile_lines()` ∩ 아치(중앙 28%/35%, 꼬리 45% — 깜빡임과 반대로 위볼록 ^^), 같은 항등 패치 텍스처에 키 방향만 정방향(EyeSmile 1=감김). 깜빡임 패치 위 draw order (스마일 중 깜빡임 가림).
- **홍조**: `lib/expr_assets.make_cheek_blush` — 눈 bbox에서 결정론 파생(눈 아래 0.55h), 피부 중앙값 45%+핑크 55%, (1−d²)² 폴오프, 얼굴 알파로 클램프. head_angle_warp 소속(머리 동행).
- **입꼬리**: mouth_line 메시 9×5 승격 + ParamMouthForm 키폼 3개(−1/0/+1) — 중앙 30% 고정, 꼬리 제곱 프로파일 상승(+0.55h)/하강(−0.4h). **다중 키 정점 키폼에는 0 항등 키 명시 필수** (없으면 −1·+1 사이 보간으로 중립이 어긋남).
- **트래킹 자동**: 드라이브 convert()에 eyeSquint+smile→ParamEyeSmile, mouthSmile(0.55 데드존)→ParamCheek. MediaPipe mouthSmile→ParamMouthForm은 이미 계산되고 있었으나 리그에 파라미터가 없어 버려지던 것 — 그릇 신설로 연결 완성.
- **수동 프리셋**: 드라이브 페이지 버튼+숫자키 토글, fade_ms 가중 블렌딩(트래킹 출력 위 오버라이드). `__EXPRESSIONS__` 템플릿 주입 (구 프로젝트 빈 목록 호환).
- 검증: validator PASS(39파트·18파라미터), mesh verify smile 상태 추가 — canvas·pixi 6/6 distinct, blink 정확성 PASS 유지(worst mean 2.2). 비주얼: 중간값(0.5) 자연 보간·입꼬리 ±·홍조 클램프 확인 (헤드리스 캡처).
- 교훈: 새 표현 축을 만들기 전에 **트래킹이 이미 보내는 신호 중 리그가 버리는 것부터 찾기** (MouthForm이 그랬다).

## 2026-06-11 EYE-NATURAL-002 — 깜빡임 정점 키폼 (크로스페이드 잔상 폐기, 공식 키폼 등가)

- 주인님 보고: 감는 중 이전 단계 눈이 흐릿하게 겹쳐 보여 어지러움. 원인 = 베이크 4단계 크로스페이드 — 전환 구간에서 꺼풀 위치가 다른 두 프레임이 반투명으로 겹침. 공식 모델은 페이드가 아니라 **메시 정점의 연속 키폼 보간** (한 장 텍스처 위 정점 이동 — 잔상 원리적 0).
- 전환 가능했던 수학적 근거: ① 커튼 워프는 세로 구간별 선형(3밴드) → 경계 곡선 4줄에 정점 행을 두면 메시 선형 보간이 워프를 그대로 재현 ② 꺼풀선이 t에 선형 → 키폼은 열림/닫힘 **2개로 전 구간 정확** (중간 베이크 불필요).
- 구현: 런타임 `rig.js` `keyformBaseVertices()` — 메시 `vertex_keyforms` {param, keys:[{value,vertices}]}를 기준 정점에 보간 적용 후 디포머 체인 누적 (canvas/pixi 공용 경로 1곳, 텍스처 소스 좌표는 원본 정점이라 양 백엔드 무수정 정합). 빌더 `blink_mesh()` (`run_arap_blink_experiment.py`, lid_lines SSOT 공용) — 6행×4px 컬럼 메시, 눈꼬리 자동 고정점. 파트 8개(crossfade)→2개(eye_L/R_blink, 항등 패치 t=0 텍스처), 불투명도 커브는 완전 열림 0.97~1.0 숨김뿐 (그 구간 워프≈항등이라 밑의 생눈과 픽셀 동일 — 전환 비가시).
- **잔상 0 수치 입증** (`validate_blink_keyforms.py`, 파이프라인 P5 4번째 검증으로 편입): 키포인트가 아닌 v=0.9/0.72/0.51/0.35에서 런타임 추출 = 기준 curtain_warp(t) 단일 프레임과 일치 — worst mean Δ 2.2/strong 0.8% (±1px 시프트 허용; 크로스페이드라면 두 프레임 혼합으로 수 % strong). 컬럼 샘플 10px→4px 교훈: 타원 곡선 선형 근사는 눈꼬리에서 1~3px 어긋남 (FAIL→PASS).
- 회귀: validator PASS, mesh verify canvas·pixi 5/5, 중립 항등 유지 (v=1에서 키폼=열림=기준 정점).
- **주인님 육안 합격 (2026-06-11)**: "전보다 훨씬 좋아" — 잔상 어지러움 해소 확인. EYE-NATURAL-001(상하 감김)도 동일 세션 합격 ("전보다 괜찮아졌어").
- 교훈: **상태 머신(레이어 스왑/크로스페이드)은 전환 잔상이 본질적 한계 — 연속량은 정점 보간으로.** 입 4상태는 외형 변화(다른 그림)라 스프라이트가 맞고, 눈 감김은 가림(같은 그림의 변형)이라 키폼이 맞다 — 동작 본질에 따라 기법을 가른 부위별 공식 재확인.

## 2026-06-11 EYE-NATURAL-001 — 눈 상하 감김 (아랫꺼풀 상승, 공식 모델 패턴)

- 배경: 기존 커튼 워프(ARAP-EXP-001 v2)는 윗꺼풀만 닫힘 아치로 하강 — 아랫꺼풀 고정 셔터식. 공식 모델 실측 근거: strong20 코퍼스에서 koharu_haruto가 `_右下まつげ`/`_左下まつげ`(아랫속눈썹)를 독립 파트로 분리, miara_pro는 Eyelid/Eyelid Shadow 파트 — 감을 때 아래에서도 올라와 중심 아래에서 만나는 구조.
- 구현 (`run_arap_blink_experiment.curtain_warp` v3): 컬럼별 아랫꺼풀선 `lid_low = low_x − t·lower_rise·(low_x−up_x)` (lower_rise=0.2, 눈꼬리는 컬럼 눈높이 0이라 자동 고정점) + 눈 아래 피부 밴드 [low_x, y1+0.35h]가 따라 늘어나 아랫속눈썹 동반 상승. 3밴드 리매핑(위 피부 스트레치/눈 압축/아래 피부 스트레치). lower_rise=0이면 구형과 동일 (하위 호환). 베이크 패치 크롭도 아래 밴드만큼 확장.
- 기하 보장: lid_low ≥ 닫힘 아치 항상 성립 (0.45+0.35a > 0.45+0.28a) — t=1에서 눈 밴드가 7%a 높이로 남아 닫힘 속눈썹 선 보존.
- 검증: 003 재베이크 8레이어 → 눈바닥 18% 밴드에서 베이크 픽셀 ~50%가 피부로 대체 (t=100, L 48.4%/R 49.6% — 구형은 0%), 아래밴드(y1 이하)도 t 단조 증가 변화. 리그 리빌드(42파트·53바인딩 동일) validator PASS + mesh verify canvas·pixi 5/5. 스트립: `experiments/autorig-character-003/reports/eye_natural_001/strip_lowerlid/blink_strip.png`.
- 래칫: 파이프라인 P3 베이크 설정에 lower_rise/lower_band 명시 (004부터 자동 상속), FACIAL-TEST-CHECKLIST에 상하 감김 행 추가 (셔터식이면 FAIL).
- 교훈: 깜빡임 자연스러움의 핵심은 닫힘 위치(중심 아래 아치)와 **양방향 운동** — 레퍼런스는 외부가 아니라 이미 보유한 strong20 코퍼스의 파트 구조에서 확보.

## 2026-06-11 정비 패키지 — git 위생·빌더 분리·INDEX core·에러 규칙

- **git 위생 (최대 리스크 해소)**: 사이드 브랜치(codex/...)에 63커밋 + 미커밋 522파일로 떠 있던 상태를 정리 — ignore 정책 확장(외부 샌드박스/node_modules/공식 샘플 모델/바이너리/gif), 미추적 스크립트 224개 + 증거 JSON/MD 코퍼스 커밋, main fast-forward 머지, 우분투發 CUDA 조사 커밋 합류, origin 푸시. 백업: `backup/pre-merge-20260611`.
- **빌더 500줄 룰 복귀**: build_autorig_rig_v0 584→423줄 — 파라미터/바인딩/커브/물리를 `lib/rig_keyforms.py`로 기계적 분리. 무회귀 증명: 003 재빌드 character.json **완전 동일** (generated_at 제외).
- **INDEX core 태그**: ⭐ = 현행 파이프라인 체인(run_autorig_pipeline에서 동적 추출 + 상시 도구) 21개 — 레거시 260여 개와의 오선택 방지.
- **코드 규칙 7 신설**: 에러 삼키기 금지 (조용한 except는 증거 오염) — 바이브코딩 체크리스트(DC 특이점갤)에서 채택. 나머지 항목은 기존 체계가 이미 커버함을 리뷰로 확인 (행동 검증·500줄·INDEX 의무·lib SSOT).

## 2026-06-11 SHOULDER-HAIR-SPLIT — clothes에 구워진 어깨 가닥 분리 (주인님 근본 진단 적중)

- 주인님 진단: "근본적으로 cloth에 머리카락이 붙어있어서 머리를 움직이면 분리된다" — 실측 확인: clothes 레이어에 머리카락색 픽셀 28,605개 (양 어깨·가슴 위 가닥). 몸(±8)만 따라가니 회두(±13) 시 본체와 분리.
- PNG 한계 아님: ① 소유권 문제 — 분리 기법으로 해결 ② 가려진 픽셀(가닥 밑 가슴/끈)은 합성 비용 — 숨은 목과 같은 종류.
- 신규 `split_shoulder_hair.py`: 머리카락색(중앙값 거리<60·휘도<150) + 밀도 필터(스펙클 제거) → shoulder_hair 파트 + clothes는 정규화 블러 필드로 재도색(알파 유지 — 구멍 아님). 재합성 무손실 PASS (strong 0.20%, mean 0.52).
- 빌더: shoulder_hair → back_hair_warp(머리 추종+몸 탑승+찰랑 0.7), draw order clothes+2(목 피부 위), 9x? big 메시. 파이프라인 P3 정식 편입 + P4 인자.
- 검증: verify 5/5(pixi), 완전 회두 ±30 캡처에서 가닥이 머리 본체와 동행 — 가슴 잔류 조각 0.
- 교훈: **"파트 분리 의심" 규율 세 번째 입증 (머리카락→목→어깨 가닥). 분해 소유권 검사를 색-거리 진단으로 정례화할 것** (머리카락색 픽셀이 비-머리 레이어에 있으면 분리 후보).

## 2026-06-11 CHAIN-001 — 뒷머리·목·몸 체인 개선 (strong20 공식 구조 이식)

- 주인님 발견: 뒷머리가 머리를 안 따라감(물리 찰랑임만), 몸 스웨이 시 머리-몸 분리감. 실측: back_hair_warp가 root 자식 + Angle/HairBack 바인딩 0개.
- strong20 재분석 (haru_greeter/haruto 디포머 체인 실측): ① 뒷머리 = 얼굴 체인 자식(後ろ髪の曲面 ← AngleX/Y) → AngleZ 워프 → 揺れ 워프(ParamHairBack, 물리 구동) ② 머리가 몸 체인 위에 중첩(首の位置 ← BodyAngleX가 얼굴 전체 운반) ③ 목 ← AngleZ(首の曲面) ④ 물리 출력 1위 = body_angle 123개.
- 이식 (`build_autorig_rig_v0.py`): **upper_warp 신설**(首の位置 등가 — 비고정 3x3, head∪neck∪back_hair 경계; head_angle_warp가 edge-pin 의사3D라 몸 추종 직접 바인딩 불가 → 상위 워프로 통째 탑승) + head/back_hair 부모를 upper로, neck의 BodyAngle/Breath 바인딩 제거(이중 적용 방지) + neck AngleZ ±3 + back_hair 감쇠 추종(AngleX ±13=60%·AngleY ±7·AngleZ ±5, 핀 해제 — 하단 스윕은 몸 뒤 draw order라 안전, pivot=head) + ParamHairBack ±10 신설 + HairFront 음수 키 보강.
- 파이프라인 갭 봉합: 원커맨드 P3에 split_neck_skin 스테이지 + P4 --neck-split-dir (H2 수동 추가분이 파이프라인에 없어 003 최종 상태 재현 불가였음).
- 검증: validator PASS, mesh verify canvas·pixi 5/5, 수치 스모크 — AngleX=30 뒷머리 실루엣 변화 0→27.7, BodyAngleX=10 얼굴 변화 0→9.75(탑승), HairBack=1 뒷머리 43.6/얼굴 2.1. eye cover 설정 리빌드 보존 확인.
- **v2 보정 (주인님 H 피드백 "목-어깨 분리 악화")**: upper_warp 균일 운반이 접합부에서 가슴(edge-pin 페이드 ~0)과 어긋남 (8 vs ~3). bounds를 head∪neck로 축소 + `pin_edges:["bottom"]` + 세로 5행 — **머리 100% → 목 점감 → 접합부 0** 그라데이션 ("목이 늘어난다"의 구현). 접합부 시각 확인 매끈, 얼굴 탑승 18.1 유지, verify 5/5. 교훈: **운반 워프는 고정된 이웃과 만나는 변에서 0으로 점감해야 한다 — 균일 운반은 경계마다 슬립을 만든다.**
- **v3 (주인님 "아직 그대로" — 접합부 연속의 원리 확정)**: v2 점감은 가슴이 접합부에서 ~5px 움직여 부호만 바뀐 슬립이었다. 원리 = **접합부에서 목·가슴·배경판이 같은 변위로 만나야 한다**: upper 균일 +8 복원 + body 격자 상단을 얼굴 높이로 연장(edge-pin 페이드를 접합부 밖으로 추방 → 가슴도 접합부에서 풀 +8) + 뒷머리는 root 소속(upper 부분 겹침 시어 방지) 자체 BodyAngle 균일 바인딩. 4상태 접합부 캡처 연속 확인, verify 5/5.
- 교훈: **부위가 안 움직이면 디포머 "부모 체인"부터 본다 — 바인딩이 아니라 소속이 끊긴 것일 수 있다.** edge-pin 워프엔 전역 이동 바인딩을 직접 넣지 말고 비고정 상위 워프를 끼운다.

## 2026-06-11 입 패치 V선 사건 — 생성 셀의 얼굴 윤곽 스트로크, 연결성분 분리로 해결

- 증상 (주인님 보고): 입을 벌리면 턱에 V 모양 선. canvas/pixi 양 백엔드 비교로 렌더러 무관 = 소재 확정. 닫힘/벌림 픽셀 차이맵으로 V 픽셀 좌표 추출 → 입 상태 패치 알파 내부로 특정.
- 근본 원인: 생성 입 시트의 **모든 셀에 캐릭터 얼굴 윤곽선(턱 V) 전체가 딸려 들어옴** (셀 가장자리→아펙스 풀폭). 추출기의 콘텐츠 검출(피부색 거리)이 윤곽선도 콘텐츠로 분류 → 하단 페이드가 윤곽선까지 불투명 유지. 패치는 0.97 스케일 립 정렬이라 원본 윤곽과 어긋난 위치에 복제 V가 그려짐.
- **실패한 접근 3종 (기록 — 재시도 금지)**: ① 행 갭 검출 — V팔이 대각이라 행 유니언이 연속, 갭 없음. ② 컬럼별 첫 블록 컷 — 입 내부의 연한 픽셀이 콘텐츠 미달이라 내부가 세로 줄무늬로 파괴. ③ 행 폭 프로파일(25% 임계) — V 아펙스는 수평이라 행 폭이 넓어 strong 오인.
- **성공한 접근: 연결성분 분리.** 입술 블롭과 윤곽 스트로크는 모든 셀에서 분리된 성분 — 중앙 시드(상단 75%×중앙 20% 컬럼)에서 numpy roll 기반 flood-grow한 성분만 콘텐츠로 인정, 행·열 밀착 범위도 그 성분에서만 측정. 가장자리 접촉 시 누설 경고 출력 (`extract_mouth_states.py`).
- 검증: 4상태 합성 진단 V 소멸, 닫힘/벌림 런타임 차이맵에서 V 윤곽 소멸(입 블롭만 잔존), 주인님 육안 합격.
- 교훈: **생성 셀에는 요청한 부위만 오지 않는다 — 주변 윤곽이 통째로 딸려온다. 모양 기반 휴리스틱(행 갭/컬럼/폭 프로파일)은 대각·수평이 섞인 스트로크에 전부 깨지고, 위상(연결성)만이 안전하다.**

## 2026-06-11 PIXI-RENDER-001 — PixiJS v8 WebGL 백엔드 (렌더 병목 해소, 풀해상도 60fps)

- 배경: canvas2d 병목 = 삼각형당 클립/블릿 CPU 오버헤드 (해상도 무관 — render_scale 0.55 무효과 실측). 웹검색: PixiJS v8이 웹 버튜버 생태계 표준(pixi-live2d-display), MeshSimple(vertices/uvs/indices)이 우리 메시 JSON과 1:1.
- 구현: `mini_cubism_app/vendor/pixi.min.mjs`(8.19.0 벤더링, MIT) + `src/core/draw_pixi.js`(~250줄). **rig.js 변형 수학 무수정** — 그리기만 교체. ?renderer=pixi 동적 임포트(canvas 모드는 의존성 0), draw() 디스패처, 에디터 오버레이는 #overlay-canvas(2d) 겹침, probe 백엔드 분기(extract.pixels + regionAlphaCount), 텍스처는 bbox 크롭(풀캔버스 41장=690MB GPU 방지), 눈 클리핑=흰자 클론 메시 스텐실 마스크(둘 다 격자 변형 — AngleZ 이탈 회귀 방지), 눈꺼풀 커버=오프스크린 1회 렌더 스프라이트.
- 실측 (003 리그, 2048 풀해상도): 상태 전환 75~130ms → **0.7~1.8ms (~100×)**, rAF 실효 FPS 4~6 → **60 (상한)**. mesh verify 5/5 PASS 양 백엔드(중립 항등·상태 상이·목 투명 0·backend_match — silent 폴백 검출 체크 신설). canvas 무회귀 5/5.
- 함정 3종 (기록): ① components render()가 캔버스 DOM 재생성 — pixi 영속 캔버스 재부착 + 리스너 중복 가드 ② headless WebGL은 SwiftShader라 2048² 합성 ~1s/frame — rAF가 1fps 허수, `--enable-gpu --use-angle=metal`로 실 GPU 측정 ③ 재생 17fps는 녹화 스트림 케이던스(트래킹 한계)지 렌더러 한계 아님.
- 드라이브 기본 pixi 전환(`--renderer canvas` 폴백 유지, render_scale 0.55 경로 보존). `?transparent=1`은 backgroundAlpha 0 + 배경 스프라이트 숨김으로 이미 배선.
- 다음 레버: WebGPU는 Pixi 설정 스위치(코드 무수정) — 공식 권고가 "프로덕션은 WebGL"인 동안 보류.

## 2026-06-11 캐릭터 003 풀런 — 원커맨드 파이프라인 실증, H2 조건부 합격

- **run_autorig_pipeline.py 원커맨드**: P0 검증→분해→재스킨→어셈블리→H1.5→추출→리깅→검증3종→H2, 관제탑 이벤트+스톱워치. 총 76분(게이트 검수·개선 반복 포함, 순수 연산 ~22분 — 1시간 목표 내).
- 생성물 2장(마스터+입시트)만으로 41파트·14파라미터 리그 자동 완성 — **캐릭터-무관성 실증** (002와 동일 구성, 리허설은 98초).
- H2 검수 루프 7건 개선(전부 코드 박제): 숨은 목 v4(몸 고정 배경판·턱그늘 아래 채취·블러·높이 캡), 목 피부 분리(split_neck_skin — 분해가 clothes에 합친 목을 꼬리 기법으로 분리), 방향별 격자 핀(pin_edges — 목 위 자유·아래 고정), **공식 의사3D 모션**(head 격자 하향 연장 제거 — 윤곽 고정·이목구비 이동, 턱 이동 1/3), body 격자 edge-pin(접합부), 목 추종 정합(±5/±3), 빈 bbox의 bounds 오염 가드.
- **H2 조건부 합격 (주인님)**: 트인 목의 미세 접합 잔존은 알려진 한계 — 대응: MASTER-SPEC 9번(초커·옷깃 가림 권장, 다음 캐릭터부터 적용), 키폼 사다리·렌더 고도화에서 근본 개선.
- 규율 후보 확정: "움직임이 어색하면 파트 분리를 의심하라" (머리카락→목 두 번 입증).

## 2026-06-11 rig v1.3 — H2 2차 피드백 3종 해소

- **눈알 이탈**: 클리핑 파트(홍채)가 구식 강체 경로에 남아 AngleZ에서 자기 중심 자전 → 이탈. 홍채·흰자 마스크 모두 FFD 메시 경로로 (쌍둥이 캐시 캔버스). 교훈: **렌더 경로 이원화 시 모든 파트 클래스가 같은 변형계를 타는지 검사할 것.**
- **목-몸 분리 재발**: 목을 head 자식으로 옮기며 body 추종 상실 — BodyAngleX가 몸만 밀어 분리. 하이브리드 복원: 목 부모=body(몸 추종) + 머리 35% 수동 바인딩 + 숨은 목. 교훈: **목은 머리·몸 양쪽에 걸친 부위 — 단일 부모로 풀 수 없다.**
- **툭툭 끊김**: render_scale 도입 — 드라이브 iframe을 0.55 해상도로 렌더(좌표계 2048 유지). 실효 18fps (기존 3~6), 10초 스트림 실시간 완주.
- mesh verify 4/4 + validator + T3 PASS. 다음 성능 레버: WebGL (필요 시).

## 2026-06-11 rig v1.2 — FFD 격자 메시 변형 (주인님 "따로 노는 파츠" 해소)

- 원인: 메시를 생성해놓고 런타임이 통짜 스프라이트 강체 변형만 수행. 주인님의 "발췌인가 고안인가" 추궁으로 자체 고안 falloff 수식을 폐기하고 **공식 Cubism 메커니즘 이식**: 디포머=FFD 제어점 격자, edge-pinned(가장자리 링 고정)=리거 공식 경계 연결 기법, 정점=격자 이중선형 보간을 체인 누적.
- neck_warp을 head 자식으로 재배치 — head 격자의 edge-pin 페이드가 목 추종을 자동 생성 (수동 35% 바인딩 삭제). 물리: root_to_tip 정점 가중(v0-3 포맷)으로 머리뿌리 두피 고정.
- 렌더 3단 고속화: 항등 패스(중립=스프라이트와 캔버스 해시 동일 검증) / 파트 어파인 패스 / 삼각형(이음새 1.5% 확장 클립 + 소스 부분 blit + 빈 삼각형 빌드타임 컬링).
- 검증: 중립 항등 PASS, 변형 상태 상이, 목 투명픽셀 0, validator+T3 PASS. **잔여: 최대 기울임 리드로 ~250ms — 성능 패스(WebGL/오프스크린) 별도 큐.**

## 2026-06-11 rig v1.1 — 페이셜 품질 패스 (주인님 H2 1차 피드백 반영)

- **까딱·기울임**: ParamAngleY(ty±12)/Z(rotate±10°) 리깅 + 물리 세로 출렁 연동.
- **목 분리 해소 (업계 정석 2종)**: 숨은 목(분해 목 레이어가 비어 있어 **마스터에서 직접 채취** — 턱선~옷깃 피부 사각형, 가로1.3×/위+140px) + neck_warp 35% 추종. 수치 검사: 머리 X30+Y30 최대 이동에서 목 밴드 투명픽셀 0.
- **프레임 끊김**: 클리핑 임시캔버스 캐시(매 드로우 2048 신규 할당이 주범) + MediaPipe GPU delegate(CPU 폴백). 별건으로 재생 틱 프레임스킵(렌더러 38초 블록 해소).
- **눈썹**: BrowL/RY ±8px 파트 바인딩 (슬라이더 우선, 트래킹 매핑 후속).
- **체크리스트**: `docs/ref/FACIAL-TEST-CHECKLIST.md` — 업계 기준 H2 시트, 매 캐릭터 재사용. 옆모습은 v2 보류 명시.
- 40파트·9워프·14파라미터·32바인딩, validator+T3+확장 스윕(6상태) PASS.

## 2026-06-11 rig v1.0 — 전신 완성 (몸+머리분할+물리, H2 검수 대기)

- **Phase A 몸**: body_warp + ParamBodyAngleX/Y(±10, 공식 실측)·ParamBreath. 스윕 4상태 상이.
- **Phase B 머리 분할**: `split_hair_chunks.py` — front 3 + back 2 덩어리, "불투명 자기영역 + 페이드 꼬리" 설계(겹침 복제·재합성 무손실: 강변화 0.007~0.019%). 0.5+0.5 알파 페더는 합성상 비침 — 꼬리 설계가 정답 (기록).
- **Phase C 물리**: v0-3 검증 프로파일 이식(soft 0.13/0.82, heavy 0.08/0.88, accessory 0.2/0.72) + BodyAngleX 연동. 임펄스 스모크: 목표 오프셋 정확 도달 후 0으로 감쇠. 드라이브 rAF에 stepPhysics 추가.
- **Phase D**: T3 재생 175프레임 전 구간 **applied 9 파라미터**(6→9). validator PASS (39파트·8워프·10파라미터).
- 다음: 주인님 H2 (웹캠으로 머리 찰랑임·호흡·상체 기울기 확인).

## 2026-06-11 입 성공패턴 — VERIFIED (주인님 "아주 좋아" 합격)

**최종 입 성공패턴 (autorig 계보 v1):**
1. **재료**: 진짜 마스터 참조 동일세션 4상태 시트 1장 (2x2: closed/small/mid/wide, 동일 폭·동일 입꼬리 위치 강제 프롬프트). 별도 세션·분리 내부 생성은 금지 (v10·오늘 재확인).
2. **추출** (`scripts/extract_mouth_states.py`, 전 수치 상수화):
   - 트림 (상단 30%·측면 10%) — 패치가 코·뺨을 침범하지 않게
   - 톤 매칭 — 패치 피부색을 원본 입 아래 피부 중앙값에 채널별 정합 (게인 0.85~1.18)
   - 사방 밀착 페이드 — 입술 콘텐츠를 **측정**해 그 둘레만 불투명 (피부 최소화)
   - **턱선 가드** — 원본 턱 스트로크 y를 측정, 그 위 6px 아래로는 알파 강제 0 (구조적 침범 불가)
   - 스케일 절제 0.97 (v21 wide-open 교훈)
3. **커브**: v21 겹침 크로스페이드 수치 그대로, **closed는 원본 mouth_line** (중립 100% 원본).
4. **부위별 공식 확정**: 눈 = ARAP 워프 (가림 동작) / 입 = 밀착 스프라이트 (외형 변화 동작). 워프를 입에 쓰면 경첩 턱 — 구조적 부적합.
- 재조정: 상수 수정 → 재추출 1명령 → 빌더 `--mouth-states-dir`.

## 2026-06-11 rig v0.6 — 입 구조 최종 판정: 입술 밀착 스프라이트 (워프의 구조적 한계 확정)

- 주인님 연속 검수로 구조 결론 도달: **워프는 입에 구조적으로 부적합** — 다문 미소선을 어떤 변위장으로 변형해도 "벌어진 입술 링"(다른 두께/하이라이트/곡률)이 되지 않아 경첩감이 사라지지 않는다. 입의 동작은 가림이 아니라 **외형 변화**.
- **부위별 최종 공식**: 눈 = ARAP 워프 (가림 동작) / 입 = 동일세션 상태 스프라이트 + **측정 기반 사방 밀착 페이드**(입술 콘텐츠에 패치 밀착, 피부·턱 불관여 — v21의 턱 워프 0.8~1.6px≈정지와 일치).
- 경과 기록: v0.4 스프라이트(피부 과다→이음새) → v0.5 워프(이음새 0이나 경첩) → v0.6 밀착 스프라이트(형태 변화 + 이음새 0). 워프 기계는 눈 전용으로 확정, 입 기계는 extract_mouth_states.py(트림/톤매칭/사방밀착 전부 측정 기반).

## 2026-06-11 rig v0.5 — 입 ARAP 워프 채택 (주인님 결정, 턱 문제 근본 해소)

- 스프라이트 경로(v0.4)는 패치 피부가 원본 턱선을 가려 트림→톤매칭→하단/사방 페이드 3중 봉합에도 잔여 가림 — 주인님이 ARAP 교체를 제안.
- 워프 경로의 과거 약점 2개(내부 출처, 짜부)는 이미 해소된 상태였으므로 교체 즉시 성공: **원본 입술·턱 픽셀의 변형이라 톤 이음새·턱선 가림이 원리적으로 0.** 내부 12px 상향으로 이빨 노출 타이밍 보정.
- 최종 입 공식 갱신: **눈과 입 모두 ARAP 워프** (입만 "진짜 마스터 동일세션 내부"를 마스크 노출로 결합). 스프라이트 경로는 --mouth-states-dir 대안으로 보존.
- 교훈: "거의 성공"으로 기록된 기계는 약점이 해소되면 재평가할 것 — 폐기가 아니라 보류였다.

## 2026-06-11 rig v0.4 — v21 최종 입 패턴 부활 (주인님 정정)

- 주인님 정정: 워프 방식은 기록된 마지막 입 성공패턴이 아니었다. **v21 실제 최종 패턴 = 일관된 풀 입 상태 스프라이트 4장(closed_smile/small/mid_teeth/wide_teeth_tongue)의 겹침 크로스페이드, 분리 내부 레이어(inner/teeth/tongue)는 전 구간 불투명도 0으로 폐기**되어 있었다 (v21 character.json 실측).
- 재구현: v21 커브 수치 그대로 + 상태 스프라이트는 진짜 마스터 참조 동일세션 시트로 재생성 + **closed는 원본 mouth_line이 담당**(픽셀-가이드) + 패치 트림/페더로 경계 띠 제거. 런타임 자연 개방 확인.
- 워프 경로(v0.3)는 폐기 아닌 보존 — 눈 깜빡임은 워프가 정답(덮기), 입은 상태 스프라이트가 정답(드러내기+형태 변화)이라는 부위별 공식 차이를 기록.

## 2026-06-11 rig v0.3 — 입 단계화 통합 (재생성 성공)

- 구 내부(별도 세션·클린베이스 참조) 주인님 "자연스럽지 않음" 판정 → **진짜 마스터 참조 4상태 일관 시트 1장 재생성** (v10 실패→B3 revision 처방의 완성형). 내부 단독 셀만 픽셀 채택, 나머지 상태는 가이드.
- 워프 개선: 내부를 짜부 대신 **마스크 노출**(이빨 비율 보존, 공식 방식). 패치 4장(입술=원본 워프+진짜 내부)이 MouthOpenY 삼각 커브로 구동.
- validator PASS, 런타임 5단계 개방 확인. 입 워프 수치 = mouth_open_bake_config.json (1명령 재베이크).
- 역사 기록 정정: "재생성 성공했었나" → v10 FAIL → B3 revision PASS_CANDIDATE(중단) → **이번에 휴먼 합격으로 완결**.

## 2026-06-11 rig v0.2 — ARAP 깜빡임 통합 (주인님 조건부 합격)

- ARAP-EXP-001 v2 (아몬드 보정: 윗꺼풀 주도, 눈꼬리 고정, 63% 아래볼록 아치 — 공식 모델 hiyori/miara 실측 반영) 주인님 합격, 단 상시 수정 가능 조건.
- 수정 보장 구조: 워프 수치 = `arap_blink_layers/arap_blink_config.json`, 재베이크 = `bake_arap_blink_layers.py` 1명령 → 빌더 `--arap-eye-dir`로 반영.
- 원본 픽셀 패치 8장(좌우×4단계)이 삼각 크로스페이드 커브로 구동, 생성 감은꺼풀 폐기. validator PASS, 런타임 5단계 깜빡임 확인.
- 다음: 입 단계화 (MouthOpenY — 같은 워프 기법으로 입술 벌어짐), 이후 HAIR-SPLIT + 물리.

## 2026-06-11 rig v0.1 + ARAP-EXP-001 — PENDING_HUMAN_REVIEW

- **v0.1 입 재정합 (VERIFIED)**: 생성 입 내부의 위치·크기를 원본 mouth_line bbox에서 파생 (픽셀-가이드 원칙). 과대 입 해소, 스윕 렌더 자연.
- **ARAP-EXP-001 (판정 대기)**: 컬럼별 커튼 워프(타원 눈꺼풀 곡선)로 원본 픽셀만 사용한 5단계 깜빡임 스트립 생성. 생성 픽셀 0 → 스타일 드리프트 0. 합격 시 워프 프레임을 inbetween 레이어로 구워 기존 v21 5단계 불투명도 커브에 연결 (런타임 무수정 통합 경로).
- 증거: `experiments/autorig-template-001/reports/arap_blink_exp/blink_strip.png`, `scripts/run_arap_blink_experiment.py`.

## 2026-06-11 P3 자동 리깅 v0 — VERIFIED_SWEEP_SMOKE

- `scripts/build_autorig_rig_v0.py`: 하이브리드 레이어(재스킨 25 + 생성 숨은 5)에서 mini_cubism `character.json` 자동 생성. v21 성공패턴 스키마·수치 이식 (워프 6, 파라미터 7, 클램프 0.27/0.85, 불투명도 스왑).
- Validator PASS + 파라미터 스윕 스모크: neutral/blink/mouth/gaze/head **5상태 전부 상이한 렌더** — 자동 생성 리그가 실제로 움직임.
- 런타임 수정: `drawClippedEyePart`의 클립 마스크를 하드코딩 프리픽스 대신 클리핑 페어에서 역추적 (v21 하위호환, T3 스모크 PASS).
- 발견한 런타임 계약: 파트-디포머 매칭은 `deformer.child_ids` (deformer_node 필드는 메타데이터일 뿐), `part.bbox`는 [x,y,w,h].
- v0 잔여: 입 내부 과대(열림 상태), 머리 회전 시 hair_back 정지(v21 동일), 물리 미적용.
- 다음: T3 웹캠 드라이브를 이 리그에 연결 (자동 생성 캐릭터 최초 웹캠 구동).

## 2026-06-11 진짜 마스터 하이브리드 — VERIFIED_REVIEW_READY

- **치명적 교훈**: 기물 눈·얼룩의 진범은 `source_front_2048_inpaint_clean`(v22 때 눈을 지운 클린베이스)을 마스터로 오인한 것. 분해도 생성도 눈 없는 얼굴을 참조했다. **마스터 선택을 자동화 파이프라인의 명시적 입력 검증 단계로 만들 것** (눈/입 존재 검사).
- 진짜 마스터 = `new_character_002_source_front.raw.png`(1254→2048 승격, `experiments/autorig-template-001/true_master_2048.png`).
- 확정 레시피: ① See-through 640 분해(기하·레이어 분리) ② `reskin_seethrough_layers.py` 재스킨(픽셀 소유권 앞→뒤 배타 부여, 보이는 영역=원본 픽셀, 가린 영역=인페인팅, 안개 알파 90 제거) ③ **눈 포함 모든 가시 레이어는 분해+재스킨(원본 픽셀) 그대로 사용** — 생성 눈 삽입은 비대칭으로 폐기 ④ 슬롯 생성은 리깅용 숨은 레이어 전용(감은꺼풀·눈꺼풀 inbetween·홍채 완전체·입 내부) = v21 성공패턴과 동일 구조. 결과물 `hybrid_true_origeyes.png` — 원본과 사실상 동일하면서 레이어 분리 완료.
- 남은 미세 항목: 홍채 색(남색→보라끼 미세조정), 분해 풀해상도화(Ubuntu CUDA 런북).

## 2026-06-11 전체 슬롯 생성 전신 조립 — DISCARDED_GEOMETRIC_INCOHERENCE (주인님 판정: 괴물)

- 64파트 전부를 독립 슬롯 생성 후 bbox-fit 배치한 전신 조립은 시각 FAIL. 원인: 각 파트가 독립된 암묵적 비례/원근으로 생성되어 전역 기하 정합이 불가능 (bbox는 위치+크기 2자유도뿐). 음영류 파트는 기댈 형태가 없어 색 덩어리화.
- 결론: **`single_master_png_first` 원칙은 유효하다.** 슬롯 생성은 "마스터에 없는 숨은 레이어"(감은꺼풀/홍채 전체/입 내부/밑색 ~18개) 전용으로 한정하고, 가시 파트 ~46개는 마스터에서 분리한다 (See-through 경로). 오염(국소·수리가능)과 기하 비정합(전역·수리불가) 중 후자가 치명적.
- 보존 가치: 슬롯 준수 63/64·크로마 추출·despill·조립 합성 파이프와 "숨은 레이어 생성" 경로는 검증됨. 전신 슬롯 생성만 폐기.

## 2026-06-11 템플릿 슬롯 생성 — 전체 12시트 (VERIFIED_TECHNICAL / H1.5 대기)

- 64-part 전부를 고정 슬롯 시트 12장으로 분리 생성 (gpt-image-2, 스타일 레퍼런스 = source_front). 슬롯 준수 63/64 (입꼬리 2개는 초소형 임계값 오판, 추출은 64/64 성공). **사후 추출이 없으므로 이웃 오염 0** — v22 오염 클래스의 구조적 해소를 실증.
- 전신 조립 합성 성공 (캐릭터로 인식됨). 중립 조립 규칙 확장: closed 외에 mouth_inner/teeth/tongue도 키포즈 전용으로 제외.
- 교훈: ① codex exec는 분리된 백그라운드 컨텍스트에서 세션 생성 전에 멈춘다 — 생성은 포그라운드 셸에서. ② 타임아웃이 codex 자식 바이너리를 고아로 남긴다 — pkill 정리 필요. ③ 초소형 파트(입꼬리·코)는 점유율 임계값을 별도로.
- 증거: `experiments/autorig-template-001/reports/` (시트별 pilot_report + full_assembly_report), 뷰어 `review_viewer.html`.
- 다음: 주인님 H1.5 검수 (배치/크기 드래그 보정 — 볼터치 과대, 오른눈 속눈썹, 가슴 의류 패널이 1차 후보).

## 2026-06-11 T3 + 관제탑 (VERIFIED)

- **T3 PASS — 체인 끝단 최초 연결**: 저장된 T1 웹캠 스트림(175프레임)과 합성 12샘플을 `__miniProbe.setParameterValues`로 자체 Mini Cubism 런타임(v21 supported rig)에 주입. 적용 파라미터 중앙값 6, EyeOpen 0.27/MouthOpenY 0.85 클램프 왕복 검증, 캔버스 해시 모션 확인. 증거: `experiments/mini-cubism-webcam-drive-001/reports/t3_smoke_report.json`. 실웹캠 데모: `python3 scripts/run_mini_cubism_webcam_drive.py` → /drive.
- **관제탑 VERIFIED**: 이벤트 JSONL 컨벤션(`scripts/autorig_events.py`, run_started~run_completed 12종) + 읽기전용 대시보드(`control_tower/`, 8095) + 시뮬레이터. 파이썬 스모크 18/18(라이브러리/API/게이트 왕복/크래시 복원), 브라우저 스모크 8/8(타임라인/피드 증가/게이트 배너/마커 드래그→JSONL 기록/패널 재배치/완주). 증거: `experiments/autorig-control-tower-001/reports/`.
- 교훈: ① 폴링 재렌더 중 드래그가 끊긴다 → 조작 중 렌더 가드 필수. ② 강제 종료된 시뮬 런은 GATE_WAITING 좀비로 남는다 → 자동 런 전환 로직 금지, 명시 선택. ③ 헤드리스 드래그는 뷰포트 밖 좌표에서 조용히 실패한다 → scrollIntoView 선행.

## 2026-06-10 방향 전환 (AUTORIG 피벗)

주인님 결정으로 Cubism Editor 수동 저작 경로(구 G7/G8)를 폐기하고, **자체 에디터/런타임 + AI 자동리깅**으로 전환했다. 상세는 `docs/ref/AUTORIG-PIPELINE-V1.md`.

- 유지: Cubism 파라미터 ID 표준, 64-part `v2_standard` 스펙, MediaPipe→Cubism 트래킹 맵(T0–T2 PASS), character-002 64-part 후보, strong20 구조 기준치.
- 폐기/중단: `.cmo3/.moc3` 저작 게이트, B4/B5 수동 앵커 미세조정 루프(템플릿 슬롯 생성이 앵커 문제 자체를 제거), PSD→Cubism import 체크리스트 계열 작업 ID.
- 피벗 전 전체 상태 문서: `docs/archive/2026-06-10-PROJECT-STATUS-pre-autorig-pivot.md` (증거 테이블 169행 + 검증 명령 보존).
- 아래 기존 Evidence 상태 테이블의 항목들은 사실 기록으로 유효하다. 단 "real Cubism authoring 필요" 류의 결론은 AUTORIG 경로에서는 "자체 rig JSON 저작·검증"으로 읽는다.

## 목적

`2d-vtuber-ai-tool-plan.md`의 주장을 실제 실험 근거 기준으로 분리한다. 웹검색으로 유망한 내용과 로컬에서 직접 검증한 내용을 섞지 않기 위해, 모든 핵심 가정은 아래 상태 중 하나로 관리한다.

```text
VERIFIED:
  현재 Vtube 폴더의 입력/출력/명령/스크린샷/리포트로 재확인 가능

OBSERVED:
  로컬 실험은 했지만 수치화/자동화/반복성 검증은 부족함

RESEARCHED:
  웹검색, 논문, 오픈소스 문서 기준으로 유망함
  아직 주인님 환경에서 실행하지 않음

UNVERIFIED:
  플랜상 필요하지만 아직 실험 없음

BLOCKED:
  실행 조건, 라이선스, 하드웨어, OS, 의존성 문제로 막힘

DISCARDED:
  실험 결과 플랜에서 제외
```

## 현재 Evidence 상태

| 항목 | 현재 상태 | 근거 | 플랜 반영 수준 |
|---|---:|---|---|
| Cubism v2 new character 002 material-pack-first | VERIFIED_TECHNICAL_PNG / HUMAN_REVIEW_REGENERATE_CLEAN_BASES | `experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png`, `material_keypose_pack_closeups.raw.png`, `material_keypose_pack_fullface.raw.png`, `material_pack_first_v0/normalized_layers/`, `reports/material_pack_first_keypose_validation_report.json`, `reports/material_pack_first_contact_sheet.png`, `reports/material_pack_first_overlay_qa_report.md`, `reports/material_pack_first_overlay_human_review_20260609.md`, `reports/overlay_qa/eye_overlay_qa_sheet.png`, `reports/overlay_qa/mouth_overlay_qa_sheet.png`, `scripts/normalize_cubism_v2_material_pack_first_002.py`, `scripts/build_cubism_v2_material_pack_first_overlay_qa_002.py` | Source/front and same-character material sheets were generated and normalized into 21 full-canvas 2048 RGBA candidates, including open eyes plus the 19 validator-required clean/keypose PNGs. `validate_cubism_v2_keypose_pngs.py` PASSed with missing 0, normalize required 0, alpha/mode repair 0. Overlay QA corrected eye/mouth anchors and shows mouth states are centered much better, but 주인님 confirmed clean socket/closed underpaint and `mouth_base_clean` still look pasted over the original with visible round/oval skin-patch boundaries. Production material promotion remains blocked until these weak clean-base assets are regenerated or edited; manual-aligned Mini Cubism diagnostics are tracked separately. |
| Cubism v2 new character 002 Mini Cubism v7 EyeOpen diagnostic | VERIFIED_MINI_CUBISM_EYE_OPEN_027 | `scripts/build_mini_cubism_eye_open_027_packet_002.py`, `experiments/cubism-v2-new-character-002/model_edit_v7_smooth_mouth_preview/mini_cubism_diagnostic_project/reports/validation_report.json`, `experiments/cubism-v2-new-character-002/reports/model_edit_v7_smooth_mouth_preview/eye_open_027_success_packet/eye_open_027_success_report.json`, `eye_open_027_contact_sheet.png` | v7 diagnostic preview validates with 19 parts, 19 meshes, 6 deformers, 5 active parameters, and 6 keyform bindings. Browser automation drove `ParamEyeLOpen/ROpen` at 1.0, 0.5, 0.27, and 0.0. `0.27` activates `eye_L/R_half_closed_lid` and matches 주인님's natural-close observation; `0.0` activates closed lid plus closed underpaint and remains a technical full-close check. This is local Mini Cubism diagnostic/keypose evidence only, not real Cubism `.cmo3/.moc3` authoring success. |
| Vtube 로컬 자산 목록 | VERIFIED | `find /Users/family/jason/Vtube`, PNG 크기/해시 확인 | 자산 baseline으로 사용 가능 |
| imagegen canonical 정면 생성 | OBSERVED | `experiments/imagegen-limit-test-001/results.md` | 후보 생성 전략에 반영 가능 |
| imagegen labeled parts sheet 한계 | OBSERVED | 라벨 오타, 좌우 불균형, canonical 불일치 관찰 | "최종 PSD로 바로 쓰지 않음" 근거로 사용 |
| imagegen no-label parts sheet 개선 | OBSERVED | `imagegen-limit-test-002` 결과 | no text/no labels 규칙 반영 가능 |
| imagegen eye/mouth/underpaint 개별 생성 | OBSERVED | `imagegen-limit-test-002` 결과 | 다음 crop/mask 실험 대상으로 사용 |
| imagegen crop/mask 자동화 가능성 | VERIFIED | `validation-smoke-001`에서 mouth 14개, eye 18개 crop/mask 생성 | smoke 통과, semantic 분류는 추가 필요 |
| canonical 위 mouth/eye 합성 가능성 | OBSERVED | `validation-smoke-001/composites/*` 생성 | mouth는 후속 가치 있음, eye는 분류/위치 보정 필요 |
| 좌표 기반 mouth/iris 자동 정렬 | VERIFIED | `coordinate-align-001`에서 anchor 검출, alpha center 정렬, placement error 측정 | 스크린샷 기반 조정보다 우선할 성공패턴 |
| full eye semantic grouping | DISCARDED | `eye-grouping-001` human review: 위치와 미술 품질 모두 부족 | naive sheet-part grouping은 production 경로에서 제외 |
| full-canvas mouth layer | OBSERVED | `full-canvas-layer-001`에서 canonical 크기 투명 mouth layer 생성 | previewer 입력 구조로 유지, 미술 품질은 REVISE |
| canonical eye geometry/mask | VERIFIED | `canonical-eye-001`에서 iris/eye ROI/mask 추출 | 눈 작업 기준 geometry로 유지 |
| sheet closed-lid blink | DISCARDED | `blink-001`에서 ROI 안에는 들어오지만 visual alignment FAIL | sheet blink 후보 폐기 |
| mouth candidate scoring | OBSERVED | `mouth-style-001`에서 expression type/shortlist/reject 생성 | 후보 축소용으로 유지, 승인 근거는 아님 |
| non-human anchor schema split | VERIFIED | `creature-schema-001`에서 human/dog/cat schema 분리 | 비인간 캐릭터에 human 공식 재사용 금지 |
| production 2048 canvas policy | VERIFIED | `production-canvas-2048-001/reports/resolution_spec_report.json` | 상반신 production master는 2048x2048로 고정 |
| production 2048 canonical master | OBSERVED | `production-canvas-2048-001/canonical/canonical_front_2048.png`, source 1254x1254 → 2048 normalize | visual review 필요, native 2048 생성은 미확인 |
| production 2048 anchor/ROI extraction | OBSERVED | `production-canvas-2048-001/reports/anchor_2048_report.json` | mouth ROI는 유지, eye ROI detector는 fallback이라 개선 필요 |
| production 2048 full-canvas mouth layers | OBSERVED | `production-canvas-2048-001/reports/mouth_gen_2048_report.json` | previewer 후보로 유지, human visual quality는 REVISE |
| production 2048 canonical-mask blink | OBSERVED | `production-canvas-2048-001/reports/blink_2048_report.json` | full eye replacement 없이 layer 생성, visual alignment는 REVISE |
| production 2048 preview/report harness | VERIFIED/ARCHIVED | `experiments/archive/legacy-review-previews-20260604/production-canvas-2048-001-preview/index.html`, `harness_2048_report.json`, shared harness file | 레거시 standalone preview는 archive로 이동. 현재 검수는 `review_app`만 사용 |
| production 2048 next raw assets | OBSERVED | `asset-generation-2048-001/raw/*`, `reports/asset_manifest.json`, `reports/generated_assets_contact_sheet.png` | MOUTH-APPLY-DELTA, BLINK-STAGE, ALPHA-CLEANUP 입력 후보 |
| mouth A/B sheet after calibrated delta | VERIFIED | `mouth-apply-delta-001/reports/mouth_apply_delta_report.json`, `mouth_shortlist_report.json`, 주인님 visual review | calibrated `canvas_dx=-37.842`, `canvas_dy=6.307` 적용 후 훨씬 좋아졌고 사용 가능할 수 있는 수준. 주인님 결정으로 입 후보 10개 전부 사용. 개별 mouth offset은 rig preview에서 문제 보일 때만 fallback |
| blink staged full-canvas layers | OBSERVED/ARCHIVED | `blink-stage-001/reports/blink_stage_report.json`, `experiments/archive/legacy-review-previews-20260604/blink-stage-001-preview/index.html` | 3단계 `half/mostly_closed/closed` 생성 evidence는 유지. 레거시 preview는 archive로 이동 |
| blink saved placement apply | OBSERVED/ARCHIVED | `blink-apply-review-001/reports/blink_apply_review_report.json`, `experiments/archive/legacy-review-previews-20260604/blink-apply-review-001-preview/index.html` | 저장된 blink 위치값 evidence는 유지. 레거시 preview는 archive로 이동 |
| Live2D key-pose production direction | VERIFIED | `live2d-keypose-spec-001/reports/live2d_keypose_spec.md` | 입/깜빡임 PNG는 프로덕션 frame-swap 자산이 아니라 Cubism ArtMesh/Deformer/parameter key-pose reference로 사용. production target은 `ParamEyeLOpen/ParamEyeROpen`, `ParamMouthOpenY/ParamMouthForm` 매핑 |
| Cubism import material pack v1 | VERIFIED | `experiments/cubism-material-pack-001/reports/validation_report.json`, `reports/cubism_import_smoke.json`, `import_ready.psd`, `layer_manifest.json`, `rigger_handoff.md` | production layer와 reference_pack 분리, mouth/blink 후보는 PSD 밖 reference로 유지. raw-minimal PSD writer는 Cubism parsing 실패(`error signature @ 0x00000026`), psd-tools writer는 Cubism Editor 5.3 import smoke PASS 후 `import_ready.psd`로 승격 |
| Vtube doc SSOT cleanup | VERIFIED | `experiments/doc-ssot-cleanup-001/reports/doc_ssot_cleanup_report.json` | 루트 플랜을 얇은 최신 진입점으로 교체, 옛 6주 MVP 플랜은 `docs/archive/2026-06-03-legacy-2d-vtuber-ai-tool-plan.md`로 보존 |
| See-through PSD layer baseline | BLOCKED | repo clone/entrypoint 확인, 로컬 Mac 직접 inference는 CUDA/dependency 조건으로 미통과 | confirmed core path로 쓰지 않음 |
| ComfyUI-See-through Mac 실행성 | BLOCKED | plugin clone/py_compile PASS, standalone은 ComfyUI runtime 미설치로 실패 | 별도 ComfyUI 또는 remote GPU Gate 필요 |
| See-through layer 품질 | UNVERIFIED | 현재 canonical으로 출력 없음 | 플랜 핵심 게이트 |
| Mac ComfyUI See-through branch | FAIL_MPS_MEMORY | `experiments/see-through-layer-decomp-001/reports/comfyui_setup_report.json`, `reports/comfyui_mps_crash_report.json`, `reports/comfyui_inference_report.json` | MPS runtime/custom node/model download는 통과했지만 GenerateLayers에서 MPS memory abort 또는 no layers output. 실제 decomposition은 Ubuntu CUDA로 전환 |
| Mac MPS compatibility track | PASS_WITH_CUBISM_IMPORT | `docs/ref/MAC-LAYER-DECOMP-OPTIONS.md`, `experiments/see-through-mps-compat-002/reports/mps_patch_report.json`, `reports/mps_512_safe_inference_report.json`, `reports/mps_640_safe_inference_report.json`, `reports/normalize_report.json`, `reports/psd_candidate_gate_report.json`, `reports/cubism_import_smoke.json`, `reports/manual_mask_report.json`, `qa_report.md`, `review_app/review_manifest.json`, `scripts/apply_mps_manual_mask.py` | 512에서 MPS median/sort unsupported abort를 패치로 우회했고, 이후 640도 `*_layers.json`, raw 29 layers, normalized 2048 후보 29개 생성을 통과했다. 640은 주인님 검수에서 더 선명하다고 판단됐고, `O` 후보가 저장 즉시 PSD 후보로 자동 빌드된다. 최종 MPS baseline은 ROI `neck`, ROI `neck_underpaint`, ROI `mouth_inner`를 포함하고 raw `mouth_line`은 제외한 16레이어 `import_ready.psd`를 Cubism Editor 5.3에서 다시 열어 개별 레이어 import를 확인했다. |
| Imagen Live2D 001 pipeline | LEGACY_SHALLOW_RIG_FAILURE_FIXTURE / FORCED_REVIEW | `experiments/imagen-live2d-001/canonical/canonical_front_2048.png`, `reports/mps_512_safe_inference_report.json`, `reports/mps_640_safe_inference_report.json`, `layer_manifest.json`, `reports/mps_candidate_contact_sheet.png`, `reports/part_visual_review.json`, `reports/forced_pass_front_hair_arms_report.json`, `reports/psd_candidate_gate_report.json`, `reports/cubism_import_smoke.json`, `reports/cubism_mvp_rig_smoke_plan.json`, `reports/cubism_mvp_rig_smoke_checklist.md`, `reports/cubism_mvp_rig_validation.json`, `reports/cmo3_structure_report.json`, `reports/cubism_mvp_rig_evidence/gui_parts_parameters_current.png`, `cubism_mvp_rig.cmo3`, `moc3_export_smoke/`, `import_ready.psd` | Imagen canonical, MPS decomposition, Cubism import smoke, FREE-limit audit, texture atlas, CMO3 preservation, and MOC3 runtime export smoke passed. However CMO3 structure has 19 ArtMeshes and 27 Parameters with 0 Warp Deformers, 0 Rotation Deformers, and 0 KeyformBindings. Keep this as an import/runtime smoke reference and shallow-rig failure fixture, not the default next-model path. |
| Official Live2D reference model structure baseline | VERIFIED_CUBISM_FIRST_SPEC | `experiments/reference-model-structure-001/official_samples/download_manifest.json`, `official_github_samples/github_sample_manifest.json`, `catalog.official_samples.json`, `catalog.official_github_samples.json`, `catalog.official_combined.json`, `reports/official_sample_profiles.md`, `reports/reference_model_structure_summary.combined.md`, `reports/reference_rig_pattern_baseline.combined.md`, `reports/cubism_success_pattern_spec.md`, `docs/ref/CUBISM-V2-SUCCESS-PATTERN-PLAN.md`, `docs/ref/VTUBE-HARNESS-SKILL-ROUTING-AUDIT.md`, shared harnesses `vtube-reference-model-structure.md`, `vtube-cubism-success-pattern-spec.md` | Live2D 공식 샘플 페이지의 학습 포인트를 짧은 profile로 정리하고, 주인님이 제공한 24개 공식 zip과 5개 공식 Live2D GitHub SDK/Garage repo runtime resources를 구조만 분석했다. Combined 결과는 57 official reports, 34 `FULL_STRUCTURE`, 23 `RUNTIME_ONLY`, `py-moc3` PASS 50, 필수 baseline 섹션 `eye/mouth/hair/body_angle` non-empty다. `cubism_success_pattern_spec.md`와 `CUBISM-V2-SUCCESS-PATTERN-PLAN.md`가 현재 기본 경로이며, 다음 모델을 이미지 해상도보다 Cubism part/deformer/keyform spec 기준으로 설계하도록 고정한다. 공식 샘플의 그림/텍스처/PSD는 우리 모델에 재사용하지 않는다. |
| Live2D strong20 deep motion analysis | VERIFIED_DEEP_NUMERIC_BASELINE_WITH_CORE | `experiments/live2d-strong-model-pattern-001/reports/deep_reference_motion_analysis.json`, `deep_reference_motion_analysis.md`, `strong20_core_api_extractor_report.json`, `strong20_core_api_extractor_report.md`, `core_api/*/core_snapshot.json`, `scripts/build_live2d_deep_reference_motion_analysis.py`, `scripts/run_live2d_core_api_extractor.py` | strong20의 기존 neutral/motion/extreme 캡처와 CMO3/model3/physics3/motion3 evidence를 재사용해 더 깊은 수치 분석을 추가했다. 결과는 360 visual diff rows, 215 category-inferred parameter influence rows, 20/20 physics3 response proxy, 8,525 motion3 curves다. 추가로 Cubism SDK for Web / Live2DCubismCore-backed Framework snapshot extractor가 20/20 PASS하여 Parameters/Parts/Drawables/Offscreens/CanvasInfo, drawable mask, drawOrder/renderOrder, dynamic flags, vertex bounds를 모델별 `core_snapshot.json`으로 저장했다. Core 보강 후 mask/draw-order risk는 LOW 7 / MEDIUM 7 / HIGH 6이다. 분석은 자산 복제가 아니라 구조/움직임/위험 패턴 계측이다. |
| Live2D parameter single sweep and generation readiness | VERIFIED_PRE_GENERATION_READY | `experiments/live2d-strong-model-pattern-001/reports/strong20_parameter_single_sweep_report.json`, `strong20_parameter_single_sweep_report.md`, `parameter_single_sweep/*/*.png`, `experiments/reference-model-structure-001/reports/cubism_v2_new_model_pre_generation_readiness.json`, `cubism_v2_new_model_pre_generation_readiness.md`, `scripts/run_live2d_parameter_single_sweep.py`, `scripts/build_cubism_v2_pre_generation_readiness_spec.py`, skill `/Users/family/.codex/skills/vtube-cubism-success-pattern-workflow/SKILL.md`, harnesses `vtube-live2d-strong-model-pattern.md`, `vtube-live2d-all57-production-design.md` | strong20에서 단일 파라미터 min/max sweep을 실행해 20 models, 320 samples, 27 parameters를 확보했다. Category summary: body_angle 108 samples median 0.026783, eye 156 samples median 0.004109, mouth 34 samples median 0.024491, hair 22 samples median 0.040611. Readiness spec은 기존 64-part v2_standard taxonomy를 유지하고, 첫 v2_standard 모델에는 full runtime/Core 분석을 strong20 밖으로 확장하지 않는다고 결정했다. 추가 분석은 v2_rich, non-human, side-view, heavy effects, complex arm/hand switching 때만 한다. 새 스킬 생성 대신 기존 Cubism success-pattern skill과 shared harness들을 업데이트했다. |
| Cubism v2 character prompt template | VERIFIED_PROMPT_TEMPLATE_READY | `experiments/reference-model-structure-001/reports/cubism_v2_character_prompt_template.json`, `cubism_v2_character_prompt_template.md`, `scripts/build_cubism_v2_character_prompt_template.py` | production spec schema v2, 64-part v2_standard part spec, G0-G3 readiness checklist를 입력으로 단일 master PNG 생성용 프롬프트 템플릿을 생성했다. 결과는 `single_master_png_first`, target 64 parts, physics target 4-6, required parameters 12개, required deformer hierarchy nodes 9개, G0-G3 연결, safe/default 및 extra-clean-split variant 2개를 포함한다. Negative prompt는 text/labels/UI/watermark/part diagram/exploded layer sheet와 얼굴/눈/입 가림, 복잡한 손/소품을 금지한다. 이는 이미지 생성을 바로 승인하는 것이 아니라 G0 concept 후보 생성 전 입력 기준이다. |
| Cubism v2 new character G0 concept | VERIFIED_G0_CANDIDATE_SELECTED | `experiments/cubism-v2-new-character-001/concepts/g0_adult_cute_female_candidate_001.png`, `g0_adult_cute_female_candidate_002.png`, `reports/g0_concept_selection_report.json`, `g0_concept_selection_report.md` | 주인님 요청 `여자 성인 귀여운 느낌`을 v2_standard prompt template에 맞춰 첫 G0 후보로 생성했다. Candidate 001은 예쁘지만 목걸이/귀걸이/헤어핀/레이스/의상 디테일이 많아 `REFERENCE_ONLY`. Candidate 002는 성인 여성 귀여운 인상, 정면 상반신, 눈/입 명확, 앞머리/옆머리/뒷머리/목/어깨/상체 경계가 더 깨끗해 `KEEP_FOR_G1`로 선택했다. 아직 production 성공은 아니며 다음 검증은 G1 64파트 taxonomy split feasibility다. |
| Cubism v2 new character G1 taxonomy | VERIFIED_G1_TAXONOMY_PASS_WITH_DERIVED_REQUIREMENTS | `experiments/cubism-v2-new-character-001/reports/g1_part_taxonomy_review.json`, `g1_part_taxonomy_review.md`, `g1_part_taxonomy_visual_guide.png`, `scripts/build_cubism_v2_g1_taxonomy_review.py` | Candidate 002를 64파트 v2_standard taxonomy 기준으로 검수했다. 결과는 `PASS_WITH_DERIVED_PART_REQUIREMENTS`: 64 parts, DIRECT_VISIBLE 30, DIRECT_VISIBLE_RISK 16, DERIVED_KEYPOSE_REQUIRED 7, UNDERPAINT_REQUIRED 9, SIMPLIFY_OR_MERGE 2. 직접 보이거나 리스크를 감수하고 분리 가능한 파츠는 46개다. 단일 PNG에서 보이지 않는 mouth inner/teeth/tongue/closed lid/underpaint는 실패가 아니라 material planning에서 생성/수동 제작할 항목으로 분류했다. 다음 단계는 G1 material planning packet이다. |
| Cubism v2 new character G1 material planning | VERIFIED_G1_MATERIAL_PLAN_READY | `experiments/cubism-v2-new-character-001/reports/g1_material_planning_packet.json`, `g1_material_planning_packet.md`, `scripts/build_cubism_v2_g1_material_plan.py` | G1 taxonomy 결과를 실제 PSD/material pack 제작 순서로 변환했다. Self-review PASS: 원본 직접 추출 46개(안전 30 + 정리 필요 16), 보조 생성 keypose 7개, underpaint 9개, 병합/단순화 의상 그림자 2개, 10단계 PSD/material pack 제작 순서, draw-order band, 64파트 전체 accounted. 다음 검증은 실제 full-canvas material asset 생성 후 contact sheet와 G1 material QA다. |
| Cubism v2 new character material asset draft | VERIFIED_MATERIAL_ASSET_DRAFT_READY | `experiments/cubism-v2-new-character-001/material_pack_v0/material_asset_manifest.json`, `layer_manifest.json`, `production_layers/*.png`, `reports/material_contact_sheet.png`, `reports/material_asset_validation_report.json`, `import_ready_candidate.psd`, `scripts/build_cubism_v2_material_asset_manifest.py`, `scripts/generate_cubism_v2_full_canvas_material_assets.py`, `scripts/build_cubism_v2_material_contact_sheet.py`, `scripts/validate_cubism_v2_material_assets.py` | Candidate 002를 Cubism용 material asset draft로 변환했다. 자동검사 PASS: 64 taxonomy accounted, 62 generated full-canvas 2048 PNG layers, 2 merged metadata entries, critical missing 0, warning 0, PSD candidate 2048x2048 RGB 8-bit with 62 layers. Contact sheet에서 작은 눈/입/머리끝 파츠는 사람이 다시 봐야 하며, `import_ready_candidate.psd`는 Cubism Editor import smoke 전까지 `import_ready.psd`로 승격하지 않는다. |
| Cubism v2 material review UI | VERIFIED_LOCAL_REVIEW_UI_READY | `scripts/run_cubism_v2_material_review_server.py`, `experiments/cubism-v2-new-character-001/material_pack_v0/reports/material_human_review.json`, `material_human_review_summary.json`, `material_review_fix_queue.json`, browser screenshot `cubism-v2-material-review-ui.png` | Material pack draft를 한국어 로컬 UI에서 파츠별로 검수하고 저장할 수 있게 했다. UI는 큰 파츠 미리보기, 검색, gate/verdict 필터, `KEEP/REVISE/REGENERATE/MERGE/IGNORE` 판정, issue tag, human note를 지원한다. API smoke에서 state/load, review save, asset load가 PASS했고 테스트 판정은 다시 `UNREVIEWED`로 되돌렸다. 현재 실제 사람 검수 시작 상태는 64 `UNREVIEWED`, fix queue 0이다. |
| Cubism v2 material first-pass review | OBSERVED_CODEX_FIRST_PASS_FIX_QUEUE_READY | `scripts/seed_cubism_v2_material_review_first_pass.py`, `experiments/cubism-v2-new-character-001/material_pack_v0/reports/material_human_review.json`, `material_human_review_summary.json`, `material_review_fix_queue.json`, browser screenshot `cubism-v2-material-review-first-pass.png` | 주인님이 판별이 어렵다고 해서 Codex 보수적 1차 검수를 저장했다. 이것은 최종 human visual approval이 아니라 fix queue 생성용 first-pass다. 결과: 64 reviewed, `KEEP` 9, `REVISE` 41, `REGENERATE` 12, `MERGE` 2, fix queue 53. 이 결과는 현재 bbox/color-mask material draft가 technical scaffold로는 통과했지만, Cubism import smoke 전에 semantic mask cleanup, eye/mouth 재생성, underpaint trimming이 필요하다는 evidence다. |
| Cubism v2 material fix batch 001 | VERIFIED_FIX_BATCH_001_APPLIED | `scripts/build_cubism_v2_material_fix_batch_report.py`, `experiments/cubism-v2-new-character-001/material_pack_v0/reports/material_fix_batch_001_report.json`, `material_fix_batch_001_report.md`, `material_contact_sheet.png`, `material_asset_validation_report.json`, browser screenshot `cubism-v2-material-fix-batch-001.png` | 요청된 1차 수정 묶음을 적용했다. 감은 눈/눈 하이라이트/입 안쪽/치아/혀/입술 마스크/입선/입꼬리 12개는 source cut 대신 derived detail 생성으로 바뀌어 `REGENERATE` 0이 됐다. underpaint 9개는 bbox 축소와 hidden-area fill 보정으로 블록감을 완화했고, 몸/얼굴/의상 주요 bbox도 일부 축소했다. 자동검사 PASS는 유지된다: 64 taxonomy accounted, 62 PNG layers, PSD 62 layers. 남은 53 `REVISE`는 semantic/manual polish queue다. |
| Cubism v2 material Cubism import smoke | VERIFIED_CUBISM_IMPORT_SMOKE | `experiments/cubism-v2-new-character-001/material_pack_v0/reports/cubism_import_smoke.json`, `cubism_import_smoke.md`, `cubism_import_smoke_imported_layers.png`, `import_ready.psd` | Live2D Cubism Editor 5.3.01 FREE 버전에서 `import_ready_candidate.psd`를 내부 `PSD 파일로 새 모델 생성` 흐름으로 열었다. 창 제목은 `import_ready_candidate`로 바뀌었고, 로그에는 `Read LayerAndMaskInfo`, `Read ImageData`, `load @PSDDocument`가 기록됐다. 파츠 패널에는 `61_collar_front`, `56_hair_front_tip_R`, `44_mouth_corner_R`, `39_mouth_upper_lip_mask` 같은 개별 레이어가 보여 평탄화되지 않은 import로 판정했다. `import_ready.psd`는 technical import-gate pass artifact이며, 남은 53 `REVISE`는 visual/semantic polish queue로 계속 분리한다. |
| Cubism v2 material Mini Cubism open smoke | VERIFIED_MINI_CUBISM_MATERIAL_OPEN_SMOKE | `scripts/build_mini_cubism_project_from_cubism_v2_material_pack.py`, `experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_v0/character.json`, `reports/mini_cubism_material_open_smoke.json`, `mini_cubism_material_preview.png` | 주인님 지적에 맞춰 정식 Cubism Editor import와 별도로, 현재 material pack을 우리 Mini Cubism preview 포맷으로 변환해 열었다. 결과는 62 parts, 62 meshes, 11 deformers, 15 parameters, 22 keyform bindings, 3 physics profiles. 브라우저 smoke에서 project loaded, 2048 canvas non-empty, sampled bbox `[612, 356, 836, 1388]`, `ParamAngleX/ParamMouthOpenY/ParamHairFront` 값 주입 PASS를 확인했다. 이는 local preview/QA evidence이며 CMO3/ArtMesh/final rigging evidence는 아니다. |
| Cubism v2 neutral composite repair | VERIFIED_NEUTRAL_REPAIR_V1 | `scripts/repair_cubism_v2_neutral_composite.py`, `experiments/cubism-v2-new-character-001/material_pack_v0/reports/neutral_repair_report.json`, `neutral_repair_report.md`, `neutral_repair_manifest.json`, `neutral_composite_before.png`, `neutral_diff_overlay_before.png`, `neutral_composite_after.png`, `neutral_diff_overlay_after.png`, `mini_cubism_project_material_v0/reports/mini_cubism_neutral_repair_v1_smoke.json`, `mini_cubism_neutral_repair_v1_smoke.md` | 주인님이 Mini Cubism import 화면에서 눈/입/underpaint가 어긋나 보인다고 지적한 뒤, neutral composite gate를 고정했다. Before all-visible bad ratio는 0.448374, neutral-visibility-only bad ratio는 0.443789로 리깅 전 FAIL이었다. Repair v1은 원본 `candidate_002`와의 after bad ratio를 0.0, missing/extra 0으로 낮췄고, before 문제 파츠 기여도 top20도 기록한다. 상위 원인은 `hair_back_underpaint`, `body_underpaint`, `chest_cloth_base`, `torso_base`, `arm_R_underpaint`다. `layer_manifest.json`에는 `NEUTRAL_REPAIR_V1_APPLIED`, 숨김 파츠 9개, `part_opacity_keyframes` 9개가 기록됐다. Mini Cubism smoke도 PASS: 62 parts/meshes, opacity keyframes 9, neutral에서 closed lid/open-mouth helper opacity 0, mouth open/eye closed extreme에서 해당 파츠 opacity 1. 이 검증은 pre-rig material neutral gate이며, 움직이는 ArtMesh/CMO3 성공 증거는 아니다. |
| Cubism v2 G1.5 semantic purity gate | VERIFIED_G1_5_SEMANTIC_PURITY_GATE | `scripts/build_cubism_v2_semantic_purity_gate.py`, `scripts/build_cubism_v2_semantic_owner_map.py`, `scripts/build_cubism_v2_layer_alone_qa.py`, `scripts/repair_cubism_v2_semantic_masks.py`, `experiments/cubism-v2-new-character-001/material_pack_v0/reports/semantic_purity/semantic_purity_gate_report.json`, `semantic_purity_gate_report.md`, `semantic_owner_map_before.png`, `semantic_owner_map_after.png`, `layer_alone_contact_sheet_after.png`, `layer_alone_problem_sheet_after.png`, `eye_mouth_roi_closeup_after.png`, `underpaint_leakage_map_after.png`, `mini_cubism_project_material_v0/reports/mini_cubism_semantic_purity_v1_smoke.json` | neutral composite PASS 이후에도 “픽셀 주인이 맞는가”를 확인하기 위해 G1.5 gate를 추가했다. Semantic owner map, layer-alone QA, eye/mouth ROI alignment, underpaint leakage check, targeted semantic remask가 한 번에 실행된다. Targeted remask는 neutral에서 top owner였던 underpaint 픽셀을 의미상 맞는 visible 파츠로 옮기고, eye/mouth 파츠 alpha를 전용 ROI 안으로 clamp한다. 결과: `PASS_G1_5_SEMANTIC_PURITY_GATE`, neutral after bad ratio 0.000022, missing/extra 0, underpaint top-owner pixels 76,826 -> 0, eye/mouth ROI alignment PASS, Mini Cubism semantic smoke PASS. 이는 G1.5 material semantic gate이며, 최종 Live2D CMO3/deformer/keyform 성공 증거는 아니다. |
| Cubism v2 G1.6 manual semantic anchor editor | VERIFIED_LOCAL_UI_READY | `scripts/run_cubism_v2_semantic_anchor_editor.py`, `experiments/cubism-v2-new-character-001/material_pack_v0/reports/manual_semantic_overrides.json`, `manual_semantic_overrides_summary.md`, `manual_semantic_anchor_editor_smoke.json`, `g1_6_semantic_anchor_editor.png` | 파츠 역할 정의 자체가 틀렸을 때 주인님이 원본 위에서 직접 “이 위치가 이 파츠”라고 지정할 수 있는 G1.6 UI를 추가했다. UI는 `http://127.0.0.1:5174/`에서 실행되며, 파츠 검색, ROI 박스 드래그, 모서리 resize, anchor 점 드래그, numeric ROI/anchor 편집, action/semantic_role/note 저장을 지원한다. 저장 대상은 `manual_semantic_overrides.json`이다. API smoke는 `eye_L_pupil` 임시 override를 저장한 뒤 삭제해 실제 수동 라벨 데이터를 오염시키지 않고 PASS했다. 이 evidence는 manual correction input UI 준비 증거이며, 저장된 실제 override를 semantic remask에 반영하는 것은 후속 단계다. |
| Face tracking to Cubism parameter map | VERIFIED_MAPPING_SPEC / WEBCAM_SMOKE_VERIFIED | `experiments/reference-model-structure-001/reports/face_tracking_to_cubism_parameter_map.json`, `face_tracking_to_cubism_parameter_map.md`, `scripts/build_face_tracking_to_cubism_parameter_map.py` | MediaPipe Face Landmarker/ARKit-like 입력을 v2_standard Cubism parameter floor에 연결하는 스펙을 생성했다. 14개 mapping이 있으며 required production parameters 12개는 모두 직접 또는 ownership 정책으로 커버된다: head yaw/pitch/roll → `ParamAngleX/Y/Z`, blink inversion → `ParamEyeLOpen/ROpen`, gaze → `ParamEyeBallX/Y`, `jawOpen` → `ParamMouthOpenY`, smile-frown → `ParamMouthForm`, damped head pose → body angle, idle → `ParamBreath`, optional vowels → v2_rich/motion-sync. T1 내장 웹캠 smoke가 통과했으므로 live tracking 입력 변환까지는 verified다. |
| Face tracking synthetic parameter smoke | VERIFIED_T0_STATIC_SYNTHETIC | `experiments/reference-model-structure-001/reports/face_tracking_synthetic_parameter_smoke.json`, `face_tracking_synthetic_parameter_smoke.md`, `scripts/run_face_tracking_synthetic_parameter_smoke.py` | 웹캠 없이 synthetic tracking samples 20개를 Cubism parameter 값으로 변환했다. 결과는 PASS: required production outputs 12개 모두 covered, failure_count 0, 모든 값 finite/in-range. Extremes include `ParamAngleX/Y/Z` -30..30, `ParamEyeLOpen/ROpen` 0..1, `ParamEyeBallX/Y` -1..1, `ParamMouthOpenY` 0..1, `ParamMouthForm` -0.7..0.8, body damped angles, `ParamBreath` 0..1. 이 evidence는 mapping 공식/범위 smoke다. |
| Face tracking webcam probe | VERIFIED_T1_LIVE_WEBCAM | `experiments/reference-model-structure-001/reports/face_tracking_webcam_probe_raw.json`, `face_tracking_webcam_probe_report.json`, `face_tracking_webcam_probe_report.md`, `scripts/run_face_tracking_webcam_probe_server.py`, `experiments/reference-model-structure-001/face_tracking_webcam_probe/index.html` | 노트북 내장 웹캠으로 MediaPipe browser probe를 실행했고, 10.05초 / 175프레임 / face_present_ratio 1.0으로 PASS했다. 12개 required Cubism output이 모두 175 samples, missing 0으로 covered됐고 failures/warnings는 none이다. 움직임 span은 `ParamAngleX` 31.386768, `ParamAngleZ` 36.872167, `ParamEyeLOpen` 0.538495, `ParamEyeROpen` 0.522155, `ParamMouthOpenY` 1.0, `ParamMouthForm` 1.105825다. 다음 검증은 이 stream으로 실제 Live2D model 또는 v2 rig preview를 구동하는 T2 parameter-drive smoke다. |
| Live2D webcam parameter drive | VERIFIED_T2_REFERENCE_MODEL_DRIVE | `experiments/live2d-strong-model-pattern-001/reports/webcam_parameter_drive_report.json`, `webcam_parameter_drive_report.md`, `webcam_parameter_drive_contact_sheet.png`, `experiments/live2d-strong-model-pattern-001/webcam_parameter_drive/*.png`, `scripts/run_live2d_webcam_parameter_drive.py` | T1에서 저장한 내장 웹캠 Cubism parameter stream을 실제 Cubism Web runtime reference model `haru_greeter_pro_jp_haru_greeter_t05`에 주입했다. `__vtubeProbe.setParameterValues`로 12개 대표 프레임을 적용했고, 각 프레임은 13/13 matched parameter applied, missing 0이다. 첫 실행의 neutral 배경-only 오염을 self-review로 발견해 neutral에도 모델 기본값을 먼저 적용한 뒤 재실행했다. 최종 결과는 PASS: neutral-model-relative changed_ratio median 0.008589, max 0.014553, contact sheet 정상. 이는 tracking stream이 verified reference model을 움직인다는 증거이며, 새 v2 production avatar 성공은 아직 아니다. |
| Live2D all57 auxiliary runtime metadata | VERIFIED_OPTIONAL_RUNTIME_METADATA | `experiments/reference-model-structure-001/reports/all57_runtime_metadata_extras.json`, `all57_runtime_metadata_extras.md`, `scripts/build_live2d_runtime_metadata_extras.py`, `experiments/reference-model-structure-001/reports/cubism_v2_new_model_pre_generation_readiness.json`, `cubism_v2_new_model_pre_generation_readiness.md` | 공식 문서 기준 `.cdi3.json`은 파라미터/파트/그룹 표시명, `.pose3.json`은 파츠 표시/숨김 전환, `.userdata3.json`은 ArtMesh 유저데이터, `.exp3.json`은 표정 diff/fade, `.model3.json`은 HitAreas와 EyeBlink/LipSync group, `.motionsync3.json`은 고급 립싱크 설정을 담는다. all57 스캔 결과: model3 50, cdi3 50, pose3 22, userdata3 6, exp3 model groups 19, motionsync3 4, hit-area models 25, LipSync group models 39, EyeBlink group models 47. 이 항목들은 이름/터치/표정/고급 립싱크 설계 보조이며 첫 v2_standard 컨셉/이미지 생성의 blocker가 아니다. |
| Live2D strong20 carousel player | VERIFIED_LOCAL_PLAYER | `experiments/live2d-strong-model-pattern-001/probe_sandbox/strong20/Samples/TypeScript/Demo/public/model_carousel.html`, `scripts/build_live2d_model_carousel_player.py`, `scripts/run_live2d_model_carousel_player.py`, `run-live2d-model-player.command`, `live2d-model-carousel-player.png` | 검증된 strong20 모델을 좌우 화살표로 넘겨보는 로컬 Web Player를 추가했다. 기존 Cubism Web sandbox와 `__vtubeProbe`를 사용해 모델 렌더 영역을 화면 대부분으로 유지하고, 한국어 상단 컨트롤/좌우 버튼/키보드 ArrowLeft/ArrowRight를 제공한다. Browser smoke 결과: `hasProbe=true`, `namesCount=20`, 첫 모델 `haru_greeter_t05` 표시, 오른쪽 화살표 후 `haruto_t01` 표시, screenshot 1440x1000 저장. |
| Live2D all57 carousel player | VERIFIED_LOCAL_PLAYER_WITH_MOTION_BUTTON | `experiments/live2d-strong-model-pattern-001/reports/all57_render_manifest.json`, `all57_render_manifest.md`, `all57_manual_operator_observations_20260608.json`, `all57_manual_operator_observations_20260608.md`, `probe_sandbox/all57/Samples/TypeScript/Demo/public/all57_model_carousel.html`, `scripts/build_live2d_all57_render_manifest.py`, `scripts/build_live2d_all57_model_carousel_player.py`, `scripts/run_live2d_all57_model_carousel_player.py`, `run-live2d-all57-model-player.command`, `live2d-all57-model-carousel-player.png` | all57 전체를 좌우 화살표로 넘기는 로컬 Web Player를 추가했다. Manifest는 57개 전체를 유지하고, 실제 runtime-capable 50개와 CMO3-only 7개를 구분한다. 주인님 manual observation도 저장했다: 1/2/4/22/23은 눈만 움직임, 3은 작동 잘함, 6은 움직임, 8/9는 안 움직임, 5/11/14는 렌더링x, 24는 눈 움직임, 25는 기록 끊김. 기존 carousel은 모델 전환 후 motion을 clear해서 neutral/blink 상태로 세웠으므로 eye-only는 고장 확정이 아니다. `모션 재생` 버튼을 추가했고 Browser smoke에서 `chitose_t01`의 `모션 재생: Idle`이 확인됐다. |
| Live2D all57 motion playback QA matrix | VERIFIED_ALL57_MOTION_QA | `experiments/live2d-strong-model-pattern-001/reports/all57_motion_playback_qa_matrix.json`, `all57_motion_playback_qa_matrix.md`, `all57_motion_playback_qa_raw.json`, `all57_motion_qa/*/*.png`, `scripts/run_live2d_all57_motion_playback_qa.py` | all57 Web Player sandbox에서 57개 전체를 순차 QA했다. 50개 runtime-capable 모델은 neutral/motion_20/motion_50/motion_80 캡처를 저장했고, 7개 CMO3-only 모델은 `NO_RUNTIME`으로 보존했다. 결과: 57 rows, 200 PNG captures, `MOTION_STRONG` 43, `MOTION_VISIBLE` 2, `NO_MOTION_GROUP` 5, `NO_RUNTIME` 7. 주인님 manual observation은 자동 matrix에 병합되어 eye-only/no-render/works-well 같은 사람 관찰과 픽셀 변화량 판정이 나란히 남는다. |
| Live2D all34 CMO3 deformer hierarchy detail | VERIFIED_GUID_LINKED_HIERARCHY | `experiments/reference-model-structure-001/reports/all34_cmo3_deformer_hierarchy_table.json`, `all34_cmo3_deformer_hierarchy_table.md`, `scripts/inspect_cmo3_structure.mjs`, `scripts/build_live2d_cmo3_deformer_hierarchy_table.py`, per-model `official_combined_analysis/models/*/cmo3_structure_report.json` | 기존 CMO3 inspector가 deformer source row id와 Cubism 내부 `CDeformerGuid`를 혼동해 hierarchy depth/child count가 0으로 나오는 결함을 수정했다. inspector는 이제 `CDeformerGuid xs.n="guid"` 참조를 기록하고, hierarchy builder는 이 GUID로 parent deformer와 child ArtMesh를 연결한다. 34/34 `FULL_STRUCTURE` 모델 재파싱 후 결과는 3,020 deformer rows, 1,978 warp, 1,042 rotation, max depth 19, median depth 7.0, child ArtMesh가 붙은 deformer 1,774개, child deformer가 붙은 deformer 1,785개다. |
| Ubuntu CUDA See-through runbook | READY_TO_RUN | `docs/ref/UBUNTU-CUDA-SEETHROUGH-RUNBOOK.md` | Ubuntu CUDA에서 `*_layers.json` 생성 후 Mac review/PSD gate로 회수하는 절차 문서화 |
| Mini Cubism OSS candidates | RESEARCHED | `docs/ref/MINI-CUBISM-OSS-RESEARCH.md`, `docs/status/NEXT-AGENT-HANDOFF.md`, shared harness `vtube-open-source-rigging-research.md` | Inochi2D/Inochi Creator는 성숙한 OSS puppet editor/runtime 참고, Stretchy Studio는 구조 참고로만 제한, Imervue/SkelForm/AnimeEffects/DragonBones는 보조 참고. |
| Mini Cubism v0 core+preview | PASS_LOCAL_PREVIEW | `experiments/mini-cubism-v0-001/mini_cubism_project/character.json`, `reports/build_report.json`, `reports/validation_report.json`, `reports/preview_evidence/preview_smoke_report.json`, `mini_cubism_app/`, shared harness `vtube-mini-cubism-v0.md` | 19개 Imagen Live2D accepted PSD 후보 파츠에서 Vtube-native `parts/meshes/deformers/parameters/keyform_bindings/glue: []` 포맷을 생성했다. Validator PASS, desktop/mobile browser smoke PASS, slider 변경 후 canvas hash 변화 확인. 이는 CMO3/MOC3 export나 최종 Cubism rig 품질이 아니라 local preview proof다. |
| Mini Cubism auto authoring v0.1 | PASS_LOCAL_PREVIEW | `experiments/mini-cubism-auto-authoring-001/baseline/reports/pose_sweep_report.json`, `reports/candidate_score_report.json`, `review_packet/contact_sheet.png`, `review_packet/review_summary.md`, shared harness `vtube-mini-cubism-auto-authoring.md` | 자동 pose sweep이 desktop/mobile에서 neutral, angle, eye close, mouth open, hair swing screenshot을 생성했고, pixel scoring으로 conservative keyform 후보 9개를 랭킹했다. `candidate_009`가 best로 선택됐고 contact sheet가 생성됐다. 이는 local Mini Cubism preview/keyform tuning evidence이며 Glue/CMO3/MOC3 호환 evidence는 아니다. |
| Mini Cubism Physics v0.3 | PASS_LOCAL_PHYSICS_PREVIEW | `experiments/mini-cubism-physics-v0-3-001/best/mini_cubism_project/character.json`, `motion_evidence/reports/motion_sweep_report.json`, `motion_evidence/reports/physics_score_report.json`, `motion_evidence/gifs/*.gif`, `review_packet/contact_sheet.png`, `review_packet/best_motion.gif`, `review_packet/review_summary.md`, shared harness `vtube-mini-cubism-physics-v0-3.md` | `candidate_009` 기반으로 새 best project를 생성했다. 21 parts/meshes, 9 deformers, 5 parameters, 10 keyform bindings, part opacity keyframes 5개(mouth 3 + iris hide 2), vertex weight sets 5개, spring-damper physics profiles 3개가 있다. `angle_swing`, `hair_settle`, `mouth_talk`, `eye_blink` GIF/frame evidence가 생성됐고 `physics_score_report.json`이 PASS다. 이 evidence는 local preview physics proof이며 Cubism CMO3/MOC3 또는 Glue 구현 증거가 아니다. |
| Mini Cubism dedicated model v1 targeted split | PASS_TARGETED_SPLIT_LOCAL_RIG | `experiments/mini-cubism-dedicated-model-v1-001/canonical/canonical_front_2048.png`, `reports/mps_512_safe_inference_report.json`, `layer_manifest.json`, `targeted_split_v1/targeted_layer_manifest.json`, `reports/targeted_split_validation_report.json`, `reports/targeted_split_contact_sheet.png`, `reports/targeted_split_review_summary.md`, `mini_cubism_project_targeted/character.json`, `mini_cubism_project_targeted/reports/validation_report.json` | Mini Cubism 전용 canonical을 Mac MPS See-through로 먼저 29 normalized layers / 19 production candidates까지 분해한 뒤, targeted splitter v1이 hair/eye/mouth/body/accessory 후보를 73개 full-canvas layer로 확장했다. Targeted split validator는 73 parts, 18 hair, 16 eye, 8 mouth, 33 physics targets로 PASS했다. `mini_cubism_project_targeted`도 73 parts/meshes, 10 deformers, 10 parameters, 18 keyform bindings로 Mini Cubism validator PASS다. 생성/파생 mouth·eye keypose는 candidate evidence이며, visual art quality review와 motion evidence는 다음 단계다. |
| Stretchy Studio 참고 가치 | RESEARCHED | GitHub/사이트 조사만 있음 | benchmark 후보로만 유지 |
| PachiPakuGen eye/mouth 자동화 가치 | RESEARCHED | GitHub 조사만 있음 | 아이디어만 반영, 도입은 보류 |
| Mini Cubism browser previewer 구현성 | PASS_LOCAL_PREVIEW | `mini_cubism_app/`, `experiments/mini-cubism-v0-001/mini_cubism_project/reports/preview_evidence/preview_smoke_report.json` | Vanilla canvas preview에서 part render, mesh/deformer overlay, parameter sliders가 동작한다. WebGL/PixiJS는 아직 필요하지 않음 |
| MediaPipe tracking smoke | T0_PASS / T1_WEBCAM_PASS / T2_REFERENCE_MODEL_DRIVE_PASS / NEW_V2_DRIVE_PENDING | `face_tracking_synthetic_parameter_smoke.md` verifies static synthetic conversion; `face_tracking_webcam_probe_report.md` verifies built-in webcam capture and Cubism parameter conversion; `webcam_parameter_drive_report.md` verifies reference Live2D Web model drive | 다음 검증은 같은 stream을 새 v2 rig preview 또는 Cubism-authored export에 연결하는 production-specific G3 motion smoke다. |
| Live2D PSD import 호환성 | VERIFIED_CURRENT_PACK | `experiments/cubism-v2-new-character-001/material_pack_v0/reports/cubism_import_smoke.json`, 이전 `experiments/cubism-material-pack-001/reports/cubism_import_smoke.json` | psd-tools writer 기반 PSD가 Cubism Editor 5.3에서 실제 PSD document로 로드되고 개별 레이어가 보이는 것을 현재 v2 pack에서도 재확인했다. 일반 호환성 보장은 아니며, 각 새 pack마다 import smoke를 반복한다. |

## Legacy/Reference 검증 백로그

아래 Gate 목록은 2026-06-02 기준의 초기 검증 백로그다. 현재 production SSOT는 Live2D/Cubism 방향으로 조정되었으므로, 이 목록을 그대로 최신 플랜으로 사용하지 않는다.

현재 우선순위는:

```text
PSD-LAYER-SCHEMA-001
LIVE2D-PARAM-MAP-001
CUBISM-IMPORT-CHECKLIST-001
RIG-REFERENCE-PACK-001
```

## 완성도 높은 플랜을 위한 필수 검증

아래 검증을 통과하면 "가능해 보임"이 아니라 "실행 가능한 플랜"으로 바꿀 수 있다. 완벽한 플랜은 예측으로 나오지 않고, 실패 조건까지 기록된 evidence matrix에서 나온다.

### Gate 0: 자산 Baseline

목표:
현재 자산이 어떤 테스트의 입력인지 고정한다.

검증:
- 모든 PNG의 경로, 크기, 해시 기록
- 중복 raw/generated 파일 구분
- canonical source 하나 지정

통과 기준:
```text
asset_inventory.json 또는 markdown 표가 존재한다.
canonical_front 후보가 하나 지정된다.
같은 입력으로 다음 테스트를 재실행할 수 있다.
```

### Gate 1: imagegen 후보의 후처리 가능성

목표:
imagegen 결과가 "보기 좋은 그림"이 아니라 실제 파츠 후보로 쓸 수 있는지 검증한다.

검증:
- `individual_mouth_parts.png`에서 mouth 후보 자동 crop
- `individual_eye_parts.png`에서 eye 후보 자동 crop
- 흰 배경 제거 또는 alpha mask 생성
- canonical 얼굴 위에 mouth/eye를 합성
- 합성 screenshot 저장

통과 기준:
```text
최소 mouth 3개, eye 2개를 crop한다.
각 crop의 alpha 영역이 비어 있지 않다.
canonical 위 합성 screenshot에서 위치/스케일 조정이 가능하다.
수동 보정이 필요한 항목이 qa_report.md에 기록된다.
```

실패 시 플랜 조정:
```text
imagegen parts는 production 후보가 아니라 reference-only로 낮춘다.
mouth/eye는 See-through 또는 수동 제작 우선으로 전환한다.
```

### Gate 2: See-through/ComfyUI-See-through 실행성

목표:
웹검색 기반 주장을 주인님 환경의 실행 evidence로 바꾼다.

검증:
- See-through 또는 ComfyUI-See-through 설치 가능 여부 확인
- Mac에서 실행 가능한 경로 확인
- 현재 `canonical_front.png` 입력으로 PSD 또는 PNG layer 출력
- 출력 시간을 기록
- GPU/CPU/메모리/실패 로그 기록

통과 기준:
```text
external/see_through/ 아래 출력물이 존재한다.
실행 명령, 소요 시간, 실패 복구 방법이 기록된다.
출력 layer 개수와 각 layer alpha coverage가 기록된다.
```

실패 시 플랜 조정:
```text
See-through는 local baseline이 아니라 optional external tool로 낮춘다.
1차 MVP는 imagegen/manual crop + 자체 normalizer로 축소한다.
```

Mac Apple Silicon 재검증은 `see-through-layer-decomp-001` 1280 production 시도가 아니라
`see-through-mps-compat-002`의 512/640/768 compatibility smoke로 수행한다. 이 경로의
최소 통과 기준은 `*_layers.json` 생성이며, production 승격은 review app과 Cubism gate를 통과해야 한다.
현재 512 smoke는 `scripts/patch_comfyui_seethrough_mps.py` 적용 후 `PASS_MPS_512_LAYERS`가 되었다.
다음 검증은 `Mac MPS 후보` 29개를 review app에서 사람이 보고 hair/face/eye/mouth 계열 5개 이상이
`O` 또는 `REVISE`인지 확인하는 것이다.

### Gate 3: See-through layer 품질 평가

목표:
See-through 출력이 실제 VTuber layer baseline으로 충분한지 검증한다.

검증:
- layer별 alpha coverage 측정
- 빈 레이어, 너무 작은 레이어, 전체 이미지에 가까운 레이어 탐지
- face/hair/eye/mouth/torso 계열로 매핑 가능 여부 판정
- draw order가 시각적으로 말이 되는지 screenshot 비교
- underpaint가 실제로 존재하는지 확인

통과 기준:
```text
필수 계열(face, hair, eye, mouth, torso) 중 4개 이상이 매핑 가능하다.
빈/노이즈 layer 비율이 허용 범위 안이다.
layer_quality_report.json이 생성된다.
채택/수정/폐기 layer 목록이 있다.
```

실패 시 플랜 조정:
```text
See-through는 underpaint/reference extraction 용도로만 사용한다.
PSD baseline 자동화 목표를 낮춘다.
```

### Gate 4: Layer Normalizer 가능성

목표:
See-through/imagegen/manual 후보를 같은 내부 규격으로 합칠 수 있는지 검증한다.

검증:
- `layer_manifest_draft.json`을 내부 `psd/layer_manifest.json`으로 변환
- layer name, source, bbox, alpha coverage, draw order 기록
- 누락 필수 파츠 목록 자동 산출
- PSD import checklist 생성

통과 기준:
```text
avatar2d layers normalize 또는 동등한 스크립트가 샘플 입력에서 동작한다.
필수 파츠 누락 목록이 자동으로 나온다.
layer_manifest.json이 모든 parts/*.png를 참조한다.
```

실패 시 플랜 조정:
```text
CLI 개발 전에 manifest schema를 더 작게 줄인다.
draw order와 anchor는 수동 JSON으로 시작한다.
```

### Gate 5: 경량 Previewer Spike

목표:
Live2D/Cubism 없이도 파츠 움직임을 검수할 수 있는지 확인한다.

검증:
- 최소 HTML/Canvas 또는 PixiJS previewer 생성
- face, hair, eye, mouth, torso 5계열 렌더링
- 슬라이더로 mouth_open, eye_open, head_x 이동
- screenshot 저장

통과 기준:
```text
로컬 브라우저에서 previewer가 열린다.
슬라이더 조작 전/후 screenshot이 저장된다.
layer draw order 문제가 qa_report에 기록된다.
```

실패 시 플랜 조정:
```text
PixiJS 대신 Canvas 2D로 더 작은 previewer를 먼저 만든다.
tracking smoke는 연기한다.
```

### Gate 6: MediaPipe Tracking Smoke

목표:
트래킹 완성도가 아니라 parameter 연결 가능성만 확인한다.

검증:
- sample JSON 또는 webcam으로 face blendshape/landmark 입력
- mouth_open, eye_l_open, eye_r_open, head_x에 매핑
- clamp와 smoothing 적용 전/후 비교

통과 기준:
```text
tracking input이 rig2d parameter로 변환된다.
튀는 값이 clamp된다.
대표 screenshot 또는 parameter log가 reports에 저장된다.
```

실패 시 플랜 조정:
```text
MVP에서는 tracking을 optional로 낮추고 previewer/manual QA를 우선한다.
```

### Gate 7: Harness 재실행성

목표:
Codex와 Claude가 같은 절차로 실험을 반복할 수 있게 만든다.

검증:
- 실험 카드 작성
- 명령어, 입력, 출력, 기대 결과 기록
- keep/discard 조건 기록
- 공용 하네스 후보를 `/Users/family/jason/jason-agent-harness-template`에 저장할 가치 평가

통과 기준:
```text
한 테스트를 새 세션에서 다시 실행할 수 있다.
결과가 reports에 남는다.
성공/실패 판단이 사람 감상에만 의존하지 않는다.
```

## 우선순위 테스트 순서

### Phase A: 지금 자산만으로 가능한 검증

```text
A1. asset_inventory 생성
A2. imagegen mouth crop/mask smoke
A3. imagegen eye crop/mask smoke
A4. canonical 위 mouth/eye 합성 screenshot
A5. crop/mask 결과 qa_report 작성
```

목표:
외부 OSS 설치 전에 현재 imagegen 자산의 실제 재사용성을 확정한다.

### Phase B: See-through baseline 검증

```text
B1. See-through/ComfyUI-See-through 실행 경로 선택
B2. canonical_front 입력으로 layer bundle 생성
B3. layer alpha/draw-order 품질 측정
B4. 내부 layer_manifest_draft 작성
B5. imagegen 후보와 See-through 출력 중 어느 쪽이 낫는지 비교
```

목표:
See-through를 MVP 핵심 baseline으로 둘지, optional reference tool로 낮출지 결정한다.

### Phase C: 자체 툴 개발 전 검증

```text
C1. layer_manifest schema 최소화
C2. layer normalizer spike
C3. previewer spike
C4. QA report 자동 생성
C5. harness export draft
```

목표:
코드 개발을 시작하기 전에 만들 도구의 입력/출력/판정 기준을 고정한다.

## 테스트 진행 기록 템플릿

새 실험은 아래 형식으로 계속 추가한다.

```yaml
id:
date:
owner:
status: UNVERIFIED
hypothesis:
input:
command:
output:
metric:
pass_condition:
fail_condition:
result:
evidence_files:
decision: keep | revise | discard
next_action:
```

## 진행 로그

| ID | 날짜 | 상태 | 가설 | 결과 | Evidence 파일 | 다음 액션 |
|---|---|---:|---|---|---|---|
| IMG-001 | 2026-06-02 | OBSERVED | imagegen으로 canonical/parts/underpaint 후보 생성 가능 | 후보 생성은 가능하나 final PSD는 불가 | `experiments/imagegen-limit-test-001/results.md` | crop/mask smoke |
| IMG-002 | 2026-06-02 | OBSERVED | no-label + 파츠군별 생성이 더 실용적 | mouth/eye/underpaint 후보가 더 좋음 | `experiments/imagegen-limit-test-002/results.md` | mouth/eye 합성 smoke |
| IMG-003 | 2026-06-02 | VERIFIED | imagegen mouth/eye PNG에서 실제 crop/mask 후보 생성 가능 | mouth 14개, eye 18개 crop/mask 생성 PASS | `experiments/validation-smoke-001/reports/crop_mask_composite_report.json` | semantic 분류 |
| IMG-004 | 2026-06-02 | OBSERVED | canonical 위에 mouth/eye 후보를 합성할 수 있다 | 합성 PNG 5개 생성. mouth는 유망, eye는 바로 production 불가 | `experiments/validation-smoke-001/composites/` | 위치/분류 보정 |
| ALIGN-001 | 2026-06-02 | VERIFIED | 스크립트가 좌표와 alpha bbox로 mouth/iris 후보를 자동 정렬할 수 있다 | anchor/mouth/iris 정렬 PASS. mouth error <= 0.5px, iris error <= 0.6px | `experiments/coordinate-align-001/reports/coordinate_alignment_report.json` | full eye grouping |
| EYE-001 | 2026-06-02 | DISCARDED | eye_white/iris/lash 후보를 semantic group으로 조립하면 full eye replacement가 되는가 | technical grouping은 됐지만 human review에서 위치/미술 품질 FAIL | `experiments/eye-grouping-001/reports/eye_grouping_report.json` | canonical eye geometry/mask 기반 재설계 |
| FCANVAS-001 | 2026-06-02 | OBSERVED | mouth crop을 canonical과 같은 full-canvas layer로 만들면 runtime placement가 필요 없어지는가 | full-canvas/no-runtime-place PASS, visual quality REVISE | `experiments/full-canvas-layer-001/reports/full_canvas_layer_report.json` | previewer smoke |
| CANON-EYE-001 | 2026-06-02 | VERIFIED | canonical 원본 눈에서 geometry/mask를 추출할 수 있는가 | iris delta/ROI/mask PASS | `experiments/canonical-eye-001/reports/canonical_eye_geometry_report.json` | canonical 기반 blink 재설계 |
| BLINK-001 | 2026-06-02 | DISCARDED | sheet closed-lid 후보만 canonical eye ROI 안에 얹으면 blink layer가 되는가 | ROI 안에는 들어오지만 visual alignment FAIL | `experiments/blink-001/reports/blink_report.json` | edit/inpaint 또는 수동 split |
| MOUTH-STYLE-001 | 2026-06-02 | OBSERVED | mouth 후보를 expression/style 기준으로 shortlist/reject할 수 있는가 | expression/shortlist/reject PASS, visual quality REVISE | `experiments/mouth-style-001/reports/mouth_candidate_score_report.json` | human review shortlist |
| CREATURE-SCHEMA-001 | 2026-06-02 | VERIFIED | 비인간 캐릭터 anchor schema를 human과 분리할 수 있는가 | human/dog/cat required anchors와 missing-anchor rule 정의 | `experiments/creature-schema-001/reports/anchor_schema_report.json` | 비인간 fixture 생성 전 대기 |
| DOC-SSOT-CLEANUP-001 | 2026-06-03 | VERIFIED | 문서가 많아져도 최신 생산 방향을 한 곳에서 복원할 수 있는가 | 루트 플랜을 얇은 SSOT 진입점으로 교체하고, 옛 6주 MVP 플랜을 archive로 이동 | `experiments/doc-ssot-cleanup-001/reports/doc_ssot_cleanup_report.json` | PSD/LIVE2D 문서 생성 |
| EXT-001 | 2026-06-02 | BLOCKED | See-through가 canonical을 유용한 PSD layer로 분해한다 | repo는 확보했지만 로컬 Mac 직접 처리 미통과 | `experiments/validation-smoke-001/reports/see_through_environment_report.md` | remote GPU 또는 ComfyUI 별도 Gate |
| LYR-001 | TBD | UNVERIFIED | layer normalizer로 후보들을 내부 manifest로 통합 가능 | 미실행 | TBD | schema spike |
| PRV-001 | TBD | UNVERIFIED | 경량 previewer로 파츠 움직임 검수 가능 | 미실행 | TBD | Canvas/Pixi spike |

## 플랜 확정 기준

아래 조건을 만족하면 `2d-vtuber-ai-tool-plan.md`의 6주 MVP를 evidence-backed plan으로 승격한다.

```text
1. imagegen 후보가 최소 mouth/eye 합성 smoke를 통과한다.
2. See-through 또는 대체 baseline의 실행 가능/불가능이 evidence로 기록된다.
3. layer_quality_report.json 또는 동등한 수동 리포트가 존재한다.
4. layer_manifest.json 초안이 실제 파일을 참조한다.
5. previewer spike가 최소 3개 parameter를 움직인다.
6. 실패한 항목이 플랜에서 낮은 우선순위 또는 보류로 이동한다.
7. 한 개 이상의 실험이 공용 하네스 후보로 재실행 가능하다.
```

## 지금 당장 가장 중요한 검증 3개

```text
1. full-canvas mouth layer를 previewer에 연결해 runtime placement 제거 검증
2. blink는 sheet 후보를 폐기하고 canonical edit/inpaint 또는 수동 split 경로 설계
3. See-through/ComfyUI-See-through를 remote GPU, HuggingFace Space, ModelScope, 또는 별도 ComfyUI 환경 중 어디서 검증할지 선택
```

좌표 기반 정렬 smoke 결과 기준으로 imagegen mouth/iris 보강 전략은 완전 폐기할 필요가 없다. 위치 조정은 스크린샷 기반 AI 판단이 아니라 anchor/bbox/alpha center/placement_error 기반으로 진행해야 한다. 다만 full eye replacement는 `eye-grouping-001`에서 실패했으므로 sheet-part semantic grouping 경로를 버리고 canonical eye geometry/mask 기반으로 다시 설계해야 한다. See-through 중심 플랜은 현재 로컬 Mac evidence 기준 optional 또는 remote-GPU validation 대상으로 낮춰야 한다.

## CMO3-STRUCTURE-001

```yaml
id: CMO3-STRUCTURE-001
date: 2026-06-04
owner: Codex
status: WARN
hypothesis: Cubism GUI screenshot 대신 .cmo3 내부 구조를 CLI로 검사하면 ArtMesh, parameter, deformer, keyform 존재 여부를 더 정확히 분리할 수 있다.
input: experiments/imagen-live2d-001/cubism_mvp_rig.cmo3
command: node scripts/inspect_cmo3_structure.mjs --experiment-id imagen-live2d-001
output:
  - experiments/imagen-live2d-001/reports/cmo3_structure_report.json
  - experiments/imagen-live2d-001/reports/cmo3_structure_report.md
metric:
  - CArtMeshSource definitions
  - CParameterSource definitions
  - CWarpDeformerSource definitions
  - CRotationDeformerSource definitions
  - KeyformBindingSource definitions
result: 19 CArtMeshSource and 27 CParameterSource entries found; 0 CWarpDeformerSource, 0 CRotationDeformerSource, and 0 KeyformBindingSource entries found.
decision: keep
next_action: Use the report after every Cubism save; do not claim professional rigging until deformer/keyform bindings exist and runtime/visual motion validation passes.
```

## CMO3-GUI-DEFORMER-ATTEMPT-001

```yaml
id: CMO3-GUI-DEFORMER-ATTEMPT-001
date: 2026-06-04
owner: Codex
status: FAIL_GUI_AUTOMATION
hypothesis: macOS Accessibility/cliclick can directly create a Warp Deformer in Cubism Editor and save a CMO3 delta.
input: experiments/imagen-live2d-001/cubism_mvp_rig.cmo3
result: Reached 모델링 > 디포머 > 워프 디포머 생성... and opened the dialog, but Cubism displayed "텍스쳐 아틀라스가 생성된 후에 호출해주세요." and no saved CMO3 structure delta was detected.
evidence_files:
  - experiments/imagen-live2d-001/reports/cubism_gui_deformer_direct_attempt.md
  - experiments/imagen-live2d-001/reports/cmo3_structure_deformer_test_delta.json
decision: Do not rely on screenshot/coordinate-only GUI automation for rig authoring.
next_action: Use manual Cubism authoring plus CMO3 structure inspection, and keep programmatic fixtures for regression tests.
```

## CMO3-POSITIVE-FIXTURE-001

```yaml
id: CMO3-POSITIVE-FIXTURE-001
date: 2026-06-04
owner: Codex
status: FACE_QA_TECH_PASS_VISUAL_FAIL
hypothesis: A generated CMO3 with real deformer/keyform structures should be detected by scripts/inspect_cmo3_structure.mjs.
input: scripts/build_cmo3_structure_positive_fixture.mjs
output:
  - experiments/cmo3-structure-fixture-001/rigged_positive_fixture.cmo3
  - experiments/cmo3-structure-fixture-001/reports/cmo3_structure_report.json
result: Inspector reported PASS with 7 ArtMeshes, 23 parameters, 13 Warp Deformers, 1 Rotation Deformer, and 23 KeyformBindings.
decision: keep
next_action: Use this as a regression fixture for CMO3 inspector changes.
```

## MINI-CUBISM-SKILL-CAPTURE-001

```yaml
id: MINI-CUBISM-SKILL-CAPTURE-001
date: 2026-06-05
owner: Codex
status: PASS
hypothesis: Mini Cubism dedicated targeted splitter workflow is reusable enough to capture as Codex and Claude-side skills plus shared harness guidance.
input:
  - experiments/mini-cubism-dedicated-model-v1-001/targeted_split_v1/targeted_layer_manifest.json
  - experiments/mini-cubism-dedicated-model-v1-001/mini_cubism_project_targeted/reports/validation_report.json
command:
  - python3 /Users/family/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/family/.codex/skills/vtube-mini-cubism-targeted-splitter-workflow
  - python3 /Users/family/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/family/.codex/skills/vtube-mini-cubism-physics-workflow
  - bash /Users/family/jason/jason-agent-harness-template/scripts/check-skills.sh
  - bash /Users/family/jason/jason-agent-harness-template/scripts/check-harness.sh
output:
  - /Users/family/.codex/skills/vtube-mini-cubism-targeted-splitter-workflow/SKILL.md
  - /Users/family/.codex/skills/vtube-mini-cubism-physics-workflow/SKILL.md
  - /Users/family/jason/jason-agent-harness-template/.claude/skills/vtube-mini-cubism-targeted-splitter/SKILL.md
  - /Users/family/jason/jason-agent-harness-template/.agents/skills/vtube-mini-cubism-targeted-splitter/SKILL.md
result: Codex skill validation PASS, shared Claude skill check PASS, and shared harness check PASS.
decision: keep
next_action: Use targeted splitter skill for layer expansion/review packet work, then switch to Mini Cubism physics workflow for targeted motion evidence.
```

## MINI-CUBISM-DEDICATED-MOTION-001

```yaml
id: MINI-CUBISM-DEDICATED-MOTION-001
date: 2026-06-05
owner: Codex
status: PASS
hypothesis: The 73-part Mini Cubism dedicated targeted project can generate visual QA, motion GIF evidence, automatic physics scoring, and a one-page review packet so 주인님 only reviews contact sheet/GIF output.
input:
  - experiments/mini-cubism-dedicated-model-v1-001/mini_cubism_project_targeted/character.json
command:
  - python3 scripts/validate_mini_cubism_project.py --project experiments/mini-cubism-dedicated-model-v1-001/mini_cubism_project_targeted
  - python3 scripts/run_mini_cubism_motion_sweep.py --project /Users/family/jason/Vtube/experiments/mini-cubism-dedicated-model-v1-001/mini_cubism_project_targeted --out /Users/family/jason/Vtube/experiments/mini-cubism-dedicated-model-v1-001/targeted_motion_evidence
  - python3 scripts/score_mini_cubism_physics.py --run /Users/family/jason/Vtube/experiments/mini-cubism-dedicated-model-v1-001/targeted_motion_evidence
  - python3 scripts/build_mini_cubism_motion_review_packet.py --run /Users/family/jason/Vtube/experiments/mini-cubism-dedicated-model-v1-001/targeted_motion_evidence --out /Users/family/jason/Vtube/experiments/mini-cubism-dedicated-model-v1-001/review_packet
output:
  - experiments/mini-cubism-dedicated-model-v1-001/targeted_motion_evidence/reports/motion_sweep_report.json
  - experiments/mini-cubism-dedicated-model-v1-001/targeted_motion_evidence/reports/physics_score_report.json
  - experiments/mini-cubism-dedicated-model-v1-001/targeted_motion_evidence/gifs/angle_swing.gif
  - experiments/mini-cubism-dedicated-model-v1-001/targeted_motion_evidence/gifs/hair_settle.gif
  - experiments/mini-cubism-dedicated-model-v1-001/targeted_motion_evidence/gifs/mouth_talk.gif
  - experiments/mini-cubism-dedicated-model-v1-001/targeted_motion_evidence/gifs/eye_blink.gif
  - experiments/mini-cubism-dedicated-model-v1-001/review_packet/contact_sheet.png
  - experiments/mini-cubism-dedicated-model-v1-001/review_packet/best_motion.gif
  - experiments/mini-cubism-dedicated-model-v1-001/review_packet/review_summary.md
metric:
  - 73 parts / 73 meshes / 10 deformers / 10 parameters / 18 keyform bindings
  - 9 active physics profiles
  - 26 physics target slots, minimum 12
  - contact sheet 900x1312
  - best motion GIF 520x520
result: Validator PASS, motion sweep CAPTURED_PENDING_SCORE, physics score PASS, review packet PASS.
decision: keep
next_action: 주인님 checks only `review_packet/contact_sheet.png` and `review_packet/best_motion.gif`; next automatic loop can tune stronger/weaker/softer motion based on that one visual decision.
```

## MINI-CUBISM-FACE-V1-001

```yaml
id: MINI-CUBISM-FACE-V1-001
date: 2026-06-05
owner: Codex
status: PASS
hypothesis: The targeted physics baseline can be preserved while a face-only Mini Cubism candidate adds explicit eye-ball, brow, cheek, mouth-form, nose, and mouth-corner controls with close-up visual QA.
input:
  - experiments/mini-cubism-dedicated-model-v1-001/mini_cubism_project_targeted/character.json
command:
  - python3 scripts/build_mini_cubism_face_v1.py --experiment experiments/mini-cubism-dedicated-model-v1-001
  - python3 scripts/validate_mini_cubism_project.py --project experiments/mini-cubism-dedicated-model-v1-001/mini_cubism_project_face_v1
  - python3 scripts/run_mini_cubism_face_qa.py --project /Users/family/jason/Vtube/experiments/mini-cubism-dedicated-model-v1-001/mini_cubism_project_face_v1 --out /Users/family/jason/Vtube/experiments/mini-cubism-dedicated-model-v1-001/face_qa_v1
output:
  - experiments/mini-cubism-dedicated-model-v1-001/face_split_v1/face_split_manifest.json
  - experiments/mini-cubism-dedicated-model-v1-001/reports/face_split_v1_contact_sheet.png
  - experiments/mini-cubism-dedicated-model-v1-001/mini_cubism_project_face_v1/reports/validation_report.json
  - experiments/mini-cubism-dedicated-model-v1-001/face_qa_v1/reports/face_qa_report.json
  - experiments/mini-cubism-dedicated-model-v1-001/face_qa_v1/face_contact_sheet.png
  - experiments/mini-cubism-dedicated-model-v1-001/face_qa_v1/face_motion.gif
metric:
  - 79 parts / 79 meshes / 10 deformers / 15 parameters / 78 keyform bindings
  - required face parameters present: ParamEyeBallX, ParamEyeBallY, ParamBrowLY, ParamBrowRY, ParamMouthForm, ParamCheek
  - required face parts present: nose_bridge, nose_tip, mouth_corner_L, mouth_corner_R, eye_shadow_L, eye_shadow_R
  - 12 distinct close-up pose hashes
result: Face v1 project validator PASS and face QA technical checks PASS, but 주인님 visual review FAIL because procedural face marks look like overlays and do not match the canonical art style.
decision: keep as failure fixture only; do not promote to visual success
next_action: Preserve the targeted hair/body/clothes baseline, then build Face v2 by regenerating or ROI-deriving face/eye/mouth/ear/choker parts instead of redrawing them procedurally.
```

## SEETHROUGH-70-CUSTOM-SPLIT-V2-001

```yaml
id: SEETHROUGH-70-CUSTOM-SPLIT-V2-001
date: 2026-06-05
owner: Codex
status: REVISE_VISUAL_GATE_WORKING
hypothesis: A QA-first See-through 70+ custom split validator can prevent generated/procedural face, eye, and mouth candidates from being promoted even when the structural 70+ part floor passes.
input:
  - experiments/mini-cubism-dedicated-model-v1-001/canonical/canonical_front_2048.png
  - experiments/mini-cubism-dedicated-model-v1-001/layer_manifest.json
  - experiments/mini-cubism-dedicated-model-v1-001/part_spec_manifest.json
command:
  - python3 -m py_compile scripts/validate_seethrough_70_custom_split_v2.py scripts/build_seethrough_70_custom_split_v2.py scripts/build_mini_cubism_project_from_seethrough70_v2.py
  - python3 scripts/run_mps_compat_matrix.py --experiment-id mini-cubism-dedicated-model-v1-001 --case mps_640_safe --dry-run
  - python3 scripts/validate_seethrough_70_custom_split_v2.py --experiment experiments/mini-cubism-dedicated-model-v1-001 --manifest experiments/mini-cubism-dedicated-model-v1-001/targeted_split_v1/targeted_layer_manifest.json
  - python3 scripts/validate_seethrough_70_custom_split_v2.py --experiment experiments/mini-cubism-dedicated-model-v1-001 --manifest experiments/mini-cubism-dedicated-model-v1-001/face_split_v1/face_split_manifest.json
  - python3 scripts/build_seethrough_70_custom_split_v2.py --experiment experiments/mini-cubism-dedicated-model-v1-001
  - python3 scripts/build_mini_cubism_project_from_seethrough70_v2.py --experiment experiments/mini-cubism-dedicated-model-v1-001
output:
  - scripts/validate_seethrough_70_custom_split_v2.py
  - scripts/build_seethrough_70_custom_split_v2.py
  - scripts/build_mini_cubism_project_from_seethrough70_v2.py
  - experiments/mini-cubism-dedicated-model-v1-001/seethrough_70_custom_split_v2/candidate_layer_manifest.json
  - experiments/mini-cubism-dedicated-model-v1-001/seethrough_70_custom_split_v2/reports/seethrough_70_custom_split_v2_qa_report.json
  - experiments/mini-cubism-dedicated-model-v1-001/seethrough_70_custom_split_v2/reports/problem_contact_sheet.png
  - experiments/mini-cubism-dedicated-model-v1-001/seethrough_70_custom_split_v2/reports/face_closeup_sheet.png
  - experiments/mini-cubism-dedicated-model-v1-001/seethrough_70_custom_split_v2/reports/review_summary.md
metric:
  - dedicated mps_640_safe actual run reached GenerateLayers complete and wrote `mini_cubism_dedicated_v1_mps_640_safe_20260605_132255_9931136b_layers.json`
  - normalized 640 coarse layers: 29
  - mps candidate triage from 640: 18 review priority, 1 high risk, 3 reference review, 7 empty, 11 practical gate targets
  - v2 structural counts after 640 normalize: 73 parts, 18 hair, 16 eye, 8 mouth, 33 physics targets
  - v2 QA status: REVISE_VISUAL
  - structural_status: PASS
  - visual_status: FAIL
  - action counts after 640 normalize: 50 KEEP_SEETHROUGH_MASK, 23 VISUAL_FAIL
  - dedicated mps_640_safe clean inference report: missing because ComfyUI server exited after writing layers/depth outputs
result: QA-first v2 split builds a 73-part candidate from the 640-normalized coarse layer manifest but blocks Mini Cubism project promotion because critical face/eye/mouth candidates are still generated/fallback style. Existing targeted_split_v1 also regresses to REVISE_VISUAL under the stricter QA, and Face v1 fails as the expected negative fixture.
decision: keep as gate evidence; do not promote to production or Mini Cubism v2 project until QA status is PASS
next_action: Use 640 layers as partial evidence, but retry ROI See-through or style-matched keypose asset generation for failed face/eye/mouth parts before attempting Mini Cubism v2 project promotion.
```

## MINI-CUBISM-PACK-SPLITTER-V0-PLAN-001

```yaml
id: MINI-CUBISM-PACK-SPLITTER-V0-PLAN-001
date: 2026-06-05
owner: Codex
status: PLANNED_PENDING_PROBE
hypothesis: A clean base mannequin plus pack-level decomposition strategy is a safer Mini Cubism path than forcing one completed character image into 70+ generated/fallback parts.
input:
  - docs/status/PROJECT-STATUS.md
  - experiments/mini-cubism-dedicated-model-v1-001/seethrough_70_custom_split_v2/reports/seethrough_70_custom_split_v2_qa_report.json
  - Hugging Face and web research on LayerD, BiRefNet, SAM2.1, Fashion SegFormer, and AnimeInstanceSegmentation
output:
  - docs/ref/MINI-CUBISM-PACK-SPLITTER-v0-PLAN.md
  - experiments/mini-cubism-pack-splitter-v0-001/README.md
  - experiments/mini-cubism-pack-splitter-v0-001/reports/pack_splitter_v0_plan_report.json
  - /Users/family/jason/jason-agent-harness-template/harnesses/vtube-mini-cubism-pack-splitter-v0.md
metric:
  - pack strategy fixed: base_mannequin, hair_pack, outfit_pack, accessory_pack, keypose_asset_pack
  - primary model probe order fixed: LayerD, BiRefNet variants, SAM2.1, Fashion SegFormer, AnimeInstanceSegmentation
  - promotion rule fixed: no `mini_cubism_project_pack_v0` until pack QA PASS
  - previous See-through 70+ v2 remains negative gate evidence
result: Decision-complete execution plan created for Mini Cubism pack-splitter-v0. No HF probe or mannequin generation has run yet.
decision: keep
next_action: Implement bootstrap/probe/validator scripts and generate the first model-comparison contact sheet for 주인님 review.
```

## MINI-CUBISM-PACK-SPLITTER-V0-LOCAL-PROBE-001

```yaml
id: MINI-CUBISM-PACK-SPLITTER-V0-LOCAL-PROBE-001
date: 2026-06-05
owner: Codex
status: ARCHIVED_PROCEDURAL_PLACEHOLDER_PROBE
hypothesis: The clean base mannequin plus pack-level decomposition pipeline can generate reviewable candidate masks and QA reports before any Mini Cubism project promotion or actual HF model dependency risk.
input:
  - docs/ref/MINI-CUBISM-PACK-SPLITTER-v0-PLAN.md
  - experiments/mini-cubism-pack-splitter-v0-001/README.md
command:
  - python3 -m py_compile scripts/bootstrap_mini_cubism_pack_splitter_v0.py scripts/run_mini_cubism_hf_pack_probe.py scripts/validate_mini_cubism_pack_splitter_v0.py
  - python3 scripts/bootstrap_mini_cubism_pack_splitter_v0.py --experiment experiments/mini-cubism-pack-splitter-v0-001
  - python3 scripts/run_mini_cubism_hf_pack_probe.py --experiment experiments/mini-cubism-pack-splitter-v0-001
  - python3 scripts/validate_mini_cubism_pack_splitter_v0.py --experiment experiments/mini-cubism-pack-splitter-v0-001
  - python3 -m json.tool experiments/mini-cubism-pack-splitter-v0-001/reports/hf_probe_report.json
output:
  - scripts/bootstrap_mini_cubism_pack_splitter_v0.py
  - scripts/run_mini_cubism_hf_pack_probe.py
  - scripts/validate_mini_cubism_pack_splitter_v0.py
  - experiments/mini-cubism-pack-splitter-v0-001/pack_splitter_manifest.json
  - experiments/mini-cubism-pack-splitter-v0-001/base_mannequin/canonical_base.png
  - experiments/mini-cubism-pack-splitter-v0-001/hair_pack/source_hair_pack.png
  - experiments/mini-cubism-pack-splitter-v0-001/outfit_pack/source_outfit_pack.png
  - experiments/mini-cubism-pack-splitter-v0-001/accessory_pack/source_accessory_pack.png
  - experiments/mini-cubism-pack-splitter-v0-001/keypose_asset_pack/source_keypose_guide.png
  - experiments/mini-cubism-pack-splitter-v0-001/reports/source_composite_preview.png
  - experiments/mini-cubism-pack-splitter-v0-001/reports/hf_probe_report.json
  - experiments/mini-cubism-pack-splitter-v0-001/reports/model_comparison_contact_sheet.png
  - experiments/mini-cubism-pack-splitter-v0-001/reports/pack_problem_contact_sheet.png
  - experiments/mini-cubism-pack-splitter-v0-001/reports/pack_splitter_qa_report.json
  - experiments/mini-cubism-pack-splitter-v0-001/reports/review_summary.md
metric:
  - packs: 5
  - total local-adapter candidate/reference outputs: 252
  - CANDIDATE outputs: 196
  - REFERENCE_ONLY outputs: 56
  - actual HF inference outputs: 0
  - runtime: python torch available, transformers unavailable in default python, model downloads disabled
  - QA failures: none
result: Bootstrap, local-adapter probe, JSON validation, and pack QA passed structurally, but 주인님 visual review correctly identified the source composite as procedural shape dummy art. These outputs were archived and are no longer current quality evidence.
decision: keep as archived pipeline/failure fixture only
next_action: Use the clean base mannequin connection evidence below, then generate real hair/outfit/accessory/keypose pack assets before any new HF probe.
```

## MINI-CUBISM-PACK-SPLITTER-V0-CLEAN-BASE-001

```yaml
id: MINI-CUBISM-PACK-SPLITTER-V0-CLEAN-BASE-001
date: 2026-06-05
owner: Codex
status: CLEAN_BASE_CONNECTED_PACK_ASSETS_PENDING
hypothesis: Replacing the procedural dummy source with a real clean base mannequin will give the pack splitter a visually valid base source while keeping project promotion blocked until real pack assets and model inference exist.
input:
  - /Users/family/.codex/generated_images/019e9236-5200-7303-963b-eeaed1e21242/ig_0264a8b1ba69e69c016a2256ac1acc8191bb67ef6e02a9815f.png
command:
  - python3 /Users/family/.codex/skills/.system/imagegen/scripts/remove_chroma_key.py --input experiments/mini-cubism-pack-splitter-v0-001/base_mannequin/source_originals/clean_base_mannequin_v1_chroma.png --out experiments/mini-cubism-pack-splitter-v0-001/base_mannequin/source_originals/clean_base_mannequin_v1_alpha_raw.png --auto-key border --soft-matte --transparent-threshold 12 --opaque-threshold 220 --despill
  - normalize clean base to 2048 full-canvas alpha PNG
  - archive procedural placeholder sources, local-adapter probe outputs, and old contact sheets under experiments/mini-cubism-pack-splitter-v0-001/archive/procedural_placeholder_20260605
output:
  - experiments/mini-cubism-pack-splitter-v0-001/base_mannequin/canonical_base.png
  - experiments/mini-cubism-pack-splitter-v0-001/base_mannequin/canonical_base_clean_v1.png
  - experiments/mini-cubism-pack-splitter-v0-001/base_mannequin/source_originals/clean_base_mannequin_v1_chroma.png
  - experiments/mini-cubism-pack-splitter-v0-001/base_mannequin/source_originals/clean_base_mannequin_v1_alpha_raw.png
  - experiments/mini-cubism-pack-splitter-v0-001/reports/source_composite_preview.png
  - experiments/mini-cubism-pack-splitter-v0-001/reports/clean_base_mannequin_v1_preview.png
  - experiments/mini-cubism-pack-splitter-v0-001/reports/clean_base_connection_report.json
  - experiments/mini-cubism-pack-splitter-v0-001/reports/review_summary.md
  - experiments/mini-cubism-pack-splitter-v0-001/archive/procedural_placeholder_20260605
metric:
  - clean base canvas: 2048x2048 RGBA
  - alpha bbox: [500, 69, 1047, 1940]
  - nonzero alpha pixels: 845891
  - archived local-adapter placeholder PNG outputs: 252
  - project promotion: blocked
result: The current pack splitter source preview now shows a real clean base mannequin instead of procedural shapes. Hair/outfit/accessory/keypose packs are marked pending real assets.
decision: keep
next_action: Generate real hair, outfit, accessory, and keypose pack assets, then run actual HF inference starting with LayerD / `cyberagent/layerd-birefnet`.
```

## MINI-CUBISM-PACK-SPLITTER-V0-CLEAN-BASE-TWOPIECE-002

```yaml
id: MINI-CUBISM-PACK-SPLITTER-V0-CLEAN-BASE-TWOPIECE-002
date: 2026-06-05
owner: Codex
status: CLEAN_BASE_TWOPIECE_CONNECTED_PACK_ASSETS_PENDING
hypothesis: The default Mini Cubism base should use a neutral two-piece rig underlayer so abdomen-visible outfits remain possible, instead of a one-piece bodysuit that hides the belly.
input:
  - /Users/family/.codex/generated_images/019e9236-5200-7303-963b-eeaed1e21242/ig_0264a8b1ba69e69c016a2259730e18819197ccc0a5600b161e.png
command:
  - python3 /Users/family/.codex/skills/.system/imagegen/scripts/remove_chroma_key.py --input experiments/mini-cubism-pack-splitter-v0-001/base_mannequin/source_originals/clean_base_twopiece_v3_chroma.png --out experiments/mini-cubism-pack-splitter-v0-001/base_mannequin/source_originals/clean_base_twopiece_v3_alpha_raw.png --auto-key border --soft-matte --transparent-threshold 12 --opaque-threshold 220 --despill
  - normalize clean base v3 to 2048 full-canvas alpha PNG
output:
  - experiments/mini-cubism-pack-splitter-v0-001/base_mannequin/canonical_base.png
  - experiments/mini-cubism-pack-splitter-v0-001/base_mannequin/canonical_base_twopiece_v3.png
  - experiments/mini-cubism-pack-splitter-v0-001/base_mannequin/source_originals/clean_base_twopiece_v3_chroma.png
  - experiments/mini-cubism-pack-splitter-v0-001/base_mannequin/source_originals/clean_base_twopiece_v3_alpha_raw.png
  - experiments/mini-cubism-pack-splitter-v0-001/reports/source_composite_preview.png
  - experiments/mini-cubism-pack-splitter-v0-001/reports/clean_base_twopiece_v3_preview.png
  - experiments/mini-cubism-pack-splitter-v0-001/reports/clean_base_connection_report.json
  - experiments/mini-cubism-pack-splitter-v0-001/archive/clean_base_v2_onepiece_aborted_20260605
metric:
  - clean base canvas: 2048x2048 RGBA
  - alpha bbox: [654, 44, 740, 1980]
  - nonzero alpha pixels: 524858
  - underlayer policy: chest and pelvis covered, abdomen visible skin
  - project promotion: blocked
result: The current base now uses a neutral two-piece rig underlayer. The one-piece swimsuit attempt was archived as aborted because it hid the abdomen.
decision: keep
next_action: Generate real hair, outfit, accessory, and keypose pack assets against this two-piece base, then run actual HF inference starting with LayerD / `cyberagent/layerd-birefnet`.
```

## MINI-CUBISM-PACK-SPLITTER-V0-REAL-PACK-LOCAL-PROBE-003

```yaml
id: MINI-CUBISM-PACK-SPLITTER-V0-REAL-PACK-LOCAL-PROBE-003
date: 2026-06-05
owner: Codex
status: REAL_PACK_ASSETS_LOCAL_ADAPTER_QA_PASS_PENDING_ACTUAL_HF
hypothesis: Real hair/outfit/accessory/keypose pack assets can replace procedural placeholders and pass the local pack QA loop before actual HF model inference is attempted.
input:
  - experiments/mini-cubism-pack-splitter-v0-001/base_mannequin/canonical_base.png
  - generated imagegen hair/outfit/accessory/keypose pack source images
command:
  - remove chroma key for hair/outfit/accessory/keypose pack assets
  - normalize each pack to 2048 full-canvas alpha PNG
  - python3 scripts/run_mini_cubism_hf_pack_probe.py --experiment experiments/mini-cubism-pack-splitter-v0-001
  - python3 scripts/validate_mini_cubism_pack_splitter_v0.py --experiment experiments/mini-cubism-pack-splitter-v0-001
output:
  - experiments/mini-cubism-pack-splitter-v0-001/hair_pack/source_hair_pack.png
  - experiments/mini-cubism-pack-splitter-v0-001/outfit_pack/source_outfit_pack.png
  - experiments/mini-cubism-pack-splitter-v0-001/accessory_pack/source_accessory_pack.png
  - experiments/mini-cubism-pack-splitter-v0-001/keypose_asset_pack/source_keypose_guide.png
  - experiments/mini-cubism-pack-splitter-v0-001/reports/real_pack_sources_contact_sheet.png
  - experiments/mini-cubism-pack-splitter-v0-001/reports/real_pack_connection_report.json
  - experiments/mini-cubism-pack-splitter-v0-001/reports/hf_probe_report.json
  - experiments/mini-cubism-pack-splitter-v0-001/reports/model_comparison_contact_sheet.png
  - experiments/mini-cubism-pack-splitter-v0-001/reports/pack_problem_contact_sheet.png
  - experiments/mini-cubism-pack-splitter-v0-001/reports/pack_splitter_qa_report.json
metric:
  - connected real packs: hair_pack, outfit_pack, accessory_pack, keypose_asset_pack
  - local adapter candidates: 336
  - CANDIDATE outputs: 238
  - REFERENCE_ONLY outputs: 98
  - actual HF inference outputs: 0
  - QA failures: none
  - optional empty keypose target removed: mouth_smile
result: Real pack assets replaced the procedural placeholders and passed local-adapter QA. This is a baseline/contact-sheet gate, not actual LayerD/BiRefNet/SAM2 model evidence.
decision: keep
next_action: Run actual HF inference starting with LayerD / `cyberagent/layerd-birefnet`, add BiRefNet cleanup and SAM2 ROI candidates, then rebuild QA contact sheets.
```

## MINI-CUBISM-PACK-SPLITTER-V0-LAYERD-ACTUAL-004

```yaml
id: MINI-CUBISM-PACK-SPLITTER-V0-LAYERD-ACTUAL-004
date: 2026-06-05
owner: Codex
status: LAYERD_ACTUAL_RUNTIME_PASS_REVISE_MASK_PENDING_SAM2
hypothesis: Actual LayerD BiRefNet inference can run locally on the real pack assets and produce model-derived masks for comparison against the local-adapter baseline.
input:
  - experiments/mini-cubism-pack-splitter-v0-001/hair_pack/source_hair_pack.png
  - experiments/mini-cubism-pack-splitter-v0-001/outfit_pack/source_outfit_pack.png
  - experiments/mini-cubism-pack-splitter-v0-001/accessory_pack/source_accessory_pack.png
  - experiments/mini-cubism-pack-splitter-v0-001/keypose_asset_pack/source_keypose_guide.png
command:
  - /Users/family/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m venv experiments/mini-cubism-pack-splitter-v0-001/.venv-hf-pack312
  - experiments/mini-cubism-pack-splitter-v0-001/.venv-hf-pack312/bin/python -m pip install torch torchvision transformers==4.57.3 timm safetensors einops kornia
  - experiments/mini-cubism-pack-splitter-v0-001/.venv-hf-pack312/bin/python scripts/run_layerd_birefnet_pack_inference.py --experiment experiments/mini-cubism-pack-splitter-v0-001 --packs hair_pack,outfit_pack,accessory_pack,keypose_asset_pack --device auto
output:
  - scripts/run_layerd_birefnet_pack_inference.py
  - experiments/mini-cubism-pack-splitter-v0-001/hf_actual/layerd_birefnet/hair_pack/hair_pack_layerd_birefnet.png
  - experiments/mini-cubism-pack-splitter-v0-001/hf_actual/layerd_birefnet/outfit_pack/outfit_pack_layerd_birefnet.png
  - experiments/mini-cubism-pack-splitter-v0-001/hf_actual/layerd_birefnet/accessory_pack/accessory_pack_layerd_birefnet.png
  - experiments/mini-cubism-pack-splitter-v0-001/hf_actual/layerd_birefnet/keypose_asset_pack/keypose_asset_pack_layerd_birefnet.png
  - experiments/mini-cubism-pack-splitter-v0-001/reports/layerd_birefnet_inference_report.json
  - experiments/mini-cubism-pack-splitter-v0-001/reports/layerd_birefnet_contact_sheet.png
metric:
  - actual LayerD BiRefNet inference outputs: 4
  - runtime_status: PASS
  - quality_status: REVISE_MASK
  - hair_pack: CANDIDATE
  - outfit_pack: CANDIDATE
  - accessory_pack: REVISE_MASK, BROAD_MASK_ALPHA_COVERAGE
  - keypose_asset_pack: REVISE_MASK, BROAD_MASK_ALPHA_COVERAGE, BBOX_NEAR_FULL_CANVAS
result: Actual LayerD BiRefNet inference runs locally using Python 3.12 and transformers 4.57.3. Hair/outfit masks are usable candidates; accessory/keypose need SAM2 ROI refinement before project promotion.
decision: keep
next_action: Add SAM2 ROI refinement for accessory/keypose broad masks and rebuild actual-model QA contact sheets.
```

## MINI-CUBISM-PACK-SPLITTER-V0-MODEL-COMPARISON-005

```yaml
id: MINI-CUBISM-PACK-SPLITTER-V0-MODEL-COMPARISON-005
date: 2026-06-05
owner: Codex
status: MODEL_COMPARISON_DONE_PROMOTION_BLOCKED_RELAYOUT_REQUIRED
hypothesis: The pack-splitter pipeline can choose model roles by comparing all listed candidates on the real hair/outfit/accessory/keypose pack assets before any Mini Cubism project promotion.
input:
  - experiments/mini-cubism-pack-splitter-v0-001/hair_pack/source_hair_pack.png
  - experiments/mini-cubism-pack-splitter-v0-001/outfit_pack/source_outfit_pack.png
  - experiments/mini-cubism-pack-splitter-v0-001/accessory_pack/source_accessory_pack.png
  - experiments/mini-cubism-pack-splitter-v0-001/keypose_asset_pack/source_keypose_guide.png
command:
  - experiments/mini-cubism-pack-splitter-v0-001/.venv-hf-pack312/bin/python scripts/run_layerd_birefnet_pack_inference.py --experiment experiments/mini-cubism-pack-splitter-v0-001 --packs hair_pack,outfit_pack,accessory_pack,keypose_asset_pack --model-id birefnet --device auto
  - experiments/mini-cubism-pack-splitter-v0-001/.venv-hf-pack312/bin/python scripts/run_layerd_birefnet_pack_inference.py --experiment experiments/mini-cubism-pack-splitter-v0-001 --packs hair_pack,outfit_pack,accessory_pack,keypose_asset_pack --model-id birefnet_hr --device auto
  - experiments/mini-cubism-pack-splitter-v0-001/.venv-hf-pack312/bin/python scripts/run_layerd_birefnet_pack_inference.py --experiment experiments/mini-cubism-pack-splitter-v0-001 --packs hair_pack,outfit_pack,accessory_pack,keypose_asset_pack --model-id birefnet_matting --device auto
  - experiments/mini-cubism-pack-splitter-v0-001/.venv-hf-pack312/bin/python scripts/run_sam2_roi_pack_refinement.py --experiment experiments/mini-cubism-pack-splitter-v0-001 --packs accessory_pack,keypose_asset_pack --model-id facebook/sam2.1-hiera-tiny --device auto
  - experiments/mini-cubism-pack-splitter-v0-001/.venv-hf-pack312/bin/python scripts/run_sam2_roi_pack_refinement.py --experiment experiments/mini-cubism-pack-splitter-v0-001 --packs accessory_pack,keypose_asset_pack --model-id facebook/sam2.1-hiera-large --device auto
  - experiments/mini-cubism-pack-splitter-v0-001/.venv-hf-pack312/bin/python scripts/run_misc_pack_model_probes.py --experiment experiments/mini-cubism-pack-splitter-v0-001 --model-id fashion_segformer --packs outfit_pack --device auto
  - experiments/mini-cubism-pack-splitter-v0-001/.venv-hf-pack312/bin/python scripts/run_misc_pack_model_probes.py --experiment experiments/mini-cubism-pack-splitter-v0-001 --model-id anime_instance --packs hair_pack,outfit_pack,accessory_pack,keypose_asset_pack --device auto
  - experiments/mini-cubism-pack-splitter-v0-001/.venv-hf-pack312/bin/python scripts/build_pack_model_candidate_comparison.py --experiment experiments/mini-cubism-pack-splitter-v0-001
output:
  - scripts/build_pack_model_candidate_comparison.py
  - experiments/mini-cubism-pack-splitter-v0-001/reports/birefnet_inference_report.json
  - experiments/mini-cubism-pack-splitter-v0-001/reports/birefnet_hr_inference_report.json
  - experiments/mini-cubism-pack-splitter-v0-001/reports/birefnet_matting_inference_report.json
  - experiments/mini-cubism-pack-splitter-v0-001/reports/facebook_sam2_1_hiera_tiny_roi_refinement_report.json
  - experiments/mini-cubism-pack-splitter-v0-001/reports/facebook_sam2_1_hiera_large_roi_refinement_report.json
  - experiments/mini-cubism-pack-splitter-v0-001/reports/fashion_segformer_probe_report.json
  - experiments/mini-cubism-pack-splitter-v0-001/reports/anime_instance_probe_report.json
  - experiments/mini-cubism-pack-splitter-v0-001/reports/model_candidate_comparison_report.json
  - experiments/mini-cubism-pack-splitter-v0-001/reports/model_candidate_comparison_contact_sheet.png
  - experiments/mini-cubism-pack-splitter-v0-001/reports/model_candidate_decision.md
metric:
  - compared model candidates: 8
  - BiRefNet outputs: PASS, 4 packs
  - BiRefNet_HR outputs: PASS, 4 packs
  - BiRefNet-matting outputs: RUNTIME_PASS_REVISE_MASK, keypose near full-canvas
  - SAM2 tiny outputs: RUNTIME_PASS_VISUAL_FAIL, 16 ROI records
  - SAM2 large outputs: RUNTIME_PASS_VISUAL_FAIL, 16 ROI records
  - Fashion SegFormer: BLOCKED_MODEL_PROBE, missing/default image processor path
  - AnimeInstance: BLOCKED_MODEL_PROBE, not directly loadable by Transformers config
result: Select `ZhengPeng7/BiRefNet_HR` as the primary full-pack alpha cleanup model and `ZhengPeng7/BiRefNet` as stable fallback. Keep LayerD as reference only, BiRefNet-matting as optional hair/outfit/accessory edge cleanup only, and reject current SAM2 tiny/large outputs because they crop or fragment small accessory/keypose parts.
decision: keep model roles, block project promotion
next_action: Regenerate or relayout accessory/keypose packs with larger spacing, then retry connected-component/SAM2 splitting on BiRefNet-cleaned alpha before Mini Cubism project promotion.
```

## MINI-CUBISM-HAIR-FACE-MOTION-V1-001

```yaml
id: MINI-CUBISM-HAIR-FACE-MOTION-V1-001
date: 2026-06-05
owner: Codex
status: TECH_PASS_HUMAN_VISUAL_FAIL_RATIO
hypothesis: A smaller Mini Cubism project using the current clean base, BiRefNet_HR hair alpha, local hair splitting, and separate generated eye/mouth keyposes can prove hair/face motion before outfit and accessory packs are solved.
input:
  - experiments/mini-cubism-pack-splitter-v0-001/base_mannequin/canonical_base.png
  - experiments/mini-cubism-pack-splitter-v0-001/hf_actual/birefnet_hr/hair_pack/hair_pack_birefnet_hr.png
command:
  - python3 scripts/build_mini_cubism_hair_split_v1.py --experiment experiments/mini-cubism-hair-face-motion-v1-001
  - python3 scripts/build_mini_cubism_hair_fit_v1.py --experiment experiments/mini-cubism-hair-face-motion-v1-001
  - python3 scripts/build_mini_cubism_hair_split_v1.py --experiment experiments/mini-cubism-hair-face-motion-v1-001 --source-hair experiments/mini-cubism-hair-face-motion-v1-001/hair_fit_v1/hair_fit_birefnet_hr.png
  - python3 scripts/build_mini_cubism_face_keypose_pack_v1.py --experiment experiments/mini-cubism-hair-face-motion-v1-001
  - python3 scripts/build_mini_cubism_hair_face_project_v1.py --experiment experiments/mini-cubism-hair-face-motion-v1-001
  - python3 scripts/validate_mini_cubism_project.py --project experiments/mini-cubism-hair-face-motion-v1-001/mini_cubism_project
  - python3 scripts/run_mini_cubism_motion_sweep.py --project experiments/mini-cubism-hair-face-motion-v1-001/mini_cubism_project --out experiments/mini-cubism-hair-face-motion-v1-001/motion_evidence
  - python3 scripts/score_mini_cubism_physics.py --run experiments/mini-cubism-hair-face-motion-v1-001/motion_evidence
  - python3 scripts/build_mini_cubism_motion_review_packet.py --run experiments/mini-cubism-hair-face-motion-v1-001 --out experiments/mini-cubism-hair-face-motion-v1-001/review_packet
output:
  - scripts/build_mini_cubism_hair_fit_v1.py
  - experiments/mini-cubism-hair-face-motion-v1-001/hair_fit_v1/hair_fit_birefnet_hr.png
  - experiments/mini-cubism-hair-face-motion-v1-001/hair_fit_v1/reports/hair_fit_report.json
  - experiments/mini-cubism-hair-face-motion-v1-001/hair_fit_v1/reports/hair_fit_contact_sheet.png
  - experiments/mini-cubism-hair-face-motion-v1-001/reports/human_visual_review_ratio_fail_20260605.json
  - scripts/build_mini_cubism_hair_split_v1.py
  - scripts/build_mini_cubism_face_keypose_pack_v1.py
  - scripts/build_mini_cubism_hair_face_project_v1.py
  - experiments/mini-cubism-hair-face-motion-v1-001/hair_split_v1/hair_split_manifest.json
  - experiments/mini-cubism-hair-face-motion-v1-001/face_keypose_v1/face_keypose_manifest.json
  - experiments/mini-cubism-hair-face-motion-v1-001/mini_cubism_project/character.json
  - experiments/mini-cubism-hair-face-motion-v1-001/mini_cubism_project/reports/validation_report.json
  - experiments/mini-cubism-hair-face-motion-v1-001/motion_evidence/reports/motion_sweep_report.json
  - experiments/mini-cubism-hair-face-motion-v1-001/motion_evidence/reports/physics_score_report.json
  - experiments/mini-cubism-hair-face-motion-v1-001/review_packet/contact_sheet.png
  - experiments/mini-cubism-hair-face-motion-v1-001/review_packet/best_motion.gif
  - experiments/mini-cubism-hair-face-motion-v1-001/review_packet/review_summary.md
metric:
  - hair fit scale: 0.5859
  - fitted hair bbox: [602, 18, 845, 1050]
  - hair split parts: 16
  - face keypose layers: 10, including face_cover
  - project parts/meshes: 27
  - deformers: 9
  - parameters: 7
  - keyform bindings: 14
  - part opacity keyframes: 9
  - vertex weight sets: 16
  - active hair physics profiles: 5
  - physics targets: 16
  - motion scenarios: angle_swing, head_tilt, hair_settle, mouth_talk, eye_blink
result: Technical local preview still validates and motion/physics evidence PASS, but 주인님 visual review failed the composite because the full-body base and fitted hair still have mismatched style/ratio. This proves motion mechanics only, not a usable visual baseline.
decision: keep as a failure fixture and local motion-mechanics evidence; do not promote this exact composite as the current hair+face visual baseline
next_action: Rebuild from a matched single-source character or generate clean base and hair as a matched pair, then rerun BiRefNet_HR cleanup, local hair split, separate face keyposes, Mini Cubism project build, and motion evidence.
```

## LIVE2D-OFFICIAL-WEB-RUNTIME-RENDER-SMOKE-001

```yaml
id: LIVE2D-OFFICIAL-WEB-RUNTIME-RENDER-SMOKE-001
date: 2026-06-06
owner: Codex
status: PASS
hypothesis: Official Web Samples runtime bundles that looked motion-ready by JSON inventory should also render in the real Cubism Web runtime without viewport clipping.
input:
  - experiments/reference-model-structure-001/official_github_samples/CubismSdkForWeb-5-r.5.zip
  - experiments/reference-model-structure-001/official_github_samples/repos/live2d_cubism_web_samples/Samples/TypeScript/Demo
command:
  - npm run copy_resources
  - npm run start -- --host 127.0.0.1
  - Playwright browser sequence capture through the official gear scene switcher
output:
  - experiments/live2d-owned-model-motion-preview-test-001/reports/runtime_render_smoke_report.json
  - experiments/live2d-owned-model-motion-preview-test-001/reports/runtime_render_smoke_report.md
  - experiments/live2d-owned-model-motion-preview-test-001/reports/runtime_render_sequence_contact_sheet.png
  - experiments/live2d-owned-model-motion-preview-test-001/reports/runtime_render_sequence/01_Haru.png
  - experiments/live2d-owned-model-motion-preview-test-001/reports/runtime_render_sequence/02_Hiyori.png
  - experiments/live2d-owned-model-motion-preview-test-001/reports/runtime_render_sequence/03_Mark.png
  - experiments/live2d-owned-model-motion-preview-test-001/reports/runtime_render_sequence/04_Natori.png
  - experiments/live2d-owned-model-motion-preview-test-001/reports/runtime_render_sequence/05_Rice.png
  - experiments/live2d-owned-model-motion-preview-test-001/reports/runtime_render_sequence/06_Mao.png
  - experiments/live2d-owned-model-motion-preview-test-001/reports/runtime_render_sequence/07_Wanko.png
  - experiments/live2d-owned-model-motion-preview-test-001/reports/runtime_render_sequence/08_Ren.png
metric:
  - tested runtime models: 8
  - rendered in browser: 8
  - viewport clipping PASS: 8
  - WARN: 0
  - FAIL: 0
result: Haru, Hiyori, Mark, Natori, Rice, Mao, Wanko, and Ren rendered in the official Cubism Web demo after replacing the generic 5.1 Core with the matching official SDK for Web 5-r.5 Core. Median-background screenshot bbox analysis found no viewport-edge clipping.
decision: Use this as real runtime render evidence for the official Web sample baseline; keep structure extraction, runtime visual smoke, and future Cubism Editor CMO3 authoring evidence separate.
next_action: Build a repeatable runtime smoke script if more official/runtime models are added, then connect this visual smoke to the v2 review packet only as G3 motion_visual evidence.
```

## LIVE2D-STRONG-MODEL-PATTERN-001

```yaml
id: LIVE2D-STRONG-MODEL-PATTERN-001
date: 2026-06-08
owner: Codex
status: PASS_CUBISM_V2_SPEC
hypothesis: Official sample models that are strong by inventory should be rendered in a real Cubism Web runtime, captured at neutral/motion/extreme states, then combined with CMO3 inspector structure values to define the Cubism v2 tier baseline before generating new art.
input:
  - experiments/live2d-owned-model-motion-readiness-001/reports/owned_model_motion_readiness.json
  - experiments/reference-model-structure-001/official_samples/extracted
  - experiments/reference-model-structure-001/official_github_samples/repos/live2d_cubism_web_samples
command:
  - python3 scripts/build_live2d_strong_model_render_manifest.py
  - python3 scripts/build_live2d_runtime_probe_sandbox.py --manifest experiments/live2d-strong-model-pattern-001/reports/pilot_render_manifest.json
  - npm install && npm run build in experiments/live2d-strong-model-pattern-001/probe_sandbox/pilot/Samples/TypeScript/Demo
  - python3 scripts/run_live2d_runtime_probe_capture.py --manifest experiments/live2d-strong-model-pattern-001/reports/pilot_render_manifest.json --sandbox-report experiments/live2d-strong-model-pattern-001/reports/pilot_runtime_probe_sandbox.json --port 5077
  - python3 scripts/build_live2d_part_success_pattern_spec.py --manifest experiments/live2d-strong-model-pattern-001/reports/pilot_render_manifest.json --runtime-report experiments/live2d-strong-model-pattern-001/reports/pilot_runtime_probe_report.json
  - python3 scripts/build_live2d_runtime_probe_sandbox.py --manifest experiments/live2d-strong-model-pattern-001/reports/strong20_render_manifest.json
  - npm install && npm run build in experiments/live2d-strong-model-pattern-001/probe_sandbox/strong20/Samples/TypeScript/Demo
  - python3 scripts/run_live2d_runtime_probe_capture.py --manifest experiments/live2d-strong-model-pattern-001/reports/strong20_render_manifest.json --sandbox-report experiments/live2d-strong-model-pattern-001/reports/strong20_runtime_probe_sandbox.json --port 5078
  - python3 scripts/build_live2d_part_success_pattern_spec.py --manifest experiments/live2d-strong-model-pattern-001/reports/strong20_render_manifest.json --runtime-report experiments/live2d-strong-model-pattern-001/reports/strong20_runtime_probe_report.json
output:
  - scripts/build_live2d_strong_model_render_manifest.py
  - scripts/build_live2d_runtime_probe_sandbox.py
  - scripts/run_live2d_runtime_probe_capture.py
  - scripts/build_live2d_part_success_pattern_spec.py
  - experiments/live2d-strong-model-pattern-001/reports/pilot_render_manifest.json
  - experiments/live2d-strong-model-pattern-001/reports/pilot_runtime_probe_report.json
  - experiments/live2d-strong-model-pattern-001/reports/pilot_contact_sheet.png
  - experiments/live2d-strong-model-pattern-001/reports/strong20_render_manifest.json
  - experiments/live2d-strong-model-pattern-001/reports/strong20_runtime_probe_report.json
  - experiments/live2d-strong-model-pattern-001/reports/strong20_contact_sheet.png
  - experiments/live2d-strong-model-pattern-001/reports/cmo3_structure_batch_summary.json
  - experiments/live2d-strong-model-pattern-001/reports/cmo3_structure_batch_summary.md
  - experiments/live2d-strong-model-pattern-001/reports/part_success_patterns.json
  - experiments/live2d-strong-model-pattern-001/reports/part_success_patterns.md
  - experiments/live2d-strong-model-pattern-001/reports/cubism_v2_tier_spec.json
  - experiments/live2d-strong-model-pattern-001/reports/cubism_v2_tier_spec.md
  - experiments/live2d-strong-model-pattern-001/captures/*/*.png
  - /Users/family/jason/jason-agent-harness-template/harnesses/vtube-live2d-strong-model-pattern.md
metric:
  - pilot runtime render: 5/5 PASS
  - strong20 runtime render: 20/20 PASS
  - strong20 CMO3 reports: 20 generated, 0 missing
  - strong20 observed ArtMeshes: min 57, median 88, max 262, mean 117.65
  - strong20 observed Parameters: min 25, median 44, max 138, mean 56.4
  - strong20 observed Warp Deformers: min 27, median 53.5, max 128, mean 62.35
  - strong20 observed Rotation Deformers: min 2, median 20, max 107, mean 29.8
  - strong20 observed KeyformBindings: min 85, median 220.5, max 497, mean 253.45
  - part success sections populated: eye, mouth, hair, body_angle, arm, physics, mask_pose_expression, psd_layering
result: The real runtime pass rate confirms the selected official references render in Web Cubism before they are used as success-pattern evidence. The CMO3/runtime combined baseline supports keeping `v2_standard` as the first production target and treating `v2_min` only as a deformer/keyform/physics gate fixture.
decision: Use `live2d-strong-model-pattern-001/reports/part_success_patterns.md` and `cubism_v2_tier_spec.md` as the immediate next Cubism v2 design inputs. Do not use official screenshots or textures as assets.
next_action: Write the new model's v2_standard part taxonomy, parameter map, deformer/keyform floor, physics groups, and G0/G1/G2/G3 review packet expectations before generating or splitting new character art.
```

## LIVE2D-ALL57-PRODUCTION-DESIGN-SPEC-001

```yaml
id: LIVE2D-ALL57-PRODUCTION-DESIGN-SPEC-001
date: 2026-06-07
owner: Codex
status: PASS_PRODUCTION_DESIGN_READY
hypothesis: The complete 57-reference Live2D corpus should be unfolded into concrete Cubism v2 production design tables before any new character art is generated.
input:
  - experiments/reference-model-structure-001/reports/reference_model_structure_summary.combined.json
  - experiments/reference-model-structure-001/official_combined_analysis/models/*/reference_model_report.json
  - experiments/reference-model-structure-001/official_combined_analysis/models/*/cmo3_structure_report.json
command:
  - python3 -m py_compile scripts/build_live2d_all57_production_design_spec.py
  - python3 scripts/build_live2d_all57_production_design_spec.py
  - python3 scripts/validate_review_app.py
  - python3 scripts/validate_review_app.py --manifest experiments/cubism-v2-validator-fixtures-001/review_manifest.fixtures.json
  - bash /Users/family/jason/jason-agent-harness-template/scripts/check-harness.sh
output:
  - scripts/build_live2d_all57_production_design_spec.py
  - experiments/reference-model-structure-001/reports/all57_part_taxonomy_matrix.json
  - experiments/reference-model-structure-001/reports/all57_part_taxonomy_matrix.md
  - experiments/reference-model-structure-001/reports/all57_parameter_map.json
  - experiments/reference-model-structure-001/reports/all57_parameter_map.md
  - experiments/reference-model-structure-001/reports/all57_deformer_keyform_floor.json
  - experiments/reference-model-structure-001/reports/all57_deformer_keyform_floor.md
  - experiments/reference-model-structure-001/reports/all57_physics_group_design.json
  - experiments/reference-model-structure-001/reports/all57_physics_group_design.md
  - experiments/reference-model-structure-001/reports/cubism_v2_production_design_spec.json
  - experiments/reference-model-structure-001/reports/cubism_v2_production_design_spec.md
  - /Users/family/jason/jason-agent-harness-template/harnesses/vtube-live2d-all57-production-design.md
metric:
  - all57 model count: 57
  - FULL_STRUCTURE/RUNTIME_ONLY: 34/23
  - rig-floor eligible FULL_STRUCTURE models: 32
  - physics-present models: 44
  - taxonomy categories: 20
  - parameter categories: 13
  - production tiers: v2_min, v2_standard, v2_rich
  - production spec schema_version: 2
  - schema v2 parameter_map_detail entries: 17
  - schema v2 deformer_hierarchy nodes: 11
  - schema v2 physics_blueprint groups: 6
  - schema v2 acceptance gates: G0_CONCEPT, G1_PART_TAXONOMY, G2_STRUCTURE, G3_MOTION_VISUAL
  - self-review enhancement: parameter map includes top motion parameter IDs; deformer/keyform floor includes section-level keyform binding stats for eye/mouth/hair/body_angle/arm
  - v2_standard floor: parameters >=25, warp >=35, rotation >=8, keyform >=120, physics_groups >=4
  - v2_standard recommended target: parameters 35-55, warp 40-65, rotation 12-25, keyform 160-260, physics_groups 4-6
result: The all57 corpus is now available as production design tables. Deformer/keyform floors are calculated from FULL_STRUCTURE only; RUNTIME_ONLY taxonomy rows are marked as parameter/physics inferred. The production spec JSON was expanded to schema v2 so the parameter map detail, deformer hierarchy, physics blueprint, and G0-G3 acceptance checklist are machine-readable before Markdown/UI usage. `v2_standard` remains the first production target.
decision: Use `cubism_v2_production_design_spec.md` and the all57 tables as the production design basis before generating or splitting new character art.
next_action: Write the project-specific v2_standard character spec: exact 50-70 part list, parameter map, Cubism deformer/keyform checklist, physics groups, and G0/G1/G2/G3 review packet.
```

## CUBISM-V2-NEW-MODEL-PART-SPEC-001

```yaml
id: CUBISM-V2-NEW-MODEL-PART-SPEC-001
date: 2026-06-08
owner: Codex
status: SPEC_CONFIRMED
hypothesis: The schema v2 production spec should be turned into a concrete 50-70 source-part taxonomy before generating the new matched character art.
input:
  - experiments/reference-model-structure-001/reports/cubism_v2_production_design_spec.json
command:
  - python3 -m py_compile scripts/build_cubism_v2_new_model_part_spec.py
  - python3 scripts/build_cubism_v2_new_model_part_spec.py
output:
  - scripts/build_cubism_v2_new_model_part_spec.py
  - experiments/reference-model-structure-001/reports/cubism_v2_new_model_v2_standard_part_spec.json
  - experiments/reference-model-structure-001/reports/cubism_v2_new_model_v2_standard_part_spec.md
metric:
  - self_review: PASS
  - confirmed part count: 64
  - group counts: body 10, face_base 8, eye_L 8, eye_R 8, brow 2, mouth 8, hair 16, clothing 4
  - underpaint parts: 9
  - physics groups covered: front_hair_physics, side_hair_L_physics, side_hair_R_physics, back_hair_physics, body_breath_physics
  - required parameters covered: ParamAngleX, ParamAngleY, ParamAngleZ, ParamBodyAngleX, ParamBodyAngleY, ParamEyeLOpen, ParamEyeROpen, ParamEyeBallX, ParamEyeBallY, ParamMouthOpenY, ParamMouthForm, ParamBreath
  - deferred to v2_rich: complex hands/fingers, heavy props, large effects, skirt/cloth secondary rig, vowel lip-sync ParamA/I/U/E/O
result: The new model's v2_standard source part taxonomy is confirmed at 64 parts. The list is intentionally production-oriented: enough split for eye/mouth/hair/body angle and simple arms, but not overloaded with v2_rich hands, props, effects, or advanced vowel lip-sync.
decision: Use `cubism_v2_new_model_v2_standard_part_spec.md` as the source-part target for the next matched character generation and G1 part taxonomy review.
next_action: Build the image-generation prompt/PSD layer naming plan from the 64-part spec, then generate only concepts that can satisfy G0/G1 before Cubism authoring.
```

## VTUBE-DOCS-LEGACY-ARCHIVE-2026-06-08

```yaml
id: VTUBE-DOCS-LEGACY-ARCHIVE-2026-06-08
date: 2026-06-08
owner: Codex
status: ARCHIVED_SUPERSEDED_PLANS
hypothesis: Docs that conflict with the current Cubism v2 64-part production path should be moved to archive so future agents do not treat Mini Cubism, old See-through, White Wolf, or v1 part-purity plans as the active SSOT.
input:
  - docs/ref/*.md
  - docs/status/NEXT-AGENT-HANDOFF.md
command:
  - mkdir -p docs/archive/2026-06-08-superseded-plans
  - mv superseded plan docs into docs/archive/2026-06-08-superseded-plans
output:
  - docs/archive/2026-06-08-superseded-plans/README.md
  - docs/archive/2026-06-08-superseded-plans/LIVE2D-PART-PURITY-PIPELINE.md
  - docs/archive/2026-06-08-superseded-plans/LIVE2D-PART-SCHEMA.md
  - docs/archive/2026-06-08-superseded-plans/MAC-LAYER-DECOMP-OPTIONS.md
  - docs/archive/2026-06-08-superseded-plans/MINI-CUBISM-DEDICATED-PART-SPEC-v1.md
  - docs/archive/2026-06-08-superseded-plans/MINI-CUBISM-FEATURE-SPEC.md
  - docs/archive/2026-06-08-superseded-plans/MINI-CUBISM-GLUE-FIXTURE-GATE.md
  - docs/archive/2026-06-08-superseded-plans/MINI-CUBISM-OSS-RESEARCH.md
  - docs/archive/2026-06-08-superseded-plans/MINI-CUBISM-PACK-SPLITTER-v0-PLAN.md
  - docs/archive/2026-06-08-superseded-plans/NEXT-AGENT-HANDOFF.md
  - docs/archive/2026-06-08-superseded-plans/UBUNTU-CUDA-SEETHROUGH-RUNBOOK.md
  - docs/archive/2026-06-08-superseded-plans/WHITE-WOLF-GOTH-CONCEPT.md
  - docs/status/NEXT-AGENT-HANDOFF.md
  - docs/status/PROJECT-STATUS.md
  - docs/archive/ARCHIVE-INDEX.md
metric:
  - archived docs: 11
  - current docs/ref kept: CUBISM-V2-SUCCESS-PATTERN-PLAN.md, CUBISM-V2-REVIEW-GATE-SPEC.md, VTUBE-HARNESS-SKILL-ROUTING-AUDIT.md
  - current progress snapshot added to PROJECT-STATUS.md
result: Superseded plan documents were preserved under archive instead of deleted. The active handoff now points to Cubism v2 production spec schema v2 and the confirmed 64-part v2_standard new model spec.
decision: Treat archived docs as history/support only; current SSOT remains PROJECT-STATUS plus Cubism v2 spec reports.
next_action: Build the image-generation prompt and PSD layer naming plan from the confirmed 64-part spec.
```

## CUBISM-V2-PART-LOCALIZATION-TEMPLATE-001

```yaml
id: CUBISM-V2-PART-LOCALIZATION-TEMPLATE-001
date: 2026-06-08
owner: Codex
status: REVISE_TEMPLATE_SPLIT_NEEDS_SEMANTIC_MASKING
hypothesis: Saved manual semantic ROI labels can become a reusable localization template and can drive an actual current-candidate layer split.
input:
  - experiments/cubism-v2-new-character-001/material_pack_v0/reports/manual_semantic_overrides.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/layer_manifest.json
command:
  - python3 -m py_compile scripts/build_cubism_v2_part_localization_template.py scripts/apply_cubism_v2_part_localization_template.py scripts/build_cubism_v2_semantic_purity_gate.py scripts/build_cubism_v2_localization_validation_report.py
  - python3 scripts/build_cubism_v2_part_localization_template.py
  - python3 scripts/apply_cubism_v2_part_localization_template.py
  - python3 scripts/build_cubism_v2_semantic_purity_gate.py --source-manifest experiments/cubism-v2-new-character-001/material_pack_v0/layer_manifest.json --no-apply-remask
  - python3 scripts/build_mini_cubism_project_from_cubism_v2_material_pack.py --pack experiments/cubism-v2-new-character-001/material_pack_v0 --out experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_localized_v1
  - python3 scripts/validate_mini_cubism_project.py --project experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_localized_v1
  - python3 scripts/build_cubism_v2_localization_validation_report.py
output:
  - scripts/build_cubism_v2_part_localization_template.py
  - scripts/apply_cubism_v2_part_localization_template.py
  - scripts/build_cubism_v2_localization_validation_report.py
  - experiments/cubism-v2-new-character-001/material_pack_v0/reports/part_localization_template.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/reports/part_localization_template.md
  - experiments/cubism-v2-new-character-001/material_pack_v0/reports/part_localization_split_report.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/reports/part_localization_split_contact_sheet.png
  - experiments/cubism-v2-new-character-001/material_pack_v0/reports/semantic_purity_localization_split/semantic_purity_gate_report.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/reports/part_localization_template_validation_report.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/reports/part_localization_template_validation_report.md
  - experiments/cubism-v2-new-character-001/material_pack_v0/layer_manifest.localization_template_split_v1.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/production_layers_localized_v1
  - experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_localized_v1/reports/validation_report.json
metric:
  - manual overrides: 37
  - template parts: 37
  - localized split applied parts: 37
  - localized split kept parts: 25
  - Mini Cubism localized project: PASS, 62 parts, 62 meshes, 11 deformers, 15 parameters, 22 keyform bindings
  - direct G1.5 source manifest: active layer_manifest.json, not stale pre-semantic backup
  - G1.5 localized split status: REVISE_G1_5_SEMANTIC_PURITY_GATE
  - neutral_after_bad_ratio_visible: 0.088469
  - required neutral threshold: <= 0.05
  - eye/mouth ROI after status: PASS
  - underpaint top-owner pixels: 3110 -> 145
  - remaining layer-alone issues: 9 underpaint review rows
result: Manual labels successfully became a reusable localization template and drove an actual current-candidate layer split. The split is structurally usable in Mini Cubism, but raw ROI crop is not production-ready because the semantic/neutral gate still fails.
decision: Keep `part_localization_template.json` and `layer_manifest.localization_template_split_v1.json` as localization evidence for future characters and targeted remask. The active `layer_manifest.json` was restored to the prior G1.5 PASS semantic repair state; do not promote `production_layers_localized_v1` as final material evidence without semantic mask/underpaint repair and G1.5 PASS.
next_action: Use the saved template to guide semantic owner-map repair: keep good existing semantic repair layers for large body/hair/clothing areas, apply ROI-guided remask only to mislabeled eye/mouth/face parts, and regenerate/repair underpaint separately.
```

## CUBISM-V2-ROI-GUIDED-SEMANTIC-REMASK-001

```yaml
id: CUBISM-V2-ROI-GUIDED-SEMANTIC-REMASK-001
date: 2026-06-08
owner: Codex
status: PASS_ROI_GUIDED_SEMANTIC_REMASK_V1
hypothesis: `part_localization_template.json` should be used as a correct-position seed, not as a raw crop command; semantic owner-map repair and underpaint transfer should produce production-safer layers.
input:
  - experiments/cubism-v2-new-character-001/material_pack_v0/reports/part_localization_template.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/layer_manifest.before_semantic_repair_v1.json
command:
  - python3 -m py_compile scripts/build_cubism_v2_roi_guided_semantic_remask.py
  - python3 scripts/build_cubism_v2_roi_guided_semantic_remask.py
  - python3 scripts/build_cubism_v2_roi_guided_semantic_remask.py --promote
  - python3 scripts/build_mini_cubism_project_from_cubism_v2_material_pack.py --pack experiments/cubism-v2-new-character-001/material_pack_v0 --out experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_roi_guided_v1
  - python3 scripts/validate_mini_cubism_project.py --project experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_roi_guided_v1
  - /Users/family/jason/Vtube/.venv-cubism-v2-material/bin/python scripts/validate_cubism_v2_material_assets.py
output:
  - scripts/build_cubism_v2_roi_guided_semantic_remask.py
  - experiments/cubism-v2-new-character-001/material_pack_v0/production_layers_roi_semantic_remask_v1
  - experiments/cubism-v2-new-character-001/material_pack_v0/layer_manifest.roi_guided_semantic_remask_v1.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/layer_manifest.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/reports/roi_guided_semantic_remask/roi_guided_semantic_remask_report.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/reports/roi_guided_semantic_remask/roi_guided_semantic_remask_report.md
  - experiments/cubism-v2-new-character-001/material_pack_v0/reports/roi_guided_semantic_remask/semantic_owner_map_before.png
  - experiments/cubism-v2-new-character-001/material_pack_v0/reports/roi_guided_semantic_remask/semantic_owner_map_after.png
  - experiments/cubism-v2-new-character-001/material_pack_v0/reports/roi_guided_semantic_remask/changed_layers_contact_sheet.png
  - experiments/cubism-v2-new-character-001/material_pack_v0/reports/roi_guided_semantic_remask/eye_mouth_roi_closeup_after.png
  - experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_roi_guided_v1/reports/validation_report.json
metric:
  - template parts: 37
  - ROI-guided alpha remask parts: 29
  - changed layers: 38
  - underpaint moved pixels: 76826
  - neutral_after_bad_ratio_visible: 0.000022
  - missing_pixels: 0
  - extra_pixels: 0
  - underpaint top-owner pixels after: 0
  - eye/mouth after status: PASS
  - material validator: PASS_MATERIAL_ASSET_DRAFT_READY
  - Mini Cubism ROI-guided project: PASS, 62 parts, 62 meshes, 11 deformers, 15 parameters, 22 keyform bindings
result: The manual localization template is now integrated into the successful semantic owner-map path. Unlike raw ROI crop split, ROI-guided remask keeps existing layer art, clamps relevant eye/mouth/face detail alpha to manual ROI seeds, and repairs exposed underpaint through owner-map transfer.
decision: Active `layer_manifest.json` is now `ROI_GUIDED_SEMANTIC_REMASK_V1_APPLIED`. Keep raw `production_layers_localized_v1` as a failure/control fixture only. Use `production_layers_roi_semantic_remask_v1` as the current material-pack layer source for Mini Cubism preview and the next human polish pass.
next_action: Run visual QA on ROI-guided contact sheets and Mini Cubism preview, then proceed to real Cubism ArtMesh/deformer/keyform authoring after human material acceptance.
```

## CUBISM-V2-FACE-DETAIL-VISUAL-DIAGNOSTIC-001

```yaml
id: CUBISM-V2-FACE-DETAIL-VISUAL-DIAGNOSTIC-001
date: 2026-06-08
owner: Codex
status: FAIL_FACE_DETAIL_SPLIT_DEBUG_READY
hypothesis: The repeated Mini Cubism face corruption is caused by separated face/eye/mouth layer pixels and masks, not by the Mini Cubism renderer itself.
input:
  - experiments/cubism-v2-new-character-001/material_pack_v0/layer_manifest.anchor_position_repair_candidate_v1.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/layer_manifest.clean_neutral_opacity_candidate_v1.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/layer_manifest.group_position_clean_candidate_v1.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/canonical/candidate_002_2048_rgba.png
command:
  - python3 scripts/build_cubism_v2_flattened_canonical_debug_candidate.py
  - python3 scripts/build_mini_cubism_project_from_cubism_v2_material_pack.py --pack experiments/cubism-v2-new-character-001/material_pack_v0/flattened_canonical_debug_pack_v1 --out experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_flattened_debug_v1
  - python3 scripts/validate_mini_cubism_project.py --project experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_flattened_debug_v1
  - python3 scripts/mini_cubism_preview_server.py --project experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_flattened_debug_v1 --port 8070
output:
  - scripts/build_cubism_v2_flattened_canonical_debug_candidate.py
  - experiments/cubism-v2-new-character-001/material_pack_v0/layer_manifest.flattened_canonical_debug_v1.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/flattened_canonical_debug_pack_v1/layer_manifest.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/reports/flattened_canonical_debug_candidate_report.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_flattened_debug_v1/reports/validation_report.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_flattened_debug_v1/reports/neutral_composite_offline.png
  - experiments/cubism-v2-new-character-001/material_pack_v0/canonical/canonical_on_beige.png
metric:
  - 8065 anchor-position candidate: position diagnostic only; not visual PASS
  - 8066 clean-neutral candidate: helper opacity diagnostic only; not face detail PASS
  - 8067/8069 merge attempts: human visual FAIL by 주인님 screenshots
  - 8070 debug candidate: 63 parts, 63 meshes, 11 deformers, 15 parameters, 22 keyform bindings
  - hidden problematic face detail overlays: 33
  - part_opacity_keyframes: 53
  - browser console: favicon 404 only; no project loading error observed
result: Transform-only merging is insufficient. `face_base` and detailed eye/mouth/nose/cheek/brow layers do not yet satisfy semantic ownership/visual quality even when structural Mini Cubism validation passes.
decision: Do not promote 8065, 8066, 8067, 8068, 8069, or 8070 as production material evidence. Keep them as diagnostics. At the time, the proposed recovery was rebuilding face_base plus eye/mouth masks from the clean canonical.
next_action: SUPERSEDED_BY_CUBISM-V2-MATERIAL-PACK-FIRST-GEN-PLAN-001. Do not use this as the current next-session default unless 주인님 explicitly asks to continue repairing `cubism-v2-new-character-001`.
```

## MINI-CUBISM-EYE-CLOSE-UNDERPAINT-PATCH-001

```yaml
id: MINI-CUBISM-EYE-CLOSE-UNDERPAINT-PATCH-001
date: 2026-06-08
owner: Codex
status: DISCARDED_VISUAL_FAIL
hypothesis: A closed-eye underpaint generated only from the saved eye_socket_cover bbox might hide baked open-eye pixels in `face_base`.
input:
  - experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_face_detail_rebuild_v1/mini_rig.json
  - saved eye bbox L [878, 689, 103, 73]
  - saved eye bbox R [1078, 691, 110, 73]
output:
  - experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_face_detail_rebuild_v1/reports/closed_underpaint_generation_report.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_face_detail_rebuild_v1/reports/eye_mode_validation/eye_mode_validation_report.json
metric:
  - project validation after removal: PASS, 62 parts, 62 meshes, 11 deformers, 15 parameters, 46 keyform bindings
  - eye mode numeric validation after removal: PASS
  - failed patch active references after removal: []
result: The sampled rectangular closed-eye underpaint patch could cover some baked eye pixels but looked like visible skin blocks and did not solve the root issue naturally.
decision: Do not promote bbox-sampled closed-eye underpaint patches. Active `character.json` no longer references `eye_L_closed_underpaint` or `eye_R_closed_underpaint`. Keep numeric EyeOpen/EyeBall checks as diagnostics only.
next_action: Stop rig-only tuning for this issue. Regenerate `face_base_clean` with baked eyes removed, then generate style-matched closed-eye underpaint/keypose parts and rerun layer-alone, neutral composite, Mini Cubism visual QA, and eye-mode numeric validation.
```

## MINI-CUBISM-EYE-CLOSE-SKIN-UNDERPAINT-002

```yaml
id: MINI-CUBISM-EYE-CLOSE-SKIN-UNDERPAINT-002
date: 2026-06-09
owner: Codex
status: REVISE_VISUAL_CANDIDATE
hypothesis: A clean eye socket should be generated before further rig tuning, but automatic full `face_base` repaint must not corrupt open-eye states.
input:
  - experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_face_detail_rebuild_v1
  - saved eye bbox L [878, 689, 103, 73]
  - saved eye bbox R [1078, 691, 110, 73]
output:
  - scripts/build_mini_cubism_face_base_clean_v1.py
  - experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_face_base_clean_v1/reports/face_base_clean_rebuild_report.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_face_base_clean_v2/reports/face_base_clean_rebuild_report.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_face_base_clean_v3/reports/face_base_clean_rebuild_report.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_closed_underpaint_skin_v1/reports/face_base_clean_rebuild_report.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_closed_underpaint_skin_v1/reports/eye_mode_validation/eye_close_review_crop.png
metric:
  - v4 project validation: PASS, 64 parts, 64 meshes, 11 deformers, 15 parameters, 46 keyform bindings
  - v4 eye mode numeric validation: PASS
  - v4 outside changed pixels: 0 for all tested eye modes
result: v1 rectangular inpaint, v2 alpha-only inpaint, and v3 permanent skin synthesis are visual failures. v4 preserves original `face_base` and shows feathered skin underpaint only during eye close, so open-eye and EyeBall states are preserved, but closed-eye review still shows pale underpaint and faint baked-eye remnants.
decision: Do not promote automatic `face_base_clean` or closed underpaint as production success yet. Use v4 only as a browser-review candidate and continue with mask/color/opacity refinement or manual clean eye-socket repaint.
next_action: Run the v4 preview on 8076, inspect EyeOpen closed and EyeBall X/Y, then decide whether to tune the closed-only underpaint or switch to manual repaint of the eye socket.
```

## CUBISM-V2-CLEAN-SOCKET-KEYPOSE-REQ-001

```yaml
id: CUBISM-V2-CLEAN-SOCKET-KEYPOSE-REQ-001
date: 2026-06-09
owner: Codex
status: PASS_REQUIREMENTS_READY_CURRENT_ASSETS_REVISE
hypothesis: EyeOpen/MouthOpen should not continue as rig tuning until clean sockets and in-between keypose PNGs exist as validated material assets.
input:
  - experiments/live2d-keypose-spec-001/reports/live2d_keypose_spec.md
  - experiments/cubism-v2-new-character-001/reports/g1_material_planning_packet.md
  - experiments/cubism-v2-new-character-001/material_pack_v0/production_layers_face_detail_rebuild_v1
output:
  - scripts/build_cubism_v2_clean_socket_keypose_spec.py
  - scripts/validate_cubism_v2_keypose_pngs.py
  - experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/clean_socket_keypose_requirements.md
  - experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/clean_socket_keypose_requirements.json
  - experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/current_face_detail_keypose_validation_report.md
metric:
  - required assets: 19
  - current face-detail validation: REVISE, 5 found, 14 missing
  - existing no-resize assets: eye_L_closed_lid, eye_R_closed_lid, mouth_inner, mouth_teeth, mouth_tongue are 2048x2048 RGBA
  - selected concept candidate_002: 1086x1448 RGB, requires 2048 full-canvas normalization plus alpha extraction before material-layer use
decision: Clean sockets, eye half/mostly/closed keyposes, and mouth clean/keyposes are now explicit material requirements before more rig tuning. Imagen may be used to generate them, but outputs must pass PNG validation and visual QA before Mini Cubism/Cubism promotion.
next_action: Generate missing assets with the prompt plan, normalize non-2048/crop/RGB outputs using ROI/anchor evidence, then rerun `validate_cubism_v2_keypose_pngs.py`.
```

## CUBISM-V2-IMAGEN-KEYPOSE-INPUT-PACK-001

```yaml
id: CUBISM-V2-IMAGEN-KEYPOSE-INPUT-PACK-001
date: 2026-06-09
owner: Codex
status: PASS_INPUT_PACK_READY
hypothesis: The clean socket/keypose requirements should be converted into a concrete Imagen input pack before any new generation or rig tuning.
input:
  - experiments/cubism-v2-new-character-001/material_pack_v0/canonical/candidate_002_2048_rgba.png
  - experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/clean_socket_keypose_requirements.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_face_detail_rebuild_v1/character.json
  - experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_face_detail_rebuild_v1/mini_rig.json
output:
  - scripts/build_cubism_v2_imagen_keypose_input_pack.py
  - experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/imagen_input_pack_v1/README.md
  - experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/imagen_input_pack_v1/imagen_input_pack_manifest.json
  - experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/imagen_input_pack_v1/references/source_roi_overlay.png
  - experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/imagen_input_pack_v1/references/roi_crop_contact_sheet.png
  - experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/imagen_input_pack_v1/prompts/*.md
  - experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/imagen_input_pack_v1/prompts/*.json
  - experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/imagen_input_pack_v1/masks/*_full_canvas_mask.png
metric:
  - input pack status: PASS_INPUT_PACK_READY
  - assets covered: 19
  - ROI eye_L: [761, 613, 297, 233]
  - ROI eye_R: [1014, 616, 297, 235]
  - ROI mouth: [907, 773, 250, 356]
  - ROI face: [584, 312, 866, 1460]
  - manual saved eye bbox preserved: L [878, 689, 103, 73], R [1078, 691, 110, 73]
decision: Use this pack for the next Imagen/manual generation pass. Keep generated outputs out of promotion until `validate_cubism_v2_keypose_pngs.py` and human visual QA pass.
next_action: Generate missing PNGs from the per-asset prompt files, put outputs in a generated directory, then run the keypose PNG validator and normalize any non-2048/RGB/crop outputs.
```

## CUBISM-V2-LOCAL-KEYPOSE-PNG-GEN-001

```yaml
id: CUBISM-V2-LOCAL-KEYPOSE-PNG-GEN-001
date: 2026-06-09
owner: Codex
status: PASS_LOCAL_PNG_VALIDATION_VISUAL_QA_REQUIRED
hypothesis: The prepared clean socket/keypose input pack can be realized into actual 2048 RGBA PNG files and checked with the keypose PNG validator before any further rig tuning.
input:
  - experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/imagen_input_pack_v1/imagen_input_pack_manifest.json
  - experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/clean_socket_keypose_requirements.json
  - experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/imagen_input_pack_v1/references/source_candidate_002_2048_rgba.png
  - experiments/cubism-v2-new-character-001/material_pack_v0/production_layers_face_detail_rebuild_v1
output:
  - scripts/generate_cubism_v2_keypose_pngs_from_pack_local.py
  - experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/local_generated_keypose_v1/local_generation_report.json
  - experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/local_generated_keypose_v1/local_generated_keypose_validation_report.json
  - experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/local_generated_keypose_v1/local_generated_keypose_validation_report.md
  - experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/local_generated_keypose_v1/local_generated_keypose_contact_sheet.png
  - experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/local_generated_keypose_v1/normalized_layers/*.png
metric:
  - generated PNG assets: 19
  - validator status: PASS_READY_FOR_VISUAL_QA
  - validator found: 19/19
  - missing: 0
  - normalize required: 0
  - alpha/mode repair required: 0
  - copied existing validated layers: eye_L_closed_lid, eye_R_closed_lid, mouth_inner, mouth_teeth, mouth_tongue
  - newly local-generated candidates: face_base_clean, eye_L/R_clean_socket, eye_L/R_half_closed_lid, eye_L/R_mostly_closed_lid, eye_L/R_closed_underpaint, mouth_base_clean, mouth_closed_smile, mouth_small_open, mouth_wide_open, mouth_o_vowel
decision: This is real PNG output and a technical validator PASS, but not a production visual PASS. The contact sheet shows procedural clean-socket patches and simplified keyposes, so these outputs must remain visual-QA/model-native-inpaint/manual-repaint candidates only.
next_action: Review `local_generated_keypose_contact_sheet.png`; either use the generated folder for a Mini Cubism diagnostic smoke or replace the rough procedural assets with model-native/edit-based inpaint outputs before production rigging.
```

## CUBISM-V2-MATERIAL-PACK-FIRST-GEN-PLAN-001

```yaml
id: CUBISM-V2-MATERIAL-PACK-FIRST-GEN-PLAN-001
date: 2026-06-09
owner: Codex
status: SPEC_READY_NEXT_SESSION
hypothesis: The next new character should generate the source front image and same-character clean bases/keyposes as a coordinated material pack from the beginning, instead of repairing baked face details after the fact.
input:
  - experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/local_generated_keypose_v1/local_generated_keypose_contact_sheet.png
  - experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/local_generated_keypose_v1/local_generated_keypose_validation_report.json
  - experiments/reference-model-structure-001/reports/cubism_v2_new_model_v2_standard_part_spec.md
  - experiments/reference-model-structure-001/reports/cubism_v2_character_prompt_template.md
output:
  - docs/ref/CUBISM-V2-MATERIAL-PACK-FIRST-GENERATION.md
  - docs/status/NEXT-AGENT-HANDOFF.md
  - docs/status/PROJECT-STATUS.md
  - experiments/cubism-v2-new-character-002/README.md
  - experiments/cubism-v2-new-character-002/reports/material_pack_first_generation_spec.json
  - /Users/family/jason/jason-agent-harness-template/harnesses/vtube-cubism-v2-material-pack-first-generation.md
metric:
  - required next experiment id: cubism-v2-new-character-002
  - required source: new_character_002_source_front
  - required eye assets: eye_L/R_open, eye_L/R_clean_socket, eye_L/R_half_closed, eye_L/R_mostly_closed, eye_L/R_closed, eye_L/R_closed_underpaint
  - required mouth assets: mouth_base_clean, mouth_closed, mouth_small_open, mouth_wide_open, mouth_o_vowel, mouth_inner, mouth_teeth, mouth_tongue
  - validation gate: `validate_cubism_v2_keypose_pngs.py` before Mini Cubism diagnostics
  - visual gate: contact sheet/human QA before any production rigging claim
decision: Next default path is material-pack-first generation for `cubism-v2-new-character-002`. `cubism-v2-new-character-001/local_generated_keypose_v1` remains a technical validator fixture and visual failure candidate, not the next production material source.
next_action: In the next session, read `CUBISM-V2-MATERIAL-PACK-FIRST-GENERATION.md`, create the `cubism-v2-new-character-002` experiment folder/spec, generate the source front image plus coordinated material/keypose PNG set, normalize outputs, run PNG validation, and ask for visual QA.
```

## CUBISM-V2-NEW-CHARACTER-002-LOCAL-CLEANBASE-REPAIR-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-LOCAL-CLEANBASE-REPAIR-001
date: 2026-06-09
owner: Codex
status: REVISE_MINI_CUBISM_BLOCKED
hypothesis: Keeping the selected source_front and repairing only clean sockets/underpaint/mouth base with source-face inpaint or layer-alpha masks may remove the pasted skin-patch boundaries without restarting the whole character.
input:
  - experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png
  - experiments/cubism-v2-new-character-002/material_pack_first_v0/normalized_layers
  - experiments/cubism-v2-new-character-002/reports/material_pack_first_overlay_human_review_20260609.md
output:
  - scripts/build_cubism_v2_source_inpaint_clean_bases_002.py
  - scripts/build_cubism_v2_feature_mask_clean_bases_002.py
  - experiments/cubism-v2-new-character-002/material_pack_first_v1_source_inpaint/normalized_layers
  - experiments/cubism-v2-new-character-002/material_pack_first_v2_feature_mask/normalized_layers
  - experiments/cubism-v2-new-character-002/material_pack_first_v3_feature_seed_mask/normalized_layers
  - experiments/cubism-v2-new-character-002/material_pack_first_v4_layer_alpha_seed/normalized_layers
  - experiments/cubism-v2-new-character-002/material_pack_first_v5_layer_alpha_seed_strict_expr/normalized_layers
  - experiments/cubism-v2-new-character-002/reports/layer_alpha_seed_v5/layer_alpha_seed_keypose_validation_report.json
  - experiments/cubism-v2-new-character-002/reports/layer_alpha_seed_v5/layer_alpha_seed_visual_qa_report.md
metric:
  - v1 source-inpaint validator: PASS_READY_FOR_VISUAL_QA
  - v2 feature-mask validator: PASS_READY_FOR_VISUAL_QA
  - v4 layer-alpha-seed validator: PASS_READY_FOR_VISUAL_QA
  - v5 layer-alpha-seed strict-expression validator: PASS_READY_FOR_VISUAL_QA
  - v5 mouth overlay: oval patch boundary reduced, but mouth_base_clean still leaves the original source mouth line visible
  - v5 eye overlay: clean socket/underpaint still looks like smeared local inpaint around hair/skin/eyelid boundaries
decision: Do not proceed to Mini Cubism diagnostic preview from the local/source-inpaint repair candidates. The character/source can stay, but clean-base assets need model-native/edit-based inpainting or manual repaint before overlay QA can pass.
next_action: Generate or manually repaint eye_L/R_clean_socket, eye_L/R_closed_underpaint, and mouth_base_clean from the source face with native clean-base context, then rerun PNG validator and overlay QA. Only after visual QA passes should Mini Cubism diagnostic preview resume.
```

## CUBISM-V2-NEW-CHARACTER-002-EYEOPEN-027-DIAGNOSTIC-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-EYEOPEN-027-DIAGNOSTIC-001
date: 2026-06-09
owner: Codex
status: PASS_MINI_CUBISM_EYE_OPEN_027_CAPTURED
hypothesis: After manual eye/mouth alignment and v7 slider cleanup, the current Character 002 keypose pack has a usable natural eye-close threshold around EyeOpen 0.27 even though production clean-base material polish is still blocked.
input:
  - experiments/cubism-v2-new-character-002/model_edit_v7_smooth_mouth_preview/mini_cubism_diagnostic_project
  - experiments/cubism-v2-new-character-002/reports/model_edit_v4_strict_mouth/manual_alignment_v1/manual_keypose_alignment_overrides.json
output:
  - scripts/build_mini_cubism_eye_open_027_packet_002.py
  - experiments/cubism-v2-new-character-002/reports/model_edit_v7_smooth_mouth_preview/eye_open_027_success_packet/eye_open_027_success_report.json
  - experiments/cubism-v2-new-character-002/reports/model_edit_v7_smooth_mouth_preview/eye_open_027_success_packet/eye_open_027_success_report.md
  - experiments/cubism-v2-new-character-002/reports/model_edit_v7_smooth_mouth_preview/eye_open_027_success_packet/eye_open_027_contact_sheet.png
  - experiments/cubism-v2-new-character-002/reports/model_edit_v7_smooth_mouth_preview/eye_open_027_success_packet/frames/*.png
metric:
  - v7 validator: PASS
  - v7 parts: 19
  - v7 meshes: 19
  - v7 deformers: 6
  - v7 parameters: 5
  - v7 keyform_bindings: 6
  - captured EyeOpen values: 1.0, 0.5, 0.27, 0.0
  - EyeOpen 0.27 active parts: eye_L_half_closed_lid, eye_R_half_closed_lid
  - EyeOpen 0.0 active parts: eye_L_closed_lid, eye_R_closed_lid, eye_L_closed_underpaint, eye_R_closed_underpaint
decision: Record EyeOpen 0.27 as the current natural-close success pattern for the v7 Mini Cubism diagnostic preview. Keep 0.0 as technical full-close only. Do not claim real Cubism production success from this packet.
next_action: Use this packet as the eye-close baseline while continuing material cleanup for clean sockets, closed underpaint, and mouth_base_clean; after material QA passes, retest mouth smoothness and real hair/front-hair separation before Cubism authoring.
```

## CUBISM-V2-NEW-CHARACTER-002-EXISTING-MOUTH-PACKET-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-EXISTING-MOUTH-PACKET-001
date: 2026-06-09
owner: Codex
status: PASS_EXISTING_MOUTH_PACKET_READY_FOR_VISUAL_QA
hypothesis: The next mouth diagnostic should proceed with the already generated mouth PNGs instead of generating new smile-open art.
input:
  - experiments/cubism-v2-new-character-002/model_edit_v7_smooth_mouth_preview/mini_cubism_diagnostic_project/parts/mouth_closed_smile.png
  - experiments/cubism-v2-new-character-002/model_edit_v7_smooth_mouth_preview/mini_cubism_diagnostic_project/parts/mouth_small_open.png
  - experiments/cubism-v2-new-character-002/model_edit_v7_smooth_mouth_preview/mini_cubism_diagnostic_project/parts/mouth_inner.png
  - experiments/cubism-v2-new-character-002/model_edit_v7_smooth_mouth_preview/mini_cubism_diagnostic_project/parts/mouth_teeth.png
  - experiments/cubism-v2-new-character-002/model_edit_v7_smooth_mouth_preview/mini_cubism_diagnostic_project/parts/mouth_tongue.png
  - experiments/cubism-v2-new-character-002/model_edit_v7_smooth_mouth_preview/mini_cubism_diagnostic_project/parts/mouth_o_vowel.png
  - experiments/cubism-v2-new-character-002/model_edit_v6_no_wide_open/normalized_layers/mouth_wide_open.png
output:
  - scripts/build_cubism_v2_existing_mouth_review_packet_002.py
  - experiments/cubism-v2-new-character-002/reports/model_edit_v8_existing_mouth_packet/existing_generated_mouth_packet_report.json
  - experiments/cubism-v2-new-character-002/reports/model_edit_v8_existing_mouth_packet/existing_generated_mouth_packet_report.md
  - experiments/cubism-v2-new-character-002/reports/model_edit_v8_existing_mouth_packet/existing_generated_mouth_contact_sheet.png
  - experiments/cubism-v2-new-character-002/reports/model_edit_v8_existing_mouth_packet/normalized_layers/mouth_*.png
metric:
  - copied existing mouth PNGs: 7
  - full-canvas 2048 RGBA: PASS
  - active v7 mouth states: mouth_closed_smile, mouth_small_open
  - reference-only helper states: mouth_inner, mouth_teeth, mouth_tongue
  - active-excluded states: mouth_o_vowel, mouth_wide_open
decision: Proceed with existing generated mouth assets. Keep `mouth_closed_smile` and `mouth_small_open` as active `ParamMouthOpenY` states. Preserve `inner/teeth/tongue` as references only for now because they read as separate large mouth pieces when directly overlaid. Preserve but exclude `mouth_o_vowel` and `mouth_wide_open`.
next_action: Tune or preview only the existing active two-state mouth crossfade first; do not generate new smile-open art unless 주인님 rejects this existing-mouth review packet.
```

## CUBISM-V2-NEW-CHARACTER-002-EXISTING-MOUTH-TUNED-PREVIEW-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-EXISTING-MOUTH-TUNED-PREVIEW-001
date: 2026-06-09
owner: Codex
status: PASS_EXISTING_MOUTH_OPEN_CAPTURED_REVIEW_LIMITED_BY_ASSET
hypothesis: Existing generated mouth assets can be made less abrupt by reducing mouth_warp movement and using a wider opacity crossfade, without generating new mouth art.
input:
  - experiments/cubism-v2-new-character-002/model_edit_v7_smooth_mouth_preview/mini_cubism_diagnostic_project
  - experiments/cubism-v2-new-character-002/reports/model_edit_v8_existing_mouth_packet/existing_generated_mouth_packet_report.json
output:
  - scripts/build_mini_cubism_v8_existing_mouth_tuned_preview_002.py
  - scripts/build_mini_cubism_existing_mouth_open_packet_002.py
  - experiments/cubism-v2-new-character-002/model_edit_v8_existing_mouth_tuned_preview/mini_cubism_diagnostic_project
  - experiments/cubism-v2-new-character-002/model_edit_v8_existing_mouth_tuned_preview/mini_cubism_diagnostic_project/reports/validation_report.json
  - experiments/cubism-v2-new-character-002/reports/model_edit_v8_existing_mouth_tuned_preview/mini_cubism_v8_existing_mouth_tuned_preview_report.json
  - experiments/cubism-v2-new-character-002/reports/model_edit_v8_existing_mouth_tuned_preview/existing_mouth_open_packet/existing_mouth_open_report.json
  - experiments/cubism-v2-new-character-002/reports/model_edit_v8_existing_mouth_tuned_preview/existing_mouth_open_packet/existing_mouth_open_contact_sheet.png
metric:
  - validator: PASS
  - parts: 19
  - meshes: 19
  - deformers: 6
  - parameters: 5
  - keyform_bindings: 7
  - active mouth states: mouth_closed_smile, mouth_small_open
  - captured MouthOpenY values: 0.0, 0.2, 0.4, 0.6, 0.8, 1.0
  - v7 mouth_warp: translate [0,8], scale [1,1.15]
  - v8 mouth_warp: key 0.5 translate [0,1], scale [1,1.015]; key 1.0 translate [0,2], scale [1,1.03]
decision: Existing-only v8 is structurally valid and less transform-heavy than v7. Visual review still depends on whether 주인님 accepts the existing `mouth_small_open` art, which reads as a small centered speaking mouth rather than a true smile-open mouth.
next_action: Show v8 preview to 주인님. If accepted, keep v8 as the current existing-mouth diagnostic baseline; if rejected, the blocker is mouth art, not crossfade timing.
```

## CUBISM-V2-NEW-CHARACTER-002-GENERATED-MOUTH-EYE-CLAMP-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-GENERATED-MOUTH-EYE-CLAMP-001
date: 2026-06-09
owner: Codex
status: PASS_GENERATED_MOUTH_V10_EYE_CLAMP
hypothesis: A new generated smile-open mouth sheet can fix the wide/teeth/tongue asset problem, and the eye success threshold can be enforced by clamping EyeOpen parameters at 0.27.
input:
  - /Users/family/.codex/generated_images/019ea9dd-f119-74d1-824b-b6ce2f40def8/ig_03de1a91a14034b9016a27a27300908191bf90b33fbeb96d6d.png
  - experiments/cubism-v2-new-character-002/model_edit_v8_existing_mouth_tuned_preview/mini_cubism_diagnostic_project
output:
  - scripts/process_generated_smile_mouth_sheet_002.py
  - scripts/build_mini_cubism_v10_generated_mouth_eye_clamp_preview_002.py
  - experiments/cubism-v2-new-character-002/generated_mouth_v10/raw_outputs/smile_mouth_keypose_sheet_chromakey.png
  - experiments/cubism-v2-new-character-002/generated_mouth_v10/normalized_layers/mouth_smile_closed_gen.png
  - experiments/cubism-v2-new-character-002/generated_mouth_v10/normalized_layers/mouth_smile_small_open_gen.png
  - experiments/cubism-v2-new-character-002/generated_mouth_v10/normalized_layers/mouth_smile_mid_teeth_gen.png
  - experiments/cubism-v2-new-character-002/generated_mouth_v10/normalized_layers/mouth_smile_wide_teeth_tongue_gen.png
  - experiments/cubism-v2-new-character-002/generated_mouth_v10/reports/generated_smile_mouth_contact_sheet.png
  - experiments/cubism-v2-new-character-002/model_edit_v10_generated_mouth_eye_clamp_preview/mini_cubism_diagnostic_project
  - experiments/cubism-v2-new-character-002/model_edit_v10_generated_mouth_eye_clamp_preview/mini_cubism_diagnostic_project/reports/validation_report.json
  - experiments/cubism-v2-new-character-002/reports/model_edit_v10_generated_mouth_eye_clamp_preview/generated_mouth_open_packet/existing_mouth_open_contact_sheet.png
metric:
  - generated mouth layers: 4
  - generated mouth layer format: 2048 RGBA full-canvas
  - v10 validator: PASS
  - v10 parts: 21
  - v10 meshes: 21
  - v10 deformers: 6
  - v10 parameters: 5
  - v10 keyform_bindings: 7
  - EyeOpen min clamp: ParamEyeLOpen 0.27, ParamEyeROpen 0.27
  - automation clamp check: input EyeOpen 0/0 -> snapshot EyeOpen 0.27/0.27
decision: Use v10 as the current generated-mouth diagnostic baseline. The new wide mouth includes teeth/tongue as one natural keypose, so old `mouth_inner/teeth/tongue` helpers stay hidden. Eye close cannot go below 0.27 through UI or automation because the app clamps setParameterValue by project parameter min/max.
next_action: 주인님 visual QA on v10 at `http://127.0.0.1:8087/`; if accepted, keep generated mouth v10 and proceed to final mouth/eye diagnostic packet.
```

## CUBISM-V2-NEW-CHARACTER-002-V10-CODEX-VISUAL-QA-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V10-CODEX-VISUAL-QA-001
date: 2026-06-09
owner: Codex
status: REVISE_MOUTH_PASS_EYE_CLAMP
hypothesis: The v10 generated smile-open mouth and EyeOpen 0.27 clamp should be checked visually before treating the diagnostic as accepted.
input:
  - experiments/cubism-v2-new-character-002/generated_mouth_v10/reports/generated_smile_mouth_contact_sheet.png
  - experiments/cubism-v2-new-character-002/reports/model_edit_v10_generated_mouth_eye_clamp_preview/generated_mouth_open_packet/existing_mouth_open_contact_sheet.png
  - experiments/cubism-v2-new-character-002/reports/model_edit_v10_generated_mouth_eye_clamp_preview/eye_open_clamp_packet/eye_open_027_contact_sheet.png
output:
  - experiments/cubism-v2-new-character-002/reports/model_edit_v10_generated_mouth_eye_clamp_preview/v10_visual_qa_codex_20260609.md
metric:
  - eye clamp: PASS
  - input EyeOpen 0.00 snapshot: ParamEyeLOpen 0.27, ParamEyeROpen 0.27
  - generated mouth closed/small/mid: improved over v8
  - generated mouth wide/full: REVISE, too large and teeth read as flat white band
decision: Keep v10 as the current generated-mouth diagnostic baseline, but do not promote mouth visual QA to final PASS. Eye clamp is accepted. Next mouth revision should reduce wide-open scale and improve teeth/tongue integration, or clamp MouthOpenY below the full wide state until a better keypose exists.
next_action: Either create v11 with a smaller natural wide-open keypose, or add a temporary MouthOpenY visual max below the full wide state for preview while preserving the v10 evidence.
```

## CUBISM-V2-NEW-CHARACTER-002-GENERATED-MOUTH-V12-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-GENERATED-MOUTH-V12-001
date: 2026-06-09
owner: Codex
status: PASS_DIAGNOSTIC_CANDIDATE_PRODUCTION_VISUAL_REVIEW_REQUIRED
hypothesis: Regenerating the mouth as one coherent four-state sheet, then reducing wide-open scale and clamping MouthOpenY, will avoid the v10 pasted/oversized wide-mouth failure while preserving the EyeOpen 0.27 success pattern.
input:
  - /Users/family/.codex/generated_images/019ea9dd-f119-74d1-824b-b6ce2f40def8/ig_0c778645cb880012016a27aa51b96081939f7ae2865fb52fd3.png
  - experiments/cubism-v2-new-character-002/model_edit_v10_generated_mouth_eye_clamp_preview/mini_cubism_diagnostic_project
output:
  - scripts/process_generated_smile_mouth_sheet_002.py
  - scripts/build_mini_cubism_v10_generated_mouth_eye_clamp_preview_002.py
  - experiments/cubism-v2-new-character-002/generated_mouth_v12/raw_outputs/smile_mouth_keypose_sheet_chromakey.png
  - experiments/cubism-v2-new-character-002/generated_mouth_v12/normalized_layers/mouth_smile_closed_gen.png
  - experiments/cubism-v2-new-character-002/generated_mouth_v12/normalized_layers/mouth_smile_small_open_gen.png
  - experiments/cubism-v2-new-character-002/generated_mouth_v12/normalized_layers/mouth_smile_mid_teeth_gen.png
  - experiments/cubism-v2-new-character-002/generated_mouth_v12/normalized_layers/mouth_smile_wide_teeth_tongue_gen.png
  - experiments/cubism-v2-new-character-002/generated_mouth_v12/reports/generated_smile_mouth_contact_sheet.png
  - experiments/cubism-v2-new-character-002/model_edit_v12_generated_mouth_eye_clamp_preview/mini_cubism_diagnostic_project
  - experiments/cubism-v2-new-character-002/model_edit_v12_generated_mouth_eye_clamp_preview/mini_cubism_diagnostic_project/reports/validation_report.json
  - experiments/cubism-v2-new-character-002/reports/model_edit_v12_generated_mouth_eye_clamp_preview/generated_mouth_open_packet/existing_mouth_open_contact_sheet.png
  - experiments/cubism-v2-new-character-002/reports/model_edit_v12_generated_mouth_eye_clamp_preview/eye_open_clamp_packet/eye_open_027_contact_sheet.png
  - experiments/cubism-v2-new-character-002/reports/model_edit_v12_generated_mouth_eye_clamp_preview/v12_visual_qa_codex_20260609.md
metric:
  - generated mouth layers: 4
  - generated mouth layer format: 2048 RGBA full-canvas
  - v12 validator: PASS
  - v12 parts: 21
  - v12 meshes: 21
  - v12 deformers: 6
  - v12 parameters: 5
  - v12 keyform_bindings: 7
  - EyeOpen min clamp: ParamEyeLOpen 0.27, ParamEyeROpen 0.27
  - MouthOpenY max clamp: 0.85
  - mouth full-open input: ParamMouthOpenY 1.00 -> snapshot 0.85
decision: Use v12 as the current Character 002 Mini Cubism diagnostic candidate. It is visibly better than v10/v11 because wide/full is smaller and less disruptive. Do not promote it as final production mouth art for real Cubism authoring without separate production visual review.
next_action: 주인님 visual QA on v12 at `http://127.0.0.1:8088/`; if accepted, continue local diagnostic motion/parameter testing from v12 while preserving v10/v11 as evidence.
```

## CUBISM-V2-NEW-CHARACTER-002-V13-SCALED-EYE-MOUTH-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V13-SCALED-EYE-MOUTH-001
date: 2026-06-09
owner: Codex
status: PASS_CURRENT_DIAGNOSTIC_CANDIDATE
hypothesis: Slightly reducing v12 eye and mouth part scale will preserve the best current expression set while improving face proportion.
input:
  - experiments/cubism-v2-new-character-002/model_edit_v12_generated_mouth_eye_clamp_preview/mini_cubism_diagnostic_project
output:
  - scripts/build_mini_cubism_v13_scale_tune_preview_002.py
  - experiments/cubism-v2-new-character-002/model_edit_v13_scaled_eye_mouth_preview/mini_cubism_diagnostic_project
  - experiments/cubism-v2-new-character-002/reports/model_edit_v13_scaled_eye_mouth_preview/mini_cubism_v13_scaled_eye_mouth_report.json
  - experiments/cubism-v2-new-character-002/model_edit_v13_scaled_eye_mouth_preview/mini_cubism_diagnostic_project/reports/validation_report.json
  - experiments/cubism-v2-new-character-002/reports/model_edit_v13_scaled_eye_mouth_preview/generated_mouth_open_packet/existing_mouth_open_contact_sheet.png
  - experiments/cubism-v2-new-character-002/reports/model_edit_v13_scaled_eye_mouth_preview/eye_open_clamp_packet/eye_open_027_contact_sheet.png
  - experiments/cubism-v2-new-character-002/reports/model_edit_v13_scaled_eye_mouth_preview/v13_visual_qa_codex_20260609.md
metric:
  - eye_scale: 0.94
  - mouth_scale: 0.92
  - validator: PASS
  - parts: 21
  - meshes: 21
  - deformers: 6
  - parameters: 5
  - keyform_bindings: 7
  - EyeOpen min clamp: 0.27
  - MouthOpenY max clamp: 0.85
decision: Use v13 as the current best Mini Cubism diagnostic candidate. It keeps the v12 expression set but improves proportions by making eyes and mouth slightly smaller.
next_action: 주인님 visual QA at `http://127.0.0.1:8080/`; if accepted, continue from v13 for local diagnostic motion and parameter testing.
```

## CUBISM-V2-NEW-CHARACTER-002-V14-EYE-DETAIL-INBETWEEN-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V14-EYE-DETAIL-INBETWEEN-001
date: 2026-06-09
owner: Codex
status: PASS_TECHNICAL_EYE_DETAIL_PACKET_READY_HUMAN_VISUAL_QA_REQUIRED
hypothesis: Preserve the v13 successful proportions, EyeOpen 0.27 clamp, and MouthOpenY 0.85 clamp while adding diagnostic iris/pupil/highlight parts and smoother EyeOpen in-between lid assets.
input:
  - experiments/cubism-v2-new-character-002/model_edit_v13_scaled_eye_mouth_preview/mini_cubism_diagnostic_project
output:
  - scripts/build_mini_cubism_v14_eye_detail_inbetween_preview_002.py
  - scripts/build_mini_cubism_v14_eye_detail_review_packet_002.py
  - experiments/cubism-v2-new-character-002/model_edit_v14_eye_detail_inbetween_preview/mini_cubism_diagnostic_project
  - experiments/cubism-v2-new-character-002/reports/model_edit_v14_eye_detail_inbetween_preview/mini_cubism_v14_eye_detail_inbetween_report.json
  - experiments/cubism-v2-new-character-002/model_edit_v14_eye_detail_inbetween_preview/mini_cubism_diagnostic_project/reports/validation_report.json
  - experiments/cubism-v2-new-character-002/reports/model_edit_v14_eye_detail_inbetween_preview/eye_detail_review_packet/v14_eye_detail_review_report.json
  - experiments/cubism-v2-new-character-002/reports/model_edit_v14_eye_detail_inbetween_preview/eye_detail_review_packet/v14_eye_detail_review_contact_sheet.png
metric:
  - validator: PASS
  - parts: 35
  - meshes: 35
  - deformers: 6
  - parameters: 7
  - keyform_bindings: 31
  - EyeOpen min clamp: 0.27
  - MouthOpenY max clamp: 0.85
  - ParamEyeBallX/Y: added
  - derived eye detail parts: eye_L/R_white, eye_L/R_iris, eye_L/R_pupil, eye_L/R_highlight
  - in-between lid parts: eye_L/R_lid_inbetween_080, eye_L/R_lid_inbetween_065, eye_L/R_lid_inbetween_038
  - review packet technical_nonblank: true
  - review packet eye_ball_moved_numeric: true
  - review packet eye_close_changed_numeric: true
decision: Use v14 as the current eye-detail diagnostic candidate only if 주인님 accepts visual QA. The iris/pupil/highlight split is derived from baked v13 `eye_open` art, so it proves local Mini Cubism parameter behavior but does not replace production clean eye material authoring.
next_action: Run v14 preview at `http://127.0.0.1:8080/` for 주인님 review. If accepted, record the eye-detail extension as the current diagnostic success pattern; if rejected, fall back to v13 and regenerate true separated eye assets.
```

## CUBISM-V2-NEW-CHARACTER-002-V15-EYE-NOSE-POSITION-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V15-EYE-NOSE-POSITION-001
date: 2026-06-09
owner: Codex
status: ACTIVE_REVIEW_CANDIDATE_AFTER_ROLLBACK
hypothesis: Fix v14 visual review issues by making iris/pupil/highlight move together, shifting the eye group upward, and restoring a subtle nose detail without adding a rectangular skin patch.
input:
  - experiments/cubism-v2-new-character-002/model_edit_v14_eye_detail_inbetween_preview/mini_cubism_diagnostic_project
  - experiments/cubism-v2-new-character-002/reports/overlay_qa/source_front_2048.png
output:
  - scripts/build_mini_cubism_v15_eye_nose_position_preview_002.py
  - experiments/cubism-v2-new-character-002/model_edit_v15_eye_nose_position_preview/mini_cubism_diagnostic_project
  - experiments/cubism-v2-new-character-002/reports/model_edit_v15_eye_nose_position_preview/mini_cubism_v15_eye_nose_position_report.json
  - experiments/cubism-v2-new-character-002/model_edit_v15_eye_nose_position_preview/mini_cubism_diagnostic_project/reports/validation_report.json
  - experiments/cubism-v2-new-character-002/reports/model_edit_v15_eye_nose_position_preview/eye_detail_review_packet/v15_eye_nose_position_contact_sheet.png
metric:
  - validator: PASS
  - parts: 36
  - meshes: 36
  - deformers: 6
  - parameters: 7
  - keyform_bindings: 31
  - EyeOpen min clamp: 0.27
  - MouthOpenY max clamp: 0.85
  - eye_shift_y: -18
  - EyeBallX/Y movement: iris, pupil, and highlight all use identical X 7.5 / Y 4.5 deltas
  - nose_detail bbox: [1001, 757, 35, 48]
decision: Use v15 as the active review candidate at `http://127.0.0.1:8080/`. It fixes the iris/pupil cohesion issue and raises eye placement. The nose is restored subtly; if 주인님 wants it more visible, tune `nose_detail` alpha rather than changing the whole face base.
next_action: 주인님 visual QA on v15. Check iris/pupil cohesion, eye height, nose visibility, and whether the derived eye-white boundary is acceptable.
```

## CUBISM-V2-NEW-CHARACTER-002-V16-WHOLE-EYEBALL-REJECTED-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V16-WHOLE-EYEBALL-REJECTED-001
date: 2026-06-09
owner: Codex
status: REVISE_DO_NOT_ACTIVATE
hypothesis: Moving `eye_L/R_white` together with iris/pupil/highlight might satisfy the request for whole-eyeball movement.
input:
  - experiments/cubism-v2-new-character-002/model_edit_v15_eye_nose_position_preview/mini_cubism_diagnostic_project
output:
  - scripts/build_mini_cubism_v16_whole_eyeball_preview_002.py
  - experiments/cubism-v2-new-character-002/model_edit_v16_whole_eyeball_preview/mini_cubism_diagnostic_project
  - experiments/cubism-v2-new-character-002/reports/model_edit_v16_whole_eyeball_preview/mini_cubism_v16_whole_eyeball_report.json
  - experiments/cubism-v2-new-character-002/model_edit_v16_whole_eyeball_preview/mini_cubism_diagnostic_project/reports/validation_report.json
metric:
  - validator: PASS
  - parts: 36
  - meshes: 36
  - parameters: 7
  - keyform_bindings: 39
decision: Reject as active direction. 주인님 clarified that the white of the eye should not move. Use v15 instead: eye white stays fixed, while iris/pupil/highlight move together with identical deltas.
next_action: Keep `http://127.0.0.1:8080/` on v15 unless a new v17 tuning pass is needed for iris/pupil movement strength or nose alpha.
```

## CUBISM-V2-NEW-CHARACTER-002-V18-CLEAN-WHITE-CENTER-IRIS-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V18-CLEAN-WHITE-CENTER-IRIS-001
date: 2026-06-09
owner: Codex
status: REVISE_ROLLED_BACK_DO_NOT_ACTIVATE
hypothesis: The v15 issue where only part of the original eyeball appears to move comes from baked iris residue in fixed `eye_L/R_white`; rebuild fixed white with stronger iris removal and rebuild moving iris/pupil/highlight around the centered iris only.
input:
  - experiments/cubism-v2-new-character-002/model_edit_v15_eye_nose_position_preview/mini_cubism_diagnostic_project
output:
  - scripts/build_mini_cubism_v17_clean_white_full_iris_preview_002.py
  - scripts/build_mini_cubism_v18_clean_white_center_iris_preview_002.py
  - experiments/cubism-v2-new-character-002/model_edit_v17_clean_white_full_iris_preview/mini_cubism_diagnostic_project
  - experiments/cubism-v2-new-character-002/model_edit_v18_clean_white_center_iris_preview/mini_cubism_diagnostic_project
  - experiments/cubism-v2-new-character-002/reports/model_edit_v18_clean_white_center_iris_preview/mini_cubism_v18_clean_white_center_iris_report.json
  - experiments/cubism-v2-new-character-002/model_edit_v18_clean_white_center_iris_preview/mini_cubism_diagnostic_project/reports/validation_report.json
  - experiments/cubism-v2-new-character-002/reports/model_edit_v18_clean_white_center_iris_preview/eye_detail_review_packet/v18_clean_white_center_iris_contact_sheet.png
metric:
  - validator: PASS
  - parts: 36
  - meshes: 36
  - deformers: 6
  - parameters: 7
  - keyform_bindings: 31
  - eye_L/R_white EyeBall bindings: 0
  - iris/pupil/highlight EyeBall bindings: 4 each, identical deltas X 7.5 / Y 4.5
decision: Roll back from v18 to v15. v18 is technically valid but still reads as mask surgery on baked eye art, not a clean eye asset solution.
next_action: Keep `http://127.0.0.1:8080/` on v15. The next durable fix should generate true eye assets: fixed clean white/socket plus a coherent moving iris+pupil+highlight asset generated together from the same source.
```

## CUBISM-V2-NEW-CHARACTER-002-V19-GENERATED-EYE-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V19-GENERATED-EYE-001
date: 2026-06-09
owner: Codex
status: ACTIVE_REVIEW_CANDIDATE_HUMAN_VISUAL_QA_REQUIRED
hypothesis: Generating true eye assets should solve the baked-eye residue problem better than mask surgery: fixed clean white/socket assets stay still while coherent iris+pupil+highlight assets move as one unit.
input:
  - experiments/cubism-v2-new-character-002/model_edit_v15_eye_nose_position_preview/mini_cubism_diagnostic_project
  - experiments/cubism-v2-new-character-002/reports/model_edit_v19_generated_eye_packet/v19_eye_generation_reference_packet.png
  - experiments/cubism-v2-new-character-002/generated_eye_v19/raw_outputs/eye_asset_sheet_chromakey.png
output:
  - scripts/process_generated_eye_sheet_v19_002.py
  - scripts/build_mini_cubism_v19_generated_eye_preview_002.py
  - experiments/cubism-v2-new-character-002/generated_eye_v19/normalized_layers/eye_L_white.png
  - experiments/cubism-v2-new-character-002/generated_eye_v19/normalized_layers/eye_R_white.png
  - experiments/cubism-v2-new-character-002/generated_eye_v19/normalized_layers/eye_L_iris.png
  - experiments/cubism-v2-new-character-002/generated_eye_v19/normalized_layers/eye_R_iris.png
  - experiments/cubism-v2-new-character-002/generated_eye_v19/reports/generated_eye_v19_contact_sheet.png
  - experiments/cubism-v2-new-character-002/model_edit_v19_generated_eye_preview/mini_cubism_diagnostic_project
  - experiments/cubism-v2-new-character-002/model_edit_v19_generated_eye_preview/mini_cubism_diagnostic_project/reports/validation_report.json
  - experiments/cubism-v2-new-character-002/reports/model_edit_v19_generated_eye_preview/eye_detail_review_packet/v19_generated_eye_contact_sheet.png
metric:
  - validator: PASS
  - parts: 36
  - meshes: 36
  - deformers: 6
  - parameters: 7
  - keyform_bindings: 15
  - fixed eye whites: eye_L_white, eye_R_white
  - moving coherent eye details: eye_L_iris, eye_R_iris
  - old split pupil/highlight: hidden
decision: Use v19 as the active review candidate at `http://127.0.0.1:8080/`. It solves the baked-eye partial-movement problem structurally, but human visual QA is still required because the generated eye style is cleaner/sharper than the original.
next_action: 주인님 visual QA on v19. Check whether the new generated eyes match the character style and whether EyeBallX/Y reads as one coherent moving eyeball detail.
```

## CUBISM-V2-NEW-CHARACTER-002-V20-MANUAL-EYE-ANCHOR-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V20-MANUAL-EYE-ANCHOR-001
date: 2026-06-09
owner: Codex
status: ACTIVE_REVIEW_CANDIDATE_HUMAN_VISUAL_QA_REQUIRED
hypothesis: Applying 주인님-saved drag/zoom eye-detail anchors to the v19 generated-eye candidate will reduce the crossed-eye visual mismatch without regenerating the eye art.
input:
  - experiments/cubism-v2-new-character-002/model_edit_v19_generated_eye_preview/mini_cubism_diagnostic_project
  - experiments/cubism-v2-new-character-002/reports/model_edit_v19_generated_eye_preview/manual_eye_detail_anchor_v1/manual_eye_detail_anchor_overrides.json
output:
  - scripts/run_v19_eye_detail_anchor_editor_002.py
  - scripts/build_mini_cubism_v20_manual_eye_anchor_preview_002.py
  - mini_cubism_app/src/app.js
  - mini_cubism_app/src/styles.css
  - experiments/cubism-v2-new-character-002/model_edit_v20_manual_eye_anchor_preview/mini_cubism_diagnostic_project
  - experiments/cubism-v2-new-character-002/reports/model_edit_v20_manual_eye_anchor_preview/mini_cubism_v20_manual_eye_anchor_report.json
  - experiments/cubism-v2-new-character-002/model_edit_v20_manual_eye_anchor_preview/mini_cubism_diagnostic_project/reports/validation_report.json
  - experiments/cubism-v2-new-character-002/reports/model_edit_v20_manual_eye_anchor_preview/eye_detail_review_packet/v20_manual_eye_anchor_report.json
  - experiments/cubism-v2-new-character-002/reports/model_edit_v20_manual_eye_anchor_preview/eye_detail_review_packet/v20_manual_eye_anchor_contact_sheet.png
  - /Users/family/.codex/skills/vtube-manual-part-anchor-correction/SKILL.md
metric:
  - validator: PASS
  - parts: 36
  - meshes: 36
  - deformers: 6
  - parameters: 7
  - keyform_bindings: 15
  - contact_sheet_status: PASS_TECHNICAL_EYE_DETAIL_PACKET_READY
  - human_visual_qa: REQUIRED
  - L_current_center: [884.14, 665.24]
  - L_target_anchor: [898, 679]
  - L_applied_delta_xy: [14, 14]
  - R_current_center: [1166.05, 665.25]
  - R_target_anchor: [1153, 679]
  - R_applied_delta_xy: [-13, 14]
  - 8080_model_view_zoom_control: present
  - 8080_default_canvas_css_width: 860px at 1280x900 smoke viewport
decision: Use v20 as the active manual-anchor diagnostic review candidate at `http://127.0.0.1:8080/`. This records the reusable part-correction pattern: drag/zoom editor saves anchors, next build applies full-canvas RGBA shifts, validator/contact sheet gate before activation.
next_action: 주인님 visual QA on v20. Check centered gaze, EyeBallX/Y motion, EyeOpen in-betweens, and whether further manual anchor correction is needed before changing mouth or hair.
```

## CUBISM-V2-NEW-CHARACTER-002-V21-SUPPORTED-RIG-SMOKE-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V21-SUPPORTED-RIG-SMOKE-001
date: 2026-06-09
owner: Codex
status: PASS_SUPPORTED_CONTROL_MINI_CUBISM_RIG_SMOKE_NOT_REAL_CUBISM_AUTHORING
hypothesis: v20 can proceed to a Mini Cubism rig smoke if unsupported contract-only HairFront is hidden from the active preview and the pose sweep uses automation parameter writes instead of UI slider sequencing.
input:
  - experiments/cubism-v2-new-character-002/model_edit_v20_manual_eye_anchor_preview/mini_cubism_diagnostic_project
  - experiments/cubism-v2-new-character-002/reports/model_edit_v20_manual_eye_anchor_preview/rig_readiness_pose_sweep_v2/reports/pose_sweep_report.json
output:
  - scripts/run_mini_cubism_pose_sweep.py
  - scripts/build_mini_cubism_v20_rig_readiness_report_002.py
  - scripts/build_mini_cubism_v21_supported_rig_smoke_preview_002.py
  - mini_cubism_app/src/app.js
  - experiments/cubism-v2-new-character-002/reports/model_edit_v20_manual_eye_anchor_preview/rig_readiness_v1/v20_rig_readiness_report.json
  - experiments/cubism-v2-new-character-002/model_edit_v21_supported_rig_smoke_preview/mini_cubism_diagnostic_project
  - experiments/cubism-v2-new-character-002/reports/model_edit_v21_supported_rig_smoke_preview/mini_cubism_v21_supported_rig_smoke_report.json
  - experiments/cubism-v2-new-character-002/model_edit_v21_supported_rig_smoke_preview/mini_cubism_diagnostic_project/reports/validation_report.json
  - experiments/cubism-v2-new-character-002/reports/model_edit_v21_supported_rig_smoke_preview/supported_pose_sweep_v2/reports/pose_sweep_report.json
metric:
  - v20_fixed_pose_sweep_status: PASS
  - v20_fixed_pose_sweep_score: 201
  - v21_validator: PASS
  - v21_parts: 36
  - v21_meshes: 36
  - v21_deformers: 6
  - v21_parameters: 7
  - v21_keyform_bindings: 15
  - v21_supported_pose_sweep_status: PASS
  - v21_supported_pose_sweep_score: 180
  - v21_supported_pose_sweep_pass_rows: 12
  - v21_supported_pose_sweep_revise_rows: 0
  - active_controls: [ParamAngleX, ParamEyeBallX, ParamEyeBallY, ParamEyeLOpen, ParamEyeROpen, ParamMouthOpenY]
  - hidden_unsupported_controls: [ParamHairFront]
decision: Use v21 as the active supported-control Mini Cubism rig smoke at `http://127.0.0.1:8080/`. `ParamHairFront` remains in the project for validator compatibility but is hidden from the preview because no independent front hair child parts exist. This is still local diagnostic evidence, not final Cubism `.cmo3/.moc3` authoring.
next_action: 주인님 visual QA on v21. If accepted, the next production step is front-hair part generation/separation or real Cubism authoring prep from finalized production layers; do not claim final rig success from v21 alone.
```

## CUBISM-V2-NEW-CHARACTER-002-V21-SUCCESS-PATTERN-REPLAY-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V21-SUCCESS-PATTERN-REPLAY-001
date: 2026-06-09
owner: Codex
status: PASS_REPRODUCED_SUCCESS_PATTERN_TO_V21_SUPPORTED_RIG_SMOKE
hypothesis: The current success pattern can be replayed end-to-end from saved v19 eye anchors through v20 manual-eye anchor correction and v21 supported-control rig smoke.
input:
  - experiments/cubism-v2-new-character-002/reports/model_edit_v19_generated_eye_preview/manual_eye_detail_anchor_v1/manual_eye_detail_anchor_overrides.json
  - experiments/cubism-v2-new-character-002/model_edit_v19_generated_eye_preview/mini_cubism_diagnostic_project
output:
  - scripts/build_mini_cubism_v20_manual_eye_anchor_preview_002.py
  - scripts/build_mini_cubism_v20_rig_readiness_report_002.py
  - scripts/build_mini_cubism_v21_supported_rig_smoke_preview_002.py
  - scripts/run_mini_cubism_pose_sweep.py
  - scripts/build_mini_cubism_pose_sweep_contact_sheet.py
  - experiments/cubism-v2-new-character-002/reports/model_edit_v20_manual_eye_anchor_preview/eye_detail_review_packet_replay_v1/v14_eye_detail_review_contact_sheet.png
  - experiments/cubism-v2-new-character-002/reports/model_edit_v20_manual_eye_anchor_preview/rig_readiness_pose_sweep_replay_v1/reports/pose_sweep_report.json
  - experiments/cubism-v2-new-character-002/reports/model_edit_v20_manual_eye_anchor_preview/rig_readiness_replay_v1/v20_rig_readiness_report.json
  - experiments/cubism-v2-new-character-002/reports/model_edit_v21_supported_rig_smoke_preview/supported_pose_sweep_clean_replay_v2/reports/pose_sweep_report.json
  - experiments/cubism-v2-new-character-002/reports/model_edit_v21_supported_rig_smoke_preview/supported_pose_sweep_clean_replay_v2/v21_supported_pose_sweep_clean_contact_sheet.png
  - experiments/cubism-v2-new-character-002/reports/model_edit_v21_supported_rig_smoke_preview/success_pattern_replay_v1/success_pattern_replay_report.json
metric:
  - v20_anchor_replay: V20_MANUAL_EYE_ANCHOR_READY_FOR_VALIDATION
  - v20_validator: PASS
  - v20_eye_detail_replay: PASS_TECHNICAL_EYE_DETAIL_PACKET_READY
  - v20_pose_sweep_replay: PASS
  - v20_pose_sweep_replay_score: 201
  - v20_rig_readiness_replay: READY_FOR_V21_SUPPORTED_CONTROL_RIG_SMOKE_WITH_HAIR_EXCLUDED
  - v21_validator: PASS
  - v21_clean_pose_sweep_replay: PASS
  - v21_clean_pose_sweep_replay_score: 175
  - v21_clean_pose_sweep_rows: {PASS: 12, REVISE: 0, FAIL: 0}
  - active_controls: [ParamAngleX, ParamEyeBallX, ParamEyeBallY, ParamEyeLOpen, ParamEyeROpen, ParamMouthOpenY]
  - hidden_unsupported_controls: [ParamHairFront]
decision: The v20 -> v21 success pattern is repeatable and now has a clean canvas-only review contact sheet. Keep v21 as the active supported-control Mini Cubism rig smoke. This remains diagnostic Mini Cubism evidence, not final real Cubism authoring.
next_action: 주인님 visual QA on the clean v21 contact sheet and 8080 preview. If accepted, choose between front-hair part generation/separation and real Cubism authoring prep.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-64PART-GENERATION-SPEC-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-64PART-GENERATION-SPEC-001
date: 2026-06-09
owner: Codex
status: PASS_SPEC_READY_FOR_IMAGE_GENERATION_PLANNING
hypothesis: Before regenerating a full 64-part character pack, the v21 diagnostic success pattern and the known visual failure patterns can be made explicit enough to prevent repeating late patch cleanup, eye drift, pasted mouth internals, and fake HairFront controls.
input:
  - docs/status/PROJECT-STATUS.md
  - docs/ref/CUBISM-V2-MATERIAL-PACK-FIRST-GENERATION.md
  - experiments/reference-model-structure-001/reports/cubism_v2_new_model_v2_standard_part_spec.json
  - experiments/cubism-v2-new-character-002/reports/model_edit_v21_supported_rig_smoke_preview/success_pattern_replay_v1/success_pattern_replay_report.md
output:
  - scripts/build_cubism_v2_64part_generation_spec_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_64part_generation_spec/v22_64part_generation_spec.json
  - experiments/cubism-v2-new-character-002/reports/v22_64part_generation_spec/v22_64part_generation_spec.md
  - /Users/family/jason/jason-agent-harness-template/harnesses/vtube-character-002-v22-64part-generation.md
metric:
  - part_count: 64
  - group_counts: {body: 10, face_base: 8, eye_L: 8, eye_R: 8, brow: 2, mouth: 8, hair: 16, clothing: 4}
  - no_duplicate_part_ids: true
  - has_real_hairfront_scope: true
  - has_eye_detail_split_scope: true
  - has_mouth_internal_scope: true
  - quality_gates: [G0_source_identity, G1_64part_completeness, G2_full_canvas_rgba, G3_technical_validators, G4_contact_sheet_visual_qa, G5_overlay_qa, G6_manual_anchor_correction, G7_mini_cubism_diagnostic, G8_real_cubism_authoring_readiness]
  - failure_patterns: [late_patch_clean_base, moving_eye_white, split_eye_detail_drift, oversized_or_centered_mouth, pasted_mouth_internals, fake_hairfront_slider, validator_only_promotion, mini_cubism_as_real_cubism]
decision: Use v22 as the gate spec before full 64-part image generation. This distinguishes success from failure by source identity, clean-base generation, eye detail anchor locking, coordinated mouth internals, real front hair child parts, and separated evidence gates. It is a generation/readiness spec only; no new images or Cubism authoring were produced by this step.
next_action: Generate the v22 full 64-part prompt/input packet from this spec, then run G0 source/style review before expanding into normalized 64-part RGBA layers.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-GENERATION-INPUT-PACKET-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-GENERATION-INPUT-PACKET-001
date: 2026-06-09
owner: Codex
status: PASS_READY_FOR_G0_SOURCE_STYLE_REVIEW
hypothesis: The v22 64-part generation spec can be converted into concrete image-generation prompts and a G0 review checklist without starting image generation prematurely.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_64part_generation_spec/v22_64part_generation_spec.json
  - experiments/reference-model-structure-001/reports/cubism_v2_character_prompt_template.json
output:
  - scripts/build_cubism_v2_64part_generation_input_packet_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_64part_generation_input_packet/v22_64part_generation_input_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_64part_generation_input_packet/v22_64part_generation_input_packet.md
  - experiments/cubism-v2-new-character-002/reports/v22_64part_generation_input_packet/v22_g0_source_style_review_checklist.md
metric:
  - batch_count: 6
  - batches: [B0_source_identity, B1_clean_base_underpaint, B2_eye_pack, B3_mouth_pack, B4_hair_pack, B5_body_clothing_pack]
  - has_b0_source_prompt: true
  - has_eye_prompt: true
  - has_mouth_prompt: true
  - has_hair_prompt: true
  - has_g0_checklist: true
  - part_count: 64
  - self_review: PASS
decision: The next human gate is G0 source/style review. Do not generate all 64 normalized layers until 주인님 accepts the source identity/style as production-worthy or asks to regenerate it.
next_action: Use the B0 source prompt and G0 checklist to select or regenerate the source/front style, then proceed to B1-B5 only after G0 PASS.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G0-EXISTING-SOURCE-REVIEW-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G0-EXISTING-SOURCE-REVIEW-001
date: 2026-06-09
owner: Codex
status: PASS_READY_FOR_64PART_GENERATION
hypothesis: The existing character-002 source/front can pass the v22 G0 source identity and style gate without regenerating a B0 source image.
input:
  - experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png
  - experiments/cubism-v2-new-character-002/reports/v22_64part_generation_input_packet/v22_64part_generation_input_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_64part_generation_input_packet/v22_g0_source_style_review_checklist.md
output:
  - scripts/build_cubism_v2_g0_existing_source_review_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_64part_generation_input_packet/v22_g0_existing_source_review.json
  - experiments/cubism-v2-new-character-002/reports/v22_64part_generation_input_packet/v22_g0_existing_source_review.md
metric:
  - source_size: 1254x1254
  - image_generation: NOT_RUN
  - allowed_verdict: true
  - checklist_count: 10
  - review_item_count: 10
  - all_items_have_valid_status: true
  - self_review: PASS
decision: Existing `new_character_002_source_front.raw.png` passes G0 source/style review and unlocks B1-B5 preparation. This is G0 source acceptance only, not 64-part material promotion or real Cubism rig success.
next_action: Begin B1-B5 generation planning from the v22 packet, starting with clean bases and underpaints so baked eye/mouth pixels are not patched late. Keep technical PNG validation, visual QA, Mini Cubism diagnostics, and real Cubism CMO3/deformer/keyform authoring as separate gates.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B1-CLEAN-BASE-REFERENCE-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B1-CLEAN-BASE-REFERENCE-001
date: 2026-06-09
owner: Codex
status: B1_RAW_CLEAN_BASE_REFERENCE_READY_FOR_VISUAL_QA
hypothesis: After G0 source/style PASS, a same-character B1 clean-base reference can be generated that removes open eyes, iris/pupil/white/lash residue, and the mouth line without repeating the previous oval/rectangular skin-patch failure.
input:
  - experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png
  - experiments/cubism-v2-new-character-002/reports/v22_64part_generation_input_packet/v22_64part_generation_input_packet.json
output:
  - scripts/build_cubism_v2_b1_clean_base_review_002.py
  - experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/raw_outputs/b1_clean_base_underpaint_reference_001.png
  - experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_clean_base_review.json
  - experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_clean_base_review.md
  - experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_clean_base_contact_sheet.png
metric:
  - imagegen_mode: built_in_image_gen
  - raw_size: 1254x1254
  - same_size_as_source: true
  - roi_count: 3
  - roi_feature_residue_reduced: true
  - eye_L_feature_roi: {source_feature_density: 0.458381, b1_feature_density: 0.22251, status: REVIEW_VISUALLY}
  - eye_R_feature_roi: {source_feature_density: 0.408421, b1_feature_density: 0.157004, status: PASS_REDUCED_FEATURE_RESIDUE}
  - mouth_feature_roi: {source_feature_density: 0.004142, b1_feature_density: 0.0, status: PASS_REDUCED_FEATURE_RESIDUE}
  - self_review: PASS
decision: Keep this as the v22 B1 raw clean-base/underpaint reference candidate. It is visually stronger than the previous patch-style clean-base attempts, but it is not yet separated B1 output layers or material PASS.
next_action: Split/normalize the B1 expected outputs into full-canvas RGBA layers, then run contact-sheet and overlay QA before promoting B1 or generating B2/B3/B4/B5 production material.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B1-LAYER-PACK-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B1-LAYER-PACK-001
date: 2026-06-09
owner: Codex
status: B1_CODEX_VISUAL_QA_PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED
hypothesis: The B1 raw clean-base reference can be split into all 11 B1 expected outputs as full-canvas 2048 RGBA candidates without missing or empty layers, while still keeping visual/human PASS separate.
input:
  - experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/raw_outputs/b1_clean_base_underpaint_reference_001.png
  - experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_clean_base_review.json
output:
  - scripts/build_cubism_v2_b1_clean_base_layer_pack_002.py
  - scripts/build_cubism_v2_b1_visual_qa_002.py
  - experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/b1_clean_base_underpaint_reference_001_2048.png
  - experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/normalized_layers/face_base.png
  - experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/normalized_layers/face_underpaint_L.png
  - experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/normalized_layers/face_underpaint_R.png
  - experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/normalized_layers/eye_L_underpaint.png
  - experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/normalized_layers/eye_R_underpaint.png
  - experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/normalized_layers/mouth_base_clean_reference.png
  - experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/normalized_layers/body_underpaint.png
  - experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/normalized_layers/neck_shadow_underpaint.png
  - experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/normalized_layers/arm_L_underpaint.png
  - experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/normalized_layers/arm_R_underpaint.png
  - experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/normalized_layers/hair_back_underpaint.png
  - experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_layer_pack_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_layer_pack_report.md
  - experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_layer_pack_contact_sheet.png
  - experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_layer_pack_overlay_qa.png
  - experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_visual_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_visual_qa_report.md
metric:
  - expected_output_count: 11
  - generated_output_count: 11
  - missing_output_count: 0
  - empty_output_count: 0
  - canvas: 2048x2048
  - layer_mode: RGBA
  - layer_pack_self_review: PASS
  - codex_visual_qa: PASS_CANDIDATE
  - human_visual_review: REQUIRED
decision: Keep B1 as the current clean-base/underpaint candidate. It is good enough to guide B2/B3 prompt inputs, but it is not B1 final material PASS because automatic masks remain coarse and 주인님 human visual QA is still required.
next_action: Generate B2 eye pack using fixed eye whites and anchor-locked iris/pupil/highlight while preserving EyeOpen 0.27 as the natural close threshold. Keep B1 available as the clean-base/underpaint input and do not activate Mini Cubism diagnostic from B1 alone.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B2-EYE-PACK-RAW-CANDIDATE-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B2-EYE-PACK-RAW-CANDIDATE-001
date: 2026-06-09
owner: Codex
status: B2_RAW_EYE_PACK_CANDIDATE_READY_FOR_EXTRACTION_HUMAN_REVIEW_REQUIRED
hypothesis: After 주인님 instructed not to use existing eye assets, a newly generated B2 eye-pack raw reference can preserve character-002 eye style while keeping v19/v20/v21 eye PNGs explicitly forbidden as B2 inputs.
input:
  - experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png
  - experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/raw_outputs/b1_clean_base_underpaint_reference_001.png
  - experiments/cubism-v2-new-character-002/reports/v22_64part_generation_input_packet/v22_64part_generation_input_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_visual_qa_report.json
forbidden_input:
  - experiments/cubism-v2-new-character-002/generated_eye_v19
  - experiments/cubism-v2-new-character-002/model_edit_v14_eye_detail_inbetween_preview/mini_cubism_diagnostic_project/parts
  - experiments/cubism-v2-new-character-002/model_edit_v15_eye_nose_position_preview/mini_cubism_diagnostic_project/parts
  - experiments/cubism-v2-new-character-002/model_edit_v19_generated_eye_preview/mini_cubism_diagnostic_project/parts
  - experiments/cubism-v2-new-character-002/model_edit_v20_manual_eye_anchor_preview/mini_cubism_diagnostic_project/parts
  - experiments/cubism-v2-new-character-002/model_edit_v21_supported_rig_smoke_preview/mini_cubism_diagnostic_project/parts
output:
  - scripts/build_cubism_v2_b2_eye_pack_review_002.py
  - experiments/cubism-v2-new-character-002/v22_b2_eye_pack/raw_outputs/b2_eye_pack_reference_001.png
  - experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_eye_pack_review.json
  - experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_eye_pack_review.md
  - experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_eye_pack_contact_sheet.png
metric:
  - imagegen_mode: built_in_image_gen
  - raw_size: 1254x1254
  - raw_mode: RGB
  - allowed_input_count: 4
  - forbidden_existing_eye_asset_count: 6
  - visual_check_count: 6
  - same_character_eye_style: PASS_CANDIDATE
  - eyeopen_keypose_rows: PASS_CANDIDATE
  - fixed_white_and_locked_iris_cluster_scope: PASS_CANDIDATE
  - extraction_readiness: REVISE_BEFORE_LAYER_PROMOTION
  - human_visual_review: REQUIRED
  - self_review: PASS
decision: Keep this as the v22 B2 newly generated eye-pack raw candidate. It can feed B2 extraction planning, but it is not yet separated full-canvas RGBA eye material and does not unlock Mini Cubism or real Cubism success claims.
next_action: Extract/normalize B2 components into full-canvas RGBA candidates, run contact-sheet and overlay QA against the G0 source and B1 sockets, and regenerate B2 if fixed whites or iris/pupil/highlight locking fail instead of reusing old v19/v20/v21 eye assets.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B2-EYE-LAYER-PACK-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B2-EYE-LAYER-PACK-001
date: 2026-06-09
owner: Codex
status: B2_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED
hypothesis: The newly generated B2 raw eye sheet can be extracted into the 18 expected v22 B2 outputs as full-canvas RGBA candidates while preserving the no-existing-eye-assets constraint.
input:
  - experiments/cubism-v2-new-character-002/v22_b2_eye_pack/raw_outputs/b2_eye_pack_reference_001.png
  - experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_eye_pack_review.json
forbidden_input:
  - experiments/cubism-v2-new-character-002/generated_eye_v19
  - experiments/cubism-v2-new-character-002/model_edit_v14_eye_detail_inbetween_preview/mini_cubism_diagnostic_project/parts
  - experiments/cubism-v2-new-character-002/model_edit_v15_eye_nose_position_preview/mini_cubism_diagnostic_project/parts
  - experiments/cubism-v2-new-character-002/model_edit_v19_generated_eye_preview/mini_cubism_diagnostic_project/parts
  - experiments/cubism-v2-new-character-002/model_edit_v20_manual_eye_anchor_preview/mini_cubism_diagnostic_project/parts
  - experiments/cubism-v2-new-character-002/model_edit_v21_supported_rig_smoke_preview/mini_cubism_diagnostic_project/parts
output:
  - scripts/build_cubism_v2_b2_eye_layer_pack_002.py
  - experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_L_white.png
  - experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_L_iris.png
  - experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_L_pupil.png
  - experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_L_highlight.png
  - experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_L_upper_lash.png
  - experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_L_lower_lash.png
  - experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_L_closed_lid.png
  - experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_R_white.png
  - experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_R_iris.png
  - experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_R_pupil.png
  - experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_R_highlight.png
  - experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_R_upper_lash.png
  - experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_R_lower_lash.png
  - experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_R_closed_lid.png
  - experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_open_reference.png
  - experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_half_closed_reference.png
  - experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_mostly_closed_reference.png
  - experiments/cubism-v2-new-character-002/v22_b2_eye_pack/normalized_layers/eye_closed_reference.png
  - experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_layer_pack_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_layer_pack_report.md
  - experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_layer_pack_contact_sheet.png
  - experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_layer_pack_overlay_qa.png
metric:
  - expected_output_count: 18
  - generated_output_count: 18
  - missing_output_count: 0
  - empty_output_count: 0
  - all_layers_rgba: true
  - all_layers_2048: true
  - forbidden_existing_eye_asset_count: 6
  - forbidden_assets_not_output_path: true
  - left_anchor_status: PASS_ANCHOR_LOCKED_SAME_TARGET
  - right_anchor_status: PASS_ANCHOR_LOCKED_SAME_TARGET
  - human_visual_review: REQUIRED
  - self_review: PASS
decision: Keep this B2 extraction as a full-canvas RGBA candidate only. It preserves the new generated eye sheet and same-target iris/pupil/highlight anchors, but visual overlay and 주인님 review are required before B2 material PASS.
next_action: Run overlay QA against the B1 clean-base sockets; if visual QA accepts B2, continue to B3 mouth-pack generation without using existing mouth assets unless 주인님 explicitly allows them; if B2 eye detail drifts, regenerate a new B2 sheet instead of importing v19/v20/v21 eye PNGs.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B2-OVERLAY-QA-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B2-OVERLAY-QA-001
date: 2026-06-09
owner: Codex
status: B2_CODEX_OVERLAY_QA_PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED
hypothesis: The newly extracted B2 eye layers can be overlaid on the B1 clean-base sockets well enough to continue B3 generation, while keeping B2 material PASS blocked on human visual review and possible manual anchor correction.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_layer_pack_report.json
  - experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/raw_outputs/b1_clean_base_underpaint_reference_001.png
output:
  - scripts/build_cubism_v2_b2_overlay_qa_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_overlay_qa_report.md
  - experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_overlay_qa_on_b1_clean_base.png
metric:
  - b2_layer_pack_status: B2_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED
  - b2_layer_self_review_status: PASS
  - check_count: 6
  - open_eye_socket_alignment: PASS_CANDIDATE
  - fixed_white_policy_visible: PASS_CANDIDATE
  - iris_pupil_highlight_anchor_lock: PASS_CANDIDATE
  - closed_lid_overlay: PASS_CANDIDATE
  - matte_and_style_risk: REVISE_BEFORE_FINAL_MATERIAL_PASS
  - human_visual_review: REQUIRED
  - self_review: PASS
decision: B2 is acceptable as a candidate input for continuing B3 generation, but it is not final material PASS. Keep visual/human QA, Mini Cubism diagnostics, and real Cubism authoring separate.
next_action: Generate a new B3 mouth-pack raw candidate without using existing v10/v12/v13 mouth assets; keep B2 layer-pack available for later manual anchor correction if 주인님 rejects the overlay scale or socket feel.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B3-MOUTH-PACK-RAW-CANDIDATE-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B3-MOUTH-PACK-RAW-CANDIDATE-001
date: 2026-06-09
owner: Codex
status: B3_RAW_MOUTH_PACK_CANDIDATE_READY_FOR_EXTRACTION_HUMAN_REVIEW_REQUIRED
hypothesis: A newly generated B3 mouth-pack raw reference can preserve the source character's mouth style and coordinated smile-open internals while keeping prior generated/model_edit mouth assets explicitly forbidden as B3 inputs.
input:
  - experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png
  - experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/raw_outputs/b1_clean_base_underpaint_reference_001.png
  - experiments/cubism-v2-new-character-002/reports/v22_64part_generation_input_packet/v22_64part_generation_input_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_visual_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_overlay_qa_report.json
forbidden_input:
  - experiments/cubism-v2-new-character-002/generated_mouth_v10
  - experiments/cubism-v2-new-character-002/generated_mouth_v11
  - experiments/cubism-v2-new-character-002/generated_mouth_v12
  - experiments/cubism-v2-new-character-002/model_edit_v4_mouth_alpha
  - experiments/cubism-v2-new-character-002/model_edit_v4_strict_mouth
  - experiments/cubism-v2-new-character-002/model_edit_v7_smooth_mouth_preview
  - experiments/cubism-v2-new-character-002/model_edit_v8_existing_mouth_tuned_preview
  - experiments/cubism-v2-new-character-002/model_edit_v9_all_mouth_enabled_preview
  - experiments/cubism-v2-new-character-002/model_edit_v10_generated_mouth_eye_clamp_preview
  - experiments/cubism-v2-new-character-002/model_edit_v11_generated_mouth_eye_clamp_preview
  - experiments/cubism-v2-new-character-002/model_edit_v12_generated_mouth_eye_clamp_preview
  - experiments/cubism-v2-new-character-002/model_edit_v13_scaled_eye_mouth_preview
output:
  - scripts/build_cubism_v2_b3_mouth_pack_review_002.py
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack/raw_outputs/b3_mouth_pack_reference_001.png
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack/v22_b3_mouth_pack_review.json
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack/v22_b3_mouth_pack_review.md
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack/v22_b3_mouth_pack_contact_sheet.png
metric:
  - imagegen_mode: built_in_image_gen
  - raw_size: 1254x1254
  - raw_mode: RGB
  - allowed_input_count: 5
  - forbidden_existing_mouth_asset_count: 12
  - visual_check_count: 7
  - same_character_mouth_style: PASS_CANDIDATE
  - mouthopen_keypose_rows: PASS_CANDIDATE
  - coordinated_internals: PASS_CANDIDATE
  - wide_mouth_limit: REVIEW_VISUALLY
  - extraction_readiness: REVISE_BEFORE_LAYER_PROMOTION
  - human_visual_review: REQUIRED
  - self_review: PASS
decision: Keep this as the v22 B3 newly generated mouth-pack raw candidate. It can feed B3 extraction planning, but it is not yet separated full-canvas RGBA mouth material and does not unlock Mini Cubism or real Cubism success claims.
next_action: Extract/normalize B3 components into full-canvas RGBA candidates, run contact-sheet and overlay QA against the G0 source and B1 clean mouth base, and regenerate B3 if wide mouth is too large or internals look pasted instead of reusing old v10/v12/v13 mouth assets.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B3-MOUTH-LAYER-PACK-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B3-MOUTH-LAYER-PACK-001
date: 2026-06-09
owner: Codex
status: B3_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED
hypothesis: The newly generated B3 raw mouth sheet can be extracted into the 12 expected v22 B3 outputs as full-canvas RGBA candidates while preserving the no-existing-mouth-assets constraint.
input:
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack/raw_outputs/b3_mouth_pack_reference_001.png
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack/v22_b3_mouth_pack_review.json
forbidden_input:
  - experiments/cubism-v2-new-character-002/generated_mouth_v10
  - experiments/cubism-v2-new-character-002/generated_mouth_v11
  - experiments/cubism-v2-new-character-002/generated_mouth_v12
  - experiments/cubism-v2-new-character-002/model_edit_v4_mouth_alpha
  - experiments/cubism-v2-new-character-002/model_edit_v4_strict_mouth
  - experiments/cubism-v2-new-character-002/model_edit_v7_smooth_mouth_preview
  - experiments/cubism-v2-new-character-002/model_edit_v8_existing_mouth_tuned_preview
  - experiments/cubism-v2-new-character-002/model_edit_v9_all_mouth_enabled_preview
  - experiments/cubism-v2-new-character-002/model_edit_v10_generated_mouth_eye_clamp_preview
  - experiments/cubism-v2-new-character-002/model_edit_v11_generated_mouth_eye_clamp_preview
  - experiments/cubism-v2-new-character-002/model_edit_v12_generated_mouth_eye_clamp_preview
  - experiments/cubism-v2-new-character-002/model_edit_v13_scaled_eye_mouth_preview
output:
  - scripts/build_cubism_v2_b3_mouth_layer_pack_002.py
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack/normalized_layers/mouth_line.png
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack/normalized_layers/mouth_inner.png
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack/normalized_layers/mouth_upper_lip_mask.png
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack/normalized_layers/mouth_lower_lip_mask.png
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack/normalized_layers/mouth_teeth.png
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack/normalized_layers/mouth_tongue.png
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack/normalized_layers/mouth_corner_L.png
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack/normalized_layers/mouth_corner_R.png
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack/normalized_layers/mouth_closed_smile_reference.png
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack/normalized_layers/mouth_small_open_reference.png
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack/normalized_layers/mouth_mid_teeth_reference.png
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack/normalized_layers/mouth_wide_teeth_tongue_reference.png
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack/v22_b3_layer_pack_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack/v22_b3_layer_pack_report.md
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack/v22_b3_layer_pack_contact_sheet.png
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack/v22_b3_layer_pack_overlay_qa.png
metric:
  - expected_output_count: 12
  - generated_output_count: 12
  - missing_output_count: 0
  - empty_output_count: 0
  - all_layers_rgba: true
  - all_layers_2048: true
  - forbidden_existing_mouth_asset_count: 12
  - forbidden_assets_not_output_path: true
  - human_visual_review: REQUIRED
  - wide_mouth_review_gate: true
  - self_review: PASS
decision: Keep this B3 extraction as a full-canvas RGBA candidate only. It preserves the new generated mouth sheet, but wide-mouth restraint, internals coherence, overlay QA, and 주인님 review are required before B3 material PASS.
next_action: Run B3 overlay QA against the B1 clean mouth base, then revise extraction or regenerate B3 if visual QA rejects the internals.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B3-OVERLAY-QA-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B3-OVERLAY-QA-001
date: 2026-06-09
owner: Codex
status: B3_CODEX_OVERLAY_QA_REVISE_EXTRACTION_OR_REGENERATE_HUMAN_REVIEW_REQUIRED
hypothesis: B3 technical extraction may pass the 12-output RGBA gate while still failing visual overlay QA because separated mouth internals can look pasted or misaligned.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack/v22_b3_layer_pack_report.json
  - experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/raw_outputs/b1_clean_base_underpaint_reference_001.png
output:
  - scripts/build_cubism_v2_b3_overlay_qa_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack/v22_b3_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack/v22_b3_overlay_qa_report.md
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack/v22_b3_overlay_qa_on_b1_clean_base.png
metric:
  - b3_layer_pack_status: B3_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED
  - b3_layer_self_review_status: PASS
  - check_count: 5
  - technical_layer_pack: PASS_TECHNICAL
  - closed_line_overlay: REVIEW_VISUALLY
  - open_internals_overlay: REVISE_EXTRACTION_OR_REGENERATE
  - wide_reference_restraint: REVIEW_VISUALLY
  - human_visual_review: REQUIRED
  - self_review: PASS
decision: Do not promote B3 layer-pack to material PASS. Keep the raw B3 sheet as useful evidence, but revise extraction or regenerate B3 before proceeding to Mini Cubism diagnostics.
next_action: Revise B3 extraction around one coherent mouth opening, or regenerate a new B3 sheet if teeth/tongue/inner still look pasted. Do not reuse v10/v12/v13 mouth PNGs as a shortcut.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B3-MOUTH-LAYER-PACK-REVISION-V1-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B3-MOUTH-LAYER-PACK-REVISION-V1-001
date: 2026-06-09
owner: Codex
status: B3_REVISION_V1_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED
hypothesis: The failed first B3 extraction can be preserved as REVISE while a revised extraction uses only the newly generated B3 raw sheet to rebuild coherent full-canvas RGBA mouth candidates.
input:
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack/raw_outputs/b3_mouth_pack_reference_001.png
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack/v22_b3_overlay_qa_report.json
forbidden_input:
  - experiments/cubism-v2-new-character-002/generated_mouth_v10
  - experiments/cubism-v2-new-character-002/generated_mouth_v11
  - experiments/cubism-v2-new-character-002/generated_mouth_v12
  - experiments/cubism-v2-new-character-002/model_edit_v4_mouth_alpha
  - experiments/cubism-v2-new-character-002/model_edit_v4_strict_mouth
  - experiments/cubism-v2-new-character-002/model_edit_v7_smooth_mouth_preview
  - experiments/cubism-v2-new-character-002/model_edit_v8_existing_mouth_tuned_preview
  - experiments/cubism-v2-new-character-002/model_edit_v9_all_mouth_enabled_preview
  - experiments/cubism-v2-new-character-002/model_edit_v10_generated_mouth_eye_clamp_preview
  - experiments/cubism-v2-new-character-002/model_edit_v11_generated_mouth_eye_clamp_preview
  - experiments/cubism-v2-new-character-002/model_edit_v12_generated_mouth_eye_clamp_preview
  - experiments/cubism-v2-new-character-002/model_edit_v13_scaled_eye_mouth_preview
output:
  - scripts/build_cubism_v2_b3_mouth_layer_pack_revision_v1_002.py
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack_revision_v1/normalized_layers/mouth_line.png
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack_revision_v1/normalized_layers/mouth_inner.png
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack_revision_v1/normalized_layers/mouth_upper_lip_mask.png
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack_revision_v1/normalized_layers/mouth_lower_lip_mask.png
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack_revision_v1/normalized_layers/mouth_teeth.png
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack_revision_v1/normalized_layers/mouth_tongue.png
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack_revision_v1/normalized_layers/mouth_corner_L.png
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack_revision_v1/normalized_layers/mouth_corner_R.png
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack_revision_v1/normalized_layers/mouth_closed_smile_reference.png
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack_revision_v1/normalized_layers/mouth_small_open_reference.png
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack_revision_v1/normalized_layers/mouth_mid_teeth_reference.png
  - experiments/cubism-v2-new-character-002/v22_b3_mouth_pack_revision_v1/normalized_layers/mouth_wide_teeth_tongue_reference.png
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack_revision_v1/v22_b3_revision_v1_layer_pack_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack_revision_v1/v22_b3_revision_v1_layer_pack_report.md
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack_revision_v1/v22_b3_revision_v1_layer_pack_contact_sheet.png
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack_revision_v1/v22_b3_revision_v1_layer_pack_overlay_qa.png
metric:
  - previous_overlay_status_preserved: B3_CODEX_OVERLAY_QA_REVISE_EXTRACTION_OR_REGENERATE_HUMAN_REVIEW_REQUIRED
  - expected_output_count: 12
  - generated_output_count: 12
  - missing_output_count: 0
  - empty_output_count: 0
  - all_layers_rgba: true
  - all_layers_2048: true
  - forbidden_existing_mouth_asset_count: 12
  - forbidden_assets_not_output_path: true
  - human_visual_review: REQUIRED
  - wide_mouth_review_gate: true
  - self_review: PASS
decision: Keep B3 revision v1 as the current mouth extraction candidate while preserving the first extraction as REVISE. This is candidate material only, not B3 material PASS.
next_action: Run/review revision v1 overlay QA against the B1 clean mouth base. If 주인님 rejects mouth anchor, scale, or internals, use manual anchor correction or regenerate B3 instead of reusing v10/v12/v13 mouth assets.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B3-REVISION-V1-OVERLAY-QA-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B3-REVISION-V1-OVERLAY-QA-001
date: 2026-06-09
owner: Codex
status: B3_REVISION_V1_CODEX_OVERLAY_QA_PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED
hypothesis: Revising B3 around coherent mouth-state crops can remove the pasted large skin patch and produce a better overlay candidate, while still keeping human visual review as the approval gate.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack_revision_v1/v22_b3_revision_v1_layer_pack_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack/v22_b3_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/raw_outputs/b1_clean_base_underpaint_reference_001.png
output:
  - scripts/build_cubism_v2_b3_revision_v1_overlay_qa_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack_revision_v1/v22_b3_revision_v1_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack_revision_v1/v22_b3_revision_v1_overlay_qa_report.md
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack_revision_v1/v22_b3_revision_v1_overlay_qa_on_b1_clean_base.png
metric:
  - revision_layer_pack_status: B3_REVISION_V1_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED
  - revision_layer_self_review_status: PASS
  - previous_overlay_status: B3_CODEX_OVERLAY_QA_REVISE_EXTRACTION_OR_REGENERATE_HUMAN_REVIEW_REQUIRED
  - large_skin_patch_removed: PASS_CANDIDATE
  - coordinated_mouth_internals: PASS_CANDIDATE
  - mouth_anchor_scale: REVIEW_VISUALLY
  - mouthopen_085_wide_restraint: REVIEW_VISUALLY
  - human_visual_review: REQUIRED
  - self_review: PASS
decision: Treat B3 revision v1 as the current Codex overlay QA pass candidate only. It may feed 주인님 review/manual anchor correction, but it does not unlock Mini Cubism diagnostics or real Cubism authoring by itself.
next_action: Continue with B4 hair-pack generation as an independent image-generation step, while B3 waits for 주인님 visual review or manual anchor correction before material PASS.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B4-HAIR-PACK-RAW-CANDIDATE-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B4-HAIR-PACK-RAW-CANDIDATE-001
date: 2026-06-09
owner: Codex
status: B4_RAW_HAIR_PACK_CANDIDATE_READY_FOR_EXTRACTION_HUMAN_REVIEW_REQUIRED
hypothesis: A newly generated B4 hair-pack raw reference can preserve the source hairstyle and create real front/side/back hair child scope, without reusing prior normalized/model_edit hair parts.
input:
  - experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png
  - experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/raw_outputs/b1_clean_base_underpaint_reference_001.png
  - experiments/cubism-v2-new-character-002/reports/v22_64part_generation_spec/v22_64part_generation_spec.json
  - experiments/cubism-v2-new-character-002/reports/v22_64part_generation_input_packet/v22_64part_generation_input_packet.json
forbidden_input:
  - experiments/cubism-v2-new-character-002/material_pack_first_v0/normalized_layers
  - experiments/cubism-v2-new-character-002/model_edit_v13_scaled_eye_mouth_preview/mini_cubism_diagnostic_project/parts
  - experiments/cubism-v2-new-character-002/model_edit_v19_generated_eye_preview/mini_cubism_diagnostic_project/parts
  - experiments/cubism-v2-new-character-002/model_edit_v20_manual_eye_anchor_preview/mini_cubism_diagnostic_project/parts
  - experiments/cubism-v2-new-character-002/model_edit_v21_supported_rig_smoke_preview/mini_cubism_diagnostic_project/parts
output:
  - scripts/build_cubism_v2_b4_hair_pack_review_002.py
  - experiments/cubism-v2-new-character-002/v22_b4_hair_pack/raw_outputs/b4_hair_pack_reference_001.png
  - experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_hair_pack_review.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_hair_pack_review.md
  - experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_hair_pack_contact_sheet.png
metric:
  - expected_b4_part_count: 16
  - b4_raw_mode: RGB
  - b4_raw_size: [1536, 1024]
  - forbidden_existing_hair_asset_count: 5
  - forbidden_assets_not_output_path: true
  - same_character_hair_style: PASS_CANDIDATE
  - front_hair_children_visible: PASS_CANDIDATE
  - side_back_hair_groups_visible: PASS_CANDIDATE
  - hairfront_contract_gate: HOLD_UNSUPPORTED_CONTROL
  - human_visual_review: REQUIRED
  - self_review: PASS
decision: Keep this as the v22 B4 newly generated hair-pack raw candidate. It can feed B4 extraction planning, but it is not yet separated full-canvas RGBA hair material and does not unlock ParamHairFront or real Cubism success claims.
next_action: Extract/normalize B4 components into the 16 expected full-canvas RGBA hair candidates or continue breadth-first to B5 body/clothing generation. Keep ParamHairFront hidden until hair_front_* child parts are extracted, aligned, and visually accepted.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B5-BODY-CLOTHING-PACK-RAW-CANDIDATE-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B5-BODY-CLOTHING-PACK-RAW-CANDIDATE-001
date: 2026-06-09
owner: Codex
status: B5_RAW_BODY_CLOTHING_PACK_CANDIDATE_READY_FOR_EXTRACTION_HUMAN_REVIEW_REQUIRED
hypothesis: A newly generated B5 body/clothing raw reference can provide torso, neck, shoulder, arm, clothing, brow, nose, cheek, and face-shadow material scope without depending on source lower-body crop reuse.
input:
  - experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png
  - experiments/cubism-v2-new-character-002/v22_b1_clean_base_underpaint/raw_outputs/b1_clean_base_underpaint_reference_001.png
  - experiments/cubism-v2-new-character-002/reports/v22_64part_generation_spec/v22_64part_generation_spec.json
  - experiments/cubism-v2-new-character-002/reports/v22_64part_generation_input_packet/v22_64part_generation_input_packet.json
forbidden_input:
  - experiments/cubism-v2-new-character-002/material_pack_first_v0/normalized_layers
  - experiments/cubism-v2-new-character-002/model_edit_v13_scaled_eye_mouth_preview/mini_cubism_diagnostic_project/parts
  - experiments/cubism-v2-new-character-002/model_edit_v21_supported_rig_smoke_preview/mini_cubism_diagnostic_project/parts
  - experiments/cubism-v2-new-character-001/material_pack_v0/production_layers
  - experiments/cubism-v2-new-character-001/material_pack_v0/production_layers_roi_semantic_remask_v1
output:
  - scripts/build_cubism_v2_b5_body_clothing_pack_review_002.py
  - experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/raw_outputs/b5_body_clothing_pack_reference_001.png
  - experiments/cubism-v2-new-character-002/reports/v22_b5_body_clothing_pack/v22_b5_body_clothing_pack_review.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_body_clothing_pack/v22_b5_body_clothing_pack_review.md
  - experiments/cubism-v2-new-character-002/reports/v22_b5_body_clothing_pack/v22_b5_body_clothing_pack_contact_sheet.png
metric:
  - expected_b5_part_count: 17
  - b5_raw_mode: RGB
  - b5_raw_size: [1536, 1024]
  - forbidden_existing_body_clothing_asset_count: 5
  - forbidden_assets_not_output_path: true
  - same_character_outfit_style: PASS_CANDIDATE
  - body_clothing_scope_visible: PASS_CANDIDATE
  - face_detail_scope_visible: PASS_CANDIDATE
  - breath_body_angle_support: REVIEW_VISUALLY
  - human_visual_review: REQUIRED
  - self_review: PASS
decision: Keep this as the v22 B5 newly generated body/clothing-pack raw candidate. It can feed B5 extraction planning, but it is not yet separated full-canvas RGBA material and does not prove body-motion or real Cubism success.
next_action: Extract/normalize B5 components into the 17 expected full-canvas RGBA body/clothing/face-detail candidates, then run contact-sheet and overlay QA before manifest or material promotion.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B4-HAIR-LAYER-PACK-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B4-HAIR-LAYER-PACK-001
date: 2026-06-09
owner: Codex
status: B4_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED
hypothesis: The newly generated B4 hair raw sheet can be extracted into the 16 expected v22 B4 outputs as full-canvas RGBA candidates while preserving the no-existing-hair-assets constraint.
input:
  - experiments/cubism-v2-new-character-002/v22_b4_hair_pack/raw_outputs/b4_hair_pack_reference_001.png
  - experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_hair_pack_review.json
forbidden_input:
  - experiments/cubism-v2-new-character-002/material_pack_first_v0/normalized_layers
  - experiments/cubism-v2-new-character-002/model_edit_v13_scaled_eye_mouth_preview/mini_cubism_diagnostic_project/parts
  - experiments/cubism-v2-new-character-002/model_edit_v19_generated_eye_preview/mini_cubism_diagnostic_project/parts
  - experiments/cubism-v2-new-character-002/model_edit_v20_manual_eye_anchor_preview/mini_cubism_diagnostic_project/parts
  - experiments/cubism-v2-new-character-002/model_edit_v21_supported_rig_smoke_preview/mini_cubism_diagnostic_project/parts
output:
  - scripts/build_cubism_v2_b4_hair_layer_pack_002.py
  - experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_back_base.png
  - experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_back_strand_L.png
  - experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_back_strand_R.png
  - experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_back_center.png
  - experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_front_center.png
  - experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_front_L.png
  - experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_front_R.png
  - experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_front_side_L.png
  - experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_front_side_R.png
  - experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_front_tip_L.png
  - experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_front_tip_R.png
  - experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_side_L_outer.png
  - experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_side_L_inner.png
  - experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_side_R_outer.png
  - experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_side_R_inner.png
  - experiments/cubism-v2-new-character-002/v22_b4_hair_pack/normalized_layers/hair_back_underpaint.png
  - experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_layer_pack_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_layer_pack_report.md
  - experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_layer_pack_contact_sheet.png
  - experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_layer_pack_overlay_qa.png
metric:
  - expected_output_count: 16
  - generated_output_count: 16
  - missing_output_count: 0
  - empty_output_count: 0
  - all_layers_rgba: true
  - all_layers_2048: true
  - forbidden_existing_hair_asset_count: 5
  - forbidden_assets_not_output_path: true
  - human_visual_review: REQUIRED
  - hairfront_contract_gate: true
  - self_review: PASS
decision: Keep this B4 extraction as full-canvas RGBA candidate evidence only. It creates real hair_front_* scope, but does not unlock ParamHairFront or material PASS before overlay QA and 주인님 review.
next_action: Run B4 overlay QA and revise anchor placement/crop assignment before using B4 in Mini Cubism diagnostics.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B4-OVERLAY-QA-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B4-OVERLAY-QA-001
date: 2026-06-09
owner: Codex
status: B4_CODEX_OVERLAY_QA_REVISE_ANCHOR_OR_EXTRACTION_HUMAN_REVIEW_REQUIRED
hypothesis: B4 technical RGBA extraction can pass while still failing visual overlay QA because hair crops and anchors may not align with the source hairstyle silhouette.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_layer_pack_report.json
output:
  - scripts/build_cubism_v2_b4_overlay_qa_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_overlay_qa_report.md
  - experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_layer_pack_overlay_qa.png
metric:
  - b4_layer_pack_status: B4_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED
  - b4_layer_self_review_status: PASS
  - technical_layer_pack: PASS_TECHNICAL
  - real_hairfront_children_scope: PASS_CANDIDATE
  - front_hair_overlay_alignment: REVISE_ANCHOR_OR_EXTRACTION
  - back_side_hair_overlay_alignment: REVISE_ANCHOR_OR_EXTRACTION
  - hairfront_contract_gate: HOLD_UNSUPPORTED_CONTROL
  - human_visual_review: REQUIRED
  - self_review: PASS
decision: Do not promote B4 to material PASS. Keep the 16 RGBA hair outputs as extraction candidates, but revise anchor placement/crop assignment before enabling ParamHairFront or using B4 for Mini Cubism diagnostics.
next_action: Use manual anchor correction or a refined extraction script for hair_front_* and side/back hair placement; regenerate B4 only if crop refinement cannot make the parts read as the source hairstyle.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B5-BODY-CLOTHING-LAYER-PACK-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B5-BODY-CLOTHING-LAYER-PACK-001
date: 2026-06-09
owner: Codex
status: B5_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED
hypothesis: The newly generated B5 body/clothing raw sheet can be extracted into the 17 expected v22 B5 outputs as full-canvas RGBA candidates while preserving the no-existing-body-clothing-assets constraint.
input:
  - experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/raw_outputs/b5_body_clothing_pack_reference_001.png
  - experiments/cubism-v2-new-character-002/reports/v22_b5_body_clothing_pack/v22_b5_body_clothing_pack_review.json
forbidden_input:
  - experiments/cubism-v2-new-character-002/material_pack_first_v0/normalized_layers
  - experiments/cubism-v2-new-character-002/model_edit_v13_scaled_eye_mouth_preview/mini_cubism_diagnostic_project/parts
  - experiments/cubism-v2-new-character-002/model_edit_v21_supported_rig_smoke_preview/mini_cubism_diagnostic_project/parts
  - experiments/cubism-v2-new-character-001/material_pack_v0/production_layers
  - experiments/cubism-v2-new-character-001/material_pack_v0/production_layers_roi_semantic_remask_v1
output:
  - scripts/build_cubism_v2_b5_body_clothing_layer_pack_002.py
  - experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/torso_base.png
  - experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/neck.png
  - experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/shoulder_L.png
  - experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/shoulder_R.png
  - experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/arm_L_upper_simple.png
  - experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/arm_R_upper_simple.png
  - experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/collar_front.png
  - experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/collar_shadow.png
  - experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/chest_cloth_base.png
  - experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/chest_cloth_shadow.png
  - experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/brow_L.png
  - experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/brow_R.png
  - experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/nose.png
  - experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/cheek_L.png
  - experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/cheek_R.png
  - experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/face_shadow_L.png
  - experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/normalized_layers/face_shadow_R.png
  - experiments/cubism-v2-new-character-002/reports/v22_b5_body_clothing_pack/v22_b5_layer_pack_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_body_clothing_pack/v22_b5_layer_pack_report.md
  - experiments/cubism-v2-new-character-002/reports/v22_b5_body_clothing_pack/v22_b5_layer_pack_contact_sheet.png
  - experiments/cubism-v2-new-character-002/reports/v22_b5_body_clothing_pack/v22_b5_layer_pack_overlay_qa.png
metric:
  - expected_output_count: 17
  - generated_output_count: 17
  - missing_output_count: 0
  - empty_output_count: 0
  - all_layers_rgba: true
  - all_layers_2048: true
  - forbidden_existing_body_clothing_asset_count: 5
  - forbidden_assets_not_output_path: true
  - human_visual_review: REQUIRED
  - face_detail_scope: true
  - self_review: PASS
decision: Keep this B5 extraction as full-canvas RGBA candidate evidence only. It does not prove body-motion, visual material PASS, Mini Cubism success, or real Cubism success before overlay QA and 주인님 review.
next_action: Run B5 overlay QA and revise anchor placement/crop assignment before using B5 in manifest promotion or Mini Cubism diagnostics.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B5-OVERLAY-QA-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B5-OVERLAY-QA-001
date: 2026-06-09
owner: Codex
status: B5_CODEX_OVERLAY_QA_REVISE_ANCHOR_OR_EXTRACTION_HUMAN_REVIEW_REQUIRED
hypothesis: B5 technical RGBA extraction can pass while still failing visual overlay QA because body/clothing and face-detail crops may not align with the source silhouette.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b5_body_clothing_pack/v22_b5_layer_pack_report.json
output:
  - scripts/build_cubism_v2_b5_overlay_qa_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_b5_body_clothing_pack/v22_b5_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_body_clothing_pack/v22_b5_overlay_qa_report.md
  - experiments/cubism-v2-new-character-002/reports/v22_b5_body_clothing_pack/v22_b5_layer_pack_overlay_qa.png
metric:
  - b5_layer_pack_status: B5_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED
  - b5_layer_self_review_status: PASS
  - technical_layer_pack: PASS_TECHNICAL
  - body_clothing_scope: PASS_CANDIDATE
  - body_clothing_overlay_alignment: REVISE_ANCHOR_OR_EXTRACTION
  - face_detail_overlay_alignment: REVISE_ANCHOR_OR_EXTRACTION
  - breath_body_angle_gate: REVIEW_BLOCKED_UNTIL_ALIGNMENT
  - human_visual_review: REQUIRED
  - self_review: PASS
decision: Do not promote B5 to material PASS. Keep the 17 RGBA body/clothing outputs as extraction candidates, but revise anchor placement/crop assignment before manifest promotion, Mini Cubism diagnostics, or real Cubism authoring.
next_action: Use manual anchor correction or a refined extraction script for torso, neck, arms, clothing, and face-detail placement; regenerate B5 only if crop refinement cannot make the parts read as source-matched material.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-64PART-CANDIDATE-MANIFEST-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-64PART-CANDIDATE-MANIFEST-001
date: 2026-06-09
owner: Codex
status: G1_64PART_MANIFEST_COMPLETE_TECHNICAL_PASS_VISUAL_REVISE_BLOCKED
hypothesis: B1-B5 candidate outputs can satisfy G1 64-part technical completeness while preserving B4/B5 visual REVISE gates so material promotion remains blocked.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_64part_generation_spec/v22_64part_generation_spec.json
  - experiments/cubism-v2-new-character-002/reports/v22_64part_generation_input_packet/v22_g0_existing_source_review.json
  - experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_layer_pack_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_layer_pack_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack_revision_v1/v22_b3_revision_v1_layer_pack_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_layer_pack_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_body_clothing_pack/v22_b5_layer_pack_report.json
output:
  - scripts/build_cubism_v2_64part_candidate_manifest_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_64part_candidate_manifest/v22_64part_candidate_manifest.json
  - experiments/cubism-v2-new-character-002/reports/v22_64part_candidate_manifest/v22_64part_candidate_manifest.md
  - experiments/cubism-v2-new-character-002/reports/v22_64part_candidate_manifest/v22_64part_candidate_manifest_contact_sheet.png
metric:
  - required_part_count: 64
  - manifest_entry_count: 64
  - unique_manifest_part_count: 64
  - missing_part_count: 0
  - wrong_mode_count: 0
  - wrong_size_count: 0
  - empty_part_count: 0
  - duplicate_part_count: 0
  - group_counts_match_spec: true
  - g1_64part_completeness: PASS_TECHNICAL
  - g2_full_canvas_rgba: PASS_TECHNICAL
  - g4_g5_visual_overlay: BLOCKED_REVISE
  - b4_revise_parts: true
  - b5_revise_parts: true
  - param_hair_front: HIDDEN_CONTRACT_ONLY
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: The v22 64 required part IDs are technically present as 2048 RGBA candidates, but B4 and B5 overlay QA are REVISE. Do not promote to material PASS, Mini Cubism diagnostics, or real Cubism authoring.
next_action: Refine B4/B5 anchors or crop assignments, or run manual anchor correction for visually misaligned parts. Rebuild the manifest after corrected B4/B5 visual QA passes.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B4-B5-ANCHOR-CORRECTION-READINESS-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B4-B5-ANCHOR-CORRECTION-READINESS-001
date: 2026-06-09
owner: Codex
status: G6_B4_B5_ANCHOR_CORRECTION_READY_OVERRIDE_PENDING
hypothesis: The current B4/B5 visual REVISE state can be converted into a repeatable G6 correction target list with current bbox/center evidence, while preserving all promotion blocks.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_64part_candidate_manifest/v22_64part_candidate_manifest.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_body_clothing_pack/v22_b5_overlay_qa_report.json
output:
  - scripts/build_cubism_v2_b4_b5_anchor_correction_readiness_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_correction_readiness/v22_b4_b5_anchor_correction_readiness.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_correction_readiness/v22_b4_b5_anchor_correction_readiness.md
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_correction_readiness/manual_anchor_override_template.json
metric:
  - manifest_status: G1_64PART_MANIFEST_COMPLETE_TECHNICAL_PASS_VISUAL_REVISE_BLOCKED
  - b4_overlay_status: B4_CODEX_OVERLAY_QA_REVISE_ANCHOR_OR_EXTRACTION_HUMAN_REVIEW_REQUIRED
  - b5_overlay_status: B5_CODEX_OVERLAY_QA_REVISE_ANCHOR_OR_EXTRACTION_HUMAN_REVIEW_REQUIRED
  - target_count: 33
  - b4_target_count: 16
  - b5_target_count: 17
  - all_targets_have_bbox: true
  - all_targets_pending_override: true
  - param_hair_front_hidden: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: B4/B5 are ready for G6 correction capture, not material promotion. Current bbox/center evidence is recorded for each visually revised target, and the override template remains pending until real target anchors are saved.
next_action: Open or build a drag/zoom anchor editor for these targets, save target anchors into the override JSON, rebuild corrected B4/B5 candidates, then rerun overlay QA and rebuild the 64-part manifest before any G7 Mini Cubism diagnostic.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B4-B5-ANCHOR-EDITOR-SMOKE-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B4-B5-ANCHOR-EDITOR-SMOKE-001
date: 2026-06-09
owner: Codex
status: PASS_V22_B4_B5_ANCHOR_EDITOR_API_SMOKE
hypothesis: A local drag/zoom editor can load the B4/B5 correction targets and save target anchors through an API without promoting material quality or polluting the real override file during smoke.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_correction_readiness/v22_b4_b5_anchor_correction_readiness.json
  - experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png
output:
  - scripts/run_v22_b4_b5_anchor_editor_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_correction_readiness/v22_b4_b5_anchor_editor_smoke.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_correction_readiness/manual_anchor_overrides_smoke.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_correction_readiness/v22_b4_b5_anchor_editor_browser.png
metric:
  - state_target_count: 33
  - source_exists: true
  - all_target_layers_exist: true
  - has_drag_zoom_editor: true
  - api_state_pass: true
  - api_save_pass: true
  - browser_snapshot_loaded: true
  - real_manual_anchor_overrides_not_touched_by_smoke: true
  - self_review: PASS
decision: The editor is ready for 주인님 or operator anchor capture, but the smoke saved only a separate smoke override. No B4/B5 material approval, Mini Cubism diagnostic unlock, or real Cubism authoring unlock has occurred.
next_action: Run `python3 scripts/run_v22_b4_b5_anchor_editor_002.py --host 127.0.0.1 --port 8092`, save real B4/B5 target anchors to `manual_anchor_overrides.json`, then build corrected candidate layers from those saved anchors.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B4-B5-AUTO-ANCHOR-DRAFT-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B4-B5-AUTO-ANCHOR-DRAFT-001
date: 2026-06-09
owner: Codex
status: G6_B4_B5_AUTO_ANCHOR_DRAFT_READY_FOR_REBUILD
hypothesis: Codex can reduce 주인님 manual work by saving conservative first-pass anchors for all B4/B5 correction targets while preserving visual and Cubism promotion gates.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_correction_readiness/v22_b4_b5_anchor_correction_readiness.json
output:
  - scripts/build_cubism_v2_b4_b5_auto_anchor_draft_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_correction_readiness/manual_anchor_overrides_auto_draft.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_correction_readiness/manual_anchor_overrides_auto_draft.md
metric:
  - target_count: 33
  - saved_count: 33
  - all_targets_have_override: true
  - param_hair_front_hidden: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: Keep this as an automatic draft only. It is useful for rebuilding a first corrected candidate, not for material PASS.
next_action: Rebuild corrected B4/B5 candidates from the auto draft and run overlay QA.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B4-B5-AUTO-DRAFT-CORRECTED-CANDIDATE-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B4-B5-AUTO-DRAFT-CORRECTED-CANDIDATE-001
date: 2026-06-09
owner: Codex
status: G6_B4_B5_AUTO_ANCHOR_DRAFT_CORRECTED_CANDIDATE_READY_FOR_OVERLAY_QA
hypothesis: Saved JSON overrides can rebuild B4/B5 corrected full-canvas candidates without 주인님 placing all 33 anchors manually.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_correction_readiness/manual_anchor_overrides_auto_draft.json
output:
  - scripts/build_cubism_v2_b4_b5_anchor_corrected_candidate_002.py
  - experiments/cubism-v2-new-character-002/v22_b4_b5_anchor_corrected_auto_draft/normalized_layers
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_anchor_corrected_auto_draft_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_anchor_corrected_auto_draft_contact_sheet.png
metric:
  - target_count: 33
  - entry_count: 33
  - saved_override_count: 33
  - applied_override_count: 33
  - copied_pending_override_count: 0
  - b4_entry_count: 16
  - b5_entry_count: 17
  - all_layers_rgba: true
  - all_layers_2048: true
  - all_layers_nonempty: true
  - param_hair_front_hidden: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: JSON override-based regeneration works. Keep the result as corrected candidate evidence only until overlay QA and human review pass.
next_action: Run auto-draft overlay QA and triage whether problems are anchor or extraction-mask issues.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B4-B5-AUTO-DRAFT-OVERLAY-QA-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B4-B5-AUTO-DRAFT-OVERLAY-QA-001
date: 2026-06-09
owner: Codex
status: G6_B4_B5_AUTO_DRAFT_OVERLAY_QA_REVIEW_REQUIRED
hypothesis: Auto-draft corrected B4/B5 candidates can be reviewed through overlay QA without promoting them to material PASS.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_anchor_corrected_auto_draft_report.json
output:
  - scripts/build_cubism_v2_b4_b5_auto_draft_overlay_qa_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_auto_draft_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_auto_draft_overlay_qa.png
metric:
  - entry_count: 33
  - b4_entry_count: 16
  - b5_entry_count: 17
  - applied_override_count: 33
  - overlay_sheet_exists: true
  - has_review_required_gate: true
  - param_hair_front_hidden: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: Auto-draft overlay QA is review evidence only. It shows several issues are semantic extraction/mask problems, not simple anchor problems.
next_action: Triage which parts should be refined automatically versus shown to 주인님 for focused review.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B4-B5-AUTO-DRAFT-REVIEW-TRIAGE-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B4-B5-AUTO-DRAFT-REVIEW-TRIAGE-001
date: 2026-06-09
owner: Codex
status: G6_B4_B5_AUTO_DRAFT_TRIAGE_REEXTRACTION_AND_FOCUSED_REVIEW_REQUIRED
hypothesis: 주인님 should not need to manually anchor all B4/B5 parts; overlay review can split extraction-mask work from focused human review.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_auto_draft_overlay_qa_report.json
output:
  - scripts/build_cubism_v2_b4_b5_auto_draft_review_triage_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_auto_draft_review_triage.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_auto_draft_review_triage.md
metric:
  - entry_count: 33
  - refine_extraction_mask_count: 13
  - review_anchor_and_mask_count: 15
  - review_draw_order_or_mask_count: 3
  - review_or_refine_small_mask_count: 2
  - review_focus_count: 12
  - does_not_require_owner_review_all_33: true
  - param_hair_front_hidden: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: Do not ask 주인님 to manually anchor all 33 parts. Send 13 B5/body/face/clothing-style mask problems to refined extraction first, and use human review mainly for the focused hair/draw-order/anchor set.
next_action: Build refined extraction/mask candidates for the 13 `REFINE_EXTRACTION_MASK` targets, then rerun corrected overlay QA and keep the focused review set small.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B5-REFINED-MASK-V1-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B5-REFINED-MASK-V1-001
date: 2026-06-09
owner: Codex
status: B5_REFINED_MASK_V1_CANDIDATE_READY_FOR_OVERLAY_REVIEW
hypothesis: The 13 B5 extraction-mask targets can be refined automatically as a separate candidate without asking 주인님 to manually anchor all B5 parts.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_auto_draft_review_triage.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_anchor_corrected_auto_draft_report.json
output:
  - scripts/build_cubism_v2_b5_refined_mask_v1_002.py
  - experiments/cubism-v2-new-character-002/v22_b5_refined_mask_v1/normalized_layers
  - experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v1/v22_b5_refined_mask_v1_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v1/v22_b5_refined_mask_v1_contact_sheet.png
  - experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v1/v22_b5_refined_mask_v1_overlay_qa.png
metric:
  - entry_count: 17
  - refined_mask_count: 13
  - copied_from_auto_draft_count: 4
  - expected_refine_target_count: 13
  - all_layers_rgba: true
  - all_layers_2048: true
  - all_layers_nonempty: true
  - overlay_sheet_exists: true
  - contact_sheet_exists: true
  - validator_only_promotion_blocked: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: B5 refined-mask v1 is a useful intermediate candidate, not material PASS. It reduces some patch width but still requires overlay QA and focused revision.
next_action: Run conservative overlay QA and identify the smaller focused revise set.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B5-REFINED-MASK-V1-OVERLAY-QA-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B5-REFINED-MASK-V1-OVERLAY-QA-001
date: 2026-06-09
owner: Codex
status: B5_REFINED_MASK_V1_OVERLAY_QA_REVISE_REEXTRACTION_OR_HUMAN_REVIEW_REQUIRED
hypothesis: B5 refined-mask v1 can improve some overlay artifacts, but visual PASS must remain blocked if torso/shoulder/face-detail parts still read as patches.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v1/v22_b5_refined_mask_v1_report.json
output:
  - scripts/build_cubism_v2_b5_refined_mask_v1_overlay_qa_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v1/v22_b5_refined_mask_v1_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v1/v22_b5_refined_mask_v1_overlay_qa_report.md
metric:
  - refined_report_status: B5_REFINED_MASK_V1_CANDIDATE_READY_FOR_OVERLAY_REVIEW
  - refined_mask_count: 13
  - copied_from_auto_draft_count: 4
  - focused_revise_parts: [torso_base, shoulder_L, shoulder_R, face_shadow_L, face_shadow_R, nose]
  - has_revise_gate: true
  - has_blocked_material_gate: true
  - validator_only_promotion_blocked: true
  - param_hair_front_hidden: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: Keep B5 refined-mask v1 as intermediate evidence. Continue automatic v2 refinement for the six focused revise parts before asking 주인님 for broad B5 approval.
next_action: Build B5 refined-mask v2 for torso_base, shoulder_L, shoulder_R, face_shadow_L, face_shadow_R, and nose; keep B4 hair review separate.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B5-REFINED-MASK-V2-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B5-REFINED-MASK-V2-001
date: 2026-06-09
owner: Codex
status: B5_REFINED_MASK_V2_CANDIDATE_READY_FOR_OVERLAY_REVIEW
hypothesis: The six B5 v1 focused revise parts can be further reduced as a smaller v2 candidate without changing the rest of the B5 set.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v1/v22_b5_refined_mask_v1_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v1/v22_b5_refined_mask_v1_overlay_qa_report.json
output:
  - scripts/build_cubism_v2_b5_refined_mask_v2_002.py
  - experiments/cubism-v2-new-character-002/v22_b5_refined_mask_v2/normalized_layers
  - experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_contact_sheet.png
  - experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_overlay_qa.png
metric:
  - entry_count: 17
  - refined_mask_v2_count: 6
  - copied_from_v1_count: 11
  - expected_focused_target_count: 6
  - all_layers_rgba: true
  - all_layers_2048: true
  - all_layers_nonempty: true
  - overlay_sheet_exists: true
  - contact_sheet_exists: true
  - validator_only_promotion_blocked: true
  - param_hair_front_hidden: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: B5 refined-mask v2 is the current smallest automatic mask-reduction candidate for B5, not material PASS.
next_action: Run conservative v2 overlay QA and decide whether remaining torso/shoulder issues need regeneration/re-extraction rather than more alpha shrinking.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B5-REFINED-MASK-V2-OVERLAY-QA-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B5-REFINED-MASK-V2-OVERLAY-QA-001
date: 2026-06-09
owner: Codex
status: B5_REFINED_MASK_V2_OVERLAY_QA_REVISE_REGENERATE_OR_HUMAN_REVIEW_REQUIRED
hypothesis: B5 refined-mask v2 can narrow face-detail issues, but torso and shoulders may need regeneration/re-extraction or focused human acceptance instead of more mask shrinking.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_report.json
output:
  - scripts/build_cubism_v2_b5_refined_mask_v2_overlay_qa_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_overlay_qa_report.md
metric:
  - v2_report_status: B5_REFINED_MASK_V2_CANDIDATE_READY_FOR_OVERLAY_REVIEW
  - refined_mask_v2_count: 6
  - copied_from_v1_count: 11
  - remaining_b5_revise_parts: [torso_base, shoulder_L, shoulder_R]
  - possible_human_review_parts: [nose, face_shadow_L, face_shadow_R]
  - has_revise_gate: true
  - has_regenerate_or_reextract_gate: true
  - has_blocked_material_gate: true
  - validator_only_promotion_blocked: true
  - param_hair_front_hidden: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: Keep B5 refined-mask v2 as the current best automatic B5 mask-reduction candidate, but do not keep shrinking body masks blindly. Torso and shoulders should move to regeneration/re-extraction or focused human review.
next_action: Generate or re-extract the three remaining body blockers (`torso_base`, `shoulder_L`, `shoulder_R`) as a new B5 body mini-pass, while keeping B4 hair review separate.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B5-BODY-BLOCKER-DRAW-ORDER-REVIEW-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B5-BODY-BLOCKER-DRAW-ORDER-REVIEW-001
date: 2026-06-09
owner: Codex
status: B5_BODY_BLOCKER_DRAW_ORDER_REVIEW_READY_HUMAN_DECISION_REQUIRED
hypothesis: The three remaining B5 hard blockers should be reviewed as focused body/draw-order decisions, not as a request for 주인님 to manually anchor all B4/B5 parts.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_overlay_qa_report.json
output:
  - scripts/build_cubism_v2_b5_body_blocker_draw_order_review_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_b5_body_blocker_draw_order_review/v22_b5_body_blocker_draw_order_review.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_body_blocker_draw_order_review/v22_b5_body_blocker_draw_order_review.md
  - experiments/cubism-v2-new-character-002/reports/v22_b5_body_blocker_draw_order_review/v22_b5_body_blocker_draw_order_review.png
metric:
  - target_count: 3
  - targets: [torso_base, shoulder_L, shoulder_R]
  - torso_base_recommendation: REGENERATE_OR_FOCUSED_HUMAN_ACCEPT_BROAD_UNDERPAINT
  - shoulder_L_recommendation: REVIEW_DRAW_ORDER_BEFORE_REGENERATE
  - shoulder_R_recommendation: REVIEW_DRAW_ORDER_BEFORE_REGENERATE
  - shoulder_L_hair_occlusion_overlap_ratio: 0.870193
  - shoulder_R_hair_occlusion_overlap_ratio: 0.868247
  - does_not_require_owner_review_all_33: true
  - validator_only_promotion_blocked: true
  - param_hair_front_hidden: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: Keep B5 blocked from material PASS, but split the next decision: review shoulders with draw-order/occlusion before regenerating them, and treat torso_base as the main regenerate-or-focused-accept body underpaint decision.
next_action: Ask for focused accept/reject on only `torso_base`, `shoulder_L`, and `shoulder_R`; if rejected, run the recorded B5 body mini-pass regeneration prompt. Keep B4 hair focused review separate.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B4-HAIR-FOCUSED-REVIEW-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B4-HAIR-FOCUSED-REVIEW-001
date: 2026-06-09
owner: Codex
status: B4_HAIR_FOCUSED_REVIEW_READY_PARAMHAIRFRONT_STILL_HIDDEN
hypothesis: The B4 hair review should be narrowed to actual front-hair child candidates and draw-order/mask issues, without unlocking ParamHairFront or asking 주인님 to place all 33 B4/B5 anchors.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_layer_pack_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_auto_draft_review_triage.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_anchor_corrected_auto_draft_report.json
output:
  - scripts/build_cubism_v2_b4_hair_focused_review_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_b4_hair_focused_review/v22_b4_hair_focused_review.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_hair_focused_review/v22_b4_hair_focused_review.md
  - experiments/cubism-v2-new-character-002/reports/v22_b4_hair_focused_review/v22_b4_hair_focused_review.png
metric:
  - focus_part_count: 12
  - front_hair_focus_count: 7
  - front_hair_child_candidate_count: 7
  - front_hair_candidate_recommendation: FRONT_HAIR_CHILD_CANDIDATE_HUMAN_REVIEW_REQUIRED
  - back_or_underpaint_review_count: 3
  - back_or_underpaint_recommendation: KEEP_AS_BACK_OR_UNDERPAINT_REVIEW_DRAW_ORDER_MASK
  - back_strand_review_count: 2
  - back_strand_recommendation: REVIEW_ANCHOR_AND_MASK
  - does_not_require_owner_review_all_33: true
  - validator_only_promotion_blocked: true
  - param_hair_front_hidden: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: B4 has real independent hair_front_* candidate files, but this is focused review evidence only. Keep ParamHairFront hidden until front hair candidates pass human visual QA and later motion-readiness checks.
next_action: Ask for focused review of the B4 hair sheet; if front hair child candidates are accepted, prepare a motion-readiness check while keeping ParamHairFront hidden until that check passes.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B4-B5-FOCUSED-OWNER-REVIEW-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B4-B5-FOCUSED-OWNER-REVIEW-001
date: 2026-06-09
owner: Codex
status: B4_B5_FOCUSED_OWNER_REVIEW_PACKET_READY_PENDING_OWNER_DECISIONS
hypothesis: B4/B5 owner review can be reduced to ten primary decisions while keeping material PASS, ParamHairFront, Mini Cubism, and real Cubism gates blocked.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b4_hair_focused_review/v22_b4_hair_focused_review.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_body_blocker_draw_order_review/v22_b5_body_blocker_draw_order_review.json
output:
  - scripts/build_cubism_v2_b4_b5_focused_owner_review_packet_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_focused_owner_review.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_focused_owner_review.md
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_focused_owner_review.png
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_focused_owner_review_decision_template.json
metric:
  - primary_decision_count: 10
  - b4_front_hair_primary_count: 7
  - b5_body_primary_count: 3
  - secondary_followup_count: 5
  - all_primary_pending_owner_review: true
  - does_not_require_owner_review_all_33: true
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE
  - g8_real_cubism_status: BLOCKED
  - validator_only_promotion_blocked: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: Keep the packet as owner-review handoff only. No row is accepted yet; no B4/B5 material promotion or rig-stage unlock happens from this packet.
next_action: Collect owner decisions for the ten primary rows, then apply accepted/revised/regenerated paths separately before rerunning corrected B4/B5 overlay QA.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B4-B5-FOCUSED-OWNER-REVIEW-SERVER-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B4-B5-FOCUSED-OWNER-REVIEW-SERVER-001
date: 2026-06-09
owner: Codex
status: PASS_V22_B4_B5_FOCUSED_OWNER_REVIEW_SERVER_SMOKE
hypothesis: The focused owner review should be collectable in a local UI without asking 주인님 to manually anchor all B4/B5 parts and without unlocking any material or rig gates.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_focused_owner_review.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_focused_owner_review_decision_template.json
output:
  - scripts/run_v22_b4_b5_focused_owner_review_server_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_focused_owner_review_server_smoke.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_focused_owner_review_decisions_smoke.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_focused_owner_review_browser.png
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_owner_review_console_errors.json
metric:
  - primary_decision_count: 10
  - asset_crop_count: 40
  - tmp_png_count: 0
  - save_api_noop_pending_pass: true
  - browser_console_errors: 0
  - real_decisions_path: experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_focused_owner_review_decisions.json
  - smoke_decisions_path: experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_focused_owner_review_decisions_smoke.json
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: Use the 8093 UI to collect only the ten focused owner decisions. This is decision capture, not B4/B5 acceptance, material promotion, Mini Cubism promotion, or real Cubism promotion.
next_action: 주인님 reviews the ten rows in the UI, saves accept/revise/regenerate choices, then Codex applies the chosen paths and reruns corrected B4/B5 overlay QA before any G7/G8 work.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B4-B5-OWNER-DECISION-ROUTE-PLAN-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B4-B5-OWNER-DECISION-ROUTE-PLAN-001
date: 2026-06-09
owner: Codex
status: B4_B5_OWNER_DECISION_ROUTE_PLAN_BLOCKED_PENDING_OWNER_DECISIONS
hypothesis: Owner decisions should route B4/B5 into focused accept/revise/regenerate work without asking 주인님 to manually anchor all B4/B5 parts and without unlocking later gates from pending rows.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_focused_owner_review.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_focused_owner_review_decision_template.json
output:
  - scripts/build_cubism_v2_b4_b5_owner_decision_route_plan_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_owner_decision_route_plan.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_owner_decision_route_plan.md
metric:
  - decision_source_status: MISSING_REAL_DECISION_FILE_USING_TEMPLATE_PENDING
  - primary_decision_count: 10
  - decision_row_count: 10
  - pending_count: 10
  - accepted_count: 0
  - revise_count: 0
  - regenerate_count: 0
  - invalid_decision_count: 0
  - wait_owner_decision_routes: 10
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: Current evidence proves the route planner is ready but the real owner decisions are still pending. Pending rows block correction application, material promotion, Mini Cubism, and real Cubism.
next_action: 주인님 saves the ten focused decisions in the 8093 UI; then rerun the route planner and apply only the focused accept/revise/regenerate routes it emits.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B4-B5-CODEX-PROVISIONAL-ROUTE-PLAN-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B4-B5-CODEX-PROVISIONAL-ROUTE-PLAN-001
date: 2026-06-09
owner: Codex
status: B4_B5_OWNER_DECISION_ROUTE_PLAN_READY_FOR_REVISION_WORK
hypothesis: After 주인님 explicitly asked to continue without acceptance, Codex can use success-pattern provisional decisions to continue focused B4/B5 work while clearly not claiming owner approval or final material/rig success.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_focused_owner_review.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_focused_codex_provisional_decisions.json
output:
  - scripts/build_cubism_v2_b4_b5_codex_provisional_decisions_002.py
  - scripts/build_cubism_v2_b4_b5_owner_decision_route_plan_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_focused_codex_provisional_decisions.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_focused_codex_provisional_decisions.md
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_owner_decision_route_plan.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_owner_decision_route_plan.md
metric:
  - codex_decision_status: CODEX_PROVISIONAL_DECISIONS_READY_NO_OWNER_APPROVAL
  - decision_source_status: CODEX_PROVISIONAL_DECISION_FILE
  - decision_count: 10
  - pending_count: 0
  - accepted_count: 7
  - revise_count: 2
  - regenerate_count: 1
  - b4_front_hair_motion_readiness_candidate_routes: 7
  - b5_shoulder_draw_order_or_mask_refinement_routes: 2
  - b5_body_minipass_regeneration_routes: 1
  - not_owner_approval: true
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: Continue without 주인님 acceptance by using Codex provisional success-pattern routes. This unlocks focused B5 revision/regeneration and B4 motion-readiness preparation, but it does not count as human approval or material/rig success.
next_action: Apply focused B5 work first: regenerate `torso_base` as a B5 mini-pass and revise `shoulder_L`/`shoulder_R` draw-order or masks; keep B4 front hair as motion-readiness candidates with `ParamHairFront` hidden.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B5-PROVISIONAL-MINIPASS-INPUT-PACKET-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B5-PROVISIONAL-MINIPASS-INPUT-PACKET-001
date: 2026-06-09
owner: Codex
status: B5_PROVISIONAL_MINIPASS_INPUT_PACKET_READY
hypothesis: The Codex provisional route should produce a narrow B5 generation/revision input packet so progress continues without owner acceptance and without restarting B1-B5.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_owner_decision_route_plan.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_focused_codex_provisional_decisions.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_body_blocker_draw_order_review/v22_b5_body_blocker_draw_order_review.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_overlay_qa_report.json
output:
  - scripts/build_cubism_v2_b5_provisional_minipass_input_packet_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_b5_provisional_minipass_input_packet/v22_b5_provisional_minipass_input_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_provisional_minipass_input_packet/v22_b5_provisional_minipass_input_packet.md
metric:
  - route_plan_status: B4_B5_OWNER_DECISION_ROUTE_PLAN_READY_FOR_REVISION_WORK
  - codex_decision_status: CODEX_PROVISIONAL_DECISIONS_READY_NO_OWNER_APPROVAL
  - b5_overlay_qa_status: B5_REFINED_MASK_V2_OVERLAY_QA_REVISE_REGENERATE_OR_HUMAN_REVIEW_REQUIRED
  - target_count: 3
  - target_parts: [torso_base, shoulder_L, shoulder_R]
  - regenerate_target_count: 1
  - revise_target_count: 2
  - all_targets_have_crop_box: true
  - prompt_present: true
  - not_owner_approval: true
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: Use this packet as the next focused B5 generation/revision input. It narrows work to one torso regeneration and two shoulder draw-order/mask revisions.
next_action: Generate or revise B5 candidates from the packet, normalize to full-canvas RGBA, then rerun B5 overlay QA before rebuilding any promoted 64-part candidate.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B5-PROVISIONAL-MINIPASS-CANDIDATE-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B5-PROVISIONAL-MINIPASS-CANDIDATE-001
date: 2026-06-10
owner: Codex
status: B5_PROVISIONAL_MINIPASS_CANDIDATE_READY_FOR_OVERLAY_QA
hypothesis: The B5 provisional input packet can be applied to create a new full-canvas candidate without owner approval while preserving material and rig gates.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b5_provisional_minipass_input_packet/v22_b5_provisional_minipass_input_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_report.json
  - experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/raw_outputs/b5_body_clothing_pack_reference_001.png
output:
  - scripts/build_cubism_v2_b5_provisional_minipass_candidate_002.py
  - experiments/cubism-v2-new-character-002/v22_b5_provisional_minipass_candidate/normalized_layers/*.png
  - experiments/cubism-v2-new-character-002/reports/v22_b5_provisional_minipass_candidate/v22_b5_provisional_minipass_candidate_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_provisional_minipass_candidate/v22_b5_provisional_minipass_candidate_report.md
  - experiments/cubism-v2-new-character-002/reports/v22_b5_provisional_minipass_candidate/v22_b5_provisional_minipass_candidate_contact_sheet.png
  - experiments/cubism-v2-new-character-002/reports/v22_b5_provisional_minipass_candidate/v22_b5_provisional_minipass_candidate_overlay.png
metric:
  - entry_count: 17
  - target_count: 3
  - regenerated_from_b5_raw_count: 1
  - revised_draw_order_mask_count: 2
  - copied_from_v2_count: 14
  - all_layers_rgba: true
  - all_layers_2048: true
  - all_layers_nonempty: true
  - contact_sheet_exists: true
  - overlay_sheet_exists: true
  - not_owner_approval: true
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: Keep this as a B5 candidate for overlay QA only. It does not promote B5, the 64-part manifest, Mini Cubism, or real Cubism.
next_action: Run B5 provisional mini-pass overlay QA and decide whether to rebuild the corrected B4/B5 manifest with these B5 candidate layers.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-B5-PROVISIONAL-MINIPASS-OVERLAY-QA-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-B5-PROVISIONAL-MINIPASS-OVERLAY-QA-001
date: 2026-06-10
owner: Codex
status: B5_PROVISIONAL_MINIPASS_OVERLAY_QA_REVIEW_REQUIRED
hypothesis: The B5 provisional mini-pass should reduce shoulder hair-occlusion mask conflict while keeping torso and shoulders review-required before material promotion.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b5_provisional_minipass_candidate/v22_b5_provisional_minipass_candidate_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_overlay_qa_report.json
output:
  - scripts/build_cubism_v2_b5_provisional_minipass_overlay_qa_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_b5_provisional_minipass_candidate/v22_b5_provisional_minipass_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_provisional_minipass_candidate/v22_b5_provisional_minipass_overlay_qa_report.md
  - experiments/cubism-v2-new-character-002/reports/v22_b5_provisional_minipass_candidate/v22_b5_provisional_minipass_overlay_qa.png
metric:
  - target_count: 3
  - torso_verdict: REVIEW_REGENERATED_TORSO_UNDERPAINT
  - shoulder_improvement_candidate_count: 2
  - shoulder_verdict: PASS_DRAW_ORDER_MASK_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED
  - previous_remaining_b5_revise_parts: [torso_base, shoulder_L, shoulder_R]
  - remaining_review_parts: [torso_base, shoulder_L, shoulder_R]
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - validator_only_promotion_blocked: true
  - not_owner_approval: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: The shoulders are now draw-order/mask improvement candidates, and torso is a regenerated underpaint review candidate. All three are still review-required and blocked from material promotion.
next_action: Rebuild a corrected B4/B5 manifest candidate using the B5 provisional layers, then rerun full B4/B5 overlay QA before any G7/G8 work.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-CORRECTED-B4-B5-64PART-MANIFEST-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-CORRECTED-B4-B5-64PART-MANIFEST-001
date: 2026-06-10
owner: Codex
status: G1_64PART_CORRECTED_B4_B5_MANIFEST_TECHNICAL_PASS_REVIEW_REQUIRED
hypothesis: The 64-part candidate manifest can be rebuilt with corrected B4 and B5 provisional layers while keeping material and rig gates blocked.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_64part_generation_spec/v22_64part_generation_spec.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_anchor_corrected_auto_draft_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_provisional_minipass_candidate/v22_b5_provisional_minipass_candidate_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_provisional_minipass_candidate/v22_b5_provisional_minipass_overlay_qa_report.json
output:
  - scripts/build_cubism_v2_64part_corrected_b4_b5_manifest_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_64part_corrected_b4_b5_manifest/v22_64part_corrected_b4_b5_manifest.json
  - experiments/cubism-v2-new-character-002/reports/v22_64part_corrected_b4_b5_manifest/v22_64part_corrected_b4_b5_manifest.md
  - experiments/cubism-v2-new-character-002/reports/v22_64part_corrected_b4_b5_manifest/v22_64part_corrected_b4_b5_manifest_contact_sheet.png
metric:
  - required_part_count: 64
  - manifest_entry_count: 64
  - unique_manifest_part_count: 64
  - missing_part_count: 0
  - wrong_mode_count: 0
  - wrong_size_count: 0
  - empty_part_count: 0
  - duplicate_part_count: 0
  - group_counts_match_spec: true
  - b4_entry_count: 16
  - b5_entry_count: 17
  - b4_front_hair_motion_candidate_count: 7
  - b5_provisional_target_count: 3
  - b5_shoulder_improvement_candidate_count: 2
  - b5_torso_review_candidate: true
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - validator_only_promotion_blocked: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: The corrected B4/B5 64-part manifest is technically complete and no longer points to the old B5 layers for torso/shoulders, but it remains review-required and blocked from material/rig promotion.
next_action: Run corrected B4/B5 manifest overlay QA and only proceed toward G2-G5 material QA if that visual review is accepted separately.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-CORRECTED-B4-B5-MANIFEST-OVERLAY-QA-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-CORRECTED-B4-B5-MANIFEST-OVERLAY-QA-001
date: 2026-06-10
owner: Codex
status: CORRECTED_B4_B5_MANIFEST_OVERLAY_QA_REVIEW_REQUIRED
hypothesis: Corrected B4/B5 overlay QA should reflect the updated B5 provisional layers and B4 front-hair candidate separation without promoting material success.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_64part_corrected_b4_b5_manifest/v22_64part_corrected_b4_b5_manifest.json
output:
  - scripts/build_cubism_v2_corrected_b4_b5_manifest_overlay_qa_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_64part_corrected_b4_b5_manifest/v22_corrected_b4_b5_manifest_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_64part_corrected_b4_b5_manifest/v22_corrected_b4_b5_manifest_overlay_qa_report.md
  - experiments/cubism-v2-new-character-002/reports/v22_64part_corrected_b4_b5_manifest/v22_corrected_b4_b5_manifest_overlay_qa.png
metric:
  - qa_entry_count: 33
  - b4_entry_count: 16
  - b5_entry_count: 17
  - b4_front_hair_candidate_count: 7
  - b5_shoulder_improvement_candidate_count: 2
  - b5_torso_review_candidate_count: 1
  - verdict_counts:
      B4_FRONT_HAIR_MOTION_CANDIDATE_REVIEW_REQUIRED: 7
      B4_SECONDARY_DRAW_ORDER_OR_MASK_REVIEW_REQUIRED: 9
      B5_COPIED_LAYER_REVIEW_REQUIRED: 14
      B5_SHOULDER_DRAW_ORDER_MASK_IMPROVEMENT_REVIEW_REQUIRED: 2
      B5_TORSO_REGENERATED_UNDERPAINT_REVIEW_REQUIRED: 1
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - validator_only_promotion_blocked: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: Corrected B4/B5 overlay QA is review-required. It is suitable as the next visual gate, not as approval for material PASS, ParamHairFront, Mini Cubism, or real Cubism.
next_action: Prepare a concise corrected B4/B5 visual review packet or continue automatic review heuristics before G2-G5 material QA.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-CORRECTED-B4-B5-CODEX-VISUAL-TRIAGE-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-CORRECTED-B4-B5-CODEX-VISUAL-TRIAGE-001
date: 2026-06-10
owner: Codex
status: CORRECTED_B4_B5_CODEX_VISUAL_TRIAGE_READY_G2_G5_PREP_BLOCKED
hypothesis: After 주인님 asked to continue without acceptance, corrected B4/B5 review-required rows can be converted into a provisional work queue while keeping material and rig gates blocked.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_64part_corrected_b4_b5_manifest/v22_corrected_b4_b5_manifest_overlay_qa_report.json
output:
  - scripts/build_cubism_v2_corrected_b4_b5_codex_visual_triage_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_64part_corrected_b4_b5_manifest/v22_corrected_b4_b5_codex_visual_triage.json
  - experiments/cubism-v2-new-character-002/reports/v22_64part_corrected_b4_b5_manifest/v22_corrected_b4_b5_codex_visual_triage.md
  - experiments/cubism-v2-new-character-002/reports/v22_64part_corrected_b4_b5_manifest/v22_corrected_b4_b5_codex_visual_triage.png
metric:
  - triage_entry_count: 33
  - auto_candidate_count: 9
  - hold_review_count: 23
  - hard_review_count: 1
  - bucket_counts:
      AUTO_CANDIDATE: 9
      HARD_REVIEW: 1
      HOLD_REVIEW: 23
  - triage_counts:
      ACCEPT_AS_DRAW_ORDER_MASK_IMPROVEMENT_CANDIDATE: 2
      ACCEPT_AS_MOTION_READINESS_CANDIDATE_KEEP_HAIRFRONT_HIDDEN: 7
      HARD_REVIEW_TORSO_UNDERPAINT_BEFORE_MATERIAL_PREP: 1
      HOLD_FOR_COPIED_B5_LAYER_REVIEW: 14
      HOLD_FOR_SECONDARY_DRAW_ORDER_MASK_REVIEW: 9
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - not_owner_approval: true
  - validator_only_promotion_blocked: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: Codex provisional triage keeps progress moving without owner acceptance. B4 front hair and B5 shoulders are candidate-level keeps, while torso and the remaining copied/secondary B4/B5 layers block material promotion.
next_action: Prepare G2-G5 material QA only as a blocked/prep packet, keep ParamHairFront hidden, and do not start G7/G8 from this provisional triage.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G2-G5-MATERIAL-QA-PREP-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G2-G5-MATERIAL-QA-PREP-001
date: 2026-06-10
owner: Codex
status: G2_G5_MATERIAL_QA_PREP_PACKET_READY_BLOCKED_BY_CODEX_TRIAGE
hypothesis: The corrected 64-part manifest can prepare G2-G5 material QA structure, but Codex triage must block material acceptance and rig promotion until B4/B5 review rows are resolved.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_64part_corrected_b4_b5_manifest/v22_64part_corrected_b4_b5_manifest.json
  - experiments/cubism-v2-new-character-002/reports/v22_64part_corrected_b4_b5_manifest/v22_corrected_b4_b5_codex_visual_triage.json
output:
  - scripts/build_cubism_v2_g2_g5_material_qa_prep_packet_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g2_g5_material_qa_prep/v22_g2_g5_material_qa_prep_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g2_g5_material_qa_prep/v22_g2_g5_material_qa_prep_packet.md
metric:
  - manifest_entry_count: 64
  - triage_entry_count: 33
  - auto_candidate_count: 9
  - hold_review_count: 23
  - hard_review_count: 1
  - ready_gate_count: 1
  - blocked_or_prep_only_gate_count: 3
  - G2_LAYER_MANIFEST_TECHNICAL_QA: PREP_READY
  - G3_VISUAL_OVERLAY_QA: BLOCKED_REVIEW_REQUIRED
  - G4_PSD_IMPORT_PREP: PREP_ONLY_BLOCKED
  - G5_MATERIAL_ACCEPTANCE: BLOCKED
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - not_owner_approval: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: G2-G5 material QA can be prepared as a checklist and technical validation packet, but B4/B5 Codex triage blocks material acceptance, ParamHairFront, Mini Cubism, and real Cubism.
next_action: Run only G2 layer-manifest technical QA from the corrected 64-part manifest; resolve B4/B5 hard/hold review before G4 PSD promotion or G5 material acceptance.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G2-LAYER-MANIFEST-TECHNICAL-QA-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G2-LAYER-MANIFEST-TECHNICAL-QA-001
date: 2026-06-10
owner: Codex
status: G2_LAYER_MANIFEST_TECHNICAL_QA_PASS_MATERIAL_STILL_BLOCKED
hypothesis: The corrected 64-part manifest can pass file/manifest technical QA while preserving visual, material, Mini Cubism, and real Cubism gates.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_64part_corrected_b4_b5_manifest/v22_64part_corrected_b4_b5_manifest.json
  - experiments/cubism-v2-new-character-002/reports/v22_g2_g5_material_qa_prep/v22_g2_g5_material_qa_prep_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_64part_generation_spec/v22_64part_generation_spec.json
output:
  - scripts/build_cubism_v2_g2_layer_manifest_technical_qa_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g2_layer_manifest_technical_qa/v22_g2_layer_manifest_technical_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_g2_layer_manifest_technical_qa/v22_g2_layer_manifest_technical_qa_report.md
metric:
  - required_part_count: 64
  - manifest_entry_count: 64
  - unique_manifest_part_count: 64
  - missing_part_count: 0
  - extra_part_count: 0
  - duplicate_part_count: 0
  - failed_entry_count: 0
  - group_counts_match_spec: true
  - forbidden_reuse_path_hit_count: 0
  - sha256_recorded_count: 64
  - active_controls_match_v21_supported_subset: true
  - eye_open_027_policy_present: true
  - mouth_open_085_policy_present: true
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - material_pass_status: BLOCKED
  - g3_visual_overlay_status: BLOCKED_REVIEW_REQUIRED
  - g4_psd_import_prep_status: PREP_ONLY_BLOCKED
  - g5_material_acceptance_status: BLOCKED
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: G2 layer-manifest technical QA passes for the corrected 64-part manifest, but this is technical evidence only. It does not promote visual QA, material acceptance, Mini Cubism, or real Cubism.
next_action: Keep G3 visual overlay QA blocked until B4/B5 hard and hold review rows are resolved; do not build/promote import_ready.psd from this QA alone.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G3-B4-B5-BLOCKER-REDUCTION-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G3-B4-B5-BLOCKER-REDUCTION-001
date: 2026-06-10
owner: Codex
status: G3_B4_B5_BLOCKER_REDUCTION_PACKET_READY_PRIMARY_10_MATERIAL_BLOCKED
hypothesis: After G2 technical QA passes, B4/B5 G3 visual blocker work can be narrowed into primary, secondary, and context routes without claiming visual PASS.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_64part_corrected_b4_b5_manifest/v22_corrected_b4_b5_codex_visual_triage.json
  - experiments/cubism-v2-new-character-002/reports/v22_g2_layer_manifest_technical_qa/v22_g2_layer_manifest_technical_qa_report.json
output:
  - scripts/build_cubism_v2_g3_b4_b5_blocker_reduction_packet_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g3_b4_b5_blocker_reduction/v22_g3_b4_b5_blocker_reduction_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g3_b4_b5_blocker_reduction/v22_g3_b4_b5_blocker_reduction_packet.md
  - experiments/cubism-v2-new-character-002/reports/v22_g3_b4_b5_blocker_reduction/v22_g3_b4_b5_blocker_reduction_sheet.png
metric:
  - blocker_row_count: 24
  - primary_blocker_count: 10
  - secondary_blocker_count: 7
  - context_review_count: 7
  - priority_counts:
      P0: 1
      P1: 9
      P2: 7
      P3: 7
  - route_counts:
      B5_TORSO_MINIPASS_V2_OR_HUMAN_ACCEPT_REQUIRED: 1
      B4_SECONDARY_HAIR_DRAW_ORDER_OR_MASK_REVIEW: 9
      B5_BODY_CLOTHING_STACK_CONTEXT_REVIEW: 7
      B5_FACE_MICRO_DETAIL_CONTEXT_REVIEW: 7
  - auto_candidate_count_preserved: 9
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g3_visual_overlay_status: BLOCKED_PRIMARY_REVIEW_REQUIRED
  - g4_psd_import_prep_status: PREP_ONLY_BLOCKED
  - g5_material_acceptance_status: BLOCKED
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - not_owner_approval: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: G3 blocker work is reduced to 10 primary visual blockers first: one torso hard review plus nine B4 secondary hair draw-order/mask rows. Seven B5 body/clothing rows and seven B5 face micro-detail rows remain for later context review.
next_action: Resolve P0 torso first, then P1 B4 secondary hair rows; do not promote material PASS, ParamHairFront, Mini Cubism, or real Cubism from this packet.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-P0-TORSO-MINIPASS-V2-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-P0-TORSO-MINIPASS-V2-001
date: 2026-06-10
owner: Codex
status: P0_TORSO_MINIPASS_V2_CANDIDATE_READY_FOR_G3_REVIEW
hypothesis: The P0 torso blocker can be reduced from broad regenerated underpaint into a tighter review candidate while keeping G3 and material gates blocked.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_b5_provisional_minipass_candidate/v22_b5_provisional_minipass_candidate_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_g3_b4_b5_blocker_reduction/v22_g3_b4_b5_blocker_reduction_packet.json
  - experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png
  - experiments/cubism-v2-new-character-002/v22_b5_body_clothing_pack/raw_outputs/b5_body_clothing_pack_reference_001.png
output:
  - scripts/build_cubism_v2_g3_p0_torso_minipass_v2_002.py
  - experiments/cubism-v2-new-character-002/v22_b5_p0_torso_minipass_v2_candidate/normalized_layers/torso_base.png
  - experiments/cubism-v2-new-character-002/reports/v22_g3_p0_torso_minipass_v2/v22_g3_p0_torso_minipass_v2_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_g3_p0_torso_minipass_v2/v22_g3_p0_torso_minipass_v2_report.md
  - experiments/cubism-v2-new-character-002/reports/v22_g3_p0_torso_minipass_v2/v22_g3_p0_torso_minipass_v2_overlay_qa.png
  - experiments/cubism-v2-new-character-002/reports/v22_g3_p0_torso_minipass_v2/v22_g3_p0_torso_minipass_v2_contact_sheet.png
metric:
  - entry_count: 17
  - old_alpha_coverage: 0.20855403
  - new_alpha_coverage: 0.05906725
  - alpha_sum_ratio: 0.357488
  - old_bbox: [534, 915, 1547, 1927]
  - new_bbox: [504, 874, 1500, 1342]
  - torso_improvement_candidate: true
  - verdict: P0_TORSO_MINIPASS_V2_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED
  - all_layers_rgba: true
  - all_layers_2048: true
  - all_layers_nonempty: true
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g3_visual_overlay_status: BLOCKED_PRIMARY_REVIEW_REQUIRED
  - g4_psd_import_prep_status: PREP_ONLY_BLOCKED
  - g5_material_acceptance_status: BLOCKED
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - not_owner_approval: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: P0 torso minipass v2 is an improvement candidate because alpha is tighter and source-aligned, but it remains review-required and cannot promote material PASS.
next_action: Use the v2 torso QA sheet to decide whether to rebuild the corrected 64-part manifest with this torso candidate; keep G3 visual overlay blocked until P0 and P1 rows are resolved.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-P0-TORSO-V2-64PART-MANIFEST-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-P0-TORSO-V2-64PART-MANIFEST-001
date: 2026-06-10
owner: Codex
status: G3_P0_TORSO_V2_64PART_MANIFEST_TECHNICAL_PASS_REVIEW_REQUIRED
hypothesis: The P0 torso v2 candidate can be integrated into a separate 64-part manifest variant without changing the corrected baseline manifest or unlocking material promotion.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_64part_corrected_b4_b5_manifest/v22_64part_corrected_b4_b5_manifest.json
  - experiments/cubism-v2-new-character-002/reports/v22_g3_p0_torso_minipass_v2/v22_g3_p0_torso_minipass_v2_report.json
  - experiments/cubism-v2-new-character-002/v22_b5_p0_torso_minipass_v2_candidate/normalized_layers/torso_base.png
output:
  - scripts/build_cubism_v2_64part_p0_torso_v2_manifest_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_64part_p0_torso_v2_manifest/v22_64part_p0_torso_v2_manifest.json
  - experiments/cubism-v2-new-character-002/reports/v22_64part_p0_torso_v2_manifest/v22_64part_p0_torso_v2_manifest.md
  - experiments/cubism-v2-new-character-002/reports/v22_64part_p0_torso_v2_manifest/v22_64part_p0_torso_v2_manifest_contact_sheet.png
metric:
  - required_part_count: 64
  - manifest_entry_count: 64
  - unique_manifest_part_count: 64
  - missing_part_count: 0
  - wrong_mode_count: 0
  - wrong_size_count: 0
  - empty_part_count: 0
  - duplicate_part_count: 0
  - group_counts_match_spec: true
  - b5_p0_torso_v2_candidate_count: 1
  - p0_torso_v2_verdict: P0_TORSO_MINIPASS_V2_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED
  - p0_torso_alpha_sum_ratio: 0.357488
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g3_visual_overlay_status: REVIEW_REQUIRED
  - g4_psd_import_prep_status: PREP_ONLY_BLOCKED
  - g5_material_acceptance_status: BLOCKED
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - not_owner_approval: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: The P0 torso v2 manifest variant is technically complete and preserves all material/rig gates, but remains review-required.
next_action: Run P0 torso v2 manifest overlay QA and continue G3 blocker reduction; do not promote G4/G5, ParamHairFront, Mini Cubism, or real Cubism.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-P0-TORSO-V2-MANIFEST-OVERLAY-QA-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-P0-TORSO-V2-MANIFEST-OVERLAY-QA-001
date: 2026-06-10
owner: Codex
status: G3_P0_TORSO_V2_MANIFEST_OVERLAY_QA_REVIEW_REQUIRED
hypothesis: Overlay QA for the P0 torso v2 manifest variant can reduce the torso hard blocker into a review candidate while preserving the remaining B4/B5 review gates.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_64part_p0_torso_v2_manifest/v22_64part_p0_torso_v2_manifest.json
  - experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png
output:
  - scripts/build_cubism_v2_p0_torso_v2_manifest_overlay_qa_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_64part_p0_torso_v2_manifest/v22_p0_torso_v2_manifest_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_64part_p0_torso_v2_manifest/v22_p0_torso_v2_manifest_overlay_qa_report.md
  - experiments/cubism-v2-new-character-002/reports/v22_64part_p0_torso_v2_manifest/v22_p0_torso_v2_manifest_overlay_qa.png
metric:
  - qa_entry_count: 33
  - b4_entry_count: 16
  - b5_entry_count: 17
  - b4_front_hair_candidate_count: 7
  - b4_secondary_review_count: 9
  - b5_shoulder_improvement_candidate_count: 2
  - b5_torso_p0_v2_candidate_count: 1
  - b5_torso_p0_v2_verdict: B5_TORSO_P0_V2_IMPROVEMENT_CANDIDATE_REVIEW_REQUIRED
  - b5_copied_layer_review_count: 14
  - overlay_sheet_exists: true
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g4_psd_import_prep_status: PREP_ONLY_BLOCKED
  - g5_material_acceptance_status: BLOCKED
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - not_owner_approval: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: P0 torso v2 overlay QA marks torso as an improvement candidate and keeps all other B4/B5 review gates visible; this is not material PASS.
next_action: Continue G3 blocker reduction with the nine P1 B4 secondary hair rows, while keeping G4/G5, ParamHairFront, G7, and G8 blocked.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G3-P1-B4-SECONDARY-HAIR-REDUCTION-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G3-P1-B4-SECONDARY-HAIR-REDUCTION-001
date: 2026-06-10
owner: Codex
status: G3_P1_B4_SECONDARY_HAIR_REDUCTION_PACKET_READY_REVIEW_REQUIRED
hypothesis: The nine P1 B4 secondary-hair rows can be routed into a smaller focused follow-up set without claiming visual or material acceptance.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_64part_p0_torso_v2_manifest/v22_p0_torso_v2_manifest_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_hair_focused_review/v22_b4_hair_focused_review.json
output:
  - scripts/build_cubism_v2_g3_p1_b4_secondary_hair_reduction_packet_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g3_p1_b4_secondary_hair_reduction/v22_g3_p1_b4_secondary_hair_reduction_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g3_p1_b4_secondary_hair_reduction/v22_g3_p1_b4_secondary_hair_reduction_packet.md
  - experiments/cubism-v2-new-character-002/reports/v22_g3_p1_b4_secondary_hair_reduction/v22_g3_p1_b4_secondary_hair_reduction_sheet.png
metric:
  - p1_input_count: 9
  - remaining_primary_count: 2
  - reduced_to_context_count: 7
  - anchor_mask_review_count: 2
  - back_stack_context_candidate_count: 3
  - side_hair_low_alpha_context_candidate_count: 4
  - route_counts:
      B4_BACK_STACK_DRAW_ORDER_CONTEXT_CANDIDATE_REVIEW_REQUIRED: 3
      B4_BACK_STRAND_ANCHOR_MASK_REVIEW_REQUIRED: 2
      B4_SIDE_HAIR_LOW_ALPHA_CONTEXT_CANDIDATE_REVIEW_REQUIRED: 4
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g3_visual_overlay_status: P1_REDUCED_REVIEW_REQUIRED
  - g4_psd_import_prep_status: PREP_ONLY_BLOCKED
  - g5_material_acceptance_status: BLOCKED
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - not_owner_approval: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: P1 B4 secondary-hair work is reduced from nine equal blockers to two anchor/mask priority rows plus seven context candidates; this is not visual PASS.
next_action: Handle `hair_back_strand_L` and `hair_back_strand_R` first, then build a combined G3 visual overlay review while keeping G4/G5, ParamHairFront, G7, and G8 blocked.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G3-P1A-B4-BACK-STRAND-ANCHOR-MASK-PROBE-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G3-P1A-B4-BACK-STRAND-ANCHOR-MASK-PROBE-001
date: 2026-06-10
owner: Codex
status: G3_P1A_B4_BACK_STRAND_ANCHOR_MASK_NUMERIC_PASS_CONTEXT_REVIEW_REQUIRED
hypothesis: The two remaining P1A B4 back-strand rows can be lowered from primary blockers to context review if saved no-op anchor evidence and mask-support metrics pass.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_g3_p1_b4_secondary_hair_reduction/v22_g3_p1_b4_secondary_hair_reduction_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_b4_hair_focused_review/v22_b4_hair_focused_review.json
  - experiments/cubism-v2-new-character-002/v22_b4_b5_anchor_corrected_auto_draft/normalized_layers/hair_back_strand_L.png
  - experiments/cubism-v2-new-character-002/v22_b4_b5_anchor_corrected_auto_draft/normalized_layers/hair_back_strand_R.png
output:
  - scripts/build_cubism_v2_g3_p1a_b4_back_strand_anchor_mask_probe_002.py
  - experiments/cubism-v2-new-character-002/v22_b4_p1a_back_strand_anchor_mask_probe/normalized_layers/
  - experiments/cubism-v2-new-character-002/reports/v22_g3_p1a_b4_back_strand_anchor_mask_probe/v22_g3_p1a_b4_back_strand_anchor_mask_probe_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_g3_p1a_b4_back_strand_anchor_mask_probe/v22_g3_p1a_b4_back_strand_anchor_mask_probe_report.md
  - experiments/cubism-v2-new-character-002/reports/v22_g3_p1a_b4_back_strand_anchor_mask_probe/v22_g3_p1a_b4_back_strand_anchor_mask_probe_overrides.json
  - experiments/cubism-v2-new-character-002/reports/v22_g3_p1a_b4_back_strand_anchor_mask_probe/v22_g3_p1a_b4_back_strand_anchor_mask_probe_sheet.png
metric:
  - target_count: 2
  - numeric_pass_count: 2
  - anchor_numeric_pass_count: 2
  - mask_support_numeric_pass_count: 2
  - sha256_unchanged_count: 2
  - remaining_primary_after_probe_count: 0
  - context_candidate_after_probe_count: 2
  - all_layers_rgba: true
  - all_layers_2048: true
  - all_layers_nonempty: true
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g3_visual_overlay_status: CONTEXT_REVIEW_REQUIRED_NOT_VISUAL_PASS
  - g4_psd_import_prep_status: PREP_ONLY_BLOCKED
  - g5_material_acceptance_status: BLOCKED
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - not_owner_approval: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: Both P1A back-strand rows have no-op anchor evidence and numeric mask support, so they can move to context review; this is not visual PASS.
next_action: Build the combined G3 context overlay before any G4/G5 material promotion attempt.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G3-COMBINED-CONTEXT-OVERLAY-REVIEW-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G3-COMBINED-CONTEXT-OVERLAY-REVIEW-001
date: 2026-06-10
owner: Codex
status: G3_COMBINED_CONTEXT_OVERLAY_REVIEW_READY_MATERIAL_BLOCKED
hypothesis: After P0 torso v2 and P1A back-strand reduction, all B4/B5 G3 rows can be presented as context review with zero primary blocker rows while preserving material and rig gates.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_64part_p0_torso_v2_manifest/v22_p0_torso_v2_manifest_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_g3_p1_b4_secondary_hair_reduction/v22_g3_p1_b4_secondary_hair_reduction_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g3_p1a_b4_back_strand_anchor_mask_probe/v22_g3_p1a_b4_back_strand_anchor_mask_probe_report.json
output:
  - scripts/build_cubism_v2_g3_combined_context_overlay_review_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g3_combined_context_overlay_review/v22_g3_combined_context_overlay_review_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_g3_combined_context_overlay_review/v22_g3_combined_context_overlay_review_report.md
  - experiments/cubism-v2-new-character-002/reports/v22_g3_combined_context_overlay_review/v22_g3_combined_context_overlay_review.png
metric:
  - qa_entry_count: 33
  - primary_remaining_count: 0
  - context_review_count: 33
  - classification_counts:
      G3_CONTEXT_FRONT_HAIR_MOTION_CANDIDATE_KEEP_HAIRFRONT_HIDDEN: 7
      G3_CONTEXT_BACK_STACK_DRAW_ORDER_REVIEW_REQUIRED: 3
      G3_CONTEXT_BACK_STRAND_NUMERIC_PASS_REVIEW_REQUIRED: 2
      G3_CONTEXT_SIDE_HAIR_LOW_ALPHA_REVIEW_REQUIRED: 4
      G3_CONTEXT_TORSO_P0_V2_REVIEW_REQUIRED: 1
      G3_CONTEXT_SHOULDER_IMPROVEMENT_REVIEW_REQUIRED: 2
      G3_CONTEXT_B5_BODY_CLOTHING_STACK_REVIEW_REQUIRED: 7
      G3_CONTEXT_B5_FACE_MICRO_DETAIL_REVIEW_REQUIRED: 7
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g3_visual_overlay_status: COMBINED_CONTEXT_REVIEW_REQUIRED_NOT_PASS
  - g4_psd_import_prep_status: PREP_ONLY_BLOCKED
  - g5_material_acceptance_status: BLOCKED
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - not_owner_approval: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: B4/B5 primary blockers are reduced to zero for this context overlay, but all 33 rows remain context-review evidence; this is not material PASS.
next_action: Use the combined overlay as the G3 context-review surface before G4/G5, keeping ParamHairFront, G7, and G8 blocked.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G4-G5-MATERIAL-PROMOTION-READINESS-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G4-G5-MATERIAL-PROMOTION-READINESS-001
date: 2026-06-10
owner: Codex
status: G4_G5_MATERIAL_PROMOTION_READINESS_BLOCKED_CONTEXT_REVIEW
hypothesis: After G3 primary blockers are reduced to zero, G4/G5 can be evaluated as a readiness matrix while still blocking material promotion until B1-B5 visual/context review is accepted separately.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_64part_p0_torso_v2_manifest/v22_64part_p0_torso_v2_manifest.json
  - experiments/cubism-v2-new-character-002/reports/v22_g3_combined_context_overlay_review/v22_g3_combined_context_overlay_review_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_visual_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack_revision_v1/v22_b3_revision_v1_overlay_qa_report.json
output:
  - scripts/build_cubism_v2_g4_g5_material_promotion_readiness_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g4_g5_material_promotion_readiness/v22_g4_g5_material_promotion_readiness_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_g4_g5_material_promotion_readiness/v22_g4_g5_material_promotion_readiness_report.md
metric:
  - required_part_count: 64
  - manifest_entry_count: 64
  - technical_manifest_pass: true
  - b1_b3_human_review_required_count: 3
  - b4_b5_primary_remaining_count: 0
  - b4_b5_context_review_count: 33
  - promotion_blocker_count: 2
  - promotion_blockers:
      - B1_B2_B3_PASS_CANDIDATES_STILL_HUMAN_REVIEW_REQUIRED
      - B4_B5_COMBINED_CONTEXT_REVIEW_REQUIRED
  - g4_contact_sheet_visual_qa_status: READY_FOR_REVIEW_NOT_PASS
  - g5_material_acceptance_status: BLOCKED_CONTEXT_REVIEW_NOT_OWNER_APPROVAL
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - validator_only_promotion_blocked: true
  - not_owner_approval: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: G4/G5 material promotion is blocked despite technical readiness because B1-B3 remain pass-candidate/human-review-required and B4/B5 remain combined context-review evidence.
next_action: Build or use a compact G4 visual review surface before any separate G5 material acceptance packet; keep ParamHairFront, G7, and G8 blocked.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G4-COMPACT-VISUAL-REVIEW-SURFACE-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G4-COMPACT-VISUAL-REVIEW-SURFACE-001
date: 2026-06-10
owner: Codex
status: G4_COMPACT_VISUAL_REVIEW_SURFACE_READY_NOT_PASS
hypothesis: A compact G4 review surface can combine B1-B5 visual evidence into one review artifact while preserving the material acceptance block.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_g4_g5_material_promotion_readiness/v22_g4_g5_material_promotion_readiness_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_layer_pack_overlay_qa.png
  - experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_overlay_qa_on_b1_clean_base.png
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack_revision_v1/v22_b3_revision_v1_overlay_qa.png
  - experiments/cubism-v2-new-character-002/reports/v22_g3_combined_context_overlay_review/v22_g3_combined_context_overlay_review.png
  - experiments/cubism-v2-new-character-002/reports/v22_64part_p0_torso_v2_manifest/v22_64part_p0_torso_v2_manifest_contact_sheet.png
output:
  - scripts/build_cubism_v2_g4_compact_visual_review_surface_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g4_compact_visual_review_surface/v22_g4_compact_visual_review_surface_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_g4_compact_visual_review_surface/v22_g4_compact_visual_review_surface_report.md
  - experiments/cubism-v2-new-character-002/reports/v22_g4_compact_visual_review_surface/v22_g4_compact_visual_review_surface.png
metric:
  - review_item_count: 5
  - b1_b3_item_count: 3
  - b4_b5_context_item_count: 1
  - manifest_contact_item_count: 1
  - source_image_count: 5
  - source_report_count: 5
  - manifest_entry_count: 64
  - b4_b5_primary_remaining_count: 0
  - b4_b5_context_review_count: 33
  - promotion_blocker_count: 2
  - g4_visual_review_status: READY_FOR_VISUAL_ACCEPTANCE_NOT_PASS
  - g5_material_acceptance_status: BLOCKED_CONTEXT_REVIEW_NOT_OWNER_APPROVAL
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - requires_visual_acceptance: true
  - validator_only_promotion_blocked: true
  - not_owner_approval: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: Compact G4 visual review surface is ready, but it is not material PASS and cannot unlock G5, ParamHairFront, G7, or G8.
next_action: Use this sheet for visual acceptance review of B1-B5 as a set; only then create a separate G5 material acceptance packet.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G4-VISUAL-DECISION-PACKET-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G4-VISUAL-DECISION-PACKET-001
date: 2026-06-10
owner: Codex
status: G4_VISUAL_DECISION_PACKET_READY_PENDING_REVIEW_MATERIAL_BLOCKED
hypothesis: The compact G4 visual surface can be converted into a repeatable decision packet without promoting visual or material PASS.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_g4_compact_visual_review_surface/v22_g4_compact_visual_review_surface_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_g4_g5_material_promotion_readiness/v22_g4_g5_material_promotion_readiness_report.json
output:
  - scripts/build_cubism_v2_g4_visual_decision_packet_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g4_visual_decision_packet/v22_g4_visual_decision_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g4_visual_decision_packet/v22_g4_visual_decision_packet.md
  - experiments/cubism-v2-new-character-002/reports/v22_g4_visual_decision_packet/v22_g4_visual_decision_template.json
  - experiments/cubism-v2-new-character-002/reports/v22_g4_visual_decision_packet/v22_g4_visual_decision_smoke.json
metric:
  - decision_item_count: 5
  - pending_visual_review_count: 5
  - accepted_visual_candidate_count: 0
  - revise_before_g5_count: 0
  - regenerate_batch_or_context_count: 0
  - expected_review_items_present: true
  - allowed_visual_decision_values_checked: true
  - smoke_decision_values_checked: true
  - all_decisions_pending: true
  - all_source_images_exist: true
  - all_source_reports_exist: true
  - template_decision_count: 5
  - smoke_decision_count: 5
  - g4_visual_review_status: PENDING_VISUAL_REVIEW_NOT_PASS
  - g5_material_acceptance_status: BLOCKED_CONTEXT_REVIEW_NOT_OWNER_APPROVAL
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - requires_visual_acceptance: true
  - requires_separate_g5_acceptance: true
  - validator_only_promotion_blocked: true
  - not_owner_approval: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: The G4 visual decision packet is ready with five pending review rows. It records allowed decisions and follow-up routes, but it is not owner approval and does not grant material PASS.
next_action: Use the decision template or a later UI to record G4 visual decisions; if rows are accepted, create a separate G5 material acceptance packet rather than promoting from this G4 packet.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G4-CODEX-PROVISIONAL-VISUAL-DECISIONS-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G4-CODEX-PROVISIONAL-VISUAL-DECISIONS-001
date: 2026-06-10
owner: Codex
status: G4_CODEX_PROVISIONAL_VISUAL_DECISIONS_READY_NO_OWNER_APPROVAL
hypothesis: Current success-pattern evidence can seed a non-owner G4 visual route without granting G5 material acceptance.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_g4_visual_decision_packet/v22_g4_visual_decision_packet.json
output:
  - scripts/build_cubism_v2_g4_codex_provisional_visual_decisions_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g4_visual_decision_packet/v22_g4_codex_provisional_visual_decisions.json
  - experiments/cubism-v2-new-character-002/reports/v22_g4_visual_decision_packet/v22_g4_codex_provisional_visual_decisions.md
metric:
  - decision_count: 5
  - pending_count: 0
  - accepted_visual_candidate_count: 4
  - revise_before_g5_count: 1
  - regenerate_batch_or_context_count: 0
  - has_b4_b5_revise_gate: true
  - g4_visual_review_status: CODEX_PROVISIONAL_REVIEW_READY_NOT_OWNER_APPROVAL
  - g5_material_acceptance_status: BLOCKED_CONTEXT_REVIEW_NOT_OWNER_APPROVAL
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - validator_only_promotion_blocked: true
  - not_owner_approval: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: B1, B2, B3, and the 64-part contact sheet are kept as visual candidates only, while B4/B5 combined context routes to focused revision before G5.
next_action: Run the G4 visual decision route planner with this Codex provisional file and resolve B4/B5 focused follow-up before any G5 material acceptance packet.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G4-VISUAL-DECISION-ROUTE-PLAN-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G4-VISUAL-DECISION-ROUTE-PLAN-001
date: 2026-06-10
owner: Codex
status: G4_VISUAL_DECISION_ROUTE_PLAN_READY_FOR_FOCUSED_FOLLOWUP_MATERIAL_BLOCKED
hypothesis: The G4 Codex provisional decisions can be validated into a focused route plan that blocks G5 until B4/B5 context follow-up is resolved.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_g4_visual_decision_packet/v22_g4_visual_decision_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g4_visual_decision_packet/v22_g4_codex_provisional_visual_decisions.json
output:
  - scripts/build_cubism_v2_g4_visual_decision_route_plan_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g4_visual_decision_packet/v22_g4_visual_decision_route_plan.json
  - experiments/cubism-v2-new-character-002/reports/v22_g4_visual_decision_packet/v22_g4_visual_decision_route_plan.md
metric:
  - decision_item_count: 5
  - decision_row_count: 5
  - pending_count: 0
  - accepted_visual_candidate_count: 4
  - revise_before_g5_count: 1
  - regenerate_batch_or_context_count: 0
  - invalid_decision_count: 0
  - route_counts:
      KEEP_AS_G4_VISUAL_CANDIDATE: 4
      ROUTE_TO_B4_B5_FOCUSED_FOLLOWUP_BEFORE_G5: 1
  - g4_visual_review_status: ROUTE_PLANNED_NOT_MATERIAL_PASS
  - g5_material_acceptance_status: BLOCKED_PENDING_FOCUSED_G4_FOLLOWUP
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - has_focused_followup_path: true
  - validator_only_promotion_blocked: true
  - not_owner_approval: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: G4 can proceed into focused follow-up routing, but not into G5 material acceptance, because B4/B5 combined context still requires focused work.
next_action: Apply only the focused B4/B5 follow-up route, then regenerate the G4/G5 readiness evidence before any G5 material acceptance packet.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G4-B4-B5-FOCUSED-FOLLOWUP-PACKET-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G4-B4-B5-FOCUSED-FOLLOWUP-PACKET-001
date: 2026-06-10
owner: Codex
status: G4_B4_B5_FOCUSED_FOLLOWUP_PACKET_READY_MATERIAL_BLOCKED
hypothesis: The single G4 B4/B5 follow-up route can be expanded into reproducible row-level work lanes while keeping all material and rig gates blocked.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_g4_visual_decision_packet/v22_g4_visual_decision_route_plan.json
  - experiments/cubism-v2-new-character-002/reports/v22_g3_combined_context_overlay_review/v22_g3_combined_context_overlay_review_report.json
output:
  - scripts/build_cubism_v2_g4_b4_b5_focused_followup_packet_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g4_b4_b5_focused_followup/v22_g4_b4_b5_focused_followup_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g4_b4_b5_focused_followup/v22_g4_b4_b5_focused_followup_packet.md
  - experiments/cubism-v2-new-character-002/reports/v22_g4_b4_b5_focused_followup/v22_g4_b4_b5_focused_followup_sheet.png
metric:
  - followup_row_count: 33
  - pre_g5_focused_followup_count: 3
  - motion_readiness_followup_count: 7
  - context_review_followup_count: 23
  - lane_counts:
      P0_PRE_G5_B5_SHOULDER_DRAW_ORDER_MASK_FOLLOWUP: 2
      P0_PRE_G5_B5_TORSO_VISUAL_FOLLOWUP: 1
      P1_B4_FRONT_HAIR_MOTION_READINESS_KEEP_HAIRFRONT_HIDDEN: 7
      P2_B4_BACK_STACK_DRAW_ORDER_CONTEXT_REVIEW: 3
      P2_B4_BACK_STRAND_NUMERIC_CONTEXT_REVIEW: 2
      P2_B4_SIDE_HAIR_LOW_ALPHA_CONTEXT_REVIEW: 4
      P3_B5_BODY_CLOTHING_STACK_CONTEXT_REVIEW: 7
      P3_B5_FACE_MICRO_DETAIL_CONTEXT_REVIEW: 7
  - g4_route_status: G4_VISUAL_DECISION_ROUTE_PLAN_READY_FOR_FOCUSED_FOLLOWUP_MATERIAL_BLOCKED
  - combined_g3_status: G3_COMBINED_CONTEXT_OVERLAY_REVIEW_READY_MATERIAL_BLOCKED
  - g5_material_acceptance_status: BLOCKED_PENDING_B4_B5_FOCUSED_FOLLOWUP
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - matches_combined_context_row_count: true
  - has_pre_g5_focused_followup: true
  - has_motion_readiness_followup: true
  - has_context_review_followup: true
  - followup_sheet_exists: true
  - validator_only_promotion_blocked: true
  - not_owner_approval: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: B4/B5 focused follow-up is now a row-level work-order packet, not a visual acceptance or G5 material acceptance packet.
next_action: Handle the P0 B5 torso/shoulder focused follow-up rows first, keep B4 front hair as motion-readiness candidates with ParamHairFront hidden, and refresh G4/G5 readiness only after focused follow-up evidence exists.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G4-P0-B5-FOLLOWUP-DECISION-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G4-P0-B5-FOLLOWUP-DECISION-001
date: 2026-06-10
owner: Codex
status: G4_P0_B5_FOLLOWUP_DECISION_READY_TORSO_REVIEW_REMAINING_MATERIAL_BLOCKED
hypothesis: The three P0 B5 pre-G5 rows can be narrowed to one torso review/regeneration blocker because shoulder draw-order/mask evidence has improved enough to carry as G4 refresh candidates.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_g4_b4_b5_focused_followup/v22_g4_b4_b5_focused_followup_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_body_blocker_draw_order_review/v22_b5_body_blocker_draw_order_review.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_provisional_minipass_candidate/v22_b5_provisional_minipass_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_g3_p0_torso_minipass_v2/v22_g3_p0_torso_minipass_v2_report.json
output:
  - scripts/build_cubism_v2_g4_p0_b5_followup_decision_packet_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g4_p0_b5_followup_decision/v22_g4_p0_b5_followup_decision_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g4_p0_b5_followup_decision/v22_g4_p0_b5_followup_decision_packet.md
  - experiments/cubism-v2-new-character-002/reports/v22_g4_p0_b5_followup_decision/v22_g4_p0_b5_followup_decision_sheet.png
metric:
  - input_pre_g5_followup_count: 3
  - decision_row_count: 3
  - torso_review_remaining_count: 1
  - shoulder_g4_refresh_candidate_count: 2
  - pre_g5_remaining_count: 1
  - pre_g5_resolved_to_candidate_count: 2
  - pre_g5_reduced_from_3_to_1: true
  - shoulder_L_overlap_before: 0.870193
  - shoulder_L_overlap_after: 0.0
  - shoulder_R_overlap_before: 0.868247
  - shoulder_R_overlap_after: 0.0
  - torso_decision: P0_TORSO_REVIEW_OR_REGENERATE_BEFORE_G5
  - shoulder_decision: P0_SHOULDER_ACCEPT_AS_DRAW_ORDER_MASK_CANDIDATE_KEEP_MATERIAL_BLOCKED
  - g5_material_acceptance_status: BLOCKED_PENDING_TORSO_REVIEW_OR_REGENERATION
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - validator_only_promotion_blocked: true
  - not_owner_approval: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: P0 B5 follow-up is narrowed from three pre-G5 rows to one torso review/regeneration blocker. Shoulders are only G4 refresh candidates, not visual or material PASS.
next_action: Handle `torso_base` as the remaining P0 pre-G5 visual review/regeneration row, then rebuild G4/G5 readiness with shoulders treated as candidates only.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G4-TORSO-BASE-REGEN-REVIEW-PACKET-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G4-TORSO-BASE-REGEN-REVIEW-PACKET-001
date: 2026-06-10
owner: Codex
status: G4_TORSO_BASE_REGEN_REVIEW_PACKET_READY_MATERIAL_BLOCKED
hypothesis: The remaining pre-G5 blocker can be isolated to a single torso_base regeneration/review input packet without promoting the current P0 v2 alpha-tight candidate to material PASS.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_g4_p0_b5_followup_decision/v22_g4_p0_b5_followup_decision_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g3_p0_torso_minipass_v2/v22_g3_p0_torso_minipass_v2_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_provisional_minipass_input_packet/v22_b5_provisional_minipass_input_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_provisional_minipass_candidate/v22_b5_provisional_minipass_overlay_qa_report.json
output:
  - scripts/build_cubism_v2_g4_torso_base_regen_review_packet_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g4_torso_base_regen_review_packet/v22_g4_torso_base_regen_review_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g4_torso_base_regen_review_packet/v22_g4_torso_base_regen_review_packet.md
  - experiments/cubism-v2-new-character-002/reports/v22_g4_torso_base_regen_review_packet/v22_g4_torso_base_regen_input_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g4_torso_base_regen_review_packet/v22_g4_torso_base_regen_review_sheet.png
metric:
  - target_part: torso_base
  - remaining_pre_g5_blocker_count: 1
  - old_v2_alpha_coverage: 0.14019799
  - provisional_alpha_coverage: 0.20855403
  - p0_v2_alpha_coverage: 0.05906725
  - coverage_ratio_p0_to_old: 0.4213131
  - recommended_route: REGENERATE_OR_FOCUSED_VISUAL_ACCEPT_TORSO_BEFORE_G5
  - default_codex_route: REGENERATE_TORSO_BASE_BODY_UNDERPAINT_INPUT_READY
  - regen_input_status: TORSO_BASE_REGEN_INPUT_READY_MATERIAL_BLOCKED
  - g5_material_acceptance_status: BLOCKED_PENDING_TORSO_REVIEW_OR_REGENERATION
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - all_candidate_paths_exist: true
  - all_candidates_rgba_2048: true
  - p0_is_tighter_than_old_v2: true
  - prompt_present: true
  - acceptance_checks_present: true
  - validator_only_promotion_blocked: true
  - not_owner_approval: true
  - mini_cubism_not_promoted: true
  - real_cubism_not_promoted: true
  - self_review: PASS
decision: torso_base remains the only pre-G5 blocker. P0 v2 is alpha-tighter than old v2, but the safe default route is focused torso_base regeneration/review input, not material acceptance.
next_action: Use the regen input packet to generate or review one torso_base replacement candidate, normalize it as full-canvas 2048 RGBA, and rerun overlay QA before G5.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G4-TORSO-BASE-REGEN-CANDIDATE-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G4-TORSO-BASE-REGEN-CANDIDATE-001
date: 2026-06-10
owner: Codex
status: G4_TORSO_BASE_REGEN_CANDIDATE_READY_FOR_OVERLAY_QA_MATERIAL_BLOCKED
hypothesis: A focused generated torso_base underpaint can be normalized into a full-canvas 2048 RGBA review candidate without promoting it to material PASS or unlocking G5.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_g4_torso_base_regen_review_packet/v22_g4_torso_base_regen_input_packet.json
  - experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png
  - experiments/cubism-v2-new-character-002/v22_g4_torso_base_regen_candidate/raw_outputs/torso_base_regen_reference_001.png
  - experiments/cubism-v2-new-character-002/v22_g4_torso_base_regen_candidate/normalized_layers/torso_base_generated_alpha_candidate.png
output:
  - scripts/build_cubism_v2_g4_torso_base_regen_candidate_002.py
  - experiments/cubism-v2-new-character-002/v22_g4_torso_base_regen_candidate/normalized_layers/torso_base.png
  - experiments/cubism-v2-new-character-002/reports/v22_g4_torso_base_regen_candidate/v22_g4_torso_base_regen_candidate_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_g4_torso_base_regen_candidate/v22_g4_torso_base_regen_candidate_report.md
  - experiments/cubism-v2-new-character-002/reports/v22_g4_torso_base_regen_candidate/v22_g4_torso_base_regen_candidate_overlay.png
  - experiments/cubism-v2-new-character-002/reports/v22_g4_torso_base_regen_candidate/v22_g4_torso_base_regen_candidate_mask_overlay.png
  - experiments/cubism-v2-new-character-002/reports/v22_g4_torso_base_regen_candidate/v22_g4_torso_base_regen_candidate_contact_sheet.png
metric:
  - input_status: TORSO_BASE_REGEN_INPUT_READY_MATERIAL_BLOCKED
  - full_canvas_mode: RGBA
  - full_canvas_size: [2048, 2048]
  - full_canvas_bbox: [520, 880, 1539, 1688]
  - alpha_coverage: 0.1204493
  - transparent_corners: true
  - crop_contains_bbox: true
  - automated_verdict: PASS_TECHNICAL_CANDIDATE_REVIEW_REQUIRED
  - visual_verdict: PENDING_OVERLAY_QA_REVIEW
  - material_pass_status: BLOCKED
  - g5_status: BLOCKED_PENDING_TORSO_OVERLAY_QA_AND_SEPARATE_G5_ACCEPTANCE
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - not_owner_approval: true
  - self_review: PASS
decision: The generated torso_base is a valid technical review candidate, not material approval. It must go through overlay QA before G5 can be reconsidered.
next_action: Run a focused torso_base overlay QA/triage packet against this generated candidate, then decide whether it replaces P0 v2 or needs another regeneration pass.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G4-TORSO-BASE-REGEN-OVERLAY-QA-ROUTE-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G4-TORSO-BASE-REGEN-OVERLAY-QA-ROUTE-001
date: 2026-06-10
owner: Codex
status: G4_TORSO_BASE_REGEN_OVERLAY_QA_ROUTE_READY_MATERIAL_BLOCKED
hypothesis: The generated torso_base candidate can replace P0 v2 as the next manifest rebuild input when it restores lower underpaint coverage while remaining below the old broad v2 alpha footprint.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_g4_torso_base_regen_candidate/v22_g4_torso_base_regen_candidate_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_g4_torso_base_regen_review_packet/v22_g4_torso_base_regen_review_packet.json
  - experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png
output:
  - scripts/build_cubism_v2_g4_torso_base_regen_overlay_qa_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g4_torso_base_regen_overlay_qa/v22_g4_torso_base_regen_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_g4_torso_base_regen_overlay_qa/v22_g4_torso_base_regen_overlay_qa_report.md
  - experiments/cubism-v2-new-character-002/reports/v22_g4_torso_base_regen_overlay_qa/v22_g4_torso_base_regen_overlay_qa.png
metric:
  - generated_bbox: [520, 880, 1539, 1688]
  - generated_alpha_coverage: 0.1204493
  - p0_v2_alpha_coverage: 0.05906725
  - old_v2_alpha_coverage: 0.14019799
  - generated_vs_p0_bottom_extension_px: 346
  - generated_vs_p0_top_delta_px: 6
  - generated_alpha_ratio_to_p0: 2.038
  - generated_alpha_ratio_to_old: 0.87191864
  - coverage_between_p0_and_old: true
  - generated_under_old_coverage: true
  - crop_contains_generated_bbox: true
  - technical_verdict: PASS_FOCUSED_OVERLAY_ROUTE_CANDIDATE
  - visual_verdict: ROUTE_GENERATED_TORSO_TO_NEXT_REBUILD_REVIEW_REQUIRED
  - route: USE_GENERATED_TORSO_FOR_NEXT_MANIFEST_REBUILD_KEEP_G5_BLOCKED
  - material_pass_status: BLOCKED
  - g5_status: BLOCKED_PENDING_NEXT_MANIFEST_REBUILD_AND_SEPARATE_G5_ACCEPTANCE
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - validator_only_promotion_blocked: true
  - not_owner_approval: true
  - self_review: PASS
decision: Use the generated torso_base as the next manifest rebuild input, but do not unlock G5 or material PASS from this focused overlay route.
next_action: Build a G4 torso-selected 64-part manifest variant that replaces only B5 torso_base with the generated candidate, then rerun corrected B4/B5 overlay QA before any G5 acceptance packet.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G4-TORSO-SELECTED-64PART-MANIFEST-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G4-TORSO-SELECTED-64PART-MANIFEST-001
date: 2026-06-10
owner: Codex
status: G4_TORSO_SELECTED_64PART_MANIFEST_TECHNICAL_PASS_REVIEW_REQUIRED
hypothesis: The generated torso_base selected by focused G4 overlay routing can be applied to a 64-part manifest variant by replacing exactly one B5 entry while preserving technical completeness and material locks.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_g4_torso_base_regen_overlay_qa/v22_g4_torso_base_regen_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/v22_g4_torso_base_regen_candidate/normalized_layers/torso_base.png
  - experiments/cubism-v2-new-character-002/reports/v22_64part_corrected_b4_b5_manifest/v22_64part_corrected_b4_b5_manifest.json
output:
  - scripts/build_cubism_v2_64part_g4_torso_selected_manifest_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_64part_g4_torso_selected_manifest/v22_64part_g4_torso_selected_manifest.json
  - experiments/cubism-v2-new-character-002/reports/v22_64part_g4_torso_selected_manifest/v22_64part_g4_torso_selected_manifest.md
  - experiments/cubism-v2-new-character-002/reports/v22_64part_g4_torso_selected_manifest/v22_64part_g4_torso_selected_manifest_contact_sheet.png
metric:
  - required_part_count: 64
  - manifest_entry_count: 64
  - missing_part_count: 0
  - wrong_mode_count: 0
  - wrong_size_count: 0
  - empty_part_count: 0
  - duplicate_part_count: 0
  - group_counts_match_spec: true
  - g4_torso_selected_replacement_count: 1
  - b5_generated_torso_selected_count: 1
  - generated_torso_bbox: [520, 880, 1539, 1688]
  - generated_torso_alpha_coverage: 0.1204493
  - generated_vs_p0_bottom_extension_px: 346
  - generated_alpha_ratio_to_old: 0.87191864
  - g4_torso_route: USE_GENERATED_TORSO_FOR_NEXT_MANIFEST_REBUILD_KEEP_G5_BLOCKED
  - g5_material_acceptance_status: BLOCKED_PENDING_NEXT_OVERLAY_QA_AND_SEPARATE_G5_ACCEPTANCE
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - validator_only_promotion_blocked: true
  - not_owner_approval: true
  - self_review: PASS
decision: The 64-part manifest is technically complete with the generated torso selected, but remains review-required and cannot unlock G5/material.
next_action: Run G4 torso-selected manifest overlay QA and reduce the remaining B4/B5 review lanes before any G5 acceptance packet.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G4-TORSO-SELECTED-MANIFEST-OVERLAY-QA-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G4-TORSO-SELECTED-MANIFEST-OVERLAY-QA-001
date: 2026-06-10
owner: Codex
status: G4_TORSO_SELECTED_MANIFEST_OVERLAY_QA_REVIEW_REQUIRED_MATERIAL_BLOCKED
hypothesis: Overlay QA for the torso-selected manifest should confirm the generated torso is selected while proving that remaining B4/B5 review lanes still block G5/material promotion.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_64part_g4_torso_selected_manifest/v22_64part_g4_torso_selected_manifest.json
  - experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png
output:
  - scripts/build_cubism_v2_g4_torso_selected_manifest_overlay_qa_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_64part_g4_torso_selected_manifest/v22_g4_torso_selected_manifest_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_64part_g4_torso_selected_manifest/v22_g4_torso_selected_manifest_overlay_qa_report.md
  - experiments/cubism-v2-new-character-002/reports/v22_64part_g4_torso_selected_manifest/v22_g4_torso_selected_manifest_overlay_qa.png
metric:
  - qa_entry_count: 33
  - b4_entry_count: 16
  - b5_entry_count: 17
  - generated_torso_review_count: 1
  - b4_front_hair_candidate_count: 7
  - b4_secondary_review_count: 9
  - b5_shoulder_improvement_candidate_count: 2
  - b5_copied_layer_review_count: 14
  - verdict_counts:
      B4_FRONT_HAIR_MOTION_CANDIDATE_REVIEW_REQUIRED: 7
      B4_SECONDARY_DRAW_ORDER_OR_MASK_REVIEW_REQUIRED: 9
      B5_TORSO_GENERATED_UNDERPAINT_REBUILD_REVIEW_REQUIRED: 1
      B5_SHOULDER_DRAW_ORDER_MASK_IMPROVEMENT_REVIEW_REQUIRED: 2
      B5_COPIED_LAYER_REVIEW_REQUIRED: 14
  - g5_material_acceptance_status: BLOCKED_PENDING_OVERLAY_REDUCTION_OR_SEPARATE_G5_ACCEPTANCE
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - validator_only_promotion_blocked: true
  - not_owner_approval: true
  - self_review: PASS
decision: The generated torso is selected in the manifest, but 33 B4/B5 overlay review lanes remain, so G5/material stays blocked.
next_action: Build a compact G4 torso-selected review/reduction packet that separates remaining B4/B5 lanes before any G5 attempt.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G4-TORSO-SELECTED-REVIEW-REDUCTION-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G4-TORSO-SELECTED-REVIEW-REDUCTION-001
date: 2026-06-10
owner: Codex
status: G4_TORSO_SELECTED_REVIEW_REDUCTION_PACKET_READY_MATERIAL_BLOCKED
hypothesis: The 33 B4/B5 overlay rows can be compacted into a phase-based work order that narrows immediate pre-G5 blockers to torso plus shoulders while preserving HairFront/G7/G8 locks.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_64part_g4_torso_selected_manifest/v22_64part_g4_torso_selected_manifest.json
  - experiments/cubism-v2-new-character-002/reports/v22_64part_g4_torso_selected_manifest/v22_g4_torso_selected_manifest_overlay_qa_report.json
output:
  - scripts/build_cubism_v2_g4_torso_selected_review_reduction_packet_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g4_torso_selected_review_reduction/v22_g4_torso_selected_review_reduction_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g4_torso_selected_review_reduction/v22_g4_torso_selected_review_reduction_packet.md
  - experiments/cubism-v2-new-character-002/reports/v22_g4_torso_selected_review_reduction/v22_g4_torso_selected_review_reduction_sheet.png
metric:
  - review_row_count: 33
  - pre_g5_blocking_row_count: 3
  - pre_g5_blocking_row_count_is_three: true
  - generated_torso_selected_count: 1
  - shoulder_candidate_count: 2
  - front_hair_candidate_count: 7
  - b4_secondary_context_count: 9
  - b5_copied_context_count: 14
  - context_review_row_count: 23
  - hairfront_hidden_candidate_count: 7
  - generated_torso_selected: true
  - g5_material_acceptance_status: BLOCKED_PENDING_REDUCTION_PACKET_REVIEW
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - validator_only_promotion_blocked: true
  - not_owner_approval: true
  - self_review: PASS
decision: The immediate pre-G5 surface is reduced to three rows, but the packet is a work order only and does not unlock material PASS, HairFront, Mini Cubism, or real Cubism.
next_action: Resolve the three P0 pre-G5 torso/shoulder rows first, then keep HairFront and context rows blocked until separate review evidence exists.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G4-P0-TORSO-SHOULDER-DECISION-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G4-P0-TORSO-SHOULDER-DECISION-001
date: 2026-06-10
owner: Codex
status: G4_P0_TORSO_SHOULDER_DECISION_READY_G5_PREP_UNBLOCKED_MATERIAL_BLOCKED
hypothesis: The three P0 torso/shoulder rows can be resolved as G5 prep candidates only, unblocking a later G5 prep packet without approving material PASS.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_g4_torso_selected_review_reduction/v22_g4_torso_selected_review_reduction_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g4_torso_base_regen_overlay_qa/v22_g4_torso_base_regen_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b5_provisional_minipass_candidate/v22_b5_provisional_minipass_overlay_qa_report.json
output:
  - scripts/build_cubism_v2_g4_p0_torso_shoulder_decision_packet_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g4_p0_torso_shoulder_decision/v22_g4_p0_torso_shoulder_decision_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g4_p0_torso_shoulder_decision/v22_g4_p0_torso_shoulder_decision_packet.md
  - experiments/cubism-v2-new-character-002/reports/v22_g4_p0_torso_shoulder_decision/v22_g4_p0_torso_shoulder_decision_sheet.png
metric:
  - input_p0_blocking_row_count: 3
  - decision_row_count: 3
  - resolved_to_g5_prep_candidate_count: 3
  - remaining_p0_pre_g5_blocker_count: 0
  - all_p0_rows_resolved_for_g5_prep: true
  - torso_g5_prep_candidate_count: 1
  - shoulder_g5_prep_candidate_count: 2
  - g5_prep_status: UNBLOCKED_FOR_PREP_PACKET_ONLY
  - g5_material_acceptance_status: BLOCKED_PENDING_SEPARATE_G5_ACCEPTANCE_PACKET
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED
  - g8_real_cubism_status: BLOCKED
  - validator_only_promotion_blocked: true
  - not_owner_approval: true
  - self_review: PASS
decision: P0 torso/shoulder rows are resolved only as G5 prep candidates; G5 acceptance and material PASS remain blocked.
next_action: Build a G5 prep packet from the torso-selected manifest and P0 candidate decisions, while carrying HairFront and context rows as locked/review-required.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G5-PREP-FROM-TORSO-SELECTED-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G5-PREP-FROM-TORSO-SELECTED-001
date: 2026-06-10
owner: Codex
status: G5_PREP_PACKET_READY_FROM_TORSO_SELECTED_P0_DECISION_MATERIAL_ACCEPTANCE_BLOCKED
hypothesis: The torso-selected 64-part manifest plus P0 torso/shoulder decisions can open a G5 prep surface while keeping material acceptance, ParamHairFront, Mini Cubism, and real Cubism blocked.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_64part_g4_torso_selected_manifest/v22_64part_g4_torso_selected_manifest.json
  - experiments/cubism-v2-new-character-002/reports/v22_g4_torso_selected_review_reduction/v22_g4_torso_selected_review_reduction_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g4_p0_torso_shoulder_decision/v22_g4_p0_torso_shoulder_decision_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_visual_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack_revision_v1/v22_b3_revision_v1_overlay_qa_report.json
output:
  - scripts/build_cubism_v2_g5_prep_from_torso_selected_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g5_prep_from_torso_selected/v22_g5_prep_from_torso_selected_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g5_prep_from_torso_selected/v22_g5_prep_from_torso_selected_packet.md
metric:
  - manifest_status: G4_TORSO_SELECTED_64PART_MANIFEST_TECHNICAL_PASS_REVIEW_REQUIRED
  - review_reduction_status: G4_TORSO_SELECTED_REVIEW_REDUCTION_PACKET_READY_MATERIAL_BLOCKED
  - p0_decision_status: G4_P0_TORSO_SHOULDER_DECISION_READY_G5_PREP_UNBLOCKED_MATERIAL_BLOCKED
  - technical_manifest_pass: true
  - manifest_entry_count: 64
  - unique_manifest_part_count: 64
  - p0_decision_row_count: 3
  - p0_remaining_pre_g5_blocker_count: 0
  - b1_b3_candidate_human_required_count: 3
  - remaining_review_row_count: 30
  - hairfront_hidden_candidate_count: 7
  - context_review_row_count: 23
  - remaining_pre_g5_blocking_row_count: 0
  - g5_prep_status: READY_FOR_PREP_PACKET_ONLY
  - g5_material_acceptance_status: BLOCKED_PENDING_SEPARATE_G5_ACCEPTANCE_PACKET
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE
  - g8_real_cubism_status: BLOCKED
  - v21_eye_open_lower_bound: 0.27
  - v21_mouth_open_y_max: 0.85
  - validator_only_promotion_blocked: true
  - not_owner_approval: true
  - self_review: PASS
decision: The latest torso-selected 64-part manifest is ready for a separate G5 material acceptance packet, but this G5 prep packet is not material acceptance and does not unlock ParamHairFront, Mini Cubism, or real Cubism.
next_action: Build a separate G5 material acceptance packet that reviews B1-B3 candidates, P0 torso/shoulder prep decisions, and the 30 remaining HairFront/context rows without promoting them automatically.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G5-MATERIAL-ACCEPTANCE-FROM-PREP-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G5-MATERIAL-ACCEPTANCE-FROM-PREP-001
date: 2026-06-10
owner: Codex
status: G5_MATERIAL_ACCEPTANCE_PACKET_REVIEW_REQUIRED_MATERIAL_NOT_ACCEPTED
hypothesis: The G5 prep surface should become an explicit material acceptance packet that blocks promotion until candidate and context rows have separate acceptance or revision evidence.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_g5_prep_from_torso_selected/v22_g5_prep_from_torso_selected_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_64part_g4_torso_selected_manifest/v22_64part_g4_torso_selected_manifest.json
  - experiments/cubism-v2-new-character-002/reports/v22_g4_torso_selected_review_reduction/v22_g4_torso_selected_review_reduction_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g4_p0_torso_shoulder_decision/v22_g4_p0_torso_shoulder_decision_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_b1_clean_base_underpaint/v22_b1_visual_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_overlay_qa_report.json
  - experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack_revision_v1/v22_b3_revision_v1_overlay_qa_report.json
output:
  - scripts/build_cubism_v2_g5_material_acceptance_from_prep_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g5_material_acceptance_from_prep/v22_g5_material_acceptance_from_prep_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g5_material_acceptance_from_prep/v22_g5_material_acceptance_from_prep_packet.md
metric:
  - g5_acceptance_verdict: REVIEW_REQUIRED_MATERIAL_NOT_ACCEPTED
  - g5_prep_status: G5_PREP_PACKET_READY_FROM_TORSO_SELECTED_P0_DECISION_MATERIAL_ACCEPTANCE_BLOCKED
  - manifest_status: G4_TORSO_SELECTED_64PART_MANIFEST_TECHNICAL_PASS_REVIEW_REQUIRED
  - technical_manifest_pass: true
  - material_acceptance_pass_count: 0
  - candidate_acceptance_row_count: 6
  - b1_b3_candidate_human_required_count: 3
  - p0_prep_candidate_count: 3
  - p0_remaining_pre_g5_blocker_count: 0
  - remaining_review_row_count: 30
  - hairfront_hidden_candidate_count: 7
  - context_review_row_count: 23
  - material_acceptance_required_before_g7_count: 36
  - g5_material_acceptance_status: BLOCKED_REVIEW_REQUIRED_MATERIAL_NOT_ACCEPTED
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE
  - g8_real_cubism_status: BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE
  - v21_eye_open_lower_bound: 0.27
  - v21_mouth_open_y_max: 0.85
  - validator_only_promotion_blocked: true
  - not_owner_approval: true
  - self_review: PASS
decision: G5 material acceptance is explicitly not passed. The packet records six candidate acceptance rows and thirty remaining HairFront/context rows, all blocked from material promotion until separate acceptance or revision evidence exists.
next_action: Reduce the 36 material-acceptance-required rows with separate accept/revise/regenerate evidence, rerun this G5 packet, and keep G7/G8 blocked until material acceptance is explicitly passed.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G5-MATERIAL-ACCEPTANCE-REDUCTION-ROUTE-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G5-MATERIAL-ACCEPTANCE-REDUCTION-ROUTE-001
date: 2026-06-10
owner: Codex
status: G5_MATERIAL_ACCEPTANCE_REDUCTION_ROUTE_READY_PRIMARY6_MATERIAL_NOT_ACCEPTED
hypothesis: The 36 blocked G5 material acceptance rows can be preserved while routing the immediate next acceptance/revision work to six primary rows.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_g5_material_acceptance_from_prep/v22_g5_material_acceptance_from_prep_packet.json
output:
  - scripts/build_cubism_v2_g5_material_acceptance_reduction_route_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g5_material_acceptance_reduction_route/v22_g5_material_acceptance_reduction_route_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g5_material_acceptance_reduction_route/v22_g5_material_acceptance_reduction_route_packet.md
metric:
  - source_status: G5_MATERIAL_ACCEPTANCE_PACKET_REVIEW_REQUIRED_MATERIAL_NOT_ACCEPTED
  - source_verdict: REVIEW_REQUIRED_MATERIAL_NOT_ACCEPTED
  - source_material_acceptance_pass_count: 0
  - total_route_row_count: 36
  - primary6_row_count: 6
  - secondary_context_row_count: 23
  - hairfront_contract_row_count: 7
  - primary6_unresolved_count: 6
  - total_unresolved_material_acceptance_count: 36
  - primary6_ids:
      - B1_CLEAN_BASE_UNDERPAINT
      - B2_EYE_PACK
      - B3_MOUTH_PACK_REVISION_V1
      - torso_base
      - shoulder_L
      - shoulder_R
  - g5_material_acceptance_status: BLOCKED_PRIMARY6_REDUCTION_READY_MATERIAL_NOT_ACCEPTED
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE
  - g8_real_cubism_status: BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE
  - v21_eye_open_lower_bound: 0.27
  - v21_mouth_open_y_max: 0.85
  - validator_only_promotion_blocked: true
  - not_owner_approval: true
  - self_review: PASS
decision: The next automatic G5 work surface is reduced to six primary rows, but all 36 rows remain unresolved for material acceptance and no material PASS is granted.
next_action: Build or apply a G5 primary6 accept/revise packet for B1, B2, B3, torso_base, shoulder_L, and shoulder_R while keeping HairFront hidden and G7/G8 blocked.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G5-PRIMARY6-CODEX-DECISIONS-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G5-PRIMARY6-CODEX-DECISIONS-001
date: 2026-06-10
owner: Codex
status: G5_PRIMARY6_CODEX_PROVISIONAL_DECISIONS_READY_MATERIAL_NOT_ACCEPTED
hypothesis: The six primary G5 rows can be provisionally accepted by Codex as candidate evidence while preserving owner/material PASS locks and leaving the remaining 30 context/HairFront rows blocked.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_g5_material_acceptance_reduction_route/v22_g5_material_acceptance_reduction_route_packet.json
output:
  - scripts/build_cubism_v2_g5_primary6_codex_decisions_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g5_primary6_codex_decisions/v22_g5_primary6_codex_decisions_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g5_primary6_codex_decisions/v22_g5_primary6_codex_decisions_packet.md
metric:
  - source_status: G5_MATERIAL_ACCEPTANCE_REDUCTION_ROUTE_READY_PRIMARY6_MATERIAL_NOT_ACCEPTED
  - source_primary6_row_count: 6
  - codex_decision: CODEX_PROVISIONAL_ACCEPT_AS_G5_CANDIDATE_NOT_OWNER_APPROVAL
  - g5_primary_gate: CODEX_PROVISIONAL_CANDIDATE_ACCEPTED_NOT_MATERIAL_PASS
  - primary6_decision_row_count: 6
  - primary6_codex_candidate_accept_count: 6
  - primary6_revise_count: 0
  - primary6_unresolved_count_after_decision: 0
  - owner_approval_count: 0
  - material_acceptance_pass_count: 0
  - remaining_context_row_count: 23
  - remaining_hairfront_contract_row_count: 7
  - remaining_material_acceptance_required_before_g7_count: 30
  - g5_material_acceptance_status: BLOCKED_CONTEXT_HAIRFRONT_REMAINING_NOT_OWNER_APPROVAL
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE
  - g8_real_cubism_status: BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE
  - v21_eye_open_lower_bound: 0.27
  - v21_mouth_open_y_max: 0.85
  - validator_only_promotion_blocked: true
  - not_owner_approval: true
  - self_review: PASS
decision: Primary6 is reduced to Codex candidate evidence with zero unresolved primary rows, but material PASS remains blocked and the remaining G7 blocker surface is 30 context/HairFront rows.
next_action: Run a secondary context/HairFront reduction packet over the remaining 30 rows, keeping ParamHairFront hidden and G7/G8 blocked.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G5-SECONDARY-HAIRFRONT-REDUCTION-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G5-SECONDARY-HAIRFRONT-REDUCTION-001
date: 2026-06-10
owner: Codex
status: G5_SECONDARY_HAIRFRONT_REDUCTION_READY_MATERIAL_NOT_ACCEPTED
hypothesis: After primary6 candidate decisions, the 23 secondary context rows can be kept as context-only evidence while the seven HairFront rows remain deferred with ParamHairFront hidden.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_g5_primary6_codex_decisions/v22_g5_primary6_codex_decisions_packet.json
output:
  - scripts/build_cubism_v2_g5_secondary_hairfront_reduction_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g5_secondary_hairfront_reduction/v22_g5_secondary_hairfront_reduction_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g5_secondary_hairfront_reduction/v22_g5_secondary_hairfront_reduction_packet.md
metric:
  - source_status: G5_PRIMARY6_CODEX_PROVISIONAL_DECISIONS_READY_MATERIAL_NOT_ACCEPTED
  - source_remaining_material_acceptance_required_before_g7_count: 30
  - reduction_row_count: 30
  - context_keep_count: 23
  - context_decision: CODEX_PROVISIONAL_CONTEXT_KEPT_NOT_MATERIAL_PASS
  - hairfront_defer_count: 7
  - hairfront_decision: DEFER_HAIRFRONT_KEEP_PARAM_HIDDEN_CONTRACT_ONLY
  - followup_required_count: 7
  - material_acceptance_pass_count: 0
  - owner_approval_count: 0
  - g5_material_acceptance_remaining_count: 7
  - source_counts_b4: 16
  - source_counts_b5: 14
  - g5_material_acceptance_status: BLOCKED_HAIRFRONT_MOTION_READINESS_REMAINING_NOT_OWNER_APPROVAL
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE
  - g8_real_cubism_status: BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE
  - v21_eye_open_lower_bound: 0.27
  - v21_mouth_open_y_max: 0.85
  - validator_only_promotion_blocked: true
  - not_owner_approval: true
  - self_review: PASS
decision: Secondary context is kept as context-only candidate evidence and the only remaining G5/G7 follow-up surface is seven HairFront rows; no material PASS or ParamHairFront activation is granted.
next_action: Build a HairFront motion-readiness acceptance packet for the seven front-hair rows while keeping ParamHairFront hidden until acceptance is explicitly passed.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G5-HAIRFRONT-MOTION-READINESS-ACCEPTANCE-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G5-HAIRFRONT-MOTION-READINESS-ACCEPTANCE-001
date: 2026-06-10
owner: Codex
status: G5_HAIRFRONT_MOTION_READINESS_REVIEW_REQUIRED_PARAM_HIDDEN
hypothesis: The seven front-hair child PNGs can be confirmed as independent static candidates while keeping motion-readiness, material acceptance, ParamHairFront activation, G7, and G8 blocked.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_g5_secondary_hairfront_reduction/v22_g5_secondary_hairfront_reduction_packet.json
output:
  - scripts/build_cubism_v2_g5_hairfront_motion_readiness_acceptance_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g5_hairfront_motion_readiness_acceptance/v22_g5_hairfront_motion_readiness_acceptance_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g5_hairfront_motion_readiness_acceptance/v22_g5_hairfront_motion_readiness_acceptance_packet.md
metric:
  - hairfront_acceptance_verdict: REVIEW_REQUIRED_KEEP_PARAM_HAIRFRONT_HIDDEN
  - source_status: G5_SECONDARY_HAIRFRONT_REDUCTION_READY_MATERIAL_NOT_ACCEPTED
  - source_g5_material_acceptance_remaining_count: 7
  - hairfront_row_count: 7
  - hairfront_png_exists_count: 7
  - independent_part_candidate_count: 7
  - motion_readiness_pass_count: 0
  - motion_readiness_review_required_count: 7
  - param_hairfront_activation_count: 0
  - param_hairfront_hidden_count: 7
  - material_acceptance_pass_count: 0
  - owner_approval_count: 0
  - g5_material_acceptance_remaining_count: 7
  - all_png_exist: true
  - all_independent_candidates: true
  - g5_static_part_gate: PRESENT_AS_INDEPENDENT_CANDIDATES
  - g5_hairfront_motion_readiness: REVIEW_REQUIRED_KEEP_PARAM_HIDDEN
  - g5_material_acceptance_status: BLOCKED_HAIRFRONT_MOTION_READINESS_REVIEW_REQUIRED
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE
  - g8_real_cubism_status: BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE
  - v21_eye_open_lower_bound: 0.27
  - v21_mouth_open_y_max: 0.85
  - validator_only_promotion_blocked: true
  - not_owner_approval: true
  - self_review: PASS
decision: Seven front-hair child PNGs exist as independent static candidates, but static PNG existence does not prove motion-readiness. ParamHairFront remains hidden/contract-only and G5/G7/G8 remain blocked.
next_action: Create a HairFront motion-readiness preview or pose-sweep packet that demonstrates safe independent front-hair motion before considering ParamHairFront activation or G7 unlock.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G5-HAIRFRONT-MOTION-READINESS-PREVIEW-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G5-HAIRFRONT-MOTION-READINESS-PREVIEW-001
date: 2026-06-10
owner: Codex
status: G5_HAIRFRONT_MOTION_READINESS_PREVIEW_READY_REVIEW_REQUIRED_PARAM_HIDDEN
hypothesis: A deterministic pre-G7 static shift preview can provide HairFront motion review evidence without activating ParamHairFront or claiming material/G7 acceptance.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_g5_hairfront_motion_readiness_acceptance/v22_g5_hairfront_motion_readiness_acceptance_packet.json
output:
  - scripts/build_cubism_v2_g5_hairfront_motion_readiness_preview_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g5_hairfront_motion_readiness_preview/v22_g5_hairfront_motion_readiness_preview_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g5_hairfront_motion_readiness_preview/v22_g5_hairfront_motion_readiness_preview_packet.md
  - experiments/cubism-v2-new-character-002/reports/v22_g5_hairfront_motion_readiness_preview/v22_g5_hairfront_motion_readiness_preview_sheet.png
metric:
  - source_status: G5_HAIRFRONT_MOTION_READINESS_REVIEW_REQUIRED_PARAM_HIDDEN
  - hairfront_row_count: 7
  - pose_frame_count: 5
  - preview_contact_sheet_exists: true
  - all_pose_frames_exist: true
  - static_independent_candidate_count: 7
  - motion_preview_generated_count: 5
  - motion_readiness_pass_count: 0
  - motion_readiness_review_required_count: 7
  - param_hairfront_activation_count: 0
  - material_acceptance_pass_count: 0
  - owner_approval_count: 0
  - g5_hairfront_motion_preview: PREVIEW_READY_REVIEW_REQUIRED
  - g5_hairfront_motion_readiness: REVIEW_REQUIRED_KEEP_PARAM_HIDDEN
  - g5_material_acceptance_status: BLOCKED_HAIRFRONT_PREVIEW_REVIEW_REQUIRED
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE
  - g8_real_cubism_status: BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE
  - v21_eye_open_lower_bound: 0.27
  - v21_mouth_open_y_max: 0.85
  - validator_only_promotion_blocked: true
  - not_owner_approval: true
  - self_review: PASS
decision: HairFront pre-G7 motion preview frames and contact sheet are ready for review, but this is not rig pose-sweep success, not material acceptance, and not ParamHairFront activation.
next_action: Review the contact sheet for drift/edge/occlusion issues, then either build a dedicated HairFront diagnostic preview or route the seven rows to manual anchor correction/regeneration.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G5-HAIRFRONT-PREVIEW-CODEX-TRIAGE-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G5-HAIRFRONT-PREVIEW-CODEX-TRIAGE-001
date: 2026-06-10
owner: Codex
status: G5_HAIRFRONT_PREVIEW_CODEX_TRIAGE_READY_REVIEW_REQUIRED_PARAM_HIDDEN
hypothesis: Codex can automatically confirm the HairFront pre-G7 preview frames are technically complete without promoting them to material acceptance, owner approval, ParamHairFront activation, G7, or G8.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_g5_hairfront_motion_readiness_preview/v22_g5_hairfront_motion_readiness_preview_packet.json
output:
  - scripts/build_cubism_v2_g5_hairfront_preview_codex_triage_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g5_hairfront_preview_codex_triage/v22_g5_hairfront_preview_codex_triage_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g5_hairfront_preview_codex_triage/v22_g5_hairfront_preview_codex_triage_packet.md
  - experiments/cubism-v2-new-character-002/reports/v22_g5_hairfront_motion_readiness_preview/v22_g5_hairfront_motion_readiness_preview_sheet.png
metric:
  - source_status: G5_HAIRFRONT_MOTION_READINESS_PREVIEW_READY_REVIEW_REQUIRED_PARAM_HIDDEN
  - triage_verdict: NO_CATASTROPHIC_TECHNICAL_FAILURE_DETECTED_REVIEW_REQUIRED
  - codex_provisional_visual_verdict: CODEX_PROVISIONAL_REVIEW_REQUIRED_NOT_OWNER_APPROVAL
  - hairfront_row_count: 7
  - pose_frame_count: 5
  - technical_frame_pass_count: 5
  - shifted_bbox_canvas_violation_count: 0
  - max_changed_ratio_vs_neutral: 0.04140663
  - min_changed_ratio_vs_neutral: 0.02912807
  - codex_visual_acceptance_pass_count: 0
  - motion_readiness_pass_count: 0
  - param_hairfront_activation_count: 0
  - material_acceptance_pass_count: 0
  - owner_approval_count: 0
  - g5_material_acceptance_status: BLOCKED_HAIRFRONT_PREVIEW_REVIEW_REQUIRED
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE
  - g8_real_cubism_status: BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE
  - v21_eye_open_lower_bound: 0.27
  - v21_mouth_open_y_max: 0.85
  - validator_only_promotion_blocked: true
  - codex_visual_not_owner_approval: true
  - not_owner_approval: true
  - self_review: PASS
decision: Five HairFront preview frames pass technical triage for file existence, 2048 size, and shifted bboxes staying inside canvas. This remains review-required Codex evidence only; material acceptance, motion-readiness PASS, ParamHairFront activation, G7, and real Cubism remain blocked.
next_action: Continue only with diagnostic/review artifacts unless a separate material decision gate is recorded; keep ParamHairFront hidden.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G6-HAIRFRONT-ANCHOR-PROBE-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G6-HAIRFRONT-ANCHOR-PROBE-001
date: 2026-06-10
owner: Codex
status: G6_HAIRFRONT_ANCHOR_PROBE_READY_REVIEW_REQUIRED_PARAM_HIDDEN
hypothesis: The seven HairFront rows can be converted into reproducible G6 anchor/envelope evidence without promoting them to material acceptance, owner approval, ParamHairFront activation, G7, or G8.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_g5_hairfront_motion_readiness_acceptance/v22_g5_hairfront_motion_readiness_acceptance_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g5_hairfront_motion_readiness_preview/v22_g5_hairfront_motion_readiness_preview_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g5_hairfront_preview_codex_triage/v22_g5_hairfront_preview_codex_triage_packet.json
output:
  - scripts/build_cubism_v2_g6_hairfront_anchor_probe_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g6_hairfront_anchor_probe/v22_g6_hairfront_anchor_probe_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g6_hairfront_anchor_probe/v22_g6_hairfront_anchor_probe_packet.md
  - experiments/cubism-v2-new-character-002/reports/v22_g6_hairfront_anchor_probe/v22_g6_hairfront_anchor_probe_sheet.png
metric:
  - probe_verdict: ANCHOR_PROBE_READY_REVIEW_REQUIRED_NOT_MATERIAL_PASS
  - source_acceptance_status: G5_HAIRFRONT_MOTION_READINESS_REVIEW_REQUIRED_PARAM_HIDDEN
  - source_preview_status: G5_HAIRFRONT_MOTION_READINESS_PREVIEW_READY_REVIEW_REQUIRED_PARAM_HIDDEN
  - source_triage_status: G5_HAIRFRONT_PREVIEW_CODEX_TRIAGE_READY_REVIEW_REQUIRED_PARAM_HIDDEN
  - hairfront_row_count: 7
  - anchor_probe_row_count: 7
  - anchor_center_count: 7
  - motion_envelope_count: 7
  - pose_shift_count: 5
  - technical_frame_pass_count: 5
  - shifted_bbox_canvas_violation_count: 0
  - motion_envelope_min_margin_to_canvas: 221
  - contact_sheet_exists: true
  - manual_anchor_override_ready_count: 7
  - manual_anchor_override_saved_count: 0
  - codex_visual_acceptance_pass_count: 0
  - motion_readiness_pass_count: 0
  - param_hairfront_activation_count: 0
  - material_acceptance_pass_count: 0
  - owner_approval_count: 0
  - g6_anchor_correction_status: READY_IF_VISUAL_REVIEW_REQUIRES_CORRECTION
  - g5_material_acceptance_status: BLOCKED_HAIRFRONT_ANCHOR_PROBE_REVIEW_REQUIRED
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE
  - g8_real_cubism_status: BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE
  - v21_eye_open_lower_bound: 0.27
  - v21_mouth_open_y_max: 0.85
  - validator_only_promotion_blocked: true
  - codex_visual_not_owner_approval: true
  - not_owner_approval: true
  - self_review: PASS
decision: Seven HairFront candidates now have reproducible anchor centers and motion-envelope bboxes for G6 correction/review. This is correction evidence only; G5 material acceptance, motion-readiness PASS, ParamHairFront activation, G7, and real Cubism remain blocked.
next_action: Build a correction input packet that can store HairFront manual override JSON, or route rows to regeneration if visual review rejects the current anchors.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G6-HAIRFRONT-ANCHOR-CORRECTION-INPUT-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G6-HAIRFRONT-ANCHOR-CORRECTION-INPUT-001
date: 2026-06-10
owner: Codex
status: G6_HAIRFRONT_ANCHOR_CORRECTION_INPUT_READY_OVERRIDES_NOT_SAVED_PARAM_HIDDEN
hypothesis: The G6 HairFront anchor probe can be converted into a reusable override template without applying movement or promoting material acceptance, owner approval, ParamHairFront activation, G7, or G8.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_g6_hairfront_anchor_probe/v22_g6_hairfront_anchor_probe_packet.json
output:
  - scripts/build_cubism_v2_g6_hairfront_anchor_correction_input_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g6_hairfront_anchor_correction_input/v22_g6_hairfront_anchor_correction_input_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g6_hairfront_anchor_correction_input/v22_g6_hairfront_anchor_correction_input_packet.md
  - experiments/cubism-v2-new-character-002/reports/v22_g6_hairfront_anchor_correction_input/manual_hairfront_anchor_overrides.template.json
metric:
  - correction_input_verdict: CORRECTION_INPUT_READY_NO_OVERRIDE_APPLIED_NOT_MATERIAL_PASS
  - source_status: G6_HAIRFRONT_ANCHOR_PROBE_READY_REVIEW_REQUIRED_PARAM_HIDDEN
  - hairfront_row_count: 7
  - anchor_probe_row_count: 7
  - correction_input_row_count: 7
  - override_template_entry_count: 7
  - current_anchor_count: 7
  - target_anchor_default_count: 7
  - zero_delta_default_count: 7
  - saved_override_count: 0
  - manual_anchor_override_ready_count: 7
  - manual_anchor_override_applied_count: 0
  - regeneration_route_ready_count: 7
  - codex_visual_acceptance_pass_count: 0
  - motion_readiness_pass_count: 0
  - param_hairfront_activation_count: 0
  - material_acceptance_pass_count: 0
  - owner_approval_count: 0
  - g6_anchor_correction_status: INPUT_READY_OVERRIDES_NOT_SAVED
  - g5_material_acceptance_status: BLOCKED_HAIRFRONT_CORRECTION_INPUT_REVIEW_REQUIRED
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE
  - g8_real_cubism_status: BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE
  - v21_eye_open_lower_bound: 0.27
  - v21_mouth_open_y_max: 0.85
  - validator_only_promotion_blocked: true
  - codex_visual_not_owner_approval: true
  - not_owner_approval: true
  - self_review: PASS
decision: HairFront anchor correction input and an override template are ready. No override has been saved or applied, so this does not grant material acceptance, ParamHairFront activation, G7, or real Cubism readiness.
next_action: Serve or reuse a drag/zoom editor that writes a reviewed override JSON from the template, or route rejected rows to regeneration.
```

## CUBISM-V2-NEW-CHARACTER-002-V22-G6-HAIRFRONT-ANCHOR-EDITOR-001

```yaml
id: CUBISM-V2-NEW-CHARACTER-002-V22-G6-HAIRFRONT-ANCHOR-EDITOR-001
date: 2026-06-10
owner: Codex
status: G6_HAIRFRONT_ANCHOR_EDITOR_SMOKE_PASS
hypothesis: A drag/zoom editor can load the HairFront correction input, render a movable composite, and exercise the save path without creating a real manual override or promoting material/G7/G8.
input:
  - experiments/cubism-v2-new-character-002/reports/v22_g6_hairfront_anchor_correction_input/v22_g6_hairfront_anchor_correction_input_packet.json
  - experiments/cubism-v2-new-character-002/reports/v22_g6_hairfront_anchor_correction_input/manual_hairfront_anchor_overrides.template.json
output:
  - scripts/run_v22_g6_hairfront_anchor_editor_002.py
  - experiments/cubism-v2-new-character-002/reports/v22_g6_hairfront_anchor_correction_input/v22_g6_hairfront_anchor_editor_smoke.json
  - experiments/cubism-v2-new-character-002/reports/v22_g6_hairfront_anchor_correction_input/manual_hairfront_anchor_overrides.smoke.json
metric:
  - source_status: G6_HAIRFRONT_ANCHOR_CORRECTION_INPUT_READY_OVERRIDES_NOT_SAVED_PARAM_HIDDEN
  - entry_count: 7
  - composite_first_row: hair_front_center
  - composite_png_bytes: 559270
  - smoke_saved_override_count: 1
  - smoke_move_anchor_count: 0
  - actual_override_exists: false
  - actual_override_not_created_by_smoke: true
  - material_acceptance_pass_count: 0
  - param_hairfront_activation_count: 0
  - owner_approval_count: 0
  - g5_material_acceptance_status: BLOCKED_HAIRFRONT_EDITOR_REVIEW_REQUIRED
  - material_pass_status: BLOCKED
  - param_hair_front_status: HIDDEN_CONTRACT_ONLY
  - g7_mini_cubism_status: BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE
  - g8_real_cubism_status: BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE
  - v21_eye_open_lower_bound: 0.27
  - v21_mouth_open_y_max: 0.85
  - validator_only_promotion_blocked: true
  - self_review: PASS
decision: HairFront drag/zoom editor smoke passes and save-path plumbing is verified using a smoke override file only. Real manual override JSON is still absent, so no correction has been applied and material/G7/G8 remain blocked.
next_action: Run the editor for real review, save `manual_hairfront_anchor_overrides.json` only after deliberate visual placement, then rebuild shifted full-canvas HairFront PNGs and rerun QA.
```

# Vtube Project Status

Updated: 2026-06-13 (입 MOUTH-LIP-PARTS·템플릿화 TEMPLATE-001 돌파. 각도 작화 스왑은 폐기·리셋. 입 H2 판정이 다음 차례)

## Current Phase

- **AUTORIG 피벗 (2026-06-10, 주인님 결정)**: Cubism Editor 수동 저작 경로를 폐기하고, 자체 에디터/런타임 + AI 자동리깅으로 전환.
- 방향 상세: `docs/ref/AUTORIG-PIPELINE-V1.md` (P0–P6, "자동화파이프라인 시작" 원커맨드, 1시간 목표).
- 문서 내비게이션: `docs/INDEX.md`.

## What Changed / What Stays

| 항목 | 결정 |
|---|---|
| Cubism Editor 저작 (구 G7/G8) | 폐기 — 자체 rig JSON + 자체 런타임으로 대체 |
| Cubism 파라미터 ID 표준 | 유지 — 57모델 분석·MediaPipe 맵 재사용 위해 |
| 64-part `v2_standard` 스펙 | 유지 — 템플릿 슬롯 매핑의 기반 |
| B4/B5 수동 앵커 미세조정 루프 | 중단 — 템플릿 슬롯 생성이 앵커 문제를 제거 |
| character-002 64-part 후보 | 보존 — AUTORIG P3 자동 리깅의 첫 입력 후보 |
| 트래킹 체인 (T0–T2 PASS) | 유지 — P6에 그대로 연결 |

## Progress Snapshot

| Stage | Progress | Status |
|---|---:|---|
| 레퍼런스 분석·성공 패턴 (57모델) | 100% | 완료, AUTORIG 품질 사다리 기준치로 사용 |
| character-002 64-part 후보 | 기술 PASS | 주인님 시각 판정: 오염 多 → 템플릿 방식으로 재생성 예정 (소재만 폐기, 스펙·증거 유지) |
| 트래킹 (MediaPipe→Cubism 파라미터) | **얼굴+어깨 실측 (주인님 승인 2026-06-11)** | Face 랜드마커 + **Pose 어깨 1:1 매핑**(SHOULDER-TRACK-001: 기울기→BodyZ·이동→BodyX·으쓱→BodyY, 자동/버튼 캘리브레이션, 머리 기반 폴백). 오버레이 점 9개(얼굴 7 파랑+어깨 2 주황+어깨선). 페이지는 `scripts/templates/mini_cubism_drive.html` (서버 분리) |
| 자체 런타임 (mini_cubism 계보) | 주입 API 완비 | `__miniProbe` (waitReady/setParameterValues/canvasHash) 추가 |
| **관제탑 대시보드** | **완성 (2026-06-11)** | 이벤트 JSONL 컨벤션(`scripts/autorig_events.py`) + 서버(8095, macOS 알림) + 토스스타일 UI(타임라인/피드/게이트 드래그 수정/QA/로그) + 시뮬레이터. 스모크: 파이썬 18/18, 브라우저 8/8 PASS |
| **소재 (하이브리드 레시피)** | **VERIFIED** | 진짜 마스터 분해+원본 재스킨(가시) + 동일세션 시트(숨은) — `vtube-hybrid-material-recipe` 하니스화. 전체 슬롯 생성은 기하 비정합으로 DISCARDED |
| **자동 리깅 (rig v1.11)** | **몸·목·입·옷 사이클 완료 (2026-06-12)** | 눈: 상하 감김+정점 키폼(잔상 0 입증) · 입: 높이 키폼 정렬+하드 밴드 스냅(잔상 해소 — 근본은 004 부품형 입) + **MouthForm 파라미터(20종째 — 입꼬리 워프 근사, 트래킹 mouthSmile/Frown 연동, MouthOpenY 0..1 개편)** · 몸: 골반 진자 스웨이(공식 体の回転 패턴, 접합부 등변위 픽셀 실측 18px 균일)+파라미터 스프링(BodyAngleX/Z 물리 소유)+어깨 실측 입력 · 목: 首の曲面 전가장자리 핀(참수선 해소, 주인님 스크린샷 진단) · **옷: 드레이프 스프링(CLOTH-PHYS-001 — 공식 스커트 그룹 실측 정박: 입력 BodyAngleX/Z 100/100, Delay 0.6 비율, A/B 픽셀 증명 8.09≈기대 7.92px, 접합 슬립 0.52px)** · 건강검진: 인스펙터 무반응 0건. 눈웃음 워프(EXPR-002)·입꼬리·표정은 004에서 부품형 입·표정 시트로 대체 완료. **각도 입체감: ANGLE-FORESHORTEN-001 — 돌릴 때 머리 윤곽 가로 12% 압축(head_z+back_hair sx=0.88, 비핀), 어깨가닥 upper_warp 분리로 정합 PASS·중립 무회귀(8062 캡처).** 잔존 갭: 팔 리깅·각도 비대칭 원근(볼 파츠)·눈썹 모양 변형·리본 개별 찰랑(분해 슬롯에 리본 미분리)·분해 풀해상도화 |
| **렌더 백엔드 (PIXI-RENDER-001)** | **완료 (2026-06-11)** | PixiJS v8 WebGL 기본(`?renderer=pixi`) — 풀해상도 상태 전환 ~1ms·실효 60fps (canvas2d 대비 ~100×). canvas 폴백 유지. verify 5/5 양 백엔드 PASS |
| AUTORIG-TEMPLATE-SPEC-001 | 완료 (2026-06-11 개정) | 생성 목록: 마스터 + 입 시트 + **눈 표정 시트(눈웃음·윙크·놀람·반개·><·하트눈) + 액센트 시트(홍조·그늘·눈물·땀)** — 표정은 워프가 아니라 동일세션 생성 작화 (`docs/ref/AUTORIG-MASTER-SPEC.md` §3.2~3.4) |
| AUTORIG-PIPELINE-CLI-001 | **완료 (2026-06-11)** | `run_autorig_pipeline.py` 원커맨드 — 003 풀런 76분(순수 연산 ~22분), H1/H1.5/H2 관제탑 게이트. **P5 자동 검증 9게이트** (004 확장): validator·mesh verify·blink 잔상·perf·rig 인스펙터(무반응 — tile_max 판정)·옷 물리 A/B·트래킹 매퍼 QA(6검사)·**부품형 입 구조 검사**(`validate_mouth_parts_keyforms.py`)·**유기성 게이트**(`analyze_rig_cohesion.py` — 인접 16쌍 이음새 상대변위). 시트 P0(`validate_generated_sheets.py`)는 생성 직후 |
| AUTORIG-ANCHOR-DETECT-001 | 0% | 프로덕션 갭 (임의 업로드 PNG 앵커 검출) |

## Production Direction

- Target: 템플릿 이미지 생성 → 결정론적 추출 → 자동 리깅(rig JSON) → 자체 런타임 → 웹캠 실시간 버튜버 서비스.
- 픽셀 좌표는 결정론적 도구만 사용한다. LLM 비전 좌표 추측 금지 (evidence log DISCARDED 결론).
- PNG 풀캔버스 실험은 배치/키포즈 증거이며 프레임 스왑 런타임이 아니다.

## Evidence

- 전체 증거 테이블(169행)과 검증 명령 모음은 `docs/archive/2026-06-10-PROJECT-STATUS-pre-autorig-pivot.md`에 보존.
- 시행착오 이력과 상태 관리(VERIFIED/DISCARDED 등)는 `vtube-validation-evidence-log.md`.
- 실험별 증거는 각 `experiments/<id>/reports/`.

## AUTORIG-CHARACTER-004 (위벨) — 2026-06-13

- 생성: gpt-image-2 API 4장(마스터+입+눈표정+액센트) $0.87, H1 승인. 시트 P0 검증기 신설 (입=하드 게이트).
- 신규 리깅: **부품형 입**(입술 정점 키폼 연속 개폐+입안 클리핑, 실패 시 4상태 폴백) · **눈 표정 6종**(ParamEyeExpr, 스킨 플레이트+기본 눈 자동 숨김) · **액센트 4종**(Cheek/Gloom/Tear/Sweat) · MouthForm 입선 입꼬리 키폼.
- **H2 피드백 2라운드 반영 (주인님 육안 → 수치 박제)**:
  - 어깨 좌우 떨림 → 드라이브 어깨 X/Z 데드존±5%+EMA (입력 지터 91%↓, 트래킹 QA 지터 0)
  - 기울임 기준점 어색 → **HEAD-Z-PIVOT-001**: 비핀 전용 회전 디포머(피벗=턱 관절), 목은 체인 분리로 고정
  - 치마·하체 동반+분리 / 앞뒷머리 어긋남 → **RIG-COHESION-001**: 유기성 분석기(`analyze_rig_cohesion.py`, 16쌍×9파라미터 이음새 상대변위) 신설·P5 게이트화. 잠복 버그 3건 검거: `'ear' in pid`가 `~wear`에 오매칭(하의가 얼굴 디포머 소속, 134px→0) / 뒷머리 Z 반각(29px→0) / Breath 골반 스케일 슬립(13px→2px)
- **입 H2 5라운드 (주인님 육안 → 근본 재설계)**: "입이 미소 그대로 안 열림"
  - 1~3차: 부품형 입 앵커 보정 (미소선 중심→입안 상단), 미소선=윗입술 승격 — 실제 캡처로 진단(내 합성 시뮬 오판 반복 교훈)
  - 진단: 마스터 입은 '다문 미소선 한 줄'이라 윗입술 부적합. 시트 부품의 아랫입술이 위벨 미소곡선 그 자체
  - **MOUTH-LIP-PARTS-001**(주인님 "시트로 일관 처리" 선택): 윗입술(시트, 고정+MouthForm) + 아랫입술(시트 미소곡선, MouthOpenY 하강) + 입안/이빨/혀(페이드+클리핑), 마스터 입선 숨김. 실제 캡처: 닫힘=위벨 미소, 열림=미소 윗입술 고정·아랫입술만 하강
  - 입 시트 위벨 컨셉 재생성($0.44): 활짝→차분한 미소, 입꼬리 곡선 유지
- 최신 입 풀런: `runs/autorig-character-004_20260613_193420` — P5 9게이트 PASS, **입 H2 판정 대기** (8062/8063)
- 상세: evidence log `…-MOUTH-PARTS-EXPR-001`·`-HEAD-Z-PIVOT-001`·`RIG-COHESION-001`·`-MOUTH-ANCHOR-001`·`-MOUTH-LIP-RIDE-001`·`-MOUTH-LIP-PARTS-001`

## AUTORIG-TEMPLATE-001 (템플릿화 정비) — 2026-06-13 완료

주인님 메타 질문("캐릭터마다 코드 수정? 템플릿화 안 됨?") + 입 5번 삽질 교훈에서 정비. 캐릭터 특성을 코드 상수+사후 튜닝이 아니라 **스펙 파일 + 자동 실측**으로.

- **캐릭터 스펙**: `characters/<id>.yaml`(외형·`expression_style`·색 힌트) + `scripts/lib/character_spec.py`. 005부터 yaml 1개만 만들면 **코드 0줄 수정**으로 캐릭터 추가 (가상 005 검증).
- **표정 성격 주입**: `expression_style`이 입·눈 시트 생성에 들어가 캐릭터 성격(차분/활발)이 입 개방을 결정 — 입 삽질 구조적 차단. `generate_master_sheets --character-spec`.
- **튜닝 자동화**: 색 임계(`split_shoulder_hair`, 검은드레스 오분류 무재발)·입 OVERLAP(`extract_mouth_parts`)·목 높이(`split_neck_skin`)를 실측 자동 파생. 003·004 무회귀.
- 보류(백로그): 신체/머리 sway·head tx(3D 미세 — H2 육안이 잡음).
- 상세: evidence log `AUTORIG-TEMPLATE-001`, 스펙 `docs/ref/AUTORIG-MASTER-SPEC.md` §1.5·조건 11.

## ~~ANGLE-SWAP (각도 작화 스왑)~~ — 폐기 (2026-06-13)

정면에서 옆모습을 작화 스왑으로 보여주는 접근은 **폐기**. 옆모습 작화가 정지 사진(표정 없음)이고 정면↔측면 전환이 사진 넘기기라 "현재 방식으로는 안 됨"(주인님 판정). 코드·미니프로젝트·드라이브 매핑 전부 리셋. 머리 각도는 본체 메시 의사3D ±30(표정 살아있는 라이브 변형)으로 유지 = 실제 Live2D와 동일 수준. 시도/실패 상세는 evidence log `AUTORIG-ANGLE-SWAP-001/002`(ABANDONED). 진짜 3D 회전은 PNG→3D 원클릭 툴 부재로 불가(VRoid/VRM 별도 피벗 필요) — 2D 유지.

## Next Actions

1. **004 입 H2 판정** — 8062 입 슬라이더로 미소 개폐 확인 → 합격 시 정비 코드(TEMPLATE-001)로 통합 풀런 → rig v2.0 박제. 잔여 후보: 치마 드레이프 ±9px(주인님 체감).
2. `AUTORIG-PLAYER-001` — 사용자 산출물(웹 링크·OBS 브라우저 소스·투명 모드 `?transparent=1`·오픈 ZIP).
3. `AUTORIG-ANCHOR-DETECT-001` — 임의 업로드 PNG 앵커 자동 검출 + rembg 전처리 (프로덕션 갭).
4. 분해 풀해상도화 (CUDA 런북 `docs/archive/2026-06-08-superseded-plans/`) + 키폼 사다리.

## 다음 세션 빠른 재개 (서버·게이트 상태)

- **떠있을 수 있는 서버**(세션 종료 시 꺼짐 — 재기동 필요): 8062 입 리깅앱·8063/drive 웹캠·8095 관제탑.
  - 입: `python3 scripts/mini_cubism_preview_server.py --project experiments/autorig-character-004/rig_v0_project --port 8062`
- **대기 게이트**: 입 풀런 `runs/autorig-character-004_20260613_193420` H2 WAITING (주인님 판정 미완).

## Rules

- 증거 JSON, QA 리포트, 수동 리뷰 JSON 삭제 금지.
- 이 문서는 짧게 유지. 상세 이력은 evidence log나 실험 reports로.
- 대체된 플랜은 `docs/archive/`로 이동하고 `ARCHIVE-INDEX.md`에 기록.
- Human review FAIL은 keep으로 승격하지 않는다.

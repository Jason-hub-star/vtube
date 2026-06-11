# Vtube Project Status

Updated: 2026-06-11 (CHAIN-001 — strong20 체인 이식 + 어깨 가닥 분리 + 입 V선 방어)

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
| **자동 리깅 (rig v1.10)** | **몸·목·입·옷 사이클 완료 (2026-06-12)** | 눈: 상하 감김+정점 키폼(잔상 0 입증) · 입: 높이 키폼 정렬+하드 밴드 스냅(잔상 해소 — 근본은 004 부품형 입) · 몸: 골반 진자 스웨이(공식 体の回転 패턴, 접합부 등변위 픽셀 실측 18px 균일)+파라미터 스프링(BodyAngleX/Z 물리 소유)+어깨 실측 입력 · 목: 首の曲面 전가장자리 핀(참수선 해소, 주인님 스크린샷 진단) · **옷: 드레이프 스프링(CLOTH-PHYS-001 — 공식 스커트 그룹 실측 정박: 입력 BodyAngleX/Z 100/100, Delay 0.6 비율, A/B 픽셀 증명 8.09≈기대 7.92px, 접합 슬립 0.52px)** · 건강검진: 인스펙터 무반응 0건. 눈웃음 워프(EXPR-002 곡선 A)는 폴백 — 표정은 004 생성 시트. 잔존 갭: 입꼬리 파라미터·팔·각도 폼·눈썹 모양·리본 개별 찰랑(004 분리 작화 필요) |
| **렌더 백엔드 (PIXI-RENDER-001)** | **완료 (2026-06-11)** | PixiJS v8 WebGL 기본(`?renderer=pixi`) — 풀해상도 상태 전환 ~1ms·실효 60fps (canvas2d 대비 ~100×). canvas 폴백 유지. verify 5/5 양 백엔드 PASS |
| AUTORIG-TEMPLATE-SPEC-001 | 완료 (2026-06-11 개정) | 생성 목록: 마스터 + 입 시트 + **눈 표정 시트(눈웃음·윙크·놀람·반개·><·하트눈) + 액센트 시트(홍조·그늘·눈물·땀)** — 표정은 워프가 아니라 동일세션 생성 작화 (`docs/ref/AUTORIG-MASTER-SPEC.md` §3.2~3.4) |
| AUTORIG-PIPELINE-CLI-001 | **완료 (2026-06-11)** | `run_autorig_pipeline.py` 원커맨드 — 003 풀런 76분(순수 연산 ~22분), H1/H1.5/H2 관제탑 게이트. **P5 자동 검증 6종**: validator·mesh verify·blink 잔상·perf·rig 인스펙터(무반응 게이트)·**옷 물리 A/B**(`validate_clothes_physics.py`) |
| AUTORIG-ANCHOR-DETECT-001 | 0% | 프로덕션 갭 (임의 업로드 PNG 앵커 검출) |

## Production Direction

- Target: 템플릿 이미지 생성 → 결정론적 추출 → 자동 리깅(rig JSON) → 자체 런타임 → 웹캠 실시간 버튜버 서비스.
- 픽셀 좌표는 결정론적 도구만 사용한다. LLM 비전 좌표 추측 금지 (evidence log DISCARDED 결론).
- PNG 풀캔버스 실험은 배치/키포즈 증거이며 프레임 스왑 런타임이 아니다.

## Evidence

- 전체 증거 테이블(169행)과 검증 명령 모음은 `docs/archive/2026-06-10-PROJECT-STATUS-pre-autorig-pivot.md`에 보존.
- 시행착오 이력과 상태 관리(VERIFIED/DISCARDED 등)는 `vtube-validation-evidence-log.md`.
- 실험별 증거는 각 `experiments/<id>/reports/`.

## Next Actions

1. **AUTORIG-CHARACTER-004 풀런** — 초커 기본 적용 마스터 재생성 → 원커맨드 (이번 세션 규칙 전부 자동 상속, FACIAL-TEST-CHECKLIST로 H2).
2. `AUTORIG-PLAYER-001` — 사용자 산출물(웹 링크·OBS 브라우저 소스·투명 모드 `?transparent=1`·오픈 ZIP).
3. `AUTORIG-ANCHOR-DETECT-001` — 임의 업로드 PNG 앵커 자동 검출 + rembg 입력 전처리 (프로덕션 갭).
4. 분해 풀해상도화 (CUDA 런북은 `docs/archive/2026-06-08-superseded-plans/`에 보존 — 재개 시 꺼내 갱신) + 키폼 사다리 (목 접합 근본 개선).

## Rules

- 증거 JSON, QA 리포트, 수동 리뷰 JSON 삭제 금지.
- 이 문서는 짧게 유지. 상세 이력은 evidence log나 실험 reports로.
- 대체된 플랜은 `docs/archive/`로 이동하고 `ARCHIVE-INDEX.md`에 기록.
- Human review FAIL은 keep으로 승격하지 않는다.

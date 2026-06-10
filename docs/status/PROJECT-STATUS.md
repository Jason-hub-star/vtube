# Vtube Project Status

Updated: 2026-06-11 (rig v1.0)

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
| 트래킹 (MediaPipe→Cubism 파라미터) | **T3 PASS (2026-06-11)** | **체인 끝단 최초 연결**: T1 스트림 → `__miniProbe` → 자체 Mini Cubism 런타임(v21). 합성 12샘플 + 175프레임 재생 스모크 PASS. `scripts/run_mini_cubism_webcam_drive.py` (실웹캠 /drive 페이지 포함) |
| 자체 런타임 (mini_cubism 계보) | 주입 API 완비 | `__miniProbe` (waitReady/setParameterValues/canvasHash) 추가 |
| **관제탑 대시보드** | **완성 (2026-06-11)** | 이벤트 JSONL 컨벤션(`scripts/autorig_events.py`) + 서버(8095, macOS 알림) + 토스스타일 UI(타임라인/피드/게이트 드래그 수정/QA/로그) + 시뮬레이터. 스모크: 파이썬 18/18, 브라우저 8/8 PASS |
| **소재 (하이브리드 레시피)** | **VERIFIED** | 진짜 마스터 분해+원본 재스킨(가시) + 동일세션 시트(숨은) — `vtube-hybrid-material-recipe` 하니스화. 전체 슬롯 생성은 기하 비정합으로 DISCARDED |
| **자동 리깅 (rig v1.0)** | **완성, H2 대기** | `build_autorig_rig_v0.py` — 39파트·8워프·10파라미터·물리 3그룹. 표정 성공패턴: 눈=ARAP 워프, 입=밀착 4상태 스프라이트+턱선가드 (주인님 합격). 몸 BodyAngle±10+Breath, 머리 5덩어리(무손실 분할)+v0-3 스프링. T3 재생 applied 9/프레임 |
| AUTORIG-TEMPLATE-SPEC-001 | 완료 | 12시트 스펙 (숨은 레이어 생성 전용으로 용도 확정) |
| AUTORIG-PIPELINE-CLI-001 | 관제 인프라 완료 | 단계 스크립트들은 검증됨 — 원커맨드 묶기가 남은 작업 |
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

1. **주인님 H2 검수** — 웹캠 드라이브(8063)에서 rig v1.0 전신 확인 (머리 찰랑임·호흡·상체).
2. `AUTORIG-PIPELINE-CLI-001` — 검증된 단계 스크립트들을 "자동화파이프라인 시작" 원커맨드로 묶기 (+P0 마스터 검증 게이트).
3. `AUTORIG-ANCHOR-DETECT-001` — 임의 업로드 PNG 앵커 자동 검출 (프로덕션 갭).
4. 분해 풀해상도화 (Ubuntu CUDA 런북) + ARAP 메시변형 고도화 (v2 품질 사다리).

## Rules

- 증거 JSON, QA 리포트, 수동 리뷰 JSON 삭제 금지.
- 이 문서는 짧게 유지. 상세 이력은 evidence log나 실험 reports로.
- 대체된 플랜은 `docs/archive/`로 이동하고 `ARCHIVE-INDEX.md`에 기록.
- Human review FAIL은 keep으로 승격하지 않는다.

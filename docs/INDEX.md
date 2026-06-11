# Vtube 문서 인덱스 (AI 컨텍스트 내비게이션)

Updated: 2026-06-11

AI 에이전트는 이 파일을 먼저 읽고, 필요한 문서만 골라 연다. 전부 읽지 않는다.

## 읽기 순서 (새 세션)

1. `docs/status/PROJECT-STATUS.md` — 현재 방향·진행률·다음 작업 (짧음, 항상 최신)
2. `docs/ref/AUTORIG-PIPELINE-V1.md` — 현재 생산 방향 상세 (자체 에디터 + AI 자동리깅)
3. 작업과 관련된 항목만 아래 지도에서 선택

## 문서 지도

### 현재 SSOT (항상 신뢰)

| 문서 | 내용 |
|---|---|
| `docs/status/PROJECT-STATUS.md` | 현재 단계, 블로커, 다음 작업 ID |
| `docs/ref/AUTORIG-PIPELINE-V1.md` | AUTORIG 파이프라인 P0–P6 스펙, 재사용 자산, 폐기 항목 |
| `vtube-validation-evidence-log.md` | 전체 시행착오 기록 (VERIFIED/OBSERVED/DISCARDED 상태 관리, 5000줄+ — grep으로 검색해서 읽기) |

### 레퍼런스 (필요할 때만)

| 문서 | 내용 |
|---|---|
| `docs/ref/AUTORIG-MASTER-SPEC.md` | **마스터 생성 사양 (P0)** — 생성 조건표·프롬프트 템플릿·입 4상태 시트 규약 (매 캐릭터 재사용) |
| `docs/ref/FACIAL-TEST-CHECKLIST.md` | H2 페이셜 검수 시트 (머리 XYZ/눈/입/물리/성능 — 매 캐릭터 재사용) |
| `docs/ref/CUBISM-V2-SUCCESS-PATTERN-PLAN.md` | 57모델 분석 기준치·티어·택소노미·파라미터 표준 (분석만 잔류 — 구 플랜 절은 아카이브) |
| `docs/ref/CUBISM-V2-REVIEW-GATE-SPEC.md` | 시각/시맨틱 QA 게이트 체크리스트 (P4 게이트에 재사용) |
| `experiments/live2d-keypose-spec-001/reports/live2d_keypose_spec.md` | 키포즈 스펙 (PNG=증거, 리그=생산 원칙) |

### 핵심 실험 증거 (경로만 기억, 본문은 grep)

| 실험 | 내용 |
|---|---|
| `experiments/reference-model-structure-001/` | 57모델 구조 분석, 64-part 스펙, MediaPipe→Cubism 파라미터 맵, T0/T1 트래킹 스모크 |
| `experiments/live2d-strong-model-pattern-001/` | strong20/all57 런타임 베이스라인, 디포머 계층 테이블, T2 파라미터 드라이브 |
| `experiments/autorig-character-003/` | **현재 캐릭터** — 원커맨드 풀런 실증 (41파트 리그, H2 조건부 합격, pixi perf 리포트) |
| `experiments/cubism-v2-new-character-002/` | 구캐릭터 (64-part 후보, CLI 리허설 표본) |
| `experiments/see-through-mps-compat-002/` | 레이어 분해 Mac MPS 경로 (512/640 PASS) |
| `experiments/imagen-live2d-001/` | 얕은 리그 실패 fixture (반복 금지 증거) |
| `experiments/cmo3-structure-fixture-001/` | 리그 구조 검증기 양성 fixture |

### 앱/도구

| 경로 | 내용 |
|---|---|
| `mini_cubism_app/` | **자체 런타임** (003 풀런 실증) — 기본 PixiJS v8 WebGL(`?renderer=pixi`, 풀해상도 60fps) + canvas2d 폴백, rig JSON, FFD 격자 변형 |
| `review_app/` | 파트 순도 휴먼 리뷰 UI (KEEP/REVISE/REGENERATE) |
| `scripts/INDEX.md` | **스크립트 색인 (266개, 카테고리·설명·LOC)** — 새 스크립트 작성 전 여기서 먼저 찾기. `build_scripts_index.py`로 재생성 |
| `scripts/lib/` | 공유 라이브러리 (io/image/server/proc) — 새 코드는 복붙 대신 여기서 import (코드 규칙: AUTORIG-PIPELINE-V1.md) |
| `asset_dashboard/index.html` | 썸네일 자산 대시보드 (`scripts/build_asset_dashboard.py`로 재생성) |
| `control_tower/` + `scripts/run_autorig_control_tower.py` | **관제탑** — 런 실시간 대시보드 (포트 8095, 게이트 알림/드래그 수정). 이벤트 컨벤션: `scripts/autorig_events.py`, 데모: `scripts/simulate_autorig_run.py` |
| `scripts/run_autorig_pipeline.py` | **원커맨드 파이프라인** — 마스터+입시트 2장 → P0~H2 전자동 (관제탑 게이트, 003 풀런 76분 실증) |
| `scripts/run_mini_cubism_webcam_drive.py` | **T3 웹캠 드라이브** — /drive에서 실웹캠·재생 모드로 자체 런타임 구동 (T3 스모크 PASS) |
| `experiments/cubism-v2-new-character-002/reports/autorig_current_candidates/current_candidates.json` | **64-part 현재 후보 단일 매니페스트** — AUTORIG P3 입력 (`scripts/build_autorig_current_candidates_002.py`) |

### 아카이브 (현재 방향 아님)

- `docs/archive/ARCHIVE-INDEX.md` — 아카이브 목록과 대체 문서
- `docs/archive/2026-06-10-PROJECT-STATUS-pre-autorig-pivot.md` — 피벗 전 전체 상태 (증거 테이블 169행 + 검증 명령 보존)

## 규칙

- 증거 JSON/QA 리포트/수동 리뷰 JSON은 삭제 금지.
- 이 인덱스는 문서가 추가·아카이브될 때마다 함께 갱신한다.
- 상세 이력은 evidence log나 실험 reports에 쓰고, PROJECT-STATUS는 짧게 유지한다.

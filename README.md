# Vtube

This project is an evidence-driven 2D VTuber production workspace.

## Read First

1. `/Users/family/jason/Vtube/docs/status/PROJECT-STATUS.md`
2. `/Users/family/jason/Vtube/docs/INDEX.md` — 문서 지도 (필요한 것만 골라 읽기)
3. `/Users/family/jason/Vtube/docs/ref/AUTORIG-PIPELINE-V1.md`

Do not read the full `vtube-validation-evidence-log.md` (5000+ lines); grep it for the topic at hand.

## Current Direction

**AUTORIG (2026-06-10 피벗)**: 자체 에디터/런타임 + AI 자동리깅. Cubism Editor 수동 저작 폐기, Cubism 파라미터 ID 표준은 유지.

- 입력: 마스터 1장 + 입 4상태 시트 1장 (`docs/ref/AUTORIG-MASTER-SPEC.md`)
- 원커맨드: `scripts/run_autorig_pipeline.py` (P0~H2, 관제탑 게이트 — 003 풀런 실증)
- 런타임: `mini_cubism_app/` — PixiJS v8 WebGL 기본(풀해상도 60fps) + canvas2d 폴백
- 픽셀 좌표는 결정론적 도구만 사용. LLM 비전 좌표 추측 금지.

Current mouth and blink PNG experiments are placement and key-pose evidence. They are not the final production runtime method.

## Current Next Work

`CLAUDE.md`의 "Current Next Work" 목록이 SSOT (PLAYER → ANCHOR-DETECT → RIG-SCHEMA → EDITOR).

## Evidence Rules

- Keep evidence JSON, QA reports, generated asset manifests, and manual review JSON.
- Archive superseded plans instead of deleting useful history.
- Treat human visual review and numeric ROI/bbox evidence as separate signals.
- Do not promote `FAIL` or `REVISE` evidence into production success without a new passing review.

## Shared Harness

Useful shared harnesses live here:

`/Users/family/jason/jason-agent-harness-template`

Run the harness health check:

```bash
bash /Users/family/jason/jason-agent-harness-template/scripts/check-harness.sh
```

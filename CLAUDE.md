# CLAUDE.md

## Start Here

Read these files first:

1. `/Users/family/jason/Vtube/docs/status/PROJECT-STATUS.md`
2. `/Users/family/jason/Vtube/docs/INDEX.md` — 문서 지도. 나머지는 여기서 필요한 것만 골라 읽는다.
3. `/Users/family/jason/Vtube/docs/ref/AUTORIG-PIPELINE-V1.md`

Do not read the full `vtube-validation-evidence-log.md` (5000+ lines); grep it for the topic at hand.

## Current Production Target

**AUTORIG (2026-06-10 피벗): 자체 에디터/런타임 + AI 자동리깅.** Cubism Editor 수동 저작은 폐기. Cubism 파라미터 ID 표준은 유지 (트래킹 맵·레퍼런스 분석 재사용).

Pipeline: 템플릿 슬롯 이미지 생성 → 결정론적 추출 → 자동 리깅(rig JSON) → 자체 런타임 → 웹캠 연동. 픽셀 좌표에 LLM 비전 추측 금지 — 결정론적 도구만 사용.

Do not treat the full-canvas mouth/blink PNG experiments as the final production runtime path. They are placement and key-pose evidence.

## Shared Harnesses

Shared Claude/Codex harnesses live in:

```text
/Users/family/jason/jason-agent-harness-template
```

Relevant Vtube harness:

```text
/Users/family/jason/jason-agent-harness-template/harnesses/vtube-doc-ssot-cleanup.md
```

Before changing the document structure, check:

```bash
bash /Users/family/jason/jason-agent-harness-template/scripts/check-harness.sh
sed -n '1,220p' /Users/family/jason/jason-agent-harness-template/harnesses/vtube-doc-ssot-cleanup.md
```

## Document Management

- Keep `/Users/family/jason/Vtube/docs/status/PROJECT-STATUS.md` short and current.
- Put detailed history in `/Users/family/jason/Vtube/vtube-validation-evidence-log.md` or experiment reports.
- Keep experiment evidence in each `experiments/<id>/reports/` folder.
- Archive superseded plans under `/Users/family/jason/Vtube/docs/archive/`.
- Do not delete evidence JSON, QA reports, generated asset manifests, or manual review JSON unless 주인님 explicitly asks.

## Current Next Work

1. `AUTORIG-CHARACTER-004` — 위벨 풀런 **H2 재판정 대기** (부품형 입·표정 6종·액센트 리깅 완료, H2 피드백 2라운드 반영 — HEAD-Z-PIVOT·RIG-COHESION 유기성 게이트 신설, P5 9게이트 PASS)
2. `AUTORIG-PLAYER-001` — 사용자 산출물 (웹 링크·OBS 브라우저 소스·투명 모드 `?transparent=1`·오픈 ZIP)
3. `AUTORIG-ANCHOR-DETECT-001` — 임의 업로드 PNG 앵커 자동 검출 + rembg 입력 전처리 (프로덕션 갭)
4. `AUTORIG-RIG-SCHEMA-001` — rig JSON 스키마 확정 (mini_rig.json: 메시/디포머/pin_edges/물리)
5. `AUTORIG-EDITOR-001` — 분산 에디터(8092/5174/review_app) 통합

완료 (2026-06-11): `AUTORIG-TEMPLATE-SPEC-001`(생성 목록 확정 — `docs/ref/AUTORIG-MASTER-SPEC.md`),
`AUTORIG-PIPELINE-CLI-001`(`run_autorig_pipeline.py`, 003 풀런 76분 실증),
`PIXI-RENDER-001`(PixiJS v8 WebGL 기본, 풀해상도 60fps).

(구 `PSD-LAYER-SCHEMA-001`/`CUBISM-IMPORT-CHECKLIST-001` 계열은 Cubism Editor 경로와 함께 폐기됨)

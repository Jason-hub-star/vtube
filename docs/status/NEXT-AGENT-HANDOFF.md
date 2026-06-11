# Next Agent Handoff

Updated: 2026-06-11

Address the user as `주인님` and work in Korean by default.

## Start Here

```text
/Users/family/jason/Vtube/docs/status/PROJECT-STATUS.md
/Users/family/jason/Vtube/docs/INDEX.md
/Users/family/jason/Vtube/docs/ref/AUTORIG-PIPELINE-V1.md
```

## Current Direction (2026-06-10 AUTORIG 피벗)

- Cubism Editor 수동 저작 폐기. 자체 에디터/런타임 + AI 자동리깅.
- Cubism 파라미터 ID 표준과 트래킹 맵(T0–T2 PASS)은 유지·재사용.
- 픽셀 좌표는 결정론적 도구만. LLM 비전 좌표 추측 금지.
- 완료 (2026-06-11): TEMPLATE-SPEC(개정 — 마스터+입+눈표정+액센트 시트 4장), PIPELINE-CLI(P5 자동검증 5종), PIXI-RENDER, EYE-NATURAL(상하 감김+정점 키폼 잔상 0), MOUTH-SNAP(잔상 해소 — 근본은 004 부품형 입), BODY-SWAY(골반 진자+파라미터 스프링), SHOULDER-TRACK(Pose 어깨 1:1, 주인님 승인), NECK-PIN(참수선 해소), RIG-HEALTH(인스펙터 무반응 0건·P5 게이트 편입).
- 실패 박제 (재시도 금지 경로): EXPR-001 표정 3종 일괄+자동발동(롤백 — evidence log 참조), TREMBLE-001 고정 임계 데드존.
- 다음 작업: 옷 물리(싼 워밍업) → `AUTORIG-CHARACTER-004` 사이클(생성 4장→H1→눈표정/액센트 추출기+부품형 입 구현→풀런) → `AUTORIG-PLAYER-001` → `AUTORIG-ANCHOR-DETECT-001` → `AUTORIG-RIG-SCHEMA-001` → `AUTORIG-EDITOR-001`.

피벗 이전 핸드오프(구 Cubism 저작 경로)는 `docs/archive/2026-06-10-NEXT-AGENT-HANDOFF-pre-autorig-pivot.md`에 보존.

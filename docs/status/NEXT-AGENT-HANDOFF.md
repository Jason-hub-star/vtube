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
- 완료 (2026-06-11): TEMPLATE-SPEC(개정 — 마스터+입+눈표정+액센트 시트 4장), PIPELINE-CLI(P5 자동검증 7종), PIXI-RENDER, EYE-NATURAL(상하 감김+정점 키폼 잔상 0), MOUTH-SNAP(잔상 해소 — 근본은 004 부품형 입), BODY-SWAY(골반 진자+파라미터 스프링), SHOULDER-TRACK(Pose 어깨 1:1, 주인님 승인), NECK-PIN(참수선 해소), RIG-HEALTH(인스펙터 무반응 0건·P5 게이트 편입), **CLOTH-PHYS-001(옷 드레이프 스프링 — 공식 스커트 그룹 정박, A/B 픽셀 증명, P5 편입; 2026-06-12)**, **TRACKING-MAPPER-QA-001(MouthForm 20번째 파라미터 + 저장 스트림 재생 QA 6검사 풀 PASS, P5 편입; 2026-06-12)**.
- 실패 박제 (재시도 금지 경로): EXPR-001 표정 3종 일괄+자동발동(롤백 — evidence log 참조), TREMBLE-001 고정 임계 데드존.
- 측정 박제 (CLOTH-PHYS-001 교훈): 밴드 시프트 측정 시 스프링 비대상 파트(팔·머리 실루엣)가 SSD를 지배해 효과를 0으로 오측정 — 순수 대상 x창으로 제한할 것. 헤드리스 벽시계 대기는 타이머 스로틀로 비결정 — `__miniStepPhysics` 직접 스텝으로 정착시킬 것.
- 다음 작업: `AUTORIG-CHARACTER-004` 사이클(생성 4장→H1→눈표정/액센트 추출기+부품형 입 구현→풀런) → `AUTORIG-PLAYER-001` → `AUTORIG-ANCHOR-DETECT-001` → `AUTORIG-RIG-SCHEMA-001` → `AUTORIG-EDITOR-001`.
- **004 캐릭터 (주인님 지정 2026-06-12): 위벨 (장송의 프리렌)** — 녹색 머리·녹색 눈·앞머리 사이 눈 노출. MASTER-SPEC 조건 적용: 얇은 초커(조건 9)·리본/옷자락 분리 작화(조건 10). 주의: 실존 IP 캐릭터라 생성 API가 이름 직지정을 거부할 수 있음 — 거부 시 외형 서술형 프롬프트("Übel-inspired": green layered hair, sharp green eyes, dark dress)로 폴백.
- **이미지 생성 = OpenAI API (gpt-image-2, Codex 구독 종료)**: 키는 `~/.config/vtube/openai_api_key` (600, 저장소 밖 — 절대 커밋 금지). 생성 스크립트가 이 파일을 읽어 `OPENAI_API_KEY`로 사용. 비용 ~$0.26/장(high 1024² + 마스터 레퍼런스 입력), 1사이클 4장 ≈ $1.

피벗 이전 핸드오프(구 Cubism 저작 경로)는 `docs/archive/2026-06-10-NEXT-AGENT-HANDOFF-pre-autorig-pivot.md`에 보존.

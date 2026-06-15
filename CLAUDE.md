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

1. `AUTORIG-CHARACTER-005` (지피쨩) — **첫 "코드 0줄 3D급" 빌드 완료 (2026-06-15)**: 머리 XYZ 입체(foreshortening)+상체회전(torso_turn_warp)을 빌더 자동 내장, 맥 MPS 분해, 입 3단 수정(원형·이중·입꼬리 해소). **다음 우선: 턱 "수염" = face_base 알파 가장자리가 목 위에 점선 이음새(은발 보브라 턱 노출). fix=face_base 가장자리 목에 페더 블렌드.** 상세: evidence `AUTORIG-CHARACTER-005`, PROJECT-STATUS 인수인계
2. `AUTORIG-CHARACTER-004` — 위벨 풀런 **H2 재판정 대기** (부품형 입=윗입술 고정+아랫입술 하강 MOUTH-LIP-PARTS, 표정 6종·액센트, H2 5라운드 반영). 입 5번 삽질 교훈 → 정비로 박제
2. `AUTORIG-TEMPLATE-001` — **캐릭터 스펙 분리 정비 완료 (2026-06-13)**: `characters/<id>.yaml`(외형·`expression_style`·색 힌트) + `lib/character_spec.py`, `generate_master_sheets --character-spec`, 색·OVERLAP·목높이 실측 자동화. 005부터 코드 0줄 수정으로 캐릭터 추가. 잔여: 입 H2 후 정비 코드로 통합 풀런
3. `AUTORIG-PLAYER-001` — 사용자 산출물 (웹 링크·OBS 브라우저 소스·투명 모드 `?transparent=1`·오픈 ZIP)
4. `AUTORIG-ANCHOR-DETECT-001` — 임의 업로드 PNG 앵커 자동 검출 + rembg 입력 전처리 (프로덕션 갭)
5. `AUTORIG-RIG-SCHEMA-001` — rig JSON 스키마 확정 (mini_rig.json: 메시/디포머/pin_edges/물리)
6. `AUTORIG-EDITOR-001` — 분산 에디터(8092/5174/review_app) 통합

폐기 (2026-06-13): `AUTORIG-ANGLE-SWAP-001/002`(각도 작화 스왑) — 정면에서 옆모습은 작화 스왑으로 안 됨(정지 사진·사진넘기기). 코드·미니·드라이브 매핑 리셋. 머리 각도는 본체 메시 ±30 유지. PNG→3D 원클릭 리깅툴 부재로 진짜 3D는 별도 피벗 필요 → 2D 유지. 상세 evidence `AUTORIG-ANGLE-SWAP-001/002`(ABANDONED)

완료 (2026-06-11): `AUTORIG-TEMPLATE-SPEC-001`(생성 목록 확정 — `docs/ref/AUTORIG-MASTER-SPEC.md`),
`AUTORIG-PIPELINE-CLI-001`(`run_autorig_pipeline.py`, 003 풀런 76분 실증),
`PIXI-RENDER-001`(PixiJS v8 WebGL 기본, 풀해상도 60fps).

(구 `PSD-LAYER-SCHEMA-001`/`CUBISM-IMPORT-CHECKLIST-001` 계열은 Cubism Editor 경로와 함께 폐기됨)

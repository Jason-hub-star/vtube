# AUTORIG Pipeline v1 — 자체 에디터 + AI 자동리깅 방향 문서

Updated: 2026-06-10
Status: CURRENT DIRECTION (주인님 결정, 2026-06-10)

## 목표

주인님이 **"자동화파이프라인 시작"** 이라고 말하면, 사람 개입 없이 아래 체인이 1시간 이내에 완주된다.

```text
템플릿 이미지 생성 → 레이어 추출/정규화 → 자동 리깅 → 자체 런타임 로드 → 웹캠 연동
```

Cubism Editor는 사용하지 않는다. 리깅 결과물은 자체 오픈 포맷(rig JSON)이고,
렌더는 자체 런타임(mini_cubism_app 계보)이 담당한다.

## 핵심 원칙

1. **Cubism Editor 비사용, 파라미터 표준은 유지.**
   `.cmo3/.moc3` 수동 저작 경로는 폐기한다. 단 파라미터 ID는 Cubism 표준
   (`ParamAngleX`, `ParamEyeLOpen`, `ParamMouthOpenY` 등)을 그대로 쓴다.
   이유: 57모델 성공 패턴 분석과 MediaPipe→Cubism 파라미터 맵(T0–T2 PASS)을 그대로 재사용하기 위함.
2. **템플릿화된 이미지 생성 = 결정론적 앵커.**
   파트 시트를 "고정 슬롯 레이아웃"으로 생성한다. 어느 슬롯에 어떤 파트가 있는지
   생성 시점에 이미 알기 때문에, 추출·배치에 LLM 비전 추측이 필요 없다.
   (evidence log 결론: 좌표 추측 DISCARDED, 수치 앵커 VERIFIED — 이 원칙의 근거)
3. **LLM은 오케스트레이션과 합/불 판단만, 픽셀 좌표는 결정론적 도구만.**
   알파 무게중심, bbox, 고정 슬롯 ROI, 랜드마크 검출이 좌표를 결정한다.
4. **품질 사다리.** v0 자동 리그는 strong20 중앙값(ArtMesh 88, 파라미터 44, Warp 53.5,
   Keyform 220.5)에 못 미쳐도 된다. 단계별 자동 생성 규칙을 늘려 사다리를 올라간다.

## 파이프라인 스테이지 (시간 예산 합계 ≈ 45분, 상한 1시간)

| 스테이지 | 내용 | 자동화 방식 | 예산 |
|---|---|---|---:|
| P0 | 캐릭터 컨셉 입력 → config 생성 | 템플릿 config (파트 스펙 64-part 재사용) | 2분 |
| P1 | 템플릿 슬롯 시트 이미지 생성 | imagegen, 고정 레이아웃 프롬프트 | 15분 |
| P2 | 슬롯 기반 추출·2048 RGBA 정규화 | 고정 ROI 크롭 + 알파 클린업 (LLM 불개입) | 5분 |
| P3 | 자동 리깅: rig JSON 생성 | 알파 지오메트리→메시, 파트 스펙→디포머 트리, 템플릿 키포즈→키폼 | 8분 |
| P4 | 자동 QA 게이트 | 기존 validator 재사용 + 수치 오버레이 diff (비전 LLM 최소화) | 5분 |
| P5 | 자체 런타임 로드 + 파라미터 스윕 스모크 | mini_cubism 런타임, 헤드리스 캡처 | 5분 |
| P6 | 웹캠 연동 | 검증된 MediaPipe→Cubism 파라미터 맵 (T0–T2 PASS 재사용) | 5분 |

## 휴먼 검수 게이트 (주인님 결정, 2026-06-10)

- **캐릭터 디자인: character-002 유지.** 기존 source front를 스타일 레퍼런스로만 사용 (픽셀 재사용 금지, 그림체·생김새 기준).
- 검수 원칙: 기계가 판단 못 하는 것에만 주인님을 부른다. 주인님의 메인 검수 지점은 **파트 배치**다 (역대 실패의 최빈 원인).

| 게이트 | 위치 | 내용 | 예상 시간 |
|---|---|---|---:|
| H1 스타일 락 | P1 직후 | 마스터 시트 1장 보고 그림체/캐릭터 일치 승인 | 2분 |
| **H1.5 배치 검수 (메인)** | **P2 직후, P3 리깅 전** | 합성 오버레이 1장으로 전 파트 위치 확인, 어긋난 파트는 드래그 에디터로 즉석 수정 → 저장 시 자동 재개 | 5–10분 |
| H2 최종 승인 | P6 직후 | 웹캠으로 움직이는 결과를 보고 승인/반려 | 5분 |

- **검수 단위 규칙 (주인님 피드백, 2026-06-11): 휴먼 시각 검수는 항상 "조립 합성" 단위로 보여준다.** 눈은 흰자+홍채+동공+하이라이트+속눈썹이 합쳐진 상태, 입은 내부+이빨+혀+입술이 합쳐진 상태. 낱장 레이어로는 품질 판정이 불가능하므로 게이트 UI에 낱장만 제시하는 것을 금지한다 (낱장은 위치/추출 디버그용). 합성 규칙: draw_order_band back→mid→front, 중립 조립에서 closed 키포즈 레이어 제외 (`scripts/build_asset_dashboard.py:compose` 참조).
- 배치 검수를 P3 앞에 두는 이유: 잘못된 배치 위에 리깅하면 메시/키폼 재작업이 가장 비싸다.
- 중간 파트 품질은 수치 게이트 + 대시보드 비동기 확인 (파이프라인 비차단, 사후 REVISE 가능).
- 파이프라인이 게이트에서 대기 중일 때는 로컬 UI(드래그 에디터/오버레이 뷰)를 자동으로 띄운다.

## 재사용 자산 (이미 검증된 것)

- **파트 분류 체계**: `v2_standard` 64-part 스펙 (`reference-model-structure-001`)
- **리그 구조 목표치**: strong20/all34 디포머 계층·키폼 floor (`live2d-strong-model-pattern-001`)
- **자체 런타임 씨앗**: `mini_cubism_app/` + `mini_rig.json` 포맷 (19파트, 디포머, 키폼 바인딩, 파라미터 슬라이더 동작 확인)
- **앵커/드래그 에디터 씨앗**: `run_cubism_v2_keypose_anchor_editor_002.py`(8092), `run_cubism_v2_semantic_anchor_editor.py`(5174), review_app — AUTORIG 에디터로 통합 예정
- **트래킹 체인**: MediaPipe→12 파라미터 맵, T0(합성)/T1(웹캠)/T2(레퍼런스 모델 드라이브) PASS
- **검증 인프라**: keypose/material validator, overlay QA, Mini Cubism 헤드리스 스모크

## 폐기/보류 항목

- G7 "실제 Cubism Editor 저작" 게이트: 폐기 (자체 리깅으로 대체)
- G8 CMO3/MOC3 구조 검증: 자체 rig JSON 구조 검증으로 대체
- `.moc3` export 및 Live2D SDK 출판 라이선스 의존: 보류 (자체 런타임이라 불필요)
- B4/B5 수동 앵커 미세조정 루프: 템플릿 슬롯 방식이 앵커 문제 자체를 제거하므로 중단

## 가설 규율 (2026-06-11 괴물 사건 회고에서)

1. **기존 성공패턴(예: `single_master_png_first`)을 폐기하는 새 방식은, 폐기 근거 실험 1건을 먼저 만들고 나서 SSOT에 쓴다.** 미검증 가설을 SSOT에 사실처럼 적는 것 금지 — SSOT 오염의 실제 사례가 이 사건이다.
2. **파일럿 판정은 자력 맥락에서**: 원본 위 오버레이처럼 기존 기하를 빌린 화면으로 새 방식을 합격시키지 않는다. 자력 조립으로 판정한다.
3. **P0 입력 검증**: 마스터 이미지는 눈/입 존재 검사를 통과해야 한다 (클린베이스 오인 방지). 사용자 업로드 서비스에서도 동일.
4. **주인님이 "이상하다"고 하면 표면 수정 전에 아키텍처 가정부터 의심한다.**

## 코드 규칙 (주인님 승인, 2026-06-11)

배경: scripts/ 258개 평면 파일에 `rel()` 151벌·`load_json` 145벌·컨택트시트 26벌이 복붙되어 있던 상태의 재발 방지.

1. **lib 사용 의무**: 새 스크립트는 `scripts/lib/`(vtube_io·vtube_image·vtube_server·vtube_proc)에서 import한다. rel/load_json/write_json/컨택트시트/서버 보일러플레이트/wait_for_server 복붙 금지.
2. **캐릭터 ID 하드코딩 금지**: 캐릭터 종속 경로·ID는 `--config`/인자로 받는다. `*_002.py` 같은 캐릭터 접미사 스크립트를 새로 만들지 않는다.
3. **파일 500줄 상한**: 넘으면 분리. `scripts/INDEX.md`에 ⚠️로 표시된다.
4. **인덱스 갱신**: 스크립트 추가/삭제 후 `python3 scripts/build_scripts_index.py` 재실행. 새 스크립트 작성 전 INDEX에서 기존 것을 먼저 찾는다.
5. **기존 스크립트는 일괄 수정하지 않는다**: 검증된 증거 스크립트는 손대는 시점에만 lib로 점진 전환.
6. **scripts/ 물리적 폴더 이동 금지**(lib/ 제외): 증거 로그·상태 문서가 `scripts/<이름>.py` 경로를 수백 곳 참조하므로 이동 대신 INDEX 분류로 관리한다.

## 선행 작업 (AUTORIG 런타임 승격 전 필수)

- `AUTORIG-RUNTIME-SPLIT-001`: ✅ **완료 (2026-06-11)**. app.js 1,673줄 모놀리스를 11개 ES 모듈로 분할 (`core/`: state·utils·rig·physics·draw — DOM 의존 없는 서비스 플레이어 코어 / `ui/`: components·rig_panel·pointer·dom / `probe.js` / `main.js`, 최대 392줄). 분할은 `scripts/split_mini_cubism_app.py`가 기계적으로 수행 (코드 수정 0, import 자동 계산). 무회귀 검증: T3 스모크 PASS + eye mode validator 구/신 동일 판정(REVISE는 분할 전부터 존재하던 아이커버 WIP 상태). 서비스 플레이어는 `core/*` + 최소 부트스트랩만 로드하면 된다.

## 다음 작업 ID

1. `AUTORIG-TEMPLATE-SPEC-001` — 고정 슬롯 시트 레이아웃 스펙 + 생성 프롬프트 템플릿 (64-part를 슬롯에 매핑) ✅ 완료, 눈 시트 파일럿 슬롯 준수 16/16
1-b. `AUTORIG-ANCHOR-DETECT-001` — **프로덕션 갭**: 임의 업로드 PNG에서 타깃 앵커(눈/입/얼굴 bbox) 자동 검출. 지금은 character-002 매니페스트 bbox 재사용으로 대체 중. 프로덕션 입력(사용자 PNG 업로드)은 ① 스타일 레퍼런스(숨은 레이어 생성) ② 앵커 검출 소스 ③ 가시 대형 파트의 분리 소스 세 역할로 쓰인다. 눈/입 내부는 가림(occlusion) 때문에 분리가 아니라 생성이 정답 (v22 오염의 근본 원인).
2. `AUTORIG-RIG-SCHEMA-001` — rig JSON 스키마 확정 (mini_rig.json 확장: 메시/디포머/키폼/물리)
3. `AUTORIG-PIPELINE-CLI-001` — P0–P6 원커맨드 CLI (character-agnostic, config 기반)
4. `AUTORIG-EDITOR-001` — 분산된 로컬 에디터(8092/5174/review_app)를 단일 자체 에디터로 통합

## P3 자동 리깅 설계 노트 (2026-06-11 웹 리서치 반영)

- **메시 생성**: 레이어 알파 윤곽 기반 들로네 삼각분할 (Live2D 자체 auto-mesh와 동일 원리, 결정론적).
- **변형 후보 — ARAP(As-Rigid-As-Possible)**: Meta [AnimatedDrawings](https://github.com/facebookresearch/AnimatedDrawings) (MIT, 코드·모델 공개)가 쓰는 방식. 소수 제어점만 움직이면 메시 전체가 자연스럽게 따라온다 — 키폼을 손으로 다 만들지 않고 "제어점 키포즈"만 정의하는 경로. 머리카락 흔들림/얼굴 워프 후보.
- **아키텍처 외부 검증**: [CartoonAlive](https://arxiv.org/abs/2507.17327) (초상화 1장→Live2D 30초, 코드 미공개)가 동일 구조(분해→메시→랜드마크 기반 파라미터 회귀→숨은부위 합성)를 사용. 코드 공개 시 추적.
- **앵커 자동 검출 실현 근거**: AnimatedDrawings는 아마추어 드로잉 17.8만 장으로 파인튠한 검출기로 자동 리깅 — 애니메 얼굴 랜드마크 검출도 동일 접근 가능 (`AUTORIG-ANCHOR-DETECT-001`).
- 참고 도구: [Stretchy Studio](https://github.com/MangoLion/stretchystudio) (FOSS, 일러스트→메시 변형, 2026-04 갱신) — `rigging-open-source-research-001`에 이미 수집됨, 메시 UX 참고.

## 리스크 메모

- 템플릿 슬롯 생성의 이미지 모델 순응도(슬롯 이탈, 스타일 불일치)는 P1에서 자동 재시도 + 수치 슬롯 점유율 검사로 방어한다.
- 자동 메시/키폼의 시각 품질 하한은 P5 파라미터 스윕 캡처로 수치화하고, 미달 시 품질 사다리 규칙을 추가한다.
- VTube Studio 등 외부 생태계 호환이 나중에 필요해지면 그때 export 어댑터를 검토한다 (지금은 비목표).

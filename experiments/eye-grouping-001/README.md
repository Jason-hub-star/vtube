# eye-grouping-001

작성일: 2026-06-02

## 목적

`eye_white / iris / lash_or_lid` 후보를 semantic class로 나누고, canonical iris anchor 기준으로 full eye group을 자동 조립할 수 있는지 검증한다.

## 실행 명령

```bash
python3 /Users/family/jason/Vtube/experiments/eye-grouping-001/scripts/eye_grouping_smoke.py
```

## 결과

```text
technical_grouping: PASS
coordinate_overlay: PASS
visual_alignment: FAIL
art_quality: FAIL
full_eye_composite: FAIL
decision: revise
```

## 핵심 수치

```text
class counts:
  eye_white: 4
  iris: 2
  lash_or_lid: 8
  other_eye_part: 4

left group:
  white=eye_03
  iris=eye_05
  lash=eye_04
  placement error=0.588px

right group:
  white=eye_02
  iris=eye_06
  lash=eye_01
  placement error=0.607px
```

## 실제로 통과한 것

```text
1. crop 후보를 alpha/color/shape feature로 대략 분류할 수 있다.
2. 좌우별로 eye_white, iris, lash_or_lid를 하나씩 고를 수 있다.
3. canonical iris anchor 근처에 부품을 얹을 수 있다.
```

## Human Review

```text
verdict: FAIL
reason: 위치도 안 맞고 미술 품질도 한참 부족함.
```

## 결론

```text
eye-grouping-001은 성공패턴이 아니다.
naive semantic grouping + iris anchor placement만으로는 full eye replacement가 불가능하다는 실패 evidence다.
iris-only placement는 유지할 수 있지만, full eye는 canonical eye geometry/mask 기반으로 다시 설계해야 한다.
```

## Evidence

```text
reports/eye_grouping_report.json
reports/qa_report.md
groups/left_eye_group.png
groups/right_eye_group.png
composites/both_full_eye_composite.png
```

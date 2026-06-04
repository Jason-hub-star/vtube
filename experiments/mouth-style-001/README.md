# MOUTH-STYLE-001 Mouth Candidate Scoring

작성일: 2026-06-02

## 목적

mouth 후보를 expression type, bbox ratio, color/style feature로 분류해 human review용 shortlist와 rejected 후보를 만든다.

## 실행

```bash
python3 /Users/family/jason/Vtube/experiments/mouth-style-001/scripts/mouth_candidate_scoring.py
```

## 결과

```text
expression_type_assignment: PASS
shortlist_created: PASS
rejected_candidates_recorded: PASS
visual_quality: REVISE
decision: keep
```

## Evidence

```text
reports/mouth_candidate_score_report.json
reports/qa_report.md
```

## 결론

mouth scoring은 후보 축소용으로 유지한다. style score는 production 승인 근거가 아니며 human review가 필요하다.

# CREATURE-SCHEMA-001 Non-Human Anchor Schema

작성일: 2026-06-02

## 목적

사람형 anime anchor 공식을 dog/cat/mascot 캐릭터에 그대로 재사용하지 않도록 schema를 분리한다.

## 결과

```text
human_anime: defined
dog_mascot: defined
cat_mascot: defined
missing_anchor_rule: defined
decision: keep
```

## Evidence

```text
reports/anchor_schema_report.json
reports/anchor_schema_plan.md
```

## 결론

비인간 캐릭터는 별도 canonical fixture가 생기기 전까지 human_anime placement 공식을 사용하지 않는다.

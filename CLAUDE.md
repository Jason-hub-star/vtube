# CLAUDE.md

## Start Here

Read these files first:

1. `/Users/family/jason/Vtube/AGENTS.md`
2. `/Users/family/jason/Vtube/docs/status/PROJECT-STATUS.md`
3. `/Users/family/jason/Vtube/2d-vtuber-ai-tool-plan.md`
4. `/Users/family/jason/Vtube/vtube-validation-evidence-log.md`
5. `/Users/family/jason/Vtube/experiments/live2d-keypose-spec-001/reports/live2d_keypose_spec.md`

## Current Production Target

Live2D/Cubism production rigging is the current target.

Do not treat the full-canvas mouth/blink PNG experiments as the final production runtime path. They are placement and key-pose evidence for PSD/Cubism work.

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

1. `PSD-LAYER-SCHEMA-001`
2. `LIVE2D-PARAM-MAP-001`
3. `CUBISM-IMPORT-CHECKLIST-001`
4. `RIG-REFERENCE-PACK-001`

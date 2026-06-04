# AGENTS.md

## User Preference

- Address the user as `주인님`.
- Work in Korean by default unless the task clearly needs another language.
- The main workspace root is `/Users/family/jason`.
- The current project is `/Users/family/jason/Vtube`.

## Collaboration

- Claude and Codex may work together on this project.
- Check Claude-side project instructions and shared harnesses when planning documentation, validation, or handoff work.
- Shared skills and harnesses are mainly stored in:

```text
/Users/family/jason/jason-agent-harness-template
```

## Harness Rule

When a useful reusable harness is discovered during work:

1. Save it under `/Users/family/jason/jason-agent-harness-template`.
2. Test it before treating it as useful.
3. Prefer evidence-backed harnesses over one-off notes.

## Vtube Project Rules

- Start with `/Users/family/jason/Vtube/docs/status/PROJECT-STATUS.md`.
- Use `/Users/family/jason/Vtube/vtube-validation-evidence-log.md` for detailed evidence status.
- Keep current direction aligned with Live2D/Cubism production, not PNG frame-swap production.
- Never delete evidence JSON, QA reports, generated asset manifests, or manual review JSON unless 주인님 explicitly asks.
- Archive superseded plans under `/Users/family/jason/Vtube/docs/archive/`.
- Keep screenshot review, human review, and numeric ROI/bbox evidence separate.
- Human review `FAIL` is never promoted to production success.

## Useful Commands

```bash
bash /Users/family/jason/jason-agent-harness-template/scripts/check-harness.sh
find /Users/family/jason/Vtube -path '*/external_repos/*' -prune -o \( -name '*.md' -o -name '*.json' \) -type f -print | wc -l
```

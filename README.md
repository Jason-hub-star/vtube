# Vtube

This project is an evidence-driven 2D VTuber production workspace.

## Read First

1. `/Users/family/jason/Vtube/docs/status/PROJECT-STATUS.md`
2. `/Users/family/jason/Vtube/2d-vtuber-ai-tool-plan.md`
3. `/Users/family/jason/Vtube/vtube-validation-evidence-log.md`
4. `/Users/family/jason/Vtube/experiments/live2d-keypose-spec-001/reports/live2d_keypose_spec.md`

## Current Direction

The current production target is Live2D/Cubism rigging:

- PSD-separated parts
- Cubism ArtMesh and Deformer setup
- standard Live2D parameters
- Cubism keyforms

Current mouth and blink PNG experiments are placement and key-pose evidence. They are not the final production runtime method.

## Current Next Tests

1. `PSD-LAYER-SCHEMA-001`
2. `LIVE2D-PARAM-MAP-001`
3. `CUBISM-IMPORT-CHECKLIST-001`
4. `RIG-REFERENCE-PACK-001`

## Evidence Rules

- Keep evidence JSON, QA reports, generated asset manifests, and manual review JSON.
- Archive superseded plans instead of deleting useful history.
- Treat human visual review and numeric ROI/bbox evidence as separate signals.
- Do not promote `FAIL` or `REVISE` evidence into production success without a new passing review.

## Shared Harness

Useful shared harnesses live here:

`/Users/family/jason/jason-agent-harness-template`

Run the harness health check:

```bash
bash /Users/family/jason/jason-agent-harness-template/scripts/check-harness.sh
```

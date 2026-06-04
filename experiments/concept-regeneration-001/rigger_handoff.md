# White Wolf Goth Cubism Handoff

Generated: 2026-06-04T02:11:49.720750+00:00
Status: PASS_WITH_CUBISM_IMPORT

## Gate Rule

Only parts with human verdict `O` are eligible for `import_ready_candidate.psd`.
`X`, `REVISE`, `REFERENCE_ONLY`, and unreviewed parts are excluded.

## Files

- Candidate PSD: `import_ready_candidate.psd`
- Candidate PNG layers: `psd_candidate_layers/`
- Gate report: `reports/psd_candidate_gate_report.json`
- Visual review: `reports/part_visual_review.json`
- AI fix queue: `reports/ai_fix_queue.json`

## Current Result

- Accepted layer count: 6
- Excluded layer count: 29
- PSD candidate exists: True

## Cubism Import Smoke

If `import_ready_candidate.psd` exists, open it in Live2D Cubism Editor 5.3 and
record `reports/cubism_import_smoke.json`:

```json
{
  "cubism_import_success": true,
  "layers_flattened": false,
  "reviewer": "name",
  "notes": "Layer list visible in Cubism Editor."
}
```

Do not promote `import_ready.psd` until this smoke passes.

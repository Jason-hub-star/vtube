# See-through Cubism Handoff

Generated: 2026-06-04T07:42:37.254399+00:00
Status: PASS_WITH_CUBISM_IMPORT

## Files

- Candidate PSD: `import_ready_candidate.psd`
- Candidate layers: `psd_candidate_layers/`
- Visual review: `reports/part_visual_review.json`
- Gate report: `reports/psd_candidate_gate_report.json`

## Cubism Smoke Requirement

Create `reports/cubism_import_smoke.json` after opening the PSD in Cubism Editor:

```json
{ "cubism_import_success": true, "layers_flattened": false, "notes": "Layer list visible." }
```


# Vtube Project Status

Updated: 2026-06-04

## Current Phase

- Live2D part-purity review and cleanup queue after Cubism PSD import validation.

## Production Direction

- Target: Live2D/Cubism rigging.
- Required production path: PSD-separated parts, ArtMesh, Deformer, standard parameters, Cubism keyforms.
- Current PNG tests are reference/key-pose evidence, not production frame-swap runtime.

## Current Evidence

| Track | Status | Evidence | Decision |
|---|---:|---|---|
| 2048 production canvas | VERIFIED | `production-canvas-2048-001/reports/resolution_spec_report.json` | Keep 2048 master canvas |
| Mouth placement workflow | VERIFIED | `mouth-apply-delta-001/reports/mouth_apply_delta_report.json` | Keep all current mouth candidates by 주인님 review |
| Blink staged candidates | OBSERVED/REVISE | `blink-stage-001/reports/blink_stage_report.json` | Use as Live2D key-pose reference only |
| Blink saved placement | OBSERVED/REVISE | `blink-apply-review-001/reports/blink_apply_review_report.json` | Do not promote to production success |
| Live2D direction | VERIFIED | `live2d-keypose-spec-001/reports/live2d_keypose_spec.md` | Current production SSOT |
| Cubism material pack v1 | VERIFIED | `cubism-material-pack-001/reports/validation_report.json` | psd-tools PSD imported in Cubism Editor 5.3; `import_ready.psd` promoted |
| Part purity review UI | VERIFIED | `part-purity-001/reports/part_visual_review.json` | Unified local UI saves human verdicts and AI cleanup queue |
| White Wolf Goth concept | PASS_WITH_CUBISM_IMPORT | `concept-regeneration-001/reports/cubism_import_smoke.json` | 2048 canonical, 35 review candidates, O-only PSD gate, and Cubism Editor import smoke passed for 6 AI technical-smoke layers |
| Full eye replacement | DISCARDED | `eye-grouping-001/reports/eye_grouping_report.json` | Do not retry sheet grouping by default |
| See-through local Mac path | BLOCKED | `validation-smoke-001/reports/see_through_environment_report.md` | Direct script path is blocked by deps/CUDA assumptions |
| Mac ComfyUI See-through path | FAIL_MPS_MEMORY | `see-through-layer-decomp-001/reports/comfyui_setup_report.json`, `reports/comfyui_mps_crash_report.json` | MPS runtime and nodes load, but GenerateLayers fails before layer output |
| Ubuntu CUDA See-through path | READY_TO_RUN | `docs/ref/UBUNTU-CUDA-SEETHROUGH-RUNBOOK.md` | Use CUDA for actual decomposition, then bring `*_layers.json` back to Mac review pipeline |

## Active Assets

- Canonical: `/Users/family/jason/Vtube/experiments/production-canvas-2048-001/canonical/canonical_front_2048.png`
- Mouth references: `/Users/family/jason/Vtube/experiments/mouth-apply-delta-001/layers/`
- Blink references: `/Users/family/jason/Vtube/experiments/blink-apply-review-001/layers/`
- Manual mouth evidence: `/Users/family/jason/Vtube/experiments/production-canvas-2048-001/reports/manual_adjustments_2048.json`
- Blink review evidence: `/Users/family/jason/Vtube/experiments/blink-stage-001/reports/blink_stage_review.json`
- Part purity UI: `/Users/family/jason/Vtube/review_app/index.html`
- AI fix queue: `/Users/family/jason/Vtube/experiments/part-purity-001/reports/ai_fix_queue.json`
- Part purity pipeline plan: `/Users/family/jason/Vtube/docs/ref/LIVE2D-PART-PURITY-PIPELINE.md`
- White Wolf Goth canonical: `/Users/family/jason/Vtube/experiments/concept-regeneration-001/canonical/canonical_front_2048.png`
- White Wolf Goth AI fix queue: `/Users/family/jason/Vtube/experiments/concept-regeneration-001/reports/ai_fix_queue.json`
- See-through Mac experiment: `/Users/family/jason/Vtube/experiments/see-through-layer-decomp-001`
- Ubuntu CUDA See-through runbook: `/Users/family/jason/Vtube/docs/ref/UBUNTU-CUDA-SEETHROUGH-RUNBOOK.md`

## Next Actions

1. Finish production part review in `review_app` and save every `O`, `X`, or `REVISE`.
2. Use `docs/ref/LIVE2D-PART-PURITY-PIPELINE.md` as the operating plan.
3. Start `part-purity-002` from `ai_fix_queue.json`, prioritizing `R_upper_lash` and `mouth_inner`.
4. For `concept-regeneration-001`, replace remaining bootstrap rough masks with AI-cleaned/generated part PNGs from its own `ai_fix_queue.json`.
5. Continue human visual review until all required concept production parts are either `O` or explicitly queued for regeneration.
6. Re-run `python3 scripts/build_concept_psd_candidate.py --promote` after each accepted batch.
7. Start minimal Cubism rigging only after critical face/eye/mouth/hair contamination is cleared.
8. Run See-through on Ubuntu CUDA using `docs/ref/UBUNTU-CUDA-SEETHROUGH-RUNBOOK.md`, then normalize ComfyUI `*_layers.json` into the review app before trusting any See-through layer.

## Verification Commands

- `bash /Users/family/jason/jason-agent-harness-template/scripts/check-harness.sh`
- `python3 scripts/build_review_manifest.py`
- `python3 scripts/build_concept_bootstrap_parts.py`
- `python3 scripts/build_concept_psd_candidate.py`
- `python3 scripts/setup_comfyui_seethrough_mac.py`
- `python3 scripts/run_comfyui_seethrough_prompt.py --resolution 1280 --steps 30 --depth-resolution 720`
- `python3 scripts/normalize_seethrough_outputs.py --layers-json <ComfyUI output *_layers.json>`
- `python3 scripts/build_seethrough_psd_candidate.py`
- `python3 scripts/validate_review_app.py`
- `find /Users/family/jason/Vtube -path '*/external_repos/*' -prune -o \( -name '*.md' -o -name '*.json' \) -type f -print | wc -l`

## Rules

- Do not delete evidence JSON, QA reports, or manual review JSON.
- Archive superseded plan documents instead of leaving them as current guidance.
- Keep this status short; detailed history belongs in `vtube-validation-evidence-log.md` or experiment reports.
- Human review FAIL is never promoted to keep.

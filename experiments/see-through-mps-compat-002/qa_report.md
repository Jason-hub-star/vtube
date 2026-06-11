# See-through MPS Compatibility 002 QA

Generated: 2026-06-04

## Scope

This experiment tests whether Apple Silicon MPS can produce useful See-through
layer candidates for Live2D/Cubism material prep. The outputs are not trusted as
production until human review, PSD candidate generation, and Cubism Editor import
smoke pass.

## Current Status

Status: `PASS_WITH_CUBISM_IMPORT`

Current review session: `mps_640_safe`

Current result:

- 512 MPS generated `*_layers.json`.
- 640 MPS generated `*_layers.json`.
- 640 produced 29 normalized 2048x2048 review candidates.
- User review says 640 is somewhat sharper than 512.
- 640 human review plus manual-mask review currently produced 15 PSD-accepted
  candidates.
- Practical gate passes with more than 5 useful `O` or `REVISE` candidates.
- Review saves now auto-build `import_ready_candidate.psd` from human `O`
  candidates.
- Cubism Editor 5.3 import smoke passed with 15 visible layer entries after the
  review-app manual neck mask was included.
- `import_ready_candidate.psd` was promoted to `import_ready.psd`.
- Three cleanup candidates were generated for the remaining failed/revise parts:
  `seethrough_mps_clean__face_base`, `seethrough_mps_clean__neck`, and
  `seethrough_mps_clean__clothes`.

## Evidence

```text
reports/mps_patch_report.json
reports/mps_512_safe_inference_report.json
reports/mps_640_safe_inference_report.json
reports/mps_640_safe_run_report.json
reports/normalize_report.json
reports/mps_candidate_contact_sheet.png
reports/mps_candidate_triage_report.json
reports/part_visual_review.json
reports/ai_fix_queue.json
reports/psd_candidate_gate_report.json
reports/psd_candidate_qa.md
reports/cubism_import_smoke.json
reports/cubism_import_smoke_log_excerpt.txt
reports/cubism_smoke_evidence/cubism_import_candidate_screen.png
reports/cubism_smoke_evidence/cubism_import_candidate_manual_neck_screen.png
reports/cleanup_candidate_report.json
reports/cleanup_candidate_contact_sheet.png
reports/manual_mask_report.json
import_ready_candidate.psd
import_ready.psd
psd_candidate_layers/
manual_masks/
manual_layers/
```

## 640 Smoke

Run settings:

```text
resolution=640
steps=12
depth_resolution=512
PYTORCH_ENABLE_MPS_FALLBACK=1
PYTORCH_MPS_LOW_WATERMARK_RATIO=0.90
PYTORCH_MPS_HIGH_WATERMARK_RATIO=1.30
```

Observed:

- `GenerateLayers` completed with 24 layers.
- `GenerateDepth` completed with 23 depth maps.
- `PostProcess` completed with 29 layers.
- Prompt execution time was about 402 seconds.

## Review Summary

Accepted `O` candidates are immediately copied into `psd_candidate_layers/` and
written into `import_ready_candidate.psd`.

Current Cubism-imported PSD accepted layers:

```text
back_hair
neck
face_base
mouth_line
R_brow
L_brow
R_iris
R_upper_lash
R_eye_white
L_eye_white
L_iris
L_upper_lash
L_ear_outer
R_ear_outer
front_hair
```

Current fix queue:

```text
clothes: X, skin_mixed
manual neck: O, included as neck
face_base: cleanup candidate O, raw face_base excluded by duplicate priority
clothes: X / cleanup still not accepted
```

## 512 Snapshot

The earlier 512 human review was preserved before resetting the current review
session for 640:

```text
reports/part_visual_review_20260604_512_review_before_640.json
reports/ai_fix_queue_20260604_512_review_before_640.json
```

Do not treat 512 verdicts as 640 quality evidence.

## Acceptance Gate

Current PSD metadata and Cubism Editor smoke pass.

Observed Cubism evidence:

```text
Cubism Editor 5.3.01 loaded import_ready_candidate.psd.
Log shows Read LayerAndMaskInfo:7137448 and load @PSDDocument.
Screenshot shows individual layer entries in the Cubism Parts panel, including
face_base, neck, and back_hair.
layers_flattened=false.
```

`import_ready.psd` is now the current MPS-derived Cubism import baseline. Art
quality is still limited by the current accepted candidates; `clothes` remains
the main cleanup/regeneration target.

## Cleanup Candidates

Current cleanup candidate status:

```text
seethrough_mps_clean__face_base: generated, O; selected over raw face_base by duplicate priority
seethrough_mps_clean__neck: generated, not selected
seethrough_mps_clean__clothes: generated, review pending; likely still broad
seethrough_mps_manual__neck: generated from review-app mask, O; included as neck
```

If a cleanup candidate receives human `O`, the review server will automatically
rebuild `import_ready_candidate.psd`. Cubism import smoke must be rerun before
promoting the expanded `import_ready.psd`.

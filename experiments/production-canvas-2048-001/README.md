# Production Canvas 2048 Test

Date: 2026-06-02

## Goal

Validate a production-oriented 2048x2048 bust-up VTuber canvas path for custom mouth and blink layers.

## Inputs

- `assets/canonical_source.png`: imagegen canonical source
- `assets/mouth_sheet_source.png`: imagegen mouth expression candidate sheet

## Outputs

- `canonical/canonical_front_2048.png`
- `layers/mouth_*_full.png`
- `layers/blink_closed_lids_full.png`
- `masks/left_eye_roi.png`
- `masks/right_eye_roi.png`
- `masks/mouth_roi.png`
- `overlays/*`
- `preview/index.html`
- `reports/*.json`
- `reports/qa_report.md`

## Review UI

`preview/index.html` now supports minimal manual review controls:

- candidate selection list
- drag layer adjustment
- arrow key nudge, with Shift for 10px
- scale and opacity sliders
- Korean review labels
- PASS/REVISE/FAIL verdict shown as 통과/수정/실패
- apply current placement to every candidate of the same part type
- local auto-save via browser localStorage
- server save to `reports/manual_adjustments_2048.json` when opened through `scripts/review_server_2048.py`
- browser download fallback for `manual_adjustments_2048.json`

Run the saving preview server:

```bash
python3 /Users/family/jason/Vtube/scripts/review_server_2048.py --port 8028
```

## Codex Skill

The current success pattern is captured as a Codex skill:

- `/Users/family/.codex/skills/vtube-custom-parts-validation/SKILL.md`
- `/Users/family/.codex/skills/vtube-custom-parts-validation/references/current-pattern.md`

Use it when continuing Vtube custom part validation in a new Codex session.

## Current Verdict

OBSERVED. The 2048 full-canvas workflow is structurally viable, but production approval still requires human visual review.

Important caveats:

- The image generator emitted a 1254x1254 source, then the script normalized it to 2048x2048.
- The canonical has visible chroma-key edge fringe.
- Eye ROI was usable, but automatic eye detection used fallback.
- Mouth full-canvas layers are numerically aligned, but visual quality remains `REVISE`.
- Blink layer avoids full eye replacement, but visual alignment remains `REVISE`.

## Repeat

```bash
python3 /Users/family/jason/Vtube/scripts/production_canvas_2048_smoke.py \
  --canonical-source /Users/family/jason/Vtube/experiments/production-canvas-2048-001/assets/canonical_source.png \
  --mouth-source /Users/family/jason/Vtube/experiments/production-canvas-2048-001/assets/mouth_sheet_source.png
```

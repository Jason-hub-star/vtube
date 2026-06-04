# Mouth Apply Delta 001

Date: 2026-06-02

## Goal

Apply the saved mouth manual correction from `production-canvas-2048-001` to newly generated mouth set A/B and determine whether corrected mouth sheet candidates can become production candidates.

## Inputs

- `asset-generation-2048-001/raw/mouth_set_a_stylematch_source.png`
- `asset-generation-2048-001/raw/mouth_set_b_simple_source.png`
- `production-canvas-2048-001/canonical/canonical_front_2048.png`
- `production-canvas-2048-001/reports/manual_adjustments_2048.json`

## Applied Delta

```json
{ "dx": -12, "dy": 2, "scale": 1.0, "opacity": 1.0 }
```

## Outputs

- `crops/*.png`
- `layers/*_auto_full.png`
- `layers/*_corrected_full.png`
- `overlays/*_auto_overlay.png`
- `overlays/*_corrected_overlay.png`
- `preview/index.html`
- `reports/mouth_apply_delta_report.json`
- `reports/qa_report.md`

## Verdict

VERIFIED.

Numeric ROI placement passed. 주인님 corrected the visual judgement: the mouth asset quality was acceptable, and calibrated canvas-coordinate placement made the corrected overlays usable enough.

After the updated review UI saved calibrated `canvas_dx/canvas_dy`, the corrected result became much better and usable enough by 주인님 visual review.

Keep:

- full-canvas layer structure
- manual delta evidence
- ROI/bbox reports
- preview/review workflow

Keep:

- calibrated full-canvas mouth layer workflow
- manual review evidence with display-pixel and 2048-canvas-pixel coordinates
- generated mouth sheet candidates as shortlist inputs

## Next

Use all 10 mouth candidates by 주인님 visual review. Move to other part tests now; revisit per-expression mouth offsets only if the rig preview exposes a specific issue.

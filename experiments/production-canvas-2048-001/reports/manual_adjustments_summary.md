# Manual Adjustments Summary

Date: 2026-06-02

Source:

- `reports/manual_adjustments_2048.json`

## Verdict

Manual evidence was saved successfully.

This is stronger evidence than a screenshot because it records numeric correction values that can be applied to the next alignment/revise pass.

Important correction: this legacy evidence was saved before the review UI recorded coordinate units. The `dx/dy` values are browser display pixels, not proven 2048 canvas pixels.

## Saved Corrections

| Part group | Candidates | dx | dy | scale | opacity | verdict |
|---|---:|---:|---:|---:|---:|---|
| mouth | 5 | -12 | 2 | 1.00 | 1.00 | REVISE |
| blink | 1 | -4 | -24 | 1.00 | 1.00 | REVISE |

## Interpretation

- Mouth candidates share the same visible correction: move left by 12 display px and down by 2 display px.
- Because all five mouth candidates use the same correction, this should be treated as a shared mouth target offset, not a per-expression issue.
- Blink closed lids need a separate visible correction: move left by 4 display px and up by 24 display px.
- Scale remains 1.00 for both groups, so the current issue is mostly placement, not size.
- Opacity remains 1.00, so transparency is not the review blocker.
- 주인님 correction: mouth asset quality was acceptable; the unresolved issue is calibrated placement.

## Next Revise Inputs

Use these values only as legacy display-pixel reference:

```json
{
  "mouth_group_delta": {
    "dx": -12,
    "dy": 2,
    "scale": 1.0,
    "opacity": 1.0
  },
  "blink_closed_lids_delta": {
    "dx": -4,
    "dy": -24,
    "scale": 1.0,
    "opacity": 1.0
  }
}
```

## Caution

All saved verdicts are still `REVISE`. These adjustments prove the visible direction of the needed placement correction, but they do not prove the correct 2048 canvas-pixel offset. Save evidence again from the updated review UI and use `canvas_dx/canvas_dy` for automatic image processing.

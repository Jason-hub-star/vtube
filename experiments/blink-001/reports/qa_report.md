# BLINK-001 QA Report

## Result

- closed_lid_inside_roi: PASS
- no_full_eye_replacement: PASS
- visual_alignment: FAIL
- decision: discard

## Guardrail

This test does not approve full eye replacement. It only checks closed-lid overlay within canonical eye ROI.

## Human Review

```text
verdict: FAIL
reason: Sheet closed-lid candidates fit inside the ROI numerically but do not follow the canonical eye shape.
```

## Revised Next Step

```text
Stop using sheet closed-lid candidates.
Use canonical edit/inpaint or manual layer split for blink.
```

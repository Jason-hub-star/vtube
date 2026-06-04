# eye-grouping-001 QA Report

## Result

- technical_grouping: PASS
- coordinate_overlay: PASS
- visual_alignment: FAIL
- art_quality: FAIL
- full_eye_composite: FAIL
- decision: revise

## Class Counts

- eye_white: 4
- iris: 2
- lash_or_lid: 8
- other_eye_part: 4

## Groups

- left: white=eye_03, iris=eye_05, lash=eye_04, error=0.588px, accepted=True
- right: white=eye_02, iris=eye_06, lash=eye_01, error=0.607px, accepted=True

## What Actually Passed

1. The script can classify rough eye component types.
2. The script can choose one eye_white, one iris, and one lash/lid per side.
3. The script can place selected components near the canonical iris anchors.

## Human Review

```text
verdict: FAIL
reason: 위치도 안 맞고 미술 품질도 한참 부족함.
```

This means `eye-grouping-001` is not a success pattern for production eye replacement. It is evidence that naive semantic grouping is insufficient.

## Caveats

- Numeric proximity to iris anchors did not guarantee visual alignment.
- Lash/lid part choice is too crude.
- The generated eye parts do not match the canonical eye shape/style closely enough.
- Production cannot rely on this grouping strategy without a stronger fitting model.

## Revised Next Step

```text
Do not attempt full eye replacement from this sheet yet.
Keep iris-only coordinate placement as useful.
For full eye work, first extract canonical eye geometry/masks or generate/edit parts directly against the canonical face.
```

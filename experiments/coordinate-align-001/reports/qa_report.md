# coordinate-align-001 QA Report

## Result

- anchor_detection: PASS
- mouth_coordinate_alignment: PASS
- eye_semantic_classification: PASS
- iris_coordinate_alignment: PASS
- decision: keep-as-success-pattern

## Anchor

- left iris: [686.75, 300.02]
- right iris: [802.77, 299.32]
- eye distance: 116.03px
- mouth target center: [744.76, 373.93]
- mouth target width: 48.73px

## Success Pattern

1. Detect stable canonical anchors numerically.
2. Measure candidate alpha bbox and alpha center.
3. Scale candidate from target width, not by visual guessing.
4. Paste by matching alpha center to target anchor.
5. Emit placement error and only use screenshots for final QA.

## Caveats

- Mouth target is inferred from iris distance because the original canonical mouth is a very small line.
- Eye classification currently identifies iris candidates; full eye replacement still needs white/lash/lid grouping.
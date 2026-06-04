# Next Test Plan for Generated Assets

Date: 2026-06-02

## Summary

Updated after calibrated `MOUTH-APPLY-DELTA-001`: 주인님 says the corrected mouth result is much better and usable enough.

Use the remaining generated raw assets to run the next validation loop in a narrower order:

```text
BLINK-REVIEW-001
→ BLINK-APPLY-REVIEW-001
→ LIVE2D-KEYPOSE-SPEC-001
→ ALPHA-CLEANUP-001
→ EYE-ROI-DETECTOR-001
→ MOUTH-PER-EXPRESSION-OFFSET-001 only if needed
```

Do not start non-human, MediaPipe, or Live2D/PSD import tests until these pass.

## 1. MOUTH-APPLY-DELTA-001

Status:

VERIFIED.

Result:

- 10 corrected full-canvas mouth layers were generated.
- corrected numeric ROI/bbox checks passed.
- Calibrated canvas delta was applied: `dx=-37.842`, `dy=6.307`.
- 주인님 human review says it is much better and usable enough.

Decision:

- Keep full-canvas/manual-delta review workflow.
- Keep all generated mouth candidates by 주인님 visual review.
- Numeric ROI remains 4/10, so keep numeric evidence separate from human keep decision.
- Do not spend more time tuning mouth before testing other parts.

## 2. MOUTH-SHORTLIST-001

Status:

VERIFIED.

Result:

- 주인님 decided to use all mouth candidates.
- `mouth_shortlist_report.json` records all 10 as kept by user review.
- Per-expression mouth offset is fallback only.

Decision:

- Keep all mouth candidates for now.
- Move to blink/eye/alpha tests.

## 3. BLINK-STAGE-001

Status:

OBSERVED.

Result:

- 3 full-canvas blink stages were generated: `half`, `mostly_closed`, `closed`.
- All combined layers are `2048x2048`.
- Eye ROI numeric check passed: `3/3`.
- Coverage decreases by stage: `half 0.520`, `mostly_closed 0.405`, `closed 0.280`.
- Previous line-only blink delta was not applied because it does not fit staged blink sheet geometry.

Decision:

- Keep this as the current staged blink candidate.
- Human visual review must decide whether file candidates look like eyelid closure rather than eyebrow/eyeliner.
- If visually usable but slightly misplaced, run `BLINK-CALIBRATION-001`.

## 4. BLINK-REVIEW-001

Inputs:

- `blink-stage-001/preview/index.html`
- `blink-stage-001/reports/blink_stage_report.json`

Procedure:

1. Select file candidate: `half`, `mostly_closed`, `closed`.
2. Adjust placement if needed.
3. Save review evidence.

Pass criteria:

- file-candidate stage identity is preserved
- placement evidence includes `canvas_dx/canvas_dy`
- review evidence is saved

Fail criteria:

- file candidate still looks like eyebrow/eyeliner
- placement evidence is missing

## 5. BLINK-APPLY-REVIEW-001

Status:

OBSERVED.

Result:

- Saved blink placement was applied to all 3 full-canvas stage candidates.
- Full-canvas corrected layers were generated.
- Numeric ROI is `0/3`, so visual judgement and numeric ROI must stay separate.
- This is not the production runtime method; it is Live2D key-pose placement evidence.

Decision:

- Keep as rigging evidence.
- Do not implement production blink as PNG frame swapping.

## 6. LIVE2D-KEYPOSE-SPEC-001

Inputs:

- mouth corrected candidates
- blink corrected candidates
- canonical master
- saved placement reports

Procedure:

1. Map blink candidates to Live2D eye-open parameter key poses:
   - open: canonical
   - half: `ParamEyeLOpen/ParamEyeROpen ~= 0.5`
   - mostly_closed: `~ 0.2`
   - closed: `0`
2. Map mouth candidates to `ParamMouthOpenY` / `ParamMouthForm`.
3. Produce PSD layer naming and Cubism Editor rigging checklist.
4. Mark generated PNGs as guide/reference/key-pose evidence, not final runtime frame assets.

Pass criteria:

- Live2D standard parameters are listed
- PSD/import layer targets are listed
- key-pose references are linked to current corrected assets
- production route is Cubism ArtMesh/Deformer/parameter, not PNG swapping

Fail criteria:

- plan suggests PNG frame swap as Live2D production
- no mapping to `ParamEyeLOpen`, `ParamEyeROpen`, `ParamMouthOpenY`, `ParamMouthForm`

Inputs:

- `asset-generation-2048-001/raw/blink_stage_sheet_source.png`
- existing canonical eye ROI/masks from `production-canvas-2048-001`

Procedure:

1. Remove green chroma-key.
2. Crop left/right eyelid patch pairs.
3. Classify candidates into:

```text
eye_half
eye_mostly_closed
eye_closed
```

4. Convert each stage to `2048x2048` full-canvas layers.
5. Overlay on canonical eye ROI.
6. Measure visible iris/eye-white coverage reduction per stage.

Pass criteria:

- each stage is visibly different
- iris/eye-white coverage decreases from half to closed
- result reads as eyelid closure, not eyebrow/eyeliner
- no full eye replacement

Fail criteria:

- patches do not cover iris/eye-white
- stages are visually indistinguishable
- human review says eyebrow/eyeliner

Decision:

- If it passes, build a blink-stage generator.
- If it fails, switch blink to canonical edit/inpaint or manual layer split.

## 5. ALPHA-CLEANUP-001

Inputs:

- `asset-generation-2048-001/raw/clean_canonical_cyan_source.png`
- existing green-key canonical source from `production-canvas-2048-001`

Procedure:

1. Remove cyan chroma-key from the new clean canonical candidate.
2. Normalize to `2048x2048`.
3. Compare with existing green-key canonical on:

```text
dark background
light background
checker background
```

4. Record edge fringe, alpha bbox, and visible hair/detail loss.

Pass criteria:

- cyan-key candidate has less visible fringe than current canonical
- no obvious cyan edge remains
- face/eye/mouth quality remains usable

Fail criteria:

- cyan fringe still visible
- identity/style drifts too much
- native size/resize artifacts are worse than the current canonical

Decision:

- If cyan-key wins, update canonical baseline candidate.
- If not, test native transparency fallback or manual alpha cleanup.

## Deprioritized For Now

- dog/cat non-human fixtures
- MediaPipe tracking
- Live2D/PSD import
- See-through local Mac path
- large expression packs
- more mouth sheets with the same detached asset-sheet approach

## Next Best Action

Run `BLINK-STAGE-001` next. Mouth is good enough to keep; further mouth offset tuning should wait until a rig preview exposes a specific expression problem.

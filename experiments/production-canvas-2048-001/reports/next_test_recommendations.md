# Next Test Recommendations

Date: 2026-06-02

Basis:

- `vtube-validation-evidence-log.md`
- `reports/qa_report.md`
- `reports/manual_adjustments_2048.json`
- `reports/manual_adjustments_summary.md`
- Existing discarded evidence for full eye replacement and sheet closed-lid blink

## Recommended Order

### 1. MOUTH-APPLY-DELTA-001

Goal:
Apply the saved mouth correction to all full-canvas mouth layers.

Why first:
The mouth group has the cleanest evidence. All five mouth candidates share the same correction:

```json
{ "dx": -12, "dy": 2, "scale": 1.0, "opacity": 1.0 }
```

Pass criteria:

- corrected full-canvas mouth layers remain `2048x2048`
- corrected overlays are created
- placement report records both original and corrected bbox/center
- 주인님 gives per-candidate human verdict

Decision:
If at least 2 mouth candidates become human `PASS`, keep mouth generation path.

### 2. BLINK-STAGE-001

Goal:
Replace the current line-only blink with staged blink states.

Minimum stages:

```text
eye_open
eye_half
eye_closed
```

Why second:
Current `blink_closed_lids` is not a production blink. It draws closed-lid lines, but iris/eye-white remain visible, so it can be confused with eyeliner/eyebrow.

Pass criteria:

- each stage is a full-canvas `2048x2048` layer
- eye ROI is used, not full eye replacement
- iris/eye-white visible area decreases from open to half to closed
- human review does not describe the layer as eyebrow/eyeliner

Decision:
If staged blink fails, switch to canonical edit/inpaint or manual layer split.

### 3. ALPHA-CLEANUP-001

Goal:
Remove the visible chroma-key edge fringe from the canonical.

Why third:
Current canonical is structurally useful but has green edge artifacts. This can poison later preview and layer quality review.

Pass criteria:

- dark background preview has no visible green fringe
- light background preview has no visible green fringe
- alpha bbox remains stable
- no meaningful hair/detail loss at edges

Decision:
If chroma cleanup fails, use native transparency or a better source generation path.

### 4. EYE-ROI-DETECTOR-001

Goal:
Remove fallback dependence from eye ROI detection.

Why fourth:
Current eye ROI works for smoke testing, but `anchor_2048_report.json` marks eye detection as fallback. Production blink needs a stable eye ROI.

Pass criteria:

- left/right eye ROI detected without fallback
- iris center or eye contour is detected in both eyes
- ROI is stable across canonical preview backgrounds

Decision:
If automatic ROI remains unstable, add manual landmark seed input to the review UI.

### 5. REVIEW-EVIDENCE-LOOP-001

Goal:
Make the review UI evidence loop robust enough for repeated use.

Pass criteria:

- `증거 저장` writes to `reports/manual_adjustments_2048.json`
- export fallback still works if the server is not running
- saved JSON includes selected candidate, per-candidate delta, verdict, and notes
- Codex can read the saved JSON and create a summary report

Decision:
Keep this as the standard human-review path before revising prompts or generated layers.

## Deprioritized

- See-through local Mac path: still BLOCKED; not part of the immediate test path.
- Non-human dog/cat mascot: wait until human 2048 mouth/blink success pattern is stronger.
- MediaPipe tracking: wait until mouth/blink visual states are accepted.
- Live2D/PSD import: wait until layer candidates and masks are cleaner.

## Next Best Action

Run `MOUTH-APPLY-DELTA-001` first. It has the clearest evidence and lowest risk.

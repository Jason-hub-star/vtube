# Mouth Apply Delta QA

Date: 2026-06-02

## Verdict

- Status: VERIFIED
- 주인님 correction: mouth asset quality was acceptable.
- Calibrated 2048 canvas delta was applied.
- 주인님 visual review: 훨씬 좋아졌고 사용 가능할 수 있는 수준.

## Evidence

- Applied delta: dx=-37.842, dy=6.307
- Candidates: 10
- Corrected numeric pass count: 4
- Delta interpretation: manual canvas_dx/canvas_dy interpreted as 2048 canvas pixels
- Calibrated canvas delta: yes
- Human asset quality: PASS_BY_USER_REVIEW
- Position after delta: PASS_BY_USER_REVIEW
- Production candidate: KEEP_USABLE_CANDIDATES

## Decision

- Keep the calibrated full-canvas mouth layer workflow.
- Use all 10 mouth candidates by 주인님 visual review.
- Do not tune mouth further before testing other parts.
- Per-expression mouth offset remains fallback only if the rig preview exposes a specific issue.

## Review

- Preview: `/Users/family/jason/Vtube/experiments/mouth-apply-delta-001/preview/index.html`
- Report: `/Users/family/jason/Vtube/experiments/mouth-apply-delta-001/reports/mouth_apply_delta_report.json`

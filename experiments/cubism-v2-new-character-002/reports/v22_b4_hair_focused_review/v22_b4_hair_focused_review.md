# Character 002 v22 B4 Hair Focused Review

- status: `B4_HAIR_FOCUSED_REVIEW_READY_PARAMHAIRFRONT_STILL_HIDDEN`
- B4 layer pack: `experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_layer_pack_report.json`
- B4 overlay QA: `experiments/cubism-v2-new-character-002/reports/v22_b4_hair_pack/v22_b4_overlay_qa_report.json`
- review sheet: `experiments/cubism-v2-new-character-002/reports/v22_b4_hair_focused_review/v22_b4_hair_focused_review.png`
- ParamHairFront: `BLOCKED_UNTIL_HUMAN_VISUAL_AND_MOTION_QA`

## Summary

- `focus_part_count`: `12`
- `front_hair_focus_count`: `7`
- `front_hair_child_candidate_count`: `7`
- `recommendation_counts`: `{'KEEP_AS_BACK_OR_UNDERPAINT_REVIEW_DRAW_ORDER_MASK': 3, 'REVIEW_ANCHOR_AND_MASK': 2, 'FRONT_HAIR_CHILD_CANDIDATE_HUMAN_REVIEW_REQUIRED': 7}`
- `param_hair_front_unlock_status`: `BLOCKED_UNTIL_HUMAN_VISUAL_AND_MOTION_QA`

## Focus Parts

### hair_back_base

- recommendation: `KEEP_AS_BACK_OR_UNDERPAINT_REVIEW_DRAW_ORDER_MASK`
- triage action: `REVIEW_DRAW_ORDER_OR_MASK`
- source hair support ratio: `0.56329`
- source skin/light overlap ratio: `0.424138`
- target anchor: `[1024.0, 720.0]`

### hair_back_center

- recommendation: `KEEP_AS_BACK_OR_UNDERPAINT_REVIEW_DRAW_ORDER_MASK`
- triage action: `REVIEW_DRAW_ORDER_OR_MASK`
- source hair support ratio: `0.233427`
- source skin/light overlap ratio: `0.74999`
- target anchor: `[1024.0, 822.0]`

### hair_back_underpaint

- recommendation: `KEEP_AS_BACK_OR_UNDERPAINT_REVIEW_DRAW_ORDER_MASK`
- triage action: `REVIEW_DRAW_ORDER_OR_MASK`
- source hair support ratio: `0.211991`
- source skin/light overlap ratio: `0.772935`
- target anchor: `[1024.0, 880.0]`

### hair_back_strand_L

- recommendation: `REVIEW_ANCHOR_AND_MASK`
- triage action: `REVIEW_ANCHOR_AND_MASK`
- source hair support ratio: `0.862361`
- source skin/light overlap ratio: `0.133777`
- target anchor: `[725.0, 820.0]`

### hair_back_strand_R

- recommendation: `REVIEW_ANCHOR_AND_MASK`
- triage action: `REVIEW_ANCHOR_AND_MASK`
- source hair support ratio: `0.947048`
- source skin/light overlap ratio: `0.050653`
- target anchor: `[1335.0, 830.0]`

### hair_front_L

- recommendation: `FRONT_HAIR_CHILD_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- triage action: `REVIEW_ANCHOR_AND_MASK`
- source hair support ratio: `0.806941`
- source skin/light overlap ratio: `0.18899`
- target anchor: `[882.0, 445.0]`

### hair_front_R

- recommendation: `FRONT_HAIR_CHILD_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- triage action: `REVIEW_ANCHOR_AND_MASK`
- source hair support ratio: `0.789021`
- source skin/light overlap ratio: `0.193552`
- target anchor: `[1160.0, 455.0]`

### hair_front_center

- recommendation: `FRONT_HAIR_CHILD_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- triage action: `REVIEW_ANCHOR_AND_MASK`
- source hair support ratio: `0.820735`
- source skin/light overlap ratio: `0.165886`
- target anchor: `[1024.0, 430.0]`

### hair_front_side_L

- recommendation: `FRONT_HAIR_CHILD_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- triage action: `REVIEW_ANCHOR_AND_MASK`
- source hair support ratio: `0.816601`
- source skin/light overlap ratio: `0.178608`
- target anchor: `[812.0, 635.0]`

### hair_front_side_R

- recommendation: `FRONT_HAIR_CHILD_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- triage action: `REVIEW_ANCHOR_AND_MASK`
- source hair support ratio: `0.994566`
- source skin/light overlap ratio: `0.005337`
- target anchor: `[1287.0, 635.0]`

### hair_front_tip_L

- recommendation: `FRONT_HAIR_CHILD_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- triage action: `REVIEW_ANCHOR_AND_MASK`
- source hair support ratio: `0.922023`
- source skin/light overlap ratio: `0.072314`
- target anchor: `[760.0, 873.0]`

### hair_front_tip_R

- recommendation: `FRONT_HAIR_CHILD_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- triage action: `REVIEW_ANCHOR_AND_MASK`
- source hair support ratio: `0.606942`
- source skin/light overlap ratio: `0.391676`
- target anchor: `[1209.0, 885.0]`

## Decision

B4 has real independent hair_front_* candidate files, but this packet is focused review evidence only. ParamHairFront remains hidden/contract-only until front hair candidates pass human visual QA and later motion-readiness checks.

## Next Action

- Ask for focused review only on the B4 hair review sheet, not all 33 B4/B5 anchors.
- If front hair child candidates are accepted, prepare a motion-readiness check while keeping ParamHairFront hidden until that check passes.
- If front hair masks are rejected, refine mask/extraction or regenerate B4 front hair mini-pass.
- Keep B5 torso/shoulder focused decision separate.

## Self Review

- `b4_layer_pack_status`: `B4_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED`
- `b4_overlay_qa_status`: `B4_CODEX_OVERLAY_QA_REVISE_ANCHOR_OR_EXTRACTION_HUMAN_REVIEW_REQUIRED`
- `triage_status`: `G6_B4_B5_AUTO_DRAFT_TRIAGE_REEXTRACTION_AND_FOCUSED_REVIEW_REQUIRED`
- `focus_part_count`: `12`
- `entries_count`: `12`
- `all_focus_parts_present`: `True`
- `review_sheet_exists`: `True`
- `has_front_hair_children_scope`: `True`
- `front_hair_child_candidate_count`: `7`
- `param_hair_front_hidden`: `True`
- `has_human_required_gate`: `True`
- `does_not_require_owner_review_all_33`: `True`
- `validator_only_promotion_blocked`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`

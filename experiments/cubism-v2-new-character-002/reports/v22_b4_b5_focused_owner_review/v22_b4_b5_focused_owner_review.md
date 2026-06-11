# Character 002 v22 B4/B5 Focused Owner Review

- status: `B4_B5_FOCUSED_OWNER_REVIEW_PACKET_READY_PENDING_OWNER_DECISIONS`
- review sheet: `experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_focused_owner_review.png`
- decision template: `experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_focused_owner_review_decision_template.json`
- material PASS: `BLOCKED`
- ParamHairFront: `HIDDEN_CONTRACT_ONLY`
- G7 Mini Cubism: `BLOCKED`
- G8 real Cubism: `BLOCKED`

## Primary Decisions

### 1. hair_front_L

- group: `B4_FRONT_HAIR`
- recommendation: `FRONT_HAIR_CHILD_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- owner decision: `PENDING_OWNER_REVIEW`
- allowed decisions: `ACCEPT_FOR_MOTION_READINESS_CANDIDATE, REVISE_MASK_OR_ANCHOR, REGENERATE_B4_FRONT_HAIR_MINIPASS`
- if accept: Prepare B4 front-hair motion-readiness check while keeping ParamHairFront hidden until that check passes.
- if revise: Use mask/anchor refinement for this front-hair child.
- if regenerate: Run a B4 front-hair mini-pass, not a full B1-B5 restart.

### 2. hair_front_R

- group: `B4_FRONT_HAIR`
- recommendation: `FRONT_HAIR_CHILD_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- owner decision: `PENDING_OWNER_REVIEW`
- allowed decisions: `ACCEPT_FOR_MOTION_READINESS_CANDIDATE, REVISE_MASK_OR_ANCHOR, REGENERATE_B4_FRONT_HAIR_MINIPASS`
- if accept: Prepare B4 front-hair motion-readiness check while keeping ParamHairFront hidden until that check passes.
- if revise: Use mask/anchor refinement for this front-hair child.
- if regenerate: Run a B4 front-hair mini-pass, not a full B1-B5 restart.

### 3. hair_front_center

- group: `B4_FRONT_HAIR`
- recommendation: `FRONT_HAIR_CHILD_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- owner decision: `PENDING_OWNER_REVIEW`
- allowed decisions: `ACCEPT_FOR_MOTION_READINESS_CANDIDATE, REVISE_MASK_OR_ANCHOR, REGENERATE_B4_FRONT_HAIR_MINIPASS`
- if accept: Prepare B4 front-hair motion-readiness check while keeping ParamHairFront hidden until that check passes.
- if revise: Use mask/anchor refinement for this front-hair child.
- if regenerate: Run a B4 front-hair mini-pass, not a full B1-B5 restart.

### 4. hair_front_side_L

- group: `B4_FRONT_HAIR`
- recommendation: `FRONT_HAIR_CHILD_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- owner decision: `PENDING_OWNER_REVIEW`
- allowed decisions: `ACCEPT_FOR_MOTION_READINESS_CANDIDATE, REVISE_MASK_OR_ANCHOR, REGENERATE_B4_FRONT_HAIR_MINIPASS`
- if accept: Prepare B4 front-hair motion-readiness check while keeping ParamHairFront hidden until that check passes.
- if revise: Use mask/anchor refinement for this front-hair child.
- if regenerate: Run a B4 front-hair mini-pass, not a full B1-B5 restart.

### 5. hair_front_side_R

- group: `B4_FRONT_HAIR`
- recommendation: `FRONT_HAIR_CHILD_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- owner decision: `PENDING_OWNER_REVIEW`
- allowed decisions: `ACCEPT_FOR_MOTION_READINESS_CANDIDATE, REVISE_MASK_OR_ANCHOR, REGENERATE_B4_FRONT_HAIR_MINIPASS`
- if accept: Prepare B4 front-hair motion-readiness check while keeping ParamHairFront hidden until that check passes.
- if revise: Use mask/anchor refinement for this front-hair child.
- if regenerate: Run a B4 front-hair mini-pass, not a full B1-B5 restart.

### 6. hair_front_tip_L

- group: `B4_FRONT_HAIR`
- recommendation: `FRONT_HAIR_CHILD_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- owner decision: `PENDING_OWNER_REVIEW`
- allowed decisions: `ACCEPT_FOR_MOTION_READINESS_CANDIDATE, REVISE_MASK_OR_ANCHOR, REGENERATE_B4_FRONT_HAIR_MINIPASS`
- if accept: Prepare B4 front-hair motion-readiness check while keeping ParamHairFront hidden until that check passes.
- if revise: Use mask/anchor refinement for this front-hair child.
- if regenerate: Run a B4 front-hair mini-pass, not a full B1-B5 restart.

### 7. hair_front_tip_R

- group: `B4_FRONT_HAIR`
- recommendation: `FRONT_HAIR_CHILD_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- owner decision: `PENDING_OWNER_REVIEW`
- allowed decisions: `ACCEPT_FOR_MOTION_READINESS_CANDIDATE, REVISE_MASK_OR_ANCHOR, REGENERATE_B4_FRONT_HAIR_MINIPASS`
- if accept: Prepare B4 front-hair motion-readiness check while keeping ParamHairFront hidden until that check passes.
- if revise: Use mask/anchor refinement for this front-hair child.
- if regenerate: Run a B4 front-hair mini-pass, not a full B1-B5 restart.

### 8. torso_base

- group: `B5_BODY_BLOCKER`
- recommendation: `REGENERATE_OR_FOCUSED_HUMAN_ACCEPT_BROAD_UNDERPAINT`
- owner decision: `PENDING_OWNER_REVIEW`
- allowed decisions: `ACCEPT_WITH_DRAW_ORDER_CONTEXT, REVISE_MASK_OR_DRAW_ORDER, REGENERATE_B5_BODY_MINIPASS`
- if accept: Keep as focused accepted candidate but do not promote material PASS until full corrected B4/B5 overlay QA passes.
- if revise: Adjust draw-order/mask for shoulders or refine torso underpaint.
- if regenerate: Run the recorded B5 body mini-pass prompt, not a full B1-B5 restart.

### 9. shoulder_L

- group: `B5_BODY_BLOCKER`
- recommendation: `REVIEW_DRAW_ORDER_BEFORE_REGENERATE`
- owner decision: `PENDING_OWNER_REVIEW`
- allowed decisions: `ACCEPT_WITH_DRAW_ORDER_CONTEXT, REVISE_MASK_OR_DRAW_ORDER, REGENERATE_B5_BODY_MINIPASS`
- if accept: Keep as focused accepted candidate but do not promote material PASS until full corrected B4/B5 overlay QA passes.
- if revise: Adjust draw-order/mask for shoulders or refine torso underpaint.
- if regenerate: Run the recorded B5 body mini-pass prompt, not a full B1-B5 restart.

### 10. shoulder_R

- group: `B5_BODY_BLOCKER`
- recommendation: `REVIEW_DRAW_ORDER_BEFORE_REGENERATE`
- owner decision: `PENDING_OWNER_REVIEW`
- allowed decisions: `ACCEPT_WITH_DRAW_ORDER_CONTEXT, REVISE_MASK_OR_DRAW_ORDER, REGENERATE_B5_BODY_MINIPASS`
- if accept: Keep as focused accepted candidate but do not promote material PASS until full corrected B4/B5 overlay QA passes.
- if revise: Adjust draw-order/mask for shoulders or refine torso underpaint.
- if regenerate: Run the recorded B5 body mini-pass prompt, not a full B1-B5 restart.

## Secondary Followups

- `hair_back_base` `KEEP_AS_BACK_OR_UNDERPAINT_REVIEW_DRAW_ORDER_MASK`: Keep for follow-up draw-order, underpaint, anchor, or mask review after primary B4/B5 decisions.
- `hair_back_center` `KEEP_AS_BACK_OR_UNDERPAINT_REVIEW_DRAW_ORDER_MASK`: Keep for follow-up draw-order, underpaint, anchor, or mask review after primary B4/B5 decisions.
- `hair_back_underpaint` `KEEP_AS_BACK_OR_UNDERPAINT_REVIEW_DRAW_ORDER_MASK`: Keep for follow-up draw-order, underpaint, anchor, or mask review after primary B4/B5 decisions.
- `hair_back_strand_L` `REVIEW_ANCHOR_AND_MASK`: Keep for follow-up draw-order, underpaint, anchor, or mask review after primary B4/B5 decisions.
- `hair_back_strand_R` `REVIEW_ANCHOR_AND_MASK`: Keep for follow-up draw-order, underpaint, anchor, or mask review after primary B4/B5 decisions.

## Decision

This is the focused owner-review handoff for B4/B5. It deliberately keeps all primary decisions pending and blocks material PASS, Mini Cubism, and real Cubism promotion.

## Next Action

- Collect owner decisions for the ten primary rows.
- Apply accepted/revised/regenerated paths separately; do not restart B1-B5 unless the owner rejects the whole visual direction.
- After accepted corrections exist, rebuild the corrected B4/B5 candidate and rerun overlay QA.

## Self Review

- `b4_status`: `B4_HAIR_FOCUSED_REVIEW_READY_PARAMHAIRFRONT_STILL_HIDDEN`
- `b5_status`: `B5_BODY_BLOCKER_DRAW_ORDER_REVIEW_READY_HUMAN_DECISION_REQUIRED`
- `primary_decision_count`: `10`
- `b4_front_hair_primary_count`: `7`
- `b5_body_primary_count`: `3`
- `secondary_followup_count`: `5`
- `review_sheet_exists`: `True`
- `decision_template_exists`: `True`
- `all_primary_pending_owner_review`: `True`
- `does_not_require_owner_review_all_33`: `True`
- `validator_only_promotion_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`

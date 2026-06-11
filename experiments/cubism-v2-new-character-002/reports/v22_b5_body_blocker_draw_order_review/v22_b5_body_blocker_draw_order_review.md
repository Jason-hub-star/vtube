# Character 002 v22 B5 Body Blocker Draw-Order Review

- status: `B5_BODY_BLOCKER_DRAW_ORDER_REVIEW_READY_HUMAN_DECISION_REQUIRED`
- source image: `experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png`
- v2 report: `experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_report.json`
- v2 QA: `experiments/cubism-v2-new-character-002/reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_overlay_qa_report.json`
- review sheet: `experiments/cubism-v2-new-character-002/reports/v22_b5_body_blocker_draw_order_review/v22_b5_body_blocker_draw_order_review.png`

## Target Decisions

### torso_base

- recommendation: `REGENERATE_OR_FOCUSED_HUMAN_ACCEPT_BROAD_UNDERPAINT`
- alpha coverage: `0.14019799`
- hair occlusion overlap ratio: `0.141695`
- interpretation: Torso remains a broad underpaint/body material decision and should not be solved by more alpha shrinking.

### shoulder_L

- recommendation: `REVIEW_DRAW_ORDER_BEFORE_REGENERATE`
- alpha coverage: `0.01091456`
- hair occlusion overlap ratio: `0.870193`
- interpretation: Shoulder overlap is likely partly draw-order/occlusion related; review before regenerating.

### shoulder_R

- recommendation: `REVIEW_DRAW_ORDER_BEFORE_REGENERATE`
- alpha coverage: `0.00972676`
- hair occlusion overlap ratio: `0.868247`
- interpretation: Shoulder overlap is likely partly draw-order/occlusion related; review before regenerating.

## Regeneration Prompt If Rejected

```text
Create a focused Live2D/Cubism B5 body mini-pass for the same accepted G0 source character.
Generate only clean rig-friendly body material references for torso_base, shoulder_L, and shoulder_R.
Keep the same adult cute woman identity, pale soft skin, warm brown hair context, white ribbed off-shoulder sweater, shoulder straps, line thickness, and soft anime shading.
The shoulders must be clean skin/strap/cloth underpaint suitable to sit behind front/side hair without hair pixels baked into the shoulder layer.
The torso_base must be a complete upper-body base for breath/body-angle support, with coherent skin-to-clothing continuity and no pasted crop artifacts.
No labels, arrows, grids, extra faces, hands, jewelry, props, hairstyle changes, new outfit, perspective pose, cropped shoulders, or source-crop artifacts.
```

## Decision

The three B5 hard blockers remain blocked from material PASS, but this packet separates draw-order-aware shoulder review from true regeneration/re-extraction. Do not ask the owner to manually anchor all B5 parts.

## Next Action

- Ask for focused accept/reject only on torso_base, shoulder_L, and shoulder_R using this review sheet.
- If shoulders are rejected after draw-order review, run the regeneration prompt for a B5 body mini-pass.
- If torso_base is rejected, regenerate or re-extract a complete torso/body underpaint instead of shrinking alpha again.
- Keep B4 hair focused review separate and keep G7/G8 blocked.

## Self Review

- `v2_status`: `B5_REFINED_MASK_V2_CANDIDATE_READY_FOR_OVERLAY_REVIEW`
- `v2_qa_status`: `B5_REFINED_MASK_V2_OVERLAY_QA_REVISE_REGENERATE_OR_HUMAN_REVIEW_REQUIRED`
- `previous_remaining_b5_revise_parts`: `['torso_base', 'shoulder_L', 'shoulder_R']`
- `target_count`: `3`
- `entries_count`: `3`
- `all_targets_present`: `True`
- `review_sheet_exists`: `True`
- `has_regeneration_prompt`: `True`
- `has_human_decision_gate`: `True`
- `does_not_require_owner_review_all_33`: `True`
- `validator_only_promotion_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`

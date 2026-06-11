# Character 002 v22 B5 Provisional Mini-Pass Input Packet

- status: `B5_PROVISIONAL_MINIPASS_INPUT_PACKET_READY`
- source image: `experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png`
- route plan: `experiments/cubism-v2-new-character-002/reports/v22_b4_b5_focused_owner_review/v22_b4_b5_owner_decision_route_plan.json`

## Targets

- `torso_base` `REGENERATE_BODY_MINIPASS` `ROUTE_TO_B5_BODY_MINIPASS_REGENERATION`: Regenerate this as a coherent B5 torso/body underpaint reference; do not solve it by alpha shrinking.
- `shoulder_L` `REVISE_DRAW_ORDER_OR_MASK` `ROUTE_TO_B5_DRAW_ORDER_OR_MASK_REFINEMENT`: Revise draw-order context or mask separation so shoulder material can sit behind front/side hair without baked hair pixels.
- `shoulder_R` `REVISE_DRAW_ORDER_OR_MASK` `ROUTE_TO_B5_DRAW_ORDER_OR_MASK_REFINEMENT`: Revise draw-order context or mask separation so shoulder material can sit behind front/side hair without baked hair pixels.

## Image Generation Prompt

```text
Create a focused Live2D/Cubism B5 body mini-pass for the same accepted G0 source character.
Generate only clean rig-friendly body material references for torso_base, shoulder_L, and shoulder_R.
Keep the same adult cute woman identity, pale soft skin, warm brown hair context, white ribbed off-shoulder sweater, shoulder straps, line thickness, and soft anime shading.
The shoulders must be clean skin/strap/cloth underpaint suitable to sit behind front/side hair without hair pixels baked into the shoulder layer.
The torso_base must be a complete upper-body base for breath/body-angle support, with coherent skin-to-clothing continuity and no pasted crop artifacts.
No labels, arrows, grids, extra faces, hands, jewelry, props, hairstyle changes, new outfit, perspective pose, cropped shoulders, or source-crop artifacts.
```

## Output Requirements

- Return clean full-canvas 2048x2048 RGBA candidates for torso_base, shoulder_L, and shoulder_R.
- Keep same character identity, off-shoulder white sweater, shoulder straps, line thickness, and soft anime shading.
- Shoulders must be usable behind front/side hair without hair baked into the shoulder art.
- torso_base must be coherent enough for later breath/body-angle support.
- Do not unlock material PASS until overlay QA and visual QA pass after normalization.

## Self Review

- `route_plan_status`: `B4_B5_OWNER_DECISION_ROUTE_PLAN_READY_FOR_REVISION_WORK`
- `codex_decision_status`: `CODEX_PROVISIONAL_DECISIONS_READY_NO_OWNER_APPROVAL`
- `b5_overlay_qa_status`: `B5_REFINED_MASK_V2_OVERLAY_QA_REVISE_REGENERATE_OR_HUMAN_REVIEW_REQUIRED`
- `target_count`: `3`
- `target_parts`: `['torso_base', 'shoulder_L', 'shoulder_R']`
- `regenerate_target_count`: `1`
- `revise_target_count`: `2`
- `all_targets_have_crop_box`: `True`
- `prompt_present`: `True`
- `not_owner_approval`: `True`
- `material_pass_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`

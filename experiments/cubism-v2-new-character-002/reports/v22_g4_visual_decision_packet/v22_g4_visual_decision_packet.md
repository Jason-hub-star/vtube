# Character 002 v22 G4 Visual Decision Packet

- status: `G4_VISUAL_DECISION_PACKET_READY_PENDING_REVIEW_MATERIAL_BLOCKED`
- source surface: `experiments/cubism-v2-new-character-002/reports/v22_g4_compact_visual_review_surface/v22_g4_compact_visual_review_surface_report.json`
- decision template: `experiments/cubism-v2-new-character-002/reports/v22_g4_visual_decision_packet/v22_g4_visual_decision_template.json`
- smoke decisions: `experiments/cubism-v2-new-character-002/reports/v22_g4_visual_decision_packet/v22_g4_visual_decision_smoke.json`
- material PASS: `BLOCKED`
- G5 material acceptance: `BLOCKED_CONTEXT_REVIEW_NOT_OWNER_APPROVAL`
- ParamHairFront: `HIDDEN_CONTRACT_ONLY`
- G7 Mini Cubism: `BLOCKED`
- G8 real Cubism: `BLOCKED`

## Decision Items

### B1_CLEAN_BASE_UNDERPAINT

- title: `B1 Clean Base / Underpaint`
- source status: `B1_CODEX_VISUAL_QA_PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- review gate: `PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- visual decision: `PENDING_VISUAL_REVIEW`
- allowed decisions: `PENDING_VISUAL_REVIEW, ACCEPT_VISUAL_CANDIDATE_KEEP_MATERIAL_BLOCKED, REVISE_BEFORE_G5, REGENERATE_BATCH_OR_CONTEXT`
- if accept: Keep this batch as a visual candidate; G5 remains blocked until the full five-item G4 packet is accepted separately.
- if revise: Apply focused mask/anchor/source cleanup for this batch before G5.
- if regenerate: Regenerate this batch only; do not restart unrelated B batches.

### B2_EYE_PACK

- title: `B2 Eye Pack`
- source status: `B2_CODEX_OVERLAY_QA_PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- review gate: `PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- visual decision: `PENDING_VISUAL_REVIEW`
- allowed decisions: `PENDING_VISUAL_REVIEW, ACCEPT_VISUAL_CANDIDATE_KEEP_MATERIAL_BLOCKED, REVISE_BEFORE_G5, REGENERATE_BATCH_OR_CONTEXT`
- if accept: Keep this batch as a visual candidate; G5 remains blocked until the full five-item G4 packet is accepted separately.
- if revise: Apply focused mask/anchor/source cleanup for this batch before G5.
- if regenerate: Regenerate this batch only; do not restart unrelated B batches.

### B3_MOUTH_PACK_REVISION_V1

- title: `B3 Mouth Pack Revision v1`
- source status: `B3_REVISION_V1_CODEX_OVERLAY_QA_PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- review gate: `PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED`
- visual decision: `PENDING_VISUAL_REVIEW`
- allowed decisions: `PENDING_VISUAL_REVIEW, ACCEPT_VISUAL_CANDIDATE_KEEP_MATERIAL_BLOCKED, REVISE_BEFORE_G5, REGENERATE_BATCH_OR_CONTEXT`
- if accept: Keep this batch as a visual candidate; G5 remains blocked until the full five-item G4 packet is accepted separately.
- if revise: Apply focused mask/anchor/source cleanup for this batch before G5.
- if regenerate: Regenerate this batch only; do not restart unrelated B batches.

### B4_B5_COMBINED_CONTEXT

- title: `B4/B5 Combined Context Overlay`
- source status: `G3_COMBINED_CONTEXT_OVERLAY_REVIEW_READY_MATERIAL_BLOCKED`
- review gate: `CONTEXT_REVIEW_REQUIRED_NOT_PASS`
- visual decision: `PENDING_VISUAL_REVIEW`
- allowed decisions: `PENDING_VISUAL_REVIEW, ACCEPT_VISUAL_CANDIDATE_KEEP_MATERIAL_BLOCKED, REVISE_BEFORE_G5, REGENERATE_BATCH_OR_CONTEXT`
- if accept: Keep B4/B5 as visual candidates only; G5 remains blocked until a separate material acceptance packet exists.
- if revise: Return to focused B4/B5 context rows and adjust only the failing masks, anchors, draw order, or mini-pass target.
- if regenerate: Regenerate the failing B4 or B5 batch/context only; do not restart B1-B3.

### G1_G2_64PART_CONTACT

- title: `64-Part Contact Sheet`
- source status: `G3_P0_TORSO_V2_64PART_MANIFEST_TECHNICAL_PASS_REVIEW_REQUIRED`
- review gate: `TECHNICAL_PASS_VISUAL_REVIEW_REQUIRED`
- visual decision: `PENDING_VISUAL_REVIEW`
- allowed decisions: `PENDING_VISUAL_REVIEW, ACCEPT_VISUAL_CANDIDATE_KEEP_MATERIAL_BLOCKED, REVISE_BEFORE_G5, REGENERATE_BATCH_OR_CONTEXT`
- if accept: Treat the contact sheet as visually ordered enough for G4 review only; this is not material PASS.
- if revise: Revise manifest display/order or obvious wrong-layer presentation before G5.
- if regenerate: Rebuild the affected manifest source rows, preserving existing PASS candidates.

## Summary

- `decision_item_count`: `5`
- `pending_visual_review_count`: `5`
- `accepted_visual_candidate_count`: `0`
- `revise_before_g5_count`: `0`
- `regenerate_batch_or_context_count`: `0`
- `b4_b5_primary_remaining_count`: `0`
- `b4_b5_context_review_count`: `33`
- `promotion_blocker_count`: `2`
- `g4_visual_review_status`: `PENDING_VISUAL_REVIEW_NOT_PASS`
- `g5_material_acceptance_status`: `BLOCKED_CONTEXT_REVIEW_NOT_OWNER_APPROVAL`
- `material_pass_status`: `BLOCKED`
- `param_hair_front_status`: `HIDDEN_CONTRACT_ONLY`
- `g7_mini_cubism_status`: `BLOCKED`
- `g8_real_cubism_status`: `BLOCKED`

## Self Review

- `surface_status`: `G4_COMPACT_VISUAL_REVIEW_SURFACE_READY_NOT_PASS`
- `readiness_status`: `G4_G5_MATERIAL_PROMOTION_READINESS_BLOCKED_CONTEXT_REVIEW`
- `decision_item_count`: `5`
- `expected_review_items_present`: `True`
- `allowed_visual_decision_values_checked`: `True`
- `smoke_decision_values_checked`: `True`
- `all_decisions_pending`: `True`
- `all_source_images_exist`: `True`
- `all_source_reports_exist`: `True`
- `decision_template_exists`: `True`
- `smoke_decisions_exists`: `True`
- `template_decision_count`: `5`
- `smoke_decision_count`: `5`
- `requires_visual_acceptance`: `True`
- `requires_separate_g5_acceptance`: `True`
- `material_pass_blocked`: `True`
- `validator_only_promotion_blocked`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `not_owner_approval`: `True`
- `status`: `PASS`

## Decision

The G4 visual decision packet is ready with five pending review rows. It records the allowed decisions and follow-up routes, but does not grant material PASS.

## Next Action

- Use the decision template or a later UI to record G4 visual decisions.
- If rows are accepted, create a separate G5 material acceptance packet rather than promoting from this G4 packet.
- If any row is revise or regenerate, apply only that focused follow-up path.
- Keep ParamHairFront hidden, and keep G7/G8 blocked.

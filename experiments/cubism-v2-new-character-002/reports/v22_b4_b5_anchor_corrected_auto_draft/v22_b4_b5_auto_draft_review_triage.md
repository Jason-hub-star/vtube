# Character 002 v22 B4/B5 Auto-Draft Review Triage

- status: `G6_B4_B5_AUTO_DRAFT_TRIAGE_REEXTRACTION_AND_FOCUSED_REVIEW_REQUIRED`
- overlay sheet: `experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_auto_draft_overlay_qa.png`

## Summary

- `entry_count`: `33`
- `recommended_action_counts`: `{'REFINE_EXTRACTION_MASK': 13, 'REVIEW_ANCHOR_AND_MASK': 15, 'REVIEW_DRAW_ORDER_OR_MASK': 3, 'REVIEW_OR_REFINE_SMALL_MASK': 2}`
- `review_focus_count`: `12`
- `review_focus_parts`: `['hair_back_base', 'hair_back_center', 'hair_back_underpaint', 'hair_back_strand_L', 'hair_back_strand_R', 'hair_front_L', 'hair_front_R', 'hair_front_center', 'hair_front_side_L', 'hair_front_side_R', 'hair_front_tip_L', 'hair_front_tip_R']`

## Decision

Do not ask 주인님 to manually anchor all 33 parts. Many B5 face/body/clothing issues are extraction-mask problems. Use automatic/refined extraction first, then ask 주인님 to review the focused hair/draw-order/anchor set.

## Next Action

- Refine extraction masks for B5 body/clothing/face-detail problem parts before another anchor-only pass.
- Use the editor only for focused hair and remaining anchor/draw-order issues.
- Keep ParamHairFront hidden and keep G7/G8 blocked.

## Entries

- `REFINE_EXTRACTION_MASK` `arm_L_upper_simple` `B5`: Sleeve/arm crop has strong internal noise and should be remasked or regenerated.
- `REFINE_EXTRACTION_MASK` `arm_R_upper_simple` `B5`: Sleeve/arm crop has strong internal noise and should be remasked or regenerated.
- `REFINE_EXTRACTION_MASK` `cheek_L` `B5`: Cheek patch remains too large/oval and needs mask refinement rather than more anchor movement.
- `REFINE_EXTRACTION_MASK` `cheek_R` `B5`: Cheek patch remains too large/oval and needs mask refinement rather than more anchor movement.
- `REFINE_EXTRACTION_MASK` `chest_cloth_base` `B5`: Chest cloth base includes noisy stripe/garment artifacts and needs mask refinement.
- `REFINE_EXTRACTION_MASK` `chest_cloth_shadow` `B5`: Chest cloth shadow shape is too blocky and needs mask refinement.
- `REFINE_EXTRACTION_MASK` `collar_shadow` `B5`: Shadow line is too thin/noisy and likely needs extraction refinement.
- `REFINE_EXTRACTION_MASK` `face_shadow_L` `B5`: Face shadow is patch-like and too broad; this is a semantic mask issue.
- `REFINE_EXTRACTION_MASK` `face_shadow_R` `B5`: Face shadow is patch-like and too broad; this is a semantic mask issue.
- `REFINE_EXTRACTION_MASK` `nose` `B5`: Nose candidate is too blob-like after scaling and needs smaller semantic extraction.
- `REFINE_EXTRACTION_MASK` `shoulder_L` `B5`: Patch-like shoulder crop overlays hair/skin area and needs refined extraction.
- `REFINE_EXTRACTION_MASK` `shoulder_R` `B5`: Patch-like shoulder crop overlays hair/skin area and needs refined extraction.
- `REFINE_EXTRACTION_MASK` `torso_base` `B5`: Large body/clothing overlay includes noisy garment/skin regions; anchor alone will not make this material-ready.
- `REVIEW_DRAW_ORDER_OR_MASK` `hair_back_base` `B4`: Back hair base covers the face area in overlay; draw order/visibility and mask scope need review.
- `REVIEW_DRAW_ORDER_OR_MASK` `hair_back_center` `B4`: Back center overlaps face/neck and needs draw-order/material review.
- `REVIEW_DRAW_ORDER_OR_MASK` `hair_back_underpaint` `B4`: Back underpaint overlaps face/neck strongly; keep as underpaint candidate only.
- `REVIEW_ANCHOR_AND_MASK` `hair_back_strand_L` `B4`: Left back strand roughly follows side hair but needs focused review.
- `REVIEW_ANCHOR_AND_MASK` `hair_back_strand_R` `B4`: Right back strand roughly follows side hair but needs focused review.
- `REVIEW_ANCHOR_AND_MASK` `hair_front_L` `B4`: Left front hair follows bang area but still needs focused manual review.
- `REVIEW_ANCHOR_AND_MASK` `hair_front_R` `B4`: Right front hair follows bang area but still needs focused manual review.
- `REVIEW_ANCHOR_AND_MASK` `hair_front_center` `B4`: Front hair is the highest HairFront priority; anchor is plausible but mask still needs review.
- `REVIEW_ANCHOR_AND_MASK` `hair_front_side_L` `B4`: Left side-front hair is plausible but may cover the eye/face too much.
- `REVIEW_ANCHOR_AND_MASK` `hair_front_side_R` `B4`: Right side-front hair is plausible but may cover the eye/face too much.
- `REVIEW_ANCHOR_AND_MASK` `hair_front_tip_L` `B4`: Left front tip is plausible but should be reviewed as a separate motion child.
- `REVIEW_ANCHOR_AND_MASK` `hair_front_tip_R` `B4`: Right front tip is plausible but should be reviewed as a separate motion child.
- `REVIEW_ANCHOR_AND_MASK` `hair_side_L_inner` `B4`: Left side inner hair follows silhouette but needs focused review.
- `REVIEW_ANCHOR_AND_MASK` `hair_side_L_outer` `B4`: Left side outer hair follows silhouette but needs focused review.
- `REVIEW_ANCHOR_AND_MASK` `hair_side_R_inner` `B4`: Right side inner hair follows silhouette but needs focused review.
- `REVIEW_ANCHOR_AND_MASK` `hair_side_R_outer` `B4`: Right side outer hair follows silhouette but needs focused review.
- `REVIEW_ANCHOR_AND_MASK` `collar_front` `B5`: Collar location is plausible; use focused review before remasking.
- `REVIEW_ANCHOR_AND_MASK` `neck` `B5`: Neck placement is plausible, but the face/neck boundary still needs visual review.
- `REVIEW_OR_REFINE_SMALL_MASK` `brow_L` `B5`: Small brow overlay is close enough for focused review, but mask may still include hair/skin.
- `REVIEW_OR_REFINE_SMALL_MASK` `brow_R` `B5`: Small brow overlay is close enough for focused review, but mask may still include hair/skin.

## Self Review

- `entry_count`: `33`
- `has_reextraction_bucket`: `True`
- `has_focused_review_bucket`: `True`
- `does_not_require_owner_review_all_33`: `True`
- `param_hair_front_hidden`: `True`
- `mini_cubism_not_promoted`: `True`
- `real_cubism_not_promoted`: `True`
- `status`: `PASS`

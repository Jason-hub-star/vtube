# Cubism v2 Character 002 Overlay QA

- status: `OVERLAY_QA_REVISE_MINI_CUBISM_BLOCKED`
- judgement: `OVERLAY_QA_REVISE_MINI_CUBISM_BLOCKED`

## Sheets

- eye: `experiments/cubism-v2-new-character-002/reports/layer_alpha_seed_v5/overlay_qa/eye_overlay_qa_sheet.png`
- face: `experiments/cubism-v2-new-character-002/reports/layer_alpha_seed_v5/overlay_qa/face_overlay_qa_sheet.png`
- mouth: `experiments/cubism-v2-new-character-002/reports/layer_alpha_seed_v5/overlay_qa/mouth_overlay_qa_sheet.png`

## Findings

| Area | Status | Note |
|---|---|---|
| `eye_open` | `KEEP_FOR_REVIEW` | Open-eye candidates align near the real eyes after anchor correction, but scale/style still need human preference review. |
| `eye_clean_socket_and_underpaint` | `REVISE_OR_REGENERATE` | Skin patch boundaries are visible when composited over the source face. |
| `eye_half_mostly_closed` | `REVISE` | Blink states land in the correct area, but inherit the socket patch boundary problem. |
| `mouth_anchor` | `KEEP_FOR_REVIEW` | Mouth states are centered much better after anchor correction. |
| `mouth_base_clean` | `REVISE` | Mouth base removes the baked smile but has a visible oval patch boundary. |
| `mouth_expression_shapes` | `KEEP_FOR_REVIEW` | Closed, small-open, wide-open, O-vowel, inner, teeth, and tongue candidates are useful, but should be used only after mouth_base cleanup. |

## Decision

- Do not proceed to Mini Cubism diagnostic preview yet.
- Regenerate or edit clean sockets, closed underpaint, and `mouth_base_clean` with source-face inpaint/native clean-base context.
- Rerun this overlay QA after cleanup.

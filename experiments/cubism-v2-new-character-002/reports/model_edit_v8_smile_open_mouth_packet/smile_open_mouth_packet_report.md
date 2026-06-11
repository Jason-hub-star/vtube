# Character 002 Smile-Open Mouth Packet v1

- Status: `PASS_READY_FOR_HUMAN_VISUAL_QA`
- Contact sheet: `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/model_edit_v8_smile_open_mouth_packet/smile_open_mouth_contact_sheet.png`
- Generated at: `2026-06-09T04:17:56.761192+00:00`

## Decision

- This packet isolates smile-form mouth opening candidates from rejected `mouth_wide_open` and `mouth_o_vowel` assets.
- The generated PNGs are 2048 RGBA full-canvas candidates for visual review, not production-approved Live2D/Cubism mouth art.
- Use this packet to decide whether the synthetic smile-open direction is acceptable or whether model-native/manual repaint is needed.

## Candidates

| Candidate | Open Value | BBox | QA | Path |
|---|---:|---|---|---|
| `mouth_smile_closed` | 0.00 | `[952, 851, 1121, 945]` | `reference` | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/model_edit_v8_smile_open_mouth_packet/normalized_layers/mouth_smile_closed.png` |
| `mouth_smile_small_open` | 0.35 | `[973, 878, 1086, 906]` | `candidate` | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/model_edit_v8_smile_open_mouth_packet/normalized_layers/mouth_smile_small_open.png` |
| `mouth_smile_mid_open` | 0.65 | `[973, 878, 1096, 911]` | `candidate` | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/model_edit_v8_smile_open_mouth_packet/normalized_layers/mouth_smile_mid_open.png` |
| `mouth_smile_wide_open_candidate` | 1.00 | `[964, 878, 1109, 916]` | `candidate_needs_human_review` | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/model_edit_v8_smile_open_mouth_packet/normalized_layers/mouth_smile_wide_open_candidate.png` |

## Validation

- PASS: all candidates are 2048 RGBA, non-empty, and in the expected mouth review zone.

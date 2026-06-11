# Character 002 Existing Generated Mouth Packet

- Status: `PASS_EXISTING_MOUTH_PACKET_READY_FOR_VISUAL_QA`
- Contact sheet: `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/reports/model_edit_v8_existing_mouth_packet/existing_generated_mouth_contact_sheet.png`
- Generated at: `2026-06-09T04:24:38.622909+00:00`

## Decision

- Proceed using existing generated mouth PNGs only.
- Active v7 mouth states remain `mouth_closed_smile` and `mouth_small_open`.
- `mouth_inner`, `mouth_teeth`, and `mouth_tongue` are preserved as references, but not active in the current v7 crossfade.
- `mouth_o_vowel` and `mouth_wide_open` are preserved as evidence but excluded from active preview.

## Mouth PNGs

| ID | Policy | BBox | Source |
|---|---|---|---|
| `mouth_closed_smile` | `ACTIVE` | `[952, 851, 1121, 945]` | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/model_edit_v7_smooth_mouth_preview/mini_cubism_diagnostic_project/parts/mouth_closed_smile.png` |
| `mouth_small_open` | `ACTIVE` | `[934, 845, 1118, 946]` | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/model_edit_v7_smooth_mouth_preview/mini_cubism_diagnostic_project/parts/mouth_small_open.png` |
| `mouth_inner` | `REFERENCE_ONLY` | `[937, 849, 1122, 942]` | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/model_edit_v7_smooth_mouth_preview/mini_cubism_diagnostic_project/parts/mouth_inner.png` |
| `mouth_teeth` | `REFERENCE_ONLY` | `[930, 867, 1128, 923]` | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/model_edit_v7_smooth_mouth_preview/mini_cubism_diagnostic_project/parts/mouth_teeth.png` |
| `mouth_tongue` | `REFERENCE_ONLY` | `[940, 846, 1116, 944]` | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/model_edit_v7_smooth_mouth_preview/mini_cubism_diagnostic_project/parts/mouth_tongue.png` |
| `mouth_o_vowel` | `REJECTED_ACTIVE_EXCLUDED` | `[937, 845, 1111, 951]` | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/model_edit_v7_smooth_mouth_preview/mini_cubism_diagnostic_project/parts/mouth_o_vowel.png` |
| `mouth_wide_open` | `REJECTED_ACTIVE_EXCLUDED` | `[943, 841, 1128, 945]` | `/Users/family/jason/Vtube/experiments/cubism-v2-new-character-002/model_edit_v6_no_wide_open/normalized_layers/mouth_wide_open.png` |

## Validation

- PASS: existing mouth PNGs are full-canvas 2048 RGBA and non-empty.

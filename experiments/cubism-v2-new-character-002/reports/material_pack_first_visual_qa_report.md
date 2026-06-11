# Cubism v2 Character 002 Material-Pack-First Visual QA

- status: `REVISE_VISUAL_QA`
- technical gate: `PASS_READY_FOR_VISUAL_QA`
- visual gate: `REVISE`
- contact sheet: `experiments/cubism-v2-new-character-002/reports/material_pack_first_contact_sheet.png`

## Decision

Do not proceed to Mini Cubism diagnostic preview yet.

The 21 normalized PNGs include open eyes plus the 19 validator-required clean/keypose assets. The required 19 pass the technical keypose validator, but the visual gate is not clean enough for production promotion. This is useful evidence, not final material approval.

## Source Front

- path: `experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png`
- status: `KEEP_FOR_G0_REVIEW`

The source is front-facing and has visible eyes, mouth, hair, neck, shoulders, and torso. Hair and face regions are readable for Cubism planning. The outfit/body emphasis should still be reviewed by 주인님 before production promotion.

## Findings

| Area | Status | Reason |
|---|---|---|
| `face_base_clean` | `REVISE` | Clean face removes baked eyes and mouth, but still needs human style/identity review. |
| eye open states | `KEEP_FOR_REVIEW` | Open eye candidates exist for both sides; anchor/scale overlay QA is still required. |
| eye clean sockets / underpaint | `REVISE` | Technical candidates look like isolated skin patches and may create visible stains when composited. |
| eye half-closed states | `KEEP_FOR_REVIEW` | Iris/eye white is expected for half-closed states, but alignment and symmetry need overlay QA. |
| eye mostly/closed states | `KEEP_FOR_REVIEW` | No obvious iris/pupil/eye-white leakage in the contact sheet. |
| mouth keyposes | `REVISE` | Coherent technical candidates, but mouth_base_clean/detail crops need compositing QA. |
| mouth inner/teeth/tongue | `KEEP_FOR_REVIEW` | Separate detail candidates exist; anchor and scale overlay QA is still required. |

## Next Actions

1. Build an overlay QA sheet on top of `source_front` to check eye/mouth anchors and patch visibility.
2. Regenerate or edit clean sockets, closed underpaint, and `mouth_base_clean` if overlay QA shows visible stains.
3. Ask 주인님 to review the source style and outfit before expanding to 64-part production layers.

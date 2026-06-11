# Cubism v2 Material-Pack-First Generation

Updated: 2026-06-09

## Decision

The next character experiment is `cubism-v2-new-character-002`, and it must start as a Live2D/Cubism material-pack-first generation test.

Do not repeat the failed pattern:

```text
pretty single front image
-> later try to erase baked eyes and mouth
-> procedural patches / stains / original-eye remnants
```

Use this pattern instead:

```text
single matched front character source
-> same-character clean bases and keyposes immediately
-> normalize to shared canvas
-> validate PNG requirements
-> visual QA
-> only then Mini Cubism diagnostic rigging
```

## Why

`candidate_002` proved that a visually appealing single image is not enough for natural Live2D eye and mouth motion. The source face has open eyes and mouth pixels baked into `face_base`; later rig tuning cannot reliably hide those pixels.

The fix is to request the clean bases and keyposes at generation time, while the image model still has the character identity, face proportions, line style, and shading in context.

## Experiment

```text
experiment_id: cubism-v2-new-character-002
mode: material_pack_first
target: v2_standard
default_canvas: 2048x2048 RGBA after normalization
production_target: Live2D/Cubism PSD material, ArtMesh, Deformer, Keyform
not_target: PNG frame-swap runtime
```

## Required First Batch

Generate these as one coordinated character set, not as unrelated standalone prompts.

```text
new_character_002_source_front
face_base_clean
eye_L_open
eye_R_open
eye_L_clean_socket
eye_R_clean_socket
eye_L_half_closed
eye_R_half_closed
eye_L_mostly_closed
eye_R_mostly_closed
eye_L_closed
eye_R_closed
eye_L_closed_underpaint
eye_R_closed_underpaint
mouth_base_clean
mouth_closed
mouth_small_open
mouth_wide_open
mouth_o_vowel
mouth_inner
mouth_teeth
mouth_tongue
```

`eye_L/R_open` may be generated as an open-eye composite reference first, but it must be splittable into Cubism eye materials later: white, iris, pupil, highlight, lash/lid, and optionally lower lash. If the generated open eye cannot be split cleanly, the batch is not ready for rigging.

## Prompt Rules

Use the same identity across all assets:

```text
same adult cute female character
same face proportions
same camera and head angle
same hair shape and bang occlusion
same line thickness and anime shading style
same eye size and mouth location
no labels
no guide marks
no sprite sheet text
no new accessories between assets
```

For the source front image:

```text
front-facing or near-front upper-body Live2D-ready character
clear eyes and mouth
visible neck, shoulders, torso
simple clothing layers
hair groups readable as front/side/back
arms and props must not cover eyes, mouth, or hair silhouette
```

For clean bases:

```text
face_base_clean has no open eye, iris, pupil, eye white, lash artifacts, mouth line, teeth, or tongue pixels.
mouth_base_clean has no baked mouth line or open-mouth remnants.
eye clean sockets and closed underpaint preserve skin gradient, blush, eyelid fold, and hair occlusion.
```

For keyposes:

```text
eye open, half, mostly, closed must keep the same eye size and eyelid/lash style.
closed eyes must not contain visible iris, pupil, or eye white.
mouth closed, small open, wide open, and O vowel must keep the same mouth anchor and line style.
```

## Normalization Rules

Keep raw generated outputs, then create normalized candidates.

```text
raw_outputs/
normalized_layers/
reports/
```

Validation target for the first pass:

```text
2048x2048
RGBA
full-canvas aligned
non-empty alpha
no direct stretch-resize
crop outputs must be placed into full canvas with ROI/anchor metadata
```

## Gates

### Gate A: Technical PNG Gate

Run the keypose validator against `normalized_layers`.

```bash
python3 scripts/validate_cubism_v2_keypose_pngs.py \
  --input-dir experiments/cubism-v2-new-character-002/material_pack_first_v0/normalized_layers \
  --out experiments/cubism-v2-new-character-002/reports/material_pack_first_keypose_validation_report.json
```

Expected result:

```text
status: PASS_READY_FOR_VISUAL_QA
missing: 0
normalize_required: 0
alpha_or_mode_required: 0
```

### Gate B: Visual QA Gate

Technical PNG PASS is not enough.

Fail visual QA if any of these are visible:

```text
open-eye pixels inside closed-eye states
rectangular clean-socket patch
skin-tone stain around eyes or mouth
eye size mismatch between open/half/mostly/closed
mouth anchor moves between expressions
new character details appear in only some keyposes
```

### Gate C: Mini Cubism Diagnostic Gate

Only after Gate A and Gate B:

```text
build Mini Cubism diagnostic project
test EyeOpen, EyeBall X/Y, MouthOpenY, MouthForm
capture contact sheet and close-up motion evidence
keep Mini Cubism evidence separate from Cubism Editor production evidence
```

## Existing Character Role

`cubism-v2-new-character-001` remains useful, but only as evidence:

```text
candidate_002: selected visual source but material-pack-late failure
local_generated_keypose_v1: validator PASS but visual QA failure candidate
manual bbox evidence: localization evidence only
Mini Cubism eye/mouth failures: do not promote
```

The next session should start from `cubism-v2-new-character-002`, not by polishing the procedural `local_generated_keypose_v1` assets into production.


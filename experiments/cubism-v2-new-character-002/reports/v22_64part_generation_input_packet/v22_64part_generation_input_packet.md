# Character 002 v22 64-Part Generation Input Packet

- status: `PASS_READY_FOR_G0_SOURCE_STYLE_REVIEW`
- generated_at: `2026-06-09T09:36:22.260189+00:00`
- source spec: `experiments/cubism-v2-new-character-002/reports/v22_64part_generation_spec/v22_64part_generation_spec.json`
- source prompt template: `experiments/reference-model-structure-001/reports/cubism_v2_character_prompt_template.json`

## Goal

Prepare image-generation inputs for the full 64-part material pack, then run G0 source/style review before layer production.

## Identity Lock

- same adult cute female character as the accepted source front
- same face proportions, eye spacing, nose position, and mouth anchor
- same hairstyle silhouette, bang occlusion, line thickness, and shading style
- same outfit design, color palette, and simple upper-body composition
- front-facing or near-front neutral upper-body Live2D/Cubism-ready view

## Global Negative Prompt

```text
labels, guide marks, UI, watermark, text, part names, arrows, exploded diagram
different character, different outfit, new accessory, changed hairstyle
face-covering hair, covered eyes, covered mouth, crossed arms, complex hands, large props
cropped head, cropped shoulders, side view, extreme pose, perspective distortion
patch boundary, rectangular skin fill, oval mouth patch, visible erased-eye residue
moving eye whites, detached pupil, detached highlight, crossed-eye gaze
oversized round wide-open mouth, tiny centered mouth, pasted teeth, pasted tongue
heavy glow, motion blur, transparent effects, messy dense overlap
```

## G0 Source/Style Review Checklist

- same adult cute female character identity is appealing enough for production expansion
- front/near-front upper-body pose is centered and not cropped
- both eyes are visible and eye size is not too large
- mouth is visible, small enough, and placed naturally
- nose is visible as subtle face detail
- front/side/back hair groups are readable and not fused into one mass
- neck, shoulders, torso, collar, and simple upper arms are visible
- no props, hands, hair, or accessories cover eyes or mouth
- design appears splittable into 64 v2_standard parts
- no labels, part names, guide marks, or diagram layout

## Batch Prompts

### B0_source_identity

Lock one same-character source before any split asset is accepted.

Expected outputs:
- `new_character_002_source_front`
- `source_palette_reference`
- `source_identity_notes`

Positive prompt:

```text
Live2D Cubism v2_standard material-pack generation.
same adult cute female character as the accepted source front
same face proportions, eye spacing, nose position, and mouth anchor
same hairstyle silhouette, bang occlusion, line thickness, and shading style
same outfit design, color palette, and simple upper-body composition
front-facing or near-front neutral upper-body Live2D/Cubism-ready view

Base character source constraints:
Live2D Cubism v2_standard VTuber character, front-facing upper-body, centered neutral pose.
A single clean master PNG for later PSD part separation and Cubism rigging.
Clear face base, both eyes fully visible, separated left and right eye groups, readable eyebrows, clear mouth not covered by anything.
Layer-friendly hair: separate front bangs, left side hair, right side hair, and back hair, clean strand groups for hair physics.
Visible neck, simple upper body, clear shoulders, simple upper arms, no complex hands, no large props.
Clean silhouette, minimal overlap, low clipping risk, underpaint-friendly design, simple draw order.
Consistent polished anime illustration style, clean line art, clean color separation.

Batch: B0_source_identity
Lock one same-character source before any split asset is accepted.
Create the accepted source/front identity reference.
Prioritize clean silhouette, readable hair groups, visible eyes/mouth/nose, visible neck/shoulders/torso.
Do not make this a part sheet; make it the coherent source image for the material pack.

Required output IDs:
- new_character_002_source_front
- source_palette_reference
- source_identity_notes

Batch rules:
- adult cute female character identity remains fixed across all following assets
- front or near-front upper-body pose with visible neck, shoulders, torso, eyes, mouth, and readable hair groups
- no labels, guides, text, props covering eyes/mouth/hair, or accessory changes between sheets
```

Must pass:
- 주인님 accepts the character style/outfit for production expansion
- eyes, mouth, nose, hair groups, neck, shoulders, and torso are readable
- design looks splittable into the confirmed 64-part taxonomy

### B1_clean_base_underpaint

Create clean bases at generation time instead of patching baked pixels later.

Expected outputs:
- `face_base`
- `face_underpaint_L`
- `face_underpaint_R`
- `eye_L_underpaint`
- `eye_R_underpaint`
- `mouth_base_clean_reference`
- `body_underpaint`
- `neck_shadow_underpaint`
- `arm_L_underpaint`
- `arm_R_underpaint`
- `hair_back_underpaint`

Positive prompt:

```text
Live2D Cubism v2_standard material-pack generation.
same adult cute female character as the accepted source front
same face proportions, eye spacing, nose position, and mouth anchor
same hairstyle silhouette, bang occlusion, line thickness, and shading style
same outfit design, color palette, and simple upper-body composition
front-facing or near-front neutral upper-body Live2D/Cubism-ready view

Base character source constraints:
Live2D Cubism v2_standard VTuber character, front-facing upper-body, centered neutral pose.
A single clean master PNG for later PSD part separation and Cubism rigging.
Clear face base, both eyes fully visible, separated left and right eye groups, readable eyebrows, clear mouth not covered by anything.
Layer-friendly hair: separate front bangs, left side hair, right side hair, and back hair, clean strand groups for hair physics.
Visible neck, simple upper body, clear shoulders, simple upper arms, no complex hands, no large props.
Clean silhouette, minimal overlap, low clipping risk, underpaint-friendly design, simple draw order.
Consistent polished anime illustration style, clean line art, clean color separation.

Batch: B1_clean_base_underpaint
Create clean bases at generation time instead of patching baked pixels later.
Generate clean base and underpaint material for the same character.
Face and underpaint areas must be naturally painted, not erased or covered.
Clean sockets must preserve skin gradient, blush, eyelid fold, and hair occlusion.

Required output IDs:
- face_base
- face_underpaint_L
- face_underpaint_R
- eye_L_underpaint
- eye_R_underpaint
- mouth_base_clean_reference
- body_underpaint
- neck_shadow_underpaint
- arm_L_underpaint
- arm_R_underpaint
- hair_back_underpaint

Batch rules:
- face_base has no open-eye, iris, pupil, eye-white, lash, mouth-line, teeth, or tongue remnants
- underpaint preserves skin/hair gradients and occlusion, with no rectangular patch boundary
- do not promote procedural cover patches or late mask surgery as production clean base
```

Must pass:
- face_base has no open-eye, iris, pupil, white, lash, mouth line, teeth, or tongue residue
- no rectangular or oval patch boundary around eyes or mouth
- underpaints are suitable for head angle, blink, mouth open, body angle, and hair physics gaps

### B2_eye_pack

Generate production eye parts and blink in-betweens as one coordinated eye packet.

Expected outputs:
- `eye_L_white`
- `eye_L_iris`
- `eye_L_pupil`
- `eye_L_highlight`
- `eye_L_upper_lash`
- `eye_L_lower_lash`
- `eye_L_closed_lid`
- `eye_R_white`
- `eye_R_iris`
- `eye_R_pupil`
- `eye_R_highlight`
- `eye_R_upper_lash`
- `eye_R_lower_lash`
- `eye_R_closed_lid`
- `eye_open_reference`
- `eye_half_closed_reference`
- `eye_mostly_closed_reference`
- `eye_closed_reference`

Positive prompt:

```text
Live2D Cubism v2_standard material-pack generation.
same adult cute female character as the accepted source front
same face proportions, eye spacing, nose position, and mouth anchor
same hairstyle silhouette, bang occlusion, line thickness, and shading style
same outfit design, color palette, and simple upper-body composition
front-facing or near-front neutral upper-body Live2D/Cubism-ready view

Base character source constraints:
Live2D Cubism v2_standard VTuber character, front-facing upper-body, centered neutral pose.
A single clean master PNG for later PSD part separation and Cubism rigging.
Clear face base, both eyes fully visible, separated left and right eye groups, readable eyebrows, clear mouth not covered by anything.
Layer-friendly hair: separate front bangs, left side hair, right side hair, and back hair, clean strand groups for hair physics.
Visible neck, simple upper body, clear shoulders, simple upper arms, no complex hands, no large props.
Clean silhouette, minimal overlap, low clipping risk, underpaint-friendly design, simple draw order.
Consistent polished anime illustration style, clean line art, clean color separation.

Batch: B2_eye_pack
Generate production eye parts and blink in-betweens as one coordinated eye packet.
Generate left/right eye production parts and blink references as one coherent eye packet.
Eye whites are socket-bound material; iris, pupil, and highlight must be mutually aligned.
Blink in-betweens should follow the v21 natural close pattern, avoiding a harsh 0.0 default close.

Required output IDs:
- eye_L_white
- eye_L_iris
- eye_L_pupil
- eye_L_highlight
- eye_L_upper_lash
- eye_L_lower_lash
- eye_L_closed_lid
- eye_R_white
- eye_R_iris
- eye_R_pupil
- eye_R_highlight
- eye_R_upper_lash
- eye_R_lower_lash
- eye_R_closed_lid
- eye_open_reference
- eye_half_closed_reference
- eye_mostly_closed_reference
- eye_closed_reference

Batch rules:
- eye whites stay fixed for EyeBallX/Y; iris, pupil, and highlight move together from the same anchor
- split iris/pupil/highlight may pass only if they are generated as a coherent packet and anchor-locked
- if split details drift or create crossed eyes, fall back to a coherent iris-detail diagnostic asset and regenerate the production split
- EyeOpen visual clamp target starts from v21 pattern: natural close is around 0.27, not hard 0.0
```

Must pass:
- left and right gaze centers are natural and not crossed
- iris/pupil/highlight can move together from one anchor
- closed lids and underpaint reveal no original open-eye pixels

### B3_mouth_pack

Generate mouth rig parts as a coordinated smile-open material packet.

Expected outputs:
- `mouth_line`
- `mouth_inner`
- `mouth_upper_lip_mask`
- `mouth_lower_lip_mask`
- `mouth_teeth`
- `mouth_tongue`
- `mouth_corner_L`
- `mouth_corner_R`
- `mouth_closed_smile_reference`
- `mouth_small_open_reference`
- `mouth_mid_teeth_reference`
- `mouth_wide_teeth_tongue_reference`

Positive prompt:

```text
Live2D Cubism v2_standard material-pack generation.
same adult cute female character as the accepted source front
same face proportions, eye spacing, nose position, and mouth anchor
same hairstyle silhouette, bang occlusion, line thickness, and shading style
same outfit design, color palette, and simple upper-body composition
front-facing or near-front neutral upper-body Live2D/Cubism-ready view

Base character source constraints:
Live2D Cubism v2_standard VTuber character, front-facing upper-body, centered neutral pose.
A single clean master PNG for later PSD part separation and Cubism rigging.
Clear face base, both eyes fully visible, separated left and right eye groups, readable eyebrows, clear mouth not covered by anything.
Layer-friendly hair: separate front bangs, left side hair, right side hair, and back hair, clean strand groups for hair physics.
Visible neck, simple upper body, clear shoulders, simple upper arms, no complex hands, no large props.
Clean silhouette, minimal overlap, low clipping risk, underpaint-friendly design, simple draw order.
Consistent polished anime illustration style, clean line art, clean color separation.

Batch: B3_mouth_pack
Generate mouth rig parts as a coordinated smile-open material packet.
Generate one coordinated smile-open mouth packet for production splitting.
Mouth internals must be drawn inside the same mouth opening, not pasted later.
Wide open should show teeth and tongue naturally but remain proportion-limited.

Required output IDs:
- mouth_line
- mouth_inner
- mouth_upper_lip_mask
- mouth_lower_lip_mask
- mouth_teeth
- mouth_tongue
- mouth_corner_L
- mouth_corner_R
- mouth_closed_smile_reference
- mouth_small_open_reference
- mouth_mid_teeth_reference
- mouth_wide_teeth_tongue_reference

Batch rules:
- teeth/tongue/inner must be drawn naturally inside the same mouth opening, not pasted as separate centered overlays
- wide-open reference must be proportion-limited; reject oversized round mouth shapes
- ParamMouthOpenY max remains visually clamped around 0.85 until a better mouth packet is approved
- ParamMouthForm is not active in v21 diagnostic unless a real production mouth-form set is generated
```

Must pass:
- mouth anchor stays consistent across closed, small, mid, and wide references
- teeth/tongue/inner read naturally and follow the mouth shape
- wide-open mouth is not oversized, circular, or patchy

### B4_hair_pack

Create independent front/back/side hair children so HairFront can become real.

Expected outputs:
- `hair_back_base`
- `hair_back_strand_L`
- `hair_back_strand_R`
- `hair_back_center`
- `hair_front_center`
- `hair_front_L`
- `hair_front_R`
- `hair_front_side_L`
- `hair_front_side_R`
- `hair_front_tip_L`
- `hair_front_tip_R`
- `hair_side_L_outer`
- `hair_side_L_inner`
- `hair_side_R_outer`
- `hair_side_R_inner`

Positive prompt:

```text
Live2D Cubism v2_standard material-pack generation.
same adult cute female character as the accepted source front
same face proportions, eye spacing, nose position, and mouth anchor
same hairstyle silhouette, bang occlusion, line thickness, and shading style
same outfit design, color palette, and simple upper-body composition
front-facing or near-front neutral upper-body Live2D/Cubism-ready view

Base character source constraints:
Live2D Cubism v2_standard VTuber character, front-facing upper-body, centered neutral pose.
A single clean master PNG for later PSD part separation and Cubism rigging.
Clear face base, both eyes fully visible, separated left and right eye groups, readable eyebrows, clear mouth not covered by anything.
Layer-friendly hair: separate front bangs, left side hair, right side hair, and back hair, clean strand groups for hair physics.
Visible neck, simple upper body, clear shoulders, simple upper arms, no complex hands, no large props.
Clean silhouette, minimal overlap, low clipping risk, underpaint-friendly design, simple draw order.
Consistent polished anime illustration style, clean line art, clean color separation.

Batch: B4_hair_pack
Create independent front/back/side hair children so HairFront can become real.
Generate independent front, side, and back hair children for real HairFront/HairSide/HairBack controls.
Front bangs must remain consistent with face/eye occlusion from the source.
Hair underpaint must cover expected motion gaps.

Required output IDs:
- hair_back_base
- hair_back_strand_L
- hair_back_strand_R
- hair_back_center
- hair_front_center
- hair_front_L
- hair_front_R
- hair_front_side_L
- hair_front_side_R
- hair_front_tip_L
- hair_front_tip_R
- hair_side_L_outer
- hair_side_L_inner
- hair_side_R_outer
- hair_side_R_inner

Batch rules:
- ParamHairFront stays unsupported until real hair_front_* child parts exist and move independently
- front bangs must preserve face/eye occlusion consistency across clean base and eye packets
- side/back hair parts must leave underpaint coverage for angle and physics motion
```

Must pass:
- hair_front_* children are visible and separable
- front hair can move independently without exposing holes
- side/back hair groups have readable strand boundaries for physics

### B5_body_clothing_pack

Complete torso, neck, shoulder, arm, and clothing layers for standard body motion.

Expected outputs:
- `torso_base`
- `neck`
- `shoulder_L`
- `shoulder_R`
- `arm_L_upper_simple`
- `arm_R_upper_simple`
- `collar_front`
- `collar_shadow`
- `chest_cloth_base`
- `chest_cloth_shadow`
- `brow_L`
- `brow_R`
- `nose`
- `cheek_L`
- `cheek_R`
- `face_shadow_L`
- `face_shadow_R`

Positive prompt:

```text
Live2D Cubism v2_standard material-pack generation.
same adult cute female character as the accepted source front
same face proportions, eye spacing, nose position, and mouth anchor
same hairstyle silhouette, bang occlusion, line thickness, and shading style
same outfit design, color palette, and simple upper-body composition
front-facing or near-front neutral upper-body Live2D/Cubism-ready view

Base character source constraints:
Live2D Cubism v2_standard VTuber character, front-facing upper-body, centered neutral pose.
A single clean master PNG for later PSD part separation and Cubism rigging.
Clear face base, both eyes fully visible, separated left and right eye groups, readable eyebrows, clear mouth not covered by anything.
Layer-friendly hair: separate front bangs, left side hair, right side hair, and back hair, clean strand groups for hair physics.
Visible neck, simple upper body, clear shoulders, simple upper arms, no complex hands, no large props.
Clean silhouette, minimal overlap, low clipping risk, underpaint-friendly design, simple draw order.
Consistent polished anime illustration style, clean line art, clean color separation.

Batch: B5_body_clothing_pack
Complete torso, neck, shoulder, arm, and clothing layers for standard body motion.
Generate body, clothing, brow, nose, cheek, and face shadow production parts.
Keep the v2_standard scope simple and rig-friendly.
Nose and cheeks must stay subtle but visible as separate material.

Required output IDs:
- torso_base
- neck
- shoulder_L
- shoulder_R
- arm_L_upper_simple
- arm_R_upper_simple
- collar_front
- collar_shadow
- chest_cloth_base
- chest_cloth_shadow
- brow_L
- brow_R
- nose
- cheek_L
- cheek_R
- face_shadow_L
- face_shadow_R

Batch rules:
- keep first v2_standard scope simple: no complex hands, large props, heavy effects, or rich vowel set
- nose must remain visible as its own subtle part; do not lose it during face cleanup
- body and clothing parts must support breath and body-angle motion without visible holes
```

Must pass:
- neck, shoulders, torso, simple arms, collar, and chest cloth are readable
- nose is not lost during clean face/base generation
- body/clothing underpaint can support breath/body angle without visible holes

## Output Rules

- Keep raw outputs as evidence before normalization.
- Normalize accepted crops or sheets to shared full-canvas RGBA PNGs.
- Default normalization canvas is 2048x2048 unless a later Cubism authoring decision explicitly changes it.
- Every crop output must preserve ROI/anchor metadata for later full-canvas placement.
- Do not delete rejected outputs; mark them REVISE, FAIL, DISCARDED, or BLOCKED.

## Next After G0 Pass

- generate B1 clean base/underpaint packet
- generate B2 eye packet
- generate B3 mouth packet
- generate B4 hair packet
- generate B5 body/clothing packet
- normalize raw outputs to full-canvas RGBA
- run technical validators and build contact sheet before Mini Cubism diagnostic

## Self Review

- `batch_count`: `6`
- `has_b0_source_prompt`: `True`
- `has_eye_prompt`: `True`
- `has_mouth_prompt`: `True`
- `has_hair_prompt`: `True`
- `has_g0_checklist`: `True`
- `part_count`: `64`
- `status`: `PASS`

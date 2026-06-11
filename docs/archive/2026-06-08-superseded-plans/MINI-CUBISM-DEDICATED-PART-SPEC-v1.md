# Mini Cubism Dedicated Part Spec v1

Updated: 2026-06-05

## Goal

새 Mini Cubism 전용 모델은 기존 `mini-cubism-physics-v0-3-001`의 엔진 검증 결과를 바탕으로, 처음부터 physics와 keypose가 잘 먹히도록 파츠를 설계한다. 목표는 예쁜 한 장이 아니라 **파츠 분리, keypose, vertex weight, spring-damper physics, 자동 motion review**까지 이어지는 pipeline 입력을 만드는 것이다.

Experiment:

```text
experiments/mini-cubism-dedicated-model-v1-001
```

Recommended target:

```text
Reduced production candidate: 68 parts
Full expressive target: 86 parts
Minimum acceptable: 60 parts
```

## Design Rules

- 흔들려야 하는 곳은 독립 파츠로 나눈다.
- 안정적이어야 하는 곳은 큰 기준 파츠로 둔다.
- Eyes and mouth are keypose-first, not physics-first.
- Hair and accessories are physics-first.
- Body is anchor-first; avoid cheap full-body wobble.
- Generated mouth/eye keypose art must be separate from canonical base art.
- Glue remains fixture-gated and is not part of v1 generation.

## Reduced 68-Part Target

### Body And Anchor

| Part | Physics | Notes |
|---|---:|---|
| body_base | none | root visual anchor |
| neck | none | head/body bridge |
| neck_shadow | none | bridge shading |
| chest | low | torso mass |
| chest_shadow | none | depth |
| shoulder_L | low | arm anchor |
| shoulder_R | low | arm anchor |
| arm_L | optional slow | reduced from upper/forearm/hand |
| arm_R | optional slow | reduced from upper/forearm/hand |
| sleeve_L | soft small | cloth motion |
| sleeve_R | soft small | cloth motion |

### Face And Ear

| Part | Physics | Notes |
|---|---:|---|
| face_base | none | expression anchor |
| face_shadow_L | none | angle support |
| face_shadow_R | none | angle support |
| ear_L | small | secondary motion |
| ear_R | small | secondary motion |
| ear_inner_L | parent follow | parent to ear |
| ear_inner_R | parent follow | parent to ear |
| cheek_blush_L | none | expression overlay |
| cheek_blush_R | none | expression overlay |

### Hair

| Part | Physics | Notes |
|---|---:|---|
| front_bang_L | light spring | root-to-tip weight |
| front_bang_CL | light spring | slight independent lag |
| front_bang_C | light spring | central bang |
| front_bang_CR | light spring | slight independent lag |
| front_bang_R | light spring | root-to-tip weight |
| front_side_lock_L | medium spring | side motion |
| front_side_lock_R | medium spring | side motion |
| side_hair_L_upper | medium | upper follows head |
| side_hair_L_lower | slow | lower delayed follow |
| side_hair_R_upper | medium | upper follows head |
| side_hair_R_lower | slow | lower delayed follow |
| back_hair_base | low | stable mass |
| back_hair_L | heavy spring | large mass |
| back_hair_C | heavy spring | large mass |
| back_hair_R | heavy spring | large mass |
| back_hair_tip_L | heavy slow | visible settle |
| back_hair_tip_C | heavy slow | visible settle |
| back_hair_tip_R | heavy slow | visible settle |

### Eyes

| Part | Keypose | Notes |
|---|---:|---|
| eye_white_L | open/half/closed | masked by blink |
| eye_white_R | open/half/closed | masked by blink |
| iris_L | open/half, hidden closed | no closed-eye ghost |
| iris_R | open/half, hidden closed | no closed-eye ghost |
| pupil_L | open/half, hidden closed | follows iris |
| pupil_R | open/half, hidden closed | follows iris |
| catchlight_L | open/half, hidden closed | follows iris |
| catchlight_R | open/half, hidden closed | follows iris |
| upper_lid_L | open/half/closed | blink shape |
| upper_lid_R | open/half/closed | blink shape |
| lower_lid_L | open/half/closed | blink shape |
| lower_lid_R | open/half/closed | blink shape |
| upper_lash_L | open/half/closed | visible closed |
| upper_lash_R | open/half/closed | visible closed |
| brow_L | expression | angle/form |
| brow_R | expression | angle/form |

### Mouth

| Part | Keypose | Notes |
|---|---:|---|
| mouth_closed_line | closed | visible only at openY 0 |
| mouth_half_outer | half | visible only at openY 0.5 |
| mouth_half_inner | half | visible only at openY 0.5 |
| mouth_open_outer | open | visible only at openY 1 |
| mouth_open_inner | open | visible only at openY 1 |
| mouth_teeth_upper | open | optional at open/half |
| mouth_tongue | open | optional at open |
| mouth_shadow | open/half | depth |

### Clothes And Accessories

| Part | Physics | Notes |
|---|---:|---|
| choker_base | none | neck anchor |
| choker_gem | fast small | visible accessory physics |
| ribbon_center | low | anchor |
| ribbon_loop_L | medium | soft cloth |
| ribbon_loop_R | medium | soft cloth |
| ribbon_tail_L | medium spring | delayed flutter |
| ribbon_tail_R | medium spring | delayed flutter |
| shoulder_frill_L | low flutter | small cloth |
| shoulder_frill_R | low flutter | small cloth |
| sleeve_frill_L | soft flutter | small cloth |
| sleeve_frill_R | soft flutter | small cloth |

## Key Parameters

```text
ParamAngleX      -30..30
ParamAngleY      -20..20
ParamAngleZ      -15..15
ParamEyeLOpen    0..1 key values 0, 0.5, 1
ParamEyeROpen    0..1 key values 0, 0.5, 1
ParamMouthOpenY  0..1 key values 0, 0.5, 1
ParamMouthForm   -1..1 frown/neutral/smile
ParamHairFront   -1..1
ParamHairBack    -1..1
ParamAccessory   -1..1
```

## Physics Profiles

Recommended profile groups:

```text
front_bang_light
front_side_lock_medium
side_hair_lower_slow
back_hair_heavy
back_hair_tip_slow
ribbon_tail_spring
choker_gem_fast
sleeve_frill_flutter
ear_small_secondary
```

Rules:

- hair root weight near 0.0, tip weight near 1.0
- accessory anchors near 0.0, loose ends near 1.0
- face/eyes/mouth physics weight 0.0
- settle within 40 frames
- no infinite oscillation

## Image Generation Brief

Canonical image generation should request:

```text
front-facing 2D anime VTuber model design, symmetrical standing bust, clean separated silhouette, long layered dark hair with clearly separated bangs and side locks, visible ribbon/choker and sleeve frills, simple readable eyes and mouth, neutral expression, arms visible but not crossed, high resolution, plain transparent or flat light background, no labels, no text, no watermark, not cropped
```

Avoid:

```text
busy hair clumps, occluded eyes, hidden mouth, crossed arms, complex props, tilted head, profile pose, open mouth only, text labels
```

## Pipeline Goal

The dedicated model pipeline is successful only when:

```text
part_count >= 60
hair_parts >= 18
eye_parts >= 16
mouth_parts >= 8
physics_targets >= 12
mouth closed/half/open has exclusive visibility
eye closed hides iris/pupil/catchlight
spring profiles settle within 40 frames
motion GIFs and review packet are generated
```

## Current Relationship To v0.3

`mini-cubism-physics-v0-3-001` remains the engine validation model. This v1 dedicated model is the first model designed for that engine, not a replacement for the evidence already created.

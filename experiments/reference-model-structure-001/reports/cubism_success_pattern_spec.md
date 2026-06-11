# Cubism Success Pattern Spec

Generated: 2026-06-05T15:28:31.029640+00:00

This is the Cubism-first baseline for the next Vtube model. It learns structure only and must not copy official sample art, textures, PSD layers, or character designs.

## Position

- `imagen-live2d-001`: Use imagen-live2d-001 only as a shallow-rig failure fixture unless it is manually rerigged in Cubism.
- New model rule: Design the next model from Cubism rig requirements first; image resolution is secondary.
- Asset policy: Do not reuse official sample art, textures, PSD layers, or character designs.

## Official Core Stats

| Metric | Value |
|---|---:|
| model_count | 18 |
| art_meshes_median | 90 |
| parameters_median | 51 |
| warp_deformers_median | 52 |
| rotation_deformers_median | 22 |
| keyform_bindings_median | 227 |
| physics_groups_median | 6 |
| art_meshes_min_nonzero | 33 |
| parameters_min_nonzero | 27 |
| warp_deformers_min_nonzero | 26 |
| keyform_bindings_min_nonzero | 90 |

## Minimum Cubism v2 Pass Gate

| Item | Gate |
|---|---|
| art_meshes | >= 20 |
| parameters | >= 15 |
| warp_deformers | >= 8 |
| rotation_deformers | >= 1 |
| keyform_bindings | >= 20 |
| physics_groups | >= 1 when hair is medium/long; optional for bald/very short hair |

Comparator:

- `--expect-warp-increase`
- `--expect-keyform-binding-increase`

## Standard Target

| Item | Target |
|---|---|
| art_meshes | 50-120 for first solid avatar; official rich samples go much higher |
| parameters | 25-60 before optional expressions |
| warp_deformers | 25-60 |
| rotation_deformers | 5-25 |
| keyform_bindings | 90-250 |
| physics_groups | 2-8 |

## Image Policy

- Resolution: 1024, 1536, or 2048 are all acceptable; choose by downstream split/import stability.

Generation order:

- Cubism part/deformer spec
- single-source matched character prompt
- part split and alpha cleanup plan
- Cubism import material pack
- manual Cubism deformer/keyform authoring

Hard requirements:

- front-facing or near-front upper-body character
- clear separated eyes, mouth, face outline, front/side/back hair masses
- neck and shoulder area visible enough for body angle deformation
- arms not covering mouth, eyes, or hair silhouette in the first pass
- minimal text, props, extreme accessories, and heavy transparent effects

## Part Taxonomy

### eye

- eye white L/R
- iris/pupil L/R
- upper eyelid L/R
- lower eyelid or lash L/R
- brow L/R

### mouth

- mouth line
- upper lip or upper mouth mask
- lower lip or lower mouth mask
- mouth inner
- teeth/tongue optional

### hair

- front hair clumps
- side hair L/R
- back hair
- long strand/twin-tail groups when present

### body_angle

- face base
- head container
- neck
- upper body/torso
- shoulders
- arms/hands optional for v2.1

## Parameters

Required:

- `ParamAngleX`
- `ParamAngleY`
- `ParamAngleZ`
- `ParamBodyAngleX`
- `ParamBodyAngleY`
- `ParamEyeLOpen`
- `ParamEyeROpen`
- `ParamEyeBallX`
- `ParamEyeBallY`
- `ParamMouthOpenY`
- `ParamMouthForm`
- `ParamBreath`

Recommended:

- `ParamBrowLY`
- `ParamBrowRY`
- `ParamHairFront`
- `ParamHairSideL`
- `ParamHairSideR`
- `ParamHairBack`

## Deformer And Keyform Spec

Required deformer groups:

- root/body warp
- head/face warp
- eye L/R warp
- mouth warp
- front hair warp
- side/back hair warp
- neck/body angle warp
- at least one rotation deformer for head, hair, or body

Required keyforms:

- AngleX -30/0/+30
- AngleY -30/0/+30
- AngleZ -10/0/+10
- EyeOpen L/R 0/0.5/1
- MouthOpenY 0/0.5/1
- MouthForm -1/0/+1
- Hair swing left/neutral/right
- BodyAngleX -10/0/+10

## Physics Spec

- Inputs: ParamAngleX, ParamAngleY, ParamAngleZ, ParamBodyAngleX
- Outputs: front hair, side hair, back hair, optional accessory
- First pass groups: front hair, side hair, back hair, optional accessory

## Evidence Gate

- before/after cmo3 structure report
- compare_cmo3_structure_reports.py with warp and keyform expectations
- Cubism GUI screenshots for eye, mouth, hair, angle extremes
- draw order and overhang note
- runtime model3/moc3 export smoke only after CMO3 structure passes

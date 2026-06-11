# Mini Cubism Feature Spec

Updated: 2026-06-04

## Purpose

This document defines what "small Cubism" means for the Vtube project.

The target is not a toy layer previewer. The target is a small rigging tool that
can eventually reach Cubism-like production concepts:

```text
separated parts
-> dense ArtMesh
-> nested deformers
-> parameter keyforms
-> glue / attachment constraints
-> draw-order and overhang validation
-> runtime preview
```

The reference image from 주인님 shows a dense Cubism rig surface: many mesh
vertices, green deformer boxes, orange selected control points, and Glue labels
around hair, ears, hood, hat, accessories, and effect parts. That sets the
feature target higher than the current MVP.

## Product Goal

Build a local "Mini Cubism" that can author, inspect, and preview Vtube rigs
without depending on screenshot-only Cubism GUI automation.

Near-term goal:

```text
Create a minimal but real rig authoring surface for parts, meshes, deformers,
parameters, and preview.
```

Long-term goal:

```text
Automate enough Cubism-style rigging that repeated avatar setup is faster than
manual Cubism Editor work.
```

Non-goal for v0:

```text
Do not clone all of Live2D Cubism.
Do not require .moc3 export.
Do not claim production equivalence until deformation quality is validated.
```

## GitHub Reference Map

The current reference list is intentionally small and feature-oriented. Add a
new repository only after it explains one of the feature gaps below better than
the current references.

Reference rule:

```text
Do not clone another tool's UX or architecture.
Use GitHub projects as evidence sources for isolated concepts, then design the
Mini Cubism data model and workflow around Vtube's own requirements.
```

| Feature Area | Primary GitHub Reference | Secondary Reference | Why |
|---|---|---|---|
| mature small-Cubism editor UX | `https://github.com/Inochi2D/inochi-creator` | `https://github.com/JeffreyChen-s-Utils/Imervue` | Part tree, viewport, mesh editor, parameter panels, and puppet workflow |
| non-Cubism puppet runtime model | `https://github.com/Inochi2D/inochi2d` | `https://github.com/DragonBones/DragonBonesJS` | Runtime file model, drawable hierarchy, animation/runtime separation |
| CMO3/deformer/keyform structure research | `https://github.com/MangoLion/stretchystudio` | current local positive fixture | Best match for this repo because it overlaps with layers, mesh deformation, and CMO3 writer research |
| mesh generation and manual mesh editing | `https://github.com/Inochi2D/inochi-creator` | `https://github.com/Retropaint/SkelForm` | Automesh, mesh editor UX, vertex/edge/triangle workflows |
| parameter binding and deformation UX | `https://github.com/Inochi2D/inochi-creator` | `https://github.com/JeffreyChen-s-Utils/Imervue` | Parameter sliders, editable deformation state, puppet animation concepts |
| dense mesh and 2D animation reference | `https://github.com/AnimeEffectsDevs/AnimeEffects` | `https://github.com/Retropaint/SkelForm` | Historical 2D mesh deformation and animation workflow reference |
| skeletal/runtime comparison | `https://github.com/DragonBones/DragonBonesJS` | `https://github.com/Inochi2D/inochi2d` | Useful contrast for drawables, bones, runtime update loops, and animation data |
| Glue structure and runtime sections | `https://github.com/MangoLion/stretchystudio` | `https://github.com/Ludentes/py-moc3` | Stretchy documents `CGlueSource`/`CAffecterSourceSet` and MOC3 glue sections; py-moc3 exposes MOC3 glue section entries for reader/writer work |

Current known references:

```text
Inochi Creator: https://github.com/Inochi2D/inochi-creator
Inochi2D SDK:   https://github.com/Inochi2D/inochi2d
Stretchy Studio: https://github.com/MangoLion/stretchystudio
Imervue: https://github.com/JeffreyChen-s-Utils/Imervue
SkelForm: https://github.com/Retropaint/SkelForm
AnimeEffects: https://github.com/AnimeEffectsDevs/AnimeEffects
DragonBonesJS: https://github.com/DragonBones/DragonBonesJS
py-moc3: https://github.com/Ludentes/py-moc3
```

Glue reference conclusion:

```text
No complete open-source Cubism-Glue authoring implementation has been proven.

Best current references:
1. Live2D official Glue manual for behavior and UX semantics.
2. Stretchy Studio for CMO3/MOC3 structure names around CGlueSource,
   CAffecterSourceSet, and glue runtime sections.
3. py-moc3 for MOC3 binary reader/writer section mapping.

Open gap:
We still need a local glue fixture or a public CMO3 with real CGlueSource data
that can be inspected and converted into a Mini Cubism glue schema.
```

Stretchy Studio caution:

```text
Stretchy Studio is not the product blueprint.
It is only a structure reference for CMO3/MOC3 terms and brittle export lessons.
Our UI, local save format, rig authoring workflow, and validation gates must be
Vtube-native.
```

## Feature Tiers

### Tier 0: Evidence And Inspection

Status target: already partly proven by current CMO3 inspector.

Required:

- Load current Vtube experiment manifests and PSD candidate layer manifests.
- Inspect CMO3-like rig structure counts:
  - ArtMeshes
  - Warp Deformers
  - Rotation Deformers
  - KeyformBindings
  - Parameters
  - Glue/constraint equivalents
- Compare before/after rig structure deltas.
- Keep screenshots, human review, numeric bbox/ROI evidence, and structure
  reports separate.

Acceptance:

```text
Given a saved rig file, the tool can say whether it has real deformers and
keyform bindings, not only imported parts.
```

### Tier 1: Part And Mesh Authoring

Required:

- Import full-canvas PNG parts without flattening.
- Preserve part ids, display names, source paths, bbox, alpha coverage, and
  draw order.
- Show part tree with folders:
  - Hair
  - Face
  - Eyes
  - Mouth
  - Body
  - Accessory
  - Effects
- Toggle visibility, lock, solo, opacity, and selection.
- Generate initial alpha-based meshes.
- Support manual mesh editing:
  - add/delete vertices
  - move vertices
  - add/delete edges
  - triangulate faces
  - show vertex density heatmap
  - preserve boundary vertices around transparent edges
- Support dense mesh mode for hair, ears, hood, accessories, and effects.

Acceptance:

```text
The tool can create non-empty editable meshes for all visible parts and save
them as reusable mesh data.
```

### Tier 2: Deformer Authoring

Required:

- Create Warp Deformers with visible bounding boxes and handles.
- Create Rotation Deformers with pivot controls.
- Nest deformers into a hierarchy.
- Parent ArtMeshes under deformers.
- Move, scale, rotate, rename, duplicate, and delete deformers.
- Show deformer tree and canvas overlays at the same time.
- Support conservative default templates:
  - Root
  - Body
  - Head_X
  - Face_Base
  - Eye_L
  - Eye_R
  - Mouth
  - Hair_Front
  - Hair_Back
  - Ear_L
  - Ear_R
  - Accessory groups

Acceptance:

```text
At least one head/face hierarchy can deform child meshes through nested warp
and rotation deformers.
```

### Tier 3: Parameter And Keyform Binding

Required:

- Parameter panel with standard Live2D-style parameters:
  - ParamAngleX
  - ParamAngleY
  - ParamAngleZ
  - ParamEyeLOpen
  - ParamEyeROpen
  - ParamEyeBallX
  - ParamEyeBallY
  - ParamBrowLY
  - ParamBrowRY
  - ParamMouthOpenY
  - ParamMouthForm
  - ParamBodyAngleX
  - ParamBodyAngleY
  - ParamBodyAngleZ
  - ParamBreath
  - ParamHairFront
  - ParamHairSide
  - ParamHairBack
- Custom parameters for project-specific parts:
  - ears
  - hood
  - hat
  - earrings
  - beam/effect parts
  - arms/sleeves
- Parameter ranges, defaults, and key positions.
- Bind mesh vertices or deformer handles to parameter keyforms.
- Edit neutral and extreme poses.
- Interpolate between keyforms.
- Show active keyform state on canvas.

Acceptance:

```text
Moving ParamEyeLOpen, ParamMouthOpenY, ParamAngleX, and one hair/accessory
parameter visibly changes the rig and can be saved/reloaded.
```

### Tier 4: Glue And Attachment Constraints

The reference image makes Glue a first-class requirement, not a later polish
item.

Reference basis:

- Official Cubism behavior: Glue binds overlapping vertices from two ArtMeshes.
- Vertex weight is per vertex.
- Compatibility is controlled per keyform/parameter state.
- Multiple Glue objects may be attached to one ArtMesh.
- Mesh edits after Glue require caution because stale/empty Glue can remain.
- Runtime/export structure needs separate records for Glue objects, bound
  ArtMesh A/B, per-vertex weights, bound position indices, and keyform
  intensities.

Required:

- Create Glue links between two ArtMeshes or deformers.
- Display Glue labels and connector lines on canvas.
- Support edge/region attachment for:
  - front hair to face/head
  - cat ears to hair/head
  - hat to hair/head
  - earrings to ear/head
  - hood to hair/body
  - effects to body/accessory parts
- Store Glue name, source, target, strength, affected vertices, and parameter
  conditions.
- Toggle Glue visibility.
- Validate Glue targets are not missing after part rename/delete.

Acceptance:

```text
Attached parts follow the parent/head motion without obvious separation at
normal parameter extremes.
```

### Tier 5: Draw Order, Masking, And Overhang Validation

Required:

- Draw-order list with drag reorder.
- Per-part blend mode and opacity.
- Optional clipping/mask groups for eyes, mouth, hair, and accessories.
- Overhang warnings when motion exposes empty underpaint.
- Collision/occlusion preview for dense hair and accessory layers.
- Screenshot capture at neutral and parameter extremes.

Acceptance:

```text
The tool can show whether hair, ears, hood, mouth, eyes, and effects break at
parameter extremes before exporting or handing off to Cubism.
```

### Tier 6: Runtime Preview

Required:

- Browser or local preview with GPU canvas rendering.
- Parameter sliders.
- Preset expressions and motions.
- Simple physics approximation for hair/accessories.
- Webcam/tracking input adapter later:
  - eye open
  - mouth open
  - head x/y/z
  - brow movement
- Export preview bundle:
  - character.json
  - parts/*.png
  - meshes/*.json
  - deformers/*.json
  - parameters/*.json
  - glue/*.json
  - motions/*.json

Acceptance:

```text
The saved rig can be opened in preview mode and driven by sliders without the
authoring UI.
```

## Minimum Viable Rig Quality

The first useful Mini Cubism prototype must support this rig quality:

```text
Parts:
  15-30 visible parts

Meshes:
  editable meshes for every visible part
  dense mesh support for hair/accessories/effects

Deformers:
  nested warp and rotation deformers
  at least head, face, eyes, mouth, hair, body, accessory groups

Parameters:
  eye open/close
  mouth open/form
  head angle X/Y/Z
  body angle X/Y/Z
  hair swing
  accessory/effect motion

Glue:
  at least hair/head, ear/head, hat/head, earring/ear, hood/body style links

Validation:
  neutral and extreme screenshots
  structure counts
  draw order check
  overhang check
  save/reload check
```

## Data Model

Preferred local format:

```text
mini_cubism_project/
  character.json
  parts/
    *.png
  meshes/
    *.json
  deformers/
    *.json
  parameters/
    *.json
  glue/
    *.json
  motions/
    *.json
  reports/
    validation.json
    screenshots/
```

Core records:

```text
Part:
  id, displayName, sourcePath, bbox, alphaCoverage, drawOrder, folderId

Mesh:
  partId, vertices, edges, triangles, boundaryVertexIds

Deformer:
  id, type, parentId, childIds, bounds, pivot, handles

Parameter:
  id, displayName, min, max, default, keyValues

KeyformBinding:
  parameterId, keyValue, targetId, vertexDeltas or deformerHandleDeltas

Glue:
  id, sourceTargetId, destinationTargetId, vertexPairs, strength, enabled
```

## Build Order

1. Build save/load format and part tree.
2. Add mesh generation and manual vertex editing.
3. Add warp/rotation deformer hierarchy.
4. Add parameters and keyform binding.
5. Add Glue constraints.
6. Add draw-order and overhang validation.
7. Add runtime preview bundle.
8. Compare output against Cubism evidence and positive fixtures.

## Current Decision

Small Cubism is the long-term target for this project, but the first prototype
must be scoped as a rig authoring and preview tool.

The current `imagen-live2d-001` CMO3 remains useful as negative evidence:

```text
ArtMeshes and parameters are present, but deformers and keyform bindings are 0.
```

The positive fixture remains useful as structure evidence:

```text
Warp Deformers, Rotation Deformers, and KeyformBindings can be detected.
```

The first Mini Cubism milestone should bridge those two states: author a saved
local rig that has real mesh/deformer/keyform/glue structure and visible motion.

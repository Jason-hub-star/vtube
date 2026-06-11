# Open Source Rigging Analysis

Updated: 2026-06-04

## Scope

This research pass cloned and inspected open-source projects that may help the Vtube pipeline move beyond PSD import smoke toward automated rigging assistance.

Cloned repositories:

- `external_repos/stretchystudio`
- `external_repos/inochi-creator`

## Main Finding

`stretchystudio` is the most relevant repo for the current Cubism automation direction.

It contains direct Live2D/Cubism project-generation code, including:

- PSD/layer organization
- alpha-based mesh generation
- Delaunay triangulation
- armature grouping from layer tags or DWPose
- `.cmo3` writer
- Cubism deformer XML emission
- standard Live2D parameter generation
- eye closure, neck warp, face parallax, hair/clothing physics-like parameter wiring
- `.cmo3` inspection scripts

`inochi-creator` is useful as a mature open-source rigging editor reference, especially for mesh editing, automesh, parameter UI, and deformation workflows. It is less directly useful for Cubism `.cmo3/.moc3` automation because it targets the Inochi2D ecosystem rather than Cubism project files.

## Relevant Stretchy Studio Files

- `src/mesh/generate.js`
  - alpha mask to contour
  - edge/interior point sampling
  - Delaunay triangulation
  - produces vertices, UVs, triangles, edge indices

- `src/io/armatureOrganizer.js`
  - maps named semantic layers to rig groups
  - estimates skeleton pivots from bounds or DWPose
  - assigns parts to head, eyes, neck, torso, arms, legs

- `src/io/live2d/cmo3writer.js`
  - generates Cubism `.cmo3`
  - creates standard parameters such as `ParamEyeLOpen`, `ParamMouthOpenY`, `ParamHairFront`
  - emits art mesh sources, part sources, parameter groups, rotation parameters, keyforms

- `src/io/live2d/cmo3/deformerEmit.js`
  - emits `CWarpDeformerSource`
  - emits `KeyformGridSource`
  - provides reusable single-parameter keyform helpers

- `src/io/live2d/cmo3/bodyRig.js`
  - emits neck warp
  - emits face rotation deformer

- `src/io/live2d/cmo3/faceParallax.js`
  - emits 6x6 face warp
  - uses 9 keyforms over `ParamAngleX` and `ParamAngleY`
  - protects eye/brow/nose/mouth regions from over-deformation

- `scripts/inspect_cmo3.mjs`
  - reads Cubism `.cmo3` CAFF archive
  - extracts `main.xml`
  - searches generated Cubism structures

## Relevance To Professional Rigging

The reference screenshot shows dense professional rigging work:

- many ArtMesh vertices
- local deformation grids
- green deformer boxes
- parameter-driven keyforms
- glue-style relationship labels
- draw-order and part hierarchy density

Stretchy Studio does not fully solve professional Live2D rigging quality. However, it gives concrete building blocks:

- automatic mesh generation from alpha
- automatic deformer/keyform XML emission
- parameter naming and grouping
- face/neck/eye/hair motion heuristics
- `.cmo3` introspection route

This means the next feasible automation step is not screen-clicking Cubism Editor. It is:

1. Generate or inspect Cubism project structure programmatically.
2. Add validation around deformer/keyform presence.
3. Use runtime or `.cmo3` XML evidence to verify rig completeness.
4. Keep final polish in Cubism Editor until generated rigs are reliable.

## Recommended Next Experiment

Create `cubism-cmo3-inspection-001`:

1. Use `scripts/inspect_cmo3.mjs` from Stretchy Studio as a reference.
2. Build a Vtube-native `.cmo3` inspector or wrapper.
3. Extract counts and names for:
   - `CArtMeshSource`
   - `CWarpDeformerSource`
   - `CRotationDeformerSource`
   - `KeyformGridSource`
   - standard parameter IDs
   - part hierarchy entries
4. Run it against `experiments/imagen-live2d-001/cubism_mvp_rig.cmo3`.
5. Compare with `reports/cubism_mvp_rig_validation.json`.

## Decision

Use Stretchy Studio as the primary open-source reference for Cubism-oriented rig automation research.

Use Inochi Creator as a secondary reference for mesh editing UX and automesh concepts, not as a direct Cubism export source.

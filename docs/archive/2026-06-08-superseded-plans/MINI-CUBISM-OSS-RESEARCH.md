# Mini Cubism OSS Research

Updated: 2026-06-04

## Purpose

This document records the current open-source research around building a "small
Cubism" style tool for the Vtube pipeline.

The current project target remains Live2D/Cubism production:

```text
AI canonical image
-> part decomposition
-> part purity review
-> PSD candidate
-> Cubism import/export smoke
-> Cubism deformer/keyform validation
```

Mini Cubism is a research track, not the current production replacement for
Cubism Editor.

## Current Conclusion

Do not start by cloning all of Cubism.

The practical direction is:

```text
1. Keep Cubism as the production compatibility path.
2. Use OSS tools to learn mesh, deformer, parameter, and runtime structures.
3. Build small helper tools first:
   - CMO3 structure inspector
   - deformer/keyform delta checker
   - part tree/parameter template mapper
   - simple preview/runtime experiments
4. Only build a Mini Rigger after repeated Cubism work reveals stable patterns.
```

Feature target:

```text
docs/ref/MINI-CUBISM-FEATURE-SPEC.md
```

That spec defines the required small-Cubism capabilities for dense mesh,
deformer, keyform, Glue, draw-order, overhang, and runtime preview work.
It also maps each feature area to the current GitHub references.

## Candidate Projects

| Project | Link | Type | Project Fit | Current Status |
|---|---|---|---|---|
| Inochi Creator | https://github.com/Inochi2D/inochi-creator | Open-source 2D puppet editor | Best reference for a mature "small Cubism" editor UX, mesh editing, parameter panels, and puppet workflow | RESEARCHED |
| Inochi2D SDK | https://github.com/Inochi2D/inochi2d | Puppet runtime / standard | Best reference for a non-Cubism layered puppet runtime and file model | RESEARCHED |
| Stretchy Studio | https://github.com/MangoLion/stretchystudio | Web/FOSS rigging and animation tool | Best fit for this repo because it already overlaps with See-through, PSD/layer decomposition, mesh deformation, and `.cmo3` writer research | CLONED/USED FOR INSPECTOR |
| Imervue | https://github.com/JeffreyChen-s-Utils/Imervue | Python/PySide/OpenGL puppet animator | Interesting reference for zip/json-style puppet formats with drawables, parameters, deformers, motion, and physics concepts | RESEARCHED |
| SkelForm | https://github.com/Retropaint/SkelForm | 2D skeletal/mesh animation tool | Useful for general 2D mesh/bone animation concepts, less directly aligned with VTuber/Cubism compatibility | RESEARCHED |
| AnimeEffects | https://github.com/AnimeEffectsDevs/AnimeEffects | Older 2D mesh deformation animation tool | Useful historical reference for mesh deformation and PSD-style workflows, but not the primary route | RESEARCHED |
| DragonBones | https://github.com/DragonBones/DragonBonesJS | 2D skeletal animation runtime/editor ecosystem | Useful for runtime architecture comparison, but not Live2D-style face/parameter rigging by default | RESEARCHED |
| py-moc3 | https://github.com/Ludentes/py-moc3 | Python `.moc3` reader/writer | Best secondary reference for MOC3 binary section mapping, including Glue section names; not an authoring UI | RESEARCHED |

## Why Inochi2D Matters

Inochi2D is the closest known open-source "small Cubism" style direction:

- layered 2D puppet concept
- mesh/deformation workflow
- parameter-driven movement
- editor plus runtime ecosystem
- independent format instead of Cubism `.moc3`

Use it to study:

```text
part tree model
mesh editor UX
parameter binding UX
deformation model
runtime file format
export/runtime boundaries
```

Do not assume it can directly import our PSD and produce Cubism-compatible
`.moc3`.

## How To Use Stretchy Studio Safely

Stretchy Studio is useful, but it must not become the product blueprint.

Current GitHub status checked on 2026-06-04:

```text
repo: https://github.com/MangoLion/stretchystudio
default branch: master
archived: false
last pushed: 2026-04-28T03:53:09Z
license: MIT
```

This means it is usable as a reference, but recent activity is limited enough
that we should assume it may have stale assumptions or unfinished edges.

Use Stretchy Studio only for:

```text
1. CMO3/MOC3 structure vocabulary.
2. CAFF archive and main.xml inspection patterns.
3. Deformer/keyform/glue field names and fixture ideas.
4. Negative tests that reveal brittle Cubism export assumptions.
```

Do not use Stretchy Studio for:

```text
1. Product UX.
2. Mini Cubism architecture.
3. Our save format.
4. Our part/mesh/deformer authoring workflow.
5. A copied CMO3 writer as the primary implementation.
```

It has already informed these local tools, which are acceptable because they
are inspectors/fixtures rather than a copied product:

```text
scripts/inspect_cmo3_structure.mjs
scripts/compare_cmo3_structure_reports.py
scripts/build_cmo3_structure_positive_fixture.mjs
```

Current proven local result:

```text
experiments/cmo3-structure-fixture-001/rigged_positive_fixture.cmo3
```

The positive fixture proves our inspector can detect real rig structure:

```text
warpDeformers > 0
rotationDeformers > 0
keyformBindings > 0
```

For Glue, Stretchy Studio remains the best current GitHub reference because its
Live2D export notes mention `CGlueSource`, `CAffecterSourceSet`, and MOC3 glue
sections. It does not yet provide a proven full Glue authoring path for this
repo.

`py-moc3` is useful as a secondary binary-format reference because it exposes
MOC3 section names such as glue indices, glue info weights, position indices,
and keyform intensities.

Decision:

```text
Stretchy Studio is a structure reference, not a design source.
Mini Cubism must be specified from Vtube requirements, Live2D/Cubism behavior,
and our own evidence gates.
```

## Decision Matrix

| Option | Pros | Cons | Decision |
|---|---|---|---|
| Keep using Cubism only | Real Live2D compatibility, known export path | Human rigging effort remains high | Current production path |
| Build full Cubism clone | Full control in theory | Huge scope: PSD import, mesh editor, deformers, keyforms, physics, runtime, export, legal/format risk | Do not pursue now |
| Build Mini Cubism runtime | Control, easier web/OBS/Unity integration | Still needs mesh/deformer/parameter authoring and custom format | Long-term research |
| Build Cubism helper automation | Reduces repetitive work while keeping compatibility | Still requires Cubism for final authoring | Best near-term path |
| Adapt Stretchy-style `.cmo3` generation | Could automate real rig structures | Must validate in Cubism Editor and avoid brittle generated files | Research spike candidate |
| Study Inochi2D editor/runtime | Mature OSS reference | Different format and ecosystem | Strong design reference |

## Minimal Feature Set For A Future Mini Rigger

Only consider building this after Cubism MVP rigging has been repeated enough to
show stable patterns.

Required v0 features:

```text
1. Import full-canvas PNG parts with draw order.
2. Preserve part ids and Korean/English display names.
3. Generate simple alpha-based meshes.
4. Show a part tree and visibility toggles.
5. Provide parameter sliders:
   - ParamEyeLOpen
   - ParamEyeROpen
   - ParamMouthOpenY
   - ParamAngleX
   - ParamAngleY
6. Bind parameters to simple mesh vertex transforms.
7. Save a readable local format:
   - character.json
   - parts/*.png
   - meshes/*.json
   - motions/*.json
8. Preview in browser or local app.
```

Do not make `.moc3` export a v0 requirement.

## Near-Term Recommended Work

The next agent should not build a new editor immediately.

Recommended next sequence:

```text
1. Keep `imagen-live2d-001` as the real Cubism evidence target.
2. Manually create a minimal Cubism deformer/keyform rig once.
3. Save the CMO3.
4. Run:
   node scripts/inspect_cmo3_structure.mjs --experiment-id imagen-live2d-001
5. Compare against the baseline:
   python3 scripts/compare_cmo3_structure_reports.py ...
6. Extract the repeated rig pattern into a template plan.
7. Only then decide whether the template should become:
   - Cubism checklist automation
   - CMO3 writer spike
   - Mini Rigger prototype
```

## Acceptance Gates For Any Mini Cubism Spike

Any future "small Cubism" prototype must pass these gates before it is treated
as useful:

```text
1. It loads Vtube full-canvas part PNGs without flattening.
2. It preserves draw order and part ids.
3. It can generate or load non-empty meshes.
4. It can bind at least one parameter to visible deformation.
5. It can save and reload the same state.
6. It can export a preview bundle or runtime bundle.
7. Its output can be compared against Cubism evidence, not just viewed in isolation.
```

## Current Warnings

- Mini Cubism does not remove rigging complexity; it moves that complexity into
  our own codebase.
- `.moc3` compatible export is not a near-term requirement and may carry legal
  and technical risk.
- The user-facing value may be higher if we automate Cubism preparation and
  validation before replacing Cubism itself.
- Forced `O` review in current experiments is MVP-only evidence, not final
  art-quality approval.

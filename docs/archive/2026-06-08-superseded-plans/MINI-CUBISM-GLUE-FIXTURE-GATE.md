# Mini Cubism Glue Fixture Gate

Updated: 2026-06-04

## Purpose

Mini Cubism에서 Glue는 fixture-backed evidence가 생길 때까지 구현하지 않는다. v0/v0.1에서 preview-only attachment나 deformer-follow behavior를 만들 수는 있지만, real Cubism `.cmo3` 안의 Glue 구조를 확인하기 전에는 그것을 Live2D/Cubism Glue라고 부르지 않는다.

## Required Fixture

Glue implementation can start only after we have a local or public sample that proves:

- A real `.cmo3` contains `CGlueSource`.
- The sample connects at least two `CArtMeshSource` entries.
- The structure exposes or can infer weight, affecter, and affected mesh information.
- `scripts/inspect_cmo3_structure.mjs` or a dedicated inspector can reproduce the Glue count and references.
- The fixture is saved as evidence under `/Users/family/jason/Vtube/experiments/` with a report JSON and a short markdown note.

## Allowed Before Fixture

- Keep `character.json` `glue: []` as the reserved schema placeholder.
- Research `CGlueSource`, `CAffecterSourceSet`, and related names in public references.
- Build preview-only attachment experiments if they are clearly named as constraints, not Glue.

## Not Allowed Before Fixture

- Do not mark Mini Cubism Glue as implemented.
- Do not copy Stretchy Studio save format or UI.
- Do not write a CMO3/MOC3 Glue exporter based on guessed field layout.
- Do not promote preview-only constraints to Cubism compatibility evidence.

## Next Gate

The next Glue task is fixture acquisition, not implementation. PASS requires a report that lists the fixture path, detected Glue sources, connected ArtMesh references, and inspector command output.

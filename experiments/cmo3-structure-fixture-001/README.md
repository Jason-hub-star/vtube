# CMO3 Structure Fixture 001

This experiment is a positive structural fixture for `scripts/inspect_cmo3_structure.mjs`.

It uses the cloned Stretchy Studio CMO3 writer to generate a non-production `.cmo3` that contains ArtMeshes, parameters, warp deformers, a rotation deformer, and keyform bindings.

## Commands

```bash
cd /Users/family/jason/Vtube
node scripts/build_cmo3_structure_positive_fixture.mjs
node scripts/inspect_cmo3_structure.mjs \
  --cmo3 experiments/cmo3-structure-fixture-001/rigged_positive_fixture.cmo3 \
  --out-json experiments/cmo3-structure-fixture-001/reports/cmo3_structure_report.json \
  --out-md experiments/cmo3-structure-fixture-001/reports/cmo3_structure_report.md
```

## Current Result

```text
status: PASS
artMeshes: 7
parameters: 23
warpDeformers: 13
rotationDeformers: 1
keyformBindings: 23
```

## Decision

Keep this fixture as a regression test proving that the CMO3 inspector can detect real deformer/keyform structures when they exist.


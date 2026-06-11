# Next Agent Handoff

Updated: 2026-06-04

## Start Here

Read these first:

```text
/Users/family/jason/Vtube/docs/status/PROJECT-STATUS.md
/Users/family/jason/Vtube/vtube-validation-evidence-log.md
/Users/family/jason/Vtube/docs/ref/MINI-CUBISM-OSS-RESEARCH.md
/Users/family/jason/jason-agent-harness-template/harnesses/vtube-open-source-rigging-research.md
```

Address the user as `주인님` and work in Korean by default.

## Current Situation

The Imagen -> MPS/See-through -> review app -> PSD -> Cubism import/export path
has passed technical smoke, but rig quality is not proven.

Current real CMO3:

```text
/Users/family/jason/Vtube/experiments/imagen-live2d-001/cubism_mvp_rig.cmo3
```

Current structure status:

```text
ArtMesh: present
Parameters: present
Warp Deformer: 0
Rotation Deformer: 0
KeyformBinding: 0
Status: WARN
```

This means the current model is not yet a real MVP rig. It is an imported model
with parts and parameters, pending deformer/keyform work.

## Important Recent Result

A Stretchy Studio-derived positive fixture exists:

```text
/Users/family/jason/Vtube/experiments/cmo3-structure-fixture-001/rigged_positive_fixture.cmo3
```

It proves the local inspector can detect real rig structure:

```text
Warp Deformer: 13
Rotation Deformer: 1
KeyformBinding: 23
Status: PASS
```

This is not production art. It is an inspector regression fixture.

## User Question Being Handed Off

주인님 asked whether building a small Cubism is the best solution.

Current answer:

```text
Not as the immediate next step.
Keep Cubism as production compatibility path.
Research Mini Cubism through OSS references.
Automate Cubism preparation and validation first.
```

The newest research doc is:

```text
/Users/family/jason/Vtube/docs/ref/MINI-CUBISM-OSS-RESEARCH.md
```

## OSS Research Summary

Primary references:

```text
Inochi2D / Inochi Creator:
  best mature open-source small-Cubism-style editor/runtime reference

Stretchy Studio:
  best match for this repo because it overlaps with See-through, PSD/layers,
  mesh deformation, and CMO3 writer experiments

Imervue:
  useful puppet file format and parameter/deformer reference

SkelForm / AnimeEffects / DragonBones:
  secondary references for 2D mesh/skeletal animation architecture
```

## Commands To Verify Current Rig State

```bash
cd /Users/family/jason/Vtube
node scripts/inspect_cmo3_structure.mjs --experiment-id imagen-live2d-001
```

Before/after deformer smoke:

```bash
python3 scripts/compare_cmo3_structure_reports.py \
  --before experiments/imagen-live2d-001/reports/cmo3_structure_baseline_before_deformer_test.json \
  --after experiments/imagen-live2d-001/reports/cmo3_structure_after_deformer_test_current.json \
  --expect-warp-increase \
  --out-json experiments/imagen-live2d-001/reports/cmo3_structure_deformer_test_delta.json \
  --out-md experiments/imagen-live2d-001/reports/cmo3_structure_deformer_test_delta.md
```

Positive fixture regression:

```bash
node scripts/build_cmo3_structure_positive_fixture.mjs
```

Shared harness check:

```bash
bash /Users/family/jason/jason-agent-harness-template/scripts/check-harness.sh
```

## Recommended Next Work

Do this next:

```text
1. Do not start building a full Mini Cubism editor yet.
2. Get one manual Cubism MVP rig saved:
   - eye open/close
   - mouth open/close
   - one basic hair or head deformer
3. Run `inspect_cmo3_structure.mjs`.
4. Confirm Warp/Rotation Deformer and KeyformBinding counts increased.
5. Capture parameter extreme screenshots.
6. Update `cubism_mvp_rig_validation.json`.
7. Extract repeated patterns into a rig template.
8. Decide whether to implement:
   - Cubism checklist/template helper
   - Stretchy-style CMO3 writer spike
   - Mini Rigger prototype
```

## Do Not Do

- Do not delete evidence JSON, QA reports, review JSON, generated manifests, or
  Cubism export bundles.
- Do not treat forced `O` review as final art approval.
- Do not mark the project complete until deformer/keyform/draw-order/overhang
  evidence exists.
- Do not claim Mini Cubism is the best path until a small prototype passes the
  gates in `MINI-CUBISM-OSS-RESEARCH.md`.


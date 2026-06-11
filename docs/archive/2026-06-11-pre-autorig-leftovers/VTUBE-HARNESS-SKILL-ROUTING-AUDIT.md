# Vtube Harness And Skill Routing Audit

Updated: 2026-06-06

## Current Default

Use these for the next production-oriented Cubism work:

```text
vtube-cubism-success-pattern-workflow
vtube-cubism-success-pattern-spec
vtube-reference-model-structure
vtube-custom-parts-validation
```

## Keep As Current

`vtube-reference-model-structure`

```text
Role: official sample/profile/catalog analyzer.
Reason: source of the 57-report combined baseline and Cubism success pattern spec.
Action: keep.
```

`vtube-cubism-success-pattern-spec`

```text
Role: current Cubism-first model planning and validation gate.
Reason: prevents defaulting back to imagen-live2d-001 or 2048-only assumptions.
Action: keep as current default.
```

`vtube-custom-parts-validation`

```text
Role: PSD/material pack and visual QA support.
Reason: still useful, but 2048 is no longer mandatory.
Action: keep with updated trigger.
```

## Keep As Fixture Or Support Only

`vtube-imagen-cubism-mvp`

```text
Role: legacy import/runtime smoke and shallow-rig failure fixture.
Risk: name and trigger can pull agents back into imagen-live2d-001.
Action: status changed to legacy-fixture; do not use as next-model default.
```

`vtube-imagen-cubism-mvp-success-pattern`

```text
Role: legacy skill for explicitly requested imagen-live2d-001 work.
Risk: “success-pattern” name is misleading.
Action: trigger narrowed; new work should use vtube-cubism-success-pattern-workflow.
```

`vtube-mini-cubism-*`

```text
Role: local preview, taxonomy, physics, and QA references.
Risk: local validation may be mistaken for Cubism CMO3/MOC3 production proof.
Action: keep, but route production model planning through Cubism success-pattern spec.
```

`vtube-comfyui-seethrough-mac`

```text
Role: blocked/failure evidence and MPS lessons.
Risk: direct Mac See-through path may be retried as if it were current.
Action: keep only as failure/compatibility record.
```

## Do Not Use As Default

```text
imagen-live2d-001 reruns
2048-only image generation
Mini Cubism local preview as production proof
visual-fail face/hair experiments as model baselines
```

## Next Routing Rule

If a task asks “what next for my Vtube model,” use:

```text
1. docs/status/PROJECT-STATUS.md
2. docs/ref/CUBISM-V2-SUCCESS-PATTERN-PLAN.md
3. experiments/reference-model-structure-001/reports/cubism_success_pattern_spec.md
4. vtube-cubism-success-pattern-workflow skill
5. vtube-cubism-success-pattern-spec harness
```

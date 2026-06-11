# Goal Draft: Mini Cubism Dedicated Model v1

```text
/goal Mini Cubism Dedicated Model v1을 만든다. 목표는 기존 v0.3 엔진 검증 모델을 보존한 채, physics-first 파츠 설계에 맞는 새 canonical 이미지를 생성하고, 60개 이상 파츠로 분해/검수/정규화하여 Mini Cubism local rig + physics preview까지 재현 가능한 pipeline evidence를 만드는 것이다.

검증:
- python3 scripts/validate_mini_cubism_dedicated_part_spec.py
- canonical image candidate exists under /Users/family/jason/Vtube/experiments/mini-cubism-dedicated-model-v1-001/canonical/
- generated/decomposed part manifest maps to /Users/family/jason/Vtube/experiments/mini-cubism-dedicated-model-v1-001/part_spec_manifest.json
- part_count >= 60, hair_parts >= 18, eye_parts >= 16, mouth_parts >= 8, physics_targets >= 12
- Mini Cubism project validator PASS
- motion sweep and physics scoring PASS
- review_packet/contact_sheet.png, best_motion.gif, review_summary.md generated
- status/evidence docs and shared harness updated

성공 기준:
- 새 canonical image is front-facing, not cropped, no labels/text, physics-friendly silhouette.
- mouth closed/half/open keypose layers are present and exclusive.
- eye open/half/closed keypose hides iris/pupil/catchlight when closed.
- at least 6 physics profiles are active, with at least 12 targets.
- spring profiles settle within 40 frames.
- 주인님 review only requires contact sheet/GIF choices.

제약:
- Do not overwrite mini-cubism-v0-001, mini-cubism-auto-authoring-001, or mini-cubism-physics-v0-3-001.
- Do not modify imagen-live2d-001 CMO3/MOC3 bundles.
- Do not delete evidence JSON, QA reports, generated manifests, or manual review JSON.
- Glue remains unimplemented until CGlueSource fixture evidence exists.
- Stretchy Studio is reference only; do not copy UI, architecture, or save format.

반복 정책:
- Change one hypothesis at a time: canonical prompt, decomposition, part mapping, keypose art, physics profile, scoring.
- Preserve each candidate under a candidate subfolder.
- If image generation is rate-limited, keep the prompt and mark blocked instead of inventing evidence.
```
```

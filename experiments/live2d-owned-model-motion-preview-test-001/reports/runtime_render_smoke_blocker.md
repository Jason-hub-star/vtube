# Live2D Runtime Render Smoke Blocker

Status: `BLOCKED_CORE_MISSING`

The official Cubism Web TypeScript demo was started from:

```text
experiments/reference-model-structure-001/official_github_samples/repos/live2d_cubism_web_samples/Samples/TypeScript/Demo
```

Observed local URL:

```text
http://127.0.0.1:5001/
```

Observed blocker:

```text
GET /Core/live2dcubismcore.js 404
ReferenceError: Live2DCubismCore is not defined
```

Interpretation:

- The official sample resources and framework source are present.
- The Cubism Core redistributable file is not present in this checkout.
- Actual browser rendering/GIF motion proof is blocked until `Core/live2dcubismcore.js` is provided from the official Cubism SDK/Core redistributable package.
- File-level runtime readiness still passed for the 8 web sample models in `live2d_model_motion_view_test.md`.

Current file-level result:

```text
tested_models: 8
runtime_motion_pass: 8
view_pass: 5
view_warn: 3
view_fail: 0
```

View warning models:

```text
Mao
Ren
Wanko
```

These warnings mean texture alpha touches the atlas edge, so actual Cubism rendering should be visually checked before declaring "no clipping".

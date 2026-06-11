# Mini Cubism Material Open Smoke

Status: `PASS_MINI_CUBISM_MATERIAL_OPEN_SMOKE`

URL: `http://127.0.0.1:8063/`

## Result

The Cubism v2 material pack was converted into a local Mini Cubism preview project and opened successfully.

Counts:

- Parts: 62
- Meshes: 62
- Deformers: 11
- Parameters: 15
- Keyform bindings: 22
- Physics profiles: 3

Browser smoke confirmed:

- project loaded,
- 2048x2048 canvas rendered,
- sampled model bbox was non-empty: `[612, 356, 836, 1388]`,
- `ParamAngleX`, `ParamMouthOpenY`, and `ParamHairFront` values updated through the Mini Cubism automation API.

Screenshot:

`/Users/family/jason/Vtube/experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_v0/reports/mini_cubism_material_preview.png`

## Meaning

This is the correct local preview smoke for 주인님's Mini Cubism. It checks whether our own preview system can load the material pack as a structured project.

It is separate from the real Cubism Editor import smoke:

- Cubism Editor smoke checks PSD compatibility and layer import.
- Mini Cubism smoke checks our local preview project, simple deformer/keyform response, draw order, and QA visibility.

Neither one alone proves final rigging. Real production success still requires Cubism ArtMesh, Warp/Rotation Deformer, KeyformBinding authoring, CMO3 inspector comparison, and runtime export smoke.

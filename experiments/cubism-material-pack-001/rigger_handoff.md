# Cubism Rigger Handoff

Date: 2026-06-03

## Goal

Import `import_ready_candidate.psd` into Live2D Cubism Editor and verify whether it can be promoted to `import_ready.psd`.

## Files

- `import_ready_candidate.psd`: Python-generated PSD candidate. Do not trust until Cubism import smoke passes.
- `production_layers/`: PNG fallback layers for manual PSD assembly in Photoshop, Clip Studio Paint, or Krita.
- `reference_pack/mouth/`: mouth key-pose references for `ParamMouthOpenY` and `ParamMouthForm`.
- `reference_pack/blink/`: blink key-pose references for `ParamEyeLOpen` and `ParamEyeROpen`.
- `layer_manifest.json`: layer roles, draw order, bbox, and `include_in_import_psd` flags.
- `param_map.json`: key-pose mapping.

## Cubism Checklist

1. Open `import_ready_candidate.psd` in Cubism Editor.
2. Confirm layers are visible as separate parts, not flattened.
3. Confirm only production layers are imported; mouth/blink references must stay outside the PSD.
4. Run automatic mesh generation for broad parts.
5. Manually mesh mouth, eyelashes, brows, and deform-heavy eye parts.
6. Create Deformer hierarchy for face, eyes, mouth, hair, and body.
7. Key `ParamEyeLOpen`, `ParamEyeROpen`, `ParamMouthOpenY`, and `ParamMouthForm` using `reference_pack/`.
8. Edit texture atlas.
9. Export `.moc3`, `.model3.json`, textures, and optional `.physics3.json` from Cubism Editor.

## Smoke Evidence

After testing in Cubism Editor, create `reports/cubism_import_smoke.json`:

```json
{
  "cubism_import_success": true,
  "layers_flattened": false,
  "reviewer": "name",
  "notes": "Layer list visible in Cubism Editor."
}
```

Then rerun:

```bash
python3 /Users/family/jason/Vtube/scripts/validate_cubism_psd_inputs.py --pack /Users/family/jason/Vtube/experiments/cubism-material-pack-001
```

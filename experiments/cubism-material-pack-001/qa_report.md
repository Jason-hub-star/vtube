# cubism-material-pack-001 QA Report

Date: 2026-06-04
Status: PASS_WITH_CUBISM_IMPORT

## Checks

- `manifest_schema`: PASS
- `duplicate_layer_names`: PASS
- `required_production_roles`: PASS
- `reference_layers_excluded_from_import_psd`: PASS
- `psd_metadata`: PASS
- `cubism_import_smoke`: PASS

## PSD Metadata

```json
{
  "exists": true,
  "valid_header": true,
  "channels": 3,
  "width": 2048,
  "height": 2048,
  "depth": 8,
  "color_mode": "RGB",
  "layer_mask_section_length": 18001292,
  "layer_count": 27
}
```

## PSD Writer

```json
{
  "date": "2026-06-03",
  "writer": "psd-tools"
}
```

## Cubism Import Gate

Cubism Editor actual import passed, and `import_ready.psd` may be used for the next Cubism rigging step.

Record manual smoke evidence in `reports/cubism_import_smoke.json` with:

```json
{
  "cubism_import_success": true,
  "layers_flattened": false,
  "reviewer": "name",
  "notes": "Layer list visible in Cubism Editor."
}
```

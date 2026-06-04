# Cubism Material Pack 001

Date: 2026-06-03

## Goal

Create a Live2D/Cubism import material pack that separates production PSD layers from mouth/blink reference evidence.

## Outputs

- `import_ready_candidate.psd`
- `production_layers/*.png`
- `reference_pack/mouth/*.png`
- `reference_pack/blink/*.png`
- `layer_manifest.json`
- `param_map.json`
- `qa_report.md`
- `rigger_handoff.md`
- `reports/validation_report.json`

## Current Verdict

`PASS_WITH_CUBISM_IMPORT`.

Automatic checks pass, and the psd-tools generated PSD has been opened by Live2D Cubism Editor 5.3. The smoke evidence is recorded in `reports/cubism_import_smoke.json`, and `import_ready_candidate.psd` has been promoted to `import_ready.psd`.

Important history:

- The first raw-minimal Python PSD writer failed Cubism parsing with `error signature @ 0x00000026`.
- The accepted writer is `psd-tools`; keep `requirements-cubism-psd.txt` installed for repeatable PSD generation.

## Repeat

```bash
python3 /Users/family/jason/Vtube/scripts/build_cubism_material_pack.py --character-id vtube_001
python3 /Users/family/jason/Vtube/scripts/validate_cubism_psd_inputs.py --pack /Users/family/jason/Vtube/experiments/cubism-material-pack-001
python3 /Users/family/jason/Vtube/scripts/export_rigger_handoff.py --pack /Users/family/jason/Vtube/experiments/cubism-material-pack-001
```

Install PSD writer dependency if needed:

```bash
python3 -m pip install -r /Users/family/jason/Vtube/requirements-cubism-psd.txt
```

## Cubism Smoke Gate

Smoke evidence is stored at:

```text
reports/cubism_import_smoke.json
```

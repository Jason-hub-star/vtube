# Reference Model Structure 001

## Purpose

Build a catalog-first analyzer for public Live2D reference models without
copying another model's image assets, texture atlas, PSD layers, or art style.

The output is a structure table and recommendation summary for Vtube rigging
research:

```text
official_sample_profiles.json
catalog.official_samples.json
catalog.official_github_samples.json
catalog.official_combined.json
-> scripts/analyze_reference_model_catalog.py
-> models/<id>/reference_model_report.json
-> reports/reference_model_structure_summary.json
-> reports/reference_rig_pattern_baseline.md
-> reports/cubism_success_pattern_spec.md
```

## Safety Policy

Public model candidates can be recorded broadly, but local structure analysis is
allowed only when provenance and license are clear.

Analysis modes:

```text
FULL_STRUCTURE:
  Safe official, OSS, owned, or explicitly permitted local model files.

RUNTIME_ONLY:
  Safe runtime bundle only. Analyze .moc3 and runtime JSON, not editable source.

METADATA_ONLY:
  Public but unclear, unverified, or suspected reupload. Record URL and notes
  only. Do not download or inspect local assets.
```

## Commands

From `/Users/family/jason/Vtube`:

Prepare the official sample inventory and generated catalog from the 24
user-provided Live2D sample zips:

```bash
python3 scripts/prepare_official_live2d_samples.py
```

Build concise official learning profiles from the Live2D sample page metadata:

```bash
python3 scripts/build_live2d_official_sample_profiles.py \
  --zip-manifest experiments/reference-model-structure-001/official_samples/download_manifest.json \
  --out-dir experiments/reference-model-structure-001/reports
```

Analyze the official sample catalog with the dedicated `py-moc3` venv:

```bash
.venv-reference-models/bin/python scripts/analyze_reference_model_catalog.py \
  --catalog experiments/reference-model-structure-001/catalog.official_samples.json \
  --out experiments/reference-model-structure-001
```

Build the rig pattern baseline used for new image requirements:

```bash
.venv-reference-models/bin/python scripts/build_reference_rig_pattern_baseline.py \
  --profiles experiments/reference-model-structure-001/reports/official_sample_profiles.json \
  --summary experiments/reference-model-structure-001/reports/reference_model_structure_summary.json \
  --models-dir experiments/reference-model-structure-001/models \
  --out-dir experiments/reference-model-structure-001/reports
```

Fetch official GitHub SDK/Garage runtime samples and build the combined catalog:

```bash
python3 scripts/prepare_official_live2d_github_samples.py
```

Analyze the combined official catalog into a separate output tree:

```bash
.venv-reference-models/bin/python scripts/analyze_reference_model_catalog.py \
  --catalog experiments/reference-model-structure-001/catalog.official_combined.json \
  --out experiments/reference-model-structure-001/official_combined_analysis
```

Build the combined baseline and Cubism-first success pattern spec:

```bash
.venv-reference-models/bin/python scripts/build_reference_rig_pattern_baseline.py \
  --profiles experiments/reference-model-structure-001/reports/official_sample_profiles.json \
  --summary experiments/reference-model-structure-001/official_combined_analysis/reports/reference_model_structure_summary.json \
  --models-dir experiments/reference-model-structure-001/official_combined_analysis/models \
  --out-dir experiments/reference-model-structure-001/official_combined_analysis/reports

cp experiments/reference-model-structure-001/official_combined_analysis/reports/reference_model_structure_summary.json \
  experiments/reference-model-structure-001/reports/reference_model_structure_summary.combined.json
cp experiments/reference-model-structure-001/official_combined_analysis/reports/reference_rig_pattern_baseline.json \
  experiments/reference-model-structure-001/reports/reference_rig_pattern_baseline.combined.json

.venv-reference-models/bin/python scripts/build_cubism_success_pattern_spec.py \
  --summary experiments/reference-model-structure-001/reports/reference_model_structure_summary.combined.json \
  --baseline experiments/reference-model-structure-001/reports/reference_rig_pattern_baseline.combined.json \
  --out-dir experiments/reference-model-structure-001/reports
```

Seed/local regression catalog:

```bash
python3 scripts/analyze_reference_model_catalog.py \
  --catalog experiments/reference-model-structure-001/catalog.json \
  --out experiments/reference-model-structure-001
```

Optional dry shape check without invoking the CMO3 inspector:

```bash
python3 scripts/analyze_reference_model_catalog.py \
  --catalog experiments/reference-model-structure-001/catalog.json \
  --out experiments/reference-model-structure-001 \
  --skip-cmo3-inspector
```

## Expected Evidence

```text
experiments/reference-model-structure-001/official_samples/download_manifest.json
experiments/reference-model-structure-001/catalog.official_samples.json
experiments/reference-model-structure-001/reports/official_sample_profiles.json
experiments/reference-model-structure-001/reports/official_sample_profiles.md
experiments/reference-model-structure-001/catalog.json
experiments/reference-model-structure-001/models/local_cmo3_positive_fixture/reference_model_report.json
experiments/reference-model-structure-001/models/local_imagen_live2d_001/reference_model_report.json
experiments/reference-model-structure-001/reports/reference_model_structure_summary.json
experiments/reference-model-structure-001/reports/reference_model_structure_summary.md
experiments/reference-model-structure-001/reports/reference_rig_pattern_baseline.json
experiments/reference-model-structure-001/reports/reference_rig_pattern_baseline.md
experiments/reference-model-structure-001/official_github_samples/github_sample_manifest.json
experiments/reference-model-structure-001/catalog.official_github_samples.json
experiments/reference-model-structure-001/catalog.official_combined.json
experiments/reference-model-structure-001/reports/reference_model_structure_summary.combined.json
experiments/reference-model-structure-001/reports/reference_model_structure_summary.combined.md
experiments/reference-model-structure-001/reports/reference_rig_pattern_baseline.combined.json
experiments/reference-model-structure-001/reports/reference_rig_pattern_baseline.combined.md
experiments/reference-model-structure-001/reports/cubism_success_pattern_spec.json
experiments/reference-model-structure-001/reports/cubism_success_pattern_spec.md
```

Latest official sample run:

```text
zip_count: 24
cmo3: 34
moc3: 28
model3_json: 28
physics3_json: 22
motion3_json: 252
cdi3_json: 28
exp3_json: 64
pose3_json: 14
psd: 8
model_reports: 38
FULL_STRUCTURE: 34
RUNTIME_ONLY: 4
py_moc3_status PASS: 31
required baseline sections: eye, mouth, hair, body_angle
```

Latest official GitHub runtime sample run:

```text
repos: 5
ready_repos: 5
moc3: 19
model3_json: 19
physics3_json: 19
motion3_json: 168
cdi3_json: 19
exp3_json: 64
pose3_json: 8
github_model_reports: 19
combined_model_reports: 57
combined_FULL_STRUCTURE: 34
combined_RUNTIME_ONLY: 23
combined_py_moc3_status_PASS: 50
```

Cubism success pattern spec anchors the next model on structure first:

```text
minimum gate:
  art_meshes >= 20
  parameters >= 15
  warp_deformers >= 8
  rotation_deformers >= 1
  keyform_bindings >= 20
standard target:
  warp_deformers 25-60
  keyform_bindings 90-250
```

## Interpretation

- `KEEP` means useful as a rig structure reference.
- `REFERENCE_ONLY` means useful for naming, runtime JSON shape, or gap analysis.
- `IGNORE` means do not use for implementation until license/provenance improves.
- This evidence is structural only. It does not prove visual rig quality.

# Imagen Live2D 001

Imagen으로 생성한 새 정면 캐릭터를 Live2D/Cubism production material pack까지 밀어보기 위한 실험이다.

## Source

```text
experiments/imagen-live2d-001/raw/imagen_source.png
```

## Canonical

```text
canonical/canonical_front_2048.png
input/canonical_front_mps_512.png
input/canonical_front_mps_640.png
input/canonical_front_mps_768.png
```

## Pipeline

```bash
python3 scripts/run_mps_compat_matrix.py --experiment-id imagen-live2d-001 --case mps_512_safe
python3 scripts/run_mps_compat_matrix.py --experiment-id imagen-live2d-001 --case mps_640_safe
python3 scripts/build_mps_candidate_review_sheet.py --experiment-id imagen-live2d-001
python3 scripts/build_review_manifest.py --experiment-id imagen-live2d-001
python3 scripts/validate_review_app.py
```

Only `O` production candidates may enter `import_ready_candidate.psd`.
Cubism Editor actual import smoke is still required before promotion to `import_ready.psd`.

# See-through MPS Compatibility 002

목표는 Apple Silicon에서 See-through 계열 decomposition이 production 품질로 충분한지 보는 것이 아니라,
저해상도 안전 매트릭스에서 `*_layers.json`이 실제로 생성되는지 확인하는 것이다.

## 입력

원본 기준:

```text
experiments/see-through-layer-decomp-001/input/canonical_front_1280.png
```

working copy:

```text
input/canonical_front_mps_512.png
input/canonical_front_mps_640.png
input/canonical_front_mps_768.png
```

## 실행

ComfyUI-See-through 서버를 먼저 실행한 뒤:

```bash
python3 scripts/run_mps_compat_matrix.py --case mps_512_safe
```

현재 512 실제 실행은 `FAIL_MPS_UNSUPPORTED_SORT_AXIS_512`로 실패했다.
`layerdiffuse/vae.py:232`의 MPS median/sort path patch 전에는 640/768로 확장하지 않는다.

512가 `*_layers.json`을 만들면 640, 그 다음 768을 실행한다.

```bash
python3 scripts/run_mps_compat_matrix.py --case mps_640_safe
python3 scripts/run_mps_compat_matrix.py --case mps_768_safe
```

## 판정

- 최소 성공: 512 또는 640에서 `*_layers.json` 생성
- 실용 성공: review app에서 hair/face/eye/mouth 계열 5개 이상이 `O` 또는 `REVISE`
- 실패: 512에서도 출력 없음, 또는 전부 semantic contamination이 심함

`mps_512_high_watermark_manual`은 마지막 수동 실험이다. 기본 실행에서 제외한다.

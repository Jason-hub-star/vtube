# Mac Layer Decomposition Options

이 문서는 Apple Silicon Mac에서 See-through와 유사한 “단일 캐릭터 이미지 -> 레이어 후보”
작업을 어떻게 다룰지 정리한다. 결론부터 말하면, 2026-06-04 현재 확인된 범위에서는
**See-through 공식 Mac 전용 버전은 없다.** Mac에서 가능한 경로는 ComfyUI MPS 위에서
저해상도 compatibility smoke를 하는 것이다.

## Decision

```text
Mac Apple Silicon:
  low-resolution smoke, review app, normalization, PSD gate

CUDA / cloud / external service:
  high-quality layer decomposition inference
```

Mac 경로의 목표는 production 품질이 아니라 `*_layers.json`이 나오는지 확인하는 것이다.
출력 레이어가 생겨도 Live2D production 성공으로 보지 않고, 반드시 part purity review에서
`O/X/REVISE/REFERENCE_ONLY`를 받는다.

## Option Matrix

| Tool | Mac 가능성 | 출력 | Live2D production 평가 | Reference-only 평가 | Discard 조건 |
| --- | --- | --- | --- | --- | --- |
| See-through official | 낮음 | layered PSD, depth, masks | CUDA 기준. Mac production path 아님 | 알고리즘/레이어명/후처리 기준 참고 | Mac 512에서도 output 없음 |
| ComfyUI-See-through | 중간 | PNG layers + metadata + browser PSD | MPS smoke 통과 후에도 바로 production 금지 | 가장 중요한 Mac compatibility 후보 | MPS memory/unsupported op로 반복 실패 |
| ComfyUI-LayerDivider | 중간-높음 | 색/segment 기반 PSD/layers | 숨은 부분 복원 없음. production은 제한적 | 파츠 mask 초안/색 영역 참고 | hair/skin/eye contamination이 심함 |
| Qwen Layers ComfyUI | 낮음-중간 | RGBA layers, PSD/TIFF/PNG | 모델이 크고 Mac 성능 리스크 큼 | object/element 분해 비교 후보 | 모델 로드 실패 또는 semantic layer가 너무 조악함 |
| VTuber2D.AI | 높음, 외부 서비스 | Live2D workflow용 layered PSD 목표 | 로컬 파이프라인은 아님. 라이선스/반복 비용 확인 전 production 금지 | See-through 기반 cloud reference 비교 | 서비스 접근/비용/권리 조건 불명확 |
| Anime-layer-decomposition research | 미정 | line/flat/shadow/highlight | Live2D body-part 파츠가 아니라 채색 production layer 쪽 | 스타일/채색 분해 연구 참고 | 코드/모델이 Mac 실행 불가 또는 목적 불일치 |

## Source Notes

- See-through official repo says the main pipeline exports semantic layered PSD plus depth/masks, and notes that it is not a full Image-to-Live2D pipeline because Live2D still needs finer artistic decomposition and rigging.
- See-through low-VRAM guidance is NVIDIA VRAM oriented: 1280 default is roughly 12-16GB VRAM, 8GB path uses NF4/group offload. This does not prove Apple MPS viability.
- ComfyUI-See-through documents MPS-agnostic ComfyUI nodes, browser PSD export, depth output, and low-VRAM controls such as lower resolution, depth resolution, and group offload.
- ComfyUI Desktop macOS supports Apple Silicon and recommends MPS, but that is ComfyUI platform support, not proof that every custom node/model is stable on MPS.
- PyTorch MPS supports Apple Silicon through the `mps` device, but each model still needs compatibility and memory testing.

References:

```text
https://github.com/shitagaki-lab/see-through
https://github.com/jtydhr88/ComfyUI-See-through
https://github.com/jtydhr88/ComfyUI-LayerDivider
https://github.com/EricRollei/Qwen_Layers_Diffuser_Pipeline_Comfyui
https://docs.comfy.org/installation/desktop/macos
https://huggingface.co/docs/diffusers/optimization/mps
https://vtuber2d.ai/
https://arxiv.org/abs/2603.14925
```

## Mac MPS Compatibility Track

Experiment:

```text
experiments/see-through-mps-compat-002/
```

Input source:

```text
experiments/see-through-layer-decomp-001/input/canonical_front_1280.png
```

Working copies:

```text
input/canonical_front_mps_512.png
input/canonical_front_mps_640.png
input/canonical_front_mps_768.png
```

Current evidence:

```text
experiments/see-through-mps-compat-002/reports/mps_512_safe_actual_failure_report.json
```

Result: pre-patch `mps_512_safe` loaded both See-through models and entered `GenerateLayers`, but
aborted before writing `*_layers.json` because MPS does not support the 5D sort/median path used by
`layerdiffuse/vae.py:232`. After applying `scripts/patch_comfyui_seethrough_mps.py`, the same
512 case produced `*_layers.json`, 29 raw layers, and 29 normalized 2048 review candidates.

Run matrix:

| Case | Resolution | Steps | Depth resolution | MPS env | Gate |
| --- | ---: | ---: | ---: | --- | --- |
| `mps_512_safe` | 512 | 8 | 384 | fallback=1, low=0.85, high=1.20 | minimum output smoke |
| `mps_640_safe` | 640 | 12 | 512 | fallback=1, low=0.90, high=1.30 | practical smoke |
| `mps_768_safe` | 768 | 16 | 512 | fallback=1, low=0.95, high=1.40 | quality probe |
| `mps_512_high_watermark_manual` | 512 | 8 | 384 | fallback=1, low=0.00, high=0.00 | manual-only dangerous last resort |

`PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0` disables the hard allocator limit and may destabilize
the Mac under system-wide OOM. It is never part of the default automated run.

## Patch Candidates For Mac

These are research tasks, not v1 production requirements:

1. Detect MPS and avoid CUDA-only assumptions.
2. Lower depth resolution by default on MPS.
3. Done in `scripts/patch_comfyui_seethrough_mps.py`: in `layerdiffuse/vae.py:232`, bypass `torch.median(result, dim=0)` when only one augmentation tensor exists.
4. Done in `scripts/patch_comfyui_seethrough_mps.py`: on MPS, move the augmented median calculation to CPU and move the result back to the original device.
5. Allow depth model and LayerDiff model to unload between stages.
6. Add `torch.mps.empty_cache()` between model load, layer generation, depth generation, and post-process.
7. Make `use_lama=false` available for the first smoke if LaMa/inpaint is the failing stage.
8. Record node/stage failures into `reports/*_inference_report.json`.

## Acceptance

Minimum success:

```text
512 or 640 run produces *_layers.json
```

Current minimum status:

```text
PASS_MPS_512_LAYERS
```

Practical success:

```text
review app shows candidates, and at least 5 hair/face/eye/mouth candidates are O or REVISE
```

Failure:

```text
512 produces no *_layers.json, or all candidates are too contaminated for review
```

If failure is reached, mark the Mac See-through path as `RESEARCH_ONLY` and keep the production
pipeline focused on mask-based cleanup/inpaint plus human review.

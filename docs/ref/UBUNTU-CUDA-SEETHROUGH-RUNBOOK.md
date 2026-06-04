# Ubuntu CUDA See-through Runbook

이 문서는 `see-through-layer-decomp-001`을 Ubuntu + NVIDIA CUDA 환경에서 실행하기 위한
작업 절차다. Mac Apple Silicon에서는 ComfyUI와 노드 로드는 성공했지만, 실제
`GenerateLayers` 단계에서 MPS 메모리 한계로 `*_layers.json` 생성에 실패했다. 따라서
See-through 실제 layer decomposition은 Ubuntu CUDA에서 실행하고, 결과물 검수/PSD gate는
Mac Vtube 프로젝트에서 계속한다.

## Current Decision

```text
Mac:
  review_app, manifest, normalization, PSD gate, Cubism handoff

Ubuntu CUDA:
  ComfyUI-See-through model download and actual layer decomposition
```

Mac evidence:

| Gate | Status | Evidence |
| --- | --- | --- |
| ComfyUI server + MPS | PASS_SETUP | `experiments/see-through-layer-decomp-001/reports/comfyui_setup_report.json` |
| See-through nodes | PASS_SETUP | 6 nodes loaded |
| 1280 inference | FAIL_MPS_MEMORY_1280 | `reports/comfyui_mps_crash_report.json` |
| layer output | MISSING | no `*_layers.json` yet |

## Recommended Ubuntu Machine

Minimum practical target:

```text
OS: Ubuntu 22.04 or 24.04
GPU: NVIDIA RTX 4090 / RTX 3090 / L4 / A10G or better
VRAM: 24GB minimum, 48GB+ preferred
RAM: 32GB minimum
Disk: 60GB+ free
Python: 3.11 or 3.12
CUDA PyTorch: required
```

Avoid for first run:

```text
T4 16GB unless using very low resolution
Apple Silicon MPS as production inference path
CPU-only
```

## Files To Copy To Ubuntu

Copy the Vtube project or at minimum these files:

```text
/Users/family/jason/Vtube/
  scripts/run_comfyui_seethrough_prompt.py
  scripts/normalize_seethrough_outputs.py
  experiments/see-through-layer-decomp-001/input/canonical_front_1280.png
  experiments/see-through-layer-decomp-001/input/canonical_front_2048.png
  experiments/see-through-layer-decomp-001/workflow/seethrough-basic-vtube.json
  experiments/validation-smoke-001/external_repos/ComfyUI-See-through/
```

Preferred remote layout:

```text
~/Vtube/
```

## Ubuntu Setup

Install base packages:

```bash
sudo apt update
sudo apt install -y git python3.11 python3.11-venv python3-pip curl
```

Clone ComfyUI if it is not already present:

```bash
cd ~/Vtube/experiments/see-through-layer-decomp-001
mkdir -p external_repos
cd external_repos
git clone https://github.com/comfyanonymous/ComfyUI.git
```

Install the See-through custom node:

```bash
cd ~/Vtube/experiments/see-through-layer-decomp-001/external_repos/ComfyUI/custom_nodes
ln -s ~/Vtube/experiments/validation-smoke-001/external_repos/ComfyUI-See-through ComfyUI-See-through
```

Create venv:

```bash
cd ~/Vtube/experiments/see-through-layer-decomp-001
python3.11 -m venv .venv-comfyui-cuda
source .venv-comfyui-cuda/bin/activate
python -m pip install --upgrade pip
```

Install PyTorch CUDA. Pick the CUDA wheel that matches the machine. For most current cloud images:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
```

Install ComfyUI and See-through dependencies:

```bash
pip install -r external_repos/ComfyUI/requirements.txt
pip install -r external_repos/ComfyUI/custom_nodes/ComfyUI-See-through/requirements.txt
```

If `bitsandbytes` fails on the first baseline setup, remove it only for the non-NF4 baseline:

```bash
grep -v '^bitsandbytes' external_repos/ComfyUI/custom_nodes/ComfyUI-See-through/requirements.txt > requirements-seethrough-cuda-baseline.txt
pip install -r requirements-seethrough-cuda-baseline.txt
```

## Input Placement

Put the prepared 1280 input into ComfyUI input:

```bash
mkdir -p ~/Vtube/experiments/see-through-layer-decomp-001/external_repos/ComfyUI/input
cp ~/Vtube/experiments/see-through-layer-decomp-001/input/canonical_front_1280.png \
  ~/Vtube/experiments/see-through-layer-decomp-001/external_repos/ComfyUI/input/
```

## Server Smoke

Start ComfyUI:

```bash
cd ~/Vtube
experiments/see-through-layer-decomp-001/.venv-comfyui-cuda/bin/python \
  experiments/see-through-layer-decomp-001/external_repos/ComfyUI/main.py \
  --listen 0.0.0.0 --port 8188
```

Expected log:

```text
Device: cuda
ComfyUI-See-through Loaded 6 nodes
To see the GUI go to: http://0.0.0.0:8188
```

Do not proceed if the device is CPU or MPS.

## First Inference

Use the already scripted API runner from another shell:

```bash
cd ~/Vtube
python3 scripts/run_comfyui_seethrough_prompt.py \
  --base-url http://127.0.0.1:8188 \
  --timeout 7200 \
  --poll-interval 15 \
  --resolution 1280 \
  --steps 30 \
  --depth-resolution 720 \
  --filename-prefix white_wolf_goth_seethrough_cuda_1280
```

Expected output:

```text
experiments/see-through-layer-decomp-001/external_repos/ComfyUI/output/
  white_wolf_goth_seethrough_cuda_1280_*_layers.json
  white_wolf_goth_seethrough_cuda_1280_*.png
```

If 1280 fails due VRAM:

```bash
python3 scripts/run_comfyui_seethrough_prompt.py \
  --base-url http://127.0.0.1:8188 \
  --timeout 7200 \
  --poll-interval 15 \
  --resolution 1024 \
  --steps 20 \
  --depth-resolution 512 \
  --filename-prefix white_wolf_goth_seethrough_cuda_1024
```

If 1024 fails, use `quant_mode=nf4` and/or `group_offload=true` only as a second CUDA experiment,
not as the first baseline. Record it as a separate report.

## Copy Results Back To Mac

From Mac:

```bash
rsync -av ubuntu-host:~/Vtube/experiments/see-through-layer-decomp-001/external_repos/ComfyUI/output/ \
  /Users/family/jason/Vtube/experiments/see-through-layer-decomp-001/raw_comfyui_output/
```

At minimum, copy:

```text
*_layers.json
all layer PNG referenced by that JSON
depth PNGs if present
```

## Normalize On Mac

Back on Mac:

```bash
cd /Users/family/jason/Vtube
python3 scripts/normalize_seethrough_outputs.py \
  --layers-json experiments/see-through-layer-decomp-001/raw_comfyui_output/<output>_layers.json
python3 scripts/build_review_manifest.py
python3 scripts/review_app_server.py --port 8040
```

Open:

```text
http://127.0.0.1:8040/
```

Review tab:

```text
See-through 후보
```

Use these tags:

```text
semantic_too_coarse: See-through layer is too broad for Live2D parts
depth_order_wrong: front/back or occlusion order is wrong
hair_mixed / skin_mixed / eye_white_mixed / iris_mixed: contamination
```

## PSD Gate On Mac

After human review:

```bash
python3 scripts/build_seethrough_psd_candidate.py
```

Rules:

```text
O + production_candidate=true -> eligible for import_ready_candidate.psd
X / REVISE / REFERENCE_ONLY / unreviewed -> excluded
```

Final acceptance still requires:

```text
Live2D Cubism Editor actual import
layers not flattened
production-only layers visible
reports/cubism_import_smoke.json recorded
```

## Status Labels

Use these labels in reports:

```text
PASS_CUDA_1280
PASS_CUDA_1024
FAIL_CUDA_MEMORY
FAIL_CUDA_DEP
FAIL_OUTPUT_QUALITY
BLOCKED_NO_LAYERS_JSON
PSD_CANDIDATE_PENDING_CUBISM_IMPORT
PASS_WITH_CUBISM_IMPORT
```

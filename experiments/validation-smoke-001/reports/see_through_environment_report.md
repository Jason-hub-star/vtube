# See-through / ComfyUI-See-through Environment Report

작성일: 2026-06-02

## 목적

`canonical_front.png`를 See-through 또는 ComfyUI-See-through로 직접 layer/PSD 분해할 수 있는지 주인님 Mac 환경에서 확인한다.

## 입력

```text
/Users/family/jason/Vtube/experiments/imagegen-limit-test-001/generated/canonical_front.png
```

## 로컬 환경

```text
macOS: 26.3.1 arm64
python3: 3.14.3
uv: available
git: available
node: available
nvidia-smi: not found
torch: 2.11.0
torch.cuda.is_available(): False
torch.backends.mps.is_available(): True
```

## Repo 확보

```text
See-through clone: PASS
ComfyUI-See-through clone: PASS
See-through repo size: 18M
ComfyUI-See-through repo size: 18M
```

## See-through 본체 확인

README 기준 실행 조건:

```text
Python 3.12
PyTorch CUDA 12.8
default pipeline: roughly 12-16 GB VRAM at 1280 resolution
8GB path: quantized or blockswap pipeline
```

로컬 entrypoint 확인:

```bash
python3 inference/scripts/inference_psd.py --help
```

결과:

```text
FAIL: ModuleNotFoundError: No module named 'utils'
```

`PYTHONPATH=common` 보정 후:

```bash
PYTHONPATH=/Users/family/jason/Vtube/experiments/validation-smoke-001/external_repos/see-through/common \
python3 inference/scripts/inference_psd.py --help
```

결과:

```text
FAIL: ModuleNotFoundError: No module named 'diffusers'
```

판정:

```text
See-through 본체는 repo/entrypoint는 확인됨.
현재 시스템 Python에는 필수 dependency가 없음.
더 중요한 차단 조건은 CUDA/NVIDIA 부재다.
Mac MPS 경로가 코드 일부에 보이지만 공식 README의 주 실행 경로는 CUDA 기준이며, canonical 처리 성공은 아직 검증되지 않았다.
```

## ComfyUI-See-through 확인

README 기준:

```text
ComfyUI custom_nodes 아래 설치
pip install -r requirements.txt
ComfyUI workflow에서 SeeThrough nodes 사용
models auto-download from HuggingFace
```

로컬 dependency 확인:

```text
diffusers: MISSING
accelerate: MISSING
transformers: MISSING
psd_tools: MISSING
torch: OK
cv2: OK
sklearn: MISSING
```

문법 컴파일:

```bash
python3 -m py_compile external_repos/ComfyUI-See-through/nodes.py
```

결과:

```text
PASS
```

standalone 실행:

```bash
python3 external_repos/ComfyUI-See-through/nodes.py
```

결과:

```text
FAIL: ModuleNotFoundError: No module named 'folder_paths'
```

판정:

```text
ComfyUI-See-through는 standalone CLI가 아니라 ComfyUI plugin이다.
현재 Vtube 환경에는 ComfyUI runtime이 없으므로 canonical 처리 불가.
ComfyUI 설치 + dependencies + model download + device viability 검증이 별도 Gate로 필요하다.
```

## 최종 Verdict

```text
status: BLOCKED
scope: local Mac direct processing
reason:
  - NVIDIA/CUDA 없음
  - See-through 필수 dependency 미설치
  - ComfyUI runtime 미설치
  - 모델 다운로드와 실제 MPS/CPU 실행 가능성 미검증

decision:
  See-through/ComfyUI-See-through를 현재 6주 MVP의 confirmed core path로 두면 안 된다.
  플랜에서는 RESEARCHED/BLOCKED로 유지하고, optional external baseline 또는 remote GPU validation으로 분리한다.
```

## 다음 검증 옵션

```text
Option A:
  HuggingFace Space 또는 ModelScope demo로 canonical_front를 처리해 PSD/layer output만 확보

Option B:
  NVIDIA GPU 환경 또는 cloud GPU에서 See-through 본체 실행

Option C:
  별도 ComfyUI 환경을 만들고 ComfyUI-See-through workflow를 실행

Option D:
  See-through를 보류하고 현재 imagegen crop/mask + 자체 layer normalizer를 1차 MVP baseline으로 사용
```

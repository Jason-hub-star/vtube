# See-through Layer Decomposition 001

목표: Mac ComfyUI + ComfyUI-See-through로 White Wolf Goth canonical front 1장을 분해하고,
그 결과를 바로 PSD로 믿지 않고 `part purity review`에서 검수한다.

## Commands

```bash
python3 scripts/setup_comfyui_seethrough_mac.py
```

ComfyUI 실행 후 workflow를 열고 한 번 처리한다.

```bash
python3 experiments/see-through-layer-decomp-001/.venv-comfyui/bin/python \
  experiments/see-through-layer-decomp-001/external_repos/ComfyUI/main.py \
  --listen 127.0.0.1 --port 8188
```

생성된 `*_layers.json`을 정규화한다.

```bash
python3 scripts/normalize_seethrough_outputs.py --layers-json /path/to/white_wolf_goth_seethrough_*_layers.json
python3 scripts/build_review_manifest.py
python3 scripts/review_app_server.py --port 8040
```

검수 후 O 파츠만 PSD 후보로 만든다.

```bash
python3 scripts/build_seethrough_psd_candidate.py
```

## Gate

- setup/node-load 성공은 production 성공이 아니다.
- `seethrough__*` 후보는 기본적으로 PSD 제외다.
- 사람이 review app에서 `O`를 준 production candidate만 PSD 후보가 된다.
- `import_ready.psd` 승격은 Cubism Editor 실제 import smoke 후에만 가능하다.

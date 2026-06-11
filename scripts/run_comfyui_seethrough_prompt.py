#!/usr/bin/env python3
"""Queue the Vtube See-through workflow through ComfyUI's HTTP API."""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXP = ROOT / "experiments" / "see-through-layer-decomp-001"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def request_json(url: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def get_text(url: str, timeout: int = 10) -> str:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read().decode("utf-8")


def resolve_repo_path(value: str | None, default: Path) -> Path:
    if not value:
        return default
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def api_prompt(
    *,
    input_image: str,
    resolution: int,
    steps: int,
    depth_resolution: int,
    filename_prefix: str,
    quant_mode: str,
    group_offload: bool,
    use_lama: bool,
    auto_download: bool,
) -> dict[str, Any]:
    return {
        "27": {
            "class_type": "LoadImage",
            "inputs": {"image": input_image},
        },
        "28": {
            "class_type": "SeeThrough_LoadLayerDiffModel",
            "inputs": {
                "model": "layerdifforg/seethroughv0.0.2_layerdiff3d",
                "vae_ckpt": "",
                "unet_ckpt": "",
                "quant_mode": quant_mode,
                "cache_tag_embeds": True,
                "group_offload": group_offload,
                "auto_download": auto_download,
            },
        },
        "29": {
            "class_type": "SeeThrough_LoadDepthModel",
            "inputs": {
                "model": "layerdifforg/seethroughv0.0.1_marigold",
                "quant_mode": quant_mode,
                "cache_tag_embeds": True,
                "group_offload": group_offload,
                "auto_download": auto_download,
            },
        },
        "24": {
            "class_type": "SeeThrough_GenerateLayers",
            "inputs": {
                "image": ["27", 0],
                "layerdiff_model": ["28", 0],
                "seed": 42,
                "resolution": resolution,
                "num_inference_steps": steps,
            },
        },
        "23": {
            "class_type": "SeeThrough_GenerateDepth",
            "inputs": {
                "layers": ["24", 0],
                "depth_model": ["29", 0],
                "seed": 42,
                "resolution_depth": depth_resolution,
            },
        },
        "20": {
            "class_type": "SeeThrough_PostProcess",
            "inputs": {
                "layers_depth": ["23", 0],
                "tblr_split": True,
                "use_lama": use_lama,
            },
        },
        "21": {
            "class_type": "SeeThrough_SavePSD",
            "inputs": {
                "parts": ["20", 0],
                "filename_prefix": filename_prefix,
            },
        },
        "22": {
            "class_type": "PreviewImage",
            "inputs": {"images": ["20", 1]},
        },
    }


def wait_for_server(base_url: str, timeout_seconds: int) -> None:
    deadline = time.time() + timeout_seconds
    last_error = ""
    while time.time() < deadline:
        try:
            get_text(f"{base_url}/", timeout=5)
            return
        except Exception as exc:  # noqa: BLE001
            last_error = repr(exc)
            time.sleep(1)
    raise TimeoutError(f"ComfyUI server not ready: {last_error}")


def latest_layers_json(output_dir: Path, since: float, filename_prefix: str) -> list[str]:
    if not output_dir.exists():
        return []
    found = []
    for path in sorted(output_dir.glob(f"{filename_prefix}_*_layers.json")):
        if path.stat().st_mtime >= since:
            found.append(str(path))
    return found


def run(args: argparse.Namespace) -> dict[str, Any]:
    base = args.base_url.rstrip("/")
    exp = resolve_repo_path(args.experiment_dir, DEFAULT_EXP)
    output_dir = resolve_repo_path(args.output_dir, exp / "external_repos" / "ComfyUI" / "output")
    report_path = resolve_repo_path(args.report_path, exp / "reports" / "comfyui_inference_report.json")
    experiment_id = args.experiment_id or exp.name
    wait_for_server(base, args.server_timeout)
    started = time.time()
    prompt = api_prompt(
        input_image=args.input_image,
        resolution=args.resolution,
        steps=args.steps,
        depth_resolution=args.depth_resolution,
        filename_prefix=args.filename_prefix,
        quant_mode=args.quant_mode,
        group_offload=args.group_offload,
        use_lama=not args.no_lama,
        auto_download=not args.no_auto_download,
    )
    payload = {"prompt": prompt, "client_id": args.client_id}
    response = request_json(f"{base}/prompt", payload=payload, timeout=60)
    prompt_id = response.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"ComfyUI did not return prompt_id: {response}")

    status = "RUNNING"
    history_payload: dict[str, Any] = {}
    error: str | None = None
    consecutive_connection_errors = 0
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        try:
            history = request_json(f"{base}/history/{prompt_id}", timeout=30)
            consecutive_connection_errors = 0
            if prompt_id in history:
                history_payload = history[prompt_id]
                status = "COMPLETED"
                break
        except urllib.error.HTTPError as exc:
            error = f"HTTPError {exc.code}: {exc.read().decode('utf-8', errors='replace')}"
            consecutive_connection_errors = 0
        except Exception as exc:  # noqa: BLE001
            error = repr(exc)
            consecutive_connection_errors += 1
            if consecutive_connection_errors >= args.server_lost_threshold:
                status = "SERVER_LOST"
                break
        time.sleep(args.poll_interval)
    else:
        status = "TIMEOUT"

    layers_json = latest_layers_json(output_dir, started, args.filename_prefix)
    report = {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "generated_at": now(),
        "status": status,
        "base_url": base,
        "prompt_id": prompt_id,
        "started_at_epoch": started,
        "timeout_seconds": args.timeout,
        "poll_interval_seconds": args.poll_interval,
        "response": response,
        "last_error": error,
        "consecutive_connection_errors": consecutive_connection_errors,
        "history": history_payload,
        "layers_json": layers_json,
        "output_dir": str(output_dir),
        "report_path": str(report_path),
        "environment": {
            "PYTORCH_ENABLE_MPS_FALLBACK": os.environ.get("PYTORCH_ENABLE_MPS_FALLBACK"),
            "PYTORCH_MPS_LOW_WATERMARK_RATIO": os.environ.get("PYTORCH_MPS_LOW_WATERMARK_RATIO"),
            "PYTORCH_MPS_HIGH_WATERMARK_RATIO": os.environ.get("PYTORCH_MPS_HIGH_WATERMARK_RATIO"),
        },
        "settings": {
            "input_image": args.input_image,
            "resolution": args.resolution,
            "steps": args.steps,
            "depth_resolution": args.depth_resolution,
            "filename_prefix": args.filename_prefix,
            "quant_mode": args.quant_mode,
            "group_offload": args.group_offload,
            "use_lama": not args.no_lama,
            "auto_download": not args.no_auto_download,
        },
        "prompt": prompt,
    }
    if status == "COMPLETED" and not layers_json:
        report["status"] = "COMPLETED_NO_LAYERS_JSON"
    save_json(report_path, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run See-through workflow through ComfyUI API")
    parser.add_argument("--base-url", default="http://127.0.0.1:8188")
    parser.add_argument("--experiment-id")
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP.relative_to(ROOT)))
    parser.add_argument("--output-dir")
    parser.add_argument("--report-path")
    parser.add_argument("--client-id", default="vtube-see-through-runner")
    parser.add_argument("--timeout", type=int, default=7200)
    parser.add_argument("--server-timeout", type=int, default=180)
    parser.add_argument("--poll-interval", type=int, default=10)
    parser.add_argument("--server-lost-threshold", type=int, default=6)
    parser.add_argument("--input-image", default="canonical_front_1280.png")
    parser.add_argument("--resolution", type=int, default=1280)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--depth-resolution", type=int, default=720)
    parser.add_argument("--filename-prefix", default="white_wolf_goth_seethrough")
    parser.add_argument("--quant-mode", default="none")
    parser.add_argument("--group-offload", action="store_true")
    parser.add_argument("--no-lama", action="store_true")
    parser.add_argument("--no-auto-download", action="store_true")
    args = parser.parse_args()
    report = run(args)
    print(json.dumps({k: report.get(k) for k in ["status", "prompt_id", "layers_json", "last_error"]}, ensure_ascii=False, indent=2))
    return 0 if report["status"] in {"COMPLETED", "COMPLETED_NO_LAYERS_JSON"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

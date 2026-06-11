#!/usr/bin/env python3
"""Generate clean-socket/keypose PNGs with Vertex Imagen edit API."""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACK = (
    ROOT
    / "experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/imagen_input_pack_v1"
)
DEFAULT_OUT = (
    ROOT / "experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/imagen_generated_v1"
)
PROJECT_FALLBACK = "chrome-folio-489112-s9"
MODEL = "imagen-3.0-capability-001"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def run_text(args: list[str]) -> str:
    return subprocess.check_output(args, text=True).strip()


def gcloud_project() -> str:
    try:
        value = run_text(["gcloud", "config", "get-value", "project"])
        return value or PROJECT_FALLBACK
    except Exception:
        return PROJECT_FALLBACK


def access_token() -> str:
    return run_text(["gcloud", "auth", "print-access-token"])


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def edit_mode(asset: dict[str, Any]) -> str:
    if asset["kind"] in {"clean_base", "clean_socket"}:
        return "EDIT_MODE_INPAINT_REMOVAL"
    return "EDIT_MODE_INPAINT_INSERTION"


def compact_prompt(text: str) -> str:
    # Keep the request concise for Imagen while preserving the output contract.
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def request_imagen(
    project: str,
    region: str,
    token: str,
    prompt: str,
    raw_image: Path,
    mask_image: Path,
    mode: str,
    seed: int | None,
) -> dict[str, Any]:
    endpoint = (
        f"https://{region}-aiplatform.googleapis.com/v1/projects/{project}/locations/{region}"
        f"/publishers/google/models/{MODEL}:predict"
    )
    params: dict[str, Any] = {
        "sampleCount": 1,
        "editMode": mode,
        "baseSteps": 35,
        "guidanceScale": 60,
        "language": "en",
        "personGeneration": "allow_adult",
        "safetySetting": "block_only_high",
        "includeRaiReason": True,
        "includeSafetyAttributes": True,
        "outputOptions": {"mimeType": "image/png"},
    }
    if seed is not None:
        params["seed"] = seed
    payload = {
        "instances": [
            {
                "prompt": prompt,
                "referenceImages": [
                    {
                        "referenceType": "REFERENCE_TYPE_RAW",
                        "referenceId": 1,
                        "referenceImage": {"bytesBase64Encoded": b64(raw_image)},
                    },
                    {
                        "referenceType": "REFERENCE_TYPE_MASK",
                        "referenceId": 2,
                        "referenceImage": {"bytesBase64Encoded": b64(mask_image)},
                        "maskImageConfig": {
                            "maskMode": "MASK_MODE_USER_PROVIDED",
                            "dilation": 0.01 if mode != "EDIT_MODE_BGSWAP" else 0.0,
                        },
                    },
                ],
            }
        ],
        "parameters": params,
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=240) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Imagen HTTP {exc.code}: {body}") from exc


def mask_alpha(mask_path: Path) -> Image.Image:
    mask = Image.open(mask_path).convert("L")
    arr = np.asarray(mask, dtype=np.uint8)
    alpha = np.where(arr > 0, 255, 0).astype(np.uint8)
    return Image.fromarray(alpha, "L")


def existing_face_alpha(asset_id: str) -> Image.Image | None:
    candidates = {
        "face_base_clean": ROOT
        / "experiments/cubism-v2-new-character-001/material_pack_v0/production_layers_face_detail_rebuild_v1/11_face_base.png",
    }
    path = candidates.get(asset_id)
    if path and path.exists():
        return Image.open(path).convert("RGBA").getchannel("A")
    return None


def normalize_layer(raw_output: Path, mask_path: Path, asset_id: str, out_path: Path) -> None:
    image = Image.open(raw_output).convert("RGBA")
    alpha = existing_face_alpha(asset_id) or mask_alpha(mask_path)
    if alpha.size != image.size:
        alpha = alpha.resize(image.size, Image.Resampling.NEAREST)
    image.putalpha(alpha)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)


def selected_assets(manifest: dict[str, Any], requested: list[str], limit: int | None) -> list[dict[str, Any]]:
    assets = manifest["assets"]
    if requested:
        wanted = set(requested)
        assets = [row for row in assets if row["asset_id"] in wanted]
    if limit is not None:
        assets = assets[:limit]
    return assets


def run(pack_dir: Path, out_dir: Path, region: str, requested: list[str], limit: int | None, seed: int | None) -> dict[str, Any]:
    manifest = load_json(pack_dir / "imagen_input_pack_manifest.json")
    project = gcloud_project()
    token = access_token()
    raw_image = Path(manifest["references"]["source_2048_rgba"])
    raw_dir = out_dir / "raw_full_canvas"
    layer_dir = out_dir / "normalized_layers"
    request_dir = out_dir / "requests"
    result_dir = out_dir / "responses"
    rows = []
    for index, row in enumerate(selected_assets(manifest, requested, limit), start=1):
        asset_id = row["asset_id"]
        prompt_payload = load_json(Path(row["prompt_json_path"]))
        asset = prompt_payload["asset"]
        prompt = compact_prompt(prompt_payload["prompt"])
        mask = Path(row["full_mask_path"])
        mode = edit_mode(asset)
        started = datetime.now(timezone.utc).isoformat()
        req_record = {
            "asset_id": asset_id,
            "started_at": started,
            "project": project,
            "region": region,
            "model": MODEL,
            "edit_mode": mode,
            "raw_image": str(raw_image),
            "mask": str(mask),
            "prompt": prompt,
        }
        write_json(request_dir / f"{asset_id}.request.json", req_record)
        status = "PASS"
        error = None
        raw_output = raw_dir / f"{asset_id}.png"
        layer_output = layer_dir / f"{asset_id}.png"
        response_payload: dict[str, Any] | None = None
        try:
            response_payload = request_imagen(project, region, token, prompt, raw_image, mask, mode, seed)
            predictions = response_payload.get("predictions") or []
            if not predictions or "bytesBase64Encoded" not in predictions[0]:
                status = "FAIL_NO_IMAGE"
                error = json.dumps(response_payload, ensure_ascii=False)[:2000]
            else:
                raw_output.parent.mkdir(parents=True, exist_ok=True)
                raw_output.write_bytes(base64.b64decode(predictions[0]["bytesBase64Encoded"]))
                normalize_layer(raw_output, mask, asset_id, layer_output)
        except Exception as exc:  # noqa: BLE001
            status = "FAIL"
            error = str(exc)
        if response_payload is not None:
            write_json(result_dir / f"{asset_id}.response.json", response_payload)
        rows.append(
            {
                "asset_id": asset_id,
                "status": status,
                "error": error,
                "raw_output": str(raw_output) if raw_output.exists() else None,
                "normalized_layer": str(layer_output) if layer_output.exists() else None,
                "edit_mode": mode,
            }
        )
        print(json.dumps(rows[-1], ensure_ascii=False))
        time.sleep(0.5)

    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "REVISE",
        "pack": str(pack_dir),
        "out_dir": str(out_dir),
        "project": project,
        "region": region,
        "model": MODEL,
        "count": len(rows),
        "results": rows,
    }
    write_json(out_dir / "imagen_generation_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--region", default="us-central1")
    parser.add_argument("--asset", action="append", default=[])
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    report = run(args.pack.resolve(), args.out.resolve(), args.region, args.asset, args.limit, args.seed)
    print(json.dumps({"ok": report["status"] == "PASS", "status": report["status"], "report": str(args.out / "imagen_generation_report.json")}, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

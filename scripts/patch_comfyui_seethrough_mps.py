#!/usr/bin/env python3
"""Apply local Apple Silicon MPS compatibility patches to ComfyUI-See-through."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLUGIN = (
    ROOT
    / "experiments"
    / "see-through-layer-decomp-001"
    / "external_repos"
    / "ComfyUI"
    / "custom_nodes"
    / "ComfyUI-See-through"
)
PATCH_REPORT = ROOT / "experiments" / "see-through-mps-compat-002" / "reports" / "mps_patch_report.json"


OLD_MEDIAN_BLOCK = """        result = torch.stack(result, dim=0)
        median = torch.median(result, dim=0).values
        return median
"""

NEW_MEDIAN_BLOCK = """        # Apple Silicon MPS does not support the 5D sort path used by
        # torch.median(result, dim=0). The current loop exits after the first
        # augmentation candidate, so bypass median entirely in that common case.
        if len(result) == 1:
            return result[0]

        result = torch.stack(result, dim=0)
        if result.device.type == "mps":
            median = torch.median(result.cpu(), dim=0).values.to(result.device)
        else:
            median = torch.median(result, dim=0).values
        return median
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def patch_file(path: Path, dry_run: bool) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": str(path),
            "status": "FAIL_MISSING_FILE",
        }
    text = path.read_text()
    if NEW_MEDIAN_BLOCK in text:
        return {
            "path": str(path),
            "status": "ALREADY_PATCHED",
        }
    if OLD_MEDIAN_BLOCK not in text:
        return {
            "path": str(path),
            "status": "FAIL_PATTERN_NOT_FOUND",
        }

    backup = path.with_suffix(path.suffix + ".pre_mps_patch")
    if not dry_run:
        if not backup.exists():
            shutil.copy2(path, backup)
        path.write_text(text.replace(OLD_MEDIAN_BLOCK, NEW_MEDIAN_BLOCK))
    return {
        "path": str(path),
        "backup": str(backup),
        "status": "DRY_RUN_READY" if dry_run else "PATCHED",
        "patch": "Bypass torch.median for single augmentation result; use CPU median fallback on MPS for multi-result tensors.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch ComfyUI-See-through for Apple Silicon MPS smoke runs")
    parser.add_argument("--plugin-dir", default=str(DEFAULT_PLUGIN))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    plugin = Path(args.plugin_dir)
    vae_path = plugin / "see-through" / "common" / "modules" / "layerdiffuse" / "vae.py"
    result = patch_file(vae_path, args.dry_run)
    report = {
        "schema_version": 1,
        "experiment_id": "see-through-mps-compat-002",
        "generated_at": now(),
        "dry_run": args.dry_run,
        "plugin_dir": str(plugin),
        "result": result,
        "acceptance": "Patch is only useful if mps_512_safe creates *_layers.json after rerun.",
    }
    save_json(PATCH_REPORT, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"PATCHED", "ALREADY_PATCHED", "DRY_RUN_READY"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

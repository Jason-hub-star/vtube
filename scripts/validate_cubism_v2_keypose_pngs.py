#!/usr/bin/env python3
"""Validate clean-socket/keypose PNG outputs for the current Cubism v2 material pack."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPEC = (
    ROOT
    / "experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/clean_socket_keypose_requirements.json"
)
DEFAULT_OUT = ROOT / "experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def find_asset_file(input_dir: Path, asset_id: str, recursive: bool) -> Path | None:
    pattern = "**/*.png" if recursive else "*.png"
    candidates = [path for path in input_dir.glob(pattern) if asset_id.lower() in path.stem.lower()]
    if candidates:
        return sorted(candidates, key=lambda path: (len(path.name), str(path)))[0]
    relaxed = asset_id.lower().replace("_", "")
    candidates = [path for path in input_dir.glob(pattern) if relaxed in path.stem.lower().replace("_", "")]
    return sorted(candidates, key=lambda path: (len(path.name), str(path)))[0] if candidates else None


def image_stats(path: Path) -> dict[str, Any]:
    image = Image.open(path)
    result: dict[str, Any] = {
        "path": str(path),
        "size": list(image.size),
        "mode": image.mode,
        "has_alpha": "A" in image.getbands(),
        "alpha_bbox": None,
        "alpha_coverage": None,
    }
    if result["has_alpha"]:
        alpha = image.convert("RGBA").getchannel("A")
        result["alpha_bbox"] = list(alpha.getbbox()) if alpha.getbbox() else None
        arr = np.asarray(alpha, dtype=np.uint8)
        result["alpha_coverage"] = round(float((arr > 0).sum()) / float(arr.size), 8)
    return result


def validate_asset(asset: dict[str, Any], found: Path | None, required_size: list[int], required_mode: str) -> dict[str, Any]:
    row: dict[str, Any] = {
        "asset_id": asset["asset_id"],
        "group": asset["group"],
        "kind": asset["kind"],
        "required": asset.get("required", True),
        "status": "MISSING",
        "resize_decision": "NO_FILE",
        "issues": [],
    }
    if found is None:
        row["issues"].append("required PNG not found")
        return row

    stats = image_stats(found)
    row.update(stats)
    size_ok = stats["size"] == required_size
    mode_ok = stats["mode"] == required_mode
    alpha_ok = bool(stats["has_alpha"])
    if not size_ok:
        row["issues"].append(f"size is {stats['size']}, expected {required_size}")
    if not mode_ok:
        row["issues"].append(f"mode is {stats['mode']}, expected {required_mode}")
    if not alpha_ok:
        row["issues"].append("missing alpha channel; alpha extraction/masking required")
    if stats.get("alpha_bbox") is None and alpha_ok:
        row["issues"].append("alpha is empty")

    if size_ok and mode_ok and alpha_ok and stats.get("alpha_bbox") is not None:
        row["status"] = "PASS_READY_FOR_VISUAL_QA"
        row["resize_decision"] = "NO_RESIZE"
    elif not size_ok:
        row["status"] = "REVISE_NORMALIZE_REQUIRED"
        row["resize_decision"] = "NORMALIZE_TO_FULL_CANVAS_DO_NOT_STRETCH"
    elif not alpha_ok or not mode_ok:
        row["status"] = "REVISE_ALPHA_OR_MODE_REQUIRED"
        row["resize_decision"] = "NO_RESIZE_UNTIL_ALPHA_LAYER_EXISTS"
    else:
        row["status"] = "REVISE"
        row["resize_decision"] = "CHECK_MANUALLY"
    return row


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Cubism v2 Keypose PNG Validation",
        "",
        f"- status: `{report['status']}`",
        f"- input_dir: `{report['input_dir']}`",
        f"- required_size: `{report['required_size']}`",
        f"- required_mode: `{report['required_mode']}`",
        "",
        "## Summary",
        "",
        f"- total required: `{report['summary']['total_required']}`",
        f"- found: `{report['summary']['found']}`",
        f"- missing: `{report['summary']['missing']}`",
        f"- resize/normalize required: `{report['summary']['normalize_required']}`",
        f"- alpha/mode repair required: `{report['summary']['alpha_or_mode_required']}`",
        "",
        "## Asset Results",
        "",
        "| asset_id | status | size | mode | alpha_bbox | resize decision | issues |",
        "|---|---|---:|---|---|---|---|",
    ]
    for row in report["assets"]:
        lines.append(
            "| {asset_id} | `{status}` | {size} | {mode} | {bbox} | `{decision}` | {issues} |".format(
                asset_id=row["asset_id"],
                status=row["status"],
                size=row.get("size", "-"),
                mode=row.get("mode", "-"),
                bbox=row.get("alpha_bbox", "-"),
                decision=row["resize_decision"],
                issues="; ".join(row.get("issues", [])) or "-",
            )
        )
    lines += [
        "",
        "## Resize Rule",
        "",
        "- 2048x2048 RGBA full-canvas aligned PNG: do not resize.",
        "- Non-2048 output: do not stretch-resize directly; preserve aspect ratio and place into 2048x2048 transparent canvas using ROI/anchor evidence.",
        "- RGB/full illustration output: alpha extraction is required before it can become a Cubism material layer.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT / "keypose_png_validation_report.json")
    parser.add_argument("--recursive", action="store_true")
    args = parser.parse_args()

    spec = load_json(args.spec)
    required_size = spec["validation_policy"]["current_material_pack_canvas"]
    required_mode = spec["validation_policy"]["required_png_mode"]
    input_dir = args.input_dir.resolve()
    rows = []
    for asset in spec["required_assets"]:
        found = find_asset_file(input_dir, asset["asset_id"], args.recursive)
        rows.append(validate_asset(asset, found, required_size, required_mode))

    summary = {
        "total_required": len(rows),
        "found": sum(1 for row in rows if row["status"] != "MISSING"),
        "missing": sum(1 for row in rows if row["status"] == "MISSING"),
        "normalize_required": sum(1 for row in rows if row["status"] == "REVISE_NORMALIZE_REQUIRED"),
        "alpha_or_mode_required": sum(1 for row in rows if row["status"] == "REVISE_ALPHA_OR_MODE_REQUIRED"),
    }
    status = "PASS_READY_FOR_VISUAL_QA" if all(row["status"] == "PASS_READY_FOR_VISUAL_QA" for row in rows) else "REVISE"
    report = {
        "schema_version": 1,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "input_dir": str(input_dir),
        "spec": str(args.spec.resolve()),
        "required_size": required_size,
        "required_mode": required_mode,
        "summary": summary,
        "assets": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    args.out.with_suffix(".md").write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"ok": status == "PASS_READY_FOR_VISUAL_QA", "status": status, "report": str(args.out)}, ensure_ascii=False, indent=2))
    return 0 if status == "PASS_READY_FOR_VISUAL_QA" else 1


if __name__ == "__main__":
    raise SystemExit(main())

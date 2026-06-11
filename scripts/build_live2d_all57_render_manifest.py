#!/usr/bin/env python3
"""Build an all57 Live2D player manifest from the official combined catalog."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_EXP = ROOT / "experiments" / "reference-model-structure-001"
STRONG_EXP = ROOT / "experiments" / "live2d-strong-model-pattern-001"
DEFAULT_CATALOG = REFERENCE_EXP / "catalog.official_combined.json"
DEFAULT_OUT_DIR = STRONG_EXP / "reports"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path | str | None) -> str | None:
    if path is None:
        return None
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return p.resolve().as_posix()


def safe_id(model_id: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in model_id).strip("_").lower()


def as_path(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("path")
    return None


def first_existing(paths: list[str]) -> str | None:
    for path in paths:
        if (ROOT / path).exists():
            return path
    return None


def verify_runtime_paths(local_paths: dict[str, Any]) -> list[str]:
    missing = []
    model3 = as_path(local_paths.get("model3_json"))
    if not model3 or not (ROOT / model3).exists():
        return ["model3_json"]
    data = load_json(ROOT / model3)
    base = (ROOT / model3).parent
    refs = data.get("FileReferences", {}) or {}
    moc = refs.get("Moc")
    if not moc or not (base / moc).exists():
        missing.append("referenced_moc")
    textures = refs.get("Textures", []) or []
    if not textures:
        missing.append("referenced_textures")
    elif any(not (base / texture).exists() for texture in textures):
        missing.append("referenced_textures")
    return missing


def normalize_local_paths(local_paths: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in local_paths.items():
        if isinstance(value, list):
            out[key] = [item for item in value if isinstance(item, str)]
        elif isinstance(value, str):
            out[key] = value
        elif isinstance(value, dict) and value.get("path"):
            out[key] = value["path"]
    return out


def build_entry(entry: dict[str, Any], rank: int) -> dict[str, Any]:
    paths = normalize_local_paths(entry.get("local_paths") or {})
    runtime_missing = verify_runtime_paths(paths)
    has_runtime = not runtime_missing
    return {
        "rank": rank,
        "id": entry.get("id"),
        "safe_id": safe_id(entry.get("id") or f"model_{rank:02d}"),
        "name": entry.get("name") or entry.get("id") or f"model_{rank:02d}",
        "source_type": entry.get("source_type"),
        "analysis_mode": entry.get("analysis_mode"),
        "local_paths": paths,
        "manifest_status": "PASS" if has_runtime else "NO_RUNTIME",
        "missing_required_paths": runtime_missing,
        "notes": entry.get("notes", []),
    }


def write_md(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Live2D All57 Render Manifest",
        "",
        f"- total: `{manifest['summary']['model_count']}`",
        f"- renderable: `{manifest['summary']['renderable_count']}`",
        f"- no_runtime: `{manifest['summary']['no_runtime_count']}`",
        "",
        "| Rank | Model | Status | Missing |",
        "|---:|---|---|---|",
    ]
    for item in manifest["models"]:
        missing = ", ".join(item["missing_required_paths"]) if item["missing_required_paths"] else ""
        lines.append(f"| {item['rank']} | `{item['name']}` | {item['manifest_status']} | {missing} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    catalog = load_json(args.catalog)
    entries = [build_entry(item, idx + 1) for idx, item in enumerate(catalog.get("models", []))]
    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "kind": "all57",
        "policy": {
            "asset_reuse": "local viewing and success-pattern checking only; do not reuse official art/textures",
            "runtime_note": "Entries without model3/moc/textures are kept in the carousel list as NO_RUNTIME.",
        },
        "summary": {
            "model_count": len(entries),
            "renderable_count": sum(1 for item in entries if item["manifest_status"] == "PASS"),
            "no_runtime_count": sum(1 for item in entries if item["manifest_status"] != "PASS"),
        },
        "models": entries,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_json = args.out_dir / "all57_render_manifest.json"
    out_md = args.out_dir / "all57_render_manifest.md"
    write_json(out_json, manifest)
    write_md(out_md, manifest)
    print(
        json.dumps(
            {
                "status": "PASS",
                "json": rel(out_json),
                "markdown": rel(out_md),
                "summary": manifest["summary"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

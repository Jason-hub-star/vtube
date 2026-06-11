#!/usr/bin/env python3
"""Normalize ComfyUI-See-through layer outputs into Vtube review candidates."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXP = ROOT / "experiments" / "see-through-layer-decomp-001"
CANONICAL_2048 = ROOT / "experiments" / "concept-regeneration-001" / "canonical" / "canonical_front_2048.png"
CANVAS = (2048, 2048)


TAG_TO_PART = {
    "front hair": "front_hair",
    "fronthair": "front_hair",
    "front_hair": "front_hair",
    "back hair": "back_hair",
    "backhair": "back_hair",
    "back_hair": "back_hair",
    "face": "face_base",
    "head": "face_base",
    "neck": "neck",
    "topwear": "clothes",
    "shirt": "clothes",
    "coat": "clothes",
    "jacket": "clothes",
    "mouth": "mouth_line",
    "irides": "iris",
    "iris": "iris",
    "eyes": "iris",
    "eye": "iris",
    "eyewhite": "eye_white",
    "sclera": "eye_white",
    "eyelash": "upper_lash",
    "eyebrow": "brow",
    "ears": "ear_outer",
    "ear": "ear_outer",
    "earwear": "ear_inner",
    "neckwear": "choker",
    "headwear": "headwear_reference",
    "handwear": "arm",
    "nose": "nose_reference",
    "objects": "object_reference",
    "tail": "tail_reference",
    "wings": "wings_reference",
}

PRODUCTION_BASES = {
    "front_hair",
    "back_hair",
    "face_base",
    "neck",
    "clothes",
    "mouth_line",
    "iris",
    "eye_white",
    "upper_lash",
    "brow",
    "ear_outer",
    "ear_inner",
    "choker",
    "arm",
}

ROLE_FOR_PART = {
    "front_hair": "front_hair",
    "back_hair": "back_hair",
    "face_base": "face",
    "neck": "neck",
    "clothes": "clothes",
    "mouth_line": "mouth_line",
    "iris": "iris",
    "eye_white": "eye_white",
    "upper_lash": "upper_lash",
    "brow": "brow",
    "ear_outer": "ears",
    "ear_inner": "ears",
    "choker": "accessory",
    "arm": "arm",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def resolve_repo_path(value: str | None, default: Path) -> Path:
    if not value:
        return default
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", value.strip().replace("-", "_")).strip("_") or "layer"


def split_side(tag: str) -> tuple[str, str | None]:
    text = tag.strip()
    lower = text.lower()
    for suffix, side in [("-l", "L"), ("_l", "L"), (" left", "L"), ("-r", "R"), ("_r", "R"), (" right", "R")]:
        if lower.endswith(suffix):
            return text[: -len(suffix)].strip(), side
    return text, None


def target_for_tag(tag: str) -> tuple[str, str | None, bool]:
    base_tag, side = split_side(tag)
    base_key = base_tag.lower().replace("_", " ")
    part = TAG_TO_PART.get(base_key) or TAG_TO_PART.get(base_key.replace(" ", "_")) or f"raw_{safe_name(base_tag)}"
    production_candidate = part in PRODUCTION_BASES
    if side and part in {"iris", "eye_white", "upper_lash", "brow", "ear_outer", "ear_inner", "arm"}:
        return f"{side}_{part}", side, production_candidate
    if part in {"iris", "eye_white", "upper_lash", "brow", "ear_outer", "ear_inner"}:
        production_candidate = False
    return part, side, production_candidate


def bbox_from_alpha(path: Path) -> list[int] | None:
    img = Image.open(path).convert("RGBA")
    alpha = np.array(img)[:, :, 3]
    ys, xs = np.where(alpha > 10)
    if len(xs) == 0:
        return None
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    return [x0, y0, x1 - x0, y1 - y0]


def alpha_coverage(path: Path, bbox: list[int] | None) -> float:
    if not bbox:
        return 0.0
    x, y, w, h = bbox
    if w <= 0 or h <= 0:
        return 0.0
    img = Image.open(path).convert("RGBA")
    alpha = np.array(img.crop((x, y, x + w, y + h)))[:, :, 3]
    return round(float(np.count_nonzero(alpha > 10) / alpha.size), 6)


def find_latest_layers_json(exp: Path, raw_dir: Path) -> Path:
    candidates = list(raw_dir.glob("*_layers.json"))
    comfy_output = exp / "external_repos" / "ComfyUI" / "output"
    if comfy_output.exists():
        candidates.extend(comfy_output.glob("*_layers.json"))
    if not candidates:
        raise FileNotFoundError("No *_layers.json found. Pass --layers-json from ComfyUI output.")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def resolve_layer_file(base: Path, filename: str) -> Path:
    candidate = Path(filename)
    if candidate.is_absolute():
        return candidate
    return base / filename


def normalize_layer(
    *,
    raw_path: Path,
    entry: dict[str, Any],
    scale_x: float,
    scale_y: float,
    target_name: str,
    normalized_dir: Path,
) -> Path:
    img = Image.open(raw_path).convert("RGBA")
    left = int(round(float(entry.get("left", 0)) * scale_x))
    top = int(round(float(entry.get("top", 0)) * scale_y))
    width = max(1, int(round(img.width * scale_x)))
    height = max(1, int(round(img.height * scale_y)))
    resized = img.resize((width, height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    canvas.paste(resized, (left, top), resized)
    out = normalized_dir / f"{target_name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)
    return out


def normalize(args: argparse.Namespace) -> dict[str, Any]:
    exp = resolve_repo_path(args.experiment_dir, DEFAULT_EXP)
    experiment_id = args.experiment_id or exp.name
    raw_dir = resolve_repo_path(args.raw_dir, exp / "raw_comfyui_output")
    normalized_dir = resolve_repo_path(args.normalized_dir, exp / "normalized_layers")
    depth_dir = resolve_repo_path(args.depth_dir, exp / "depth_layers")
    report_dir = exp / "reports"
    manifest_path = exp / "layer_manifest.json"
    normalize_report = report_dir / "normalize_report.json"
    canonical_path = resolve_repo_path(
        args.canonical_path,
        exp / "canonical" / "canonical_front_2048.png" if (exp / "canonical" / "canonical_front_2048.png").exists() else CANONICAL_2048,
    )

    layers_json = Path(args.layers_json) if args.layers_json else find_latest_layers_json(exp, raw_dir)
    layer_info = json.loads(layers_json.read_text())
    base = layers_json.parent
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)
    depth_dir.mkdir(parents=True, exist_ok=True)

    width = int(layer_info.get("width") or 1280)
    height = int(layer_info.get("height") or 1280)
    scale_x = CANVAS[0] / width
    scale_y = CANVAS[1] / height

    layers = []
    used_names: set[str] = set()
    for index, entry in enumerate(layer_info.get("layers", [])):
        tag = str(entry.get("name") or f"layer_{index}")
        raw_src = resolve_layer_file(base, entry["filename"])
        if not raw_src.exists():
            continue
        raw_copy = raw_dir / raw_src.name
        if raw_src.resolve() != raw_copy.resolve():
            shutil.copy2(raw_src, raw_copy)

        target_part, side, production_candidate = target_for_tag(tag)
        safe_target = safe_name(target_part)
        prefix = "seethrough_mps" if experiment_id == "see-through-mps-compat-002" else safe_name(experiment_id)
        layer_name = f"{prefix}__{safe_target}"
        if layer_name in used_names:
            layer_name = f"{layer_name}_{index:02d}"
        used_names.add(layer_name)
        normalized = normalize_layer(
            raw_path=raw_copy,
            entry=entry,
            scale_x=scale_x,
            scale_y=scale_y,
            target_name=layer_name,
            normalized_dir=normalized_dir,
        )

        depth_copy = None
        if entry.get("depth_filename"):
            depth_src = resolve_layer_file(base, entry["depth_filename"])
            if depth_src.exists():
                depth_copy = depth_dir / depth_src.name
                shutil.copy2(depth_src, depth_copy)

        bbox = bbox_from_alpha(normalized)
        role = ROLE_FOR_PART.get(target_part, "seethrough_reference")
        status = "OBSERVED" if production_candidate else "REFERENCE_ONLY"
        layers.append(
            {
                "layer_name": layer_name,
                "original_part_id": target_part,
                "raw_tag": tag,
                "role": role,
                "side": side,
                "source_path": str(raw_copy),
                "output_path": str(normalized),
                "canonical_path": str(canonical_path),
                "canvas_size": list(CANVAS),
                "bbox": bbox,
                "alpha_coverage": alpha_coverage(normalized, bbox),
                "draw_order": 300 + index,
                "depth_median": entry.get("depth_median"),
                "status": status,
                "include_in_import_psd": False,
                "production_candidate": production_candidate,
                "depth_path": str(depth_copy) if depth_copy else None,
                "experiment_id": experiment_id,
                "notes": "See-through normalized candidate. Never include in PSD until human O review and Cubism smoke gate.",
            }
        )

    manifest = {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "generated_at": now(),
        "source_layers_json": str(layers_json),
        "source_canvas_size": [width, height],
        "normalized_canvas_size": list(CANVAS),
        "scale_to_2048": [scale_x, scale_y],
        "layers": layers,
        "counts": {
            "raw_layers": len(layer_info.get("layers", [])),
            "normalized_layers": len(layers),
            "production_candidates": sum(1 for layer in layers if layer.get("production_candidate")),
            "reference_only": sum(1 for layer in layers if not layer.get("production_candidate")),
        },
    }
    save_json(manifest_path, manifest)
    save_json(normalize_report, manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize ComfyUI-See-through output layers")
    parser.add_argument("--experiment-id")
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP.relative_to(ROOT)))
    parser.add_argument("--raw-dir")
    parser.add_argument("--normalized-dir")
    parser.add_argument("--depth-dir")
    parser.add_argument("--canonical-path")
    parser.add_argument("--layers-json", help="Path to ComfyUI *_layers.json. Defaults to latest known output.")
    args = parser.parse_args()
    manifest = normalize(args)
    manifest_path = resolve_repo_path(args.experiment_dir, DEFAULT_EXP) / "layer_manifest.json"
    print(json.dumps({"layers": len(manifest["layers"]), "manifest": str(manifest_path.relative_to(ROOT))}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

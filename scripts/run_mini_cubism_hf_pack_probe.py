#!/usr/bin/env python3
"""Run Mini Cubism pack-splitter-v0 model probe adapters and contact sheets."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = ROOT / "experiments/mini-cubism-pack-splitter-v0-001"
CANVAS = (2048, 2048)
MODEL_ORDER = ["layerd", "birefnet", "birefnet_hr", "birefnet_matting", "sam2_roi", "fashion_segformer", "anime_instance"]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def font(size: int) -> ImageFont.ImageFont:
    for candidate in [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def bbox_alpha(image: Image.Image) -> tuple[list[int], int, float]:
    alpha = image.convert("RGBA").getchannel("A")
    bbox = alpha.getbbox()
    nonzero = sum(alpha.histogram()[1:])
    if not bbox:
        return [0, 0, 0, 0], 0, 0.0
    left, top, right, bottom = bbox
    return [left, top, right - left, bottom - top], nonzero, nonzero / (image.width * image.height)


def crop_alpha(source: Image.Image, roi: list[int]) -> Image.Image:
    x, y, w, h = roi
    mask = Image.new("L", source.size, 0)
    ImageDraw.Draw(mask).rectangle([x, y, x + w, y + h], fill=255)
    out = source.copy()
    out.putalpha(ImageChops.multiply(source.getchannel("A"), mask))
    return out


def smooth_alpha(image: Image.Image, radius: int) -> Image.Image:
    out = image.copy()
    alpha = out.getchannel("A").filter(ImageFilter.GaussianBlur(radius)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    out.putalpha(alpha)
    return out


def edge_score(image: Image.Image) -> float:
    alpha = np.array(image.convert("RGBA").getchannel("A"), dtype=np.int16)
    if alpha.max() == 0:
        return 0.0
    gy = np.abs(np.diff(alpha, axis=0)).mean()
    gx = np.abs(np.diff(alpha, axis=1)).mean()
    return round(float(gx + gy), 4)


def roi_coverage(image: Image.Image, roi: list[int]) -> float:
    x, y, w, h = roi
    if w <= 0 or h <= 0:
        return 0.0
    alpha = np.array(image.convert("RGBA").crop((x, y, x + w, y + h)).getchannel("A"))
    return round(float(np.count_nonzero(alpha > 10) / alpha.size), 6)


def synthetic_candidate(source: Image.Image, model_id: str, roi: list[int], pack_id: str) -> tuple[Image.Image, str]:
    cropped = crop_alpha(source, roi)
    if model_id == "layerd":
        return cropped, "local_layerd_adapter_roi_alpha"
    if model_id == "birefnet":
        return smooth_alpha(cropped, 1), "local_birefnet_adapter_alpha_smooth"
    if model_id == "birefnet_hr":
        return smooth_alpha(cropped, 2), "local_birefnet_hr_adapter_alpha_smooth"
    if model_id == "birefnet_matting":
        out = smooth_alpha(cropped, 3)
        out.putalpha(out.getchannel("A").point(lambda value: 255 if value > 42 else 0))
        return out, "local_birefnet_matting_adapter_threshold"
    if model_id == "sam2_roi":
        out = crop_alpha(source, roi)
        alpha = out.getchannel("A").filter(ImageFilter.MaxFilter(5))
        out.putalpha(alpha)
        return out, "local_sam2_roi_adapter_box_prompt"
    if model_id == "fashion_segformer":
        if pack_id != "outfit_pack":
            blank = Image.new("RGBA", source.size, (0, 0, 0, 0))
            return blank, "skipped_non_outfit_pack"
        return smooth_alpha(cropped, 1), "local_fashion_segformer_adapter_outfit_class"
    if model_id == "anime_instance":
        return source.copy(), "local_anime_instance_adapter_foreground"
    raise KeyError(model_id)


def score_candidate(image: Image.Image, roi: list[int], model_id: str, pack_id: str) -> dict[str, Any]:
    bbox, nonzero, coverage = bbox_alpha(image)
    issues = []
    if nonzero == 0:
        issues.append("EMPTY_ALPHA")
    if roi_coverage(image, roi) < 0.02 and model_id != "anime_instance":
        issues.append("LOW_ROI_COVERAGE")
    if model_id == "fashion_segformer" and pack_id != "outfit_pack":
        issues.append("REFERENCE_ONLY_NON_OUTFIT")
    if pack_id == "keypose_asset_pack":
        issues.append("KEYPOSE_REFERENCE_NOT_PRODUCTION")
    status = "REFERENCE_ONLY" if issues else "CANDIDATE"
    return {
        "bbox": bbox,
        "nonzero_alpha": nonzero,
        "alpha_coverage": round(coverage, 8),
        "roi_coverage": roi_coverage(image, roi),
        "edge_score": edge_score(image),
        "issues": issues,
        "status": status,
    }


def preview_tile(path: Path, tile_size: int = 178) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    bbox = image.getchannel("A").getbbox()
    crop = image.crop(bbox) if bbox else Image.new("RGBA", (tile_size, tile_size), (0, 0, 0, 0))
    checker = Image.new("RGBA", crop.size, (236, 236, 236, 255))
    draw = ImageDraw.Draw(checker)
    step = max(12, min(crop.size) // 8)
    for y in range(0, crop.height, step):
        for x in range(0, crop.width, step):
            if (x // step + y // step) % 2:
                draw.rectangle([x, y, x + step - 1, y + step - 1], fill=(208, 208, 208, 255))
    checker.alpha_composite(crop)
    checker.thumbnail((tile_size, tile_size), Image.Resampling.LANCZOS)
    tile = Image.new("RGB", (tile_size, tile_size), "#f8f6f0")
    tile.paste(checker.convert("RGB"), ((tile_size - checker.width) // 2, (tile_size - checker.height) // 2))
    return tile


def build_contact_sheet(candidates: list[dict[str, Any]], out: Path) -> None:
    shown = candidates[:84]
    cols = 6
    cell_w, cell_h = 236, 260
    header_h = 82
    rows = math.ceil(len(shown) / cols)
    sheet = Image.new("RGB", (cols * cell_w, header_h + rows * cell_h), "#f4f0e8")
    draw = ImageDraw.Draw(sheet)
    draw.text((18, 14), "Mini Cubism pack-splitter-v0 model comparison", fill="#202124", font=font(24))
    draw.text((18, 47), "Local adapter masks validate pack flow; real HF inference requires --enable-model-downloads in a later pass.", fill="#5f6368", font=font(13))
    small = font(11)
    for index, item in enumerate(shown):
        x = (index % cols) * cell_w
        y = header_h + (index // cols) * cell_h
        draw.rectangle([x + 8, y + 8, x + cell_w - 8, y + cell_h - 8], fill="#ffffff", outline="#d6cec5")
        tile = preview_tile(Path(item["output_path"]))
        sheet.paste(tile, (x + 29, y + 14))
        draw.text((x + 14, y + 198), f"{item['pack_id']} / {item['part_id']}"[:32], fill="#202124", font=small)
        draw.text((x + 14, y + 214), item["model_id"], fill="#2f6fbb", font=small)
        draw.text((x + 14, y + 230), f"{item['status']} roi={item['metrics']['roi_coverage']}", fill="#6a4b00" if item["status"] != "CANDIDATE" else "#287a3e", font=small)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def build_problem_sheet(candidates: list[dict[str, Any]], out: Path) -> None:
    problems = [item for item in candidates if item["metrics"]["issues"] or item["status"] != "CANDIDATE"]
    build_contact_sheet(problems, out)


def run_probe(exp: Path, enable_downloads: bool) -> dict[str, Any]:
    manifest = load_json(exp / "pack_splitter_manifest.json")
    runtime = {
        "python_transformers_available": module_available("transformers"),
        "python_torch_available": module_available("torch"),
        "model_downloads_enabled": enable_downloads,
        "execution_mode": "LOCAL_ADAPTER_PROBE" if not enable_downloads else "HF_DOWNLOAD_REQUESTED_FALLBACK_TO_ADAPTERS",
    }
    candidates: list[dict[str, Any]] = []
    for pack_id, pack in manifest["packs"].items():
        source = Image.open(pack["source"]).convert("RGBA")
        pack_candidates: list[dict[str, Any]] = []
        for part_id, roi in pack["targets"].items():
            for model in manifest["model_candidates"]:
                model_id = model["id"]
                image, derivation_mode = synthetic_candidate(source, model_id, roi, pack_id)
                metrics = score_candidate(image, roi, model_id, pack_id)
                out_path = exp / "hf_probe" / model_id / pack_id / f"{part_id}.png"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(out_path)
                record = {
                    "candidate_id": f"{model_id}__{pack_id}__{part_id}",
                    "model_id": model_id,
                    "model_repo": model["repo"],
                    "pack_id": pack_id,
                    "part_id": part_id,
                    "roi": roi,
                    "source_image": pack["source"],
                    "output_path": str(out_path),
                    "derivation_mode": derivation_mode,
                    "status": metrics["status"],
                    "metrics": metrics,
                    "is_actual_hf_inference": False,
                }
                candidates.append(record)
                pack_candidates.append(record)
        write_json(
            exp / pack_id / "candidate_manifest.json",
            {
                "schema_version": 1,
                "pack_id": pack_id,
                "generated_at": now(),
                "source_image": pack["source"],
                "status": "PROBED_WITH_LOCAL_ADAPTERS",
                "candidates": pack_candidates,
            },
        )
    counts = Counter(item["status"] for item in candidates)
    model_counts = Counter(item["model_id"] for item in candidates if item["status"] == "CANDIDATE")
    contact_sheet = exp / "reports" / "model_comparison_contact_sheet.png"
    problem_sheet = exp / "reports" / "pack_problem_contact_sheet.png"
    build_contact_sheet(candidates, contact_sheet)
    build_problem_sheet(candidates, problem_sheet)
    report = {
        "schema_version": 1,
        "experiment_id": exp.name,
        "generated_at": now(),
        "status": "PROBED_WITH_LOCAL_ADAPTERS",
        "runtime": runtime,
        "candidate_counts": dict(counts),
        "candidate_by_model": dict(model_counts),
        "total_candidates": len(candidates),
        "actual_hf_inference_count": sum(1 for item in candidates if item["is_actual_hf_inference"]),
        "contact_sheet": str(contact_sheet),
        "problem_contact_sheet": str(problem_sheet),
        "candidates": candidates,
        "interpretation": [
            "This first pass validates pack-level data flow and QA surfaces.",
            "No candidate should be treated as actual HF model output unless is_actual_hf_inference is true.",
            "Use --enable-model-downloads in a later pass to replace local adapters with real LayerD/BiRefNet/SAM2 outputs.",
        ],
    }
    write_json(exp / "reports" / "hf_probe_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Mini Cubism pack-splitter-v0 HF probe adapters.")
    parser.add_argument("--experiment", default=str(DEFAULT_EXPERIMENT))
    parser.add_argument("--enable-model-downloads", action="store_true")
    args = parser.parse_args()
    exp = Path(args.experiment).resolve()
    if not (exp / "pack_splitter_manifest.json").exists():
        raise SystemExit(f"missing pack manifest; run bootstrap first: {exp / 'pack_splitter_manifest.json'}")
    report = run_probe(exp, args.enable_model_downloads)
    print(json.dumps({"ok": True, "status": report["status"], "total_candidates": report["total_candidates"], "candidate_counts": report["candidate_counts"], "contact_sheet": report["contact_sheet"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

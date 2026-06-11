#!/usr/bin/env python3
"""Run SAM2 ROI refinement for Mini Cubism pack source targets."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = ROOT / "experiments/mini-cubism-pack-splitter-v0-001"
DEFAULT_MODEL = "facebook/sam2.1-hiera-tiny"
DEFAULT_PACKS = ["accessory_pack", "keypose_asset_pack"]


def model_slug(model_id: str) -> str:
    return model_id.replace("/", "_").replace(".", "_").replace("-", "_").lower()


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


def bbox_alpha(image: Image.Image) -> tuple[list[int], int, float]:
    alpha = image.convert("RGBA").getchannel("A")
    bbox = alpha.getbbox()
    nonzero = sum(alpha.histogram()[1:])
    if not bbox:
        return [0, 0, 0, 0], 0, 0.0
    left, top, right, bottom = bbox
    return [left, top, right - left, bottom - top], nonzero, nonzero / (image.width * image.height)


def crop_rgba_to_rgb(crop: Image.Image) -> Image.Image:
    crop = crop.convert("RGBA")
    bg = Image.new("RGBA", crop.size, (248, 246, 240, 255))
    bg.alpha_composite(crop)
    return bg.convert("RGB")


def alpha_centroid(crop: Image.Image) -> tuple[int, int] | None:
    alpha = np.array(crop.convert("RGBA").getchannel("A"), dtype=np.float32)
    ys, xs = np.nonzero(alpha > 20)
    if len(xs) == 0:
        return None
    weights = alpha[ys, xs]
    cx = int(round(float((xs * weights).sum() / weights.sum())))
    cy = int(round(float((ys * weights).sum() / weights.sum())))
    return cx, cy


def select_mask(mask_array: np.ndarray, reference_alpha: np.ndarray) -> tuple[np.ndarray, int]:
    """Select the SAM candidate whose area best matches alpha inside the ROI."""
    # Common shape after post-process: [num_points, multimask, H, W] or [multimask, H, W].
    arr = np.asarray(mask_array)
    while arr.ndim > 3:
        arr = arr[0]
    if arr.ndim == 2:
        candidates = arr[None, :, :]
    else:
        candidates = arr
    ref_area = max(1, int(np.count_nonzero(reference_alpha > 20)))
    best_index = 0
    best_score = float("inf")
    best_mask = candidates[0]
    for index, candidate in enumerate(candidates):
        binary = candidate > 0
        area = int(np.count_nonzero(binary))
        if area == 0:
            score = float("inf")
        else:
            score = abs(area - ref_area) / ref_area
        if score < best_score:
            best_index = index
            best_score = score
            best_mask = binary
    return best_mask.astype(np.uint8) * 255, best_index


def mask_edge_clip_ratio(mask: np.ndarray) -> float:
    if mask.size == 0:
        return 0.0
    binary = mask > 0
    total = int(np.count_nonzero(binary))
    if total == 0:
        return 0.0
    edge = np.zeros_like(binary, dtype=bool)
    edge[0, :] = True
    edge[-1, :] = True
    edge[:, 0] = True
    edge[:, -1] = True
    return round(float(np.count_nonzero(binary & edge) / total), 6)


def build_sheet(records: list[dict[str, Any]], out: Path) -> None:
    shown = records[:40]
    cols = 5
    cell_w, cell_h = 260, 272
    header_h = 84
    rows = max(1, (len(shown) + cols - 1) // cols)
    sheet = Image.new("RGB", (cols * cell_w, header_h + rows * cell_h), "#f4f0e8")
    draw = ImageDraw.Draw(sheet)
    draw.text((18, 14), "SAM2 ROI refinement candidates", fill="#202124", font=font(24))
    draw.text((18, 47), "ROI point-prompt masks for accessory/keypose broad LayerD masks.", fill="#5f6368", font=font(13))
    small = font(11)
    for idx, record in enumerate(shown):
        x = (idx % cols) * cell_w
        y = header_h + (idx // cols) * cell_h
        draw.rectangle([x + 8, y + 8, x + cell_w - 8, y + cell_h - 8], fill="#fffaf2", outline="#d6cec5")
        image = Image.open(record["output_path"]).convert("RGBA")
        bbox = image.getchannel("A").getbbox()
        crop = image.crop(bbox) if bbox else Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        bg = Image.new("RGB", crop.size, "#f8f6f0")
        bg.paste(crop.convert("RGB"), mask=crop.getchannel("A"))
        bg.thumbnail((cell_w - 34, cell_h - 82), Image.Resampling.LANCZOS)
        sheet.paste(bg, (x + (cell_w - bg.width) // 2, y + 16))
        draw.text((x + 14, y + cell_h - 56), f"{record['pack_id']} / {record['part_id']}"[:31], fill="#202124", font=small)
        draw.text((x + 14, y + cell_h - 39), record["quality_status"], fill="#287a3e" if record["quality_status"] == "CANDIDATE" else "#9a6700", font=small)
        draw.text((x + 14, y + cell_h - 22), f"cov={record['roi_mask_coverage']}", fill="#5f6368", font=small)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SAM2 ROI refinement on Mini Cubism pack source targets.")
    parser.add_argument("--experiment", default=str(DEFAULT_EXPERIMENT))
    parser.add_argument("--packs", default=",".join(DEFAULT_PACKS))
    parser.add_argument("--model-id", default=DEFAULT_MODEL)
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "mps"])
    args = parser.parse_args()

    exp = Path(args.experiment).resolve()
    manifest = load_json(exp / "pack_splitter_manifest.json")
    packs = [item.strip() for item in args.packs.split(",") if item.strip()]
    slug = model_slug(args.model_id)
    report_path = exp / "reports" / f"{slug}_roi_refinement_report.json"
    try:
        import torch
        from transformers import Sam2Model, Sam2Processor

        if args.device == "auto":
            device = "mps" if torch.backends.mps.is_available() else "cpu"
        else:
            device = args.device
        processor = Sam2Processor.from_pretrained(args.model_id)
        model = Sam2Model.from_pretrained(args.model_id).to(device)
        model.eval()
        records: list[dict[str, Any]] = []
        for pack_id in packs:
            pack = manifest["packs"][pack_id]
            source = Path(pack["source"])
            source_image = Image.open(source).convert("RGBA")
            for part_id, roi in pack["targets"].items():
                x, y, w, h = [int(value) for value in roi]
                crop_box = (max(0, x), max(0, y), min(source_image.width, x + w), min(source_image.height, y + h))
                if crop_box[2] <= crop_box[0] or crop_box[3] <= crop_box[1]:
                    continue
                crop = source_image.crop(crop_box)
                point = alpha_centroid(crop)
                if point is None:
                    continue
                rgb = crop_rgba_to_rgb(crop)
                input_points = [[[[float(point[0]), float(point[1])]]]]
                input_labels = [[[1]]]
                inputs = processor(images=rgb, input_points=input_points, input_labels=input_labels, return_tensors="pt")
                inputs = {key: value.to(device) if hasattr(value, "to") else value for key, value in inputs.items()}
                with torch.no_grad():
                    outputs = model(**inputs)
                masks = processor.post_process_masks(outputs.pred_masks.cpu(), inputs["original_sizes"].cpu())[0]
                reference_alpha = np.array(crop.getchannel("A"))
                selected, selected_index = select_mask(masks.numpy(), reference_alpha)
                out_crop = crop.copy()
                out_crop.putalpha(Image.fromarray(selected, mode="L"))
                canvas = Image.new("RGBA", source_image.size, (0, 0, 0, 0))
                canvas.alpha_composite(out_crop, (crop_box[0], crop_box[1]))
                out_path = exp / "hf_actual" / slug / pack_id / f"{part_id}_{slug}.png"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                canvas.save(out_path)
                bbox, nonzero, coverage = bbox_alpha(canvas)
                roi_mask_coverage = round(float(np.count_nonzero(selected > 0) / selected.size), 6)
                edge_clip_ratio = mask_edge_clip_ratio(selected)
                issues: list[str] = []
                hard_failures: list[str] = []
                if roi_mask_coverage > 0.72:
                    issues.append("ROI_MASK_TOO_BROAD")
                if roi_mask_coverage < 0.02:
                    issues.append("ROI_MASK_TOO_SMALL_OR_FRAGMENT")
                    hard_failures.append("VISUAL_FAIL_FRAGMENT")
                if edge_clip_ratio > 0.001:
                    issues.append("MASK_TOUCHES_ROI_EDGE")
                    hard_failures.append("VISUAL_FAIL_CROPPED_BY_ROI")
                quality_status = "VISUAL_FAIL" if hard_failures else ("REVISE_MASK" if issues else "CANDIDATE")
                records.append(
                    {
                        "pack_id": pack_id,
                        "part_id": part_id,
                        "source_path": str(source),
                        "output_path": str(out_path),
                        "roi": roi,
                        "prompt_point": [point[0] + crop_box[0], point[1] + crop_box[1]],
                        "selected_mask_index": selected_index,
                        "bbox": bbox,
                        "nonzero_alpha": nonzero,
                        "alpha_coverage": round(coverage, 8),
                        "roi_mask_coverage": roi_mask_coverage,
                        "edge_clip_ratio": edge_clip_ratio,
                        "issues": issues,
                        "hard_failures": sorted(set(hard_failures)),
                        "quality_status": quality_status,
                        "is_actual_hf_inference": True,
                    }
                )
        sheet = exp / "reports" / f"{slug}_roi_refinement_contact_sheet.png"
        build_sheet(records, sheet)
        issue_count = sum(len(record["issues"]) for record in records)
        hard_failure_count = sum(len(record.get("hard_failures", [])) for record in records)
        report = {
            "schema_version": 1,
            "experiment_id": exp.name,
            "generated_at": now(),
            "status": "RUNTIME_PASS_VISUAL_FAIL" if hard_failure_count else ("PASS" if records and not issue_count else ("RUNTIME_PASS_REVISE_MASK" if records else "FAIL_NO_RECORDS")),
            "runtime_status": "PASS" if records else "FAIL_NO_RECORDS",
            "quality_status": "VISUAL_FAIL" if hard_failure_count else ("CANDIDATE" if records and not issue_count else "REVISE_MASK"),
            "model_id": args.model_id,
            "device": device,
            "actual_hf_inference_count": len(records),
            "issue_count": issue_count,
            "hard_failure_count": hard_failure_count,
            "records": records,
            "contact_sheet": str(sheet),
        }
        write_json(report_path, report)
        print(json.dumps({"ok": True, "status": report["status"], "records": len(records), "issue_count": issue_count, "report": str(report_path)}, indent=2))
        return 0 if records else 1
    except Exception as exc:
        report = {
            "schema_version": 1,
            "experiment_id": exp.name,
            "generated_at": now(),
            "status": "BLOCKED_SAM2_ROI_REFINEMENT",
            "model_id": args.model_id,
            "packs": packs,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        write_json(report_path, report)
        print(json.dumps({"ok": False, "status": report["status"], "error": str(exc), "report": str(report_path)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

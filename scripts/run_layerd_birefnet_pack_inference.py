#!/usr/bin/env python3
"""Run actual LayerD BiRefNet HF inference on Mini Cubism pack sources."""

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
DEFAULT_PACKS = ["hair_pack", "outfit_pack", "accessory_pack", "keypose_asset_pack"]
DEFAULT_MODEL_ID = "cyberagent/layerd-birefnet"
MODEL_ALIASES = {
    "layerd_birefnet": "cyberagent/layerd-birefnet",
    "birefnet": "ZhengPeng7/BiRefNet",
    "birefnet_hr": "ZhengPeng7/BiRefNet_HR",
    "birefnet_matting": "ZhengPeng7/BiRefNet-matting",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def font(size: int) -> ImageFont.ImageFont:
    for candidate in [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def rgba_to_rgb(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    bg = Image.new("RGBA", image.size, (248, 246, 240, 255))
    bg.alpha_composite(image)
    return bg.convert("RGB")


def output_to_tensor(output: Any) -> Any:
    """Find a likely mask tensor from common BiRefNet output shapes."""
    if hasattr(output, "logits"):
        return output.logits
    if isinstance(output, (list, tuple)):
        candidate = output[-1]
        if isinstance(candidate, (list, tuple)):
            return candidate[-1]
        return candidate
    if isinstance(output, dict):
        for key in ["logits", "preds", "prediction", "out"]:
            if key in output:
                return output[key]
    return output


def bbox_alpha(image: Image.Image) -> tuple[list[int], int, float]:
    alpha = image.convert("RGBA").getchannel("A")
    bbox = alpha.getbbox()
    nonzero = sum(alpha.histogram()[1:])
    if not bbox:
        return [0, 0, 0, 0], 0, 0.0
    left, top, right, bottom = bbox
    return [left, top, right - left, bottom - top], nonzero, nonzero / (image.width * image.height)


def model_slug(model_id: str) -> str:
    for alias, repo in MODEL_ALIASES.items():
        if repo == model_id or alias == model_id:
            return alias
    return model_id.replace("/", "_").replace("-", "_").lower()


def build_sheet(records: list[dict[str, Any]], out: Path, model_id: str) -> None:
    cols = max(1, min(4, len(records)))
    cell_w, cell_h = 360, 420
    header_h = 76
    sheet = Image.new("RGB", (cols * cell_w, header_h + cell_h), "#f4f0e8")
    draw = ImageDraw.Draw(sheet)
    draw.text((18, 14), "BiRefNet-family actual HF inference", fill="#202124", font=font(24))
    draw.text((18, 45), model_id, fill="#5f6368", font=font(14))
    small = font(13)
    for idx, record in enumerate(records[:cols]):
        x = idx * cell_w
        y = header_h
        draw.rectangle([x + 10, y + 10, x + cell_w - 10, y + cell_h - 10], fill="#fffaf2", outline="#d6cec5")
        image = Image.open(record["output_path"]).convert("RGBA")
        bbox = image.getchannel("A").getbbox()
        crop = image.crop(bbox) if bbox else image
        bg = Image.new("RGB", crop.size, "#f8f6f0")
        bg.paste(crop.convert("RGB"), mask=crop.getchannel("A"))
        bg.thumbnail((cell_w - 44, cell_h - 95), Image.Resampling.LANCZOS)
        sheet.paste(bg, (x + (cell_w - bg.width) // 2, y + 22))
        draw.text((x + 18, y + cell_h - 58), record["pack_id"], fill="#202124", font=small)
        draw.text((x + 18, y + cell_h - 36), f"bbox={record['bbox']} alpha={record['nonzero_alpha']}", fill="#5f6368", font=small)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run LayerD BiRefNet actual HF inference on pack sources.")
    parser.add_argument("--experiment", default=str(DEFAULT_EXPERIMENT))
    parser.add_argument("--packs", default=",".join(DEFAULT_PACKS))
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID, help="HF repo id or alias: layerd_birefnet, birefnet, birefnet_hr, birefnet_matting")
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "mps"])
    args = parser.parse_args()

    exp = Path(args.experiment).resolve()
    manifest = load_json(exp / "pack_splitter_manifest.json")
    packs = [item.strip() for item in args.packs.split(",") if item.strip()]
    resolved_model_id = MODEL_ALIASES.get(args.model_id, args.model_id)
    slug = model_slug(resolved_model_id)
    report_path = exp / "reports" / f"{slug}_inference_report.json"
    out_dir = exp / "hf_actual" / slug
    try:
        import torch
        from torchvision import transforms
        from transformers import AutoModelForImageSegmentation

        if args.device == "auto":
            device = "mps" if torch.backends.mps.is_available() else "cpu"
        else:
            device = args.device
        model = AutoModelForImageSegmentation.from_pretrained(resolved_model_id, trust_remote_code=True)
        model.to(device)
        model.eval()
        preprocess = transforms.Compose(
            [
                transforms.Resize((1024, 1024)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        )
        records: list[dict[str, Any]] = []
        for pack_id in packs:
            source = Path(manifest["packs"][pack_id]["source"])
            source_image = Image.open(source).convert("RGBA")
            input_image = rgba_to_rgb(source_image)
            tensor = preprocess(input_image).unsqueeze(0).to(device)
            with torch.no_grad():
                output = model(tensor)
            pred = output_to_tensor(output)
            if isinstance(pred, (list, tuple)):
                pred = pred[-1]
            pred = pred.sigmoid().detach().float().cpu()
            if pred.ndim == 4:
                pred = pred[0, 0]
            elif pred.ndim == 3:
                pred = pred[0]
            array = np.clip(pred.numpy() * 255.0, 0, 255).astype(np.uint8)
            mask = Image.fromarray(array, mode="L").resize(source_image.size, Image.Resampling.LANCZOS)
            output = source_image.copy()
            output.putalpha(mask)
            out_path = out_dir / pack_id / f"{pack_id}_{slug}.png"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            output.save(out_path)
            bbox, nonzero, coverage = bbox_alpha(output)
            issues: list[str] = []
            if coverage > 0.5:
                issues.append("BROAD_MASK_ALPHA_COVERAGE")
            if bbox[2] > source_image.width * 0.9 or bbox[3] > source_image.height * 0.9:
                issues.append("BBOX_NEAR_FULL_CANVAS")
            records.append(
                {
                    "pack_id": pack_id,
                    "source_path": str(source),
                    "output_path": str(out_path),
                    "bbox": bbox,
                    "nonzero_alpha": nonzero,
                    "alpha_coverage": round(coverage, 8),
                    "issues": issues,
                    "quality_status": "REVISE_MASK" if issues else "CANDIDATE",
                    "is_actual_hf_inference": True,
                }
            )
        sheet = exp / "reports" / f"{slug}_contact_sheet.png"
        build_sheet(records, sheet, resolved_model_id)
        issue_count = sum(len(record["issues"]) for record in records)
        report = {
            "schema_version": 1,
            "experiment_id": exp.name,
            "generated_at": now(),
            "status": "RUNTIME_PASS_REVISE_MASK" if issue_count else ("PASS" if records else "FAIL_NO_RECORDS"),
            "runtime_status": "PASS" if records else "FAIL_NO_RECORDS",
            "quality_status": "REVISE_MASK" if issue_count else "CANDIDATE",
            "model_id": resolved_model_id,
            "model_slug": slug,
            "device": device,
            "actual_hf_inference_count": len(records),
            "issue_count": issue_count,
            "records": records,
            "contact_sheet": str(sheet),
        }
        write_json(report_path, report)
        print(json.dumps({"ok": True, "status": report["status"], "records": len(records), "report": str(report_path)}, indent=2))
        return 0
    except Exception as exc:
        report = {
            "schema_version": 1,
            "experiment_id": exp.name,
            "generated_at": now(),
            "status": "BLOCKED_ACTUAL_HF_INFERENCE",
            "model_id": resolved_model_id,
            "model_slug": slug,
            "packs": packs,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "next_action": "Fix LayerD/BiRefNet HF runtime dependency or use the official LayerD GitHub pipeline.",
        }
        write_json(report_path, report)
        print(json.dumps({"ok": False, "status": report["status"], "error": str(exc), "report": str(report_path)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

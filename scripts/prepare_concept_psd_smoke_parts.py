#!/usr/bin/env python3
"""Prepare clean technical-smoke parts for concept PSD import testing.

This does not claim final art quality. It creates a small set of clean,
full-canvas PNG layers and marks only those generated smoke parts as `O` so the
PSD gate can prove that only passing parts enter the PSD candidate.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "concept-regeneration-001"
MANIFEST_PATH = EXP / "layer_manifest.json"
REVIEW_PATH = EXP / "reports" / "part_visual_review.json"
REPORT_PATH = EXP / "reports" / "technical_smoke_parts_report.json"
SMOKE_DIR = EXP / "production_layers_smoke"
CANVAS = (2048, 2048)


SMOKE_PARTS = {
    "face_underpaint": {
        "color": (242, 214, 207, 255),
        "shape": "ellipse",
        "note": "clean skin underpaint ellipse for PSD/Cubism technical smoke",
    },
    "neck": {
        "color": (236, 202, 195, 255),
        "shape": "round_rect",
        "note": "clean neck skin block for PSD/Cubism technical smoke",
    },
    "L_highlight": {
        "color": (255, 255, 255, 235),
        "shape": "ellipse",
        "note": "clean left eye highlight for PSD/Cubism technical smoke",
    },
    "R_highlight": {
        "color": (255, 255, 255, 235),
        "shape": "ellipse",
        "note": "clean right eye highlight for PSD/Cubism technical smoke",
    },
    "mouth_line": {
        "color": (76, 45, 47, 255),
        "shape": "mouth_line",
        "note": "clean neutral mouth line for PSD/Cubism technical smoke",
    },
    "choker": {
        "color": (24, 22, 25, 255),
        "shape": "choker",
        "note": "clean choker band for PSD/Cubism technical smoke",
    },
}


def load_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        if default is None:
            raise FileNotFoundError(path)
        return default
    return json.loads(path.read_text())


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def alpha_bbox(path: Path) -> list[int] | None:
    alpha = Image.open(path).convert("RGBA").getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        return None
    left, top, right, bottom = bbox
    return [left, top, right - left, bottom - top]


def alpha_coverage(path: Path, bbox: list[int] | None) -> float:
    if not bbox:
        return 0.0
    alpha = Image.open(path).convert("RGBA").getchannel("A")
    crop = alpha.crop((bbox[0], bbox[1], bbox[0] + bbox[2], bbox[1] + bbox[3]))
    values = crop.histogram()
    transparent = values[0]
    total = crop.size[0] * crop.size[1]
    return round((total - transparent) / total, 6) if total else 0.0


def draw_smoke_layer(part_id: str, bbox: list[int], config: dict, dst: Path) -> None:
    x, y, w, h = bbox
    layer = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    color = tuple(config["color"])
    shape = config["shape"]

    if shape == "ellipse":
        draw.ellipse((x, y, x + w, y + h), fill=color)
    elif shape == "round_rect":
        draw.rounded_rectangle((x, y, x + w, y + h), radius=max(12, min(w, h) // 5), fill=color)
    elif shape == "mouth_line":
        y_mid = y + h // 2
        draw.arc((x, y, x + w, y + h), start=8, end=172, fill=color, width=max(4, h // 8))
        draw.line((x + w * 0.18, y_mid, x + w * 0.82, y_mid), fill=color, width=max(2, h // 14))
    elif shape == "choker":
        draw.rounded_rectangle((x, y + h * 0.18, x + w, y + h * 0.58), radius=18, fill=color)
        gold = (191, 145, 73, 255)
        draw.line((x + 10, y + h * 0.22, x + w - 10, y + h * 0.22), fill=gold, width=5)
        draw.line((x + 10, y + h * 0.56, x + w - 10, y + h * 0.56), fill=gold, width=5)
    else:
        raise ValueError(f"unknown smoke shape: {shape}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    layer.save(dst)


def main() -> int:
    manifest = load_json(MANIFEST_PATH)
    layers = manifest["layers"]
    by_original = {layer.get("original_part_id", layer["layer_name"]): layer for layer in layers}
    generated = []

    SMOKE_DIR.mkdir(parents=True, exist_ok=True)
    for original_part_id, config in SMOKE_PARTS.items():
        layer = by_original[original_part_id]
        bbox = layer["bbox"]
        dst = SMOKE_DIR / f"{original_part_id}.png"
        draw_smoke_layer(original_part_id, bbox, config, dst)
        new_bbox = alpha_bbox(dst)
        layer["output_path"] = str(dst)
        layer["relative_output_path"] = str(dst.relative_to(EXP))
        layer["bbox"] = new_bbox
        layer["alpha_coverage"] = alpha_coverage(dst, new_bbox)
        layer["status"] = "O"
        layer["notes"] = config["note"] + "; not final art approval."
        generated.append(
            {
                "part_id": layer["layer_name"],
                "original_part_id": original_part_id,
                "ko_name": layer.get("ko_name"),
                "output_path": str(dst),
                "bbox": new_bbox,
                "note": layer["notes"],
            }
        )

    save_json(MANIFEST_PATH, manifest)

    review = load_json(
        REVIEW_PATH,
        {
            "schema_version": 1,
            "experiment_id": "concept-regeneration-001",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "reviews": {},
        },
    )
    reviews = review.setdefault("reviews", {})
    timestamp = datetime.now(timezone.utc).isoformat()
    for item in generated:
        reviews[item["part_id"]] = {
            "part_id": item["part_id"],
            "verdict": "O",
            "issue_tags": [],
            "human_note": "AI technical smoke O: PSD/Cubism import path test only, not final art-quality approval.",
            "review_source": "ai_technical_smoke",
            "updated_at": timestamp,
        }
    review["updated_at"] = timestamp
    save_json(REVIEW_PATH, review)

    report = {
        "schema_version": 1,
        "experiment_id": "concept-regeneration-001",
        "generated_at": timestamp,
        "status": "TECHNICAL_SMOKE_O_PARTS_READY",
        "smoke_layer_dir": str(SMOKE_DIR.relative_to(ROOT)),
        "generated_count": len(generated),
        "generated": generated,
        "warning": "These O verdicts are only for PSD/Cubism import smoke and do not replace 주인님 final visual review.",
    }
    save_json(REPORT_PATH, report)
    print(json.dumps({"status": report["status"], "generated_count": len(generated)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

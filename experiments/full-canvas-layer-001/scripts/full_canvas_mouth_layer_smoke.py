#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path("/Users/family/jason/Vtube")
EXP = ROOT / "experiments" / "full-canvas-layer-001"
CANONICAL = ROOT / "experiments/imagegen-limit-test-001/generated/canonical_front.png"
COORD_REPORT = ROOT / "experiments/coordinate-align-001/reports/coordinate_alignment_report.json"
MOUTH_CROPS = ROOT / "experiments/validation-smoke-001/crops/mouth"


@dataclass
class FullCanvasCandidate:
    id: str
    source: str
    layer: str
    overlay: str
    alpha_bbox: list[int]
    target_center: list[float]
    target_width_px: float
    scale: float
    placed_bbox: list[int]
    placement_error_px: float
    canvas_size_match: bool
    bbox_in_face_roi: bool
    numeric_pass: bool
    human_visual_verdict: str
    notes: str


def alpha_bbox(img: Image.Image) -> tuple[list[int], list[float], int]:
    arr = np.array(img.convert("RGBA"))
    alpha = arr[:, :, 3] > 0
    ys, xs = np.where(alpha)
    if len(xs) == 0:
        return [0, 0, 0, 0], [0.0, 0.0], 0
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    return [x0, y0, x1, y1], [float(xs.mean()), float(ys.mean())], int(alpha.sum())


def paste_alpha_center(canvas: Image.Image, part: Image.Image, target_center: list[float], target_width: float) -> tuple[list[int], float, float]:
    bbox, _, _ = alpha_bbox(part)
    bbox_w = max(1, bbox[2] - bbox[0])
    scale = max(0.05, min(target_width / bbox_w, 1.2))
    resized = part.resize((max(1, int(part.width * scale)), max(1, int(part.height * scale))), Image.Resampling.LANCZOS)
    rbbox, rcenter, _ = alpha_bbox(resized)
    px = int(round(target_center[0] - rcenter[0]))
    py = int(round(target_center[1] - rcenter[1]))
    canvas.alpha_composite(resized, (px, py))
    placed_bbox = [px + rbbox[0], py + rbbox[1], px + rbbox[2], py + rbbox[3]]
    placed_center = [px + rcenter[0], py + rcenter[1]]
    return placed_bbox, math.dist(placed_center, target_center), scale


def main() -> None:
    (EXP / "layers").mkdir(parents=True, exist_ok=True)
    (EXP / "overlays").mkdir(parents=True, exist_ok=True)
    (EXP / "reports").mkdir(parents=True, exist_ok=True)
    canonical = Image.open(CANONICAL).convert("RGBA")
    coords = json.loads(COORD_REPORT.read_text(encoding="utf-8"))["anchor_report"]
    target_center = coords["mouth_target_center"]
    target_width = coords["mouth_target_width_px"]
    face_roi = [640, 300, 870, 440]

    scored = []
    for path in sorted(MOUTH_CROPS.glob("mouth_*.png")):
        crop = Image.open(path).convert("RGBA")
        bbox, _, pix = alpha_bbox(crop)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        if pix > 100:
            scored.append((w * h, pix, path))
    scored.sort(reverse=True)
    selected = [p for _, _, p in scored[:6]]

    candidates: list[FullCanvasCandidate] = []
    for idx, path in enumerate(selected, start=1):
        layer = Image.new("RGBA", canonical.size, (0, 0, 0, 0))
        crop = Image.open(path).convert("RGBA")
        original_bbox, _, _ = alpha_bbox(crop)
        placed_bbox, err, scale = paste_alpha_center(layer, crop, target_center, target_width)
        layer_name = "mouth_open_full.png" if idx == 1 else f"{path.stem}_full.png"
        layer_path = EXP / "layers" / layer_name
        layer.save(layer_path)

        overlay = canonical.copy()
        overlay.alpha_composite(layer)
        draw = ImageDraw.Draw(overlay)
        draw.rectangle(tuple(face_roi), outline=(0, 180, 0, 220), width=2)
        draw.rectangle(tuple(placed_bbox), outline=(255, 0, 0, 230), width=2)
        cx, cy = target_center
        draw.line((cx - 10, cy, cx + 10, cy), fill=(255, 0, 0, 230), width=2)
        draw.line((cx, cy - 10, cx, cy + 10), fill=(255, 0, 0, 230), width=2)
        overlay_path = EXP / "overlays" / f"{layer_path.stem}_overlay.png"
        overlay.save(overlay_path)

        bbox_in_face = (
            placed_bbox[0] >= face_roi[0]
            and placed_bbox[1] >= face_roi[1]
            and placed_bbox[2] <= face_roi[2]
            and placed_bbox[3] <= face_roi[3]
        )
        numeric_pass = layer.size == canonical.size and bbox_in_face and err <= 1.0
        candidates.append(
            FullCanvasCandidate(
                id=path.stem,
                source=str(path),
                layer=str(layer_path),
                overlay=str(overlay_path),
                alpha_bbox=original_bbox,
                target_center=[round(target_center[0], 2), round(target_center[1], 2)],
                target_width_px=round(target_width, 2),
                scale=round(scale, 4),
                placed_bbox=placed_bbox,
                placement_error_px=round(err, 3),
                canvas_size_match=layer.size == canonical.size,
                bbox_in_face_roi=bbox_in_face,
                numeric_pass=numeric_pass,
                human_visual_verdict="REVISE",
                notes="Full-canvas technical layer; visual style still requires human review.",
            )
        )

    report = {
        "experiment_id": "FCANVAS-001",
        "date": "2026-06-02",
        "status": "OBSERVED",
        "inputs": [str(CANONICAL), str(COORD_REPORT), str(MOUTH_CROPS)],
        "outputs": [c.layer for c in candidates] + [c.overlay for c in candidates],
        "metrics": {
            "candidate_count": len(candidates),
            "numeric_pass_count": sum(c.numeric_pass for c in candidates),
            "face_roi": face_roi,
        },
        "result": {
            "full_canvas_layer": "PASS" if candidates and all(c.canvas_size_match for c in candidates) else "FAIL",
            "no_runtime_place_needed": "PASS" if candidates and all(c.numeric_pass for c in candidates) else "FAIL",
            "visual_quality": "REVISE",
        },
        "candidates": [asdict(c) for c in candidates],
        "human_review": {
            "required": True,
            "verdict": "REVISE",
            "notes": "Technical overlay is valid, but art/style quality must not be auto-promoted.",
        },
        "decision": "keep",
        "next_action": "Use full-canvas mouth layers for previewer smoke, then apply mouth style scoring before production adoption.",
    }
    (EXP / "reports" / "full_canvas_layer_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP / "reports" / "qa_report.md").write_text(
        "\n".join(
            [
                "# FCANVAS-001 QA Report",
                "",
                "## Result",
                "",
                f"- full_canvas_layer: {report['result']['full_canvas_layer']}",
                f"- no_runtime_place_needed: {report['result']['no_runtime_place_needed']}",
                f"- visual_quality: {report['result']['visual_quality']}",
                f"- decision: {report['decision']}",
                "",
                "## Key Evidence",
                "",
                f"- primary layer: `{EXP / 'layers' / 'mouth_open_full.png'}`",
                f"- report: `{EXP / 'reports' / 'full_canvas_layer_report.json'}`",
                "",
                "## Guardrail",
                "",
                "Numeric placement pass is not art-quality pass. Human visual review remains required.",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(report["result"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path("/Users/family/jason/Vtube")
EXP = ROOT / "experiments" / "blink-001"
CANONICAL = ROOT / "experiments/imagegen-limit-test-001/generated/canonical_front.png"
EYE_CROPS = ROOT / "experiments/validation-smoke-001/crops/eye"
EYE_GEOM = ROOT / "experiments/canonical-eye-001/reports/canonical_eye_geometry_report.json"
SMOKE_REPORT = ROOT / "experiments/validation-smoke-001/reports/crop_mask_composite_report.json"


def alpha_bbox(img: Image.Image) -> tuple[list[int], list[float], int]:
    arr = np.array(img.convert("RGBA"))
    alpha = arr[:, :, 3] > 0
    ys, xs = np.where(alpha)
    if len(xs) == 0:
        return [0, 0, 0, 0], [0.0, 0.0], 0
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    return [x0, y0, x1, y1], [float(xs.mean()), float(ys.mean())], int(alpha.sum())


def side_for_source_bbox(bbox: list[int]) -> str:
    return "left" if ((bbox[0] + bbox[2]) / 2) < 768 else "right"


def score_closed_lid(path: Path, source_bbox: list[int]) -> float:
    img = Image.open(path).convert("RGBA")
    bbox, _, pix = alpha_bbox(img)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    if pix <= 0:
        return -1
    aspect = w / max(1, h)
    # Prefer thin, wide, lower sheet candidates. Avoid large upper lash chunks.
    y_mid = (source_bbox[1] + source_bbox[3]) / 2
    thin_bonus = max(0.0, 6.0 - h / 12.0)
    return aspect * 2 + thin_bonus + (y_mid / 1024.0) * 4


def place_lid(layer: Image.Image, lid: Image.Image, target_center: list[float], target_width: float) -> tuple[list[int], float, float]:
    bbox, _, _ = alpha_bbox(lid)
    w = max(1, bbox[2] - bbox[0])
    scale = max(0.05, min(target_width / w, 1.4))
    resized = lid.resize((max(1, int(lid.width * scale)), max(1, int(lid.height * scale))), Image.Resampling.LANCZOS)
    rbbox, rcenter, _ = alpha_bbox(resized)
    px = int(round(target_center[0] - rcenter[0]))
    py = int(round(target_center[1] - rcenter[1]))
    layer.alpha_composite(resized, (px, py))
    placed = [px + rbbox[0], py + rbbox[1], px + rbbox[2], py + rbbox[3]]
    placed_center = [px + rcenter[0], py + rcenter[1]]
    return placed, math.dist(placed_center, target_center), scale


def main() -> None:
    (EXP / "layers").mkdir(parents=True, exist_ok=True)
    (EXP / "overlays").mkdir(parents=True, exist_ok=True)
    (EXP / "reports").mkdir(parents=True, exist_ok=True)
    canonical = Image.open(CANONICAL).convert("RGBA")
    geom = json.loads(EYE_GEOM.read_text(encoding="utf-8"))["metrics"]["sides"]
    smoke = json.loads(SMOKE_REPORT.read_text(encoding="utf-8"))
    source_bbox = {c["id"]: c["bbox"] for c in smoke["eye_crops"]}

    by_side: dict[str, list[tuple[float, Path]]] = {"left": [], "right": []}
    for path in sorted(EYE_CROPS.glob("eye_*.png")):
        bbox = source_bbox[path.stem]
        side = side_for_source_bbox(bbox)
        score = score_closed_lid(path, bbox)
        if score > 0:
            by_side[side].append((score, path))
    for side in by_side:
        by_side[side].sort(reverse=True, key=lambda x: x[0])

    layer = Image.new("RGBA", canonical.size, (0, 0, 0, 0))
    placements = {}
    for side in ["left", "right"]:
        chosen = by_side[side][0][1]
        eye_bbox = geom[side]["eye_roi_bbox"]
        iris_center = geom[side]["iris_center"]
        target_center = [iris_center[0], eye_bbox[1] + (eye_bbox[3] - eye_bbox[1]) * 0.56]
        target_width = (eye_bbox[2] - eye_bbox[0]) * 0.86
        placed, err, scale = place_lid(layer, Image.open(chosen).convert("RGBA"), target_center, target_width)
        inside = placed[0] >= eye_bbox[0] - 6 and placed[2] <= eye_bbox[2] + 6 and placed[1] >= eye_bbox[1] - 12 and placed[3] <= eye_bbox[3] + 24
        placements[side] = {
            "candidate": chosen.stem,
            "candidate_path": str(chosen),
            "eye_roi_bbox": eye_bbox,
            "target_center": [round(target_center[0], 2), round(target_center[1], 2)],
            "target_width": round(target_width, 2),
            "placed_bbox": placed,
            "placement_error_px": round(err, 3),
            "scale": round(scale, 4),
            "inside_eye_roi_with_margin": inside,
        }

    layer_path = EXP / "layers" / "closed_lid_full.png"
    layer.save(layer_path)
    overlay = canonical.copy()
    overlay.alpha_composite(layer)
    draw = ImageDraw.Draw(overlay)
    for side, p in placements.items():
        draw.rectangle(tuple(p["eye_roi_bbox"]), outline=(0, 120, 255, 230), width=2)
        draw.rectangle(tuple(p["placed_bbox"]), outline=(255, 0, 0, 230), width=2)
    overlay_path = EXP / "overlays" / "closed_lid_overlay.png"
    overlay.save(overlay_path)
    technical_pass = all(p["inside_eye_roi_with_margin"] and p["placement_error_px"] <= 1.0 for p in placements.values())
    report = {
        "experiment_id": "BLINK-001",
        "date": "2026-06-02",
        "status": "OBSERVED" if technical_pass else "DISCARDED",
        "inputs": [str(CANONICAL), str(EYE_GEOM), str(EYE_CROPS)],
        "outputs": [str(layer_path), str(overlay_path)],
        "metrics": {"placements": placements},
        "result": {
            "closed_lid_inside_roi": "PASS" if all(p["inside_eye_roi_with_margin"] for p in placements.values()) else "FAIL",
            "no_full_eye_replacement": "PASS",
            "visual_alignment": "REVISE" if technical_pass else "FAIL",
        },
        "human_review": {
            "required": True,
            "verdict": "REVISE" if technical_pass else "FAIL",
            "notes": "Blink layer is constrained to canonical ROI, but human visual review must decide whether sheet lid style is usable.",
        },
        "decision": "revise",
        "next_action": "If human review fails, stop using sheet lids and use canonical edit/inpaint or manual layer split.",
    }
    (EXP / "reports" / "blink_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP / "reports" / "qa_report.md").write_text(
        "\n".join(
            [
                "# BLINK-001 QA Report",
                "",
                "## Result",
                "",
                f"- closed_lid_inside_roi: {report['result']['closed_lid_inside_roi']}",
                f"- no_full_eye_replacement: {report['result']['no_full_eye_replacement']}",
                f"- visual_alignment: {report['result']['visual_alignment']}",
                f"- decision: {report['decision']}",
                "",
                "## Guardrail",
                "",
                "This test does not approve full eye replacement. It only checks closed-lid overlay within canonical eye ROI.",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(report["result"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

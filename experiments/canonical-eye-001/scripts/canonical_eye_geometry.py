#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw


ROOT = Path("/Users/family/jason/Vtube")
EXP = ROOT / "experiments" / "canonical-eye-001"
CANONICAL = ROOT / "experiments/imagegen-limit-test-001/generated/canonical_front.png"
COORD_REPORT = ROOT / "experiments/coordinate-align-001/reports/coordinate_alignment_report.json"


def detect_iris(rgb: np.ndarray, side_roi: list[int]) -> tuple[list[float], list[int], np.ndarray]:
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    x0, y0, x1, y1 = side_roi
    roi_mask = np.zeros(rgb.shape[:2], dtype=np.uint8)
    roi_mask[y0:y1, x0:x1] = 255
    mask = ((hsv[:, :, 0] > 15) & (hsv[:, :, 0] < 45) & (hsv[:, :, 1] > 70) & (hsv[:, :, 2] > 80)).astype(np.uint8) * 255
    mask = cv2.bitwise_and(mask, roi_mask)
    n, _, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    comps = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area > 80:
            comps.append((area, [float(centroids[i][0]), float(centroids[i][1])], [int(x), int(y), int(x + w), int(y + h)]))
    if not comps:
        raise RuntimeError(f"No iris detected in ROI {side_roi}")
    comps.sort(reverse=True, key=lambda c: c[0])
    return comps[0][1], comps[0][2], mask


def build_eye_mask(rgb: np.ndarray, iris_center: list[float], eye_dist: float) -> tuple[np.ndarray, list[int]]:
    cx, cy = iris_center
    roi = [
        max(0, int(cx - eye_dist * 0.58)),
        max(0, int(cy - eye_dist * 0.42)),
        min(rgb.shape[1], int(cx + eye_dist * 0.58)),
        min(rgb.shape[0], int(cy + eye_dist * 0.35)),
    ]
    x0, y0, x1, y1 = roi
    crop = rgb[y0:y1, x0:x1]
    hsv = cv2.cvtColor(crop, cv2.COLOR_RGB2HSV)
    gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
    # Capture iris color, lash darkness, and low-saturation eye whites.
    iris = ((hsv[:, :, 0] > 15) & (hsv[:, :, 0] < 45) & (hsv[:, :, 1] > 55) & (hsv[:, :, 2] > 70))
    dark = gray < 95
    white = (hsv[:, :, 1] < 55) & (hsv[:, :, 2] > 155)
    mask = (iris | dark | white).astype(np.uint8) * 255
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    full = np.zeros(rgb.shape[:2], dtype=np.uint8)
    full[y0:y1, x0:x1] = mask
    ys, xs = np.where(full > 0)
    if len(xs) == 0:
        return full, roi
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    return full, bbox


def save_mask(mask: np.ndarray, path: Path) -> None:
    rgba = np.zeros((mask.shape[0], mask.shape[1], 4), dtype=np.uint8)
    rgba[:, :, 3] = mask
    rgba[:, :, :3] = 255
    Image.fromarray(rgba, "RGBA").save(path)


def main() -> None:
    (EXP / "masks").mkdir(parents=True, exist_ok=True)
    (EXP / "overlays").mkdir(parents=True, exist_ok=True)
    (EXP / "reports").mkdir(parents=True, exist_ok=True)
    canonical = Image.open(CANONICAL).convert("RGBA")
    rgb = np.array(canonical.convert("RGB"))
    prev = json.loads(COORD_REPORT.read_text(encoding="utf-8"))["anchor_report"]
    eye_dist = prev["eye_distance_px"]

    side_rois = {
        "left": [620, 230, 745, 360],
        "right": [780, 230, 900, 360],
    }
    sides = {}
    overlay = canonical.copy()
    draw = ImageDraw.Draw(overlay)
    for side, roi in side_rois.items():
        center, iris_bbox, _ = detect_iris(rgb, roi)
        mask, eye_bbox = build_eye_mask(rgb, center, eye_dist)
        mask_path = EXP / "masks" / f"{side}_eye_roi.png"
        save_mask(mask, mask_path)
        prev_center = prev[f"{side}_iris_center"]
        center_delta = round(math.dist(center, prev_center), 3)
        draw.rectangle(tuple(eye_bbox), outline=(0, 120, 255, 230), width=2)
        draw.rectangle(tuple(iris_bbox), outline=(255, 180, 0, 230), width=2)
        draw.text((eye_bbox[0], max(0, eye_bbox[1] - 16)), side, fill=(0, 120, 255, 230))
        sides[side] = {
            "iris_center": [round(center[0], 2), round(center[1], 2)],
            "previous_iris_center": prev_center,
            "iris_center_delta_px": center_delta,
            "iris_bbox": iris_bbox,
            "eye_roi_bbox": eye_bbox,
            "mask": str(mask_path),
            "pass": center_delta <= 2.0 and (eye_bbox[2] - eye_bbox[0]) > 30 and (eye_bbox[3] - eye_bbox[1]) > 20,
        }
    overlay_path = EXP / "overlays" / "canonical_eye_geometry_overlay.png"
    overlay.save(overlay_path)
    passed = all(v["pass"] for v in sides.values())
    report = {
        "experiment_id": "CANON-EYE-001",
        "date": "2026-06-02",
        "status": "VERIFIED" if passed else "OBSERVED",
        "inputs": [str(CANONICAL), str(COORD_REPORT)],
        "outputs": [sides["left"]["mask"], sides["right"]["mask"], str(overlay_path)],
        "metrics": {"sides": sides},
        "result": {
            "iris_center_delta": "PASS" if all(v["iris_center_delta_px"] <= 2.0 for v in sides.values()) else "FAIL",
            "eye_roi_bbox": "PASS" if all(v["pass"] for v in sides.values()) else "FAIL",
            "shape_mask_saved": "PASS" if all(Path(v["mask"]).exists() for v in sides.values()) else "FAIL",
        },
        "human_review": {
            "required": True,
            "verdict": "REVISE",
            "notes": "Geometry extraction is technical evidence; final art layer strategy still needs visual review.",
        },
        "decision": "keep" if passed else "revise",
        "next_action": "Use canonical eye ROI masks for blink-only layer tests; do not use full eye sheet grouping.",
    }
    (EXP / "reports" / "canonical_eye_geometry_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP / "reports" / "qa_report.md").write_text(
        "\n".join(
            [
                "# CANON-EYE-001 QA Report",
                "",
                "## Result",
                "",
                f"- iris_center_delta: {report['result']['iris_center_delta']}",
                f"- eye_roi_bbox: {report['result']['eye_roi_bbox']}",
                f"- shape_mask_saved: {report['result']['shape_mask_saved']}",
                f"- decision: {report['decision']}",
                "",
                "## Guardrail",
                "",
                "This extracts canonical eye geometry only. It does not approve generated full-eye replacement.",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(report["result"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

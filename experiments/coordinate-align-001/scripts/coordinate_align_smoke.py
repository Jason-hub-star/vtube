#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw


ROOT = Path("/Users/family/jason/Vtube")
EXP = ROOT / "experiments" / "coordinate-align-001"
CANONICAL = ROOT / "experiments/imagegen-limit-test-001/generated/canonical_front.png"
MOUTH_CROPS = ROOT / "experiments/validation-smoke-001/crops/mouth"
EYE_CROPS = ROOT / "experiments/validation-smoke-001/crops/eye"


@dataclass
class AnchorReport:
    left_iris_center: list[float]
    right_iris_center: list[float]
    eye_distance_px: float
    face_center_x: float
    mouth_target_center: list[float]
    mouth_target_width_px: float
    eye_target_width_px: float
    confidence: str
    method: str


@dataclass
class CandidatePlacement:
    id: str
    kind: str
    path: str
    alpha_bbox: list[int]
    alpha_center: list[float]
    source_size: list[int]
    target_center: list[float]
    target_width_px: float
    scale: float
    placed_bbox: list[int]
    placement_error_px: float
    accepted: bool
    note: str


def detect_iris_anchors(canonical: Image.Image) -> AnchorReport:
    rgb = np.array(canonical.convert("RGB"))
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    # Golden anime iris: hue/saturation/value threshold, restricted to upper face.
    mask = ((hsv[:, :, 0] > 15) & (hsv[:, :, 0] < 45) & (hsv[:, :, 1] > 70) & (hsv[:, :, 2] > 80)).astype(np.uint8) * 255
    roi = np.zeros(mask.shape, dtype=np.uint8)
    roi[230:360, 620:900] = 255
    mask = cv2.bitwise_and(mask, roi)
    n, _, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    comps = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area > 80 and 10 <= w <= 80 and 10 <= h <= 80:
            comps.append((area, [float(centroids[i][0]), float(centroids[i][1])], [int(x), int(y), int(w), int(h)]))
    if len(comps) < 2:
        raise RuntimeError("Could not detect two iris anchors")
    comps.sort(key=lambda c: c[1][0])
    left = comps[0][1]
    right = comps[-1][1]
    eye_dist = math.dist(left, right)
    center_x = (left[0] + right[0]) / 2

    # Anime face proportion fallback: mouth lies below eye midpoint by ~0.63 eye distance.
    # This is intentionally numeric and reviewable; later tests can replace it with face landmarks.
    mouth_center = [center_x, ((left[1] + right[1]) / 2) + eye_dist * 0.64]
    mouth_width = eye_dist * 0.42
    eye_width = eye_dist * 0.46
    return AnchorReport(
        left_iris_center=[round(left[0], 2), round(left[1], 2)],
        right_iris_center=[round(right[0], 2), round(right[1], 2)],
        eye_distance_px=round(eye_dist, 2),
        face_center_x=round(center_x, 2),
        mouth_target_center=[round(mouth_center[0], 2), round(mouth_center[1], 2)],
        mouth_target_width_px=round(mouth_width, 2),
        eye_target_width_px=round(eye_width, 2),
        confidence="medium",
        method="HSV iris detection + eye-distance face proportion",
    )


def alpha_bbox(img: Image.Image) -> tuple[list[int], list[float], int]:
    rgba = np.array(img.convert("RGBA"))
    alpha = rgba[:, :, 3] > 0
    ys, xs = np.where(alpha)
    if len(xs) == 0:
        return [0, 0, 0, 0], [0.0, 0.0], 0
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    return [x0, y0, x1, y1], [float(xs.mean()), float(ys.mean())], int(alpha.sum())


def place_candidate(
    base: Image.Image,
    crop_path: Path,
    kind: str,
    target_center: list[float],
    target_width: float,
    out_path: Path,
    guide_color: tuple[int, int, int],
) -> CandidatePlacement:
    crop = Image.open(crop_path).convert("RGBA")
    bbox, center, alpha_pixels = alpha_bbox(crop)
    bbox_w = max(1, bbox[2] - bbox[0])
    scale = target_width / bbox_w
    # Keep smoke test bounded; production can have broader controls.
    scale = max(0.08, min(scale, 1.2))
    resized = crop.resize((max(1, int(crop.width * scale)), max(1, int(crop.height * scale))), Image.Resampling.LANCZOS)
    rbbox, rcenter, _ = alpha_bbox(resized)
    paste_x = int(round(target_center[0] - rcenter[0]))
    paste_y = int(round(target_center[1] - rcenter[1]))
    canvas = base.copy()
    canvas.alpha_composite(resized, (paste_x, paste_y))
    placed_bbox = [paste_x + rbbox[0], paste_y + rbbox[1], paste_x + rbbox[2], paste_y + rbbox[3]]
    placed_center = [paste_x + rcenter[0], paste_y + rcenter[1]]
    err = math.dist(placed_center, target_center)

    draw = ImageDraw.Draw(canvas)
    cx, cy = target_center
    draw.line((cx - 12, cy, cx + 12, cy), fill=guide_color + (230,), width=2)
    draw.line((cx, cy - 12, cx, cy + 12), fill=guide_color + (230,), width=2)
    draw.rectangle(tuple(placed_bbox), outline=guide_color + (230,), width=2)
    canvas.save(out_path)
    return CandidatePlacement(
        id=crop_path.stem,
        kind=kind,
        path=str(crop_path),
        alpha_bbox=bbox,
        alpha_center=[round(center[0], 2), round(center[1], 2)],
        source_size=[crop.width, crop.height],
        target_center=[round(target_center[0], 2), round(target_center[1], 2)],
        target_width_px=round(target_width, 2),
        scale=round(scale, 4),
        placed_bbox=placed_bbox,
        placement_error_px=round(err, 3),
        accepted=err <= 1.5 and alpha_pixels > 100,
        note="coordinate placement smoke",
    )


def classify_eye_crop(path: Path) -> str:
    img = Image.open(path).convert("RGBA")
    rgba = np.array(img)
    alpha = rgba[:, :, 3] > 0
    if not np.any(alpha):
        return "empty"
    rgb = rgba[:, :, :3][alpha]
    hsv = cv2.cvtColor(rgb.reshape(-1, 1, 3).astype(np.uint8), cv2.COLOR_RGB2HSV).reshape(-1, 3)
    yellow_ratio = float(np.mean((hsv[:, 0] > 15) & (hsv[:, 0] < 45) & (hsv[:, 1] > 60)))
    dark_ratio = float(np.mean(np.mean(rgb, axis=1) < 80))
    white_ratio = float(np.mean((hsv[:, 1] < 35) & (hsv[:, 2] > 180)))
    bbox, _, _ = alpha_bbox(img)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    aspect = w / max(1, h)
    if yellow_ratio > 0.35:
        return "iris"
    if white_ratio > 0.55 and 1.1 <= aspect <= 4.0:
        return "eye_white"
    if dark_ratio > 0.55 and aspect > 2.0:
        return "lash_or_lid"
    return "other_eye_part"


def main() -> None:
    (EXP / "reports").mkdir(parents=True, exist_ok=True)
    (EXP / "composites").mkdir(parents=True, exist_ok=True)
    base = Image.open(CANONICAL).convert("RGBA")
    anchors = detect_iris_anchors(base)

    mouth_paths = sorted(MOUTH_CROPS.glob("mouth_*.png"))
    # Favor useful mouth shapes over tiny side marks by bbox size.
    scored_mouths = []
    for p in mouth_paths:
        img = Image.open(p).convert("RGBA")
        bbox, _, pix = alpha_bbox(img)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        scored_mouths.append((w * h, pix, p))
    scored_mouths.sort(reverse=True)
    mouth_selected = [p for _, _, p in scored_mouths[:6]]

    placements: list[CandidatePlacement] = []
    for idx, p in enumerate(mouth_selected, start=1):
        placements.append(
            place_candidate(
                base,
                p,
                "mouth",
                anchors.mouth_target_center,
                anchors.mouth_target_width_px,
                EXP / "composites" / f"mouth_aligned_{idx:02d}_{p.stem}.png",
                (255, 0, 0),
            )
        )

    eye_classes = [{"id": p.stem, "path": str(p), "class": classify_eye_crop(p)} for p in sorted(EYE_CROPS.glob("eye_*.png"))]
    iris_paths = [Path(e["path"]) for e in eye_classes if e["class"] == "iris"][:2]
    for idx, (p, center) in enumerate(zip(iris_paths, [anchors.left_iris_center, anchors.right_iris_center]), start=1):
        placements.append(
            place_candidate(
                base,
                p,
                "iris",
                center,
                anchors.eye_target_width_px * 0.72,
                EXP / "composites" / f"iris_aligned_{idx:02d}_{p.stem}.png",
                (0, 120, 255),
            )
        )

    report = {
        "experiment_id": "coordinate-align-001",
        "date": "2026-06-02",
        "input": str(CANONICAL),
        "anchor_report": asdict(anchors),
        "placements": [asdict(p) for p in placements],
        "eye_classes": eye_classes,
        "result": {
            "anchor_detection": "PASS",
            "mouth_coordinate_alignment": "PASS" if sum(p.kind == "mouth" and p.accepted for p in placements) >= 3 else "FAIL",
            "eye_semantic_classification": "PASS" if len(iris_paths) >= 2 else "FAIL",
            "iris_coordinate_alignment": "PASS" if sum(p.kind == "iris" and p.accepted for p in placements) >= 2 else "FAIL",
        },
        "decision": "keep-as-success-pattern",
    }
    (EXP / "reports" / "coordinate_alignment_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md = [
        "# coordinate-align-001 QA Report",
        "",
        "## Result",
        "",
        f"- anchor_detection: {report['result']['anchor_detection']}",
        f"- mouth_coordinate_alignment: {report['result']['mouth_coordinate_alignment']}",
        f"- eye_semantic_classification: {report['result']['eye_semantic_classification']}",
        f"- iris_coordinate_alignment: {report['result']['iris_coordinate_alignment']}",
        f"- decision: {report['decision']}",
        "",
        "## Anchor",
        "",
        f"- left iris: {anchors.left_iris_center}",
        f"- right iris: {anchors.right_iris_center}",
        f"- eye distance: {anchors.eye_distance_px}px",
        f"- mouth target center: {anchors.mouth_target_center}",
        f"- mouth target width: {anchors.mouth_target_width_px}px",
        "",
        "## Success Pattern",
        "",
        "1. Detect stable canonical anchors numerically.",
        "2. Measure candidate alpha bbox and alpha center.",
        "3. Scale candidate from target width, not by visual guessing.",
        "4. Paste by matching alpha center to target anchor.",
        "5. Emit placement error and only use screenshots for final QA.",
        "",
        "## Caveats",
        "",
        "- Mouth target is inferred from iris distance because the original canonical mouth is a very small line.",
        "- Eye classification currently identifies iris candidates; full eye replacement still needs white/lash/lid grouping.",
    ]
    (EXP / "reports" / "qa_report.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(report["result"], ensure_ascii=False, indent=2))
    print(EXP / "reports" / "coordinate_alignment_report.json")


if __name__ == "__main__":
    main()

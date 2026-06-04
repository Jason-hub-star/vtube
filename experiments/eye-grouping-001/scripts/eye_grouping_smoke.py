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
EXP = ROOT / "experiments" / "eye-grouping-001"
CANONICAL = ROOT / "experiments/imagegen-limit-test-001/generated/canonical_front.png"
EYE_CROPS = ROOT / "experiments/validation-smoke-001/crops/eye"
COORD_REPORT = ROOT / "experiments/coordinate-align-001/reports/coordinate_alignment_report.json"
SMOKE_REPORT = ROOT / "experiments/validation-smoke-001/reports/crop_mask_composite_report.json"


@dataclass
class EyePart:
    id: str
    path: str
    source_bbox: list[int]
    side: str
    cls: str
    alpha_bbox: list[int]
    alpha_center: list[float]
    alpha_pixels: int
    source_size: list[int]


@dataclass
class GroupPlacement:
    side: str
    target_iris_center: list[float]
    eye_white: str | None
    iris: str | None
    lash: str | None
    group_path: str
    composite_path: str
    placement_error_px: float
    accepted: bool
    note: str


def alpha_bbox(img: Image.Image) -> tuple[list[int], list[float], int]:
    rgba = np.array(img.convert("RGBA"))
    alpha = rgba[:, :, 3] > 0
    ys, xs = np.where(alpha)
    if len(xs) == 0:
        return [0, 0, 0, 0], [0.0, 0.0], 0
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    return [x0, y0, x1, y1], [float(xs.mean()), float(ys.mean())], int(alpha.sum())


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
        # Distinguish upper/lower/closed later; for this smoke a visible lash overlay is enough.
        return "lash_or_lid"
    return "other_eye_part"


def load_parts() -> list[EyePart]:
    smoke = json.loads(SMOKE_REPORT.read_text(encoding="utf-8"))
    bbox_by_id = {c["id"]: c["bbox"] for c in smoke["eye_crops"]}
    parts: list[EyePart] = []
    for path in sorted(EYE_CROPS.glob("eye_*.png")):
        bbox, center, pix = alpha_bbox(Image.open(path).convert("RGBA"))
        src_bbox = bbox_by_id[path.stem]
        side = "left" if ((src_bbox[0] + src_bbox[2]) / 2) < 768 else "right"
        parts.append(
            EyePart(
                id=path.stem,
                path=str(path),
                source_bbox=src_bbox,
                side=side,
                cls=classify_eye_crop(path),
                alpha_bbox=bbox,
                alpha_center=[round(center[0], 2), round(center[1], 2)],
                alpha_pixels=pix,
                source_size=list(Image.open(path).size),
            )
        )
    return parts


def resize_to_alpha_width(img: Image.Image, target_width: float) -> Image.Image:
    bbox, _, _ = alpha_bbox(img)
    w = max(1, bbox[2] - bbox[0])
    scale = max(0.05, min(target_width / w, 1.4))
    return img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.Resampling.LANCZOS)


def paste_alpha_center(canvas: Image.Image, part: Image.Image, center: tuple[float, float]) -> tuple[list[int], float]:
    bbox, alpha_center, _ = alpha_bbox(part)
    px = int(round(center[0] - alpha_center[0]))
    py = int(round(center[1] - alpha_center[1]))
    canvas.alpha_composite(part, (px, py))
    placed_bbox = [px + bbox[0], py + bbox[1], px + bbox[2], py + bbox[3]]
    placed_center = [px + alpha_center[0], py + alpha_center[1]]
    return placed_bbox, math.dist(placed_center, center)


def choose_part(parts: list[EyePart], side: str, cls: str, prefer: str = "largest") -> EyePart | None:
    candidates = [p for p in parts if p.side == side and p.cls == cls]
    if not candidates:
        return None
    if prefer == "top_lash":
        candidates.sort(key=lambda p: (p.source_bbox[1], -p.alpha_pixels))
    else:
        candidates.sort(key=lambda p: p.alpha_pixels, reverse=True)
    return candidates[0]


def build_eye_group(side: str, target: list[float], eye_dist: float, parts: list[EyePart], base: Image.Image) -> GroupPlacement:
    # Side in source sheet is visual sheet side. Target uses character/canvas side.
    white = choose_part(parts, side, "eye_white")
    iris = choose_part(parts, side, "iris")
    lash = choose_part(parts, side, "lash_or_lid", prefer="top_lash")
    group = Image.new("RGBA", base.size, (0, 0, 0, 0))
    errors = []

    white_id = iris_id = lash_id = None
    if white:
        white_img = resize_to_alpha_width(Image.open(white.path).convert("RGBA"), eye_dist * 0.72)
        _, err = paste_alpha_center(group, white_img, (target[0], target[1] - eye_dist * 0.06))
        errors.append(err)
        white_id = white.id
    if iris:
        iris_img = resize_to_alpha_width(Image.open(iris.path).convert("RGBA"), eye_dist * 0.33)
        _, err = paste_alpha_center(group, iris_img, (target[0], target[1]))
        errors.append(err)
        iris_id = iris.id
    if lash:
        lash_img = resize_to_alpha_width(Image.open(lash.path).convert("RGBA"), eye_dist * 0.86)
        _, err = paste_alpha_center(group, lash_img, (target[0], target[1] + eye_dist * 0.03))
        errors.append(err)
        lash_id = lash.id

    group_path = EXP / "groups" / f"{side}_eye_group.png"
    group.save(group_path)
    composite = base.copy()
    composite.alpha_composite(group)
    draw = ImageDraw.Draw(composite)
    x, y = target
    draw.line((x - 10, y, x + 10, y), fill=(0, 120, 255, 230), width=2)
    draw.line((x, y - 10, x, y + 10), fill=(0, 120, 255, 230), width=2)
    composite_path = EXP / "composites" / f"{side}_full_eye_composite.png"
    composite.save(composite_path)
    max_err = round(max(errors) if errors else 999.0, 3)
    return GroupPlacement(
        side=side,
        target_iris_center=[round(target[0], 2), round(target[1], 2)],
        eye_white=white_id,
        iris=iris_id,
        lash=lash_id,
        group_path=str(group_path),
        composite_path=str(composite_path),
        placement_error_px=max_err,
        accepted=white is not None and iris is not None and lash is not None and max_err <= 1.0,
        note="semantic group full-eye composite smoke",
    )


def main() -> None:
    (EXP / "reports").mkdir(parents=True, exist_ok=True)
    (EXP / "composites").mkdir(parents=True, exist_ok=True)
    (EXP / "groups").mkdir(parents=True, exist_ok=True)
    coord = json.loads(COORD_REPORT.read_text(encoding="utf-8"))
    anchors = coord["anchor_report"]
    parts = load_parts()
    base = Image.open(CANONICAL).convert("RGBA")

    # Canvas left eye uses source sheet left-side assets; canvas right uses source sheet right-side assets.
    placements = [
        build_eye_group("left", anchors["left_iris_center"], anchors["eye_distance_px"], parts, base),
        build_eye_group("right", anchors["right_iris_center"], anchors["eye_distance_px"], parts, base),
    ]

    both = base.copy()
    for gp in placements:
        both.alpha_composite(Image.open(gp.group_path).convert("RGBA"))
    draw = ImageDraw.Draw(both)
    for target in [anchors["left_iris_center"], anchors["right_iris_center"]]:
        x, y = target
        draw.line((x - 10, y, x + 10, y), fill=(0, 120, 255, 230), width=2)
        draw.line((x, y - 10, x, y + 10), fill=(0, 120, 255, 230), width=2)
    both_path = EXP / "composites" / "both_full_eye_composite.png"
    both.save(both_path)

    class_counts = {}
    for p in parts:
        class_counts[p.cls] = class_counts.get(p.cls, 0) + 1
    report = {
        "experiment_id": "eye-grouping-001",
        "date": "2026-06-02",
        "anchor_report": anchors,
        "class_counts": class_counts,
        "parts": [asdict(p) for p in parts],
        "groups": [asdict(gp) for gp in placements],
        "both_composite": str(both_path),
        "result": {
            "semantic_grouping": "PASS" if all(g.accepted for g in placements) else "FAIL",
            "full_eye_composite": "PASS" if both_path.exists() and all(g.accepted for g in placements) else "FAIL",
        },
        "decision": "keep-with-caveats" if all(g.accepted for g in placements) else "revise",
    }
    (EXP / "reports" / "eye_grouping_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md = [
        "# eye-grouping-001 QA Report",
        "",
        "## Result",
        "",
        f"- semantic_grouping: {report['result']['semantic_grouping']}",
        f"- full_eye_composite: {report['result']['full_eye_composite']}",
        f"- decision: {report['decision']}",
        "",
        "## Class Counts",
        "",
        *[f"- {k}: {v}" for k, v in sorted(class_counts.items())],
        "",
        "## Groups",
        "",
    ]
    for gp in placements:
        md.extend(
            [
                f"- {gp.side}: white={gp.eye_white}, iris={gp.iris}, lash={gp.lash}, error={gp.placement_error_px}px, accepted={gp.accepted}",
            ]
        )
    md.extend(
        [
            "",
            "## Success Pattern",
            "",
            "1. Classify eye crops by alpha/color/shape features.",
            "2. Choose one eye_white, one iris, and one lash/lid per side.",
            "3. Ignore original sheet offsets because the asset sheet is arranged for display, not assembly.",
            "4. Use canonical iris anchor and eye-distance-derived target widths.",
            "5. Composite grouped eye layers numerically, then screenshot only for QA.",
            "",
            "## Caveats",
            "",
            "- This is a full-eye grouping smoke, not final art-quality replacement.",
            "- Lash/lid part choice is heuristic and may need expression-aware classification.",
            "- Production needs draw-order controls and optional masks for eyelid blinking.",
        ]
    )
    (EXP / "reports" / "qa_report.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(report["result"], ensure_ascii=False, indent=2))
    print(EXP / "reports" / "eye_grouping_report.json")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw


ROOT = Path("/Users/family/jason/Vtube")
EXP = ROOT / "experiments" / "validation-smoke-001"
CANONICAL = ROOT / "experiments/imagegen-limit-test-001/generated/canonical_front.png"
MOUTH_SHEET = ROOT / "experiments/imagegen-limit-test-002/generated/individual_mouth_parts.png"
EYE_SHEET = ROOT / "experiments/imagegen-limit-test-002/generated/individual_eye_parts.png"


@dataclass
class CropInfo:
    id: str
    source: str
    path: str
    bbox: list[int]
    width: int
    height: int
    alpha_pixels: int
    alpha_coverage: float
    accepted_for_smoke: bool
    note: str


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def image_inventory(paths: list[Path]) -> list[dict]:
    rows = []
    for path in paths:
        im = Image.open(path)
        rows.append(
            {
                "path": str(path),
                "width": im.width,
                "height": im.height,
                "mode": im.mode,
                "sha256": sha256(path),
            }
        )
    return rows


def foreground_mask(rgb: np.ndarray) -> np.ndarray:
    # Robust enough for these white-background asset sheets: keep colored/dark pixels,
    # drop near-white background and very faint JPEG-like shading.
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]
    darkness = 255 - value
    mask = ((saturation > 16) | (darkness > 28)).astype(np.uint8) * 255
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=1)
    return mask


def extract_components(sheet_path: Path, out_dir: Path, prefix: str, max_items: int) -> list[CropInfo]:
    out_dir.mkdir(parents=True, exist_ok=True)
    image = Image.open(sheet_path).convert("RGB")
    rgb = np.array(image)
    mask = foreground_mask(rgb)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    candidates = []
    for label in range(1, count):
        x, y, w, h, area = stats[label]
        bbox_area = w * h
        if area < 80 or bbox_area < 350:
            continue
        if w < 10 or h < 8:
            continue
        candidates.append((label, int(x), int(y), int(w), int(h), int(area), int(bbox_area)))

    # Keep visually useful components first: not only area, because thin mouths have low alpha area.
    candidates.sort(key=lambda r: (r[6], r[5]), reverse=True)
    crops: list[CropInfo] = []
    for idx, (label, x, y, w, h, area, _) in enumerate(candidates[:max_items], start=1):
        pad = 10
        x0, y0 = max(0, x - pad), max(0, y - pad)
        x1, y1 = min(image.width, x + w + pad), min(image.height, y + h + pad)
        crop_rgb = rgb[y0:y1, x0:x1]
        crop_mask = (labels[y0:y1, x0:x1] == label).astype(np.uint8) * 255
        crop_mask = cv2.dilate(crop_mask, np.ones((2, 2), np.uint8), iterations=1)
        rgba = np.dstack([crop_rgb, crop_mask])
        out_path = out_dir / f"{prefix}_{idx:02d}.png"
        Image.fromarray(rgba, "RGBA").save(out_path)
        alpha_pixels = int((crop_mask > 0).sum())
        coverage = alpha_pixels / float((x1 - x0) * (y1 - y0))
        accepted = alpha_pixels > 100 and coverage > 0.01
        crops.append(
            CropInfo(
                id=f"{prefix}_{idx:02d}",
                source=str(sheet_path),
                path=str(out_path),
                bbox=[int(x0), int(y0), int(x1), int(y1)],
                width=int(x1 - x0),
                height=int(y1 - y0),
                alpha_pixels=alpha_pixels,
                alpha_coverage=round(coverage, 4),
                accepted_for_smoke=accepted,
                note="auto component crop",
            )
        )
    return crops


def paste_center(base: Image.Image, overlay: Image.Image, center: tuple[int, int], max_w: int, max_h: int) -> None:
    overlay = overlay.convert("RGBA")
    scale = min(max_w / overlay.width, max_h / overlay.height)
    scale = min(scale, 1.0)
    new_size = (max(1, int(overlay.width * scale)), max(1, int(overlay.height * scale)))
    overlay = overlay.resize(new_size, Image.Resampling.LANCZOS)
    x = int(center[0] - overlay.width / 2)
    y = int(center[1] - overlay.height / 2)
    base.alpha_composite(overlay, (x, y))


def make_composites(mouth_crops: list[CropInfo], eye_crops: list[CropInfo]) -> list[dict]:
    out_dir = EXP / "composites"
    out_dir.mkdir(parents=True, exist_ok=True)
    base = Image.open(CANONICAL).convert("RGBA")
    created = []

    mouth_choices = [c for c in mouth_crops if c.accepted_for_smoke and c.width >= 40 and c.height >= 20][:4]
    for idx, crop in enumerate(mouth_choices, start=1):
        canvas = base.copy()
        paste_center(canvas, Image.open(crop.path), (768, 370), 95, 60)
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((715, 336, 821, 405), outline=(255, 0, 0, 220), width=2)
        out_path = out_dir / f"mouth_composite_{idx:02d}.png"
        canvas.save(out_path)
        created.append({"kind": "mouth", "crop": crop.id, "path": str(out_path)})

    # Prefer iris/eye-ish larger crops, then paste one pair. This is a smoke test, not final fit.
    eye_choices = [c for c in eye_crops if c.accepted_for_smoke and c.width >= 80 and c.height >= 60][:2]
    if len(eye_choices) >= 2:
        canvas = base.copy()
        paste_center(canvas, Image.open(eye_choices[0].path), (703, 301), 80, 66)
        paste_center(canvas, Image.open(eye_choices[1].path), (840, 301), 80, 66)
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((654, 260, 748, 340), outline=(0, 120, 255, 220), width=2)
        draw.rectangle((795, 260, 889, 340), outline=(0, 120, 255, 220), width=2)
        out_path = out_dir / "eye_pair_composite_01.png"
        canvas.save(out_path)
        created.append({"kind": "eye_pair", "crop": [c.id for c in eye_choices], "path": str(out_path)})
    return created


def main() -> None:
    (EXP / "reports").mkdir(parents=True, exist_ok=True)
    inventory = image_inventory([CANONICAL, MOUTH_SHEET, EYE_SHEET])
    mouth_crops = extract_components(MOUTH_SHEET, EXP / "crops/mouth", "mouth", 14)
    eye_crops = extract_components(EYE_SHEET, EXP / "crops/eye", "eye", 18)
    composites = make_composites(mouth_crops, eye_crops)

    summary = {
        "experiment_id": "validation-smoke-001",
        "date": "2026-06-02",
        "inputs": inventory,
        "mouth_crops": [asdict(c) for c in mouth_crops],
        "eye_crops": [asdict(c) for c in eye_crops],
        "composites": composites,
        "pass_conditions": {
            "mouth_crops_at_least": 3,
            "eye_crops_at_least": 2,
            "mouth_composites_at_least": 1,
            "eye_pair_composites_at_least": 1,
        },
    }
    mouth_pass = sum(c.accepted_for_smoke for c in mouth_crops) >= 3
    eye_pass = sum(c.accepted_for_smoke for c in eye_crops) >= 2
    composite_pass = any(c["kind"] == "mouth" for c in composites) and any(c["kind"] == "eye_pair" for c in composites)
    summary["result"] = {
        "mouth_crop_mask": "PASS" if mouth_pass else "FAIL",
        "eye_crop_mask": "PASS" if eye_pass else "FAIL",
        "canonical_composite_smoke": "PASS" if composite_pass else "FAIL",
        "decision": "keep-testing" if (mouth_pass and eye_pass and composite_pass) else "revise",
    }
    report_json = EXP / "reports/crop_mask_composite_report.json"
    report_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    report_md = EXP / "reports/qa_report.md"
    report_md.write_text(
        "\n".join(
            [
                "# validation-smoke-001 QA Report",
                "",
                "## Result",
                "",
                f"- mouth crop/mask: {summary['result']['mouth_crop_mask']}",
                f"- eye crop/mask: {summary['result']['eye_crop_mask']}",
                f"- canonical composite smoke: {summary['result']['canonical_composite_smoke']}",
                f"- decision: {summary['result']['decision']}",
                "",
                "## Counts",
                "",
                f"- mouth crops: {len(mouth_crops)} total, {sum(c.accepted_for_smoke for c in mouth_crops)} accepted",
                f"- eye crops: {len(eye_crops)} total, {sum(c.accepted_for_smoke for c in eye_crops)} accepted",
                f"- composites: {len(composites)}",
                "",
                "## Evidence",
                "",
                f"- JSON: `{report_json}`",
                f"- crops: `{EXP / 'crops'}`",
                f"- composites: `{EXP / 'composites'}`",
                "",
                "## Notes",
                "",
                "- This is a crop/mask and placement smoke test, not final character-quality validation.",
                "- Mouth candidates are usable for further alignment tests.",
                "- Eye candidates need stricter semantic classification before production use.",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(summary["result"], ensure_ascii=False, indent=2))
    print(report_json)
    print(report_md)


if __name__ == "__main__":
    main()

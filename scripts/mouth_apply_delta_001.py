#!/usr/bin/env python3
"""Apply saved mouth manual delta to new generated mouth sheets."""

from __future__ import annotations

import argparse
import base64
import json
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw


CANVAS = (2048, 2048)
EXPRESSIONS = ["neutral_smile", "small_open", "wide_open", "o_vowel", "happy_open"]


@dataclass
class BBox:
    x: int
    y: int
    w: int
    h: int

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.w / 2.0, self.y + self.h / 2.0)

    def as_list(self) -> list[int]:
        return [self.x, self.y, self.w, self.h]

    def padded(self, pad_x: int, pad_y: int, limit: tuple[int, int]) -> "BBox":
        x0 = max(0, self.x - pad_x)
        y0 = max(0, self.y - pad_y)
        x1 = min(limit[0], self.x + self.w + pad_x)
        y1 = min(limit[1], self.y + self.h + pad_y)
        return BBox(x0, y0, x1 - x0, y1 - y0)


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def bbox_from_alpha(img: Image.Image, threshold: int = 10) -> BBox | None:
    alpha = np.array(img.convert("RGBA"))[:, :, 3]
    ys, xs = np.where(alpha > threshold)
    if len(xs) == 0:
        return None
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    return BBox(x0, y0, x1 - x0, y1 - y0)


def center_of_alpha(img: Image.Image) -> tuple[float, float] | None:
    alpha = np.array(img.convert("RGBA"))[:, :, 3]
    ys, xs = np.where(alpha > 10)
    if len(xs) == 0:
        return None
    return (float(xs.mean()), float(ys.mean()))


def remove_green_background(img: Image.Image) -> Image.Image:
    arr = np.array(img.convert("RGBA")).astype(np.int16)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    key = ((g > 150) & (r < 110) & (b < 110)) | ((g - np.maximum(r, b) > 80) & (g > 125))
    arr[:, :, 3] = np.where(key, 0, arr[:, :, 3])
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def crop_candidates(sheet_path: Path, out_dir: Path, set_name: str) -> list[Path]:
    img = remove_green_background(Image.open(sheet_path).convert("RGBA"))
    alpha = np.array(img)[:, :, 3]
    binary = (alpha > 20).astype(np.uint8) * 255
    kernel = np.ones((5, 5), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes: list[BBox] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w * h > 80 and w > 10 and h > 5:
            boxes.append(BBox(x, y, w, h).padded(8, 8, img.size))
    boxes = sorted(boxes, key=lambda b: b.x)[:5]
    paths: list[Path] = []
    for index, box in enumerate(boxes):
        expression = EXPRESSIONS[index] if index < len(EXPRESSIONS) else f"candidate_{index + 1}"
        crop = img.crop((box.x, box.y, box.x + box.w, box.y + box.h))
        path = out_dir / f"{set_name}_{expression}_crop.png"
        crop.save(path)
        paths.append(path)
    return paths


def fit_crop_to_roi(crop: Image.Image, mouth_roi: BBox) -> Image.Image:
    crop_bbox = bbox_from_alpha(crop)
    if not crop_bbox:
        return crop
    max_w = max(28, int(mouth_roi.w * 0.72))
    max_h = max(14, int(mouth_roi.h * 0.72))
    scale = min(max_w / crop_bbox.w, max_h / crop_bbox.h, 1.25)
    new_size = (max(1, int(crop.width * scale)), max(1, int(crop.height * scale)))
    return crop.resize(new_size, Image.Resampling.LANCZOS)


def place_full_layer(crop: Image.Image, target: tuple[float, float], dx: float = 0, dy: float = 0) -> Image.Image:
    center = center_of_alpha(crop)
    if center is None:
        return Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    x = int(round(target[0] + dx - center[0]))
    y = int(round(target[1] + dy - center[1]))
    full = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    full.alpha_composite(crop, (x, y))
    return full


def bbox_inside(inner: BBox | None, outer: BBox) -> bool:
    return bool(
        inner
        and inner.x >= outer.x
        and inner.y >= outer.y
        and inner.x + inner.w <= outer.x + outer.w
        and inner.y + inner.h <= outer.y + outer.h
    )


def overlay(canonical: Image.Image, layer: Image.Image, mouth_roi: BBox, out_path: Path) -> None:
    img = canonical.copy()
    img.alpha_composite(layer)
    draw = ImageDraw.Draw(img)
    draw.rectangle([mouth_roi.x, mouth_roi.y, mouth_roi.x + mouth_roi.w, mouth_roi.y + mouth_roi.h], outline="red", width=5)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)


def data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def build_preview(canonical_path: Path, records: list[dict], out_path: Path) -> None:
    cards = []
    for record in records:
        cards.append(
            {
                "set": record["set"],
                "expression": record["expression"],
                "auto": data_uri(Path(record["auto_overlay"])),
                "corrected": data_uri(Path(record["corrected_overlay"])),
                "auto_error": record["auto_error_px"],
                "corrected_error": record["corrected_error_px"],
                "inside": record["corrected_bbox_inside_mouth_roi"],
            }
        )
    payload = json.dumps(cards, ensure_ascii=False)
    html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <title>Mouth Apply Delta 001</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #171b20; color: #f5f7fb; }}
    main {{ display: grid; grid-template-columns: 320px 1fr; min-height: 100vh; }}
    aside {{ padding: 16px; border-right: 1px solid rgba(255,255,255,.14); overflow: auto; }}
    button {{ display: block; width: 100%; margin: 0 0 8px; padding: 10px; border: 1px solid rgba(255,255,255,.16); background: #2d3541; color: #f5f7fb; border-radius: 8px; text-align: left; cursor: pointer; }}
    button.active {{ border-color: #73d0ff; background: #254253; }}
    .stage {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; padding: 18px; align-content: start; }}
    figure {{ margin: 0; }}
    figcaption {{ margin-bottom: 8px; color: #b8c1cc; font-size: 13px; }}
    img {{ display: block; width: 100%; background: #2d3541; }}
    .meta {{ margin: 10px 0 16px; color: #b8c1cc; font-size: 13px; line-height: 1.45; }}
    @media (max-width: 900px) {{ main {{ grid-template-columns: 1fr; }} .stage {{ grid-template-columns: 1fr; }} aside {{ border-right: 0; border-bottom: 1px solid rgba(255,255,255,.14); }} }}
  </style>
</head>
<body>
<main>
  <aside>
    <h1>입 보정 비교</h1>
    <p class="meta">왼쪽은 자동 배치, 오른쪽은 저장된 보정값을 원본 2048 좌표에 적용한 비교입니다.</p>
    <div id="list"></div>
    <div id="meta" class="meta"></div>
  </aside>
  <section class="stage">
    <figure><figcaption>자동 배치</figcaption><img id="auto" alt="auto overlay"></figure>
    <figure><figcaption>보정 적용</figcaption><img id="corrected" alt="corrected overlay"></figure>
  </section>
</main>
<script>
const cards = {payload};
const list = document.getElementById('list');
const meta = document.getElementById('meta');
const auto = document.getElementById('auto');
const corrected = document.getElementById('corrected');
function select(i) {{
  [...list.children].forEach((button, idx) => button.classList.toggle('active', idx === i));
  const card = cards[i];
  auto.src = card.auto;
  corrected.src = card.corrected;
  meta.textContent = `${{card.set}} / ${{card.expression}} / auto ${{card.auto_error.toFixed(2)}}px / corrected ${{card.corrected_error.toFixed(2)}}px / ROI ${{card.inside ? 'PASS' : 'REVISE'}}`;
}}
cards.forEach((card, i) => {{
  const button = document.createElement('button');
  button.textContent = `${{card.set}} / ${{card.expression}}`;
  button.onclick = () => select(i);
  list.appendChild(button);
}});
if (cards.length) select(0);
</script>
</body>
</html>
"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")


def average_manual_mouth_delta(manual: dict) -> tuple[float, float, str, list[dict]]:
    mouth_deltas = [v for k, v in manual.get("reviews", {}).items() if k.startswith("mouth:")]
    if not mouth_deltas:
        return 0.0, 0.0, "no saved mouth delta; using zero delta", []

    if all("canvas_dx" in v and "canvas_dy" in v for v in mouth_deltas):
        dx = float(round(sum(float(v["canvas_dx"]) for v in mouth_deltas) / len(mouth_deltas), 3))
        dy = float(round(sum(float(v["canvas_dy"]) for v in mouth_deltas) / len(mouth_deltas), 3))
        interpretation = "manual canvas_dx/canvas_dy interpreted as 2048 canvas pixels"
    else:
        dx = float(round(sum(float(v["dx"]) for v in mouth_deltas) / len(mouth_deltas), 3))
        dy = float(round(sum(float(v["dy"]) for v in mouth_deltas) / len(mouth_deltas), 3))
        interpretation = (
            "legacy manual dx/dy interpreted as 2048 canvas pixels; unreliable because "
            "old review UI saved browser display pixels only"
        )
    return dx, dy, interpretation, mouth_deltas


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("/Users/family/jason/Vtube/experiments/mouth-apply-delta-001"))
    parser.add_argument("--canonical", type=Path, default=Path("/Users/family/jason/Vtube/experiments/production-canvas-2048-001/canonical/canonical_front_2048.png"))
    parser.add_argument("--anchor-report", type=Path, default=Path("/Users/family/jason/Vtube/experiments/production-canvas-2048-001/reports/anchor_2048_report.json"))
    parser.add_argument("--manual-report", type=Path, default=Path("/Users/family/jason/Vtube/experiments/production-canvas-2048-001/reports/manual_adjustments_2048.json"))
    parser.add_argument("--mouth-a", type=Path, default=Path("/Users/family/jason/Vtube/experiments/asset-generation-2048-001/raw/mouth_set_a_stylematch_source.png"))
    parser.add_argument("--mouth-b", type=Path, default=Path("/Users/family/jason/Vtube/experiments/asset-generation-2048-001/raw/mouth_set_b_simple_source.png"))
    args = parser.parse_args()

    dirs = {
        "crops": args.root / "crops",
        "layers": args.root / "layers",
        "overlays": args.root / "overlays",
        "reports": args.root / "reports",
        "preview": args.root / "preview",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)

    anchor = json.loads(args.anchor_report.read_text(encoding="utf-8"))
    manual = json.loads(args.manual_report.read_text(encoding="utf-8"))
    mouth_roi = BBox(*anchor["metrics"]["mouth_roi"])
    target = tuple(anchor["metrics"]["mouth_center"])
    dx, dy, delta_interpretation, mouth_deltas = average_manual_mouth_delta(manual)
    calibrated_delta = all("canvas_dx" in v and "canvas_dy" in v for v in mouth_deltas) if mouth_deltas else False

    canonical = Image.open(args.canonical).convert("RGBA")
    records: list[dict] = []
    for set_name, sheet_path in [("set_a_stylematch", args.mouth_a), ("set_b_simple", args.mouth_b)]:
        crop_paths = crop_candidates(sheet_path, dirs["crops"], set_name)
        for index, crop_path in enumerate(crop_paths):
            expression = EXPRESSIONS[index] if index < len(EXPRESSIONS) else f"candidate_{index + 1}"
            crop = fit_crop_to_roi(Image.open(crop_path).convert("RGBA"), mouth_roi)
            auto_layer = place_full_layer(crop, target)
            corrected_layer = place_full_layer(crop, target, dx=dx, dy=dy)

            auto_bbox = bbox_from_alpha(auto_layer)
            corrected_bbox = bbox_from_alpha(corrected_layer)
            auto_center = center_of_alpha(auto_layer)
            corrected_center = center_of_alpha(corrected_layer)
            auto_error = math.dist(target, auto_center) if auto_center else None
            corrected_target = (target[0] + dx, target[1] + dy)
            corrected_error = math.dist(corrected_target, corrected_center) if corrected_center else None

            auto_layer_path = dirs["layers"] / f"{set_name}_{expression}_auto_full.png"
            corrected_layer_path = dirs["layers"] / f"{set_name}_{expression}_corrected_full.png"
            auto_overlay_path = dirs["overlays"] / f"{set_name}_{expression}_auto_overlay.png"
            corrected_overlay_path = dirs["overlays"] / f"{set_name}_{expression}_corrected_overlay.png"
            auto_layer.save(auto_layer_path)
            corrected_layer.save(corrected_layer_path)
            overlay(canonical, auto_layer, mouth_roi, auto_overlay_path)
            overlay(canonical, corrected_layer, mouth_roi, corrected_overlay_path)

            records.append(
                {
                    "set": set_name,
                    "expression": expression,
                    "crop": str(crop_path),
                    "auto_layer": str(auto_layer_path),
                    "corrected_layer": str(corrected_layer_path),
                    "auto_overlay": str(auto_overlay_path),
                    "corrected_overlay": str(corrected_overlay_path),
                    "auto_bbox": auto_bbox.as_list() if auto_bbox else None,
                    "corrected_bbox": corrected_bbox.as_list() if corrected_bbox else None,
                    "auto_center": list(auto_center) if auto_center else None,
                    "corrected_center": list(corrected_center) if corrected_center else None,
                    "auto_error_px": auto_error,
                    "corrected_error_px": corrected_error,
                    "corrected_bbox_inside_mouth_roi": bbox_inside(corrected_bbox, mouth_roi),
                }
            )

    corrected_pass = sum(1 for record in records if record["corrected_bbox_inside_mouth_roi"] and record["corrected_error_px"] is not None and record["corrected_error_px"] <= 1.0)
    next_action = (
        "Open preview/index.html and visually review the calibrated corrected overlays. If at least two expressions are visually aligned, mark them as keep candidates."
        if calibrated_delta
        else "Save evidence again from the updated review UI so display pixels and 2048 canvas pixels are both recorded, then rerun this test."
    )
    placement_result = "REVISE"
    human_notes = (
        "주인님 review: asset quality was acceptable. Calibrated canvas-coordinate delta has been applied; visual alignment review is required."
        if calibrated_delta
        else "주인님 review: asset quality was acceptable; placement did not match. Calibrated canvas-coordinate evidence is required."
    )
    report = {
        "experiment_id": "MOUTH-APPLY-DELTA-001",
        "date": str(date.today()),
        "status": "OBSERVED" if records else "BLOCKED",
        "inputs": [str(args.mouth_a), str(args.mouth_b), str(args.canonical), str(args.manual_report)],
        "outputs": [str(dirs["preview"] / "index.html"), str(dirs["reports"] / "mouth_apply_delta_report.json")],
        "metrics": {
            "canvas_size": list(CANVAS),
            "mouth_roi": mouth_roi.as_list(),
            "original_target": list(target),
            "applied_delta": {"dx": dx, "dy": dy, "scale": 1.0, "opacity": 1.0},
            "candidate_count": len(records),
            "corrected_numeric_pass_count": corrected_pass,
            "delta_interpretation": delta_interpretation,
            "calibrated_canvas_delta": calibrated_delta,
        },
        "result": {
            "corrected_full_canvas_layers": "PASS" if records else "FAIL",
            "corrected_bbox_inside_mouth_roi": "PASS" if corrected_pass >= 2 else "REVISE",
            "human_visual_quality": "PASS_BY_USER_REVIEW",
            "position_after_delta": "REVISE",
            "set_winner": "PENDING_HUMAN_REVIEW",
            "production_candidate": "REVISE",
        },
        "candidates": records,
        "human_review": {"required": True, "verdict": "REVISE", "notes": human_notes},
        "decision": "revise",
        "next_action": next_action,
    }
    save_json(dirs["reports"] / "mouth_apply_delta_report.json", report)

    qa = [
        "# Mouth Apply Delta QA",
        "",
        f"Date: {date.today()}",
        "",
        "## Verdict",
        "",
        "- Status: OBSERVED",
        "- 주인님 correction: mouth asset quality was acceptable.",
        (
            "- Calibrated 2048 canvas delta was applied; visual review is now needed on corrected overlays."
            if calibrated_delta
            else "- Current saved delta may be legacy browser display pixels, not calibrated 2048 canvas pixels."
        ),
        "",
        "## Evidence",
        "",
        f"- Applied delta: dx={dx}, dy={dy}",
        f"- Candidates: {len(records)}",
        f"- Corrected numeric pass count: {corrected_pass}",
        f"- Delta interpretation: {delta_interpretation}",
        f"- Calibrated canvas delta: {'yes' if calibrated_delta else 'no'}",
        "- Human asset quality: PASS_BY_USER_REVIEW",
        f"- Position after delta: {placement_result}",
        "",
        "## Review",
        "",
        f"- Preview: `{dirs['preview'] / 'index.html'}`",
        f"- Report: `{dirs['reports'] / 'mouth_apply_delta_report.json'}`",
    ]
    (dirs["reports"] / "qa_report.md").write_text("\n".join(qa) + "\n", encoding="utf-8")
    build_preview(args.canonical, records, dirs["preview"] / "index.html")
    print(json.dumps({"root": str(args.root), "preview": str(dirs["preview"] / "index.html"), "report": str(dirs["reports"] / "mouth_apply_delta_report.json")}, indent=2))


if __name__ == "__main__":
    main()

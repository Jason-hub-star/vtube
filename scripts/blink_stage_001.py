#!/usr/bin/env python3
"""Create and validate staged blink full-canvas layers."""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw


CANVAS = (2048, 2048)
STAGES = ["half", "mostly_closed", "closed"]


@dataclass
class BBox:
    x: int
    y: int
    w: int
    h: int

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.w / 2.0, self.y + self.h / 2.0)

    @property
    def area(self) -> int:
        return self.w * self.h

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


def crop_blink_pairs(sheet_path: Path, crop_dir: Path) -> list[dict]:
    crop_dir.mkdir(parents=True, exist_ok=True)
    keyed = remove_green_background(Image.open(sheet_path).convert("RGBA"))
    alpha = np.array(keyed)[:, :, 3]
    binary = (alpha > 20).astype(np.uint8) * 255
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes: list[BBox] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        box = BBox(x, y, w, h)
        if box.area > 200 and w > 10 and h > 5:
            boxes.append(box.padded(10, 10, keyed.size))
    boxes = sorted(boxes, key=lambda box: (box.y, box.x))[:6]
    if len(boxes) < 6:
        raise RuntimeError(f"expected 6 blink components, got {len(boxes)}")

    rows = [sorted(boxes[i : i + 2], key=lambda box: box.x) for i in range(0, 6, 2)]
    records = []
    for stage, pair in zip(STAGES, rows):
        pair_records = []
        for side, box in zip(["left", "right"], pair):
            crop = keyed.crop((box.x, box.y, box.x + box.w, box.y + box.h))
            path = crop_dir / f"{stage}_{side}_crop.png"
            crop.save(path)
            pair_records.append({"side": side, "source_bbox": box.as_list(), "crop": str(path), "source_area": box.area})
        records.append({"stage": stage, "parts": pair_records})
    return records


def fit_to_eye_roi(crop: Image.Image, eye_roi: BBox) -> tuple[Image.Image, float]:
    crop_bbox = bbox_from_alpha(crop)
    if not crop_bbox:
        return crop, 1.0
    max_w = max(20, int(eye_roi.w * 0.98))
    max_h = max(12, int(eye_roi.h * 0.82))
    scale = min(max_w / crop_bbox.w, max_h / crop_bbox.h, 1.4)
    new_size = (max(1, int(crop.width * scale)), max(1, int(crop.height * scale)))
    return crop.resize(new_size, Image.Resampling.LANCZOS), scale


def place_part(crop: Image.Image, eye_roi: BBox, dx: float, dy: float) -> tuple[Image.Image, dict]:
    fitted, scale = fit_to_eye_roi(crop, eye_roi)
    fitted_bbox = bbox_from_alpha(fitted)
    full = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    if fitted_bbox is None:
        return full, {"scale": scale, "alpha_bbox": None, "alpha_center": None, "inside_eye_roi": False}
    target = (eye_roi.center[0] + dx, eye_roi.center[1] + dy)
    x = int(round(target[0] - fitted_bbox.center[0]))
    y = int(round(target[1] - fitted_bbox.center[1]))
    full.alpha_composite(fitted, (x, y))
    bbox = bbox_from_alpha(full)
    alpha_center = center_of_alpha(full)
    inside = bool(
        bbox
        and bbox.x >= eye_roi.x
        and bbox.y >= eye_roi.y
        and bbox.x + bbox.w <= eye_roi.x + eye_roi.w
        and bbox.y + bbox.h <= eye_roi.y + eye_roi.h
    )
    return full, {
        "scale": scale,
        "target_center": [round(target[0], 3), round(target[1], 3)],
        "alpha_bbox": bbox.as_list() if bbox else None,
        "alpha_center": [round(alpha_center[0], 3), round(alpha_center[1], 3)] if alpha_center else None,
        "placement_error_px": round(math.dist(target, alpha_center), 3) if alpha_center else None,
        "inside_eye_roi": inside,
    }


def alpha_coverage_in_roi(layer: Image.Image, roi: BBox) -> float:
    alpha = np.array(layer.convert("RGBA"))[roi.y : roi.y + roi.h, roi.x : roi.x + roi.w, 3]
    return float((alpha > 10).sum() / max(1, roi.area))


def build_preview(root: Path, records: list[dict], out_path: Path, canonical_path: Path) -> None:
    def rel(path: str) -> str:
        return Path(os.path.relpath(path, out_path.parent)).as_posix()

    canonical_rel = rel(str(canonical_path))
    buttons = "\n".join(f'<button data-index="{i}"></button>' for i, _ in enumerate(records))
    payload = json.dumps(
        [
            {
                "stage": r["stage"],
                "overlay": rel(r["overlay"]),
                "layer": rel(r["combined_layer"]),
                "coverage": r["coverage_mean"],
                "inside": r["both_inside_eye_roi"],
                "review": r["human_verdict"],
                "parts": r["parts"],
            }
            for r in records
        ],
        ensure_ascii=False,
    )
    html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <title>Blink Stage 001</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #171b20; color: #f5f7fb; }}
    main {{ display: grid; grid-template-columns: minmax(360px, 1fr) 420px; min-height: 100vh; }}
    aside {{ padding: 16px; border-left: 1px solid rgba(255,255,255,.14); background: #222832; overflow: auto; }}
    h1 {{ margin: 0 0 12px; font-size: 20px; }}
    h2 {{ margin: 16px 0 8px; font-size: 14px; color: #b8c1cc; }}
    p {{ color: #b8c1cc; line-height: 1.45; }}
    button, select, textarea {{ width: 100%; border: 1px solid rgba(255,255,255,.16); background: #2d3541; color: #f5f7fb; border-radius: 8px; }}
    button {{ display: block; margin: 0 0 8px; padding: 10px; font: inherit; text-align: left; cursor: pointer; }}
    button.active {{ border-color: #73d0ff; background: #254253; }}
    button.primary {{ text-align: center; border-color: #73d0ff; }}
    button.verdict.active {{ border-color: #ffd166; }}
    select {{ min-height: 38px; padding: 8px; }}
    textarea {{ min-height: 72px; padding: 9px; resize: vertical; font: inherit; }}
    label {{ display: grid; gap: 6px; margin: 10px 0; color: #b8c1cc; font-size: 13px; }}
    .grid3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; }}
    .grid2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
    .grid3 button {{ text-align: center; }}
    .grid2 button {{ text-align: center; }}
    .stage {{ display: grid; place-items: center; padding: 22px; background: #242a33; }}
    .canvas {{ position: relative; width: min(82vh, calc(100vw - 470px)); min-width: 340px; aspect-ratio: 1 / 1; background: #343b46; overflow: hidden; box-shadow: 0 16px 38px rgba(0,0,0,.34); }}
    .canvas img {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; user-select: none; -webkit-user-drag: none; }}
    #layer {{ cursor: grab; transform-origin: center; }}
    #layer.dragging {{ cursor: grabbing; }}
    #layer.hidden {{ display: none; }}
    #canonical.dimmed {{ opacity: .28; }}
    figure {{ margin: 0; }}
    figcaption {{ margin-bottom: 8px; color: #b8c1cc; font-size: 13px; }}
    img {{ display: block; width: 100%; background: #343b46; }}
    .meta {{ margin-top: 14px; color: #b8c1cc; font-size: 13px; }}
    .status {{ padding: 9px; border: 1px solid rgba(255,255,255,.14); background: rgba(255,255,255,.05); border-radius: 8px; color: #b8c1cc; font-size: 13px; }}
    .metric {{ margin: 8px 0; padding: 9px; border: 1px solid rgba(255,255,255,.14); background: rgba(255,255,255,.05); border-radius: 8px; color: #b8c1cc; font-size: 13px; overflow-wrap: anywhere; }}
    .ok {{ color: #78d98f; }}
    .warn {{ color: #ffd166; }}
    @media (max-width: 900px) {{ main {{ grid-template-columns: 1fr; }} aside {{ border-left: 0; border-top: 1px solid rgba(255,255,255,.14); }} .canvas {{ width: min(92vw, 74vh); min-width: 0; }} }}
  </style>
</head>
<body>
<main>
  <section class="stage">
    <div class="canvas" id="canvas">
      <img src="{canonical_rel}" alt="기준 이미지">
      <img id="layer" alt="깜빡임 레이어">
    </div>
  </section>
  <aside>
    <h1>깜빡임 검수</h1>
    <p>파일 후보를 고르고, 위치를 맞춘 뒤 검수 저장합니다.</p>
    <div id="list">{buttons}</div>
    <h2>검수</h2>
    <div id="reviewPanel"></div>
    <div id="meta" class="meta"></div>
  </aside>
</main>
<script>
const records = {payload};
const labelKey = 'blink-stage-001-labels-v1';
const reviewKey = 'blink-stage-001-review-v1';
const placementKey = 'blink-stage-001-placement-v1';
const labels = JSON.parse(localStorage.getItem(labelKey) || '{{}}');
const reviews = JSON.parse(localStorage.getItem(reviewKey) || '{{}}');
const placements = JSON.parse(localStorage.getItem(placementKey) || '{{}}');
const list = document.getElementById('list');
const reviewPanel = document.getElementById('reviewPanel');
const meta = document.getElementById('meta');
const layer = document.getElementById('layer');
const canonical = document.querySelector('#canvas img[alt="기준 이미지"]');
const canvas = document.getElementById('canvas');
let selected = 0;
let drag = null;
const stageName = {{ half: '반쯤 감김', mostly_closed: '거의 감김', closed: '완전 감김', not_blink_stage: '단계 아님' }};
const verdictName = {{ PASS: '통과', REVISE: '수정', FAIL: '실패' }};
const defaultLabel = (record) => ({{
  stage_label: record.stage,
  semantic_type: 'blink_stage',
  order_label: record.stage,
  source: 'inferred_from_file_candidate'
}});
const defaultReview = () => ({{ verdict: 'REVISE', notes: '' }});
const defaultPlacement = () => ({{ dx: 0, dy: 0, scale: 1, opacity: 0.65, viewMode: 'compare' }});
const keyFor = (record) => record.stage;
const getLabel = (record) => labels[keyFor(record)] || defaultLabel(record);
const getReview = (record) => reviews[keyFor(record)] || defaultReview();
const getPlacement = (record) => placements[keyFor(record)] || defaultPlacement();
function ensureLabel(record) {{
  const key = keyFor(record);
  if (!labels[key]) labels[key] = defaultLabel(record);
}}
function saveLocal() {{
  localStorage.setItem(labelKey, JSON.stringify(labels, null, 2));
  localStorage.setItem(reviewKey, JSON.stringify(reviews, null, 2));
  localStorage.setItem(placementKey, JSON.stringify(placements, null, 2));
}}
function canvasMetrics() {{
  const rect = canvas.getBoundingClientRect();
  const width = rect.width || 1;
  const height = rect.height || 1;
  return {{
    canonical_canvas_size: [2048, 2048],
    canvas_display_size: [Number(width.toFixed(3)), Number(height.toFixed(3))],
    display_to_canvas_scale: [
      Number((2048 / width).toFixed(6)),
      Number((2048 / height).toFixed(6))
    ]
  }};
}}
function canvasDelta(placement) {{
  const metrics = canvasMetrics();
  return {{
    canvas_dx: Number((placement.dx * metrics.display_to_canvas_scale[0]).toFixed(3)),
    canvas_dy: Number((placement.dy * metrics.display_to_canvas_scale[1]).toFixed(3))
  }};
}}
function evidencePlacement(placement) {{
  const delta = canvasDelta(placement);
  return {{
    ...placement,
    unit: 'display_px',
    display_dx: placement.dx,
    display_dy: placement.dy,
    ...delta
  }};
}}
function setPlacement(record, patch) {{
  placements[keyFor(record)] = {{ ...getPlacement(record), ...patch }};
  saveLocal();
  applyLayerTransform(record);
  renderReviewPanel(record);
}}
function applyPlacementToAll(record) {{
  const source = getPlacement(record);
  records.forEach((target) => {{
    placements[keyFor(target)] = {{ ...getPlacement(target), ...source }};
  }});
  saveLocal();
  applyLayerTransform(record);
  renderReviewPanel(record);
}}
function applyCurrentReviewToAll(record) {{
  const sourceReview = getReview(record);
  records.forEach((target) => {{
    labels[keyFor(target)] = defaultLabel(target);
    reviews[keyFor(target)] = {{ ...sourceReview }};
  }});
  saveLocal();
  renderList();
  renderReviewPanel(record);
}}
function applyLayerTransform(record) {{
  const placement = getPlacement(record);
  layer.style.opacity = placement.opacity;
  layer.style.transform = `translate(${{placement.dx}}px, ${{placement.dy}}px) scale(${{placement.scale}})`;
  layer.classList.toggle('hidden', placement.viewMode === 'original');
  canonical.classList.toggle('dimmed', placement.viewMode === 'layer');
}}
function allLabeled() {{
  return records.every((record) => labels[keyFor(record)] && labels[keyFor(record)].semantic_type);
}}
function currentLabeled(record) {{
  ensureLabel(record);
  return true;
}}
function renderList() {{
  [...list.children].forEach((button, idx) => {{
    const record = records[idx];
    button.classList.toggle('active', idx === selected);
    button.textContent = `${{stageName[record.stage] || record.stage}}`;
  }});
}}
function renderReviewPanel(record) {{
  const review = getReview(record);
  const placement = getPlacement(record);
  const delta = canvasDelta(placement);
  reviewPanel.innerHTML = `
    <h2>1. 위치 보정</h2>
    <div class="grid3">
      ${{[
        ['compare','비교'],
        ['original','원본'],
        ['layer','파츠']
      ].map(([value, label]) => `<button class="${{placement.viewMode === value ? 'active' : ''}}" data-view-mode="${{value}}">${{label}}</button>`).join('')}}
    </div>
    <div class="metric">화면: ${{placement.dx}}, ${{placement.dy}} · 원본: ${{delta.canvas_dx}}, ${{delta.canvas_dy}}</div>
    <label>크기 <input data-placement-field="scale" type="range" min="0.50" max="1.50" step="0.01" value="${{placement.scale}}"></label>
    <label>투명도 <input data-placement-field="opacity" type="range" min="0.10" max="1" step="0.01" value="${{placement.opacity}}"></label>
    <button data-apply-placement-all>같은 위치 모두 적용</button>
    <button data-apply-review-all>라벨/검수도 모두 적용</button>
    <button data-reset-placement>위치 초기화</button>
    <h2>2. 검수</h2>
    <div class="grid3">
      ${{['PASS','REVISE','FAIL'].map(v => `<button class="verdict ${{review.verdict === v ? 'active' : ''}}" data-verdict="${{v}}">${{verdictName[v]}}</button>`).join('')}}
    </div>
    <textarea data-review-notes placeholder="검수 메모">${{review.notes || ''}}</textarea>
    <button class="primary" data-save-review>검수 저장</button>
    <div class="status"><span class="ok">파일 후보 기준으로 저장 가능</span></div>
  `;
}}
function select(i) {{
  selected = i;
  const record = records[i];
  ensureLabel(record);
  saveLocal();
  layer.src = record.layer;
  renderList();
  renderReviewPanel(record);
  applyLayerTransform(record);
  meta.textContent = `${{stageName[record.stage] || record.stage}} / ROI ${{record.inside ? '통과' : '수정'}} / 덮임 ${{record.coverage.toFixed(3)}}`;
}}
async function postJson(url, payload, fallbackName) {{
  try {{
    const response = await fetch(url, {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify(payload) }});
    if (response.ok) {{
      const result = await response.json();
      alert(`저장 완료: ${{result.path}}`);
      return;
    }}
  }} catch (error) {{
    console.warn('server save failed', error);
  }}
  const blob = new Blob([JSON.stringify(payload, null, 2)], {{ type: 'application/json' }});
  const urlObject = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = urlObject;
  link.download = fallbackName;
  link.click();
  URL.revokeObjectURL(urlObject);
}}
function labelEvidence() {{
  return {{
    experiment_id: 'BLINK-LABEL-001',
    date: new Date().toISOString(),
    inputs: records.map(r => r.stage),
    labels,
    placements: Object.fromEntries(Object.entries(placements).map(([key, placement]) => [key, evidencePlacement(placement)])),
    complete: allLabeled()
  }};
}}
function reviewEvidence() {{
  return {{
    experiment_id: 'BLINK-REVIEW-001',
    date: new Date().toISOString(),
    label_required_first: false,
    stage_inferred_from_file_candidate: true,
    label_complete: allLabeled(),
    selected: keyFor(records[selected]),
    selected_label_complete: currentLabeled(records[selected]),
    labels,
    placements: Object.fromEntries(Object.entries(placements).map(([key, placement]) => [key, evidencePlacement(placement)])),
    reviews
  }};
}}
list.addEventListener('click', (event) => {{
  const button = event.target.closest('[data-index]');
  if (button) select(Number(button.dataset.index));
}});
reviewPanel.addEventListener('click', async (event) => {{
  const record = records[selected];
  const key = keyFor(record);
  const verdict = event.target.closest('[data-verdict]');
  if (verdict) {{
    reviews[key] = {{ ...getReview(record), verdict: verdict.dataset.verdict }};
    saveLocal();
    renderReviewPanel(record);
  }}
  const viewMode = event.target.closest('[data-view-mode]');
  if (viewMode) setPlacement(record, {{ viewMode: viewMode.dataset.viewMode }});
  if (event.target.closest('[data-apply-placement-all]')) applyPlacementToAll(record);
  if (event.target.closest('[data-apply-review-all]')) applyCurrentReviewToAll(record);
  if (event.target.closest('[data-reset-placement]')) setPlacement(record, defaultPlacement());
  if (event.target.closest('[data-save-review]')) {{
    ensureLabel(record);
    reviews[key] = {{ ...getReview(record) }};
    saveLocal();
    await postJson('/api/save-blink-review', reviewEvidence(), 'blink_stage_review.json');
  }}
}});
reviewPanel.addEventListener('input', (event) => {{
  const record = records[selected];
  if (event.target.matches('[data-placement-field]')) {{
    setPlacement(record, {{ [event.target.dataset.placementField]: Number(event.target.value) }});
  }}
  if (event.target.matches('[data-review-notes]')) {{
    const key = keyFor(record);
    reviews[key] = {{ ...getReview(record), notes: event.target.value }};
    saveLocal();
  }}
}});
layer.addEventListener('pointerdown', (event) => {{
  const record = records[selected];
  const placement = getPlacement(record);
  drag = {{ x: event.clientX, y: event.clientY, dx: placement.dx, dy: placement.dy }};
  layer.classList.add('dragging');
  layer.setPointerCapture(event.pointerId);
}});
layer.addEventListener('pointermove', (event) => {{
  if (!drag) return;
  const record = records[selected];
  setPlacement(record, {{
    dx: Math.round(drag.dx + event.clientX - drag.x),
    dy: Math.round(drag.dy + event.clientY - drag.y)
  }});
}});
layer.addEventListener('pointerup', () => {{
  drag = null;
  layer.classList.remove('dragging');
}});
window.addEventListener('keydown', (event) => {{
  if (!['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) return;
  const record = records[selected];
  const placement = getPlacement(record);
  const step = event.shiftKey ? 10 : 1;
  const delta = {{
    ArrowUp: [0, -step],
    ArrowDown: [0, step],
    ArrowLeft: [-step, 0],
    ArrowRight: [step, 0]
  }}[event.key];
  event.preventDefault();
  setPlacement(record, {{ dx: placement.dx + delta[0], dy: placement.dy + delta[1] }});
}});
if (records.length) select(0);
</script>
</body>
</html>
"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("/Users/family/jason/Vtube/experiments/blink-stage-001"))
    parser.add_argument("--canonical", type=Path, default=Path("/Users/family/jason/Vtube/experiments/production-canvas-2048-001/canonical/canonical_front_2048.png"))
    parser.add_argument("--anchor-report", type=Path, default=Path("/Users/family/jason/Vtube/experiments/production-canvas-2048-001/reports/anchor_2048_report.json"))
    parser.add_argument("--manual-report", type=Path, default=Path("/Users/family/jason/Vtube/experiments/production-canvas-2048-001/reports/manual_adjustments_2048.json"))
    parser.add_argument("--blink-sheet", type=Path, default=Path("/Users/family/jason/Vtube/experiments/asset-generation-2048-001/raw/blink_stage_sheet_source.png"))
    parser.add_argument("--apply-manual-delta", action="store_true", help="Apply saved blink canvas_dx/canvas_dy. Default keeps stage test centered on eye ROI.")
    args = parser.parse_args()

    dirs = {
        "canonical": args.root / "canonical",
        "crops": args.root / "crops",
        "layers": args.root / "layers",
        "overlays": args.root / "overlays",
        "reports": args.root / "reports",
        "preview": args.root / "preview",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)

    local_canonical = dirs["canonical"] / "canonical_front_2048.png"
    if args.canonical.resolve() != local_canonical.resolve():
        shutil.copy2(args.canonical, local_canonical)

    anchor = json.loads(args.anchor_report.read_text(encoding="utf-8"))
    manual = json.loads(args.manual_report.read_text(encoding="utf-8")) if args.manual_report.exists() else {}
    blink_review = manual.get("reviews", {}).get("blink:closed_lids", {})
    saved_dx = float(blink_review.get("canvas_dx", 0))
    saved_dy = float(blink_review.get("canvas_dy", 0))
    saved_calibrated_delta = "canvas_dx" in blink_review and "canvas_dy" in blink_review
    dx = saved_dx if args.apply_manual_delta else 0.0
    dy = saved_dy if args.apply_manual_delta else 0.0

    eye_rois = {
        "left": BBox(*anchor["metrics"]["left_eye_roi"]),
        "right": BBox(*anchor["metrics"]["right_eye_roi"]),
    }
    canonical = Image.open(local_canonical).convert("RGBA")
    pairs = crop_blink_pairs(args.blink_sheet, dirs["crops"])

    records = []
    for pair in pairs:
        stage = pair["stage"]
        combined = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
        part_records = []
        for part in pair["parts"]:
            side = part["side"]
            crop = Image.open(part["crop"]).convert("RGBA")
            layer, placement = place_part(crop, eye_rois[side], dx, dy)
            part_path = dirs["layers"] / f"{stage}_{side}_full.png"
            layer.save(part_path)
            combined.alpha_composite(layer)
            coverage = alpha_coverage_in_roi(layer, eye_rois[side])
            part_records.append({**part, **placement, "full_layer": str(part_path), "eye_roi": eye_rois[side].as_list(), "roi_alpha_coverage": coverage})

        combined_path = dirs["layers"] / f"blink_{stage}_full.png"
        overlay_path = dirs["overlays"] / f"blink_{stage}_overlay.png"
        combined.save(combined_path)
        overlay = canonical.copy()
        overlay.alpha_composite(combined)
        draw = ImageDraw.Draw(overlay)
        for side, roi in eye_rois.items():
            draw.rectangle([roi.x, roi.y, roi.x + roi.w, roi.y + roi.h], outline="cyan", width=4)
            draw.text((roi.x + 5, roi.y + 5), side, fill="cyan")
        overlay.save(overlay_path)
        coverage_mean = float(sum(p["roi_alpha_coverage"] for p in part_records) / len(part_records))
        records.append(
            {
                "stage": stage,
                "parts": part_records,
                "combined_layer": str(combined_path),
                "overlay": str(overlay_path),
                "coverage_mean": coverage_mean,
                "both_inside_eye_roi": all(p["inside_eye_roi"] for p in part_records),
                "human_verdict": "REVISE",
            }
        )

    coverage_values = [r["coverage_mean"] for r in records]
    coverage_trend_pass = coverage_values == sorted(coverage_values, reverse=True)
    inside_count = sum(1 for r in records if r["both_inside_eye_roi"])
    status = "OBSERVED"
    result = {
        "stage_layers_created": "PASS" if len(records) == 3 else "FAIL",
        "full_canvas_layers": "PASS" if all(Image.open(r["combined_layer"]).size == CANVAS for r in records) else "FAIL",
        "no_full_eye_replacement": "PASS",
        "both_parts_inside_eye_roi": "PASS" if inside_count == len(records) else "REVISE",
        "coverage_decreases_by_stage": "PASS" if coverage_trend_pass else "REVISE",
        "visual_alignment": "REVISE",
    }
    report = {
        "experiment_id": "BLINK-STAGE-001",
        "date": str(date.today()),
        "status": status,
        "inputs": [str(args.blink_sheet), str(local_canonical), str(args.anchor_report), str(args.manual_report)],
        "outputs": [str(dirs["preview"] / "index.html"), str(dirs["reports"] / "blink_stage_report.json")] + [r["combined_layer"] for r in records] + [r["overlay"] for r in records],
        "metrics": {
            "canvas_size": list(CANVAS),
            "left_eye_roi": eye_rois["left"].as_list(),
            "right_eye_roi": eye_rois["right"].as_list(),
            "saved_manual_blink_delta": {"dx": saved_dx, "dy": saved_dy, "calibrated_canvas_delta": saved_calibrated_delta},
            "placement_strategy": "saved_manual_delta" if args.apply_manual_delta else "eye_roi_center_no_delta",
            "manual_blink_delta_applied": {"dx": dx, "dy": dy, "applied": args.apply_manual_delta},
            "stage_count": len(records),
            "inside_eye_roi_stage_count": inside_count,
            "coverage_by_stage": {r["stage"]: r["coverage_mean"] for r in records},
        },
        "result": result,
        "stages": records,
        "human_review": {"required": True, "verdict": "REVISE", "notes": "Review whether stages read as eyelid closure rather than eyebrow/eyeliner. Numeric ROI is not enough."},
        "decision": "revise",
        "next_action": "Open preview/index.html and visually review half/mostly_closed/closed stages. If visual REVISE/PASS, run BLINK-CALIBRATION-001 to save a blink-specific correction.",
    }
    save_json(dirs["reports"] / "blink_stage_report.json", report)

    qa = [
        "# Blink Stage 001 QA",
        "",
        f"Date: {date.today()}",
        "",
        "## Verdict",
        "",
        "- Status: OBSERVED",
        "- Blink stage full-canvas layers were generated.",
        "- Human review is required before calling this production blink.",
        "",
        "## Evidence",
        "",
        f"- Stages: {len(records)}",
        f"- Eye ROI inside stages: {inside_count}/{len(records)}",
        f"- Placement strategy: {'saved manual delta' if args.apply_manual_delta else 'eye ROI center, no manual delta'}",
        f"- Saved manual blink delta available: dx={saved_dx}, dy={saved_dy}, calibrated={saved_calibrated_delta}",
        f"- Manual blink delta applied: dx={dx}, dy={dy}, applied={args.apply_manual_delta}",
        f"- Coverage by stage: {json.dumps(report['metrics']['coverage_by_stage'], ensure_ascii=False)}",
        f"- Coverage decreases by stage: {result['coverage_decreases_by_stage']}",
        "",
        "## Review",
        "",
        f"- Preview: `{dirs['preview'] / 'index.html'}`",
        f"- Report: `{dirs['reports'] / 'blink_stage_report.json'}`",
    ]
    (dirs["reports"] / "qa_report.md").write_text("\n".join(qa) + "\n", encoding="utf-8")
    build_preview(args.root, records, dirs["preview"] / "index.html", local_canonical)
    print(json.dumps({"root": str(args.root), "preview": str(dirs["preview"] / "index.html"), "report": str(dirs["reports"] / "blink_stage_report.json")}, indent=2))


if __name__ == "__main__":
    main()

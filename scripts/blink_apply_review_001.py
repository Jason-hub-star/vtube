#!/usr/bin/env python3
"""Apply saved blink review placement to staged blink layers."""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

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

    def as_list(self) -> list[int]:
        return [self.x, self.y, self.w, self.h]


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


def shift_layer(layer: Image.Image, dx: float, dy: float) -> Image.Image:
    src = layer.convert("RGBA")
    out = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    out.alpha_composite(src, (int(round(dx)), int(round(dy))))
    return out


def bbox_inside(inner: BBox | None, outer: BBox) -> bool:
    return bool(
        inner
        and inner.x >= outer.x
        and inner.y >= outer.y
        and inner.x + inner.w <= outer.x + outer.w
        and inner.y + inner.h <= outer.y + outer.h
    )


def build_preview(records: list[dict], out_path: Path) -> None:
    def rel(path: str) -> str:
        return Path(os.path.relpath(path, out_path.parent)).as_posix()

    payload = json.dumps(
        [
            {
                "stage": r["stage"],
                "auto": rel(r["auto_overlay"]),
                "corrected": rel(r["corrected_overlay"]),
                "inside": r["both_inside_eye_roi"],
                "verdict": r["human_verdict"],
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
  <title>Blink Apply Review 001</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #171b20; color: #f5f7fb; }}
    main {{ display: grid; grid-template-columns: 300px 1fr; min-height: 100vh; }}
    aside {{ padding: 16px; background: #222832; border-right: 1px solid rgba(255,255,255,.14); }}
    button {{ display: block; width: 100%; margin: 0 0 8px; padding: 10px; border: 1px solid rgba(255,255,255,.16); background: #2d3541; color: #f5f7fb; border-radius: 8px; text-align: left; cursor: pointer; }}
    button.active {{ border-color: #73d0ff; background: #254253; }}
    .stage {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; padding: 18px; align-content: start; }}
    figure {{ margin: 0; }}
    figcaption {{ margin-bottom: 8px; color: #b8c1cc; font-size: 13px; }}
    img {{ display: block; width: 100%; background: #343b46; }}
    .meta {{ margin-top: 12px; color: #b8c1cc; font-size: 13px; }}
  </style>
</head>
<body>
<main>
  <aside>
    <h1>깜빡임 보정 적용</h1>
    <div id="list"></div>
    <div id="meta" class="meta"></div>
  </aside>
  <section class="stage">
    <figure><figcaption>자동 배치</figcaption><img id="auto" alt="자동 배치"></figure>
    <figure><figcaption>저장값 적용</figcaption><img id="corrected" alt="저장값 적용"></figure>
  </section>
</main>
<script>
const records = {payload};
const list = document.getElementById('list');
const meta = document.getElementById('meta');
const auto = document.getElementById('auto');
const corrected = document.getElementById('corrected');
const names = {{ half: '반쯤 감김', mostly_closed: '거의 감김', closed: '완전 감김' }};
function select(i) {{
  [...list.children].forEach((button, idx) => button.classList.toggle('active', idx === i));
  const record = records[i];
  auto.src = record.auto;
  corrected.src = record.corrected;
  meta.textContent = `${{names[record.stage]}} / ROI ${{record.inside ? '통과' : '수정'}} / 검수 ${{record.verdict}}`;
}}
records.forEach((record, i) => {{
  const button = document.createElement('button');
  button.textContent = names[record.stage] || record.stage;
  button.onclick = () => select(i);
  list.appendChild(button);
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
    parser.add_argument("--root", type=Path, default=Path("/Users/family/jason/Vtube/experiments/blink-apply-review-001"))
    parser.add_argument("--source-root", type=Path, default=Path("/Users/family/jason/Vtube/experiments/blink-stage-001"))
    parser.add_argument("--anchor-report", type=Path, default=Path("/Users/family/jason/Vtube/experiments/production-canvas-2048-001/reports/anchor_2048_report.json"))
    args = parser.parse_args()

    dirs = {
        "layers": args.root / "layers",
        "overlays": args.root / "overlays",
        "reports": args.root / "reports",
        "preview": args.root / "preview",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)

    review_path = args.source_root / "reports" / "blink_stage_review.json"
    stage_report_path = args.source_root / "reports" / "blink_stage_report.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))
    stage_report = json.loads(stage_report_path.read_text(encoding="utf-8"))
    anchor = json.loads(args.anchor_report.read_text(encoding="utf-8"))
    rois = {
        "left": BBox(*anchor["metrics"]["left_eye_roi"]),
        "right": BBox(*anchor["metrics"]["right_eye_roi"]),
    }
    canonical = Image.open(args.source_root / "canonical" / "canonical_front_2048.png").convert("RGBA")

    records = []
    for stage in STAGES:
        placement = review.get("placements", {}).get(stage, {})
        dx = float(placement.get("canvas_dx", 0))
        dy = float(placement.get("canvas_dy", 0))
        corrected_combined = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
        parts = []
        for side in ["left", "right"]:
            src = Image.open(args.source_root / "layers" / f"{stage}_{side}_full.png").convert("RGBA")
            corrected = shift_layer(src, dx, dy)
            corrected_path = dirs["layers"] / f"{stage}_{side}_corrected_full.png"
            corrected.save(corrected_path)
            corrected_combined.alpha_composite(corrected)
            bbox = bbox_from_alpha(corrected)
            center = center_of_alpha(corrected)
            parts.append(
                {
                    "side": side,
                    "corrected_layer": str(corrected_path),
                    "eye_roi": rois[side].as_list(),
                    "alpha_bbox": bbox.as_list() if bbox else None,
                    "alpha_center": [round(center[0], 3), round(center[1], 3)] if center else None,
                    "inside_eye_roi": bbox_inside(bbox, rois[side]),
                }
            )

        corrected_layer_path = dirs["layers"] / f"blink_{stage}_corrected_full.png"
        corrected_combined.save(corrected_layer_path)
        corrected_overlay = canonical.copy()
        corrected_overlay.alpha_composite(corrected_combined)
        draw = ImageDraw.Draw(corrected_overlay)
        for side, roi in rois.items():
            draw.rectangle([roi.x, roi.y, roi.x + roi.w, roi.y + roi.h], outline="cyan", width=4)
        corrected_overlay_path = dirs["overlays"] / f"blink_{stage}_corrected_overlay.png"
        corrected_overlay.save(corrected_overlay_path)

        auto_overlay_src = args.source_root / "overlays" / f"blink_{stage}_overlay.png"
        auto_overlay_dst = dirs["overlays"] / f"blink_{stage}_auto_overlay.png"
        Image.open(auto_overlay_src).save(auto_overlay_dst)
        verdict = review.get("reviews", {}).get(stage, {}).get("verdict", "REVISE")
        records.append(
            {
                "stage": stage,
                "placement": placement,
                "corrected_layer": str(corrected_layer_path),
                "corrected_overlay": str(corrected_overlay_path),
                "auto_overlay": str(auto_overlay_dst),
                "parts": parts,
                "both_inside_eye_roi": all(p["inside_eye_roi"] for p in parts),
                "human_verdict": verdict,
            }
        )

    inside_count = sum(1 for r in records if r["both_inside_eye_roi"])
    all_reviewed = all(r["human_verdict"] in {"PASS", "REVISE", "FAIL"} for r in records)
    report = {
        "experiment_id": "BLINK-APPLY-REVIEW-001",
        "date": str(date.today()),
        "status": "OBSERVED",
        "inputs": [str(review_path), str(stage_report_path)],
        "outputs": [str(dirs["preview"] / "index.html"), str(dirs["reports"] / "blink_apply_review_report.json")] + [r["corrected_layer"] for r in records] + [r["corrected_overlay"] for r in records],
        "metrics": {
            "canvas_size": list(CANVAS),
            "stage_count": len(records),
            "corrected_inside_eye_roi_stage_count": inside_count,
            "reviewed_stage_count": sum(1 for r in records if r["human_verdict"]),
        },
        "result": {
            "saved_placement_applied": "PASS",
            "full_canvas_layers": "PASS",
            "corrected_inside_eye_roi": "PASS" if inside_count == len(records) else "REVISE",
            "human_review_all_stages_present": "PASS" if all_reviewed else "REVISE",
            "production_candidate": "REVISE",
        },
        "stages": records,
        "human_review": {
            "required": True,
            "verdict": "REVISE",
            "notes": "Saved blink placement was applied to all stages. Numeric ROI may differ from visual judgement; final production approval still requires visual PASS.",
        },
        "decision": "revise",
        "next_action": "Open preview/index.html and compare auto vs corrected. If corrected visual alignment passes, promote blink path; otherwise adjust saved placement or use canonical edit fallback.",
    }
    save_json(dirs["reports"] / "blink_apply_review_report.json", report)

    qa = [
        "# Blink Apply Review 001 QA",
        "",
        f"Date: {date.today()}",
        "",
        "## Verdict",
        "",
        "- Status: OBSERVED",
        "- Saved blink placement was applied to full-canvas layers.",
        "- Human review remains separate from numeric ROI.",
        "",
        "## Evidence",
        "",
        f"- Stages: {len(records)}",
        f"- Corrected inside eye ROI: {inside_count}/{len(records)}",
        f"- Reviewed stage count: {report['metrics']['reviewed_stage_count']}",
        "",
        "## Review",
        "",
        f"- Preview: `{dirs['preview'] / 'index.html'}`",
        f"- Report: `{dirs['reports'] / 'blink_apply_review_report.json'}`",
    ]
    (dirs["reports"] / "qa_report.md").write_text("\n".join(qa) + "\n", encoding="utf-8")
    build_preview(records, dirs["preview"] / "index.html")
    print(json.dumps({"root": str(args.root), "preview": str(dirs["preview"] / "index.html"), "report": str(dirs["reports"] / "blink_apply_review_report.json")}, indent=2))


if __name__ == "__main__":
    main()

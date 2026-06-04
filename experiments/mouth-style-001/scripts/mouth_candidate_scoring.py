#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


ROOT = Path("/Users/family/jason/Vtube")
EXP = ROOT / "experiments" / "mouth-style-001"
CANONICAL = ROOT / "experiments/imagegen-limit-test-001/generated/canonical_front.png"
MOUTH_CROPS = ROOT / "experiments/validation-smoke-001/crops/mouth"
FULL_CANVAS_REPORT = ROOT / "experiments/full-canvas-layer-001/reports/full_canvas_layer_report.json"


def alpha_bbox(img: Image.Image) -> tuple[list[int], int]:
    arr = np.array(img.convert("RGBA"))
    alpha = arr[:, :, 3] > 0
    ys, xs = np.where(alpha)
    if len(xs) == 0:
        return [0, 0, 0, 0], 0
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1], int(alpha.sum())


def color_features(img: Image.Image) -> dict:
    arr = np.array(img.convert("RGBA"))
    alpha = arr[:, :, 3] > 0
    if not np.any(alpha):
        return {"dark_ratio": 0, "red_ratio": 0, "white_ratio": 0, "mean_rgb": [0, 0, 0]}
    rgb = arr[:, :, :3][alpha]
    hsv = cv2.cvtColor(rgb.reshape(-1, 1, 3).astype(np.uint8), cv2.COLOR_RGB2HSV).reshape(-1, 3)
    dark_ratio = float(np.mean(np.mean(rgb, axis=1) < 90))
    red_ratio = float(np.mean(((hsv[:, 0] < 12) | (hsv[:, 0] > 165)) & (hsv[:, 1] > 45)))
    white_ratio = float(np.mean((hsv[:, 1] < 35) & (hsv[:, 2] > 180)))
    return {
        "dark_ratio": round(dark_ratio, 4),
        "red_ratio": round(red_ratio, 4),
        "white_ratio": round(white_ratio, 4),
        "mean_rgb": [round(float(x), 2) for x in rgb.mean(axis=0)],
    }


def expression_type(width: int, height: int, features: dict) -> str:
    aspect = width / max(1, height)
    if width >= 70 and aspect > 4.0 and height >= 10:
        return "closed_or_smile_line"
    if width < 50 or height < 25:
        return "reject_mark_or_fragment"
    if features["dark_ratio"] > 0.35 and height > 70:
        return "open_mouth"
    if features["white_ratio"] > 0.35:
        return "teeth_smile"
    if features["red_ratio"] > 0.45 and height > width * 0.5:
        return "tongue_or_open_vowel"
    return "mouth_candidate"


def style_score(width: int, height: int, features: dict) -> float:
    # Prefer readable mouth shapes with moderate size and clear non-white foreground.
    area_term = min((width * height) / 20000.0, 1.0)
    color_term = min(features["dark_ratio"] + features["red_ratio"] + features["white_ratio"], 1.0)
    fragment_penalty = 0.45 if width < 50 or height < 25 else 0.0
    huge_penalty = 0.25 if width > 240 or height > 210 else 0.0
    return round(max(0.0, area_term * 0.45 + color_term * 0.55 - fragment_penalty - huge_penalty), 4)


def main() -> None:
    (EXP / "reports").mkdir(parents=True, exist_ok=True)
    full = json.loads(FULL_CANVAS_REPORT.read_text(encoding="utf-8"))
    full_by_id = {c["id"]: c for c in full["candidates"]}
    candidates = []
    for path in sorted(MOUTH_CROPS.glob("mouth_*.png")):
        img = Image.open(path).convert("RGBA")
        bbox, alpha_pixels = alpha_bbox(img)
        width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        features = color_features(img)
        xtype = expression_type(width, height, features)
        score = style_score(width, height, features)
        full_entry = full_by_id.get(path.stem)
        rejected = xtype == "reject_mark_or_fragment" or (score < 0.18 and xtype != "closed_or_smile_line")
        candidates.append(
            {
                "id": path.stem,
                "path": str(path),
                "alpha_bbox": bbox,
                "width": width,
                "height": height,
                "alpha_pixels": alpha_pixels,
                "expression_type": xtype,
                "features": features,
                "style_score": score,
                "full_canvas_layer": full_entry["layer"] if full_entry else None,
                "placement_error_px": full_entry["placement_error_px"] if full_entry else None,
                "decision": "reject" if rejected else "shortlist",
                "decision_reason": "fragment_or_low_style_score" if rejected else "candidate_for_human_review",
            }
        )
    shortlist = sorted([c for c in candidates if c["decision"] == "shortlist"], key=lambda c: c["style_score"], reverse=True)
    rejected = [c for c in candidates if c["decision"] == "reject"]
    expression_types = sorted(set(c["expression_type"] for c in candidates if c["decision"] == "shortlist"))
    passed = len(expression_types) >= 3 and len(shortlist) >= 3 and len(rejected) >= 1
    report = {
        "experiment_id": "MOUTH-STYLE-001",
        "date": "2026-06-02",
        "status": "OBSERVED" if passed else "UNVERIFIED",
        "inputs": [str(MOUTH_CROPS), str(FULL_CANVAS_REPORT)],
        "outputs": [str(EXP / "reports" / "mouth_candidate_score_report.json")],
        "metrics": {
            "candidate_count": len(candidates),
            "shortlist_count": len(shortlist),
            "rejected_count": len(rejected),
            "expression_types": expression_types,
        },
        "result": {
            "expression_type_assignment": "PASS" if len(expression_types) >= 3 else "FAIL",
            "shortlist_created": "PASS" if len(shortlist) >= 3 else "FAIL",
            "rejected_candidates_recorded": "PASS" if rejected else "FAIL",
            "visual_quality": "REVISE",
        },
        "candidates": candidates,
        "shortlist": [c["id"] for c in shortlist[:6]],
        "rejected": [c["id"] for c in rejected],
        "human_review": {
            "required": True,
            "verdict": "REVISE",
            "notes": "Scores rank candidates but do not replace human style judgment.",
        },
        "decision": "keep" if passed else "revise",
        "next_action": "Use shortlist for previewer, then require visual accept/reject per expression.",
    }
    out = EXP / "reports" / "mouth_candidate_score_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP / "reports" / "qa_report.md").write_text(
        "\n".join(
            [
                "# MOUTH-STYLE-001 QA Report",
                "",
                "## Result",
                "",
                f"- expression_type_assignment: {report['result']['expression_type_assignment']}",
                f"- shortlist_created: {report['result']['shortlist_created']}",
                f"- rejected_candidates_recorded: {report['result']['rejected_candidates_recorded']}",
                f"- visual_quality: {report['result']['visual_quality']}",
                "",
                "## Shortlist",
                "",
                ", ".join(report["shortlist"]),
                "",
                "## Rejected",
                "",
                ", ".join(report["rejected"]),
                "",
                "## Guardrail",
                "",
                "Style scores only narrow the review set. They do not approve production art quality.",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(report["result"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

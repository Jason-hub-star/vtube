#!/usr/bin/env python3
"""EXPR-002 눈웃음 후보 비교 스트립 — ∩/∪ 곡선 후보를 실제 조립본에 렌더해 주인님이 고른다.

지난 EXPR-001 실패 교훈: 곡선 수치를 추측해서 박지 말고, 후보를 나란히 렌더해
육안 선택을 먼저 받는다. 선택된 수치만 리그 키폼으로 들어간다.

사용: python3 scripts/build_eye_smile_candidates.py \
        --arap-config experiments/autorig-character-003/arap_blink_layers/arap_blink_config.json \
        --out-dir experiments/autorig-character-003/reports/eye_smile_candidates
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, load_json, now_iso, rel, write_json  # noqa: E402
from run_arap_blink_experiment import curtain_warp, eye_bbox_from_layer  # noqa: E402

# (라벨, lid_center, low_center, 설명) — 0.45 미만 = ∩(^^), 초과 = ∪(니코니코)
CANDIDATES = [
    ("A", 0.34, 0.42, "얕은 ^^ (선이 높고 완만)"),
    ("B", 0.28, 0.35, "깊은 ^^ (지난 1차 수치)"),
    ("C", 0.40, 0.48, "중간 높이 (살짝만 ^)"),
    ("D", 0.58, 0.66, "니코니코 ∪ (선이 낮고 아래로 볼록)"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arap-config", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    cfg = load_json(args.arap_config)
    base = np.asarray(Image.open(ROOT / cfg["assembly"]).convert("RGBA"))
    bboxes = [eye_bbox_from_layer(ROOT / cfg[f"eye_white_{side}"]) for side in ("L", "R")]

    # 두 눈 + 볼 일부 크롭 영역
    fx0 = min(b[0] for b in bboxes) - 90
    fx1 = max(b[2] for b in bboxes) + 90
    fy0 = min(b[1] for b in bboxes) - 110
    fy1 = max(b[3] for b in bboxes) + 150

    panels = [("원본", Image.fromarray(base, "RGBA").crop((fx0, fy0, fx1, fy1)).convert("RGB"))]
    for label, lid_c, low_c, _desc in CANDIDATES:
        warped = base
        for bbox in bboxes:
            warped = curtain_warp(warped, bbox, 1.0, smile=(lid_c, low_c))
        panels.append((label, Image.fromarray(warped, "RGBA").crop((fx0, fy0, fx1, fy1)).convert("RGB")))

    pw, ph = panels[0][1].size
    label_h = 56
    strip = Image.new("RGB", (pw * len(panels) + 8 * (len(panels) - 1), ph + label_h), (255, 255, 255))
    draw = ImageDraw.Draw(strip)
    for i, (label, img) in enumerate(panels):
        x = i * (pw + 8)
        strip.paste(img, (x, label_h))
        draw.text((x + pw // 2 - 14, 10), label, fill=(20, 20, 20), font_size=36)
    strip_path = out / "smile_candidates.png"
    strip.save(strip_path)

    write_json(out / "smile_candidates.json", {
        "test_id": "EXPR-002-smile-candidates",
        "generated_at": now_iso(),
        "candidates": [{"label": c[0], "lid_center": c[1], "low_center": c[2], "desc": c[3]} for c in CANDIDATES],
        "strip": rel(strip_path),
        "verdict": "PENDING_OWNER_CHOICE",
    })
    print(f"strip: {rel(strip_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

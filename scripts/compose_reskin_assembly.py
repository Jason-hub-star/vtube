#!/usr/bin/env python3
"""재스킨 레이어를 draw_order 순으로 합성해 어셈블리 PNG를 만든다.

H1.5 게이트 아티팩트이자 입 추출(톤매칭·턱선 측정)과 ARAP 베이크의 입력.

사용: python3 scripts/compose_reskin_assembly.py \
        --reskin-manifest experiments/<exp>/seethrough_true_reskinned/reskin_manifest.json \
        --out experiments/<exp>/reports/full_assembly/assembly.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, load_json, rel  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reskin-manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    manifest = load_json(args.reskin_manifest)
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)

    canvas = None
    count = 0
    for layer in sorted(manifest["layers"], key=lambda item: item["draw_order"]):
        if "reference" in layer["part_id"]:
            continue
        path = ROOT / layer["path"]
        if not path.exists():
            continue
        img = Image.open(path).convert("RGBA")
        if canvas is None:
            canvas = Image.new("RGBA", img.size, (255, 255, 255, 255))
        canvas.alpha_composite(img)
        count += 1
    if canvas is None:
        raise SystemExit("합성할 레이어가 없어요")
    canvas.save(out)
    print(f"assembly: {rel(out)} (layers={count})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

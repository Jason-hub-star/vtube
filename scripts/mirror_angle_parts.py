#!/usr/bin/env python3
"""좌향 각도 작화를 수평 flip해 우향 미러 생성 (ANGLE-SWAP-002).

extract_angle_sheet가 만든 head_angle_1..4.png(좌향, 머리 꼭대기를 캔버스 중심
x=1024 앵커에 정렬)를 x중심 기준으로 수평 반전 → head_angle_right_1..4.png.
앵커가 캔버스 중심 x라 flip해도 머리 정렬이 유지된다. 가르마/머리타래는 뒤집힘
(주인님 무료 미러 선택 — 위벨은 좌우 비대칭이 약해 티가 적음).

정면(head_angle_0)은 미러 불필요 — 통합 시 정면은 라이브 리그가 그린다.

사용: python3 scripts/mirror_angle_parts.py --parts experiments/autorig-character-004/angle_swap_project/parts
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, now_iso, rel, write_json  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parts", type=Path, required=True,
                        help="head_angle_1..4.png 가 있는 parts 디렉터리")
    parser.add_argument("--count", type=int, default=4, help="미러할 좌향 각도 수 (정면 제외)")
    args = parser.parse_args()
    parts = args.parts if args.parts.is_absolute() else ROOT / args.parts
    if not parts.is_dir():
        raise SystemExit(f"parts 디렉터리 없음: {parts}")

    written = []
    for i in range(1, args.count + 1):
        src = parts / f"head_angle_{i}.png"
        if not src.exists():
            raise SystemExit(f"좌향 각도 없음: {src} — extract_angle_sheet 먼저")
        img = Image.open(src).convert("RGBA")
        # 캔버스 중심(x=W/2)이 머리 앵커 → 좌우반전해도 머리 제자리
        mirrored = img.transpose(Image.FLIP_LEFT_RIGHT)
        dst = parts / f"head_angle_right_{i}.png"
        mirrored.save(dst)
        written.append(dst.name)
        print(f"head_angle_{i} -> {dst.name} (flip x={img.width // 2})")

    write_json(parts.parent / "mirror_manifest.json", {
        "generated_at": now_iso(), "source_parts": rel(parts), "count": args.count,
        "method": "FLIP_LEFT_RIGHT around canvas center x", "written": written,
        "note": "좌향 head_angle_1..4 -> 우향 head_angle_right_1..4 무료 미러"})
    print(f"우향 미러 {len(written)}장 -> {rel(parts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""모든 시트의 정규화 레이어를 모아 전신 조립 합성을 만든다 (검수 단위 규칙).

- draw order: FULL_BAND_ORDER (hair_back이 맨 뒤 … hair_front가 맨 앞), 같은 밴드는 underpaint 먼저
- 중립 조립: closed 키포즈 레이어 제외
- 클리핑: *_white가 같은 눈의 iris/pupil/highlight를 클리핑 (런타임 동일)
- 산출: full_assembly.png + 그룹별 조립 + 원본 비교용 사이드바이사이드

사용: python3 scripts/build_autorig_full_assembly.py \
        --spec <template spec json> --layers-root <out-dir>/normalized_layers \
        --style-ref <png> --out-dir <out-dir>/reports/full_assembly
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, load_json, now_iso, rel, write_json  # noqa: E402
from lib.vtube_image import make_thumb  # noqa: E402

FULL_BAND_ORDER = [
    "hair_back", "body_back", "body_mid", "body_front", "clothing_mid", "clothing_front",
    "face_back", "face_mid", "face_front", "eye_back", "eye_mid", "eye_front",
    "brow_front", "mouth_back", "mouth_mid", "mouth_front", "hair_side", "hair_front",
]
NEUTRAL_EXCLUDE_TOKENS = ("closed", "mouth_inner", "mouth_teeth", "mouth_tongue")  # 중립 = 뜬 눈 + 다문 입
CLIP_SUFFIXES = ("_iris", "_pupil", "_highlight")


def order_key(slot: dict) -> tuple:
    band = slot["draw_order_band"]
    idx = FULL_BAND_ORDER.index(band) if band in FULL_BAND_ORDER else 99
    return (idx, 0 if "underpaint" in slot["part_id"] else 1)


def compose(slots: list[dict], layers_root: Path, out_path: Path) -> tuple[Path | None, list[str]]:
    usable = [s for s in slots if not any(t in s["part_id"] for t in NEUTRAL_EXCLUDE_TOKENS)]
    usable.sort(key=order_key)
    whites: dict[str, np.ndarray] = {}
    missing: list[str] = []
    resolved: list[tuple[dict, Path]] = []
    for slot in usable:
        path = layers_root / slot["sheet_id"] / f"{slot['part_id']}.png"
        if not path.exists():
            missing.append(slot["part_id"])
            continue
        resolved.append((slot, path))
        if slot["part_id"].endswith("_white"):
            alpha = np.asarray(Image.open(path).convert("RGBA"))[..., 3].astype(np.float32) / 255.0
            whites[slot["part_id"].removesuffix("_white")] = alpha
    canvas = None
    for slot, path in resolved:
        layer = np.asarray(Image.open(path).convert("RGBA")).copy()
        if slot["part_id"].endswith(CLIP_SUFFIXES):
            mask = whites.get(slot["part_id"].rsplit("_", 1)[0])
            if mask is not None:
                layer[..., 3] = (layer[..., 3].astype(np.float32) * mask).astype(np.uint8)
        img = Image.fromarray(layer, "RGBA")
        if canvas is None:
            canvas = Image.new("RGBA", img.size, (0, 0, 0, 0))
        canvas.alpha_composite(img)
    if canvas is None:
        return None, missing
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)
    return out_path, missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--layers-root", type=Path, required=True)
    parser.add_argument("--style-ref", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    spec = load_json(args.spec)
    slots = []
    for sheet in spec["sheets"]:
        for slot in sheet["slots"]:
            slots.append({**slot, "sheet_id": sheet["sheet_id"]})

    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    full_path, missing = compose(slots, args.layers_root, out_dir / "full_assembly.png")

    group_paths = {}
    for group in sorted({s["group"] for s in slots}):
        gslots = [s for s in slots if s["group"] == group]
        gpath, _ = compose(gslots, args.layers_root, out_dir / f"assembly_{group}.png")
        if gpath:
            group_paths[group] = rel(gpath)

    side = None
    if full_path:
        ref = Image.open(args.style_ref).convert("RGBA")
        asm = Image.open(full_path).convert("RGBA")
        if ref.size != asm.size:
            ref = ref.resize(asm.size)
        white_bg = Image.new("RGBA", (asm.width * 2 + 32, asm.height), (255, 255, 255, 255))
        white_bg.alpha_composite(ref, (0, 0))
        white_bg.alpha_composite(asm, (asm.width + 32, 0))
        side = out_dir / "side_by_side_ref_vs_assembly.png"
        white_bg.convert("RGB").save(side)
        make_thumb(full_path, out_dir / "full_assembly_thumb.png", size=900, crop_alpha=True)

    report = {
        "generated_at": now_iso(),
        "full_assembly": rel(full_path) if full_path else None,
        "side_by_side": rel(side) if side else None,
        "groups": group_paths,
        "total_slots": len(slots),
        "missing_layers": missing,
        "missing_count": len(missing),
    }
    write_json(out_dir / "full_assembly_report.json", report)
    print(f"full={report['full_assembly']} missing={len(missing)} groups={len(group_paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

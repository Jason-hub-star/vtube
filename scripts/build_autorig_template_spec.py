#!/usr/bin/env python3
"""AUTORIG-TEMPLATE-SPEC-001: 64-part를 고정 슬롯 시트에 매핑하는 템플릿 스펙 생성.

핵심 아이디어: 파트를 "완성 캐릭터에서 사후 추출"하지 않고 슬롯에 분리 생성한다.
어느 슬롯에 어떤 파트가 있는지 생성 시점에 이미 알기 때문에 추출이 결정론적이다.

- 슬롯 크기: 파트 타깃 bbox 최대 변 > 480px → 2x2 대형 슬롯(1024), 이하 → 4x4 소형 슬롯(512)
- 타깃 앵커: 매니페스트의 기존 bbox 재사용 (같은 캐릭터 디자인이므로 유효)
- 배경: 크로마 마젠타 #FF00FF (투명 PNG 미지원 모델 대응)

사용: python3 scripts/build_autorig_template_spec.py \
        --manifest <64part manifest json> --out-dir <experiment>/reports/template_spec
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, load_json, now_iso, rel, write_json  # noqa: E402

CHROMA = "#FF00FF"
CANVAS = 2048
LARGE_THRESHOLD = 480

# 파트 id → 영어 생성 설명 (시트 프롬프트용). 없는 id는 generic_description으로 유도.
DESCRIPTIONS = {
    "eye_L_white": "left eye white sclera shape only (eyeball base, no iris)",
    "eye_L_underpaint": "left eye socket underpaint, flat skin-tone filler shape",
    "eye_L_iris": "left eye iris disc only, with the character's iris color and shading",
    "eye_L_pupil": "left eye pupil only, small dark ellipse",
    "eye_L_highlight": "left eye light highlights only, small white sparkle shapes",
    "eye_L_upper_lash": "left eye upper eyelash line with lash details",
    "eye_L_lower_lash": "left eye lower eyelash line, thin and subtle",
    "eye_L_closed_lid": "left eye fully closed eyelid line on skin-tone lid shape",
    "eye_R_white": "right eye white sclera shape only (eyeball base, no iris)",
    "eye_R_underpaint": "right eye socket underpaint, flat skin-tone filler shape",
    "eye_R_iris": "right eye iris disc only, with the character's iris color and shading",
    "eye_R_pupil": "right eye pupil only, small dark ellipse",
    "eye_R_highlight": "right eye light highlights only, small white sparkle shapes",
    "eye_R_upper_lash": "right eye upper eyelash line with lash details",
    "eye_R_lower_lash": "right eye lower eyelash line, thin and subtle",
    "eye_R_closed_lid": "right eye fully closed eyelid line on skin-tone lid shape",
}

SHEET_FAMILIES = {
    "eye": ("eye_L", "eye_R"),
    "mouth": ("mouth",),
    "face_brow": ("face_base", "brow"),
    "hair": ("hair",),
    "body": ("body",),
    "clothing": ("clothing",),
}


def generic_description(part_id: str, label_ko: str) -> str:
    words = part_id.replace("_", " ")
    return f"{words} — isolated part of the character ({label_ko}), drawn alone"


def sheet_prompt(sheet: dict) -> str:
    grid = sheet["grid"]
    lines = [
        "Anime character PART SHEET for Live2D-style rigging. Square 2048x2048 image.",
        f"The ENTIRE background must be one flat solid magenta color {CHROMA} with no gradient.",
        f"Imagine an invisible {grid['rows']}x{grid['cols']} grid of {grid['cell']}px cells.",
        "Draw EXACTLY ONE isolated element per cell, centered in its cell, fully inside the cell",
        "with generous margin; nothing may touch or cross cell boundaries.",
        "STRICT: no text, no labels, no numbers, no grid lines, no boxes, no full character,",
        "no extra elements, no drop shadows on the background.",
        "Every element must match the art style, line weight, colors and facial design of the",
        "attached reference character EXACTLY (same character).",
        "Elements by cell (row, column), top-left is (1,1):",
    ]
    for slot in sheet["slots"]:
        lines.append(f"- ({slot['row']},{slot['col']}): {slot['description']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True, help="64-part 후보 매니페스트 JSON")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    entries = manifest["manifest_entries"]
    by_group: dict[str, list[dict]] = {}
    for entry in entries:
        by_group.setdefault(entry["group"], []).append(entry)

    sheets = []
    for family, groups in SHEET_FAMILIES.items():
        parts = [e for g in groups for e in by_group.get(g, [])]
        small = [e for e in parts if max(e["bbox"][2] - e["bbox"][0], e["bbox"][3] - e["bbox"][1]) <= LARGE_THRESHOLD]
        large = [e for e in parts if e not in small]
        for kind, pool, per_sheet, dims in (("small", small, 16, (4, 4, 512)), ("large", large, 4, (2, 2, 1024))):
            for chunk_idx in range(0, len(pool), per_sheet):
                chunk = pool[chunk_idx : chunk_idx + per_sheet]
                rows, cols, cell = dims
                slots = []
                for i, entry in enumerate(chunk):
                    row, col = divmod(i, cols)
                    x0, y0, x1, y1 = entry["bbox"]
                    slots.append(
                        {
                            "index": i,
                            "row": row + 1,
                            "col": col + 1,
                            "cell_px": [col * cell, row * cell, (col + 1) * cell, (row + 1) * cell],
                            "part_id": entry["id"],
                            "label_ko": entry["label_ko"],
                            "group": entry["group"],
                            "draw_order_band": entry["draw_order_band"],
                            "target_bbox": entry["bbox"],
                            "target_center": [round((x0 + x1) / 2), round((y0 + y1) / 2)],
                            "description": DESCRIPTIONS.get(entry["id"]) or generic_description(entry["id"], entry["label_ko"]),
                        }
                    )
                sheet_id = f"{family}_{kind}_{chunk_idx // per_sheet + 1:02d}"
                sheet = {
                    "sheet_id": sheet_id,
                    "family": family,
                    "grid": {"rows": rows, "cols": cols, "cell": cell},
                    "canvas": CANVAS,
                    "chroma": CHROMA,
                    "slots": slots,
                }
                sheet["prompt"] = sheet_prompt(sheet)
                sheets.append(sheet)

    spec = {
        "schema_version": 1,
        "spec_id": "autorig_template_spec_v1",
        "generated_at": now_iso(),
        "source_manifest": rel(args.manifest),
        "canvas": CANVAS,
        "chroma": CHROMA,
        "rules": {
            "no_labels": "evidence log: 라벨 시트는 오타/불균형 유발 — 텍스트 전면 금지",
            "slot_margin": "셀 경계 접촉 금지, 점유율 검사로 강제",
            "anchor_reuse": "동일 캐릭터 디자인이므로 기존 매니페스트 bbox를 타깃 앵커로 재사용",
        },
        "sheet_count": len(sheets),
        "part_count": sum(len(s["slots"]) for s in sheets),
        "sheets": sheets,
    }
    out = write_json(args.out_dir / "autorig_template_spec.json", spec)
    summary = [f"{s['sheet_id']}: {len(s['slots'])} slots ({s['grid']['rows']}x{s['grid']['cols']}@{s['grid']['cell']})" for s in sheets]
    print(f"wrote {out}")
    print(f"sheets={len(sheets)} parts={spec['part_count']}")
    print("\n".join(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

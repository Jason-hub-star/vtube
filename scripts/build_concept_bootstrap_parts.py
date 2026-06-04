#!/usr/bin/env python3
"""Create rough full-canvas concept part candidates for visual review.

These are bootstrap masks, not final production parts. They intentionally favor
making the part visible in the review UI over clean segmentation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "concept-regeneration-001"
CANONICAL = EXP / "canonical" / "canonical_front_2048.png"
OUT_DIR = EXP / "production_layers_candidate"
MANIFEST = EXP / "layer_manifest.json"
SCHEMA = EXP / "concept_part_schema.json"
REPORT = EXP / "reports" / "bootstrap_generation_report.json"


BOXES: dict[str, tuple[int, int, int, int]] = {
    "face_underpaint": (700, 610, 680, 650),
    "face_base": (705, 600, 670, 620),
    "neck": (900, 1130, 280, 260),
    "body": (470, 1180, 1110, 850),
    "clothes": (620, 1180, 820, 850),
    "back_hair": (260, 120, 1530, 1580),
    "front_hair": (520, 150, 1010, 900),
    "L_side_hair": (260, 360, 610, 1320),
    "R_side_hair": (1180, 360, 610, 1320),
    "L_eye_white": (720, 745, 260, 140),
    "R_eye_white": (1070, 745, 260, 140),
    "L_iris": (800, 745, 100, 130),
    "R_iris": (1150, 745, 100, 130),
    "L_pupil": (835, 770, 45, 70),
    "R_pupil": (1185, 770, 45, 70),
    "L_highlight": (845, 730, 36, 45),
    "R_highlight": (1195, 730, 36, 45),
    "L_upper_lash": (685, 710, 330, 115),
    "R_upper_lash": (1035, 710, 330, 115),
    "L_lower_lash": (725, 850, 250, 80),
    "R_lower_lash": (1075, 850, 250, 80),
    "L_brow": (700, 650, 300, 90),
    "R_brow": (1050, 650, 300, 90),
    "mouth_line": (955, 1010, 160, 70),
    "mouth_inner": (970, 1025, 130, 65),
    "teeth": (980, 1018, 110, 28),
    "tongue": (990, 1050, 90, 35),
    "L_ear_outer": (560, 20, 420, 500),
    "R_ear_outer": (1120, 20, 420, 500),
    "L_ear_inner": (650, 80, 240, 350),
    "R_ear_inner": (1210, 80, 240, 350),
    "L_fur_shoulder": (70, 1460, 780, 470),
    "R_fur_shoulder": (1200, 1460, 780, 470),
    "choker": (845, 1200, 360, 190),
    "gold_ornaments": (820, 1270, 420, 520),
}

ELLIPSE_ROLES = {
    "face_underpaint",
    "face_base",
    "neck",
    "L_eye_white",
    "R_eye_white",
    "L_iris",
    "R_iris",
    "L_pupil",
    "R_pupil",
    "mouth_inner",
    "teeth",
    "tongue",
}


def alpha_bbox(mask: Image.Image) -> list[int] | None:
    bbox = mask.getbbox()
    if not bbox:
        return None
    left, top, right, bottom = bbox
    return [left, top, right - left, bottom - top]


def coverage(mask: Image.Image, bbox: list[int]) -> float:
    cropped = mask.crop((bbox[0], bbox[1], bbox[0] + bbox[2], bbox[1] + bbox[3]))
    nonzero = sum(1 for value in cropped.getdata() if value)
    area = bbox[2] * bbox[3]
    return round(nonzero / area, 6) if area else 0.0


def draw_mask(part_id: str, canvas_size: tuple[int, int]) -> Image.Image:
    mask = Image.new("L", canvas_size, 0)
    draw = ImageDraw.Draw(mask)
    x, y, w, h = BOXES[part_id]
    box = (x, y, x + w, y + h)
    if part_id in ELLIPSE_ROLES:
        draw.ellipse(box, fill=255)
    elif "ear" in part_id:
        if part_id.startswith("L_"):
            points = [(x + w, y + h), (x + w // 2, y), (x, y + h)]
        else:
            points = [(x, y + h), (x + w // 2, y), (x + w, y + h)]
        draw.polygon(points, fill=255)
    else:
        draw.rounded_rectangle(box, radius=24, fill=255)
    return mask


def main() -> int:
    source = Image.open(CANONICAL).convert("RGBA")
    schema = json.loads(SCHEMA.read_text())
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    layers = []

    for index, part in enumerate(schema["production_parts"]):
        original_part_id = part["part_id"]
        review_part_id = f"concept__{original_part_id}"
        mask = draw_mask(original_part_id, source.size)
        layer = Image.new("RGBA", source.size, (0, 0, 0, 0))
        layer.paste(source, (0, 0), mask)
        out_path = OUT_DIR / f"{original_part_id}.png"
        layer.save(out_path)
        bbox = alpha_bbox(mask) or [0, 0, 0, 0]
        layers.append(
            {
                "layer_name": review_part_id,
                "original_part_id": original_part_id,
                "role": part["group"],
                "side": "L" if original_part_id.startswith("L_") else "R" if original_part_id.startswith("R_") else None,
                "source_path": str(CANONICAL),
                "output_path": str(out_path),
                "canvas_size": list(source.size),
                "bbox": bbox,
                "alpha_coverage": coverage(mask, bbox),
                "draw_order": 100 + index,
                "status": "REVISE",
                "include_in_import_psd": bool(part.get("required", True)),
                "notes": "Bootstrap rough mask candidate for visual review; not final segmentation.",
                "relative_output_path": str(out_path.relative_to(EXP)),
                "ko_name": part["ko_name"],
                "group": part["group"],
                "experiment_id": "concept-regeneration-001",
            }
        )

    manifest = {
        "experiment_id": "concept-regeneration-001",
        "date": datetime.now(timezone.utc).date().isoformat(),
        "canonical_path": str(CANONICAL),
        "layers": layers,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    REPORT.write_text(
        json.dumps(
            {
                "experiment_id": "concept-regeneration-001",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "source": str(CANONICAL),
                "output_dir": str(OUT_DIR),
                "layer_count": len(layers),
                "status": "BOOTSTRAP_REVIEW_READY",
                "notes": [
                    "These rough masks are only for testing review_app and AI fix queue flow.",
                    "Do not promote these layers to PSD without human O verdicts.",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(f"Wrote {MANIFEST.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Generated {len(layers)} bootstrap part candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

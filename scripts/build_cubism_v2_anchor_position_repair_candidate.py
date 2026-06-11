#!/usr/bin/env python3
"""Build a visual candidate that trusts saved manual anchors for small parts.

This is a diagnostic/visual repair candidate, not an automatic production pass:

- The earlier ROI-guided remask trusted ROI boxes and only used anchors as
  metadata. 주인님's feedback shows the saved anchors are often the visually
  correct locations while the ROI boxes can be vertically offset.
- For small facial parts, this script recenters extraction/translation around
  the saved anchor.
- Large body/hair/clothing parts stay on the active ROI-guided layers to avoid
  broad contamination from rectangular crops.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


ROOT = Path("/Users/family/jason/Vtube")
PACK = ROOT / "experiments/cubism-v2-new-character-001/material_pack_v0"
MANIFEST_PATH = PACK / "layer_manifest.json"
OVERRIDES_PATH = PACK / "reports/manual_semantic_overrides.json"
CANONICAL = PACK / "canonical/candidate_002_2048_rgba.png"
OUT_DIR = PACK / "production_layers_anchor_position_repair_candidate_v1"
SNAPSHOT_MANIFEST = PACK / "layer_manifest.anchor_position_repair_candidate_v1.json"
REPORT_JSON = PACK / "reports/anchor_position_repair_candidate_report.json"
REPORT_MD = PACK / "reports/anchor_position_repair_candidate_report.md"


CANVAS = (2048, 2048)
CANONICAL_REEXTRACT = {
    "brow_L",
    "brow_R",
    "cheek_L",
    "cheek_R",
    "eye_L_highlight",
    "eye_L_iris",
    "eye_L_lower_lash",
    "eye_L_pupil",
    "eye_L_upper_lash",
    "eye_L_white",
    "eye_R_highlight",
    "eye_R_iris",
    "eye_R_lower_lash",
    "eye_R_pupil",
    "eye_R_upper_lash",
    "eye_R_white",
    "mouth_line",
    "nose",
}
TRANSLATE_TO_ANCHOR = {
    "eye_L_closed_lid",
    "eye_R_closed_lid",
    "mouth_inner",
    "mouth_teeth",
    "mouth_tongue",
    "mouth_upper_lip_mask",
    "mouth_lower_lip_mask",
    "mouth_corner_L",
    "mouth_corner_R",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def resolve(path_value: str) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def bbox_from_alpha(image: Image.Image, threshold: int = 5) -> list[int]:
    arr = np.array(image.convert("RGBA"))
    ys, xs = np.where(arr[:, :, 3] > threshold)
    if len(xs) == 0:
        return [0, 0, 0, 0]
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    return [x0, y0, x1 - x0, y1 - y0]


def centered_box(anchor: list[int], size_box: list[int]) -> list[int]:
    _, _, w, h = [int(v) for v in size_box]
    ax, ay = [int(v) for v in anchor]
    x = max(0, min(CANVAS[0] - w, int(round(ax - w / 2))))
    y = max(0, min(CANVAS[1] - h, int(round(ay - h / 2))))
    return [x, y, max(2, w), max(2, h)]


def alpha_coverage(image: Image.Image) -> float:
    arr = np.array(image.convert("RGBA"))
    return round(float((arr[:, :, 3] > 5).sum() / (arr.shape[0] * arr.shape[1])), 8)


def crop_canonical(canonical: Image.Image, box: list[int]) -> Image.Image:
    x, y, w, h = box
    canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    crop = canonical.crop((x, y, x + w, y + h)).convert("RGBA")
    canvas.paste(crop, (x, y), crop)
    return canvas


def translate_layer(source: Image.Image, target_center: list[int]) -> Image.Image:
    bbox = bbox_from_alpha(source)
    if bbox[2] <= 0 or bbox[3] <= 0:
        return source.copy()
    cx = bbox[0] + bbox[2] / 2
    cy = bbox[1] + bbox[3] / 2
    dx = int(round(target_center[0] - cx))
    dy = int(round(target_center[1] - cy))
    out = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    out.alpha_composite(source.convert("RGBA"), (dx, dy))
    return out


def build() -> dict[str, Any]:
    manifest = load_json(MANIFEST_PATH)
    overrides = load_json(OVERRIDES_PATH).get("overrides", {})
    canonical = Image.open(CANONICAL).convert("RGBA")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    updated = json.loads(json.dumps(manifest))
    updated["status"] = "ANCHOR_POSITION_REPAIR_CANDIDATE_V1"
    updated["anchor_position_repair_candidate"] = {
        "schema_version": 1,
        "generated_at": now(),
        "manual_overrides": rel(OVERRIDES_PATH),
        "output_dir": rel(OUT_DIR),
        "method": "trust saved manual anchors for small face/eye/mouth parts; keep large body/hair/clothing layers from active ROI-guided manifest",
        "production_decision": "VISUAL_REVIEW_REQUIRED_NOT_PROMOTED",
    }

    rows: list[dict[str, Any]] = []
    for layer in updated["layers"]:
        if not layer.get("include_in_import_psd"):
            continue
        part_id = layer["part_id"]
        source = Image.open(resolve(layer["output_path"])).convert("RGBA")
        override = overrides.get(part_id)
        method = "KEEP_ACTIVE_ROI_GUIDED"
        target_box = None
        if override and part_id in CANONICAL_REEXTRACT:
            target_box = centered_box(override["anchor"], override["roi"])
            output = crop_canonical(canonical, target_box)
            method = "ANCHOR_CENTERED_CANONICAL_REEXTRACT"
        elif override and part_id in TRANSLATE_TO_ANCHOR:
            output = translate_layer(source, override["anchor"])
            target_box = bbox_from_alpha(output)
            method = "ANCHOR_CENTERED_TRANSLATE_EXISTING"
        else:
            output = source.copy()
            target_box = bbox_from_alpha(output)

        out_path = OUT_DIR / Path(layer["output_path"]).name
        output.save(out_path)
        layer["pre_anchor_position_repair_output_path"] = layer["output_path"]
        layer["output_path"] = rel(out_path)
        layer["anchor_position_repair_method"] = method
        layer["anchor_position_repair_target_box"] = target_box
        layer["bbox_actual"] = bbox_from_alpha(output)
        layer["alpha_coverage"] = alpha_coverage(output)
        rows.append(
            {
                "part_id": part_id,
                "method": method,
                "saved_anchor": override.get("anchor") if override else None,
                "saved_roi": override.get("roi") if override else None,
                "target_box": target_box,
                "bbox_actual": layer["bbox_actual"],
                "alpha_coverage": layer["alpha_coverage"],
            }
        )

    write_json(SNAPSHOT_MANIFEST, updated)
    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "BUILT_ANCHOR_POSITION_REPAIR_CANDIDATE_V1",
        "snapshot_manifest": rel(SNAPSHOT_MANIFEST),
        "output_dir": rel(OUT_DIR),
        "counts": {
            "canonical_reextract": sum(1 for row in rows if row["method"] == "ANCHOR_CENTERED_CANONICAL_REEXTRACT"),
            "translated_existing": sum(1 for row in rows if row["method"] == "ANCHOR_CENTERED_TRANSLATE_EXISTING"),
            "kept_active": sum(1 for row in rows if row["method"] == "KEEP_ACTIVE_ROI_GUIDED"),
            "png_layers": len(list(OUT_DIR.glob("*.png"))),
        },
        "rows": rows,
        "interpretation": [
            "This candidate is for visual diagnosis after 주인님 observed that saved positions did not match active layer placement.",
            "It trusts saved anchors for small facial parts and avoids moving large structural parts.",
            "Do not promote without human visual review and semantic/material validation.",
        ],
    }
    write_json(REPORT_JSON, report)
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Anchor Position Repair Candidate v1",
                "",
                f"- status: `{report['status']}`",
                f"- canonical reextract: `{report['counts']['canonical_reextract']}`",
                f"- translated existing: `{report['counts']['translated_existing']}`",
                f"- kept active: `{report['counts']['kept_active']}`",
                f"- png layers: `{report['counts']['png_layers']}`",
                f"- snapshot manifest: `{report['snapshot_manifest']}`",
                "",
                "This is a visual review candidate, not production approval.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report


def main() -> int:
    report = build()
    print(json.dumps({"ok": True, "status": report["status"], "counts": report["counts"], "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

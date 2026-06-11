#!/usr/bin/env python3
"""Build an anchor-position + clean-neutral candidate without rectangular crops."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from build_cubism_v2_clean_neutral_opacity_candidate import HELPER_OPACITY_KEYFRAMES


ROOT = Path("/Users/family/jason/Vtube")
PACK = ROOT / "experiments/cubism-v2-new-character-001/material_pack_v0"
MANIFEST_PATH = PACK / "layer_manifest.json"
OVERRIDES_PATH = PACK / "reports/manual_semantic_overrides.json"
OUT_DIR = PACK / "production_layers_anchor_masked_clean_candidate_v1"
SNAPSHOT_MANIFEST = PACK / "layer_manifest.anchor_masked_clean_candidate_v1.json"
REPORT_JSON = PACK / "reports/anchor_masked_clean_candidate_report.json"
REPORT_MD = PACK / "reports/anchor_masked_clean_candidate_report.md"


CANVAS = (2048, 2048)
SMALL_ANCHOR_PARTS = {
    "brow_L",
    "brow_R",
    "cheek_L",
    "cheek_R",
    "eye_L_closed_lid",
    "eye_R_closed_lid",
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
    "mouth_corner_L",
    "mouth_corner_R",
    "mouth_inner",
    "mouth_line",
    "mouth_lower_lip_mask",
    "mouth_teeth",
    "mouth_tongue",
    "mouth_upper_lip_mask",
    "nose",
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


def alpha_coverage(image: Image.Image) -> float:
    arr = np.array(image.convert("RGBA"))
    return round(float((arr[:, :, 3] > 5).sum() / (arr.shape[0] * arr.shape[1])), 8)


def translate_layer_to_anchor(source: Image.Image, anchor: list[int]) -> Image.Image:
    bbox = bbox_from_alpha(source)
    if bbox[2] <= 0 or bbox[3] <= 0:
        return source.copy()
    cx = bbox[0] + bbox[2] / 2
    cy = bbox[1] + bbox[3] / 2
    dx = int(round(anchor[0] - cx))
    dy = int(round(anchor[1] - cy))
    out = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    out.alpha_composite(source.convert("RGBA"), (dx, dy))
    return out


def merge_helper_opacity_keyframes(doc: dict[str, Any]) -> list[dict[str, Any]]:
    rows = list(doc.get("part_opacity_keyframes") or [])
    seen = {(row.get("part_id"), row.get("parameter_id")) for row in rows}
    for part_id, (parameter_id, pairs) in HELPER_OPACITY_KEYFRAMES.items():
        key = (part_id, parameter_id)
        if key in seen:
            continue
        rows.append(
            {
                "part_id": part_id,
                "parameter_id": parameter_id,
                "mode": "linear",
                "keyframes": [{"value": value, "opacity": opacity} for value, opacity in pairs],
                "purpose": "hide helper/underpaint patches at neutral; reveal only during angle/gaze preview",
            }
        )
    return rows


def build() -> dict[str, Any]:
    manifest = load_json(MANIFEST_PATH)
    overrides = load_json(OVERRIDES_PATH).get("overrides", {})
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    updated = json.loads(json.dumps(manifest))
    updated["status"] = "ANCHOR_MASKED_CLEAN_CANDIDATE_V1"
    updated["part_opacity_keyframes"] = merge_helper_opacity_keyframes(updated)
    updated["anchor_masked_clean_candidate"] = {
        "schema_version": 1,
        "generated_at": now(),
        "manual_overrides": rel(OVERRIDES_PATH),
        "output_dir": rel(OUT_DIR),
        "method": "translate existing alpha-shaped small facial layers to saved anchors and add clean-neutral helper opacity; no canonical rectangular crop",
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
        if override and part_id in SMALL_ANCHOR_PARTS:
            output = translate_layer_to_anchor(source, override["anchor"])
            method = "ANCHOR_TRANSLATE_ALPHA_SHAPE"
        else:
            output = source.copy()
        out_path = OUT_DIR / Path(layer["output_path"]).name
        output.save(out_path)
        layer["pre_anchor_masked_clean_output_path"] = layer["output_path"]
        layer["output_path"] = rel(out_path)
        layer["anchor_masked_clean_method"] = method
        layer["bbox_actual"] = bbox_from_alpha(output)
        layer["alpha_coverage"] = alpha_coverage(output)
        rows.append(
            {
                "part_id": part_id,
                "method": method,
                "saved_anchor": override.get("anchor") if override else None,
                "bbox_actual": layer["bbox_actual"],
                "alpha_coverage": layer["alpha_coverage"],
            }
        )

    write_json(SNAPSHOT_MANIFEST, updated)
    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "BUILT_ANCHOR_MASKED_CLEAN_CANDIDATE_V1",
        "snapshot_manifest": rel(SNAPSHOT_MANIFEST),
        "output_dir": rel(OUT_DIR),
        "counts": {
            "anchor_translated_alpha_shape": sum(1 for row in rows if row["method"] == "ANCHOR_TRANSLATE_ALPHA_SHAPE"),
            "kept_active": sum(1 for row in rows if row["method"] == "KEEP_ACTIVE_ROI_GUIDED"),
            "part_opacity_keyframes": len(updated.get("part_opacity_keyframes", [])),
            "png_layers": len(list(OUT_DIR.glob("*.png"))),
        },
        "rows": rows,
        "interpretation": [
            "This candidate removes rectangular canonical reextract patches.",
            "Small face/eye/mouth parts are moved by saved anchor while preserving the original alpha shape.",
            "Clean-neutral opacity hides helper underpaint/face shadow at neutral.",
        ],
    }
    write_json(REPORT_JSON, report)
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Anchor Masked + Clean-Neutral Candidate v1",
                "",
                f"- status: `{report['status']}`",
                f"- anchor translated alpha-shape parts: `{report['counts']['anchor_translated_alpha_shape']}`",
                f"- kept active: `{report['counts']['kept_active']}`",
                f"- part opacity keyframes: `{report['counts']['part_opacity_keyframes']}`",
                f"- png layers: `{report['counts']['png_layers']}`",
                f"- snapshot manifest: `{report['snapshot_manifest']}`",
                "",
                "This is the candidate to check after `8067` still showed face blotches.",
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

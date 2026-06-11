#!/usr/bin/env python3
"""Combine 8065 position success with 8066 clean-neutral opacity safely.

This differs from the failed 8068 candidate:
- It does not move every eye/mouth subpart independently to its saved anchor.
- It computes group-level deltas from the 8065 anchor-position candidate and
  applies those deltas to the 8066 clean-neutral layers.
- It keeps 8066 opacity keyframes, so helper/underpaint patches stay hidden at
  neutral.
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


ROOT = Path("/Users/family/jason/Vtube")
PACK = ROOT / "experiments/cubism-v2-new-character-001/material_pack_v0"
CLEAN_MANIFEST = PACK / "layer_manifest.clean_neutral_opacity_candidate_v1.json"
ANCHOR_MANIFEST = PACK / "layer_manifest.anchor_position_repair_candidate_v1.json"
OUT_DIR = PACK / "production_layers_group_position_clean_candidate_v1"
SNAPSHOT_MANIFEST = PACK / "layer_manifest.group_position_clean_candidate_v1.json"
REPORT_JSON = PACK / "reports/group_position_clean_candidate_report.json"
REPORT_MD = PACK / "reports/group_position_clean_candidate_report.md"


CANVAS = (2048, 2048)
GROUPS = {
    "eye_L": {
        "eye_L_white",
        "eye_L_iris",
        "eye_L_pupil",
        "eye_L_highlight",
        "eye_L_upper_lash",
        "eye_L_lower_lash",
        "eye_L_closed_lid",
    },
    "eye_R": {
        "eye_R_white",
        "eye_R_iris",
        "eye_R_pupil",
        "eye_R_highlight",
        "eye_R_upper_lash",
        "eye_R_lower_lash",
        "eye_R_closed_lid",
    },
    "mouth": {
        "mouth_line",
        "mouth_inner",
        "mouth_teeth",
        "mouth_tongue",
        "mouth_upper_lip_mask",
        "mouth_lower_lip_mask",
        "mouth_corner_L",
        "mouth_corner_R",
    },
}
INDIVIDUAL_POSITION_PARTS = {
    "brow_L",
    "brow_R",
    "nose",
    "cheek_L",
    "cheek_R",
}
NEVER_MOVE = {
    "eye_L_underpaint",
    "eye_R_underpaint",
    "face_underpaint_L",
    "face_underpaint_R",
    "face_shadow_L",
    "face_shadow_R",
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


def center(box: list[int]) -> tuple[float, float]:
    return (box[0] + box[2] / 2, box[1] + box[3] / 2)


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


def translate_layer(source: Image.Image, dx: float, dy: float) -> Image.Image:
    out = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    out.alpha_composite(source.convert("RGBA"), (int(round(dx)), int(round(dy))))
    return out


def part_maps(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["part_id"]: row for row in doc.get("layers", []) if row.get("include_in_import_psd")}


def compute_group_deltas(clean_by_part: dict[str, dict[str, Any]], anchor_by_part: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    deltas: dict[str, dict[str, Any]] = {}
    for group_name, parts in GROUPS.items():
        dxs: list[float] = []
        dys: list[float] = []
        rows: list[dict[str, Any]] = []
        for part_id in sorted(parts):
            if part_id not in clean_by_part or part_id not in anchor_by_part:
                continue
            clean_box = clean_by_part[part_id].get("bbox_actual") or clean_by_part[part_id].get("bbox")
            anchor_box = anchor_by_part[part_id].get("bbox_actual") or anchor_by_part[part_id].get("bbox")
            if not clean_box or not anchor_box or clean_box[2] <= 0 or anchor_box[2] <= 0:
                continue
            cc = center(clean_box)
            ac = center(anchor_box)
            dx = ac[0] - cc[0]
            dy = ac[1] - cc[1]
            dxs.append(dx)
            dys.append(dy)
            rows.append({"part_id": part_id, "dx": round(dx, 2), "dy": round(dy, 2), "clean_bbox": clean_box, "anchor_bbox": anchor_box})
        deltas[group_name] = {
            "dx": round(statistics.median(dxs), 2) if dxs else 0,
            "dy": round(statistics.median(dys), 2) if dys else 0,
            "source_rows": rows,
        }
    return deltas


def find_group(part_id: str) -> str | None:
    for group, parts in GROUPS.items():
        if part_id in parts:
            return group
    return None


def build() -> dict[str, Any]:
    clean = load_json(CLEAN_MANIFEST)
    anchor = load_json(ANCHOR_MANIFEST)
    clean_by_part = part_maps(clean)
    anchor_by_part = part_maps(anchor)
    group_deltas = compute_group_deltas(clean_by_part, anchor_by_part)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    updated = json.loads(json.dumps(clean))
    updated["status"] = "GROUP_POSITION_CLEAN_CANDIDATE_V1"
    updated["group_position_clean_candidate"] = {
        "schema_version": 1,
        "generated_at": now(),
        "clean_source_manifest": rel(CLEAN_MANIFEST),
        "anchor_position_source_manifest": rel(ANCHOR_MANIFEST),
        "output_dir": rel(OUT_DIR),
        "method": "apply 8065 group-level position deltas to 8066 clean-neutral layers",
        "production_decision": "VISUAL_REVIEW_REQUIRED_NOT_PROMOTED",
    }

    rows: list[dict[str, Any]] = []
    for layer in updated["layers"]:
        if not layer.get("include_in_import_psd"):
            continue
        part_id = layer["part_id"]
        source = Image.open(resolve(layer["output_path"])).convert("RGBA")
        method = "KEEP_8066_CLEAN"
        dx = dy = 0.0
        group = find_group(part_id)
        if part_id in NEVER_MOVE:
            method = "KEEP_HELPER_NEUTRAL_HIDDEN"
        elif group:
            dx = group_deltas[group]["dx"]
            dy = group_deltas[group]["dy"]
            method = f"GROUP_DELTA_{group}"
        elif part_id in INDIVIDUAL_POSITION_PARTS and part_id in anchor_by_part:
            clean_box = layer.get("bbox_actual") or layer.get("bbox")
            anchor_box = anchor_by_part[part_id].get("bbox_actual") or anchor_by_part[part_id].get("bbox")
            if clean_box and anchor_box:
                cc = center(clean_box)
                ac = center(anchor_box)
                dx = ac[0] - cc[0]
                dy = ac[1] - cc[1]
                method = "INDIVIDUAL_8065_DELTA"
        output = translate_layer(source, dx, dy) if dx or dy else source.copy()
        out_path = OUT_DIR / Path(layer["output_path"]).name
        output.save(out_path)
        layer["pre_group_position_clean_output_path"] = layer["output_path"]
        layer["output_path"] = rel(out_path)
        layer["group_position_clean_method"] = method
        layer["group_position_clean_delta"] = [round(dx, 2), round(dy, 2)]
        layer["bbox_actual"] = bbox_from_alpha(output)
        layer["alpha_coverage"] = alpha_coverage(output)
        rows.append(
            {
                "part_id": part_id,
                "method": method,
                "delta": [round(dx, 2), round(dy, 2)],
                "bbox_actual": layer["bbox_actual"],
                "alpha_coverage": layer["alpha_coverage"],
            }
        )

    write_json(SNAPSHOT_MANIFEST, updated)
    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "BUILT_GROUP_POSITION_CLEAN_CANDIDATE_V1",
        "snapshot_manifest": rel(SNAPSHOT_MANIFEST),
        "output_dir": rel(OUT_DIR),
        "group_deltas": group_deltas,
        "counts": {
            "group_delta_layers": sum(1 for row in rows if row["method"].startswith("GROUP_DELTA_")),
            "individual_delta_layers": sum(1 for row in rows if row["method"] == "INDIVIDUAL_8065_DELTA"),
            "helper_kept": sum(1 for row in rows if row["method"] == "KEEP_HELPER_NEUTRAL_HIDDEN"),
            "kept_clean": sum(1 for row in rows if row["method"] == "KEEP_8066_CLEAN"),
            "part_opacity_keyframes": len(updated.get("part_opacity_keyframes", [])),
            "png_layers": len(list(OUT_DIR.glob("*.png"))),
        },
        "rows": rows,
        "interpretation": [
            "This is the direct interpretation of 주인님's request: combine 8065 position success with 8066 clean-neutral success.",
            "It uses group-level deltas to avoid the 8068 individual-part face breakage.",
            "It keeps helper layers neutral-hidden to avoid 8064/8067 blotches.",
        ],
    }
    write_json(REPORT_JSON, report)
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Group Position + Clean-Neutral Candidate v1",
                "",
                f"- status: `{report['status']}`",
                f"- group delta layers: `{report['counts']['group_delta_layers']}`",
                f"- individual delta layers: `{report['counts']['individual_delta_layers']}`",
                f"- helper kept neutral-hidden: `{report['counts']['helper_kept']}`",
                f"- part opacity keyframes: `{report['counts']['part_opacity_keyframes']}`",
                f"- png layers: `{report['counts']['png_layers']}`",
                f"- snapshot manifest: `{report['snapshot_manifest']}`",
                "",
                "## Group Deltas",
                "",
                *[f"- `{group}`: dx `{row['dx']}`, dy `{row['dy']}`" for group, row in group_deltas.items()],
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report


def main() -> int:
    report = build()
    print(json.dumps({"ok": True, "status": report["status"], "counts": report["counts"], "group_deltas": report["group_deltas"], "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

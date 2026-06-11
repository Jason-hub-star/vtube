#!/usr/bin/env python3
"""Build Character 002 v13 preview by slightly reducing v12 eye and mouth scale."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
DEFAULT_SOURCE = EXP / "model_edit_v12_generated_mouth_eye_clamp_preview/mini_cubism_diagnostic_project"
DEFAULT_OUT = EXP / "model_edit_v13_scaled_eye_mouth_preview/mini_cubism_diagnostic_project"
DEFAULT_REPORTS = EXP / "reports/model_edit_v13_scaled_eye_mouth_preview"
CANVAS_SIZE = [2048, 2048]

LEFT_EYE_ANCHOR = (880, 687)
RIGHT_EYE_ANCHOR = (1170, 687)
MOUTH_ANCHOR = (1035, 892)

EYE_PARTS = {
    "eye_L_clean_socket",
    "eye_R_clean_socket",
    "eye_L_closed_underpaint",
    "eye_R_closed_underpaint",
    "eye_L_open",
    "eye_R_open",
    "eye_L_half_closed_lid",
    "eye_R_half_closed_lid",
    "eye_L_mostly_closed_lid",
    "eye_R_mostly_closed_lid",
    "eye_L_closed_lid",
    "eye_R_closed_lid",
}
MOUTH_PARTS = {
    "mouth_closed_smile",
    "mouth_small_open",
    "mouth_mid_teeth_gen",
    "mouth_wide_teeth_tongue_gen",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def part_anchor(part_id: str) -> tuple[int, int]:
    if part_id.startswith("eye_L_"):
        return LEFT_EYE_ANCHOR
    if part_id.startswith("eye_R_"):
        return RIGHT_EYE_ANCHOR
    if part_id.startswith("mouth_"):
        return MOUTH_ANCHOR
    raise ValueError(f"no anchor for {part_id}")


def scale_full_canvas_layer(path: Path, scale: float, anchor: tuple[int, int]) -> dict[str, Any]:
    image = Image.open(path).convert("RGBA")
    if list(image.size) != CANVAS_SIZE:
        raise ValueError(f"expected {CANVAS_SIZE}, got {image.size}: {path}")
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError(f"empty alpha: {path}")
    crop = image.crop(bbox)
    scaled_size = (
        max(1, int(round(crop.width * scale))),
        max(1, int(round(crop.height * scale))),
    )
    resized = crop.resize(scaled_size, Image.Resampling.LANCZOS)
    old_center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
    dx = old_center[0] - anchor[0]
    dy = old_center[1] - anchor[1]
    new_center = (anchor[0] + dx * scale, anchor[1] + dy * scale)
    paste_xy = (
        int(round(new_center[0] - resized.width / 2)),
        int(round(new_center[1] - resized.height / 2)),
    )
    out = Image.new("RGBA", tuple(CANVAS_SIZE), (0, 0, 0, 0))
    out.alpha_composite(resized, paste_xy)
    out.save(path)
    alpha = out.getchannel("A")
    new_bbox = alpha.getbbox()
    if new_bbox is None:
        raise ValueError(f"scaled layer became empty: {path}")
    hist = alpha.histogram()
    nonzero = int(sum(hist[1:]))
    return {
        "bbox_xywh": [new_bbox[0], new_bbox[1], new_bbox[2] - new_bbox[0], new_bbox[3] - new_bbox[1]],
        "alpha_nonzero": nonzero,
        "alpha_coverage": round(nonzero / (CANVAS_SIZE[0] * CANVAS_SIZE[1]), 8),
        "old_bbox": list(bbox),
        "new_bbox": list(new_bbox),
        "scale": scale,
        "anchor": list(anchor),
    }


def mesh_for_part(part_id: str, bbox: list[int], canvas_size: list[int]) -> dict[str, Any]:
    x, y, width, height = bbox
    cols = 4
    rows = 3
    vertices: list[list[float]] = []
    uvs: list[list[float]] = []
    triangles: list[list[int]] = []
    for row in range(rows + 1):
        for col in range(cols + 1):
            vx = x + width * col / cols
            vy = y + height * row / rows
            vertices.append([round(vx, 3), round(vy, 3)])
            uvs.append([round(vx / canvas_size[0], 6), round(vy / canvas_size[1], 6)])
    for row in range(rows):
        for col in range(cols):
            a = row * (cols + 1) + col
            b = a + 1
            c = a + cols + 1
            d = c + 1
            triangles.append([a, c, b])
            triangles.append([b, c, d])
    return {"part_id": part_id, "vertices": vertices, "triangles": triangles, "uvs": uvs, "mesh_path": f"meshes/{part_id}.json"}


def update_character_for_scaled_part(character: dict[str, Any], project: Path, part_id: str, metrics: dict[str, Any]) -> None:
    for part in character.get("parts", []):
        if part.get("id") == part_id:
            part["bbox"] = metrics["bbox_xywh"]
            part["alpha_coverage"] = metrics["alpha_coverage"]
            tags = set(part.get("risk_tags", []))
            tags.add("v13_scaled_eye_mouth")
            part["risk_tags"] = sorted(tags)
            break
    mesh = mesh_for_part(part_id, metrics["bbox_xywh"], CANVAS_SIZE)
    (project / "meshes" / f"{part_id}.json").write_text(json.dumps(mesh, ensure_ascii=False, indent=2) + "\n")
    character["meshes"] = [row for row in character.get("meshes", []) if row.get("part_id") != part_id] + [mesh]


def sort_project(character: dict[str, Any]) -> None:
    character["parts"] = sorted(character["parts"], key=lambda row: (row.get("draw_order", 0), row.get("id", "")))
    order = {part["id"]: index for index, part in enumerate(character["parts"])}
    character["meshes"] = sorted(character["meshes"], key=lambda row: order.get(row.get("part_id"), 9999))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-project", default=str(DEFAULT_SOURCE))
    parser.add_argument("--out-project", default=str(DEFAULT_OUT))
    parser.add_argument("--reports", default=str(DEFAULT_REPORTS))
    parser.add_argument("--eye-scale", type=float, default=0.94)
    parser.add_argument("--mouth-scale", type=float, default=0.92)
    args = parser.parse_args()

    source_project = Path(args.source_project).resolve()
    out_project = Path(args.out_project).resolve()
    reports = Path(args.reports).resolve()
    if out_project.exists():
        shutil.rmtree(out_project)
    shutil.copytree(source_project, out_project)
    reports.mkdir(parents=True, exist_ok=True)

    character_path = out_project / "character.json"
    character = json.loads(character_path.read_text())
    scaled: dict[str, Any] = {}
    for part_id in sorted(EYE_PARTS | MOUTH_PARTS):
        scale = args.eye_scale if part_id in EYE_PARTS else args.mouth_scale
        path = out_project / "parts" / f"{part_id}.png"
        if not path.exists():
            continue
        metrics = scale_full_canvas_layer(path, scale, part_anchor(part_id))
        update_character_for_scaled_part(character, out_project, part_id, metrics)
        scaled[part_id] = metrics

    character["experiment_id"] = "cubism-v2-new-character-002/model_edit_v13_scaled_eye_mouth_preview"
    character["generated_at"] = now()
    character["notes"] = character.get("notes", []) + [
        f"v13 scales eye parts by {args.eye_scale:.3f} and active generated mouth parts by {args.mouth_scale:.3f} from v12.",
        "v13 preserves EyeOpen min 0.27 and MouthOpenY max 0.85 from v12.",
    ]
    sort_project(character)
    character_path.write_text(json.dumps(character, ensure_ascii=False, indent=2) + "\n")

    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "V13_SCALED_EYE_MOUTH_READY_FOR_VALIDATION",
        "source_project": rel(source_project),
        "project": rel(out_project),
        "eye_scale": args.eye_scale,
        "mouth_scale": args.mouth_scale,
        "scaled_parts": scaled,
    }
    report_path = reports / "mini_cubism_v13_scaled_eye_mouth_report.json"
    write_json(report_path, report)
    print(json.dumps({"ok": True, "report": str(report_path), "project": str(out_project)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

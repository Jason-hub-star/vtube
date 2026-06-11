#!/usr/bin/env python3
"""Build Character 002 v15 by fixing v14 eyeball cohesion, eye position, and nose visibility."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
DEFAULT_SOURCE = EXP / "model_edit_v14_eye_detail_inbetween_preview/mini_cubism_diagnostic_project"
DEFAULT_OUT = EXP / "model_edit_v15_eye_nose_position_preview/mini_cubism_diagnostic_project"
DEFAULT_REPORTS = EXP / "reports/model_edit_v15_eye_nose_position_preview"
DEFAULT_SOURCE_FRONT = EXP / "reports/overlay_qa/source_front_2048.png"
CANVAS_SIZE = [2048, 2048]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def bbox_metrics(image: Image.Image) -> tuple[list[int], int, float]:
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError("empty alpha")
    nonzero = int(sum(alpha.histogram()[1:]))
    return [bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]], nonzero, round(nonzero / (CANVAS_SIZE[0] * CANVAS_SIZE[1]), 8)


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


def save_part_and_mesh(character: dict[str, Any], project: Path, part: dict[str, Any], image: Image.Image) -> dict[str, Any]:
    bbox, nonzero, coverage = bbox_metrics(image)
    part_id = part["id"]
    image.save(project / "parts" / f"{part_id}.png")
    part["bbox"] = bbox
    part["alpha_coverage"] = coverage
    mesh = mesh_for_part(part_id, bbox, CANVAS_SIZE)
    (project / "meshes" / f"{part_id}.json").write_text(json.dumps(mesh, ensure_ascii=False, indent=2) + "\n")
    character["meshes"] = [row for row in character.get("meshes", []) if row.get("part_id") != part_id] + [mesh]
    return {"bbox_xywh": bbox, "alpha_nonzero": nonzero, "alpha_coverage": coverage}


def shift_layer(image: Image.Image, dx: int, dy: int) -> Image.Image:
    out = Image.new("RGBA", tuple(CANVAS_SIZE), (0, 0, 0, 0))
    out.alpha_composite(image, (dx, dy))
    return out


def shift_eye_parts(character: dict[str, Any], project: Path, dy: int) -> dict[str, Any]:
    shifted: dict[str, Any] = {}
    for part in character.get("parts", []):
        if not part["id"].startswith(("eye_L_", "eye_R_")):
            continue
        path = project / part["source_path"]
        image = Image.open(path).convert("RGBA")
        shifted_image = shift_layer(image, 0, dy)
        tags = set(part.get("risk_tags", []))
        tags.add("v15_eye_position_shift")
        part["risk_tags"] = sorted(tags)
        shifted[part["id"]] = save_part_and_mesh(character, project, part, shifted_image)
    for deformer in character.get("deformers", []):
        if deformer.get("id") not in {"eye_L_warp", "eye_R_warp"}:
            continue
        bounds = deformer.get("bounds")
        if isinstance(bounds, list) and len(bounds) == 4:
            deformer["bounds"] = [bounds[0], bounds[1] + dy, bounds[2], bounds[3] + dy]
        pivot = deformer.get("pivot")
        if isinstance(pivot, list) and len(pivot) == 2:
            deformer["pivot"] = [pivot[0], pivot[1] + dy]
    return shifted


def make_nose_detail(source_front: Path, face_base: Path) -> Image.Image:
    source = Image.open(source_front).convert("RGBA")
    base = Image.open(face_base).convert("RGBA")
    if source.size != tuple(CANVAS_SIZE):
        source = source.resize(tuple(CANVAS_SIZE), Image.Resampling.LANCZOS)
    if base.size != tuple(CANVAS_SIZE):
        base = base.resize(tuple(CANVAS_SIZE), Image.Resampling.LANCZOS)

    roi = (990, 690, 1072, 820)
    source_crop = source.crop(roi)
    base_crop = base.crop(roi)
    diff = ImageChops.difference(source_crop.convert("RGB"), base_crop.convert("RGB"))
    diff_l = diff.convert("L")

    ellipse = Image.new("L", source_crop.size, 0)
    draw = ImageDraw.Draw(ellipse)
    draw.ellipse((12, 4, source_crop.width - 8, source_crop.height - 3), fill=255)
    ellipse = ellipse.filter(ImageFilter.GaussianBlur(4.0))

    alpha = Image.new("L", source_crop.size, 0)
    diff_px = diff_l.load()
    mask_px = ellipse.load()
    alpha_px = alpha.load()
    for y in range(source_crop.height):
        for x in range(source_crop.width):
            strength = max(0, diff_px[x, y] - 5)
            # Keep only the nose line/highlight difference, not a skin-colored patch.
            alpha_px[x, y] = min(180, int(strength * 5.2 * (mask_px[x, y] / 255)))
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.7))

    detail = source_crop.copy()
    detail.putalpha(alpha)
    out = Image.new("RGBA", tuple(CANVAS_SIZE), (0, 0, 0, 0))
    out.alpha_composite(detail, roi[:2])
    return out


def add_nose_part(character: dict[str, Any], project: Path, source_front: Path) -> dict[str, Any]:
    template = next(part for part in character["parts"] if part["id"] == "face_base_clean")
    nose = make_nose_detail(source_front, project / "parts/face_base_clean.png")
    bbox, nonzero, coverage = bbox_metrics(nose)
    part_id = "nose_detail"
    nose.save(project / "parts/nose_detail.png")
    mesh = mesh_for_part(part_id, bbox, CANVAS_SIZE)
    (project / "meshes/nose_detail.json").write_text(json.dumps(mesh, ensure_ascii=False, indent=2) + "\n")
    part = {
        "id": part_id,
        "display_name": part_id,
        "source_path": "parts/nose_detail.png",
        "original_source_path": str(source_front),
        "bbox": bbox,
        "alpha_coverage": coverage,
        "draw_order": 255,
        "folder": "Face",
        "deformer_node": "head_angle_warp",
        "material_group": "face",
        "risk_tags": sorted(set(template.get("risk_tags", []) + ["v15_nose_detail_delta_from_source", "diagnostic_face_feature_restore"])),
    }
    character["parts"] = [row for row in character.get("parts", []) if row.get("id") != part_id] + [part]
    character["meshes"] = [row for row in character.get("meshes", []) if row.get("part_id") != part_id] + [mesh]
    for deformer in character.get("deformers", []):
        if deformer.get("id") == "head_angle_warp":
            deformer["child_ids"] = list(dict.fromkeys(deformer.get("child_ids", []) + [part_id]))
            break
    return {"bbox_xywh": bbox, "alpha_nonzero": nonzero, "alpha_coverage": coverage}


def update_eye_ball_bindings(character: dict[str, Any], strength_x: float, strength_y: float) -> None:
    detail_ids = {
        "eye_L_iris",
        "eye_L_pupil",
        "eye_L_highlight",
        "eye_R_iris",
        "eye_R_pupil",
        "eye_R_highlight",
    }
    character["keyform_bindings"] = [
        row
        for row in character.get("keyform_bindings", [])
        if not (row.get("parameter_id") in {"ParamEyeBallX", "ParamEyeBallY"} and row.get("target_id") in detail_ids)
    ]
    for part_id in sorted(detail_ids):
        character["keyform_bindings"].extend(
            [
                binding("ParamEyeBallX", part_id, -1, [-strength_x, 0]),
                binding("ParamEyeBallX", part_id, 1, [strength_x, 0]),
                binding("ParamEyeBallY", part_id, -1, [0, -strength_y]),
                binding("ParamEyeBallY", part_id, 1, [0, strength_y]),
            ]
        )


def binding(parameter_id: str, target_id: str, key_value: float, translate: list[float]) -> dict[str, Any]:
    return {
        "parameter_id": parameter_id,
        "key_value": key_value,
        "target_id": target_id,
        "delta_type": "deformer_transform",
        "deltas": {"translate": translate, "scale": [1, 1], "rotate": 0, "opacity": 1},
    }


def sort_project(character: dict[str, Any]) -> None:
    character["parts"] = sorted(character["parts"], key=lambda row: (row.get("draw_order", 0), row.get("id", "")))
    order = {part["id"]: index for index, part in enumerate(character["parts"])}
    character["meshes"] = sorted(character["meshes"], key=lambda row: order.get(row.get("part_id"), 9999))
    character["keyform_bindings"] = sorted(
        character["keyform_bindings"],
        key=lambda row: (row.get("parameter_id", ""), row.get("target_id", ""), float(row.get("key_value", 0))),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-project", default=str(DEFAULT_SOURCE))
    parser.add_argument("--out-project", default=str(DEFAULT_OUT))
    parser.add_argument("--reports", default=str(DEFAULT_REPORTS))
    parser.add_argument("--source-front", default=str(DEFAULT_SOURCE_FRONT))
    parser.add_argument("--eye-shift-y", type=int, default=-18)
    parser.add_argument("--eye-ball-x", type=float, default=7.5)
    parser.add_argument("--eye-ball-y", type=float, default=4.5)
    args = parser.parse_args()

    source_project = Path(args.source_project).resolve()
    out_project = Path(args.out_project).resolve()
    reports = Path(args.reports).resolve()
    source_front = Path(args.source_front).resolve()
    if out_project.exists():
        shutil.rmtree(out_project)
    shutil.copytree(source_project, out_project)
    reports.mkdir(parents=True, exist_ok=True)

    character_path = out_project / "character.json"
    character = json.loads(character_path.read_text())

    shifted = shift_eye_parts(character, out_project, args.eye_shift_y)
    nose_metrics = add_nose_part(character, out_project, source_front)
    update_eye_ball_bindings(character, args.eye_ball_x, args.eye_ball_y)

    character["experiment_id"] = "cubism-v2-new-character-002/model_edit_v15_eye_nose_position_preview"
    character["generated_at"] = now()
    character["notes"] = character.get("notes", []) + [
        "v15 preserves v14 eye-detail/in-between structure and v13 mouth pattern.",
        f"v15 shifts all eye parts by {args.eye_shift_y}px on Y after visual review.",
        f"v15 makes iris, pupil, and highlight share identical EyeBall movement: X {args.eye_ball_x}px, Y {args.eye_ball_y}px.",
        "v15 adds a diagnostic nose_detail layer from source/front vs face_base_clean delta only; this restores feature visibility without a rectangular skin patch.",
    ]
    sort_project(character)
    character_path.write_text(json.dumps(character, ensure_ascii=False, indent=2) + "\n")

    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "V15_EYE_NOSE_POSITION_READY_FOR_VALIDATION",
        "source_project": rel(source_project),
        "project": rel(out_project),
        "source_front": rel(source_front),
        "eye_shift_y": args.eye_shift_y,
        "eye_ball_binding_strength": {"x": args.eye_ball_x, "y": args.eye_ball_y, "same_for_iris_pupil_highlight": True},
        "nose_detail": nose_metrics,
        "shifted_eye_parts": shifted,
        "policy": {
            "preserve_v13_mouth_pattern": True,
            "eye_open_min": 0.27,
            "mouth_open_y_max": 0.85,
            "production_claim": "diagnostic only; nose and eye details require human visual QA before promotion",
        },
    }
    report_path = reports / "mini_cubism_v15_eye_nose_position_report.json"
    write_json(report_path, report)
    print(json.dumps({"ok": True, "report": str(report_path), "project": str(out_project)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

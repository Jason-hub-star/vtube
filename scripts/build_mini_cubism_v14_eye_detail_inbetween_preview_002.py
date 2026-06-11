#!/usr/bin/env python3
"""Build Character 002 v14 eye-detail/in-between diagnostic preview from v13."""

from __future__ import annotations

import argparse
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
DEFAULT_SOURCE = EXP / "model_edit_v13_scaled_eye_mouth_preview/mini_cubism_diagnostic_project"
DEFAULT_OUT = EXP / "model_edit_v14_eye_detail_inbetween_preview/mini_cubism_diagnostic_project"
DEFAULT_REPORTS = EXP / "reports/model_edit_v14_eye_detail_inbetween_preview"
CANVAS_SIZE = [2048, 2048]

EYE_DETAIL_IDS = [
    "eye_{side}_white",
    "eye_{side}_iris",
    "eye_{side}_pupil",
    "eye_{side}_highlight",
    "eye_{side}_lid_inbetween_080",
    "eye_{side}_lid_inbetween_065",
    "eye_{side}_lid_inbetween_038",
]


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


def upsert_parameter(character: dict[str, Any], parameter: dict[str, Any]) -> None:
    rows = [row for row in character.get("parameters", []) if row.get("id") != parameter["id"]]
    rows.append(parameter)
    character["parameters"] = rows


def add_or_replace_part(
    character: dict[str, Any],
    project: Path,
    part_id: str,
    image: Image.Image,
    template: dict[str, Any],
    draw_order: int,
    source_note: str,
    risk_tags: list[str],
) -> dict[str, Any]:
    if list(image.size) != CANVAS_SIZE:
        raise ValueError(f"{part_id} size must be {CANVAS_SIZE}, got {image.size}")
    bbox, nonzero, coverage = bbox_metrics(image)
    part_path = project / "parts" / f"{part_id}.png"
    image.save(part_path)
    mesh = mesh_for_part(part_id, bbox, CANVAS_SIZE)
    (project / "meshes" / f"{part_id}.json").write_text(json.dumps(mesh, ensure_ascii=False, indent=2) + "\n")
    part = {
        "id": part_id,
        "display_name": part_id,
        "source_path": f"parts/{part_id}.png",
        "original_source_path": source_note,
        "bbox": bbox,
        "alpha_coverage": coverage,
        "draw_order": draw_order,
        "folder": template.get("folder", "Eyes"),
        "deformer_node": template.get("deformer_node"),
        "material_group": template.get("material_group"),
        "risk_tags": sorted(set(template.get("risk_tags", []) + risk_tags)),
    }
    character["parts"] = [row for row in character.get("parts", []) if row.get("id") != part_id] + [part]
    character["meshes"] = [row for row in character.get("meshes", []) if row.get("part_id") != part_id] + [mesh]
    return {"bbox_xywh": bbox, "alpha_nonzero": nonzero, "alpha_coverage": coverage}


def ellipse_mask(size: tuple[int, int], box: tuple[float, float, float, float], blur: float = 1.5) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(tuple(int(round(v)) for v in box), fill=255)
    if blur:
        mask = mask.filter(ImageFilter.GaussianBlur(blur))
    return mask


def apply_alpha_mask(image: Image.Image, mask: Image.Image) -> Image.Image:
    rgba = image.copy().convert("RGBA")
    rgba.putalpha(ImageChops.multiply(rgba.getchannel("A"), mask))
    return rgba


def dark_pixel_mask(image: Image.Image, iris_mask: Image.Image) -> Image.Image:
    mask = Image.new("L", image.size, 0)
    pix = image.load()
    iris = iris_mask.load()
    out = mask.load()
    for y in range(image.height):
        for x in range(image.width):
            if iris[x, y] < 24:
                continue
            r, g, b, a = pix[x, y]
            value = max(r, g, b)
            if a > 30 and value < 80:
                out[x, y] = min(255, int(a * 1.25))
    return mask.filter(ImageFilter.GaussianBlur(0.6))


def make_eye_detail_layers(open_eye: Image.Image, side: str) -> dict[str, Image.Image]:
    alpha_bbox = open_eye.getchannel("A").getbbox()
    if alpha_bbox is None:
        raise ValueError(f"eye_{side}_open is empty")
    x0, y0, x1, y1 = alpha_bbox
    width = x1 - x0
    height = y1 - y0
    # The source eye is baked; use a soft centered region that preserves the current iris color
    # without importing a mismatched newly generated eye.
    center_x = x0 + (0.52 if side == "L" else 0.48) * width
    center_y = y0 + 0.46 * height
    iris_rx = width * 0.20
    iris_ry = height * 0.30
    iris_box = (center_x - iris_rx, center_y - iris_ry, center_x + iris_rx, center_y + iris_ry)
    iris_mask = ellipse_mask(tuple(CANVAS_SIZE), iris_box, blur=1.8)

    iris = apply_alpha_mask(open_eye, iris_mask)
    pupil_mask = dark_pixel_mask(open_eye, iris_mask)
    pupil = Image.new("RGBA", tuple(CANVAS_SIZE), (22, 23, 32, 0))
    pupil.putalpha(pupil_mask)

    highlight = Image.new("RGBA", tuple(CANVAS_SIZE), (255, 255, 255, 0))
    draw = ImageDraw.Draw(highlight)
    highlight_rx = max(5, int(width * 0.038))
    highlight_ry = max(3, int(height * 0.050))
    hx = center_x - width * 0.055
    hy = center_y - height * 0.105
    draw.ellipse((hx - highlight_rx, hy - highlight_ry, hx + highlight_rx, hy + highlight_ry), fill=(255, 255, 255, 160))
    highlight = highlight.filter(ImageFilter.GaussianBlur(0.35))

    white = open_eye.copy().convert("RGBA")
    white_pix = white.load()
    mask_pix = iris_mask.load()
    for y in range(y0, y1):
        for x in range(x0, x1):
            amount = mask_pix[x, y] / 255
            if amount <= 0:
                continue
            r, g, b, a = white_pix[x, y]
            if a <= 0:
                continue
            target = (238, 228, 218)
            blend = min(0.82, amount * 0.82)
            white_pix[x, y] = (
                int(r * (1 - blend) + target[0] * blend),
                int(g * (1 - blend) + target[1] * blend),
                int(b * (1 - blend) + target[2] * blend),
                a,
            )
    return {
        f"eye_{side}_white": white,
        f"eye_{side}_iris": iris,
        f"eye_{side}_pupil": pupil,
        f"eye_{side}_highlight": highlight,
    }


def alpha_scaled(image: Image.Image, scale: float) -> Image.Image:
    rgba = image.copy().convert("RGBA")
    alpha = rgba.getchannel("A")
    alpha = alpha.point(lambda v: int(max(0, min(255, round(v * scale)))))
    rgba.putalpha(alpha)
    return rgba


def make_lid_inbetweens(project: Path, side: str) -> dict[str, Image.Image]:
    half = Image.open(project / "parts" / f"eye_{side}_half_closed_lid.png").convert("RGBA")
    mostly = Image.open(project / "parts" / f"eye_{side}_mostly_closed_lid.png").convert("RGBA")
    closed = Image.open(project / "parts" / f"eye_{side}_closed_lid.png").convert("RGBA")
    lid_080 = alpha_scaled(half, 0.42)
    lid_065 = alpha_scaled(half, 0.72)
    lid_038 = Image.alpha_composite(alpha_scaled(mostly, 0.72), alpha_scaled(closed, 0.22))
    return {
        f"eye_{side}_lid_inbetween_080": lid_080,
        f"eye_{side}_lid_inbetween_065": lid_065,
        f"eye_{side}_lid_inbetween_038": lid_038,
    }


def opacity_key(part_id: str, parameter_id: str, keyframes: list[tuple[float, float]]) -> dict[str, Any]:
    return {
        "part_id": part_id,
        "parameter_id": parameter_id,
        "mode": "linear",
        "purpose": "v14 eye detail/in-between diagnostic",
        "keyframes": [{"value": value, "opacity": opacity} for value, opacity in keyframes],
    }


def replace_eye_opacity_keyframes(character: dict[str, Any]) -> None:
    eye_ids = set()
    for side in ["L", "R"]:
        eye_ids.update(
            [
                f"eye_{side}_clean_socket",
                f"eye_{side}_open",
                f"eye_{side}_white",
                f"eye_{side}_iris",
                f"eye_{side}_pupil",
                f"eye_{side}_highlight",
                f"eye_{side}_lid_inbetween_080",
                f"eye_{side}_lid_inbetween_065",
                f"eye_{side}_lid_inbetween_038",
                f"eye_{side}_half_closed_lid",
                f"eye_{side}_mostly_closed_lid",
                f"eye_{side}_closed_underpaint",
                f"eye_{side}_closed_lid",
            ]
        )
    character["part_opacity_keyframes"] = [
        row for row in character.get("part_opacity_keyframes", []) if row.get("part_id") not in eye_ids
    ]
    for side in ["L", "R"]:
        p = f"ParamEye{side}Open"
        detail_frames = [(0.27, 0.0), (0.38, 0.20), (0.50, 0.50), (0.65, 0.78), (0.80, 0.96), (1.00, 1.00)]
        for part_id in [f"eye_{side}_white", f"eye_{side}_iris", f"eye_{side}_pupil", f"eye_{side}_highlight"]:
            character["part_opacity_keyframes"].append(opacity_key(part_id, p, detail_frames))
        character["part_opacity_keyframes"].extend(
            [
                opacity_key(f"eye_{side}_clean_socket", p, [(0.27, 0), (1.00, 0)]),
                opacity_key(f"eye_{side}_open", p, [(0.27, 0), (1.00, 0)]),
                opacity_key(f"eye_{side}_lid_inbetween_080", p, [(0.27, 0), (0.50, 0), (0.65, 0.25), (0.80, 0.55), (1.00, 0)]),
                opacity_key(f"eye_{side}_lid_inbetween_065", p, [(0.27, 0), (0.38, 0.05), (0.50, 0.35), (0.65, 0.65), (0.80, 0), (1.00, 0)]),
                opacity_key(f"eye_{side}_lid_inbetween_038", p, [(0.27, 0.35), (0.38, 0.78), (0.50, 0.20), (0.65, 0), (1.00, 0)]),
                opacity_key(f"eye_{side}_half_closed_lid", p, [(0.27, 0), (0.38, 0.20), (0.50, 0.75), (0.65, 0.55), (0.80, 0), (1.00, 0)]),
                opacity_key(f"eye_{side}_mostly_closed_lid", p, [(0.27, 0.35), (0.38, 0.85), (0.50, 0.40), (0.65, 0), (1.00, 0)]),
                opacity_key(f"eye_{side}_closed_underpaint", p, [(0.27, 1.0), (0.38, 0.35), (0.50, 0), (1.00, 0)]),
                opacity_key(f"eye_{side}_closed_lid", p, [(0.27, 1.0), (0.38, 0.65), (0.50, 0.20), (0.65, 0), (1.00, 0)]),
            ]
        )


def binding(parameter_id: str, target_id: str, key_value: float, translate: list[float], scale: list[float] | None = None) -> dict[str, Any]:
    return {
        "parameter_id": parameter_id,
        "key_value": key_value,
        "target_id": target_id,
        "delta_type": "deformer_transform",
        "deltas": {"translate": translate, "scale": scale or [1, 1], "rotate": 0, "opacity": 1},
    }


def add_eye_ball_bindings(character: dict[str, Any], strength_x: float, strength_y: float) -> None:
    detail_ids = [
        "eye_L_iris",
        "eye_L_pupil",
        "eye_L_highlight",
        "eye_R_iris",
        "eye_R_pupil",
        "eye_R_highlight",
    ]
    character["keyform_bindings"] = [
        row
        for row in character.get("keyform_bindings", [])
        if not (row.get("parameter_id") in {"ParamEyeBallX", "ParamEyeBallY"} and row.get("target_id") in detail_ids)
    ]
    for part_id in detail_ids:
        multiplier = 1.08 if part_id.endswith("_pupil") else (1.15 if part_id.endswith("_highlight") else 1.0)
        character["keyform_bindings"].extend(
            [
                binding("ParamEyeBallX", part_id, -1, [-strength_x * multiplier, 0]),
                binding("ParamEyeBallX", part_id, 1, [strength_x * multiplier, 0]),
                binding("ParamEyeBallY", part_id, -1, [0, -strength_y * multiplier]),
                binding("ParamEyeBallY", part_id, 1, [0, strength_y * multiplier]),
            ]
        )


def update_deformer_children(character: dict[str, Any]) -> None:
    part_ids = {part["id"] for part in character.get("parts", [])}
    for deformer in character.get("deformers", []):
        if deformer.get("id") == "eye_L_warp":
            extras = [fmt.format(side="L") for fmt in EYE_DETAIL_IDS]
        elif deformer.get("id") == "eye_R_warp":
            extras = [fmt.format(side="R") for fmt in EYE_DETAIL_IDS]
        else:
            continue
        child_ids = list(dict.fromkeys(deformer.get("child_ids", []) + [part_id for part_id in extras if part_id in part_ids]))
        deformer["child_ids"] = child_ids


def sort_project(character: dict[str, Any]) -> None:
    character["parts"] = sorted(character["parts"], key=lambda row: (row.get("draw_order", 0), row.get("id", "")))
    order = {part["id"]: index for index, part in enumerate(character["parts"])}
    character["meshes"] = sorted(character["meshes"], key=lambda row: order.get(row.get("part_id"), 9999))
    character["parameters"] = sorted(character["parameters"], key=lambda row: row.get("id", ""))
    character["keyform_bindings"] = sorted(
        character["keyform_bindings"],
        key=lambda row: (row.get("parameter_id", ""), row.get("target_id", ""), float(row.get("key_value", 0))),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-project", default=str(DEFAULT_SOURCE))
    parser.add_argument("--out-project", default=str(DEFAULT_OUT))
    parser.add_argument("--reports", default=str(DEFAULT_REPORTS))
    parser.add_argument("--eye-ball-x", type=float, default=8.0)
    parser.add_argument("--eye-ball-y", type=float, default=5.0)
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
    upsert_parameter(character, {"id": "ParamEyeBallX", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]})
    upsert_parameter(character, {"id": "ParamEyeBallY", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]})

    created: dict[str, Any] = {}
    for side, draw_base in [("L", 302), ("R", 303)]:
        template = next(part for part in character["parts"] if part["id"] == f"eye_{side}_open")
        open_eye = Image.open(out_project / "parts" / f"eye_{side}_open.png").convert("RGBA")
        detail_layers = make_eye_detail_layers(open_eye, side)
        lid_layers = make_lid_inbetweens(out_project, side)
        for offset, part_id in enumerate([f"eye_{side}_white", f"eye_{side}_iris", f"eye_{side}_pupil", f"eye_{side}_highlight"]):
            created[part_id] = add_or_replace_part(
                character,
                out_project,
                part_id,
                detail_layers[part_id],
                template,
                draw_base + offset * 2,
                f"derived from {rel(out_project / 'parts' / f'eye_{side}_open.png')}",
                ["v14_eye_detail_split_diagnostic", "baked_eye_derivative"],
            )
        for offset, part_id in enumerate([f"eye_{side}_lid_inbetween_080", f"eye_{side}_lid_inbetween_065", f"eye_{side}_lid_inbetween_038"]):
            created[part_id] = add_or_replace_part(
                character,
                out_project,
                part_id,
                lid_layers[part_id],
                template,
                312 + (0 if side == "L" else 1) + offset * 4,
                f"derived from v13 eye_{side} lid keyposes",
                ["v14_eye_close_inbetween_diagnostic"],
            )

    replace_eye_opacity_keyframes(character)
    add_eye_ball_bindings(character, args.eye_ball_x, args.eye_ball_y)
    update_deformer_children(character)
    character["experiment_id"] = "cubism-v2-new-character-002/model_edit_v14_eye_detail_inbetween_preview"
    character["generated_at"] = now()
    character["notes"] = character.get("notes", []) + [
        "v14 preserves v13 eye/mouth scale, EyeOpen min 0.27, and MouthOpenY max 0.85.",
        "v14 adds diagnostic eye_L/R_white, iris, pupil, highlight parts derived from baked v13 eye_open art.",
        "v14 adds EyeOpen linear opacity in-between lid layers; this is diagnostic layer-split evidence, not production clean eye material approval.",
    ]
    sort_project(character)
    character_path.write_text(json.dumps(character, ensure_ascii=False, indent=2) + "\n")

    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "V14_EYE_DETAIL_INBETWEEN_READY_FOR_VALIDATION",
        "source_project": rel(source_project),
        "project": rel(out_project),
        "policy": {
            "preserve_v13_success_pattern": True,
            "eye_open_min": 0.27,
            "mouth_open_y_max": 0.85,
            "production_claim": "diagnostic only; baked eye derivative split requires human visual QA before promotion",
        },
        "eye_ball_binding_strength": {"x": args.eye_ball_x, "y": args.eye_ball_y},
        "created_parts": created,
    }
    report_path = reports / "mini_cubism_v14_eye_detail_inbetween_report.json"
    write_json(report_path, report)
    print(json.dumps({"ok": True, "report": str(report_path), "project": str(out_project)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

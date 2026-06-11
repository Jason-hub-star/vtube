#!/usr/bin/env python3
"""Build Character 002 v18 with fixed white and centered iris-only movement."""

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
DEFAULT_SOURCE = EXP / "model_edit_v15_eye_nose_position_preview/mini_cubism_diagnostic_project"
DEFAULT_OUT = EXP / "model_edit_v18_clean_white_center_iris_preview/mini_cubism_diagnostic_project"
DEFAULT_REPORTS = EXP / "reports/model_edit_v18_clean_white_center_iris_preview"
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


def save_part(character: dict[str, Any], project: Path, part_id: str, image: Image.Image, tag: str) -> dict[str, Any]:
    bbox, nonzero, coverage = bbox_metrics(image)
    image.save(project / "parts" / f"{part_id}.png")
    mesh = mesh_for_part(part_id, bbox, CANVAS_SIZE)
    (project / "meshes" / f"{part_id}.json").write_text(json.dumps(mesh, ensure_ascii=False, indent=2) + "\n")
    for part in character.get("parts", []):
        if part.get("id") == part_id:
            part["bbox"] = bbox
            part["alpha_coverage"] = coverage
            tags = set(part.get("risk_tags", []))
            tags.add(tag)
            part["risk_tags"] = sorted(tags)
            break
    character["meshes"] = [row for row in character.get("meshes", []) if row.get("part_id") != part_id] + [mesh]
    return {"bbox_xywh": bbox, "alpha_nonzero": nonzero, "alpha_coverage": coverage}


def ellipse_mask(size: tuple[int, int], box: tuple[float, float, float, float], blur: float) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(tuple(int(round(v)) for v in box), fill=255)
    if blur:
        mask = mask.filter(ImageFilter.GaussianBlur(blur))
    return mask


def eye_geometry(open_eye: Image.Image, side: str) -> tuple[float, float, float, float]:
    bbox = open_eye.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError(f"eye_{side}_open is empty")
    x0, y0, x1, y1 = bbox
    width = x1 - x0
    height = y1 - y0
    cx = x0 + (0.52 if side == "L" else 0.48) * width
    cy = y0 + 0.49 * height
    return cx, cy, width, height


def make_iris_mask(open_eye: Image.Image, side: str) -> Image.Image:
    cx, cy, width, height = eye_geometry(open_eye, side)
    gate = ellipse_mask(tuple(CANVAS_SIZE), (cx - width * 0.215, cy - height * 0.335, cx + width * 0.215, cy + height * 0.335), 1.1)
    src = open_eye.load()
    gate_px = gate.load()
    out = Image.new("L", tuple(CANVAS_SIZE), 0)
    out_px = out.load()
    for y in range(CANVAS_SIZE[1]):
        for x in range(CANVAS_SIZE[0]):
            if gate_px[x, y] <= 0:
                continue
            r, g, b, a = src[x, y]
            if a < 24:
                continue
            value = max(r, g, b)
            sat = (value - min(r, g, b)) / max(value, 1)
            if value < 150 or sat > 0.17 or b > r + 10:
                out_px[x, y] = min(255, int(a * (gate_px[x, y] / 255) * 1.25))
    return out.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.7))


def make_clean_white(open_eye: Image.Image, iris_mask: Image.Image, side: str) -> Image.Image:
    cx, cy, width, height = eye_geometry(open_eye, side)
    erase = ellipse_mask(tuple(CANVAS_SIZE), (cx - width * 0.255, cy - height * 0.39, cx + width * 0.255, cy + height * 0.39), 3.5)
    erase = ImageChops.lighter(erase, iris_mask.filter(ImageFilter.MaxFilter(19)).filter(ImageFilter.GaussianBlur(3)))
    white = open_eye.copy().convert("RGBA")
    pix = white.load()
    erase_px = erase.load()
    for y in range(CANVAS_SIZE[1]):
        for x in range(CANVAS_SIZE[0]):
            amount = erase_px[x, y] / 255
            if amount <= 0:
                continue
            r, g, b, a = pix[x, y]
            if a <= 0:
                continue
            target = (242, 235, 228)
            blend = min(1.0, amount * 1.08)
            pix[x, y] = (
                int(r * (1 - blend) + target[0] * blend),
                int(g * (1 - blend) + target[1] * blend),
                int(b * (1 - blend) + target[2] * blend),
                a,
            )
    return white


def apply_mask(image: Image.Image, mask: Image.Image) -> Image.Image:
    out = image.copy().convert("RGBA")
    out.putalpha(ImageChops.multiply(out.getchannel("A"), mask))
    return out


def make_pupil(open_eye: Image.Image, iris_mask: Image.Image) -> Image.Image:
    src = open_eye.load()
    iris_px = iris_mask.load()
    out = Image.new("L", tuple(CANVAS_SIZE), 0)
    out_px = out.load()
    for y in range(CANVAS_SIZE[1]):
        for x in range(CANVAS_SIZE[0]):
            if iris_px[x, y] < 24:
                continue
            r, g, b, a = src[x, y]
            if a > 20 and max(r, g, b) < 90:
                out_px[x, y] = min(255, int(a * 1.25))
    out = out.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.5))
    pupil = Image.new("RGBA", tuple(CANVAS_SIZE), (24, 22, 34, 0))
    pupil.putalpha(out)
    return pupil


def make_highlight(open_eye: Image.Image, iris_mask: Image.Image) -> Image.Image:
    src = open_eye.load()
    iris_px = iris_mask.load()
    out = Image.new("L", tuple(CANVAS_SIZE), 0)
    out_px = out.load()
    for y in range(CANVAS_SIZE[1]):
        for x in range(CANVAS_SIZE[0]):
            if iris_px[x, y] < 20:
                continue
            r, g, b, a = src[x, y]
            if a > 20 and min(r, g, b) > 190 and max(r, g, b) - min(r, g, b) < 55:
                out_px[x, y] = min(220, int(a * 1.15))
    out = out.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.35))
    highlight = Image.new("RGBA", tuple(CANVAS_SIZE), (255, 255, 255, 0))
    highlight.putalpha(out)
    return highlight


def rebuild_assets(character: dict[str, Any], project: Path) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for side in ["L", "R"]:
        open_eye = Image.open(project / "parts" / f"eye_{side}_open.png").convert("RGBA")
        iris_mask = make_iris_mask(open_eye, side)
        metrics[f"eye_{side}_white"] = save_part(character, project, f"eye_{side}_white", make_clean_white(open_eye, iris_mask, side), "v18_clean_fixed_eye_white")
        metrics[f"eye_{side}_iris"] = save_part(character, project, f"eye_{side}_iris", apply_mask(open_eye, iris_mask), "v18_center_moving_iris")
        metrics[f"eye_{side}_pupil"] = save_part(character, project, f"eye_{side}_pupil", make_pupil(open_eye, iris_mask), "v18_center_moving_pupil")
        metrics[f"eye_{side}_highlight"] = save_part(character, project, f"eye_{side}_highlight", make_highlight(open_eye, iris_mask), "v18_center_moving_highlight")
    return metrics


def sort_project(character: dict[str, Any]) -> None:
    character["parts"] = sorted(character["parts"], key=lambda row: (row.get("draw_order", 0), row.get("id", "")))
    order = {part["id"]: index for index, part in enumerate(character["parts"])}
    character["meshes"] = sorted(character["meshes"], key=lambda row: order.get(row.get("part_id"), 9999))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-project", default=str(DEFAULT_SOURCE))
    parser.add_argument("--out-project", default=str(DEFAULT_OUT))
    parser.add_argument("--reports", default=str(DEFAULT_REPORTS))
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
    rebuilt = rebuild_assets(character, out_project)
    character["experiment_id"] = "cubism-v2-new-character-002/model_edit_v18_clean_white_center_iris_preview"
    character["generated_at"] = now()
    character["notes"] = character.get("notes", []) + [
        "v18 preserves v15 bindings: fixed eye white, moving iris/pupil/highlight.",
        "v18 cleans fixed eye white more strongly while keeping the moving mask centered on iris only, excluding lashes/lids.",
    ]
    sort_project(character)
    character_path.write_text(json.dumps(character, ensure_ascii=False, indent=2) + "\n")

    report = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "V18_CLEAN_WHITE_CENTER_IRIS_READY_FOR_VALIDATION",
        "source_project": rel(source_project),
        "project": rel(out_project),
        "rebuilt_parts": rebuilt,
        "policy": {
            "eye_white_moves": False,
            "iris_pupil_highlight_move_together": True,
            "moving_mask_excludes_lashes": True,
            "production_claim": "diagnostic only; true production eye split still needs clean source material",
        },
    }
    report_path = reports / "mini_cubism_v18_clean_white_center_iris_report.json"
    write_json(report_path, report)
    print(json.dumps({"ok": True, "report": str(report_path), "project": str(out_project)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

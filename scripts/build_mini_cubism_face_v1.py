#!/usr/bin/env python3
"""Build a face-focused Mini Cubism candidate from the targeted project."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from build_mini_cubism_dedicated_model_v1 import CANVAS, mesh_for_part


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = ROOT / "experiments/mini-cubism-dedicated-model-v1-001"
SOURCE_PROJECT_NAME = "mini_cubism_project_targeted"
FACE_PROJECT_NAME = "mini_cubism_project_face_v1"

FACE_BBOXES = {
    "nose_bridge": [1014, 662, 26, 132],
    "nose_tip": [998, 770, 58, 32],
    "mouth_corner_L": [1082, 844, 38, 34],
    "mouth_corner_R": [928, 844, 38, 34],
    "eye_shadow_L": [1048, 596, 220, 126],
    "eye_shadow_R": [780, 596, 220, 126],
}

FACE_REPLACE_IDS = {
    "cheek_blush_L",
    "cheek_blush_R",
    "upper_lid_L",
    "upper_lid_R",
    "lower_lid_L",
    "lower_lid_R",
    "brow_L",
    "brow_R",
    "mouth_half_outer",
    "mouth_half_inner",
    "mouth_open_outer",
    "mouth_open_inner",
    "mouth_teeth_upper",
    "mouth_tongue",
    "mouth_shadow",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def bbox_alpha(image: Image.Image) -> tuple[list[int], float]:
    alpha = image.convert("RGBA").getchannel("A")
    bbox = alpha.getbbox()
    nonzero = sum(alpha.histogram()[1:])
    total = image.width * image.height
    if not bbox:
        return [0, 0, 2, 2], 0.0
    left, top, right, bottom = bbox
    return [left, top, right - left, bottom - top], round(nonzero / total, 8)


def font(size: int) -> ImageFont.ImageFont:
    for candidate in [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def draw_soft_ellipse(draw: ImageDraw.ImageDraw, bbox: list[float], fill: tuple[int, int, int, int]) -> None:
    draw.ellipse([round(v) for v in bbox], fill=fill)


def draw_face_part(part_id: str) -> Image.Image:
    image = Image.new("RGBA", tuple(CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    skin_line = (109, 61, 67, 190)
    blush = (238, 118, 143, 95)
    lid = (74, 42, 52, 220)
    shadow = (82, 55, 72, 58)
    mouth = (112, 43, 58, 235)
    inner = (34, 13, 24, 245)
    tongue = (205, 84, 105, 220)

    if part_id == "cheek_blush_L":
        draw_soft_ellipse(draw, [1105, 712, 1245, 778], blush)
    elif part_id == "cheek_blush_R":
        draw_soft_ellipse(draw, [795, 712, 935, 778], blush)
    elif part_id == "nose_bridge":
        draw.arc([1002, 655, 1056, 806], 82, 178, fill=skin_line, width=5)
    elif part_id == "nose_tip":
        draw.arc([994, 752, 1060, 810], 28, 152, fill=skin_line, width=5)
    elif part_id == "eye_shadow_L":
        draw_soft_ellipse(draw, [1048, 590, 1268, 724], shadow)
    elif part_id == "eye_shadow_R":
        draw_soft_ellipse(draw, [780, 590, 1000, 724], shadow)
    elif part_id == "upper_lid_L":
        draw.arc([1038, 592, 1278, 706], 198, 342, fill=lid, width=8)
        draw.arc([1044, 608, 1268, 714], 198, 342, fill=(247, 212, 205, 120), width=18)
    elif part_id == "upper_lid_R":
        draw.arc([766, 592, 1006, 706], 198, 342, fill=lid, width=8)
        draw.arc([776, 608, 996, 714], 198, 342, fill=(247, 212, 205, 120), width=18)
    elif part_id == "lower_lid_L":
        draw.arc([1050, 650, 1266, 752], 18, 164, fill=(118, 70, 78, 170), width=4)
    elif part_id == "lower_lid_R":
        draw.arc([782, 650, 998, 752], 18, 164, fill=(118, 70, 78, 170), width=4)
    elif part_id == "brow_L":
        draw.arc([1060, 512, 1264, 574], 194, 340, fill=(27, 22, 42, 235), width=11)
    elif part_id == "brow_R":
        draw.arc([784, 512, 988, 574], 200, 346, fill=(27, 22, 42, 235), width=11)
    elif part_id == "mouth_half_outer":
        draw.ellipse([936, 817, 1114, 884], fill=mouth)
    elif part_id == "mouth_half_inner":
        draw.ellipse([968, 835, 1082, 873], fill=inner)
    elif part_id == "mouth_open_outer":
        draw.ellipse([922, 802, 1128, 930], fill=mouth)
    elif part_id == "mouth_open_inner":
        draw.ellipse([958, 826, 1092, 912], fill=inner)
    elif part_id == "mouth_teeth_upper":
        draw.rounded_rectangle([982, 826, 1068, 852], radius=8, fill=(252, 240, 229, 232))
    elif part_id == "mouth_tongue":
        draw.ellipse([980, 868, 1072, 904], fill=tongue)
    elif part_id == "mouth_shadow":
        draw.ellipse([950, 842, 1100, 912], fill=(20, 8, 15, 155))
    elif part_id == "mouth_corner_L":
        draw.arc([1074, 830, 1126, 878], 190, 305, fill=(89, 35, 50, 210), width=5)
    elif part_id == "mouth_corner_R":
        draw.arc([922, 830, 974, 878], 235, 350, fill=(89, 35, 50, 210), width=5)
    else:
        raise KeyError(part_id)
    return image


def preview_tile(path: Path, tile_size: int = 200) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    bbox = image.getchannel("A").getbbox()
    crop = image.crop(bbox) if bbox else Image.new("RGBA", (tile_size, tile_size), (0, 0, 0, 0))
    crop.thumbnail((tile_size, tile_size - 28), Image.Resampling.LANCZOS)
    tile = Image.new("RGB", (tile_size, tile_size), "#f4f0e8")
    tile.paste(crop.convert("RGB"), ((tile_size - crop.width) // 2, 6), crop)
    return tile


def build_contact_sheet(layers: list[dict[str, Any]], out: Path) -> None:
    cols = 5
    cell_w = 240
    cell_h = 258
    header_h = 74
    rows = (len(layers) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, header_h + rows * cell_h), "#f4f0e8")
    draw = ImageDraw.Draw(sheet)
    draw.text((18, 14), "Mini Cubism Face Split v1", fill="#202124", font=font(25))
    draw.text((18, 46), "Face-only replacement candidate; targeted physics baseline is preserved.", fill="#5f6368", font=font(13))
    small = font(12)
    for i, layer in enumerate(layers):
        x = (i % cols) * cell_w
        y = header_h + (i // cols) * cell_h
        draw.rectangle([x + 8, y + 8, x + cell_w - 8, y + cell_h - 8], fill="#ffffff", outline="#d6d0c8")
        tile = preview_tile(Path(layer["output_path"]))
        sheet.paste(tile, (x + 20, y + 14))
        draw.text((x + 16, y + 216), layer["part_id"][:28], fill="#202124", font=small)
        draw.text((x + 16, y + 234), layer["derivation_mode"], fill="#2f6fbb", font=small)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def part_record(part_id: str, png: Path, bbox: list[int], coverage: float, draw_order: int, folder: str, original: str) -> dict[str, Any]:
    return {
        "id": part_id,
        "display_name": part_id,
        "source_path": f"parts/{png.name}",
        "original_source_path": original,
        "bbox": bbox,
        "alpha_coverage": coverage,
        "draw_order": draw_order,
        "folder": folder,
    }


def upsert_part(project: Path, character: dict[str, Any], part_id: str, image: Image.Image, draw_order: int, folder: str, original: str) -> dict[str, Any]:
    png = project / "parts" / f"{part_id}.png"
    image.save(png)
    bbox, coverage = bbox_alpha(image)
    mesh = mesh_for_part(part_id, bbox, CANVAS)
    mesh_path = project / "meshes" / f"{part_id}.json"
    mesh["mesh_path"] = f"meshes/{mesh_path.name}"
    write_json(mesh_path, mesh)
    record = part_record(part_id, png, bbox, coverage, draw_order, folder, original)

    character["parts"] = [part for part in character["parts"] if part["id"] != part_id] + [record]
    character["meshes"] = [item for item in character["meshes"] if item["part_id"] != part_id] + [mesh]
    return record


def ensure_parameter(character: dict[str, Any], parameter: dict[str, Any]) -> None:
    if not any(item.get("id") == parameter["id"] for item in character["parameters"]):
        character["parameters"].append(parameter)


def add_binding(bindings: list[dict[str, Any]], parameter_id: str, key_value: float, target_id: str, translate: list[float] | None = None, scale: list[float] | None = None, rotate: float = 0, opacity: float = 1) -> None:
    bindings.append(
        {
            "parameter_id": parameter_id,
            "key_value": key_value,
            "target_id": target_id,
            "delta_type": "deformer_transform",
            "deltas": {
                "translate": translate or [0, 0],
                "scale": scale or [1, 1],
                "rotate": rotate,
                "opacity": opacity,
            },
        }
    )


def add_face_bindings(character: dict[str, Any]) -> None:
    for parameter in [
        {"id": "ParamEyeBallX", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
        {"id": "ParamEyeBallY", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
        {"id": "ParamBrowLY", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
        {"id": "ParamBrowRY", "min": -1, "max": 1, "default": 0, "key_values": [-1, 0, 1]},
        {"id": "ParamCheek", "min": 0, "max": 1, "default": 0, "key_values": [0, 1]},
    ]:
        ensure_parameter(character, parameter)

    bindings = character["keyform_bindings"]
    eye_motion_parts = ["iris_L", "iris_R", "pupil_L", "pupil_R", "catchlight_L", "catchlight_R"]
    for part_id in eye_motion_parts:
        add_binding(bindings, "ParamEyeBallX", -1, part_id, translate=[-16, 0])
        add_binding(bindings, "ParamEyeBallX", 1, part_id, translate=[16, 0])
        add_binding(bindings, "ParamEyeBallY", -1, part_id, translate=[0, 10])
        add_binding(bindings, "ParamEyeBallY", 1, part_id, translate=[0, -10])

    add_binding(bindings, "ParamBrowLY", -1, "brow_L", translate=[0, 12], rotate=3)
    add_binding(bindings, "ParamBrowLY", 1, "brow_L", translate=[0, -16], rotate=-5)
    add_binding(bindings, "ParamBrowRY", -1, "brow_R", translate=[0, 12], rotate=-3)
    add_binding(bindings, "ParamBrowRY", 1, "brow_R", translate=[0, -16], rotate=5)
    for part_id in ["mouth_closed_line", "mouth_half_outer", "mouth_half_inner", "mouth_open_outer", "mouth_open_inner", "mouth_teeth_upper", "mouth_tongue", "mouth_shadow"]:
        add_binding(bindings, "ParamMouthForm", -1, part_id, translate=[0, 6], scale=[0.94, 0.95], rotate=-1)
        add_binding(bindings, "ParamMouthForm", 1, part_id, translate=[0, -8], scale=[1.08, 0.9], rotate=1)
    for part_id, sign in [("mouth_corner_L", 1), ("mouth_corner_R", -1)]:
        add_binding(bindings, "ParamMouthForm", -1, part_id, translate=[-6 * sign, 6], rotate=-8 * sign)
        add_binding(bindings, "ParamMouthForm", 1, part_id, translate=[8 * sign, -12], rotate=8 * sign)
    for part_id in ["nose_bridge", "nose_tip", "cheek_blush_L", "cheek_blush_R", "eye_shadow_L", "eye_shadow_R"]:
        add_binding(bindings, "ParamAngleX", -30, part_id, translate=[-8, 0])
        add_binding(bindings, "ParamAngleX", 30, part_id, translate=[8, 0])

    character.setdefault("part_opacity_keyframes", [])
    for part_id in ["cheek_blush_L", "cheek_blush_R"]:
        character["part_opacity_keyframes"] = [item for item in character["part_opacity_keyframes"] if not (item.get("part_id") == part_id and item.get("parameter_id") == "ParamCheek")]
        character["part_opacity_keyframes"].append(
            {"part_id": part_id, "parameter_id": "ParamCheek", "mode": "linear", "keyframes": [{"value": 0, "opacity": 0.45}, {"value": 1, "opacity": 1}]}
        )


def update_deformers(character: dict[str, Any], face_ids: set[str]) -> None:
    for deformer in character["deformers"]:
        if deformer["id"] == "Face_Base":
            deformer["child_ids"] = sorted(set(deformer.get("child_ids", [])) | face_ids)
        if deformer["id"] == "Mouth":
            deformer["child_ids"] = sorted(set(deformer.get("child_ids", [])) | {"mouth_corner_L", "mouth_corner_R"})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", default=str(DEFAULT_EXPERIMENT))
    args = parser.parse_args()

    exp = Path(args.experiment).resolve()
    source_project = exp / SOURCE_PROJECT_NAME
    project = exp / FACE_PROJECT_NAME
    if not (source_project / "character.json").exists():
        raise SystemExit(f"missing targeted project: {source_project}")
    for subdir in ["parts", "meshes", "deformers", "parameters", "motions"]:
        shutil.copytree(source_project / subdir, project / subdir, dirs_exist_ok=True)
    (project / "reports").mkdir(parents=True, exist_ok=True)
    character = load_json(source_project / "character.json")
    character["experiment_id"] = f"{exp.name}-face-v1"
    character["source_selection"] = "face_split_v1/face_split_manifest.json"
    character.setdefault("notes", []).append("Face Split v1 replaces only face/eye/mouth expression candidates; targeted physics baseline remains preserved.")

    face_dir = exp / "face_split_v1"
    parts_dir = face_dir / "parts"
    parts_dir.mkdir(parents=True, exist_ok=True)
    face_layers: list[dict[str, Any]] = []
    replacement_ids = sorted(FACE_REPLACE_IDS | set(FACE_BBOXES))
    for index, part_id in enumerate(replacement_ids):
        image = draw_face_part(part_id)
        source_png = parts_dir / f"{part_id}.png"
        image.save(source_png)
        bbox, coverage = bbox_alpha(image)
        draw_order = 360 + index if part_id.startswith(("nose", "cheek", "eye_shadow")) else 520 + index
        if part_id.startswith("mouth"):
            draw_order = 615 + index
        folder = "Mouth" if part_id.startswith("mouth") else "Eyes" if any(key in part_id for key in ["eye", "lid", "brow"]) else "Face"
        project_image = Image.open(source_png).convert("RGBA")
        upsert_part(project, character, part_id, project_image, draw_order, folder, f"face_split_v1:{source_png}")
        face_layers.append(
            {
                "part_id": part_id,
                "output_path": str(source_png),
                "bbox": bbox,
                "alpha_coverage": coverage,
                "draw_order": draw_order,
                "folder": folder,
                "derivation_mode": "face_v1_procedural_replacement",
                "status": "FACE_CANDIDATE",
            }
        )

    face_ids = {item["part_id"] for item in face_layers if item["folder"] == "Face"}
    update_deformers(character, face_ids | {"cheek_blush_L", "cheek_blush_R"})
    add_face_bindings(character)
    write_json(project / "character.json", character)
    write_json(project / "deformers" / "deformers.json", character["deformers"])
    write_json(project / "parameters" / "parameters.json", character["parameters"])

    contact_sheet = exp / "reports" / "face_split_v1_contact_sheet.png"
    build_contact_sheet(face_layers, contact_sheet)
    manifest = {
        "schema_version": 1,
        "experiment_id": exp.name,
        "generated_at": now(),
        "status": "BUILT_PENDING_VALIDATION",
        "source_project": str(source_project),
        "project": str(project),
        "face_split_dir": str(face_dir),
        "layers": face_layers,
        "counts": {
            "face_replacement_parts": len(face_layers),
            "new_parameters": 5,
            "total_parameters": len(character["parameters"]),
            "total_keyform_bindings": len(character["keyform_bindings"]),
        },
        "review_contact_sheet": str(contact_sheet),
        "interpretation": [
            "This is a face-only candidate replacement over the targeted Mini Cubism baseline.",
            "It does not discard the previous targeted split or motion evidence.",
            "Generated face expression parts require close-up visual QA before promotion.",
        ],
    }
    write_json(face_dir / "face_split_manifest.json", manifest)
    write_json(exp / "reports" / "face_split_v1_report.json", manifest)
    print(json.dumps({"ok": True, "project": str(project), "manifest": str(face_dir / "face_split_manifest.json"), "counts": manifest["counts"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

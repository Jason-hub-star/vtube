#!/usr/bin/env python3
"""Build a Mini Cubism candidate with baked eye pixels removed from face_base."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = (
    ROOT
    / "experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_face_detail_rebuild_v1"
)
DEFAULT_OUTPUT = (
    ROOT
    / "experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_face_base_clean_v1"
)
EYE_PART_SUFFIXES = [
    "white",
    "underpaint",
    "iris",
    "pupil",
    "highlight",
    "upper_lash",
    "lower_lash",
    "closed_lid",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def alpha_bbox(image: Image.Image) -> list[int]:
    bbox = image.getchannel("A").getbbox()
    if not bbox:
        return [0, 0, image.width, image.height]
    left, top, right, bottom = bbox
    return [left, top, right - left, bottom - top]


def alpha_coverage(image: Image.Image) -> float:
    alpha = np.asarray(image.getchannel("A"), dtype=np.uint8)
    return round(float((alpha > 0).sum()) / float(alpha.size), 8)


def bbox_to_mask(mask: np.ndarray, bbox: list[int], value: int = 255) -> None:
    height, width = mask.shape
    x, y, w, h = [int(v) for v in bbox]
    left = max(0, x)
    top = max(0, y)
    right = min(width, x + w)
    bottom = min(height, y + h)
    if right > left and bottom > top:
        mask[top:bottom, left:right] = value


def ellipse_to_mask(mask: np.ndarray, bbox: list[int], value: int = 255) -> None:
    x, y, w, h = [int(v) for v in bbox]
    center = (int(x + w / 2), int(y + h / 2))
    axes = (max(1, int(w / 2)), max(1, int(h / 2)))
    cv2.ellipse(mask, center, axes, 0, 0, 360, value, thickness=-1)


def expanded_bbox(bbox: list[int], pad: int, canvas_size: tuple[int, int]) -> list[int]:
    width, height = canvas_size
    x, y, w, h = [int(v) for v in bbox]
    left = max(0, x - pad)
    top = max(0, y - pad)
    right = min(width, x + w + pad)
    bottom = min(height, y + h + pad)
    return [left, top, max(1, right - left), max(1, bottom - top)]


def union_bboxes(bboxes: list[list[int]], pad: int, canvas_size: tuple[int, int]) -> list[int]:
    width, height = canvas_size
    left = max(0, min(bbox[0] for bbox in bboxes) - pad)
    top = max(0, min(bbox[1] for bbox in bboxes) - pad)
    right = min(width, max(bbox[0] + bbox[2] for bbox in bboxes) + pad)
    bottom = min(height, max(bbox[1] + bbox[3] for bbox in bboxes) + pad)
    return [left, top, right - left, bottom - top]


def paste_part_alpha(mask: np.ndarray, project_dir: Path, part: dict[str, Any]) -> None:
    image = Image.open(project_dir / part["source_path"]).convert("RGBA")
    alpha = np.asarray(image.getchannel("A"), dtype=np.uint8)
    mask[alpha > 8] = 255


def build_eye_masks(
    project_dir: Path,
    character: dict[str, Any],
    rig: dict[str, Any],
    dilate_px: int,
    bbox_pad: int,
    include_part_union_box: bool,
    cover_shape: str,
    mask_source: str,
) -> tuple[np.ndarray, dict[str, Any]]:
    canvas_size = tuple(character["canvas_size"])
    width, height = canvas_size
    parts_by_id = {part["id"]: part for part in character["parts"]}
    full_mask = np.zeros((height, width), dtype=np.uint8)
    side_masks: dict[str, np.ndarray] = {
        "L": np.zeros((height, width), dtype=np.uint8),
        "R": np.zeros((height, width), dtype=np.uint8),
    }
    mask_meta: dict[str, Any] = {"sides": {}, "manual_eye_socket_covers": {}}
    covers = (rig.get("eye_socket_covers") or {}) if rig else {}

    for side in ["L", "R"]:
        prefix = f"eye_{side}_"
        selected_ids = [f"{prefix}{suffix}" for suffix in EYE_PART_SUFFIXES if f"{prefix}{suffix}" in parts_by_id]
        selected_parts = [parts_by_id[part_id] for part_id in selected_ids]
        if not selected_parts:
            continue
        side_mask = side_masks[side]
        if mask_source != "manual_only":
            for part in selected_parts:
                paste_part_alpha(side_mask, project_dir, part)
        part_union = union_bboxes([part["bbox"] for part in selected_parts], bbox_pad, canvas_size)
        if include_part_union_box and mask_source != "manual_only":
            bbox_to_mask(side_mask, part_union)
        cover_bbox = ((covers.get(side) or {}).get("bbox") if isinstance(covers, dict) else None) or None
        if isinstance(cover_bbox, list) and len(cover_bbox) == 4:
            mask_meta["manual_eye_socket_covers"][side] = cover_bbox
            cover_mask_bbox = expanded_bbox(cover_bbox, bbox_pad, canvas_size)
            if cover_shape == "box":
                bbox_to_mask(side_mask, cover_mask_bbox)
            elif cover_shape == "ellipse":
                ellipse_to_mask(side_mask, cover_mask_bbox)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate_px * 2 + 1, dilate_px * 2 + 1))
        side_mask = cv2.dilate(side_mask, kernel, iterations=1)
        side_masks[side] = side_mask
        full_mask = np.maximum(full_mask, side_mask)
        ys, xs = np.where(side_mask > 0)
        mask_bbox = [int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)]
        mask_meta["sides"][side] = {
            "selected_part_ids": selected_ids,
            "part_union_bbox": part_union,
            "include_part_union_box": include_part_union_box,
            "cover_shape": cover_shape,
            "mask_source": mask_source,
            "actual_mask_bbox": mask_bbox,
            "masked_pixels": int((side_mask > 0).sum()),
        }

    mask_meta["masked_pixels_total"] = int((full_mask > 0).sum())
    return full_mask, {"full": full_mask, "sides": side_masks, "meta": mask_meta}


def inpaint_face_base(face_base: Image.Image, mask: np.ndarray, radius: int) -> Image.Image:
    rgba = np.asarray(face_base.convert("RGBA"), dtype=np.uint8)
    rgb = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2BGR)
    cleaned = cv2.inpaint(rgb, mask, radius, cv2.INPAINT_TELEA)
    cleaned_rgb = cv2.cvtColor(cleaned, cv2.COLOR_BGR2RGB)
    out = np.dstack([cleaned_rgb, rgba[:, :, 3]])
    return Image.fromarray(out, "RGBA")


def synthesize_skin_face_base(face_base: Image.Image, masks: dict[str, Any]) -> Image.Image:
    rgba = np.asarray(face_base.convert("RGBA"), dtype=np.uint8).copy()
    rgb = rgba[:, :, :3].astype(np.float32)
    result = rgb.copy()
    for side in ["L", "R"]:
        side_mask = masks["sides"][side] > 0
        ys, xs = np.where(side_mask)
        if len(xs) == 0:
            continue
        pad = 58
        left = max(0, int(xs.min()) - pad)
        top = max(0, int(ys.min()) - pad)
        right = min(face_base.width, int(xs.max()) + pad + 1)
        bottom = min(face_base.height, int(ys.max()) + pad + 1)
        roi = result[top:bottom, left:right].copy()
        source_roi = rgb[top:bottom, left:right].copy()
        mask_roi = side_mask[top:bottom, left:right]
        alpha_roi = rgba[top:bottom, left:right, 3] > 0
        r = source_roi[:, :, 0]
        g = source_roi[:, :, 1]
        b = source_roi[:, :, 2]
        skin_candidates = (
            alpha_roi
            & ~mask_roi
            & (r > 188)
            & (g > 145)
            & (b > 130)
            & ((r - b) < 92)
            & ((r - g) < 72)
            & ((r - g) > 7)
            & ((g - b) > 3)
        )
        if int(skin_candidates.sum()) < 64:
            skin_candidates = alpha_roi & ~mask_roi & (r > 170) & (g > 120) & (b > 110)
        median = np.median(source_roi[skin_candidates], axis=0) if int(skin_candidates.sum()) else np.array([244, 218, 205])
        skin_field = source_roi.copy()
        skin_field[~skin_candidates] = median
        skin_field[mask_roi] = median
        skin_field = cv2.GaussianBlur(skin_field.astype(np.uint8), (0, 0), 19).astype(np.float32)

        yy = np.linspace(-1.0, 1.0, skin_field.shape[0], dtype=np.float32)[:, None]
        vertical = np.dstack([np.full_like(yy, 5.0), np.full_like(yy, 1.0), np.full_like(yy, -1.5)])
        skin_field = np.clip(skin_field + vertical, 0, 255)
        feather = cv2.GaussianBlur((mask_roi.astype(np.uint8) * 255), (0, 0), 4).astype(np.float32) / 255.0
        feather = np.clip(feather[:, :, None], 0, 1)
        roi = source_roi * (1 - feather) + skin_field * feather
        result[top:bottom, left:right] = roi
    out = np.dstack([np.clip(result, 0, 255).astype(np.uint8), rgba[:, :, 3]])
    return Image.fromarray(out, "RGBA")


def create_underpaint_layer(clean_face: Image.Image, side_mask: np.ndarray, feather_sigma: float) -> Image.Image:
    rgba = np.asarray(clean_face.convert("RGBA"), dtype=np.uint8).copy()
    soft = cv2.GaussianBlur((side_mask > 0).astype(np.uint8) * 255, (0, 0), feather_sigma)
    alpha = np.clip(soft.astype(np.float32) * 1.35, 0, 255).astype(np.uint8)
    alpha[side_mask == 0] = 0
    alpha = np.minimum(alpha, rgba[:, :, 3])
    rgba[:, :, 3] = alpha
    return Image.fromarray(rgba, "RGBA")


def grid_mesh(part_id: str, bbox: list[int], canvas_size: tuple[int, int], cols: int = 4, rows: int = 3) -> dict[str, Any]:
    x, y, w, h = bbox
    canvas_w, canvas_h = canvas_size
    vertices = []
    uvs = []
    for row in range(rows + 1):
        vy = y + h * row / rows
        for col in range(cols + 1):
            vx = x + w * col / cols
            vertices.append([round(vx, 3), round(vy, 3)])
            uvs.append([round(vx / canvas_w, 6), round(vy / canvas_h, 6)])
    triangles = []
    for row in range(rows):
        for col in range(cols):
            a = row * (cols + 1) + col
            b = a + 1
            c = a + cols + 1
            d = c + 1
            triangles.append([a, c, b])
            triangles.append([b, c, d])
    boundary = sorted(
        {
            index
            for index, (vx, vy) in enumerate(vertices)
            if abs(vx - x) < 0.001 or abs(vx - (x + w)) < 0.001 or abs(vy - y) < 0.001 or abs(vy - (y + h)) < 0.001
        }
    )
    return {
        "part_id": part_id,
        "vertices": vertices,
        "triangles": triangles,
        "uvs": uvs,
        "boundary_vertex_ids": boundary,
        "mesh_strategy": {
            "kind": "face_base_clean_underpaint_bbox_grid",
            "cols": cols,
            "rows": rows,
            "note": "Mini Cubism preview mesh only; rebuild in Cubism editor before production.",
        },
    }


def remove_generated_underpaint(character: dict[str, Any]) -> None:
    generated_ids = {"eye_L_closed_underpaint", "eye_R_closed_underpaint"}
    character["parts"] = [part for part in character["parts"] if part.get("id") not in generated_ids]
    character["meshes"] = [mesh for mesh in character["meshes"] if mesh.get("part_id") not in generated_ids]
    character["part_opacity_keyframes"] = [
        row for row in character.get("part_opacity_keyframes", []) if row.get("part_id") not in generated_ids
    ]
    for deformer in character.get("deformers", []):
        deformer["child_ids"] = [child for child in deformer.get("child_ids", []) if child not in generated_ids]


def add_closed_underpaint_parts(
    output_dir: Path,
    character: dict[str, Any],
    clean_face: Image.Image,
    masks: dict[str, Any],
    underpaint_feather: float,
) -> list[dict[str, Any]]:
    canvas_size = tuple(character["canvas_size"])
    created = []
    remove_generated_underpaint(character)
    head = next((deformer for deformer in character["deformers"] if deformer["id"] == "head_angle_warp"), None)
    for side, label, draw_order, parameter_id in [
        ("L", "왼쪽 감은 눈 밑색", 1024.5, "ParamEyeLOpen"),
        ("R", "오른쪽 감은 눈 밑색", 1032.5, "ParamEyeROpen"),
    ]:
        part_id = f"eye_{side}_closed_underpaint"
        layer = create_underpaint_layer(clean_face, masks["sides"][side], underpaint_feather)
        source_path = f"parts/{part_id}.png"
        layer.save(output_dir / source_path)
        bbox = alpha_bbox(layer)
        part = {
            "id": part_id,
            "display_name": label,
            "source_path": source_path,
            "original_source_path": "generated from cleaned face_base eye mask",
            "bbox": bbox,
            "alpha_coverage": alpha_coverage(layer),
            "draw_order": draw_order,
            "folder": "Eyes",
            "deformer_node": "head_angle_warp",
            "material_group": f"eye_{side}",
            "risk_tags": ["generated_underpaint_candidate"],
        }
        mesh = grid_mesh(part_id, bbox, canvas_size)
        character["parts"].append(part)
        character["meshes"].append(mesh)
        character.setdefault("part_opacity_keyframes", []).append(
            {
                "part_id": part_id,
                "parameter_id": parameter_id,
                "mode": "linear",
                "purpose": "closed eye clean underpaint candidate",
                "keyframes": [
                    {"value": 0, "opacity": 1},
                    {"value": 0.2, "opacity": 1},
                    {"value": 1, "opacity": 0},
                ],
            }
        )
        if head and part_id not in head["child_ids"]:
            face_index = head["child_ids"].index("face_base") + 1 if "face_base" in head["child_ids"] else len(head["child_ids"])
            head["child_ids"].insert(face_index, part_id)
        created.append(part)
    character["parts"].sort(key=lambda part: float(part["draw_order"]))
    return created


def write_debug_masks(output_dir: Path, full_mask: np.ndarray, masks: dict[str, Any]) -> dict[str, str]:
    debug_dir = output_dir / "reports/face_base_clean_debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    Image.fromarray(full_mask).save(debug_dir / "eye_removal_mask_full.png")
    paths["full_mask"] = str(debug_dir / "eye_removal_mask_full.png")
    for side in ["L", "R"]:
        Image.fromarray(masks["sides"][side]).save(debug_dir / f"eye_removal_mask_{side}.png")
        paths[f"{side}_mask"] = str(debug_dir / f"eye_removal_mask_{side}.png")
    return paths


def build(
    source_dir: Path,
    output_dir: Path,
    dilate_px: int,
    bbox_pad: int,
    inpaint_radius: int,
    include_part_union_box: bool,
    cover_shape: str,
    fill_mode: str,
    preserve_face_base: bool,
    underpaint_feather: float,
    mask_source: str,
) -> dict[str, Any]:
    if not (source_dir / "character.json").exists():
        raise SystemExit(f"Missing character.json: {source_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, output_dir, dirs_exist_ok=True)

    character = load_json(output_dir / "character.json")
    rig = load_json(output_dir / "mini_rig.json") if (output_dir / "mini_rig.json").exists() else {}
    face_base_part = next(part for part in character["parts"] if part["id"] == "face_base")
    face_path = output_dir / face_base_part["source_path"]
    original_face = Image.open(face_path).convert("RGBA")
    full_mask, masks = build_eye_masks(
        output_dir,
        character,
        rig,
        dilate_px=dilate_px,
        bbox_pad=bbox_pad,
        include_part_union_box=include_part_union_box,
        cover_shape=cover_shape,
        mask_source=mask_source,
    )
    if fill_mode == "skin":
        clean_face = synthesize_skin_face_base(original_face, masks)
    else:
        clean_face = inpaint_face_base(original_face, full_mask, inpaint_radius)
    if not preserve_face_base:
        clean_face.save(face_path)
        face_base_part["original_source_path"] = str(source_dir / face_base_part["source_path"])
        face_base_part.setdefault("risk_tags", [])
        if "face_base_clean_candidate" not in face_base_part["risk_tags"]:
            face_base_part["risk_tags"].append("face_base_clean_candidate")
    created_underpaints = add_closed_underpaint_parts(output_dir, character, clean_face, masks, underpaint_feather)
    mask_paths = write_debug_masks(output_dir, full_mask, masks)

    character.setdefault("notes", []).append(
        "face_base_clean_v1 removes baked open-eye pixels before closed-eye rig tuning; visual review is still required."
    )
    write_json(output_dir / "character.json", character)
    report = {
        "schema_version": 1,
        "status": "GENERATED_CANDIDATE_REQUIRES_VISUAL_REVIEW",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_project": str(source_dir),
        "output_project": str(output_dir),
        "method": {
            "face_base": "Preserved original face_base; clean pixels are generated for closed underpaint only."
            if preserve_face_base
            else "Generated clean face_base over eye part alpha masks plus optional manual cover seed shape.",
            "closed_underpaint": "Transparent full-canvas layers copied from cleaned face_base using the same side-specific eye removal masks.",
            "dilate_px": dilate_px,
            "bbox_pad": bbox_pad,
            "inpaint_radius": inpaint_radius,
            "include_part_union_box": include_part_union_box,
            "cover_shape": cover_shape,
            "fill_mode": fill_mode,
            "preserve_face_base": preserve_face_base,
            "underpaint_feather": underpaint_feather,
            "mask_source": mask_source,
        },
        "mask": masks["meta"],
        "debug_masks": mask_paths,
        "created_underpaint_parts": created_underpaints,
        "decision_gate": "Do not promote until closed-eye screenshot review confirms no open-eye remnants or rectangular skin blocks.",
    }
    write_json(output_dir / "reports/face_base_clean_rebuild_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dilate-px", type=int, default=8)
    parser.add_argument("--bbox-pad", type=int, default=8)
    parser.add_argument("--inpaint-radius", type=int, default=7)
    parser.add_argument("--include-part-union-box", action="store_true")
    parser.add_argument("--cover-shape", choices=["none", "ellipse", "box"], default="ellipse")
    parser.add_argument("--fill-mode", choices=["inpaint", "skin"], default="skin")
    parser.add_argument("--preserve-face-base", action="store_true")
    parser.add_argument("--underpaint-feather", type=float, default=4.0)
    parser.add_argument("--mask-source", choices=["eye_parts_plus_manual", "manual_only"], default="eye_parts_plus_manual")
    args = parser.parse_args()
    report = build(
        args.source.resolve(),
        args.output.resolve(),
        args.dilate_px,
        args.bbox_pad,
        args.inpaint_radius,
        args.include_part_union_box,
        args.cover_shape,
        args.fill_mode,
        args.preserve_face_base,
        args.underpaint_feather,
        args.mask_source,
    )
    print(json.dumps({"ok": True, "status": report["status"], "output_project": report["output_project"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

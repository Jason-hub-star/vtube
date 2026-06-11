#!/usr/bin/env python3
"""Build an Imagen input pack for clean sockets and eye/mouth keyposes."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
MATERIAL_DIR = ROOT / "experiments/cubism-v2-new-character-001/material_pack_v0"
SPEC_PATH = (
    ROOT
    / "experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/clean_socket_keypose_requirements.json"
)
DEFAULT_OUT = (
    ROOT
    / "experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/imagen_input_pack_v1"
)
DEFAULT_PROJECT = MATERIAL_DIR / "mini_cubism_project_material_face_detail_rebuild_v1"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def safe_copy(src: Path, dst: Path) -> str | None:
    if not src.exists():
        return None
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return str(dst)


def union_bbox(bboxes: list[list[int]], pad: int, canvas: tuple[int, int]) -> list[int]:
    width, height = canvas
    left = max(0, min(b[0] for b in bboxes) - pad)
    top = max(0, min(b[1] for b in bboxes) - pad)
    right = min(width, max(b[0] + b[2] for b in bboxes) + pad)
    bottom = min(height, max(b[1] + b[3] for b in bboxes) + pad)
    return [left, top, right - left, bottom - top]


def crop_bbox(image: Image.Image, bbox: list[int]) -> Image.Image:
    x, y, w, h = bbox
    return image.crop((x, y, x + w, y + h))


def draw_bbox_overlay(image: Image.Image, boxes: dict[str, list[int]], out_path: Path) -> None:
    overlay = image.convert("RGBA").copy()
    draw = ImageDraw.Draw(overlay)
    colors = {
        "eye_L": (0, 160, 255, 255),
        "eye_R": (0, 160, 255, 255),
        "mouth": (255, 90, 90, 255),
        "face": (80, 220, 130, 255),
    }
    font = ImageFont.load_default()
    for label, bbox in boxes.items():
        x, y, w, h = bbox
        color = colors.get(label, (255, 220, 0, 255))
        draw.rectangle((x, y, x + w, y + h), outline=color, width=4)
        draw.rectangle((x, max(0, y - 18), x + len(label) * 7 + 8, y), fill=(20, 24, 32, 220))
        draw.text((x + 4, max(0, y - 15)), label, fill=(255, 255, 255, 255), font=font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    overlay.save(out_path)


def make_mask(canvas: tuple[int, int], bbox: list[int], out_path: Path) -> None:
    image = Image.new("L", canvas, 0)
    draw = ImageDraw.Draw(image)
    x, y, w, h = bbox
    draw.rectangle((x, y, x + w, y + h), fill=255)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)


def make_mask_crop(bbox: list[int], out_path: Path) -> None:
    _, _, w, h = bbox
    image = Image.new("L", (w, h), 255)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)


def part_map(project: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {part["id"]: part for part in project["parts"]}


def derive_rois(project: dict[str, Any], rig: dict[str, Any]) -> dict[str, list[int]]:
    canvas = tuple(project["canvas_size"])
    parts = part_map(project)
    eye_l_ids = [
        "eye_L_white",
        "eye_L_iris",
        "eye_L_pupil",
        "eye_L_highlight",
        "eye_L_upper_lash",
        "eye_L_lower_lash",
        "eye_L_closed_lid",
    ]
    eye_r_ids = [part_id.replace("eye_L", "eye_R") for part_id in eye_l_ids]
    mouth_ids = [
        "mouth_line",
        "mouth_inner",
        "mouth_upper_lip_mask",
        "mouth_lower_lip_mask",
        "mouth_teeth",
        "mouth_tongue",
        "mouth_corner_L",
        "mouth_corner_R",
    ]
    face_ids = ["face_base", "face_shadow_L", "face_shadow_R", "cheek_L", "cheek_R", "nose"]
    rois = {
        "eye_L": union_bbox([parts[part_id]["bbox"] for part_id in eye_l_ids if part_id in parts], 56, canvas),
        "eye_R": union_bbox([parts[part_id]["bbox"] for part_id in eye_r_ids if part_id in parts], 56, canvas),
        "mouth": union_bbox([parts[part_id]["bbox"] for part_id in mouth_ids if part_id in parts], 64, canvas),
        "face": union_bbox([parts[part_id]["bbox"] for part_id in face_ids if part_id in parts], 24, canvas),
    }
    covers = rig.get("eye_socket_covers") or {}
    if covers.get("L", {}).get("bbox"):
        rois["manual_eye_L_bbox"] = covers["L"]["bbox"]
    if covers.get("R", {}).get("bbox"):
        rois["manual_eye_R_bbox"] = covers["R"]["bbox"]
    return rois


def asset_roi(asset_id: str, rois: dict[str, list[int]]) -> tuple[str, list[int]]:
    if asset_id.startswith("eye_L_"):
        return "eye_L", rois["eye_L"]
    if asset_id.startswith("eye_R_"):
        return "eye_R", rois["eye_R"]
    if asset_id.startswith("mouth_"):
        return "mouth", rois["mouth"]
    return "face", rois["face"]


def prompt_for_asset(asset: dict[str, Any], spec: dict[str, Any]) -> str:
    prompts = spec["prompt_plan"]
    common = "\n".join(f"- {line}" for line in prompts["common_constraints"])
    kind = asset["kind"]
    if kind == "clean_base":
        task = (
            "Create a clean full face base material. Remove baked open-eye pixels and mouth remnants while preserving "
            "skin tone, blush, nose, cheek shading, face contour, and hair occlusion. This must be usable under all "
            "eye and mouth keyposes."
        )
    elif kind == "clean_socket" and asset["group"].startswith("eye"):
        task = prompts["eye_clean_socket_prompt"]
    elif kind == "eye_keypose":
        task = prompts["eye_keypose_prompt"]
    elif kind == "underpaint" and asset["group"].startswith("eye"):
        task = prompts["eye_clean_socket_prompt"] + " Make it a soft underpaint layer for closed-eye states."
    elif kind == "clean_socket" and asset["group"] == "mouth":
        task = prompts["mouth_clean_socket_prompt"]
    elif kind == "mouth_keypose":
        task = prompts["mouth_keypose_prompt"]
    else:
        task = prompts["detail_prompt"]
    return (
        f"Asset: {asset['asset_id']}\n"
        f"Korean name: {asset['ko']}\n"
        f"Target group: {asset['group']}\n"
        f"Target parameter: {', '.join(asset['param_targets'])}\n\n"
        "Common constraints:\n"
        f"{common}\n\n"
        "Task:\n"
        f"{task}\n\n"
        "Output requirements:\n"
        "- Preferred: 2048x2048 RGBA full-canvas transparent PNG aligned to the provided reference canvas.\n"
        "- If only a crop can be generated, keep the crop aspect ratio and include the ROI name in the filename; "
        "the normalization pipeline will place it into 2048x2048.\n"
        "- Do not create a sprite sheet. Do not include labels or guide marks.\n"
    )


def build_contact_sheet(crops: list[tuple[str, Image.Image]], out_path: Path) -> None:
    thumb_w, thumb_h = 360, 220
    sheet = Image.new("RGB", (thumb_w * 2, thumb_h * 2), (245, 242, 235))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, (label, crop) in enumerate(crops[:4]):
        x = (index % 2) * thumb_w
        y = (index // 2) * thumb_h
        thumb = crop.convert("RGB")
        thumb.thumbnail((thumb_w, thumb_h - 24), Image.Resampling.LANCZOS)
        sheet.paste(thumb, (x + (thumb_w - thumb.width) // 2, y + 24))
        draw.rectangle((x, y, x + thumb_w - 1, y + 24), fill=(20, 24, 32))
        draw.text((x + 6, y + 7), label, fill=(255, 255, 255), font=font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Imagen Clean Socket + Keypose Input Pack v1",
        "",
        f"- status: `{manifest['status']}`",
        f"- output_dir: `{manifest['output_dir']}`",
        f"- required assets: `{len(manifest['assets'])}`",
        "",
        "## Source References",
        "",
    ]
    for label, path in manifest["references"].items():
        lines.append(f"- `{label}`: `{path}`")
    lines += [
        "",
        "## ROI Boxes",
        "",
        "| ROI | bbox |",
        "|---|---:|",
    ]
    for label, bbox in manifest["rois"].items():
        lines.append(f"| {label} | `{bbox}` |")
    lines += [
        "",
        "## Asset Prompts",
        "",
        "| asset_id | roi | prompt | mask |",
        "|---|---|---|---|",
    ]
    for asset in manifest["assets"]:
        lines.append(
            f"| {asset['asset_id']} | `{asset['roi_name']}` | `{asset['prompt_path']}` | `{asset['full_mask_path']}` |"
        )
    lines += [
        "",
        "## Validation After Generation",
        "",
        "```bash",
        "python3 scripts/validate_cubism_v2_keypose_pngs.py \\",
        "  --input-dir /path/to/generated_pngs \\",
        "  --out experiments/cubism-v2-new-character-001/reports/clean_socket_keypose_requirements/generated_keypose_validation_report.json",
        "```",
        "",
        "Do not stretch-resize generated crops. Use ROI/anchor normalization into a 2048x2048 transparent canvas.",
        "",
    ]
    return "\n".join(lines)


def build(out_dir: Path, spec_path: Path, project_dir: Path) -> dict[str, Any]:
    spec = load_json(spec_path)
    project = load_json(project_dir / "character.json")
    rig = load_json(project_dir / "mini_rig.json") if (project_dir / "mini_rig.json").exists() else {}
    canvas = tuple(project["canvas_size"])
    source_canvas = MATERIAL_DIR / "canonical/candidate_002_2048_rgba.png"
    beige_canvas = MATERIAL_DIR / "canonical/canonical_on_beige.png"
    white_canvas = MATERIAL_DIR / "canonical/canonical_on_white.png"
    source = Image.open(source_canvas).convert("RGBA")
    rois = derive_rois(project, rig)

    refs_dir = out_dir / "references"
    crops_dir = out_dir / "roi_crops"
    masks_dir = out_dir / "masks"
    prompts_dir = out_dir / "prompts"
    refs = {
        "source_2048_rgba": safe_copy(source_canvas, refs_dir / "source_candidate_002_2048_rgba.png"),
        "source_on_beige": safe_copy(beige_canvas, refs_dir / "source_candidate_002_on_beige.png"),
        "source_on_white": safe_copy(white_canvas, refs_dir / "source_candidate_002_on_white.png"),
        "current_eye_close_failure": safe_copy(
            MATERIAL_DIR
            / "mini_cubism_project_material_closed_underpaint_manual_bbox_v1/reports/eye_mode_validation/eye_close_review_crop.png",
            refs_dir / "current_eye_close_failure_crop.png",
        ),
        "requirements": safe_copy(spec_path, refs_dir / "clean_socket_keypose_requirements.json"),
    }
    refs = {key: value for key, value in refs.items() if value is not None}

    draw_bbox_overlay(source, {k: v for k, v in rois.items() if k in {"eye_L", "eye_R", "mouth", "face"}}, refs_dir / "source_roi_overlay.png")

    crop_entries = []
    for label in ["eye_L", "eye_R", "mouth", "face"]:
        crop = crop_bbox(source, rois[label])
        crops_dir.mkdir(parents=True, exist_ok=True)
        crop.save(crops_dir / f"{label}_source_crop.png")
        crop_entries.append((label, crop))
        make_mask(canvas, rois[label], masks_dir / f"{label}_full_canvas_mask.png")
        make_mask_crop(rois[label], masks_dir / f"{label}_crop_mask.png")
    build_contact_sheet(crop_entries, refs_dir / "roi_crop_contact_sheet.png")

    asset_entries = []
    for asset in spec["required_assets"]:
        roi_name, roi_bbox = asset_roi(asset["asset_id"], rois)
        prompt_text = prompt_for_asset(asset, spec)
        prompt_path = prompts_dir / f"{asset['asset_id']}.md"
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt_text, encoding="utf-8")
        write_json(
            prompts_dir / f"{asset['asset_id']}.json",
            {
                "asset": asset,
                "roi_name": roi_name,
                "roi_bbox": roi_bbox,
                "prompt": prompt_text,
                "input_references": {
                    "source_2048_rgba": str(refs_dir / "source_candidate_002_2048_rgba.png"),
                    "roi_crop": str(crops_dir / f"{roi_name}_source_crop.png"),
                    "full_canvas_mask": str(masks_dir / f"{roi_name}_full_canvas_mask.png"),
                    "crop_mask": str(masks_dir / f"{roi_name}_crop_mask.png"),
                },
                "post_generation_validation": "python3 scripts/validate_cubism_v2_keypose_pngs.py --input-dir /path/to/generated_pngs",
            },
        )
        asset_entries.append(
            {
                "asset_id": asset["asset_id"],
                "roi_name": roi_name,
                "roi_bbox": roi_bbox,
                "prompt_path": str(prompt_path),
                "prompt_json_path": str(prompts_dir / f"{asset['asset_id']}.json"),
                "roi_crop_path": str(crops_dir / f"{roi_name}_source_crop.png"),
                "full_mask_path": str(masks_dir / f"{roi_name}_full_canvas_mask.png"),
                "crop_mask_path": str(masks_dir / f"{roi_name}_crop_mask.png"),
            }
        )

    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS_INPUT_PACK_READY",
        "output_dir": str(out_dir),
        "source_project": str(project_dir),
        "references": refs,
        "rois": rois,
        "assets": asset_entries,
        "official_context": {
            "live2d_material_separation": "https://docs.live2d.com/en/cubism-editor-manual/divide-the-material/",
            "live2d_psd_import": "https://docs.live2d.com/en/cubism-editor-manual/psd-import/",
            "imagen_edit_reference": "https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-reference/imagen-api-edit",
        },
    }
    write_json(out_dir / "imagen_input_pack_manifest.json", manifest)
    (out_dir / "README.md").write_text(markdown(manifest), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--spec", type=Path, default=SPEC_PATH)
    parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT)
    args = parser.parse_args()
    manifest = build(args.out.resolve(), args.spec.resolve(), args.project.resolve())
    print(
        json.dumps(
            {"ok": True, "status": manifest["status"], "out": manifest["output_dir"], "assets": len(manifest["assets"])},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build See-through 70+ custom split v2 candidates, then run QA gate."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from build_mini_cubism_dedicated_model_v1 import CANVAS, GROUP_FOLDERS
from build_mini_cubism_targeted_split_v1 import (
    bbox_alpha,
    draw_order_for,
    group_for_part,
    targeted_image,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = ROOT / "experiments/mini-cubism-dedicated-model-v1-001"
PRIMARY_MPS_CASE = "mps_640_safe"
FALLBACK_MPS_CASE = "mps_512_safe"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def layer_by_original(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for layer in manifest.get("layers", []):
        original = layer.get("original_part_id")
        if original and layer.get("output_path"):
            result[original] = layer
    return result


def font(size: int) -> ImageFont.ImageFont:
    for candidate in [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def mps_case_status(exp: Path) -> dict[str, Any]:
    primary_report = exp / "reports" / f"{PRIMARY_MPS_CASE}_inference_report.json"
    fallback_report = exp / "reports" / f"{FALLBACK_MPS_CASE}_inference_report.json"
    primary = load_json(primary_report) if primary_report.exists() else None
    fallback = load_json(fallback_report) if fallback_report.exists() else None
    comfy_output = ROOT / "experiments/see-through-layer-decomp-001/external_repos/ComfyUI/output"
    primary_layers = sorted(comfy_output.glob("mini_cubism_dedicated_v1_mps_640_safe_*_layers.json"), key=lambda item: item.stat().st_mtime, reverse=True) if comfy_output.exists() else []
    if primary and primary.get("status") in {"COMPLETED", "PASS_RUNNER", "PASS_NORMALIZED"}:
        return {"primary_case": PRIMARY_MPS_CASE, "status": "PRIMARY_640_EVIDENCE_PRESENT", "report": str(primary_report)}
    if primary_layers:
        return {
            "primary_case": PRIMARY_MPS_CASE,
            "status": "PRIMARY_640_LAYERS_JSON_PRESENT_WITH_INCOMPLETE_RUN_REPORT",
            "layers_json": str(primary_layers[0]),
            "report": str(primary_report) if primary_report.exists() else None,
        }
    if fallback:
        return {"primary_case": PRIMARY_MPS_CASE, "status": "PRIMARY_640_MISSING_USING_512_EXISTING_FALLBACK", "fallback_case": FALLBACK_MPS_CASE, "report": str(fallback_report)}
    return {"primary_case": PRIMARY_MPS_CASE, "status": "NO_MPS_REPORT_FOUND_BUILDING_FROM_EXISTING_LAYER_MANIFEST"}


def preview_tile(path: Path, tile: int = 180) -> Image.Image:
    img = Image.open(path).convert("RGBA")
    bbox = img.getchannel("A").getbbox()
    crop = img.crop(bbox) if bbox else Image.new("RGBA", (tile, tile), (0, 0, 0, 0))
    crop.thumbnail((tile, tile), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (tile, tile), "#f8f6f0")
    canvas.paste(crop.convert("RGB"), ((tile - crop.width) // 2, (tile - crop.height) // 2), crop)
    return canvas


def build_contact_sheet(layers: list[dict[str, Any]], out: Path) -> None:
    cols = 5
    cell_w, cell_h = 236, 260
    header_h = 76
    rows = (len(layers) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, header_h + rows * cell_h), "#f4f0e8")
    draw = ImageDraw.Draw(sheet)
    draw.text((18, 14), "See-through 70+ Custom Split v2 Candidates", fill="#202124", font=font(24))
    draw.text((18, 46), "QA-first candidate sheet; visual QA must pass before Mini Cubism project promotion.", fill="#5f6368", font=font(13))
    small = font(11)
    for index, layer in enumerate(layers):
        x = (index % cols) * cell_w
        y = header_h + (index // cols) * cell_h
        draw.rectangle([x + 8, y + 8, x + cell_w - 8, y + cell_h - 8], fill="#ffffff", outline="#d5cec4")
        tile = preview_tile(Path(layer["output_path"]))
        sheet.paste(tile, (x + 28, y + 18))
        draw.text((x + 14, y + 200), layer["part_id"][:29], fill="#202124", font=small)
        draw.text((x + 14, y + 216), layer["group"], fill="#5f6368", font=small)
        draw.text((x + 14, y + 232), layer["derivation_mode"][:32], fill="#2f6fbb", font=small)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def build_candidate(exp: Path) -> dict[str, Any]:
    spec = load_json(exp / "part_spec_manifest.json")
    source_manifest = load_json(exp / "layer_manifest.json")
    part_groups = spec["part_groups"]
    source_by_original = layer_by_original(source_manifest)
    out_dir = exp / "seethrough_70_custom_split_v2"
    parts_dir = out_dir / "parts"
    report_dir = out_dir / "reports"
    parts_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    layers: list[dict[str, Any]] = []
    all_parts = [part for group in part_groups.values() for part in group]
    for index, part_id in enumerate(all_parts):
        group = group_for_part(part_id, part_groups)
        image, derivation_mode, source_id = targeted_image(part_id, source_by_original)
        bbox, coverage, nonzero = bbox_alpha(image)
        output_path = parts_dir / f"{part_id}.png"
        image.save(output_path)
        if nonzero == 0:
            derivation_mode = "empty_candidate"
        layers.append(
            {
                "part_id": part_id,
                "layer_name": f"seethrough_70_custom_split_v2__{part_id}",
                "original_part_id": part_id,
                "group": group,
                "folder": GROUP_FOLDERS[group],
                "role": group,
                "source_original_part_id": source_id,
                "source_manifest": str(exp / "layer_manifest.json"),
                "output_path": str(output_path),
                "canvas_size": CANVAS,
                "bbox": bbox,
                "alpha_coverage": coverage,
                "draw_order": draw_order_for(group, index),
                "include_in_import_psd": False,
                "production_candidate": False,
                "status": "QA_REQUIRED_BEFORE_PROMOTION",
                "derivation_mode": derivation_mode,
                "qa_policy": "critical face/eye/mouth generated/procedural/fallback parts must fail visual gate",
            }
        )

    mouth_visibility = {
        "parameter_id": "ParamMouthOpenY",
        "states": {
            "0": ["mouth_closed_line"],
            "0.5": ["mouth_half_outer", "mouth_half_inner"],
            "1": ["mouth_open_outer", "mouth_open_inner", "mouth_teeth_upper", "mouth_tongue", "mouth_shadow"],
        },
    }
    eye_hidden = ["iris_L", "iris_R", "pupil_L", "pupil_R", "catchlight_L", "catchlight_R"]
    counts = {
        "parts": len(layers),
        "hair_parts": len(part_groups["hair_physics"]),
        "eye_parts": len(part_groups["eyes_keypose"]),
        "mouth_parts": len(part_groups["mouth_keypose"]),
        "physics_targets": len(
            set(part_groups["hair_physics"])
            | set(part_groups["clothes_accessory_physics"])
            | {part for part in part_groups["face_ear"] if part.startswith("ear_")}
        ),
        "from_seethrough_masks": sum(1 for item in layers if item["derivation_mode"] == "targeted_mask_from_seethrough"),
        "generated_or_fallback_candidates": sum(1 for item in layers if any(token in item["derivation_mode"] for token in ["generated", "fallback", "procedural"])),
    }
    manifest = {
        "schema_version": 2,
        "experiment_id": exp.name,
        "generated_at": now(),
        "source_canonical": str(exp / "canonical/canonical_front_2048.png"),
        "source_layer_manifest": str(exp / "layer_manifest.json"),
        "source_part_spec_manifest": str(exp / "part_spec_manifest.json"),
        "targeted_split_dir": str(out_dir),
        "canvas_size": CANVAS,
        "mps_primary_case": PRIMARY_MPS_CASE,
        "mps_fallback_case": FALLBACK_MPS_CASE,
        "mps_case_status": mps_case_status(exp),
        "layers": layers,
        "part_groups": part_groups,
        "mouth_visibility_groups": mouth_visibility,
        "eye_closed_hidden_parts": eye_hidden,
        "counts": counts,
        "status": "BUILT_PENDING_QA",
        "interpretation": [
            "This v2 candidate preserves existing evidence and applies a stricter QA gate before project promotion.",
            "640 MPS is the primary intended See-through case; 512 is fallback evidence only.",
            "Face/eye/mouth generated candidates are not production success and must be caught by QA.",
        ],
    }
    write_json(out_dir / "candidate_layer_manifest.json", manifest)
    write_json(report_dir / "seethrough_70_custom_split_v2_build_report.json", manifest)
    build_contact_sheet(layers, report_dir / "candidate_contact_sheet.png")
    return manifest


def run_qa(exp: Path, manifest_path: Path) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "validate_seethrough_70_custom_split_v2.py"),
        "--experiment",
        str(exp),
        "--manifest",
        str(manifest_path),
    ]
    completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    return {
        "command": cmd,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
        "status": "PASS_QA" if completed.returncode == 0 else "QA_REVISE_OR_FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build See-through 70+ custom split v2 candidate and run strict QA.")
    parser.add_argument("--experiment", default=str(DEFAULT_EXPERIMENT))
    parser.add_argument("--skip-qa", action="store_true")
    args = parser.parse_args()

    exp = Path(args.experiment).resolve()
    manifest = build_candidate(exp)
    manifest_path = exp / "seethrough_70_custom_split_v2" / "candidate_layer_manifest.json"
    qa = {"status": "SKIPPED"} if args.skip_qa else run_qa(exp, manifest_path)
    summary = {
        "ok": qa.get("status") == "PASS_QA",
        "manifest": str(manifest_path),
        "counts": manifest["counts"],
        "mps_case_status": manifest["mps_case_status"],
        "qa": qa,
        "next_action": "Build Mini Cubism project only after QA PASS." if qa.get("status") == "PASS_QA" else "Do not promote; inspect QA problem sheets and retry ROI/keypose generation.",
    }
    write_json(exp / "seethrough_70_custom_split_v2" / "reports" / "build_and_qa_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if qa.get("status") == "PASS_QA" else 1


if __name__ == "__main__":
    raise SystemExit(main())

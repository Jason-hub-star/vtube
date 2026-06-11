#!/usr/bin/env python3
"""Repair the Cubism v2 material pack neutral composite toward the canonical PNG."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = ROOT / "experiments/cubism-v2-new-character-001/material_pack_v0"
MANIFEST_PATH = PACK_DIR / "layer_manifest.json"
CANONICAL_PATH = PACK_DIR / "canonical/candidate_002_2048_rgba.png"
REPAIRED_DIR = PACK_DIR / "production_layers_neutral_repair_v1"
REPORTS_DIR = PACK_DIR / "reports"
REPAIR_DIR = REPORTS_DIR / "neutral_repair"

NEUTRAL_HIDDEN_PARTS = {
    "eye_L_closed_lid",
    "eye_R_closed_lid",
    "mouth_inner",
    "mouth_teeth",
    "mouth_tongue",
    "mouth_upper_lip_mask",
    "mouth_lower_lip_mask",
    "mouth_corner_L",
    "mouth_corner_R",
}

MOUTH_OPEN_PARTS = {
    "mouth_inner",
    "mouth_teeth",
    "mouth_tongue",
    "mouth_upper_lip_mask",
    "mouth_lower_lip_mask",
    "mouth_corner_L",
    "mouth_corner_R",
}

CLOSED_LID_PARAMS = {
    "eye_L_closed_lid": "ParamEyeLOpen",
    "eye_R_closed_lid": "ParamEyeROpen",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def resolve(path_value: str) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_layer_arrays(layers: list[dict[str, Any]]) -> dict[str, np.ndarray]:
    arrays: dict[str, np.ndarray] = {}
    for layer in layers:
        if not layer.get("include_in_import_psd"):
            continue
        image = Image.open(resolve(layer["output_path"])).convert("RGBA")
        arrays[layer["part_id"]] = np.array(image)
    return arrays


def composite(
    layers: list[dict[str, Any]],
    arrays: dict[str, np.ndarray],
    hidden: set[str],
    size: tuple[int, int],
) -> tuple[np.ndarray, np.ndarray]:
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    owner = np.full((size[1], size[0]), "", dtype=object)
    for layer in sorted([item for item in layers if item.get("include_in_import_psd")], key=lambda item: int(item.get("draw_order", 500))):
        part_id = layer["part_id"]
        if part_id in hidden:
            continue
        array = arrays[part_id]
        alpha_mask = array[:, :, 3] > 0
        owner[alpha_mask] = part_id
        canvas.alpha_composite(Image.fromarray(array, "RGBA"))
    return np.array(canvas), owner


def score(canonical: np.ndarray, current: np.ndarray) -> dict[str, Any]:
    visible = (canonical[:, :, 3] > 5) | (current[:, :, 3] > 5)
    rgb_diff = np.abs(canonical[:, :, :3].astype(int) - current[:, :, :3].astype(int)).mean(axis=2)
    alpha_diff = np.abs(canonical[:, :, 3].astype(int) - current[:, :, 3].astype(int))
    bad = visible & ((rgb_diff > 35) | (alpha_diff > 35))
    missing = (canonical[:, :, 3] > 5) & (current[:, :, 3] <= 5)
    extra = (current[:, :, 3] > 5) & (canonical[:, :, 3] <= 5)
    return {
        "visible_pixels": int(visible.sum()),
        "bad_pixels": int(bad.sum()),
        "bad_ratio_visible": round(float(bad.sum() / max(1, visible.sum())), 6),
        "missing_pixels": int(missing.sum()),
        "extra_pixels": int(extra.sum()),
    }


def diff_masks(canonical: np.ndarray, current: np.ndarray) -> dict[str, np.ndarray]:
    visible = (canonical[:, :, 3] > 5) | (current[:, :, 3] > 5)
    rgb_diff = np.abs(canonical[:, :, :3].astype(int) - current[:, :, :3].astype(int)).mean(axis=2)
    alpha_diff = np.abs(canonical[:, :, 3].astype(int) - current[:, :, 3].astype(int))
    bad = visible & ((rgb_diff > 35) | (alpha_diff > 35))
    missing = (canonical[:, :, 3] > 5) & (current[:, :, 3] <= 5)
    extra = (current[:, :, 3] > 5) & (canonical[:, :, 3] <= 5)
    return {"bad": bad, "missing": missing, "extra": extra}


def make_diff_overlay(canonical: np.ndarray, current: np.ndarray) -> Image.Image:
    overlay = canonical.copy()
    masks = diff_masks(canonical, current)
    overlay[masks["bad"]] = [255, 0, 0, 220]
    overlay[masks["missing"]] = [0, 80, 255, 220]
    overlay[masks["extra"]] = [255, 210, 0, 220]
    return Image.fromarray(overlay.astype(np.uint8), "RGBA")


def part_problem_contributions(
    layers: list[dict[str, Any]],
    arrays: dict[str, np.ndarray],
    canonical: np.ndarray,
    current: np.ndarray,
    owner: np.ndarray,
) -> list[dict[str, Any]]:
    masks = diff_masks(canonical, current)
    yy, xx = np.indices(masks["bad"].shape)
    rows: list[dict[str, Any]] = []
    for layer in layers:
        if not layer.get("include_in_import_psd"):
            continue
        part_id = layer["part_id"]
        alpha = arrays[part_id][:, :, 3] > 5
        bad_owned = masks["bad"] & (owner == part_id)
        extra_owned = masks["extra"] & (owner == part_id)
        # Missing pixels do not have an owner in the composite, so attribute them
        # to layers whose declared bbox could plausibly contain the missing region.
        missing_in_bbox = masks["missing"] & bbox_contains(layer, xx, yy)
        total = int(bad_owned.sum() + extra_owned.sum() + missing_in_bbox.sum())
        if total <= 0:
            continue
        rows.append(
            {
                "part_id": part_id,
                "draw_order": int(layer.get("draw_order", 500)),
                "source_type": layer.get("source_type"),
                "alpha_pixels": int(alpha.sum()),
                "bad_owned_pixels": int(bad_owned.sum()),
                "extra_owned_pixels": int(extra_owned.sum()),
                "missing_in_bbox_pixels": int(missing_in_bbox.sum()),
                "problem_score_pixels": total,
            }
        )
    return sorted(rows, key=lambda item: item["problem_score_pixels"], reverse=True)


def bbox_contains(layer: dict[str, Any], x: np.ndarray, y: np.ndarray) -> np.ndarray:
    bx, by, bw, bh = layer.get("bbox_actual") or layer.get("bbox") or [0, 0, 0, 0]
    pad = 12
    return (x >= bx - pad) & (x < bx + bw + pad) & (y >= by - pad) & (y < by + bh + pad)


def repair_arrays(layers: list[dict[str, Any]], arrays: dict[str, np.ndarray], canonical: np.ndarray) -> dict[str, np.ndarray]:
    repaired = {part_id: array.copy() for part_id, array in arrays.items()}
    canonical_alpha_visible = canonical[:, :, 3] > 0

    # First, remove obvious pixels outside the canonical silhouette and set neutral pixels
    # to canonical color inside the current alpha. This keeps full-canvas coordinates
    # intact while reducing gray/flat source artifacts.
    for layer in layers:
        if not layer.get("include_in_import_psd"):
            continue
        part_id = layer["part_id"]
        array = repaired[part_id]
        alpha = array[:, :, 3] > 0
        array[alpha & canonical_alpha_visible, :3] = canonical[alpha & canonical_alpha_visible, :3]
        array[alpha & ~canonical_alpha_visible, 3] = 0

    current, owner = composite(layers, repaired, NEUTRAL_HIDDEN_PARTS, (canonical.shape[1], canonical.shape[0]))
    masks = diff_masks(canonical, current)

    # If the top visible part is wrong, make that exact part carry the canonical pixel
    # in neutral. This is a conservative local preview repair, not final ArtMesh design.
    for part_id, array in repaired.items():
        if part_id in NEUTRAL_HIDDEN_PARTS:
            continue
        part_owner_bad = masks["bad"] & (owner == part_id)
        if part_owner_bad.any():
            array[part_owner_bad] = canonical[part_owner_bad]
        part_owner_extra = masks["extra"] & (owner == part_id)
        if part_owner_extra.any():
            array[part_owner_extra, 3] = 0

    # Assign missing canonical pixels to the highest draw-order neutral-visible layer
    # whose design bbox contains the pixel. This patches mask holes without adding a
    # synthetic one-piece overlay.
    current, owner = composite(layers, repaired, NEUTRAL_HIDDEN_PARTS, (canonical.shape[1], canonical.shape[0]))
    missing = diff_masks(canonical, current)["missing"]
    yy, xx = np.indices(missing.shape)
    candidate_layers = [
        layer
        for layer in sorted(layers, key=lambda item: int(item.get("draw_order", 500)), reverse=True)
        if layer.get("include_in_import_psd")
        and layer["part_id"] not in NEUTRAL_HIDDEN_PARTS
        and layer.get("source_type") != "UNDERPAINT"
    ]
    remaining = missing.copy()
    for layer in candidate_layers:
        part_id = layer["part_id"]
        target = remaining & bbox_contains(layer, xx, yy)
        if target.any():
            repaired[part_id][target] = canonical[target]
            remaining[target] = False
        if not remaining.any():
            break

    # Fall back to broad base layers for any remaining holes.
    fallback_ids = ["face_base", "hair_back_base", "torso_base", "chest_cloth_base", "neck"]
    for part_id in fallback_ids:
        if not remaining.any() or part_id not in repaired:
            continue
        repaired[part_id][remaining] = canonical[remaining]
        remaining[:] = False

    # Final neutral partition cleanup: if a pixel still differs, make the
    # topmost owner carry the canonical pixel and suppress lower overlaps at
    # that same pixel. This keeps the repaired neutral composite visually close
    # to the source without creating a one-piece overlay layer.
    current, owner = composite(layers, repaired, NEUTRAL_HIDDEN_PARTS, (canonical.shape[1], canonical.shape[0]))
    final_masks = diff_masks(canonical, current)
    problem = final_masks["bad"] | final_masks["extra"] | final_masks["missing"]
    if problem.any():
        for part_id, array in repaired.items():
            if part_id in NEUTRAL_HIDDEN_PARTS:
                continue
            owned = problem & (owner == part_id)
            lower_overlap = problem & (owner != part_id) & (array[:, :, 3] > 0)
            if owned.any():
                array[owned] = canonical[owned]
                transparent = owned & (canonical[:, :, 3] <= 40)
                array[transparent, 3] = 0
            if lower_overlap.any():
                array[lower_overlap, 3] = 0
        current, owner = composite(layers, repaired, NEUTRAL_HIDDEN_PARTS, (canonical.shape[1], canonical.shape[0]))
        remaining_missing = diff_masks(canonical, current)["missing"]
        if remaining_missing.any() and "face_base" in repaired:
            repaired["face_base"][remaining_missing] = canonical[remaining_missing]

    return repaired


def part_opacity_keyframes() -> list[dict[str, Any]]:
    keyframes: list[dict[str, Any]] = []
    for part_id, parameter_id in CLOSED_LID_PARAMS.items():
        keyframes.append(
            {
                "part_id": part_id,
                "parameter_id": parameter_id,
                "mode": "linear",
                "keyframes": [
                    {"value": 0, "opacity": 1},
                    {"value": 0.2, "opacity": 1},
                    {"value": 1, "opacity": 0},
                ],
            }
        )
    for part_id in sorted(MOUTH_OPEN_PARTS):
        keyframes.append(
            {
                "part_id": part_id,
                "parameter_id": "ParamMouthOpenY",
                "mode": "linear",
                "keyframes": [
                    {"value": 0, "opacity": 0},
                    {"value": 0.25, "opacity": 0},
                    {"value": 1, "opacity": 1},
                ],
            }
        )
    return keyframes


def update_bbox_metadata(layer: dict[str, Any], array: np.ndarray) -> None:
    alpha = Image.fromarray(array[:, :, 3], "L")
    bbox = alpha.getbbox()
    if bbox is None:
        layer["bbox_actual"] = [0, 0, 0, 0]
        layer["alpha_coverage"] = 0
        return
    left, top, right, bottom = bbox
    nonzero = int((array[:, :, 3] > 0).sum())
    layer["bbox_actual"] = [left, top, right - left, bottom - top]
    layer["alpha_coverage"] = round(nonzero / (array.shape[0] * array.shape[1]), 8)


def main() -> int:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    REPAIR_DIR.mkdir(parents=True, exist_ok=True)
    REPAIRED_DIR.mkdir(parents=True, exist_ok=True)

    backup = MANIFEST_PATH.with_name("layer_manifest.before_neutral_repair_v1.json")
    source_manifest_path = backup if backup.exists() else MANIFEST_PATH
    manifest = load_json(source_manifest_path)
    layers = manifest["layers"]
    canonical_image = Image.open(CANONICAL_PATH).convert("RGBA")
    canonical = np.array(canonical_image)
    arrays = load_layer_arrays(layers)

    before_all, before_all_owner = composite(layers, arrays, set(), canonical_image.size)
    before_neutral, _ = composite(layers, arrays, NEUTRAL_HIDDEN_PARTS, canonical_image.size)
    before_all_score = score(canonical, before_all)
    before_neutral_score = score(canonical, before_neutral)
    before_problem_parts = part_problem_contributions(layers, arrays, canonical, before_all, before_all_owner)

    Image.fromarray(before_all.astype(np.uint8), "RGBA").save(REPAIR_DIR / "neutral_composite_before.png")
    make_diff_overlay(canonical, before_all).save(REPAIR_DIR / "neutral_diff_overlay_before.png")

    repaired_arrays = repair_arrays(layers, arrays, canonical)

    repaired_manifest = manifest.copy()
    repaired_manifest["status"] = "NEUTRAL_REPAIR_V1_APPLIED"
    repaired_manifest["neutral_visibility"] = {
        "hidden_at_neutral": sorted(NEUTRAL_HIDDEN_PARTS),
        "policy": "Auxiliary blink/open-mouth parts are hidden at neutral through Mini Cubism part_opacity_keyframes.",
    }
    repaired_manifest["part_opacity_keyframes"] = part_opacity_keyframes()
    repaired_manifest["neutral_repair"] = {
        "schema_version": 1,
        "applied_at": now(),
        "repaired_layer_dir": rel(REPAIRED_DIR),
        "method": "clip outside canonical alpha, recolor visible pixels to canonical RGB, patch missing neutral pixels into existing semantic source layers",
    }

    for layer in repaired_manifest["layers"]:
        if not layer.get("include_in_import_psd"):
            continue
        part_id = layer["part_id"]
        repaired_path = REPAIRED_DIR / Path(layer["output_path"]).name
        Image.fromarray(repaired_arrays[part_id].astype(np.uint8), "RGBA").save(repaired_path)
        layer["pre_neutral_repair_output_path"] = layer["output_path"]
        layer["output_path"] = rel(repaired_path)
        update_bbox_metadata(layer, repaired_arrays[part_id])
        notes = layer.get("notes") or ""
        layer["notes"] = f"{notes} Neutral repair v1 adjusted alpha/RGB for canonical neutral composite.".strip()

    # Preserve the previous manifest once, then write the repaired manifest in-place.
    if not backup.exists():
        shutil.copy2(MANIFEST_PATH, backup)
    write_json(MANIFEST_PATH, repaired_manifest)

    after_arrays = load_layer_arrays(repaired_manifest["layers"])
    after_neutral, _ = composite(repaired_manifest["layers"], after_arrays, NEUTRAL_HIDDEN_PARTS, canonical_image.size)
    after_score = score(canonical, after_neutral)
    Image.fromarray(after_neutral.astype(np.uint8), "RGBA").save(REPAIR_DIR / "neutral_composite_after.png")
    make_diff_overlay(canonical, after_neutral).save(REPAIR_DIR / "neutral_diff_overlay_after.png")

    report = {
        "schema_version": 1,
        "status": "PASS_NEUTRAL_REPAIR_V1" if after_score["bad_ratio_visible"] <= 0.10 else "REVISE_NEUTRAL_REPAIR_V1",
        "generated_at": now(),
        "canonical": str(CANONICAL_PATH),
        "manifest": str(MANIFEST_PATH),
        "manifest_backup": str(backup),
        "hidden_at_neutral": sorted(NEUTRAL_HIDDEN_PARTS),
        "problem_part_contributions": {
            "basis": "before_all_visible draw-order composite; bad/extra pixels are attributed to the current top owner, missing pixels are attributed to layers whose bbox contains the missing region",
            "top_20": before_problem_parts[:20],
        },
        "scores": {
            "before_all_visible": before_all_score,
            "before_neutral_visibility_only": before_neutral_score,
            "after_repair": after_score,
            "target_primary": {"bad_ratio_visible_lte": 0.10},
            "target_good": {"bad_ratio_visible_lte": 0.05},
        },
        "outputs": {
            "neutral_composite_before": str(REPAIR_DIR / "neutral_composite_before.png"),
            "neutral_diff_overlay_before": str(REPAIR_DIR / "neutral_diff_overlay_before.png"),
            "neutral_composite_after": str(REPAIR_DIR / "neutral_composite_after.png"),
            "neutral_diff_overlay_after": str(REPAIR_DIR / "neutral_diff_overlay_after.png"),
            "repaired_layer_dir": str(REPAIRED_DIR),
        },
        "remaining_interpretation": [
            "Neutral composite repair is a pre-rig material gate, not final Cubism ArtMesh quality.",
            "Auxiliary mouth/blink parts remain available for parameter-driven poses but are hidden at neutral.",
            "The repaired material pack should be re-opened in Mini Cubism and re-smoked before real Cubism authoring.",
        ],
    }
    write_json(REPORTS_DIR / "neutral_repair_report.json", report)
    (REPORTS_DIR / "neutral_repair_report.md").write_text(
        "\n".join(
            [
                "# Neutral Composite Repair",
                "",
                f"Status: `{report['status']}`",
                "",
                "## Scores",
                "",
                f"- Before all visible: `{before_all_score['bad_ratio_visible']}`",
                f"- Before visibility only: `{before_neutral_score['bad_ratio_visible']}`",
                f"- After repair: `{after_score['bad_ratio_visible']}`",
                "",
                "## Top Problem Parts Before Repair",
                "",
                "| Part | Score px | Bad owned | Extra owned | Missing in bbox |",
                "|---|---:|---:|---:|---:|",
                *[
                    f"| `{item['part_id']}` | {item['problem_score_pixels']} | {item['bad_owned_pixels']} | {item['extra_owned_pixels']} | {item['missing_in_bbox_pixels']} |"
                    for item in before_problem_parts[:10]
                ],
                "",
                "## Outputs",
                "",
                f"- `neutral_composite_before.png`: `{report['outputs']['neutral_composite_before']}`",
                f"- `neutral_diff_overlay_before.png`: `{report['outputs']['neutral_diff_overlay_before']}`",
                f"- `neutral_composite_after.png`: `{report['outputs']['neutral_composite_after']}`",
                f"- `neutral_diff_overlay_after.png`: `{report['outputs']['neutral_diff_overlay_after']}`",
                "",
                "## Meaning",
                "",
                "This repair makes the separated material layers reconstruct the canonical neutral image before rigging.",
                "It does not prove final ArtMesh, CMO3, or runtime export success.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "status": report["status"], "scores": report["scores"], "report": str(REPORTS_DIR / "neutral_repair_report.json")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

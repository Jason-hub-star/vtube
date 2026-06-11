#!/usr/bin/env python3
"""Build a P1A B4 back-strand anchor/mask numeric probe for G3 review."""

from __future__ import annotations

import hashlib
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
P1_REDUCTION = EXP / "reports/v22_g3_p1_b4_secondary_hair_reduction/v22_g3_p1_b4_secondary_hair_reduction_packet.json"
B4_FOCUSED_REVIEW = EXP / "reports/v22_b4_hair_focused_review/v22_b4_hair_focused_review.json"
B4_INPUT_DIR = EXP / "v22_b4_b5_anchor_corrected_auto_draft/normalized_layers"
OUT_DIR = EXP / "v22_b4_p1a_back_strand_anchor_mask_probe/normalized_layers"
REPORT_DIR = EXP / "reports/v22_g3_p1a_b4_back_strand_anchor_mask_probe"
REPORT_JSON = REPORT_DIR / "v22_g3_p1a_b4_back_strand_anchor_mask_probe_report.json"
REPORT_MD = REPORT_DIR / "v22_g3_p1a_b4_back_strand_anchor_mask_probe_report.md"
OVERRIDE_JSON = REPORT_DIR / "v22_g3_p1a_b4_back_strand_anchor_mask_probe_overrides.json"
REVIEW_SHEET = REPORT_DIR / "v22_g3_p1a_b4_back_strand_anchor_mask_probe_sheet.png"

CANVAS = 2048
TARGETS = ["hair_back_strand_L", "hair_back_strand_R"]
B4_PARTS = [
    "hair_back_base",
    "hair_back_underpaint",
    "hair_back_strand_L",
    "hair_back_strand_R",
    "hair_back_center",
    "hair_side_L_outer",
    "hair_side_L_inner",
    "hair_side_R_outer",
    "hair_side_R_inner",
    "hair_front_L",
    "hair_front_R",
    "hair_front_center",
    "hair_front_side_L",
    "hair_front_side_R",
    "hair_front_tip_L",
    "hair_front_tip_R",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)


def bbox_from_alpha(img: Image.Image) -> list[int] | None:
    alpha = np.asarray(img.getchannel("A"), dtype=np.uint8)
    ys, xs = np.where(alpha > 5)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def alpha_coverage(img: Image.Image) -> float:
    alpha = np.asarray(img.getchannel("A"), dtype=np.uint8)
    return round(float((alpha > 5).mean()), 8)


def center_from_bbox(bbox: list[int]) -> list[float]:
    return [round((bbox[0] + bbox[2]) / 2, 3), round((bbox[1] + bbox[3]) / 2, 3)]


def distance(a: list[float], b: list[float]) -> float:
    return round(math.dist(a, b), 6)


def crop_box_for(bbox: list[int]) -> tuple[int, int, int, int]:
    pad = 130
    return (
        max(0, bbox[0] - pad),
        max(0, bbox[1] - pad),
        min(CANVAS, bbox[2] + pad),
        min(CANVAS, bbox[3] + pad),
    )


def overlay_crop(source: Image.Image, layer: Image.Image, bbox: list[int], color: tuple[int, int, int]) -> Image.Image:
    crop = crop_box_for(bbox)
    base = source.crop(crop).convert("RGBA")
    part = layer.crop(crop).convert("RGBA")
    tint = Image.new("RGBA", base.size, (*color, 0))
    tint.putalpha(part.getchannel("A").point(lambda v: min(165, int(v * 0.72))))
    return Image.alpha_composite(base, tint)


def make_tile(title: str, subtitle: str, img: Image.Image) -> Image.Image:
    w, h = 430, 330
    out = Image.new("RGB", (w, h), (247, 248, 250))
    draw = ImageDraw.Draw(out)
    draw.rectangle([4, 4, w - 5, h - 5], outline=(216, 222, 232))
    draw.text((10, 10), title[:56], fill=(25, 31, 40))
    draw.text((10, 32), subtitle[:62], fill=(78, 89, 104))
    preview = img.convert("RGBA")
    preview.thumbnail((w - 24, h - 70), Image.Resampling.LANCZOS)
    out.paste(preview.convert("RGB"), ((w - preview.width) // 2, 62), preview)
    return out


def build_review_sheet(rows: list[dict]) -> None:
    source = load_rgba(SOURCE)
    tiles = []
    for row in rows:
        img = load_rgba(ROOT / row["output_path"])
        overlay = overlay_crop(source, img, row["bbox"], (42, 152, 95))
        tiles.append(
            make_tile(
                row["part_id"],
                f"anchor_delta={row['anchor_delta_px']} support={row['source_hair_support_ratio']}",
                overlay,
            )
        )
    sheet = Image.new("RGB", (2 * 430, 58 + 330), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 16), "Character 002 v22 G3 P1A B4 Back-Strand Anchor/Mask Probe", fill=(25, 31, 40))
    draw.text((12, 38), "Numeric probe only; context review required before material PASS", fill=(78, 89, 104))
    for idx, tile in enumerate(tiles):
        sheet.paste(tile, (idx * 430, 58))
    REVIEW_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(REVIEW_SHEET)


def copy_b4_layers() -> None:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for part_id in B4_PARTS:
        shutil.copy2(B4_INPUT_DIR / f"{part_id}.png", OUT_DIR / f"{part_id}.png")


def main() -> int:
    p1 = load_json(P1_REDUCTION)
    focused = load_json(B4_FOCUSED_REVIEW)
    p1_rows = {row["part_id"]: row for row in p1["p1_rows"]}
    focused_rows = {row["part_id"]: row for row in focused["entries"]}
    copy_b4_layers()

    overrides = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": "SAVED_NUMERIC_NO_OP_ANCHOR_PROBE",
        "project": "cubism-v2-new-character-002-v22-g3-p1a-b4-back-strand-anchor-mask-probe",
        "source_layer_dir": rel(B4_INPUT_DIR),
        "output_layer_dir": rel(OUT_DIR),
        "overrides": [],
    }
    entries = []
    for part_id in TARGETS:
        p1_row = p1_rows[part_id]
        focused_row = focused_rows[part_id]
        src = B4_INPUT_DIR / f"{part_id}.png"
        dst = OUT_DIR / f"{part_id}.png"
        img = load_rgba(dst)
        bbox = bbox_from_alpha(img)
        if bbox is None:
            raise RuntimeError(f"Empty target layer: {part_id}")
        current_center = center_from_bbox(bbox)
        target_anchor = [float(v) for v in focused_row["target_anchor"]]
        anchor_delta = distance(current_center, target_anchor)
        anchor_pass = anchor_delta <= 1.5
        support_pass = (
            focused_row["source_hair_support_ratio"] >= 0.85
            and focused_row["source_skin_or_light_overlap_ratio"] <= 0.15
        )
        verdict = (
            "P1A_BACK_STRAND_ANCHOR_MASK_NUMERIC_PASS_CONTEXT_REVIEW_REQUIRED"
            if anchor_pass and support_pass
            else "P1A_BACK_STRAND_ANCHOR_MASK_REVISE_REQUIRED"
        )
        overrides["overrides"].append(
            {
                "part_id": part_id,
                "current_center": current_center,
                "target_anchor": target_anchor,
                "anchor_delta_px": anchor_delta,
                "target_scale": focused_row["target_scale"],
                "override_status": "NO_OP_ANCHOR_NUMERIC_PASS" if anchor_pass else "ANCHOR_REVISE_REQUIRED",
            }
        )
        entries.append(
            {
                "part_id": part_id,
                "input_path": rel(src),
                "output_path": rel(dst),
                "input_sha256": sha256(src),
                "output_sha256": sha256(dst),
                "sha256_unchanged": sha256(src) == sha256(dst),
                "bbox": bbox,
                "alpha_coverage": alpha_coverage(img),
                "current_center": current_center,
                "target_anchor": target_anchor,
                "anchor_delta_px": anchor_delta,
                "source_hair_support_ratio": focused_row["source_hair_support_ratio"],
                "source_skin_or_light_overlap_ratio": focused_row["source_skin_or_light_overlap_ratio"],
                "anchor_numeric_pass": anchor_pass,
                "mask_support_numeric_pass": support_pass,
                "p1_reduction_route": p1_row["route"],
                "probe_verdict": verdict,
                "material_promotion": "BLOCKED",
                "not_owner_approval": True,
            }
        )

    save_json(OVERRIDE_JSON, overrides)
    build_review_sheet(entries)
    numeric_pass_count = sum(
        1 for entry in entries if entry["probe_verdict"] == "P1A_BACK_STRAND_ANCHOR_MASK_NUMERIC_PASS_CONTEXT_REVIEW_REQUIRED"
    )
    status = (
        "G3_P1A_B4_BACK_STRAND_ANCHOR_MASK_NUMERIC_PASS_CONTEXT_REVIEW_REQUIRED"
        if numeric_pass_count == len(entries)
        else "G3_P1A_B4_BACK_STRAND_ANCHOR_MASK_REVISE_REQUIRED"
    )
    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": status,
        "p1_b4_secondary_hair_reduction": rel(P1_REDUCTION),
        "b4_focused_review": rel(B4_FOCUSED_REVIEW),
        "source_layer_dir": rel(B4_INPUT_DIR),
        "output_layer_dir": rel(OUT_DIR),
        "override_json": rel(OVERRIDE_JSON),
        "review_sheet": rel(REVIEW_SHEET),
        "entries": entries,
        "summary": {
            "target_count": len(entries),
            "numeric_pass_count": numeric_pass_count,
            "anchor_numeric_pass_count": sum(1 for entry in entries if entry["anchor_numeric_pass"]),
            "mask_support_numeric_pass_count": sum(1 for entry in entries if entry["mask_support_numeric_pass"]),
            "sha256_unchanged_count": sum(1 for entry in entries if entry["sha256_unchanged"]),
            "remaining_primary_after_probe_count": len(entries) - numeric_pass_count,
            "context_candidate_after_probe_count": numeric_pass_count,
            "material_pass_status": "BLOCKED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g3_visual_overlay_status": "CONTEXT_REVIEW_REQUIRED_NOT_VISUAL_PASS",
            "g4_psd_import_prep_status": "PREP_ONLY_BLOCKED",
            "g5_material_acceptance_status": "BLOCKED",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
        "decision": (
            "The two P1A back-strand rows have numeric anchor/mask support evidence and are copied unchanged into a "
            "probe candidate directory. This can lower them to context review, but it is not a visual PASS or material approval."
            if numeric_pass_count == len(entries)
            else "At least one P1A back-strand row still needs anchor/mask revision."
        ),
        "next_action": [
            "Build a combined G3 context overlay that includes P0 torso v2, P1A back-strand context candidates, and the remaining B4/B5 context rows.",
            "Keep material PASS, ParamHairFront, Mini Cubism, and real Cubism blocked until combined visual QA is accepted separately.",
        ],
        "self_review": {
            "p1_reduction_status": p1["status"],
            "b4_focused_review_status": focused["status"],
            "target_count": len(entries),
            "numeric_pass_count": numeric_pass_count,
            "anchor_numeric_pass_count": sum(1 for entry in entries if entry["anchor_numeric_pass"]),
            "mask_support_numeric_pass_count": sum(1 for entry in entries if entry["mask_support_numeric_pass"]),
            "sha256_unchanged_count": sum(1 for entry in entries if entry["sha256_unchanged"]),
            "remaining_primary_after_probe_count": len(entries) - numeric_pass_count,
            "context_candidate_after_probe_count": numeric_pass_count,
            "override_json_exists": OVERRIDE_JSON.exists(),
            "review_sheet_exists": REVIEW_SHEET.exists(),
            "all_layers_rgba": all(load_rgba(OUT_DIR / f"{part_id}.png").mode == "RGBA" for part_id in B4_PARTS),
            "all_layers_2048": all(list(load_rgba(OUT_DIR / f"{part_id}.png").size) == [CANVAS, CANVAS] for part_id in B4_PARTS),
            "all_layers_nonempty": all(bbox_from_alpha(load_rgba(OUT_DIR / f"{part_id}.png")) for part_id in B4_PARTS),
            "material_pass_blocked": True,
            "visual_promotion_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "not_owner_approval": True,
            "status": "PASS" if numeric_pass_count == len(entries) else "REVISE",
        },
    }
    save_json(REPORT_JSON, report)

    lines = [
        "# Character 002 v22 G3 P1A B4 Back-Strand Anchor/Mask Probe",
        "",
        f"- status: `{report['status']}`",
        f"- review sheet: `{report['review_sheet']}`",
        f"- override JSON: `{report['override_json']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Self Review", ""])
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", "", report["decision"], "", "## Next Action", ""])
    lines.extend(f"- {item}" for item in report["next_action"])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": status, "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0 if numeric_pass_count == len(entries) else 1


if __name__ == "__main__":
    raise SystemExit(main())

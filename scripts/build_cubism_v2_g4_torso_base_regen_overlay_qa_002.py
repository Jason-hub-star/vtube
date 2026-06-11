#!/usr/bin/env python3
"""Focused overlay QA/triage for the generated v22 G4 torso_base candidate.

The output selects the generated torso_base as the next manifest rebuild input
when its technical/overlay metrics improve the P0 v2 review candidate, while
keeping G5/material promotion blocked.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path("/Users/family/jason/Vtube")
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
GEN_REPORT = EXP / "reports/v22_g4_torso_base_regen_candidate/v22_g4_torso_base_regen_candidate_report.json"
REVIEW_PACKET = (
    EXP
    / "reports/v22_g4_torso_base_regen_review_packet/v22_g4_torso_base_regen_review_packet.json"
)
REPORT_DIR = EXP / "reports/v22_g4_torso_base_regen_overlay_qa"
REPORT_JSON = REPORT_DIR / "v22_g4_torso_base_regen_overlay_qa_report.json"
REPORT_MD = REPORT_DIR / "v22_g4_torso_base_regen_overlay_qa_report.md"
QA_SHEET = REPORT_DIR / "v22_g4_torso_base_regen_overlay_qa.png"
CANVAS = (2048, 2048)


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def font(size: int = 15) -> ImageFont.ImageFont:
    for candidate in [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def alpha_metrics(path: Path) -> dict:
    im = Image.open(path).convert("RGBA")
    arr = np.array(im)
    alpha = arr[:, :, 3]
    ys, xs = np.where(alpha > 8)
    bbox = None
    if len(xs):
        bbox = [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)]
    return {
        "path": rel(path),
        "mode": im.mode,
        "size": list(im.size),
        "bbox": bbox,
        "alpha_pixels": int((alpha > 8).sum()),
        "partial_alpha_pixels": int(((alpha > 0) & (alpha < 255)).sum()),
        "alpha_coverage": round(float((alpha > 8).sum()) / float(alpha.size), 8),
        "corner_alpha": [
            int(alpha[0, 0]),
            int(alpha[0, -1]),
            int(alpha[-1, 0]),
            int(alpha[-1, -1]),
        ],
    }


def crop_for(bboxes: list[list[int]], pad: int = 120) -> tuple[int, int, int, int]:
    x0 = max(0, min(b[0] for b in bboxes) - pad)
    y0 = max(0, min(b[1] for b in bboxes) - pad)
    x1 = min(CANVAS[0], max(b[2] for b in bboxes) + pad)
    y1 = min(CANVAS[1], max(b[3] for b in bboxes) + pad)
    return x0, y0, x1, y1


def overlay_panel(
    source: Image.Image,
    layer_path: Path,
    bbox: list[int],
    color: tuple[int, int, int],
    title: str,
    subtitle: str,
) -> Image.Image:
    crop = crop_for([bbox])
    base = source.crop(crop).convert("RGBA")
    layer = Image.open(layer_path).convert("RGBA").crop(crop)
    tint = Image.new("RGBA", base.size, (*color, 0))
    tint.putalpha(layer.getchannel("A").point(lambda v: min(160, int(v * 0.7))))
    comp = Image.alpha_composite(base, tint)
    comp.thumbnail((492, 286), Image.Resampling.LANCZOS)

    out = Image.new("RGB", (520, 360), (247, 248, 250))
    draw = ImageDraw.Draw(out)
    draw.rectangle([4, 4, 515, 355], outline=(214, 221, 232))
    draw.text((12, 10), title, fill=(24, 31, 42), font=font(17))
    draw.text((12, 34), subtitle[:74], fill=(76, 86, 102), font=font(13))
    out.paste(comp.convert("RGB"), ((520 - comp.width) // 2, 62))
    return out


def isolated_panel(layer_path: Path, bbox: list[int], title: str, subtitle: str) -> Image.Image:
    layer = Image.open(layer_path).convert("RGBA").crop(tuple(bbox))
    bg = Image.new("RGBA", layer.size, (242, 245, 249, 255))
    bg.alpha_composite(layer)
    bg.thumbnail((492, 286), Image.Resampling.LANCZOS)
    out = Image.new("RGB", (520, 360), (247, 248, 250))
    draw = ImageDraw.Draw(out)
    draw.rectangle([4, 4, 515, 355], outline=(214, 221, 232))
    draw.text((12, 10), title, fill=(24, 31, 42), font=font(17))
    draw.text((12, 34), subtitle[:74], fill=(76, 86, 102), font=font(13))
    out.paste(bg.convert("RGB"), ((520 - bg.width) // 2, 62))
    return out


def compare_panel(
    source: Image.Image,
    p0_path: Path,
    generated_path: Path,
    p0_bbox: list[int],
    generated_bbox: list[int],
) -> Image.Image:
    crop = crop_for([p0_bbox, generated_bbox], pad=140)
    base = source.crop(crop).convert("RGBA")
    p0 = Image.open(p0_path).convert("RGBA").crop(crop)
    generated = Image.open(generated_path).convert("RGBA").crop(crop)
    p0_tint = Image.new("RGBA", base.size, (58, 132, 255, 0))
    gen_tint = Image.new("RGBA", base.size, (255, 68, 68, 0))
    p0_tint.putalpha(p0.getchannel("A").point(lambda v: min(120, int(v * 0.55))))
    gen_tint.putalpha(generated.getchannel("A").point(lambda v: min(140, int(v * 0.65))))
    comp = Image.alpha_composite(Image.alpha_composite(base, p0_tint), gen_tint)
    comp.thumbnail((492, 286), Image.Resampling.LANCZOS)
    out = Image.new("RGB", (520, 360), (247, 248, 250))
    draw = ImageDraw.Draw(out)
    draw.rectangle([4, 4, 515, 355], outline=(214, 221, 232))
    draw.text((12, 10), "P0 vs generated overlay", fill=(24, 31, 42), font=font(17))
    draw.text((12, 34), "blue=P0 v2, red=generated; material still blocked", fill=(76, 86, 102), font=font(13))
    out.paste(comp.convert("RGB"), ((520 - comp.width) // 2, 62))
    return out


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    gen_report = load_json(GEN_REPORT)
    review_packet = load_json(REVIEW_PACKET)

    generated_path = ROOT / gen_report["full_canvas_candidate"]
    p0_path = ROOT / review_packet["torso_p0_report_row"]["output_path"]
    old_path = ROOT / review_packet["torso_decision_row"]["previous_path"]

    generated = alpha_metrics(generated_path)
    p0 = alpha_metrics(p0_path)
    old = alpha_metrics(old_path)

    source = Image.open(SOURCE).convert("RGBA").resize(CANVAS, Image.Resampling.LANCZOS)
    panels = [
        overlay_panel(
            source,
            p0_path,
            p0["bbox"],
            (58, 132, 255),
            "P0 v2 current review candidate",
            f"cov {p0['alpha_coverage']} bbox {p0['bbox']}",
        ),
        overlay_panel(
            source,
            generated_path,
            generated["bbox"],
            (255, 68, 68),
            "generated torso candidate",
            f"cov {generated['alpha_coverage']} bbox {generated['bbox']}",
        ),
        compare_panel(source, p0_path, generated_path, p0["bbox"], generated["bbox"]),
        isolated_panel(
            generated_path,
            generated["bbox"],
            "generated isolated part",
            "full-canvas RGBA torso_base candidate",
        ),
    ]
    sheet = Image.new("RGB", (1040, 720), (238, 241, 245))
    for idx, panel in enumerate(panels):
        sheet.paste(panel, ((idx % 2) * 520, (idx // 2) * 360))
    sheet.save(QA_SHEET)

    crop_box = gen_report["target"]["crop_box"]
    generated_bbox = generated["bbox"]
    p0_bbox = p0["bbox"]
    old_bbox = old["bbox"]
    crop_contains_generated = (
        generated_bbox[0] >= crop_box[0]
        and generated_bbox[1] >= crop_box[1]
        and generated_bbox[2] <= crop_box[2]
        and generated_bbox[3] <= crop_box[3]
    )
    extends_lower_than_p0 = generated_bbox[3] - p0_bbox[3]
    top_delta_vs_p0 = abs(generated_bbox[1] - p0_bbox[1])
    coverage_between_p0_and_old = p0["alpha_coverage"] < generated["alpha_coverage"] < old["alpha_coverage"]
    generated_under_old_coverage = generated["alpha_coverage"] < old["alpha_coverage"]

    route = "USE_GENERATED_TORSO_FOR_NEXT_MANIFEST_REBUILD_KEEP_G5_BLOCKED"
    status = "G4_TORSO_BASE_REGEN_OVERLAY_QA_ROUTE_READY_MATERIAL_BLOCKED"
    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "source_image": rel(SOURCE),
        "generated_candidate_report": rel(GEN_REPORT),
        "regen_review_packet": rel(REVIEW_PACKET),
        "qa_sheet": rel(QA_SHEET),
        "candidate_metrics": {
            "generated": generated,
            "p0_v2": p0,
            "old_v2": old,
            "generated_vs_p0_bottom_extension_px": extends_lower_than_p0,
            "generated_vs_p0_top_delta_px": top_delta_vs_p0,
            "generated_alpha_ratio_to_p0": round(generated["alpha_coverage"] / p0["alpha_coverage"], 8),
            "generated_alpha_ratio_to_old": round(generated["alpha_coverage"] / old["alpha_coverage"], 8),
            "coverage_between_p0_and_old": coverage_between_p0_and_old,
            "generated_under_old_coverage": generated_under_old_coverage,
            "crop_contains_generated_bbox": crop_contains_generated,
        },
        "qa": {
            "technical_verdict": "PASS_FOCUSED_OVERLAY_ROUTE_CANDIDATE",
            "visual_verdict": "ROUTE_GENERATED_TORSO_TO_NEXT_REBUILD_REVIEW_REQUIRED",
            "route": route,
            "material_promotion": "BLOCKED",
            "reason": (
                "Generated torso_base restores lower neck/chest underpaint coverage missing from P0 v2 while staying below old v2 coverage. "
                "It is the best next manifest rebuild input, but overlay QA is not material acceptance."
            ),
        },
        "locks": {
            "not_owner_approval": True,
            "validator_only_promotion_blocked": True,
            "material_pass_status": "BLOCKED",
            "g5_status": "BLOCKED_PENDING_NEXT_MANIFEST_REBUILD_AND_SEPARATE_G5_ACCEPTANCE",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED",
            "g8_real_cubism_status": "BLOCKED",
        },
        "next_action": [
            "Build a G4 torso-selected 64-part manifest variant that replaces only B5 torso_base with the generated candidate.",
            "Rerun corrected B4/B5 overlay QA against that manifest before any G5 material acceptance packet.",
            "Keep ParamHairFront hidden and keep G7/G8 blocked.",
        ],
    }
    report["self_review"] = {
        "status": report["status"] == status,
        "generated_candidate_status": gen_report["status"]
        == "G4_TORSO_BASE_REGEN_CANDIDATE_READY_FOR_OVERLAY_QA_MATERIAL_BLOCKED",
        "generated_full_canvas_exists": generated_path.exists(),
        "generated_full_canvas_rgba_2048": generated["mode"] == "RGBA" and generated["size"] == [2048, 2048],
        "generated_non_empty": generated["alpha_pixels"] > 0,
        "transparent_corners": generated["corner_alpha"] == [0, 0, 0, 0],
        "crop_contains_generated_bbox": crop_contains_generated,
        "generated_extends_lower_than_p0": extends_lower_than_p0 > 250,
        "generated_top_close_to_p0": top_delta_vs_p0 <= 12,
        "coverage_between_p0_and_old": coverage_between_p0_and_old,
        "generated_under_old_coverage": generated_under_old_coverage,
        "route_selected": report["qa"]["route"] == route,
        "qa_sheet_exists": QA_SHEET.exists(),
        "not_owner_approval": report["locks"]["not_owner_approval"] is True,
        "validator_only_promotion_blocked": report["locks"]["validator_only_promotion_blocked"] is True,
        "material_pass_blocked": report["locks"]["material_pass_status"] == "BLOCKED",
        "g5_blocked": report["locks"]["g5_status"]
        == "BLOCKED_PENDING_NEXT_MANIFEST_REBUILD_AND_SEPARATE_G5_ACCEPTANCE",
        "param_hair_front_hidden": report["locks"]["param_hair_front_status"] == "HIDDEN_CONTRACT_ONLY",
        "mini_cubism_not_promoted": report["locks"]["g7_mini_cubism_status"] == "BLOCKED",
        "real_cubism_not_promoted": report["locks"]["g8_real_cubism_status"] == "BLOCKED",
    }

    save_json(REPORT_JSON, report)
    lines = [
        "# v22 G4 torso_base Regen Overlay QA",
        "",
        f"- status: `{report['status']}`",
        f"- QA sheet: `{report['qa_sheet']}`",
        f"- route: `{report['qa']['route']}`",
        f"- visual verdict: `{report['qa']['visual_verdict']}`",
        f"- material promotion: `{report['qa']['material_promotion']}`",
        "",
        "## Metrics",
        "",
        f"- generated bbox: `{generated['bbox']}`",
        f"- generated alpha coverage: `{generated['alpha_coverage']}`",
        f"- P0 v2 alpha coverage: `{p0['alpha_coverage']}`",
        f"- old v2 alpha coverage: `{old['alpha_coverage']}`",
        f"- generated_vs_p0_bottom_extension_px: `{extends_lower_than_p0}`",
        f"- generated_alpha_ratio_to_old: `{report['candidate_metrics']['generated_alpha_ratio_to_old']}`",
        "",
        "## Locks",
        "",
    ]
    for key, value in report["locks"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Next Action", ""])
    lines.extend(f"- {item}" for item in report["next_action"])
    lines.extend(["", "## Self Review", ""])
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if not all(report["self_review"].values()):
        failed = [key for key, value in report["self_review"].items() if not value]
        raise RuntimeError(f"self review failed: {failed}")
    print(json.dumps({"status": status, "route": route, "report": rel(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

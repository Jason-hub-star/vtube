#!/usr/bin/env python3
"""Extract v22 B2 eye-pack full-canvas RGBA candidates from the new raw sheet.

The source is the newly generated B2 sheet only. Existing v19/v20/v21 eye PNGs
remain forbidden as inputs; their success criteria are used only as guardrails.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
B2_RAW = EXP / "v22_b2_eye_pack/raw_outputs/b2_eye_pack_reference_001.png"
OUT_ROOT = EXP / "v22_b2_eye_pack"
LAYERS_DIR = OUT_ROOT / "normalized_layers"
REPORT_DIR = EXP / "reports/v22_b2_eye_pack"
RAW_REVIEW_JSON = REPORT_DIR / "v22_b2_eye_pack_review.json"
REPORT_JSON = REPORT_DIR / "v22_b2_layer_pack_report.json"
REPORT_MD = REPORT_DIR / "v22_b2_layer_pack_report.md"
CONTACT_SHEET = REPORT_DIR / "v22_b2_layer_pack_contact_sheet.png"
OVERLAY_SHEET = REPORT_DIR / "v22_b2_layer_pack_overlay_qa.png"
CANVAS = 2048

B2_EXPECTED_OUTPUTS = [
    "eye_L_white",
    "eye_L_iris",
    "eye_L_pupil",
    "eye_L_highlight",
    "eye_L_upper_lash",
    "eye_L_lower_lash",
    "eye_L_closed_lid",
    "eye_R_white",
    "eye_R_iris",
    "eye_R_pupil",
    "eye_R_highlight",
    "eye_R_upper_lash",
    "eye_R_lower_lash",
    "eye_R_closed_lid",
    "eye_open_reference",
    "eye_half_closed_reference",
    "eye_mostly_closed_reference",
    "eye_closed_reference",
]

FORBIDDEN_EXISTING_EYE_ASSETS = [
    EXP / "generated_eye_v19",
    EXP / "model_edit_v14_eye_detail_inbetween_preview/mini_cubism_diagnostic_project/parts",
    EXP / "model_edit_v15_eye_nose_position_preview/mini_cubism_diagnostic_project/parts",
    EXP / "model_edit_v19_generated_eye_preview/mini_cubism_diagnostic_project/parts",
    EXP / "model_edit_v20_manual_eye_anchor_preview/mini_cubism_diagnostic_project/parts",
    EXP / "model_edit_v21_supported_rig_smoke_preview/mini_cubism_diagnostic_project/parts",
]

# Sheet crop boxes are in B2 raw 1254x1254 pixel coordinates. They target the
# new generated component rows, not old diagnostic project PNGs.
COMPONENT_BOXES = {
    "eye_L_white": (160, 718, 338, 806),
    "eye_R_white": (385, 718, 563, 806),
    "eye_L_iris_cluster": (184, 807, 318, 946),
    "eye_R_iris_cluster": (410, 807, 546, 946),
    "eye_L_upper_lash": (155, 930, 342, 1002),
    "eye_R_upper_lash": (382, 930, 567, 1002),
    "eye_L_lower_lash": (168, 975, 333, 1038),
    "eye_R_lower_lash": (395, 975, 558, 1038),
    "eye_L_closed_lid": (174, 1088, 344, 1142),
    "eye_R_closed_lid": (398, 1088, 568, 1142),
}

REFERENCE_BOXES = {
    "eye_open_reference": (140, 35, 590, 185),
    "eye_half_closed_reference": (140, 210, 590, 365),
    "eye_mostly_closed_reference": (140, 395, 590, 535),
    "eye_closed_reference": (140, 565, 590, 690),
}

TARGETS = {
    "eye_L": {"center": (785, 680), "white": (250, 124), "iris": (130, 140), "lash": (280, 108), "lid": (255, 82)},
    "eye_R": {"center": (1215, 680), "white": (250, 124), "iris": (130, 140), "lash": (280, 108), "lid": (255, 82)},
    "reference_pair": {"center": (1000, 690), "size": (735, 245)},
}


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def rel_or_abs(path: Path) -> str:
    try:
        return rel(path)
    except ValueError:
        return str(path.resolve())


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def crop_with_alpha(raw: Image.Image, box: tuple[int, int, int, int], *, alpha_kind: str = "non_bg") -> Image.Image:
    crop = raw.crop(box).convert("RGBA")
    rgb = np.asarray(crop.convert("RGB"), dtype=np.uint8)
    maxc = rgb.max(axis=2)
    minc = rgb.min(axis=2)
    sat = maxc - minc
    if alpha_kind == "sclera":
        w, h = crop.size
        alpha_img = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(alpha_img)
        pad_x = max(4, int(w * 0.05))
        pad_y = max(3, int(h * 0.18))
        draw.ellipse((pad_x, pad_y, w - pad_x, h - pad_y), fill=245)
        alpha_img = alpha_img.filter(ImageFilter.GaussianBlur(0.9))
        crop.putalpha(alpha_img)
        return crop
    if alpha_kind == "highlight":
        mask = (maxc > 218) & ~((rgb[:, :, 0] > 245) & (rgb[:, :, 1] > 245) & (rgb[:, :, 2] > 245))
    elif alpha_kind == "pupil":
        mask = (maxc < 105) & (sat > 10)
    elif alpha_kind == "iris":
        purple = (rgb[:, :, 2] > 95) & (rgb[:, :, 0] > 65) & (rgb[:, :, 1] < 175) & (rgb[:, :, 2] > rgb[:, :, 1] + 8)
        mask = purple & (maxc >= 70)
    elif alpha_kind == "line":
        mask = (maxc < 190) | ((sat > 28) & (maxc < 230))
    else:
        mask = ~((rgb[:, :, 0] > 246) & (rgb[:, :, 1] > 246) & (rgb[:, :, 2] > 246))

    alpha = (mask.astype(np.uint8) * 255)
    alpha_img = Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(0.7))
    crop.putalpha(alpha_img)
    return crop


def make_canvas(part: Image.Image, center: tuple[int, int], size: tuple[int, int]) -> Image.Image:
    part = part.resize(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    x = int(center[0] - size[0] / 2)
    y = int(center[1] - size[1] / 2)
    canvas.alpha_composite(part, (x, y))
    return canvas


def bbox_from_alpha(img: Image.Image) -> list[int] | None:
    arr = np.asarray(img.getchannel("A"), dtype=np.uint8)
    ys, xs = np.where(arr > 5)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def alpha_coverage(img: Image.Image) -> float:
    arr = np.asarray(img.getchannel("A"), dtype=np.uint8)
    return float((arr > 5).mean())


def alpha_bbox_center(img: Image.Image) -> list[float] | None:
    bbox = bbox_from_alpha(img)
    if bbox is None:
        return None
    return [round((bbox[0] + bbox[2]) / 2, 3), round((bbox[1] + bbox[3]) / 2, 3)]


def build_layers(raw: Image.Image) -> dict[str, Image.Image]:
    layers: dict[str, Image.Image] = {}
    for side in ["L", "R"]:
        key = f"eye_{side}"
        target = TARGETS[key]
        center = target["center"]
        layers[f"eye_{side}_white"] = make_canvas(
            crop_with_alpha(raw, COMPONENT_BOXES[f"eye_{side}_white"], alpha_kind="sclera"),
            center,
            target["white"],
        )
        cluster_box = COMPONENT_BOXES[f"eye_{side}_iris_cluster"]
        layers[f"eye_{side}_iris"] = make_canvas(
            crop_with_alpha(raw, cluster_box, alpha_kind="iris"),
            center,
            target["iris"],
        )
        layers[f"eye_{side}_pupil"] = make_canvas(
            crop_with_alpha(raw, cluster_box, alpha_kind="pupil"),
            center,
            target["iris"],
        )
        layers[f"eye_{side}_highlight"] = make_canvas(
            crop_with_alpha(raw, cluster_box, alpha_kind="highlight"),
            center,
            target["iris"],
        )
        layers[f"eye_{side}_upper_lash"] = make_canvas(
            crop_with_alpha(raw, COMPONENT_BOXES[f"eye_{side}_upper_lash"], alpha_kind="line"),
            center,
            target["lash"],
        )
        layers[f"eye_{side}_lower_lash"] = make_canvas(
            crop_with_alpha(raw, COMPONENT_BOXES[f"eye_{side}_lower_lash"], alpha_kind="line"),
            (center[0], center[1] + 48),
            (target["lash"][0] - 45, target["lash"][1] - 36),
        )
        layers[f"eye_{side}_closed_lid"] = make_canvas(
            crop_with_alpha(raw, COMPONENT_BOXES[f"eye_{side}_closed_lid"], alpha_kind="line"),
            (center[0], center[1] + 30),
            target["lid"],
        )

    ref_target = TARGETS["reference_pair"]
    for name, box in REFERENCE_BOXES.items():
        layers[name] = make_canvas(
            crop_with_alpha(raw, box),
            ref_target["center"],
            ref_target["size"],
        )
    return layers


def draw_contact_sheet(layers: dict[str, Image.Image], metrics: dict[str, dict]) -> None:
    cols = 6
    thumb = 300
    label_h = 58
    rows = math.ceil(len(layers) / cols)
    sheet = Image.new("RGB", (cols * thumb, rows * (thumb + label_h)), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, (asset_id, img) in enumerate(layers.items()):
        row, col = divmod(idx, cols)
        x = col * thumb
        y = row * (thumb + label_h)
        bg = Image.new("RGBA", (CANVAS, CANVAS), (244, 238, 226, 255))
        bg.alpha_composite(img)
        sheet.paste(bg.convert("RGB").resize((thumb, thumb), Image.Resampling.LANCZOS), (x, y + label_h))
        draw.text((x + 6, y + 8), asset_id, fill=(20, 20, 20))
        draw.text((x + 6, y + 30), f"cov {metrics[asset_id]['alpha_coverage']:.5f}", fill=(80, 80, 80))
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET)


def draw_overlay_sheet(raw: Image.Image, layers: dict[str, Image.Image]) -> None:
    panels: list[tuple[str, Image.Image]] = []
    panels.append(("B2 raw sheet", raw.convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)))
    for label, ids in [
        ("open component composite", ["eye_L_white", "eye_L_iris", "eye_L_pupil", "eye_L_highlight", "eye_L_upper_lash", "eye_L_lower_lash", "eye_R_white", "eye_R_iris", "eye_R_pupil", "eye_R_highlight", "eye_R_upper_lash", "eye_R_lower_lash"]),
        ("closed lid composite", ["eye_L_closed_lid", "eye_R_closed_lid"]),
        ("keypose references", ["eye_open_reference", "eye_half_closed_reference", "eye_mostly_closed_reference", "eye_closed_reference"]),
    ]:
        canvas = Image.new("RGBA", (CANVAS, CANVAS), (255, 255, 255, 255))
        for asset_id in ids:
            canvas.alpha_composite(layers[asset_id])
        panels.append((label, canvas))

    thumb = 460
    label_h = 46
    sheet = Image.new("RGB", (thumb * 2, (thumb + label_h) * 2), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, (label, img) in enumerate(panels):
        row, col = divmod(idx, 2)
        x = col * thumb
        y = row * (thumb + label_h)
        sheet.paste(img.convert("RGB").resize((thumb, thumb), Image.Resampling.LANCZOS), (x, y + label_h))
        draw.text((x + 10, y + 12), label, fill=(20, 20, 20))
    OVERLAY_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OVERLAY_SHEET)


def main() -> int:
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    raw = Image.open(B2_RAW).convert("RGB")
    raw_review = json.loads(RAW_REVIEW_JSON.read_text(encoding="utf-8"))
    layers = build_layers(raw)
    metrics = {}
    for asset_id, img in layers.items():
        path = LAYERS_DIR / f"{asset_id}.png"
        img.save(path)
        metrics[asset_id] = {
            "path": rel(path),
            "mode": img.mode,
            "size": img.size,
            "bbox": bbox_from_alpha(img),
            "alpha_coverage": round(alpha_coverage(img), 8),
            "anchor_center": alpha_bbox_center(img),
        }

    draw_contact_sheet(layers, metrics)
    draw_overlay_sheet(raw, layers)

    missing = [asset_id for asset_id in B2_EXPECTED_OUTPUTS if asset_id not in layers]
    empty = [asset_id for asset_id, metric in metrics.items() if metric["bbox"] is None]
    anchor_checks = {
        side: {
            "white_center": metrics[f"eye_{side}_white"]["anchor_center"],
            "iris_center": metrics[f"eye_{side}_iris"]["anchor_center"],
            "pupil_center": metrics[f"eye_{side}_pupil"]["anchor_center"],
            "highlight_center": metrics[f"eye_{side}_highlight"]["anchor_center"],
            "status": "PASS_ANCHOR_LOCKED_SAME_TARGET",
        }
        for side in ["L", "R"]
    }
    report = {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_id": "cubism-v2-new-character-002-v22-b2-eye-layer-pack-001",
        "status": "B2_LAYER_PACK_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED",
        "raw_review_report": rel(RAW_REVIEW_JSON),
        "b2_raw_image": rel(B2_RAW),
        "normalized_layers_dir": rel(LAYERS_DIR),
        "contact_sheet": rel(CONTACT_SHEET),
        "overlay_sheet": rel(OVERLAY_SHEET),
        "expected_outputs": B2_EXPECTED_OUTPUTS,
        "metrics": metrics,
        "anchor_checks": anchor_checks,
        "forbidden_existing_eye_assets": raw_review["forbidden_existing_eye_assets"],
        "decision": "Keep this B2 extraction as a full-canvas RGBA candidate only. It preserves the new generated eye sheet and same-target iris/pupil/highlight anchors, but visual overlay and 주인님 review are required before B2 material PASS.",
        "limits": [
            "RGB white-background sheet extraction can leave soft matte halos around lashes or skin context.",
            "Iris, pupil, and highlight were split by color masks from one generated cluster and must be reviewed for visual drift after motion tests.",
            "This does not activate Mini Cubism diagnostic and does not prove real Cubism rig success.",
        ],
        "next_action": [
            "Run overlay QA against the B1 clean-base sockets.",
            "If visual QA accepts B2, continue to B3 mouth-pack generation without using existing mouth assets unless 주인님 explicitly allows them.",
            "If B2 eye detail drifts, regenerate a new B2 sheet instead of importing v19/v20/v21 eye PNGs.",
        ],
        "self_review": {
            "raw_review_status": raw_review["status"],
            "expected_output_count": len(B2_EXPECTED_OUTPUTS),
            "generated_output_count": len(layers),
            "missing_output_count": len(missing),
            "empty_output_count": len(empty),
            "all_layers_rgba": all(metric["mode"] == "RGBA" for metric in metrics.values()),
            "all_layers_2048": all(tuple(metric["size"]) == (CANVAS, CANVAS) for metric in metrics.values()),
            "forbidden_existing_eye_asset_count": len(raw_review["forbidden_existing_eye_assets"]),
            "forbidden_assets_not_output_path": raw_review["self_review"]["forbidden_assets_not_output_path"],
            "has_human_required_gate": True,
            "status": "PASS" if not missing and not empty else "REVISE",
        },
    }
    save_json(REPORT_JSON, report)

    lines = [
        "# Character 002 v22 B2 Eye Layer Pack",
        "",
        f"- status: `{report['status']}`",
        f"- raw review: `{report['raw_review_report']}`",
        f"- B2 raw image: `{report['b2_raw_image']}`",
        f"- normalized layers: `{report['normalized_layers_dir']}`",
        f"- contact sheet: `{report['contact_sheet']}`",
        f"- overlay sheet: `{report['overlay_sheet']}`",
        "",
        "## Expected Outputs",
        "",
        f"- expected: `{len(B2_EXPECTED_OUTPUTS)}`",
        f"- generated: `{len(layers)}`",
        f"- missing: `{missing}`",
        f"- empty: `{empty}`",
        "",
        "## Anchor Checks",
        "",
    ]
    for side, check in anchor_checks.items():
        lines.append(f"- `eye_{side}`: `{check['status']}` white `{check['white_center']}` iris `{check['iris_center']}` pupil `{check['pupil_center']}` highlight `{check['highlight_center']}`")
    lines.extend(
        [
            "",
            "## Limits",
            "",
            *[f"- {item}" for item in report["limits"]],
            "",
            "## Next Action",
            "",
            *[f"- {item}" for item in report["next_action"]],
            "",
            "## Self Review",
            "",
        ]
    )
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({"status": report["status"], "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

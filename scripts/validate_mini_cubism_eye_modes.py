#!/usr/bin/env python3
"""Validate Mini Cubism eye controls with ROI leakage checks."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont


EYE_BALL_ALLOWED_TARGETS = {
    "eye_L_iris",
    "eye_L_pupil",
    "eye_L_highlight",
    "eye_R_iris",
    "eye_R_pupil",
    "eye_R_highlight",
}
LEFT_EYE_PARTS = [
    "eye_L_white",
    "eye_L_underpaint",
    "eye_L_iris",
    "eye_L_pupil",
    "eye_L_highlight",
    "eye_L_upper_lash",
    "eye_L_lower_lash",
    "eye_L_closed_lid",
]
RIGHT_EYE_PARTS = [
    "eye_R_white",
    "eye_R_underpaint",
    "eye_R_iris",
    "eye_R_pupil",
    "eye_R_highlight",
    "eye_R_upper_lash",
    "eye_R_lower_lash",
    "eye_R_closed_lid",
]
DEFAULT_PROJECT = (
    Path(__file__).resolve().parents[1]
    / "experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_face_detail_rebuild_v1"
)


@dataclass(frozen=True)
class Transform:
    translate: tuple[float, float] = (0.0, 0.0)
    scale: tuple[float, float] = (1.0, 1.0)
    rotate: float = 0.0
    opacity: float = 1.0


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def load_project(project_dir: Path) -> dict[str, Any]:
    project = load_json(project_dir / "character.json")
    rig_path = project_dir / "mini_rig.json"
    project["_mini_rig"] = load_json(rig_path) if rig_path.exists() else None
    return project


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def bbox_center(bbox: list[int]) -> tuple[float, float]:
    return (bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2)


def union_bbox(parts: list[dict[str, Any]], pad: int = 0) -> list[int]:
    left = min(part["bbox"][0] for part in parts)
    top = min(part["bbox"][1] for part in parts)
    right = max(part["bbox"][0] + part["bbox"][2] for part in parts)
    bottom = max(part["bbox"][1] + part["bbox"][3] for part in parts)
    return [left - pad, top - pad, right - left + pad * 2, bottom - top + pad * 2]


def bbox_mask(canvas_size: tuple[int, int], bbox: list[int]) -> np.ndarray:
    width, height = canvas_size
    x, y, w, h = bbox
    left = max(0, x)
    top = max(0, y)
    right = min(width, x + w)
    bottom = min(height, y + h)
    mask = np.zeros((height, width), dtype=bool)
    if right > left and bottom > top:
        mask[top:bottom, left:right] = True
    return mask


def merge_transform(a: Transform, b: Transform) -> Transform:
    return Transform(
        translate=(a.translate[0] + b.translate[0], a.translate[1] + b.translate[1]),
        scale=(a.scale[0] * b.scale[0], a.scale[1] * b.scale[1]),
        rotate=a.rotate + b.rotate,
        opacity=a.opacity * b.opacity,
    )


def transform_from_deltas(deltas: dict[str, Any]) -> Transform:
    translate = deltas.get("translate") or [0, 0]
    scale = deltas.get("scale") or [1, 1]
    return Transform(
        translate=(float(translate[0] or 0), float(translate[1] or 0)),
        scale=(float(scale[0]), float(scale[1])),
        rotate=float(deltas.get("rotate") or 0),
        opacity=float(deltas.get("opacity", 1)),
    )


def interpolate_transform(a: Transform, b: Transform, t: float) -> Transform:
    return Transform(
        translate=(lerp(a.translate[0], b.translate[0], t), lerp(a.translate[1], b.translate[1], t)),
        scale=(lerp(a.scale[0], b.scale[0], t), lerp(a.scale[1], b.scale[1], t)),
        rotate=lerp(a.rotate, b.rotate, t),
        opacity=lerp(a.opacity, b.opacity, t),
    )


def sample_transform(keyframes: list[dict[str, Any]], value: float) -> Transform:
    if not keyframes:
        return Transform()
    keyframes = sorted(keyframes, key=lambda item: item["key_value"])
    if value <= keyframes[0]["key_value"]:
        return transform_from_deltas(keyframes[0]["deltas"])
    if value >= keyframes[-1]["key_value"]:
        return transform_from_deltas(keyframes[-1]["deltas"])
    for lower, upper in zip(keyframes, keyframes[1:]):
        if lower["key_value"] <= value <= upper["key_value"]:
            span = upper["key_value"] - lower["key_value"] or 1
            t = clamp((value - lower["key_value"]) / span, 0, 1)
            return interpolate_transform(transform_from_deltas(lower["deltas"]), transform_from_deltas(upper["deltas"]), t)
    return Transform()


def sample_opacity(keyframes: list[dict[str, Any]], value: float, mode: str) -> float:
    if not keyframes:
        return 1.0
    keyframes = sorted(keyframes, key=lambda item: item["value"])
    if mode == "step_nearest":
        return min(keyframes, key=lambda item: abs(item["value"] - value))["opacity"]
    if value <= keyframes[0]["value"]:
        return float(keyframes[0]["opacity"])
    if value >= keyframes[-1]["value"]:
        return float(keyframes[-1]["opacity"])
    for lower, upper in zip(keyframes, keyframes[1:]):
        if lower["value"] <= value <= upper["value"]:
            span = upper["value"] - lower["value"] or 1
            return lerp(float(lower["opacity"]), float(upper["opacity"]), clamp((value - lower["value"]) / span, 0, 1))
    return 1.0


def group_by(items: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        result.setdefault(item[key], []).append(item)
    return result


def parameter_map(project: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {param["id"]: param for param in project["parameters"]}


def default_parameters(project: dict[str, Any]) -> dict[str, float]:
    return {param["id"]: float(param["default"]) for param in project["parameters"]}


def binding_transform(project: dict[str, Any], parameters: dict[str, float], target_id: str) -> Transform:
    params = parameter_map(project)
    transform = Transform()
    bindings = [item for item in effective_keyform_bindings(project) if item["target_id"] == target_id]
    for parameter_id, rows in group_by(bindings, "parameter_id").items():
        param = params.get(parameter_id)
        if not param:
            continue
        value = parameters.get(parameter_id, float(param["default"]))
        keyframes = [{"key_value": float(param["default"]), "deltas": {}}] + rows
        transform = merge_transform(transform, sample_transform(keyframes, value))
    return transform


def binding_key(binding: dict[str, Any]) -> tuple[Any, Any, Any]:
    return (binding.get("parameter_id"), binding.get("target_id"), binding.get("key_value"))


def effective_keyform_bindings(project: dict[str, Any]) -> list[dict[str, Any]]:
    overrides = (project.get("_mini_rig") or {}).get("keyform_overrides") or []
    if not overrides:
        return list(project.get("keyform_bindings", []))
    override_keys = {binding_key(binding) for binding in overrides}
    return [binding for binding in project.get("keyform_bindings", []) if binding_key(binding) not in override_keys] + list(overrides)


def primary_deformer(project: dict[str, Any], part_id: str) -> dict[str, Any] | None:
    deformers = project.get("deformers", [])
    preferred = ["Eye_L", "Eye_R", "Mouth", "Hair_Front", "Hair_Back"]
    for deformer_id in preferred:
        for deformer in deformers:
            if deformer["id"] == deformer_id and part_id in deformer.get("child_ids", []):
                return deformer
    for deformer in deformers:
        if deformer["id"] != "Root" and part_id in deformer.get("child_ids", []):
            if "hair" in part_id:
                head = next((item for item in deformers if item["id"] == "Head_X"), None)
                if head:
                    return head
            return deformer
    return None


def deformer_transform(project: dict[str, Any], parameters: dict[str, float], deformer: dict[str, Any] | None) -> Transform:
    if not deformer:
        return Transform()
    by_id = {item["id"]: item for item in project.get("deformers", [])}
    chain = []
    current: dict[str, Any] | None = deformer
    while current:
        chain.insert(0, current)
        current = by_id.get(current.get("parent_id"))
    result = Transform()
    for item in chain:
        result = merge_transform(result, binding_transform(project, parameters, item["id"]))
    return result


def is_eye_ball_detail_part(part_id: str) -> bool:
    return part_id.endswith("_iris") or part_id.endswith("_pupil") or part_id.endswith("_highlight")


def neutral_activation_parameters(part_id: str) -> set[str]:
    ids: set[str] = set()
    if part_id.startswith("eye_L_"):
        ids.add("ParamEyeLOpen")
        if is_eye_ball_detail_part(part_id) or part_id == "eye_L_white":
            ids.update(["ParamEyeBallX", "ParamEyeBallY"])
    if part_id.startswith("eye_R_"):
        ids.add("ParamEyeROpen")
        if is_eye_ball_detail_part(part_id) or part_id == "eye_R_white":
            ids.update(["ParamEyeBallX", "ParamEyeBallY"])
    if part_id.startswith("mouth_"):
        ids.update(["ParamMouthOpenY", "ParamMouthForm"])
    if part_id.startswith("hair_front_"):
        ids.add("ParamHairFront")
    if part_id.startswith("hair_side_"):
        ids.add("ParamHairSide")
    if part_id.startswith("hair_back_"):
        ids.add("ParamHairBack")
    if part_id in {"torso_base", "neck", "shoulder_L", "shoulder_R", "arm_L_upper_simple", "arm_R_upper_simple"}:
        ids.update(["ParamBodyAngleX", "ParamBodyAngleY", "ParamBreath"])
    if "cloth" in part_id or part_id.startswith("collar_"):
        ids.update(["ParamBodyAngleX", "ParamBodyAngleY", "ParamBreath"])
    return ids


def parameter_moved(project: dict[str, Any], parameters: dict[str, float], parameter_id: str) -> bool:
    params = parameter_map(project)
    param = params.get(parameter_id)
    if not param:
        return False
    return abs(parameters.get(parameter_id, float(param["default"])) - float(param["default"])) > 0.001


def part_opacity(project: dict[str, Any], parameters: dict[str, float], part_id: str) -> float:
    part = next(item for item in project["parts"] if item["id"] == part_id)
    opacity = float(part.get("opacity", 1))
    has_neutral_suppression = False
    params = parameter_map(project)
    for keyform in project.get("part_opacity_keyframes", []):
        if keyform["part_id"] != part_id:
            continue
        if str(keyform.get("purpose", "")).startswith("neutral visual repair"):
            has_neutral_suppression = True
            continue
        param = params.get(keyform["parameter_id"])
        if not param:
            continue
        value = parameters.get(keyform["parameter_id"], float(param["default"]))
        opacity *= sample_opacity(keyform.get("keyframes", []), value, keyform.get("mode", "linear"))
    if has_neutral_suppression:
        activators = neutral_activation_parameters(part_id)
        if not activators or not any(parameter_moved(project, parameters, parameter_id) for parameter_id in activators):
            opacity *= 0
    return clamp(opacity, 0, 1)


def part_transform(project: dict[str, Any], parameters: dict[str, float], part: dict[str, Any]) -> Transform:
    base = deformer_transform(project, parameters, primary_deformer(project, part["id"]))
    own = binding_transform(project, parameters, part["id"])
    return merge_transform(base, own)


def transform_image(image: Image.Image, center: tuple[float, float], transform: Transform) -> Image.Image:
    sx = transform.scale[0] or 1
    sy = transform.scale[1] or 1
    tx, ty = transform.translate
    cx, cy = center
    if abs(transform.rotate) > 0.001:
        # The current eye validation modes do not use rotation. Keep a simple
        # fallback so non-eye rows remain renderable if future modes expand.
        image = image.rotate(transform.rotate, center=center, resample=Image.Resampling.BICUBIC)
    coeffs = (
        1 / sx,
        0,
        cx - (cx + tx) / sx,
        0,
        1 / sy,
        cy - (cy + ty) / sy,
    )
    return image.transform(image.size, Image.Transform.AFFINE, coeffs, resample=Image.Resampling.BICUBIC)


def composite_project(project: dict[str, Any], project_dir: Path, parameters: dict[str, float]) -> Image.Image:
    canvas_size = tuple(project["canvas_size"])
    canvas = Image.new("RGBA", canvas_size, (244, 240, 232, 255))
    for part in sorted(project["parts"], key=lambda item: item["draw_order"]):
        opacity = part_opacity(project, parameters, part["id"])
        transform = part_transform(project, parameters, part)
        if opacity <= 0.01 or transform.opacity <= 0.01:
            continue
        image = Image.open(project_dir / part["source_path"]).convert("RGBA")
        transformed = transform_image(image, bbox_center(part["bbox"]), transform)
        alpha = transformed.getchannel("A")
        alpha = Image.fromarray(np.clip(np.asarray(alpha, dtype=np.float32) * opacity * transform.opacity, 0, 255).astype(np.uint8))
        transformed.putalpha(alpha)
        canvas.alpha_composite(transformed)
    return canvas


def changed_mask(a: Image.Image, b: Image.Image, threshold: int) -> np.ndarray:
    arr_a = np.asarray(a.convert("RGBA"), dtype=np.int16)
    arr_b = np.asarray(b.convert("RGBA"), dtype=np.int16)
    diff = np.abs(arr_a - arr_b)
    return np.max(diff, axis=2) > threshold


def mode_definitions(project: dict[str, Any]) -> list[dict[str, Any]]:
    base = default_parameters(project)
    modes = [
        {"id": "neutral", "label_ko": "중립", "parameters": {}},
        {"id": "eye_ball_x_left", "label_ko": "눈동자 왼쪽", "parameters": {"ParamEyeBallX": -1}},
        {"id": "eye_ball_x_right", "label_ko": "눈동자 오른쪽", "parameters": {"ParamEyeBallX": 1}},
        {"id": "eye_ball_y_up", "label_ko": "눈동자 위", "parameters": {"ParamEyeBallY": -1}},
        {"id": "eye_ball_y_down", "label_ko": "눈동자 아래", "parameters": {"ParamEyeBallY": 1}},
        {"id": "eye_l_closed", "label_ko": "왼눈 닫힘", "parameters": {"ParamEyeLOpen": 0}},
        {"id": "eye_r_closed", "label_ko": "오른눈 닫힘", "parameters": {"ParamEyeROpen": 0}},
        {"id": "both_eyes_closed", "label_ko": "양눈 닫힘", "parameters": {"ParamEyeLOpen": 0, "ParamEyeROpen": 0}},
    ]
    for mode in modes:
        values = dict(base)
        values.update(mode["parameters"])
        mode["resolved_parameters"] = values
    return modes


def contract_checks(project: dict[str, Any]) -> dict[str, Any]:
    eye_ball_bindings = [item for item in effective_keyform_bindings(project) if item["parameter_id"] in {"ParamEyeBallX", "ParamEyeBallY"}]
    bad_eye_ball_targets = sorted({item["target_id"] for item in eye_ball_bindings if item["target_id"] not in EYE_BALL_ALLOWED_TARGETS})
    missing_eye_ball_targets = sorted(EYE_BALL_ALLOWED_TARGETS - {item["target_id"] for item in eye_ball_bindings})
    eye_open_bindings = [item for item in effective_keyform_bindings(project) if item["parameter_id"] in {"ParamEyeLOpen", "ParamEyeROpen"}]
    bad_eye_open_targets = sorted(
        {
            item["target_id"]
            for item in eye_open_bindings
            if item["target_id"] not in {"eye_L_warp", "eye_R_warp"}
        }
    )
    return {
        "eye_ball_allowed_target_status": "PASS" if not bad_eye_ball_targets and not missing_eye_ball_targets else "FAIL",
        "eye_ball_binding_count": len(eye_ball_bindings),
        "bad_eye_ball_targets": bad_eye_ball_targets,
        "missing_eye_ball_targets": missing_eye_ball_targets,
        "eye_open_target_status": "PASS" if not bad_eye_open_targets else "FAIL",
        "bad_eye_open_targets": bad_eye_open_targets,
    }


def build_contact_sheet(images: list[tuple[str, Image.Image]], out_path: Path) -> None:
    thumb_w, thumb_h = 320, 320
    cols = 4
    rows = math.ceil(len(images) / cols)
    sheet = Image.new("RGB", (cols * thumb_w, rows * thumb_h), (245, 242, 235))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, (label, image) in enumerate(images):
        col = index % cols
        row = index // cols
        thumb = image.convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = col * thumb_w
        y = row * thumb_h
        sheet.paste(thumb, (x, y))
        draw.rectangle([x, y, x + thumb_w - 1, y + 22], fill=(20, 24, 32))
        draw.text((x + 6, y + 6), label, fill=(255, 255, 255), font=font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def mode_allowed_mask(project: dict[str, Any], mode_id: str, pad: int) -> np.ndarray:
    parts_by_id = {part["id"]: part for part in project["parts"]}
    canvas_size = tuple(project["canvas_size"])
    left = union_bbox([parts_by_id[part_id] for part_id in LEFT_EYE_PARTS if part_id in parts_by_id], pad)
    right = union_bbox([parts_by_id[part_id] for part_id in RIGHT_EYE_PARTS if part_id in parts_by_id], pad)
    if mode_id == "eye_l_closed":
        return bbox_mask(canvas_size, left)
    if mode_id == "eye_r_closed":
        return bbox_mask(canvas_size, right)
    if mode_id == "neutral":
        return np.zeros((canvas_size[1], canvas_size[0]), dtype=bool)
    return bbox_mask(canvas_size, left) | bbox_mask(canvas_size, right)


def validate(project_dir: Path, out_dir: Path, threshold: int, pad: int, warn_pixels: int, fail_pixels: int) -> dict[str, Any]:
    project = load_project(project_dir)
    modes = mode_definitions(project)
    rendered: dict[str, Image.Image] = {}
    for mode in modes:
        rendered[mode["id"]] = composite_project(project, project_dir, mode["resolved_parameters"])
    neutral = rendered["neutral"]

    results = []
    for mode in modes:
        mode_id = mode["id"]
        if mode_id == "neutral":
            results.append(
                {
                    "id": mode_id,
                    "label_ko": mode["label_ko"],
                    "status": "PASS",
                    "outside_changed_pixels": 0,
                    "allowed_changed_pixels": 0,
                    "parameters": mode["parameters"],
                }
            )
            continue
        mask = changed_mask(neutral, rendered[mode_id], threshold)
        allowed = mode_allowed_mask(project, mode_id, pad)
        outside_changed = int(np.logical_and(mask, ~allowed).sum())
        allowed_changed = int(np.logical_and(mask, allowed).sum())
        status = "PASS" if outside_changed <= warn_pixels else "REVISE"
        if outside_changed > fail_pixels:
            status = "FAIL"
        results.append(
            {
                "id": mode_id,
                "label_ko": mode["label_ko"],
                "status": status,
                "outside_changed_pixels": outside_changed,
                "allowed_changed_pixels": allowed_changed,
                "parameters": mode["parameters"],
            }
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    for mode_id, image in rendered.items():
        image.save(out_dir / f"{mode_id}.png")
    build_contact_sheet([(mode["label_ko"], rendered[mode["id"]]) for mode in modes], out_dir / "eye_mode_contact_sheet.png")

    report = {
        "schema_version": 1,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "project": str(project_dir),
        "mini_rig_present": project.get("_mini_rig") is not None,
        "mini_rig_keyform_overrides": len((project.get("_mini_rig") or {}).get("keyform_overrides") or []),
        "threshold": threshold,
        "eye_roi_padding": pad,
        "warn_pixels": warn_pixels,
        "fail_pixels": fail_pixels,
        "contract_checks": contract_checks(project),
        "modes": results,
    }
    contract_ok = (
        report["contract_checks"]["eye_ball_allowed_target_status"] == "PASS"
        and report["contract_checks"]["eye_open_target_status"] == "PASS"
    )
    mode_ok = all(row["status"] == "PASS" for row in results)
    report["status"] = "PASS" if contract_ok and mode_ok else "REVISE"
    (out_dir / "eye_mode_validation_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (out_dir / "eye_mode_validation_report.md").write_text(markdown_report(report), encoding="utf-8")
    return report


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Mini Cubism Eye Mode Validation",
        "",
        f"- Status: `{report['status']}`",
        f"- Project: `{report['project']}`",
        f"- Mini rig present: `{report['mini_rig_present']}`",
        f"- Mini rig keyform overrides: `{report['mini_rig_keyform_overrides']}`",
        f"- Pixel threshold: `{report['threshold']}`",
        f"- Eye ROI padding: `{report['eye_roi_padding']}`",
        "",
        "## Contract Checks",
        "",
        f"- EyeBallX/Y target whitelist: `{report['contract_checks']['eye_ball_allowed_target_status']}`",
        f"- EyeBallX/Y binding count: `{report['contract_checks']['eye_ball_binding_count']}`",
        f"- EyeOpen target check: `{report['contract_checks']['eye_open_target_status']}`",
        "",
        "## Mode Leakage",
        "",
        "| Mode | Status | Outside changed pixels | Allowed changed pixels |",
        "|---|---:|---:|---:|",
    ]
    for row in report["modes"]:
        lines.append(
            f"| {row['label_ko']} (`{row['id']}`) | `{row['status']}` | {row['outside_changed_pixels']} | {row['allowed_changed_pixels']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--threshold", type=int, default=12)
    parser.add_argument("--eye-roi-pad", type=int, default=28)
    parser.add_argument("--warn-pixels", type=int, default=0)
    parser.add_argument("--fail-pixels", type=int, default=250)
    args = parser.parse_args()

    project_dir = args.project.resolve()
    out_dir = args.out.resolve() if args.out else project_dir / "reports/eye_mode_validation"
    report = validate(project_dir, out_dir, args.threshold, args.eye_roi_pad, args.warn_pixels, args.fail_pixels)
    print(json.dumps({"ok": report["status"] == "PASS", "status": report["status"], "report": str(out_dir / "eye_mode_validation_report.json")}, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

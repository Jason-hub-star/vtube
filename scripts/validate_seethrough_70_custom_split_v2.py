#!/usr/bin/env python3
"""QA-first validator for See-through 70+ custom split v2 candidates."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = ROOT / "experiments/mini-cubism-dedicated-model-v1-001"
DEFAULT_MANIFEST = DEFAULT_EXPERIMENT / "seethrough_70_custom_split_v2/candidate_layer_manifest.json"
CANVAS = (2048, 2048)

CRITICAL_GROUPS = {"face_ear", "eyes_keypose", "mouth_keypose"}
BAD_DERIVATION_TOKENS = ("generated", "procedural", "fallback")
REQUIRED_COUNTS = {
    "parts": 70,
    "hair_parts": 18,
    "eye_parts": 16,
    "mouth_parts": 8,
    "physics_targets": 12,
}
ROI_LIMITS = {
    "face_ear": (430, 230, 1610, 1150),
    "eyes_keypose": (650, 430, 1370, 820),
    "mouth_keypose": (760, 720, 1250, 990),
}
REQUIRED_EYE_HIDDEN = {"iris_L", "iris_R", "pupil_L", "pupil_R", "catchlight_L", "catchlight_R"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        fail(f"missing JSON: {path}")
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def font(size: int) -> ImageFont.ImageFont:
    for candidate in [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def group_lookup(part_groups: dict[str, list[str]]) -> dict[str, str]:
    return {part_id: group for group, parts in part_groups.items() for part_id in parts}


def bbox_from_alpha(path: Path) -> tuple[list[int], int, float]:
    image = Image.open(path).convert("RGBA")
    if image.size != CANVAS:
        return [0, 0, 0, 0], 0, 0.0
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    nonzero = sum(alpha.histogram()[1:])
    if not bbox:
        return [0, 0, 0, 0], 0, 0.0
    left, top, right, bottom = bbox
    return [left, top, right - left, bottom - top], nonzero, nonzero / (CANVAS[0] * CANVAS[1])


def bbox_center(bbox: list[int]) -> tuple[float, float]:
    x, y, w, h = bbox
    return x + w / 2, y + h / 2


def center_in_roi(bbox: list[int], roi: tuple[int, int, int, int]) -> bool:
    cx, cy = bbox_center(bbox)
    x0, y0, x1, y1 = roi
    return x0 <= cx <= x1 and y0 <= cy <= y1


def is_bad_derivation(mode: str) -> bool:
    lower = mode.lower()
    return any(token in lower for token in BAD_DERIVATION_TOKENS)


def classify_action(layer: dict[str, Any], issues: list[str]) -> str:
    group = layer.get("group", "")
    mode = str(layer.get("derivation_mode", ""))
    if "VISUAL_FAIL_DERIVATION" in issues or "VISUAL_FAIL_PROCEDURAL_FACE_FIXTURE" in issues:
        return "VISUAL_FAIL"
    if "ROI_FAIL" in issues:
        return "RETRY_ROI_SEETHROUGH"
    if "ALPHA_EMPTY" in issues or "ALPHA_TOO_TINY" in issues:
        return "DISCARD"
    if group in {"eyes_keypose", "mouth_keypose"} and is_bad_derivation(mode):
        return "REGENERATE_KEYPOSE_ASSET"
    if issues:
        return "NEEDS_HUMAN_REVIEW"
    return "KEEP_SEETHROUGH_MASK"


def evaluate_layer(layer: dict[str, Any], part_groups: dict[str, list[str]]) -> dict[str, Any]:
    part_id = layer.get("part_id") or layer.get("id")
    if not part_id:
        return {"part_id": "<missing>", "issues": ["MISSING_PART_ID"], "action": "DISCARD"}
    lookup = group_lookup(part_groups)
    group = layer.get("group") or lookup.get(part_id, "unknown")
    output_path = layer.get("output_path")
    issues: list[str] = []
    bbox = layer.get("bbox", [0, 0, 0, 0])
    coverage = float(layer.get("alpha_coverage", 0) or 0)
    nonzero = 0
    resolved_path = resolve(output_path) if output_path else None

    if not output_path or not resolved_path or not resolved_path.exists():
        issues.append("MISSING_FILE")
    else:
        alpha_bbox, nonzero, alpha_coverage = bbox_from_alpha(resolved_path)
        if Image.open(resolved_path).size != CANVAS:
            issues.append("NOT_FULL_CANVAS_2048")
        if nonzero == 0:
            issues.append("ALPHA_EMPTY")
        bbox = alpha_bbox if alpha_bbox != [0, 0, 0, 0] else bbox
        coverage = alpha_coverage

    derivation_mode = str(layer.get("derivation_mode", ""))
    if group in CRITICAL_GROUPS and is_bad_derivation(derivation_mode):
        issues.append("VISUAL_FAIL_DERIVATION")
    if derivation_mode == "face_v1_procedural_replacement":
        issues.append("VISUAL_FAIL_PROCEDURAL_FACE_FIXTURE")
    if group in ROI_LIMITS and nonzero > 0 and not center_in_roi(bbox, ROI_LIMITS[group]):
        issues.append("ROI_FAIL")
    if nonzero and nonzero < 32:
        issues.append("ALPHA_TOO_TINY")
    if group in {"face_ear", "eyes_keypose", "mouth_keypose"} and coverage > 0.035:
        issues.append("ALPHA_TOO_BROAD_FOR_FACE_REGION")
    if group == "mouth_keypose" and bbox[1] < 680:
        issues.append("MOUTH_TOO_HIGH")
    if group == "eyes_keypose" and (bbox[1] < 430 or bbox[1] > 760):
        issues.append("EYE_ROI_Y_SUSPICIOUS")

    action = classify_action({**layer, "group": group}, issues)
    return {
        "part_id": part_id,
        "group": group,
        "derivation_mode": derivation_mode,
        "bbox": bbox,
        "alpha_coverage": round(coverage, 8),
        "nonzero_alpha": nonzero,
        "output_path": output_path,
        "issues": issues,
        "action": action,
    }


def count_parts(layers: list[dict[str, Any]], part_groups: dict[str, list[str]]) -> dict[str, int]:
    seen = {layer["part_id"] for layer in layers if layer.get("part_id")}
    hair = set(part_groups.get("hair_physics", []))
    eye = set(part_groups.get("eyes_keypose", []))
    mouth = set(part_groups.get("mouth_keypose", []))
    physics = (
        set(part_groups.get("hair_physics", []))
        | set(part_groups.get("clothes_accessory_physics", []))
        | {part for part in part_groups.get("face_ear", []) if part.startswith("ear_")}
    )
    return {
        "parts": len(seen),
        "hair_parts": len(seen & hair),
        "eye_parts": len(seen & eye),
        "mouth_parts": len(seen & mouth),
        "physics_targets": len(seen & physics),
    }


def manifest_structural_issues(manifest: dict[str, Any], part_groups: dict[str, list[str]], layers: list[dict[str, Any]]) -> dict[str, Any]:
    issues: dict[str, Any] = {}
    counts = count_parts(layers, part_groups)
    floor_failures = {key: {"actual": counts[key], "required": req} for key, req in REQUIRED_COUNTS.items() if counts[key] < req}
    if floor_failures:
        issues["floor_failures"] = floor_failures

    ids = [layer.get("part_id") for layer in layers]
    duplicates = sorted([part for part, count in Counter(ids).items() if part and count > 1])
    if duplicates:
        issues["duplicate_part_ids"] = duplicates

    mouth_states = manifest.get("mouth_visibility_groups", {}).get("states", {})
    seen_state: dict[str, str] = {}
    overlap = []
    for state, parts in mouth_states.items():
        for part in parts:
            if part in seen_state:
                overlap.append(part)
            seen_state[part] = state
    missing_mouth = sorted(set(part_groups.get("mouth_keypose", [])) - set(seen_state))
    if overlap:
        issues["mouth_visibility_overlap"] = sorted(set(overlap))
    if missing_mouth:
        issues["mouth_visibility_missing"] = missing_mouth

    hidden = set(manifest.get("eye_closed_hidden_parts", []))
    missing_hidden = sorted(REQUIRED_EYE_HIDDEN - hidden)
    if missing_hidden:
        issues["eye_closed_hidden_missing"] = missing_hidden
    return {"counts": counts, "issues": issues}


def preview_tile(layer: dict[str, Any], canonical: Image.Image | None, tile_size: int = 220) -> Image.Image:
    path = resolve(layer["output_path"]) if layer.get("output_path") else None
    bbox = layer.get("bbox") or [0, 0, 0, 0]
    if canonical is not None and bbox[2] and bbox[3]:
        pad = 70
        x, y, w, h = bbox
        crop_box = (max(0, x - pad), max(0, y - pad), min(CANVAS[0], x + w + pad), min(CANVAS[1], y + h + pad))
        base = canonical.crop(crop_box).convert("RGBA")
    else:
        base = Image.new("RGBA", (tile_size, tile_size), (245, 245, 245, 255))
        crop_box = None
    if path and path.exists():
        part = Image.open(path).convert("RGBA")
        if crop_box:
            part = part.crop(crop_box)
        tint = Image.new("RGBA", part.size, (255, 60, 40, 145))
        part_alpha = part.getchannel("A")
        overlay = Image.new("RGBA", part.size, (0, 0, 0, 0))
        overlay.paste(tint, (0, 0), part_alpha)
        base.alpha_composite(overlay)
    base.thumbnail((tile_size, tile_size - 44), Image.Resampling.LANCZOS)
    tile = Image.new("RGB", (tile_size, tile_size), "#f8f6f0")
    tile.paste(base.convert("RGB"), ((tile_size - base.width) // 2, 8))
    return tile


def build_contact_sheet(rows: list[dict[str, Any]], canonical_path: Path | None, out: Path, title: str) -> None:
    canonical = Image.open(canonical_path).convert("RGBA") if canonical_path and canonical_path.exists() else None
    selected = rows[:40]
    cols = 4
    cell_w, cell_h = 300, 300
    header_h = 86
    sheet = Image.new("RGB", (cols * cell_w, header_h + math.ceil(len(selected) / cols) * cell_h), "#f4f0e8")
    draw = ImageDraw.Draw(sheet)
    draw.text((18, 16), title, fill="#202124", font=font(24))
    draw.text((18, 50), "Red overlay shows candidate alpha on canonical crop; only failed/review-needed parts are shown.", fill="#5f6368", font=font(13))
    small = font(11)
    for index, row in enumerate(selected):
        x = (index % cols) * cell_w
        y = header_h + (index // cols) * cell_h
        draw.rectangle([x + 8, y + 8, x + cell_w - 8, y + cell_h - 8], fill="#ffffff", outline="#d4cec5")
        tile = preview_tile(row, canonical)
        sheet.paste(tile, (x + 40, y + 14))
        draw.text((x + 16, y + 238), row["part_id"][:34], fill="#202124", font=small)
        draw.text((x + 16, y + 254), row.get("action", "")[:34], fill="#9b2c2c", font=small)
        issue_text = ",".join(row.get("issues", []))[:42]
        draw.text((x + 16, y + 270), issue_text, fill="#5f6368", font=small)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def build_summary(out: Path, report: dict[str, Any]) -> None:
    counts = report["counts"]
    actions = report["action_counts"]
    status = report["status"]
    lines = [
        "# See-through 70+ Custom Split v2 QA Summary",
        "",
        f"- Status: {status}",
        f"- Structural status: {report['structural_status']}",
        f"- Visual status: {report['visual_status']}",
        f"- Parts / Hair / Eye / Mouth / Physics: {counts['parts']} / {counts['hair_parts']} / {counts['eye_parts']} / {counts['mouth_parts']} / {counts['physics_targets']}",
        f"- Actions: {dict(actions)}",
        "",
    ]
    if status != "PASS":
        lines += [
            "## Next Automatic Action",
            "",
            "- Do not build or promote a Mini Cubism project from this candidate yet.",
            "- Retry ROI See-through or regenerate style-matched face/eye/mouth keypose assets for failed critical parts.",
            "- Use the problem and face close-up contact sheets for review instead of inspecting individual PNGs.",
            "",
        ]
    else:
        lines += [
            "## Next Automatic Action",
            "",
            "- Candidate can advance to Mini Cubism project generation and motion evidence.",
            "",
        ]
    out.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate See-through 70+ custom split v2 candidates before rig promotion.")
    parser.add_argument("--experiment", default=str(DEFAULT_EXPERIMENT))
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--part-spec")
    parser.add_argument("--canonical")
    args = parser.parse_args()

    exp = Path(args.experiment).resolve()
    manifest_path = resolve(args.manifest)
    manifest = load_json(manifest_path)
    part_spec_path = resolve(args.part_spec) if args.part_spec else resolve(manifest.get("source_part_spec_manifest", exp / "part_spec_manifest.json"))
    part_spec = load_json(part_spec_path)
    part_groups = manifest.get("part_groups") or part_spec.get("part_groups", {})
    layers = manifest.get("layers", [])
    if not layers:
        fail("manifest has no layers")

    evaluated = [evaluate_layer(layer, part_groups) for layer in layers]
    structure = manifest_structural_issues(manifest, part_groups, evaluated)
    visual_failures = [row for row in evaluated if row["action"] == "VISUAL_FAIL"]
    roi_failures = [row for row in evaluated if "ROI_FAIL" in row["issues"]]
    critical_visual_failures = [row for row in visual_failures if row["group"] in CRITICAL_GROUPS]
    action_counts = Counter(row["action"] for row in evaluated)
    issue_counts = Counter(issue for row in evaluated for issue in row["issues"])

    structural_status = "PASS" if not structure["issues"] else "FAIL"
    visual_status = "PASS" if not critical_visual_failures else "FAIL"
    status = "PASS" if structural_status == "PASS" and visual_status == "PASS" else "REVISE_VISUAL" if structural_status == "PASS" else "FAIL"

    canonical_path = resolve(args.canonical) if args.canonical else resolve(manifest.get("source_canonical", exp / "canonical/canonical_front_2048.png"))
    report_dir = exp / "seethrough_70_custom_split_v2" / "reports"
    problem_rows = [row for row in evaluated if row["issues"] or row["action"] != "KEEP_SEETHROUGH_MASK"]
    face_rows = [row for row in problem_rows if row["group"] in CRITICAL_GROUPS]
    problem_sheet = report_dir / "problem_contact_sheet.png"
    face_sheet = report_dir / "face_closeup_sheet.png"
    build_contact_sheet(problem_rows, canonical_path, problem_sheet, "See-through 70+ v2 Problem Sheet")
    build_contact_sheet(face_rows, canonical_path, face_sheet, "See-through 70+ v2 Face/Eye/Mouth Failures")

    report = {
        "schema_version": 1,
        "validated_at": now(),
        "experiment": str(exp),
        "manifest": str(manifest_path),
        "part_spec_manifest": str(part_spec_path),
        "status": status,
        "structural_status": structural_status,
        "visual_status": visual_status,
        "counts": structure["counts"],
        "required_counts": REQUIRED_COUNTS,
        "structural_issues": structure["issues"],
        "action_counts": dict(action_counts),
        "issue_counts": dict(issue_counts),
        "critical_visual_failures": [row["part_id"] for row in critical_visual_failures],
        "roi_failures": [row["part_id"] for row in roi_failures],
        "layer_actions": evaluated,
        "outputs": {
            "problem_contact_sheet": str(problem_sheet),
            "face_closeup_sheet": str(face_sheet),
            "review_summary": str(report_dir / "review_summary.md"),
        },
        "interpretation": [
            "Structural PASS does not imply visual production success.",
            "Generated/procedural/fallback critical face, eye, or mouth parts cannot advance without style-matched visual evidence.",
            "Face v1 procedural candidates are expected to fail this QA and remain a negative regression fixture.",
        ],
    }
    write_json(report_dir / "seethrough_70_custom_split_v2_qa_report.json", report)
    build_summary(report_dir / "review_summary.md", report)
    print(json.dumps({"ok": status == "PASS", "status": status, "structural_status": structural_status, "visual_status": visual_status, "counts": structure["counts"], "report": str(report_dir / "seethrough_70_custom_split_v2_qa_report.json")}, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

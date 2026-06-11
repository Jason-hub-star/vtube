#!/usr/bin/env python3
"""Convert manual semantic overrides into a reusable part localization template."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path("/Users/family/jason/Vtube")
PACK = ROOT / "experiments/cubism-v2-new-character-001/material_pack_v0"
OVERRIDES_PATH = PACK / "reports/manual_semantic_overrides.json"
MANIFEST_PATH = PACK / "layer_manifest.json"
OUT_JSON = PACK / "reports/part_localization_template.json"
OUT_MD = PACK / "reports/part_localization_template.md"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def union_bbox(boxes: list[list[int]], pad: int = 0) -> list[int]:
    valid = [box for box in boxes if box and box[2] > 0 and box[3] > 0]
    if not valid:
        return [0, 0, 2048, 2048]
    x0 = max(0, min(box[0] for box in valid) - pad)
    y0 = max(0, min(box[1] for box in valid) - pad)
    x1 = min(2048, max(box[0] + box[2] for box in valid) + pad)
    y1 = min(2048, max(box[1] + box[3] for box in valid) + pad)
    return [x0, y0, x1 - x0, y1 - y0]


def relative_box(box: list[int], basis: list[int]) -> list[float]:
    bx, by, bw, bh = basis
    x, y, w, h = box
    return [
        round((x - bx) / max(1, bw), 6),
        round((y - by) / max(1, bh), 6),
        round(w / max(1, bw), 6),
        round(h / max(1, bh), 6),
    ]


def relative_point(point: list[int], basis: list[int]) -> list[float]:
    bx, by, bw, bh = basis
    return [round((point[0] - bx) / max(1, bw), 6), round((point[1] - by) / max(1, bh), 6)]


def choose_basis(part_id: str, override: dict[str, Any], reference_bboxes: dict[str, list[int]]) -> str:
    group = override.get("expected_group") or ""
    if part_id.startswith("eye_L_"):
        return "eye_L"
    if part_id.startswith("eye_R_"):
        return "eye_R"
    if part_id.startswith("mouth_"):
        return "mouth"
    if part_id.startswith("brow_"):
        return "brow"
    if part_id.startswith("face_") or part_id in {"nose", "cheek_L", "cheek_R"} or group == "face_base":
        return "face"
    if part_id.startswith("hair_"):
        return "head"
    if any(token in part_id for token in ["torso", "neck", "shoulder", "arm_", "body"]):
        return "body"
    return "canvas"


def main() -> int:
    if not OVERRIDES_PATH.exists():
        raise SystemExit(f"Missing overrides: {OVERRIDES_PATH}")
    overrides_doc = load_json(OVERRIDES_PATH)
    manifest = load_json(MANIFEST_PATH)
    overrides = overrides_doc.get("overrides", {})
    by_part = {row["part_id"]: row for row in manifest.get("layers", [])}

    boxes = {part: row["roi"] for part, row in overrides.items()}
    reference_bboxes = {
        "canvas": [0, 0, 2048, 2048],
        "eye_L": union_bbox([box for part, box in boxes.items() if part.startswith("eye_L_")], pad=12),
        "eye_R": union_bbox([box for part, box in boxes.items() if part.startswith("eye_R_")], pad=12),
        "mouth": union_bbox([box for part, box in boxes.items() if part.startswith("mouth_")], pad=12),
        "brow": union_bbox([box for part, box in boxes.items() if part.startswith("brow_")], pad=12),
        "face": union_bbox([box for part, box in boxes.items() if part.startswith("face_") or part in {"nose", "cheek_L", "cheek_R"}], pad=20),
        "body": union_bbox([box for part, box in boxes.items() if any(token in part for token in ["torso", "neck", "shoulder", "arm_", "body"])], pad=24),
    }
    reference_bboxes["head"] = union_bbox(
        [
            reference_bboxes["eye_L"],
            reference_bboxes["eye_R"],
            reference_bboxes["mouth"],
            reference_bboxes["brow"],
            reference_bboxes["face"],
        ],
        pad=30,
    )

    parts: dict[str, Any] = {}
    anchor_outside = []
    for part_id, row in sorted(overrides.items()):
        basis_name = choose_basis(part_id, row, reference_bboxes)
        basis = reference_bboxes[basis_name]
        roi = [int(v) for v in row["roi"]]
        anchor = [int(v) for v in row["anchor"]]
        center_anchor = [round(roi[0] + roi[2] / 2), round(roi[1] + roi[3] / 2)]
        anchor_inside = roi[0] <= anchor[0] <= roi[0] + roi[2] and roi[1] <= anchor[1] <= roi[1] + roi[3]
        if not anchor_inside:
            anchor_outside.append(part_id)
        parts[part_id] = {
            "part_id": part_id,
            "semantic_role": row.get("semantic_role"),
            "expected_group": row.get("expected_group"),
            "source_type": by_part.get(part_id, {}).get("source_type"),
            "draw_order": by_part.get(part_id, {}).get("draw_order"),
            "basis": basis_name,
            "roi_abs": roi,
            "roi_rel": relative_box(roi, basis),
            "anchor_abs_saved": anchor,
            "anchor_abs_roi_center": center_anchor,
            "anchor_rel_saved": relative_point(anchor, basis),
            "anchor_rel_roi_center": relative_point(center_anchor, basis),
            "anchor_inside_roi": anchor_inside,
            "action": row.get("action", "REEXTRACT_FROM_CANONICAL"),
            "note": row.get("note", ""),
        }

    payload = {
        "schema_version": 1,
        "status": "PASS_PART_LOCALIZATION_TEMPLATE_READY" if parts else "FAIL_EMPTY_TEMPLATE",
        "generated_at": now(),
        "source_overrides": rel(OVERRIDES_PATH),
        "source_manifest": rel(MANIFEST_PATH),
        "canvas_size": [2048, 2048],
        "reference_bboxes": reference_bboxes,
        "parts": parts,
        "quality_notes": {
            "override_count": len(parts),
            "anchor_outside_roi_count": len(anchor_outside),
            "anchor_outside_roi_parts": anchor_outside,
            "anchor_policy": "Use roi center as extraction anchor by default; saved anchor is kept as human intent metadata because many saved anchors are outside ROI.",
            "generalization_policy": "For new matched front-facing v2_standard characters, map reference_bboxes to detected face/eye/mouth/body anchors, then apply roi_rel per part.",
        },
    }
    write_json(OUT_JSON, payload)
    OUT_MD.write_text(
        "\n".join(
            [
                "# Cubism v2 Part Localization Template",
                "",
                f"- status: `{payload['status']}`",
                f"- overrides: `{len(parts)}`",
                f"- anchor outside ROI: `{len(anchor_outside)}`",
                f"- json: `{rel(OUT_JSON)}`",
                "",
                "## Reference BBoxes",
                "",
                "| Basis | BBox |",
                "|---|---|",
                *[f"| `{key}` | `{value}` |" for key, value in reference_bboxes.items()],
                "",
                "## Policy",
                "",
                "- ROI absolute coordinates are used for current-candidate remasking.",
                "- ROI relative coordinates are the reusable template for future similarly framed characters.",
                "- Saved anchors are preserved, but ROI center is safer for extraction because many saved anchors are outside the ROI.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"ok": payload["status"].startswith("PASS"), "status": payload["status"], "parts": len(parts), "out": str(OUT_JSON)}, indent=2))
    return 0 if payload["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())

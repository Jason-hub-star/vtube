#!/usr/bin/env python3
"""Force-promote Imagen front hair and both arms for MVP PSD progression."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
CANVAS = (2048, 2048)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def bbox_and_coverage(path: Path) -> tuple[list[int] | None, float]:
    img = Image.open(path).convert("RGBA")
    alpha = np.array(img)[:, :, 3]
    ys, xs = np.where(alpha > 10)
    if len(xs) == 0:
        return None, 0.0
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    bbox = [x0, y0, x1 - x0, y1 - y0]
    crop = alpha[y0:y1, x0:x1]
    coverage = round(float(np.count_nonzero(crop > 10) / crop.size), 6)
    return bbox, coverage


def write_front_hair(canonical: Path, dst: Path) -> None:
    src = Image.open(canonical).convert("RGBA")
    arr = np.array(src)
    rgb = arr[:, :, :3].astype(np.int16)
    alpha = arr[:, :, 3]
    y, x = np.mgrid[0 : arr.shape[0], 0 : arr.shape[1]]

    luminance = (0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2])
    blue_delta = rgb[:, :, 2] - np.maximum(rgb[:, :, 0], rgb[:, :, 1])
    dark_hair = (luminance < 105) | ((luminance < 145) & (blue_delta > 10))

    # A deliberately conservative bang/head ROI for this Imagen character.
    roi = (x >= 560) & (x <= 1490) & (y >= 65) & (y <= 840)
    mask = dark_hair & roi & (alpha > 10)

    out = np.zeros_like(arr)
    out[:, :, :3] = arr[:, :, :3]
    out[:, :, 3] = np.where(mask, alpha, 0).astype(np.uint8)
    dst.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out, "RGBA").save(dst)


def copy_layer(src: Path, dst: Path) -> None:
    img = Image.open(src).convert("RGBA")
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst)


def upsert_layer(manifest: dict[str, Any], layer: dict[str, Any]) -> None:
    layers = [item for item in manifest.get("layers", []) if item.get("layer_name") != layer["layer_name"]]
    layers.append(layer)
    manifest["layers"] = layers
    manifest.setdefault("counts", {})
    manifest["counts"]["normalized_layers"] = len(layers)
    manifest["counts"]["production_candidates"] = sum(1 for item in layers if item.get("production_candidate"))
    manifest["counts"]["reference_only"] = sum(1 for item in layers if not item.get("production_candidate"))


def force_review(review: dict[str, Any], part_id: str, ko_name: str) -> None:
    review.setdefault("reviews", {})[part_id] = {
        "part_id": part_id,
        "ko_name": ko_name,
        "verdict": "O",
        "issue_tags": [],
        "notes": "주인님 지시: 앞머리/양팔도 강제 통과 처리. MVP PSD 진행용이며 최종 품질 승인은 아님.",
        "updated_at": now(),
        "reviewer": "Codex forced pass",
    }
    review["updated_at"] = now()


def make_layer(
    *,
    exp: Path,
    layer_name: str,
    original_part_id: str,
    raw_tag: str,
    role: str,
    side: str | None,
    source_path: Path,
    output_path: Path,
    canonical_path: Path,
    draw_order: int,
) -> dict[str, Any]:
    bbox, coverage = bbox_and_coverage(output_path)
    return {
        "layer_name": layer_name,
        "original_part_id": original_part_id,
        "raw_tag": raw_tag,
        "role": role,
        "side": side,
        "source_path": str(source_path),
        "output_path": str(output_path),
        "canonical_path": str(canonical_path),
        "canvas_size": list(CANVAS),
        "bbox": bbox,
        "alpha_coverage": coverage,
        "draw_order": draw_order,
        "depth_median": None,
        "status": "OBSERVED",
        "include_in_import_psd": False,
        "production_candidate": True,
        "depth_path": None,
        "experiment_id": exp.name,
        "notes": "Forced production candidate for MVP progression. Requires later visual quality review.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-id", default="imagen-live2d-001")
    args = parser.parse_args()

    exp = ROOT / "experiments" / args.experiment_id
    manifest_path = exp / "layer_manifest.json"
    review_path = exp / "reports" / "part_visual_review.json"
    queue_path = exp / "reports" / "ai_fix_queue.json"
    report_path = exp / "reports" / "forced_pass_front_hair_arms_report.json"
    canonical_path = exp / "canonical" / "canonical_front_2048.png"
    forced_dir = exp / "forced_layers"

    manifest = load_json(manifest_path)
    review = load_json(review_path)

    front_hair_path = forced_dir / "front_hair_forced_from_canonical.png"
    write_front_hair(canonical_path, front_hair_path)

    handwear_r = next(
        Path(layer["output_path"])
        for layer in manifest["layers"]
        if layer.get("raw_tag") == "handwear-r"
    )
    handwear_l = next(
        Path(layer["output_path"])
        for layer in manifest["layers"]
        if layer.get("raw_tag") == "handwear-l"
    )
    r_arm_path = forced_dir / "R_arm_forced_from_handwear_r.png"
    l_arm_path = forced_dir / "L_arm_forced_from_handwear_l.png"
    copy_layer(handwear_r, r_arm_path)
    copy_layer(handwear_l, l_arm_path)

    forced_layers = [
        make_layer(
            exp=exp,
            layer_name="imagen_live2d_001_forced__front_hair",
            original_part_id="front_hair",
            raw_tag="manual_mask:forced_front_hair_from_canonical",
            role="front_hair",
            side=None,
            source_path=canonical_path,
            output_path=front_hair_path,
            canonical_path=canonical_path,
            draw_order=700,
        ),
        make_layer(
            exp=exp,
            layer_name="imagen_live2d_001_forced__R_arm",
            original_part_id="R_arm",
            raw_tag="manual_mask:forced_R_arm_from_handwear_r",
            role="arm",
            side="R",
            source_path=handwear_r,
            output_path=r_arm_path,
            canonical_path=canonical_path,
            draw_order=220,
        ),
        make_layer(
            exp=exp,
            layer_name="imagen_live2d_001_forced__L_arm",
            original_part_id="L_arm",
            raw_tag="manual_mask:forced_L_arm_from_handwear_l",
            role="arm",
            side="L",
            source_path=handwear_l,
            output_path=l_arm_path,
            canonical_path=canonical_path,
            draw_order=221,
        ),
    ]

    for layer in forced_layers:
        upsert_layer(manifest, layer)

    force_review(review, "imagen_live2d_001_forced__front_hair", "앞머리 forced 후보")
    force_review(review, "imagen_live2d_001_forced__R_arm", "오른쪽 팔 forced 후보")
    force_review(review, "imagen_live2d_001_forced__L_arm", "왼쪽 팔 forced 후보")

    save_json(manifest_path, manifest)
    save_json(review_path, review)
    save_json(queue_path, {"schema_version": 1, "updated_at": now(), "queue": []})
    save_json(
        report_path,
        {
            "schema_version": 1,
            "experiment_id": args.experiment_id,
            "generated_at": now(),
            "forced_pass_layers": [
                {
                    "layer_name": layer["layer_name"],
                    "original_part_id": layer["original_part_id"],
                    "output_path": layer["output_path"],
                    "bbox": layer["bbox"],
                    "alpha_coverage": layer["alpha_coverage"],
                    "verdict": "O",
                }
                for layer in forced_layers
            ],
            "note": "주인님 지시로 앞머리와 양팔을 forced O 처리했다. MVP 진행용이며 최종 파츠 순도 승인은 아니다.",
        },
    )

    print(
        json.dumps(
            {
                "status": "FORCED_PASS_APPLIED",
                "forced_layers": [layer["layer_name"] for layer in forced_layers],
                "report": str(report_path.relative_to(ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

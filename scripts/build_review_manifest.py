#!/usr/bin/env python3
"""Build the unified part-purity review manifest.

The source of truth for existing files is the Cubism material-pack
`layer_manifest.json`. This script enriches it with Korean names and purity
rules used by the local review UI.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CUBISM_PACK = ROOT / "experiments" / "cubism-material-pack-001"
SOURCE_MANIFEST = CUBISM_PACK / "layer_manifest.json"
CONCEPT_EXP = ROOT / "experiments" / "concept-regeneration-001"
CONCEPT_MANIFEST = CONCEPT_EXP / "layer_manifest.json"
SEETHROUGH_EXP = ROOT / "experiments" / "see-through-layer-decomp-001"
SEETHROUGH_MANIFEST = SEETHROUGH_EXP / "layer_manifest.json"
OUT_MANIFEST = ROOT / "review_app" / "review_manifest.json"
PART_GENERATION_MANIFEST = ROOT / "experiments" / "part-purity-001" / "part_generation_manifest.json"
CONCEPT_GENERATION_MANIFEST = CONCEPT_EXP / "part_generation_manifest.json"
SEETHROUGH_GENERATION_MANIFEST = SEETHROUGH_EXP / "part_generation_manifest.json"
SCHEMA_DOC = ROOT / "docs" / "ref" / "LIVE2D-PART-SCHEMA.md"

CANONICAL_PATH = ROOT / "experiments" / "production-canvas-2048-001" / "canonical" / "canonical_front_2048.png"
OVERLAY_DIR = CUBISM_PACK / "reference_pack" / "overlays"


PART_RULES: dict[str, dict[str, Any]] = {
    "face_underpaint": {
        "ko_name": "얼굴 언더페인트",
        "group": "face",
        "allowed_features": ["hidden skin fill behind face parts"],
        "forbidden_contamination": ["hair", "eyes", "mouth", "clothes"],
    },
    "back_hair": {
        "ko_name": "뒷머리",
        "group": "hair",
        "allowed_features": ["rear hair mass only"],
        "forbidden_contamination": ["face", "neck", "front_hair", "side_hair"],
    },
    "body": {
        "ko_name": "몸통",
        "group": "body",
        "allowed_features": ["body skin and torso base"],
        "forbidden_contamination": ["clothes", "hair", "face"],
    },
    "clothes": {
        "ko_name": "의상",
        "group": "body",
        "allowed_features": ["clothing pixels only"],
        "forbidden_contamination": ["skin", "hair", "face"],
    },
    "neck": {
        "ko_name": "목",
        "group": "face",
        "allowed_features": ["neck skin only"],
        "forbidden_contamination": ["clothes", "hair", "face_outline"],
    },
    "face_base": {
        "ko_name": "얼굴 베이스",
        "group": "face",
        "allowed_features": ["visible face skin and face outline"],
        "forbidden_contamination": ["hair", "eyes", "mouth"],
    },
    "L_eye_white": {
        "ko_name": "왼쪽 흰자",
        "group": "eyes",
        "allowed_features": ["left sclera only"],
        "forbidden_contamination": ["iris", "pupil", "lash", "hair", "skin"],
    },
    "R_eye_white": {
        "ko_name": "오른쪽 흰자",
        "group": "eyes",
        "allowed_features": ["right sclera only"],
        "forbidden_contamination": ["iris", "pupil", "lash", "hair", "skin"],
    },
    "L_iris": {
        "ko_name": "왼쪽 홍채",
        "group": "eyes",
        "allowed_features": ["left iris color only"],
        "forbidden_contamination": ["pupil", "highlight", "eye_white", "lash"],
    },
    "R_iris": {
        "ko_name": "오른쪽 홍채",
        "group": "eyes",
        "allowed_features": ["right iris color only"],
        "forbidden_contamination": ["pupil", "highlight", "eye_white", "lash"],
    },
    "L_pupil": {
        "ko_name": "왼쪽 동공",
        "group": "eyes",
        "allowed_features": ["left pupil only"],
        "forbidden_contamination": ["iris", "highlight", "eye_white"],
    },
    "R_pupil": {
        "ko_name": "오른쪽 동공",
        "group": "eyes",
        "allowed_features": ["right pupil only"],
        "forbidden_contamination": ["iris", "highlight", "eye_white"],
    },
    "L_highlight": {
        "ko_name": "왼쪽 눈 하이라이트",
        "group": "eyes",
        "allowed_features": ["left eye catchlight only"],
        "forbidden_contamination": ["iris", "pupil", "eye_white"],
    },
    "R_highlight": {
        "ko_name": "오른쪽 눈 하이라이트",
        "group": "eyes",
        "allowed_features": ["right eye catchlight only"],
        "forbidden_contamination": ["iris", "pupil", "eye_white"],
    },
    "L_upper_lash": {
        "ko_name": "왼쪽 윗속눈썹",
        "group": "eyes",
        "allowed_features": ["upper lash line only"],
        "forbidden_contamination": ["hair", "skin", "eye_white", "iris"],
    },
    "R_upper_lash": {
        "ko_name": "오른쪽 윗속눈썹",
        "group": "eyes",
        "allowed_features": ["upper lash line only"],
        "forbidden_contamination": ["hair", "skin", "eye_white", "iris"],
    },
    "L_lower_lash": {
        "ko_name": "왼쪽 아랫속눈썹",
        "group": "eyes",
        "allowed_features": ["lower lash line only"],
        "forbidden_contamination": ["hair", "skin", "eye_white", "iris"],
    },
    "R_lower_lash": {
        "ko_name": "오른쪽 아랫속눈썹",
        "group": "eyes",
        "allowed_features": ["lower lash line only"],
        "forbidden_contamination": ["hair", "skin", "eye_white", "iris"],
    },
    "L_brow": {
        "ko_name": "왼쪽 눈썹",
        "group": "brows",
        "allowed_features": ["left brow only"],
        "forbidden_contamination": ["hair", "skin", "lash"],
    },
    "R_brow": {
        "ko_name": "오른쪽 눈썹",
        "group": "brows",
        "allowed_features": ["right brow only"],
        "forbidden_contamination": ["hair", "skin", "lash"],
    },
    "mouth_line": {
        "ko_name": "입 라인",
        "group": "mouth",
        "allowed_features": ["mouth outline and lip line only"],
        "forbidden_contamination": ["teeth", "tongue", "skin"],
    },
    "mouth_inner": {
        "ko_name": "입 안쪽",
        "group": "mouth",
        "allowed_features": ["dark mouth cavity only"],
        "forbidden_contamination": ["teeth", "tongue", "skin", "cropped_line"],
    },
    "teeth": {
        "ko_name": "치아",
        "group": "mouth",
        "allowed_features": ["teeth only"],
        "forbidden_contamination": ["tongue", "mouth_line", "skin"],
    },
    "tongue": {
        "ko_name": "혀",
        "group": "mouth",
        "allowed_features": ["tongue only"],
        "forbidden_contamination": ["teeth", "mouth_line", "skin"],
    },
    "L_side_hair": {
        "ko_name": "왼쪽 옆머리",
        "group": "hair",
        "allowed_features": ["left side hair lock only"],
        "forbidden_contamination": ["face", "eye", "brow", "back_hair"],
    },
    "R_side_hair": {
        "ko_name": "오른쪽 옆머리",
        "group": "hair",
        "allowed_features": ["right side hair lock only"],
        "forbidden_contamination": ["face", "eye", "brow", "back_hair"],
    },
    "front_hair": {
        "ko_name": "앞머리",
        "group": "hair",
        "allowed_features": ["front bangs only"],
        "forbidden_contamination": ["face", "eye", "brow", "side_hair", "back_hair"],
    },
    "L_ear_outer": {
        "ko_name": "왼쪽 귀 바깥",
        "group": "ears",
        "allowed_features": ["left animal ear outer fur only"],
        "forbidden_contamination": ["hair", "skin", "ear_inner", "accessory"],
    },
    "R_ear_outer": {
        "ko_name": "오른쪽 귀 바깥",
        "group": "ears",
        "allowed_features": ["right animal ear outer fur only"],
        "forbidden_contamination": ["hair", "skin", "ear_inner", "accessory"],
    },
    "L_ear_inner": {
        "ko_name": "왼쪽 귀 안쪽",
        "group": "ears",
        "allowed_features": ["left animal ear inner shadow and color only"],
        "forbidden_contamination": ["hair", "skin", "ear_outer"],
    },
    "R_ear_inner": {
        "ko_name": "오른쪽 귀 안쪽",
        "group": "ears",
        "allowed_features": ["right animal ear inner shadow and color only"],
        "forbidden_contamination": ["hair", "skin", "ear_outer"],
    },
    "L_fur_shoulder": {
        "ko_name": "왼쪽 어깨 털",
        "group": "fur",
        "allowed_features": ["left white shoulder fur only"],
        "forbidden_contamination": ["hair", "skin", "clothes", "body"],
    },
    "R_fur_shoulder": {
        "ko_name": "오른쪽 어깨 털",
        "group": "fur",
        "allowed_features": ["right white shoulder fur only"],
        "forbidden_contamination": ["hair", "skin", "clothes", "body"],
    },
    "choker": {
        "ko_name": "초커",
        "group": "accessory",
        "allowed_features": ["black choker band only"],
        "forbidden_contamination": ["neck", "clothes", "gold_ornaments", "hair"],
    },
    "gold_ornaments": {
        "ko_name": "금색 장식",
        "group": "accessory",
        "allowed_features": ["gold ornaments only"],
        "forbidden_contamination": ["choker", "clothes", "skin", "hair"],
    },
}


REFERENCE_KO = {
    "blink_closed_corrected_full": "눈감음 참고",
    "blink_half_corrected_full": "반쯤 감은 눈 참고",
    "blink_mostly_closed_corrected_full": "거의 감은 눈 참고",
    "happy_open": "웃는 열린 입 참고",
    "neutral_smile": "기본 미소 입 참고",
    "o_vowel": "오 발음 입 참고",
    "small_open": "작게 열린 입 참고",
    "wide_open": "크게 열린 입 참고",
}


ISSUE_TAGS = [
    "hair_mixed",
    "skin_mixed",
    "eye_white_mixed",
    "iris_mixed",
    "line_cut",
    "alpha_dirty",
    "bbox_too_tight",
    "missing_underpaint",
    "wrong_shape",
    "semantic_too_coarse",
    "depth_order_wrong",
]


def rel(path: str | Path | None) -> str | None:
    if not path:
        return None
    p = Path(path)
    if not p.is_absolute():
        p = CUBISM_PACK / p
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return p.resolve().as_posix()


def asset(path: str | Path | None) -> str | None:
    relative = rel(path)
    return f"/assets/{relative}" if relative else None


def reference_name(part_id: str) -> str:
    for key, ko_name in REFERENCE_KO.items():
        if key in part_id:
            return ko_name
    return part_id.replace("_", " ")


def group_for(layer: dict[str, Any]) -> str:
    role = layer["role"]
    name = layer["layer_name"]
    if name in PART_RULES:
        return PART_RULES[name]["group"]
    if role.startswith("mouth"):
        return "reference_mouth"
    if role.startswith("blink"):
        return "reference_blink"
    return "overlays"


def overlay_for(layer: dict[str, Any]) -> str | None:
    name = layer["layer_name"]
    if layer["role"] not in {"mouth_keypose_reference", "blink_keypose_reference"}:
        return None
    overlay_name = name.replace("_full", "_overlay") + ".png"
    candidate = OVERLAY_DIR / overlay_name
    return asset(candidate) if candidate.exists() else None


def build_item(layer: dict[str, Any], section: str) -> dict[str, Any]:
    part_id = layer["layer_name"]
    original_part_id = layer.get("original_part_id", part_id)
    rules = PART_RULES.get(original_part_id, PART_RULES.get(part_id, {}))
    canonical_source = layer.get("canonical_path") or layer.get("source_path") or CANONICAL_PATH
    return {
        "part_id": part_id,
        "original_part_id": original_part_id,
        "experiment_id": layer.get("experiment_id", "part-purity-001"),
        "ko_name": layer.get("ko_name") or rules.get("ko_name", reference_name(part_id)),
        "group": layer.get("group") or rules.get("group", group_for(layer)),
        "section": section,
        "role": layer["role"],
        "side": layer.get("side"),
        "image_path": asset(layer.get("output_path") or layer.get("relative_output_path")),
        "source_path": asset(layer.get("source_path")),
        "canonical_path": asset(canonical_source) if Path(canonical_source).exists() else None,
        "overlay_path": overlay_for(layer),
        "bbox": layer.get("bbox"),
        "canvas_size": layer.get("canvas_size"),
        "alpha_coverage": layer.get("alpha_coverage"),
        "draw_order": layer.get("draw_order"),
        "status": layer.get("status", "UNKNOWN"),
        "include_in_import_psd": bool(layer.get("include_in_import_psd")),
        "allowed_features": rules.get("allowed_features", ["reference key-pose guide only"]),
        "forbidden_contamination": rules.get(
            "forbidden_contamination",
            ["production layer pixels", "guide overlay pixels"],
        ),
        "suggested_generation_mode": suggested_mode(layer, section),
    }


def suggested_mode(layer: dict[str, Any], section: str) -> str:
    if section == "seethrough_candidates":
        return "seethrough_cleanup_or_schema_remap"
    if section in {"reference_mouth", "reference_blink"}:
        return "reference_regeneration"
    role = layer["role"]
    if role in {"ears", "fur", "accessory"}:
        return "part_mask_regeneration"
    if role in {"upper_lash", "lower_lash", "eye_white", "iris", "pupil", "highlight", "mouth_inner", "mouth_line"}:
        return "mask_cleanup_or_regenerate"
    if "hair" in role:
        return "part_mask_regeneration"
    return "alpha_cleanup_or_inpaint"


def build_generation_targets(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    targets = []
    for item in items:
        targets.append(
            {
                "part_id": item["part_id"],
                "ko_name": item["ko_name"],
                "group": item["group"],
                "section": item["section"],
                "source_image": item["image_path"],
                "include_in_import_psd": item["include_in_import_psd"],
                "allowed_features": item["allowed_features"],
                "forbidden_contamination": item["forbidden_contamination"],
                "suggested_generation_mode": item["suggested_generation_mode"],
            }
        )
    return targets


def main() -> int:
    source = json.loads(SOURCE_MANIFEST.read_text())
    layers = source["layers"]

    sections = {
        "production_parts": [],
        "reference_mouth": [],
        "reference_blink": [],
        "overlays": [],
    }

    for layer in layers:
        if layer.get("include_in_import_psd"):
            section = "production_parts"
        elif layer.get("role") == "mouth_keypose_reference":
            section = "reference_mouth"
        elif layer.get("role") == "blink_keypose_reference":
            section = "reference_blink"
        else:
            section = "overlays"
        sections[section].append(build_item(layer, section))

    overlay_items = []
    for overlay in sorted(OVERLAY_DIR.glob("*.png")):
        overlay_items.append(
            {
                "part_id": overlay.stem,
                "ko_name": "오버레이 비교",
                "group": "overlays",
                "section": "overlays",
                "role": "overlay_reference",
                "side": None,
                "image_path": asset(overlay),
                "source_path": None,
                "canonical_path": asset(CANONICAL_PATH) if CANONICAL_PATH.exists() else None,
                "overlay_path": asset(overlay),
                "bbox": None,
                "canvas_size": [2048, 2048],
                "alpha_coverage": None,
                "draw_order": None,
                "status": "REFERENCE_ONLY",
                "include_in_import_psd": False,
                "allowed_features": ["visual comparison overlay only"],
                "forbidden_contamination": ["production import pixels"],
                "suggested_generation_mode": "overlay_review_only",
            }
        )
    sections["overlays"] = overlay_items

    if CONCEPT_MANIFEST.exists():
        concept_source = json.loads(CONCEPT_MANIFEST.read_text())
        sections["concept_parts"] = [
            build_item(layer, "concept_parts")
            for layer in concept_source.get("layers", [])
        ]

    if SEETHROUGH_MANIFEST.exists():
        seethrough_source = json.loads(SEETHROUGH_MANIFEST.read_text())
        sections["seethrough_candidates"] = [
            build_item(layer, "seethrough_candidates")
            for layer in seethrough_source.get("layers", [])
        ]

    all_items = [item for values in sections.values() for item in values]
    manifest = {
        "schema_version": 1,
        "experiment_id": "part-purity-001",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_layer_manifest": rel(SOURCE_MANIFEST),
        "source_schema_doc": rel(SCHEMA_DOC),
        "review_outputs": {
            "part_visual_review": "experiments/part-purity-001/reports/part_visual_review.json",
            "ai_fix_queue": "experiments/part-purity-001/reports/ai_fix_queue.json",
        },
        "issue_tags": ISSUE_TAGS,
        "sections": sections,
        "counts": {key: len(value) for key, value in sections.items()},
    }

    OUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    PART_GENERATION_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    part_purity_items = [item for item in all_items if item.get("experiment_id") != "concept-regeneration-001"]
    generation_manifest = {
        "schema_version": 1,
        "experiment_id": "part-purity-001",
        "generated_at": manifest["generated_at"],
        "source_review_manifest": "review_app/review_manifest.json",
        "targets": build_generation_targets(part_purity_items),
    }
    PART_GENERATION_MANIFEST.write_text(json.dumps(generation_manifest, ensure_ascii=False, indent=2) + "\n")

    concept_items = [item for item in all_items if item.get("experiment_id") == "concept-regeneration-001"]
    if concept_items:
        CONCEPT_GENERATION_MANIFEST.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "experiment_id": "concept-regeneration-001",
                    "generated_at": manifest["generated_at"],
                    "source_review_manifest": "review_app/review_manifest.json",
                    "targets": build_generation_targets(concept_items),
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )

    seethrough_items = [item for item in all_items if item.get("experiment_id") == "see-through-layer-decomp-001"]
    if seethrough_items:
        SEETHROUGH_GENERATION_MANIFEST.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "experiment_id": "see-through-layer-decomp-001",
                    "generated_at": manifest["generated_at"],
                    "source_review_manifest": "review_app/review_manifest.json",
                    "targets": build_generation_targets(seethrough_items),
                    "gate": "See-through candidates remain PSD-excluded until human O review and gated PSD rebuild.",
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )

    print(f"Wrote {OUT_MANIFEST.relative_to(ROOT)}")
    print(f"Wrote {PART_GENERATION_MANIFEST.relative_to(ROOT)}")
    if concept_items:
        print(f"Wrote {CONCEPT_GENERATION_MANIFEST.relative_to(ROOT)}")
    if seethrough_items:
        print(f"Wrote {SEETHROUGH_GENERATION_MANIFEST.relative_to(ROOT)}")
    print(json.dumps(manifest["counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

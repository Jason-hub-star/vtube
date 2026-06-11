#!/usr/bin/env python3
"""Build the unified part-purity review manifest.

The source of truth for existing files is the Cubism material-pack
`layer_manifest.json`. This script enriches it with Korean names and purity
rules used by the local review UI.
"""

from __future__ import annotations

import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CUBISM_PACK = ROOT / "experiments" / "cubism-material-pack-001"
SOURCE_MANIFEST = CUBISM_PACK / "layer_manifest.json"
CONCEPT_EXP = ROOT / "experiments" / "concept-regeneration-001"
CONCEPT_MANIFEST = CONCEPT_EXP / "layer_manifest.json"
OUT_MANIFEST = ROOT / "review_app" / "review_manifest.json"
PART_GENERATION_MANIFEST = ROOT / "experiments" / "part-purity-001" / "part_generation_manifest.json"
CONCEPT_GENERATION_MANIFEST = CONCEPT_EXP / "part_generation_manifest.json"
SCHEMA_DOC = ROOT / "docs" / "ref" / "LIVE2D-PART-SCHEMA.md"

CANONICAL_PATH = ROOT / "experiments" / "production-canvas-2048-001" / "canonical" / "canonical_front_2048.png"
OVERLAY_DIR = CUBISM_PACK / "reference_pack" / "overlays"

LAYER_DECOMP_EXPERIMENTS = [
    {
        "experiment_id": "see-through-layer-decomp-001",
        "section": "seethrough_candidates",
        "manifest": ROOT / "experiments" / "see-through-layer-decomp-001" / "layer_manifest.json",
        "generation_manifest": ROOT / "experiments" / "see-through-layer-decomp-001" / "part_generation_manifest.json",
        "gate": "See-through candidates remain PSD-excluded until human O review and gated PSD rebuild.",
    },
    {
        "experiment_id": "see-through-mps-compat-002",
        "section": "mps_compat_candidates",
        "manifest": ROOT / "experiments" / "see-through-mps-compat-002" / "layer_manifest.json",
        "generation_manifest": ROOT / "experiments" / "see-through-mps-compat-002" / "part_generation_manifest.json",
        "gate": "Mac MPS compatibility candidates are smoke evidence first; keep PSD-excluded until human O review and Cubism gate.",
    },
    {
        "experiment_id": "imagen-live2d-001",
        "section": "imagen_live2d_candidates",
        "manifest": ROOT / "experiments" / "imagen-live2d-001" / "layer_manifest.json",
        "generation_manifest": ROOT / "experiments" / "imagen-live2d-001" / "part_generation_manifest.json",
        "gate": "Imagen-generated character candidates must pass human review, ROI cleanup if needed, and Cubism import smoke before rigging.",
    },
    {
        "experiment_id": "mini-cubism-dedicated-model-v1-001",
        "section": "mini_cubism_dedicated_candidates",
        "manifest": ROOT / "experiments" / "mini-cubism-dedicated-model-v1-001" / "layer_manifest.json",
        "generation_manifest": ROOT / "experiments" / "mini-cubism-dedicated-model-v1-001" / "part_generation_manifest.json",
        "gate": "Dedicated Mini Cubism candidates are See-through layer split evidence only; map to the 73-part taxonomy before rig build claims.",
    },
    {
        "experiment_id": "layerdivider-compat-001",
        "section": "layerdivider_candidates",
        "manifest": ROOT / "experiments" / "layerdivider-compat-001" / "layer_manifest.json",
        "generation_manifest": ROOT / "experiments" / "layerdivider-compat-001" / "part_generation_manifest.json",
        "gate": "LayerDivider output is segmentation/reference evidence unless review proves a schema-clean production candidate.",
    },
    {
        "experiment_id": "qwen-layer-compat-001",
        "section": "qwen_layer_candidates",
        "manifest": ROOT / "experiments" / "qwen-layer-compat-001" / "layer_manifest.json",
        "generation_manifest": ROOT / "experiments" / "qwen-layer-compat-001" / "part_generation_manifest.json",
        "gate": "Qwen layered output is evaluated as PSD/PNG candidate evidence, not production success.",
    },
    {
        "experiment_id": "vtuber2d-ai-compat-001",
        "section": "vtuber2d_ai_candidates",
        "manifest": ROOT / "experiments" / "vtuber2d-ai-compat-001" / "layer_manifest.json",
        "generation_manifest": ROOT / "experiments" / "vtuber2d-ai-compat-001" / "part_generation_manifest.json",
        "gate": "VTuber2D.AI output is external reference evidence until licensing, layer purity, and Cubism import are reviewed.",
    },
]


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
    "L_arm": {
        "ko_name": "왼쪽 팔",
        "group": "body",
        "allowed_features": ["left arm, sleeve, or visible arm-side silhouette only"],
        "forbidden_contamination": ["face", "hair", "right_arm", "background"],
    },
    "R_arm": {
        "ko_name": "오른쪽 팔",
        "group": "body",
        "allowed_features": ["right arm, sleeve, or visible arm-side silhouette only"],
        "forbidden_contamination": ["face", "hair", "left_arm", "background"],
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

TRIAGE_PRIORITY = {
    "REVIEW_PRIORITY": 0,
    "REVIEW_HIGH_RISK": 1,
    "REFERENCE_REVIEW": 2,
    "X_CANDIDATE_EMPTY": 3,
}


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
        "triage_status": layer.get("triage_status"),
        "triage_notes": layer.get("triage_notes", []),
        "production_candidate": bool(layer.get("production_candidate", layer.get("status") == "OBSERVED")),
    }


def suggested_mode(layer: dict[str, Any], section: str) -> str:
    if section in {
        "seethrough_candidates",
        "mps_compat_candidates",
        "imagen_live2d_candidates",
        "mini_cubism_dedicated_candidates",
        "layerdivider_candidates",
        "qwen_layer_candidates",
        "vtuber2d_ai_candidates",
    }:
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


def enrich_triage_items(items: list[dict[str, Any]], experiment_id: str) -> None:
    triage_path = ROOT / "experiments" / experiment_id / "reports" / "mps_candidate_triage_report.json"
    if not triage_path.exists():
        return
    triage = json.loads(triage_path.read_text())
    triage_by_name = {item["layer_name"]: item for item in triage.get("items", [])}
    for item in items:
        source = triage_by_name.get(item["part_id"])
        if not source:
            continue
        item["triage_status"] = source.get("triage_status")
        item["triage_notes"] = source.get("triage_notes", [])
        item["production_candidate"] = bool(source.get("production_candidate"))
        item["practical_gate_target"] = "practical_gate_target" in item["triage_notes"]
    items.sort(
        key=lambda item: (
            TRIAGE_PRIORITY.get(item.get("triage_status"), 9),
            0 if item.get("practical_gate_target") else 1,
            item.get("group") or "",
            item["part_id"],
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the local part-purity review manifest.")
    parser.add_argument(
        "--mps-only",
        action="store_true",
        help="Build a focused Mac MPS See-through review manifest instead of the full legacy review surface.",
    )
    parser.add_argument(
        "--experiment-id",
        help="Build a focused layer-decomposition review manifest for one experiment, e.g. imagen-live2d-001.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
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

    layer_decomp_items_by_experiment: dict[str, list[dict[str, Any]]] = {}
    for experiment in LAYER_DECOMP_EXPERIMENTS:
        manifest_path = experiment["manifest"]
        if not manifest_path.exists():
            continue
        source = json.loads(manifest_path.read_text())
        section = experiment["section"]
        sections[section] = [build_item(layer, section) for layer in source.get("layers", [])]
        if section in {"mps_compat_candidates", "mini_cubism_dedicated_candidates"}:
            enrich_triage_items(sections[section], experiment["experiment_id"])
        layer_decomp_items_by_experiment[experiment["experiment_id"]] = sections[section]

    focus_experiment = args.experiment_id or ("see-through-mps-compat-002" if args.mps_only else None)
    mode = "mps_only" if args.mps_only else ("experiment_only" if focus_experiment else "full")
    focused_config = None
    if focus_experiment:
        focused_config = next((experiment for experiment in LAYER_DECOMP_EXPERIMENTS if experiment["experiment_id"] == focus_experiment), None)
        if not focused_config:
            raise SystemExit(f"FAIL: unknown experiment-id: {focus_experiment}")
        focused_items = sections.get(focused_config["section"])
        if not focused_items:
            raise SystemExit(f"FAIL: {focus_experiment} layer manifest is missing")
        sections = {focused_config["section"]: focused_items}
        layer_decomp_items_by_experiment = {focus_experiment: focused_items}

    all_items = [item for values in sections.values() for item in values]
    manifest = {
        "schema_version": 1,
        "experiment_id": focus_experiment or "part-purity-001",
        "mode": mode,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_layer_manifest": rel(SOURCE_MANIFEST),
        "source_schema_doc": rel(SCHEMA_DOC),
        "review_outputs": {
            "part_visual_review": (
                f"experiments/{focus_experiment}/reports/part_visual_review.json"
                if focus_experiment
                else "experiments/part-purity-001/reports/part_visual_review.json"
            ),
            "ai_fix_queue": (
                f"experiments/{focus_experiment}/reports/ai_fix_queue.json"
                if focus_experiment
                else "experiments/part-purity-001/reports/ai_fix_queue.json"
            ),
        },
        "ui": {
            "title": "Imagen Live2D 후보 검수"
            if focus_experiment == "imagen-live2d-001"
            else ("Mini Cubism 전용 모델 레이어 후보 검수" if focus_experiment == "mini-cubism-dedicated-model-v1-001" else "Mac MPS See-through 후보 검수"),
            "subtitle": "Imagen canonical에서 분해한 후보를 보고, O 저장 시 PSD 후보에 자동 반영합니다."
            if focus_experiment == "imagen-live2d-001"
            else (
                "전용 canonical에서 분해한 후보를 보고, 73-part taxonomy 매핑 전 후보 품질만 판정합니다."
                if focus_experiment == "mini-cubism-dedicated-model-v1-001"
                else "640 MPS 후보와 cleanup 후보를 보고, O 저장 시 PSD 후보에 자동 반영합니다."
            ),
            "primary_section": focused_config["section"] if focused_config else "mps_compat_candidates",
            "practical_gate_target": 5,
            "contact_sheet": f"/assets/experiments/{focus_experiment}/reports/mps_candidate_contact_sheet.png",
        }
        if focus_experiment
        else {
            "title": "Live2D 파츠 순도 검수",
            "subtitle": "PSD용 파츠와 입/눈 참고 이미지를 분리해서 보고, O/X/수정 판정을 저장합니다.",
            "primary_section": "production_parts",
        },
        "issue_tags": ISSUE_TAGS,
        "sections": sections,
        "counts": {key: len(value) for key, value in sections.items()},
    }

    OUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    concept_items = []
    if not args.mps_only:
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

    written_layer_decomp_manifests = []
    for experiment in LAYER_DECOMP_EXPERIMENTS:
        items = layer_decomp_items_by_experiment.get(experiment["experiment_id"], [])
        if not items:
            continue
        generation_manifest_path = experiment["generation_manifest"]
        generation_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        generation_manifest_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "experiment_id": experiment["experiment_id"],
                    "generated_at": manifest["generated_at"],
                    "source_review_manifest": "review_app/review_manifest.json",
                    "targets": build_generation_targets(items),
                    "gate": experiment["gate"],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )
        written_layer_decomp_manifests.append(generation_manifest_path)

    print(f"Wrote {OUT_MANIFEST.relative_to(ROOT)}")
    if not args.mps_only:
        print(f"Wrote {PART_GENERATION_MANIFEST.relative_to(ROOT)}")
    if concept_items:
        print(f"Wrote {CONCEPT_GENERATION_MANIFEST.relative_to(ROOT)}")
    for path in written_layer_decomp_manifests:
        print(f"Wrote {path.relative_to(ROOT)}")
    print(json.dumps(manifest["counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

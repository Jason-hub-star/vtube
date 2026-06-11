#!/usr/bin/env python3
"""Build the project-specific Cubism v2_standard new model part spec."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PRODUCTION_SPEC = ROOT / "experiments" / "reference-model-structure-001" / "reports" / "cubism_v2_production_design_spec.json"
DEFAULT_OUT = ROOT / "experiments" / "reference-model-structure-001" / "reports"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def part(
    part_id: str,
    group: str,
    label_ko: str,
    deformer: str,
    parameters: list[str],
    draw_order_band: str,
    *,
    physics: list[str] | None = None,
    qa_tags: list[str] | None = None,
    purpose_ko: str = "",
) -> dict[str, Any]:
    return {
        "id": part_id,
        "group": group,
        "label_ko": label_ko,
        "deformer_node": deformer,
        "parameters": parameters,
        "physics_groups": physics or [],
        "draw_order_band": draw_order_band,
        "qa_tags": qa_tags or [],
        "purpose_ko": purpose_ko,
    }


def build_parts() -> list[dict[str, Any]]:
    parts: list[dict[str, Any]] = []
    add = parts.append

    # Body and arms: simple upper-body rig, no complex hand/finger work.
    add(part("body_underpaint", "body", "몸 밑색", "body_root_warp", ["ParamBodyAngleX", "ParamBodyAngleY"], "body_back", qa_tags=["underpaint_missing"], purpose_ko="몸 각도에서 빈틈이 보이지 않게 받치는 밑색"))
    add(part("torso_base", "body", "상체 기본", "body_root_warp", ["ParamBodyAngleX", "ParamBodyAngleY", "ParamBreath"], "body_mid", physics=["body_breath_physics"]))
    add(part("neck", "body", "목", "body_root_warp", ["ParamAngleX", "ParamBodyAngleX", "ParamBodyAngleY"], "body_mid", physics=["body_breath_physics"]))
    add(part("neck_shadow_underpaint", "body", "목 그림자 밑색", "body_root_warp", ["ParamAngleX", "ParamBodyAngleX"], "body_back", qa_tags=["underpaint_missing"]))
    add(part("shoulder_L", "body", "왼쪽 어깨", "body_root_warp", ["ParamBodyAngleX", "ParamBreath"], "body_mid", physics=["body_breath_physics"]))
    add(part("shoulder_R", "body", "오른쪽 어깨", "body_root_warp", ["ParamBodyAngleX", "ParamBreath"], "body_mid", physics=["body_breath_physics"]))
    add(part("arm_L_upper_simple", "body", "왼쪽 간단 팔", "shoulder_arm_rotation", ["ParamArmL/R or ParamHandL/R", "ParamBodyAngleX"], "body_front", qa_tags=["misaligned"]))
    add(part("arm_R_upper_simple", "body", "오른쪽 간단 팔", "shoulder_arm_rotation", ["ParamArmL/R or ParamHandL/R", "ParamBodyAngleX"], "body_front", qa_tags=["misaligned"]))
    add(part("arm_L_underpaint", "body", "왼팔 밑색", "shoulder_arm_rotation", ["ParamBodyAngleX"], "body_back", qa_tags=["underpaint_missing"]))
    add(part("arm_R_underpaint", "body", "오른팔 밑색", "shoulder_arm_rotation", ["ParamBodyAngleX"], "body_back", qa_tags=["underpaint_missing"]))

    # Face base.
    add(part("face_base", "face_base", "얼굴 기본", "head_angle_warp", ["ParamAngleX", "ParamAngleY", "ParamAngleZ"], "face_mid"))
    add(part("face_shadow_L", "face_base", "왼쪽 얼굴 그림자", "head_angle_warp", ["ParamAngleX", "ParamAngleY"], "face_front"))
    add(part("face_shadow_R", "face_base", "오른쪽 얼굴 그림자", "head_angle_warp", ["ParamAngleX", "ParamAngleY"], "face_front"))
    add(part("face_underpaint_L", "face_base", "왼쪽 얼굴 밑색", "head_angle_warp", ["ParamAngleX"], "face_back", qa_tags=["underpaint_missing"]))
    add(part("face_underpaint_R", "face_base", "오른쪽 얼굴 밑색", "head_angle_warp", ["ParamAngleX"], "face_back", qa_tags=["underpaint_missing"]))
    add(part("nose", "face_base", "코", "head_angle_warp", ["ParamAngleX", "ParamAngleY"], "face_front"))
    add(part("cheek_L", "face_base", "왼쪽 볼", "head_angle_warp", ["ParamAngleX", "ParamMouthForm"], "face_front"))
    add(part("cheek_R", "face_base", "오른쪽 볼", "head_angle_warp", ["ParamAngleX", "ParamMouthForm"], "face_front"))

    # Eyes and brows.
    for side, label in (("L", "왼쪽"), ("R", "오른쪽")):
        eye_deformer = f"eye_{side}_warp"
        eye_open = f"ParamEye{side}Open"
        add(part(f"eye_{side}_white", f"eye_{side}", f"{label} 눈 흰자", eye_deformer, [eye_open, "ParamEyeBallX", "ParamEyeBallY"], "eye_back", qa_tags=["bad_alpha"]))
        add(part(f"eye_{side}_iris", f"eye_{side}", f"{label} 홍채", eye_deformer, [eye_open, "ParamEyeBallX", "ParamEyeBallY"], "eye_mid", qa_tags=["misaligned"]))
        add(part(f"eye_{side}_pupil", f"eye_{side}", f"{label} 동공", eye_deformer, [eye_open, "ParamEyeBallX", "ParamEyeBallY"], "eye_mid", qa_tags=["misaligned"]))
        add(part(f"eye_{side}_highlight", f"eye_{side}", f"{label} 눈 하이라이트", eye_deformer, [eye_open, "ParamEyeBallX", "ParamEyeBallY"], "eye_front"))
        add(part(f"eye_{side}_upper_lash", f"eye_{side}", f"{label} 위 속눈썹", eye_deformer, [eye_open, "ParamAngleY"], "eye_front", qa_tags=["draw_order_issue"]))
        add(part(f"eye_{side}_lower_lash", f"eye_{side}", f"{label} 아래 속눈썹", eye_deformer, [eye_open, "ParamAngleY"], "eye_front"))
        add(part(f"eye_{side}_closed_lid", f"eye_{side}", f"{label} 감은 눈꺼풀", eye_deformer, [eye_open], "eye_front", qa_tags=["clipping_risk"], purpose_ko="눈 감김 extreme에서 흰자/홍채를 가리는 키폼용"))
        add(part(f"eye_{side}_underpaint", f"eye_{side}", f"{label} 눈 밑색", eye_deformer, [eye_open, "ParamAngleX"], "eye_back", qa_tags=["underpaint_missing"]))
    add(part("brow_L", "brow", "왼쪽 눈썹", "brow_L_R_warp", ["ParamBrowL/R Angle/Form/Y", "ParamAngleX"], "brow_front"))
    add(part("brow_R", "brow", "오른쪽 눈썹", "brow_L_R_warp", ["ParamBrowL/R Angle/Form/Y", "ParamAngleX"], "brow_front"))

    # Mouth.
    add(part("mouth_line", "mouth", "입 선", "mouth_warp", ["ParamMouthOpenY", "ParamMouthForm", "ParamAngleX"], "mouth_front", qa_tags=["misaligned"]))
    add(part("mouth_inner", "mouth", "입 안쪽", "mouth_warp", ["ParamMouthOpenY", "ParamMouthForm"], "mouth_back", qa_tags=["bad_alpha"]))
    add(part("mouth_upper_lip_mask", "mouth", "윗입술 마스크", "mouth_warp", ["ParamMouthOpenY", "ParamMouthForm"], "mouth_front", qa_tags=["clipping_risk"]))
    add(part("mouth_lower_lip_mask", "mouth", "아랫입술 마스크", "mouth_warp", ["ParamMouthOpenY", "ParamMouthForm"], "mouth_front", qa_tags=["clipping_risk"]))
    add(part("mouth_teeth", "mouth", "치아", "mouth_warp", ["ParamMouthOpenY"], "mouth_mid"))
    add(part("mouth_tongue", "mouth", "혀", "mouth_warp", ["ParamMouthOpenY", "ParamMouthForm"], "mouth_mid"))
    add(part("mouth_corner_L", "mouth", "왼쪽 입꼬리", "mouth_warp", ["ParamMouthOpenY", "ParamMouthForm"], "mouth_front"))
    add(part("mouth_corner_R", "mouth", "오른쪽 입꼬리", "mouth_warp", ["ParamMouthOpenY", "ParamMouthForm"], "mouth_front"))

    # Hair: enough split for v2_standard physics without entering rich strand overload.
    add(part("hair_back_base", "hair", "뒷머리 기본", "back_hair_warp", ["ParamAngleX", "ParamAngleZ", "ParamHairBack"], "hair_back", physics=["back_hair_physics"]))
    add(part("hair_back_underpaint", "hair", "뒷머리 밑색", "back_hair_warp", ["ParamAngleX", "ParamHairBack"], "hair_back", qa_tags=["underpaint_missing"]))
    add(part("hair_back_strand_L", "hair", "왼쪽 뒷머리 가닥", "back_hair_warp", ["ParamHairBack", "ParamAngleZ"], "hair_back", physics=["back_hair_physics"]))
    add(part("hair_back_strand_R", "hair", "오른쪽 뒷머리 가닥", "back_hair_warp", ["ParamHairBack", "ParamAngleZ"], "hair_back", physics=["back_hair_physics"]))
    add(part("hair_back_center", "hair", "가운데 뒷머리", "back_hair_warp", ["ParamHairBack", "ParamBreath"], "hair_back", physics=["back_hair_physics"]))
    add(part("hair_front_center", "hair", "가운데 앞머리", "front_hair_warp", ["ParamAngleX", "ParamAngleZ", "ParamHairFront"], "hair_front", physics=["front_hair_physics"], qa_tags=["draw_order_issue"]))
    add(part("hair_front_L", "hair", "왼쪽 앞머리", "front_hair_warp", ["ParamAngleX", "ParamAngleZ", "ParamHairFront"], "hair_front", physics=["front_hair_physics"]))
    add(part("hair_front_R", "hair", "오른쪽 앞머리", "front_hair_warp", ["ParamAngleX", "ParamAngleZ", "ParamHairFront"], "hair_front", physics=["front_hair_physics"]))
    add(part("hair_front_side_L", "hair", "왼쪽 앞 옆머리", "front_hair_warp", ["ParamAngleX", "ParamHairFront"], "hair_front", physics=["front_hair_physics"]))
    add(part("hair_front_side_R", "hair", "오른쪽 앞 옆머리", "front_hair_warp", ["ParamAngleX", "ParamHairFront"], "hair_front", physics=["front_hair_physics"]))
    add(part("hair_front_tip_L", "hair", "왼쪽 앞머리 끝", "front_hair_warp", ["ParamHairFront", "ParamAngleZ"], "hair_front", physics=["front_hair_physics"]))
    add(part("hair_front_tip_R", "hair", "오른쪽 앞머리 끝", "front_hair_warp", ["ParamHairFront", "ParamAngleZ"], "hair_front", physics=["front_hair_physics"]))
    add(part("hair_side_L_outer", "hair", "왼쪽 바깥 옆머리", "side_hair_L_R_warp", ["ParamHairSide", "ParamAngleX"], "hair_side", physics=["side_hair_L_physics"]))
    add(part("hair_side_L_inner", "hair", "왼쪽 안쪽 옆머리", "side_hair_L_R_warp", ["ParamHairSide", "ParamAngleX"], "hair_side", physics=["side_hair_L_physics"]))
    add(part("hair_side_R_outer", "hair", "오른쪽 바깥 옆머리", "side_hair_L_R_warp", ["ParamHairSide", "ParamAngleX"], "hair_side", physics=["side_hair_R_physics"]))
    add(part("hair_side_R_inner", "hair", "오른쪽 안쪽 옆머리", "side_hair_L_R_warp", ["ParamHairSide", "ParamAngleX"], "hair_side", physics=["side_hair_R_physics"]))

    # Simple clothing anchors for draw-order and breath/body checks.
    add(part("collar_front", "clothing", "앞깃", "body_root_warp", ["ParamBodyAngleX", "ParamBreath"], "clothing_front", physics=["body_breath_physics"]))
    add(part("collar_shadow", "clothing", "깃 그림자", "body_root_warp", ["ParamBodyAngleX"], "clothing_mid"))
    add(part("chest_cloth_base", "clothing", "가슴 의상 기본", "body_root_warp", ["ParamBodyAngleX", "ParamBreath"], "clothing_mid", physics=["body_breath_physics"]))
    add(part("chest_cloth_shadow", "clothing", "가슴 의상 그림자", "body_root_warp", ["ParamBodyAngleX"], "clothing_front"))
    return parts


def group_counts(parts: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in parts:
        counts[item["group"]] = counts.get(item["group"], 0) + 1
    return counts


def validate_spec(payload: dict[str, Any]) -> dict[str, Any]:
    parts = payload["parts"]
    ids = [item["id"] for item in parts]
    counts = group_counts(parts)
    production = payload["source_production_spec_summary"]
    required_params = {
        "ParamAngleX",
        "ParamAngleY",
        "ParamAngleZ",
        "ParamBodyAngleX",
        "ParamBodyAngleY",
        "ParamEyeLOpen",
        "ParamEyeROpen",
        "ParamEyeBallX",
        "ParamEyeBallY",
        "ParamMouthOpenY",
        "ParamMouthForm",
        "ParamBreath",
    }
    used_params = {param for item in parts for param in item["parameters"]}
    physics_groups = {group for item in parts for group in item["physics_groups"]}
    checks = {
        "production_spec_schema_v2": production["schema_version"] == 2,
        "part_count_50_to_70": 50 <= len(parts) <= 70,
        "exact_target_count_64": len(parts) == 64,
        "no_duplicate_part_ids": len(ids) == len(set(ids)),
        "has_face_base": counts.get("face_base", 0) >= 6,
        "has_eye_L": counts.get("eye_L", 0) >= 8,
        "has_eye_R": counts.get("eye_R", 0) >= 8,
        "eye_symmetry": counts.get("eye_L", 0) == counts.get("eye_R", 0),
        "has_brows": counts.get("brow", 0) >= 2,
        "has_mouth": counts.get("mouth", 0) >= 8,
        "has_hair": counts.get("hair", 0) >= 16,
        "has_body_and_simple_arms": counts.get("body", 0) >= 10,
        "has_underpaint_parts": sum(1 for item in parts if "underpaint" in item["id"]) >= 8,
        "covers_required_parameters": required_params <= used_params,
        "has_v2_standard_physics_groups": {"front_hair_physics", "side_hair_L_physics", "side_hair_R_physics", "back_hair_physics", "body_breath_physics"} <= physics_groups,
        "avoids_v2_rich_scope": not any("finger" in item["id"] or "effect" in item["id"] or "skirt" in item["id"] for item in parts),
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    return {
        "status": status,
        "checks": checks,
        "counts": {
            "parts": len(parts),
            "groups": counts,
            "underpaint_parts": sum(1 for item in parts if "underpaint" in item["id"]),
            "physics_groups": sorted(physics_groups),
            "used_parameters": sorted(used_params),
        },
        "duplicates": sorted({part_id for part_id in ids if ids.count(part_id) > 1}),
    }


def build_payload(production_spec: dict[str, Any], production_spec_path: Path) -> dict[str, Any]:
    parts = build_parts()
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "spec_id": "cubism_v2_new_model_v2_standard_part_spec",
        "status": "DRAFT_PENDING_VALIDATION",
        "source": {
            "production_spec": rel(production_spec_path),
            "basis": "all57 official/reference structure baseline normalized into cubism_v2_production_design_spec schema v2",
        },
        "target": {
            "tier": "v2_standard",
            "part_count": 64,
            "canvas_policy": "1024, 1536, or 2048 allowed; part/deformer/keyform gate is more important than fixed resolution.",
            "character_scope": "front-facing upper-body human VTuber, clear eyes/mouth/hair/body angle, simple shoulders/arms, no heavy props/effects.",
        },
        "source_production_spec_summary": {
            "schema_version": production_spec["schema_version"],
            "v2_standard_minimum_floor": production_spec["production_tiers"]["v2_standard"]["minimum_floor"],
            "v2_standard_recommended_target": production_spec["production_tiers"]["v2_standard"]["recommended_target"],
            "required_parameter_entries": len(production_spec["parameter_map_detail"]),
            "deformer_hierarchy_nodes": len(production_spec["deformer_hierarchy"]),
            "physics_blueprint_groups": len(production_spec["physics_blueprint"]["groups"]),
            "acceptance_gates": [gate["gate"] for gate in production_spec["acceptance_checklist_g0_g3"]],
        },
        "parts": parts,
        "deferred_until_v2_rich": [
            "complex hands/fingers",
            "heavy props",
            "large effects",
            "skirt/cloth secondary rig unless design requires it",
            "ParamA/I/U/E/O vowel rig unless lip-sync becomes a first release requirement",
        ],
        "self_review": {},
    }
    payload["self_review"] = validate_spec(payload)
    payload["status"] = "SPEC_CONFIRMED" if payload["self_review"]["status"] == "PASS" else "SPEC_REVISE"
    return payload


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Cubism v2 New Model v2_standard Part Spec",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- status: `{payload['status']}`",
        f"- target tier: `{payload['target']['tier']}`",
        f"- confirmed part count: `{payload['target']['part_count']}`",
        f"- source production spec: `{payload['source']['production_spec']}`",
        "",
        "## Self Review",
        "",
        f"- status: `{payload['self_review']['status']}`",
        f"- counts: `{payload['self_review']['counts']}`",
        "",
        "| Check | Result |",
        "|---|---:|",
    ]
    for key, value in payload["self_review"]["checks"].items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend([
        "",
        "## 확정 파츠 목록",
        "",
        "| # | Part ID | Group | Korean Label | Deformer | Parameters | Physics | QA Tags |",
        "|---:|---|---|---|---|---|---|---|",
    ])
    for index, item in enumerate(payload["parts"], 1):
        lines.append(
            f"| {index} | `{item['id']}` | `{item['group']}` | {item['label_ko']} | `{item['deformer_node']}` | "
            f"`{item['parameters']}` | `{item['physics_groups']}` | `{item['qa_tags']}` |"
        )
    lines.extend([
        "",
        "## Deferred Until v2_rich",
        "",
    ])
    lines.extend(f"- {item}" for item in payload["deferred_until_v2_rich"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--production-spec", type=Path, default=DEFAULT_PRODUCTION_SPEC)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    production_spec_path = args.production_spec if args.production_spec.is_absolute() else ROOT / args.production_spec
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    production_spec = load_json(production_spec_path)
    payload = build_payload(production_spec, production_spec_path)
    json_path = out_dir / "cubism_v2_new_model_v2_standard_part_spec.json"
    md_path = out_dir / "cubism_v2_new_model_v2_standard_part_spec.md"
    write_json(json_path, payload)
    write_md(md_path, payload)
    result = {
        "status": payload["status"],
        "self_review_status": payload["self_review"]["status"],
        "part_count": len(payload["parts"]),
        "group_counts": payload["self_review"]["counts"]["groups"],
        "outputs": {
            "json": rel(json_path),
            "md": rel(md_path),
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if payload["self_review"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

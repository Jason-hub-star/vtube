#!/usr/bin/env python3
"""Build the Cubism v2 Korean review manifest.

This keeps the existing review app contract intact while adding the v2 tier,
gate, compare-view, and auto-check fields used by the easier Cubism-first UI.
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "review_app" / "review_manifest.json"
DEFAULT_OUT = ROOT / "review_app" / "review_manifest.json"
DEFAULT_SPEC = ROOT / "experiments" / "reference-model-structure-001" / "reports" / "cubism_success_pattern_spec.md"
DEFAULT_CMO3 = ROOT / "experiments" / "imagen-live2d-001" / "reports" / "cmo3_structure_report.json"
DEFAULT_MINI_VALIDATION = (
    ROOT
    / "experiments"
    / "mini-cubism-dedicated-model-v1-001"
    / "mini_cubism_project_targeted"
    / "reports"
    / "validation_report.json"
)
DEFAULT_PHYSICS = (
    ROOT
    / "experiments"
    / "mini-cubism-dedicated-model-v1-001"
    / "targeted_motion_evidence"
    / "reports"
    / "physics_score_report.json"
)
DEFAULT_MOTION_DIR = ROOT / "experiments" / "mini-cubism-dedicated-model-v1-001" / "targeted_motion_evidence" / "gifs"
DEFAULT_LAYER_MANIFEST = ROOT / "experiments" / "mini-cubism-dedicated-model-v1-001" / "layer_manifest.json"

TIER_LIMITS = {
    "v2_min": 25,
    "v2_standard": 70,
    "v2_rich": 120,
}

ISSUE_TAGS = [
    {
        "code": "missing_part",
        "label_ko": "파츠 없음",
        "help_ko": "필수 파츠가 빠졌거나 거의 보이지 않아요.",
    },
    {
        "code": "bad_alpha",
        "label_ko": "테두리 지저분함",
        "help_ko": "투명 배경 가장자리에 찌꺼기나 잘림이 있어요.",
    },
    {
        "code": "misaligned",
        "label_ko": "위치 안 맞음",
        "help_ko": "파츠가 원래 자리에서 밀렸어요.",
    },
    {
        "code": "style_mismatch",
        "label_ko": "그림체 다름",
        "help_ko": "다른 파츠와 선, 색, 비율이 달라 보여요.",
    },
    {
        "code": "underpaint_missing",
        "label_ko": "밑색 없음",
        "help_ko": "움직이면 뒤가 비어 보일 수 있어요.",
    },
    {
        "code": "clipping_risk",
        "label_ko": "마스크 위험",
        "help_ko": "눈꺼풀, 앞머리, 장식처럼 마스크가 까다로운 부분이에요.",
    },
    {
        "code": "draw_order_issue",
        "label_ko": "앞뒤 순서 문제",
        "help_ko": "앞에 있어야 할 파츠와 뒤에 있어야 할 파츠가 헷갈려요.",
    },
    {
        "code": "overhang_issue",
        "label_ko": "튀어나온 부분 문제",
        "help_ko": "파츠 끝이 몸 밖으로 어색하게 튀어나와요.",
    },
]

GROUP_PRIORITY = {
    "face": 0,
    "eyes": 1,
    "brows": 2,
    "mouth": 3,
    "hair": 4,
    "body": 5,
    "ears": 6,
    "fur": 7,
    "accessory": 8,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Cubism v2 gate-based review manifest.")
    parser.add_argument("--tier", choices=sorted(TIER_LIMITS), default="v2_min")
    parser.add_argument("--source-review-manifest", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--success-spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--cmo3-report", type=Path, default=DEFAULT_CMO3)
    parser.add_argument("--mini-validation-report", type=Path, default=DEFAULT_MINI_VALIDATION)
    parser.add_argument("--physics-report", type=Path, default=DEFAULT_PHYSICS)
    parser.add_argument("--motion-dir", type=Path, default=DEFAULT_MOTION_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def rel(path: Path | str | None) -> str | None:
    if not path:
        return None
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return p.resolve().as_posix()


def asset(path: Path | str | None) -> str | None:
    if not path:
        return None
    value = str(path)
    if value.startswith("/assets/"):
        return value
    return f"/assets/{rel(path)}"


def all_source_items(source: dict[str, Any]) -> list[dict[str, Any]]:
    items = []
    for section_items in source.get("sections", {}).values():
        for item in section_items:
            if item.get("review_gate") in {"G0_CONCEPT", "G1_PART_TAXONOMY", "G2_STRUCTURE", "G3_MOTION_VISUAL"}:
                continue
            items.append(deepcopy(item))
    return items


def fallback_layer_items() -> list[dict[str, Any]]:
    manifest = load_json(DEFAULT_LAYER_MANIFEST)
    items = []
    for layer in manifest.get("layers", []):
        part_id = layer.get("layer_name")
        original = layer.get("original_part_id") or part_id
        items.append(
            {
                "part_id": part_id,
                "original_part_id": original,
                "experiment_id": layer.get("experiment_id", manifest.get("experiment_id", "mini-cubism-dedicated-model-v1-001")),
                "ko_name": ko_name(original),
                "group": group_for(original, layer.get("role")),
                "section": "fallback_layer_manifest",
                "role": layer.get("role") or original,
                "side": layer.get("side"),
                "image_path": asset(layer.get("output_path")),
                "source_path": asset(layer.get("source_path")),
                "canonical_path": asset(layer.get("canonical_path")),
                "overlay_path": None,
                "bbox": layer.get("bbox"),
                "canvas_size": layer.get("canvas_size") or manifest.get("normalized_canvas_size"),
                "alpha_coverage": layer.get("alpha_coverage"),
                "draw_order": layer.get("draw_order"),
                "status": layer.get("status", "OBSERVED"),
                "include_in_import_psd": False,
                "allowed_features": [f"{ko_name(original)}만 있어야 함"],
                "forbidden_contamination": ["다른 파츠", "배경", "잘린 선"],
                "suggested_generation_mode": "cubism_v2_part_cleanup",
                "triage_status": "REVIEW_PRIORITY" if layer.get("production_candidate") else "REFERENCE_REVIEW",
                "triage_notes": layer.get("notes", []),
                "production_candidate": bool(layer.get("production_candidate")),
            }
        )
    return items


def ko_name(part_id: str | None) -> str:
    labels = {
        "face_base": "얼굴 베이스",
        "front_hair": "앞머리",
        "back_hair": "뒷머리",
        "L_side_hair": "왼쪽 옆머리",
        "R_side_hair": "오른쪽 옆머리",
        "neck": "목",
        "body": "몸통",
        "clothes": "의상",
        "L_arm": "왼쪽 팔",
        "R_arm": "오른쪽 팔",
        "mouth_line": "입 라인",
        "mouth_inner": "입 안쪽",
        "teeth": "치아",
        "tongue": "혀",
        "L_brow": "왼쪽 눈썹",
        "R_brow": "오른쪽 눈썹",
        "L_eye_white": "왼쪽 흰자",
        "R_eye_white": "오른쪽 흰자",
        "L_iris": "왼쪽 홍채",
        "R_iris": "오른쪽 홍채",
        "L_pupil": "왼쪽 동공",
        "R_pupil": "오른쪽 동공",
        "L_highlight": "왼쪽 눈 하이라이트",
        "R_highlight": "오른쪽 눈 하이라이트",
    }
    return labels.get(part_id or "", (part_id or "파츠").replace("_", " "))


def group_for(part_id: str | None, role: str | None) -> str:
    value = f"{part_id or ''} {role or ''}".lower()
    if "eye" in value or "iris" in value or "pupil" in value or "lash" in value or "highlight" in value:
        return "eyes"
    if "brow" in value:
        return "brows"
    if "mouth" in value or "teeth" in value or "tongue" in value:
        return "mouth"
    if "hair" in value:
        return "hair"
    if "ear" in value:
        return "ears"
    if "choker" in value or "ornament" in value or "accessory" in value:
        return "accessory"
    if "arm" in value or "body" in value or "clothes" in value:
        return "body"
    return "face"


def gate_item(item: dict[str, Any], tier: str, gate: str, section: str) -> dict[str, Any]:
    next_item = deepcopy(item)
    next_item["tier"] = tier
    next_item["review_gate"] = gate
    next_item["section"] = section
    next_item["simple_label"] = item.get("simple_label") or item.get("ko_name") or item.get("part_id")
    next_item["simple_description"] = description_for_gate(gate)
    next_item["checklist"] = checklist_for_gate(gate)
    next_item.setdefault("compare_views", {})
    next_item.setdefault("auto_check_summary", None)
    next_item["auto_issue_tags"] = infer_issue_tags(next_item)
    return next_item


def description_for_gate(gate: str) -> str:
    return {
        "G0_CONCEPT": "캐릭터가 버튜버로 만들기 좋은지 먼저 고릅니다.",
        "G1_PART_TAXONOMY": "파츠가 빠지지 않고 깨끗하게 나뉘었는지 봅니다.",
        "G2_STRUCTURE": "사람 눈검수가 아니라 Cubism 구조 숫자로 확인합니다.",
        "G3_MOTION_VISUAL": "기본 포즈와 크게 움직인 포즈를 비교합니다.",
    }[gate]


def checklist_for_gate(gate: str) -> list[str]:
    return {
        "G0_CONCEPT": [
            "눈, 입, 머리카락, 몸이 한눈에 보이나요?",
            "그림체와 비율이 마음에 드나요?",
            "팔이나 머리카락이 너무 복잡하게 겹치지 않나요?",
        ],
        "G1_PART_TAXONOMY": [
            "필수 파츠가 빠지지 않았나요?",
            "투명 테두리가 깨끗한가요?",
            "파츠가 잘리거나 위치가 틀어지지 않았나요?",
        ],
        "G2_STRUCTURE": [
            "ArtMesh, Parameter가 충분한가요?",
            "Warp/Rotation Deformer와 KeyformBinding이 있나요?",
            "Physics group이 움직임 단계에 맞게 있나요?",
        ],
        "G3_MOTION_VISUAL": [
            "눈 깜빡임이 자연스럽나요?",
            "입 모양이 말하는 것처럼 보이나요?",
            "머리카락과 몸각도가 과하게 흔들리지 않나요?",
        ],
    }[gate]


def infer_issue_tags(item: dict[str, Any]) -> list[str]:
    tags = []
    if not item.get("bbox") or float(item.get("alpha_coverage") or 0) <= 0:
        tags.extend(["missing_part", "bad_alpha"])
    if item.get("bbox"):
        _, _, w, h = item["bbox"]
        if min(w, h) <= 3:
            tags.append("bad_alpha")
    role = str(item.get("role") or item.get("group") or "")
    if "underpaint" in role:
        tags.append("underpaint_missing")
    if item.get("group") in {"eyes", "hair", "accessory"}:
        tags.append("clipping_risk")
    if item.get("draw_order") is None and item.get("review_gate") == "G1_PART_TAXONOMY":
        tags.append("draw_order_issue")
    return sorted(set(tags))


def build_g0_items(source_items: list[dict[str, Any]], tier: str) -> list[dict[str, Any]]:
    candidates = []
    seen_paths = set()
    for item in source_items:
        path = item.get("image_path") or item.get("canonical_path")
        if not path or path in seen_paths:
            continue
        seen_paths.add(path)
        candidate = gate_item(item, tier, "G0_CONCEPT", "g0_concept")
        candidate["part_id"] = f"g0__candidate_{len(candidates) + 1:02d}"
        candidate["simple_label"] = f"캐릭터 후보 {len(candidates) + 1}"
        candidate["image_path"] = path
        candidate["compare_views"] = {"neutral": path, "extreme": item.get("overlay_path") or item.get("image_path") or path}
        candidate["include_in_import_psd"] = False
        candidates.append(candidate)
        if len(candidates) >= 6:
            break
    return candidates


def build_g1_items(source_items: list[dict[str, Any]], tier: str) -> list[dict[str, Any]]:
    limit = TIER_LIMITS[tier]
    sortable = [
        item
        for item in source_items
        if item.get("image_path") and item.get("group") not in {"overlays", "reference_mouth", "reference_blink", "motion", "structure"}
    ]
    sortable.sort(
        key=lambda item: (
            GROUP_PRIORITY.get(item.get("group"), 99),
            item.get("draw_order") if item.get("draw_order") is not None else 9999,
            item.get("part_id", ""),
        )
    )
    selected = sortable[:limit]
    if tier == "v2_min" and len(selected) < 20:
        extras = [item for item in fallback_layer_items() if item.get("part_id") not in {entry.get("part_id") for entry in selected}]
        extras.sort(
            key=lambda item: (
                GROUP_PRIORITY.get(item.get("group"), 99),
                item.get("draw_order") if item.get("draw_order") is not None else 9999,
                item.get("part_id", ""),
            )
        )
        selected.extend(extras[: 20 - len(selected)])
    return [gate_item(item, tier, "G1_PART_TAXONOMY", "g1_part_taxonomy") for item in selected[:limit]]


def count_def(report: dict[str, Any], key: str) -> int:
    return int(report.get("counts", {}).get(key, {}).get("definitions", 0))


def build_auto_summary(args: argparse.Namespace, g1_items: list[dict[str, Any]]) -> dict[str, Any]:
    cmo3 = load_json(args.cmo3_report)
    mini = load_json(args.mini_validation_report)
    physics = load_json(args.physics_report)
    cmo3_checks = {check.get("id"): check for check in cmo3.get("checks", [])}
    mini_counts = mini.get("counts", {})
    physics_targets = 0
    for check in physics.get("checks", []):
        physics_targets = max(physics_targets, int(check.get("physics_target_count", 0) or 0))
    checks = {
        "required_part_count": f"{len(g1_items)}/{TIER_LIMITS[args.tier]}",
        "alpha_bbox_crop": "PASS" if all(item.get("bbox") and float(item.get("alpha_coverage") or 0) > 0 for item in g1_items) else "REVISE",
        "artmesh_count": count_def(cmo3, "CArtMeshSource") or mini_counts.get("meshes"),
        "parameter_count": count_def(cmo3, "CParameterSource") or mini_counts.get("parameters"),
        "deformer_count": count_def(cmo3, "CWarpDeformerSource") + count_def(cmo3, "CRotationDeformerSource") or mini_counts.get("deformers"),
        "keyform_binding_count": count_def(cmo3, "KeyformBindingSource") or mini_counts.get("keyform_bindings"),
        "physics_group_count": count_def(cmo3, "CPhysicsSettingsSource") or len(
            [
                profile
                for check in physics.get("checks", [])
                for profile in check.get("active_profiles", [])
            ]
        ),
        "physics_target_count": physics_targets,
    }
    required_ids = ["warp_deformers_present", "rotation_deformers_present", "keyform_bindings_present"]
    missing = [check_id for check_id in required_ids if cmo3_checks.get(check_id, {}).get("status") not in {"PASS", None}]
    status = "PENDING"
    message = "자동검사 결과가 아직 없습니다."
    if cmo3 or mini:
        has_deformer = int(checks.get("deformer_count") or 0) > 0
        has_keyform = int(checks.get("keyform_binding_count") or 0) > 0
        has_physics = int(checks.get("physics_group_count") or 0) > 0
        status = "PASS" if has_deformer and has_keyform and has_physics and not missing else "REVISE"
        message = (
            "Cubism 구조 gate를 통과할 수 있는 숫자입니다."
            if status == "PASS"
            else "그림 문제가 아니라 Cubism에서 deformer/keyform/physics 보강이 필요합니다."
        )
    return {
        "status": status,
        "message": message,
        "checks": checks,
        "source_reports": {
            "cmo3_report": rel(args.cmo3_report) if args.cmo3_report.exists() else None,
            "mini_validation_report": rel(args.mini_validation_report) if args.mini_validation_report.exists() else None,
            "physics_report": rel(args.physics_report) if args.physics_report.exists() else None,
        },
    }


def build_g2_item(args: argparse.Namespace, tier: str, source_items: list[dict[str, Any]], g1_items: list[dict[str, Any]]) -> dict[str, Any]:
    base = deepcopy(source_items[0]) if source_items else {}
    item = gate_item(base, tier, "G2_STRUCTURE", "g2_structure")
    item.update(
        {
            "part_id": "g2__cubism_structure_auto_check",
            "ko_name": "Cubism 구조 자동검사",
            "simple_label": "구조 자동검사",
            "group": "structure",
            "role": "auto_check",
            "image_path": base.get("canonical_path") or base.get("image_path"),
            "overlay_path": None,
            "include_in_import_psd": False,
            "auto_check_summary": build_auto_summary(args, g1_items),
            "compare_views": {
                "neutral": base.get("canonical_path") or base.get("image_path"),
                "before": asset(args.cmo3_report) if args.cmo3_report.exists() else None,
                "after": asset(args.mini_validation_report) if args.mini_validation_report.exists() else None,
            },
        }
    )
    return item


def motion_paths(args: argparse.Namespace) -> list[tuple[str, Path]]:
    preferred = [
        ("몸각도 흔들림", "angle_swing.gif"),
        ("눈 깜빡임", "eye_blink.gif"),
        ("입 말하기", "mouth_talk.gif"),
        ("머리카락 흔들림", "hair_settle.gif"),
    ]
    found = []
    for label, name in preferred:
        path = args.motion_dir / name
        if path.exists():
            found.append((label, path))
    if not found and args.motion_dir.exists():
        found = [(path.stem.replace("_", " "), path) for path in sorted(args.motion_dir.glob("*.gif"))[:4]]
    return found


def build_g3_items(args: argparse.Namespace, tier: str, source_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    base = source_items[0] if source_items else {}
    items = []
    for label, path in motion_paths(args):
        item = gate_item(base, tier, "G3_MOTION_VISUAL", "g3_motion_visual")
        item.update(
            {
                "part_id": f"g3__{path.stem}",
                "ko_name": label,
                "simple_label": label,
                "group": "motion",
                "role": "motion_visual",
                "image_path": asset(path),
                "overlay_path": asset(path),
                "canonical_path": base.get("canonical_path") or base.get("image_path"),
                "include_in_import_psd": False,
                "compare_views": {
                    "neutral": base.get("canonical_path") or base.get("image_path"),
                    "extreme": asset(path),
                    "after": asset(path),
                    "composited": asset(path),
                },
            }
        )
        items.append(item)
    return items


def main() -> int:
    args = parse_args()
    source = load_json(args.source_review_manifest)
    source_items = all_source_items(source)
    if source.get("mode") == "cubism_v2" or not source_items:
        source_items = fallback_layer_items()
    if not source_items:
        raise SystemExit(f"FAIL: no source items found in {args.source_review_manifest}")

    g0_items = build_g0_items(source_items, args.tier)
    g1_items = build_g1_items(source_items, args.tier)
    g2_items = [build_g2_item(args, args.tier, source_items, g1_items)]
    g3_items = build_g3_items(args, args.tier, source_items)

    generated_at = datetime.now(timezone.utc).isoformat()
    manifest = {
        "schema_version": 2,
        "experiment_id": "cubism-v2-review-001",
        "mode": "cubism_v2",
        "tier": args.tier,
        "generated_at": generated_at,
        "source_review_manifest": rel(args.source_review_manifest),
        "source_success_pattern_spec": rel(args.success_spec) if args.success_spec.exists() else None,
        "review_outputs": {
            "part_visual_review": "experiments/cubism-v2-review-001/reports/part_visual_review.json",
            "ai_fix_queue": "experiments/cubism-v2-review-001/reports/ai_fix_queue.json",
            "review_packet": "experiments/cubism-v2-review-001/review_packet",
        },
        "ui": {
            "title": "Cubism v2 쉬운 검수",
            "subtitle": "캐릭터, 파츠, 구조, 움직임을 차례대로 보고 실패 후보만 다시 모읍니다.",
            "primary_section": "g0_concept" if g0_items else "g1_part_taxonomy",
            "tier_labels": {
                "v2_min": "최소형",
                "v2_standard": "표준형",
                "v2_rich": "풍부형",
            },
        },
        "issue_tags": ISSUE_TAGS,
        "sections": {
            "g0_concept": g0_items,
            "g1_part_taxonomy": g1_items,
            "g2_structure": g2_items,
            "g3_motion_visual": g3_items,
        },
    }
    manifest["counts"] = {key: len(value) for key, value in manifest["sections"].items()}

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {args.out.relative_to(ROOT)}")
    print(json.dumps(manifest["counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Extract auxiliary Live2D runtime metadata from the official reference corpus."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_EXP = ROOT / "experiments" / "reference-model-structure-001"
DEFAULT_CATALOG = REFERENCE_EXP / "catalog.official_combined.json"
DEFAULT_OUT_DIR = REFERENCE_EXP / "reports"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path | str | None) -> str | None:
    if path is None:
        return None
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return p.resolve().as_posix()


def resolve_path(path: str | Path | None, base: Path | None = None) -> Path | None:
    if not path:
        return None
    p = Path(path)
    if p.is_absolute():
        return p
    if base is not None:
        candidate = base / p
        if candidate.exists():
            return candidate
    return ROOT / p


def as_list(value: Any) -> list[Any]:
    if not value:
        return []
    if isinstance(value, list):
        return value
    return [value]


def sample(items: list[Any], limit: int = 8) -> list[Any]:
    return items[:limit]


def infer_file_reference(model3_path: Path | None, model3: dict[str, Any], key: str) -> Path | None:
    if not model3_path:
        return None
    ref = model3.get("FileReferences", {}).get(key)
    if not ref or not isinstance(ref, str):
        return None
    return resolve_path(ref, model3_path.parent)


def infer_expression_paths(model3_path: Path | None, model3: dict[str, Any]) -> list[Path]:
    if not model3_path:
        return []
    paths = []
    for entry in model3.get("FileReferences", {}).get("Expressions", []) or []:
        if isinstance(entry, dict) and entry.get("File"):
            path = resolve_path(entry["File"], model3_path.parent)
            if path and path.exists():
                paths.append(path)
    return paths


def parse_cdi3(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {"present": False}
    data = load_json(path)
    parameters = data.get("Parameters", []) or []
    groups = data.get("ParameterGroups", []) or data.get("Groups", []) or []
    parts = data.get("Parts", []) or []
    combined = data.get("CombinedParameters", []) or []
    return {
        "present": True,
        "path": rel(path),
        "parameter_display_count": len(parameters),
        "parameter_group_count": len(groups),
        "part_display_count": len(parts),
        "combined_parameter_count": len(combined),
        "parameter_groups": sample(
            [
                {"id": item.get("Id"), "parent_group_id": item.get("GroupId"), "name": item.get("Name")}
                for item in groups
            ]
        ),
        "parameter_display_samples": sample(
            [
                {"id": item.get("Id"), "group_id": item.get("GroupId"), "name": item.get("Name")}
                for item in parameters
            ],
            12,
        ),
        "part_display_samples": sample(
            [{"id": item.get("Id"), "name": item.get("Name")} for item in parts],
            12,
        ),
    }


def parse_pose3(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {"present": False}
    data = load_json(path)
    groups = data.get("Groups", []) or []
    part_ids: set[str] = set()
    linked_ids: set[str] = set()
    group_sizes = []
    group_samples = []
    for group in groups:
        if not isinstance(group, list):
            continue
        group_sizes.append(len(group))
        group_sample = []
        for part in group:
            if not isinstance(part, dict):
                continue
            part_id = part.get("Id")
            if part_id:
                part_ids.add(part_id)
            links = [x for x in part.get("Link", []) or [] if x]
            linked_ids.update(links)
            group_sample.append({"id": part_id, "links": links[:5]})
        if group_sample:
            group_samples.append(group_sample[:6])
    return {
        "present": True,
        "path": rel(path),
        "group_count": len(groups),
        "part_switch_count": len(part_ids),
        "linked_part_count": len(linked_ids),
        "max_group_size": max(group_sizes) if group_sizes else 0,
        "switch_part_samples": sample(sorted(part_ids), 16),
        "group_samples": sample(group_samples, 4),
    }


def parse_userdata3(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {"present": False}
    data = load_json(path)
    user_data = data.get("UserData", []) or []
    by_target = Counter(item.get("Target") for item in user_data if isinstance(item, dict))
    artmesh = [item for item in user_data if isinstance(item, dict) and item.get("Target") == "ArtMesh"]
    return {
        "present": True,
        "path": rel(path),
        "entry_count": len(user_data),
        "target_counts": dict(sorted(by_target.items())),
        "artmesh_user_data_count": len(artmesh),
        "artmesh_samples": sample(
            [
                {"id": item.get("Id"), "value": item.get("Value")}
                for item in artmesh
            ],
            12,
        ),
    }


def parse_exp3(paths: list[Path]) -> dict[str, Any]:
    existing = [path for path in paths if path.exists()]
    if not existing:
        return {"present": False, "expression_count": 0}
    blend_counts: Counter[str] = Counter()
    affected_parameters: Counter[str] = Counter()
    fade_in_values = []
    fade_out_values = []
    expression_samples = []
    for path in existing:
        data = load_json(path)
        params = data.get("Parameters", []) or []
        for param in params:
            blend_counts[param.get("Blend", "UNKNOWN")] += 1
            if param.get("Id"):
                affected_parameters[param["Id"]] += 1
        if isinstance(data.get("FadeInTime"), (int, float)):
            fade_in_values.append(float(data["FadeInTime"]))
        if isinstance(data.get("FadeOutTime"), (int, float)):
            fade_out_values.append(float(data["FadeOutTime"]))
        expression_samples.append(
            {
                "path": rel(path),
                "fade_in": data.get("FadeInTime"),
                "fade_out": data.get("FadeOutTime"),
                "parameter_count": len(params),
                "parameter_samples": sample(
                    [
                        {"id": item.get("Id"), "value": item.get("Value"), "blend": item.get("Blend")}
                        for item in params
                    ],
                    8,
                ),
            }
        )
    return {
        "present": True,
        "expression_count": len(existing),
        "parameter_binding_count": sum(affected_parameters.values()),
        "unique_parameter_count": len(affected_parameters),
        "blend_counts": dict(sorted(blend_counts.items())),
        "fade_in_avg": round(mean(fade_in_values), 4) if fade_in_values else None,
        "fade_out_avg": round(mean(fade_out_values), 4) if fade_out_values else None,
        "top_affected_parameters": affected_parameters.most_common(16),
        "expression_samples": sample(expression_samples, 8),
    }


def parse_model3(model3_path: Path | None) -> tuple[dict[str, Any], dict[str, Any]]:
    if not model3_path or not model3_path.exists():
        return {"present": False}, {}
    data = load_json(model3_path)
    groups = data.get("Groups", []) or []
    hit_areas = data.get("HitAreas", []) or []
    file_refs = data.get("FileReferences", {}) or {}
    motion_sync = file_refs.get("MotionSync")
    motion_sync_motion_labels = []
    motion_sound_count = 0
    for group_name, motions in (file_refs.get("Motions", {}) or {}).items():
        for motion in motions or []:
            if not isinstance(motion, dict):
                continue
            if motion.get("MotionSync"):
                motion_sync_motion_labels.append({"group": group_name, "motion_sync": motion.get("MotionSync")})
            if motion.get("Sound"):
                motion_sound_count += 1
    group_map = defaultdict(list)
    for group in groups:
        if isinstance(group, dict):
            group_map[group.get("Name", "")].extend(group.get("Ids", []) or [])
    parsed = {
        "present": True,
        "path": rel(model3_path),
        "hit_area_count": len(hit_areas),
        "hit_areas": sample(
            [{"id": item.get("Id"), "name": item.get("Name")} for item in hit_areas if isinstance(item, dict)],
            16,
        ),
        "group_count": len(groups),
        "eyeblink_parameters": sorted(set(group_map.get("EyeBlink", []))),
        "lipsync_parameters": sorted(set(group_map.get("LipSync", []))),
        "has_motion_sync_reference": bool(motion_sync),
        "motion_sync_reference": motion_sync,
        "motion_sync_motion_label_count": len(motion_sync_motion_labels),
        "motion_sync_motion_label_samples": sample(motion_sync_motion_labels, 8),
        "motion_sound_count": motion_sound_count,
        "file_references": {
            "has_display_info": bool(file_refs.get("DisplayInfo")),
            "has_pose": bool(file_refs.get("Pose")),
            "has_user_data": bool(file_refs.get("UserData")),
            "has_expressions": bool(file_refs.get("Expressions")),
            "has_physics": bool(file_refs.get("Physics")),
            "has_motion_sync": bool(file_refs.get("MotionSync")),
        },
    }
    return parsed, data


def parse_motionsync3(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {"present": False}
    data = load_json(path)
    settings = data.get("Settings", []) or data.get("Groups", []) or []
    setting_samples = []
    for item in settings:
        if not isinstance(item, dict):
            continue
        values = item.get("Values", []) or item.get("Parameters", []) or []
        setting_samples.append(
            {
                "id": item.get("Id") or item.get("Name"),
                "value_count": len(values),
                "value_samples": sample(values, 8),
            }
        )
    return {
        "present": True,
        "path": rel(path),
        "setting_count": len(settings),
        "setting_samples": sample(setting_samples, 8),
        "top_level_keys": list(data.keys()),
    }


def collect_model(entry: dict[str, Any]) -> dict[str, Any]:
    local_paths = entry.get("local_paths", {}) or {}
    model3_path = resolve_path(local_paths.get("model3_json"))
    model3_summary, model3_data = parse_model3(model3_path)
    model3_dir = model3_path.parent if model3_path and model3_path.exists() else None

    cdi_path = resolve_path(local_paths.get("cdi3_json")) or infer_file_reference(model3_path, model3_data, "DisplayInfo")
    pose_path = resolve_path(local_paths.get("pose3_json")) or infer_file_reference(model3_path, model3_data, "Pose")
    userdata_path = resolve_path(local_paths.get("userdata3_json")) or infer_file_reference(model3_path, model3_data, "UserData")
    motionsync_path = (
        resolve_path(local_paths.get("motionsync3_json"))
        or infer_file_reference(model3_path, model3_data, "MotionSync")
    )

    exp_paths = [resolve_path(path) for path in as_list(local_paths.get("exp3_json"))]
    exp_paths = [path for path in exp_paths if path is not None]
    if not exp_paths:
        exp_paths = infer_expression_paths(model3_path, model3_data)
    if model3_dir:
        exp_paths = [path if path.exists() else resolve_path(path.as_posix(), model3_dir) for path in exp_paths]
        exp_paths = [path for path in exp_paths if path is not None]

    return {
        "id": entry.get("id"),
        "name": entry.get("name"),
        "source_type": entry.get("source_type"),
        "analysis_mode": entry.get("analysis_mode"),
        "model3": model3_summary,
        "cdi3": parse_cdi3(cdi_path),
        "pose3": parse_pose3(pose_path),
        "userdata3": parse_userdata3(userdata_path),
        "exp3": parse_exp3(exp_paths),
        "motionsync3": parse_motionsync3(motionsync_path),
    }


def build_summary(models: list[dict[str, Any]]) -> dict[str, Any]:
    def count_present(key: str) -> int:
        return sum(1 for model in models if model[key].get("present"))

    hit_area_models = [model for model in models if model["model3"].get("hit_area_count", 0) > 0]
    lipsync_models = [model for model in models if model["model3"].get("lipsync_parameters")]
    eyeblink_models = [model for model in models if model["model3"].get("eyeblink_parameters")]
    expression_models = [model for model in models if model["exp3"].get("present")]
    pose_models = [model for model in models if model["pose3"].get("present")]
    motionsync_models = [model for model in models if model["motionsync3"].get("present")]

    top_expression_params: Counter[str] = Counter()
    blend_counts: Counter[str] = Counter()
    for model in expression_models:
        top_expression_params.update(dict(model["exp3"].get("top_affected_parameters", [])))
        blend_counts.update(model["exp3"].get("blend_counts", {}))

    return {
        "model_count": len(models),
        "coverage": {
            "model3_json": count_present("model3"),
            "cdi3_json": count_present("cdi3"),
            "pose3_json": count_present("pose3"),
            "userdata3_json": count_present("userdata3"),
            "exp3_json_models": count_present("exp3"),
            "motionsync3_json": count_present("motionsync3"),
            "hit_area_models": len(hit_area_models),
            "lipsync_group_models": len(lipsync_models),
            "eyeblink_group_models": len(eyeblink_models),
        },
        "averages": {
            "cdi_parameter_display_count": round(mean([m["cdi3"]["parameter_display_count"] for m in models if m["cdi3"].get("present")]), 2)
            if count_present("cdi3")
            else 0,
            "cdi_part_display_count": round(mean([m["cdi3"]["part_display_count"] for m in models if m["cdi3"].get("present")]), 2)
            if count_present("cdi3")
            else 0,
            "pose_group_count": round(mean([m["pose3"]["group_count"] for m in pose_models]), 2) if pose_models else 0,
            "expression_count": round(mean([m["exp3"]["expression_count"] for m in expression_models]), 2) if expression_models else 0,
            "hit_area_count": round(mean([m["model3"]["hit_area_count"] for m in hit_area_models]), 2) if hit_area_models else 0,
        },
        "expression_blend_counts": dict(sorted(blend_counts.items())),
        "top_expression_parameters": top_expression_params.most_common(20),
        "models_with_pose_switching": [m["id"] for m in pose_models],
        "models_with_expressions": [m["id"] for m in expression_models],
        "models_with_userdata": [m["id"] for m in models if m["userdata3"].get("present")],
        "models_with_motionsync": [m["id"] for m in motionsync_models],
        "production_use": {
            "before_character_image": [
                "cdi3의 표시 이름과 그룹은 새 모델 파츠/파라미터 명명 규칙을 사람이 읽기 쉽게 만드는 데 사용한다.",
                "pose3는 v2_standard에서는 복잡한 팔/의상 전환을 미루고, simple shoulder/arm만 유지할 근거로 사용한다.",
                "exp3는 기본 표정 세트와 fade 0.5초 전후의 부드러운 전환 기준으로 사용한다.",
                "HitAreas는 runtime export 때 얼굴/몸 터치 영역을 model3.json에 넣을 체크리스트로 사용한다.",
                "MotionSync는 Kei 계열의 고급 립싱크 참조다. v2_standard 첫 모델에서는 LipSync group만 준비하고, motionsync3는 v2_rich/고급 립싱크 단계로 미룬다.",
            ],
            "not_blockers_for_first_image": [
                "userdata3",
                "motionsync3",
                "pose3 arm switching",
                "rich expression pack",
            ],
        },
    }


def build_payload(catalog_path: Path) -> dict[str, Any]:
    catalog = load_json(catalog_path)
    models = [collect_model(entry) for entry in catalog.get("models", [])]
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "kind": "live2d_all57_runtime_metadata_extras",
        "input_catalog": rel(catalog_path),
        "safety_note": "Official sample art/textures are not reused. This report only extracts runtime metadata structure and design patterns.",
        "web_reference_basis": [
            {
                "topic": "Runtime JSON file roles",
                "url": "https://docs.live2d.com/en/cubism-sdk-manual/json-ue/",
            },
            {
                "topic": "File extensions and roles",
                "url": "https://docs.live2d.com/ko/cubism-editor-manual/file-type-and-extension/",
            },
            {
                "topic": "MotionSync Web settings",
                "url": "https://docs.live2d.com/en/cubism-sdk-manual/motion-sync-setting-web/",
            },
        ],
        "summary": build_summary(models),
        "models": models,
    }


def write_md(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    coverage = summary["coverage"]
    averages = summary["averages"]
    lines = [
        "# Live2D All57 Runtime Metadata Extras",
        "",
        "## 결론",
        "",
        "- 새 캐릭터 컨셉/이미지 생성 전에 추가로 뽑을 만한 보조 정보는 있다.",
        "- 다만 이것들은 첫 이미지 생성의 blocker가 아니라, 이후 runtime/export/운영 설계 체크리스트다.",
        "- v2_standard 첫 모델은 64파트 taxonomy와 기존 deformer/keyform/physics spec을 유지한다.",
        "",
        "## Coverage",
        "",
        "| Item | Count |",
        "|---|---:|",
    ]
    for key, value in coverage.items():
        lines.append(f"| {key} | {value} |")
    lines += [
        "",
        "## 평균값",
        "",
        "| Item | Avg |",
        "|---|---:|",
    ]
    for key, value in averages.items():
        lines.append(f"| {key} | {value} |")
    lines += [
        "",
        "## 컨셉 생성 전에 반영할 점",
        "",
    ]
    for item in summary["production_use"]["before_character_image"]:
        lines.append(f"- {item}")
    lines += [
        "",
        "## 첫 이미지 생성의 blocker가 아닌 항목",
        "",
    ]
    for item in summary["production_use"]["not_blockers_for_first_image"]:
        lines.append(f"- {item}")
    lines += [
        "",
        "## 표정 파라미터 상위 패턴",
        "",
        "| Parameter | Count |",
        "|---|---:|",
    ]
    for param, count in summary["top_expression_parameters"]:
        lines.append(f"| {param} | {count} |")
    lines += [
        "",
        "## MotionSync",
        "",
        f"- MotionSync 보유 모델: {', '.join(summary['models_with_motionsync']) if summary['models_with_motionsync'] else 'none'}",
        "- 공식 문서 기준 `.motionsync3.json`은 BlendRatio/SampleRate/Smoothing/AudioLevelEffectRatio 같은 고급 립싱크 설정을 담는다.",
        "- 첫 v2_standard에서는 `LipSync` group과 `ParamMouthOpenY/ParamMouthForm`를 우선하고, vowels/MotionSync는 다음 단계로 둔다.",
        "",
        "## 모델별 요약",
        "",
        "| Model | CDI params | Pose groups | Expressions | HitAreas | UserData | MotionSync |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for model in payload["models"]:
        lines.append(
            "| {id} | {cdi} | {pose} | {exp} | {hit} | {ud} | {ms} |".format(
                id=model["id"],
                cdi=model["cdi3"].get("parameter_display_count", 0),
                pose=model["pose3"].get("group_count", 0),
                exp=model["exp3"].get("expression_count", 0),
                hit=model["model3"].get("hit_area_count", 0),
                ud=1 if model["userdata3"].get("present") else 0,
                ms=1 if model["motionsync3"].get("present") else 0,
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    payload = build_payload(args.catalog)
    out_json = args.out_dir / "all57_runtime_metadata_extras.json"
    out_md = args.out_dir / "all57_runtime_metadata_extras.md"
    write_json(out_json, payload)
    write_md(out_md, payload)
    print(
        json.dumps(
            {
                "status": "PASS",
                "json": rel(out_json),
                "markdown": rel(out_md),
                "coverage": payload["summary"]["coverage"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

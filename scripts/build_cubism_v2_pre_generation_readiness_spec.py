#!/usr/bin/env python3
"""Build the Cubism v2 new-character pre-generation readiness spec."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_REPORTS = ROOT / "experiments" / "reference-model-structure-001" / "reports"
STRONG_REPORTS = ROOT / "experiments" / "live2d-strong-model-pattern-001" / "reports"
DEFAULT_PART_SPEC = REFERENCE_REPORTS / "cubism_v2_new_model_v2_standard_part_spec.json"
DEFAULT_PARAMETER_SWEEP = STRONG_REPORTS / "strong20_parameter_single_sweep_report.json"
DEFAULT_CORE_REPORT = STRONG_REPORTS / "strong20_core_api_extractor_report.json"
DEFAULT_DEEP_REPORT = STRONG_REPORTS / "deep_reference_motion_analysis.json"
DEFAULT_RUNTIME_METADATA_EXTRAS = REFERENCE_REPORTS / "all57_runtime_metadata_extras.json"
DEFAULT_OUT = REFERENCE_REPORTS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part-spec", type=Path, default=DEFAULT_PART_SPEC)
    parser.add_argument("--parameter-sweep", type=Path, default=DEFAULT_PARAMETER_SWEEP)
    parser.add_argument("--core-report", type=Path, default=DEFAULT_CORE_REPORT)
    parser.add_argument("--deep-report", type=Path, default=DEFAULT_DEEP_REPORT)
    parser.add_argument("--runtime-metadata-extras", type=Path, default=DEFAULT_RUNTIME_METADATA_EXTRAS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return load_json(path)


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


def sweep_category_summary(parameter_sweep: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for category, item in parameter_sweep.get("summary_by_category", {}).items():
        changed = item.get("changed_ratio", {})
        out[category] = {
            "sample_count": item.get("sample_count", 0),
            "parameter_count": item.get("parameter_count", 0),
            "median_changed_ratio": changed.get("median"),
            "max_changed_ratio": changed.get("max"),
            "production_interpretation": {
                "eye": "작은 변화도 정상이다. 눈은 bbox가 작으므로 L/R open, eyeball X의 비어있지 않은 변화와 위치 정렬을 본다.",
                "mouth": "입은 localized 변화가 정상이다. OpenY/Form 둘 다 nonzero bbox를 가져야 한다.",
                "hair": "머리는 medium 변화가 정상이다. HairFront/Side가 빈 변화면 physics/keyform 후보가 부족하다.",
                "body_angle": "몸/머리 각도는 넓은 변화가 가능하다. 너무 큰 변화는 overhang/draw-order 위험을 같이 본다.",
            }.get(category, "보조 파라미터로 취급한다."),
        }
    return out


def required_parameters_from_part_spec(part_spec: dict[str, Any]) -> list[str]:
    params = set()
    for part in part_spec.get("parts", []):
        for param in part.get("parameters", []):
            if " or " in param or "/" in param:
                continue
            params.add(param)
    return sorted(params)


def build_payload(
    part_spec: dict[str, Any],
    parameter_sweep: dict[str, Any],
    core_report: dict[str, Any],
    deep_report: dict[str, Any],
    runtime_metadata_extras: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    required_params = required_parameters_from_part_spec(part_spec)
    swept_params = set(parameter_sweep.get("summary_by_parameter", {}).keys())
    core_summary = core_report.get("summary", {})
    deep_core = deep_report.get("official_cubism_core_extractor", {})

    checklist = [
        {
            "gate": "G0_CONCEPT",
            "label_ko": "캐릭터 고르기",
            "pass_conditions": [
                "정면 또는 거의 정면의 상반신 캐릭터다.",
                "눈, 입, 앞머리, 옆머리, 뒷머리, 목, 어깨/팔 경계가 한눈에 보인다.",
                "큰 소품, 복잡한 손가락, 얼굴을 가리는 장식, 강한 투명 이펙트를 넣지 않는다.",
                "1024/1536/2048 중 하나를 쓸 수 있지만 해상도보다 파츠 분리 가능성이 우선이다.",
            ],
            "fail_if": [
                "옆얼굴/극단 포즈라 반대 방향 회전 keyform을 만들기 어렵다.",
                "머리카락이 얼굴/눈/입을 과하게 덮어 mask가 필수다.",
                "팔이 몸통과 복잡하게 겹쳐 shoulder/arm simple 범위를 넘는다.",
            ],
        },
        {
            "gate": "G1_PART_TAXONOMY",
            "label_ko": "파츠 나누기",
            "pass_conditions": [
                "64파트 v2_standard taxonomy를 기준으로 face/eye/mouth/hair/body/clothing 후보가 모두 있다.",
                "눈 L/R 각각 white/iris/pupil/highlight/lash/lid/underpaint가 있다.",
                "입은 line/inner/lip masks/teeth/tongue/corners가 분리된다.",
                "머리는 front/side/back이 분리되고 최소 5개 physics group에 연결 가능하다.",
                "underpaint 후보가 face/eye/hair/body에서 누락되지 않는다.",
            ],
            "fail_if": [
                "한 파츠가 여러 기능을 합쳐서 ParamEyeOpen/MouthOpenY/HairFront keyform을 분리하기 어렵다.",
                "alpha 테두리가 지저분하거나 bbox crop이 너무 빡빡하다.",
            ],
        },
        {
            "gate": "G2_STRUCTURE",
            "label_ko": "구조 자동검사",
            "pass_conditions": [
                "v2_standard floor: parameters >=25, warp >=35, rotation >=8, keyform >=120, physics_groups >=4.",
                "CMO3 inspector before/after 비교에서 warp/keyform 증가가 검출된다.",
                "Core/runtime export 후 Parameters/Parts/Drawables snapshot이 생성된다.",
            ],
            "fail_if": [
                "ArtMesh/Parameter만 있고 Warp/Rotation Deformer나 KeyformBinding이 0에 가깝다.",
                "runtime은 보이지만 CMO3 구조가 shallow import 수준이다.",
            ],
        },
        {
            "gate": "G3_MOTION_VISUAL",
            "label_ko": "움직임 보기",
            "pass_conditions": [
                "단일 파라미터 sweep에서 ParamAngleX/Y, ParamEyeLOpen/ROpen, ParamMouthOpenY/Form, ParamHairFront/Side가 nonblank 변화를 만든다.",
                "neutral vs extreme strip에서 눈/입/머리/몸각도 변화가 잘리고 겹치지 않는다.",
                "mask/draw-order risk가 높은 파츠는 onion-skin 또는 before/after strip으로 사람이 확인한다.",
            ],
            "fail_if": [
                "파라미터를 움직여도 화면 변화가 거의 없다.",
                "움직임은 생기지만 눈/입/머리/팔이 서로 앞뒤 순서를 깨뜨린다.",
            ],
        },
    ]

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "spec_id": "cubism_v2_new_model_pre_generation_readiness",
        "status": "READY_FOR_CHARACTER_GENERATION_CHECKLIST",
        "inputs": {
            "part_spec": rel(args.part_spec),
            "parameter_single_sweep": rel(args.parameter_sweep),
            "core_report": rel(args.core_report),
            "deep_report": rel(args.deep_report),
            "runtime_metadata_extras": rel(args.runtime_metadata_extras)
            if args.runtime_metadata_extras.exists()
            else None,
        },
        "skillization_decision": {
            "decision": "UPDATE_EXISTING_SKILL_AND_HARNESS",
            "reason_ko": "이미 vtube-cubism-success-pattern-workflow 스킬과 vtube-live2d-strong-model-pattern 하네스가 있으므로 새 스킬을 늘리기보다 Core extractor와 parameter single sweep 절차를 기존 흐름에 추가한다.",
            "skill_to_update": "/Users/family/.codex/skills/vtube-cubism-success-pattern-workflow/SKILL.md",
            "harnesses_to_update": [
                "/Users/family/jason/jason-agent-harness-template/harnesses/vtube-live2d-strong-model-pattern.md",
                "/Users/family/jason/jason-agent-harness-template/harnesses/vtube-live2d-all57-production-design.md",
            ],
            "new_skill_needed": False,
        },
        "reference_scope_decision": {
            "decision": "DO_NOT_EXPAND_FULL_RUNTIME_BEYOND_STRONG20_FOR_V2_STANDARD_NOW",
            "reason_ko": "all57은 이미 static structure/parameter/deformer/physics 설계표에 반영됐고, strong20은 runtime render/Core/single-parameter/motion/physics evidence를 모두 통과했다. v2_standard 첫 production 설계에는 충분하다.",
            "analyze_more_when": [
                "v2_rich로 넘어가서 offscreen/mask/effect-heavy 표현을 목표로 할 때",
                "비인간/SD/측면 포즈/큰 팔 스위칭 모델을 목표로 할 때",
                "새 캐릭터 디자인이 strong20 범위 밖의 장식, 소품, 긴 의상, 특수 머리카락 구조를 요구할 때",
            ],
            "next_optional_reference_batch": [
                "Ren/Rice/Mao 같은 high mask/offscreen/effect 모델 재분석",
                "Miku/Hiyori 같은 long hair physics 모델 단독 심화",
                "Kei mouth/vowel 모델 lip-sync 심화",
            ],
        },
        "part_spec_decision": {
            "decision": "KEEP_64_PART_V2_STANDARD",
            "reason_ko": "parameter single sweep과 Core risk를 봐도 64파트 taxonomy는 눈/입/머리/몸각도 production gate를 커버한다. 지금은 파츠 수를 늘리지 말고 mask와 draw-order 위험을 줄이는 생성 조건을 강화한다.",
            "part_count": part_spec.get("target", {}).get("part_count"),
            "required_parameters_from_part_spec": required_params,
            "swept_required_parameters": sorted(set(required_params) & swept_params),
            "not_swept_yet_but_required": sorted(set(required_params) - swept_params),
        },
        "parameter_single_sweep_policy": {
            "evidence_status": parameter_sweep.get("status"),
            "summary": parameter_sweep.get("summary"),
            "category_summary": sweep_category_summary(parameter_sweep),
            "required_g3_single_sweep_parameters_for_new_model": [
                "ParamAngleX",
                "ParamAngleY",
                "ParamEyeLOpen",
                "ParamEyeROpen",
                "ParamEyeBallX",
                "ParamMouthOpenY",
                "ParamMouthForm",
                "ParamHairFront",
                "ParamHairSide",
            ],
        },
        "core_runtime_policy": {
            "evidence_status": core_report.get("status"),
            "summary": core_summary,
            "deep_core_status": deep_core.get("status"),
            "new_model_mask_policy": {
                "target": "LOW_TO_MEDIUM_RISK",
                "avoid": [
                    "inverted masks unless visually necessary",
                    "offscreen-rich effects in v2_standard",
                    "hair covering eyes/mouth so much that clipping becomes mandatory",
                ],
                "allowed": [
                    "small eye/mouth clipping masks when needed",
                    "simple draw-order bands for hair_front/face/eye/mouth/body",
                ],
            },
        },
        "runtime_metadata_extras_policy": {
            "evidence_status": "PASS" if runtime_metadata_extras else "NOT_AVAILABLE",
            "summary": runtime_metadata_extras.get("summary", {}),
            "new_model_before_image_policy": {
                "use_now": [
                    "cdi3 표시 이름/그룹을 참고해 파츠와 파라미터 이름을 사람이 읽기 좋게 정한다.",
                    "HitAreas 패턴을 참고해 얼굴/몸 터치 영역은 runtime export 체크리스트에 미리 둔다.",
                    "EyeBlink/LipSync group은 첫 모델부터 준비한다.",
                    "exp3 패턴은 기본 표정 세트와 fade 기준으로만 참고한다.",
                ],
                "defer": [
                    "pose3 기반 복잡한 팔/의상 전환",
                    "userdata3 ArtMesh annotation",
                    "motionsync3 고급 립싱크 설정",
                    "대량 expression pack",
                ],
                "decision": "DO_NOT_BLOCK_FIRST_CHARACTER_IMAGE",
            },
        },
        "pre_generation_checklist": checklist,
    }


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Cubism v2 New Model Pre-generation Readiness",
        "",
        "## 결론",
        "",
        f"- status: `{payload['status']}`",
        f"- 스킬화 결정: `{payload['skillization_decision']['decision']}`",
        f"- 추가 모델 분석 결정: `{payload['reference_scope_decision']['decision']}`",
        f"- 파츠 spec 결정: `{payload['part_spec_decision']['decision']}`",
        f"- 보조 런타임 메타데이터: `{payload['runtime_metadata_extras_policy']['evidence_status']}`",
        "",
        "## 왜 strong20 밖 전체 런타임 분석을 지금 안 늘리나",
        "",
        f"- {payload['reference_scope_decision']['reason_ko']}",
        "- 더 분석할 때는 v2_rich/effect/비인간/측면/복잡한 팔처럼 새 모델 목표가 바뀔 때다.",
        "",
        "## 단일 파라미터 Sweep 반영",
        "",
        f"- evidence: `{payload['inputs']['parameter_single_sweep']}`",
        f"- samples: `{payload['parameter_single_sweep_policy']['summary']['sample_count']}`",
        f"- parameters: `{payload['parameter_single_sweep_policy']['summary']['parameter_count']}`",
        "",
        "| Category | Samples | Parameters | Median Changed | Max Changed |",
        "|---|---:|---:|---:|---:|",
    ]
    for category, item in sorted(payload["parameter_single_sweep_policy"]["category_summary"].items()):
        lines.append(
            f"| {category} | {item['sample_count']} | {item['parameter_count']} | {item['median_changed_ratio']} | {item['max_changed_ratio']} |"
        )
    metadata_summary = payload["runtime_metadata_extras_policy"].get("summary", {})
    metadata_coverage = metadata_summary.get("coverage", {})
    if metadata_coverage:
        lines += [
            "",
            "## 보조 런타임 메타데이터 반영",
            "",
            f"- evidence: `{payload['inputs']['runtime_metadata_extras']}`",
            f"- cdi3: `{metadata_coverage.get('cdi3_json')}`",
            f"- pose3: `{metadata_coverage.get('pose3_json')}`",
            f"- userdata3: `{metadata_coverage.get('userdata3_json')}`",
            f"- exp3 model groups: `{metadata_coverage.get('exp3_json_models')}`",
            f"- hit area models: `{metadata_coverage.get('hit_area_models')}`",
            f"- motionsync3: `{metadata_coverage.get('motionsync3_json')}`",
            f"- 결정: `{payload['runtime_metadata_extras_policy']['new_model_before_image_policy']['decision']}`",
            "",
        ]
    lines += [
        "",
        "## 새 캐릭터 생성 전 체크리스트",
        "",
    ]
    for gate in payload["pre_generation_checklist"]:
        lines.append(f"### {gate['gate']} - {gate['label_ko']}")
        lines.append("")
        lines.append("PASS:")
        for item in gate["pass_conditions"]:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("FAIL:")
        for item in gate["fail_if"]:
            lines.append(f"- {item}")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    payload = build_payload(
        load_json(args.part_spec),
        load_json(args.parameter_sweep),
        load_json(args.core_report),
        load_json(args.deep_report),
        load_json_if_exists(args.runtime_metadata_extras),
        args,
    )
    out_json = args.out_dir / "cubism_v2_new_model_pre_generation_readiness.json"
    out_md = args.out_dir / "cubism_v2_new_model_pre_generation_readiness.md"
    write_json(out_json, payload)
    write_md(out_md, payload)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "json": rel(out_json),
                "markdown": rel(out_md),
                "reference_scope_decision": payload["reference_scope_decision"]["decision"],
                "part_spec_decision": payload["part_spec_decision"]["decision"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

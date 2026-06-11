#!/usr/bin/env python3
"""Build Cubism v2 character prompt templates from production design evidence."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_REPORTS = ROOT / "experiments" / "reference-model-structure-001" / "reports"
DEFAULT_PRODUCTION_SPEC = REFERENCE_REPORTS / "cubism_v2_production_design_spec.json"
DEFAULT_PART_SPEC = REFERENCE_REPORTS / "cubism_v2_new_model_v2_standard_part_spec.json"
DEFAULT_READINESS = REFERENCE_REPORTS / "cubism_v2_new_model_pre_generation_readiness.json"
DEFAULT_OUT_DIR = REFERENCE_REPORTS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--production-spec", type=Path, default=DEFAULT_PRODUCTION_SPEC)
    parser.add_argument("--part-spec", type=Path, default=DEFAULT_PART_SPEC)
    parser.add_argument("--readiness", type=Path, default=DEFAULT_READINESS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
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


def part_group_summary(part_spec: dict[str, Any]) -> dict[str, Any]:
    parts = part_spec.get("parts", []) or []
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for part in parts:
        groups[part.get("group") or "unknown"].append(part)
    return {
        "total_part_count": len(parts),
        "group_counts": dict(sorted(Counter(part.get("group") or "unknown" for part in parts).items())),
        "required_groups": sorted(groups.keys()),
        "part_ids_by_group": {
            group: [part.get("id") for part in items if part.get("id")]
            for group, items in sorted(groups.items())
        },
    }


def gate_summary(readiness: dict[str, Any], production: dict[str, Any]) -> list[dict[str, Any]]:
    readiness_gates = {item.get("gate"): item for item in readiness.get("pre_generation_checklist", []) or []}
    production_gates = {item.get("gate"): item for item in production.get("acceptance_checklist_g0_g3", []) or []}
    gates = []
    for gate in ["G0_CONCEPT", "G1_PART_TAXONOMY", "G2_STRUCTURE", "G3_MOTION_VISUAL"]:
        source = readiness_gates.get(gate, {})
        production_gate = production_gates.get(gate, {})
        gates.append(
            {
                "gate": gate,
                "label_ko": source.get("label_ko") or production_gate.get("label_ko"),
                "prompt_relevance": {
                    "G0_CONCEPT": "이미지 생성 전 컨셉/구도 조건",
                    "G1_PART_TAXONOMY": "64파트로 분리 가능한 시각 구조 조건",
                    "G2_STRUCTURE": "리깅 구조를 만들 수 있게 겹침과 파츠 경계를 제한하는 조건",
                    "G3_MOTION_VISUAL": "눈/입/머리카락/몸각도 움직임이 보일 수 있는 형태 조건",
                }[gate],
                "pass_conditions": source.get("pass_conditions") or production_gate.get("pass_criteria", []),
                "fail_if": source.get("fail_if") or production_gate.get("fail_criteria", []),
            }
        )
    return gates


def build_template(
    production: dict[str, Any],
    part_spec: dict[str, Any],
    readiness: dict[str, Any],
    input_paths: dict[str, Path],
) -> dict[str, Any]:
    parts = part_group_summary(part_spec)
    gates = gate_summary(readiness, production)
    physics = production.get("physics_blueprint", {})
    hierarchy = production.get("deformer_hierarchy", []) or []
    parameter_map = production.get("parameter_map_detail", []) or []
    required_parameters = [
        item.get("production_name")
        for item in parameter_map
        if item.get("required_level") == "REQUIRED" and item.get("production_name")
    ]
    hierarchy_nodes = [
        item.get("id")
        for item in hierarchy
        if item.get("required_level") == "REQUIRED" and item.get("id")
    ]

    positive_sections = {
        "goal": [
            "Live2D Cubism v2_standard용 정면 상반신 VTuber 캐릭터",
            "single-source matched character design, one clean master PNG",
            "designed for later PSD part separation and Cubism rigging",
        ],
        "composition": [
            "front-facing or near-front upper-body portrait",
            "centered composition, neutral pose, head and shoulders fully visible",
            "clean silhouette with clear head, neck, torso, shoulders, and simple upper arms",
            "symmetrical but natural design, no extreme pose",
        ],
        "face_and_eyes": [
            "clear face base with both eyes fully visible",
            "left and right eye groups are visually separable",
            "distinct eye whites, iris, pupils, highlights, upper eyelids, lower eyelids, and lashes",
            "simple readable eyebrows separated from hair",
            "no hair or accessory covering the eyes",
        ],
        "mouth": [
            "clearly readable mouth centered on the face",
            "mouth not covered by hair, hands, scarf, microphone, or accessories",
            "mouth shape suitable for open/close and form keyforms",
            "visible mouth line and inner mouth area",
        ],
        "hair": [
            "layer-friendly hair design with clear front bangs, left side hair, right side hair, and back hair",
            "front hair clusters are cleanly grouped and do not heavily cover eyes or mouth",
            "side hair and back hair have separated strand groups suitable for physics",
            "no messy dense overlap around face edges",
        ],
        "body_and_arms": [
            "visible neck, simple upper body, clear shoulders",
            "simple left and right upper arms visible without complex hand pose",
            "arms do not cross over the face, mouth, eyes, or center torso",
            "clothing has clean color regions and simple draw order",
        ],
        "rigging_friendly_constraints": [
            "clean separated visual regions for face, eye groups, mouth, hair, neck, torso, shoulders, and arms",
            "minimal overlap between face, hair, mouth, eyes, and body",
            "low clipping risk, simple draw order, underpaint-friendly gaps",
            "consistent anime illustration style, clean line art, clean color separation",
        ],
    }
    negative_prompt = [
        "side view",
        "extreme pose",
        "crossed arms",
        "complex hands",
        "weapon",
        "large props",
        "microphone covering mouth",
        "face-covering bangs",
        "eyes covered",
        "mouth covered",
        "messy hair overlap",
        "transparent effects",
        "heavy glow",
        "motion blur",
        "multiple characters",
        "cropped head",
        "cropped shoulders",
        "text",
        "labels",
        "UI",
        "watermark",
        "logo",
        "part diagram",
        "exploded layer sheet",
    ]
    prompt_text = "\n".join(
        [
            "Live2D Cubism v2_standard VTuber character, front-facing upper-body, centered neutral pose.",
            "A single clean master PNG for later PSD part separation and Cubism rigging.",
            "Clear face base, both eyes fully visible, separated left and right eye groups, readable eyebrows, clear mouth not covered by anything.",
            "Layer-friendly hair: separate front bangs, left side hair, right side hair, and back hair, clean strand groups for hair physics.",
            "Visible neck, simple upper body, clear shoulders, simple upper arms, no complex hands, no large props.",
            "Clean silhouette, minimal overlap, low clipping risk, underpaint-friendly design, simple draw order.",
            "Consistent polished anime illustration style, clean line art, clean color separation.",
        ]
    )
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "template_id": "cubism_v2_character_prompt_template",
        "status": "PASS",
        "inputs": {
            "production_spec": rel(input_paths["production_spec"]),
            "part_spec": rel(input_paths["part_spec"]),
            "pre_generation_readiness": rel(input_paths["pre_generation_readiness"]),
        },
        "target": {
            "tier": "v2_standard",
            "source_image_mode": "single_master_png_first",
            "part_count": parts["total_part_count"],
            "purpose": "Generate one Cubism-friendly master character image before part splitting, PSD material pack, and real Cubism authoring.",
        },
        "evidence_links": {
            "part_taxonomy": parts,
            "required_parameters": required_parameters,
            "required_deformer_hierarchy_nodes": hierarchy_nodes,
            "physics_target": physics.get("v2_standard_target_group_count"),
            "gates": gates,
        },
        "positive_prompt_sections": positive_sections,
        "positive_prompt_compact": prompt_text,
        "negative_prompt": negative_prompt,
        "generation_variants": [
            {
                "id": "v2_standard_safe_default",
                "label_ko": "표준 안전형",
                "use_when": "첫 캐릭터 컨셉 후보 3-6개를 만들 때",
                "positive_prompt": prompt_text,
                "negative_prompt": ", ".join(negative_prompt),
            },
            {
                "id": "v2_standard_extra_clean_split",
                "label_ko": "파츠 분리 우선형",
                "use_when": "머리카락/눈/입 분리가 실패했을 때",
                "positive_prompt": prompt_text
                + "\nExtra clean separation between bangs, side hair, eyes, mouth, neck, shoulders, and torso. Fewer accessories, simpler clothing.",
                "negative_prompt": ", ".join(negative_prompt + ["busy costume", "tiny accessories", "dense ornaments"]),
            },
        ],
        "operator_checklist_ko": [
            "단일 PNG 1장을 먼저 만든다. 64개 파츠를 한 번에 그리라고 시키지 않는다.",
            "G0에서 정면 상반신, 눈/입/머리/몸 경계가 보이는지 본다.",
            "G1에서 64파트 taxonomy로 나눌 수 없는 디자인이면 이미지를 버리거나 재생성한다.",
            "G2/G3는 이미지가 아니라 이후 Cubism 구조/움직임 검증이다.",
            "공식 샘플의 구조 패턴만 참고하고, 그림/텍스처/캐릭터 디자인은 복사하지 않는다.",
        ],
    }


def write_md(path: Path, template: dict[str, Any]) -> None:
    sections = template["positive_prompt_sections"]
    lines = [
        "# Cubism v2 Character Prompt Template",
        "",
        "## 목적",
        "",
        "이 템플릿은 예쁜 단일 PNG를 바로 production으로 쓰기 위한 것이 아니라, 64파트 taxonomy, deformer hierarchy, physics blueprint를 만족하기 쉬운 Cubism-friendly master image를 만들기 위한 생성 기준이다.",
        "",
        "## 입력 근거",
        "",
        f"- production spec: `{template['inputs']['production_spec']}`",
        f"- 64파트 spec: `{template['inputs']['part_spec']}`",
        f"- G0-G3 readiness: `{template['inputs']['pre_generation_readiness']}`",
        "",
        "## 목표",
        "",
        f"- tier: `{template['target']['tier']}`",
        f"- source image mode: `{template['target']['source_image_mode']}`",
        f"- target part count: `{template['target']['part_count']}`",
        f"- physics target: `{template['evidence_links']['physics_target']}`",
        "",
        "## Compact Positive Prompt",
        "",
        "```text",
        template["positive_prompt_compact"],
        "```",
        "",
        "## Negative Prompt",
        "",
        "```text",
        ", ".join(template["negative_prompt"]),
        "```",
        "",
        "## Positive Prompt Sections",
        "",
    ]
    for name, items in sections.items():
        lines += [f"### {name}", ""]
        lines.extend(f"- {item}" for item in items)
        lines.append("")
    lines += [
        "## 64파트 연결 요약",
        "",
        f"- total parts: `{template['evidence_links']['part_taxonomy']['total_part_count']}`",
        "",
        "| Group | Count |",
        "|---|---:|",
    ]
    for group, count in template["evidence_links"]["part_taxonomy"]["group_counts"].items():
        lines.append(f"| `{group}` | {count} |")
    lines += [
        "",
        "## 필수 Deformer/Parameter 힌트",
        "",
        "이미지 생성 프롬프트가 직접 deformer를 만들지는 않는다. 대신 아래 구조가 가능하도록 눈/입/머리/몸 경계를 명확히 만든다.",
        "",
        "- required parameters: `" + "`, `".join(template["evidence_links"]["required_parameters"][:20]) + "`",
        "- required hierarchy nodes: `" + "`, `".join(template["evidence_links"]["required_deformer_hierarchy_nodes"][:20]) + "`",
        "",
        "## G0-G3 연결",
        "",
        "| Gate | 쉬운 이름 | 프롬프트에서의 역할 |",
        "|---|---|---|",
    ]
    for gate in template["evidence_links"]["gates"]:
        lines.append(f"| `{gate['gate']}` | {gate['label_ko']} | {gate['prompt_relevance']} |")
    lines += [
        "",
        "## 생성 Variant",
        "",
    ]
    for variant in template["generation_variants"]:
        lines += [
            f"### {variant['label_ko']}",
            "",
            f"- id: `{variant['id']}`",
            f"- use_when: {variant['use_when']}",
            "",
            "```text",
            variant["positive_prompt"],
            "```",
            "",
        ]
    lines += [
        "## 주인님 체크리스트",
        "",
    ]
    lines.extend(f"- {item}" for item in template["operator_checklist_ko"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    production = load_json(args.production_spec)
    part_spec = load_json(args.part_spec)
    readiness = load_json(args.readiness)
    template = build_template(
        production,
        part_spec,
        readiness,
        {
            "production_spec": args.production_spec,
            "part_spec": args.part_spec,
            "pre_generation_readiness": args.readiness,
        },
    )
    out_json = args.out_dir / "cubism_v2_character_prompt_template.json"
    out_md = args.out_dir / "cubism_v2_character_prompt_template.md"
    write_json(out_json, template)
    write_md(out_md, template)
    print(
        json.dumps(
            {
                "status": template["status"],
                "json": rel(out_json),
                "markdown": rel(out_md),
                "part_count": template["target"]["part_count"],
                "variant_count": len(template["generation_variants"]),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

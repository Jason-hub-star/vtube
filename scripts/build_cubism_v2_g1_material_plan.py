#!/usr/bin/env python3
"""Build the Cubism v2 G1 material planning packet.

This packet turns the G1 taxonomy feasibility result into an actionable
PSD/material-pack production plan for the selected new character candidate.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path("/Users/family/jason/Vtube")
EXPERIMENT = ROOT / "experiments/cubism-v2-new-character-001"
REPORTS = EXPERIMENT / "reports"
G1_REVIEW = REPORTS / "g1_part_taxonomy_review.json"
PART_SPEC = (
    ROOT
    / "experiments/reference-model-structure-001/reports"
    / "cubism_v2_new_model_v2_standard_part_spec.json"
)
OUT_JSON = REPORTS / "g1_material_planning_packet.json"
OUT_MD = REPORTS / "g1_material_planning_packet.md"


FEASIBILITY_LABELS_KO = {
    "DIRECT_VISIBLE": "원본에서 바로 뽑기",
    "DIRECT_VISIBLE_RISK": "원본에서 뽑되 정리 필요",
    "DERIVED_KEYPOSE_REQUIRED": "보조 생성 필요",
    "UNDERPAINT_REQUIRED": "밑색 필요",
    "SIMPLIFY_OR_MERGE": "병합/단순화",
}

DRAW_ORDER_BAND_ORDER = [
    "body_back",
    "hair_back",
    "body_mid",
    "body_front",
    "clothing_mid",
    "face_back",
    "face_mid",
    "face_front",
    "eye_back",
    "eye_mid",
    "eye_front",
    "brow_front",
    "mouth_back",
    "mouth_mid",
    "mouth_front",
    "hair_side",
    "hair_front",
    "clothing_front",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def enrich_rows(rows: list[dict[str, Any]], part_spec_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {row["id"]: row for row in part_spec_rows}
    enriched = []
    for row in rows:
        spec = by_id.get(row["part_id"], {})
        enriched.append(
            {
                **row,
                "draw_order_band": spec.get("draw_order_band", "unknown"),
                "physics_groups": spec.get("physics_groups", []),
                "purpose_ko": spec.get("purpose_ko", ""),
                "qa_tags": spec.get("qa_tags", []),
            }
        )
    return enriched


def rows_by_feasibility(rows: list[dict[str, Any]], feasibility: str) -> list[dict[str, Any]]:
    return [row for row in rows if row["feasibility"] == feasibility]


def compact_part(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "index": row["index"],
        "part_id": row["part_id"],
        "group": row["group"],
        "label_ko": row["label_ko"],
        "feasibility": row["feasibility"],
        "feasibility_label_ko": FEASIBILITY_LABELS_KO[row["feasibility"]],
        "draw_order_band": row["draw_order_band"],
        "deformer_node": row["deformer_node"],
        "parameters": row["parameters"],
        "physics_groups": row["physics_groups"],
        "risk_tags": row["risk_tags"],
        "note_ko": row["note_ko"],
    }


def make_action(row: dict[str, Any]) -> str:
    part_id = row["part_id"]
    feasibility = row["feasibility"]
    if feasibility == "DIRECT_VISIBLE":
        return "candidate_002 원본 PNG에서 alpha layer로 직접 분리한다."
    if feasibility == "DIRECT_VISIBLE_RISK":
        return "원본에서 분리하되 bbox/alpha/경계 정리 후 G1 contact sheet에서 재검수한다."
    if feasibility == "DERIVED_KEYPOSE_REQUIRED":
        if "closed_lid" in part_id:
            return "눈 ROI 스타일을 유지해 감은 눈 keypose 파츠로 보조 생성한다."
        if part_id in {"mouth_inner", "mouth_teeth", "mouth_tongue"}:
            return "입 ROI 기반으로 열린 입 내부 keypose 세트를 스타일 맞춰 보조 생성한다."
        return "입 열림용 마스크/입술 변형 보조 파츠로 생성한다."
    if feasibility == "UNDERPAINT_REQUIRED":
        return "움직임에서 빈틈이 보이지 않게 원본 주변색 확장, inpaint, 수동 채색으로 만든다."
    if feasibility == "SIMPLIFY_OR_MERGE":
        return "처음 PSD에서는 독립 파츠보다 기본 의상 레이어에 병합하고 metadata로만 추적한다."
    raise ValueError(feasibility)


def make_table_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**compact_part(row), "material_action_ko": make_action(row)} for row in rows]


def make_draw_order_plan(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    band_to_rows: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        band_to_rows.setdefault(row["draw_order_band"], []).append(row)

    ordered_bands = [band for band in DRAW_ORDER_BAND_ORDER if band in band_to_rows]
    ordered_bands.extend(sorted(set(band_to_rows) - set(ordered_bands)))
    return [
        {
            "draw_order_band": band,
            "part_ids": [row["part_id"] for row in sorted(band_to_rows[band], key=lambda r: r["index"])],
        }
        for band in ordered_bands
    ]


def make_phase(name: str, goal: str, rows: list[dict[str, Any]], exit_check: str) -> dict[str, Any]:
    return {
        "phase": name,
        "goal_ko": goal,
        "part_ids": [row["part_id"] for row in rows],
        "exit_check_ko": exit_check,
    }


def md_table(rows: list[dict[str, Any]], include_action: bool = True) -> str:
    if not rows:
        return "_없음_\n"
    headers = ["#", "part_id", "그룹", "한글명", "draw order", "주의 태그"]
    if include_action:
        headers.append("제작 액션")
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        values = [
            str(row["index"]),
            row["part_id"],
            row["group"],
            row["label_ko"],
            row["draw_order_band"],
            ", ".join(row["risk_tags"]) or "-",
        ]
        if include_action:
            values.append(row["material_action_ko"])
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def build_markdown(packet: dict[str, Any]) -> str:
    summary = packet["summary"]
    sections = packet["sections"]
    lines = [
        "# Cubism v2 G1 Material Planning Packet",
        "",
        f"- status: `{packet['status']}`",
        f"- source candidate: `{packet['source_candidate']}`",
        f"- taxonomy parts accounted: `{summary['taxonomy_parts_accounted']}`",
        f"- direct extraction total: `{summary['direct_extraction_total']}`",
        f"- auxiliary generated total: `{summary['auxiliary_generated_total']}`",
        f"- underpaint total: `{summary['underpaint_total']}`",
        f"- simplify/merge total: `{summary['simplify_or_merge_total']}`",
        f"- initial PSD layer target: `{summary['initial_psd_layer_target_ko']}`",
        "",
        "## 결정 요약",
        "",
        "- 원본에서 보이는 파츠는 46개다. 그중 30개는 바로 분리하고, 16개는 alpha/bbox/경계 정리 후 통과시킨다.",
        "- 단일 PNG에서 보이지 않는 감은 눈, 열린 입 내부, 치아, 혀, 입술 마스크는 보조 생성한다.",
        "- 몸/목/팔/얼굴/눈/뒷머리 밑색은 움직임 빈틈 방지용 underpaint로 만든다.",
        "- 의상 그림자 2개는 처음부터 독립 리깅 파츠로 무리하지 않고 기본 의상 레이어에 병합한다.",
        "",
        "## 1. 원본에서 직접 뽑을 파츠",
        "",
        "### 1A. 바로 분리",
        "",
        md_table(sections["direct_extraction_parts"]["safe"]),
        "### 1B. 분리하되 정리 필요",
        "",
        md_table(sections["direct_extraction_parts"]["risk"]),
        "## 2. 보조 생성할 파츠",
        "",
        md_table(sections["auxiliary_generated_parts"]),
        "## 3. Underpaint 필요한 파츠",
        "",
        md_table(sections["underpaint_parts"]),
        "## 4. 병합/단순화할 의상 디테일",
        "",
        md_table(sections["simplify_or_merge_parts"]),
        "## 5. PSD / Material Pack 제작 순서",
        "",
    ]
    for phase in packet["psd_material_pack_order"]:
        lines.extend(
            [
                f"### {phase['phase']}",
                "",
                f"- 목표: {phase['goal_ko']}",
                f"- 대상: `{', '.join(phase['part_ids']) if phase['part_ids'] else 'none'}`",
                f"- 통과 확인: {phase['exit_check_ko']}",
                "",
            ]
        )

    lines.extend(["## 6. Draw Order Band", ""])
    for band in packet["draw_order_plan"]:
        lines.append(f"- `{band['draw_order_band']}`: {', '.join(band['part_ids'])}")

    lines.extend(
        [
            "",
            "## Self Review",
            "",
            md_table_self_review(packet["self_review"]),
            "",
            "## 다음 단계",
            "",
            "이 패킷이 통과했으므로 다음 작업은 실제 material asset 생성이다. 먼저 direct visible 파츠부터 full-canvas alpha layer로 만들고, 그 다음 derived keypose와 underpaint를 만든다.",
            "",
        ]
    )
    return "\n".join(lines)


def md_table_self_review(items: list[dict[str, Any]]) -> str:
    lines = ["| 항목 | 결과 | 근거 |", "|---|---:|---|"]
    for item in items:
        result = "PASS" if item["passed"] else "FAIL"
        lines.append(f"| {item['item_ko']} | {result} | {item['evidence_ko']} |")
    return "\n".join(lines)


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    g1 = load_json(G1_REVIEW)
    spec = load_json(PART_SPEC)
    rows = enrich_rows(g1["rows"], spec["parts"])

    direct_safe = rows_by_feasibility(rows, "DIRECT_VISIBLE")
    direct_risk = rows_by_feasibility(rows, "DIRECT_VISIBLE_RISK")
    auxiliary = rows_by_feasibility(rows, "DERIVED_KEYPOSE_REQUIRED")
    underpaint = rows_by_feasibility(rows, "UNDERPAINT_REQUIRED")
    simplify = rows_by_feasibility(rows, "SIMPLIFY_OR_MERGE")
    direct_all = direct_safe + direct_risk

    all_accounted = len(direct_all) + len(auxiliary) + len(underpaint) + len(simplify) == 64
    expected_counts = {
        "direct_safe": 30,
        "direct_risk": 16,
        "direct_total": 46,
        "auxiliary": 7,
        "underpaint": 9,
        "simplify": 2,
    }

    self_review = [
        {
            "item_ko": "원본에서 직접 뽑을 파츠 목록 확정",
            "passed": len(direct_all) == expected_counts["direct_total"],
            "evidence_ko": f"직접/위험 직접 {len(direct_all)}개 = 안전 {len(direct_safe)}개 + 정리 필요 {len(direct_risk)}개",
        },
        {
            "item_ko": "보조 생성할 파츠 목록 확정",
            "passed": len(auxiliary) == expected_counts["auxiliary"],
            "evidence_ko": f"감은 눈/입 내부 keypose {len(auxiliary)}개",
        },
        {
            "item_ko": "underpaint 필요한 파츠 목록 확정",
            "passed": len(underpaint) == expected_counts["underpaint"],
            "evidence_ko": f"몸/목/팔/얼굴/눈/뒷머리 밑색 {len(underpaint)}개",
        },
        {
            "item_ko": "병합/단순화할 의상 디테일 확정",
            "passed": len(simplify) == expected_counts["simplify"],
            "evidence_ko": f"의상 그림자/작은 디테일 {len(simplify)}개",
        },
        {
            "item_ko": "이후 PSD/material pack 제작 순서 확정",
            "passed": True,
            "evidence_ko": "10단계 제작 순서와 draw order band를 생성함",
        },
        {
            "item_ko": "64파트 taxonomy 전체 accounted",
            "passed": all_accounted,
            "evidence_ko": f"{len(direct_all)} + {len(auxiliary)} + {len(underpaint)} + {len(simplify)} = {len(rows)}",
        },
    ]
    status = "PASS_MATERIAL_PLAN_READY" if all(item["passed"] for item in self_review) else "FAIL_REVIEW_REQUIRED"

    packet = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gate": "G1_PART_TAXONOMY_TO_MATERIAL_PLAN",
        "status": status,
        "source_candidate": str(EXPERIMENT / "concepts/g0_adult_cute_female_candidate_002.png"),
        "inputs": {
            "g1_taxonomy_review": str(G1_REVIEW),
            "part_spec": str(PART_SPEC),
        },
        "summary": {
            "taxonomy_parts_accounted": len(rows),
            "direct_extraction_safe": len(direct_safe),
            "direct_extraction_risk": len(direct_risk),
            "direct_extraction_total": len(direct_all),
            "auxiliary_generated_total": len(auxiliary),
            "underpaint_total": len(underpaint),
            "simplify_or_merge_total": len(simplify),
            "initial_psd_layer_target_ko": "62개 독립 레이어 + 2개 병합/metadata 추적. 필요하면 shadow 2개를 별도 레이어로 되돌려 64개까지 확장.",
            "cubism_taxonomy_target_parts": 64,
        },
        "sections": {
            "direct_extraction_parts": {
                "safe": make_table_rows(direct_safe),
                "risk": make_table_rows(direct_risk),
            },
            "auxiliary_generated_parts": make_table_rows(auxiliary),
            "underpaint_parts": make_table_rows(underpaint),
            "simplify_or_merge_parts": make_table_rows(simplify),
        },
        "psd_material_pack_order": [
            make_phase(
                "P0_source_normalization",
                "candidate_002를 2048 full-canvas master로 고정하고 해시/크기/파일명을 기록한다.",
                [],
                "원본 PNG, bbox guide, G1 report 경로가 manifest에 연결되어야 한다.",
            ),
            make_phase(
                "P1_roi_bbox_lock",
                "눈/입/얼굴/머리/몸 ROI와 guide box를 잠근다.",
                direct_all,
                "mouth corrected ROI를 포함해 주요 그룹 bbox가 비어 있지 않아야 한다.",
            ),
            make_phase(
                "P2_direct_visible_extraction",
                "원본에서 보이는 안전 파츠를 full-canvas alpha layer로 분리한다.",
                direct_safe,
                "각 파츠 alpha bbox가 있고 canvas 크기가 2048x2048이어야 한다.",
            ),
            make_phase(
                "P3_direct_risk_cleanup",
                "얇은 선, 머리끝, 팔, 볼/그림자처럼 리스크가 있는 직접 파츠를 정리한다.",
                direct_risk,
                "bad_alpha, crop, style_mismatch, misaligned 후보가 review packet에 표시되어야 한다.",
            ),
            make_phase(
                "P4_derived_keypose_generation",
                "감은 눈과 열린 입 내부 keypose 파츠를 보조 생성한다.",
                auxiliary,
                "neutral vs derived 비교에서 위치가 맞고 입/눈 안쪽이 비어 있지 않아야 한다.",
            ),
            make_phase(
                "P5_underpaint_generation",
                "움직일 때 구멍이 보이지 않도록 몸/얼굴/눈/머리 밑색을 만든다.",
                underpaint,
                "layer alone vs composited 비교에서 underpaint가 밖으로 과하게 삐져나오지 않아야 한다.",
            ),
            make_phase(
                "P6_clothing_simplify_merge",
                "작은 의상 그림자는 기본 의상 레이어에 병합하고 별도 리깅 대상에서 제외한다.",
                simplify,
                "병합한 디테일은 metadata에 남고 독립 deformer/keyform 요구사항으로 올라가지 않아야 한다.",
            ),
            make_phase(
                "P7_full_canvas_layer_normalization",
                "모든 결과를 full-canvas PNG/PSD layer 규격으로 맞춘다.",
                rows,
                "레이어 이름, alpha bbox, draw order band, source type이 manifest에 있어야 한다.",
            ),
            make_phase(
                "P8_psd_layer_order_and_material_pack",
                "draw order band에 맞춰 PSD/material pack을 만든다.",
                rows,
                "Cubism import smoke 전에 PSD layer count와 이름이 spec과 맞아야 한다.",
            ),
            make_phase(
                "P9_g1_exit_review_packet",
                "사람은 contact sheet 1장, 실패 후보, derived/underpaint 비교만 본다.",
                rows,
                "G1 material QA가 PASS해야 Cubism Editor authoring으로 넘어간다.",
            ),
        ],
        "draw_order_plan": make_draw_order_plan(rows),
        "self_review": self_review,
        "next_gate": "G1_MATERIAL_ASSET_GENERATION_THEN_CUBISM_IMPORT_SMOKE",
    }

    OUT_JSON.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(build_markdown(packet), encoding="utf-8")
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    print(status)


if __name__ == "__main__":
    main()

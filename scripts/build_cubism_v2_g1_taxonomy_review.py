#!/usr/bin/env python3
"""Build G1 part-taxonomy feasibility evidence for the selected Cubism v2 character."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "cubism-v2-new-character-001"
DEFAULT_IMAGE = EXPERIMENT / "concepts" / "g0_adult_cute_female_candidate_002.png"
DEFAULT_PART_SPEC = ROOT / "experiments" / "reference-model-structure-001" / "reports" / "cubism_v2_new_model_v2_standard_part_spec.json"
DEFAULT_OUT_DIR = EXPERIMENT / "reports"


DIRECT_VISIBLE = "DIRECT_VISIBLE"
DIRECT_VISIBLE_RISK = "DIRECT_VISIBLE_RISK"
DERIVED_KEYPOSE_REQUIRED = "DERIVED_KEYPOSE_REQUIRED"
UNDERPAINT_REQUIRED = "UNDERPAINT_REQUIRED"
SIMPLIFY_OR_MERGE = "SIMPLIFY_OR_MERGE"


GROUP_BANDS = {
    "face_base": {"x": 330, "y": 260, "w": 430, "h": 420, "label": "face / cheeks / nose"},
    "eye_L": {"x": 340, "y": 370, "w": 170, "h": 110, "label": "left eye group"},
    "eye_R": {"x": 590, "y": 370, "w": 170, "h": 110, "label": "right eye group"},
    "mouth": {"x": 430, "y": 520, "w": 240, "h": 95, "label": "mouth group"},
    "hair_front": {"x": 300, "y": 70, "w": 520, "h": 420, "label": "front bangs"},
    "hair_side_L": {"x": 190, "y": 260, "w": 230, "h": 690, "label": "side hair L"},
    "hair_side_R": {"x": 670, "y": 260, "w": 230, "h": 690, "label": "side hair R"},
    "hair_back": {"x": 240, "y": 80, "w": 620, "h": 820, "label": "back hair base"},
    "body": {"x": 210, "y": 720, "w": 690, "h": 650, "label": "neck / shoulders / torso"},
    "clothing": {"x": 260, "y": 850, "w": 600, "h": 500, "label": "clothing blocks"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--part-spec", type=Path, default=DEFAULT_PART_SPEC)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def load_json(path: Path) -> Any:
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


def classify_part(part: dict[str, Any]) -> tuple[str, list[str], str]:
    part_id = part["id"]
    group = part.get("group")
    risks: list[str] = []

    if "underpaint" in part_id:
        return UNDERPAINT_REQUIRED, ["underpaint_missing"], "움직임에서 빈틈을 막기 위해 원본 기반 확장/수동 밑색이 필요함"
    if part_id in {"eye_L_closed_lid", "eye_R_closed_lid"}:
        return DERIVED_KEYPOSE_REQUIRED, ["clipping_risk"], "정면 open-eye PNG에는 감은 눈꺼풀이 없으므로 blink keypose 생성 필요"
    if part_id in {"mouth_inner", "mouth_teeth", "mouth_tongue", "mouth_upper_lip_mask", "mouth_lower_lip_mask"}:
        return DERIVED_KEYPOSE_REQUIRED, ["bad_alpha", "clipping_risk"], "현재 미소 입에서는 내부/치아/혀가 충분히 보이지 않아 mouth open keypose 생성 필요"
    if part_id in {"mouth_corner_L", "mouth_corner_R", "mouth_line"}:
        return DIRECT_VISIBLE_RISK, ["misaligned"], "입 선은 보이나 작아 G1 crop과 G3 mouth form에서 위치 보정 필요"
    if part_id in {"brow_L", "brow_R"}:
        return DIRECT_VISIBLE_RISK, ["clipping_risk"], "눈썹은 보이지만 앞머리와 가까워 draw order와 alpha 분리가 필요"
    if group in {"eye_L", "eye_R"}:
        return DIRECT_VISIBLE, [], "눈 흰자/홍채/동공/하이라이트/속눈썹이 비교적 명확함"
    if group == "face_base":
        if part_id in {"face_shadow_L", "face_shadow_R", "cheek_L", "cheek_R"}:
            return DIRECT_VISIBLE_RISK, [], "얼굴/볼 shading은 보이나 별도 파츠로 과분리하면 스타일 mismatch 위험"
        return DIRECT_VISIBLE, [], "얼굴 기본형은 분리 가능"
    if group == "hair":
        if part_id in {"hair_back_strand_L", "hair_back_strand_R", "hair_back_center"}:
            return DIRECT_VISIBLE_RISK, ["draw_order_issue"], "뒷머리는 보이지만 옆머리/앞머리 뒤에 있어 underpaint와 draw order 확인 필요"
        if part_id in {"hair_front_tip_L", "hair_front_tip_R"}:
            return DIRECT_VISIBLE_RISK, ["overhang_issue"], "끝단은 보이나 어깨와 겹쳐 crop/alpha 리스크 있음"
        return DIRECT_VISIBLE, [], "앞머리/옆머리/뒷머리 그룹 경계가 비교적 명확함"
    if group == "body":
        if part_id in {"arm_L_upper_simple", "arm_R_upper_simple"}:
            return DIRECT_VISIBLE_RISK, ["misaligned"], "팔은 보이나 가디건 소매와 torso 경계가 합쳐져 단순 팔로 유지 권장"
        return DIRECT_VISIBLE, [], "목/어깨/상체는 보이며 v2_standard 단순 몸 구조에 적합"
    if group == "clothing":
        if part_id in {"collar_shadow", "chest_cloth_shadow"}:
            return SIMPLIFY_OR_MERGE, [], "그림자 전용 파츠는 첫 production에서 base에 병합하거나 최소화 권장"
        return DIRECT_VISIBLE, [], "가디건/블라우스/리본은 보이나 v2_standard에서는 단순 의상 파츠로 제한"

    risks.append("missing_part")
    return DIRECT_VISIBLE_RISK, risks, "분류 규칙 밖 파츠이므로 수동 확인 필요"


def build_visual_guide(image_path: Path, out_path: Path) -> None:
    with Image.open(image_path) as raw:
        image = raw.convert("RGB")
    draw = ImageDraw.Draw(image, "RGBA")
    try:
        font = ImageFont.truetype("Arial.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    colors = {
        "face_base": (22, 119, 255, 80),
        "eye_L": (34, 197, 94, 95),
        "eye_R": (34, 197, 94, 95),
        "mouth": (239, 68, 68, 95),
        "hair_front": (168, 85, 247, 70),
        "hair_side_L": (168, 85, 247, 60),
        "hair_side_R": (168, 85, 247, 60),
        "hair_back": (100, 116, 139, 35),
        "body": (245, 158, 11, 55),
        "clothing": (14, 165, 233, 50),
    }
    outlines = {
        "face_base": (22, 119, 255, 230),
        "eye_L": (22, 163, 74, 230),
        "eye_R": (22, 163, 74, 230),
        "mouth": (220, 38, 38, 230),
        "hair_front": (126, 34, 206, 230),
        "hair_side_L": (126, 34, 206, 230),
        "hair_side_R": (126, 34, 206, 230),
        "hair_back": (71, 85, 105, 190),
        "body": (217, 119, 6, 230),
        "clothing": (2, 132, 199, 230),
    }
    for key, band in GROUP_BANDS.items():
        x, y, w, h = band["x"], band["y"], band["w"], band["h"]
        draw.rectangle((x, y, x + w, y + h), fill=colors[key], outline=outlines[key], width=4)
        label_y = y - 34 if key in {"mouth", "eye_L", "eye_R"} and y >= 34 else y
        draw.rectangle((x, label_y, x + w, label_y + 30), fill=(255, 255, 255, 210))
        draw.text((x + 8, label_y + 5), band["label"], fill=(15, 23, 42), font=font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)


def build_report(image_path: Path, part_spec: dict[str, Any], guide_path: Path) -> dict[str, Any]:
    parts = part_spec.get("parts", [])
    rows = []
    for index, part in enumerate(parts, 1):
        status, risks, note = classify_part(part)
        rows.append(
            {
                "index": index,
                "part_id": part["id"],
                "group": part.get("group"),
                "label_ko": part.get("label_ko"),
                "feasibility": status,
                "risk_tags": sorted(set(risks + (part.get("qa_tags") or []))),
                "deformer_node": part.get("deformer_node"),
                "parameters": part.get("parameters") or [],
                "note_ko": note,
            }
        )

    counts = Counter(row["feasibility"] for row in rows)
    by_group: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        by_group[row["group"]][row["feasibility"]] += 1
    blockers = [
        row for row in rows if row["feasibility"] in {DERIVED_KEYPOSE_REQUIRED, UNDERPAINT_REQUIRED, SIMPLIFY_OR_MERGE}
    ]
    pass_condition = counts[DIRECT_VISIBLE] + counts[DIRECT_VISIBLE_RISK] >= 44 and counts[SIMPLIFY_OR_MERGE] <= 4
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gate": "G1_PART_TAXONOMY",
        "status": "PASS_WITH_DERIVED_PART_REQUIREMENTS" if pass_condition else "FAIL_REGENERATE_OR_REDESIGN",
        "image": rel(image_path),
        "visual_guide": rel(guide_path),
        "visual_guide_group_bands": GROUP_BANDS,
        "part_spec": rel(DEFAULT_PART_SPEC),
        "summary": {
            "total_parts": len(rows),
            "feasibility_counts": dict(counts),
            "group_counts": {group: dict(counter) for group, counter in sorted(by_group.items())},
            "direct_or_risk_visible": counts[DIRECT_VISIBLE] + counts[DIRECT_VISIBLE_RISK],
            "requires_derived_or_underpaint": counts[DERIVED_KEYPOSE_REQUIRED] + counts[UNDERPAINT_REQUIRED],
            "simplify_or_merge": counts[SIMPLIFY_OR_MERGE],
        },
        "decision": {
            "candidate": "candidate_002",
            "g1_decision": "KEEP_FOR_MATERIAL_PLANNING" if pass_condition else "REGENERATE",
            "next_step": "Build G1 review packet/contact sheet plan and generate/derive missing keypose/underpaint parts before PSD material pack.",
        },
        "production_notes_ko": [
            "단일 PNG에서 보이지 않는 mouth inner/teeth/tongue/closed lid/underpaint는 실패가 아니라 보조 생성 대상이다.",
            "첫 v2_standard에서는 의상 그림자와 작은 디테일을 과분리하지 말고 base에 병합해도 된다.",
            "앞머리와 옆머리 끝단은 G3에서 draw order/overhang을 반드시 확인한다.",
        ],
        "rows": rows,
        "blockers_or_generated_requirements": blockers,
    }


def write_md(path: Path, report: dict[str, Any]) -> None:
    summary = report["summary"]
    lines = [
        "# Cubism v2 New Character G1 Part Taxonomy Review",
        "",
        f"- status: `{report['status']}`",
        f"- image: `{report['image']}`",
        f"- visual_guide: `{report['visual_guide']}`",
        f"- total_parts: `{summary['total_parts']}`",
        f"- direct_or_risk_visible: `{summary['direct_or_risk_visible']}`",
        f"- requires_derived_or_underpaint: `{summary['requires_derived_or_underpaint']}`",
        f"- simplify_or_merge: `{summary['simplify_or_merge']}`",
        f"- decision: `{report['decision']['g1_decision']}`",
        "",
        "## Feasibility Counts",
        "",
        "| Status | Count | Meaning |",
        "|---|---:|---|",
    ]
    meanings = {
        DIRECT_VISIBLE: "원본에서 직접 분리 가능",
        DIRECT_VISIBLE_RISK: "직접 분리 가능하지만 alpha/draw-order/정렬 주의",
        DERIVED_KEYPOSE_REQUIRED: "감은 눈/입 안쪽처럼 보조 keypose 생성 필요",
        UNDERPAINT_REQUIRED: "움직임 빈틈 방지용 밑색 필요",
        SIMPLIFY_OR_MERGE: "첫 production에서는 병합/단순화 권장",
    }
    for key, count in sorted(summary["feasibility_counts"].items()):
        lines.append(f"| `{key}` | {count} | {meanings.get(key, '')} |")
    lines += [
        "",
        "## Group Summary",
        "",
        "| Group | Counts |",
        "|---|---|",
    ]
    for group, counts in summary["group_counts"].items():
        pretty = ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
        lines.append(f"| `{group}` | {pretty} |")
    lines += [
        "",
        "## Production Notes",
        "",
    ]
    for note in report["production_notes_ko"]:
        lines.append(f"- {note}")
    lines += [
        "",
        "## Part Rows",
        "",
        "| # | Part | Group | Feasibility | Risks | Note |",
        "|---:|---|---|---|---|---|",
    ]
    for row in report["rows"]:
        risks = ", ".join(row["risk_tags"]) if row["risk_tags"] else "-"
        lines.append(
            f"| {row['index']} | `{row['part_id']}` | `{row['group']}` | `{row['feasibility']}` | {risks} | {row['note_ko']} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    part_spec = load_json(args.part_spec)
    guide_path = args.out_dir / "g1_part_taxonomy_visual_guide.png"
    build_visual_guide(args.image, guide_path)
    report = build_report(args.image, part_spec, guide_path)
    out_json = args.out_dir / "g1_part_taxonomy_review.json"
    out_md = args.out_dir / "g1_part_taxonomy_review.md"
    write_json(out_json, report)
    write_md(out_md, report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "summary": report["summary"],
                "json": rel(out_json),
                "markdown": rel(out_md),
                "visual_guide": rel(guide_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if report["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())

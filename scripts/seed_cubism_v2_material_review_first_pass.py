#!/usr/bin/env python3
"""Seed a conservative Codex first-pass review for Cubism v2 material assets."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from run_cubism_v2_material_review_server import REVIEW_PATH, load_review_doc, save_json, summarize


ROOT = Path("/Users/family/jason/Vtube")
MANIFEST = ROOT / "experiments/cubism-v2-new-character-001/material_pack_v0/material_asset_manifest.json"

KEEP_PARTS = {
    "hair_front_center",
    "hair_front_L",
    "hair_front_R",
    "hair_front_side_L",
    "hair_front_side_R",
    "hair_side_L_outer",
    "hair_side_L_inner",
    "hair_side_R_outer",
    "hair_side_R_inner",
}

REGENERATED_DETAIL_PARTS = {
    "eye_L_closed_lid",
    "eye_R_closed_lid",
    "eye_L_highlight",
    "eye_R_highlight",
    "mouth_inner",
    "mouth_upper_lip_mask",
    "mouth_lower_lip_mask",
    "mouth_teeth",
    "mouth_tongue",
    "mouth_line",
    "mouth_corner_L",
    "mouth_corner_R",
}

MERGE_PARTS = {"collar_shadow", "chest_cloth_shadow"}

TAG_MAP = {
    "bad_alpha": "bad_alpha",
    "misaligned": "misaligned",
    "clipping_risk": "clipping_risk",
    "draw_order_issue": "draw_order_issue",
    "overhang_issue": "overhang_issue",
    "underpaint_missing": "underpaint_missing",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def issue_tags(entry: dict) -> list[str]:
    tags = {TAG_MAP[tag] for tag in entry.get("risk_tags", []) if tag in TAG_MAP}
    part_id = entry["part_id"]
    feasibility = entry["feasibility"]
    group = entry["group"]
    if feasibility == "UNDERPAINT_REQUIRED":
        tags.update({"underpaint_missing", "too_coarse"})
    if feasibility == "DERIVED_KEYPOSE_REQUIRED":
        tags.update({"style_mismatch"})
    if feasibility == "DIRECT_VISIBLE_RISK":
        tags.add("too_coarse")
    if group in {"eye_L", "eye_R", "mouth", "brow"} and part_id not in KEEP_PARTS:
        tags.add("misaligned")
    if part_id in {"eye_L_highlight", "eye_R_highlight"}:
        tags.add("too_tiny")
    if part_id in {"torso_base", "neck", "shoulder_L", "shoulder_R", "face_base", "nose", "collar_front", "chest_cloth_base"}:
        tags.add("too_coarse")
    if part_id.startswith("hair_front_tip"):
        tags.update({"overhang_issue", "too_tiny"})
    return sorted(tags)


def verdict_for(entry: dict) -> str:
    part_id = entry["part_id"]
    if part_id in MERGE_PARTS:
        return "MERGE"
    if part_id in KEEP_PARTS:
        return "KEEP"
    return "REVISE"


def note_for(entry: dict, verdict: str) -> str:
    part_id = entry["part_id"]
    if verdict == "KEEP":
        return "Codex first-pass: 큰 머리카락 파츠로는 현재 초안 사용 가능. 실제 움직임 전 draw order만 다시 확인."
    if verdict == "MERGE":
        return f"Codex first-pass: {entry.get('merged_into')}에 병합하는 현재 정책 유지."
    if part_id in REGENERATED_DETAIL_PARTS:
        return "Codex post-fix pass: 재생성 로직을 적용했으므로 이제 위치, 스타일, 크기를 확인하고 필요하면 수동 미세수정."
    if entry["feasibility"] == "UNDERPAINT_REQUIRED":
        return "Codex first-pass: 밑색 역할은 맞지만 현재는 단순 블록/타원이라 실제 움직임에서 튀어나오지 않게 다듬기 필요."
    if part_id in {"torso_base", "neck", "shoulder_L", "shoulder_R", "face_base", "nose", "collar_front", "chest_cloth_base"}:
        return "Codex first-pass: 원본에서 잘렸지만 파츠 범위가 넓거나 주변 요소가 섞여 있어 semantic mask 정리 필요."
    return "Codex first-pass: 자동 bbox/색상 마스크 초안이므로 alpha, 위치, 앞뒤 순서를 한 번 다듬는 편이 안전."


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    doc = load_review_doc()
    reviews = doc.setdefault("reviews", {})
    for entry in manifest["layers"]:
        verdict = verdict_for(entry)
        reviews[entry["part_id"]] = {
            "part_id": entry["part_id"],
            "verdict": verdict,
            "issue_tags": issue_tags(entry),
            "human_note": note_for(entry, verdict),
            "updated_at": now(),
            "reviewer": "codex_first_pass",
        }
    doc["updated_at"] = now()
    doc["review_mode"] = "codex_first_pass_conservative_seed"
    doc["notes"] = [
        "This is not the user's final visual approval.",
        "Use it as a conservative first pass to create a fix queue before Cubism import smoke.",
    ]
    save_json(REVIEW_PATH, doc)
    summary = summarize(doc)
    print(summary["status"])
    print(json.dumps(summary["verdict_counts"], ensure_ascii=False, sort_keys=True))
    print(f"fix_queue_count={summary['fix_queue_count']}")


if __name__ == "__main__":
    main()

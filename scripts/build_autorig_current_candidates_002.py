#!/usr/bin/env python3
"""AUTORIG current-candidates manifest for cubism-v2-new-character-002.

48개 시행착오 변형 폴더 중에서 64-part 각각의 "현재 후보" 1개씩만 가리키는
단일 매니페스트를 만든다. 기존 v22_64part_candidate_manifest.json을 베이스로,
B4/B5는 더 최신의 보정/미니패스 변형이 같은 파일명을 가지면 그쪽으로 오버라이드한다.
폴더는 삭제하지 않는다 (증거 보존 규칙).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/family/jason/Vtube")
EXP = ROOT / "experiments/cubism-v2-new-character-002"
BASE_MANIFEST = EXP / "reports/v22_64part_candidate_manifest/v22_64part_candidate_manifest.json"
OUT_DIR = EXP / "reports/autorig_current_candidates"

# 우선순위: 최신 변형 먼저. 같은 파일명이 있으면 위에서부터 채택.
# probe 폴더는 실험용이라 제외한다.
OVERRIDE_DIRS = [
    "v22_g4_torso_base_regen_candidate/normalized_layers",          # 06-10 10:11
    "v22_b5_p0_torso_minipass_v2_candidate/normalized_layers",       # 06-10 00:48
    "v22_b5_provisional_minipass_candidate/normalized_layers",       # 06-10 00:20
    "v22_b5_refined_mask_v2/normalized_layers",                      # 06-09 23:08
    "v22_b4_b5_anchor_corrected_auto_draft/normalized_layers",       # 06-09 22:49
]


def resolve(entry: dict) -> dict:
    base_path = ROOT / entry["path"]
    name = base_path.name
    chosen = base_path
    provenance = "base_manifest"
    alternatives: list[str] = []
    if entry["source_batch"] in ("B4", "B5"):
        for d in OVERRIDE_DIRS:
            cand = EXP / d / name
            if cand.exists():
                if provenance == "base_manifest":
                    chosen = cand
                    provenance = d.split("/")[0]
                else:
                    alternatives.append(str(cand.relative_to(ROOT)))
        if base_path.exists() and chosen != base_path:
            alternatives.append(str(base_path.relative_to(ROOT)))
    return {
        "id": entry["id"],
        "group": entry["group"],
        "label_ko": entry["label_ko"],
        "source_batch": entry["source_batch"],
        "deformer_node": entry["deformer_node"],
        "parameters": entry["parameters"],
        "draw_order_band": entry["draw_order_band"],
        "path": str(chosen.relative_to(ROOT)),
        "provenance": provenance,
        "exists": chosen.exists(),
        "superseded_alternatives": alternatives,
    }


def main() -> None:
    base = json.loads(BASE_MANIFEST.read_text())
    entries = [resolve(e) for e in base["manifest_entries"]]
    missing = [e["id"] for e in entries if not e["exists"]]
    overridden = [e["id"] for e in entries if e["provenance"] != "base_manifest"]

    sources = {
        "source_front_raw": "experiments/cubism-v2-new-character-002/material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png",
        "source_front_2048": "experiments/cubism-v2-new-character-002/reports/overlay_qa/source_front_2048.png",
        "source_front_inpaint_clean": "experiments/cubism-v2-new-character-002/reports/source_inpaint_v1/source_front_2048_inpaint_clean.png",
    }
    sources = {k: v for k, v in sources.items() if (ROOT / v).exists()}

    out = {
        "schema_version": 1,
        "manifest_id": "autorig_current_candidates_002",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_manifest": str(BASE_MANIFEST.relative_to(ROOT)),
        "purpose_ko": "AUTORIG P3 자동 리깅의 입력. 64-part 각각의 현재 후보 1개씩만 가리킨다.",
        "override_priority": OVERRIDE_DIRS,
        "sources": sources,
        "entries": entries,
        "self_review": {
            "total": len(entries),
            "missing": missing,
            "overridden_count": len(overridden),
            "overridden_ids": overridden,
            "status": "PASS" if not missing and len(entries) == 64 else "FAIL",
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_json = OUT_DIR / "current_candidates.json"
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2))

    lines = [
        "# AUTORIG Current Candidates (character-002)",
        "",
        f"Generated: {out['generated_at']}",
        f"Self-review: {out['self_review']['status']} — {len(entries)}/64, missing {len(missing)}, overridden {len(overridden)}",
        "",
        "| id | group | batch | provenance | path |",
        "|---|---|---|---|---|",
    ]
    for e in entries:
        lines.append(
            f"| {e['id']} | {e['group']} | {e['source_batch']} | {e['provenance']} | `{e['path']}` |"
        )
    (OUT_DIR / "current_candidates.md").write_text("\n".join(lines) + "\n")

    print(f"entries={len(entries)} missing={len(missing)} overridden={len(overridden)}")
    print(f"wrote {out_json}")


if __name__ == "__main__":
    main()

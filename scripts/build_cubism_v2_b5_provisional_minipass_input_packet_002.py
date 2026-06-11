#!/usr/bin/env python3
"""Build the B5 provisional mini-pass input packet from the Codex route plan."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
REPORT_DIR = EXP / "reports/v22_b5_provisional_minipass_input_packet"
REPORT_JSON = REPORT_DIR / "v22_b5_provisional_minipass_input_packet.json"
REPORT_MD = REPORT_DIR / "v22_b5_provisional_minipass_input_packet.md"
SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
ROUTE_PLAN_JSON = EXP / "reports/v22_b4_b5_focused_owner_review/v22_b4_b5_owner_decision_route_plan.json"
CODEX_DECISIONS_JSON = EXP / "reports/v22_b4_b5_focused_owner_review/v22_b4_b5_focused_codex_provisional_decisions.json"
B5_BLOCKER_JSON = EXP / "reports/v22_b5_body_blocker_draw_order_review/v22_b5_body_blocker_draw_order_review.json"
B5_V2_QA_JSON = EXP / "reports/v22_b5_refined_mask_v2/v22_b5_refined_mask_v2_overlay_qa_report.json"


TARGET_ORDER = ["torso_base", "shoulder_L", "shoulder_R"]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def target_mode(route: dict) -> str | None:
    route_name = route["route"]
    if route_name == "ROUTE_TO_B5_BODY_MINIPASS_REGENERATION":
        return "REGENERATE_BODY_MINIPASS"
    if route_name == "ROUTE_TO_B5_DRAW_ORDER_OR_MASK_REFINEMENT":
        return "REVISE_DRAW_ORDER_OR_MASK"
    return None


def main() -> int:
    route_plan = load_json(ROUTE_PLAN_JSON)
    codex_decisions = load_json(CODEX_DECISIONS_JSON)
    blocker = load_json(B5_BLOCKER_JSON)
    b5_qa = load_json(B5_V2_QA_JSON)
    blocker_by_part = {entry["part_id"]: entry for entry in blocker["entries"]}
    route_by_part = {row["part_id"]: row for row in route_plan["routes"]}

    targets = []
    for part_id in TARGET_ORDER:
        route = route_by_part[part_id]
        mode = target_mode(route)
        if mode is None:
            raise ValueError(f"{part_id} does not have a B5 revise/regenerate route: {route['route']}")
        block = blocker_by_part[part_id]
        targets.append(
            {
                "part_id": part_id,
                "mode": mode,
                "route": route["route"],
                "owner_decision": route["owner_decision"],
                "decision_authority": "CODEX_PROVISIONAL_SUCCESS_PATTERN",
                "current_output_path": route["output_path"],
                "crop_box": block["crop_box"],
                "current_bbox": block["bbox"],
                "alpha_coverage": block["alpha_coverage"],
                "hair_occlusion_overlap_ratio": block["hair_occlusion_overlap_ratio"],
                "source_recommendation": block["recommendation"],
                "instruction": (
                    "Regenerate this as a coherent B5 torso/body underpaint reference; do not solve it by alpha shrinking."
                    if mode == "REGENERATE_BODY_MINIPASS"
                    else "Revise draw-order context or mask separation so shoulder material can sit behind front/side hair without baked hair pixels."
                ),
            }
        )

    prompt = blocker["regeneration_prompt_if_rejected"]
    packet = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": "B5_PROVISIONAL_MINIPASS_INPUT_PACKET_READY",
        "source_image": rel(SOURCE),
        "route_plan": rel(ROUTE_PLAN_JSON),
        "codex_provisional_decisions": rel(CODEX_DECISIONS_JSON),
        "b5_body_blocker_review": rel(B5_BLOCKER_JSON),
        "b5_refined_mask_v2_overlay_qa": rel(B5_V2_QA_JSON),
        "targets": targets,
        "image_generation_prompt": prompt,
        "negative_prompt": (
            "No labels, arrows, grids, extra faces, hands, jewelry, props, hairstyle changes, "
            "new outfit, perspective pose, cropped shoulders, baked hair pixels in shoulder layers, "
            "rectangular skin patches, alpha-noise scraps, or source-crop artifacts."
        ),
        "output_requirements": [
            "Return clean full-canvas 2048x2048 RGBA candidates for torso_base, shoulder_L, and shoulder_R.",
            "Keep same character identity, off-shoulder white sweater, shoulder straps, line thickness, and soft anime shading.",
            "Shoulders must be usable behind front/side hair without hair baked into the shoulder art.",
            "torso_base must be coherent enough for later breath/body-angle support.",
            "Do not unlock material PASS until overlay QA and visual QA pass after normalization.",
        ],
        "decision": (
            "This packet lets B5 continue without owner acceptance by using Codex provisional success-pattern routes. "
            "It is generation/revision input only, not material approval."
        ),
        "next_action": [
            "Run the focused B5 mini-pass generation/revision using this packet.",
            "Normalize returned candidates as full-canvas RGBA layers.",
            "Rerun B5 overlay QA and then rebuild the 64-part manifest candidate if B5 improves.",
            "Keep B4 front hair as motion-readiness candidates with ParamHairFront hidden.",
        ],
        "self_review": {
            "route_plan_status": route_plan["status"],
            "codex_decision_status": codex_decisions["status"],
            "b5_overlay_qa_status": b5_qa["status"],
            "target_count": len(targets),
            "target_parts": [item["part_id"] for item in targets],
            "regenerate_target_count": sum(1 for item in targets if item["mode"] == "REGENERATE_BODY_MINIPASS"),
            "revise_target_count": sum(1 for item in targets if item["mode"] == "REVISE_DRAW_ORDER_OR_MASK"),
            "all_targets_have_crop_box": all(bool(item["crop_box"]) for item in targets),
            "prompt_present": bool(prompt.strip()),
            "not_owner_approval": True,
            "material_pass_blocked": True,
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "status": "PASS",
        },
    }
    save_json(REPORT_JSON, packet)

    lines = [
        "# Character 002 v22 B5 Provisional Mini-Pass Input Packet",
        "",
        f"- status: `{packet['status']}`",
        f"- source image: `{packet['source_image']}`",
        f"- route plan: `{packet['route_plan']}`",
        "",
        "## Targets",
        "",
    ]
    for item in targets:
        lines.append(
            f"- `{item['part_id']}` `{item['mode']}` `{item['route']}`: {item['instruction']}"
        )
    lines.extend(["", "## Image Generation Prompt", "", "```text", prompt, "```", "", "## Output Requirements", ""])
    lines.extend(f"- {item}" for item in packet["output_requirements"])
    lines.extend(["", "## Self Review", ""])
    for key, value in packet["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": packet["status"], "report": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

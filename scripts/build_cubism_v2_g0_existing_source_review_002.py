#!/usr/bin/env python3
"""Build the v22 G0 review result for character 002's existing source.

This records a source/style gate decision only. It does not generate images
and does not unlock B1-B5 unless the review verdict is PASS.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR = (
    ROOT
    / "experiments/cubism-v2-new-character-002/reports/"
    / "v22_64part_generation_input_packet"
)
PACKET_PATH = PACKET_DIR / "v22_64part_generation_input_packet.json"
SOURCE_PATH = (
    ROOT
    / "experiments/cubism-v2-new-character-002/material_pack_first_v0/"
    / "raw_outputs/new_character_002_source_front.raw.png"
)
OUT_JSON = PACKET_DIR / "v22_g0_existing_source_review.json"
OUT_MD = PACKET_DIR / "v22_g0_existing_source_review.md"

ALLOWED_VERDICTS = [
    "PASS_READY_FOR_64PART_GENERATION",
    "REVISE_SOURCE_STYLE",
    "FAIL_REGENERATE_SOURCE",
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG: {path}")
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    return width, height


def build_review(packet: dict) -> dict:
    width, height = png_size(SOURCE_PATH)
    checklist = packet["g0_review_checklist"]
    item_notes = {
        "same adult cute female character identity is appealing enough for production expansion": (
            "pass",
            "Adult cute female identity is coherent and consistent with the current character-002 source direction.",
        ),
        "front/near-front upper-body pose is centered and not cropped": (
            "pass",
            "Face, hair, shoulders, neck, and torso are centered; lower sleeves/body are not the production boundary for G0 and should be completed by B5.",
        ),
        "both eyes are visible and eye size is not too large": (
            "pass",
            "Both eyes are fully visible, readable, symmetrical enough for the existing v21/v22 eye-anchor baseline, and not oversized.",
        ),
        "mouth is visible, small enough, and placed naturally": (
            "pass",
            "Mouth is visible, subtle, naturally placed, and small enough for a controlled B3 mouth packet.",
        ),
        "nose is visible as subtle face detail": (
            "pass",
            "Nose is visible as a subtle highlight/detail and should be preserved in B5 face-detail generation.",
        ),
        "front/side/back hair groups are readable and not fused into one mass": (
            "pass",
            "Bangs, side hair, long side locks, and back hair silhouette are readable enough to guide B4 hair children.",
        ),
        "neck, shoulders, torso, collar, and simple upper arms are visible": (
            "pass",
            "Neck, shoulders, torso, collar/strap area, and simple upper arms are visible; B5 must create complete clothing/arm underpaint rather than relying on the cropped source bottom.",
        ),
        "no props, hands, hair, or accessories cover eyes or mouth": (
            "pass",
            "No hands, props, labels, or accessories obscure the eyes or mouth; hair occlusion is limited to normal bangs.",
        ),
        "design appears splittable into 64 v2_standard parts": (
            "pass",
            "The simple outfit, readable hair groups, visible face features, and uncluttered silhouette are compatible with the confirmed 64-part v2_standard split.",
        ),
        "no labels, part names, guide marks, or diagram layout": (
            "pass",
            "The source is a coherent character image with no labels, guide marks, UI, text, or part-sheet layout.",
        ),
    }
    review_items = []
    for item in checklist:
        status, note = item_notes[item]
        review_items.append({"item": item, "status": status, "evidence": note})

    verdict = "PASS_READY_FOR_64PART_GENERATION"
    return {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "review_id": "cubism-v2-new-character-002-v22-g0-existing-source-review",
        "status": verdict,
        "allowed_verdicts": ALLOWED_VERDICTS,
        "source_image": str(SOURCE_PATH.relative_to(ROOT)),
        "source_image_abs": str(SOURCE_PATH),
        "source_image_size": {"width": width, "height": height},
        "source_packet": str(PACKET_PATH.relative_to(ROOT)),
        "review_basis": [
            "existing source/front selected for G0 review instead of B0 regeneration",
            "Codex visual review against the v22 G0 checklist",
            "no new image generation was performed",
        ],
        "review_items": review_items,
        "limitations": [
            "This is G0 source/style acceptance, not G1 64-part completeness.",
            "Lower body/sleeve completion, clean bases, underpaints, eyes, mouth, and hair children still require B1-B5 generation.",
            "Mini Cubism diagnostic PASS and real Cubism CMO3/deformer/keyform PASS remain separate later gates.",
        ],
        "next_action": [
            "unlock B1-B5 image-generation preparation from the v22 input packet",
            "generate clean bases/underpaint first so baked eye or mouth pixels are not patched late",
            "build technical validators and contact sheets before Mini Cubism diagnostic preview",
        ],
        "self_review": {
            "source_exists": SOURCE_PATH.exists(),
            "source_is_png": True,
            "allowed_verdict": verdict in ALLOWED_VERDICTS,
            "checklist_count": len(checklist),
            "review_item_count": len(review_items),
            "all_items_have_valid_status": all(
                item["status"] in {"pass", "revise", "fail"} for item in review_items
            ),
            "has_next_action": True,
            "status": "PASS",
        },
    }


def write_markdown(review: dict) -> None:
    lines: list[str] = []
    lines.append("# Character 002 v22 G0 Existing Source Review")
    lines.append("")
    lines.append(f"- status: `{review['status']}`")
    lines.append(f"- generated_at: `{review['generated_at']}`")
    lines.append(f"- source image: `{review['source_image']}`")
    lines.append(
        f"- source size: `{review['source_image_size']['width']}x{review['source_image_size']['height']}`"
    )
    lines.append("- image generation: `NOT_RUN`")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append("`PASS_READY_FOR_64PART_GENERATION`")
    lines.append("")
    lines.append(
        "The existing source/front is accepted for G0 source identity and style. "
        "This unlocks B1-B5 preparation only; it does not promote any generated 64-part material pack."
    )
    lines.append("")
    lines.append("## Review Items")
    lines.append("")
    for item in review["review_items"]:
        label = item["status"].upper()
        lines.append(f"- `{label}` {item['item']}: {item['evidence']}")
    lines.append("")
    lines.append("## Limits")
    lines.append("")
    for item in review["limitations"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Next Action")
    lines.append("")
    for item in review["next_action"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Self Review")
    lines.append("")
    for key, value in review["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(SOURCE_PATH)
    packet = load_json(PACKET_PATH)
    review = build_review(packet)
    OUT_JSON.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(review)
    print(f"status={review['status']}")
    print(f"json={OUT_JSON}")
    print(f"markdown={OUT_MD}")


if __name__ == "__main__":
    main()

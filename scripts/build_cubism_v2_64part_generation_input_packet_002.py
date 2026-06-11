#!/usr/bin/env python3
"""Build the v22 image-generation input packet for character 002.

The packet converts the v22 64-part generation spec into concrete
batch prompts, negative prompts, expected output IDs, and G0 review
criteria. It does not call any image-generation API.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V22_SPEC_PATH = (
    ROOT
    / "experiments/cubism-v2-new-character-002/reports/"
    / "v22_64part_generation_spec/v22_64part_generation_spec.json"
)
PROMPT_TEMPLATE_PATH = (
    ROOT
    / "experiments/reference-model-structure-001/reports/"
    / "cubism_v2_character_prompt_template.json"
)
OUT_DIR = (
    ROOT
    / "experiments/cubism-v2-new-character-002/reports/"
    / "v22_64part_generation_input_packet"
)


IDENTITY_LOCK = [
    "same adult cute female character as the accepted source front",
    "same face proportions, eye spacing, nose position, and mouth anchor",
    "same hairstyle silhouette, bang occlusion, line thickness, and shading style",
    "same outfit design, color palette, and simple upper-body composition",
    "front-facing or near-front neutral upper-body Live2D/Cubism-ready view",
]


GLOBAL_NEGATIVE = [
    "labels, guide marks, UI, watermark, text, part names, arrows, exploded diagram",
    "different character, different outfit, new accessory, changed hairstyle",
    "face-covering hair, covered eyes, covered mouth, crossed arms, complex hands, large props",
    "cropped head, cropped shoulders, side view, extreme pose, perspective distortion",
    "patch boundary, rectangular skin fill, oval mouth patch, visible erased-eye residue",
    "moving eye whites, detached pupil, detached highlight, crossed-eye gaze",
    "oversized round wide-open mouth, tiny centered mouth, pasted teeth, pasted tongue",
    "heavy glow, motion blur, transparent effects, messy dense overlap",
]


GLOBAL_OUTPUT_RULES = [
    "Keep raw outputs as evidence before normalization.",
    "Normalize accepted crops or sheets to shared full-canvas RGBA PNGs.",
    "Default normalization canvas is 2048x2048 unless a later Cubism authoring decision explicitly changes it.",
    "Every crop output must preserve ROI/anchor metadata for later full-canvas placement.",
    "Do not delete rejected outputs; mark them REVISE, FAIL, DISCARDED, or BLOCKED.",
]


BATCH_PROMPT_POLICIES = {
    "B0_source_identity": {
        "prompt_focus": [
            "Create the accepted source/front identity reference.",
            "Prioritize clean silhouette, readable hair groups, visible eyes/mouth/nose, visible neck/shoulders/torso.",
            "Do not make this a part sheet; make it the coherent source image for the material pack.",
        ],
        "must_pass": [
            "주인님 accepts the character style/outfit for production expansion",
            "eyes, mouth, nose, hair groups, neck, shoulders, and torso are readable",
            "design looks splittable into the confirmed 64-part taxonomy",
        ],
    },
    "B1_clean_base_underpaint": {
        "prompt_focus": [
            "Generate clean base and underpaint material for the same character.",
            "Face and underpaint areas must be naturally painted, not erased or covered.",
            "Clean sockets must preserve skin gradient, blush, eyelid fold, and hair occlusion.",
        ],
        "must_pass": [
            "face_base has no open-eye, iris, pupil, white, lash, mouth line, teeth, or tongue residue",
            "no rectangular or oval patch boundary around eyes or mouth",
            "underpaints are suitable for head angle, blink, mouth open, body angle, and hair physics gaps",
        ],
    },
    "B2_eye_pack": {
        "prompt_focus": [
            "Generate left/right eye production parts and blink references as one coherent eye packet.",
            "Eye whites are socket-bound material; iris, pupil, and highlight must be mutually aligned.",
            "Blink in-betweens should follow the v21 natural close pattern, avoiding a harsh 0.0 default close.",
        ],
        "must_pass": [
            "left and right gaze centers are natural and not crossed",
            "iris/pupil/highlight can move together from one anchor",
            "closed lids and underpaint reveal no original open-eye pixels",
        ],
    },
    "B3_mouth_pack": {
        "prompt_focus": [
            "Generate one coordinated smile-open mouth packet for production splitting.",
            "Mouth internals must be drawn inside the same mouth opening, not pasted later.",
            "Wide open should show teeth and tongue naturally but remain proportion-limited.",
        ],
        "must_pass": [
            "mouth anchor stays consistent across closed, small, mid, and wide references",
            "teeth/tongue/inner read naturally and follow the mouth shape",
            "wide-open mouth is not oversized, circular, or patchy",
        ],
    },
    "B4_hair_pack": {
        "prompt_focus": [
            "Generate independent front, side, and back hair children for real HairFront/HairSide/HairBack controls.",
            "Front bangs must remain consistent with face/eye occlusion from the source.",
            "Hair underpaint must cover expected motion gaps.",
        ],
        "must_pass": [
            "hair_front_* children are visible and separable",
            "front hair can move independently without exposing holes",
            "side/back hair groups have readable strand boundaries for physics",
        ],
    },
    "B5_body_clothing_pack": {
        "prompt_focus": [
            "Generate body, clothing, brow, nose, cheek, and face shadow production parts.",
            "Keep the v2_standard scope simple and rig-friendly.",
            "Nose and cheeks must stay subtle but visible as separate material.",
        ],
        "must_pass": [
            "neck, shoulders, torso, simple arms, collar, and chest cloth are readable",
            "nose is not lost during clean face/base generation",
            "body/clothing underpaint can support breath/body angle without visible holes",
        ],
    },
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parts_by_group(parts: list[dict]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for part in parts:
        groups[part["group"]].append(part["id"])
    return dict(groups)


def build_prompt(batch: dict, compact_prompt: str) -> str:
    policy = BATCH_PROMPT_POLICIES.get(batch["id"], {})
    lines = []
    lines.append("Live2D Cubism v2_standard material-pack generation.")
    lines.extend(IDENTITY_LOCK)
    lines.append("")
    lines.append("Base character source constraints:")
    lines.append(compact_prompt)
    lines.append("")
    lines.append(f"Batch: {batch['id']}")
    lines.append(batch["purpose"])
    for item in policy.get("prompt_focus", []):
        lines.append(item)
    lines.append("")
    lines.append("Required output IDs:")
    for output in batch["outputs"]:
        lines.append(f"- {output}")
    lines.append("")
    lines.append("Batch rules:")
    for rule in batch["rules"]:
        lines.append(f"- {rule}")
    return "\n".join(lines)


def build_packet(v22: dict, template: dict) -> dict:
    compact_prompt = template["positive_prompt_compact"]
    part_groups = parts_by_group(v22["parts"])
    batches = []
    for batch in v22["generation_batches"]:
        if batch["id"] == "B6_manifest_normalize_validate":
            continue
        policy = BATCH_PROMPT_POLICIES.get(batch["id"], {})
        batches.append(
            {
                "id": batch["id"],
                "purpose": batch["purpose"],
                "expected_outputs": batch["outputs"],
                "positive_prompt": build_prompt(batch, compact_prompt),
                "negative_prompt": "\n".join(GLOBAL_NEGATIVE),
                "must_pass": policy.get("must_pass", []),
                "failure_patterns_to_watch": [
                    failure["id"]
                    for failure in v22["failure_patterns"]
                    if failure["id"]
                    in {
                        "late_patch_clean_base",
                        "moving_eye_white",
                        "split_eye_detail_drift",
                        "oversized_or_centered_mouth",
                        "pasted_mouth_internals",
                        "fake_hairfront_slider",
                    }
                ],
            }
        )
    return {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "packet_id": "cubism-v2-new-character-002-v22-64part-generation-input-packet",
        "status": "PASS_READY_FOR_G0_SOURCE_STYLE_REVIEW",
        "source_spec": str(V22_SPEC_PATH.relative_to(ROOT)),
        "source_prompt_template": str(PROMPT_TEMPLATE_PATH.relative_to(ROOT)),
        "goal": "Prepare image-generation inputs for the full 64-part material pack, then run G0 source/style review before layer production.",
        "identity_lock": IDENTITY_LOCK,
        "global_negative_prompt": GLOBAL_NEGATIVE,
        "global_output_rules": GLOBAL_OUTPUT_RULES,
        "part_groups": part_groups,
        "generation_batches": batches,
        "g0_review_checklist": [
            "same adult cute female character identity is appealing enough for production expansion",
            "front/near-front upper-body pose is centered and not cropped",
            "both eyes are visible and eye size is not too large",
            "mouth is visible, small enough, and placed naturally",
            "nose is visible as subtle face detail",
            "front/side/back hair groups are readable and not fused into one mass",
            "neck, shoulders, torso, collar, and simple upper arms are visible",
            "no props, hands, hair, or accessories cover eyes or mouth",
            "design appears splittable into 64 v2_standard parts",
            "no labels, part names, guide marks, or diagram layout",
        ],
        "next_after_g0_pass": [
            "generate B1 clean base/underpaint packet",
            "generate B2 eye packet",
            "generate B3 mouth packet",
            "generate B4 hair packet",
            "generate B5 body/clothing packet",
            "normalize raw outputs to full-canvas RGBA",
            "run technical validators and build contact sheet before Mini Cubism diagnostic",
        ],
        "self_review": {
            "batch_count": len(batches),
            "has_b0_source_prompt": any(b["id"] == "B0_source_identity" for b in batches),
            "has_eye_prompt": any(b["id"] == "B2_eye_pack" for b in batches),
            "has_mouth_prompt": any(b["id"] == "B3_mouth_pack" for b in batches),
            "has_hair_prompt": any(b["id"] == "B4_hair_pack" for b in batches),
            "has_g0_checklist": True,
            "part_count": len(v22["parts"]),
            "status": "PASS",
        },
    }


def write_markdown(packet: dict, path: Path) -> None:
    lines: list[str] = []
    lines.append("# Character 002 v22 64-Part Generation Input Packet")
    lines.append("")
    lines.append(f"- status: `{packet['status']}`")
    lines.append(f"- generated_at: `{packet['generated_at']}`")
    lines.append(f"- source spec: `{packet['source_spec']}`")
    lines.append(f"- source prompt template: `{packet['source_prompt_template']}`")
    lines.append("")
    lines.append("## Goal")
    lines.append("")
    lines.append(packet["goal"])
    lines.append("")
    lines.append("## Identity Lock")
    lines.append("")
    for item in packet["identity_lock"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Global Negative Prompt")
    lines.append("")
    lines.append("```text")
    lines.append("\n".join(packet["global_negative_prompt"]))
    lines.append("```")
    lines.append("")
    lines.append("## G0 Source/Style Review Checklist")
    lines.append("")
    for item in packet["g0_review_checklist"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Batch Prompts")
    lines.append("")
    for batch in packet["generation_batches"]:
        lines.append(f"### {batch['id']}")
        lines.append("")
        lines.append(batch["purpose"])
        lines.append("")
        lines.append("Expected outputs:")
        for output in batch["expected_outputs"]:
            lines.append(f"- `{output}`")
        lines.append("")
        lines.append("Positive prompt:")
        lines.append("")
        lines.append("```text")
        lines.append(batch["positive_prompt"])
        lines.append("```")
        lines.append("")
        lines.append("Must pass:")
        for item in batch["must_pass"]:
            lines.append(f"- {item}")
        lines.append("")
    lines.append("## Output Rules")
    lines.append("")
    for item in packet["global_output_rules"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Next After G0 Pass")
    lines.append("")
    for item in packet["next_after_g0_pass"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Self Review")
    lines.append("")
    for key, value in packet["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_g0_checklist(packet: dict, path: Path) -> None:
    lines = [
        "# Character 002 v22 G0 Source/Style Review",
        "",
        "- status: `READY_FOR_G0_SOURCE_STYLE_REVIEW`",
        "- decision needed: 주인님 accepts or rejects the source/style before full 64-part generation.",
        "",
        "## Review Items",
        "",
    ]
    for item in packet["g0_review_checklist"]:
        lines.append(f"- [ ] {item}")
    lines.extend(
        [
            "",
            "## Verdict",
            "",
            "```yaml",
            "human_review: REQUIRED",
            "allowed_values: [PASS_READY_FOR_64PART_GENERATION, REVISE_SOURCE_STYLE, FAIL_REGENERATE_SOURCE]",
            "notes: ''",
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    v22 = load_json(V22_SPEC_PATH)
    template = load_json(PROMPT_TEMPLATE_PATH)
    packet = build_packet(v22, template)
    json_path = OUT_DIR / "v22_64part_generation_input_packet.json"
    md_path = OUT_DIR / "v22_64part_generation_input_packet.md"
    g0_path = OUT_DIR / "v22_g0_source_style_review_checklist.md"
    json_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(packet, md_path)
    write_g0_checklist(packet, g0_path)
    print(f"status={packet['status']}")
    print(f"json={json_path}")
    print(f"markdown={md_path}")
    print(f"g0_checklist={g0_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build concise official-learning profiles for Live2D sample models.

The profiles intentionally store short learning targets, not copied page text.
They are used as hypotheses that are later checked against local zip structure
and CMO3/MOC3/runtime JSON reports.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "experiments" / "reference-model-structure-001" / "reports"
OFFICIAL_SAMPLE_URL = "https://www.live2d.com/ko/learn/sample/"


OFFICIAL_PROFILES: dict[str, dict[str, Any]] = {
    "ren": {
        "display_name": "Ren Foster",
        "aliases": ["ren", "ren_pro", "렌 포스터"],
        "official_learning_target": [
            "Cubism 5.3 rich drawing",
            "alpha blend masks",
            "offscreen rendering",
            "high-spec avatar expression",
        ],
        "expected_success_pattern": {
            "mask": "KEEP",
            "physics": "REFERENCE_ONLY",
            "body_angle": "REFERENCE_ONLY",
        },
        "pattern_decision": "REFERENCE_ONLY",
        "source_note": "Official page describes this as a Cubism 5.3 rich rendering sample using alpha blend masks and offscreen rendering.",
    },
    "param_ctrl": {
        "display_name": "Parameter Controller Sample",
        "aliases": ["param_ctrl", "parameter controller", "파라미터 컨트롤러"],
        "official_learning_target": [
            "parameter controller",
            "target following",
            "animation efficiency",
        ],
        "expected_success_pattern": {
            "motion_pose": "REFERENCE_ONLY",
            "body_angle": "REFERENCE_ONLY",
        },
        "pattern_decision": "REFERENCE_ONLY",
        "source_note": "Official page describes parameter controller target-following for animation production.",
    },
    "kei": {
        "display_name": "Kei",
        "aliases": ["kei", "케이"],
        "official_learning_target": [
            "motion sync",
            "lip-sync presets",
            "mouth parameter composition",
        ],
        "expected_success_pattern": {
            "mouth": "KEEP",
            "physics": "REFERENCE_ONLY",
        },
        "pattern_decision": "KEEP",
        "source_note": "Official page describes Kei as a motion-sync/lip-sync sample with preset-compatible mouth parameters.",
    },
    "mao": {
        "display_name": "Niziiro Mao",
        "aliases": ["mao", "niziiro mao", "니지이로 마오"],
        "official_learning_target": [
            "blend shapes",
            "multiply and screen color",
            "mouth, eyebrow, and hair additive shape differences",
            "wide face motion range",
        ],
        "expected_success_pattern": {
            "mouth": "KEEP",
            "eye": "KEEP",
            "hair": "KEEP",
            "body_angle": "KEEP",
            "motion_pose": "REFERENCE_ONLY",
        },
        "pattern_decision": "KEEP",
        "source_note": "Official page describes blend shapes for mouth, eyebrow, and hair swing, plus a wide face range.",
    },
    "hiyori": {
        "display_name": "Momose Hiyori",
        "aliases": ["hiyori", "momose hiyori"],
        "official_learning_target": [
            "standard Cubism 3.0 model",
            "deformer structure",
            "parameter structure",
            "hair skinning",
        ],
        "expected_success_pattern": {
            "eye": "KEEP",
            "mouth": "KEEP",
            "hair": "KEEP",
            "body_angle": "KEEP",
            "physics": "KEEP",
        },
        "pattern_decision": "KEEP",
        "source_note": "Official page describes Hiyori as a standard model for learning deformer and parameter structure, with hair skinning.",
    },
    "mark": {
        "display_name": "Mark-kun",
        "aliases": ["mark", "mark-kun", "mark_movie"],
        "official_learning_target": [
            "simple deformer structure",
            "simple parameter structure",
            "physics",
            "eye blink",
            "PSD availability",
        ],
        "expected_success_pattern": {
            "eye": "KEEP",
            "mouth": "REFERENCE_ONLY",
            "physics": "KEEP",
            "psd_layering": "KEEP",
        },
        "pattern_decision": "KEEP",
        "source_note": "Official page describes Mark-kun as a simple beginner model with physics, blinking, SDK introduction, and PSD availability.",
    },
    "miku": {
        "display_name": "Hatsune Miku",
        "aliases": ["miku", "hatsune miku"],
        "official_learning_target": [
            "twin-tail hair skinning",
            "smooth long hair motion",
        ],
        "expected_success_pattern": {
            "hair": "KEEP",
            "physics": "KEEP",
        },
        "pattern_decision": "REFERENCE_ONLY",
        "source_note": "Official page describes Miku as a sample where twin-tail hair moves smoothly through skinning. Character/art style is not reusable.",
    },
    "rice": {
        "display_name": "Rice Glassfield",
        "aliases": ["rice"],
        "official_learning_target": [
            "extended interpolation",
            "inverted mask",
            "forelock and fire effects",
        ],
        "expected_success_pattern": {
            "mask": "KEEP",
            "hair": "REFERENCE_ONLY",
            "motion_pose": "REFERENCE_ONLY",
        },
        "pattern_decision": "REFERENCE_ONLY",
        "source_note": "Official page describes Rice as useful for extended interpolation and inverted-mask expression such as forelock and fire.",
    },
    "tsumiki": {
        "display_name": "Tsumiki",
        "aliases": ["tsumiki"],
        "official_learning_target": [
            "eyelid clipping mask",
            "standard avatar motion",
        ],
        "expected_success_pattern": {
            "eye": "KEEP",
            "mask": "KEEP",
        },
        "pattern_decision": "REFERENCE_ONLY",
        "source_note": "Official page groups Tsumiki with eyelid clipping-mask learning value.",
    },
    "unitychan": {
        "display_name": "Unity-chan",
        "aliases": ["unitychan", "unity-chan"],
        "official_learning_target": [
            "eyelid clipping mask",
            "PSD layer reference",
            "deformed character model",
        ],
        "expected_success_pattern": {
            "eye": "KEEP",
            "mask": "KEEP",
            "psd_layering": "REFERENCE_ONLY",
        },
        "pattern_decision": "REFERENCE_ONLY",
        "source_note": "Official page describes eyelid clipping masks and includes a PSD, with separate Unity-chan license rules.",
    },
    "epsilon": {
        "display_name": "Epsilon",
        "aliases": ["epsilon"],
        "official_learning_target": [
            "standard easy-to-use model",
            "expression effects",
        ],
        "expected_success_pattern": {
            "eye": "REFERENCE_ONLY",
            "mouth": "REFERENCE_ONLY",
            "motion_pose": "REFERENCE_ONLY",
        },
        "pattern_decision": "REFERENCE_ONLY",
        "source_note": "Official page describes Epsilon as a standard easy-to-use model with expression effects.",
    },
    "haru": {
        "display_name": "Haru",
        "aliases": ["haru"],
        "official_learning_target": [
            "arm switching",
            "clothing changes",
            "voice and expression testing",
            "overall Live2D feature test",
        ],
        "expected_success_pattern": {
            "motion_pose": "KEEP",
            "body_angle": "REFERENCE_ONLY",
            "physics": "REFERENCE_ONLY",
        },
        "pattern_decision": "REFERENCE_ONLY",
        "source_note": "Official page describes Haru as supporting arm switching and clothing changes with voice files.",
    },
    "haru_greeter": {
        "display_name": "Haru Greeter",
        "aliases": ["haru_greeter", "greeter"],
        "official_learning_target": [
            "PSD material division",
            "PSD import material structure",
            "avatar greeting motions",
        ],
        "expected_success_pattern": {
            "psd_layering": "KEEP",
            "motion_pose": "REFERENCE_ONLY",
        },
        "pattern_decision": "KEEP",
        "source_note": "Official distribution contains material-division and import PSDs, making it useful for PSD layer structure study.",
    },
    "chitose": {
        "display_name": "Chitose",
        "aliases": ["chitose"],
        "official_learning_target": [
            "male avatar model",
            "right-arm switching",
            "handwave motion",
        ],
        "expected_success_pattern": {
            "motion_pose": "KEEP",
            "body_angle": "REFERENCE_ONLY",
        },
        "pattern_decision": "REFERENCE_ONLY",
        "source_note": "Official page describes Chitose as a male model with right-arm switching for waving.",
    },
    "izumi": {
        "display_name": "Izumi",
        "aliases": ["izumi"],
        "official_learning_target": [
            "multiple art styles",
            "oblique source pose",
            "opposite-facing motion",
        ],
        "expected_success_pattern": {
            "body_angle": "KEEP",
            "motion_pose": "REFERENCE_ONLY",
        },
        "pattern_decision": "REFERENCE_ONLY",
        "source_note": "Official page describes four texture styles and motion from an oblique original pose toward the opposite direction.",
    },
    "nito": {
        "display_name": "Nito",
        "aliases": ["nito", "nico", "nietzsche", "ni-j", "nipsilon"],
        "official_learning_target": [
            "two-head character",
            "multiple variants in one model",
            "large mouth expression",
            "limbless comical motion",
        ],
        "expected_success_pattern": {
            "mouth": "KEEP",
            "motion_pose": "KEEP",
        },
        "pattern_decision": "REFERENCE_ONLY",
        "source_note": "Official page describes Nito as a two-head character with multiple variants, large mouth expressions, and comical limb motion.",
    },
    "gantzert_felixander": {
        "display_name": "Gantzert & Felixander",
        "aliases": ["gantzert", "felixander", "gantzert_felixander"],
        "official_learning_target": [
            "additive drawing effects",
            "many clipping expressions",
            "right hand, dragon wings, thunder and fire reflection",
        ],
        "expected_success_pattern": {
            "mask": "KEEP",
            "motion_pose": "REFERENCE_ONLY",
        },
        "pattern_decision": "REFERENCE_ONLY",
        "source_note": "Official page describes additive effects and many clipping expressions for hand, wings, thunder, and fire reflection.",
    },
    "koharu": {
        "display_name": "Koharu",
        "aliases": ["koharu"],
        "official_learning_target": [
            "PSD material division",
            "paired sample character",
            "runtime motion baseline",
        ],
        "expected_success_pattern": {
            "psd_layering": "KEEP",
            "motion_pose": "REFERENCE_ONLY",
        },
        "pattern_decision": "REFERENCE_ONLY",
        "source_note": "Official zip contains Koharu PSD and runtime files; use as PSD/material structure reference.",
    },
    "haruto": {
        "display_name": "Haruto",
        "aliases": ["haruto"],
        "official_learning_target": [
            "PSD material division",
            "paired sample character",
            "runtime motion baseline",
        ],
        "expected_success_pattern": {
            "psd_layering": "KEEP",
            "motion_pose": "REFERENCE_ONLY",
        },
        "pattern_decision": "REFERENCE_ONLY",
        "source_note": "Official zip contains Haruto PSD and runtime files; use as PSD/material structure reference.",
    },
    "miara": {
        "display_name": "Miara",
        "aliases": ["miara"],
        "official_learning_target": [
            "full-body avatar",
            "voice motion",
            "physics baseline",
        ],
        "expected_success_pattern": {
            "body_angle": "REFERENCE_ONLY",
            "physics": "REFERENCE_ONLY",
        },
        "pattern_decision": "REFERENCE_ONLY",
        "source_note": "Official sample includes CMO3, runtime, motion, and physics; use as secondary full-body baseline.",
    },
    "natori": {
        "display_name": "Natori",
        "aliases": ["natori"],
        "official_learning_target": [
            "expressions",
            "pose",
            "motion baseline",
            "physics baseline",
        ],
        "expected_success_pattern": {
            "motion_pose": "KEEP",
            "physics": "REFERENCE_ONLY",
        },
        "pattern_decision": "REFERENCE_ONLY",
        "source_note": "Official sample includes many expressions, pose data, motions, and physics.",
    },
    "shizuku": {
        "display_name": "Shizuku",
        "aliases": ["shizuku"],
        "official_learning_target": [
            "legacy sample structure",
            "pose and physics baseline",
        ],
        "expected_success_pattern": {
            "motion_pose": "REFERENCE_ONLY",
            "physics": "REFERENCE_ONLY",
        },
        "pattern_decision": "REFERENCE_ONLY",
        "source_note": "Official sample includes runtime, motion, pose, and physics; use as secondary baseline only.",
    },
    "wanko": {
        "display_name": "Wanko",
        "aliases": ["wanko"],
        "official_learning_target": [
            "touch motions",
            "non-human avatar runtime",
            "physics baseline",
        ],
        "expected_success_pattern": {
            "motion_pose": "REFERENCE_ONLY",
            "physics": "REFERENCE_ONLY",
        },
        "pattern_decision": "REFERENCE_ONLY",
        "source_note": "Official sample includes touch/idle motions and physics; useful as non-human contrast only.",
    },
}


ZIP_PROFILE_HINTS: dict[str, list[str]] = {
    "chitose": ["chitose"],
    "epsilon": ["epsilon"],
    "haru_greeter": ["haru_greeter"],
    "koharu_haruto": ["koharu", "haruto"],
    "haru": ["haru"],
    "hiyori_movie": ["hiyori"],
    "hiyori": ["hiyori"],
    "kei": ["kei"],
    "mao": ["mao"],
    "mark": ["mark"],
    "miara": ["miara"],
    "natori": ["natori"],
    "param_ctrl": ["param_ctrl"],
    "ren": ["ren"],
    "rice": ["rice"],
    "shizuku": ["shizuku"],
    "tsumiki": ["tsumiki"],
    "unitychan": ["unitychan"],
    "wanko": ["wanko"],
    "miku": ["miku"],
    "tororo_hijiki": ["tororo_hijiki"],
    "nito": ["nito"],
    "izumi": ["izumi"],
    "gantzert": ["gantzert_felixander"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT), help="Output reports directory.")
    parser.add_argument("--zip-manifest", help="Optional download_manifest.json to link zip files.")
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def zip_id_from_path(path: str) -> str:
    return Path(path).stem.lower().replace("-", "_")


def profile_keys_for_zip(zip_id: str) -> list[str]:
    for token, keys in ZIP_PROFILE_HINTS.items():
        if token in zip_id:
            return keys
    return []


def build_profiles(zip_manifest_path: Path | None) -> dict[str, Any]:
    zip_links: dict[str, list[str]] = {key: [] for key in OFFICIAL_PROFILES}
    missing: list[dict[str, str]] = []
    if zip_manifest_path and zip_manifest_path.exists():
        manifest = load_json(zip_manifest_path)
        for item in manifest.get("zip_files", []):
            zip_path = item.get("zip_path") or item.get("path")
            zip_id = item.get("zip_id") or zip_id_from_path(zip_path or "")
            keys = profile_keys_for_zip(zip_id)
            if not keys:
                missing.append({"zip_id": zip_id, "zip_path": zip_path or "", "status": "OFFICIAL_PROFILE_MISSING"})
                continue
            for key in keys:
                zip_links.setdefault(key, []).append(zip_path or zip_id)

    profiles = []
    for key, profile in sorted(OFFICIAL_PROFILES.items()):
        payload = {
            "profile_key": key,
            "official_sample_url": OFFICIAL_SAMPLE_URL,
            "linked_zip_files": zip_links.get(key, []),
            "official_description": profile["source_note"],
            "official_learning_target": profile["official_learning_target"],
            "expected_success_pattern": profile["expected_success_pattern"],
            "pattern_decision": profile["pattern_decision"],
            "aliases": profile["aliases"],
            "display_name": profile["display_name"],
        }
        profiles.append(payload)
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_url": OFFICIAL_SAMPLE_URL,
        "copyright_note": "Short learning targets only; do not copy official sample art, textures, PSD layers, or long page text.",
        "profiles": profiles,
        "zip_profile_missing": missing,
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    rows = []
    for item in report["profiles"]:
        target = ", ".join(item["official_learning_target"])
        patterns = ", ".join(f"{k}:{v}" for k, v in item["expected_success_pattern"].items())
        zips = ", ".join(Path(p).name for p in item.get("linked_zip_files", [])) or "none"
        rows.append(
            f"| {item['profile_key']} | {item['display_name']} | {item['pattern_decision']} | {target} | {patterns} | {zips} |"
        )
    missing = "\n".join(
        f"- `{m['zip_id']}`: {m['status']} ({Path(m['zip_path']).name})"
        for m in report.get("zip_profile_missing", [])
    ) or "- none"
    text = f"""# Official Live2D Sample Profiles

Generated: {report['generated_at']}

Source: {report['source_url']}

This report stores short learning targets only. Do not reuse official sample art, textures, PSD layers, or character designs in Vtube outputs.

## Profiles

| Key | Model | Decision | Learning Target | Expected Pattern | Linked Zip |
|---|---|---|---|---|---|
{chr(10).join(rows)}

## Missing Profile Links

{missing}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir).expanduser().resolve()
    zip_manifest_path = Path(args.zip_manifest).expanduser().resolve() if args.zip_manifest else None
    report = build_profiles(zip_manifest_path)
    write_json(out_dir / "official_sample_profiles.json", report)
    write_markdown(out_dir / "official_sample_profiles.md", report)
    print(json.dumps({"ok": True, "profiles": len(report["profiles"]), "missing": len(report["zip_profile_missing"])}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

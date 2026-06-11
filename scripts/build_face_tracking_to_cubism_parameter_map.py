#!/usr/bin/env python3
"""Build a face-tracking to Cubism parameter mapping spec for the v2 model."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "experiments" / "reference-model-structure-001" / "reports"
DEFAULT_PRODUCTION_SPEC = REPORTS / "cubism_v2_production_design_spec.json"
DEFAULT_PART_SPEC = REPORTS / "cubism_v2_new_model_v2_standard_part_spec.json"
DEFAULT_PROMPT_TEMPLATE = REPORTS / "cubism_v2_character_prompt_template.json"
DEFAULT_RUNTIME_METADATA = REPORTS / "all57_runtime_metadata_extras.json"
DEFAULT_OUT_DIR = REPORTS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--production-spec", type=Path, default=DEFAULT_PRODUCTION_SPEC)
    parser.add_argument("--part-spec", type=Path, default=DEFAULT_PART_SPEC)
    parser.add_argument("--prompt-template", type=Path, default=DEFAULT_PROMPT_TEMPLATE)
    parser.add_argument("--runtime-metadata", type=Path, default=DEFAULT_RUNTIME_METADATA)
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


def required_params(production: dict[str, Any]) -> list[str]:
    return [
        item.get("production_name")
        for item in production.get("parameter_map_detail", []) or []
        if item.get("required_level") == "REQUIRED" and item.get("production_name")
    ]


def part_groups(part_spec: dict[str, Any]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for part in part_spec.get("parts", []) or []:
        groups.setdefault(part.get("group") or "unknown", []).append(part.get("id"))
    return {key: [value for value in values if value] for key, values in sorted(groups.items())}


def build_mappings() -> list[dict[str, Any]]:
    return [
        {
            "id": "head_yaw_to_angle_x",
            "tracking_input": "head_yaw_from_facial_transformation_matrix",
            "provider_aliases": ["MediaPipe facialTransformationMatrix yaw", "ARKit head yaw"],
            "cubism_parameter": "ParamAngleX",
            "input_range": [-25, 25],
            "output_range": [-30, 30],
            "default": 0,
            "formula": "clamp(normalize_centered(head_yaw, -25, 25) * 30, -30, 30)",
            "calibration": "center_zero_at_neutral_face",
            "smoothing": {"type": "ema", "alpha": 0.35},
            "required_parts": ["face_base", "eye_L", "eye_R", "brow", "mouth", "hair"],
            "qa_probe": "Turn face left/right; face, eyes, mouth, and front hair should follow without overhang.",
            "priority": "REQUIRED",
        },
        {
            "id": "head_pitch_to_angle_y",
            "tracking_input": "head_pitch_from_facial_transformation_matrix",
            "provider_aliases": ["MediaPipe facialTransformationMatrix pitch", "ARKit head pitch"],
            "cubism_parameter": "ParamAngleY",
            "input_range": [-20, 20],
            "output_range": [-30, 30],
            "default": 0,
            "formula": "clamp(normalize_centered(head_pitch, -20, 20) * 30, -30, 30)",
            "calibration": "center_zero_at_neutral_face",
            "smoothing": {"type": "ema", "alpha": 0.35},
            "required_parts": ["face_base", "eye_L", "eye_R", "mouth", "neck", "front_hair"],
            "qa_probe": "Look up/down; chin, neck, mouth, and bangs should not tear or expose missing underpaint.",
            "priority": "REQUIRED",
        },
        {
            "id": "head_roll_to_angle_z",
            "tracking_input": "head_roll_from_facial_transformation_matrix",
            "provider_aliases": ["MediaPipe facialTransformationMatrix roll", "ARKit head roll"],
            "cubism_parameter": "ParamAngleZ",
            "input_range": [-25, 25],
            "output_range": [-30, 30],
            "default": 0,
            "formula": "clamp(normalize_centered(head_roll, -25, 25) * 30, -30, 30)",
            "calibration": "center_zero_at_neutral_face",
            "smoothing": {"type": "ema", "alpha": 0.35},
            "required_parts": ["face_base", "hair", "neck"],
            "qa_probe": "Tilt head left/right; hair and neck should follow without draw-order inversion.",
            "priority": "REQUIRED",
        },
        {
            "id": "eye_blink_left_to_eye_l_open",
            "tracking_input": "eyeBlinkLeft",
            "provider_aliases": ["MediaPipe eyeBlinkLeft blendshape", "ARKit eyeBlinkLeft"],
            "cubism_parameter": "ParamEyeLOpen",
            "input_range": [0, 1],
            "output_range": [0, 1],
            "default": 1,
            "formula": "clamp(1 - eyeBlinkLeft, 0, 1)",
            "calibration": "open_eye_baseline_and_closed_eye_baseline",
            "smoothing": {"type": "ema", "alpha": 0.45, "fast_close": True},
            "required_parts": ["eye_white_L", "iris_L", "pupil_L", "upper_lid_L", "lower_lid_L", "upper_lash_L"],
            "qa_probe": "Blink left eye; left eye should close fully and reopen without affecting the right eye.",
            "priority": "REQUIRED",
        },
        {
            "id": "eye_blink_right_to_eye_r_open",
            "tracking_input": "eyeBlinkRight",
            "provider_aliases": ["MediaPipe eyeBlinkRight blendshape", "ARKit eyeBlinkRight"],
            "cubism_parameter": "ParamEyeROpen",
            "input_range": [0, 1],
            "output_range": [0, 1],
            "default": 1,
            "formula": "clamp(1 - eyeBlinkRight, 0, 1)",
            "calibration": "open_eye_baseline_and_closed_eye_baseline",
            "smoothing": {"type": "ema", "alpha": 0.45, "fast_close": True},
            "required_parts": ["eye_white_R", "iris_R", "pupil_R", "upper_lid_R", "lower_lid_R", "upper_lash_R"],
            "qa_probe": "Blink right eye; right eye should close fully and reopen without affecting the left eye.",
            "priority": "REQUIRED",
        },
        {
            "id": "eye_gaze_x_to_eye_ball_x",
            "tracking_input": "eye_gaze_x_from_landmarks_or_eyeLook blendshapes",
            "provider_aliases": ["eyeLookInLeft/Right", "eyeLookOutLeft/Right", "landmark iris center delta"],
            "cubism_parameter": "ParamEyeBallX",
            "input_range": [-1, 1],
            "output_range": [-1, 1],
            "default": 0,
            "formula": "clamp(eye_gaze_x, -1, 1)",
            "calibration": "center_zero_at_looking_forward",
            "smoothing": {"type": "ema", "alpha": 0.3},
            "required_parts": ["iris_L", "iris_R", "pupil_L", "pupil_R", "catchlight_L", "catchlight_R"],
            "qa_probe": "Look left/right; both irises should move together and stay inside eye masks.",
            "priority": "REQUIRED",
        },
        {
            "id": "eye_gaze_y_to_eye_ball_y",
            "tracking_input": "eye_gaze_y_from_landmarks_or_eyeLook blendshapes",
            "provider_aliases": ["eyeLookUpLeft/Right", "eyeLookDownLeft/Right", "landmark iris center delta"],
            "cubism_parameter": "ParamEyeBallY",
            "input_range": [-1, 1],
            "output_range": [-1, 1],
            "default": 0,
            "formula": "clamp(eye_gaze_y, -1, 1)",
            "calibration": "center_zero_at_looking_forward",
            "smoothing": {"type": "ema", "alpha": 0.3},
            "required_parts": ["iris_L", "iris_R", "pupil_L", "pupil_R", "catchlight_L", "catchlight_R"],
            "qa_probe": "Look up/down; irises should stay clipped by eyelids and not float outside whites.",
            "priority": "REQUIRED",
        },
        {
            "id": "jaw_open_to_mouth_open_y",
            "tracking_input": "jawOpen",
            "provider_aliases": ["MediaPipe jawOpen blendshape", "ARKit jawOpen"],
            "cubism_parameter": "ParamMouthOpenY",
            "input_range": [0, 1],
            "output_range": [0, 1],
            "default": 0,
            "formula": "clamp(remap_deadzone(jawOpen, 0.08, 0.85), 0, 1)",
            "calibration": "closed_mouth_deadzone_and_max_open",
            "smoothing": {"type": "ema", "alpha": 0.4, "fast_open": True},
            "required_parts": ["mouth_closed_line", "mouth_open_inner", "mouth_teeth_upper", "mouth_tongue", "mouth_shadow"],
            "qa_probe": "Open/close mouth; inner mouth should appear smoothly and close fully at rest.",
            "priority": "REQUIRED",
        },
        {
            "id": "smile_frown_to_mouth_form",
            "tracking_input": "mouthSmileLeft/Right minus mouthFrownLeft/Right",
            "provider_aliases": ["mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft", "mouthFrownRight"],
            "cubism_parameter": "ParamMouthForm",
            "input_range": [-1, 1],
            "output_range": [-1, 1],
            "default": 0,
            "formula": "clamp(avg(mouthSmileLeft, mouthSmileRight) - avg(mouthFrownLeft, mouthFrownRight), -1, 1)",
            "calibration": "neutral_mouth_zero",
            "smoothing": {"type": "ema", "alpha": 0.35},
            "required_parts": ["mouth_closed_line", "mouth_corner_L", "mouth_corner_R", "mouth_open_outer"],
            "qa_probe": "Smile/frown; mouth corners should move without breaking mouth-open keyforms.",
            "priority": "REQUIRED",
        },
        {
            "id": "head_yaw_to_body_angle_x",
            "tracking_input": "head_yaw_from_facial_transformation_matrix",
            "provider_aliases": ["damped head yaw"],
            "cubism_parameter": "ParamBodyAngleX",
            "input_range": [-25, 25],
            "output_range": [-10, 10],
            "default": 0,
            "formula": "clamp(normalize_centered(head_yaw, -25, 25) * 10 * 0.65, -10, 10)",
            "calibration": "follow_head_but_weaker",
            "smoothing": {"type": "ema", "alpha": 0.25},
            "required_parts": ["neck", "torso_base", "shoulder_L", "shoulder_R", "arm_L_upper_simple", "arm_R_upper_simple"],
            "qa_probe": "Turn head; body should follow subtly and never move more strongly than the head.",
            "priority": "REQUIRED",
        },
        {
            "id": "head_pitch_to_body_angle_y",
            "tracking_input": "head_pitch_from_facial_transformation_matrix",
            "provider_aliases": ["damped head pitch"],
            "cubism_parameter": "ParamBodyAngleY",
            "input_range": [-20, 20],
            "output_range": [-10, 10],
            "default": 0,
            "formula": "clamp(normalize_centered(head_pitch, -20, 20) * 10 * 0.45, -10, 10)",
            "calibration": "follow_head_but_weaker",
            "smoothing": {"type": "ema", "alpha": 0.25},
            "required_parts": ["neck", "torso_base", "shoulder_L", "shoulder_R", "body_underpaint"],
            "qa_probe": "Look up/down; torso should breathe/follow subtly without neck gap.",
            "priority": "REQUIRED",
        },
        {
            "id": "head_roll_to_body_angle_z",
            "tracking_input": "head_roll_from_facial_transformation_matrix",
            "provider_aliases": ["damped head roll"],
            "cubism_parameter": "ParamBodyAngleZ",
            "input_range": [-25, 25],
            "output_range": [-10, 10],
            "default": 0,
            "formula": "clamp(normalize_centered(head_roll, -25, 25) * 10 * 0.5, -10, 10)",
            "calibration": "follow_head_but_weaker",
            "smoothing": {"type": "ema", "alpha": 0.25},
            "required_parts": ["torso_base", "shoulder_L", "shoulder_R", "neck"],
            "qa_probe": "Tilt head; torso should tilt softly and preserve shoulder draw order.",
            "priority": "RECOMMENDED",
        },
        {
            "id": "breath_idle_to_param_breath",
            "tracking_input": "synthetic_breath_idle",
            "provider_aliases": ["idle animation", "runtime oscillator"],
            "cubism_parameter": "ParamBreath",
            "input_range": [0, 1],
            "output_range": [0, 1],
            "default": 0,
            "formula": "0.5 + 0.5 * sin(time * breath_rate)",
            "calibration": "not_face_tracking_direct",
            "smoothing": {"type": "runtime_generated"},
            "required_parts": ["torso_base", "neck", "shoulder_L", "shoulder_R"],
            "qa_probe": "Idle for 10 seconds; breath should be visible but not distract from face tracking.",
            "priority": "RECOMMENDED",
        },
        {
            "id": "mouth_vowels_optional",
            "tracking_input": "audio_motionsync_or_vowel_classifier",
            "provider_aliases": ["MotionSync", "lip-sync A/I/U/E/O"],
            "cubism_parameter": "ParamA/ParamI/ParamU/ParamE/ParamO",
            "input_range": [0, 1],
            "output_range": [0, 1],
            "default": 0,
            "formula": "optional; use only when v2_rich or motion-sync is enabled",
            "calibration": "audio_or_motionsync_specific",
            "smoothing": {"type": "provider_specific"},
            "required_parts": ["mouth_open_inner", "mouth_tongue", "mouth_teeth_upper", "mouth_corner_L", "mouth_corner_R"],
            "qa_probe": "Optional vowel test; not required for first v2_standard model.",
            "priority": "OPTIONAL_V2_RICH",
        },
    ]


def build_payload(
    production: dict[str, Any],
    part_spec: dict[str, Any],
    prompt_template: dict[str, Any],
    runtime_metadata: dict[str, Any],
    input_paths: dict[str, Path],
) -> dict[str, Any]:
    mappings = build_mappings()
    params = required_params(production)
    mapping_outputs = {item["cubism_parameter"] for item in mappings}
    params_without_mapping = [param for param in params if param not in mapping_outputs]
    metadata_summary = runtime_metadata.get("summary", {})
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "spec_id": "face_tracking_to_cubism_parameter_map",
        "status": "PASS" if not params_without_mapping else "WARN",
        "inputs": {key: rel(value) for key, value in input_paths.items()},
        "reference_sources": [
            {
                "name": "MediaPipe Face Landmarker",
                "url": "https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker",
                "used_for": "webcam/video face landmarks, blendshape scores, and facial transformation matrices",
            },
            {
                "name": "Live2D Cubism standard parameter list",
                "url": "https://docs.live2d.com/ko/cubism-editor-manual/standard-parameter-list/",
                "used_for": "Cubism parameter IDs and standard output ranges",
            },
            {
                "name": "VTube Studio value-provider priority",
                "url": "https://github.com/DenchiSoft/VTubeStudio/wiki/Interaction-between-Animations%2C-Tracking%2C-Physics%2C-etc.",
                "used_for": "tracking/animation/expression/physics priority risk",
            },
            {
                "name": "nizima LIVE parameter settings",
                "url": "https://docs.live2d.com/nizimalive/en/manual/parameter/",
                "used_for": "webcam tracking, automatic blink, lip-sync, and motion-sync interaction notes",
            },
        ],
        "input_provider": {
            "primary": "MediaPipe Face Landmarker",
            "runtime_mode": "webcam_or_video_smoke_first",
            "required_outputs": {
                "face_landmarks": True,
                "face_blendshapes": True,
                "facial_transformation_matrixes": True,
            },
            "recommended_options": {
                "num_faces": 1,
                "output_face_blendshapes": True,
                "output_facial_transformation_matrixes": True,
                "min_face_detection_confidence": 0.5,
                "min_face_presence_confidence": 0.5,
                "min_tracking_confidence": 0.5,
            },
        },
        "current_asset_readiness": {
            "has_tracking_friendly_parameter_floor": True,
            "has_actual_webcam_tracking_smoke": False,
            "required_parameters_from_production_spec": params,
            "params_without_direct_mapping": params_without_mapping,
            "part_group_counts": {key: len(value) for key, value in part_groups(part_spec).items()},
            "prompt_template_mode": prompt_template.get("target", {}).get("source_image_mode"),
            "all57_runtime_metadata_coverage": metadata_summary.get("coverage", {}),
        },
        "mappings": mappings,
        "calibration_policy": {
            "neutral_capture_seconds": 2,
            "neutral_samples_min": 45,
            "centered_head_pose": "average yaw/pitch/roll during neutral capture becomes zero",
            "blink": "measure open-eye baseline and closed-eye baseline; map tracking blink to Live2D open value with inversion",
            "mouth": "apply closed-mouth deadzone to jawOpen before ParamMouthOpenY",
            "body": "derive from head pose with damping; body must never overpower head motion",
        },
        "runtime_priority_policy": {
            "tracking_controls": [
                "ParamAngleX",
                "ParamAngleY",
                "ParamAngleZ",
                "ParamEyeLOpen",
                "ParamEyeROpen",
                "ParamEyeBallX",
                "ParamEyeBallY",
                "ParamMouthOpenY",
                "ParamMouthForm",
                "ParamBodyAngleX",
                "ParamBodyAngleY",
                "ParamBodyAngleZ",
            ],
            "physics_controls": [
                "ParamHairFront",
                "ParamHairSide",
                "ParamHairBack",
                "secondary sway outputs",
            ],
            "idle_controls": ["ParamBreath"],
            "risk_note": "Face tracking, idle animation, expressions, and physics can compete for the same parameter in viewer apps. Keep ownership explicit.",
        },
        "pre_character_generation_requirements": [
            "Character prompt must keep both eyes, mouth, eyebrows, neck, shoulders, and simple arms visible.",
            "Do not hide mouth with hands, microphone, scarf, props, or bangs.",
            "Do not hide eyes with hair or accessories; blink tracking requires visible eyelids/lashes.",
            "Use standard Live2D parameter IDs so VTube Studio/nizima/other viewers can map tracking inputs predictably.",
            "Keep body motion simple; complex arm/hand tracking is deferred.",
        ],
        "smoke_test_plan": [
            {
                "id": "T0_static_sample_json",
                "goal": "Convert recorded/synthetic MediaPipe-like values into Cubism parameter values without webcam dependency.",
                "pass": "All REQUIRED mappings produce finite values inside output ranges.",
            },
            {
                "id": "T1_webcam_tracking_probe",
                "goal": "Use MediaPipe webcam/video to emit head pose, blink, gaze, jawOpen, and mouthForm proxy values.",
                "pass": "At least 10 seconds of timestamped tracking frames are saved as JSON with no missing required channels.",
            },
            {
                "id": "T2_reference_model_parameter_drive",
                "goal": "Drive a verified reference model before using a new character.",
                "pass": "ParamAngleX/Y/Z, eye open, eye ball, mouth open/form visibly affect the model in screenshots/strip.",
            },
            {
                "id": "T3_new_model_export_tracking_gate",
                "goal": "After Cubism authoring, prove the new model responds to tracking-derived values.",
                "pass": "G3 motion strip includes head yaw/pitch/roll, blink L/R, eye gaze, mouth open, mouth form, and body damped follow.",
            },
        ],
        "next_actions": [
            "Create a MediaPipe webcam or recorded-video tracking smoke harness.",
            "Run T0 with synthetic values immediately after any mapping code is implemented.",
            "Run T1/T2 on a known-good official runtime model before generating production claims for the new character.",
            "Update the character prompt template only if G0 candidates hide eyes/mouth or make tracking-required parts ambiguous.",
        ],
    }


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Face Tracking to Cubism Parameter Map",
        "",
        "## Summary",
        "",
        f"- status: `{payload['status']}`",
        f"- primary input provider: `{payload['input_provider']['primary']}`",
        f"- actual webcam smoke: `{payload['current_asset_readiness']['has_actual_webcam_tracking_smoke']}`",
        f"- required mappings: `{sum(1 for item in payload['mappings'] if item['priority'] == 'REQUIRED')}`",
        f"- optional mappings: `{sum(1 for item in payload['mappings'] if item['priority'] != 'REQUIRED')}`",
        "",
        "## Reference Sources",
        "",
    ]
    for source in payload["reference_sources"]:
        lines.append(f"- [{source['name']}]({source['url']}): {source['used_for']}")
    lines += [
        "",
        "## Current Readiness",
        "",
        "| Item | Value |",
        "|---|---|",
        f"| tracking-friendly parameter floor | `{payload['current_asset_readiness']['has_tracking_friendly_parameter_floor']}` |",
        f"| actual webcam tracking smoke | `{payload['current_asset_readiness']['has_actual_webcam_tracking_smoke']}` |",
        f"| prompt mode | `{payload['current_asset_readiness']['prompt_template_mode']}` |",
        f"| params without direct mapping | `{', '.join(payload['current_asset_readiness']['params_without_direct_mapping']) or 'none'}` |",
        "",
        "## Mapping Table",
        "",
        "| Input | Cubism Parameter | Output Range | Formula | Priority | QA |",
        "|---|---|---|---|---|---|",
    ]
    for item in payload["mappings"]:
        lines.append(
            f"| `{item['tracking_input']}` | `{item['cubism_parameter']}` | "
            f"`{item['output_range']}` | `{item['formula']}` | `{item['priority']}` | {item['qa_probe']} |"
        )
    lines += [
        "",
        "## Calibration Policy",
        "",
    ]
    for key, value in payload["calibration_policy"].items():
        lines.append(f"- `{key}`: {value}")
    lines += [
        "",
        "## Runtime Ownership Policy",
        "",
        "- Tracking controls: `" + "`, `".join(payload["runtime_priority_policy"]["tracking_controls"]) + "`",
        "- Physics controls: `" + "`, `".join(payload["runtime_priority_policy"]["physics_controls"]) + "`",
        "- Idle controls: `" + "`, `".join(payload["runtime_priority_policy"]["idle_controls"]) + "`",
        f"- Risk: {payload['runtime_priority_policy']['risk_note']}",
        "",
        "## Pre-Character Generation Requirements",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["pre_character_generation_requirements"])
    lines += [
        "",
        "## Smoke Test Plan",
        "",
        "| Test | Goal | Pass |",
        "|---|---|---|",
    ]
    for item in payload["smoke_test_plan"]:
        lines.append(f"| `{item['id']}` | {item['goal']} | {item['pass']} |")
    lines += [
        "",
        "## Next Actions",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["next_actions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    production = load_json(args.production_spec)
    part_spec = load_json(args.part_spec)
    prompt_template = load_json(args.prompt_template)
    runtime_metadata = load_json(args.runtime_metadata)
    payload = build_payload(
        production,
        part_spec,
        prompt_template,
        runtime_metadata,
        {
            "production_spec": args.production_spec,
            "part_spec": args.part_spec,
            "prompt_template": args.prompt_template,
            "runtime_metadata": args.runtime_metadata,
        },
    )
    out_json = args.out_dir / "face_tracking_to_cubism_parameter_map.json"
    out_md = args.out_dir / "face_tracking_to_cubism_parameter_map.md"
    write_json(out_json, payload)
    write_md(out_md, payload)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "json": rel(out_json),
                "markdown": rel(out_md),
                "mapping_count": len(payload["mappings"]),
                "actual_webcam_tracking_smoke": payload["current_asset_readiness"]["has_actual_webcam_tracking_smoke"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if payload["status"] in {"PASS", "WARN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

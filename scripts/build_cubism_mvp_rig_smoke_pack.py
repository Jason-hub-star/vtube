#!/usr/bin/env python3
"""Build Cubism FREE-limit audit and MVP rig smoke checklist."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from psd_tools import PSDImage


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT_ID = "imagen-live2d-001"


FREE_LIMITS = {
    "texture_files": 1,
    "texture_max_px": 2048,
    "art_meshes": 100,
    "parameters": 30,
    "deformers": 50,
    "parts_folders": 30,
}


PARAMETERS = [
    {
        "id": "ParamAngleX",
        "ko_name": "얼굴 좌우",
        "range": [-30, 30],
        "keyforms": [-30, 0, 30],
        "target_layers": ["face_base", "front_hair", "back_hair", "neck", "clothes"],
        "mvp_motion": "Head/face left-right drift only; keep deformation tiny because parts are forced-cleanup quality.",
    },
    {
        "id": "ParamEyeLOpen",
        "ko_name": "왼쪽 눈 깜빡임",
        "range": [0, 1],
        "keyforms": [0, 1],
        "target_layers": ["L_eye_white", "L_iris", "L_upper_lash"],
        "mvp_motion": "Simple lash/white/iris squash or visibility test, not final eyelid art.",
    },
    {
        "id": "ParamEyeROpen",
        "ko_name": "오른쪽 눈 깜빡임",
        "range": [0, 1],
        "keyforms": [0, 1],
        "target_layers": ["R_eye_white", "R_iris", "R_upper_lash"],
        "mvp_motion": "Simple lash/white/iris squash or visibility test, not final eyelid art.",
    },
    {
        "id": "ParamMouthOpenY",
        "ko_name": "입 열림",
        "range": [0, 1],
        "keyforms": [0, 1],
        "target_layers": ["mouth_line"],
        "mvp_motion": "Tiny open/close vertical scale; current mouth_line is forced O and needs later ROI cleanup.",
    },
    {
        "id": "ParamHairFrontSwing",
        "ko_name": "앞머리 흔들림",
        "range": [-1, 1],
        "keyforms": [-1, 0, 1],
        "target_layers": ["front_hair"],
        "mvp_motion": "Small horizontal/rotation sway; front_hair is forced canonical extraction.",
    },
    {
        "id": "ParamHairBackSwing",
        "ko_name": "뒷머리 흔들림",
        "range": [-1, 1],
        "keyforms": [-1, 0, 1],
        "target_layers": ["back_hair"],
        "mvp_motion": "Small lower-hair sway only.",
    },
    {
        "id": "ParamArmLSwing",
        "ko_name": "왼팔 흔들림",
        "range": [-1, 1],
        "keyforms": [-1, 0, 1],
        "target_layers": ["L_arm"],
        "mvp_motion": "Optional tiny sleeve/arm sway; this layer is forced from handwear-l.",
    },
    {
        "id": "ParamArmRSwing",
        "ko_name": "오른팔 흔들림",
        "range": [-1, 1],
        "keyforms": [-1, 0, 1],
        "target_layers": ["R_arm"],
        "mvp_motion": "Optional tiny sleeve/arm sway; this layer is forced from handwear-r.",
    },
]


DEFORMERS = [
    {"id": "Root", "type": "warp", "parent": None, "layers": []},
    {"id": "Head_X", "type": "warp", "parent": "Root", "layers": ["face_base", "front_hair", "back_hair", "L_ear_outer", "R_ear_outer"]},
    {"id": "Face_Base", "type": "warp", "parent": "Head_X", "layers": ["face_base", "neck"]},
    {"id": "Eye_L", "type": "warp", "parent": "Head_X", "layers": ["L_eye_white", "L_iris", "L_upper_lash"]},
    {"id": "Eye_R", "type": "warp", "parent": "Head_X", "layers": ["R_eye_white", "R_iris", "R_upper_lash"]},
    {"id": "Mouth", "type": "warp", "parent": "Head_X", "layers": ["mouth_line"]},
    {"id": "Hair_Front", "type": "rotation", "parent": "Head_X", "layers": ["front_hair"]},
    {"id": "Hair_Back", "type": "warp", "parent": "Root", "layers": ["back_hair"]},
    {"id": "Body", "type": "warp", "parent": "Root", "layers": ["clothes", "choker", "neck"]},
    {"id": "Arm_L", "type": "rotation", "parent": "Body", "layers": ["L_arm"]},
    {"id": "Arm_R", "type": "rotation", "parent": "Body", "layers": ["R_arm"]},
]


PART_FOLDERS = {
    "Hair": ["front_hair", "back_hair"],
    "Face": ["face_base", "neck"],
    "Eyes": ["L_eye_white", "R_eye_white", "L_iris", "R_iris", "L_upper_lash", "R_upper_lash", "L_brow", "R_brow"],
    "Mouth": ["mouth_line"],
    "Body": ["clothes", "L_arm", "R_arm"],
    "Accessory": ["choker", "L_ear_outer", "R_ear_outer"],
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def layer_entries(psd_path: Path) -> list[dict[str, Any]]:
    psd = PSDImage.open(psd_path)
    entries = []
    for layer in psd:
        bbox = layer.bbox
        if hasattr(bbox, "x1"):
            bbox_values = [bbox.x1, bbox.y1, bbox.x2, bbox.y2]
        else:
            bbox_values = list(bbox)
        entries.append(
            {
                "name": layer.name,
                "bbox": bbox_values,
                "visible": bool(layer.visible),
            }
        )
    return entries


def limit_status(name: str, used: int, limit: int) -> dict[str, Any]:
    return {
        "name": name,
        "used": used,
        "limit": limit,
        "remaining": limit - used,
        "within_limit": used <= limit,
    }


def build(args: argparse.Namespace) -> dict[str, Any]:
    exp = ROOT / "experiments" / args.experiment_id
    psd_path = exp / "import_ready.psd"
    if not psd_path.exists():
        raise FileNotFoundError(psd_path)

    psd = PSDImage.open(psd_path)
    layers = layer_entries(psd_path)
    layer_names = {layer["name"] for layer in layers}
    missing_parameter_targets = sorted(
        {
            target
            for parameter in PARAMETERS
            for target in parameter["target_layers"]
            if target not in layer_names
        }
    )
    missing_deformer_targets = sorted(
        {
            target
            for deformer in DEFORMERS
            for target in deformer["layers"]
            if target not in layer_names
        }
    )
    limits = [
        limit_status("texture_files", 1, FREE_LIMITS["texture_files"]),
        limit_status("texture_max_px", max(psd.size), FREE_LIMITS["texture_max_px"]),
        limit_status("art_meshes_planned_one_per_layer", len(layers), FREE_LIMITS["art_meshes"]),
        limit_status("parameters_planned", len(PARAMETERS), FREE_LIMITS["parameters"]),
        limit_status("deformers_planned", len(DEFORMERS), FREE_LIMITS["deformers"]),
        limit_status("parts_folders_planned", len(PART_FOLDERS), FREE_LIMITS["parts_folders"]),
    ]
    status = (
        "READY_FOR_MANUAL_CUBISM_MVP_RIG"
        if all(item["within_limit"] for item in limits) and not missing_parameter_targets and not missing_deformer_targets
        else "BLOCKED_RIG_SMOKE_PLAN"
    )

    payload = {
        "schema_version": 1,
        "experiment_id": args.experiment_id,
        "generated_at": now(),
        "status": status,
        "source_psd": str(psd_path.relative_to(ROOT)),
        "cubism_version_target": "Live2D Cubism Editor 5.3 FREE",
        "official_free_limit_reference": "https://www.live2d.com/en/cubism/comparison/",
        "psd": {
            "canvas_size": list(psd.size),
            "depth": psd.depth,
            "color_mode": str(psd.color_mode),
            "layer_count": len(layers),
            "layers": layers,
        },
        "free_limit_audit": limits,
        "part_folders": PART_FOLDERS,
        "deformer_plan": DEFORMERS,
        "parameter_plan": PARAMETERS,
        "manual_outputs_required": {
            "cmo3": str((exp / "cubism_mvp_rig.cmo3").relative_to(ROOT)),
            "moc3_export_dir": str((exp / "moc3_export_smoke").relative_to(ROOT)),
            "validation_report": str((exp / "reports" / "cubism_mvp_rig_validation.json").relative_to(ROOT)),
            "validation_template": str((exp / "reports" / "cubism_mvp_rig_validation_template.json").relative_to(ROOT)),
            "screenshot_dir": str((exp / "reports" / "cubism_mvp_rig_evidence").relative_to(ROOT)),
        },
        "missing_parameter_targets": missing_parameter_targets,
        "missing_deformer_targets": missing_deformer_targets,
        "quality_caveats": [
            "This is a forced-O MVP rig smoke, not final part purity approval.",
            "front_hair is forced from canonical dark-pixel extraction.",
            "L_arm and R_arm are forced from handwear-l/r outputs.",
            "mouth_line remains a likely cleanup target after rig smoke.",
        ],
    }
    save_json(exp / "reports" / "cubism_mvp_rig_smoke_plan.json", payload)
    save_json(exp / "reports" / "cubism_mvp_rig_validation_template.json", validation_template(payload))
    write_markdown(exp / "reports" / "cubism_mvp_rig_smoke_checklist.md", payload)
    return payload


def validation_template(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "experiment_id": payload["experiment_id"],
        "status": "PENDING_MANUAL_CUBISM_VALIDATION",
        "source_plan": f"experiments/{payload['experiment_id']}/reports/cubism_mvp_rig_smoke_plan.json",
        "cmo3_path": payload["manual_outputs_required"]["cmo3"],
        "moc3_export_dir": payload["manual_outputs_required"]["moc3_export_dir"],
        "checks": {
            "cmo3_saved": None,
            "artmesh_created_for_19_layers": None,
            "deformer_hierarchy_created": None,
            "mvp_parameters_created": None,
            "eye_keyforms_tested": None,
            "mouth_keyforms_tested": None,
            "hair_keyforms_tested": None,
            "arm_keyforms_tested": None,
            "draw_order_validated": None,
            "overhang_validated": None,
            "moc3_export_smoke": None,
        },
        "blocking_issues": [],
        "revise_issues": [],
        "evidence_screenshots": [],
        "notes": [
            "Fill this after the manual Cubism FREE MVP rig smoke.",
            "Use PASS, REVISE, FAIL, or BLOCKED values for each check.",
        ],
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Cubism MVP Rig Smoke Checklist",
        "",
        f"Generated: {payload['generated_at']}",
        f"Status: {payload['status']}",
        f"Source PSD: `{payload['source_psd']}`",
        "",
        "## FREE Limit Audit",
        "",
        "| Item | Used | Limit | Result |",
        "| --- | ---: | ---: | --- |",
    ]
    for item in payload["free_limit_audit"]:
        result = "PASS" if item["within_limit"] else "FAIL"
        lines.append(f"| `{item['name']}` | {item['used']} | {item['limit']} | {result} |")
    lines.extend(
        [
            "",
            "## Parts Folder Setup",
            "",
        ]
    )
    for folder, names in payload["part_folders"].items():
        lines.append(f"- `{folder}`: " + ", ".join(f"`{name}`" for name in names))
    lines.extend(["", "## Deformer Plan", ""])
    for deformer in payload["deformer_plan"]:
        layers = ", ".join(f"`{name}`" for name in deformer["layers"]) or "none"
        parent = deformer["parent"] or "none"
        lines.append(f"- `{deformer['id']}` ({deformer['type']}), parent `{parent}`: {layers}")
    lines.extend(["", "## MVP Parameter Keyforms", ""])
    for parameter in payload["parameter_plan"]:
        targets = ", ".join(f"`{name}`" for name in parameter["target_layers"])
        lines.append(
            f"- `{parameter['id']}` / {parameter['ko_name']}: range `{parameter['range']}`, "
            f"keyforms `{parameter['keyforms']}`, targets {targets}. {parameter['mvp_motion']}"
        )
    lines.extend(
        [
            "",
            "## Manual Cubism Steps",
            "",
            "1. Open `import_ready.psd` in Cubism Editor FREE.",
            "2. Confirm the Parts panel shows 19 individual layers, not one flattened image.",
            "3. Create one simple ArtMesh per visible layer; do not exceed one mesh per layer for this smoke.",
            "4. Create the deformer hierarchy above with small, conservative bounds.",
            "5. Add only the MVP parameters listed above.",
            "6. Keyform eyes, mouth, front/back hair, and optional arm swing with tiny movement.",
            "7. Run visual validation: draw order, overhang, eye visibility, mouth shape, and forced front_hair/arm artifacts.",
            "8. Save `cubism_mvp_rig.cmo3` in this experiment folder.",
            "9. If Cubism FREE allows export and validation is not blocking, export a `.moc3` smoke under `moc3_export_smoke/`.",
            "",
            "## Evidence To Capture",
            "",
            "- Screenshot of Parts panel after ArtMesh creation.",
            "- Screenshot of Deformer hierarchy.",
            "- Screenshot of each MVP parameter at neutral and extreme keyforms.",
            "- `reports/cubism_mvp_rig_validation.json` with PASS/REVISE/BLOCKED decisions.",
            "",
            "## Caveat",
            "",
            "This is a forced-O pipeline smoke. Passing this checklist proves the pipeline can reach a Cubism rigging surface, not that the avatar is production-quality.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-id", default=DEFAULT_EXPERIMENT_ID)
    args = parser.parse_args()
    payload = build(args)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "source_psd": payload["source_psd"],
                "layer_count": payload["psd"]["layer_count"],
                "parameters": len(payload["parameter_plan"]),
                "deformers": len(payload["deformer_plan"]),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Test Live2D model runtime readiness and view-clipping risk.

This does not render Cubism. It verifies the files needed for runtime motion,
uses py-moc3 for model structure/canvas info, scans motion/physics parameter
coverage, and checks texture alpha margins as a practical clipping warning.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
VENV_SITE = ROOT / ".venv-reference-models" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
if VENV_SITE.exists() and str(VENV_SITE) not in sys.path:
    sys.path.insert(0, str(VENV_SITE))

try:
    from moc3 import Moc3
except Exception:  # pragma: no cover
    Moc3 = None


WEB_RESOURCES = (
    ROOT
    / "experiments"
    / "reference-model-structure-001"
    / "official_github_samples"
    / "repos"
    / "live2d_cubism_web_samples"
    / "Samples"
    / "Resources"
)
OUT_DIR = ROOT / "experiments" / "live2d-owned-model-motion-preview-test-001" / "reports"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test Live2D model motion readiness and clipping risk.")
    parser.add_argument("--resources-dir", type=Path, default=WEB_RESOURCES)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--edge-margin-px", type=int, default=4)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def rel(path: Path | str | None) -> str | None:
    if not path:
        return None
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return p.resolve().as_posix()


def moc_summary(moc_path: Path) -> dict[str, Any]:
    if Moc3 is None or not moc_path.exists():
        return {"status": "MOC3_PARSER_MISSING"}
    try:
        moc = Moc3.from_file(str(moc_path))
        summary = moc.summary()
        canvas_match = re.search(r"Canvas:\s+([0-9.]+)x([0-9.]+)\s+ppu=([0-9.]+)", summary)
        warp_match = re.search(r"Warp:\s+([0-9]+)", summary)
        rotation_match = re.search(r"Rotation:\s+([0-9]+)", summary)
        def count(label: str) -> int:
            match = re.search(rf"{label}:\s+([0-9]+)", summary)
            return int(match.group(1)) if match else 0
        return {
            "status": "PASS",
            "canvas": {
                "width": float(canvas_match.group(1)) if canvas_match else None,
                "height": float(canvas_match.group(2)) if canvas_match else None,
                "pixels_per_unit": float(canvas_match.group(3)) if canvas_match else None,
            },
            "parts": count("Parts"),
            "art_meshes": count("Art Meshes"),
            "parameters": count("Parameters"),
            "warp_deformers": int(warp_match.group(1)) if warp_match else 0,
            "rotation_deformers": int(rotation_match.group(1)) if rotation_match else 0,
            "glues": count("Glues"),
            "summary_text": summary,
        }
    except Exception as error:
        return {"status": "FAIL", "error": str(error)}


def texture_alpha_report(texture_paths: list[Path], edge_margin_px: int) -> dict[str, Any]:
    textures = []
    risk = "PASS"
    for path in texture_paths:
        item: dict[str, Any] = {"path": rel(path), "exists": path.exists()}
        if not path.exists():
            item["status"] = "MISSING"
            risk = "FAIL"
            textures.append(item)
            continue
        with Image.open(path) as image:
            rgba = image.convert("RGBA")
            alpha = rgba.getchannel("A")
            bbox = alpha.getbbox()
            item["size"] = list(rgba.size)
            item["alpha_bbox"] = list(bbox) if bbox else None
            if not bbox:
                item["status"] = "EMPTY_ALPHA"
                risk = "FAIL"
            else:
                left, top, right, bottom = bbox
                width, height = rgba.size
                margins = {
                    "left": left,
                    "top": top,
                    "right": width - right,
                    "bottom": height - bottom,
                }
                item["edge_margins_px"] = margins
                item["touches_edge"] = any(value <= edge_margin_px for value in margins.values())
                item["status"] = "WARN_EDGE_ALPHA" if item["touches_edge"] else "PASS"
                if item["touches_edge"] and risk == "PASS":
                    risk = "WARN"
        textures.append(item)
    return {"status": risk, "textures": textures}


def motion_report(model_dir: Path, motions: dict[str, Any]) -> dict[str, Any]:
    motion_files = []
    parameter_ids = set()
    total_duration = 0.0
    missing = []
    for group, entries in motions.items():
        for entry in entries:
            path = model_dir / entry.get("File", "")
            item = {"group": group, "path": rel(path), "exists": path.exists()}
            if not path.exists():
                missing.append(str(path))
                motion_files.append(item)
                continue
            data = load_json(path)
            meta = data.get("Meta", {})
            params = {
                curve.get("Id")
                for curve in data.get("Curves", [])
                if curve.get("Target") == "Parameter" and curve.get("Id")
            }
            parameter_ids.update(params)
            total_duration += float(meta.get("Duration", 0) or 0)
            item.update(
                {
                    "duration": meta.get("Duration"),
                    "fps": meta.get("Fps"),
                    "curve_count": meta.get("CurveCount"),
                    "parameter_curve_count": len(params),
                    "parameter_ids": sorted(params),
                }
            )
            motion_files.append(item)
    status = "PASS" if motion_files and not missing and parameter_ids else "FAIL"
    return {
        "status": status,
        "motion_file_count": len(motion_files),
        "missing_motion_files": missing,
        "total_duration": round(total_duration, 3),
        "animated_parameter_count": len(parameter_ids),
        "animated_parameter_ids": sorted(parameter_ids),
        "motion_files": motion_files,
    }


def physics_report(model_dir: Path, physics_ref: str | None) -> dict[str, Any]:
    if not physics_ref:
        return {"status": "MISSING", "physics_groups": 0, "inputs": 0, "outputs": 0}
    path = model_dir / physics_ref
    if not path.exists():
        return {"status": "MISSING", "path": rel(path), "physics_groups": 0, "inputs": 0, "outputs": 0}
    data = load_json(path)
    meta = data.get("Meta", {})
    output_ids = set()
    input_ids = set()
    for setting in data.get("PhysicsSettings", []):
        for entry in setting.get("Input", []):
            source = entry.get("Source", {})
            if source.get("Id"):
                input_ids.add(source["Id"])
        for entry in setting.get("Output", []):
            dest = entry.get("Destination", {})
            if dest.get("Id"):
                output_ids.add(dest["Id"])
    return {
        "status": "PASS" if meta.get("PhysicsSettingCount", 0) else "FAIL",
        "path": rel(path),
        "physics_groups": int(meta.get("PhysicsSettingCount", 0) or 0),
        "inputs": int(meta.get("TotalInputCount", 0) or len(input_ids)),
        "outputs": int(meta.get("TotalOutputCount", 0) or len(output_ids)),
        "input_parameter_ids": sorted(input_ids),
        "output_parameter_ids": sorted(output_ids),
    }


def model_case(model3_path: Path, edge_margin_px: int) -> dict[str, Any]:
    model_dir = model3_path.parent
    data = load_json(model3_path)
    refs = data.get("FileReferences", {})
    moc = moc_summary(model_dir / refs.get("Moc", ""))
    textures = texture_alpha_report([model_dir / path for path in refs.get("Textures", [])], edge_margin_px)
    motions = motion_report(model_dir, refs.get("Motions", {}))
    physics = physics_report(model_dir, refs.get("Physics"))
    groups = {group.get("Name"): group.get("Ids", []) for group in data.get("Groups", [])}
    view_status = "PASS"
    if textures["status"] == "FAIL":
        view_status = "FAIL"
    elif textures["status"] == "WARN":
        view_status = "WARN"
    runtime_status = "PASS" if moc.get("status") == "PASS" and motions["status"] == "PASS" and physics["status"] == "PASS" else "FAIL"
    return {
        "model_name": model3_path.stem.replace(".model3", ""),
        "model3_path": rel(model3_path),
        "status": "PASS" if runtime_status == "PASS" and view_status in {"PASS", "WARN"} else "FAIL",
        "runtime_motion_status": runtime_status,
        "view_clipping_status": view_status,
        "view_clipping_interpretation": (
            "texture alpha reaches atlas edge; actual Cubism rendering should be visually checked"
            if view_status == "WARN"
            else "no texture-edge alpha warning found"
        ),
        "moc3": moc,
        "motion": motions,
        "physics": physics,
        "texture_alpha": textures,
        "groups": groups,
        "has_eye_blink_group": bool(groups.get("EyeBlink")),
        "has_lip_sync_group": "LipSync" in groups,
    }


def write_md(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Live2D 보유 모델 실제 테스트",
        "",
        f"- tested_models: `{report['summary']['tested_models']}`",
        f"- runtime_motion_pass: `{report['summary']['runtime_motion_pass']}`",
        f"- view_pass: `{report['summary']['view_pass']}`",
        f"- view_warn: `{report['summary']['view_warn']}`",
        f"- view_fail: `{report['summary']['view_fail']}`",
        "",
        "## 해석",
        "",
        "- 이 테스트는 `model3/moc3/motion3/physics3/texture` 파일 기준 검사입니다.",
        "- `view_warn`은 텍스처 alpha가 atlas 가장자리에 닿아 실제 player에서 잘림 여부를 눈으로 확인해야 한다는 뜻입니다.",
        "- 진짜 최종 판정은 Cubism Web player 렌더링 스크린샷/GIF가 필요합니다.",
        "",
        "## Models",
    ]
    for item in report["models"]:
        lines.append(
            f"- `{item['model_name']}` runtime `{item['runtime_motion_status']}` / view `{item['view_clipping_status']}` / "
            f"motions `{item['motion']['motion_file_count']}` / animated params `{item['motion']['animated_parameter_count']}` / "
            f"physics `{item['physics']['physics_groups']}`"
        )
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    args = parse_args()
    model_paths = sorted(args.resources_dir.glob("*/*model3.json"))
    models = [model_case(path, args.edge_margin_px) for path in model_paths]
    summary = {
        "tested_models": len(models),
        "runtime_motion_pass": sum(1 for item in models if item["runtime_motion_status"] == "PASS"),
        "view_pass": sum(1 for item in models if item["view_clipping_status"] == "PASS"),
        "view_warn": sum(1 for item in models if item["view_clipping_status"] == "WARN"),
        "view_fail": sum(1 for item in models if item["view_clipping_status"] == "FAIL"),
    }
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "resources_dir": rel(args.resources_dir),
        "edge_margin_px": args.edge_margin_px,
        "summary": summary,
        "models": models,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "live2d_model_motion_view_test.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    write_md(report, args.out_dir / "live2d_model_motion_view_test.md")
    print(f"Wrote {(args.out_dir / 'live2d_model_motion_view_test.json').relative_to(ROOT)}")
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if summary["runtime_motion_pass"] == len(models) and summary["view_fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

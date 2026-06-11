#!/usr/bin/env python3
"""Build render manifests for strong official Live2D reference models."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "live2d-strong-model-pattern-001"
READINESS = ROOT / "experiments" / "live2d-owned-model-motion-readiness-001" / "reports" / "owned_model_motion_readiness.json"

PILOT_NAMES = {
    "haru_greeter_t05",
    "hiyori_pro_t11",
    "kei_vowels_pro_t02",
    "mao_pro_t06",
    "miku_sample_t05",
}

LEARNING_TARGETS = {
    "haru_greeter": "PSD/material split, receptionist avatar baseline, body and arm-safe greeting motions",
    "hiyori": "standard human avatar, head/body angle, hair skinning and physics",
    "kei": "mouth vowels, lip-sync parameter coverage, compact face motion",
    "mao": "rich face range, arms/accessories/effects, blend-shape-like expression breadth",
    "miku": "long hair and twin-tail physics/skinning baseline",
    "haruto": "paired SD avatar, motion baseline and PSD layering",
    "koharu": "paired SD avatar, expression effects and motion baseline",
    "miara": "draw order groups, full-body motion and effect-rich scene structure",
    "natori": "expression, pose, motion and physics baseline",
    "ren": "Cubism 5.3 rich drawing, offscreen/mask-style expression",
    "rice": "extended interpolation, inverted mask, side-view/special pose",
    "tsumiki": "eyelid clipping mask and SD avatar expression",
    "wanko": "non-human avatar, touch motion and accessory baseline",
    "epsilon": "simple standard reference with motion and physics",
    "chitose": "right-arm switching and handwave expression",
    "tororo_hijiki": "small non-human pair, simple physics and motion",
    "izumi": "source pose variants and opposite-facing motion reference",
    "shizuku": "older Cubism sample with dense deformers and motion",
    "unitychan": "eyelid clipping mask and SD character baseline",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness", type=Path, default=READINESS)
    parser.add_argument("--out-dir", type=Path, default=EXPERIMENT / "reports")
    parser.add_argument("--limit", type=int, default=20)
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


def resolve_report_paths(model: dict[str, Any]) -> dict[str, Any]:
    report_path = ROOT / str(model["report"])
    report = load_json(report_path)
    paths = report.get("local_paths") or {}

    def one(key: str) -> str | None:
        value = paths.get(key)
        if isinstance(value, dict):
            return value.get("path")
        if isinstance(value, str):
            return value
        return None

    def many(key: str) -> list[str]:
        value = paths.get(key)
        if isinstance(value, list):
            out = []
            for item in value:
                if isinstance(item, dict) and item.get("path"):
                    out.append(item["path"])
                elif isinstance(item, str):
                    out.append(item)
            return out
        if isinstance(value, dict) and value.get("path"):
            return [value["path"]]
        if isinstance(value, str):
            return [value]
        return []

    return {
        "cmo3": one("cmo3"),
        "moc3": one("moc3"),
        "model3_json": one("model3_json"),
        "physics3_json": one("physics3_json"),
        "cdi3_json": one("cdi3_json"),
        "pose3_json": one("pose3_json"),
        "motion3_json": many("motion3_json"),
        "exp3_json": many("exp3_json"),
        "psd": many("psd"),
    }


def safe_id(model_id: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in model_id).strip("_").lower()


def make_entry(model: dict[str, Any], rank: int) -> dict[str, Any]:
    paths = resolve_report_paths(model)
    missing = []
    for key in ("model3_json", "moc3", "cmo3", "physics3_json"):
        path = paths.get(key)
        if not path or not (ROOT / path).exists():
            missing.append(key)
    if not paths.get("motion3_json"):
        missing.append("motion3_json")
    return {
        "rank": rank,
        "id": model["id"],
        "safe_id": safe_id(model["id"]),
        "name": model["name"],
        "official_profile_key": model.get("official_profile_key"),
        "analysis_mode": model.get("analysis_mode"),
        "motion_score": model.get("motion_score"),
        "physics_groups": model.get("physics_groups"),
        "parameters": model.get("parameters"),
        "warp_deformers": model.get("warp_deformers"),
        "rotation_deformers": model.get("rotation_deformers"),
        "keyform_bindings": model.get("keyform_bindings"),
        "expected_learning_target": LEARNING_TARGETS.get(model.get("official_profile_key"), "reference structure and motion pattern"),
        "local_paths": paths,
        "manifest_status": "PASS" if not missing else "FAIL",
        "missing_required_paths": missing,
        "source_report": model.get("report"),
    }


def build_manifest(kind: str, entries: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "kind": kind,
        "policy": {
            "asset_reuse": "local evidence only; do not copy official images/textures into our model",
            "goal": "success-pattern learning, not source-model reconstruction",
        },
        "summary": {
            "model_count": len(entries),
            "pass_count": sum(1 for item in entries if item["manifest_status"] == "PASS"),
            "fail_count": sum(1 for item in entries if item["manifest_status"] == "FAIL"),
        },
        "models": entries,
    }


def write_md(manifest: dict[str, Any], path: Path) -> None:
    lines = [
        f"# Live2D {manifest['kind']} Render Manifest",
        "",
        f"- model_count: `{manifest['summary']['model_count']}`",
        f"- pass/fail: `{manifest['summary']['pass_count']}/{manifest['summary']['fail_count']}`",
        "- policy: local evidence only; no source asset reuse",
        "",
        "| Rank | Model | Status | Target | Paths |",
        "|---:|---|---:|---|---:|",
    ]
    for item in manifest["models"]:
        path_ok = "OK" if item["manifest_status"] == "PASS" else ",".join(item["missing_required_paths"])
        lines.append(
            f"| {item['rank']} | `{item['name']}` | {item['manifest_status']} | "
            f"{item['expected_learning_target']} | {path_ok} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    readiness = load_json(args.readiness)
    strong = [
        item for item in readiness.get("models", [])
        if item.get("motion_readiness") == "STRONG_MOTION_REFERENCE"
    ]
    strong = sorted(strong, key=lambda item: (-int(item.get("motion_score", 0)), item.get("name") or ""))
    strong_entries = [make_entry(item, idx + 1) for idx, item in enumerate(strong[: args.limit])]
    pilot_by_name = {item["name"]: item for item in strong}
    pilot_order = ["haru_greeter_t05", "hiyori_pro_t11", "kei_vowels_pro_t02", "mao_pro_t06", "miku_sample_t05"]
    pilot_entries = [make_entry(pilot_by_name[name], idx + 1) for idx, name in enumerate(pilot_order)]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for filename, manifest in (
        ("pilot_render_manifest", build_manifest("pilot", pilot_entries)),
        ("strong20_render_manifest", build_manifest("strong20", strong_entries)),
    ):
        write_json(args.out_dir / f"{filename}.json", manifest)
        write_md(manifest, args.out_dir / f"{filename}.md")
    print(json.dumps({
        "pilot": len(pilot_entries),
        "strong20": len(strong_entries),
        "out_dir": rel(args.out_dir),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

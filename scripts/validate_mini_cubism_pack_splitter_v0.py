#!/usr/bin/env python3
"""Validate Mini Cubism pack-splitter-v0 bootstrap/probe outputs."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = ROOT / "experiments/mini-cubism-pack-splitter-v0-001"
REQUIRED_PACKS = {"base_mannequin", "hair_pack", "outfit_pack", "accessory_pack", "keypose_asset_pack"}
REQUIRED_MODELS = {"layerd", "birefnet", "birefnet_hr", "birefnet_matting", "sam2_roi", "fashion_segformer", "anime_instance"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"missing JSON: {path}")
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def image_ok(path: Path) -> tuple[bool, str | None]:
    if not path.exists():
        return False, "missing_file"
    image = Image.open(path).convert("RGBA")
    if image.size != (2048, 2048):
        return False, f"wrong_size:{image.size}"
    if image.getchannel("A").getbbox() is None:
        return False, "empty_alpha"
    return True, None


def validate(exp: Path) -> dict[str, Any]:
    manifest = load_json(exp / "pack_splitter_manifest.json")
    probe = load_json(exp / "reports" / "hf_probe_report.json")
    packs = set(manifest.get("packs", {}))
    model_ids = {item.get("id") for item in manifest.get("model_candidates", [])}
    failures: dict[str, Any] = {}
    if not REQUIRED_PACKS.issubset(packs):
        failures["missing_packs"] = sorted(REQUIRED_PACKS - packs)
    if not REQUIRED_MODELS.issubset(model_ids):
        failures["missing_models"] = sorted(REQUIRED_MODELS - model_ids)

    source_failures = []
    for pack_id, pack in manifest.get("packs", {}).items():
        ok, reason = image_ok(Path(pack["source"]))
        if not ok:
            source_failures.append({"pack_id": pack_id, "reason": reason, "source": pack["source"]})
    if source_failures:
        failures["source_image_failures"] = source_failures

    candidates = probe.get("candidates", [])
    if len(candidates) < manifest.get("qa_thresholds", {}).get("minimum_candidate_parts", 24):
        failures["too_few_candidates"] = {"actual": len(candidates)}
    candidate_models = {item.get("model_id") for item in candidates}
    if not REQUIRED_MODELS.issubset(candidate_models):
        failures["missing_candidate_models"] = sorted(REQUIRED_MODELS - candidate_models)

    candidate_file_failures = []
    for item in candidates:
        ok, reason = image_ok(Path(item["output_path"]))
        if not ok and item.get("derivation_mode") != "skipped_non_outfit_pack":
            candidate_file_failures.append({"candidate_id": item.get("candidate_id"), "reason": reason})
    if candidate_file_failures:
        failures["candidate_file_failures"] = candidate_file_failures[:20]

    for sheet in ["model_comparison_contact_sheet.png", "pack_problem_contact_sheet.png"]:
        path = exp / "reports" / sheet
        if not path.exists() or path.stat().st_size == 0:
            failures.setdefault("missing_contact_sheets", []).append(str(path))

    project = exp / "mini_cubism_project_pack_v0"
    if project.exists():
        failures["project_promotion_violation"] = f"{project} exists before QA PASS"

    actual_hf_count = int(probe.get("actual_hf_inference_count", 0))
    status = "PASS_WITH_LOCAL_ADAPTER_PROBE" if not failures and actual_hf_count == 0 else "PASS" if not failures else "FAIL"
    action_counts = Counter(item.get("status") for item in candidates)
    report = {
        "schema_version": 1,
        "validated_at": now(),
        "experiment": str(exp),
        "status": status,
        "checks": {
            "required_packs_present": REQUIRED_PACKS.issubset(packs),
            "required_models_present": REQUIRED_MODELS.issubset(model_ids),
            "candidate_outputs_present": "candidate_file_failures" not in failures,
            "contact_sheets_present": "missing_contact_sheets" not in failures,
            "project_promotion_blocked": "project_promotion_violation" not in failures,
            "actual_hf_inference_present": actual_hf_count > 0,
        },
        "counts": {
            "packs": len(packs),
            "candidates": len(candidates),
            "actual_hf_inference": actual_hf_count,
            "candidate_status": dict(action_counts),
        },
        "failures": failures,
        "outputs": {
            "hf_probe_report": str(exp / "reports" / "hf_probe_report.json"),
            "model_comparison_contact_sheet": str(exp / "reports" / "model_comparison_contact_sheet.png"),
            "pack_problem_contact_sheet": str(exp / "reports" / "pack_problem_contact_sheet.png"),
        },
        "interpretation": [
            "PASS_WITH_LOCAL_ADAPTER_PROBE means the pack pipeline is operational but real HF inference has not run.",
            "Do not promote to final Mini Cubism project until actual model probes and visual QA pass.",
        ],
    }
    write_json(exp / "reports" / "pack_splitter_qa_report.json", report)
    summary = [
        "# Mini Cubism Pack Splitter v0 Review Summary",
        "",
        f"- Status: {status}",
        f"- Packs: {len(packs)}",
        f"- Candidate outputs: {len(candidates)}",
        f"- Actual HF inference outputs: {actual_hf_count}",
        f"- Candidate status: {dict(action_counts)}",
        "",
        "## Next Automatic Action",
        "",
    ]
    if actual_hf_count == 0:
        summary.append("- Run the same probe with actual LayerD/BiRefNet/SAM2 inference enabled before treating masks as model evidence.")
    if failures:
        summary.append("- Fix validation failures before any project promotion.")
    else:
        summary.append("- Use the model comparison contact sheet to choose which real HF adapter to implement first.")
    (exp / "reports" / "review_summary.md").write_text("\n".join(summary) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Mini Cubism pack-splitter-v0 experiment.")
    parser.add_argument("--experiment", default=str(DEFAULT_EXPERIMENT))
    args = parser.parse_args()
    report = validate(Path(args.experiment).resolve())
    print(json.dumps({"ok": report["status"].startswith("PASS"), "status": report["status"], "counts": report["counts"], "failures": report["failures"], "report": str(Path(args.experiment).resolve() / "reports" / "pack_splitter_qa_report.json")}, ensure_ascii=False, indent=2))
    return 0 if report["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())

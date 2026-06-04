#!/usr/bin/env python3
"""Build a gated PSD candidate from human-approved See-through layers."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from cubism_material_pack import psd_metadata, write_layered_psd


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "see-through-layer-decomp-001"
MANIFEST_PATH = EXP / "layer_manifest.json"
REVIEW_PATH = EXP / "reports" / "part_visual_review.json"
CANDIDATE_DIR = EXP / "psd_candidate_layers"
PSD_PATH = EXP / "import_ready_candidate.psd"
READY_PATH = EXP / "import_ready.psd"
REPORT_PATH = EXP / "reports" / "psd_candidate_gate_report.json"
QA_PATH = EXP / "qa_report.md"
HANDOFF_PATH = EXP / "rigger_handoff.md"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        if default is None:
            raise FileNotFoundError(path)
        return default
    return json.loads(path.read_text())


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def accepted_layers(manifest: dict, reviews: dict) -> tuple[list[dict], list[dict]]:
    accepted = []
    excluded = []
    for layer in manifest.get("layers", []):
        part_id = layer["layer_name"]
        verdict = reviews.get(part_id, {}).get("verdict", "UNREVIEWED")
        reason = {
            "part_id": part_id,
            "original_part_id": layer.get("original_part_id"),
            "raw_tag": layer.get("raw_tag"),
            "verdict": verdict,
            "production_candidate": bool(layer.get("production_candidate")),
            "source_path": layer.get("output_path"),
        }
        if verdict == "O" and layer.get("production_candidate"):
            accepted.append(layer)
        else:
            excluded.append(reason)
    return accepted, excluded


def copy_candidate_layers(layers: list[dict]) -> list[dict]:
    if CANDIDATE_DIR.exists():
        shutil.rmtree(CANDIDATE_DIR)
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    copied = []
    for layer in sorted(layers, key=lambda item: item["draw_order"]):
        original = layer.get("original_part_id") or layer["layer_name"].removeprefix("seethrough__")
        dst = CANDIDATE_DIR / f"{original}.png"
        shutil.copy2(layer["output_path"], dst)
        entry = dict(layer)
        entry["layer_name"] = original
        entry["output_path"] = str(dst)
        entry["relative_output_path"] = str(dst.relative_to(EXP))
        entry["include_in_import_psd"] = True
        entry["status"] = "O"
        copied.append(entry)
    return copied


def write_docs(report: dict) -> None:
    gate_note = report["cubism_gate_note"]
    QA_PATH.write_text(
        "\n".join(
            [
                "# See-through PSD Candidate QA",
                "",
                f"Generated: {report['generated_at']}",
                f"Status: {report['status']}",
                "",
                "## Gate",
                "",
                "- Only `O` See-through candidates with `production_candidate=true` are eligible.",
                "- Raw See-through output is never trusted as production by itself.",
                "- Cubism Editor actual import is still required.",
                "",
                f"- Accepted layers: {report['accepted_layer_count']}",
                f"- Excluded layers: {report['excluded_layer_count']}",
                "",
                "## PSD Metadata",
                "",
                "```json",
                json.dumps(report["psd_metadata"], indent=2),
                "```",
                "",
                gate_note,
                "",
            ]
        )
        + "\n"
    )
    HANDOFF_PATH.write_text(
        "\n".join(
            [
                "# See-through Cubism Handoff",
                "",
                f"Generated: {report['generated_at']}",
                f"Status: {report['status']}",
                "",
                "## Files",
                "",
                "- Candidate PSD: `import_ready_candidate.psd`",
                "- Candidate layers: `psd_candidate_layers/`",
                "- Visual review: `reports/part_visual_review.json`",
                "- Gate report: `reports/psd_candidate_gate_report.json`",
                "",
                "## Cubism Smoke Requirement",
                "",
                "Create `reports/cubism_import_smoke.json` after opening the PSD in Cubism Editor:",
                "",
                "```json",
                '{ "cubism_import_success": true, "layers_flattened": false, "notes": "Layer list visible." }',
                "```",
                "",
            ]
        )
        + "\n"
    )


def build(args: argparse.Namespace) -> dict:
    manifest = load_json(MANIFEST_PATH, {"layers": []})
    reviews = load_json(REVIEW_PATH, {"reviews": {}}).get("reviews", {})
    accepted, excluded = accepted_layers(manifest, reviews)
    if PSD_PATH.exists():
        PSD_PATH.unlink()
    if READY_PATH.exists() and not args.keep_ready:
        READY_PATH.unlink()
    copied = copy_candidate_layers(accepted) if accepted else []
    writer = None
    status = "BLOCKED_NO_O_LAYERS"
    if copied:
        writer = write_layered_psd(PSD_PATH, copied)
        status = "PSD_CANDIDATE_PENDING_CUBISM_IMPORT"
    smoke_path = EXP / "reports" / "cubism_import_smoke.json"
    smoke = load_json(smoke_path, {}) if smoke_path.exists() else {}
    cubism_pass = bool(smoke.get("cubism_import_success")) and not bool(smoke.get("layers_flattened"))
    if cubism_pass and PSD_PATH.exists() and args.promote:
        shutil.copy2(PSD_PATH, READY_PATH)
        status = "PASS_WITH_CUBISM_IMPORT"
    report = {
        "schema_version": 1,
        "experiment_id": "see-through-layer-decomp-001",
        "generated_at": now(),
        "status": status,
        "source_manifest": str(MANIFEST_PATH.relative_to(ROOT)),
        "source_review": str(REVIEW_PATH.relative_to(ROOT)),
        "gate": {
            "accepted_verdict": "O",
            "require_production_candidate": True,
            "excluded_verdicts": ["X", "REVISE", "REFERENCE_ONLY", "UNREVIEWED"],
        },
        "accepted_layer_count": len(copied),
        "excluded_layer_count": len(excluded),
        "accepted_layers": [
            {
                "part_id": layer["layer_name"],
                "raw_tag": layer.get("raw_tag"),
                "output_path": layer["output_path"],
                "draw_order": layer["draw_order"],
            }
            for layer in copied
        ],
        "excluded_layers": excluded,
        "psd_writer": writer,
        "psd_candidate": str(PSD_PATH.relative_to(ROOT)),
        "import_ready_psd": str(READY_PATH.relative_to(ROOT)),
        "psd_metadata": psd_metadata(PSD_PATH),
        "cubism_import_smoke": smoke or None,
        "cubism_gate_note": (
            "Cubism Editor actual import has passed and import_ready.psd may be trusted."
            if status == "PASS_WITH_CUBISM_IMPORT"
            else "Cubism Editor actual import is still required before accepting this See-through PSD."
        ),
    }
    save_json(REPORT_PATH, report)
    write_docs(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Build gated See-through PSD candidate")
    parser.add_argument("--promote", action="store_true")
    parser.add_argument("--keep-ready", action="store_true")
    args = parser.parse_args()
    report = build(args)
    print(json.dumps({"status": report["status"], "accepted_layer_count": report["accepted_layer_count"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

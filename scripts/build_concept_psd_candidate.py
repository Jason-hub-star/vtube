#!/usr/bin/env python3
"""Build a gated PSD candidate for concept-regeneration-001.

Only human-approved `O` parts are eligible. `X`, `REVISE`, `REFERENCE_ONLY`, and
unreviewed parts are excluded from the PSD candidate.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from cubism_material_pack import psd_metadata, write_layered_psd


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "concept-regeneration-001"
MANIFEST_PATH = EXP / "layer_manifest.json"
REVIEW_PATH = EXP / "reports" / "part_visual_review.json"
CANDIDATE_DIR = EXP / "psd_candidate_layers"
PSD_PATH = EXP / "import_ready_candidate.psd"
READY_PATH = EXP / "import_ready.psd"
REPORT_PATH = EXP / "reports" / "psd_candidate_gate_report.json"
QA_PATH = EXP / "qa_report.md"
HANDOFF_PATH = EXP / "rigger_handoff.md"


def load_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        if default is None:
            raise FileNotFoundError(path)
        return default
    return json.loads(path.read_text())


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def review_verdicts() -> dict[str, dict]:
    return load_json(REVIEW_PATH, {"reviews": {}}).get("reviews", {})


def source_layer_path(layer: dict) -> Path:
    return Path(layer["output_path"])


def accepted_layers(manifest: dict, reviews: dict[str, dict]) -> tuple[list[dict], list[dict]]:
    accepted = []
    rejected = []
    for layer in manifest.get("layers", []):
        part_id = layer["layer_name"]
        review = reviews.get(part_id, {})
        verdict = review.get("verdict", "UNREVIEWED")
        reason = {
            "part_id": part_id,
            "original_part_id": layer.get("original_part_id", part_id),
            "ko_name": layer.get("ko_name", part_id),
            "verdict": verdict,
            "include_in_import_psd": bool(layer.get("include_in_import_psd")),
            "source_path": layer.get("output_path"),
        }
        if verdict == "O" and layer.get("include_in_import_psd"):
            accepted.append(layer)
        else:
            rejected.append(reason)
    return accepted, rejected


def copy_candidate_layers(layers: list[dict]) -> list[dict]:
    if CANDIDATE_DIR.exists():
        shutil.rmtree(CANDIDATE_DIR)
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    copied = []
    for layer in sorted(layers, key=lambda item: item["draw_order"]):
        original_part_id = layer.get("original_part_id", layer["layer_name"])
        dst = CANDIDATE_DIR / f"{original_part_id}.png"
        shutil.copy2(source_layer_path(layer), dst)
        copied_layer = dict(layer)
        copied_layer["layer_name"] = original_part_id
        copied_layer["output_path"] = str(dst)
        copied_layer["relative_output_path"] = str(dst.relative_to(EXP))
        copied_layer["status"] = "O"
        copied_layer["include_in_import_psd"] = True
        copied.append(copied_layer)
    return copied


def write_handoff(report: dict) -> None:
    text = f"""# White Wolf Goth Cubism Handoff

Generated: {report['generated_at']}
Status: {report['status']}

## Gate Rule

Only parts with human verdict `O` are eligible for `import_ready_candidate.psd`.
`X`, `REVISE`, `REFERENCE_ONLY`, and unreviewed parts are excluded.

## Files

- Candidate PSD: `import_ready_candidate.psd`
- Candidate PNG layers: `psd_candidate_layers/`
- Gate report: `reports/psd_candidate_gate_report.json`
- Visual review: `reports/part_visual_review.json`
- AI fix queue: `reports/ai_fix_queue.json`

## Current Result

- Accepted layer count: {report['accepted_layer_count']}
- Excluded layer count: {report['excluded_layer_count']}
- PSD candidate exists: {report['psd_metadata'].get('exists')}

## Cubism Import Smoke

If `import_ready_candidate.psd` exists, open it in Live2D Cubism Editor 5.3 and
record `reports/cubism_import_smoke.json`:

```json
{{
  "cubism_import_success": true,
  "layers_flattened": false,
  "reviewer": "name",
  "notes": "Layer list visible in Cubism Editor."
}}
```

Do not promote `import_ready.psd` until this smoke passes.
"""
    HANDOFF_PATH.write_text(text)


def write_qa(report: dict) -> None:
    lines = [
        "# White Wolf Goth PSD Candidate QA",
        "",
        f"Generated: {report['generated_at']}",
        f"Status: {report['status']}",
        "",
        "## Gate",
        "",
        "- Only `O` parts are eligible.",
        "- `X`, `REVISE`, `REFERENCE_ONLY`, and unreviewed parts are excluded.",
        "",
        "## Counts",
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
        "## Cubism Import Gate",
        "",
        report["cubism_gate_note"],
        "",
    ]
    QA_PATH.write_text("\n".join(lines))


def build(args: argparse.Namespace) -> dict:
    manifest = load_json(MANIFEST_PATH)
    reviews = review_verdicts()
    accepted, rejected = accepted_layers(manifest, reviews)

    if PSD_PATH.exists():
        PSD_PATH.unlink()
    if READY_PATH.exists() and not args.keep_ready:
        READY_PATH.unlink()

    copied_layers = copy_candidate_layers(accepted) if accepted else []
    writer = None
    status = "BLOCKED_NO_O_LAYERS"
    if copied_layers:
        writer = write_layered_psd(PSD_PATH, copied_layers)
        status = "PSD_CANDIDATE_PENDING_CUBISM_IMPORT"

    smoke_path = EXP / "reports" / "cubism_import_smoke.json"
    smoke = load_json(smoke_path, {}) if smoke_path.exists() else {}
    cubism_pass = bool(smoke.get("cubism_import_success")) and not bool(smoke.get("layers_flattened"))
    if cubism_pass and PSD_PATH.exists() and args.promote:
        shutil.copy2(PSD_PATH, READY_PATH)
        status = "PASS_WITH_CUBISM_IMPORT"

    report = {
        "schema_version": 1,
        "experiment_id": "concept-regeneration-001",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "source_manifest": str(MANIFEST_PATH.relative_to(ROOT)),
        "source_review": str(REVIEW_PATH.relative_to(ROOT)),
        "gate": {
            "accepted_verdict": "O",
            "excluded_verdicts": ["X", "REVISE", "REFERENCE_ONLY", "UNREVIEWED"],
            "require_include_in_import_psd": True,
        },
        "accepted_layer_count": len(copied_layers),
        "excluded_layer_count": len(rejected),
        "accepted_layers": [
            {
                "part_id": layer["layer_name"],
                "original_part_id": layer.get("original_part_id", layer["layer_name"]),
                "ko_name": layer.get("ko_name", layer["layer_name"]),
                "output_path": layer["output_path"],
                "draw_order": layer["draw_order"],
            }
            for layer in copied_layers
        ],
        "excluded_layers": rejected,
        "psd_writer": writer,
        "psd_candidate": str(PSD_PATH.relative_to(ROOT)),
        "import_ready_psd": str(READY_PATH.relative_to(ROOT)),
        "psd_metadata": psd_metadata(PSD_PATH),
        "cubism_import_smoke": smoke or None,
        "cubism_gate_note": (
            "Cubism Editor actual import has passed and import_ready.psd may be trusted."
            if status == "PASS_WITH_CUBISM_IMPORT"
            else "Cubism Editor actual import is still required before this concept pack can be accepted."
        ),
    }
    save_json(REPORT_PATH, report)
    write_qa(report)
    write_handoff(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Build gated concept PSD candidate")
    parser.add_argument("--promote", action="store_true", help="Promote candidate to import_ready.psd when Cubism smoke passes")
    parser.add_argument("--keep-ready", action="store_true", help="Do not delete existing import_ready.psd before build")
    args = parser.parse_args()
    report = build(args)
    print(json.dumps({
        "status": report["status"],
        "accepted_layer_count": report["accepted_layer_count"],
        "excluded_layer_count": report["excluded_layer_count"],
        "psd_metadata": report["psd_metadata"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

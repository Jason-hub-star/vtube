#!/usr/bin/env python3
"""Build a gated PSD candidate from human-approved See-through layers."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from cubism_material_pack import psd_metadata, write_layered_psd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT_ID = "see-through-layer-decomp-001"


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


ROLE_DRAW_ORDER = {
    "back_hair": 100,
    "neck_underpaint": 190,
    "neck": 200,
    "clothes": 210,
    "arm": 220,
    "face": 300,
    "mouth_line": 410,
    "eye_white": 500,
    "iris": 510,
    "upper_lash": 530,
    "lower_lash": 531,
    "brow": 540,
    "ears": 600,
    "front_hair": 700,
}


def effective_draw_order(layer: dict) -> int:
    original = layer.get("original_part_id") or layer.get("layer_name", "")
    if original in ROLE_DRAW_ORDER:
        return ROLE_DRAW_ORDER[original]
    for suffix, order in ROLE_DRAW_ORDER.items():
        if str(original).endswith(f"_{suffix}") or str(original) == suffix:
            return order
    return int(layer.get("draw_order") or 9999)


def candidate_priority(layer: dict) -> tuple[int, int]:
    raw_tag = str(layer.get("raw_tag") or "")
    layer_name = str(layer.get("layer_name") or "")
    if raw_tag.startswith("manual_mask:") or "manual__" in layer_name:
        source_rank = 0
    elif raw_tag.startswith("cleanup:") or raw_tag.startswith("roi_cleanup:") or "clean__" in layer_name or "roi__" in layer_name:
        source_rank = 1
    else:
        source_rank = 2
    return source_rank, -effective_draw_order(layer)


def accepted_layers(manifest: dict, reviews: dict) -> tuple[list[dict], list[dict]]:
    accepted_by_part = {}
    excluded = []
    for layer in manifest.get("layers", []):
        part_id = layer["layer_name"]
        original = layer.get("original_part_id") or layer["layer_name"].removeprefix("seethrough__")
        verdict = reviews.get(part_id, {}).get("verdict", "UNREVIEWED")
        reason = {
            "part_id": part_id,
            "original_part_id": original,
            "raw_tag": layer.get("raw_tag"),
            "verdict": verdict,
            "production_candidate": bool(layer.get("production_candidate")),
            "source_path": layer.get("output_path"),
        }
        if verdict == "O" and layer.get("production_candidate"):
            current = accepted_by_part.get(original)
            if current and candidate_priority(layer) >= candidate_priority(current):
                excluded.append({**reason, "exclude_reason": "duplicate_lower_priority_candidate"})
                continue
            if current:
                excluded.append(
                    {
                        "part_id": current["layer_name"],
                        "original_part_id": original,
                        "raw_tag": current.get("raw_tag"),
                        "verdict": "O",
                        "production_candidate": True,
                        "source_path": current.get("output_path"),
                        "exclude_reason": "duplicate_lower_priority_candidate",
                    }
                )
            accepted_by_part[original] = layer
        else:
            excluded.append(reason)
    return list(accepted_by_part.values()), excluded


def copy_candidate_layers(layers: list[dict]) -> list[dict]:
    global CANDIDATE_DIR, EXP
    if CANDIDATE_DIR.exists():
        shutil.rmtree(CANDIDATE_DIR)
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    copied = []
    for layer in sorted(layers, key=effective_draw_order):
        original = layer.get("original_part_id") or layer["layer_name"].removeprefix("seethrough__")
        dst = CANDIDATE_DIR / f"{original}.png"
        copy_with_alpha_floor(Path(layer["output_path"]), dst)
        entry = dict(layer)
        entry["layer_name"] = original
        entry["output_path"] = str(dst)
        entry["relative_output_path"] = str(dst.relative_to(EXP))
        entry["include_in_import_psd"] = True
        entry["status"] = "O"
        entry["draw_order"] = effective_draw_order(entry)
        copied.append(entry)
    return copied


def copy_with_alpha_floor(src: Path, dst: Path, floor: int = 10) -> None:
    img = Image.open(src).convert("RGBA")
    alpha = img.getchannel("A")
    alpha = alpha.point(lambda value: 0 if value <= floor else value)
    img.putalpha(alpha)
    img.save(dst)


def write_docs(report: dict) -> None:
    global QA_PATH, HANDOFF_PATH
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


def configure_paths(experiment_id: str) -> None:
    global EXP, MANIFEST_PATH, REVIEW_PATH, CANDIDATE_DIR, PSD_PATH, READY_PATH, REPORT_PATH, QA_PATH, HANDOFF_PATH
    EXP = ROOT / "experiments" / experiment_id
    MANIFEST_PATH = EXP / "layer_manifest.json"
    REVIEW_PATH = EXP / "reports" / "part_visual_review.json"
    CANDIDATE_DIR = EXP / "psd_candidate_layers"
    PSD_PATH = EXP / "import_ready_candidate.psd"
    READY_PATH = EXP / "import_ready.psd"
    REPORT_PATH = EXP / "reports" / "psd_candidate_gate_report.json"
    QA_PATH = EXP / "reports" / "psd_candidate_qa.md"
    HANDOFF_PATH = EXP / "rigger_handoff.md"


def build(args: argparse.Namespace) -> dict:
    configure_paths(args.experiment_id)
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
        "experiment_id": args.experiment_id,
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
    parser.add_argument("--experiment-id", default=DEFAULT_EXPERIMENT_ID)
    parser.add_argument("--promote", action="store_true")
    parser.add_argument("--keep-ready", action="store_true")
    args = parser.parse_args()
    report = build(args)
    print(json.dumps({"status": report["status"], "accepted_layer_count": report["accepted_layer_count"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

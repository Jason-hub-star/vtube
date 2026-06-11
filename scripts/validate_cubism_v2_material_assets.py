#!/usr/bin/env python3
"""Validate the Cubism v2 material asset draft."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from cubism_v2_material_asset_lib import (
    CANVAS,
    CONTACT_SHEET,
    LAYER_MANIFEST_PATH,
    MANIFEST_PATH,
    PSD_CANDIDATE,
    VALIDATION_JSON,
    VALIDATION_MD,
    ROOT,
    alpha_coverage,
    bbox_from_alpha,
    load_json,
    psd_metadata,
    rel,
    save_json,
)


def validate() -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    if not MANIFEST_PATH.exists():
        errors.append("material_asset_manifest.json missing")
        manifest = {"layers": []}
    else:
        manifest = load_json(MANIFEST_PATH)

    layers = manifest.get("layers", [])
    generated = [entry for entry in layers if entry.get("include_in_import_psd")]
    merged = [entry for entry in layers if not entry.get("include_in_import_psd")]
    if len(layers) != 64:
        errors.append(f"taxonomy accounted count must be 64, got {len(layers)}")
    if len(generated) != 62:
        errors.append(f"generated/import layer count must be 62, got {len(generated)}")
    if len(merged) != 2:
        errors.append(f"merged metadata count must be 2, got {len(merged)}")

    seen = set()
    empty_alpha: list[str] = []
    wrong_canvas: list[str] = []
    missing_png: list[str] = []
    for entry in generated:
        name = entry["layer_name"]
        if name in seen:
            errors.append(f"duplicate layer name: {name}")
        seen.add(name)
        path = ROOT / entry["output_path"]
        if not path.exists():
            missing_png.append(entry["part_id"])
            continue
        img = Image.open(path)
        if img.size != CANVAS:
            wrong_canvas.append(entry["part_id"])
        bbox = bbox_from_alpha(path)
        if not bbox:
            empty_alpha.append(entry["part_id"])
        elif alpha_coverage(path, bbox) <= 0:
            empty_alpha.append(entry["part_id"])
        if not entry.get("draw_order_band"):
            errors.append(f"{entry['part_id']}: missing draw_order_band")

    if missing_png:
        errors.append(f"missing PNG layers: {missing_png}")
    if wrong_canvas:
        errors.append(f"wrong canvas layers: {wrong_canvas}")
    if empty_alpha:
        errors.append(f"empty alpha layers: {empty_alpha}")

    for entry in merged:
        if not entry.get("merged_into"):
            errors.append(f"{entry['part_id']}: merged metadata missing merged_into")

    orders = [entry["draw_order"] for entry in generated]
    if orders != sorted(orders):
        errors.append("generated layer draw order is not ascending")

    psd_meta = psd_metadata(PSD_CANDIDATE)
    if not psd_meta.get("exists"):
        errors.append("import_ready_candidate.psd missing")
    else:
        for key, expected in [("width", 2048), ("height", 2048), ("depth", 8), ("channels", 3)]:
            if psd_meta.get(key) != expected:
                errors.append(f"PSD {key} expected {expected}, got {psd_meta.get(key)}")
        if psd_meta.get("layer_count") != 62:
            errors.append(f"PSD layer_count expected 62, got {psd_meta.get('layer_count')}")

    if not CONTACT_SHEET.exists():
        errors.append("material_contact_sheet.png missing")

    risk_candidates = [
        entry["part_id"]
        for entry in layers
        if entry.get("risk_tags")
        or entry.get("feasibility") in {"DIRECT_VISIBLE_RISK", "DERIVED_KEYPOSE_REQUIRED", "UNDERPAINT_REQUIRED"}
    ]
    status = "PASS_MATERIAL_ASSET_DRAFT_READY" if not errors else "FAIL_MATERIAL_ASSET_DRAFT"
    report = {
        "schema_version": 1,
        "status": status,
        "manifest": rel(MANIFEST_PATH),
        "layer_manifest": rel(LAYER_MANIFEST_PATH),
        "contact_sheet": rel(CONTACT_SHEET),
        "psd_candidate": rel(PSD_CANDIDATE),
        "summary": {
            "taxonomy_parts_accounted": len(layers),
            "generated_png_layers": len(generated),
            "merged_metadata_entries": len(merged),
            "risk_or_review_candidates": len(risk_candidates),
            "critical_missing_count": len(errors),
            "warning_count": len(warnings),
        },
        "psd_metadata": psd_meta,
        "errors": errors,
        "warnings": warnings,
        "risk_or_review_candidates": risk_candidates,
        "next_gate": "Cubism Editor import smoke; do not promote to import_ready.psd until real import passes.",
    }
    save_json(VALIDATION_JSON, report)
    VALIDATION_MD.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION_MD.write_text(
        "\n".join(
            [
                "# Cubism v2 Material Asset Validation",
                "",
                f"- status: `{status}`",
                f"- generated PNG layers: `{len(generated)}`",
                f"- merged metadata entries: `{len(merged)}`",
                f"- PSD layer count: `{psd_meta.get('layer_count')}`",
                f"- contact sheet: `{rel(CONTACT_SHEET)}`",
                f"- critical missing count: `{len(errors)}`",
                "",
                "## Errors",
                "",
                "\n".join(f"- {error}" for error in errors) if errors else "_없음_",
                "",
                "## Next Gate",
                "",
                report["next_gate"],
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report


def main() -> None:
    report = validate()
    print(report["status"])
    print(VALIDATION_JSON)
    if report["status"].startswith("FAIL"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

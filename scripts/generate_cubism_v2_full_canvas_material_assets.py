#!/usr/bin/env python3
"""Generate full-canvas Cubism v2 material assets from the manifest."""

from __future__ import annotations

from pathlib import Path

from cubism_v2_material_asset_lib import (
    LAYER_MANIFEST_PATH,
    MANIFEST_PATH,
    REPORTS,
    ROOT,
    VALIDATION_JSON,
    create_subject_rgba,
    load_json,
    now_iso,
    rel,
    save_json,
    write_layer_entry_image,
    write_psd_candidate,
)


def main() -> None:
    if not MANIFEST_PATH.exists():
        raise SystemExit("material manifest missing. Run scripts/build_cubism_v2_material_asset_manifest.py first.")

    manifest = load_json(MANIFEST_PATH)
    src = create_subject_rgba()
    updated_layers = []
    generated_count = 0
    merged_count = 0
    failures: list[str] = []

    for entry in manifest["layers"]:
        if entry.get("source_type") == "MERGED_METADATA":
            merged_count += 1
            updated_layers.append(entry)
            continue
        try:
            updated = write_layer_entry_image(entry, src)
            generated_count += 1
            updated_layers.append(updated)
        except Exception as exc:  # noqa: BLE001 - report per-layer failure for QA
            entry["generated"] = False
            entry["status"] = "FAIL_GENERATION"
            entry["failure_reason"] = str(exc)
            failures.append(f"{entry['part_id']}: {exc}")
            updated_layers.append(entry)

    manifest["generated_at"] = now_iso()
    manifest["status"] = "PASS_ASSETS_GENERATED" if not failures else "FAIL_ASSET_GENERATION"
    manifest["layers"] = updated_layers
    manifest["summary"]["generated_layers"] = generated_count
    manifest["summary"]["merged_metadata"] = merged_count
    manifest["summary"]["generation_failures"] = len(failures)

    psd_report = {"status": "NOT_RUN"}
    if not failures:
        try:
            psd_report = {"status": "PASS_PSD_CANDIDATE_WRITTEN", **write_psd_candidate(updated_layers)}
        except Exception as exc:  # noqa: BLE001
            psd_report = {"status": "FAIL_PSD_CANDIDATE_WRITE", "error": str(exc)}
            manifest["status"] = "FAIL_PSD_CANDIDATE_WRITE"

    manifest["psd_candidate"] = psd_report
    save_json(MANIFEST_PATH, manifest)
    save_json(LAYER_MANIFEST_PATH, manifest)
    save_json(REPORTS / "material_asset_generation_report.json", {"status": manifest["status"], "failures": failures, "psd_candidate": psd_report})
    (REPORTS / "material_asset_generation_report.md").write_text(
        "\n".join(
            [
                "# Cubism v2 Material Asset Generation",
                "",
                f"- status: `{manifest['status']}`",
                f"- generated layers: `{generated_count}`",
                f"- merged metadata: `{merged_count}`",
                f"- failures: `{len(failures)}`",
                f"- psd status: `{psd_report['status']}`",
                f"- manifest: `{rel(MANIFEST_PATH)}`",
                "",
                "## Failures",
                "",
                "\n".join(f"- {item}" for item in failures) if failures else "_없음_",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(manifest["status"])
    print(f"generated_layers={generated_count} merged_metadata={merged_count}")
    print(f"psd_status={psd_report['status']}")
    if manifest["status"].startswith("FAIL"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

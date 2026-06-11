#!/usr/bin/env python3
"""Compare two CMO3 structure reports.

The reports are produced by scripts/inspect_cmo3_structure.mjs. This comparator
does not assume any character-specific part names; it compares structural counts
and discovered names from before/after reports.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


COUNT_PATHS = {
    "art_meshes": ("art_meshes", "count"),
    "parameters": ("parameters", "count"),
    "parts": ("parts", "count"),
    "warp_deformers": ("deformers", "warp_count"),
    "rotation_deformers": ("deformers", "rotation_count"),
    "keyform_grids": ("keyforms", "grid_count"),
    "keyform_bindings": ("keyforms", "binding_count"),
    "layers": ("layers", "count"),
}


NAME_PATHS = {
    "art_meshes": ("art_meshes", "names"),
    "parameters": ("parameters", "ids"),
    "parts": ("parts", "names"),
    "warp_deformers": ("deformers", "warp_names"),
    "rotation_deformers": ("deformers", "rotation_names"),
    "layers": ("layers", "names"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True, help="Before report JSON")
    parser.add_argument("--after", required=True, help="After/current report JSON")
    parser.add_argument("--out-json", help="Delta report JSON path")
    parser.add_argument("--out-md", help="Delta report Markdown path")
    parser.add_argument("--expect-warp-increase", action="store_true")
    parser.add_argument("--expect-rotation-increase", action="store_true")
    parser.add_argument("--expect-keyform-binding-increase", action="store_true")
    return parser.parse_args()


def load_json(path: str) -> dict[str, Any]:
    with Path(path).expanduser().resolve().open("r", encoding="utf-8") as f:
        return json.load(f)


def nested(data: dict[str, Any], path: tuple[str, ...], default: Any = None) -> Any:
    cur: Any = data
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def rel(path: str | Path) -> str:
    p = Path(path).expanduser().resolve()
    try:
        return str(p.relative_to(REPO_ROOT))
    except ValueError:
        return str(p)


def compare(before: dict[str, Any], after: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    counts: dict[str, dict[str, int]] = {}
    for key, path in COUNT_PATHS.items():
        b = int(nested(before, path, 0) or 0)
        a = int(nested(after, path, 0) or 0)
        counts[key] = {"before": b, "after": a, "delta": a - b}

    names: dict[str, dict[str, list[str]]] = {}
    for key, path in NAME_PATHS.items():
        b_names = set(nested(before, path, []) or [])
        a_names = set(nested(after, path, []) or [])
        names[key] = {
            "added": sorted(a_names - b_names),
            "removed": sorted(b_names - a_names),
            "unchanged_count": len(a_names & b_names),
        }

    checks = []

    def add_check(check_id: str, ok: bool, message: str) -> None:
        checks.append({"id": check_id, "status": "PASS" if ok else "FAIL", "message": message})

    if args.expect_warp_increase:
        d = counts["warp_deformers"]["delta"]
        add_check("expected_warp_deformer_increase", d > 0, f"warp deformer delta = {d}")
    if args.expect_rotation_increase:
        d = counts["rotation_deformers"]["delta"]
        add_check("expected_rotation_deformer_increase", d > 0, f"rotation deformer delta = {d}")
    if args.expect_keyform_binding_increase:
        d = counts["keyform_bindings"]["delta"]
        add_check("expected_keyform_binding_increase", d > 0, f"keyform binding delta = {d}")

    changed_keys = [key for key, item in counts.items() if item["delta"] != 0]
    changed_name_keys = [
        key for key, item in names.items() if item["added"] or item["removed"]
    ]
    checks_failed = any(c["status"] == "FAIL" for c in checks)
    if checks_failed:
        status = "FAIL_EXPECTATION_NOT_MET"
    elif changed_keys or changed_name_keys:
        status = "CHANGED"
    else:
        status = "NO_CHANGE"

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tool": "compare_cmo3_structure_reports.py",
        "status": status,
        "inputs": {
            "before": rel(args.before),
            "after": rel(args.after),
        },
        "count_deltas": counts,
        "name_deltas": names,
        "expectation_checks": checks,
        "interpretation": [
            "This compares CMO3 structure reports only.",
            "A positive deformer or keyform delta proves structure was saved, not that motion quality is good.",
            "Visual/runtime overhang validation remains separate.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    count_rows = "\n".join(
        f"| {key} | {v['before']} | {v['after']} | {v['delta']} |"
        for key, v in report["count_deltas"].items()
    )
    check_rows = "\n".join(
        f"| {c['id']} | {c['status']} | {c['message']} |"
        for c in report["expectation_checks"]
    ) or "| none | PASS | no explicit expectations were requested |"
    added_sections = []
    for key, item in report["name_deltas"].items():
        if item["added"] or item["removed"]:
            added_sections.append(
                f"### {key}\n\n"
                f"Added: {', '.join(f'`{x}`' for x in item['added']) or 'none'}\n\n"
                f"Removed: {', '.join(f'`{x}`' for x in item['removed']) or 'none'}\n"
            )
    name_delta_text = "\n".join(added_sections) if added_sections else "No name-level changes."
    return f"""# CMO3 Structure Delta Report

Generated: {report['generated_at']}

Status: **{report['status']}**

Before: `{report['inputs']['before']}`

After: `{report['inputs']['after']}`

## Count Deltas

| Item | Before | After | Delta |
|---|---:|---:|---:|
{count_rows}

## Expectation Checks

| Check | Status | Message |
|---|---:|---|
{check_rows}

## Name Deltas

{name_delta_text}

## Interpretation

- This proves saved structure changes only.
- It does not prove final visual motion quality.
- Runtime/render and Cubism visual overhang validation remain separate gates.
"""


def main() -> None:
    args = parse_args()
    before = load_json(args.before)
    after = load_json(args.after)
    report = compare(before, after, args)

    out_json = Path(args.out_json).expanduser().resolve() if args.out_json else None
    out_md = Path(args.out_md).expanduser().resolve() if args.out_md else None
    if out_json:
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if out_md:
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(markdown(report), encoding="utf-8")

    print(f"[cmo3-delta] {report['status']}")
    if out_json:
        print(f"[cmo3-delta] json: {out_json}")
    if out_md:
        print(f"[cmo3-delta] md:   {out_md}")
    if report["status"] == "FAIL_EXPECTATION_NOT_MET":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

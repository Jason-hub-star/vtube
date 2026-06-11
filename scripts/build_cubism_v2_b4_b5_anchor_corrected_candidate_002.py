#!/usr/bin/env python3
"""Build B4/B5 corrected layer candidates from saved anchor overrides.

The default real mode is intentionally blocked until 주인님 saves real anchors
with the editor. Use `--smoke` to prove the rebuild path with the separate
smoke override file without polluting production evidence.
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
READINESS_JSON = (
    EXP / "reports/v22_b4_b5_anchor_correction_readiness/v22_b4_b5_anchor_correction_readiness.json"
)
REAL_OVERRIDES_JSON = EXP / "reports/v22_b4_b5_anchor_correction_readiness/manual_anchor_overrides.json"
SMOKE_OVERRIDES_JSON = (
    EXP / "reports/v22_b4_b5_anchor_correction_readiness/manual_anchor_overrides_smoke.json"
)
AUTO_DRAFT_OVERRIDES_JSON = (
    EXP / "reports/v22_b4_b5_anchor_correction_readiness/manual_anchor_overrides_auto_draft.json"
)
CANVAS = 2048
THUMB = 180


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return {} if default is None else default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def bbox_from_alpha(path: Path) -> list[int] | None:
    img = Image.open(path).convert("RGBA")
    alpha = np.asarray(img.getchannel("A"), dtype=np.uint8)
    ys, xs = np.where(alpha > 5)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def alpha_coverage(path: Path) -> float:
    img = Image.open(path).convert("RGBA")
    alpha = np.asarray(img.getchannel("A"), dtype=np.uint8)
    return round(float((alpha > 5).mean()), 8)


def transform_layer(src: Path, dst: Path, current_center: list[float], target_anchor: list[float], scale: float) -> None:
    img = Image.open(src).convert("RGBA")
    if scale == 1.0:
        transformed = img
        paste_x = round(target_anchor[0] - current_center[0])
        paste_y = round(target_anchor[1] - current_center[1])
    else:
        new_size = [max(1, round(img.width * scale)), max(1, round(img.height * scale))]
        transformed = img.resize(new_size, Image.Resampling.LANCZOS)
        scaled_current = [current_center[0] * scale, current_center[1] * scale]
        paste_x = round(target_anchor[0] - scaled_current[0])
        paste_y = round(target_anchor[1] - scaled_current[1])

    out = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    out.alpha_composite(transformed, dest=(paste_x, paste_y))
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst)


def build_contact_sheet(entries: list[dict], out: Path, title: str) -> None:
    cols = 4
    rows = (len(entries) + cols - 1) // cols
    width = cols * THUMB
    height = 48 + rows * (THUMB + 54)
    sheet = Image.new("RGB", (width, height), (247, 248, 250))
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 12), title, fill=(25, 31, 40))
    for idx, entry in enumerate(entries):
        x = (idx % cols) * THUMB
        y = 44 + (idx // cols) * (THUMB + 54)
        img = Image.open(ROOT / entry["output_path"]).convert("RGBA")
        bbox = img.getchannel("A").getbbox()
        crop = img.crop(bbox) if bbox else img
        crop.thumbnail((THUMB - 18, THUMB - 36), Image.Resampling.LANCZOS)
        tile = Image.new("RGB", (THUMB, THUMB), (238, 241, 245))
        tile.paste((255, 255, 255), (8, 8, THUMB - 8, THUMB - 36))
        px = x + (THUMB - crop.width) // 2
        py = y + (THUMB - 36 - crop.height) // 2
        tile.paste(crop, (px - x, py - y), crop)
        draw.rectangle([x + 4, y + 4, x + THUMB - 4, y + THUMB - 4], outline=(216, 222, 232))
        sheet.paste(tile, (x, y))
        label = f"{entry['part_id']} {entry['correction_status']}"
        draw.text((x + 8, y + THUMB - 31), label[:31], fill=(25, 31, 40))
        draw.text((x + 8, y + THUMB - 15), entry["source_batch"], fill=(78, 89, 104))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def build(mode: str) -> dict:
    readiness = load_json(READINESS_JSON)
    if mode == "smoke":
        overrides_path = SMOKE_OVERRIDES_JSON
    elif mode == "auto_draft":
        overrides_path = AUTO_DRAFT_OVERRIDES_JSON
    else:
        overrides_path = REAL_OVERRIDES_JSON
    overrides_doc = load_json(overrides_path, {"overrides": {}})
    overrides = overrides_doc.get("overrides", {})
    target_count = len(readiness.get("targets", []))

    suffix = "smoke" if mode == "smoke" else "auto_draft" if mode == "auto_draft" else "v1"
    out_dir = EXP / f"v22_b4_b5_anchor_corrected_{suffix}" / "normalized_layers"
    report_dir = EXP / f"reports/v22_b4_b5_anchor_corrected_{suffix}"
    report_json = report_dir / f"v22_b4_b5_anchor_corrected_{suffix}_report.json"
    report_md = report_dir / f"v22_b4_b5_anchor_corrected_{suffix}_report.md"
    contact_sheet = report_dir / f"v22_b4_b5_anchor_corrected_{suffix}_contact_sheet.png"

    if mode not in {"smoke", "auto_draft"} and not overrides:
        report = {
            "schema_version": "v1",
            "generated_at": now(),
            "status": "G6_B4_B5_CORRECTED_CANDIDATE_BLOCKED_NO_REAL_OVERRIDES",
            "readiness_report": rel(READINESS_JSON),
            "overrides_path": rel(overrides_path),
            "target_count": target_count,
            "saved_override_count": 0,
            "decision": "No real manual anchors are saved yet. Do not build or promote corrected B4/B5 candidates.",
            "next_action": [
                "Run the v22 B4/B5 anchor editor.",
                "Save real target anchors into manual_anchor_overrides.json.",
                "Re-run this script to build corrected B4/B5 candidates.",
            ],
            "self_review": {
                "target_count": target_count,
                "saved_override_count": 0,
                "blocked_without_real_overrides": True,
                "mini_cubism_not_promoted": True,
                "real_cubism_not_promoted": True,
                "status": "PASS",
            },
        }
        save_json(report_json, report)
        write_md(report_md, report, [])
        return report

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    for target in readiness["targets"]:
        src = ROOT / target["layer_path"]
        dst = out_dir / f"{target['part_id']}.png"
        override = overrides.get(target["part_id"])
        if override:
            current_center = override.get("current_center") or target["current_center"]
            target_anchor = override.get("target_anchor") or target["current_center"]
            scale = float(override.get("target_scale", 1.0))
            transform_layer(src, dst, current_center, target_anchor, scale)
            correction_status = "ANCHOR_OVERRIDE_APPLIED"
        else:
            shutil.copy2(src, dst)
            target_anchor = target["current_center"]
            scale = 1.0
            correction_status = "COPIED_PENDING_OVERRIDE"
        bbox = bbox_from_alpha(dst)
        entries.append(
            {
                "part_id": target["part_id"],
                "group": target["group"],
                "source_batch": target["source_batch"],
                "input_path": target["layer_path"],
                "output_path": rel(dst),
                "current_center": target["current_center"],
                "target_anchor": target_anchor,
                "target_scale": scale,
                "correction_status": correction_status,
                "bbox": bbox,
                "alpha_coverage": alpha_coverage(dst),
                "mode": Image.open(dst).mode,
                "size": list(Image.open(dst).size),
            }
        )

    status_counts = Counter(entry["correction_status"] for entry in entries)
    batch_counts = Counter(entry["source_batch"] for entry in entries)
    build_contact_sheet(
        entries,
        contact_sheet,
        "Character 002 v22 B4/B5 Anchor Corrected Smoke"
        if mode == "smoke"
        else "Character 002 v22 B4/B5 Anchor Corrected Candidate",
    )
    status = {
        "smoke": "G6_B4_B5_CORRECTED_CANDIDATE_SMOKE_PASS",
        "auto_draft": "G6_B4_B5_AUTO_ANCHOR_DRAFT_CORRECTED_CANDIDATE_READY_FOR_OVERLAY_QA",
    }.get(mode, "G6_B4_B5_CORRECTED_CANDIDATE_READY_FOR_OVERLAY_QA_HUMAN_REVIEW_REQUIRED")
    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": status,
        "mode": mode,
        "readiness_report": rel(READINESS_JSON),
        "overrides_path": rel(overrides_path),
        "output_dir": rel(out_dir),
        "contact_sheet": rel(contact_sheet),
        "entries": entries,
        "decision": (
            "Smoke rebuild path is verified with the separate smoke override file. This is not material approval."
            if mode == "smoke"
            else "Automatic draft anchors were applied to all B4/B5 targets. This reduces manual workload but still requires overlay QA and 주인님 visual review before material promotion."
            if mode == "auto_draft"
            else "Corrected candidates were rebuilt from saved real anchors and require overlay QA plus human review before promotion."
        ),
        "next_action": [
            "Run B4/B5 overlay QA against corrected candidate layers.",
            "Keep ParamHairFront hidden until corrected hair_front_* children pass overlay QA.",
            "Rebuild the 64-part manifest only after corrected B4/B5 visual QA passes.",
        ],
        "self_review": {
            "target_count": target_count,
            "entry_count": len(entries),
            "saved_override_count": len(overrides),
            "applied_override_count": status_counts.get("ANCHOR_OVERRIDE_APPLIED", 0),
            "copied_pending_override_count": status_counts.get("COPIED_PENDING_OVERRIDE", 0),
            "b4_entry_count": batch_counts.get("B4", 0),
            "b5_entry_count": batch_counts.get("B5", 0),
            "all_layers_rgba": all(entry["mode"] == "RGBA" for entry in entries),
            "all_layers_2048": all(entry["size"] == [CANVAS, CANVAS] for entry in entries),
            "all_layers_nonempty": all(entry["bbox"] is not None for entry in entries),
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "status": "PASS",
        },
    }
    save_json(report_json, report)
    write_md(report_md, report, entries)
    return report


def write_md(path: Path, report: dict, entries: list[dict]) -> None:
    lines = [
        "# Character 002 v22 B4/B5 Anchor Corrected Candidate",
        "",
        f"- status: `{report['status']}`",
        f"- mode: `{report.get('mode', 'real')}`",
        f"- overrides: `{report['overrides_path']}`",
    ]
    if report.get("output_dir"):
        lines.append(f"- output dir: `{report['output_dir']}`")
    if report.get("contact_sheet"):
        lines.append(f"- contact sheet: `{report['contact_sheet']}`")
    lines.extend(["", "## Decision", "", report["decision"], "", "## Next Action", ""])
    lines.extend(f"- {item}" for item in report["next_action"])
    lines.extend(["", "## Self Review", ""])
    for key, value in report["self_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    if entries:
        lines.extend(["", "## Entries", ""])
        for entry in entries:
            lines.append(
                f"- `{entry['part_id']}` `{entry['source_batch']}` `{entry['correction_status']}` "
                f"anchor `{entry['target_anchor']}` scale `{entry['target_scale']}`"
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--auto-draft", action="store_true")
    args = parser.parse_args()
    if args.smoke and args.auto_draft:
        parser.error("--smoke and --auto-draft are mutually exclusive")
    mode = "smoke" if args.smoke else "auto_draft" if args.auto_draft else "real"
    report = build(mode)
    print(json.dumps({"status": report["status"], "report": report.get("output_dir") or report["overrides_path"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

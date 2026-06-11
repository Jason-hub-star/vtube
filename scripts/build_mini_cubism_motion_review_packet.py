#!/usr/bin/env python3
"""Build the Mini Cubism Physics v0.3 motion review packet."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


DEFAULT_SCENARIOS = ["angle_swing", "hair_settle", "mouth_talk", "eye_blink"]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def font(size: int) -> ImageFont.ImageFont:
    for candidate in [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/Library/Fonts/Arial.ttf",
    ]:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def thumb(path: Path, size: tuple[int, int]) -> Image.Image:
    canvas = Image.new("RGB", size, "#202124")
    if path.exists():
        image = Image.open(path).convert("RGB")
        image.thumbnail((size[0], size[1] - 34), Image.Resampling.LANCZOS)
        canvas.paste(image, ((size[0] - image.width) // 2, 0))
    else:
        draw = ImageDraw.Draw(canvas)
        draw.text((16, 16), "missing", fill="#ffffff", font=font(18))
    return canvas


def scenario_by_name(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {scenario["name"]: scenario for scenario in report.get("scenarios", [])}


def scenario_order(motion_report: dict[str, Any]) -> list[str]:
    scenarios = scenario_by_name(motion_report)
    order = ["angle_swing", "head_tilt", "hair_settle", "mouth_talk", "eye_blink"]
    selected = [name for name in order if name in scenarios]
    return selected or DEFAULT_SCENARIOS


def build_contact_sheet(motion_report: dict[str, Any], score_report: dict[str, Any], out_path: Path) -> None:
    scenarios = scenario_by_name(motion_report)
    ordered = scenario_order(motion_report)
    cell_w = 300
    cell_h = 260
    label_h = 52
    header_h = 64
    columns = ["state A", "state B", "state C"]
    sheet = Image.new("RGB", (cell_w * len(columns), header_h + (cell_h + label_h) * len(ordered)), "#f4f0e8")
    draw = ImageDraw.Draw(sheet)
    title_font = font(24)
    label_font = font(17)
    small_font = font(14)

    for col, label in enumerate(columns):
        x = col * cell_w
        draw.rectangle((x, 0, x + cell_w, header_h), fill="#202124")
        draw.text((x + 16, 18), label, fill="#ffffff", font=title_font)

    for row, scenario_name in enumerate(ordered):
        scenario = scenarios.get(scenario_name, {})
        frames = scenario.get("frames", [])
        if scenario_name in {"mouth_talk", "eye_blink"} and len(frames) >= 3:
            indexes = [0, 1, 2]
        else:
            indexes = [0, len(frames) // 2, len(frames) - 1] if frames else [0, 0, 0]
        y = header_h + row * (cell_h + label_h)
        for col, index in enumerate(indexes):
            x = col * cell_w
            frame = frames[index] if frames else {}
            image = thumb(Path(frame.get("screenshot", "__missing__")), (cell_w, cell_h))
            sheet.paste(image, (x, y))
            draw.rectangle((x, y + cell_h, x + cell_w, y + cell_h + label_h), fill="#ffffff")
            draw.text((x + 12, y + cell_h + 9), scenario_name, fill="#202124", font=label_font)
            draw.text((x + 170, y + cell_h + 12), f"frame {frame.get('index', '-')}", fill="#5f6368", font=small_font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def summary_text(motion_report: dict[str, Any], score_report: dict[str, Any], best_motion: Path) -> str:
    status = score_report.get("status", "UNKNOWN")
    physics_check = next((check for check in score_report.get("checks", []) if check.get("check") == "spring_damper_profiles_active_and_settle"), {})
    active = ", ".join(physics_check.get("active_profiles", [])) or "None"
    return f"""# Mini Cubism Motion Review

Generated: {now()}

## Recommended

Status: `{status}`

Best motion GIF: `{best_motion}`

Best project: `{motion_report.get("project")}`

Active physics profiles: {active}

Use this as the current Mini Cubism local motion evidence baseline if visual review does not find excessive motion or obvious art contamination.

## Evidence

- `angle_swing.gif`: head-driven delayed motion
- `head_tilt.gif`: tilt-driven head and hair motion
- `hair_settle.gif`: spring-damper settle proof
- `mouth_talk.gif`: closed/half/open mouth keypose gate
- `eye_blink.gif`: open/half/closed eye keypose proof

## Caveats

- This is local Mini Cubism preview evidence, not Cubism `.cmo3` or `.moc3` compatibility.
- Glue remains unimplemented until a real `CGlueSource` fixture is available.
- Generated or derived mouth/eye keypose shapes may need art refinement later.

## 주인님 Review Choices

- 유지
- 더 부드럽게
- 더 탄성 있게
- 너무 과함
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    run_root = Path(args.run).resolve()
    out_dir = Path(args.out).resolve()
    motion_dir = run_root / "motion_evidence"
    if not motion_dir.exists():
        motion_dir = Path(args.run).resolve()
    motion_report_path = motion_dir / "reports" / "motion_sweep_report.json"
    score_report_path = motion_dir / "reports" / "physics_score_report.json"
    if not motion_report_path.exists():
        raise SystemExit(f"missing motion_sweep_report.json: {motion_report_path}")
    if not score_report_path.exists():
        raise SystemExit(f"missing physics_score_report.json: {score_report_path}")
    motion_report = load_json(motion_report_path)
    score_report = load_json(score_report_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    contact_sheet = out_dir / "contact_sheet.png"
    build_contact_sheet(motion_report, score_report, contact_sheet)
    best_motion = out_dir / "best_motion.gif"
    source_best = motion_dir / "gifs" / "hair_settle.gif"
    if not source_best.exists():
        source_best = motion_dir / "gifs" / "angle_swing.gif"
    shutil.copy2(source_best, best_motion)

    summary_path = out_dir / "review_summary.md"
    summary_path.write_text(summary_text(motion_report, score_report, best_motion))
    packet = {
        "schema_version": 1,
        "generated_at": now(),
        "status": "PASS" if contact_sheet.exists() and best_motion.exists() and summary_path.exists() else "FAIL",
        "run": str(run_root),
        "motion_evidence": str(motion_dir),
        "best_project": motion_report.get("project"),
        "contact_sheet": str(contact_sheet),
        "best_motion": str(best_motion),
        "review_summary": str(summary_path),
    }
    packet_path = out_dir / "review_packet_report.json"
    write_json(packet_path, packet)
    print(json.dumps({"ok": packet["status"] == "PASS", "status": packet["status"], "report": str(packet_path)}, indent=2))
    return 0 if packet["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

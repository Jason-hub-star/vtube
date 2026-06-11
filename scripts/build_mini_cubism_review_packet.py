#!/usr/bin/env python3
"""Build a visual review packet for Mini Cubism auto-authoring runs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


POSE_ORDER = ["neutral", "angle_left", "angle_right", "mouth_open", "hair_swing"]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def find_pose(report: dict[str, Any], pose_name: str, viewport_name: str = "desktop") -> dict[str, Any] | None:
    for viewport in report.get("results", []):
        if viewport.get("viewport", {}).get("name") != viewport_name:
            continue
        for pose in viewport.get("poses", []):
            if pose.get("pose") == pose_name:
                return pose
    return None


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


def thumbnail(path: Path, width: int, height: int) -> Image.Image:
    if not path.exists():
        image = Image.new("RGB", (width, height), "#2b2d31")
        draw = ImageDraw.Draw(image)
        draw.text((20, 20), "missing screenshot", fill="#ffffff", font=font(18))
        return image
    image = Image.open(path).convert("RGB")
    image.thumbnail((width, height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (width, height), "#1f2125")
    canvas.paste(image, ((width - image.width) // 2, (height - image.height) // 2))
    return canvas


def build_contact_sheet(baseline: dict[str, Any] | None, best: dict[str, Any], out_path: Path) -> None:
    cell_w = 420
    cell_h = 320
    label_h = 44
    header_h = 70
    columns = [("Baseline", baseline), ("Best Candidate", best)]
    rows = POSE_ORDER
    sheet = Image.new("RGB", (cell_w * len(columns), header_h + (cell_h + label_h) * len(rows)), "#f4f0e8")
    draw = ImageDraw.Draw(sheet)
    title_font = font(28)
    label_font = font(18)
    small_font = font(15)

    for col, (label, _) in enumerate(columns):
        x = col * cell_w
        draw.rectangle((x, 0, x + cell_w, header_h), fill="#202124")
        draw.text((x + 18, 18), label, fill="#ffffff", font=title_font)

    for row_index, pose_name in enumerate(rows):
        y = header_h + row_index * (cell_h + label_h)
        for col, (_, report) in enumerate(columns):
            x = col * cell_w
            pose = find_pose(report, pose_name) if report else None
            screenshot = Path(pose["screenshot"]) if pose and pose.get("screenshot") else Path("__missing__")
            image = thumbnail(screenshot, cell_w, cell_h)
            sheet.paste(image, (x, y))
            verdict = pose.get("verdict", "MISSING") if pose else "MISSING"
            changed = pose.get("metrics", {}).get("changedRatio", 0) if pose else 0
            draw.rectangle((x, y + cell_h, x + cell_w, y + cell_h + label_h), fill="#ffffff")
            draw.text((x + 14, y + cell_h + 10), f"{pose_name} | {verdict}", fill="#202124", font=label_font)
            draw.text((x + 260, y + cell_h + 13), f"delta {changed:.4f}", fill="#5f6368", font=small_font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def markdown_summary(run_dir: Path, baseline: dict[str, Any] | None, score_report: dict[str, Any], best_report: dict[str, Any]) -> str:
    best_id = score_report.get("best_candidate_id", "unknown")
    best_score = best_report.get("score", 0)
    best_status = best_report.get("status", "UNKNOWN")
    failed = []
    for viewport in best_report.get("results", []):
        for pose in viewport.get("poses", []):
            if pose.get("verdict") != "PASS":
                failed.append(f"- {viewport['viewport']['name']} / {pose['pose']}: {pose['verdict']} ({'; '.join(pose.get('messages', []))})")
    failed_text = "\n".join(failed) if failed else "- None"
    baseline_status = baseline.get("status", "MISSING") if baseline else "MISSING"
    return f"""# Mini Cubism Auto Authoring Review

Generated: {now()}

## Recommended

Best candidate: `{best_id}`

Status: `{best_status}`

Score: `{best_score}`

Use this candidate as the next Mini Cubism local preview baseline unless visual review finds a clear issue.

## Baseline

Baseline pose sweep status: `{baseline_status}`

## Caveats

{failed_text}

## 주인님 Review Choices

- 유지: best candidate를 다음 baseline으로 사용
- 더 강하게: motion strength를 한 단계 올려 다음 후보 생성
- 더 약하게: motion strength를 한 단계 낮춰 다음 후보 생성
- 폐기: 현재 자동 authoring profile을 버리고 다른 튜닝 기준으로 재시도
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    run_dir = Path(args.run).resolve()
    out_dir = Path(args.out).resolve()
    baseline_path = run_dir / "baseline" / "reports" / "pose_sweep_report.json"
    score_path = run_dir / "reports" / "candidate_score_report.json"
    if not score_path.exists():
        raise SystemExit(f"missing candidate score report: {score_path}")
    baseline = load_json(baseline_path) if baseline_path.exists() else None
    score_report = load_json(score_path)
    best_id = score_report.get("best_candidate_id")
    best_ranked = next((item for item in score_report.get("ranked_candidates", []) if item.get("candidate_id") == best_id), None)
    if not best_ranked or not best_ranked.get("pose_sweep", {}).get("report"):
        raise SystemExit("best candidate pose sweep report is missing")
    best_report = load_json(Path(best_ranked["pose_sweep"]["report"]))

    out_dir.mkdir(parents=True, exist_ok=True)
    contact_sheet = out_dir / "contact_sheet.png"
    build_contact_sheet(baseline, best_report, contact_sheet)
    summary = markdown_summary(run_dir, baseline, score_report, best_report)
    summary_path = out_dir / "review_summary.md"
    summary_path.write_text(summary)
    packet = {
        "schema_version": 1,
        "generated_at": now(),
        "run_dir": str(run_dir),
        "best_candidate_id": best_id,
        "contact_sheet": str(contact_sheet),
        "review_summary": str(summary_path),
        "status": "PASS" if contact_sheet.exists() and summary_path.exists() else "FAIL",
    }
    packet_path = out_dir / "review_packet_report.json"
    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"ok": True, "report": str(packet_path), "contact_sheet": str(contact_sheet)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

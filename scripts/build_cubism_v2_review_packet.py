#!/usr/bin/env python3
"""Build compact human review packets for the Cubism v2 review app."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageSequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "review_app" / "review_manifest.json"
DEFAULT_OUT = ROOT / "experiments" / "cubism-v2-review-001" / "review_packet"

GATE_LABELS = {
    "g0_concept": "G0 캐릭터 고르기",
    "g1_part_taxonomy": "G1 파츠 확인",
    "g2_structure": "G2 구조 자동검사",
    "g3_motion_visual": "G3 움직임 확인",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Cubism v2 contact sheets and failure-only review packet.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--thumb-size", type=int, default=220)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def fs_path(asset_path: str | None) -> Path | None:
    if not asset_path:
        return None
    if asset_path.startswith("/assets/"):
        return ROOT / asset_path.removeprefix("/assets/")
    path = Path(asset_path)
    if path.is_absolute():
        return path
    return ROOT / path


def load_image(path: Path | None, size: int) -> Image.Image:
    if not path or not path.exists():
        image = Image.new("RGB", (size, size), "#f2f4f6")
        draw = ImageDraw.Draw(image)
        draw.text((18, size // 2 - 8), "이미지 없음", fill="#6b7684")
        return image
    with Image.open(path) as source:
        frame = next(ImageSequence.Iterator(source)).convert("RGBA")
        frame.thumbnail((size, size), Image.Resampling.LANCZOS)
        image = Image.new("RGBA", (size, size), "#ffffff")
        left = (size - frame.width) // 2
        top = (size - frame.height) // 2
        image.alpha_composite(frame, (left, top))
        return image.convert("RGB")


def font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def draw_label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, max_chars: int, fill: str = "#191f28") -> None:
    safe = text if len(text) <= max_chars else text[: max_chars - 1] + "…"
    draw.text(xy, safe, font=font(15), fill=fill)


def build_contact_sheet(items: list[dict[str, Any]], title: str, out_path: Path, thumb_size: int) -> None:
    cols = 4 if len(items) > 1 else 1
    rows = max(1, (len(items) + cols - 1) // cols)
    label_h = 58
    pad = 14
    header_h = 52
    width = cols * thumb_size + (cols + 1) * pad
    height = header_h + rows * (thumb_size + label_h) + (rows + 1) * pad
    sheet = Image.new("RGB", (width, height), "#f7f8fa")
    draw = ImageDraw.Draw(sheet)
    draw.text((pad, 16), title, font=font(22), fill="#191f28")

    for index, item in enumerate(items):
        col = index % cols
        row = index // cols
        x = pad + col * (thumb_size + pad)
        y = header_h + pad + row * (thumb_size + label_h)
        image_path = fs_path(item.get("image_path") or item.get("overlay_path") or item.get("canonical_path"))
        thumb = load_image(image_path, thumb_size)
        sheet.paste(thumb, (x, y))
        draw.rounded_rectangle((x, y, x + thumb_size, y + thumb_size), radius=8, outline="#e5e8eb", width=2)
        label = item.get("simple_label") or item.get("ko_name") or item.get("part_id", "")
        draw_label(draw, (x, y + thumb_size + 8), label, 18)
        draw_label(draw, (x, y + thumb_size + 30), item.get("part_id", ""), 22, "#6b7684")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def review_path(manifest: dict[str, Any]) -> Path:
    output = manifest.get("review_outputs", {}).get("part_visual_review")
    return ROOT / output if output else ROOT / "experiments" / manifest.get("experiment_id", "cubism-v2-review-001") / "reports" / "part_visual_review.json"


def failure_items(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    reviews = load_json(review_path(manifest)).get("reviews", {})
    all_items = [item for values in manifest.get("sections", {}).values() for item in values]
    by_id = {item.get("part_id"): item for item in all_items}
    failures = []
    for part_id, review in reviews.items():
        if review.get("verdict") in {"X", "REVISE"} and part_id in by_id:
            item = dict(by_id[part_id])
            item["review_verdict"] = review.get("verdict")
            item["issue_tags"] = review.get("issue_tags", [])
            item["human_note"] = review.get("human_note", "")
            failures.append(item)
    for item in all_items:
        summary = item.get("auto_check_summary") or {}
        if summary.get("status") in {"FAIL", "REVISE"} and item not in failures:
            clone = dict(item)
            clone["review_verdict"] = summary.get("status")
            clone["issue_tags"] = item.get("auto_issue_tags", [])
            clone["human_note"] = summary.get("message", "")
            failures.append(clone)
    return failures


def auto_checks(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    checks = []
    for section, items in manifest.get("sections", {}).items():
        for item in items:
            summary = item.get("auto_check_summary")
            if summary:
                checks.append(
                    {
                        "section": section,
                        "part_id": item.get("part_id"),
                        "status": summary.get("status"),
                        "message": summary.get("message"),
                        "checks": summary.get("checks", {}),
                        "source_reports": summary.get("source_reports", {}),
                    }
                )
    return checks


def write_markdown(manifest: dict[str, Any], packet: dict[str, Any], out_path: Path) -> None:
    lines = [
        "# Cubism v2 쉬운 검수 패킷",
        "",
        f"- tier: `{manifest.get('tier', 'v2_min')}`",
        f"- generated_at: `{packet['generated_at']}`",
        f"- 사람이 먼저 볼 것: gate별 contact sheet와 실패 후보 목록",
        "",
        "## Contact Sheets",
    ]
    for section, path in packet["contact_sheets"].items():
        lines.append(f"- {GATE_LABELS.get(section, section)}: `{path}`")
    lines.extend(["", "## Auto Checks"])
    if packet["auto_checks"]:
        for check in packet["auto_checks"]:
            lines.append(f"- {check['part_id']}: `{check.get('status')}` - {check.get('message')}")
    else:
        lines.append("- 자동검사 결과 없음")
    lines.extend(["", "## Failure Candidates"])
    if packet["failure_candidates"]:
        for item in packet["failure_candidates"]:
            label = item.get("simple_label") or item.get("ko_name") or item.get("part_id")
            tags = ", ".join(item.get("issue_tags", [])) or "태그 없음"
            lines.append(f"- {item.get('part_id')}: {label} / `{item.get('review_verdict')}` / {tags}")
    else:
        lines.append("- 실패 후보 없음")
    out_path.write_text("\n".join(lines) + "\n")


def main() -> int:
    args = parse_args()
    if not args.manifest.is_absolute():
        args.manifest = ROOT / args.manifest
    if not args.out.is_absolute():
        args.out = ROOT / args.out
    manifest = load_json(args.manifest)
    if not manifest:
        raise SystemExit(f"FAIL: manifest not found: {args.manifest}")

    args.out.mkdir(parents=True, exist_ok=True)
    contact_sheets: dict[str, str] = {}
    for section, items in manifest.get("sections", {}).items():
        if not items:
            continue
        out_path = args.out / f"{section}_contact_sheet.png"
        build_contact_sheet(items, GATE_LABELS.get(section, section), out_path, args.thumb_size)
        contact_sheets[section] = out_path.relative_to(ROOT).as_posix()

    failures = failure_items(manifest)
    failure_sheet = None
    if failures:
        failure_sheet_path = args.out / "failure_candidates_contact_sheet.png"
        build_contact_sheet(failures, "실패 후보만 보기", failure_sheet_path, args.thumb_size)
        failure_sheet = failure_sheet_path.relative_to(ROOT).as_posix()

    packet = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_manifest": args.manifest.relative_to(ROOT).as_posix(),
        "contact_sheets": contact_sheets,
        "failure_contact_sheet": failure_sheet,
        "auto_checks": auto_checks(manifest),
        "failure_candidates": failures,
    }
    (args.out / "review_packet.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n")
    write_markdown(manifest, packet, args.out / "review_packet.md")
    print(f"Wrote {args.out.relative_to(ROOT)}")
    print(json.dumps({"contact_sheets": len(contact_sheets), "failures": len(failures)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

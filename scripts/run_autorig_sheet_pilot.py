#!/usr/bin/env python3
"""AUTORIG 슬롯 시트 파일럿: 시트 1장을 생성→점유율 QA→결정론적 추출→배치→조립 합성.

이 파일럿이 검증하는 질문: "이미지 모델이 고정 슬롯 레이아웃을 지키는가?"
지키면 → 사후 추출(오염의 근원)이 사라진다. 안 지키면 → 슬롯당 1회 생성 폴백.

전 과정을 autorig_events로 기록하므로 관제탑(8095)에서 실시간 관람 가능.
마지막에 H1 게이트(스타일/조립 확인)를 띄우고 종료한다.

사용:
  python3 scripts/run_autorig_sheet_pilot.py \
    --spec experiments/autorig-template-001/reports/template_spec/autorig_template_spec.json \
    --sheet-id eye_small_01 --style-ref <reference png> \
    --out-dir experiments/autorig-template-001 [--skip-generate] [--no-gate]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from autorig_events import EventWriter  # noqa: E402
from lib.vtube_image import compose_layers, make_thumb  # noqa: E402
from lib.vtube_io import ROOT, load_json, now_iso, rel, write_json  # noqa: E402

BAND_SUFFIX_ORDER = {"back": 0, "mid": 1, "front": 2}
NEUTRAL_EXCLUDE_TOKENS = ("closed",)
ALPHA_D0, ALPHA_D1 = 70.0, 150.0  # 크로마 거리 → 알파 소프트 램프
MIN_CONTENT_RATIO, MAX_CONTENT_RATIO = 0.003, 0.85
BORDER_MARGIN = 6


def chroma_alpha(rgb: np.ndarray, chroma: tuple[int, int, int]) -> np.ndarray:
    dist = np.sqrt(((rgb.astype(np.float32) - np.array(chroma, dtype=np.float32)) ** 2).sum(axis=-1))
    return np.clip((dist - ALPHA_D0) / (ALPHA_D1 - ALPHA_D0), 0.0, 1.0)


def generate_sheet(prompt: str, style_ref: Path, out_path: Path, timeout: int = 600) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    full_prompt = (
        f"{prompt}\n\n"
        f"Use the image generation tool to create this exact 2048x2048 sheet and save the PNG to "
        f"{out_path} (overwrite if it exists). Do not create or modify any other files."
    )
    result = subprocess.run(
        [
            "codex", "exec", "-C", str(ROOT), "-s", "workspace-write", "--skip-git-repo-check",
            "-i", str(style_ref.resolve()), "--", full_prompt,
        ],
        timeout=timeout,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"codex exec 실패 (rc={result.returncode}): {result.stdout[-500:]} {result.stderr[-500:]}")
    if not out_path.exists():
        raise RuntimeError(f"codex가 시트를 저장하지 않았습니다: {out_path}")


def slot_occupancy(sheet_img: Image.Image, slot: dict, chroma: tuple[int, int, int]) -> dict:
    x0, y0, x1, y1 = slot["cell_px"]
    cell = np.asarray(sheet_img.crop((x0, y0, x1, y1)).convert("RGB"))
    alpha = chroma_alpha(cell, chroma)
    content = alpha > 0.5
    ratio = float(content.mean())
    border = np.zeros_like(content)
    m = BORDER_MARGIN
    border[:m, :] = content[:m, :]
    border[-m:, :] = content[-m:, :]
    border[:, :m] = content[:, :m]
    border[:, -m:] = content[:, -m:]
    issues = []
    if ratio < MIN_CONTENT_RATIO:
        issues.append("EMPTY_SLOT")
    if ratio > MAX_CONTENT_RATIO:
        issues.append("OVERFILLED")
    if border.any():
        issues.append("TOUCHES_BORDER")
    return {"part_id": slot["part_id"], "content_ratio": round(ratio, 5), "issues": issues, "ok": not issues}


def extract_and_place(sheet_img: Image.Image, slot: dict, chroma: tuple[int, int, int], canvas_size: int, out_path: Path) -> dict:
    x0, y0, x1, y1 = slot["cell_px"]
    cell_rgb = np.asarray(sheet_img.crop((x0, y0, x1, y1)).convert("RGB"))
    alpha = chroma_alpha(cell_rgb, chroma)
    mask = alpha > 0.5
    if not mask.any():
        return {"part_id": slot["part_id"], "status": "EMPTY"}
    ys, xs = np.where(mask)
    cx0, cy0, cx1, cy1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    rgba = np.dstack([cell_rgb, (alpha * 255).astype(np.uint8)])[cy0:cy1, cx0:cx1]
    part = Image.fromarray(rgba, "RGBA")
    tx0, ty0, tx1, ty1 = slot["target_bbox"]
    tw, th = max(tx1 - tx0, 4), max(ty1 - ty0, 4)
    scale = min(tw / part.width, th / part.height)
    new_size = (max(1, round(part.width * scale)), max(1, round(part.height * scale)))
    part = part.resize(new_size, Image.LANCZOS)
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    cx, cy = slot["target_center"]
    canvas.alpha_composite(part, (round(cx - part.width / 2), round(cy - part.height / 2)))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)
    return {
        "part_id": slot["part_id"],
        "status": "PLACED",
        "path": rel(out_path),
        "source_px": [int(cx1 - cx0), int(cy1 - cy0)],
        "placed_px": list(new_size),
        "scale": round(scale, 4),
    }


def assembly_order(slots: list[dict]) -> list[dict]:
    usable = [s for s in slots if not any(t in s["part_id"] for t in NEUTRAL_EXCLUDE_TOKENS)]
    return sorted(usable, key=lambda s: BAND_SUFFIX_ORDER.get(s["draw_order_band"].rsplit("_", 1)[-1], 1))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--sheet-id", required=True)
    parser.add_argument("--style-ref", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--skip-generate", action="store_true", help="기존 raw 시트로 추출만 재실행")
    parser.add_argument("--no-gate", action="store_true")
    args = parser.parse_args()

    spec = load_json(args.spec)
    sheet = next((s for s in spec["sheets"] if s["sheet_id"] == args.sheet_id), None)
    if sheet is None:
        raise SystemExit(f"sheet not found: {args.sheet_id}")
    chroma = tuple(int(spec["chroma"][i : i + 2], 16) for i in (1, 3, 5))
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    raw_path = out_dir / "raw_sheets" / f"{args.sheet_id}.png"
    layers_dir = out_dir / "normalized_layers" / args.sheet_id
    reports_dir = out_dir / "reports" / f"pilot_{args.sheet_id}"

    run_id = args.run_id or f"autorig-pilot-{args.sheet_id}-{int(time.time())}"
    ev = EventWriter(run_id)
    ev.run_started(f"AUTORIG 파일럿 — {args.sheet_id}", budget_seconds=3600, stages=["P0", "P1", "P2", "P4", "H1"])

    # P0
    ev.stage_started("P0", "스펙 로드")
    ev.log(f"{args.sheet_id}: 슬롯 {len(sheet['slots'])}개, 스타일 레퍼런스 {rel(args.style_ref)}")
    ev.stage_completed("P0")

    # P1 생성
    ev.stage_started("P1", "슬롯 시트 생성")
    if args.skip_generate and raw_path.exists():
        ev.log("기존 raw 시트 재사용 (--skip-generate)")
    else:
        ev.log("codex imagegen 호출 — 수 분 걸려요")
        generate_sheet(sheet["prompt"], args.style_ref, raw_path)
    sheet_img = Image.open(raw_path).convert("RGB")
    if sheet_img.size != (spec["canvas"], spec["canvas"]):
        ev.log(f"시트 크기 {sheet_img.size} → {spec['canvas']} 정규화", level="warn")
        sheet_img = sheet_img.resize((spec["canvas"], spec["canvas"]), Image.LANCZOS)
    art = ev.run_dir / "artifacts" / raw_path.name
    sheet_img.save(art)
    ev.artifact_created(f"artifacts/{raw_path.name}", label="raw 슬롯 시트", stage="P1")
    ev.stage_completed("P1")

    # P4 점유율 QA (생성 직후 — 실패면 추출 무의미)
    ev.stage_started("P4", "슬롯 점유율 QA")
    occupancy = [slot_occupancy(sheet_img, slot, chroma) for slot in sheet["slots"]]
    ok_count = sum(1 for o in occupancy if o["ok"])
    occupancy_pass = ok_count == len(occupancy)
    ev.qa_result(
        "슬롯 점유율", "PASS" if occupancy_pass else "FAIL",
        value=f"{ok_count}/{len(occupancy)}",
        detail=", ".join(f"{o['part_id']}:{'+'.join(o['issues'])}" for o in occupancy if not o["ok"])[:300],
        stage="P4",
    )
    ev.stage_completed("P4")

    # P2 추출·배치 (점유율과 무관하게 시도 — 부분 성공도 증거)
    ev.stage_started("P2", "결정론적 추출·배치")
    placements = []
    for slot in sheet["slots"]:
        result = extract_and_place(sheet_img, slot, chroma, spec["canvas"], layers_dir / f"{slot['part_id']}.png")
        placements.append(result)
    placed = [p for p in placements if p["status"] == "PLACED"]
    ev.log(f"배치 완료 {len(placed)}/{len(placements)}")
    ev.stage_completed("P2")

    # 조립 합성 (검수 단위 규칙)
    composites = {}
    groups = sorted({s["group"] for s in sheet["slots"]})
    for group in groups + ["__all__"]:
        slots = sheet["slots"] if group == "__all__" else [s for s in sheet["slots"] if s["group"] == group]
        ordered = assembly_order(slots)
        paths = [layers_dir / f"{s['part_id']}.png" for s in ordered if (layers_dir / f"{s['part_id']}.png").exists()]
        name = "assembly_all" if group == "__all__" else f"assembly_{group}"
        out = compose_layers(paths, reports_dir / f"{name}.png")
        if out:
            composites[name] = rel(out)
            art = ev.run_dir / "artifacts" / out.name
            make_thumb(out, art, size=1024, crop_alpha=True, margin=80)
            ev.artifact_created(f"artifacts/{out.name}", label=f"조립 합성 {name}", stage="P2")
    last_assembly = f"artifacts/assembly_all.png" if "assembly_all" in composites else ""

    report = {
        "schema_version": 1,
        "generated_at": now_iso(),
        "test_id": f"autorig_sheet_pilot_{args.sheet_id}",
        "status": "PASS_CANDIDATE_HUMAN_REVIEW_REQUIRED" if occupancy_pass else "SLOT_COMPLIANCE_FAIL",
        "sheet_id": args.sheet_id,
        "raw_sheet": rel(raw_path),
        "style_ref": rel(args.style_ref),
        "occupancy": occupancy,
        "occupancy_pass": occupancy_pass,
        "placements": placements,
        "composites": composites,
        "self_review": {
            "slots": len(sheet["slots"]),
            "occupancy_ok": ok_count,
            "placed": len(placed),
            "fallback_needed": not occupancy_pass,
        },
        "interpretation_ko": (
            "이미지 모델이 슬롯 레이아웃을 준수했습니다. 조립 합성을 보고 스타일/품질을 판정하세요."
            if occupancy_pass
            else "슬롯 위반이 있습니다. 위반 슬롯만 재생성하거나 슬롯당 1회 생성 폴백을 검토하세요."
        ),
    }
    write_json(reports_dir / "pilot_report.json", report)

    if not args.no_gate:
        ev.gate_waiting(
            "H1", "파일럿 시트 스타일/조립 확인이 필요해요",
            instructions="raw 시트와 조립 합성을 보고, 그림체가 캐릭터와 같고 조립이 자연스러운지 판정해주세요.",
            artifact=last_assembly,
        )
    ev.run_completed("PASS" if occupancy_pass else "FAIL")
    print(f"status={report['status']} occupancy={ok_count}/{len(occupancy)} placed={len(placed)}")
    print(f"report={rel(reports_dir / 'pilot_report.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

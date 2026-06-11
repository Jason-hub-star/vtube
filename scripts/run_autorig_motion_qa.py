#!/usr/bin/env python3
"""AUTORIG Motion QA: render sweeps for seam, blink, mouth, and hair physics."""
from __future__ import annotations
import argparse
import base64
import csv
import json
import math
import shutil
import socket
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, load_json, now_iso, rel, write_json  # noqa: E402
from lib.vtube_proc import terminate, wait_for_server  # noqa: E402
PLAYWRIGHT = ROOT / "experiments/live2d-strong-model-pattern-001/probe_sandbox/strong20/Samples/TypeScript/Demo/node_modules/playwright"
RUNNER_TEMPLATE = ROOT / "scripts/templates/autorig_motion_qa_runner.js"
BG = (32, 33, 36)
def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])
def node_bin() -> str:
    found = shutil.which("node")
    if not found:
        raise RuntimeError("node binary not found")
    return found
def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or (list(rows[0].keys()) if rows else ["empty"])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
def clamp_region(bbox: list[float], canvas: list[int], pad: int = 16, max_size: int = 96) -> dict[str, int]:
    x, y, w, h = [int(round(v)) for v in bbox]
    width, height = int(canvas[0]), int(canvas[1])
    cx, cy = x + w // 2, y + h // 2
    w = min(max_size - pad * 2, max(1, w))
    h = min(max_size - pad * 2, max(1, h))
    x, y = cx - w // 2, cy - h // 2
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(width, x + w + pad), min(height, y + h + pad)
    return {"x": x0, "y": y0, "w": max(1, x1 - x0), "h": max(1, y1 - y0)}
def union_bbox(parts: list[dict[str, Any]]) -> list[int]:
    boxes = [p.get("bbox") for p in parts if p.get("bbox")]
    if not boxes:
        return [0, 0, 64, 64]
    x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes)
    x1 = max(b[0] + b[2] for b in boxes); y1 = max(b[1] + b[3] for b in boxes)
    return [int(x0), int(y0), int(x1 - x0), int(y1 - y0)]
def resolve_parts(character: dict[str, Any], queries: list[str]) -> list[str]:
    ids = [p["id"] for p in character.get("parts", [])]
    out: list[str] = []
    for query in queries:
        if query in ids:
            out.append(query)
        else:
            out.extend(pid for pid in ids if query.lower() in pid.lower())
    return sorted(dict.fromkeys(out))
def named_regions(character: dict[str, Any], focus_parts: list[str]) -> list[dict[str, Any]]:
    canvas = character.get("canvas_size") or [2048, 2048]
    parts = character.get("parts", [])
    by_id = {p["id"]: p for p in parts}
    seam_ids = set(focus_parts)
    if any("neck" in item.lower() for item in focus_parts):
        seam_ids |= {"neck_under", "neck_skin", "clothes", "face_base", "shoulder_hair"}
    seam_items = [by_id[p] for p in seam_ids if p in by_id and (by_id[p].get("bbox") or [0, 0, 0, 0])[2] * (by_id[p].get("bbox") or [0, 0, 0, 0])[3] > 64]
    groups = {
        "seam": seam_items,
        "blink": [p for p in parts if any(k in p["id"].lower() for k in ("eye", "iris", "lash"))],
        "mouth": [p for p in parts if "mouth" in p["id"].lower()],
        "hair": [p for p in parts if "hair" in p["id"].lower()],
    }
    regions = []
    for name, items in groups.items():
        reg = clamp_region(union_bbox(items), canvas)
        regions.append({"name": name, **reg})
    return regions
def sample_tiles(character: dict[str, Any]) -> list[dict[str, int]]:
    w, h = [int(v) for v in (character.get("canvas_size") or [2048, 2048])]
    return [{"x": max(0, int(w * x) - 32), "y": max(0, int(h * y) - 32), "w": 64, "h": 64} for y in (0.30, 0.45, 0.60, 0.75) for x in (0.35, 0.45, 0.55, 0.65)]
def defaults(character: dict[str, Any]) -> dict[str, float]:
    return {p["id"]: p.get("default", 0) for p in character.get("parameters", [])}
def states(character: dict[str, Any], quick: bool) -> list[dict[str, Any]]:
    params = {p["id"] for p in character.get("parameters", [])}
    def have(values: dict[str, float]) -> dict[str, float]:
        return {k: v for k, v in values.items() if k in params}
    base = [{"name": "neutral", "group": "neutral", "parameters": {}, "reset_physics": True}]
    neck = [
        ("neck_angle_x_left", {"ParamAngleX": -30}), ("neck_angle_x_right", {"ParamAngleX": 30}),
        ("neck_angle_z_left", {"ParamAngleZ": -30}), ("neck_body_x", {"ParamBodyAngleX": 10}),
    ]
    blink_vals = [1, 0.5, 0] if quick else [1, 0.72, 0.5, 0.27, 0]
    mouth_vals = [0, 0.5, 1]
    mouth_form = [] if quick else [("mouth_form_frown", {"ParamMouthForm": -1}), ("mouth_form_smile", {"ParamMouthForm": 1})]
    hair = [
        ("hair_kick_x", {"ParamAngleX": 30, "ParamHairFront": 1}, True, 5),
        ("hair_settle", {"ParamAngleX": 0, "ParamHairFront": 0}, False, 28 if quick else 42),
        ("hair_kick_z", {"ParamAngleZ": 20, "ParamHairBack": 1}, True, 8),
    ]
    if quick:
        neck = neck[:2]
        hair = hair[:2]
    out = base
    out += [{"name": n, "group": "neck_seam", "parameters": have(v), "reset_physics": True, "physics_steps": 2} for n, v in neck]
    out += [{"name": f"blink_{str(v).replace('.', '_')}", "group": "blink", "parameters": have({"ParamEyeLOpen": v, "ParamEyeROpen": v}), "reset_physics": True} for v in blink_vals]
    out += [{"name": f"mouth_open_{str(v).replace('.', '_')}", "group": "mouth", "parameters": have({"ParamMouthOpenY": v}), "reset_physics": True} for v in mouth_vals]
    out += [{"name": n, "group": "mouth", "parameters": have(v), "reset_physics": True} for n, v in mouth_form]
    out += [{"name": n, "group": "hair_physics", "parameters": have(v), "reset_physics": reset, "physics_steps": steps} for n, v, reset, steps in hair]
    return [s for s in out if s["name"] == "neutral" or s["parameters"] or s.get("physics_steps")]
def image_bounds(path: Path) -> tuple[int, list[int] | None]:
    im = Image.open(path).convert("RGBA")
    pix = im.load(); w, h = im.size
    left, top, right, bottom, count = w, h, 0, 0, 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r, g, b, a = pix[x, y]
            if a > 10 and (abs(r - BG[0]) + abs(g - BG[1]) + abs(b - BG[2]) > 18):
                count += 4; left = min(left, x); top = min(top, y); right = max(right, x); bottom = max(bottom, y)
    return count, ([left, top, right + 1, bottom + 1] if count else None)
def save_frame_images(frames: list[dict[str, Any]], regions: list[dict[str, Any]], frames_dir: Path) -> None:
    by_name = {r["name"]: r for r in regions}
    region_for_group = {"neutral": "seam", "neck_seam": "seam", "blink": "blink", "mouth": "mouth", "hair_physics": "hair"}
    frames_dir.mkdir(parents=True, exist_ok=True)
    for index, frame in enumerate(frames):
        if frame.get("screenshot"):
            continue
        region_name = region_for_group.get(frame.get("group"), "seam")
        raw = (frame.get("region_pixels") or {}).get(region_name)
        region = by_name.get(region_name)
        if not raw or not region:
            continue
        data = base64.b64decode(raw)
        image = Image.frombytes("RGBA", (region["w"], region["h"]), data)
        path = frames_dir / f"{index:03d}_{frame['name']}.png"
        image.save(path)
        frame["screenshot"] = str(path)
def bbox_delta(a: list[int] | None, b: list[int] | None) -> float:
    if not a or not b:
        return 999.0
    return round(math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(4))), 3)
def part_opacity(frame: dict[str, Any], part_id: str) -> float:
    return float((frame.get("snapshot", {}).get("part_opacity") or {}).get(part_id, 0))
def score_motion(character: dict[str, Any], frames: list[dict[str, Any]], focus_parts: list[str], bounds: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_group = defaultdict(list)
    for f in frames:
        by_group[f.get("group")].append(f)
    blank = [f["name"] for f in frames if bounds[f["name"]]["non_bg"] < 1000]
    seam_rows, blink_rows, mouth_rows, hair_rows = [], [], [], []
    neutral_bounds = bounds.get("neutral", {}).get("bbox")
    for f in by_group["neck_seam"]:
        metric = (f.get("region_metrics") or {}).get("seam", {})
        changed = f.get("changed_sample_ratio", metric.get("changed_ratio", 0))
        mean = f.get("pixel_delta_mean_abs", metric.get("mean_abs", 0))
        seam_rows.append({"state": f["name"], "changed_ratio": round(changed, 5), "mean_abs": round(mean, 3), "bbox_delta": bbox_delta(neutral_bounds, bounds[f["name"]]["bbox"])})
    iris_parts = [p["id"] for p in character.get("parts", []) if "iris" in p["id"].lower() or "eye_white" in p["id"].lower()]
    for f in by_group["blink"]:
        value = next(iter(f.get("parameters", {}).values()), "")
        hidden = max([part_opacity(f, p) for p in iris_parts] or [0])
        metric = (f.get("region_metrics") or {}).get("blink", {})
        blink_rows.append({"state": f["name"], "eye_open": value, "hash": f.get("canvas_hash"), "hidden_opacity": round(hidden, 4), "ghost_score": round(f.get("changed_sample_ratio", metric.get("changed_ratio", 0)), 5)})
    mouth_parts = [p["id"] for p in character.get("parts", []) if "mouth" in p["id"].lower()]
    for f in by_group["mouth"]:
        visible = [p for p in mouth_parts if part_opacity(f, p) > 0.1]
        mouth_rows.append({"state": f["name"], "parameters": json.dumps(f.get("parameters", {})), "visible_parts": "|".join(visible), "visible_count": len(visible), "overlap_count": max(0, len([p for p in visible if "state" in p]) - 1), "hash": f.get("canvas_hash")})
    physics_profiles = character.get("physics_profiles") or []
    for f in by_group["hair_physics"]:
        snap = f.get("snapshot", {}).get("physics") or {}
        if snap:
            for profile_id, state in snap.items():
                off = state.get("offset", [0, 0]); vel = state.get("velocity", [0, 0])
                hair_rows.append({"state": f["name"], "profile_id": profile_id, "offset": round(math.hypot(*off), 5), "velocity": round(math.hypot(*vel), 5)})
        else:
            estimate = float(f.get("changed_sample_ratio", 0))
            for profile in physics_profiles:
                hair_rows.append({"state": f["name"], "profile_id": profile.get("id"), "offset": round(estimate, 5), "velocity": round(float(f.get("pixel_delta_mean_abs", 0)) / 255, 5)})
    max_seam = max([r["changed_ratio"] * 100 + min(20, r["bbox_delta"] / 20) for r in seam_rows] or [100])
    blink_hashes = {r["hash"] for r in blink_rows}
    max_hidden_closed = max([r["hidden_opacity"] for r in blink_rows if str(r["eye_open"]) in {"0", "0.0"}] or [0])
    mouth_hashes = {r["hash"] for r in mouth_rows if "ParamMouthOpenY" in r["parameters"]}
    max_mouth_overlap = max([r["overlap_count"] for r in mouth_rows] or [0])
    max_by_profile: dict[str, float] = defaultdict(float)
    for r in hair_rows:
        max_by_profile[r["profile_id"]] = max(max_by_profile[r["profile_id"]], r["offset"])
    active = [k for k, v in max_by_profile.items() if v >= 0.05]
    settle = [r for r in hair_rows if r["state"] == "hair_settle"]
    settle_residue = max([r["offset"] + r["velocity"] for r in settle] or [999])
    checks = [
        {"check": "blank_frames", "status": "PASS" if not blank else "FAIL", "value": len(blank), "details": blank},
        {"check": "neck_seam_score", "status": "PASS" if max_seam < 65 and not blank else "FAIL", "value": round(max_seam, 3), "threshold": 65},
        {"check": "blink_states", "status": "PASS" if len(blink_hashes) >= 3 and max_hidden_closed <= 1.0 and not blank else "FAIL", "value": len(blink_hashes), "hidden_closed": max_hidden_closed},
        {"check": "mouth_states", "status": "PASS" if len(mouth_hashes) >= 3 and max_mouth_overlap <= 1 and not blank else "FAIL", "value": len(mouth_hashes), "overlap": max_mouth_overlap},
        {"check": "hair_physics", "status": "PASS" if len(active) >= 3 and settle_residue < 0.75 and not blank else "FAIL", "value": len(active), "settle_residue": round(settle_residue, 5), "active_profiles": active},
    ]
    scores = {"neck_seam": round(max_seam, 3), "blink_distinct_hashes": len(blink_hashes), "mouth_distinct_hashes": len(mouth_hashes), "hair_active_profiles": len(active), "hair_settle_residue": round(settle_residue, 5)}
    return checks, {"scores": scores, "seam": seam_rows, "blink": blink_rows, "mouth": mouth_rows, "hair": hair_rows}
def font(size: int) -> ImageFont.ImageFont:
    for path in ["/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()
def contact_sheet(frames: list[dict[str, Any]], out: Path) -> None:
    picks = [f for f in frames if f["name"] in {"neutral", "neck_angle_x_left", "neck_angle_x_right", "blink_0", "mouth_open_1", "hair_kick_x", "hair_settle"}]
    picks = picks or frames[:8]
    cols, cell_w, cell_h = 4, 300, 280
    sheet = Image.new("RGB", (cols * cell_w, ((len(picks) + cols - 1) // cols) * cell_h + 60), "#f4f0e8")
    draw = ImageDraw.Draw(sheet); draw.text((18, 16), "AUTORIG Motion QA", fill="#202124", font=font(24))
    for i, f in enumerate(picks):
        x, y = (i % cols) * cell_w, 60 + (i // cols) * cell_h
        img = Image.open(f["screenshot"]).convert("RGB"); img.thumbnail((cell_w - 24, cell_h - 48), Image.Resampling.LANCZOS)
        sheet.paste(img, (x + (cell_w - img.width) // 2, y + 8)); draw.text((x + 12, y + cell_h - 34), f["name"], fill="#202124", font=font(14))
    out.parent.mkdir(parents=True, exist_ok=True); sheet.save(out)
def build_gifs(frames: list[dict[str, Any]], gifs_dir: Path) -> dict[str, str]:
    gifs_dir.mkdir(parents=True, exist_ok=True)
    outputs = {}
    for group, name in [("neck_seam", "neck_seam.gif"), ("blink", "blink.gif"), ("mouth", "mouth.gif"), ("hair_physics", "hair_physics.gif")]:
        images = []
        for f in [x for x in frames if x.get("group") in {"neutral", group}]:
            img = Image.open(f["screenshot"]).convert("RGB"); img.thumbnail((520, 520), Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", (520, 520), "#202124"); canvas.paste(img, ((520 - img.width) // 2, (520 - img.height) // 2)); images.append(canvas)
        if images:
            path = gifs_dir / name; images[0].save(path, save_all=True, append_images=images[1:], duration=260, loop=0); outputs[group] = str(path)
    return outputs
def run_capture(project: Path, out: Path, renderer: str, port: int, config: dict[str, Any]) -> dict[str, Any]:
    cfg = out / "motion_qa_config.json"; raw = out / "motion_qa_capture.json"; runner = out / "motion_qa_runner.js"
    runner.write_text(RUNNER_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
    write_json(cfg, {"playwright": str(PLAYWRIGHT), "url": f"http://127.0.0.1:{port}/" + ("?renderer=pixi" if renderer == "pixi" else ""), "renderer": renderer, "launch_args": ["--use-angle=swiftshader"] if renderer == "pixi" else [], "captures_dir": str(out / "frames"), "out": str(raw), **config})
    server = subprocess.Popen(["python3", str(ROOT / "scripts/mini_cubism_preview_server.py"), "--project", str(project), "--port", str(port)], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        wait_for_server("127.0.0.1", port)
        result = subprocess.run([node_bin(), str(runner), str(cfg)], cwd=ROOT, capture_output=True, text=True, timeout=300, check=False)
        if result.returncode != 0 and not raw.exists():
            raise RuntimeError(result.stderr[-2000:] or result.stdout[-2000:])
    finally:
        terminate(server)
    return load_json(raw)
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--renderer", choices=["canvas", "pixi"], default="pixi")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--focus-part", action="append", default=["neck"])
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    project = args.project if args.project.is_absolute() else ROOT / args.project
    out = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    character = load_json(project / "character.json")
    focus_parts = resolve_parts(character, args.focus_part) or resolve_parts(character, ["neck"])
    regions = named_regions(character, focus_parts)
    motion_states = [s for s in states(character, args.quick) if s["name"] != "neutral"]
    capture = run_capture(project.resolve(), out, args.renderer, args.port or free_port(), {"states": motion_states, "regions": regions, "tiles": sample_tiles(character), "defaults": defaults(character)})
    frames = capture.get("frames", [])
    save_frame_images(frames, regions, out / "frames")
    bounds = {}
    for frame in frames:
        non_bg, bbox = image_bounds(Path(frame["screenshot"]))
        bounds[frame["name"]] = {"non_bg": non_bg, "bbox": bbox}
    checks, detail = score_motion(character, frames, focus_parts, bounds)
    status = "PASS" if all(c["status"] == "PASS" for c in checks) and not capture.get("errors") else "FAIL"
    write_csv(out / "parameter_sweep.csv", [{"state": f["name"], "group": f.get("group"), "parameters": json.dumps(f.get("parameters", {})), "canvas_hash": f.get("canvas_hash"), "bbox_delta": bbox_delta(bounds.get("neutral", {}).get("bbox"), bounds[f["name"]]["bbox"])} for f in frames])
    write_csv(out / "seam_motion_delta.csv", detail["seam"])
    write_csv(out / "blink_qa.csv", detail["blink"])
    write_csv(out / "mouth_qa.csv", detail["mouth"])
    write_csv(out / "hair_physics_qa.csv", detail["hair"])
    gifs = build_gifs(frames, out / "gifs")
    contact = out / "motion_contact_sheet.png"; contact_sheet(frames, contact)
    score_report = {"schema_version": 1, "generated_at": now_iso(), "status": status, **detail["scores"]}
    report = {"schema_version": 1, "generated_at": now_iso(), "status": status, "quick": args.quick, "project": rel(project), "renderer_requested": args.renderer, "renderer_backend": capture.get("backend"), "focus_parts": focus_parts, "checks": checks, "scores": detail["scores"], "outputs": {"motion_score_report": rel(out / "motion_score_report.json"), "parameter_sweep": rel(out / "parameter_sweep.csv"), "seam_motion_delta": rel(out / "seam_motion_delta.csv"), "blink_qa": rel(out / "blink_qa.csv"), "mouth_qa": rel(out / "mouth_qa.csv"), "hair_physics_qa": rel(out / "hair_physics_qa.csv"), "motion_contact_sheet": rel(contact), "gifs": {k: rel(v) for k, v in gifs.items()}}, "errors": capture.get("errors", [])}
    write_json(out / "motion_score_report.json", score_report)
    write_json(out / "motion_qa_report.json", report)
    lines = ["# AUTORIG Motion QA Summary", "", f"Status: **{status}**", f"Project: `{rel(project)}`", f"Renderer: `{capture.get('backend')}`", f"Quick mode: `{args.quick}`", "", "| check | status | value |", "|---|---|---:|"]
    for c in checks:
        lines.append(f"| {c['check']} | {c['status']} | {c.get('value', '')} |")
    lines += ["", "Quick mode is a smoke test and does not replace full Motion QA." if args.quick else "Full Motion QA run."]
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "status": status, "out_dir": str(out), "renderer_backend": capture.get("backend"), "checks": checks}, ensure_ascii=False, indent=2))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())

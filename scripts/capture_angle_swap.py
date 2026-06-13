#!/usr/bin/env python3
"""ANGLE-SWAP-002 통합 리그 실제 런타임 캡처 (메모리 visual-verify-real-render 규율).

run_mini_cubism_pose_sweep 의 번들 node+playwright 하니스를 재사용해, 통합
프로젝트를 preview 서버로 띄우고 ParamAngleX를 스윕하며 실제 렌더를 캡처한다.
내 합성 미리보기 금지 — 8065 실런타임 캡처로만 판정.

스윕: 0(정면·표정 라이브) / ±14·±20(크로스페이드 경계, 유령 체크) / ±40·±80(작화 옆모습)
     + mouth_open@0(정면 표정 생존 확인).

사용: python3 scripts/capture_angle_swap.py \
        --project experiments/autorig-character-004/rig_v0_angle_project \
        --out experiments/autorig-character-004/reports/angle_swap_capture
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_mini_cubism_pose_sweep as ps  # noqa: E402
from lib.vtube_io import ROOT, now_iso  # noqa: E402

POSES = [
    {"name": "front_0", "parameters": {"ParamAngleX": 0}},
    {"name": "front_mouth_open", "parameters": {"ParamAngleX": 0, "ParamMouthOpenY": 1}},
    {"name": "L_live_14", "parameters": {"ParamAngleX": -14}},
    {"name": "L_cross_20", "parameters": {"ParamAngleX": -20}},
    {"name": "L_art_40", "parameters": {"ParamAngleX": -40}},
    {"name": "L_art_80", "parameters": {"ParamAngleX": -80}},
    {"name": "R_cross_20", "parameters": {"ParamAngleX": 20}},
    {"name": "R_art_40", "parameters": {"ParamAngleX": 40}},
    {"name": "R_art_80", "parameters": {"ParamAngleX": 80}},
]
VIEWPORT = {"name": "desktop", "width": 1440, "height": 1000}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    out_dir = Path(args.out).resolve()
    shots = out_dir / "screenshots"
    shots.mkdir(parents=True, exist_ok=True)
    if not (project / "character.json").exists():
        raise SystemExit(f"missing character.json: {project}")

    port = ps.free_port(args.host)
    url = f"http://{args.host}:{port}/"
    server = subprocess.Popen(
        [sys.executable, str(ROOT / "scripts" / "mini_cubism_preview_server.py"),
         "--project", str(project), "--host", args.host, "--port", str(port)],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        ps.wait_for_server(f"{url}api/project", server)
        result_path = shots / "playwright_result.json"
        config_path = shots / "playwright_config.json"
        script_path = shots / "playwright_angle.cjs"
        config = {"url": url, "outDir": str(shots), "resultPath": str(result_path),
                  "poses": POSES, "viewports": [VIEWPORT],
                  "captureElement": "canvas", "showOverlays": False}
        config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n")
        script_path.write_text(ps.browser_script())
        import os
        env = os.environ.copy()
        env["PLAYWRIGHT_MODULE"] = ps.playwright_module()
        completed = subprocess.run([ps.node_binary(), str(script_path), str(config_path)],
                                   cwd=ROOT, env=env, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            detail = result_path.read_text() if result_path.exists() else completed.stderr
            raise SystemExit(f"playwright capture failed\n{detail}\n{completed.stderr}")
        data = json.loads(result_path.read_text())
        poses = data["results"][0]["poses"]
        report = {"generated_at": now_iso(), "project": str(project), "url": url,
                  "poses": [{"pose": p["pose"], "params": p["parameters"],
                             "changedRatio": p["metrics"].get("changedRatio"),
                             "screenshot": Path(p["screenshot"]).name} for p in poses]}
        (out_dir / "angle_swap_capture_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(f"캡처 {len(poses)}장 -> {shots}")
        for p in poses:
            print(f"  {p['pose']:18s} changedRatio={p['metrics'].get('changedRatio'):.5f}")
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

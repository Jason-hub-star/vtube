#!/usr/bin/env python3
"""임의 파라미터 포즈 실런타임 캡처 (메모리 visual-verify-real-render 규율).

run_mini_cubism_pose_sweep 의 번들 node+playwright 하니스를 재사용해, --poses JSON으로
지정한 파라미터 조합을 자체 런타임에서 렌더·캡처한다. pose_sweep POSES는 고정(nod·body
없음)이라, 끄덕임(AngleY)·상체회전(AngleX+body) 같은 커스텀 포즈 검증용.

사용: python3 scripts/capture_pose.py --project <proj> --out <dir> \
        --poses '[{"name":"nod_down","parameters":{"ParamAngleY":-30}}]'
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_mini_cubism_pose_sweep as ps  # noqa: E402
from lib.vtube_io import ROOT  # noqa: E402

DEFAULT_POSES = [
    {"name": "neutral", "parameters": {}},
    {"name": "nod_down", "parameters": {"ParamAngleY": -30}},
    {"name": "nod_up", "parameters": {"ParamAngleY": 30}},
    {"name": "turn_body", "parameters": {"ParamAngleX": 30}},
]
VIEWPORT = {"name": "desktop", "width": 1440, "height": 1000}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--poses", default=None, help="JSON 포즈 리스트 (없으면 nod/body 기본)")
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    out_dir = Path(args.out).resolve()
    shots = out_dir / "screenshots"
    shots.mkdir(parents=True, exist_ok=True)
    if not (project / "character.json").exists():
        raise SystemExit(f"missing character.json: {project}")
    poses = json.loads(args.poses) if args.poses else DEFAULT_POSES

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
        script_path = shots / "playwright_pose.cjs"
        config = {"url": url, "outDir": str(shots), "resultPath": str(result_path),
                  "poses": poses, "viewports": [VIEWPORT],
                  "captureElement": "canvas", "showOverlays": False}
        config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n")
        script_path.write_text(ps.browser_script())
        env = os.environ.copy()
        env["PLAYWRIGHT_MODULE"] = ps.playwright_module()
        completed = subprocess.run([ps.node_binary(), str(script_path), str(config_path)],
                                   cwd=ROOT, env=env, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            detail = result_path.read_text() if result_path.exists() else completed.stderr
            raise SystemExit(f"capture failed\n{detail}\n{completed.stderr}")
        data = json.loads(result_path.read_text())
        for p in data["results"][0]["poses"]:
            print(f"  {p['pose']:14s} -> {shots}/desktop_{p['pose']}.png")
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

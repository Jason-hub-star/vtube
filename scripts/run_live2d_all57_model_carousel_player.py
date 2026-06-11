#!/usr/bin/env python3
"""Build and run the all57 Live2D model carousel player."""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "live2d-strong-model-pattern-001"
MANIFEST = EXPERIMENT / "reports" / "all57_render_manifest.json"
SANDBOX_REPORT = EXPERIMENT / "reports" / "all57_runtime_probe_sandbox.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=5120)
    parser.add_argument("--skip-npm-install", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def wait_for_server(host: str, port: int, timeout: float = 45.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"server did not start on {host}:{port}")


def run_step(command: list[str]) -> None:
    result = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)
    if result.stdout.strip():
        print(result.stdout.strip())


def main() -> int:
    args = parse_args()
    run_step([sys.executable, str(ROOT / "scripts" / "build_live2d_all57_render_manifest.py")])
    run_step(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_live2d_runtime_probe_sandbox.py"),
            "--manifest",
            str(MANIFEST),
        ]
    )
    run_step([sys.executable, str(ROOT / "scripts" / "build_live2d_all57_model_carousel_player.py")])
    sandbox = load_json(SANDBOX_REPORT)
    demo_dir = ROOT / sandbox["demo_dir"]
    if not args.skip_npm_install and not (demo_dir / "node_modules" / "vite").exists():
        subprocess.run(["npm", "install"], cwd=demo_dir, check=True)
    url = f"http://127.0.0.1:{args.port}/all57_model_carousel.html"
    print(f"\nLive2D all57 모델 플레이어 실행 중: {url}")
    print("종료하려면 이 터미널에서 Ctrl+C를 누르세요.\n")
    server = subprocess.Popen(
        ["npm", "run", "start", "--", "--host", "127.0.0.1", "--port", str(args.port)],
        cwd=demo_dir,
    )
    try:
        wait_for_server("127.0.0.1", args.port)
        server.wait()
    except KeyboardInterrupt:
        print("\n서버를 종료합니다.")
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

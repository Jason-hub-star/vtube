#!/usr/bin/env python3
"""T3: 웹캠/재생 트래킹 스트림으로 Mini Cubism 런타임을 구동하는 드라이브 서버.

- `/`            Mini Cubism 프리뷰 앱 (mini_cubism_preview_server 재사용)
- `/drive`       드라이브 페이지: 좌측 웹캠 트래킹(MediaPipe) → 우측 iframe 모델 주입
- `/drive?replay=1[&speed=4][&auto=1]`  저장된 T1 스트림 재생 주입 (웹캠 불필요)
- `/api/replay-stream`  T1 raw 스트림 JSON

트래킹→Cubism 변환식은 T1 프로브 페이지(face_tracking_webcam_probe/index.html)의
rawChannels/convert를 그대로 이식했다. EyeOpen 0.27 / MouthOpenY 0.85 클램프는
v21 프로젝트 파라미터 범위에 내장되어 있어 앱 쪽 setParameterValue가 자동 적용한다.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from http import HTTPStatus
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import mini_cubism_preview_server as mcps  # noqa: E402

DEFAULT_PROJECT = (
    ROOT
    / "experiments/cubism-v2-new-character-002/model_edit_v21_supported_rig_smoke_preview/mini_cubism_diagnostic_project"
)
DEFAULT_STREAM = ROOT / "experiments/reference-model-structure-001/reports/face_tracking_webcam_probe_raw.json"

# 드라이브 페이지(HTML/CSS/트래킹 JS)는 템플릿으로 분리 — 이 파일은 서버 책임만 (500줄 룰)
DRIVE_TEMPLATE = Path(__file__).resolve().parent / "templates" / "mini_cubism_drive.html"


class DriveHandler(mcps.MiniCubismHandler):
    server_version = "MiniCubismWebcamDrive/1.0"

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path == "/drive":
            model_src = self.server.model_src  # type: ignore[attr-defined]
            data = DRIVE_TEMPLATE.read_text(encoding="utf-8").replace("__MODEL_SRC__", model_src).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
            return
        if path == "/api/replay-stream":
            stream_path: Path = self.server.stream_path  # type: ignore[attr-defined]
            if not stream_path.exists():
                self.send_error(HTTPStatus.NOT_FOUND, "saved T1 stream missing")
                return
            self.serve_file(stream_path)
            return
        super().do_GET()


class DriveServer(mcps.MiniCubismServer):
    def __init__(self, address: tuple[str, int], handler, project: Path, stream_path: Path, model_src: str):
        super().__init__(address, handler, project)
        self.stream_path = stream_path.resolve()
        self.model_src = model_src


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT)
    parser.add_argument("--stream", type=Path, default=DEFAULT_STREAM)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8060)
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--init-only", action="store_true", help="설정 검증만 하고 종료")
    # PIXI-RENDER-001: 기본 pixi(WebGL, 풀해상도). canvas는 폴백 — 구 저해상 경로 유지
    parser.add_argument("--renderer", choices=["pixi", "canvas"], default="pixi")
    args = parser.parse_args()
    model_src = "/?renderer=pixi" if args.renderer == "pixi" else "/?render_scale=0.55"

    project = args.project if args.project.is_absolute() else ROOT / args.project
    if not (project / "character.json").exists():
        raise SystemExit(f"Missing character.json in {project}")

    if args.init_only:
        print(json.dumps({"ok": True, "project": str(project), "stream": str(args.stream)}, ensure_ascii=False))
        return 0

    server = DriveServer((args.host, args.port), DriveHandler, project, args.stream, model_src)
    url = f"http://{args.host}:{args.port}/drive"
    print(f"T3 webcam drive: {url}")
    print(f"Project: {project}")
    if not args.no_open:
        subprocess.run(["open", url], check=False)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

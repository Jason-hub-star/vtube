#!/usr/bin/env python3
"""Serve the Mini Cubism v0 preview app and project files."""

from __future__ import annotations

import argparse
import json
import mimetypes
import subprocess
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "mini_cubism_app"


def safe_join(base: Path, requested: str) -> Path | None:
    path = (base / requested.lstrip("/")).resolve()
    try:
        path.relative_to(base.resolve())
    except ValueError:
        return None
    return path


class MiniCubismServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], handler: type[BaseHTTPRequestHandler], project: Path):
        super().__init__(server_address, handler)
        self.project = project.resolve()


class MiniCubismHandler(BaseHTTPRequestHandler):
    server_version = "MiniCubismPreview/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path == "/api/project":
            self.serve_project_json()
            return
        if path.startswith("/project/"):
            project_path = safe_join(self.server.project, path.removeprefix("/project/"))  # type: ignore[attr-defined]
            if project_path is None:
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            self.serve_file(project_path)
            return
        static_path = "index.html" if path in {"", "/"} else path.lstrip("/")
        app_path = safe_join(APP_DIR, static_path)
        if app_path is None:
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        self.serve_file(app_path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path == "/api/mini-rig":
            self.save_mini_rig_json()
            return
        if path == "/api/validate-eye-modes":
            self.run_eye_mode_validation()
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def serve_project_json(self) -> None:
        project = self.server.project  # type: ignore[attr-defined]
        character_path = project / "character.json"
        if not character_path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "character.json is missing")
            return
        payload = json.loads(character_path.read_text())
        rig_path = project / "mini_rig.json"
        payload["_mini_rig"] = json.loads(rig_path.read_text()) if rig_path.exists() else default_mini_rig()
        payload["_project_base_url"] = "/project/"
        self.send_json(payload)

    def read_json_body(self) -> dict:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_length = 0
        if content_length <= 0:
            return {}
        raw = self.rfile.read(content_length)
        return json.loads(raw.decode("utf-8"))

    def save_mini_rig_json(self) -> None:
        project = self.server.project  # type: ignore[attr-defined]
        try:
            payload = self.read_json_body()
        except json.JSONDecodeError:
            self.send_error(HTTPStatus.BAD_REQUEST, "invalid json")
            return
        rig = payload.get("rig") if isinstance(payload, dict) else None
        if not isinstance(rig, dict):
            self.send_error(HTTPStatus.BAD_REQUEST, "missing rig object")
            return
        rig["schema_version"] = rig.get("schema_version") or 1
        rig["project_kind"] = "mini_cubism_rig_v0"
        rig_path = project / "mini_rig.json"
        rig_path.write_text(json.dumps(rig, ensure_ascii=False, indent=2) + "\n")
        self.send_json({"ok": True, "path": str(rig_path)})

    def run_eye_mode_validation(self) -> None:
        project = self.server.project  # type: ignore[attr-defined]
        script = ROOT / "scripts/validate_mini_cubism_eye_modes.py"
        result = subprocess.run(
            [sys.executable, str(script), "--project", str(project)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        report_path = project / "reports/eye_mode_validation/eye_mode_validation_report.json"
        report = json.loads(report_path.read_text()) if report_path.exists() else None
        self.send_json(
            {
                "ok": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout[-4000:],
                "stderr": result.stderr[-4000:],
                "report": report,
            },
            HTTPStatus.OK if result.returncode == 0 else HTTPStatus.ACCEPTED,
        )

    def serve_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        data = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        print(f"{self.address_string()} - {format % args}")


def default_mini_rig() -> dict:
    return {
        "schema_version": 1,
        "project_kind": "mini_cubism_rig_v0",
        "mesh_overrides": {},
        "keyform_overrides": [],
        "clipping": {
            "enabled": True,
            "pairs": {
                "eye_L_white": ["eye_L_iris", "eye_L_pupil", "eye_L_highlight"],
                "eye_R_white": ["eye_R_iris", "eye_R_pupil", "eye_R_highlight"],
            },
        },
        "eye_socket_covers": {
            "enabled": True,
            "L": {
                "bbox": [814, 674, 190, 92],
                "fade_start": 0.96,
                "fade_full": 0.08,
                "max_opacity": 0.9,
                "hide_open_parts_at": 0.22,
                "show_open_parts_at": 0.82,
                "upper_color": "#fae7dd",
                "mid_color": "#f4d7cc",
                "lower_color": "#e9bfb4",
                "blur": 1,
                "scale_x": 0.8,
                "scale_y": 0.52,
            },
            "R": {
                "bbox": [1066, 676, 190, 92],
                "fade_start": 0.96,
                "fade_full": 0.08,
                "max_opacity": 0.9,
                "hide_open_parts_at": 0.22,
                "show_open_parts_at": 0.82,
                "upper_color": "#fae7dd",
                "mid_color": "#f4d5ca",
                "lower_color": "#e8bbb0",
                "blur": 1,
                "scale_x": 0.8,
                "scale_y": 0.52,
            },
        },
        "notes": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8050, type=int)
    args = parser.parse_args()

    project = Path(args.project)
    if not project.is_absolute():
        project = ROOT / project
    if not (project / "character.json").exists():
        raise SystemExit(f"Missing character.json in {project}")
    if not APP_DIR.exists():
        raise SystemExit(f"Missing preview app directory: {APP_DIR}")

    server = MiniCubismServer((args.host, args.port), MiniCubismHandler, project)
    print(f"Mini Cubism v0 preview: http://{args.host}:{args.port}/")
    print(f"Project: {project.resolve()}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

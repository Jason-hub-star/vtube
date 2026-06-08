#!/usr/bin/env python3
"""Serve the Mini Cubism v0 preview app and project files."""

from __future__ import annotations

import argparse
import json
import mimetypes
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

    def serve_project_json(self) -> None:
        project = self.server.project  # type: ignore[attr-defined]
        character_path = project / "character.json"
        if not character_path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "character.json is missing")
            return
        payload = json.loads(character_path.read_text())
        payload["_project_base_url"] = "/project/"
        self.send_json(payload)

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

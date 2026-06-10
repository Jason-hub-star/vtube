"""로컬 HTTP 서버 공통 베이스. (ThreadingHTTPServer 보일러플레이트 13벌 복붙의 단일 원본)"""

from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer  # noqa: F401 - 재수출
from pathlib import Path


def safe_join(base: Path, requested: str) -> Path | None:
    """디렉토리 탈출을 막는 경로 결합."""
    path = (base / requested.lstrip("/")).resolve()
    try:
        path.relative_to(base.resolve())
    except ValueError:
        return None
    return path


class JsonRequestHandler(BaseHTTPRequestHandler):
    """send_json/serve_file/read_json_body가 내장된 핸들러 베이스."""

    quiet = False

    def log_message(self, fmt: str, *args) -> None:  # noqa: A002
        if not self.quiet:
            print(f"{self.address_string()} - {fmt % args}")

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def serve_file(self, path: Path, cache: bool = False) -> None:
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        data = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "max-age=3600" if cache else "no-store")
        self.end_headers()
        self.wfile.write(data)

    def read_json_body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

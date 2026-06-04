#!/usr/bin/env python3
"""Local review server that saves manual Vtube adjustment evidence."""

from __future__ import annotations

import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class ReviewHandler(SimpleHTTPRequestHandler):
    evidence_path: Path

    def do_POST(self) -> None:
        if self.path != "/api/save-evidence":
            self.send_error(404, "Not found")
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            self.send_error(400, f"Invalid JSON: {exc}")
            return

        self.evidence_path.parent.mkdir(parents=True, exist_ok=True)
        self.evidence_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        response = {"ok": True, "path": str(self.evidence_path)}
        data = json.dumps(response, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("/Users/family/jason/Vtube/experiments/production-canvas-2048-001"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8028)
    args = parser.parse_args()

    root = args.root.resolve()
    evidence = root / "reports" / "manual_adjustments_2048.json"

    class Handler(ReviewHandler):
        evidence_path = evidence

        def __init__(self, *handler_args, **handler_kwargs):
            super().__init__(*handler_args, directory=str(root), **handler_kwargs)

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Serving {root} at http://{args.host}:{args.port}")
    print(f"Evidence will save to {evidence}")
    server.serve_forever()


if __name__ == "__main__":
    main()

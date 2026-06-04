#!/usr/bin/env python3
"""Serve Blink Stage 001 preview and save label/review evidence."""

from __future__ import annotations

import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class BlinkStageHandler(SimpleHTTPRequestHandler):
    experiment_root: Path

    def _send_json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:  # noqa: N802
        if self.path not in {"/api/save-blink-labels", "/api/save-blink-review"}:
            self._send_json(404, {"error": "unknown endpoint"})
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            self._send_json(400, {"error": f"invalid json: {exc}"})
            return

        reports = self.experiment_root / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        filename = "blink_stage_labels.json" if self.path.endswith("labels") else "blink_stage_review.json"
        out_path = reports / filename
        out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if filename == "blink_stage_review.json" and "labels" in payload:
            label_payload = {
                "experiment_id": "BLINK-LABEL-001",
                "date": payload.get("date"),
                "source": "saved_with_review",
                "complete": payload.get("label_complete"),
                "selected": payload.get("selected"),
                "selected_label_complete": payload.get("selected_label_complete"),
                "labels": payload.get("labels", {}),
                "placements": payload.get("placements", {}),
            }
            (reports / "blink_stage_labels.json").write_text(json.dumps(label_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        self._send_json(200, {"ok": True, "path": str(out_path)})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("/Users/family/jason/Vtube/experiments/blink-stage-001"))
    parser.add_argument("--port", type=int, default=8031)
    args = parser.parse_args()

    root = args.root.resolve()
    BlinkStageHandler.experiment_root = root
    server = ThreadingHTTPServer(("127.0.0.1", args.port), lambda *a, **kw: BlinkStageHandler(*a, directory=str(root), **kw))
    print(f"Serving {root} at http://127.0.0.1:{args.port}/preview/index.html")
    server.serve_forever()


if __name__ == "__main__":
    main()

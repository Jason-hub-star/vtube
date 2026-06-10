#!/usr/bin/env python3
"""AUTORIG 관제탑 서버 — runs/<run_id>/events.jsonl을 읽어 대시보드에 공급한다.

  GET  /                              control_tower 앱
  GET  /api/runs                      런 목록
  GET  /api/runs/<id>/state           파생 상태 (이벤트 재생)
  GET  /api/runs/<id>/events?after=N  증분 이벤트 tail
  GET  /runs/<id>/artifacts/<png>     아티팩트 원본
  GET  /runs/<id>/thumbs/<png>        알파크롭 썸네일 (요청 시 생성, 캐시)
  POST /api/runs/<id>/gate-response   {gate, decision, overrides} → gate_resolved append

게이트 알림: 감시 스레드가 새 gate_waiting을 발견하면 macOS 알림(osascript)을 보내고
runs/<id>/notified.json에 기록한다. --no-notify는 기록만 하고 알림은 보내지 않는다.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import subprocess
import sys
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from autorig_events import EventWriter, RUNS_DIR, derive_state, list_runs, read_events  # noqa: E402

APP_DIR = ROOT / "control_tower"
THUMB_SIZE = 220
CROP_MARGIN = 40


def safe_join(base: Path, requested: str) -> Path | None:
    path = (base / requested.lstrip("/")).resolve()
    try:
        path.relative_to(base.resolve())
    except ValueError:
        return None
    return path


def make_thumb(src: Path, dest: Path) -> Path | None:
    try:
        img = Image.open(src)
        img.load()
    except Exception:
        return None
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    bbox = img.getchannel("A").getbbox()
    if bbox:
        left = max(0, bbox[0] - CROP_MARGIN)
        top = max(0, bbox[1] - CROP_MARGIN)
        right = min(img.width, bbox[2] + CROP_MARGIN)
        bottom = min(img.height, bbox[3] + CROP_MARGIN)
        img = img.crop((left, top, right, bottom))
    img.thumbnail((THUMB_SIZE, THUMB_SIZE))
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest)
    return dest


class ControlTowerHandler(BaseHTTPRequestHandler):
    server_version = "AutorigControlTower/1.0"

    def log_message(self, fmt: str, *args) -> None:  # noqa: A002
        pass  # 폴링 노이즈 억제

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode()
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

    def run_dir(self, run_id: str) -> Path | None:
        runs_dir: Path = self.server.runs_dir  # type: ignore[attr-defined]
        return safe_join(runs_dir, run_id)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path == "/api/runs":
            self.send_json({"runs": list_runs(self.server.runs_dir)})  # type: ignore[attr-defined]
            return
        if path.startswith("/api/runs/"):
            rest = path.removeprefix("/api/runs/")
            run_id, _, action = rest.partition("/")
            run_dir = self.run_dir(run_id)
            if run_dir is None or not run_dir.exists():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            if action == "state":
                self.send_json(derive_state(read_events(run_dir), run_id=run_id))
                return
            if action == "events":
                after = int(parse_qs(parsed.query).get("after", ["0"])[0])
                events = read_events(run_dir, after_seq=after)
                last_seq = max((e.get("seq", 0) for e in events), default=after)
                self.send_json({"events": events, "last_seq": last_seq})
                return
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if path.startswith("/runs/"):
            rest = path.removeprefix("/runs/")
            run_id, _, file_part = rest.partition("/")
            run_dir = self.run_dir(run_id)
            if run_dir is None:
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            if file_part.startswith("thumbs/"):
                name = Path(file_part.removeprefix("thumbs/")).name
                thumb = run_dir / "thumbs" / name
                source = run_dir / "artifacts" / name
                if not thumb.exists():
                    if not source.exists() or make_thumb(source, thumb) is None:
                        self.send_error(HTTPStatus.NOT_FOUND)
                        return
                self.serve_file(thumb, cache=True)
                return
            target = safe_join(run_dir, file_part)
            if target is None:
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            self.serve_file(target, cache=file_part.startswith("artifacts/"))
            return
        static_path = "index.html" if path in {"", "/"} else path.lstrip("/")
        app_path = safe_join(APP_DIR, static_path)
        if app_path is None:
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        self.serve_file(app_path)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if not (path.startswith("/api/runs/") and path.endswith("/gate-response")):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        run_id = path.removeprefix("/api/runs/").removesuffix("/gate-response").strip("/")
        run_dir = self.run_dir(run_id)
        if run_dir is None or not run_dir.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            gate = payload["gate"]
            decision = payload.get("decision", "approve")
            overrides = payload.get("overrides") or {}
        except Exception as exc:  # noqa: BLE001 - 로컬 UI에 그대로 노출
            self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        writer = EventWriter(run_id, self.server.runs_dir)  # type: ignore[attr-defined]
        event = writer.gate_resolved(gate, decision, overrides=overrides, source="control_tower")
        self.send_json({"ok": True, "event": event})


class ControlTowerServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], handler, runs_dir: Path):
        super().__init__(address, handler)
        self.runs_dir = runs_dir


def notification_watcher(runs_dir: Path, notify: bool, stop: threading.Event) -> None:
    """새 gate_waiting을 감지해 macOS 알림을 보낸다."""
    while not stop.is_set():
        try:
            for run_dir in runs_dir.iterdir() if runs_dir.exists() else []:
                if not run_dir.is_dir():
                    continue
                notified_path = run_dir / "notified.json"
                notified: list[int] = json.loads(notified_path.read_text()) if notified_path.exists() else []
                state = derive_state(read_events(run_dir), run_id=run_dir.name)
                changed = False
                for gate_id, gate in state["gates"].items():
                    seq = gate.get("waiting_seq")
                    if gate.get("status") != "WAITING" or seq in notified:
                        continue
                    notified.append(seq)
                    changed = True
                    if notify:
                        title = gate.get("title") or f"{gate_id} 게이트"
                        subprocess.run(
                            [
                                "osascript",
                                "-e",
                                f'display notification "주인님, 검수 차례예요 — {title}" with title "AUTORIG 관제탑" sound name "Glass"',
                            ],
                            check=False,
                            capture_output=True,
                        )
                if changed:
                    notified_path.write_text(json.dumps(notified) + "\n")
        except Exception:  # noqa: BLE001 - 감시 스레드는 죽지 않는다
            pass
        stop.wait(1.0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8095)
    parser.add_argument("--runs-dir", type=Path, default=RUNS_DIR)
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--no-notify", action="store_true", help="macOS 알림 없이 기록만")
    parser.add_argument("--init-only", action="store_true")
    args = parser.parse_args()

    if not (APP_DIR / "index.html").exists():
        raise SystemExit(f"missing control tower app: {APP_DIR / 'index.html'}")
    args.runs_dir.mkdir(parents=True, exist_ok=True)

    if args.init_only:
        print(json.dumps({"ok": True, "runs_dir": str(args.runs_dir), "runs": len(list_runs(args.runs_dir))}, ensure_ascii=False))
        return 0

    stop = threading.Event()
    watcher = threading.Thread(target=notification_watcher, args=(args.runs_dir, not args.no_notify, stop), daemon=True)
    watcher.start()

    server = ControlTowerServer((args.host, args.port), ControlTowerHandler, args.runs_dir)
    url = f"http://{args.host}:{args.port}/"
    print(f"AUTORIG control tower: {url}")
    if not args.no_open:
        subprocess.run(["open", url], check=False)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

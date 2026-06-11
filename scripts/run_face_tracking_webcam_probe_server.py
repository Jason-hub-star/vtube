#!/usr/bin/env python3
"""Serve a local MediaPipe webcam probe and save T1 face-tracking reports."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "experiments" / "reference-model-structure-001" / "face_tracking_webcam_probe"
REPORTS = ROOT / "experiments" / "reference-model-structure-001" / "reports"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5142

REQUIRED_OUTPUTS = [
    "ParamAngleX",
    "ParamAngleY",
    "ParamAngleZ",
    "ParamBodyAngleX",
    "ParamBodyAngleY",
    "ParamEyeLOpen",
    "ParamEyeROpen",
    "ParamEyeBallX",
    "ParamEyeBallY",
    "ParamMouthOpenY",
    "ParamMouthForm",
    "ParamBreath",
]

OUTPUT_RANGES = {
    "ParamAngleX": (-30.0, 30.0),
    "ParamAngleY": (-30.0, 30.0),
    "ParamAngleZ": (-30.0, 30.0),
    "ParamBodyAngleX": (-10.0, 10.0),
    "ParamBodyAngleY": (-10.0, 10.0),
    "ParamBodyAngleZ": (-10.0, 10.0),
    "ParamEyeLOpen": (0.0, 1.0),
    "ParamEyeROpen": (0.0, 1.0),
    "ParamEyeBallX": (-1.0, 1.0),
    "ParamEyeBallY": (-1.0, 1.0),
    "ParamMouthOpenY": (0.0, 1.0),
    "ParamMouthForm": (-1.0, 1.0),
    "ParamBreath": (0.0, 1.0),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    return parser.parse_args()


def rel(path: Path | str | None) -> str | None:
    if path is None:
        return None
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return p.resolve().as_posix()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def extrema(values: list[float]) -> dict[str, float]:
    if not values:
        return {"min": 0.0, "max": 0.0, "span": 0.0}
    mn = min(values)
    mx = max(values)
    return {"min": round(mn, 6), "max": round(mx, 6), "span": round(mx - mn, 6)}


def summarize_capture(payload: dict[str, Any]) -> dict[str, Any]:
    frames = payload.get("frames") or []
    valid_frames = [frame for frame in frames if frame.get("face_present")]
    duration_ms = int(payload.get("duration_ms") or 0)
    if duration_ms <= 0 and frames:
        duration_ms = int((frames[-1].get("t_ms") or 0) - (frames[0].get("t_ms") or 0))

    output_values: dict[str, list[float]] = {param: [] for param in OUTPUT_RANGES}
    missing_by_param = {param: 0 for param in REQUIRED_OUTPUTS}
    out_of_range: list[dict[str, Any]] = []
    nonfinite: list[dict[str, Any]] = []

    for index, frame in enumerate(valid_frames):
        outputs = frame.get("outputs") or {}
        for param in REQUIRED_OUTPUTS:
            value = outputs.get(param)
            if value is None:
                missing_by_param[param] += 1
                continue
            if not finite(value):
                nonfinite.append({"frame": index, "parameter": param, "value": value})
                continue
            numeric = float(value)
            output_values.setdefault(param, []).append(numeric)
            lo, hi = OUTPUT_RANGES.get(param, (-math.inf, math.inf))
            if numeric < lo or numeric > hi:
                out_of_range.append(
                    {
                        "frame": index,
                        "parameter": param,
                        "value": round(numeric, 6),
                        "range": [lo, hi],
                    }
                )

    frame_count = len(frames)
    valid_count = len(valid_frames)
    face_present_ratio = valid_count / frame_count if frame_count else 0.0
    coverage = {
        param: {
            "covered": len(output_values.get(param, [])) > 0 and missing_by_param.get(param, 0) == 0,
            "samples": len(output_values.get(param, [])),
            "missing_frames": missing_by_param.get(param, 0),
        }
        for param in REQUIRED_OUTPUTS
    }
    parameter_extrema = {param: extrema(values) for param, values in output_values.items() if values}
    movement_spans = {param: data["span"] for param, data in parameter_extrema.items()}
    movement_score = round(sum(movement_spans.values()), 6)
    low_motion = movement_score < 1.5

    failures: list[str] = []
    warnings: list[str] = []
    if frame_count < 120:
        failures.append("frame_count_below_120")
    if duration_ms < 8000:
        failures.append("duration_below_8_seconds")
    if face_present_ratio < 0.5:
        failures.append("face_present_ratio_below_0_5")
    if any(not item["covered"] for item in coverage.values()):
        failures.append("required_parameter_coverage_missing")
    if out_of_range:
        failures.append("output_range_violation")
    if nonfinite:
        failures.append("nonfinite_output")
    if low_motion and not failures:
        warnings.append("low_motion_span_try_bigger_head_blink_mouth_movements")

    status = "PASS" if not failures else "FAIL"
    capture_class = "PASS_CAPTURE"
    if status == "FAIL":
        capture_class = "FAIL_CAPTURE"
    elif warnings:
        capture_class = "PASS_CAPTURE_WARN_LOW_MOTION"

    return {
        "report_id": "face_tracking_webcam_probe_report",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "capture_class": capture_class,
        "summary": {
            "webcam_required": True,
            "live_tracking_input": True,
            "frame_count": frame_count,
            "valid_face_frame_count": valid_count,
            "duration_ms": duration_ms,
            "face_present_ratio": round(face_present_ratio, 6),
            "required_output_count": len(REQUIRED_OUTPUTS),
            "movement_score": movement_score,
            "failure_count": len(failures),
            "warning_count": len(warnings),
        },
        "checks": {
            "required_coverage": coverage,
            "parameter_extrema": parameter_extrema,
            "failures": failures,
            "warnings": warnings,
            "out_of_range": out_of_range[:100],
            "nonfinite": nonfinite[:100],
        },
        "interpretation": {
            "ko": (
                "내장 웹캠 입력이 Cubism v2 필수 파라미터로 변환되는 T1 smoke를 통과했습니다."
                if status == "PASS"
                else "내장 웹캠 입력 수집 또는 파라미터 변환 조건이 아직 부족합니다."
            ),
            "next": (
                "다음은 이 파라미터 스트림으로 Live2D Web Player 모델 또는 새 v2 rig preview를 구동하는 T2 테스트입니다."
                if status == "PASS"
                else "카메라 권한, 얼굴 위치, 조명, 10초 이상 녹화 여부를 확인하고 다시 저장하세요."
            ),
        },
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    summary = report["summary"]
    lines = [
        "# Face Tracking Webcam Probe Report",
        "",
        f"- status: `{report['status']}`",
        f"- capture_class: `{report['capture_class']}`",
        f"- frame_count: `{summary['frame_count']}`",
        f"- valid_face_frame_count: `{summary['valid_face_frame_count']}`",
        f"- duration_ms: `{summary['duration_ms']}`",
        f"- face_present_ratio: `{summary['face_present_ratio']}`",
        f"- movement_score: `{summary['movement_score']}`",
        f"- webcam_required: `{summary['webcam_required']}`",
        "",
        "## Interpretation",
        "",
        f"- {report['interpretation']['ko']}",
        f"- next: {report['interpretation']['next']}",
        "",
        "## Required Coverage",
        "",
        "| Parameter | Covered | Samples | Missing Frames |",
        "|---|---:|---:|---:|",
    ]
    for param, item in sorted(report["checks"]["required_coverage"].items()):
        lines.append(f"| `{param}` | `{item['covered']}` | {item['samples']} | {item['missing_frames']} |")
    lines += [
        "",
        "## Parameter Extrema",
        "",
        "| Parameter | Min | Max | Span |",
        "|---|---:|---:|---:|",
    ]
    for param, item in sorted(report["checks"]["parameter_extrema"].items()):
        lines.append(f"| `{param}` | {item['min']} | {item['max']} | {item['span']} |")
    lines += [
        "",
        "## Failures / Warnings",
        "",
        f"- failures: `{', '.join(report['checks']['failures']) if report['checks']['failures'] else 'none'}`",
        f"- warnings: `{', '.join(report['checks']['warnings']) if report['checks']['warnings'] else 'none'}`",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class ProbeHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[webcam-probe] {self.address_string()} {fmt % args}")

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in ("", "/"):
            target = APP_DIR / "index.html"
        else:
            target = (APP_DIR / parsed.path.lstrip("/")).resolve()
            if not str(target).startswith(str(APP_DIR.resolve())):
                self.send_error(403)
                return
        if not target.exists() or not target.is_file():
            self.send_error(404)
            return
        data = target.read_bytes()
        content_type = "text/html; charset=utf-8" if target.suffix == ".html" else "application/octet-stream"
        if target.suffix == ".js":
            content_type = "text/javascript; charset=utf-8"
        elif target.suffix == ".css":
            content_type = "text/css; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/save-report":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length") or "0")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            report = summarize_capture(payload)
            raw_path = REPORTS / "face_tracking_webcam_probe_raw.json"
            json_path = REPORTS / "face_tracking_webcam_probe_report.json"
            md_path = REPORTS / "face_tracking_webcam_probe_report.md"
            write_json(raw_path, payload)
            write_json(json_path, report)
            write_markdown(md_path, report)
            self.send_json(
                200,
                {
                    "status": report["status"],
                    "capture_class": report["capture_class"],
                    "raw": rel(raw_path),
                    "json": rel(json_path),
                    "markdown": rel(md_path),
                    "summary": report["summary"],
                },
            )
        except Exception as exc:  # noqa: BLE001 - surfaced to local operator UI.
            self.send_json(500, {"status": "ERROR", "message": str(exc)})


def main() -> int:
    args = parse_args()
    if not (APP_DIR / "index.html").exists():
        raise SystemExit(f"missing probe app: {APP_DIR / 'index.html'}")
    server = ThreadingHTTPServer((args.host, args.port), ProbeHandler)
    print(f"Face tracking webcam probe: http://{args.host}:{args.port}/")
    print("Press Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping webcam probe.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

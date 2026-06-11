#!/usr/bin/env python3
"""Local server for the unified part-purity review UI."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import subprocess
import sys
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "review_app"
REPORT_DIR = ROOT / "experiments" / "part-purity-001" / "reports"
REVIEW_PATH = REPORT_DIR / "part_visual_review.json"
FIX_QUEUE_PATH = REPORT_DIR / "ai_fix_queue.json"
MANIFEST_PATH = APP_DIR / "review_manifest.json"
PSD_AUTO_BUILD_EXPERIMENTS = {"see-through-mps-compat-002", "imagen-live2d-001"}

NEGATIVE_PROMPT_HINTS = {
    "hair_mixed": "no hair strands, no bangs, no side hair, no hair shadow",
    "skin_mixed": "no skin area, no face fill, no neck fill",
    "eye_white_mixed": "no sclera, no white eyeball region",
    "iris_mixed": "no iris, no pupil, no black eye disk",
    "line_cut": "complete continuous line art, uncropped outline",
    "alpha_dirty": "clean alpha, transparent background, no stray residue",
    "bbox_too_tight": "include safe transparent margin around the part",
    "missing_underpaint": "include hidden underpaint where deformation reveals gaps",
    "wrong_shape": "match canonical silhouette, proportions, and placement",
    "semantic_too_coarse": "single layer is too broad; split into Live2D schema parts",
    "depth_order_wrong": "wrong front/back order; separate by draw order and occlusion",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    return json.loads(path.read_text())


def load_manifest() -> dict:
    return load_json(MANIFEST_PATH, {"sections": {}})


def manifest_items_by_id() -> dict[str, dict]:
    manifest = load_manifest()
    items = {}
    for section_items in manifest.get("sections", {}).values():
        for item in section_items:
            items[item["part_id"]] = item
    return items


def experiment_report_paths(experiment_id: str) -> tuple[Path, Path]:
    report_dir = ROOT / "experiments" / experiment_id / "reports"
    return report_dir / "part_visual_review.json", report_dir / "ai_fix_queue.json"


def manifest_experiment_ids() -> list[str]:
    manifest = load_manifest()
    ids = set()
    if manifest.get("mode") != "mps_only":
        ids.add("part-purity-001")
    for section_items in manifest.get("sections", {}).values():
        for item in section_items:
            ids.add(item.get("experiment_id", "part-purity-001"))
    return sorted(ids)


def load_combined_review() -> dict:
    visible_ids = set(manifest_items_by_id())
    combined = {
        "schema_version": 1,
        "experiment_id": "combined-review",
        "reviews": {},
    }
    for experiment_id in manifest_experiment_ids():
        review_path, _ = experiment_report_paths(experiment_id)
        review = load_json(review_path, {"reviews": {}})
        combined["reviews"].update(
            {
                part_id: value
                for part_id, value in review.get("reviews", {}).items()
                if part_id in visible_ids
            }
        )
    return combined


def load_combined_fix_queue() -> dict:
    visible_ids = set(manifest_items_by_id())
    items = []
    for experiment_id in manifest_experiment_ids():
        _, fix_queue_path = experiment_report_paths(experiment_id)
        queue = load_json(fix_queue_path, {"items": []})
        items.extend([item for item in queue.get("items", []) if item.get("part_id") in visible_ids])
    return {
        "schema_version": 1,
        "experiment_id": "combined-review",
        "items": items,
        "counts": {"queued": len(items)},
    }


def normalize_review_payload(payload: dict) -> dict:
    reviews = payload.get("reviews", {})
    if isinstance(reviews, list):
        reviews = {item["part_id"]: item for item in reviews if item.get("part_id")}
    normalized = {}
    for part_id, review in reviews.items():
        if not isinstance(review, dict):
            continue
        verdict = review.get("verdict", "UNREVIEWED")
        normalized[part_id] = {
            "part_id": part_id,
            "verdict": verdict,
            "issue_tags": sorted(set(review.get("issue_tags", []))),
            "human_note": review.get("human_note") or review.get("note") or "",
            "updated_at": review.get("updated_at") or now(),
        }
    return normalized


def suggested_mode(item: dict, review: dict) -> str:
    verdict = review.get("verdict")
    tags = set(review.get("issue_tags", []))
    if verdict == "X":
        return "regenerate_part"
    if "alpha_dirty" in tags or "bbox_too_tight" in tags:
        return "alpha_cleanup"
    if "hair_mixed" in tags or "skin_mixed" in tags:
        return "mask_cleanup_or_regenerate"
    return item.get("suggested_generation_mode", "manual_review")


def build_fix_queue(review_doc: dict, experiment_id: str, review_path: Path) -> dict:
    items_by_id = manifest_items_by_id()
    queue_items = []
    for part_id, review in review_doc.get("reviews", {}).items():
        if review.get("verdict") not in {"X", "REVISE"}:
            continue
        item = items_by_id.get(part_id, {})
        tags = review.get("issue_tags", [])
        hints = [NEGATIVE_PROMPT_HINTS[tag] for tag in tags if tag in NEGATIVE_PROMPT_HINTS]
        queue_items.append(
            {
                "part_id": part_id,
                "original_part_id": item.get("original_part_id", part_id),
                "experiment_id": item.get("experiment_id", experiment_id),
                "ko_name": item.get("ko_name", part_id),
                "section": item.get("section"),
                "group": item.get("group"),
                "verdict": review.get("verdict"),
                "failure_tags": tags,
                "human_note": review.get("human_note", ""),
                "source_image": item.get("image_path"),
                "canonical_image": item.get("canonical_path"),
                "overlay_image": item.get("overlay_path"),
                "include_in_import_psd": item.get("include_in_import_psd", False),
                "suggested_generation_mode": suggested_mode(item, review),
                "negative_prompt_hints": hints,
            }
        )
    queue_items.sort(key=lambda row: (row.get("section") or "", row.get("group") or "", row["part_id"]))
    return {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "generated_at": now(),
        "source_review": str(review_path.relative_to(ROOT)),
        "items": queue_items,
        "counts": {"queued": len(queue_items)},
    }


def cubism_python() -> str:
    venv_python = ROOT / ".venv-cubism" / "bin" / "python"
    return str(venv_python) if venv_python.exists() else sys.executable


def auto_build_psd_candidate(experiment_id: str) -> dict | None:
    if experiment_id not in PSD_AUTO_BUILD_EXPERIMENTS:
        return None
    cmd = [
        cubism_python(),
        str(ROOT / "scripts" / "build_seethrough_psd_candidate.py"),
        "--experiment-id",
        experiment_id,
    ]
    completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=120)
    report_path = ROOT / "experiments" / experiment_id / "reports" / "psd_candidate_gate_report.json"
    report = load_json(report_path, {}) if report_path.exists() else {}
    return {
        "experiment_id": experiment_id,
        "command": cmd,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
        "status": report.get("status", "BUILD_FAILED" if completed.returncode else "UNKNOWN"),
        "accepted_layer_count": report.get("accepted_layer_count"),
        "psd_candidate": report.get("psd_candidate"),
    }


def rebuild_review_manifest_mps() -> dict:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "build_review_manifest.py"),
        "--mps-only",
    ]
    completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=120)
    return {
        "command": cmd,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }


def decode_data_url(data_url: str) -> bytes:
    prefix = "data:image/png;base64,"
    if not data_url.startswith(prefix):
        raise ValueError("mask_data_url must be a PNG data URL")
    return base64.b64decode(data_url.removeprefix(prefix), validate=True)


def save_manual_mask(payload: dict) -> dict:
    part_id = payload.get("part_id")
    experiment_id = payload.get("experiment_id") or manifest_items_by_id().get(part_id, {}).get("experiment_id")
    mask_data_url = payload.get("mask_data_url")
    if not part_id:
        raise ValueError("part_id is required")
    if experiment_id != "see-through-mps-compat-002":
        raise ValueError("manual masks are currently enabled only for see-through-mps-compat-002")
    if not mask_data_url:
        raise ValueError("mask_data_url is required")

    mask_dir = ROOT / "experiments" / experiment_id / "manual_masks"
    mask_dir.mkdir(parents=True, exist_ok=True)
    safe_part_id = "".join(char if char.isalnum() or char in "._-" else "_" for char in part_id)
    mask_path = mask_dir / f"{safe_part_id}.png"
    mask_path.write_bytes(decode_data_url(mask_data_url))

    cmd = [
        cubism_python(),
        str(ROOT / "scripts" / "apply_mps_manual_mask.py"),
        "--experiment-id",
        experiment_id,
        "--part-id",
        part_id,
        "--mask-path",
        str(mask_path),
    ]
    completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=120)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "manual mask apply failed")
    apply_result = json.loads(completed.stdout)
    manifest_build = rebuild_review_manifest_mps()
    if manifest_build["returncode"] != 0:
        raise RuntimeError(manifest_build["stderr_tail"] or manifest_build["stdout_tail"] or "manifest rebuild failed")
    return {
        "ok": True,
        "manual_mask": apply_result,
        "manifest_build": manifest_build,
    }


def save_experiment_review(experiment_id: str, incoming: dict) -> dict:
    review_path, fix_queue_path = experiment_report_paths(experiment_id)
    review_path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_json(
        review_path,
        {
            "schema_version": 1,
            "experiment_id": experiment_id,
            "created_at": now(),
            "reviews": {},
        },
    )
    reviews = existing.get("reviews", {})
    reviews.update(incoming)
    review_doc = {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "created_at": existing.get("created_at", now()),
        "updated_at": now(),
        "source_manifest": "review_app/review_manifest.json",
        "reviews": reviews,
    }
    for metadata_key in ["review_session", "note"]:
        if metadata_key in existing:
            review_doc[metadata_key] = existing[metadata_key]
    review_path.write_text(json.dumps(review_doc, ensure_ascii=False, indent=2) + "\n")
    fix_queue = build_fix_queue(review_doc, experiment_id, review_path)
    fix_queue_path.write_text(json.dumps(fix_queue, ensure_ascii=False, indent=2) + "\n")
    psd_candidate_build = auto_build_psd_candidate(experiment_id)
    return {
        "experiment_id": experiment_id,
        "review_path": str(review_path.relative_to(ROOT)),
        "fix_queue_path": str(fix_queue_path.relative_to(ROOT)),
        "review_count": len(reviews),
        "fix_queue_count": len(fix_queue["items"]),
        "psd_candidate_build": psd_candidate_build,
    }


def save_review(payload: dict) -> dict:
    incoming = normalize_review_payload(payload)
    items_by_id = manifest_items_by_id()
    grouped: dict[str, dict] = {}
    for part_id, review in incoming.items():
        experiment_id = items_by_id.get(part_id, {}).get("experiment_id", "part-purity-001")
        grouped.setdefault(experiment_id, {})[part_id] = review

    saved = [save_experiment_review(experiment_id, reviews) for experiment_id, reviews in sorted(grouped.items())]
    return {
        "ok": True,
        "saved": saved,
        "review_count": sum(item["review_count"] for item in saved),
        "fix_queue_count": sum(item["fix_queue_count"] for item in saved),
    }


def safe_join(base: Path, requested: str) -> Path | None:
    requested = requested.lstrip("/")
    path = (base / requested).resolve()
    try:
        path.relative_to(base.resolve())
    except ValueError:
        return None
    return path


class ReviewHandler(BaseHTTPRequestHandler):
    server_version = "PartPurityReview/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path == "/api/review":
            self.send_json(
                {
                    "review": load_combined_review(),
                    "fix_queue": load_combined_fix_queue(),
                }
            )
            return
        if path == "/review_manifest.json":
            self.serve_file(MANIFEST_PATH)
            return
        if path.startswith("/assets/"):
            asset_path = safe_join(ROOT, path.removeprefix("/assets/"))
            if asset_path is None:
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            self.serve_file(asset_path)
            return
        static_path = "index.html" if path in {"/", ""} else path.lstrip("/")
        file_path = safe_join(APP_DIR, static_path)
        if file_path is None:
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        self.serve_file(file_path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path not in {"/api/save-review", "/api/save-mask"}:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            result = save_manual_mask(payload) if parsed.path == "/api/save-mask" else save_review(payload)
        except Exception as exc:  # noqa: BLE001
            self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        self.send_json(result)

    def serve_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        data = path.read_bytes()
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
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8040, type=int)
    args = parser.parse_args()

    if not MANIFEST_PATH.exists():
        raise SystemExit("review_app/review_manifest.json is missing. Run scripts/build_review_manifest.py first.")

    server = ThreadingHTTPServer((args.host, args.port), ReviewHandler)
    print(f"Part purity review app: http://{args.host}:{args.port}/")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

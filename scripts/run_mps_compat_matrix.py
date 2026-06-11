#!/usr/bin/env python3
"""Run the See-through Apple Silicon MPS compatibility matrix."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_EXP = ROOT / "experiments" / "see-through-layer-decomp-001"
RUNNER = ROOT / "scripts" / "run_comfyui_seethrough_prompt.py"
COMFYUI_INPUT = SOURCE_EXP / "external_repos" / "ComfyUI" / "input"
COMFYUI_OUTPUT = SOURCE_EXP / "external_repos" / "ComfyUI" / "output"
EXP = ROOT / "experiments" / "see-through-mps-compat-002"
MATRIX_PATH = EXP / "mps_run_matrix.json"
REPORT_DIR = EXP / "reports"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def load_matrix() -> dict[str, Any]:
    if not MATRIX_PATH.exists():
        raise FileNotFoundError("Run scripts/setup_mps_compat_002.py first.")
    return json.loads(MATRIX_PATH.read_text())


def configure_experiment(experiment_id: str) -> None:
    global EXP, MATRIX_PATH, REPORT_DIR
    EXP = ROOT / "experiments" / experiment_id
    MATRIX_PATH = EXP / "mps_run_matrix.json"
    REPORT_DIR = EXP / "reports"


def selected_cases(matrix: dict[str, Any], requested: str, include_manual: bool) -> list[dict[str, Any]]:
    cases = matrix.get("matrix", [])
    if requested != "all":
        cases = [case for case in cases if case["case_id"] == requested]
        if not cases:
            raise ValueError(f"Unknown case: {requested}")
    if not include_manual:
        cases = [case for case in cases if case.get("status") != "MANUAL_ONLY"]
    return cases


def copy_input(case: dict[str, Any]) -> dict[str, str]:
    source = EXP / "input" / case["input_image"]
    if not source.exists():
        raise FileNotFoundError(f"Missing case input: {source}")
    COMFYUI_INPUT.mkdir(parents=True, exist_ok=True)
    target = COMFYUI_INPUT / case["input_image"]
    shutil.copy2(source, target)
    return {
        "source": str(source.relative_to(ROOT)),
        "target": str(target.relative_to(ROOT)),
    }


def command_for_case(matrix: dict[str, Any], case: dict[str, Any], args: argparse.Namespace) -> list[str]:
    prefix_base = case.get("filename_prefix") or matrix.get("filename_prefix_base") or matrix.get("character_id") or EXP.name
    prefix = f"{prefix_base}_{case['case_id']}"
    report_path = EXP / "reports" / f"{case['case_id']}_inference_report.json"
    return [
        sys.executable,
        str(RUNNER),
        "--experiment-id",
        matrix.get("experiment_id", EXP.name),
        "--experiment-dir",
        str(SOURCE_EXP.relative_to(ROOT)),
        "--output-dir",
        str(COMFYUI_OUTPUT.relative_to(ROOT)),
        "--report-path",
        str(report_path.relative_to(ROOT)),
        "--client-id",
        f"vtube-{case['case_id']}",
        "--base-url",
        args.base_url,
        "--timeout",
        str(args.timeout_per_case),
        "--server-timeout",
        str(args.server_timeout),
        "--poll-interval",
        str(args.poll_interval),
        "--input-image",
        case["input_image"],
        "--resolution",
        str(case["resolution"]),
        "--steps",
        str(case["steps"]),
        "--depth-resolution",
        str(case["depth_resolution"]),
        "--filename-prefix",
        prefix,
    ]


def normalize_if_possible(case: dict[str, Any]) -> dict[str, Any]:
    report_path = EXP / "reports" / f"{case['case_id']}_inference_report.json"
    if not report_path.exists():
        return {"status": "SKIPPED_NO_INFERENCE_REPORT"}
    report = json.loads(report_path.read_text())
    layers = report.get("layers_json", [])
    if not layers:
        return {"status": "SKIPPED_NO_LAYERS_JSON"}
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "normalize_seethrough_outputs.py"),
        "--experiment-id",
        EXP.name,
        "--experiment-dir",
        str(EXP.relative_to(ROOT)),
        "--canonical-path",
        str((EXP / "canonical" / "canonical_front_2048.png").relative_to(ROOT)),
        "--layers-json",
        layers[-1],
    ]
    completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=600)
    return {
        "status": "PASS_NORMALIZED" if completed.returncode == 0 else "FAIL_NORMALIZE",
        "command": cmd,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }


def run_case(matrix: dict[str, Any], case: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    env = os.environ.copy()
    env.update(case.get("env", {}))
    copied = copy_input(case)
    cmd = command_for_case(matrix, case, args)
    result: dict[str, Any] = {
        "case_id": case["case_id"],
        "started_at": now(),
        "settings": case,
        "copied_input": copied,
        "command": cmd,
        "dry_run": args.dry_run,
    }
    if args.dry_run:
        result["status"] = "DRY_RUN_READY"
        result["env"] = {key: env.get(key) for key in case.get("env", {})}
        return result

    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=args.timeout_per_case + args.server_timeout + 120,
    )
    result.update(
        {
            "returncode": completed.returncode,
            "stdout_tail": completed.stdout[-4000:],
            "stderr_tail": completed.stderr[-4000:],
            "status": "PASS_RUNNER" if completed.returncode == 0 else "FAIL_RUNNER",
        }
    )
    result["normalize"] = normalize_if_possible(case)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run low-resolution MPS See-through compatibility cases")
    parser.add_argument("--experiment-id", default="see-through-mps-compat-002")
    parser.add_argument("--base-url", default="http://127.0.0.1:8188")
    parser.add_argument("--case", default="all", help="case id or all")
    parser.add_argument("--include-manual", action="store_true", help="include HIGH_WATERMARK_RATIO=0.0 manual case")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--continue-on-fail", action="store_true")
    parser.add_argument("--timeout-per-case", type=int, default=3600)
    parser.add_argument("--server-timeout", type=int, default=60)
    parser.add_argument("--poll-interval", type=int, default=10)
    args = parser.parse_args()

    configure_experiment(args.experiment_id)
    matrix = load_matrix()
    cases = selected_cases(matrix, args.case, args.include_manual)
    if not cases:
        raise SystemExit("No cases selected.")

    results = []
    for case in cases:
        result = run_case(matrix, case, args)
        results.append(result)
        save_json(REPORT_DIR / f"{case['case_id']}_run_report.json", result)
        if not args.continue_on_fail and result["status"].startswith("FAIL"):
            break

    summary = {
        "schema_version": 1,
        "experiment_id": args.experiment_id,
        "generated_at": now(),
        "selected_case": args.case,
        "dry_run": args.dry_run,
        "results": results,
        "counts": {
            "selected": len(cases),
            "ran": len(results),
            "passed": sum(1 for item in results if item["status"].startswith("PASS") or item["status"] == "DRY_RUN_READY"),
            "failed": sum(1 for item in results if item["status"].startswith("FAIL")),
        },
    }
    save_json(REPORT_DIR / "mps_matrix_run_report.json", summary)
    print(json.dumps(summary["counts"], ensure_ascii=False, indent=2))
    return 0 if summary["counts"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

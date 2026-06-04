#!/usr/bin/env python3
"""Prepare and probe a Mac ComfyUI + ComfyUI-See-through experiment.

This script intentionally separates setup/probing from actual See-through
inference. First-run model downloads can be several GB and should be launched
explicitly from ComfyUI after this gate passes.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "see-through-layer-decomp-001"
REPORT_DIR = EXP / "reports"
EXTERNAL = EXP / "external_repos"
COMFYUI_DIR = EXTERNAL / "ComfyUI"
VENV = EXP / ".venv-comfyui"
PLUGIN_SOURCE = ROOT / "experiments" / "validation-smoke-001" / "external_repos" / "ComfyUI-See-through"
PLUGIN_TARGET = COMFYUI_DIR / "custom_nodes" / "ComfyUI-See-through"
WORKFLOW_SOURCE = PLUGIN_SOURCE / "workflows" / "seethrough-basic.json"
WORKFLOW_OUT = EXP / "workflow" / "seethrough-basic-vtube.json"
INPUT_SOURCE = ROOT / "experiments" / "concept-regeneration-001" / "canonical" / "canonical_front_2048.png"
INPUT_DIR = EXP / "input"
INPUT_2048 = INPUT_DIR / "canonical_front_2048.png"
INPUT_1280 = INPUT_DIR / "canonical_front_1280.png"
COMFY_INPUT_1280 = COMFYUI_DIR / "input" / INPUT_1280.name
SETUP_REPORT = REPORT_DIR / "comfyui_setup_report.json"
QA_REPORT = EXP / "qa_report.md"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def run(cmd: list[str], *, cwd: Path | None = None, timeout: int | None = None) -> dict[str, Any]:
    started = now()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "cmd": cmd,
            "cwd": str(cwd) if cwd else None,
            "started_at": started,
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-6000:],
            "stderr_tail": proc.stderr[-6000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "cmd": cmd,
            "cwd": str(cwd) if cwd else None,
            "started_at": started,
            "returncode": None,
            "timeout_seconds": timeout,
            "stdout_tail": (exc.stdout or "")[-6000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-6000:] if isinstance(exc.stderr, str) else "",
        }


def ensure_inputs() -> None:
    if not INPUT_SOURCE.exists():
        raise FileNotFoundError(INPUT_SOURCE)
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(INPUT_SOURCE, INPUT_2048)
    img = Image.open(INPUT_SOURCE).convert("RGBA")
    img.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (1280, 1280), (0, 0, 0, 0))
    x = (1280 - img.width) // 2
    y = (1280 - img.height) // 2
    canvas.paste(img, (x, y), img)
    canvas.save(INPUT_1280)
    if COMFYUI_DIR.exists():
        COMFY_INPUT_1280.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(INPUT_1280, COMFY_INPUT_1280)


def clone_comfyui(skip_clone: bool) -> dict[str, Any]:
    if COMFYUI_DIR.exists():
        return {"status": "EXISTS", "path": str(COMFYUI_DIR)}
    if skip_clone:
        return {"status": "SKIPPED", "path": str(COMFYUI_DIR)}
    EXTERNAL.mkdir(parents=True, exist_ok=True)
    result = run(["git", "clone", "--depth", "1", "https://github.com/comfyanonymous/ComfyUI.git", str(COMFYUI_DIR)], timeout=600)
    result["status"] = "PASS" if result["returncode"] == 0 else "FAIL"
    return result


def install_custom_node() -> dict[str, Any]:
    if not COMFYUI_DIR.exists():
        return {"status": "BLOCKED_NO_COMFYUI"}
    if not PLUGIN_SOURCE.exists():
        return {"status": "BLOCKED_NO_PLUGIN_SOURCE", "source": str(PLUGIN_SOURCE)}
    PLUGIN_TARGET.parent.mkdir(parents=True, exist_ok=True)
    if PLUGIN_TARGET.exists() or PLUGIN_TARGET.is_symlink():
        try:
            if PLUGIN_TARGET.resolve() == PLUGIN_SOURCE.resolve():
                return {"status": "EXISTS", "target": str(PLUGIN_TARGET), "source": str(PLUGIN_SOURCE)}
        except FileNotFoundError:
            pass
        return {"status": "BLOCKED_TARGET_EXISTS", "target": str(PLUGIN_TARGET)}
    PLUGIN_TARGET.symlink_to(PLUGIN_SOURCE, target_is_directory=True)
    return {"status": "PASS", "target": str(PLUGIN_TARGET), "source": str(PLUGIN_SOURCE)}


def write_workflow() -> dict[str, Any]:
    if not WORKFLOW_SOURCE.exists():
        return {"status": "BLOCKED_NO_WORKFLOW_SOURCE"}
    workflow = json.loads(WORKFLOW_SOURCE.read_text())
    for node in workflow.get("nodes", []):
        if node.get("type") == "LoadImage":
            node["widgets_values"] = [INPUT_1280.name, "image"]
        elif node.get("type") == "SeeThrough_GenerateLayers":
            node["widgets_values"] = [42, "fixed", 1280, 30]
        elif node.get("type") == "SeeThrough_GenerateDepth":
            node["widgets_values"] = [42, "fixed", 720]
        elif node.get("type") == "SeeThrough_SavePSD":
            node["widgets_values"] = ["white_wolf_goth_seethrough", "Download PSD", "Download Depth PSD"]
    WORKFLOW_OUT.parent.mkdir(parents=True, exist_ok=True)
    WORKFLOW_OUT.write_text(json.dumps(workflow, ensure_ascii=False, indent=2) + "\n")
    return {"status": "PASS", "workflow": str(WORKFLOW_OUT.relative_to(ROOT))}


def venv_python() -> Path:
    return VENV / "bin" / "python"


def install_dependencies(skip_install_deps: bool) -> list[dict[str, Any]]:
    if skip_install_deps:
        return [
            {
                "status": "SKIPPED_EXISTING_VENV" if venv_python().exists() else "SKIPPED_NO_VENV",
                "reason": "--skip-install-deps",
                "python": str(venv_python()) if venv_python().exists() else None,
            }
        ]
    commands: list[dict[str, Any]] = []
    commands.append(run(["uv", "venv", "--python", "3.11", str(VENV)], timeout=600))
    if commands[-1]["returncode"] != 0:
        commands[-1]["status"] = "FAIL"
        return commands

    python = str(venv_python())
    comfy_req = COMFYUI_DIR / "requirements.txt"
    if comfy_req.exists():
        commands.append(run(["uv", "pip", "install", "--python", python, "-r", str(comfy_req)], timeout=1800))
        commands[-1]["status"] = "PASS" if commands[-1]["returncode"] == 0 else "FAIL"

    plugin_req = PLUGIN_SOURCE / "requirements.txt"
    if plugin_req.exists():
        commands.append(run(["uv", "pip", "install", "--python", python, "-r", str(plugin_req)], timeout=1800))
        commands[-1]["status"] = "PASS" if commands[-1]["returncode"] == 0 else "FAIL"
        if commands[-1]["returncode"] != 0:
            mac_req = EXP / "requirements-seethrough-mac.txt"
            lines = [
                line
                for line in plugin_req.read_text().splitlines()
                if line.strip() and not line.strip().startswith("bitsandbytes")
            ]
            mac_req.write_text("\n".join(lines) + "\n")
            commands.append(run(["uv", "pip", "install", "--python", python, "-r", str(mac_req)], timeout=1800))
            commands[-1]["status"] = "PASS_MAC_FALLBACK" if commands[-1]["returncode"] == 0 else "FAIL_MAC_FALLBACK"
    return commands


def torch_probe(python: Path) -> dict[str, Any]:
    code = """
import json, platform, sys
try:
    import torch
    payload = {
        "python": sys.version,
        "platform": platform.platform(),
        "torch": torch.__version__,
        "cuda": torch.cuda.is_available(),
        "mps": torch.backends.mps.is_available(),
        "mps_built": torch.backends.mps.is_built(),
    }
except Exception as exc:
    payload = {"error": repr(exc), "python": sys.version}
print(json.dumps(payload))
"""
    result = run([str(python), "-c", code], timeout=120)
    try:
        result["payload"] = json.loads(result["stdout_tail"].strip().splitlines()[-1])
    except Exception:
        result["payload"] = {}
    return result


def node_load_probe(python: Path) -> dict[str, Any]:
    code = f"""
import importlib.util
import json
import sys
from pathlib import Path

comfy = Path({str(COMFYUI_DIR)!r})
plugin = Path({str(PLUGIN_TARGET)!r})
sys.path.insert(0, str(comfy))
spec = importlib.util.spec_from_file_location(
    "ComfyUI_See_through",
    plugin / "__init__.py",
    submodule_search_locations=[str(plugin)],
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
print(json.dumps({{
    "node_count": len(getattr(module, "NODE_CLASS_MAPPINGS", {{}})),
    "nodes": sorted(getattr(module, "NODE_CLASS_MAPPINGS", {{}}).keys()),
}}))
"""
    result = run([str(python), "-c", code], timeout=240)
    try:
        result["payload"] = json.loads(result["stdout_tail"].strip().splitlines()[-1])
    except Exception:
        result["payload"] = {}
    return result


def status_from(report: dict[str, Any]) -> str:
    dep_results = report.get("dependency_install", [])
    if dep_results and not str(dep_results[0].get("status", "")).startswith("SKIPPED"):
        hard_fail = any(str(item.get("status", "")).startswith("FAIL") for item in dep_results)
        fallback_pass = any(item.get("status") == "PASS_MAC_FALLBACK" for item in dep_results)
        if hard_fail and not fallback_pass:
            return "BLOCKED_DEP"
    node_payload = report["node_load_probe"].get("payload", {})
    if report["node_load_probe"].get("returncode") != 0 or not node_payload.get("node_count"):
        return "BLOCKED_DEP"
    torch_payload = report["torch_probe"].get("payload", {})
    if torch_payload.get("mps"):
        return "PASS_MPS"
    return "PASS_CPU_SLOW"


def write_qa(report: dict[str, Any]) -> None:
    launch = report["launch_command"]
    QA_REPORT.write_text(
        "\n".join(
            [
                "# See-through Mac ComfyUI QA",
                "",
                f"Generated: {report['generated_at']}",
                f"Status: {report['status']}",
                "",
                "## Prepared Files",
                "",
                f"- 2048 input: `{INPUT_2048.relative_to(ROOT)}`",
                f"- 1280 ComfyUI input: `{INPUT_1280.relative_to(ROOT)}`",
                f"- Workflow: `{WORKFLOW_OUT.relative_to(ROOT)}`",
                f"- Setup report: `{SETUP_REPORT.relative_to(ROOT)}`",
                "",
                "## Launch",
                "",
                "```bash",
                " ".join(launch),
                "```",
                "",
                "## Gate",
                "",
                "- This report proves setup/node-load only.",
                "- Actual model download and decomposition output are not accepted until layer PNGs are normalized and visually reviewed.",
                "- O/X/REVISE review remains the production gate.",
                "",
            ]
        )
        + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare Mac ComfyUI + ComfyUI-See-through")
    parser.add_argument("--skip-clone", action="store_true")
    parser.add_argument("--skip-install-deps", action="store_true")
    args = parser.parse_args()

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    clone = clone_comfyui(args.skip_clone)
    node = install_custom_node()
    ensure_inputs()
    workflow = write_workflow()
    deps = install_dependencies(args.skip_install_deps)
    python = venv_python() if venv_python().exists() else Path(sys.executable)
    torch = torch_probe(python)
    node_probe = node_load_probe(python) if COMFYUI_DIR.exists() and PLUGIN_TARGET.exists() else {"returncode": 1, "payload": {}}
    launch_command = [
        str(python),
        str(COMFYUI_DIR / "main.py"),
        "--listen",
        "127.0.0.1",
        "--port",
        "8188",
    ]
    report = {
        "schema_version": 1,
        "experiment_id": "see-through-layer-decomp-001",
        "generated_at": now(),
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python_used_for_probe": str(python),
        },
        "source": {
            "canonical_2048": str(INPUT_SOURCE.relative_to(ROOT)),
            "plugin_source": str(PLUGIN_SOURCE.relative_to(ROOT)),
        },
        "clone_comfyui": clone,
        "custom_node": node,
        "workflow": workflow,
        "dependency_install": deps,
        "torch_probe": torch,
        "node_load_probe": node_probe,
        "launch_command": launch_command,
        "manual_steps": [
            "Run the launch command.",
            "Open http://127.0.0.1:8188/.",
            "Load experiments/see-through-layer-decomp-001/workflow/seethrough-basic-vtube.json.",
            "Run the workflow once and keep the generated *_layers.json plus layer PNG outputs.",
            "Run scripts/normalize_seethrough_outputs.py --layers-json <ComfyUI output layers.json>.",
            "Run scripts/build_review_manifest.py and review the See-through candidates in the local review app.",
        ],
    }
    report["status"] = status_from(report)
    save_json(SETUP_REPORT, report)
    write_qa(report)
    print(json.dumps({"status": report["status"], "report": str(SETUP_REPORT.relative_to(ROOT))}, ensure_ascii=False, indent=2))
    return 0 if report["status"] in {"PASS_MPS", "PASS_CPU_SLOW", "BLOCKED_DEP"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fetch official Live2D GitHub sample resources and build runtime catalogs."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "reference-model-structure-001"
GITHUB_DIR = EXPERIMENT / "official_github_samples"
REPOS_DIR = GITHUB_DIR / "repos"


OFFICIAL_REPOS = [
    {
        "id": "live2d_cubism_web_samples",
        "url": "https://github.com/Live2D/CubismWebSamples.git",
        "web_url": "https://github.com/Live2D/CubismWebSamples",
        "sparse_paths": ["Samples/Resources", "LICENSE.md", "NOTICE.md", "README.md"],
        "note": "Official Live2D Cubism Web SDK samples. Runtime resources only.",
    },
    {
        "id": "live2d_cubism_native_samples",
        "url": "https://github.com/Live2D/CubismNativeSamples.git",
        "web_url": "https://github.com/Live2D/CubismNativeSamples",
        "sparse_paths": ["Samples/Resources", "LICENSE.md", "NOTICE.md", "README.md"],
        "note": "Official Live2D Cubism Native SDK samples. Runtime resources only.",
    },
    {
        "id": "live2d_cubism_java_samples",
        "url": "https://github.com/Live2D/CubismJavaSamples.git",
        "web_url": "https://github.com/Live2D/CubismJavaSamples",
        "sparse_paths": ["Samples/Resources", "LICENSE.md", "NOTICE.md", "README.md"],
        "note": "Official Live2D Cubism Java SDK samples. Runtime resources only.",
    },
    {
        "id": "live2d_cubism_web_motionsync",
        "url": "https://github.com/Live2D/CubismWebMotionSyncComponents.git",
        "web_url": "https://github.com/Live2D/CubismWebMotionSyncComponents",
        "sparse_paths": ["Samples/Resources", "LICENSE.md", "NOTICE.md", "README.md"],
        "note": "Official Live2D Web MotionSync sample resources. Runtime resources only.",
    },
    {
        "id": "live2d_garage_cubism_web_ar_sample",
        "url": "https://github.com/Live2D-Garage/CubismWebARSample.git",
        "web_url": "https://github.com/Live2D-Garage/CubismWebARSample",
        "sparse_paths": ["assets", "LICENSE.md", "NOTICE.md", "README.md"],
        "note": "Live2D Garage Web AR sample resources. Runtime resources only.",
    },
]


KEY_SUFFIXES = {
    "moc3": ".moc3",
    "model3_json": ".model3.json",
    "physics3_json": ".physics3.json",
    "motion3_json": ".motion3.json",
    "cdi3_json": ".cdi3.json",
    "exp3_json": ".exp3.json",
    "pose3_json": ".pose3.json",
}


PROFILE_KEY_HINTS = [
    ("haru_greeter", "haru_greeter"),
    ("gantzert", "gantzert_felixander"),
    ("felixander", "gantzert_felixander"),
    ("param_ctrl", "param_ctrl"),
    ("hiyori", "hiyori"),
    ("mark", "mark"),
    ("miku", "miku"),
    ("unity", "unitychan"),
    ("chitose", "chitose"),
    ("epsilon", "epsilon"),
    ("haruto", "haruto"),
    ("koharu", "koharu"),
    ("haru", "haru"),
    ("mao", "mao"),
    ("miara", "miara"),
    ("natori", "natori"),
    ("ren", "ren"),
    ("rice", "rice"),
    ("shizuku", "shizuku"),
    ("tsumiki", "tsumiki"),
    ("wanko", "wanko"),
    ("tororo", "tororo_hijiki"),
    ("hijiki", "tororo_hijiki"),
    ("nito", "nito"),
    ("nico", "nito"),
    ("nietzsche", "nito"),
    ("nipsilon", "nito"),
    ("izumi", "izumi"),
    ("simple", "simple"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(EXPERIMENT), help="Reference model experiment directory.")
    parser.add_argument("--refresh", action="store_true", help="Delete and reclone official sample repos.")
    parser.add_argument("--skip-fetch", action="store_true", help="Use already fetched repos only.")
    return parser.parse_args()


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def slug(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9_.-]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "sample"


def profile_key_for_text(text: str) -> str | None:
    lower = text.lower()
    for token, key in PROFILE_KEY_HINTS:
        if token in lower:
            return key
    return None


def default_branch(repo_url: str) -> str | None:
    proc = run(["git", "ls-remote", "--symref", repo_url, "HEAD"])
    if proc.returncode != 0:
        return None
    for line in proc.stdout.splitlines():
        if line.startswith("ref:") and "refs/heads/" in line:
            return line.split("refs/heads/", 1)[1].split()[0]
    return None


def fetch_repo(repo: dict[str, Any], dest: Path, refresh: bool, skip_fetch: bool) -> dict[str, Any]:
    if refresh and dest.exists():
        shutil.rmtree(dest)
    if not dest.exists() and not skip_fetch:
        branch = default_branch(repo["url"])
        cmd = ["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse"]
        if branch:
            cmd.extend(["--branch", branch])
        cmd.extend([repo["url"], str(dest)])
        clone = run(cmd)
        if clone.returncode != 0:
            return {
                "status": "FETCH_FAILED",
                "stderr": clone.stderr.strip(),
                "stdout": clone.stdout.strip(),
            }
        sparse = run(["git", "sparse-checkout", "set", "--no-cone", *repo["sparse_paths"]], cwd=dest)
        if sparse.returncode != 0:
            return {
                "status": "SPARSE_FAILED",
                "stderr": sparse.stderr.strip(),
                "stdout": sparse.stdout.strip(),
            }
    if not dest.exists():
        return {"status": "MISSING_LOCAL_REPO"}

    commit = run(["git", "rev-parse", "HEAD"], cwd=dest)
    branch_name = run(["git", "branch", "--show-current"], cwd=dest)
    return {
        "status": "READY",
        "commit": commit.stdout.strip() if commit.returncode == 0 else None,
        "branch": branch_name.stdout.strip() if branch_name.returncode == 0 else None,
        "local_path": rel(dest),
    }


def collect_files(root: Path) -> dict[str, list[Path]]:
    found = {key: [] for key in KEY_SUFFIXES}
    if not root.exists():
        return found
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        lower = path.name.lower()
        for key, suffix in KEY_SUFFIXES.items():
            if lower.endswith(suffix):
                found[key].append(path)
    for paths in found.values():
        paths.sort()
    return found


def resolve_ref(model3_path: Path, value: str | None) -> Path | None:
    if not value:
        return None
    return (model3_path.parent / value).resolve()


def resolve_ref_list(model3_path: Path, values: list[str]) -> list[Path]:
    return [p for value in values if (p := resolve_ref(model3_path, value)) and p.exists()]


def model3_refs(model3_path: Path) -> dict[str, Any]:
    try:
        data = load_json(model3_path)
    except Exception:
        return {}
    refs = data.get("FileReferences") or {}
    motions = []
    for group_items in (refs.get("Motions") or {}).values():
        if isinstance(group_items, list):
            motions.extend(item.get("File") for item in group_items if isinstance(item, dict) and item.get("File"))
    expressions = [
        item.get("File")
        for item in refs.get("Expressions", [])
        if isinstance(item, dict) and item.get("File")
    ]
    return {
        "moc3": resolve_ref(model3_path, refs.get("Moc")),
        "physics3_json": resolve_ref(model3_path, refs.get("Physics")),
        "cdi3_json": resolve_ref(model3_path, refs.get("DisplayInfo")),
        "pose3_json": resolve_ref(model3_path, refs.get("Pose")),
        "motion3_json": resolve_ref_list(model3_path, motions),
        "exp3_json": resolve_ref_list(model3_path, expressions),
    }


def make_entry(repo: dict[str, Any], repo_dir: Path, model3_path: Path) -> dict[str, Any]:
    refs = model3_refs(model3_path)
    model_name = model3_path.name.removesuffix(".model3.json")
    profile_key = profile_key_for_text(f"{model_name} {model3_path.parent.name} {repo['id']}") or "OFFICIAL_PROFILE_MISSING"
    local_paths: dict[str, Any] = {"model3_json": rel(model3_path)}
    for key, value in refs.items():
        if isinstance(value, list):
            if value:
                local_paths[key] = [rel(p) for p in value]
        elif value and value.exists():
            local_paths[key] = rel(value)

    entry_id = slug(f"github_{repo['id']}_{model3_path.relative_to(repo_dir).with_suffix('').as_posix()}")
    return {
        "id": entry_id,
        "name": model_name,
        "source_url": repo["web_url"],
        "source_type": "OFFICIAL_GITHUB_SAMPLE",
        "license_status": "OFFICIAL_SDK_SAMPLE_TERMS_REVIEWED",
        "analysis_mode": "RUNTIME_ONLY",
        "official_profile_key": profile_key,
        "has_cmo3": False,
        "has_moc3": bool(local_paths.get("moc3")),
        "has_model3_json": True,
        "has_physics3_json": bool(local_paths.get("physics3_json")),
        "has_psd": False,
        "local_paths": local_paths,
        "structure_report_path": None,
        "notes": [
            repo["note"],
            "Runtime-only structural analysis; do not reuse art, textures, or character designs.",
        ],
        "reuse_decision": "REFERENCE_ONLY",
    }


def build_catalog(repo_records: list[dict[str, Any]], out_dir: Path) -> dict[str, Any]:
    models = []
    for record in repo_records:
        if record["fetch"].get("status") != "READY":
            continue
        repo = record["repo"]
        repo_dir = Path(record["fetch"]["local_path"])
        if not repo_dir.is_absolute():
            repo_dir = ROOT / repo_dir
        for model3_path in sorted(repo_dir.rglob("*.model3.json")):
            models.append(make_entry(repo, repo_dir, model3_path.resolve()))
    return {
        "schema_version": 1,
        "purpose": "Official Live2D GitHub SDK/Garage runtime sample catalog.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "safety_note": "Runtime-only structure and pattern learning. Do not reuse official sample art, textures, or character designs.",
        "models": models,
    }


def merge_catalogs(out_dir: Path, github_catalog: dict[str, Any]) -> dict[str, Any]:
    models: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in [out_dir / "catalog.official_samples.json"]:
        if path.exists():
            catalog = load_json(path)
            for item in catalog.get("models", []):
                if item.get("id") not in seen:
                    models.append(item)
                    seen.add(item.get("id"))
    for item in github_catalog.get("models", []):
        if item.get("id") not in seen:
            models.append(item)
            seen.add(item.get("id"))
    return {
        "schema_version": 1,
        "purpose": "Combined official Live2D sample catalog from local official zips plus official GitHub runtime samples.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "safety_note": "Use structure and pattern learning only. Do not reuse art, textures, PSD layers, or character designs.",
        "models": models,
    }


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out).expanduser().resolve()
    repos_dir = out_dir / "official_github_samples" / "repos"
    repo_records = []
    for repo in OFFICIAL_REPOS:
        dest = repos_dir / repo["id"]
        fetch = fetch_repo(repo, dest, refresh=args.refresh, skip_fetch=args.skip_fetch)
        files = collect_files(dest)
        repo_records.append(
            {
                "repo": repo,
                "fetch": fetch,
                "counts": {key: len(value) for key, value in files.items()},
            }
        )

    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repos": repo_records,
        "aggregate_counts": {
            key: sum(record["counts"].get(key, 0) for record in repo_records)
            for key in KEY_SUFFIXES
        },
    }
    write_json(out_dir / "official_github_samples" / "github_sample_manifest.json", manifest)

    github_catalog = build_catalog(repo_records, out_dir)
    write_json(out_dir / "catalog.official_github_samples.json", github_catalog)
    combined = merge_catalogs(out_dir, github_catalog)
    write_json(out_dir / "catalog.official_combined.json", combined)

    print(
        json.dumps(
            {
                "ok": True,
                "repos": len(repo_records),
                "ready_repos": sum(record["fetch"].get("status") == "READY" for record in repo_records),
                "aggregate_counts": manifest["aggregate_counts"],
                "github_models": len(github_catalog["models"]),
                "combined_models": len(combined["models"]),
                "manifest": rel(out_dir / "official_github_samples" / "github_sample_manifest.json"),
                "catalog": rel(out_dir / "catalog.official_github_samples.json"),
                "combined_catalog": rel(out_dir / "catalog.official_combined.json"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

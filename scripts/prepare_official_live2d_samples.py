#!/usr/bin/env python3
"""Safely extract official Live2D sample zips and build a model catalog."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "reference-model-structure-001"
OFFICIAL_DIR = EXPERIMENT / "official_samples"
EXTRACTED_DIR = OFFICIAL_DIR / "extracted"
OFFICIAL_SAMPLE_URL = "https://www.live2d.com/ko/learn/sample/"

DEFAULT_ZIPS = [
    "/Users/family/Downloads/chitose.zip",
    "/Users/family/Downloads/Epsilon.zip",
    "/Users/family/Downloads/haru_greeter_pro_jp.zip",
    "/Users/family/Downloads/haru.zip",
    "/Users/family/Downloads/hiyori_movie_pro_ko.zip",
    "/Users/family/Downloads/kei_ko.zip",
    "/Users/family/Downloads/koharu_haruto.zip",
    "/Users/family/Downloads/mao_pro_ko.zip",
    "/Users/family/Downloads/mark_movie_pro_ko.zip",
    "/Users/family/Downloads/miara_pro_en.zip",
    "/Users/family/Downloads/natori_pro_ko.zip",
    "/Users/family/Downloads/param_ctrl_pro_ko.zip",
    "/Users/family/Downloads/ren_pro_ko.zip",
    "/Users/family/Downloads/rice_pro_ko.zip",
    "/Users/family/Downloads/shizuku.zip",
    "/Users/family/Downloads/tsumiki.zip",
    "/Users/family/Downloads/Unitychan.zip",
    "/Users/family/Downloads/wanko.zip",
    "/Users/family/Downloads/hiyori_pro_ko.zip",
    "/Users/family/Downloads/miku_pro_jp.zip",
    "/Users/family/Downloads/tororo_hijiki.zip",
    "/Users/family/Downloads/nito.zip",
    "/Users/family/Downloads/izumi.zip",
    "/Users/family/Downloads/Gantzert_Felixander.zip",
]

KEY_SUFFIXES = {
    "cmo3": ".cmo3",
    "moc3": ".moc3",
    "model3_json": ".model3.json",
    "physics3_json": ".physics3.json",
    "motion3_json": ".motion3.json",
    "cdi3_json": ".cdi3.json",
    "exp3_json": ".exp3.json",
    "pose3_json": ".pose3.json",
    "psd": ".psd",
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
    ("kei", "kei"),
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
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_paths", nargs="*", help="Official Live2D sample zip paths.")
    parser.add_argument("--out", default=str(EXPERIMENT), help="Reference model experiment directory.")
    parser.add_argument("--no-extract", action="store_true", help="Inventory only; do not extract.")
    return parser.parse_args()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def profile_key_for_model(zip_id: str, model_path: Path) -> str | None:
    """Prefer the model-local path over the zip id for multi-model archives."""
    profile_key = profile_key_for_text(model_path.stem)
    if profile_key:
        return profile_key
    local_text = " ".join(model_path.parts[-5:]).lower()
    profile_key = profile_key_for_text(local_text)
    if profile_key:
        return profile_key
    return profile_key_for_text(zip_id)


def safe_extract(zip_path: Path, dest: Path) -> list[str]:
    extracted: list[str] = []
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            name = info.filename
            target = (dest / name).resolve()
            if not str(target).startswith(str(dest.resolve()) + "/") and target != dest.resolve():
                raise ValueError(f"unsafe zip member path: {name}")
            if name.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or target.stat().st_size != info.file_size:
                with z.open(info) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
            extracted.append(rel(target))
    return extracted


def inventory_zip(zip_path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
    lower_names = [n.lower() for n in names]
    counts = {
        key: sum(name.endswith(suffix) for name in lower_names)
        for key, suffix in KEY_SUFFIXES.items()
    }
    return {
        "zip_id": slug(zip_path.stem),
        "zip_path": str(zip_path),
        "exists": zip_path.exists(),
        "size_bytes": zip_path.stat().st_size if zip_path.exists() else None,
        "entry_count": len(names),
        "counts": counts,
        "key_files": [n for n in names if any(n.lower().endswith(s) for s in KEY_SUFFIXES.values())],
    }


def collect_files(root: Path) -> dict[str, list[Path]]:
    found = {key: [] for key in KEY_SUFFIXES}
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


def common_prefix_score(a: Path, b: Path) -> int:
    a_parts = a.parts
    b_parts = b.parts
    score = 0
    for left, right in zip(a_parts, b_parts):
        if left != right:
            break
        score += 1
    return score


def closest_path(anchor: Path, candidates: list[Path], stem_hint: str | None = None) -> Path | None:
    if not candidates:
        return None
    scored = []
    hint = (stem_hint or anchor.stem).lower().replace("_t01", "").replace("_t02", "").replace("_t03", "").replace("_t04", "").replace("_t05", "").replace("_t06", "").replace("_t07", "").replace("_t11", "")
    for item in candidates:
        lower = str(item).lower()
        score = common_prefix_score(anchor, item)
        if hint and hint in lower:
            score += 10
        if "runtime" in lower:
            score += 3
        scored.append((score, -len(item.parts), item))
    scored.sort(reverse=True)
    return scored[0][2]


def closest_paths(anchor: Path, candidates: list[Path], suffix_dir_tokens: tuple[str, ...] = ()) -> list[Path]:
    if not candidates:
        return []
    anchor_parent = anchor.parent
    selected = []
    for item in candidates:
        text = str(item).lower()
        if suffix_dir_tokens and not any(token in text for token in suffix_dir_tokens):
            continue
        if common_prefix_score(anchor_parent, item.parent) >= max(1, len(anchor_parent.parts) - 1):
            selected.append(item)
    if selected:
        return sorted(selected)
    return sorted(candidates)


def make_entry(
    zip_item: dict[str, Any],
    model_path: Path,
    files: dict[str, list[Path]],
    out_dir: Path,
    mode: str,
    extra_id: str = "",
) -> dict[str, Any]:
    profile_key = profile_key_for_model(zip_item["zip_id"], model_path)
    base_id = slug(f"{zip_item['zip_id']}_{model_path.stem}{'_' + extra_id if extra_id else ''}")
    model3 = closest_path(model_path, files["model3_json"])
    moc3 = closest_path(model_path, files["moc3"], model3.stem if model3 else None)
    physics = closest_path(model_path, files["physics3_json"], model3.stem if model3 else None)
    cdi = closest_path(model_path, files["cdi3_json"], model3.stem if model3 else None)
    pose = closest_path(model_path, files["pose3_json"], model3.stem if model3 else None)
    motions = closest_paths(model3 or model_path, files["motion3_json"], ("motion", "motions"))
    expressions = closest_paths(model3 or model_path, files["exp3_json"], ("expression", "expressions", "exp"))
    psds = closest_paths(model_path, files["psd"])

    local_paths: dict[str, Any] = {}
    if mode == "FULL_STRUCTURE":
        local_paths["cmo3"] = rel(model_path)
    if moc3:
        local_paths["moc3"] = rel(moc3)
    if model3:
        local_paths["model3_json"] = rel(model3)
    if physics:
        local_paths["physics3_json"] = rel(physics)
    if cdi:
        local_paths["cdi3_json"] = rel(cdi)
    if pose:
        local_paths["pose3_json"] = rel(pose)
    if motions:
        local_paths["motion3_json"] = [rel(p) for p in motions]
    if expressions:
        local_paths["exp3_json"] = [rel(p) for p in expressions]
    if psds:
        local_paths["psd"] = [rel(p) for p in psds]

    return {
        "id": base_id,
        "name": model_path.stem,
        "source_url": OFFICIAL_SAMPLE_URL,
        "source_type": "OFFICIAL_SAMPLE_ZIP",
        "license_status": "OFFICIAL_TERMS_ACCEPTED_BY_USER",
        "analysis_mode": mode,
        "official_profile_key": profile_key or "OFFICIAL_PROFILE_MISSING",
        "has_cmo3": mode == "FULL_STRUCTURE",
        "has_moc3": bool(moc3),
        "has_model3_json": bool(model3),
        "has_physics3_json": bool(physics),
        "has_psd": bool(psds),
        "local_paths": local_paths,
        "structure_report_path": None,
        "notes": [
            "Official Live2D sample. Analyze structure and learning pattern only; do not reuse art, textures, or PSD layers.",
            f"Source zip: {Path(zip_item['zip_path']).name}",
        ],
        "reuse_decision": "REFERENCE_ONLY",
    }


def build_catalog(zip_items: list[dict[str, Any]], out_dir: Path) -> dict[str, Any]:
    models = []
    seen_model3: set[Path] = set()
    for item in zip_items:
        extract_root = out_dir / "official_samples" / "extracted" / item["zip_id"]
        files = collect_files(extract_root)
        for cmo3 in files["cmo3"]:
            entry = make_entry(item, cmo3, files, out_dir, "FULL_STRUCTURE")
            model3 = entry["local_paths"].get("model3_json")
            if model3:
                seen_model3.add((ROOT / model3).resolve())
            models.append(entry)
        for model3 in files["model3_json"]:
            if model3.resolve() in seen_model3:
                continue
            entry = make_entry(item, model3, files, out_dir, "RUNTIME_ONLY", "runtime")
            models.append(entry)
    return {
        "schema_version": 1,
        "purpose": "Official Live2D sample structure catalog generated from user-provided official zips.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_url": OFFICIAL_SAMPLE_URL,
        "safety_note": "Use structure and pattern learning only. Do not reuse official sample art, textures, PSD layers, or character designs.",
        "models": models,
    }


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out).expanduser().resolve()
    zip_paths = [Path(p).expanduser().resolve() for p in (args.zip_paths or DEFAULT_ZIPS)]
    zip_items = []
    for path in zip_paths:
        item = inventory_zip(path)
        if not item["exists"]:
            item["status"] = "MISSING"
        else:
            item["status"] = "INVENTORIED"
            if not args.no_extract:
                item["extract_dir"] = rel(out_dir / "official_samples" / "extracted" / item["zip_id"])
                item["extracted_files"] = safe_extract(path, out_dir / "official_samples" / "extracted" / item["zip_id"])
                item["status"] = "EXTRACTED"
        zip_items.append(item)

    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_url": OFFICIAL_SAMPLE_URL,
        "zip_count": len(zip_items),
        "zip_files": zip_items,
        "aggregate_counts": {
            key: sum((item.get("counts") or {}).get(key, 0) for item in zip_items)
            for key in KEY_SUFFIXES
        },
    }
    write_json(out_dir / "official_samples" / "download_manifest.json", manifest)

    if not args.no_extract:
        catalog = build_catalog(zip_items, out_dir)
        write_json(out_dir / "catalog.official_samples.json", catalog)

    print(
        json.dumps(
            {
                "ok": True,
                "zips": len(zip_items),
                "aggregate_counts": manifest["aggregate_counts"],
                "manifest": rel(out_dir / "official_samples" / "download_manifest.json"),
                "catalog": rel(out_dir / "catalog.official_samples.json") if not args.no_extract else None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""scripts/INDEX.md 자동 생성 — 258개 스크립트를 카테고리·설명·LOC로 색인한다.

새 스크립트 추가/삭제 후 이 스크립트를 재실행하면 인덱스가 갱신된다.
설명은 각 파일 docstring의 첫 줄에서 뽑는다 (docstring 없는 파일은 "(설명 없음)").
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, now_iso  # noqa: E402

SCRIPTS = ROOT / "scripts"

# 위에서부터 첫 매치가 카테고리 (순서 중요)
CATEGORIES: list[tuple[str, str, str]] = [
    ("lib", r"^lib/", "공유 라이브러리 — 새 코드는 여기서 import (복붙 금지)"),
    ("autorig", r"^(autorig_|simulate_autorig|run_autorig|build_autorig|build_asset_dashboard|build_scripts_index)", "AUTORIG 파이프라인·관제탑·자산 인덱스 (현행)"),
    ("webcam-drive", r"^(run_mini_cubism_webcam_drive|run_face_tracking|run_live2d_webcam|build_face_tracking)", "트래킹·웹캠 드라이브 (T0–T3)"),
    ("servers-editors", r"^run_.*(server|editor|player|review)", "로컬 서버·에디터·플레이어"),
    ("validators-qa", r"^(validate_|smoke_|run_.*(qa|smoke|probe|sweep|capture)|score_)", "검증·QA·스모크"),
    ("live2d-reference", r"^(build_live2d|prepare_official|analyze_reference|inspect_cmo3|build_reference|compare_cmo3|build_cubism_success|build_cmo3|test_live2d)", "공식 레퍼런스 분석 (완료된 베이스라인)"),
    ("mini-cubism", r"^(build_mini_cubism|run_mini_cubism|setup_mini_cubism|validate_mini_cubism)", "Mini Cubism 자체 런타임·리그 빌더"),
    ("seethrough", r"(seethrough|see_through|layerd|sam2)", "레이어 분해 (See-through/SAM2)"),
    ("character-002", r"_002\.py$|cubism_v2", "character-002 종속 (대부분 일회용 — 재사용 전 AUTORIG 이식 검토)"),
    ("material-psd", r"(material_pack|psd|rigger_handoff)", "소재 팩·PSD 빌더"),
    ("legacy-misc", r".", "기타·레거시"),
]


def description_of(path: Path) -> str:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        doc = ast.get_docstring(tree)
        if doc:
            return doc.strip().splitlines()[0][:110]
    except SyntaxError:
        pass
    return "(설명 없음)"


def categorize(rel_name: str) -> str:
    for key, pattern, _ in CATEGORIES:
        if re.search(pattern, rel_name):
            return key
    return "legacy-misc"


def core_scripts() -> set[str]:
    """현행 원커맨드 파이프라인이 호출하는 스크립트 + 상시 도구 = CORE (⭐).

    run_autorig_pipeline.py에서 동적으로 추출 — 파이프라인이 바뀌면 INDEX도 따라온다.
    260여 개 레거시 증거 스크립트와 한 평면에 있으므로, 다음 작업자가 현행 경로를
    오선택하지 않게 표시한다.
    """
    core = {
        "run_autorig_pipeline.py", "mini_cubism_preview_server.py",
        "run_mesh_deform_verify.py", "run_rig_perf_test.py",
        "autorig_events.py", "build_scripts_index.py",
    }
    pipeline = SCRIPTS / "run_autorig_pipeline.py"
    if pipeline.exists():
        core |= set(re.findall(r"scripts/([a-z_0-9]+\.py)", pipeline.read_text(encoding="utf-8")))
    return core


def main() -> int:
    entries: dict[str, list[tuple[str, int, str]]] = {key: [] for key, _, _ in CATEGORIES}
    files = sorted(SCRIPTS.rglob("*.py")) + sorted(SCRIPTS.glob("*.mjs"))
    for path in files:
        if "__pycache__" in str(path):
            continue
        rel_name = path.relative_to(SCRIPTS).as_posix()
        loc = len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
        desc = description_of(path) if path.suffix == ".py" else "(node)"
        entries[categorize(rel_name)].append((rel_name, loc, desc))

    total = sum(len(v) for v in entries.values())
    lines = [
        "# scripts/ 인덱스",
        "",
        f"Updated: {now_iso()[:10]} · 총 {total}개 · `python3 scripts/build_scripts_index.py`로 재생성",
        "",
        "새 스크립트를 만들기 전에 이 인덱스에서 기존 것을 먼저 찾는다.",
        "코드 규칙: `docs/ref/AUTORIG-PIPELINE-V1.md`의 '코드 규칙' 절 (lib 사용 의무, 캐릭터 하드코딩 금지, 500줄 상한).",
        "⭐ = **현행 원커맨드 파이프라인 핵심** (run_autorig_pipeline 호출 체인 + 상시 도구) — 나머지는 레거시 증거 스크립트.",
        "",
    ]
    core = core_scripts()
    for key, _, label in CATEGORIES:
        items = entries[key]
        if not items:
            continue
        lines.append(f"## {key} — {label} ({len(items)})")
        lines.append("")
        lines.append("| 파일 | LOC | 설명 |")
        lines.append("|---|---:|---|")
        for rel_name, loc, desc in sorted(items):
            flag = (" ⭐" if rel_name in core else "") + (" ⚠️" if loc >= 500 else "")
            lines.append(f"| `{rel_name}`{flag} | {loc} | {desc} |")
        lines.append("")
    out = SCRIPTS / "INDEX.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out} ({total} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

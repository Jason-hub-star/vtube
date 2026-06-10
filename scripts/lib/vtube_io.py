"""경로/JSON 입출력 공통 유틸. (기존 258개 스크립트에 rel 151벌, load_json 145벌이 복붙되어 있던 것의 단일 원본)"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def rel(path: Path | str | None) -> str | None:
    """ROOT 기준 상대 posix 경로. ROOT 밖이면 절대 경로."""
    if path is None:
        return None
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return p.resolve().as_posix()


def load_json(path: Path | str, default: Any = ...) -> Any:
    p = Path(path)
    if default is not ... and not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def write_json(path: Path | str, payload: Any) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

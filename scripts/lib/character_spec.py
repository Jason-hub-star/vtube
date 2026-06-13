"""캐릭터 스펙 로드/검증 (AUTORIG-TEMPLATE-001) — characters/<id>.yaml.

캐릭터 외형·표정 성격·색 힌트를 코드에서 분리한다. 생성 스크립트(generate_master_sheets)가
프롬프트 *템플릿*(구조 고정)에 스펙 *변수*를 주입해 캐릭터별 프롬프트를 만든다.

핵심: expression_style — 캐릭터의 미소/표정 성격을 입·눈 시트 생성에 주입해, 입 같은
사후 리깅 튜닝 삽질을 구조적으로 차단한다 (004 위벨 "차분한 미소" 5번 삽질 교훈).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REQUIRED = ["id", "name", "ip_named", "ip_desc", "appearance", "expression_style"]
REQUIRED_APPEARANCE = ["hair", "eyes", "outfit"]


def load_spec(path: Path | str) -> dict[str, Any]:
    """yaml 로드 + 필수 필드 검증 + 기본값. 누락 시 명확한 에러."""
    path = Path(path)
    if not path.exists():
        raise SystemExit(f"캐릭터 스펙 없음: {path}")
    spec = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(spec, dict):
        raise SystemExit(f"스펙이 매핑이 아님: {path}")
    missing = [k for k in REQUIRED if not spec.get(k)]
    if missing:
        raise SystemExit(f"스펙 필수 필드 누락 ({path.name}): {missing}")
    appearance = spec.get("appearance") or {}
    am = [k for k in REQUIRED_APPEARANCE if not appearance.get(k)]
    if am:
        raise SystemExit(f"스펙 appearance 필드 누락 ({path.name}): {am}")
    spec.setdefault("colors", {})        # hair_rgb / clothing_rgb — 색 적응 힌트 (실측이 최종)
    spec.setdefault("constraints", [])   # neck_visible / choker_thin / ribbons_separable …
    return spec


def color_hint(spec: dict[str, Any], key: str) -> list[int] | None:
    """colors.<key>_rgb 힌트 (없으면 None — 호출측이 실측 폴백)."""
    val = (spec.get("colors") or {}).get(f"{key}_rgb")
    if isinstance(val, list) and len(val) == 3:
        return [int(c) for c in val]
    return None

"""Vtube 공유 라이브러리.

사용법 (scripts/ 안의 스크립트에서):

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))  # scripts/
    from lib.vtube_io import ROOT, rel, load_json, write_json

규칙 (AUTORIG-PIPELINE-V1.md):
- 새 스크립트는 rel/load_json/write_json/컨택트시트/서버 보일러플레이트를 복붙하지 않고 여기서 import한다.
- 기존 스크립트는 손댈 때만 점진 전환한다 (검증된 증거 스크립트 일괄 수정 금지).
"""

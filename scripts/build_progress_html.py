#!/usr/bin/env python3
"""progress.html 생성기 — 단일 자기완결 진행상황 페이지 (PROGRESS-SHARING-STRATEGY.md 규약).

서버 없이 더블클릭으로 열리는 비동기 공유용 정적 파일. 라이브 모니터링은 관제탑(8095) 담당.
내용 4절: ① 단계 진행 바 ② QA(P5) 표 ③ 최신 시각 증거 썸네일(base64 인라인) ④ 다음 행동.
결정론적 — LLM 판단 없음. 데이터 = runs/<run_id>/events.jsonl (autorig_events 재생).

사용:
  python3 scripts/build_progress_html.py                 # 최신 런
  python3 scripts/build_progress_html.py --run-id <id>   # 특정 런
"""

from __future__ import annotations

import argparse
import base64
import html
import io
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from autorig_events import RUNS_DIR, derive_state, list_runs, read_events  # noqa: E402
from lib.vtube_io import ROOT, now_iso  # noqa: E402

OUT_DEFAULT = ROOT / "docs/status/progress.html"
MAX_THUMBS = 6
THUMB_PX = 360  # 장당 ≤50KB 목표 (JPEG q70)

STATUS_COLOR = {"COMPLETED": "#16a34a", "RUNNING": "#2563eb", "FAILED": "#dc2626",
                "WAITING": "#d97706", "PENDING": "#94a3b8", "PASS": "#16a34a", "FAIL": "#dc2626"}


def thumb_b64(path: Path) -> str | None:
    try:
        img = Image.open(path).convert("RGB")
    except Exception:
        return None
    img.thumbnail((THUMB_PX, THUMB_PX), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=70)
    return base64.b64encode(buf.getvalue()).decode()


def stage_rows(state: dict) -> str:
    rows = []
    for name in state.get("stage_order", []):
        st = state.get("stages", {}).get(name, {})
        status = (st.get("status") or "PENDING").upper()
        prog = st.get("progress")
        pct = f"{round(float(prog) * 100)}%" if isinstance(prog, (int, float)) else ("100%" if status == "COMPLETED" else "")
        color = STATUS_COLOR.get(status, "#94a3b8")
        width = pct or ("100%" if status == "COMPLETED" else "0%")
        rows.append(
            f'<div class="stage"><span class="sname">{html.escape(name)}</span>'
            f'<span class="bar"><i style="width:{width};background:{color}"></i></span>'
            f'<span class="sst" style="color:{color}">{status}</span></div>')
    return "\n".join(rows)


def qa_rows(state: dict) -> str:
    rows = []
    for qa in state.get("qa", []):
        s = (qa.get("status") or "").upper()
        rows.append(f"<tr><td>{html.escape(str(qa.get('name', '')))}</td>"
                    f"<td style='color:{STATUS_COLOR.get(s, '#334155')};font-weight:600'>{html.escape(s)}</td>"
                    f"<td>{html.escape(str(qa.get('stage', '')))}</td></tr>")
    return "\n".join(rows) or "<tr><td colspan=3>QA 결과 없음</td></tr>"


def next_actions(state: dict) -> list[str]:
    actions = [f"게이트 대기: {html.escape(str(g.get('title') or gid))}"
               for gid, g in state.get("gates", {}).items()
               if (g.get("status") or "").upper() == "WAITING"]
    if not actions:
        pending = [n for n in state.get("stage_order", [])
                   if (state.get("stages", {}).get(n, {}).get("status") or "PENDING").upper() == "PENDING"]
        if pending:
            actions.append(f"다음 단계: {html.escape(pending[0])}")
    if not actions:
        actions.append("런 완료 — 다음 작업은 docs/status/NEXT-AGENT-HANDOFF.md 참조")
    return actions


def thumbs_html(state: dict, run_dir: Path) -> str:
    cards = []
    for art in reversed(state.get("artifacts", [])):
        if len(cards) >= MAX_THUMBS:
            break
        p = Path(art.get("path", ""))
        p = p if p.is_absolute() else ROOT / p
        if p.suffix.lower() not in (".png", ".jpg", ".jpeg") or not p.exists():
            continue
        b64 = thumb_b64(p)
        if b64:
            label = html.escape(art.get("label") or p.name)
            cards.append(f'<figure><img src="data:image/jpeg;base64,{b64}"><figcaption>{label}</figcaption></figure>')
    return "\n".join(cards) or "<p class='muted'>이미지 아티팩트 없음</p>"


def render(state: dict, run_dir: Path) -> str:
    status = (state.get("status") or "UNKNOWN").upper()
    color = STATUS_COLOR.get(status, "#334155")
    actions = "".join(f"<li>{a}</li>" for a in next_actions(state))
    return f"""<!doctype html><html lang="ko"><meta charset="utf-8">
<title>Vtube AUTORIG 진행상황 — {html.escape(state.get('run_id', ''))}</title>
<style>
body{{font-family:-apple-system,'Apple SD Gothic Neo',sans-serif;background:#f6f8fa;color:#191f28;max-width:880px;margin:32px auto;padding:0 20px}}
.card{{background:#fff;border-radius:16px;box-shadow:0 1px 8px rgba(2,32,71,.07);padding:20px 24px;margin-bottom:18px}}
h1{{font-size:20px}} h2{{font-size:15px;color:#475569;margin:0 0 12px}}
.badge{{display:inline-block;padding:3px 12px;border-radius:999px;color:#fff;font-size:13px;font-weight:700;background:{color}}}
.stage{{display:flex;align-items:center;gap:10px;margin:7px 0;font-size:13px}}
.sname{{width:120px;font-weight:600}} .sst{{width:90px;text-align:right;font-size:12px;font-weight:700}}
.bar{{flex:1;height:8px;background:#e2e8f0;border-radius:99px;overflow:hidden}} .bar i{{display:block;height:100%}}
table{{width:100%;border-collapse:collapse;font-size:13px}} td,th{{padding:6px 8px;border-bottom:1px solid #f1f5f9;text-align:left}}
.thumbs{{display:flex;flex-wrap:wrap;gap:12px}} figure{{margin:0;width:170px}} figure img{{width:100%;border-radius:10px}}
figcaption{{font-size:11px;color:#64748b;margin-top:4px;word-break:break-all}}
.muted{{color:#94a3b8;font-size:13px}} ul{{margin:6px 0;padding-left:20px;font-size:14px}}
footer{{color:#94a3b8;font-size:11px;margin:24px 0}}
</style>
<div class="card"><h1>{html.escape(state.get('title') or 'AUTORIG')} <span class="badge">{status}</span></h1>
<p class="muted">run: {html.escape(state.get('run_id', ''))} · 갱신: {now_iso()}</p></div>
<div class="card"><h2>단계 진행</h2>{stage_rows(state)}</div>
<div class="card"><h2>자동 검증 (QA)</h2><table><tr><th>검사</th><th>판정</th><th>단계</th></tr>{qa_rows(state)}</table></div>
<div class="card"><h2>최신 시각 증거</h2><div class="thumbs">{thumbs_html(state, run_dir)}</div></div>
<div class="card"><h2>다음 행동</h2><ul>{actions}</ul></div>
<footer>이 파일은 scripts/build_progress_html.py가 events.jsonl에서 결정론적으로 생성 — 서버 불필요, 단일 파일.</footer>
</html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--out", type=Path, default=OUT_DEFAULT)
    args = parser.parse_args()
    if args.run_id:
        run_dir = RUNS_DIR / args.run_id
        state = derive_state(read_events(run_dir), run_id=args.run_id)
    else:
        runs = list_runs()
        if not runs:
            print("런 없음 — events.jsonl이 있는 runs/<id>가 필요합니다")
            return 0
        run_dir = RUNS_DIR / runs[0]["run_id"]
        state = derive_state(read_events(run_dir), run_id=runs[0]["run_id"])
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.write_text(render(state, run_dir), encoding="utf-8")
    print(f"progress.html -> {out} ({out.stat().st_size // 1024}KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

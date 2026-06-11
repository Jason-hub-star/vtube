#!/usr/bin/env python3
"""Build an all57 Live2D carousel page with runtime/unavailable states."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "live2d-strong-model-pattern-001"
DEFAULT_MANIFEST = EXPERIMENT / "reports" / "all57_render_manifest.json"
DEFAULT_SANDBOX_REPORT = EXPERIMENT / "reports" / "all57_runtime_probe_sandbox.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--sandbox-report", type=Path, default=DEFAULT_SANDBOX_REPORT)
    parser.add_argument("--out-name", default="all57_model_carousel.html")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path | str | None) -> str | None:
    if path is None:
        return None
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return p.resolve().as_posix()


def build_models(manifest: dict[str, Any], sandbox: dict[str, Any]) -> list[dict[str, Any]]:
    runtime_index = {safe_id: idx for idx, safe_id in enumerate(sandbox.get("model_ids", []))}
    models = []
    for model in manifest.get("models", []):
        safe_id = model.get("safe_id")
        loadable = model.get("manifest_status") == "PASS" and safe_id in runtime_index
        models.append(
            {
                "rank": model.get("rank"),
                "id": model.get("id"),
                "safe_id": safe_id,
                "name": model.get("name"),
                "analysis_mode": model.get("analysis_mode"),
                "source_type": model.get("source_type"),
                "loadable": loadable,
                "runtime_index": runtime_index.get(safe_id) if loadable else None,
                "status": model.get("manifest_status"),
                "missing": model.get("missing_required_paths", []),
            }
        )
    return models


def build_html(models: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    payload = json.dumps(models, ensure_ascii=False)
    summary_payload = json.dumps(summary, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Live2D all57 모델 넘겨보기</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f5f7fb;
      --panel: rgba(255, 255, 255, 0.95);
      --text: #172033;
      --muted: #667085;
      --blue: #2563eb;
      --blue-soft: #e8f0ff;
      --line: #dfe5ef;
      --red: #ef4444;
      --green: #22c55e;
      --amber: #f59e0b;
    }}
    * {{ box-sizing: border-box; }}
    html, body {{
      margin: 0;
      width: 100%;
      height: 100%;
      overflow: hidden;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    #stage {{
      position: fixed;
      inset: 0;
      width: 100vw;
      height: 100vh;
      border: 0;
      background: #eef2f8;
    }}
    .topbar {{
      position: fixed;
      left: 16px;
      right: 16px;
      top: 14px;
      z-index: 20;
      min-height: 70px;
      display: grid;
      grid-template-columns: 52px minmax(0, 1fr) 52px 116px auto;
      gap: 10px;
      align-items: center;
      padding: 10px;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: var(--panel);
      box-shadow: 0 16px 36px rgba(26, 45, 81, 0.14);
      backdrop-filter: blur(14px);
    }}
    button {{
      border: 0;
      border-radius: 14px;
      height: 46px;
      color: var(--blue);
      background: var(--blue-soft);
      font-size: 24px;
      font-weight: 800;
      cursor: pointer;
    }}
    button:hover {{ background: #dbe8ff; }}
    button:active {{ transform: translateY(1px); }}
    .motion-button {{
      height: 42px;
      border-radius: 999px;
      padding: 0 14px;
      font-size: 13px;
      font-weight: 800;
    }}
    .info {{
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}
    .title {{
      font-size: 16px;
      font-weight: 800;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    .sub {{
      font-size: 12px;
      color: var(--muted);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    .status {{
      display: flex;
      align-items: center;
      gap: 8px;
      height: 38px;
      padding: 0 12px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #f8fafc;
      color: var(--muted);
      font-size: 12px;
      white-space: nowrap;
    }}
    .dot {{
      width: 8px;
      height: 8px;
      border-radius: 99px;
      background: var(--green);
    }}
    .dot.loading {{ background: var(--amber); }}
    .dot.error {{ background: var(--red); }}
    .dot.skip {{ background: #94a3b8; }}
    .empty {{
      position: fixed;
      inset: 104px 18px 58px;
      z-index: 15;
      display: none;
      place-items: center;
      pointer-events: none;
    }}
    .empty.visible {{ display: grid; }}
    .empty-card {{
      max-width: 520px;
      padding: 22px;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.96);
      box-shadow: 0 18px 40px rgba(26, 45, 81, 0.16);
      text-align: center;
    }}
    .empty-title {{
      font-size: 20px;
      font-weight: 850;
      margin-bottom: 8px;
    }}
    .empty-text {{
      color: var(--muted);
      font-size: 14px;
      line-height: 1.55;
    }}
    .hint {{
      position: fixed;
      left: 18px;
      bottom: 16px;
      z-index: 20;
      padding: 8px 12px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.92);
      color: var(--muted);
      font-size: 12px;
      box-shadow: 0 10px 26px rgba(26, 45, 81, 0.12);
    }}
    @media (max-width: 760px) {{
      .topbar {{
        left: 8px;
        right: 8px;
        top: 8px;
        grid-template-columns: 44px 1fr 44px;
        border-radius: 14px;
      }}
      .motion-button {{ grid-column: 1 / -1; width: 100%; }}
      .status {{ grid-column: 1 / -1; justify-content: center; }}
      button {{ height: 40px; border-radius: 12px; }}
      .title {{ font-size: 14px; }}
      .sub {{ font-size: 11px; }}
      .empty {{ inset: 132px 10px 54px; }}
    }}
  </style>
</head>
<body>
  <iframe id="stage" src="./?all57_runtime=1" title="Live2D all57 runtime"></iframe>
  <div id="empty" class="empty">
    <div class="empty-card">
      <div class="empty-title">이 항목은 바로 렌더할 런타임 파일이 없습니다</div>
      <div id="emptyText" class="empty-text"></div>
    </div>
  </div>
  <div class="topbar">
    <button id="prev" type="button" aria-label="이전 모델">‹</button>
    <div class="info">
      <div id="title" class="title">all57 준비 중</div>
      <div id="sub" class="sub">좌우 화살표로 넘겨보세요</div>
    </div>
    <button id="next" type="button" aria-label="다음 모델">›</button>
    <button id="motion" class="motion-button" type="button">모션 재생</button>
    <div class="status"><span id="dot" class="dot loading"></span><span id="status">로딩 중</span></div>
  </div>
  <div class="hint">← / → 키로 57개 항목 이동 · 렌더 안 되는 모델은 말해주시면 기록하면 됩니다</div>
  <script>
    const models = {payload};
    const summary = {summary_payload};
    const iframe = document.getElementById('stage');
    const title = document.getElementById('title');
    const sub = document.getElementById('sub');
    const statusText = document.getElementById('status');
    const dot = document.getElementById('dot');
    const empty = document.getElementById('empty');
    const emptyText = document.getElementById('emptyText');
    let current = 0;
    let busy = false;

    function probe() {{
      return iframe.contentWindow && iframe.contentWindow.__vtubeProbe;
    }}

    function setStatus(text, mode = 'ok') {{
      statusText.textContent = text;
      dot.className = 'dot' + (mode === 'loading' ? ' loading' : mode === 'error' ? ' error' : mode === 'skip' ? ' skip' : '');
    }}

    function renderLabel() {{
      const model = models[current] || {{}};
      title.textContent = model.name || model.safe_id || `모델 ${{current + 1}}`;
      const loadText = model.loadable ? '렌더 가능' : `런타임 없음: ${{(model.missing || []).join(', ') || model.status || 'NO_RUNTIME'}}`;
      sub.textContent = `${{current + 1}} / ${{models.length}} · ${{loadText}} · renderable ${{summary.renderable_count}}/${{summary.model_count}}`;
    }}

    async function waitProbe(timeoutMs = 20000) {{
      const started = Date.now();
      while (Date.now() - started < timeoutMs) {{
        const p = probe();
        if (p && p.waitReady) {{
          const ready = await p.waitReady(1000).catch(() => false);
          if (ready) return p;
        }}
        await new Promise(resolve => setTimeout(resolve, 160));
      }}
      throw new Error('Live2D probe가 준비되지 않았습니다');
    }}

    async function show(index) {{
      if (busy || !models.length) return;
      busy = true;
      current = (index + models.length) % models.length;
      const model = models[current] || {{}};
      renderLabel();
      if (!model.loadable) {{
        empty.classList.add('visible');
        emptyText.textContent = `${{model.name || model.safe_id}}: ${{(model.missing || []).join(', ') || 'model3/moc/texture 없음'}}`;
        setStatus('런타임 없음', 'skip');
        busy = false;
        return;
      }}
      empty.classList.remove('visible');
      setStatus('모델 전환 중', 'loading');
      try {{
        const p = await waitProbe();
        await p.switchModel(model.runtime_index);
        await p.waitReady(14000);
        if (p.clear) await p.clear();
        setStatus('표시 중', 'ok');
      }} catch (error) {{
        console.error(error);
        setStatus('표시 실패', 'error');
      }} finally {{
        busy = false;
      }}
    }}

    async function playMotion() {{
      const model = models[current] || {{}};
      if (!model.loadable) {{
        setStatus('런타임 없음', 'skip');
        return;
      }}
      setStatus('모션 시작 중', 'loading');
      try {{
        const p = await waitProbe();
        const group = p.startRepresentativeMotion ? await p.startRepresentativeMotion() : null;
        setStatus(group ? `모션 재생: ${{group}}` : '모션 없음', group ? 'ok' : 'skip');
      }} catch (error) {{
        console.error(error);
        setStatus('모션 실패', 'error');
      }}
    }}

    document.getElementById('prev').addEventListener('click', () => show(current - 1));
    document.getElementById('next').addEventListener('click', () => show(current + 1));
    document.getElementById('motion').addEventListener('click', () => playMotion());
    window.addEventListener('keydown', event => {{
      if (event.key === 'ArrowLeft') show(current - 1);
      if (event.key === 'ArrowRight') show(current + 1);
    }});
    iframe.addEventListener('load', () => show(0));
    renderLabel();
  </script>
</body>
</html>
"""


def main() -> int:
    args = parse_args()
    manifest = load_json(args.manifest)
    sandbox = load_json(args.sandbox_report)
    demo_dir = ROOT / sandbox["demo_dir"]
    public_dir = demo_dir / "public"
    public_dir.mkdir(parents=True, exist_ok=True)
    models = build_models(manifest, sandbox)
    out = public_dir / args.out_name
    out.write_text(build_html(models, manifest["summary"]), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "PASS",
                "html": rel(out),
                "demo_dir": rel(demo_dir),
                "model_count": len(models),
                "loadable_count": sum(1 for item in models if item["loadable"]),
                "url_path": f"/{args.out_name}",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

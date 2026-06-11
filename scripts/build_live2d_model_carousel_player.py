#!/usr/bin/env python3
"""Build a Korean arrow-key carousel page for the strong20 Live2D sandbox."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "live2d-strong-model-pattern-001"
SANDBOX_REPORT = EXPERIMENT / "reports" / "strong20_runtime_probe_sandbox.json"
MANIFEST = EXPERIMENT / "reports" / "strong20_render_manifest.json"


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


def build_html(models: list[dict[str, Any]]) -> str:
    payload = json.dumps(models, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Live2D 모델 넘겨보기</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f5f7fb;
      --panel: rgba(255, 255, 255, 0.94);
      --text: #162033;
      --muted: #667085;
      --blue: #2563eb;
      --blue-soft: #e8f0ff;
      --line: #dfe5ef;
      --danger: #ef4444;
    }}
    * {{ box-sizing: border-box; }}
    html, body {{
      margin: 0;
      width: 100%;
      height: 100%;
      overflow: hidden;
      background: var(--bg);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
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
      min-height: 64px;
      display: grid;
      grid-template-columns: 52px 1fr 52px auto;
      gap: 10px;
      align-items: center;
      padding: 10px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: 0 16px 36px rgba(26, 45, 81, 0.14);
      backdrop-filter: blur(14px);
      z-index: 10;
    }}
    button {{
      border: 0;
      border-radius: 14px;
      height: 44px;
      font-size: 24px;
      font-weight: 800;
      color: var(--blue);
      background: var(--blue-soft);
      cursor: pointer;
    }}
    button:hover {{ background: #dbe8ff; }}
    button:active {{ transform: translateY(1px); }}
    .info {{
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 3px;
    }}
    .title {{
      font-size: 16px;
      font-weight: 800;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .sub {{
      font-size: 12px;
      color: var(--muted);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .status {{
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 0 12px;
      height: 38px;
      border-radius: 999px;
      background: #f8fafc;
      border: 1px solid var(--line);
      color: var(--muted);
      font-size: 12px;
      white-space: nowrap;
    }}
    .dot {{
      width: 8px;
      height: 8px;
      border-radius: 99px;
      background: #22c55e;
    }}
    .dot.loading {{ background: #f59e0b; }}
    .dot.error {{ background: var(--danger); }}
    .hint {{
      position: fixed;
      left: 18px;
      bottom: 16px;
      z-index: 10;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.9);
      border: 1px solid var(--line);
      color: var(--muted);
      font-size: 12px;
      box-shadow: 0 10px 26px rgba(26, 45, 81, 0.12);
    }}
    @media (max-width: 720px) {{
      .topbar {{
        left: 8px;
        right: 8px;
        top: 8px;
        grid-template-columns: 44px 1fr 44px;
        border-radius: 14px;
      }}
      .status {{
        grid-column: 1 / -1;
        justify-content: center;
      }}
      button {{ height: 40px; border-radius: 12px; }}
      .title {{ font-size: 14px; }}
      .sub {{ font-size: 11px; }}
    }}
  </style>
</head>
<body>
  <iframe id="stage" src="./?carousel_runtime=1" title="Live2D runtime"></iframe>
  <div class="topbar">
    <button id="prev" type="button" aria-label="이전 모델">‹</button>
    <div class="info">
      <div id="title" class="title">모델 준비 중</div>
      <div id="sub" class="sub">좌우 화살표로 넘겨보세요</div>
    </div>
    <button id="next" type="button" aria-label="다음 모델">›</button>
    <div class="status"><span id="dot" class="dot loading"></span><span id="status">로딩 중</span></div>
  </div>
  <div class="hint">← / → 키로 모델 이동 · 화면은 최대 크기로 유지</div>
  <script>
    const models = {payload};
    const iframe = document.getElementById('stage');
    const title = document.getElementById('title');
    const sub = document.getElementById('sub');
    const statusText = document.getElementById('status');
    const dot = document.getElementById('dot');
    let current = 0;
    let busy = false;

    function probe() {{
      return iframe.contentWindow && iframe.contentWindow.__vtubeProbe;
    }}

    function setStatus(text, mode = 'ok') {{
      statusText.textContent = text;
      dot.className = 'dot' + (mode === 'loading' ? ' loading' : mode === 'error' ? ' error' : '');
    }}

    function renderLabel() {{
      const model = models[current] || {{}};
      title.textContent = model.name || model.safe_id || `모델 ${{current + 1}}`;
      sub.textContent = `${{current + 1}} / ${{models.length}} · ${{model.safe_id || model.id || ''}}`;
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
      renderLabel();
      setStatus('모델 전환 중', 'loading');
      try {{
        const p = await waitProbe();
        await p.switchModel(current);
        await p.waitReady(12000);
        if (p.clear) await p.clear();
        setStatus('표시 중', 'ok');
      }} catch (error) {{
        console.error(error);
        setStatus('표시 실패', 'error');
      }} finally {{
        busy = false;
      }}
    }}

    document.getElementById('prev').addEventListener('click', () => show(current - 1));
    document.getElementById('next').addEventListener('click', () => show(current + 1));
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
    sandbox = load_json(SANDBOX_REPORT)
    manifest = load_json(MANIFEST)
    demo_dir = ROOT / sandbox["demo_dir"]
    public_dir = demo_dir / "public"
    public_dir.mkdir(parents=True, exist_ok=True)
    models = [
        {
            "id": model.get("id"),
            "safe_id": model.get("safe_id"),
            "name": model.get("name"),
            "motion_score": model.get("motion_score"),
            "parameters": model.get("parameters"),
            "physics_groups": model.get("physics_groups"),
        }
        for model in manifest.get("models", [])
        if model.get("manifest_status") == "PASS"
    ]
    out = public_dir / "model_carousel.html"
    out.write_text(build_html(models), encoding="utf-8")
    report = {
        "status": "PASS",
        "html": rel(out),
        "demo_dir": rel(demo_dir),
        "model_count": len(models),
        "url_path": "/model_carousel.html",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

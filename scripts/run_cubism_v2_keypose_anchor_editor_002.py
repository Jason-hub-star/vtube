#!/usr/bin/env python3
"""Serve a manual eye/mouth keypose alignment editor for character 002."""

from __future__ import annotations

import json
import mimetypes
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
CANDIDATE = EXP / "model_edit_v4_strict_mouth"
LAYERS = CANDIDATE / "normalized_layers"
REPORTS = EXP / "reports/model_edit_v4_strict_mouth/manual_alignment_v1"
OVERRIDES = REPORTS / "manual_keypose_alignment_overrides.json"
SUMMARY = REPORTS / "manual_keypose_alignment_summary.md"

GROUPS = {
    "eye_L": {
        "label": "왼쪽 눈",
        "preview": "eye_L_open",
        "parts": [
            "eye_L_clean_socket",
            "eye_L_closed_underpaint",
            "eye_L_open",
            "eye_L_half_closed_lid",
            "eye_L_mostly_closed_lid",
            "eye_L_closed_lid",
        ],
        "default_scale": 0.78,
    },
    "eye_R": {
        "label": "오른쪽 눈",
        "preview": "eye_R_open",
        "parts": [
            "eye_R_clean_socket",
            "eye_R_closed_underpaint",
            "eye_R_open",
            "eye_R_half_closed_lid",
            "eye_R_mostly_closed_lid",
            "eye_R_closed_lid",
        ],
        "default_scale": 0.78,
    },
    "mouth": {
        "label": "입",
        "preview": "mouth_small_open",
        "parts": [
            "mouth_base_clean",
            "mouth_closed_smile",
            "mouth_small_open",
            "mouth_wide_open",
            "mouth_o_vowel",
            "mouth_inner",
            "mouth_teeth",
            "mouth_tongue",
        ],
        "default_scale": 0.86,
    },
}


INDEX_HTML = r"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Character 002 Keypose Alignment</title>
  <style>
    :root{font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR",sans-serif;color:#17202a;background:#f5f7fb}
    *{box-sizing:border-box}
    body{margin:0}
    .app{height:100vh;display:grid;grid-template-columns:280px 1fr 330px;overflow:hidden}
    aside,.right{background:#fff;border-right:1px solid #dde3ea;overflow:auto}
    .right{border-left:1px solid #dde3ea;border-right:0}
    header{padding:16px;border-bottom:1px solid #dde3ea}
    h1{font-size:18px;margin:0 0 6px}
    .sub,.hint,.status{font-size:13px;color:#5f6b7a;line-height:1.45}
    .groups{padding:12px;display:grid;gap:8px}
    button{border:0;border-radius:8px;background:#edf4ff;color:#1c64d1;font-weight:800;padding:10px 12px;cursor:pointer}
    button.active{background:#1c64d1;color:#fff}
    button.primary{background:#0f9f6e;color:#fff}
    button.warn{background:#fff4dc;color:#a15c00}
    .stage-wrap{height:100%;display:grid;place-items:center;padding:14px;overflow:auto}
    .topbar{display:flex;gap:10px;align-items:center;justify-content:space-between;padding:12px 14px;background:#fff;border-bottom:1px solid #dde3ea}
    .view-controls{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
    .zoom{width:150px}
    canvas{display:block;width:720px;height:720px;background:#efeae3;border:1px solid #cfd7e3;border-radius:8px;box-shadow:0 12px 34px rgba(20,30,45,.08)}
    .right section{padding:14px;border-bottom:1px solid #dde3ea}
    .title{font-weight:900;margin-bottom:9px}
    .row{display:grid;gap:5px;margin-bottom:10px}
    label{font-size:12px;color:#5f6b7a}
    input,select{width:100%;border:1px solid #cfd7e3;border-radius:8px;padding:9px 10px;font:inherit}
    input[type=range]{padding:0}
    .grid2{display:grid;grid-template-columns:1fr 1fr;gap:8px}
    .kbd{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;background:#eef2f7;border-radius:6px;padding:2px 6px}
    .parts{font-size:12px;color:#5f6b7a;line-height:1.5;word-break:break-word}
    @media(max-width:1100px){.app{grid-template-columns:220px 1fr}.right{grid-column:1/3;height:42vh}.app{height:auto;overflow:auto}}
  </style>
</head>
<body>
<div class="app">
  <aside>
    <header>
      <h1>눈/입 수동 정렬</h1>
      <div class="sub">얼굴 위에서 중심점을 찍고 크기를 줄여 저장합니다.</div>
    </header>
    <div class="groups" id="groups"></div>
  </aside>
  <main>
    <div class="topbar">
      <div class="hint"><span class="kbd">클릭</span> 중심 이동 · <span class="kbd">드래그</span> 미세 이동 · 스케일은 오른쪽 슬라이더</div>
      <div class="view-controls">
        <button id="fitView">맞춤</button>
        <button id="zoomOut">-</button>
        <input id="zoom" class="zoom" type="range" min="0.18" max="0.72" step="0.01" value="0.34">
        <button id="zoomIn">+</button>
        <button id="toggleAlpha" class="warn">레이어 진하게</button>
        <button id="toggleAll" class="warn">선택만 보기</button>
      </div>
    </div>
    <div class="stage-wrap">
      <canvas id="canvas" width="2048" height="2048"></canvas>
    </div>
  </main>
  <div class="right">
    <section>
      <div class="title" id="selectedTitle">-</div>
      <div class="status" id="selectedStatus"></div>
    </section>
    <section>
      <div class="title">정렬값</div>
      <div class="grid2">
        <div class="row"><label>center x</label><input id="x" type="number"></div>
        <div class="row"><label>center y</label><input id="y" type="number"></div>
      </div>
      <div class="row">
        <label>scale <output id="scaleOut"></output></label>
        <input id="scale" type="range" min="0.45" max="1.15" step="0.01">
      </div>
      <div class="row">
        <label>preview layer</label>
        <select id="previewPart"></select>
      </div>
      <button id="save" class="primary">현재 그룹 저장</button>
      <button id="saveAll" class="primary">전체 저장</button>
    </section>
    <section>
      <div class="title">적용 파츠</div>
      <div class="parts" id="parts"></div>
    </section>
    <section>
      <div class="title">저장 상태</div>
      <div class="status" id="saveStatus">아직 저장 전</div>
    </section>
  </div>
</div>
<script>
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
const els = Object.fromEntries(["groups","selectedTitle","selectedStatus","x","y","scale","scaleOut","previewPart","parts","saveStatus","save","saveAll"].map(id => [id, document.getElementById(id)]));
let state = null;
let active = "eye_L";
let base = new Image();
let preview = new Image();
let alpha = 0.82;
let zoom = 0.34;
let dragging = false;
let showAll = true;
const imageCache = {};
const groupColors = {eye_L:"#00a86b", eye_R:"#1c64d1", mouth:"#f59f00"};

function bboxCenter(b){return [Math.round(b[0]+b[2]/2), Math.round(b[1]+b[3]/2)]}
function groupValue(id){
  const g = state.groups[id];
  const saved = state.overrides.groups?.[id];
  if(saved) return {...saved};
  const center = bboxCenter(state.assets[g.preview].bbox);
  return {group_id:id, anchor:center, scale:g.default_scale, preview_part:g.preview, parts:g.parts, updated_at:null};
}
function setGroupValue(id, value){
  if(!state.overrides.groups) state.overrides.groups = {};
  state.overrides.groups[id] = {...value, group_id:id, parts:state.groups[id].parts, updated_at:new Date().toISOString()};
}
async function load(){
  state = await fetch("/api/state").then(r => r.json());
  base.src = "/asset/face_base_clean.png";
  await base.decode();
  renderGroups();
  selectGroup(active);
}
function renderGroups(){
  els.groups.innerHTML = "";
  for(const [id,g] of Object.entries(state.groups)){
    const btn = document.createElement("button");
    btn.textContent = g.label;
    btn.className = id === active ? "active" : "";
    btn.onclick = () => selectGroup(id);
    els.groups.append(btn);
  }
}
async function selectGroup(id){
  active = id;
  renderGroups();
  const g = state.groups[id];
  const value = groupValue(id);
  els.selectedTitle.textContent = g.label;
  els.parts.textContent = g.parts.join(", ");
  els.previewPart.innerHTML = "";
  for(const part of g.parts){
    const opt = document.createElement("option");
    opt.value = part; opt.textContent = part;
    if(part === value.preview_part) opt.selected = true;
    els.previewPart.append(opt);
  }
  els.x.value = value.anchor[0];
  els.y.value = value.anchor[1];
  els.scale.value = value.scale;
  els.scaleOut.textContent = Number(value.scale).toFixed(2);
  await loadPreview(value.preview_part);
  draw();
}
async function loadPreview(part){
  if(imageCache[part]){
    preview = imageCache[part];
    return;
  }
  preview = new Image();
  preview.src = `/asset/${part}.png`;
  await preview.decode();
  imageCache[part] = preview;
}
function requestPreview(part){
  if(imageCache[part]) return imageCache[part];
  const img = new Image();
  imageCache[part] = img;
  img.onload = draw;
  img.src = `/asset/${part}.png`;
  return img.complete ? img : null;
}
function currentValue(){
  return {
    group_id: active,
    anchor: [Number(els.x.value), Number(els.y.value)],
    scale: Number(els.scale.value),
    preview_part: els.previewPart.value,
    parts: state.groups[active].parts,
  };
}
function draw(){
  ctx.clearRect(0,0,2048,2048);
  ctx.drawImage(base,0,0);
  if(showAll){
    for(const id of Object.keys(state.groups)){
      const saved = state.overrides.groups?.[id];
      if(!saved && id !== active) continue;
      const value = id === active ? currentValue() : saved;
      drawOverlay(value, requestPreview(value.preview_part), id, id === active);
    }
  } else {
    drawOverlay(currentValue(), preview, active, true);
  }
  const value = currentValue();
  els.selectedStatus.textContent = `${value.preview_part} / center ${Math.round(value.anchor[0])}, ${Math.round(value.anchor[1])} / scale ${value.scale.toFixed(2)} / ${showAll ? "전체보기 ON" : "단일보기"}`;
}
function drawOverlay(value, image, groupId, isActive){
  if(!image || !image.complete) return;
  const asset = state.assets[value.preview_part];
  const b = asset.bbox;
  const w = b[2] * value.scale;
  const h = b[3] * value.scale;
  const x = value.anchor[0] - w/2;
  const y = value.anchor[1] - h/2;
  ctx.save();
  ctx.globalAlpha = isActive ? alpha : Math.max(0.45, alpha * 0.72);
  ctx.drawImage(image, b[0], b[1], b[2], b[3], x, y, w, h);
  ctx.restore();
  ctx.strokeStyle = groupColors[groupId] || "#00a86b";
  ctx.lineWidth = isActive ? 5 : 4;
  ctx.strokeRect(x,y,w,h);
  ctx.fillStyle = "#f04452";
  ctx.beginPath();
  ctx.arc(value.anchor[0], value.anchor[1], 14, 0, Math.PI*2);
  ctx.fill();
  ctx.strokeStyle = "#fff";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(value.anchor[0]-24, value.anchor[1]);
  ctx.lineTo(value.anchor[0]+24, value.anchor[1]);
  ctx.moveTo(value.anchor[0], value.anchor[1]-24);
  ctx.lineTo(value.anchor[0], value.anchor[1]+24);
  ctx.stroke();
  ctx.fillStyle = groupColors[groupId] || "#00a86b";
  ctx.font = "700 28px -apple-system,BlinkMacSystemFont,sans-serif";
  ctx.fillText(state.groups[groupId]?.label || groupId, x, Math.max(34, y - 12));
}
function applyZoom(){
  const px = Math.round(2048 * zoom);
  canvas.style.width = `${px}px`;
  canvas.style.height = `${px}px`;
  const zoomInput = document.getElementById("zoom");
  if(zoomInput) zoomInput.value = String(zoom);
}
function fitZoom(){
  const wrap = document.querySelector(".stage-wrap");
  const rect = wrap.getBoundingClientRect();
  const target = Math.max(320, Math.min(rect.width - 34, rect.height - 34));
  zoom = Math.max(0.18, Math.min(0.72, target / 2048));
  applyZoom();
}
function canvasPoint(e){
  const r = canvas.getBoundingClientRect();
  return [Math.round((e.clientX-r.left) * 2048 / r.width), Math.round((e.clientY-r.top) * 2048 / r.height)];
}
canvas.addEventListener("pointerdown", e => { dragging = true; setPoint(e); canvas.setPointerCapture(e.pointerId); });
canvas.addEventListener("pointermove", e => { if(dragging) setPoint(e); });
canvas.addEventListener("pointerup", () => dragging = false);
canvas.addEventListener("pointerleave", () => dragging = false);
function setPoint(e){
  const [x,y] = canvasPoint(e);
  els.x.value = x; els.y.value = y;
  draw();
}
for(const id of ["x","y","scale"]) els[id].addEventListener("input", () => {
  els.scaleOut.textContent = Number(els.scale.value).toFixed(2);
  draw();
});
els.previewPart.addEventListener("change", async () => { await loadPreview(els.previewPart.value); draw(); });
document.getElementById("toggleAlpha").onclick = () => { alpha = alpha > 0.9 ? 0.58 : 1; draw(); };
document.getElementById("toggleAll").onclick = () => {
  showAll = !showAll;
  document.getElementById("toggleAll").textContent = showAll ? "선택만 보기" : "전체 저장값 보기";
  draw();
};
document.getElementById("fitView").onclick = () => { fitZoom(); canvas.scrollIntoView({block:"center", inline:"center"}); };
document.getElementById("zoomOut").onclick = () => { zoom = Math.max(0.18, zoom - 0.05); applyZoom(); };
document.getElementById("zoomIn").onclick = () => { zoom = Math.min(0.72, zoom + 0.05); applyZoom(); };
document.getElementById("zoom").addEventListener("input", (event) => { zoom = Number(event.target.value); applyZoom(); });
els.save.onclick = async () => {
  setGroupValue(active, currentValue());
  await save();
};
els.saveAll.onclick = async () => {
  setGroupValue(active, currentValue());
  for(const id of Object.keys(state.groups)){
    if(!state.overrides.groups?.[id]) setGroupValue(id, groupValue(id));
  }
  await save();
};
async function save(){
  state.overrides.schema_version = 1;
  state.overrides.status = "MANUAL_KEYPOSE_ALIGNMENT_REVIEW_SAVED";
  state.overrides.updated_at = new Date().toISOString();
  const result = await fetch("/api/save", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(state.overrides)}).then(r => r.json());
  els.saveStatus.textContent = result.ok ? `저장됨: ${result.path}` : `저장 실패: ${result.error}`;
}
window.addEventListener("resize", fitZoom);
load().then(fitZoom).catch(err => { document.body.textContent = err.stack || String(err); });
</script>
</body>
</html>
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def bbox_for(path: Path) -> list[int]:
    with Image.open(path) as image:
        bbox = image.convert("RGBA").getchannel("A").getbbox()
    if bbox is None:
        return [0, 0, 2, 2]
    left, top, right, bottom = bbox
    return [left, top, right - left, bottom - top]


def load_overrides() -> dict:
    if OVERRIDES.exists():
        return json.loads(OVERRIDES.read_text())
    return {
        "schema_version": 1,
        "status": "MANUAL_KEYPOSE_ALIGNMENT_NOT_SAVED",
        "candidate_id": "model_edit_v4_strict_mouth",
        "source_layers": str(LAYERS),
        "groups": {},
    }


def state_payload() -> dict:
    assets = {}
    for path in sorted(LAYERS.glob("*.png")):
        assets[path.stem] = {"id": path.stem, "bbox": bbox_for(path), "url": f"/asset/{path.name}"}
    return {
        "schema_version": 1,
        "candidate_id": "model_edit_v4_strict_mouth",
        "groups": GROUPS,
        "assets": assets,
        "overrides": load_overrides(),
    }


def write_summary(payload: dict) -> None:
    lines = [
        "# Manual Keypose Alignment Overrides",
        "",
        f"- updated_at: `{payload.get('updated_at', now())}`",
        f"- status: `{payload.get('status')}`",
        f"- candidate: `model_edit_v4_strict_mouth`",
        "",
        "| Group | Anchor | Scale | Preview | Parts |",
        "|---|---:|---:|---|---|",
    ]
    for group_id, row in sorted((payload.get("groups") or {}).items()):
        lines.append(
            f"| `{group_id}` | `{row.get('anchor')}` | `{row.get('scale')}` | "
            f"`{row.get('preview_part')}` | `{len(row.get('parts') or [])}` |"
        )
    SUMMARY.write_text("\n".join(lines) + "\n")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path == "/":
            self.send_bytes(INDEX_HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if path == "/api/state":
            self.send_json(state_payload())
            return
        if path.startswith("/asset/"):
            name = Path(path.removeprefix("/asset/")).name
            target = LAYERS / name
            if not target.exists():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_bytes(target.read_bytes(), mimetypes.guess_type(target.name)[0] or "image/png")
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/save":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            REPORTS.mkdir(parents=True, exist_ok=True)
            payload["updated_at"] = now()
            payload["candidate_id"] = "model_edit_v4_strict_mouth"
            payload["source_layers"] = str(LAYERS)
            OVERRIDES.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
            write_summary(payload)
        except Exception as exc:  # noqa: BLE001
            self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        self.send_json({"ok": True, "path": str(OVERRIDES), "summary": str(SUMMARY)})

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_bytes(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"), "application/json; charset=utf-8", status)

    def send_bytes(self, data: bytes, content_type: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.address_string()} - {fmt % args}")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8082)
    args = parser.parse_args()
    if not (LAYERS / "face_base_clean.png").exists():
        raise SystemExit(f"missing candidate layers: {LAYERS}")
    REPORTS.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Character 002 keypose alignment editor: http://{args.host}:{args.port}/")
    print(f"Overrides: {OVERRIDES}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

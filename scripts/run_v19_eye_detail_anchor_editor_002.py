#!/usr/bin/env python3
"""Serve a small manual anchor editor for Character 002 v19 generated eye detail."""

from __future__ import annotations

import json
import mimetypes
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
PROJECT = EXP / "model_edit_v19_generated_eye_preview/mini_cubism_diagnostic_project"
REPORTS = EXP / "reports/model_edit_v19_generated_eye_preview/manual_eye_detail_anchor_v1"
OVERRIDES = REPORTS / "manual_eye_detail_anchor_overrides.json"


INDEX = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>v19 Eye Detail Anchor</title>
<style>
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;background:#151719;color:#f1f3f4}
.app{height:100vh;display:grid;grid-template-columns:1fr 320px}
.stage{display:grid;place-items:center;overflow:auto;padding:18px}
canvas{background:#eee8df;border:1px solid #444;border-radius:8px;image-rendering:auto}
.side{border-left:1px solid #333;background:#202124;padding:16px;overflow:auto}
h1{font-size:18px;margin:0 0 8px}.muted{color:#b8c0c8;font-size:13px;line-height:1.45}
button{border:0;border-radius:8px;padding:10px 12px;font-weight:800;cursor:pointer;margin:4px 0;background:#2d6cdf;color:white;width:100%}
button.alt{background:#3a3f45}button.active{background:#0f9f6e}
label{display:block;color:#b8c0c8;font-size:12px;margin-top:12px}
input{width:100%;box-sizing:border-box;border:1px solid #555;border-radius:8px;background:#151719;color:white;padding:8px}
.row{display:grid;grid-template-columns:1fr 1fr;gap:8px}.status{white-space:pre-wrap;color:#d7dadc;font-size:13px}
</style>
</head>
<body>
<div class="app">
  <div class="stage"><canvas id="c" width="1220" height="520"></canvas></div>
  <div class="side">
    <h1>v19 눈알 중심 수동 지정</h1>
    <div class="muted">왼쪽/오른쪽 눈알 디테일을 클릭하거나 드래그하세요. 휠/슬라이더로 확대축소할 수 있고, 흰자/눈꺼풀은 고정한 채 iris 디테일만 이동합니다.</div>
    <button id="left" class="active">왼쪽 눈알 찍기</button>
    <button id="right" class="alt">오른쪽 눈알 찍기</button>
    <div class="row">
      <div><label>L x</label><input id="lx" type="number"></div>
      <div><label>L y</label><input id="ly" type="number"></div>
    </div>
    <div class="row">
      <div><label>R x</label><input id="rx" type="number"></div>
      <div><label>R y</label><input id="ry" type="number"></div>
    </div>
    <label>zoom</label><input id="zoom" type="range" min="1" max="4" step="0.1" value="2">
    <button id="save">저장</button>
    <button id="reset" class="alt">현재 v19 중심으로 리셋</button>
    <hr>
    <div class="status" id="status"></div>
  </div>
</div>
<script>
const c=document.getElementById('c'),ctx=c.getContext('2d');
let state, active='L', zoom=2;
const box=[720,560,1330,820];
const imgs={};
async function img(name){ if(imgs[name]) return imgs[name]; const im=new Image(); im.src='/asset/'+name+'.png'; await im.decode(); imgs[name]=im; return im; }
async function load(){ state=await fetch('/api/state').then(r=>r.json()); setInputs(); await draw(); }
function val(){ return {L:[+lx.value,+ly.value], R:[+rx.value,+ry.value]}; }
function setInputs(){ lx.value=state.anchors.L[0]; ly.value=state.anchors.L[1]; rx.value=state.anchors.R[0]; ry.value=state.anchors.R[1]; status.textContent=JSON.stringify(state,null,2); }
async function draw(){
  zoom=+document.getElementById('zoom').value;
  c.width=(box[2]-box[0])*zoom; c.height=(box[3]-box[1])*zoom;
  ctx.save(); ctx.scale(zoom,zoom); ctx.translate(-box[0],-box[1]);
  ctx.clearRect(box[0],box[1],box[2]-box[0],box[3]-box[1]);
  for(const name of ['face_base_clean','nose_detail','eye_L_white','eye_R_white','mouth_closed_smile']){
    try{ ctx.drawImage(await img(name),0,0); }catch(e){}
  }
  const anchors=val();
  await drawShifted('eye_L_iris', state.current.L, anchors.L);
  await drawShifted('eye_R_iris', state.current.R, anchors.R);
  cross(anchors.L[0],anchors.L[1],'#ff3355','L target');
  cross(anchors.R[0],anchors.R[1],'#ff3355','R target');
  cross(state.current.L[0],state.current.L[1],'#00aaff','L current');
  cross(state.current.R[0],state.current.R[1],'#00aaff','R current');
  ctx.restore();
}
async function drawShifted(name,current,target){
  const im=await img(name);
  ctx.save();
  ctx.translate(target[0]-current[0], target[1]-current[1]);
  ctx.drawImage(im,0,0);
  ctx.restore();
}
function cross(x,y,color,label){ ctx.strokeStyle=color; ctx.fillStyle=color; ctx.lineWidth=2/zoom; ctx.beginPath(); ctx.moveTo(x-10,y); ctx.lineTo(x+10,y); ctx.moveTo(x,y-10); ctx.lineTo(x,y+10); ctx.stroke(); ctx.fillText(label,x+8,y+14); }
function pointerToCanvas(e){ const r=c.getBoundingClientRect(); return [box[0]+(e.clientX-r.left)/zoom, box[1]+(e.clientY-r.top)/zoom]; }
function setActiveAnchor(x,y){ if(active==='L'){lx.value=Math.round(x);ly.value=Math.round(y)}else{rx.value=Math.round(x);ry.value=Math.round(y)} draw(); }
let dragging=false;
c.onpointerdown=e=>{ dragging=true; c.setPointerCapture(e.pointerId); const [x,y]=pointerToCanvas(e); setActiveAnchor(x,y); };
c.onpointermove=e=>{ if(!dragging) return; const [x,y]=pointerToCanvas(e); setActiveAnchor(x,y); };
c.onpointerup=e=>{ dragging=false; try{c.releasePointerCapture(e.pointerId)}catch(_){} };
c.onpointercancel=()=>{ dragging=false; };
c.onwheel=e=>{ e.preventDefault(); const z=document.getElementById('zoom'); const next=Math.max(+z.min,Math.min(+z.max,+z.value+(e.deltaY<0?0.15:-0.15))); z.value=next.toFixed(2); draw(); };
left.onclick=()=>{active='L'; left.className='active'; right.className='alt';};
right.onclick=()=>{active='R'; right.className='active'; left.className='alt';};
zoom.oninput=draw; for(const el of [lx,ly,rx,ry]) el.oninput=draw;
reset.onclick=()=>{ lx.value=state.current.L[0]; ly.value=state.current.L[1]; rx.value=state.current.R[0]; ry.value=state.current.R[1]; draw(); };
save.onclick=async()=>{ const payload={anchors:val()}; const res=await fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json()); status.textContent=JSON.stringify(res,null,2); };
load();
</script>
</body></html>"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def alpha_center(path: Path) -> list[float]:
    from PIL import Image

    im = Image.open(path).convert("RGBA")
    alpha = im.getchannel("A")
    box = alpha.getbbox()
    if box is None:
        return [0, 0]
    pix = alpha.load()
    total = sx = sy = 0
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            value = pix[x, y]
            if value:
                total += value
                sx += x * value
                sy += y * value
    return [round(sx / total, 2), round(sy / total, 2)]


def state() -> dict:
    current = {
        "L": alpha_center(PROJECT / "parts/eye_L_iris.png"),
        "R": alpha_center(PROJECT / "parts/eye_R_iris.png"),
    }
    anchors = current
    if OVERRIDES.exists():
        try:
            saved = json.loads(OVERRIDES.read_text())
            anchors = saved.get("anchors", current)
        except Exception:
            anchors = current
    return {
        "status": "V19_EYE_DETAIL_ANCHOR_REVIEW",
        "project": str(PROJECT),
        "current": current,
        "anchors": anchors,
        "overrides": str(OVERRIDES),
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        return

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            data = INDEX.encode()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if parsed.path == "/api/state":
            self.send_json(state())
            return
        if parsed.path.startswith("/asset/"):
            name = unquote(parsed.path.split("/")[-1])
            path = PROJECT / "parts" / name
            if not path.exists():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            data = path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mimetypes.guess_type(str(path))[0] or "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/save":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        anchors = payload.get("anchors", {})
        report = {
            "schema_version": 1,
            "status": "SAVED",
            "updated_at": now(),
            "project": str(PROJECT),
            "anchors": anchors,
            "current": state()["current"],
        }
        REPORTS.mkdir(parents=True, exist_ok=True)
        OVERRIDES.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        self.send_json(report)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8091)
    args = parser.parse_args()
    REPORTS.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"v19 eye detail anchor editor: http://{args.host}:{args.port}/")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

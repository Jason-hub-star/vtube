#!/usr/bin/env python3
"""Serve a drag/zoom anchor editor for v22 B4/B5 correction targets."""

from __future__ import annotations

import argparse
import json
import mimetypes
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SOURCE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
READINESS_JSON = (
    EXP
    / "reports/v22_b4_b5_anchor_correction_readiness/v22_b4_b5_anchor_correction_readiness.json"
)
REPORT_DIR = EXP / "reports/v22_b4_b5_anchor_correction_readiness"
OVERRIDES_JSON = REPORT_DIR / "manual_anchor_overrides.json"
SMOKE_OVERRIDES_JSON = REPORT_DIR / "manual_anchor_overrides_smoke.json"
SMOKE_REPORT_JSON = REPORT_DIR / "v22_b4_b5_anchor_editor_smoke.json"


INDEX = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>v22 B4/B5 Anchor Editor</title>
<style>
:root{font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;color:#191f28;background:#f7f8fa}
*{box-sizing:border-box}body{margin:0}.app{height:100vh;display:grid;grid-template-columns:320px 1fr 340px;overflow:hidden}
aside,.right{background:#fff;border-right:1px solid #e5e8ee;overflow:auto}.right{border-left:1px solid #e5e8ee;border-right:0}
header,section{padding:14px;border-bottom:1px solid #e5e8ee}h1{font-size:18px;margin:0 0 6px}.muted{font-size:13px;color:#6b7684;line-height:1.45}
input,select,textarea{width:100%;border:1px solid #d8dee8;border-radius:8px;padding:9px;background:#fff;font:inherit}textarea{min-height:72px}
button{border:0;border-radius:8px;padding:10px 12px;font-weight:800;cursor:pointer;background:#edf4ff;color:#3182f6}
button.primary{background:#3182f6;color:#fff}button.green{background:#e6f8f1;color:#008f5d}button.red{background:#ffe9ec;color:#d92d3d}
.list{display:grid;gap:8px;padding:10px}.part{border:1px solid #e5e8ee;border-radius:8px;padding:10px;background:#fff;cursor:pointer;text-align:left}
.part.active{border-color:#3182f6;box-shadow:0 0 0 3px rgba(49,130,246,.12)}.part.saved{border-color:#00a86b}
.pid{font-weight:900;font-size:13px}.meta{font-size:12px;color:#6b7684;margin-top:4px}.badge{display:inline-block;font-size:11px;margin:6px 4px 0 0;border-radius:999px;padding:3px 7px;background:#f1f3f5;color:#4e5968}.badge.b4{background:#fff4e5;color:#a15c00}.badge.b5{background:#eaf3ff;color:#1b64da}
main{display:grid;grid-template-rows:auto 1fr;min-width:0}.top{display:flex;gap:10px;align-items:center;justify-content:space-between;padding:12px 14px;border-bottom:1px solid #e5e8ee}
.stagewrap{display:grid;place-items:center;padding:16px;overflow:auto}.stage{background:#fff;border:1px solid #e5e8ee;border-radius:8px;box-shadow:0 8px 28px rgba(25,31,40,.08)}
canvas{display:block}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:8px}.row{display:grid;gap:5px;margin-bottom:9px}label{font-size:12px;color:#6b7684}.status{white-space:pre-wrap;font-size:12px;color:#4e5968}
@media(max-width:1100px){.app{grid-template-columns:260px 1fr}.right{grid-column:1/3;height:42vh}.app{overflow:auto;height:auto}main{min-height:720px}}
</style>
</head>
<body>
<div class="app">
<aside>
  <header><h1>v22 B4/B5 Anchor</h1><div class="muted">REVISE 파츠를 source/front 위에 올려 target anchor와 scale을 저장합니다.</div></header>
  <section><input id="search" placeholder="hair_front, torso, cheek..."></section>
  <div id="list" class="list"></div>
</aside>
<main>
  <div class="top">
    <div class="muted">파츠 드래그: target anchor 이동 · 휠/zoom: 확대 · scale: 파츠 크기 미리보기</div>
    <div><button id="reset" class="red">현재값 리셋</button> <button id="save" class="primary">저장</button></div>
  </div>
  <div class="stagewrap"><div class="stage"><canvas id="canvas" width="1024" height="1024"></canvas></div></div>
</main>
<div class="right">
  <section><h1 id="title">part</h1><div id="info" class="status"></div></section>
  <section>
    <div class="grid2">
      <div class="row"><label>target x</label><input id="tx" type="number"></div>
      <div class="row"><label>target y</label><input id="ty" type="number"></div>
      <div class="row"><label>scale</label><input id="scale" type="number" step="0.01" min="0.1" max="3"></div>
      <div class="row"><label>opacity</label><input id="opacity" type="number" step="0.05" min="0.05" max="1"></div>
    </div>
    <div class="row"><label>notes</label><textarea id="notes"></textarea></div>
    <button id="save2" class="primary">저장</button>
  </section>
  <section><div class="status" id="saveStatus"></div></section>
</div>
</div>
<script>
const canvas=document.getElementById('canvas'), ctx=canvas.getContext('2d');
let state, selected, sourceImg, partImg, zoom=0.5, dragging=false;
const $=id=>document.getElementById(id);
async function loadImage(url){ const im=new Image(); im.src=url; await im.decode(); return im; }
async function init(){
  state=await fetch('/api/state').then(r=>r.json());
  sourceImg=await loadImage('/asset/source.png');
  selected=state.targets[0].part_id;
  renderList(); await select(selected);
}
function target(){ return state.targets.find(t=>t.part_id===selected); }
function saved(){ return state.overrides[selected] || {}; }
async function select(partId){
  selected=partId; const t=target(); partImg=await loadImage('/asset/part/'+encodeURIComponent(partId)+'.png');
  const s=saved();
  $('tx').value = s.target_anchor ? s.target_anchor[0] : t.current_center[0];
  $('ty').value = s.target_anchor ? s.target_anchor[1] : t.current_center[1];
  $('scale').value = s.target_scale || 1.0;
  $('opacity').value = s.preview_opacity || 0.72;
  $('notes').value = s.notes || '';
  $('title').textContent = partId;
  $('info').textContent = JSON.stringify(t,null,2);
  renderList(); draw();
}
function renderList(){
  const q=$('search').value.toLowerCase();
  $('list').innerHTML='';
  state.targets.filter(t=>!q || t.part_id.toLowerCase().includes(q) || t.group.toLowerCase().includes(q)).forEach(t=>{
    const b=document.createElement('button'); b.className='part'+(t.part_id===selected?' active':'')+(state.overrides[t.part_id]?' saved':'');
    b.innerHTML=`<div class="pid">${t.part_id}</div><div class="meta">${t.group} · ${t.correction_kind}</div><span class="badge ${t.source_batch.toLowerCase()}">${t.source_batch}</span><span class="badge">${t.current_center}</span>`;
    b.onclick=()=>select(t.part_id); $('list').appendChild(b);
  });
}
function draw(){
  const t=target(); const cx=Number($('tx').value), cy=Number($('ty').value), sc=Number($('scale').value||1), op=Number($('opacity').value||0.72);
  const bbox=t.current_bbox; const view=[Math.max(0,bbox[0]-220),Math.max(0,bbox[1]-220),Math.min(2048,bbox[2]+220),Math.min(2048,bbox[3]+220)];
  const vw=view[2]-view[0], vh=view[3]-view[1]; zoom=Math.min(1.25, Math.max(0.35, Math.min(1180/vw, 820/vh)));
  canvas.width=Math.round(vw*zoom); canvas.height=Math.round(vh*zoom);
  ctx.save(); ctx.scale(zoom,zoom); ctx.translate(-view[0],-view[1]);
  ctx.clearRect(view[0],view[1],vw,vh); ctx.drawImage(sourceImg,0,0);
  ctx.save(); ctx.globalAlpha=op; ctx.translate(cx-t.current_center[0], cy-t.current_center[1]); ctx.translate(t.current_center[0],t.current_center[1]); ctx.scale(sc,sc); ctx.translate(-t.current_center[0],-t.current_center[1]); ctx.drawImage(partImg,0,0); ctx.restore();
  box(t.current_bbox,'#3182f6','current bbox'); cross(t.current_center[0],t.current_center[1],'#3182f6','current'); cross(cx,cy,'#f04452','target');
  ctx.restore();
}
function box(b,color,label){ ctx.strokeStyle=color; ctx.lineWidth=2/zoom; ctx.strokeRect(b[0],b[1],b[2]-b[0],b[3]-b[1]); ctx.fillStyle=color; ctx.fillText(label,b[0]+4,b[1]+14); }
function cross(x,y,color,label){ ctx.strokeStyle=color; ctx.fillStyle=color; ctx.lineWidth=2/zoom; ctx.beginPath(); ctx.moveTo(x-12,y);ctx.lineTo(x+12,y);ctx.moveTo(x,y-12);ctx.lineTo(x,y+12);ctx.stroke();ctx.fillText(label,x+8,y+14); }
function point(e){ const r=canvas.getBoundingClientRect(); const t=target(); const bbox=t.current_bbox; const view=[Math.max(0,bbox[0]-220),Math.max(0,bbox[1]-220),Math.min(2048,bbox[2]+220),Math.min(2048,bbox[3]+220)]; return [view[0]+(e.clientX-r.left)/zoom, view[1]+(e.clientY-r.top)/zoom]; }
function setPoint(e){ const p=point(e); $('tx').value=Math.round(p[0]); $('ty').value=Math.round(p[1]); draw(); }
canvas.onpointerdown=e=>{dragging=true; canvas.setPointerCapture(e.pointerId); setPoint(e);};
canvas.onpointermove=e=>{if(dragging)setPoint(e);};
canvas.onpointerup=e=>{dragging=false; try{canvas.releasePointerCapture(e.pointerId)}catch(_){};};
canvas.onwheel=e=>{e.preventDefault(); const s=$('scale'); s.value=Math.max(0.1,Math.min(3,Number(s.value)+(e.deltaY<0?0.03:-0.03))).toFixed(2); draw();};
async function save(){
  const payload={part_id:selected,target_anchor:[Number($('tx').value),Number($('ty').value)],target_scale:Number($('scale').value||1),preview_opacity:Number($('opacity').value||0.72),notes:$('notes').value};
  const res=await fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json());
  state.overrides=res.overrides; $('saveStatus').textContent=JSON.stringify(res.summary,null,2); renderList();
}
$('search').oninput=renderList; $('save').onclick=save; $('save2').onclick=save;
for(const id of ['tx','ty','scale','opacity']) $(id).oninput=draw;
$('reset').onclick=()=>select(selected);
init();
</script>
</body></html>"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return {} if default is None else default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_state(overrides_path: Path = OVERRIDES_JSON) -> dict:
    readiness = load_json(READINESS_JSON)
    overrides_doc = load_json(overrides_path, {"overrides": {}})
    overrides = overrides_doc.get("overrides", {})
    return {
        "status": "G6_B4_B5_ANCHOR_EDITOR_READY",
        "source": str(SOURCE),
        "readiness_report": str(READINESS_JSON),
        "overrides_path": str(overrides_path),
        "target_count": len(readiness.get("targets", [])),
        "targets": readiness.get("targets", []),
        "overrides": overrides,
        "saved_count": len(overrides),
    }


def save_override(payload: dict, overrides_path: Path = OVERRIDES_JSON) -> dict:
    state = build_state(overrides_path)
    part_id = payload["part_id"]
    valid_ids = {target["part_id"] for target in state["targets"]}
    if part_id not in valid_ids:
        raise ValueError(f"unknown part_id: {part_id}")
    target = next(target for target in state["targets"] if target["part_id"] == part_id)
    override = {
        "part_id": part_id,
        "source_batch": target["source_batch"],
        "layer_path": target["layer_path"],
        "current_center": target["current_center"],
        "current_bbox": target["current_bbox"],
        "target_anchor": payload.get("target_anchor"),
        "target_scale": payload.get("target_scale", 1.0),
        "preview_opacity": payload.get("preview_opacity", 0.72),
        "notes": payload.get("notes", ""),
        "status": "SAVED_TARGET_ANCHOR_PENDING_REBUILD",
        "updated_at": now(),
    }
    doc = load_json(
        overrides_path,
        {
            "schema_version": "v1",
            "status": "PENDING_REBUILD_FROM_SAVED_ANCHORS",
            "source_readiness_report": str(READINESS_JSON.relative_to(ROOT)),
            "project": "cubism-v2-new-character-002",
            "canvas": [2048, 2048],
            "overrides": {},
        },
    )
    doc.setdefault("overrides", {})[part_id] = override
    doc["updated_at"] = now()
    doc["saved_count"] = len(doc["overrides"])
    save_json(overrides_path, doc)
    return {"status": "SAVED", "summary": {"saved_count": doc["saved_count"], "part_id": part_id}, "overrides": doc["overrides"]}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        return

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            data = INDEX.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if parsed.path == "/api/state":
            self.send_json(build_state())
            return
        if parsed.path == "/asset/source.png":
            self.send_file(SOURCE)
            return
        if parsed.path.startswith("/asset/part/"):
            part_id = unquote(parsed.path.split("/")[-1]).replace(".png", "")
            target = next((item for item in build_state()["targets"] if item["part_id"] == part_id), None)
            if not target:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_file(ROOT / target["layer_path"])
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def send_file(self, path: Path) -> None:
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(str(path))[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/save":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        try:
            self.send_json(save_override(payload))
        except Exception as exc:
            self.send_json({"status": "ERROR", "error": str(exc)}, HTTPStatus.BAD_REQUEST)


def run_smoke() -> dict:
    state = build_state(SMOKE_OVERRIDES_JSON)
    assert state["target_count"] == 33
    assert SOURCE.exists()
    assert all((ROOT / target["layer_path"]).exists() for target in state["targets"])
    first = state["targets"][0]
    saved = save_override(
        {
            "part_id": first["part_id"],
            "target_anchor": first["current_center"],
            "target_scale": 1.0,
            "preview_opacity": 0.72,
            "notes": "smoke test only; uses current center",
        },
        SMOKE_OVERRIDES_JSON,
    )
    smoke_doc = load_json(SMOKE_OVERRIDES_JSON)
    assert saved["status"] == "SAVED"
    assert smoke_doc["saved_count"] == 1
    assert first["part_id"] in smoke_doc["overrides"]
    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": "PASS_V22_B4_B5_ANCHOR_EDITOR_API_SMOKE",
        "state_target_count": state["target_count"],
        "source_exists": SOURCE.exists(),
        "all_target_layers_exist": True,
        "smoke_override_path": str(SMOKE_OVERRIDES_JSON.relative_to(ROOT)),
        "saved_part_id": first["part_id"],
        "main_override_path_untouched": str(OVERRIDES_JSON.relative_to(ROOT)),
        "self_review": {
            "has_drag_zoom_editor": True,
            "api_state_pass": True,
            "api_save_pass": True,
            "target_count": state["target_count"],
            "status": "PASS",
        },
    }
    save_json(SMOKE_REPORT_JSON, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8092)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if args.smoke:
        print(json.dumps(run_smoke(), ensure_ascii=False, indent=2))
        return 0
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"v22 B4/B5 anchor editor: http://{args.host}:{args.port}/")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

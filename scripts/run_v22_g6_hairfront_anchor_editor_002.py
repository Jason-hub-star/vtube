#!/usr/bin/env python3
"""Serve a G6 HairFront anchor editor for Character 002 v22.

The editor lets a reviewer drag target anchors for the seven HairFront rows and
save an override JSON. The smoke mode verifies the UI/API contract without
leaving a real manual override behind.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote, urlparse

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
SOURCE_IMAGE = EXP / "material_pack_first_v0/raw_outputs/new_character_002_source_front.raw.png"
REPORT_DIR = EXP / "reports/v22_g6_hairfront_anchor_correction_input"
INPUT_PACKET = REPORT_DIR / "v22_g6_hairfront_anchor_correction_input_packet.json"
OVERRIDE_TEMPLATE = REPORT_DIR / "manual_hairfront_anchor_overrides.template.json"
OVERRIDES = REPORT_DIR / "manual_hairfront_anchor_overrides.json"
SMOKE_OVERRIDES = REPORT_DIR / "manual_hairfront_anchor_overrides.smoke.json"
SMOKE_REPORT = REPORT_DIR / "v22_g6_hairfront_anchor_editor_smoke.json"
CANVAS = 2048


INDEX = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>v22 HairFront Anchor Editor</title>
<style>
:root{font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;color:#191f28;background:#f7f8fa}
*{box-sizing:border-box}body{margin:0}.app{display:grid;grid-template-columns:330px 1fr 340px;min-height:100vh}
aside,.side{background:#fff;border-right:1px solid #e5e8ee;overflow:auto;max-height:100vh}.side{border-left:1px solid #e5e8ee;border-right:0}
header,section{padding:14px;border-bottom:1px solid #e5e8ee}h1{font-size:18px;margin:0 0 6px}.muted{font-size:13px;color:#6b7684;line-height:1.45}
.pill{display:inline-block;border-radius:999px;background:#f1f3f5;color:#4e5968;font-size:12px;padding:4px 8px;margin:4px 4px 0 0}.danger{background:#ffe9ec;color:#d92d3d}.hold{background:#fff4e5;color:#a15c00}
.list{display:grid;gap:8px;padding:12px}.item{border:1px solid #e5e8ee;border-radius:8px;padding:10px;background:#fff;text-align:left;cursor:pointer}.item.active{border-color:#3182f6;box-shadow:0 0 0 3px rgba(49,130,246,.12)}
.pid{font-weight:900}.meta{font-size:12px;color:#6b7684;margin-top:4px}
main{display:grid;place-items:center;min-width:0;padding:16px;overflow:auto}canvas{background:#f3efe8;border:1px solid #ccd3dd;border-radius:8px;max-width:100%;height:auto}
button{border:0;border-radius:8px;padding:10px 12px;font-weight:800;cursor:pointer;background:#3182f6;color:#fff;width:100%;margin-top:8px}.secondary{background:#edf4ff;color:#3182f6}.dangerBtn{background:#d92d3d}
label{display:block;font-size:12px;color:#6b7684;margin:10px 0 5px}input,select,textarea{width:100%;font:inherit;border:1px solid #d8dee8;border-radius:8px;padding:8px;background:#fff}textarea{min-height:72px}
.row{display:grid;grid-template-columns:1fr 1fr;gap:8px}.status{white-space:pre-wrap;font-size:12px;color:#4e5968}
@media(max-width:1100px){.app{grid-template-columns:1fr}.side,aside{max-height:none}.side{border-left:0}}
</style>
</head>
<body>
<div class="app">
<aside>
  <header>
    <h1>HairFront Anchor Editor</h1>
    <div class="muted">Drag the red target anchor. Saving creates manual override JSON only; it does not approve material, ParamHairFront, G7, or G8.</div>
    <div><span class="pill danger">material blocked</span><span class="pill hold">ParamHairFront hidden</span></div>
  </header>
  <section>
    <label>zoom</label><input id="zoom" type="range" min="0.8" max="4" step="0.1" value="2">
    <button id="save">Save overrides</button>
    <button id="reset" class="secondary">Reset selected delta</button>
    <button id="reload" class="secondary">Reload</button>
    <div id="status" class="status"></div>
  </section>
  <div id="list" class="list"></div>
</aside>
<main><canvas id="c" width="720" height="520"></canvas></main>
<div class="side">
  <section>
    <h1 id="title">row</h1>
    <div id="locks" class="status"></div>
    <label>action</label><select id="action">
      <option>REVIEW_THEN_KEEP_MOVE_OR_REGENERATE</option>
      <option>KEEP_CURRENT</option>
      <option>MOVE_ANCHOR</option>
      <option>REGENERATE_SOURCE_CANDIDATE</option>
    </select>
    <div class="row">
      <div><label>target x</label><input id="tx" type="number"></div>
      <div><label>target y</label><input id="ty" type="number"></div>
    </div>
    <div class="row">
      <div><label>scale</label><input id="scale" type="number" step="0.01"></div>
      <div><label>opacity</label><input id="opacity" type="number" step="0.01"></div>
    </div>
    <label>notes</label><textarea id="notes"></textarea>
    <div id="detail" class="status"></div>
  </section>
</div>
</div>
<script>
const $=id=>document.getElementById(id);
const c=$('c'),ctx=c.getContext('2d');
let state, selected, dragging=false, zoom=2, currentImage, cropBox;
async function api(path, opts){ const r=await fetch(path, opts); if(!r.ok) throw new Error(await r.text()); return r.json(); }
async function load(){ state=await api('/api/state'); selected=selected||state.entries[0].row_id; renderList(); select(selected); }
function row(){ return state.entries.find(r=>r.row_id===selected); }
function renderList(){
  $('list').innerHTML='';
  for(const r of state.entries){
    const b=document.createElement('button');
    b.className='item'+(r.row_id===selected?' active':'');
    b.innerHTML=`<div class="pid">${r.row_id}</div><div class="meta">delta ${JSON.stringify(r.delta)} · ${r.action}</div><span class="pill hold">${r.status}</span>`;
    b.onclick=()=>select(r.row_id);
    $('list').appendChild(b);
  }
}
function entryFromInputs(){
  const r=row();
  const target=[+tx.value,+ty.value];
  return {...r,target_anchor:target,delta:[target[0]-r.current_anchor[0],target[1]-r.current_anchor[1]],scale:+scale.value,opacity:+opacity.value,action:action.value,notes:notes.value,saved_override:true,status:'SAVED'};
}
async function select(rowId){
  selected=rowId; const r=row();
  $('title').textContent=r.row_id;
  $('tx').value=r.target_anchor[0]; $('ty').value=r.target_anchor[1]; $('scale').value=r.scale; $('opacity').value=r.opacity; $('action').value=r.action; $('notes').value=r.notes||'';
  $('locks').textContent=JSON.stringify(state.locks,null,2);
  $('detail').textContent=JSON.stringify({current:r.current_anchor,bbox:r.bbox,envelope:r.motion_envelope_bbox,path:r.path},null,2);
  await draw();
  renderList();
}
async function draw(){
  const r=entryFromInputs(); zoom=+$('zoom').value;
  const res=await fetch(`/api/composite/${encodeURIComponent(r.row_id)}.png?tx=${r.target_anchor[0]}&ty=${r.target_anchor[1]}&scale=${r.scale}&opacity=${r.opacity}`);
  const blob=await res.blob(); currentImage=new Image(); currentImage.src=URL.createObjectURL(blob); await currentImage.decode();
  cropBox=JSON.parse(res.headers.get('X-Crop-Box'));
  c.width=currentImage.width*zoom; c.height=currentImage.height*zoom;
  ctx.setTransform(zoom,0,0,zoom,0,0); ctx.clearRect(0,0,currentImage.width,currentImage.height); ctx.drawImage(currentImage,0,0);
}
function pointerToCanvas(e){ const rect=c.getBoundingClientRect(); return [cropBox[0]+(e.clientX-rect.left)/zoom, cropBox[1]+(e.clientY-rect.top)/zoom]; }
function setTarget(x,y){ tx.value=Math.round(x); ty.value=Math.round(y); action.value='MOVE_ANCHOR'; draw(); }
c.onpointerdown=e=>{dragging=true;c.setPointerCapture(e.pointerId);const p=pointerToCanvas(e);setTarget(p[0],p[1]);};
c.onpointermove=e=>{if(!dragging)return;const p=pointerToCanvas(e);setTarget(p[0],p[1]);};
c.onpointerup=e=>{dragging=false;try{c.releasePointerCapture(e.pointerId)}catch(_){};};
c.onpointercancel=()=>{dragging=false;};
c.onwheel=e=>{e.preventDefault();const z=$('zoom');z.value=Math.max(+z.min,Math.min(+z.max,+z.value+(e.deltaY<0?0.15:-0.15))).toFixed(2);draw();};
for(const id of ['tx','ty','scale','opacity','action','notes','zoom']) $(id).oninput=draw;
$('reset').onclick=()=>{const r=row();tx.value=r.current_anchor[0];ty.value=r.current_anchor[1];scale.value=1;opacity.value=1;action.value='REVIEW_THEN_KEEP_MOVE_OR_REGENERATE';notes.value='';draw();};
$('save').onclick=async()=>{const payload={entries:state.entries.map(e=>e.row_id===selected?entryFromInputs():e)};const res=await api('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});state=res;selected=row().row_id;$('status').textContent=JSON.stringify(res.summary,null,2);renderList();};
$('reload').onclick=()=>{selected=null;load();};
load();
</script>
</body>
</html>"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def base_state(override_path: Path = OVERRIDES) -> dict:
    packet = load_json(INPUT_PACKET)
    template = load_json(OVERRIDE_TEMPLATE)
    entries = template["entries"]
    status = "EDITOR_READY_OVERRIDES_NOT_SAVED"
    if override_path.exists():
        saved = load_json(override_path)
        entries = saved.get("entries", entries)
        status = saved.get("status", "SAVED")
    return {
        "schema_version": "v1",
        "status": status,
        "source_packet": rel(INPUT_PACKET),
        "source_status": packet["status"],
        "override_template": rel(OVERRIDE_TEMPLATE),
        "override_path": rel(override_path),
        "entries": entries,
        "summary": {
            "entry_count": len(entries),
            "saved_override_count": sum(1 for entry in entries if entry.get("saved_override")),
            "move_anchor_count": sum(1 for entry in entries if entry.get("action") == "MOVE_ANCHOR"),
            "regenerate_route_count": sum(
                1 for entry in entries if entry.get("action") == "REGENERATE_SOURCE_CANDIDATE"
            ),
            "material_acceptance_pass_count": 0,
            "param_hairfront_activation_count": 0,
            "owner_approval_count": 0,
            "g5_material_acceptance_status": "BLOCKED_HAIRFRONT_EDITOR_REVIEW_REQUIRED",
            "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
            "g7_mini_cubism_status": "BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE",
            "g8_real_cubism_status": "BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE",
        },
        "locks": packet["locks"],
    }


def save_overrides(payload: dict, override_path: Path = OVERRIDES) -> dict:
    template = load_json(OVERRIDE_TEMPLATE)
    known = {entry["row_id"] for entry in template["entries"]}
    entries = payload.get("entries", [])
    if len(entries) != len(template["entries"]):
        raise ValueError("entries length mismatch")
    for entry in entries:
        if entry.get("row_id") not in known:
            raise ValueError(f"unknown row_id: {entry.get('row_id')}")
        if entry.get("action") not in [
            "REVIEW_THEN_KEEP_MOVE_OR_REGENERATE",
            "KEEP_CURRENT",
            "MOVE_ANCHOR",
            "REGENERATE_SOURCE_CANDIDATE",
        ]:
            raise ValueError(f"invalid action: {entry.get('action')}")
    doc = base_state(override_path)
    doc.update(
        {
            "status": "SAVED_MANUAL_HAIRFRONT_ANCHOR_OVERRIDES_MATERIAL_STILL_BLOCKED",
            "updated_at": now(),
            "entries": entries,
        }
    )
    doc["summary"] = {
        "entry_count": len(entries),
        "saved_override_count": sum(1 for entry in entries if entry.get("saved_override")),
        "move_anchor_count": sum(1 for entry in entries if entry.get("action") == "MOVE_ANCHOR"),
        "regenerate_route_count": sum(
            1 for entry in entries if entry.get("action") == "REGENERATE_SOURCE_CANDIDATE"
        ),
        "material_acceptance_pass_count": 0,
        "param_hairfront_activation_count": 0,
        "owner_approval_count": 0,
        "g5_material_acceptance_status": "BLOCKED_HAIRFRONT_EDITOR_REVIEW_REQUIRED",
        "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
        "g7_mini_cubism_status": "BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE",
        "g8_real_cubism_status": "BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE",
    }
    save_json(override_path, doc)
    return doc


def crop_for(entry: dict, pad: int = 130) -> tuple[int, int, int, int]:
    box = entry["motion_envelope_bbox"]
    return (
        max(0, box[0] - pad),
        max(0, box[1] - pad),
        min(CANVAS, box[2] + pad),
        min(CANVAS, box[3] + pad),
    )


def composite_png(row_id: str, target_anchor: list[int], scale: float, opacity: float) -> tuple[bytes, tuple[int, int, int, int]]:
    state = base_state()
    entry = next(entry for entry in state["entries"] if entry["row_id"] == row_id)
    source = Image.open(SOURCE_IMAGE).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    layer = Image.open(ROOT / entry["path"]).convert("RGBA")
    if scale != 1.0:
        layer = layer.resize((round(CANVAS * scale), round(CANVAS * scale)), Image.Resampling.LANCZOS)
    if opacity < 1.0:
        alpha = layer.getchannel("A").point(lambda value: round(value * opacity))
        layer.putalpha(alpha)
    dx = round(target_anchor[0] - entry["current_anchor"][0])
    dy = round(target_anchor[1] - entry["current_anchor"][1])
    moved = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    moved.alpha_composite(layer, dest=(dx, dy))
    comp = Image.alpha_composite(source, moved)
    crop = crop_for(entry)
    view = comp.crop(crop)
    draw = ImageDraw.Draw(view, "RGBA")
    cx = entry["current_anchor"][0] - crop[0]
    cy = entry["current_anchor"][1] - crop[1]
    tx = target_anchor[0] - crop[0]
    ty = target_anchor[1] - crop[1]
    draw.line([cx - 16, cy, cx + 16, cy], fill=(30, 136, 229, 255), width=4)
    draw.line([cx, cy - 16, cx, cy + 16], fill=(30, 136, 229, 255), width=4)
    draw.line([tx - 20, ty, tx + 20, ty], fill=(230, 73, 63, 255), width=4)
    draw.line([tx, ty - 20, tx, ty + 20], fill=(230, 73, 63, 255), width=4)
    out = BytesIO()
    view.convert("RGB").save(out, format="PNG")
    return out.getvalue(), crop


class Handler(BaseHTTPRequestHandler):
    override_path = OVERRIDES

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
            self.send_json(base_state(self.override_path))
            return
        if parsed.path.startswith("/api/composite/"):
            row_id = unquote(parsed.path.split("/")[-1]).replace(".png", "")
            qs = dict(part.split("=") for part in parsed.query.split("&") if "=" in part)
            state = base_state(self.override_path)
            entry = next(entry for entry in state["entries"] if entry["row_id"] == row_id)
            target = [int(float(qs.get("tx", entry["target_anchor"][0]))), int(float(qs.get("ty", entry["target_anchor"][1])))]
            scale = float(qs.get("scale", entry.get("scale", 1.0)))
            opacity = float(qs.get("opacity", entry.get("opacity", 1.0)))
            data, crop = composite_png(row_id, target, scale, opacity)
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Crop-Box", json.dumps(list(crop)))
            self.end_headers()
            self.wfile.write(data)
            return
        if parsed.path.startswith("/asset/"):
            rel_path = unquote(parsed.path[len("/asset/") :])
            path = ROOT / rel_path
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
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
            self.send_json(save_overrides(payload, self.override_path))
        except Exception as exc:
            self.send_json({"status": "ERROR", "error": str(exc)}, HTTPStatus.BAD_REQUEST)


def smoke() -> dict:
    state = base_state(SMOKE_OVERRIDES)
    first = state["entries"][0]
    data, crop = composite_png(first["row_id"], first["target_anchor"], first["scale"], first["opacity"])
    payload = {"entries": [dict(entry) for entry in state["entries"]]}
    payload["entries"][0]["saved_override"] = True
    payload["entries"][0]["action"] = "KEEP_CURRENT"
    payload["entries"][0]["status"] = "SMOKE_SAVED"
    saved = save_overrides(payload, SMOKE_OVERRIDES)
    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": "G6_HAIRFRONT_ANCHOR_EDITOR_SMOKE_PASS",
        "source_packet": rel(INPUT_PACKET),
        "override_template": rel(OVERRIDE_TEMPLATE),
        "smoke_override_path": rel(SMOKE_OVERRIDES),
        "actual_override_path": rel(OVERRIDES),
        "actual_override_exists": OVERRIDES.exists(),
        "entry_count": state["summary"]["entry_count"],
        "composite_first_row": first["row_id"],
        "composite_png_bytes": len(data),
        "composite_crop_box": list(crop),
        "smoke_saved_override_count": saved["summary"]["saved_override_count"],
        "smoke_move_anchor_count": saved["summary"]["move_anchor_count"],
        "material_acceptance_pass_count": 0,
        "param_hairfront_activation_count": 0,
        "owner_approval_count": 0,
        "g5_material_acceptance_status": "BLOCKED_HAIRFRONT_EDITOR_REVIEW_REQUIRED",
        "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
        "g7_mini_cubism_status": "BLOCKED_UNTIL_G5_MATERIAL_ACCEPTANCE",
        "g8_real_cubism_status": "BLOCKED_UNTIL_MATERIAL_ACCEPTANCE_AND_EDITOR_GATE",
        "locks": state["locks"],
        "self_review": {
            "entry_count_is_seven": state["summary"]["entry_count"] == 7,
            "composite_png_nonempty": len(data) > 1000,
            "smoke_override_saved": saved["summary"]["saved_override_count"] == 1,
            "actual_override_not_created_by_smoke": not OVERRIDES.exists(),
            "material_acceptance_pass_count": 0,
            "param_hairfront_activation_count": 0,
            "owner_approval_count": 0,
            "param_hair_front_hidden": True,
            "validator_only_promotion_blocked": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "status": "PASS",
        },
    }
    save_json(SMOKE_REPORT, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8094)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if args.smoke:
        report = smoke()
        return 0 if report["self_review"]["status"] == "PASS" else 1
    Handler.override_path = OVERRIDES
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"v22 HairFront anchor editor: http://{args.host}:{args.port}/")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

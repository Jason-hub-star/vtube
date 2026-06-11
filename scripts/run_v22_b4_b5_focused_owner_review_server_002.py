#!/usr/bin/env python3
"""Serve a focused owner-review UI for v22 B4/B5 primary decisions."""

from __future__ import annotations

import argparse
import json
import mimetypes
from io import BytesIO
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/cubism-v2-new-character-002"
REPORT_DIR = EXP / "reports/v22_b4_b5_focused_owner_review"
PACKET_JSON = REPORT_DIR / "v22_b4_b5_focused_owner_review.json"
DECISIONS_JSON = REPORT_DIR / "v22_b4_b5_focused_owner_review_decisions.json"
SMOKE_DECISIONS_JSON = REPORT_DIR / "v22_b4_b5_focused_owner_review_decisions_smoke.json"
SMOKE_REPORT_JSON = REPORT_DIR / "v22_b4_b5_focused_owner_review_server_smoke.json"


INDEX = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>v22 B4/B5 Focused Owner Review</title>
<style>
:root{font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;color:#191f28;background:#f7f8fa}
*{box-sizing:border-box}body{margin:0}.app{display:grid;grid-template-columns:360px 1fr;min-height:100vh}
aside{background:#fff;border-right:1px solid #e5e8ee;overflow:auto;max-height:100vh;position:sticky;top:0}
header,section{padding:16px;border-bottom:1px solid #e5e8ee}h1{font-size:18px;margin:0 0 6px}.muted{font-size:13px;color:#6b7684;line-height:1.45}
.pill{display:inline-block;border-radius:999px;background:#f1f3f5;color:#4e5968;font-size:12px;padding:4px 8px;margin:4px 4px 0 0}.danger{background:#ffe9ec;color:#d92d3d}.ok{background:#e6f8f1;color:#008f5d}.hold{background:#fff4e5;color:#a15c00}
.list{display:grid;gap:8px;padding:12px}.item{border:1px solid #e5e8ee;border-radius:8px;padding:10px;background:#fff;text-align:left;cursor:pointer}.item.active{border-color:#3182f6;box-shadow:0 0 0 3px rgba(49,130,246,.12)}.item.saved{border-color:#00a86b}
.pid{font-weight:900}.meta{font-size:12px;color:#6b7684;margin-top:4px}
main{padding:18px;min-width:0}.grid{display:grid;grid-template-columns:minmax(320px,1fr) minmax(320px,1fr);gap:14px;align-items:start}.panel{background:#fff;border:1px solid #e5e8ee;border-radius:8px;overflow:hidden}.panel h2{font-size:15px;margin:0;padding:12px 14px;border-bottom:1px solid #e5e8ee}.panel .body{padding:14px}.preview{display:grid;grid-template-columns:1fr 1fr;gap:10px}.preview img{width:100%;background:#f7f8fa;border:1px solid #e5e8ee;border-radius:8px}
label{display:block;font-size:12px;color:#6b7684;margin:10px 0 5px}select,textarea{width:100%;font:inherit;border:1px solid #d8dee8;border-radius:8px;padding:9px;background:#fff}textarea{min-height:88px}
button{border:0;border-radius:8px;padding:10px 12px;font-weight:800;cursor:pointer;background:#3182f6;color:#fff}.secondary{background:#edf4ff;color:#3182f6}.status{white-space:pre-wrap;font-size:12px;color:#4e5968}
@media(max-width:980px){.app{grid-template-columns:1fr}aside{position:static;max-height:none}.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="app">
<aside>
  <header>
    <h1>B4/B5 Focused Review</h1>
    <div class="muted">10개 primary decision만 저장합니다. 저장해도 material PASS, ParamHairFront, G7/G8은 자동 승격되지 않습니다.</div>
    <div><span class="pill danger">material BLOCKED</span><span class="pill hold">HairFront hidden</span><span class="pill danger">G7/G8 blocked</span></div>
  </header>
  <section>
    <button id="saveAll">현재 결정 저장</button>
    <button id="reload" class="secondary">다시 읽기</button>
    <div id="status" class="status"></div>
  </section>
  <div id="list" class="list"></div>
</aside>
<main>
  <div class="grid">
    <div class="panel">
      <h2 id="title">part</h2>
      <div class="body">
        <div class="preview">
          <div><label>source crop</label><img id="sourceImg"></div>
          <div><label>overlay</label><img id="overlayImg"></div>
          <div><label>isolated</label><img id="isolatedImg"></div>
          <div><label>candidate</label><img id="decisionImg"></div>
        </div>
      </div>
    </div>
    <div class="panel">
      <h2>decision</h2>
      <div class="body">
        <div id="summary" class="status"></div>
        <label>owner decision</label>
        <select id="decision"></select>
        <label>owner note</label>
        <textarea id="note" placeholder="짧게: 좋음 / 어색함 / 재생성 필요 이유"></textarea>
        <p><button id="saveOne">이 항목 저장</button></p>
        <div id="detail" class="status"></div>
      </div>
    </div>
  </div>
</main>
</div>
<script>
let state, selected;
const $=id=>document.getElementById(id);
async function api(path, opts){ const r=await fetch(path, opts); if(!r.ok) throw new Error(await r.text()); return r.json(); }
async function load(){ state=await api('/api/state'); selected=selected||state.primary_decisions[0].part_id; renderList(); select(selected); }
function decisionDoc(){ return state.decisions.decisions.find(d=>d.part_id===selected) || {}; }
function item(){ return state.primary_decisions.find(i=>i.part_id===selected); }
function renderList(){
  $('list').innerHTML='';
  for(const it of state.primary_decisions){
    const d=(state.decisions.decisions||[]).find(x=>x.part_id===it.part_id)||{};
    const saved=d.owner_decision && d.owner_decision!=='PENDING_OWNER_REVIEW';
    const b=document.createElement('button');
    b.className='item'+(it.part_id===selected?' active':'')+(saved?' saved':'');
    b.innerHTML=`<div class="pid">${it.part_id}</div><div class="meta">${it.review_group}</div><span class="pill ${saved?'ok':'hold'}">${d.owner_decision||'PENDING_OWNER_REVIEW'}</span>`;
    b.onclick=()=>select(it.part_id);
    $('list').appendChild(b);
  }
}
function asset(part, kind){ return `/api/asset/${encodeURIComponent(part)}/${kind}.png`; }
function select(partId){
  selected=partId; const it=item(); const d=decisionDoc();
  $('title').textContent=`${it.part_id} · ${it.review_group}`;
  $('sourceImg').src=asset(it.part_id,'source');
  $('overlayImg').src=asset(it.part_id,'overlay');
  $('isolatedImg').src=asset(it.part_id,'isolated');
  $('decisionImg').src=asset(it.part_id,'decision');
  $('summary').textContent=JSON.stringify({recommendation:it.recommendation, owner_decision:d.owner_decision||'PENDING_OWNER_REVIEW', allowed:it.allowed_owner_decisions},null,2);
  $('decision').innerHTML='';
  for(const opt of ['PENDING_OWNER_REVIEW', ...it.allowed_owner_decisions]){
    const o=document.createElement('option'); o.value=opt; o.textContent=opt; $('decision').appendChild(o);
  }
  $('decision').value=d.owner_decision||'PENDING_OWNER_REVIEW';
  $('note').value=d.owner_note||'';
  $('detail').textContent=JSON.stringify({next_if_accept:it.next_if_accept,next_if_revise:it.next_if_revise,next_if_regenerate:it.next_if_regenerate},null,2);
  renderList();
}
async function save(partId=selected){
  const payload={part_id:partId, owner_decision:$('decision').value, owner_note:$('note').value};
  const res=await api('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  state.decisions=res.decisions; $('status').textContent=JSON.stringify(res.summary,null,2); renderList(); select(selected);
}
$('saveOne').onclick=()=>save();
$('saveAll').onclick=()=>save();
$('reload').onclick=()=>{selected=null;load()};
load();
</script>
</body>
</html>"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return {} if default is None else default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def initial_decisions(packet: dict) -> dict:
    return {
        "schema_version": "v1",
        "generated_at": now(),
        "updated_at": now(),
        "status": "OWNER_DECISIONS_PENDING",
        "source_packet": rel(PACKET_JSON),
        "instructions": "Only allowed owner_decision values may be saved. PENDING entries do not approve material PASS.",
        "decisions": [
            {
                "part_id": item["part_id"],
                "review_group": item["review_group"],
                "owner_decision": "PENDING_OWNER_REVIEW",
                "allowed_owner_decisions": item["allowed_owner_decisions"],
                "owner_note": "",
            }
            for item in packet["primary_decisions"]
        ],
        "self_review": {
            "material_pass_status": "BLOCKED",
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
        },
    }


def decisions_path(smoke: bool = False) -> Path:
    return SMOKE_DECISIONS_JSON if smoke else DECISIONS_JSON


def state(path: Path = DECISIONS_JSON) -> dict:
    packet = load_json(PACKET_JSON)
    decisions = load_json(path, initial_decisions(packet))
    return {
        "status": "B4_B5_FOCUSED_OWNER_REVIEW_SERVER_READY",
        "packet": packet,
        "decisions": decisions,
        "primary_decisions": packet.get("primary_decisions", []),
        "summary": packet.get("summary", {}),
        "decisions_path": str(path),
    }


def save_decision(payload: dict, path: Path = DECISIONS_JSON) -> dict:
    packet = load_json(PACKET_JSON)
    doc = load_json(path, initial_decisions(packet))
    primary = {item["part_id"]: item for item in packet["primary_decisions"]}
    part_id = payload["part_id"]
    if part_id not in primary:
        raise ValueError(f"unknown part_id: {part_id}")
    decision = payload.get("owner_decision", "PENDING_OWNER_REVIEW")
    allowed = ["PENDING_OWNER_REVIEW", *primary[part_id]["allowed_owner_decisions"]]
    if decision not in allowed:
        raise ValueError(f"invalid decision for {part_id}: {decision}")
    for row in doc["decisions"]:
        if row["part_id"] == part_id:
            row["owner_decision"] = decision
            row["owner_note"] = payload.get("owner_note", "")
            row["updated_at"] = now()
            break
    doc["updated_at"] = now()
    pending = sum(1 for row in doc["decisions"] if row["owner_decision"] == "PENDING_OWNER_REVIEW")
    accepted = sum(1 for row in doc["decisions"] if row["owner_decision"].startswith("ACCEPT"))
    revise = sum(1 for row in doc["decisions"] if row["owner_decision"].startswith("REVISE"))
    regen = sum(1 for row in doc["decisions"] if row["owner_decision"].startswith("REGENERATE"))
    doc["summary"] = {
        "decision_count": len(doc["decisions"]),
        "pending_count": pending,
        "accepted_count": accepted,
        "revise_count": revise,
        "regenerate_count": regen,
        "material_pass_status": "BLOCKED",
        "param_hair_front_status": "HIDDEN_CONTRACT_ONLY",
        "g7_mini_cubism_status": "BLOCKED",
        "g8_real_cubism_status": "BLOCKED",
    }
    doc["status"] = "OWNER_DECISIONS_SAVED_MATERIAL_STILL_BLOCKED"
    save_json(path, doc)
    return {"status": "SAVED", "summary": doc["summary"], "decisions": doc}


def crop_images(part_id: str) -> dict[str, Image.Image]:
    packet = load_json(PACKET_JSON)
    item = next(item for item in packet["primary_decisions"] if item["part_id"] == part_id)
    source = Image.open(ROOT / packet["source_image"]).convert("RGBA").resize((2048, 2048), Image.Resampling.LANCZOS)
    layer = Image.open(ROOT / item["output_path"]).convert("RGBA")
    crop_box = tuple(item["crop_box"])
    source_crop = source.crop(crop_box)
    layer_crop = layer.crop(crop_box)
    alpha = layer_crop.getchannel("A").point(lambda v: min(160, int(v * 0.72)))
    tint = Image.new("RGBA", source_crop.size, (*item["overlay_color"], 0))
    tint.putalpha(alpha)
    overlay = Image.alpha_composite(source_crop, tint)
    bbox = layer_crop.getchannel("A").getbbox()
    isolated = layer_crop.crop(bbox) if bbox else layer_crop
    bg = Image.new("RGBA", isolated.size, (245, 247, 250, 255))
    isolated = Image.alpha_composite(bg, isolated)
    return {
        "source": source_crop,
        "overlay": overlay,
        "isolated": isolated,
        "decision": isolated,
    }


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
        if parsed.path == "/favicon.ico":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return
        if parsed.path == "/":
            data = INDEX.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if parsed.path == "/api/state":
            self.send_json(state())
            return
        if parsed.path.startswith("/api/asset/"):
            try:
                _, _, _, part_id, kind_file = parsed.path.split("/", 4)
                kind = kind_file.rsplit(".", 1)[0]
                img = crop_images(unquote(part_id))[kind]
                buf = BytesIO()
                img.save(buf, format="PNG")
                data = buf.getvalue()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", mimetypes.guess_type(kind_file)[0] or "image/png")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except Exception as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/save":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self.send_json(save_decision(payload))
            except Exception as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)


def run_smoke() -> int:
    packet = load_json(PACKET_JSON)
    st = state(SMOKE_DECISIONS_JSON)
    assert st["status"] == "B4_B5_FOCUSED_OWNER_REVIEW_SERVER_READY"
    assert len(st["primary_decisions"]) == 10
    first = st["primary_decisions"][0]
    result = save_decision(
        {
            "part_id": first["part_id"],
            "owner_decision": "PENDING_OWNER_REVIEW",
            "owner_note": "smoke no-op pending save",
        },
        SMOKE_DECISIONS_JSON,
    )
    assert result["summary"]["decision_count"] == 10
    assert result["summary"]["material_pass_status"] == "BLOCKED"
    assert result["summary"]["param_hair_front_status"] == "HIDDEN_CONTRACT_ONLY"
    assert result["decisions"]["self_review"]["mini_cubism_not_promoted"] is True
    assert result["decisions"]["self_review"]["real_cubism_not_promoted"] is True
    for item in packet["primary_decisions"]:
        imgs = crop_images(item["part_id"])
        assert all(img.width > 0 and img.height > 0 for img in imgs.values())
    tmp_png_count = len(list(REPORT_DIR.glob(".tmp_*.png")))
    assert tmp_png_count == 0
    report = {
        "schema_version": "v1",
        "generated_at": now(),
        "status": "PASS_V22_B4_B5_FOCUSED_OWNER_REVIEW_SERVER_SMOKE",
        "packet": rel(PACKET_JSON),
        "smoke_decisions": rel(SMOKE_DECISIONS_JSON),
        "primary_decision_count": len(packet["primary_decisions"]),
        "asset_crop_count": len(packet["primary_decisions"]) * 4,
        "tmp_png_count": tmp_png_count,
        "self_review": {
            "state_loads": True,
            "save_api_noop_pending_pass": True,
            "all_asset_crops_nonempty": True,
            "no_temp_png_artifacts": True,
            "material_pass_status": "BLOCKED",
            "param_hair_front_hidden": True,
            "mini_cubism_not_promoted": True,
            "real_cubism_not_promoted": True,
            "status": "PASS",
        },
    }
    save_json(SMOKE_REPORT_JSON, report)
    print(json.dumps({"status": report["status"], "report": str(SMOKE_REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8093)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.smoke:
        return run_smoke()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Serving v22 B4/B5 focused owner review at http://{args.host}:{args.port}/")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

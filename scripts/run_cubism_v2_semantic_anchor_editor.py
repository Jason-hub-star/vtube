#!/usr/bin/env python3
"""Serve a G1.6 semantic anchor editor for Cubism v2 parts."""

from __future__ import annotations

import argparse
import json
import mimetypes
import subprocess
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path("/Users/family/jason/Vtube")
PACK = ROOT / "experiments/cubism-v2-new-character-001/material_pack_v0"
MANIFEST_PATH = PACK / "layer_manifest.json"
CANONICAL = PACK / "canonical/candidate_002_2048_rgba.png"
OVERRIDES_PATH = PACK / "reports/manual_semantic_overrides.json"
SUMMARY_PATH = PACK / "reports/manual_semantic_overrides_summary.md"

CANVAS_SIZE = [2048, 2048]
DEFAULT_ACTIONS = [
    "REEXTRACT_FROM_CANONICAL",
    "REPAIR_MASK",
    "REPAIR_POSITION",
    "REPAIR_UNDERPAINT",
    "SPLIT_PART",
    "MERGE_PART",
    "KEEP_AS_IS",
]

REVIEW_PRIORITIES: dict[str, tuple[int, str, str]] = {
    "eye_L_white": (1, "1순위: 왼쪽 눈 흰자", "눈 영역에 피부/머리 픽셀이 섞이면 가장 티가 큽니다."),
    "eye_R_white": (1, "1순위: 오른쪽 눈 흰자", "눈 영역에 피부/머리 픽셀이 섞이면 가장 티가 큽니다."),
    "eye_L_iris": (1, "1순위: 왼쪽 홍채", "홍채 위치가 틀어지면 시선이 바로 깨집니다."),
    "eye_R_iris": (1, "1순위: 오른쪽 홍채", "홍채 위치가 틀어지면 시선이 바로 깨집니다."),
    "eye_L_pupil": (1, "1순위: 왼쪽 동공", "동공은 작은 박스로 정확히 잡아야 합니다."),
    "eye_R_pupil": (1, "1순위: 오른쪽 동공", "동공은 작은 박스로 정확히 잡아야 합니다."),
    "eye_L_highlight": (1, "1순위: 왼쪽 하이라이트", "하이라이트는 작게, 눈 안쪽만 잡아야 합니다."),
    "eye_R_highlight": (1, "1순위: 오른쪽 하이라이트", "하이라이트는 작게, 눈 안쪽만 잡아야 합니다."),
    "mouth_line": (1, "1순위: 입 선", "입 선이 블록처럼 잡히면 얼굴이 즉시 어색해집니다."),
    "mouth_inner": (1, "1순위: 입 안쪽", "입 안쪽은 입 ROI 안에서만 작게 잡아야 합니다."),
    "eye_L_upper_lash": (2, "2순위: 왼쪽 위 속눈썹", "머리카락/피부가 섞이기 쉬운 눈 경계입니다."),
    "eye_R_upper_lash": (2, "2순위: 오른쪽 위 속눈썹", "머리카락/피부가 섞이기 쉬운 눈 경계입니다."),
    "eye_L_lower_lash": (2, "2순위: 왼쪽 아래 속눈썹", "눈 아래 경계만 얇게 잡는 편이 좋습니다."),
    "eye_R_lower_lash": (2, "2순위: 오른쪽 아래 속눈썹", "눈 아래 경계만 얇게 잡는 편이 좋습니다."),
    "mouth_corner_L": (2, "2순위: 왼쪽 입꼬리", "입꼬리는 작게 잡아야 입 모양 변형이 자연스럽습니다."),
    "mouth_corner_R": (2, "2순위: 오른쪽 입꼬리", "입꼬리는 작게 잡아야 입 모양 변형이 자연스럽습니다."),
    "mouth_teeth": (2, "2순위: 치아", "치아는 입 안쪽에서 밝은 부분만 잡아야 합니다."),
    "mouth_tongue": (2, "2순위: 혀", "혀는 입 안쪽 아래 영역만 잡아야 합니다."),
    "face_base": (3, "3순위: 얼굴 기본", "얼굴 전체 지지층입니다. 눈/입을 정확히 잡은 뒤 조정합니다."),
    "nose": (3, "3순위: 코", "코는 작고 부드러운 디테일만 잡으면 됩니다."),
    "cheek_L": (3, "3순위: 왼쪽 볼", "볼은 넓은 색 블록이 되지 않게 부드럽게 잡습니다."),
    "cheek_R": (3, "3순위: 오른쪽 볼", "볼은 넓은 색 블록이 되지 않게 부드럽게 잡습니다."),
    "brow_L": (3, "3순위: 왼쪽 눈썹", "눈썹은 머리카락과 섞이지 않게 잡습니다."),
    "brow_R": (3, "3순위: 오른쪽 눈썹", "눈썹은 머리카락과 섞이지 않게 잡습니다."),
}


INDEX_HTML = r"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>G1.6 Semantic Anchor Editor</title>
  <style>
    :root {
      --blue:#3182f6; --red:#f04452; --green:#00a86b; --orange:#f59f00;
      --bg:#f7f8fa; --panel:#fff; --line:#e5e8ee; --text:#191f28; --muted:#6b7684;
      font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR",sans-serif;
    }
    *{box-sizing:border-box}
    body{margin:0;background:var(--bg);color:var(--text)}
    .app{height:100vh;display:grid;grid-template-columns:300px 1fr 360px;overflow:hidden}
    aside,.right{background:var(--panel);border-right:1px solid var(--line);overflow:auto}
    .right{border-left:1px solid var(--line);border-right:0}
    header{padding:16px;border-bottom:1px solid var(--line);position:sticky;top:0;background:rgba(255,255,255,.96);z-index:2}
    h1{font-size:19px;margin:0 0 6px}
    .sub{font-size:13px;color:var(--muted);line-height:1.45}
    input,select,textarea{width:100%;border:1px solid var(--line);border-radius:8px;padding:10px 11px;font:inherit;background:#fff;outline:none}
    input:focus,select:focus,textarea:focus{border-color:var(--blue);box-shadow:0 0 0 3px rgba(49,130,246,.12)}
    .search{padding:12px;border-bottom:1px solid var(--line)}
    .list{padding:10px;display:grid;gap:8px}
    .part{border:1px solid var(--line);border-radius:8px;background:#fff;padding:10px;text-align:left;cursor:pointer}
    .part:hover,.part.active{border-color:var(--blue)}
    .part.saved{border-color:rgba(0,168,107,.45)}
    .pid{font-weight:800;font-size:13px;overflow-wrap:anywhere}
    .ko{font-size:12px;color:var(--muted);margin-top:3px}
    .badges{display:flex;gap:5px;flex-wrap:wrap;margin-top:7px}
    .badge{font-size:11px;border-radius:999px;padding:3px 7px;background:#eef4ff;color:var(--blue)}
    .badge.saved{background:#e6f8f1;color:var(--green)}
    .badge.p1{background:#ffe9ec;color:var(--red)}
    .badge.p2{background:#fff5db;color:#b7791f}
    .badge.p3{background:#edf4ff;color:var(--blue)}
    .priorityPanel{padding:12px;border-bottom:1px solid var(--line);background:#fff}
    .priorityPanel b{display:block;font-size:13px;margin-bottom:6px}
    .priorityPanel div{font-size:12px;color:var(--muted);line-height:1.45}
    main{display:grid;grid-template-rows:auto 1fr;min-width:0}
    .topbar{display:flex;gap:10px;align-items:center;justify-content:space-between;padding:12px 14px;background:rgba(247,248,250,.95);border-bottom:1px solid var(--line)}
    .help{font-size:13px;color:var(--muted)}
    .canvaswrap{height:100%;display:grid;place-items:center;padding:16px;overflow:auto}
    .stage{position:relative;background:#fff;border:1px solid var(--line);border-radius:8px;box-shadow:0 8px 28px rgba(25,31,40,.06)}
    canvas{display:block;max-width:100%;height:auto}
    .toolbar{display:flex;gap:8px;flex-wrap:wrap}
    button{border:0;border-radius:8px;background:#edf4ff;color:var(--blue);padding:10px 12px;font-weight:800;cursor:pointer}
    button.primary{background:var(--blue);color:#fff}
    button.danger{background:#ffe9ec;color:var(--red)}
    button.green{background:#e6f8f1;color:var(--green)}
    .right section{padding:14px;border-bottom:1px solid var(--line)}
    .title{font-size:14px;font-weight:900;margin-bottom:9px}
    .grid2{display:grid;grid-template-columns:1fr 1fr;gap:8px}
    .row{display:grid;gap:5px;margin-bottom:9px}
    label{font-size:12px;color:var(--muted)}
    textarea{min-height:88px;resize:vertical}
    .status{font-size:13px;color:var(--muted);padding:10px 14px}
    .preview{width:100%;height:170px;object-fit:contain;border:1px solid var(--line);border-radius:8px;background-image:linear-gradient(45deg,#eef1f5 25%,transparent 25%),linear-gradient(-45deg,#eef1f5 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#eef1f5 75%),linear-gradient(-45deg,transparent 75%,#eef1f5 75%);background-size:18px 18px;background-position:0 0,0 9px,9px -9px,-9px 0}
    @media(max-width:1100px){.app{grid-template-columns:240px 1fr}.right{grid-column:1/3;height:40vh}.app{overflow:auto;height:auto}main{min-height:760px}}
  </style>
</head>
<body>
<div class="app">
  <aside>
    <header>
      <h1>G1.6 위치 라벨링</h1>
      <div class="sub">원본 위에서 “이 영역이 이 파츠”라고 ROI와 중심점을 저장합니다.</div>
    </header>
    <div class="search">
      <input id="search" placeholder="파츠 검색: eye, mouth, underpaint..." />
    </div>
    <div class="priorityPanel">
      <b>재지정 우선순위</b>
      <div>1순위: 눈 흰자/홍채/동공/하이라이트, 입 선/입 안쪽</div>
      <div>2순위: 속눈썹, 입꼬리, 치아, 혀</div>
      <div>3순위: 얼굴 기본, 코, 볼, 눈썹</div>
    </div>
    <div class="list" id="partList"></div>
  </aside>
  <main>
    <div class="topbar">
      <div class="help">박스 안쪽 드래그: 이동 · 모서리 드래그: 크기 조절 · 점 드래그: 중심점</div>
      <div class="toolbar">
        <button id="fitBtn">화면 맞춤</button>
        <button id="centerBoxBtn" class="green">박스를 빨간점 중심으로</button>
        <button id="resetBtn" class="danger">현재 파츠 초기화</button>
      </div>
    </div>
    <div class="canvaswrap">
      <div class="stage">
        <canvas id="canvas" width="2048" height="2048"></canvas>
      </div>
    </div>
  </main>
  <div class="right">
    <section>
      <div class="title">선택 파츠</div>
      <img id="partPreview" class="preview" />
      <div class="status" id="selectedInfo"></div>
    </section>
    <section>
      <div class="title">라벨 정보</div>
      <div class="row">
        <label>semantic role</label>
        <input id="role" />
      </div>
      <div class="row">
        <label>action</label>
        <select id="action"></select>
      </div>
      <div class="grid2">
        <div class="row"><label>ROI x</label><input id="x" type="number" /></div>
        <div class="row"><label>ROI y</label><input id="y" type="number" /></div>
        <div class="row"><label>ROI w</label><input id="w" type="number" /></div>
        <div class="row"><label>ROI h</label><input id="h" type="number" /></div>
        <div class="row"><label>anchor x</label><input id="ax" type="number" /></div>
        <div class="row"><label>anchor y</label><input id="ay" type="number" /></div>
      </div>
      <div class="row">
        <label>메모</label>
        <textarea id="note" placeholder="예: 이 위치가 왼쪽 동공. 기존 bbox가 너무 넓음."></textarea>
      </div>
      <button id="saveBtn" class="primary">이 위치 저장</button>
      <button id="saveNextBtn" class="green">저장하고 다음</button>
    </section>
    <section>
      <div class="title">저장 파일</div>
      <div class="status" id="saveStatus">manual_semantic_overrides.json</div>
    </section>
  </div>
</div>
<script>
let state = {items:[], overrides:{}, actions:[], selected:null};
let image = new Image();
let dragging = null;
let scale = 1;
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const ids = ['role','action','x','y','w','h','ax','ay','note'];
const $ = id => document.getElementById(id);

function semanticRole(partId){
  if(partId.includes('underpaint')) return partId.replace('_underpaint','') + '_underpaint';
  if(partId.startsWith('eye_L_')) return 'left_' + partId.replace('eye_L_','eye_');
  if(partId.startsWith('eye_R_')) return 'right_' + partId.replace('eye_R_','eye_');
  if(partId.startsWith('mouth_')) return 'mouth_' + partId.replace('mouth_','');
  return partId;
}
function currentItem(){ return state.items.find(x => x.part_id === state.selected) || state.items[0]; }
function fallbackBox(item){
  const b = item.bbox_actual || item.bbox || [900,900,120,120];
  return {x:b[0], y:b[1], w:Math.max(20,b[2]), h:Math.max(20,b[3])};
}
function currentOverride(){
  const item = currentItem();
  const saved = state.overrides[item.part_id];
  if(saved) return JSON.parse(JSON.stringify(saved));
  const box = fallbackBox(item);
  return {
    part_id:item.part_id,
    semantic_role:semanticRole(item.part_id),
    expected_group:item.group || item.semantic_group || '',
    roi:[box.x, box.y, box.w, box.h],
    anchor:[Math.round(box.x + box.w/2), Math.round(box.y + box.h/2)],
    action:item.source_type === 'UNDERPAINT' ? 'REPAIR_UNDERPAINT' : 'REEXTRACT_FROM_CANONICAL',
    note:''
  };
}
function setOverrideForm(ov){
  $('role').value = ov.semantic_role || '';
  $('action').value = ov.action || 'REEXTRACT_FROM_CANONICAL';
  $('x').value = Math.round(ov.roi[0]); $('y').value = Math.round(ov.roi[1]);
  $('w').value = Math.round(ov.roi[2]); $('h').value = Math.round(ov.roi[3]);
  $('ax').value = Math.round(ov.anchor[0]); $('ay').value = Math.round(ov.anchor[1]);
  $('note').value = ov.note || '';
}
function formOverride(){
  const item = currentItem();
  return {
    part_id:item.part_id,
    semantic_role:$('role').value.trim() || semanticRole(item.part_id),
    expected_group:item.group || item.semantic_group || '',
    roi:[num('x'),num('y'),Math.max(2,num('w')),Math.max(2,num('h'))],
    anchor:[num('ax'),num('ay')],
    action:$('action').value,
    note:$('note').value,
    updated_at:new Date().toISOString()
  };
}
function num(id){ return Number($(id).value || 0); }
function clampOverride(ov){
  ov.roi[0] = Math.max(0, Math.min(2048, ov.roi[0]));
  ov.roi[1] = Math.max(0, Math.min(2048, ov.roi[1]));
  ov.roi[2] = Math.max(2, Math.min(2048 - ov.roi[0], ov.roi[2]));
  ov.roi[3] = Math.max(2, Math.min(2048 - ov.roi[1], ov.roi[3]));
  ov.anchor[0] = Math.max(0, Math.min(2048, ov.anchor[0]));
  ov.anchor[1] = Math.max(0, Math.min(2048, ov.anchor[1]));
  return ov;
}
async function load(){
  const res = await fetch('/api/state');
  state = await res.json();
  $('action').innerHTML = state.actions.map(a => `<option>${a}</option>`).join('');
  state.selected = state.items[0]?.part_id;
  image.src = '/asset?path=' + encodeURIComponent(state.canonical_path);
  await image.decode();
  fitCanvas();
  selectPart(state.selected);
}
function fitCanvas(){
  const wrap = document.querySelector('.canvaswrap');
  const size = Math.max(520, Math.min(wrap.clientWidth - 38, wrap.clientHeight - 38, 920));
  canvas.style.width = size + 'px';
  canvas.style.height = size + 'px';
  scale = size / 2048;
  draw();
}
function renderList(){
  const q = $('search').value.toLowerCase().trim();
  const list = $('partList');
  list.innerHTML = '';
  for(const item of state.items.filter(i => !q || [i.part_id,i.label_ko,i.group,i.source_type].join(' ').toLowerCase().includes(q))){
    const saved = !!state.overrides[item.part_id];
    const b = document.createElement('button');
    b.className = 'part ' + (item.part_id === state.selected ? 'active ' : '') + (saved ? 'saved ' : '');
    b.onclick = () => selectPart(item.part_id);
    const pClass = item.review_priority <= 3 ? `p${item.review_priority}` : '';
    const pBadge = item.review_priority <= 3 ? `<span class="badge ${pClass}">${item.review_priority_ko}</span>` : '';
    b.innerHTML = `<div class="pid">${item.part_id}</div><div class="ko">${item.label_ko || ''}</div><div class="badges">${pBadge}<span class="badge">${item.source_type}</span>${saved?'<span class="badge saved">저장됨</span>':''}</div><div class="ko">${item.review_priority_reason_ko || ''}</div>`;
    list.appendChild(b);
  }
}
function selectPart(partId){
  state.selected = partId;
  const item = currentItem();
  $('partPreview').src = item.output_path ? '/asset?path=' + encodeURIComponent(item.output_path) : '';
  $('selectedInfo').innerHTML = `<b>${item.part_id}</b><br>${item.label_ko || ''}<br><b>${item.review_priority_ko || '일반 확인'}</b><br>${item.review_priority_reason_ko || ''}<br>bbox: ${(item.bbox_actual || item.bbox || []).join(', ')}`;
  setOverrideForm(currentOverride());
  renderList();
  draw();
}
function draw(){
  ctx.clearRect(0,0,2048,2048);
  ctx.drawImage(image,0,0,2048,2048);
  const ov = clampOverride(formOverride());
  const [x,y,w,h] = ov.roi;
  ctx.save();
  ctx.fillStyle = 'rgba(49,130,246,.12)';
  ctx.strokeStyle = '#3182f6';
  ctx.lineWidth = 5;
  ctx.fillRect(x,y,w,h);
  ctx.strokeRect(x,y,w,h);
  ctx.fillStyle = '#f04452';
  ctx.strokeStyle = '#fff';
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.arc(ov.anchor[0], ov.anchor[1], 12, 0, Math.PI*2);
  ctx.fill(); ctx.stroke();
  ctx.fillStyle = 'rgba(25,31,40,.88)';
  ctx.font = '36px -apple-system, sans-serif';
  ctx.fillText(currentItem().part_id, x, Math.max(40,y-14));
  ctx.restore();
}
function canvasPoint(e){
  const r = canvas.getBoundingClientRect();
  return {x:(e.clientX-r.left)/scale, y:(e.clientY-r.top)/scale};
}
function hit(p){
  const ov = formOverride();
  const [x,y,w,h] = ov.roi;
  const ax = ov.anchor[0], ay = ov.anchor[1];
  if(Math.hypot(p.x-ax,p.y-ay) < 22) return 'anchor';
  const nearRight = Math.abs(p.x-(x+w)) < 20;
  const nearBottom = Math.abs(p.y-(y+h)) < 20;
  if(nearRight && nearBottom) return 'resize';
  if(p.x>=x && p.x<=x+w && p.y>=y && p.y<=y+h) return 'move';
  return null;
}
canvas.addEventListener('mousedown', e => {
  const p = canvasPoint(e), mode = hit(p);
  if(!mode) return;
  dragging = {mode, start:p, original:formOverride()};
});
window.addEventListener('mousemove', e => {
  if(!dragging) return;
  const p = canvasPoint(e);
  const dx = p.x - dragging.start.x, dy = p.y - dragging.start.y;
  const ov = JSON.parse(JSON.stringify(dragging.original));
  if(dragging.mode === 'move'){
    ov.roi[0] += dx; ov.roi[1] += dy; ov.anchor[0] += dx; ov.anchor[1] += dy;
  } else if(dragging.mode === 'resize'){
    ov.roi[2] += dx; ov.roi[3] += dy;
  } else if(dragging.mode === 'anchor'){
    ov.anchor = [p.x,p.y];
  }
  setOverrideForm(clampOverride(ov));
  draw();
});
window.addEventListener('mouseup', () => dragging = null);
for(const id of ids.slice(0,8)){ $(id).addEventListener('input', draw); }
$('search').addEventListener('input', renderList);
$('fitBtn').addEventListener('click', fitCanvas);
$('centerBoxBtn').addEventListener('click', () => {
  const ov = formOverride();
  ov.roi[0] = Math.round(ov.anchor[0] - ov.roi[2] / 2);
  ov.roi[1] = Math.round(ov.anchor[1] - ov.roi[3] / 2);
  setOverrideForm(clampOverride(ov));
  draw();
});
$('resetBtn').addEventListener('click', async () => {
  const id = state.selected;
  delete state.overrides[id];
  await saveOverride(null, id);
  selectPart(id);
});
$('saveBtn').addEventListener('click', () => saveOverride(formOverride()));
$('saveNextBtn').addEventListener('click', async () => {
  await saveOverride(formOverride());
  const idx = state.items.findIndex(i => i.part_id === state.selected);
  const next = state.items[(idx + 1) % state.items.length];
  selectPart(next.part_id);
});
async function saveOverride(override, deletePartId=null){
  const payload = deletePartId ? {delete_part_id:deletePartId} : {override:clampOverride(override)};
  const res = await fetch('/api/override', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
  const data = await res.json();
  if(!data.ok) throw new Error(data.error || 'save failed');
  state.overrides = data.overrides;
  $('saveStatus').textContent = `저장됨: ${Object.keys(state.overrides).length}개 override`;
  renderList();
}
load();
</script>
</body>
</html>
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def semantic_group(part_id: str, source_type: str | None = None) -> str:
    if source_type == "UNDERPAINT" or "underpaint" in part_id:
        return "underpaint"
    if part_id.startswith("eye_L_"):
        return "eye_L"
    if part_id.startswith("eye_R_"):
        return "eye_R"
    if part_id.startswith("mouth_"):
        return "mouth"
    if part_id.startswith("hair_"):
        return "hair"
    if part_id.startswith("face_") or part_id in {"nose", "cheek_L", "cheek_R"}:
        return "face"
    if "cloth" in part_id or "collar" in part_id:
        return "clothing"
    if any(token in part_id for token in ["body", "torso", "neck", "shoulder", "arm_"]):
        return "body"
    return "unknown"


def semantic_role(part_id: str) -> str:
    if "underpaint" in part_id:
        return part_id
    if part_id.startswith("eye_L_"):
        return "left_" + part_id.replace("eye_L_", "eye_")
    if part_id.startswith("eye_R_"):
        return "right_" + part_id.replace("eye_R_", "eye_")
    if part_id.startswith("mouth_"):
        return "mouth_" + part_id.replace("mouth_", "")
    return part_id


def manifest_items() -> list[dict]:
    manifest = load_json(MANIFEST_PATH, {"layers": []})
    items: list[dict] = []
    for entry in manifest.get("layers", []):
        if not entry.get("include_in_import_psd"):
            continue
        bbox = entry.get("bbox_actual") or entry.get("bbox") or [900, 900, 120, 120]
        priority, priority_ko, priority_reason_ko = REVIEW_PRIORITIES.get(
            entry["part_id"],
            (9, "일반 확인", ""),
        )
        items.append(
            {
                "part_id": entry["part_id"],
                "label_ko": entry.get("label_ko", ""),
                "group": entry.get("group") or semantic_group(entry["part_id"], entry.get("source_type")),
                "semantic_group": entry.get("semantic_group") or semantic_group(entry["part_id"], entry.get("source_type")),
                "semantic_role_default": semantic_role(entry["part_id"]),
                "source_type": entry.get("source_type"),
                "output_path": entry.get("output_path"),
                "bbox": entry.get("bbox"),
                "bbox_actual": bbox,
                "draw_order": entry.get("draw_order"),
                "anchor_default": [round(bbox[0] + bbox[2] / 2), round(bbox[1] + bbox[3] / 2)],
                "review_priority": priority,
                "review_priority_ko": priority_ko,
                "review_priority_reason_ko": priority_reason_ko,
            }
        )
    return sorted(items, key=lambda item: (int(item.get("review_priority") or 9), int(item.get("draw_order") or 9999)))


def load_override_doc() -> dict:
    items = manifest_items()
    doc = {
        "schema_version": 1,
        "gate": "G1.6_MANUAL_SEMANTIC_ANCHOR_EDITOR",
        "updated_at": now(),
        "canonical_path": rel(CANONICAL),
        "manifest": rel(MANIFEST_PATH),
        "overrides": {},
    }
    if OVERRIDES_PATH.exists():
        current = load_json(OVERRIDES_PATH)
        doc.update({key: current.get(key, doc[key]) for key in ["schema_version", "gate", "canonical_path", "manifest"]})
        doc["overrides"] = current.get("overrides", {})
    for item in items:
        override = doc["overrides"].get(item["part_id"])
        if override:
            override.setdefault("part_id", item["part_id"])
            override.setdefault("semantic_role", item["semantic_role_default"])
            override.setdefault("expected_group", item["semantic_group"])
            override.setdefault("action", "REEXTRACT_FROM_CANONICAL")
    return doc


def write_summary(doc: dict) -> None:
    rows = list(doc.get("overrides", {}).values())
    lines = [
        "# G1.6 Manual Semantic Overrides",
        "",
        f"- updated_at: `{doc.get('updated_at')}`",
        f"- overrides: `{len(rows)}`",
        f"- json: `{rel(OVERRIDES_PATH)}`",
        "",
        "| Part | Role | ROI | Anchor | Action | Note |",
        "|---|---|---|---|---|---|",
    ]
    for row in sorted(rows, key=lambda item: item["part_id"]):
        note = (row.get("note") or "").replace("\n", " ")[:80]
        lines.append(
            f"| `{row['part_id']}` | `{row.get('semantic_role','')}` | `{row.get('roi')}` | `{row.get('anchor')}` | `{row.get('action')}` | {note} |"
        )
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def ensure_initialized() -> None:
    if not OVERRIDES_PATH.exists():
        doc = load_override_doc()
        save_json(OVERRIDES_PATH, doc)
        write_summary(doc)


def validate_override(raw: dict) -> dict:
    items = {item["part_id"]: item for item in manifest_items()}
    part_id = raw.get("part_id")
    if part_id not in items:
        raise ValueError(f"unknown part_id: {part_id}")
    roi = raw.get("roi")
    anchor = raw.get("anchor")
    if not isinstance(roi, list) or len(roi) != 4:
        raise ValueError("roi must be [x, y, w, h]")
    if not isinstance(anchor, list) or len(anchor) != 2:
        raise ValueError("anchor must be [x, y]")
    x, y, w, h = [int(round(float(value))) for value in roi]
    ax, ay = [int(round(float(value))) for value in anchor]
    x = max(0, min(CANVAS_SIZE[0], x))
    y = max(0, min(CANVAS_SIZE[1], y))
    w = max(2, min(CANVAS_SIZE[0] - x, w))
    h = max(2, min(CANVAS_SIZE[1] - y, h))
    ax = max(0, min(CANVAS_SIZE[0], ax))
    ay = max(0, min(CANVAS_SIZE[1], ay))
    action = raw.get("action") or "REEXTRACT_FROM_CANONICAL"
    if action not in DEFAULT_ACTIONS:
        raise ValueError(f"unknown action: {action}")
    item = items[part_id]
    return {
        "part_id": part_id,
        "semantic_role": raw.get("semantic_role") or item["semantic_role_default"],
        "expected_group": raw.get("expected_group") or item["semantic_group"],
        "roi": [x, y, w, h],
        "anchor": [ax, ay],
        "action": action,
        "note": raw.get("note", ""),
        "updated_at": now(),
    }


def save_override(payload: dict) -> dict:
    doc = load_override_doc()
    delete_part_id = payload.get("delete_part_id")
    if delete_part_id:
        doc["overrides"].pop(delete_part_id, None)
    else:
        override = validate_override(payload.get("override", {}))
        doc["overrides"][override["part_id"]] = override
    doc["updated_at"] = now()
    save_json(OVERRIDES_PATH, doc)
    write_summary(doc)
    return {"ok": True, "overrides": doc["overrides"], "summary_path": rel(SUMMARY_PATH)}


def maybe_open_browser(port: int) -> None:
    try:
        subprocess.run(["open", f"http://127.0.0.1:{port}/"], check=False)
    except Exception:
        pass


class Handler(BaseHTTPRequestHandler):
    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_bytes(self, payload: bytes, content_type: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_bytes(INDEX_HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if parsed.path == "/favicon.ico":
            self.send_bytes(b"", "image/x-icon")
            return
        if parsed.path == "/api/state":
            ensure_initialized()
            doc = load_override_doc()
            self.send_json(
                {
                    "items": manifest_items(),
                    "overrides": doc.get("overrides", {}),
                    "canonical_path": rel(CANONICAL),
                    "actions": DEFAULT_ACTIONS,
                    "save_path": rel(OVERRIDES_PATH),
                    "summary_path": rel(SUMMARY_PATH),
                }
            )
            return
        if parsed.path == "/asset":
            raw = parse_qs(parsed.query).get("path", [""])[0]
            path = (ROOT / raw).resolve()
            if not str(path).startswith(str(ROOT)) or not path.exists():
                self.send_json({"error": "asset not found"}, HTTPStatus.NOT_FOUND)
                return
            content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            self.send_bytes(path.read_bytes(), content_type)
            return
        self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/override":
            self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            self.send_json(save_override(payload))
        except Exception as exc:  # noqa: BLE001
            self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Run G1.6 semantic anchor editor")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5174)
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--init-only", action="store_true")
    args = parser.parse_args()

    if not MANIFEST_PATH.exists():
        raise SystemExit(f"manifest missing: {MANIFEST_PATH}")
    if not CANONICAL.exists():
        raise SystemExit(f"canonical missing: {CANONICAL}")
    ensure_initialized()
    if args.init_only:
        print(OVERRIDES_PATH)
        print(SUMMARY_PATH)
        return

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"G1.6 semantic anchor editor: http://{args.host}:{args.port}/")
    print(f"Overrides JSON: {OVERRIDES_PATH}")
    if not args.no_open:
        maybe_open_browser(args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

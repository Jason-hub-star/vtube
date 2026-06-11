#!/usr/bin/env python3
"""Serve and save human review for the Cubism v2 material contact sheet."""

from __future__ import annotations

import argparse
import json
import mimetypes
import subprocess
import sys
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path("/Users/family/jason/Vtube")
PACK = ROOT / "experiments/cubism-v2-new-character-001/material_pack_v0"
MANIFEST_PATH = PACK / "material_asset_manifest.json"
REVIEW_PATH = PACK / "reports/material_human_review.json"
SUMMARY_JSON = PACK / "reports/material_human_review_summary.json"
SUMMARY_MD = PACK / "reports/material_human_review_summary.md"
FIX_QUEUE_PATH = PACK / "reports/material_review_fix_queue.json"
CONTACT_SHEET = PACK / "reports/material_contact_sheet.png"

VERDICTS = ["KEEP", "REVISE", "REGENERATE", "MERGE", "IGNORE"]
ISSUE_TAGS = {
    "missing_part": "파츠 없음",
    "bad_alpha": "테두리 지저분함",
    "misaligned": "위치 안 맞음",
    "style_mismatch": "그림체 다름",
    "underpaint_missing": "밑색 부족",
    "clipping_risk": "마스크 위험",
    "draw_order_issue": "앞뒤 순서 문제",
    "overhang_issue": "튀어나온 부분 문제",
    "too_coarse": "너무 크게 잘림",
    "too_tiny": "너무 작거나 얇음",
    "placeholder": "임시 그림 같음",
}


INDEX_HTML = r"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Cubism v2 파츠 검수</title>
  <style>
    :root {
      --blue: #3182f6;
      --green: #00a86b;
      --red: #f04452;
      --orange: #f59f00;
      --purple: #8b5cf6;
      --gray-00: #f7f8fa;
      --gray-10: #eef1f5;
      --gray-50: #6b7684;
      --gray-80: #191f28;
      --line: #e5e8ee;
      font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", sans-serif;
    }
    * { box-sizing: border-box; }
    body { margin: 0; background: var(--gray-00); color: var(--gray-80); }
    .app { min-height: 100vh; display: grid; grid-template-rows: auto 1fr; }
    header { position: sticky; top: 0; z-index: 10; background: rgba(247,248,250,.94); backdrop-filter: blur(14px); border-bottom: 1px solid var(--line); padding: 18px 24px 14px; }
    h1 { margin: 0; font-size: 24px; letter-spacing: 0; }
    .sub { color: var(--gray-50); margin-top: 6px; font-size: 14px; }
    .toprow { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
    .stats { display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }
    .pill { border-radius: 999px; padding: 7px 11px; background: white; border: 1px solid var(--line); font-size: 13px; color: var(--gray-50); }
    .layout { display: grid; grid-template-columns: minmax(460px, 1fr) 420px; gap: 16px; padding: 16px; align-items: start; }
    .panel { background: white; border: 1px solid var(--line); border-radius: 8px; box-shadow: 0 8px 24px rgba(25,31,40,.04); }
    .left { min-height: calc(100vh - 124px); overflow: hidden; }
    .toolbar { display: grid; grid-template-columns: 1fr auto; gap: 12px; padding: 14px; border-bottom: 1px solid var(--line); }
    input, select, textarea { width: 100%; border: 1px solid var(--line); border-radius: 8px; padding: 11px 12px; font: inherit; background: white; outline: none; }
    input:focus, select:focus, textarea:focus { border-color: var(--blue); box-shadow: 0 0 0 3px rgba(49,130,246,.12); }
    .filters { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
    .grid { padding: 14px; display: grid; grid-template-columns: repeat(auto-fill, minmax(156px, 1fr)); gap: 10px; max-height: calc(100vh - 208px); overflow: auto; }
    .tile { border: 2px solid var(--line); border-radius: 8px; background: #fff; padding: 8px; text-align: left; cursor: pointer; min-height: 206px; display: grid; grid-template-rows: 118px auto auto; gap: 6px; }
    .tile:hover { border-color: var(--blue); }
    .tile.active { border-color: var(--blue); box-shadow: 0 0 0 3px rgba(49,130,246,.12); }
    .tile.review-needed { border-color: var(--orange); }
    .tile.bad { border-color: var(--red); }
    .thumb { width: 100%; height: 118px; object-fit: contain; background-image: linear-gradient(45deg,#eef1f5 25%,transparent 25%), linear-gradient(-45deg,#eef1f5 25%,transparent 25%), linear-gradient(45deg,transparent 75%,#eef1f5 75%), linear-gradient(-45deg,transparent 75%,#eef1f5 75%); background-size: 18px 18px; background-position: 0 0,0 9px,9px -9px,-9px 0; border-radius: 6px; }
    .part { font-size: 13px; font-weight: 700; overflow-wrap: anywhere; color: var(--gray-80); }
    .ko { font-size: 12px; color: var(--gray-50); }
    .tagline { display: flex; gap: 4px; flex-wrap: wrap; }
    .badge { font-size: 11px; padding: 3px 6px; border-radius: 999px; color: white; background: var(--blue); }
    .badge.risk { background: var(--orange); }
    .badge.derived { background: var(--purple); }
    .badge.under { background: var(--green); }
    .badge.merge { background: #64748b; }
    .badge.verdict { background: var(--gray-80); }
    .detail { position: sticky; top: 104px; padding: 16px; }
    .preview { width: 100%; height: 360px; object-fit: contain; border-radius: 8px; background-color: #f3f5f8; background-image: linear-gradient(45deg,#e8ecf2 25%,transparent 25%), linear-gradient(-45deg,#e8ecf2 25%,transparent 25%), linear-gradient(45deg,transparent 75%,#e8ecf2 75%), linear-gradient(-45deg,transparent 75%,#e8ecf2 75%); background-size: 24px 24px; background-position: 0 0,0 12px,12px -12px,-12px 0; }
    .meta { margin: 12px 0 14px; display: grid; gap: 6px; font-size: 13px; color: var(--gray-50); }
    .meta b { color: var(--gray-80); }
    .buttons { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
    button { border: 0; border-radius: 8px; padding: 12px 10px; font: inherit; font-weight: 700; cursor: pointer; background: #edf2ff; color: var(--blue); }
    button.primary { background: var(--blue); color: white; }
    button.keep { background: #e6f8f1; color: var(--green); }
    button.revise { background: #fff4db; color: #b86b00; }
    button.regen { background: #ffe9ec; color: var(--red); }
    button.merge { background: #eef1f5; color: #475569; }
    button.active { outline: 3px solid rgba(49,130,246,.22); }
    .issues { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 14px 0; }
    label.check { display: flex; align-items: center; gap: 8px; padding: 9px; border: 1px solid var(--line); border-radius: 8px; font-size: 13px; }
    label.check input { width: auto; }
    textarea { min-height: 82px; resize: vertical; }
    .actions { display: flex; gap: 8px; margin-top: 10px; }
    .actions button { flex: 1; }
    .sheetlink { display: block; margin-top: 12px; color: var(--blue); text-decoration: none; font-size: 13px; }
    @media (max-width: 980px) {
      .layout { grid-template-columns: 1fr; }
      .detail { position: static; }
      .preview { height: 300px; }
      .toolbar { grid-template-columns: 1fr; }
      .filters { justify-content: flex-start; }
    }
  </style>
</head>
<body>
<div class="app">
  <header>
    <div class="toprow">
      <div>
        <h1>Cubism v2 파츠 검수</h1>
        <div class="sub">작은 파츠를 고르고, 유지/수정/재생성/병합 판정을 저장합니다.</div>
      </div>
      <div class="stats" id="stats"></div>
    </div>
  </header>
  <main class="layout">
    <section class="panel left">
      <div class="toolbar">
        <input id="search" placeholder="파츠 이름, 한글명, 태그 검색" />
        <div class="filters">
          <select id="gate">
            <option value="all">전체</option>
            <option value="needs">먼저 볼 것</option>
            <option value="DIRECT_VISIBLE">바로 분리</option>
            <option value="DIRECT_VISIBLE_RISK">정리 필요</option>
            <option value="DERIVED_KEYPOSE_REQUIRED">보조 생성</option>
            <option value="UNDERPAINT_REQUIRED">밑색</option>
            <option value="SIMPLIFY_OR_MERGE">병합/메타</option>
          </select>
          <select id="verdictFilter">
            <option value="all">판정 전체</option>
            <option value="UNREVIEWED">미검수</option>
            <option value="KEEP">유지</option>
            <option value="REVISE">수정</option>
            <option value="REGENERATE">재생성</option>
            <option value="MERGE">병합</option>
            <option value="IGNORE">제외</option>
          </select>
        </div>
      </div>
      <div class="grid" id="grid"></div>
    </section>
    <aside class="panel detail" id="detail"></aside>
  </main>
</div>
<script>
const labels = {
  DIRECT_VISIBLE: ["바로 분리", "badge"],
  DIRECT_VISIBLE_RISK: ["정리 필요", "badge risk"],
  DERIVED_KEYPOSE_REQUIRED: ["보조 생성", "badge derived"],
  UNDERPAINT_REQUIRED: ["밑색", "badge under"],
  SIMPLIFY_OR_MERGE: ["병합/메타", "badge merge"]
};
const verdictKo = {UNREVIEWED:"미검수", KEEP:"유지", REVISE:"수정", REGENERATE:"재생성", MERGE:"병합", IGNORE:"제외"};
const issueLabels = ISSUE_LABELS_PLACEHOLDER;
let state = {items: [], reviews: {}, selected: null, summary: {}};

async function load() {
  const res = await fetch('/api/state');
  state = await res.json();
  state.selected = state.items.find(x => x.part_id === state.selected)?.part_id || (state.items[0]?.part_id);
  render();
}
function reviewOf(id) {
  return state.reviews[id] || {part_id:id, verdict:"UNREVIEWED", issue_tags:[], human_note:""};
}
function needsReview(item) {
  return item.feasibility !== 'DIRECT_VISIBLE' || (item.risk_tags && item.risk_tags.length);
}
function itemImage(item) {
  if (item.output_path) return '/asset?path=' + encodeURIComponent(item.output_path);
  return '/asset?path=' + encodeURIComponent('experiments/cubism-v2-new-character-001/material_pack_v0/reports/material_contact_sheet.png');
}
function renderStats() {
  const counts = state.summary.verdict_counts || {};
  const total = state.items.length;
  const reviewed = total - (counts.UNREVIEWED || 0);
  document.getElementById('stats').innerHTML = [
    `<span class="pill">전체 ${total}</span>`,
    `<span class="pill">검수 ${reviewed}</span>`,
    `<span class="pill">수정 ${(counts.REVISE||0) + (counts.REGENERATE||0)}</span>`,
    `<span class="pill">저장: material_human_review.json</span>`
  ].join('');
}
function filteredItems() {
  const q = document.getElementById('search').value.trim().toLowerCase();
  const gate = document.getElementById('gate').value;
  const vf = document.getElementById('verdictFilter').value;
  return state.items.filter(item => {
    const r = reviewOf(item.part_id);
    const text = [item.part_id, item.label_ko, item.group, ...(item.risk_tags||[])].join(' ').toLowerCase();
    if (q && !text.includes(q)) return false;
    if (gate === 'needs' && !needsReview(item)) return false;
    if (gate !== 'all' && gate !== 'needs' && item.feasibility !== gate) return false;
    if (vf !== 'all' && r.verdict !== vf) return false;
    return true;
  });
}
function renderGrid() {
  const grid = document.getElementById('grid');
  grid.innerHTML = '';
  for (const item of filteredItems()) {
    const r = reviewOf(item.part_id);
    const [label, cls] = labels[item.feasibility] || [item.feasibility, 'badge'];
    const tile = document.createElement('button');
    tile.className = 'tile ' + (item.part_id === state.selected ? 'active ' : '') + (needsReview(item) ? 'review-needed ' : '') + (['REVISE','REGENERATE'].includes(r.verdict) ? 'bad ' : '');
    tile.onclick = () => { state.selected = item.part_id; render(); };
    tile.innerHTML = `
      <img class="thumb" src="${itemImage(item)}" alt="">
      <div>
        <div class="tagline"><span class="${cls}">${label}</span><span class="badge verdict">${verdictKo[r.verdict] || r.verdict}</span></div>
        <div class="part">${item.part_id}</div>
      </div>
      <div class="ko">${item.label_ko}</div>`;
    grid.appendChild(tile);
  }
}
function renderDetail() {
  const item = state.items.find(x => x.part_id === state.selected) || state.items[0];
  const wrap = document.getElementById('detail');
  if (!item) { wrap.innerHTML = '<p>파츠 없음</p>'; return; }
  const r = reviewOf(item.part_id);
  const buttons = [
    ['KEEP','유지','keep'],
    ['REVISE','수정','revise'],
    ['REGENERATE','재생성','regen'],
    ['MERGE','병합','merge'],
    ['IGNORE','제외','merge']
  ].map(([v,k,c]) => `<button class="${c} ${r.verdict===v?'active':''}" onclick="setVerdict('${v}')">${k}</button>`).join('');
  const checks = Object.entries(issueLabels).map(([code,label]) => `
    <label class="check"><input type="checkbox" value="${code}" ${r.issue_tags.includes(code)?'checked':''} onchange="toggleIssue('${code}', this.checked)" /> ${label}</label>`).join('');
  wrap.innerHTML = `
    <img class="preview" src="${itemImage(item)}" alt="">
    <div class="meta">
      <div><b>${item.part_id}</b> · ${item.label_ko}</div>
      <div>그룹: ${item.group} / 종류: ${item.feasibility}</div>
      <div>bbox: ${(item.bbox_actual || item.bbox || []).join(', ') || '없음'}</div>
      <div>주의 태그: ${(item.risk_tags || []).join(', ') || '없음'}</div>
    </div>
    <div class="buttons">${buttons}</div>
    <div class="issues">${checks}</div>
    <textarea id="note" placeholder="수정할 내용을 쉽게 적어주세요. 예: 입선이 턱 쪽으로 너무 큼">${r.human_note || ''}</textarea>
    <div class="actions">
      <button class="primary" onclick="saveCurrent()">저장</button>
      <button onclick="nextNeeds()">다음 문제 후보</button>
    </div>
    <a class="sheetlink" href="/asset?path=experiments/cubism-v2-new-character-001/material_pack_v0/reports/material_contact_sheet.png" target="_blank">전체 contact sheet 열기</a>`;
}
function render() {
  renderStats(); renderGrid(); renderDetail();
}
function setVerdict(v) {
  const id = state.selected;
  state.reviews[id] = {...reviewOf(id), verdict:v};
  renderDetail(); renderGrid(); renderStats();
}
function toggleIssue(code, checked) {
  const id = state.selected;
  const r = reviewOf(id);
  const tags = new Set(r.issue_tags || []);
  checked ? tags.add(code) : tags.delete(code);
  state.reviews[id] = {...r, issue_tags:[...tags].sort()};
}
async function saveCurrent() {
  const id = state.selected;
  const note = document.getElementById('note')?.value || '';
  const review = {...reviewOf(id), human_note:note};
  state.reviews[id] = review;
  const res = await fetch('/api/review', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(review)});
  const data = await res.json();
  state.reviews = data.reviews;
  state.summary = data.summary;
  render();
}
function nextNeeds() {
  const list = filteredItems();
  const current = list.findIndex(x => x.part_id === state.selected);
  const next = list.slice(current + 1).concat(list.slice(0, current + 1)).find(item => needsReview(item) && reviewOf(item.part_id).verdict === 'UNREVIEWED');
  if (next) state.selected = next.part_id;
  render();
}
document.getElementById('search').addEventListener('input', renderGrid);
document.getElementById('gate').addEventListener('change', renderGrid);
document.getElementById('verdictFilter').addEventListener('change', renderGrid);
load();
</script>
</body>
</html>
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def manifest_items() -> list[dict]:
    manifest = load_json(MANIFEST_PATH, {"layers": []})
    items = []
    for entry in manifest.get("layers", []):
        items.append(
            {
                "part_id": entry["part_id"],
                "layer_name": entry["layer_name"],
                "label_ko": entry["label_ko"],
                "group": entry["group"],
                "feasibility": entry["feasibility"],
                "source_type": entry["source_type"],
                "risk_tags": entry.get("risk_tags", []),
                "output_path": entry.get("output_path"),
                "bbox": entry.get("bbox"),
                "bbox_actual": entry.get("bbox_actual"),
                "draw_order_band": entry.get("draw_order_band"),
                "merged_into": entry.get("merged_into"),
                "include_in_import_psd": entry.get("include_in_import_psd", False),
                "notes": entry.get("notes", ""),
            }
        )
    return items


def default_reviews(items: list[dict]) -> dict:
    return {
        item["part_id"]: {
            "part_id": item["part_id"],
            "verdict": "UNREVIEWED",
            "issue_tags": [],
            "human_note": "",
            "updated_at": None,
        }
        for item in items
    }


def load_review_doc() -> dict:
    items = manifest_items()
    base = {
        "schema_version": 1,
        "experiment_id": "cubism-v2-new-character-001",
        "pack_id": "material_pack_v0",
        "generated_at": now(),
        "manifest": rel(MANIFEST_PATH),
        "contact_sheet": rel(CONTACT_SHEET),
        "reviews": default_reviews(items),
    }
    if REVIEW_PATH.exists():
        current = load_json(REVIEW_PATH, {})
        base["reviews"].update(current.get("reviews", {}))
        base["generated_at"] = current.get("generated_at", base["generated_at"])
    return base


def summarize(review_doc: dict) -> dict:
    items = manifest_items()
    reviews = review_doc.get("reviews", {})
    verdict_counts = {key: 0 for key in ["UNREVIEWED", *VERDICTS]}
    issue_counts = {key: 0 for key in ISSUE_TAGS}
    fix_queue = []
    for item in items:
        review = reviews.get(item["part_id"], {})
        verdict = review.get("verdict", "UNREVIEWED")
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
        for tag in review.get("issue_tags", []):
            issue_counts[tag] = issue_counts.get(tag, 0) + 1
        if verdict in {"REVISE", "REGENERATE"}:
            fix_queue.append(
                {
                    "part_id": item["part_id"],
                    "label_ko": item["label_ko"],
                    "group": item["group"],
                    "verdict": verdict,
                    "issue_tags": review.get("issue_tags", []),
                    "human_note": review.get("human_note", ""),
                    "source_image": item.get("output_path"),
                    "suggested_action": "regenerate_roi_part" if verdict == "REGENERATE" else "manual_or_mask_cleanup",
                }
            )
    reviewed = len(items) - verdict_counts.get("UNREVIEWED", 0)
    status = "PASS_HUMAN_REVIEW_COMPLETE" if reviewed == len(items) and not fix_queue else "HUMAN_REVIEW_IN_PROGRESS"
    summary = {
        "schema_version": 1,
        "status": status,
        "generated_at": now(),
        "review_path": rel(REVIEW_PATH),
        "fix_queue_path": rel(FIX_QUEUE_PATH),
        "total_items": len(items),
        "reviewed_items": reviewed,
        "verdict_counts": verdict_counts,
        "issue_counts": issue_counts,
        "fix_queue_count": len(fix_queue),
        "critical_next_action": "Fix REVISE/REGENERATE parts before Cubism import smoke." if fix_queue else "Continue to Cubism import smoke if visual QA is acceptable.",
    }
    save_json(SUMMARY_JSON, summary)
    save_json(FIX_QUEUE_PATH, {"schema_version": 1, "generated_at": now(), "items": fix_queue, "counts": {"queued": len(fix_queue)}})
    SUMMARY_MD.write_text(
        "\n".join(
            [
                "# Cubism v2 Material Human Review Summary",
                "",
                f"- status: `{summary['status']}`",
                f"- reviewed: `{reviewed}/{len(items)}`",
                f"- fix queue: `{len(fix_queue)}`",
                f"- review json: `{summary['review_path']}`",
                f"- fix queue json: `{summary['fix_queue_path']}`",
                "",
                "## Verdict Counts",
                "",
                *[f"- `{key}`: {value}" for key, value in verdict_counts.items()],
                "",
                "## Next Action",
                "",
                summary["critical_next_action"],
                "",
            ]
        ),
        encoding="utf-8",
    )
    return summary


def save_review(payload: dict) -> dict:
    part_id = payload.get("part_id")
    if not part_id:
        raise ValueError("part_id is required")
    items = {item["part_id"]: item for item in manifest_items()}
    if part_id not in items:
        raise ValueError(f"unknown part_id: {part_id}")
    verdict = payload.get("verdict", "UNREVIEWED")
    if verdict not in {"UNREVIEWED", *VERDICTS}:
        raise ValueError(f"unknown verdict: {verdict}")
    issue_tags = sorted({tag for tag in payload.get("issue_tags", []) if tag in ISSUE_TAGS})
    doc = load_review_doc()
    doc["reviews"][part_id] = {
        "part_id": part_id,
        "verdict": verdict,
        "issue_tags": issue_tags,
        "human_note": payload.get("human_note", ""),
        "updated_at": now(),
    }
    doc["updated_at"] = now()
    save_json(REVIEW_PATH, doc)
    summary = summarize(doc)
    return {"ok": True, "reviews": doc["reviews"], "summary": summary}


def ensure_initialized() -> None:
    if not REVIEW_PATH.exists():
        doc = load_review_doc()
        save_json(REVIEW_PATH, doc)
        summarize(doc)


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
            html = INDEX_HTML.replace("ISSUE_LABELS_PLACEHOLDER", json.dumps(ISSUE_TAGS, ensure_ascii=False))
            self.send_bytes(html.encode("utf-8"), "text/html; charset=utf-8")
            return
        if parsed.path == "/favicon.ico":
            self.send_bytes(b"", "image/x-icon")
            return
        if parsed.path == "/api/state":
            ensure_initialized()
            review = load_review_doc()
            summary = summarize(review)
            self.send_json({"items": manifest_items(), "reviews": review["reviews"], "summary": summary})
            return
        if parsed.path == "/asset":
            query = parse_qs(parsed.query)
            raw = query.get("path", [""])[0]
            path = (ROOT / raw).resolve()
            if not str(path).startswith(str(ROOT)) or not path.exists():
                self.send_json({"error": "asset not found"}, HTTPStatus.NOT_FOUND)
                return
            content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            self.send_bytes(path.read_bytes(), content_type)
            return
        self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/review":
            self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            self.send_json(save_review(payload))
        except Exception as exc:  # noqa: BLE001
            self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Cubism v2 material review UI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5162)
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--init-only", action="store_true", help="Create review JSON and summary without starting the server")
    args = parser.parse_args()

    if not MANIFEST_PATH.exists():
        raise SystemExit(f"manifest missing: {MANIFEST_PATH}")
    ensure_initialized()
    if args.init_only:
        print(REVIEW_PATH)
        print(SUMMARY_JSON)
        return

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}/"
    print(f"Cubism v2 material review UI: {url}")
    print(f"Review JSON: {REVIEW_PATH}")
    if not args.no_open:
        maybe_open_browser(args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

const app = document.querySelector("#app");

const STAGE_LABELS = {
  P0: "설정",
  P1: "시트 생성",
  H1: "스타일 락",
  P2: "추출·배치",
  H1_5: "배치 검수",
  P3: "자동 리깅",
  P4: "수치 QA",
  P5: "런타임 스윕",
  P6: "웹캠 연동",
  H2: "최종 승인",
};

const PANEL_ORDER_KEY = "ct_panel_order_v1";
const DEFAULT_PANELS = ["timeline", "gate", "feed", "qa", "log"];

const state = {
  runs: [],
  runId: null,
  runState: null,
  logs: [],
  lastSeq: 0,
  notifiedGates: new Set(),
  seenArtifacts: new Set(),
  gateDrafts: {},
  pinnedRun: false,
};

function panelOrder() {
  try {
    const saved = JSON.parse(localStorage.getItem(PANEL_ORDER_KEY) || "null");
    if (Array.isArray(saved) && saved.length === DEFAULT_PANELS.length) return saved;
  } catch {}
  return [...DEFAULT_PANELS];
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`${url} ${response.status}`);
  return response.json();
}

function pickRun(runs) {
  const active = runs.find((run) => run.status === "GATE_WAITING" || run.status === "RUNNING");
  return (active || runs[0])?.run_id || null;
}

async function poll() {
  try {
    const { runs } = await fetchJson("/api/runs");
    state.runs = runs;
    if (!state.runId || (!state.pinnedRun && !runs.some((r) => r.run_id === state.runId))) {
      state.runId = pickRun(runs);
      state.lastSeq = 0;
      state.logs = [];
    }
    if (state.runId) {
      state.runState = await fetchJson(`/api/runs/${state.runId}/state`);
      const tail = await fetchJson(`/api/runs/${state.runId}/events?after=${state.lastSeq}`);
      for (const event of tail.events) {
        if (event.type === "log") state.logs.push(event);
        if (["stage_started", "stage_completed", "stage_failed", "gate_waiting", "gate_resolved", "run_completed", "run_failed"].includes(event.type)) {
          state.logs.push(event);
        }
      }
      if (state.logs.length > 400) state.logs = state.logs.slice(-400);
      state.lastSeq = Math.max(state.lastSeq, tail.last_seq || 0);
      notifyGates();
    }
    if (!state.interacting) render();
  } catch (error) {
    app.innerHTML = `<div class="loading">관제탑 서버에 연결할 수 없어요: ${escapeHtml(error.message)}</div>`;
  }
}

function notifyGates() {
  const gates = state.runState?.gates || {};
  for (const [gateId, gate] of Object.entries(gates)) {
    const key = `${state.runId}:${gate.waiting_seq}`;
    if (gate.status !== "WAITING" || state.notifiedGates.has(key)) continue;
    state.notifiedGates.add(key);
    beep();
    if ("Notification" in window && Notification.permission === "granted") {
      new Notification("AUTORIG 관제탑", { body: `주인님, 검수 차례예요 — ${gate.title || gateId}` });
    }
  }
}

function beep() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.frequency.value = 880;
    gain.gain.setValueAtTime(0.12, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
    osc.connect(gain).connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.5);
  } catch {}
}

/* ---------- 렌더 ---------- */

function render() {
  app.replaceChildren(Header(), Panels());
}

function Header() {
  const runState = state.runState;
  const header = document.createElement("div");
  header.className = "header";

  const title = document.createElement("h1");
  title.textContent = "AUTORIG 관제탑";

  const pill = document.createElement("span");
  const status = runState?.status || "대기";
  const pillClass = { GATE_WAITING: "gate", PASS: "done", FAILED: "failed" }[status] || "";
  pill.className = `status-pill ${pillClass}`;
  pill.textContent = {
    RUNNING: "진행 중",
    GATE_WAITING: "검수 기다리는 중",
    PASS: "완료",
    FAILED: "실패",
    UNKNOWN: "대기",
  }[status] || status;

  const select = document.createElement("select");
  select.className = "run-select";
  for (const run of state.runs) {
    const option = document.createElement("option");
    option.value = run.run_id;
    option.textContent = `${run.run_id} · ${run.title || ""} (${run.status})`;
    if (run.run_id === state.runId) option.selected = true;
    select.append(option);
  }
  select.addEventListener("change", () => {
    state.runId = select.value;
    state.pinnedRun = true;
    state.lastSeq = 0;
    state.logs = [];
    poll();
  });

  const budget = document.createElement("div");
  budget.className = "budget";
  if (runState?.started_at) {
    const total = runState.budget_seconds || 3600;
    const end = runState.ended_at ? new Date(runState.ended_at) : new Date();
    const elapsed = Math.max(0, (end - new Date(runState.started_at)) / 1000);
    const ratio = Math.min(1, elapsed / total);
    budget.innerHTML = `
      <div class="labels"><span>경과 ${fmtDuration(elapsed)}</span><span>예산 ${fmtDuration(total)}</span></div>
      <div class="bar"><div class="fill ${elapsed > total ? "over" : ""}" style="width:${(ratio * 100).toFixed(1)}%"></div></div>`;
  }

  if ("Notification" in window && Notification.permission === "default") {
    const allow = document.createElement("button");
    allow.className = "btn secondary";
    allow.textContent = "알림 켜기";
    allow.addEventListener("click", () => Notification.requestPermission().then(render));
    header.append(title, pill, select, budget, allow);
  } else {
    header.append(title, pill, select, budget);
  }
  return header;
}

function Panels() {
  const wrap = document.createElement("div");
  wrap.className = "panels";
  const builders = { timeline: TimelinePanel, gate: GatePanel, feed: FeedPanel, qa: QaPanel, log: LogPanel };
  for (const key of panelOrder()) {
    const panel = builders[key]?.();
    if (panel) {
      panel.dataset.panel = key;
      enablePanelDrag(panel, wrap);
      wrap.append(panel);
    }
  }
  return wrap;
}

function panelShell(title, hint) {
  const panel = document.createElement("section");
  panel.className = "panel";
  const head = document.createElement("div");
  head.className = "panel-head";
  head.innerHTML = `<span class="drag-handle" draggable="true" title="끌어서 순서 바꾸기">⠿</span><h2>${escapeHtml(title)}</h2><span class="hint">${escapeHtml(hint || "")}</span>`;
  panel.append(head);
  return panel;
}

function enablePanelDrag(panel, container) {
  const handle = () => panel.querySelector(".drag-handle");
  panel.addEventListener("dragstart", (e) => {
    if (!e.target.classList?.contains("drag-handle")) {
      // 핸들에서만 시작 허용
    }
    panel.classList.add("dragging");
    e.dataTransfer.setData("text/plain", panel.dataset.panel);
    e.dataTransfer.effectAllowed = "move";
  });
  panel.addEventListener("dragend", () => panel.classList.remove("dragging"));
  panel.addEventListener("dragover", (e) => {
    e.preventDefault();
    panel.classList.add("drag-over");
  });
  panel.addEventListener("dragleave", () => panel.classList.remove("drag-over"));
  panel.addEventListener("drop", (e) => {
    e.preventDefault();
    panel.classList.remove("drag-over");
    const draggedKey = e.dataTransfer.getData("text/plain");
    if (!draggedKey || draggedKey === panel.dataset.panel) return;
    const order = panelOrder().filter((k) => k !== draggedKey);
    order.splice(order.indexOf(panel.dataset.panel), 0, draggedKey);
    localStorage.setItem(PANEL_ORDER_KEY, JSON.stringify(order));
    render();
  });
  // 핸들에서만 드래그 시작되도록
  panel.draggable = false;
  setTimeout(() => {
    const h = handle();
    if (h) {
      h.addEventListener("mousedown", () => (panel.draggable = true));
      h.addEventListener("mouseup", () => (panel.draggable = false));
    }
  });
  panel.addEventListener("dragend", () => (panel.draggable = false));
}

function TimelinePanel() {
  const panel = panelShell("스테이지 진행", "P0~P6 + 검수 게이트");
  const row = document.createElement("div");
  row.className = "timeline";
  const stages = state.runState?.stages || {};
  const gates = state.runState?.gates || {};
  for (const key of state.runState?.stage_order || Object.keys(STAGE_LABELS)) {
    const isGate = key.startsWith("H");
    const info = isGate ? gates[key] : stages[key];
    const chip = document.createElement("div");
    let cls = "";
    let progress = 0;
    if (info) {
      if (isGate) {
        cls = info.status === "WAITING" ? "gate-wait" : info.status === "RESOLVED" ? "done" : "";
        progress = info.status === "RESOLVED" ? 1 : 0;
      } else {
        cls = { RUNNING: "running", DONE: "done", FAILED: "failed" }[info.status] || "";
        progress = info.progress || 0;
      }
    }
    chip.className = `stage-chip ${cls}`;
    chip.innerHTML = `<b>${escapeHtml(key.replace("_5", ".5"))}</b>${escapeHtml(STAGE_LABELS[key] || "")}
      <div class="bar"><i style="width:${(progress * 100).toFixed(0)}%"></i></div>`;
    row.append(chip);
  }
  panel.append(row);
  return panel;
}

function GatePanel() {
  const panel = panelShell("검수 게이트", "기다리는 게이트가 있으면 여기서 처리해요");
  const gates = Object.entries(state.runState?.gates || {}).filter(([, gate]) => gate.status === "WAITING");
  if (!gates.length) {
    const empty = document.createElement("div");
    empty.className = "gate-empty";
    empty.textContent = "지금은 기다리는 검수가 없어요. 파이프라인이 알아서 달리는 중이에요.";
    panel.append(empty);
    return panel;
  }
  for (const [gateId, gate] of gates) {
    panel.append(GateCard(gateId, gate));
  }
  return panel;
}

function GateCard(gateId, gate) {
  const card = document.createElement("div");
  card.className = "gate-card";
  card.innerHTML = `<h3>${escapeHtml(gate.title || gateId)}</h3><p>${escapeHtml(gate.instructions || "")}</p>`;

  if (gate.parts?.length && gate.artifact) {
    card.append(PlacementEditor(gateId, gate));
  } else if (gate.artifact) {
    const link = document.createElement("a");
    link.className = "feed-item";
    link.href = `/runs/${state.runId}/${gate.artifact}`;
    link.target = "_blank";
    link.style.maxWidth = "180px";
    link.innerHTML = `<img src="/runs/${state.runId}/thumbs/${gate.artifact.split("/").pop()}" alt="" /><div class="cap">확인할 이미지</div>`;
    card.append(link);
  }

  const actions = document.createElement("div");
  actions.className = "gate-actions";
  const approve = document.createElement("button");
  approve.className = "btn";
  approve.textContent = gate.parts?.length ? "이대로 진행할게요" : "좋아요, 진행해요";
  approve.addEventListener("click", () => respondGate(gateId, "approve", state.gateDrafts[gateId] || {}));
  const reject = document.createElement("button");
  reject.className = "btn danger";
  reject.textContent = "다시 만들어주세요";
  reject.addEventListener("click", () => respondGate(gateId, "reject", {}));
  actions.append(approve, reject);
  card.append(actions);
  return card;
}

function PlacementEditor(gateId, gate) {
  const wrap = document.createElement("div");
  wrap.className = "gate-editor";
  const canvas = document.createElement("canvas");
  const CANVAS_SPACE = 2048;
  canvas.width = 640;
  canvas.height = 640;
  const scale = canvas.width / CANVAS_SPACE;

  const draft = (state.gateDrafts[gateId] ||= {});
  const positions = {};
  for (const part of gate.parts) {
    positions[part.part_id] = draft[part.part_id]?.target_anchor || [...part.center];
  }

  const image = new Image();
  image.src = `/runs/${state.runId}/${gate.artifact}`;
  image.onload = draw;

  function draw() {
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    if (image.complete && image.naturalWidth) {
      ctx.globalAlpha = 0.9;
      ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
      ctx.globalAlpha = 1;
    }
    for (const part of gate.parts) {
      const [x, y] = positions[part.part_id];
      const moved = draft[part.part_id];
      const px = x * scale;
      const py = y * scale;
      ctx.strokeStyle = moved ? "#f04452" : "#3182f6";
      ctx.fillStyle = ctx.strokeStyle;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(px, py, 9, 0, Math.PI * 2);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(px, py, 2.5, 0, Math.PI * 2);
      ctx.fill();
      ctx.font = "600 11px -apple-system";
      ctx.fillText(part.part_id, px + 13, py + 4);
    }
  }

  let dragging = null;
  function toSpace(e) {
    const rect = canvas.getBoundingClientRect();
    return [((e.clientX - rect.left) / rect.width) * CANVAS_SPACE, ((e.clientY - rect.top) / rect.height) * CANVAS_SPACE];
  }
  canvas.addEventListener("pointerdown", (e) => {
    const [x, y] = toSpace(e);
    for (const part of gate.parts) {
      const [px, py] = positions[part.part_id];
      if (Math.hypot(px - x, py - y) < 60) {
        dragging = part.part_id;
        canvas.setPointerCapture(e.pointerId);
        break;
      }
    }
  });
  canvas.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    const point = toSpace(e);
    positions[dragging] = point;
    draft[dragging] = { target_anchor: [Math.round(point[0]), Math.round(point[1])] };
    draw();
  });
  canvas.addEventListener("pointerup", (e) => {
    dragging = null;
    try { canvas.releasePointerCapture(e.pointerId); } catch {}
  });

  const hint = document.createElement("div");
  hint.className = "editor-hint";
  hint.textContent = "파란 마커를 끌어서 파트 위치를 고칠 수 있어요. 움직인 마커는 빨간색으로 표시돼요.";
  wrap.append(canvas, hint);
  draw();
  return wrap;
}

async function respondGate(gateId, decision, overrides) {
  try {
    await fetchJson(`/api/runs/${state.runId}/gate-response`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ gate: gateId, decision, overrides }),
    });
    delete state.gateDrafts[gateId];
    poll();
  } catch (error) {
    alert(`저장에 실패했어요: ${error.message}`);
  }
}

function FeedPanel() {
  const panel = panelShell("라이브 아티팩트", "생성되는 이미지가 실시간으로 쌓여요");
  const grid = document.createElement("div");
  grid.className = "feed";
  const artifacts = [...(state.runState?.artifacts || [])].reverse();
  if (!artifacts.length) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "아직 생성된 이미지가 없어요.";
    panel.append(empty);
    return panel;
  }
  for (const artifact of artifacts) {
    const name = artifact.path.split("/").pop();
    const item = document.createElement("a");
    const key = `${state.runId}:${artifact.seq}`;
    item.className = `feed-item ${state.seenArtifacts.has(key) ? "" : "fresh"}`;
    state.seenArtifacts.add(key);
    item.href = `/runs/${state.runId}/${artifact.path}`;
    item.target = "_blank";
    item.innerHTML = `<img loading="lazy" src="/runs/${state.runId}/thumbs/${name}" alt="" /><div class="cap">${escapeHtml(artifact.label || name)} · ${escapeHtml(artifact.stage)}</div>`;
    grid.append(item);
  }
  panel.append(grid);
  return panel;
}

function QaPanel() {
  const panel = panelShell("수치 QA", "자동 검사 결과");
  const list = document.createElement("div");
  list.className = "qa-list";
  const qa = state.runState?.qa || [];
  if (!qa.length) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "아직 QA 결과가 없어요.";
    panel.append(empty);
    return panel;
  }
  for (const item of qa) {
    const row = document.createElement("div");
    row.className = "qa-row";
    row.innerHTML = `<span class="qa-badge ${escapeHtml(item.status)}">${escapeHtml(item.status)}</span>
      <span class="name">${escapeHtml(item.name)}</span>
      <span class="value">${escapeHtml(String(item.value ?? ""))} ${escapeHtml(item.detail || "")}</span>`;
    list.append(row);
  }
  panel.append(list);
  return panel;
}

function LogPanel() {
  const panel = panelShell("이벤트 로그", "모든 일이 한 줄씩 기록돼요");
  const box = document.createElement("div");
  box.className = "log-box";
  for (const event of state.logs) {
    const line = document.createElement("div");
    const level = event.level || (event.type?.includes("failed") ? "error" : "");
    line.className = `log-line ${level}`;
    const time = new Date(event.ts).toLocaleTimeString("ko-KR", { hour12: false });
    const message =
      event.type === "log"
        ? event.message
        : {
            stage_started: `${event.stage} 시작`,
            stage_completed: `${event.stage} 완료`,
            stage_failed: `${event.stage} 실패: ${event.error || ""}`,
            gate_waiting: `${event.gate} 게이트 — 검수를 기다려요`,
            gate_resolved: `${event.gate} 게이트 ${event.decision === "approve" ? "승인" : event.decision} (${event.source})`,
            run_completed: `런 완료 (${event.status})`,
            run_failed: `런 실패: ${event.error || ""}`,
          }[event.type] || event.type;
    line.innerHTML = `<span class="t">${time}</span><span class="tag">${escapeHtml(event.type === "log" ? "·" : event.type)}</span><span>${escapeHtml(message)}</span>`;
    box.append(line);
  }
  panel.append(box);
  requestAnimationFrame(() => (box.scrollTop = box.scrollHeight));
  return panel;
}

function fmtDuration(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

// 드래그/조작 중에는 폴링이 DOM을 갈아치우지 않도록 가드
document.addEventListener("pointerdown", () => (state.interacting = true), true);
document.addEventListener("pointerup", () => setTimeout(() => (state.interacting = false), 80), true);
document.addEventListener("dragstart", () => (state.interacting = true), true);
document.addEventListener("dragend", () => setTimeout(() => (state.interacting = false), 80), true);

window.__towerState = state;
poll();
setInterval(poll, 1500);

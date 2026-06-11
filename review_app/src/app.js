import { PartList } from "./components/PartList.js";
import { PartViewer } from "./components/PartViewer.js";
import { VerdictControls } from "./components/VerdictControls.js";
import { IssueTags, normalizeTag } from "./components/IssueTags.js";
import { NotesPanel } from "./components/NotesPanel.js";
import { FixQueuePanel } from "./components/FixQueuePanel.js";
import { MaskEditor } from "./components/MaskEditor.js";

const app = document.querySelector("#app");
let saveTimer = null;

const state = {
  manifest: null,
  reviews: {},
  selectedId: null,
  viewMode: "crop_overlay",
  onionOpacity: 0.55,
  saveState: "idle",
  maskEditorOpen: false,
  maskSaveState: "idle",
  filters: {
    section: null,
    tier: "ALL",
    gate: "ALL",
    query: "",
    verdict: "ALL",
    issueTag: "ALL",
  },
  get allItems() {
    return Object.values(this.manifest?.sections || {}).flat();
  },
  get currentItems() {
    return this.manifest?.sections?.[this.filters.section] || [];
  },
  get normalizedIssueTags() {
    return (this.manifest?.issue_tags || []).map(normalizeTag).filter((tag) => tag.code);
  },
  issueTagLabel(code) {
    return this.normalizedIssueTags.find((tag) => tag.code === code)?.label || code;
  },
  get filteredItems() {
    const query = this.filters.query.trim().toLowerCase();
    return this.currentItems.filter((item) => {
      const review = this.reviews[item.part_id] || {};
      const verdict = review.verdict || "UNREVIEWED";
      const itemTier = item.tier || this.manifest?.tier || "v2_min";
      const itemGate = item.review_gate || "G1_PART_TAXONOMY";
      const itemTags = new Set([...(review.issue_tags || []), ...(item.failure_tags || []), ...(item.auto_issue_tags || [])]);
      const matchesQuery =
        !query ||
        item.part_id.toLowerCase().includes(query) ||
        (item.ko_name || "").toLowerCase().includes(query) ||
        (item.simple_label || "").toLowerCase().includes(query) ||
        (item.group || "").toLowerCase().includes(query);
      const matchesTier = this.filters.tier === "ALL" || itemTier === this.filters.tier;
      const matchesGate = this.filters.gate === "ALL" || itemGate === this.filters.gate;
      const matchesVerdict = this.filters.verdict === "ALL" || verdict === this.filters.verdict;
      const matchesIssueTag = this.filters.issueTag === "ALL" || itemTags.has(this.filters.issueTag);
      return matchesQuery && matchesTier && matchesGate && matchesVerdict && matchesIssueTag;
    });
  },
  get selectedItem() {
    return this.allItems.find((item) => item.part_id === this.selectedId) || this.filteredItems[0] || this.allItems[0];
  },
  get fixQueue() {
    return Object.values(this.reviews)
      .filter((review) => review.verdict === "X" || review.verdict === "REVISE")
      .map((review) => {
        const item = this.allItems.find((candidate) => candidate.part_id === review.part_id) || {};
        return { ...item, ...review };
      })
      .sort((a, b) => `${a.section}:${a.group}:${a.part_id}`.localeCompare(`${b.section}:${b.group}:${b.part_id}`));
  },
};

async function init() {
  try {
    const [manifest, saved] = await Promise.all([fetchJson("/review_manifest.json"), fetchJson("/api/review")]);
    state.manifest = normalizeManifest(manifest);
    state.reviews = saved.review?.reviews || {};
    state.filters.section =
      manifest.ui?.primary_section ||
      Object.keys(manifest.sections || {})[0] ||
      null;
    state.selectedId = state.filteredItems[0]?.part_id || state.allItems[0]?.part_id || null;
    render();
  } catch (error) {
    app.innerHTML = `<div class="fatal">검수 앱을 불러오지 못했습니다: ${escapeHtml(error.message)}</div>`;
  }
}

function render() {
  if (!state.manifest) return;
  const item = state.selectedItem;
  if (!item) {
    app.innerHTML = `<div class="fatal">검수할 항목이 없습니다.</div>`;
    return;
  }
  state.selectedId = item.part_id;
  const review = reviewFor(item.part_id);

  app.replaceChildren();
  app.append(
    Header(),
    PartList({
      state,
      onSelect: (partId) => {
        state.selectedId = partId;
        state.viewMode = defaultViewMode(state.selectedItem);
        state.maskEditorOpen = false;
        state.maskSaveState = "idle";
        state.saveState = "idle";
        render();
      },
      onFilterChange: (patch) => {
        const sectionChanged = patch.section && patch.section !== state.filters.section;
        state.filters = { ...state.filters, ...patch };
        const selectedStillVisible = state.filteredItems.some((candidate) => candidate.part_id === state.selectedId);
        if (!selectedStillVisible) state.selectedId = state.filteredItems[0]?.part_id || null;
        if (sectionChanged) state.viewMode = defaultViewMode(state.selectedItem);
        render();
      },
    }),
    MainReviewArea(item, review),
    RightReviewRail(item, review),
  );
}

function Header() {
  const header = document.createElement("header");
  header.className = "app-header";
  const title = document.createElement("div");
  const h1 = document.createElement("h1");
  h1.textContent = state.manifest.ui?.title || "Live2D 파츠 순도 검수";
  const p = document.createElement("p");
  p.textContent =
    state.manifest.ui?.subtitle ||
    "헷갈리는 기술 말은 줄이고, 캐릭터·파츠·구조·움직임을 차례대로 확인합니다.";
  title.append(h1, p);

  const counts = document.createElement("div");
  counts.className = "counts";
  if (state.manifest.mode === "cubism_v2") {
    for (const chip of cubismProgressChips()) counts.append(chip);
  } else if (state.manifest.mode === "mps_only") {
    for (const chip of mpsProgressChips()) counts.append(chip);
  }
  for (const [key, count] of Object.entries(state.manifest.counts || {})) {
    const chip = document.createElement("span");
    chip.textContent = `${sectionLabel(key)} ${count}개`;
    counts.append(chip);
  }
  header.append(title, counts);
  return header;
}

function cubismProgressChips() {
  const reviewed = state.allItems.filter((item) => {
    const verdict = state.reviews[item.part_id]?.verdict;
    return verdict && verdict !== "UNREVIEWED";
  }).length;
  const failed = state.allItems.filter((item) => state.reviews[item.part_id]?.verdict === "X").length;
  const entries = [
    [`${tierLabel(state.manifest.tier)} 검수`, "ok"],
    [`확인 ${reviewed}/${state.allItems.length}`, ""],
    [`다시 볼 것 ${failed + state.fixQueue.length}`, state.fixQueue.length ? "revise" : ""],
  ];
  return entries.map(([label, className]) => {
    const chip = document.createElement("span");
    chip.textContent = label;
    if (className) chip.className = className;
    return chip;
  });
}

function mpsProgressChips() {
  const reviewed = state.allItems.filter((item) => {
    const verdict = state.reviews[item.part_id]?.verdict;
    return verdict && verdict !== "UNREVIEWED";
  }).length;
  const useful = state.allItems.filter((item) => ["O", "REVISE"].includes(state.reviews[item.part_id]?.verdict)).length;
  const failed = state.allItems.filter((item) => state.reviews[item.part_id]?.verdict === "X").length;
  const target = state.manifest.ui?.practical_gate_target || 5;
  const entries = [
    [`검수 ${reviewed}/${state.allItems.length}`, ""],
    [`실용 후보 ${useful}/${target}`, useful >= target ? "ok" : "revise"],
    [`실패 ${failed}`, failed ? "bad" : ""],
  ];
  return entries.map(([label, className]) => {
    const chip = document.createElement("span");
    chip.textContent = label;
    if (className) chip.className = className;
    return chip;
  });
}

function MainReviewArea(item, review) {
  const main = document.createElement("main");
  main.className = "review-main";
  const viewer = PartViewer({
    item,
    viewMode: state.viewMode,
    onionOpacity: state.onionOpacity,
    onModeChange: (mode) => {
      state.viewMode = mode;
      render();
    },
    onOpacityChange: (opacity) => {
      state.onionOpacity = opacity;
      render();
    },
  });

  main.append(viewer);
  return main;
}

function RightReviewRail(item, review) {
  const rail = document.createElement("aside");
  rail.className = "right-rail";

  const controls = ReviewControls(item, review);
  const queue = FixQueuePanel({
    queue: state.fixQueue,
    onSelect: (partId) => {
      const found = state.allItems.find((candidate) => candidate.part_id === partId);
      if (found) state.filters.section = found.section;
      state.selectedId = partId;
      state.viewMode = defaultViewMode(found);
      render();
    },
  });
  rail.append(QaFlowPanel(item), controls, queue);
  return rail;
}

function ReviewControls(item, review) {
  const controls = document.createElement("section");
  controls.className = "control-panel";
  const verdictTitle = document.createElement("h2");
  verdictTitle.textContent = "오늘의 판정";
  controls.append(
    verdictTitle,
    VerdictControls({
      review,
      saveState: state.saveState,
      onChange: (patch) => updateReview(item.part_id, patch, true, true),
    }),
    MaskEditor({
      item,
      open: state.maskEditorOpen,
      saveState: state.maskSaveState,
      onOpenChange: (open) => {
        state.maskEditorOpen = open;
        state.maskSaveState = "idle";
        render();
      },
      onSaveMask: saveMask,
    }),
    sectionTitle("무슨 문제가 있나요?"),
    IssueTags({
      tags: state.manifest.issue_tags || [],
      selectedTags: review.issue_tags || [],
      onChange: (patch) => updateReview(item.part_id, patch, true, true),
    }),
    NotesPanel({
      item,
      review,
      onChange: (patch) => updateReview(item.part_id, patch, false),
      onSave: saveReview,
      saveState: state.saveState,
    }),
  );
  return controls;
}

function QaFlowPanel(item) {
  const panel = document.createElement("section");
  panel.className = "qa-flow-panel";
  const h2 = document.createElement("h2");
  h2.textContent = "검수 순서";
  const p = document.createElement("p");
  p.textContent = qaLead(item.review_gate);
  const ol = document.createElement("ol");
  for (const step of qaSteps(item.review_gate)) {
    const li = document.createElement("li");
    li.textContent = step;
    ol.append(li);
  }
  panel.append(h2, p, ol);
  return panel;
}

function sectionLabel(key) {
  return {
    g0_concept: "캐릭터 고르기",
    g1_part_taxonomy: "파츠 확인",
    g2_structure: "구조 자동검사",
    g3_motion_visual: "움직임 확인",
    production_parts: "PSD 파츠",
    reference_mouth: "입 참고",
    reference_blink: "눈 참고",
    overlays: "오버레이",
    concept_parts: "새 컨셉 파츠",
    seethrough_candidates: "See-through 후보",
    mps_compat_candidates: "Mac MPS 후보",
    layerdivider_candidates: "LayerDivider 후보",
    qwen_layer_candidates: "Qwen Layers 후보",
    vtuber2d_ai_candidates: "VTuber2D.AI 후보",
  }[key] || key;
}

function tierLabel(tier) {
  return {
    v2_min: "최소형",
    v2_standard: "표준형",
    v2_rich: "풍부형",
  }[tier] || tier || "최소형";
}

function defaultViewMode(item) {
  if (!item) return "crop_overlay";
  if (item.review_gate === "G3_MOTION_VISUAL") return "side_by_side";
  if (item.review_gate === "G2_STRUCTURE") return "structure_summary";
  return "crop_overlay";
}

function normalizeManifest(manifest) {
  const normalized = { ...manifest };
  const sections = {};
  for (const [section, items] of Object.entries(manifest.sections || {})) {
    sections[section] = items.map((item) => ({
      ...item,
      tier: item.tier || manifest.tier || "v2_min",
      review_gate: item.review_gate || gateForSection(section),
      simple_label: item.simple_label || item.ko_name || item.part_id,
      simple_description: item.simple_description || item.triage_notes?.join(" ") || "",
      checklist: item.checklist || checklistForGate(item.review_gate || gateForSection(section)),
      compare_views: item.compare_views || {},
      auto_check_summary: item.auto_check_summary || null,
    }));
  }
  normalized.sections = sections;
  normalized.issue_tags = (manifest.issue_tags || []).map(normalizeTag);
  return normalized;
}

function gateForSection(section) {
  if (section === "g0_concept" || section === "concept_parts") return "G0_CONCEPT";
  if (section === "g2_structure") return "G2_STRUCTURE";
  if (section === "g3_motion_visual") return "G3_MOTION_VISUAL";
  return "G1_PART_TAXONOMY";
}

function checklistForGate(gate) {
  return {
    G0_CONCEPT: ["눈, 입, 머리, 몸이 한눈에 보이나요?", "그림체가 마음에 드나요?", "팔이나 머리카락이 너무 복잡하게 겹치지 않나요?"],
    G1_PART_TAXONOMY: ["빠진 파츠가 있나요?", "투명 테두리가 깨끗한가요?", "잘린 곳이나 위치 틀어짐이 있나요?"],
    G2_STRUCTURE: ["자동검사 결과를 확인하세요.", "부족하면 Cubism 구조 작업이 필요합니다."],
    G3_MOTION_VISUAL: ["기본 포즈와 큰 움직임을 비교하세요.", "눈, 입, 머리카락, 몸각도가 자연스럽나요?"],
  }[gate] || [];
}

function sectionTitle(text) {
  const h2 = document.createElement("h2");
  h2.textContent = text;
  return h2;
}

function qaLead(gate) {
  return {
    G0_CONCEPT: "캐릭터를 오래 볼 수 있는지 고르는 단계입니다.",
    G1_PART_TAXONOMY: "큰 화면에서 파츠가 빠지거나 지저분한지만 봅니다.",
    G2_STRUCTURE: "이미지 감상이 아니라 숫자 자동검사 결과를 봅니다.",
    G3_MOTION_VISUAL: "중립과 극단 움직임을 비교해서 어색함을 찾습니다.",
  }[gate] || "큰 화면을 먼저 보고, 오른쪽에서 판정만 저장하세요.";
}

function qaSteps(gate) {
  return {
    G0_CONCEPT: [
      "가운데 큰 캐릭터를 5초 봅니다.",
      "눈, 입, 머리, 몸이 또렷한지 봅니다.",
      "마음에 들면 좋아요, 애매하면 참고만, 싫으면 다시 만들기.",
    ],
    G1_PART_TAXONOMY: [
      "파츠만 확대 또는 겹쳐 보기를 켭니다.",
      "없음, 지저분한 테두리, 위치 틀어짐만 찾습니다.",
      "문제 태그를 하나 고르고 고쳐서 쓰기 또는 다시 만들기를 누릅니다.",
    ],
    G2_STRUCTURE: [
      "자동검사 화면에서 ArtMesh/Parameter/Deformer/Keyform/Physics를 봅니다.",
      "PASS면 다음 단계, REVISE면 Cubism 구조 작업이 필요합니다.",
      "이 단계는 사람이 예쁘다/안 예쁘다로 판정하지 않습니다.",
    ],
    G3_MOTION_VISUAL: [
      "나란히 보기에서 기본 포즈와 큰 움직임을 비교합니다.",
      "눈, 입, 머리카락, 몸각도 중 어색한 곳만 찾습니다.",
      "움직임이 과하거나 끊기면 고쳐서 쓰기로 남깁니다.",
    ],
  }[gate] || [
    "가운데 큰 화면을 먼저 봅니다.",
    "문제가 있으면 태그를 고릅니다.",
    "오른쪽 판정 버튼으로 저장합니다.",
  ];
}

function reviewFor(partId) {
  if (!state.reviews[partId]) {
    state.reviews[partId] = {
      part_id: partId,
      verdict: "UNREVIEWED",
      issue_tags: [],
      human_note: "",
      updated_at: new Date().toISOString(),
    };
  }
  return state.reviews[partId];
}

function updateReview(partId, patch, rerender = true, autosave = false) {
  const current = reviewFor(partId);
  state.reviews[partId] = {
    ...current,
    ...patch,
    part_id: partId,
    updated_at: new Date().toISOString(),
  };
  state.saveState = "unsaved";
  if (rerender) render();
  if (autosave) queueSaveReview();
}

function queueSaveReview() {
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    saveTimer = null;
    saveReview();
  }, 200);
}

async function saveReview() {
  state.saveState = "saving";
  render();
  try {
    const response = await fetch("/api/save-review", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reviews: state.reviews }),
    });
    const result = await response.json();
    if (!response.ok || !result.ok) throw new Error(result.error || "Save failed");
    state.saveState = "saved";
  } catch (error) {
    console.error(error);
    state.saveState = "error";
  }
  render();
}

async function saveMask(item, maskDataUrl) {
  state.maskSaveState = "saving";
  render();
  try {
    const response = await fetch("/api/save-mask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        part_id: item.part_id,
        experiment_id: item.experiment_id,
        mask_data_url: maskDataUrl,
      }),
    });
    const result = await response.json();
    if (!response.ok || !result.ok) throw new Error(result.error || "Mask save failed");
    const [manifest, saved] = await Promise.all([fetchJson("/review_manifest.json"), fetchJson("/api/review")]);
    state.manifest = normalizeManifest(manifest);
    state.reviews = saved.review?.reviews || {};
    const manualPartId = result.manual_mask?.manual_part_id;
    if (manualPartId && state.allItems.some((candidate) => candidate.part_id === manualPartId)) {
      state.selectedId = manualPartId;
    }
    state.maskEditorOpen = false;
    state.maskSaveState = "saved";
  } catch (error) {
    console.error(error);
    state.maskSaveState = "error";
  }
  render();
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url} ${response.status}`);
  return response.json();
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" })[char]);
}

init();

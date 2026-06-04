import { PartList } from "./components/PartList.js";
import { PartViewer } from "./components/PartViewer.js";
import { VerdictControls } from "./components/VerdictControls.js";
import { IssueTags } from "./components/IssueTags.js";
import { NotesPanel } from "./components/NotesPanel.js";
import { FixQueuePanel } from "./components/FixQueuePanel.js";

const app = document.querySelector("#app");

const state = {
  manifest: null,
  reviews: {},
  selectedId: null,
  viewMode: "crop_overlay",
  saveState: "idle",
  filters: {
    section: "production_parts",
    query: "",
    verdict: "ALL",
  },
  get allItems() {
    return Object.values(this.manifest?.sections || {}).flat();
  },
  get currentItems() {
    return this.manifest?.sections?.[this.filters.section] || [];
  },
  get filteredItems() {
    const query = this.filters.query.trim().toLowerCase();
    return this.currentItems.filter((item) => {
      const review = this.reviews[item.part_id] || {};
      const verdict = review.verdict || "UNREVIEWED";
      const matchesQuery =
        !query ||
        item.part_id.toLowerCase().includes(query) ||
        item.ko_name.toLowerCase().includes(query) ||
        item.group.toLowerCase().includes(query);
      const matchesVerdict = this.filters.verdict === "ALL" || verdict === this.filters.verdict;
      return matchesQuery && matchesVerdict;
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
    state.manifest = manifest;
    state.reviews = saved.review?.reviews || {};
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
        state.viewMode = "crop_overlay";
        state.saveState = "idle";
        render();
      },
      onFilterChange: (patch) => {
        const sectionChanged = patch.section && patch.section !== state.filters.section;
        state.filters = { ...state.filters, ...patch };
        const selectedStillVisible = state.filteredItems.some((candidate) => candidate.part_id === state.selectedId);
        if (!selectedStillVisible) state.selectedId = state.filteredItems[0]?.part_id || null;
        if (sectionChanged) state.viewMode = "crop_overlay";
        render();
      },
    }),
    MainReviewArea(item, review),
    FixQueuePanel({
      queue: state.fixQueue,
      onSelect: (partId) => {
        const found = state.allItems.find((candidate) => candidate.part_id === partId);
        if (found) state.filters.section = found.section;
        state.selectedId = partId;
        render();
      },
    }),
  );
}

function Header() {
  const header = document.createElement("header");
  header.className = "app-header";
  const title = document.createElement("div");
  const h1 = document.createElement("h1");
  h1.textContent = "Live2D 파츠 순도 검수";
  const p = document.createElement("p");
  p.textContent = "PSD용 파츠와 입/눈 참고 이미지를 분리해서 보고, O/X/수정 판정을 저장합니다.";
  title.append(h1, p);

  const counts = document.createElement("div");
  counts.className = "counts";
  for (const [key, count] of Object.entries(state.manifest.counts || {})) {
    const chip = document.createElement("span");
    chip.textContent = `${sectionLabel(key)} ${count}개`;
    counts.append(chip);
  }
  header.append(title, counts);
  return header;
}

function MainReviewArea(item, review) {
  const main = document.createElement("main");
  main.className = "review-main";
  const viewer = PartViewer({
    item,
    viewMode: state.viewMode,
    onModeChange: (mode) => {
      state.viewMode = mode;
      render();
    },
  });

  const controls = document.createElement("section");
  controls.className = "control-panel";
  const verdictTitle = document.createElement("h2");
  verdictTitle.textContent = "판정";
  controls.append(
    verdictTitle,
    VerdictControls({
      review,
      onChange: (patch) => updateReview(item.part_id, patch),
    }),
    sectionTitle("문제 태그"),
    IssueTags({
      tags: state.manifest.issue_tags || [],
      selectedTags: review.issue_tags || [],
      onChange: (patch) => updateReview(item.part_id, patch),
    }),
    NotesPanel({
      item,
      review,
      onChange: (patch) => updateReview(item.part_id, patch, false),
      onSave: saveReview,
      saveState: state.saveState,
    }),
  );

  main.append(viewer, controls);
  return main;
}

function sectionLabel(key) {
  return {
    production_parts: "PSD 파츠",
    reference_mouth: "입 참고",
    reference_blink: "눈 참고",
    overlays: "오버레이",
    concept_parts: "새 컨셉 파츠",
    seethrough_candidates: "See-through 후보",
  }[key] || key;
}

function sectionTitle(text) {
  const h2 = document.createElement("h2");
  h2.textContent = text;
  return h2;
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

function updateReview(partId, patch, rerender = true) {
  const current = reviewFor(partId);
  state.reviews[partId] = {
    ...current,
    ...patch,
    part_id: partId,
    updated_at: new Date().toISOString(),
  };
  state.saveState = "idle";
  if (rerender) render();
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

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url} ${response.status}`);
  return response.json();
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" })[char]);
}

init();

export function PartList({ state, onSelect, onFilterChange }) {
  const sectionEntries = Object.entries(state.manifest.sections || {});
  const items = state.filteredItems;

  const root = document.createElement("aside");
  root.className = "part-list";

  const tabs = document.createElement("div");
  tabs.className = "tabs";
  for (const [section, sectionItems] of sectionEntries) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = section === state.filters.section ? "active" : "";
    button.textContent = tabLabel(section, sectionItems.length);
    button.addEventListener("click", () => onFilterChange({ section }));
    tabs.append(button);
  }

  const controls = document.createElement("div");
  controls.className = "list-controls";
  const search = document.createElement("input");
  search.type = "search";
  search.placeholder = "파츠 ID / 한글명 검색";
  search.value = state.filters.query;
  search.addEventListener("input", () => onFilterChange({ query: search.value }));

  const verdict = document.createElement("select");
  for (const value of ["ALL", "UNREVIEWED", "O", "X", "REVISE", "REFERENCE_ONLY"]) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = verdictLabel(value);
    option.selected = state.filters.verdict === value;
    verdict.append(option);
  }
  verdict.addEventListener("change", () => onFilterChange({ verdict: verdict.value }));
  controls.append(search, verdict);

  const list = document.createElement("div");
  list.className = "items";
  for (const item of items) {
    const review = state.reviews[item.part_id] || {};
    const button = document.createElement("button");
    button.type = "button";
    button.className = item.part_id === state.selectedId ? "part-row active" : "part-row";
    button.addEventListener("click", () => onSelect(item.part_id));

    const title = document.createElement("span");
    title.className = "part-title";
    title.textContent = item.part_id;

    const subtitle = document.createElement("span");
    subtitle.className = "part-subtitle";
    subtitle.textContent = `${item.ko_name} · ${groupLabel(item.group)}`;

    const chip = document.createElement("span");
    chip.className = `verdict-chip ${verdictClass(review.verdict || item.status)}`;
    chip.textContent = verdictLabel(review.verdict || "UNREVIEWED");

    button.append(title, subtitle, chip);
    list.append(button);
  }

  root.append(tabs, controls, list);
  return root;
}

function groupLabel(group) {
  return {
    face: "얼굴",
    hair: "머리카락",
    body: "몸/의상",
    eyes: "눈",
    brows: "눈썹",
    mouth: "입",
    ears: "귀",
    fur: "털",
    accessory: "장식",
    reference_mouth: "입 참고",
    reference_blink: "눈 참고",
    overlays: "오버레이",
    seethrough_reference: "See-through 참고",
  }[group] || group;
}

function tabLabel(section, count) {
  const labels = {
    production_parts: "PSD 파츠",
    reference_mouth: "입 참고",
    reference_blink: "눈 참고",
    overlays: "오버레이",
    concept_parts: "새 컨셉 파츠",
    seethrough_candidates: "See-through 후보",
  };
  return `${labels[section] || section} ${count}개`;
}

function verdictClass(verdict) {
  if (verdict === "O" || verdict === "OBSERVED" || verdict === "VERIFIED") return "ok";
  if (verdict === "X" || verdict === "FAIL" || verdict === "DISCARDED") return "bad";
  if (verdict === "REVISE") return "revise";
  if (verdict === "REFERENCE_ONLY") return "reference";
  return "empty";
}

function verdictLabel(verdict) {
  return {
    ALL: "전체",
    UNREVIEWED: "미검수",
    O: "O 통과",
    X: "X 실패",
    REVISE: "수정",
    REFERENCE_ONLY: "참고용",
    OBSERVED: "관찰됨",
    VERIFIED: "검증됨",
    FAIL: "실패",
    DISCARDED: "폐기",
  }[verdict] || verdict;
}

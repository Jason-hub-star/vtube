export function PartList({ state, onSelect, onFilterChange }) {
  const sectionEntries = Object.entries(state.manifest.sections || {});
  const items = state.filteredItems;

  const root = document.createElement("aside");
  root.className = "part-list";

  const tabs = document.createElement("div");
  tabs.className = "tabs";
  if (sectionEntries.length === 1) {
    const label = document.createElement("div");
    label.className = "single-section-label";
    const [section, sectionItems] = sectionEntries[0];
    label.textContent = tabLabel(section, sectionItems.length);
    tabs.append(label);
  } else {
    for (const [section, sectionItems] of sectionEntries) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = section === state.filters.section ? "active" : "";
      button.textContent = tabLabel(section, sectionItems.length);
      button.addEventListener("click", () => onFilterChange({ section }));
      tabs.append(button);
    }
  }

  const controls = document.createElement("div");
  controls.className = "list-controls";

  const tier = document.createElement("select");
  for (const value of ["ALL", "v2_min", "v2_standard", "v2_rich"]) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = tierLabel(value);
    option.selected = state.filters.tier === value;
    tier.append(option);
  }
  tier.addEventListener("change", () => onFilterChange({ tier: tier.value }));

  const gate = document.createElement("select");
  for (const value of ["ALL", "G0_CONCEPT", "G1_PART_TAXONOMY", "G2_STRUCTURE", "G3_MOTION_VISUAL"]) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = gateLabel(value);
    option.selected = state.filters.gate === value;
    gate.append(option);
  }
  gate.addEventListener("change", () => onFilterChange({ gate: gate.value }));

  const search = document.createElement("input");
  search.type = "search";
  search.placeholder = "이름 검색";
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

  const issueTag = document.createElement("select");
  for (const value of ["ALL", ...state.normalizedIssueTags.map((tag) => tag.code)]) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value === "ALL" ? "문제 전체" : state.issueTagLabel(value);
    option.selected = state.filters.issueTag === value;
    issueTag.append(option);
  }
  issueTag.addEventListener("change", () => onFilterChange({ issueTag: issueTag.value }));

  controls.append(tier, gate, search, verdict, issueTag);

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
    title.textContent = item.simple_label || item.ko_name || item.part_id;

    const subtitle = document.createElement("span");
    subtitle.className = "part-subtitle";
    subtitle.textContent = [gateLabel(item.review_gate), groupLabel(item.group), triageLabel(item.triage_status)]
      .filter(Boolean)
      .join(" · ");

    const chip = document.createElement("span");
    chip.className = `verdict-chip ${verdictClass(review.verdict || item.status)}`;
    chip.textContent = verdictLabel(review.verdict || "UNREVIEWED");

    button.append(title, subtitle, chip);
    list.append(button);
  }

  root.append(tabs, controls, list);
  return root;
}

function tierLabel(tier) {
  return {
    ALL: "단계 전체",
    v2_min: "최소형",
    v2_standard: "표준형",
    v2_rich: "풍부형",
  }[tier] || tier;
}

function gateLabel(gate) {
  return {
    ALL: "검수 전체",
    G0_CONCEPT: "캐릭터 고르기",
    G1_PART_TAXONOMY: "파츠 확인",
    G2_STRUCTURE: "구조 자동검사",
    G3_MOTION_VISUAL: "움직임 확인",
  }[gate] || gate;
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
    mps_compat_reference: "Mac MPS 참고",
    layerdivider_reference: "LayerDivider 참고",
    qwen_layer_reference: "Qwen Layers 참고",
    vtuber2d_ai_reference: "VTuber2D.AI 참고",
  }[group] || group;
}

function tabLabel(section, count) {
  const labels = {
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
    UNREVIEWED: "아직 안 봄",
    O: "좋아요",
    X: "다시 만들기",
    REVISE: "고쳐서 쓰기",
    REFERENCE_ONLY: "참고만",
    OBSERVED: "관찰됨",
    VERIFIED: "검증됨",
    FAIL: "실패",
    DISCARDED: "폐기",
  }[verdict] || verdict;
}

function triageLabel(status) {
  return {
    REVIEW_PRIORITY: "우선 검수",
    REVIEW_HIGH_RISK: "오염 위험",
    REFERENCE_REVIEW: "참고 판단",
    X_CANDIDATE_EMPTY: "빈 후보",
  }[status] || "";
}

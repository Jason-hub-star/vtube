export function PartViewer({ item, viewMode, onionOpacity = 0.55, onModeChange, onOpacityChange }) {
  const root = document.createElement("section");
  root.className = "viewer-panel";

  const header = document.createElement("div");
  header.className = "viewer-header";
  const titleWrap = document.createElement("div");
  const title = document.createElement("h1");
  title.textContent = item.simple_label || `${item.ko_name} (${item.part_id})`;
  const subtitle = document.createElement("p");
  subtitle.textContent = [
    gateLabel(item.review_gate),
    groupLabel(item.group),
    roleLabel(item.role),
    triageLabel(item.triage_status),
    item.include_in_import_psd ? "PSD 포함" : "PSD 제외",
  ]
    .filter(Boolean)
    .join(" · ");
  titleWrap.append(title, subtitle);

  const modes = document.createElement("div");
  modes.className = "mode-toggle";
  for (const mode of viewModesFor(item)) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = modeLabel(mode);
    button.className = viewMode === mode ? "active" : "";
    button.addEventListener("click", () => onModeChange(mode));
    modes.append(button);
  }
  header.append(titleWrap, modes);

  const stage = document.createElement("div");
  stage.className = `image-stage ${viewMode}`;
  const crop = cropBox(item);
  const isEmptyCandidate = !item.bbox || Number(item.alpha_coverage || 0) === 0;

  if (viewMode === "structure_summary") {
    stage.append(structureSummary(item));
  } else if (viewMode === "side_by_side") {
    stage.append(compareGrid("기본", comparePath(item, "neutral") || item.canonical_path, "크게 움직임", comparePath(item, "extreme") || item.overlay_path || item.image_path));
  } else if (viewMode === "before_after") {
    stage.append(compareGrid("수정 전", comparePath(item, "before") || item.source_path || item.canonical_path, "수정 후", comparePath(item, "after") || item.image_path || item.overlay_path));
  } else if (viewMode === "alone_composited") {
    stage.append(compareGrid("파츠만", comparePath(item, "layer") || item.image_path, "합쳐서 보기", comparePath(item, "composited") || item.overlay_path || item.canonical_path));
  } else if (viewMode === "onion_skin") {
    stage.append(onionSkin(item, crop, onionOpacity, onOpacityChange));
  } else if (viewMode === "canonical" && item.canonical_path) {
    stage.append(image(item.canonical_path, "기준 이미지", "fit-image"));
  } else if (viewMode === "checker" && item.image_path) {
    stage.append(cropFrame(item, crop, [image(item.image_path, "체커 배경 위 파츠", "crop-image")]));
  } else if (viewMode === "crop_part" && item.image_path) {
    stage.append(cropFrame(item, crop, [image(item.image_path, "확대된 파츠 이미지", "crop-image")]));
  } else if (viewMode === "full_overlay") {
    if (item.canonical_path) {
      stage.append(image(item.canonical_path, "기준 이미지", "fit-image base"));
    }
    if (item.overlay_path) {
      stage.append(image(item.overlay_path, "오버레이 비교", "fit-image overlay-image"));
    } else if (item.image_path) {
      stage.append(image(item.image_path, "파츠 전체 오버레이", "fit-image overlay-image"));
    }
  } else {
    const layers = [];
    if (item.canonical_path) layers.push(image(item.canonical_path, "확대된 기준 이미지", "crop-image base"));
    if (item.overlay_path) {
      layers.push(image(item.overlay_path, "확대된 오버레이 비교", "crop-image overlay-image"));
    } else if (item.image_path) {
      layers.push(image(item.image_path, "확대된 파츠 오버레이", "crop-image overlay-image"));
    }
    stage.append(cropFrame(item, crop, layers));
  }
  if (isEmptyCandidate && viewMode !== "canonical") {
    const notice = document.createElement("div");
    notice.className = "empty-candidate-notice";
    notice.textContent = "알파가 비어 있거나 bbox가 없습니다. 보통 X 또는 참고용 후보입니다.";
    stage.append(notice);
  }

  const meta = document.createElement("dl");
  meta.className = "item-meta";
  addMeta(meta, "검수 단계", gateLabel(item.review_gate));
  addMeta(meta, "파츠 영역", item.bbox ? item.bbox.join(", ") : "없음");
  addMeta(meta, "투명도", item.alpha_coverage ?? "해당 없음");
  addMeta(meta, "PSD", item.include_in_import_psd ? "포함" : "제외");

  const quickGuide = document.createElement("div");
  quickGuide.className = "quick-guide";
  const guideTitle = document.createElement("strong");
  guideTitle.textContent = item.simple_description || guideForGate(item.review_gate);
  quickGuide.append(guideTitle);
  if (item.checklist?.length) {
    const ul = document.createElement("ul");
    for (const check of item.checklist) {
      const li = document.createElement("li");
      li.textContent = check;
      ul.append(li);
    }
    quickGuide.append(ul);
  }

  root.append(header, quickGuide, stage, meta);
  return root;
}

function viewModesFor(item) {
  const base = ["crop_overlay", "crop_part", "full_overlay", "onion_skin", "alone_composited"];
  if (item.review_gate === "G2_STRUCTURE") return ["structure_summary", "side_by_side", "before_after"];
  if (item.review_gate === "G3_MOTION_VISUAL") return ["side_by_side", "onion_skin", "before_after", "alone_composited"];
  return [...base, "canonical", "checker"];
}

function cropBox(item) {
  const canvas = item.canvas_size || [2048, 2048];
  if (!item.bbox) return { x: 0, y: 0, w: canvas[0], h: canvas[1], canvas };
  const [x, y, w, h] = item.bbox;
  const pad = Math.max(48, Math.round(Math.max(w, h) * 0.22));
  const left = Math.max(0, x - pad);
  const top = Math.max(0, y - pad);
  const right = Math.min(canvas[0], x + w + pad);
  const bottom = Math.min(canvas[1], y + h + pad);
  return { x: left, y: top, w: right - left, h: bottom - top, canvas };
}

function cropFrame(item, crop, images) {
  const frame = document.createElement("div");
  frame.className = "crop-frame";
  frame.style.aspectRatio = `${crop.w} / ${crop.h}`;

  const label = document.createElement("div");
  label.className = "crop-label";
  label.textContent = item.bbox ? "자동 확대 보기" : "전체 캔버스 보기";

  for (const img of images) {
    img.style.width = `${(crop.canvas[0] / crop.w) * 100}%`;
    img.style.height = `${(crop.canvas[1] / crop.h) * 100}%`;
    img.style.left = `${-(crop.x / crop.w) * 100}%`;
    img.style.top = `${-(crop.y / crop.h) * 100}%`;
    frame.append(img);
  }
  frame.append(label);
  return frame;
}

function compareGrid(leftLabel, leftPath, rightLabel, rightPath) {
  const grid = document.createElement("div");
  grid.className = "compare-grid";
  grid.append(comparePane(leftLabel, leftPath), comparePane(rightLabel, rightPath));
  return grid;
}

function comparePane(labelText, src) {
  const pane = document.createElement("div");
  pane.className = "compare-pane";
  const label = document.createElement("span");
  label.textContent = labelText;
  if (src) {
    pane.append(image(src, labelText, "compare-image"));
  } else {
    const empty = document.createElement("p");
    empty.textContent = "이미지 없음";
    pane.append(empty);
  }
  pane.append(label);
  return pane;
}

function onionSkin(item, crop, opacity, onOpacityChange) {
  const root = document.createElement("div");
  root.className = "onion-wrap";
  const layers = [];
  if (comparePath(item, "neutral") || item.canonical_path) {
    layers.push(image(comparePath(item, "neutral") || item.canonical_path, "기본 이미지", "crop-image base"));
  }
  const overlay = image(comparePath(item, "extreme") || item.overlay_path || item.image_path, "겹쳐 보는 이미지", "crop-image overlay-image");
  overlay.style.opacity = String(opacity);
  layers.push(overlay);
  root.append(cropFrame(item, crop, layers));
  const control = document.createElement("label");
  control.className = "opacity-control";
  control.textContent = "겹침 진하기";
  const input = document.createElement("input");
  input.type = "range";
  input.min = "0";
  input.max = "1";
  input.step = "0.05";
  input.value = String(opacity);
  input.addEventListener("input", () => onOpacityChange?.(Number(input.value)));
  control.append(input);
  root.append(control);
  return root;
}

function structureSummary(item) {
  const root = document.createElement("div");
  root.className = "structure-summary";
  const summary = item.auto_check_summary || {};
  const status = document.createElement("strong");
  status.className = `structure-status ${String(summary.status || "PENDING").toLowerCase()}`;
  status.textContent = statusLabel(summary.status);
  const hint = document.createElement("p");
  hint.textContent =
    summary.message ||
    "자동검사 결과가 아직 없습니다. PASS로 처리하지 말고 inspector/comparator 결과를 먼저 넣어주세요.";
  root.append(status, hint);

  const checks = summary.checks || {};
  const entries = [
    ["필수 파츠", checks.required_part_count],
    ["Alpha/crop", checks.alpha_bbox_crop],
    ["ArtMesh", checks.artmesh_count],
    ["Parameter", checks.parameter_count],
    ["Deformer", checks.deformer_count],
    ["Keyform", checks.keyform_binding_count],
    ["Physics", checks.physics_group_count],
  ];
  const grid = document.createElement("dl");
  for (const [label, value] of entries) {
    addMeta(grid, label, value ?? "대기");
  }
  root.append(grid);
  return root;
}

function comparePath(item, key) {
  const value = item.compare_views?.[key];
  if (!value) return null;
  if (typeof value === "string") return value;
  return value.path || value.image_path || null;
}

function image(src, alt, className) {
  const img = document.createElement("img");
  img.src = src;
  img.alt = alt;
  img.className = className;
  img.loading = "eager";
  return img;
}

function addMeta(root, label, value) {
  const dt = document.createElement("dt");
  dt.textContent = label;
  const dd = document.createElement("dd");
  dd.textContent = String(value);
  root.append(dt, dd);
}

function modeLabel(mode) {
  return {
    crop_overlay: "확대 비교",
    crop_part: "파츠만 확대",
    full_overlay: "전체 비교",
    side_by_side: "나란히 보기",
    onion_skin: "겹쳐 보기",
    before_after: "전후 비교",
    alone_composited: "단독/합성",
    structure_summary: "자동검사",
    canonical: "기준 원본",
    checker: "투명 배경",
  }[mode];
}

function gateLabel(gate) {
  return {
    G0_CONCEPT: "캐릭터 고르기",
    G1_PART_TAXONOMY: "파츠 확인",
    G2_STRUCTURE: "구조 자동검사",
    G3_MOTION_VISUAL: "움직임 확인",
  }[gate] || "";
}

function guideForGate(gate) {
  return {
    G0_CONCEPT: "캐릭터가 마음에 드는지 먼저 고릅니다.",
    G1_PART_TAXONOMY: "파츠가 빠지거나 지저분하지 않은지 봅니다.",
    G2_STRUCTURE: "사람 눈보다 자동 숫자검사를 믿는 단계입니다.",
    G3_MOTION_VISUAL: "눈, 입, 머리카락, 몸이 움직일 때 어색한지 봅니다.",
  }[gate] || "이미지를 보고 판정합니다.";
}

function statusLabel(status) {
  return {
    PASS: "자동검사 PASS",
    FAIL: "자동검사 FAIL",
    REVISE: "구조 보강 필요",
    PENDING: "자동검사 대기",
  }[status] || "자동검사 대기";
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
    reference_blink: "눈깜빡임 참고",
    overlays: "오버레이",
    seethrough_reference: "See-through 참고",
    mps_compat_reference: "Mac MPS 참고",
    layerdivider_reference: "LayerDivider 참고",
    qwen_layer_reference: "Qwen Layers 참고",
    vtuber2d_ai_reference: "VTuber2D.AI 참고",
  }[group] || group;
}

function roleLabel(role) {
  return {
    underpaint: "언더페인트",
    back_hair: "뒷머리",
    body: "몸통",
    clothes: "의상",
    neck: "목",
    face: "얼굴",
    eye_white: "흰자",
    iris: "홍채",
    pupil: "동공",
    highlight: "하이라이트",
    upper_lash: "윗속눈썹",
    lower_lash: "아랫속눈썹",
    brow: "눈썹",
    mouth_line: "입 라인",
    mouth_inner: "입 안쪽",
    teeth: "치아",
    tongue: "혀",
    side_hair: "옆머리",
    front_hair: "앞머리",
    ears: "귀",
    fur: "털",
    accessory: "장식",
    mouth_keypose_reference: "입 키포즈 참고",
    blink_keypose_reference: "눈깜빡임 키포즈 참고",
    overlay_reference: "비교 오버레이",
    seethrough_reference: "See-through 참고",
  }[role] || role;
}

function triageLabel(status) {
  return {
    REVIEW_PRIORITY: "우선 검수",
    REVIEW_HIGH_RISK: "오염 위험",
    REFERENCE_REVIEW: "참고 판단",
    X_CANDIDATE_EMPTY: "빈 후보",
  }[status] || "";
}

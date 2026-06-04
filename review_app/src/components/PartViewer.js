export function PartViewer({ item, viewMode, onModeChange }) {
  const root = document.createElement("section");
  root.className = "viewer-panel";

  const header = document.createElement("div");
  header.className = "viewer-header";
  const titleWrap = document.createElement("div");
  const title = document.createElement("h1");
  title.textContent = `${item.ko_name} (${item.part_id})`;
  const subtitle = document.createElement("p");
  subtitle.textContent = `${groupLabel(item.group)} · ${roleLabel(item.role)} · ${item.include_in_import_psd ? "PSD 포함" : "PSD 제외"}`;
  titleWrap.append(title, subtitle);

  const modes = document.createElement("div");
  modes.className = "mode-toggle";
  for (const mode of ["crop_overlay", "crop_part", "full_overlay", "canonical", "checker"]) {
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

  if (viewMode === "canonical" && item.canonical_path) {
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

  const meta = document.createElement("dl");
  meta.className = "item-meta";
  addMeta(meta, "영역", item.bbox ? item.bbox.join(", ") : "없음");
  addMeta(meta, "알파", item.alpha_coverage ?? "해당 없음");
  addMeta(meta, "순서", item.draw_order ?? "해당 없음");
  addMeta(meta, "PSD", item.include_in_import_psd ? "포함" : "제외");

  root.append(header, stage, meta);
  return root;
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
    canonical: "기준 원본",
    checker: "투명 배경",
  }[mode];
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
